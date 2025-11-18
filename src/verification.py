#!/usr/bin/env python3
"""
3-Source Verification System - Professional Intelligence Reliability Scoring

Implements intelligence community standards for source reliability:
- CONFIRMED: 3+ independent sources OR direct observation
- PROBABLE: 2 sources OR single authoritative source
- POSSIBLE: Single source, no contradictions
- UNVERIFIED: Raw data, not yet validated

This module automatically scores data reliability across multiple sources
and flags contradictions that require human analyst review.
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
from enum import Enum
from dataclasses import dataclass, field

from .utils import setup_logger

logger = setup_logger(__name__)


class VerificationLevel(Enum):
    """Intelligence reliability levels"""
    CONFIRMED = 4   # 3+ sources or direct observation
    PROBABLE = 3    # 2 sources or authoritative source
    POSSIBLE = 2    # 1 source, no contradictions
    UNVERIFIED = 1  # Raw data, not validated
    CONTRADICTED = 0  # Multiple conflicting sources


@dataclass
class DataPoint:
    """Represents a single piece of intelligence with source"""
    field_name: str  # e.g., "email", "location", "name"
    value: str
    source: str  # e.g., "github_profile", "whois", "linkedin"
    confidence: int = 50  # 0-100
    timestamp: str = ""


@dataclass
class VerificationResult:
    """Result of 3-source verification"""
    field_name: str
    value: str
    verification_level: VerificationLevel
    sources: List[str] = field(default_factory=list)
    source_count: int = 0
    confidence: int = 0
    contradictions: List[str] = field(default_factory=list)
    notes: str = ""


class VerificationEngine:
    """
    3-Source Verification Engine

    Aggregates data from multiple sources and applies intelligence
    community standards for reliability scoring.
    """

    def __init__(self):
        """Initialize verification engine"""
        # Authoritative sources (single source = PROBABLE)
        self.authoritative_sources = {
            'whois',  # Domain registrant data
            'ssl_certificate',  # Certificate data
            'dns',  # DNS records
            'breach_database',  # haveibeenpwned, etc.
            'government_database'  # Official records
        }

        # Source reliability weights (0.0-1.0)
        self.source_weights = {
            # High reliability
            'whois': 0.95,
            'ssl_certificate': 0.95,
            'dns': 0.95,
            'breach_database': 0.90,

            # Medium reliability
            'github_profile': 0.75,
            'linkedin_profile': 0.75,
            'gravatar': 0.70,

            # Lower reliability
            'twitter_bio': 0.60,
            'instagram_bio': 0.60,
            'user_submitted': 0.50,

            # Unknown sources default
            'unknown': 0.40
        }

    def verify_data_point(self, data_points: List[DataPoint]) -> VerificationResult:
        """
        Verify a single data point across multiple sources.

        Args:
            data_points: List of DataPoint objects for the same field

        Returns:
            VerificationResult with reliability score
        """
        if not data_points:
            return VerificationResult(
                field_name="unknown",
                value="",
                verification_level=VerificationLevel.UNVERIFIED,
                notes="No data provided"
            )

        field_name = data_points[0].field_name

        # Group by value (detect contradictions)
        by_value = defaultdict(list)
        for dp in data_points:
            # Normalize value for comparison
            normalized = self._normalize_value(dp.value)
            by_value[normalized].append(dp)

        # Find most common value
        most_common_value = max(by_value.keys(), key=lambda v: len(by_value[v]))
        supporting_points = by_value[most_common_value]

        # Count unique sources
        unique_sources = set(dp.source for dp in supporting_points)
        source_count = len(unique_sources)

        # Check for authoritative sources
        has_authoritative = any(
            dp.source in self.authoritative_sources
            for dp in supporting_points
        )

        # Determine verification level
        if source_count >= 3:
            level = VerificationLevel.CONFIRMED
        elif source_count == 2 or has_authoritative:
            level = VerificationLevel.PROBABLE
        elif source_count == 1:
            level = VerificationLevel.POSSIBLE
        else:
            level = VerificationLevel.UNVERIFIED

        # Check for contradictions
        contradictions = []
        if len(by_value) > 1:
            level = VerificationLevel.CONTRADICTED
            for value, points in by_value.items():
                if value != most_common_value:
                    sources = [dp.source for dp in points]
                    contradictions.append(
                        f"{value} (from: {', '.join(sources)})"
                    )

        # Calculate weighted confidence
        confidence = self._calculate_confidence(supporting_points, level)

        return VerificationResult(
            field_name=field_name,
            value=supporting_points[0].value,  # Original (non-normalized) value
            verification_level=level,
            sources=list(unique_sources),
            source_count=source_count,
            confidence=confidence,
            contradictions=contradictions,
            notes=f"Verified by {source_count} source(s)" +
                  (f", {len(contradictions)} contradiction(s) found" if contradictions else "")
        )

    def verify_account(self, account_data: Dict) -> Dict[str, VerificationResult]:
        """
        Verify all fields in an account using 3-source methodology.

        Args:
            account_data: Dict with account information

        Returns:
            Dict of field_name -> VerificationResult
        """
        # Extract data points by field
        field_data = defaultdict(list)

        # Common fields to verify
        fields_to_check = ['name', 'email', 'location', 'username', 'bio']

        for field in fields_to_check:
            if field in account_data and account_data[field]:
                # Create data point from account
                dp = DataPoint(
                    field_name=field,
                    value=account_data[field],
                    source=account_data.get('platform', 'unknown'),
                    confidence=account_data.get('quality_score', 50)
                )
                field_data[field].append(dp)

        # Verify each field
        results = {}
        for field, data_points in field_data.items():
            results[field] = self.verify_data_point(data_points)

        return results

    def aggregate_multi_account(self, accounts: List[Dict]) -> Dict[str, VerificationResult]:
        """
        Aggregate data across multiple accounts and verify.

        This is the main entry point for multi-source verification.

        Args:
            accounts: List of account dictionaries

        Returns:
            Dict of field_name -> VerificationResult
        """
        # Collect all data points by field
        all_data_points = defaultdict(list)

        for account in accounts:
            if not account:
                continue

            platform = account.get('platform', 'unknown')
            quality = account.get('quality_score', 50)

            # Extract data points for common fields
            fields = {
                'name': account.get('name'),
                'email': account.get('email'),
                'location': account.get('location'),
                'username': account.get('username'),
                'bio': account.get('bio')
            }

            for field_name, value in fields.items():
                if value:
                    dp = DataPoint(
                        field_name=field_name,
                        value=value,
                        source=f"{platform}_profile",
                        confidence=quality
                    )
                    all_data_points[field_name].append(dp)

        # Verify each field across all sources
        verification_results = {}
        for field_name, data_points in all_data_points.items():
            verification_results[field_name] = self.verify_data_point(data_points)

        return verification_results

    def _normalize_value(self, value: str) -> str:
        """
        Normalize value for comparison.

        Handles case, whitespace, and common variations.
        """
        if not value:
            return ""

        normalized = value.lower().strip()

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        # Remove common punctuation
        normalized = normalized.replace('.', '').replace(',', '')

        return normalized

    def _calculate_confidence(self, data_points: List[DataPoint],
                            level: VerificationLevel) -> int:
        """
        Calculate weighted confidence score.

        Factors:
        - Source reliability weights
        - Number of sources
        - Verification level
        - Individual confidence scores

        Returns:
            Confidence score 0-100
        """
        if not data_points:
            return 0

        # Base score from verification level
        level_scores = {
            VerificationLevel.CONFIRMED: 90,
            VerificationLevel.PROBABLE: 75,
            VerificationLevel.POSSIBLE: 50,
            VerificationLevel.UNVERIFIED: 25,
            VerificationLevel.CONTRADICTED: 10
        }

        base_score = level_scores.get(level, 25)

        # Weight by source reliability
        source_scores = []
        for dp in data_points:
            source = dp.source
            weight = self.source_weights.get(source, self.source_weights['unknown'])
            weighted_score = dp.confidence * weight
            source_scores.append(weighted_score)

        # Average weighted scores
        if source_scores:
            avg_source_score = sum(source_scores) / len(source_scores)
        else:
            avg_source_score = base_score

        # Combine base and source scores (60% base, 40% source)
        final_score = int(base_score * 0.6 + avg_source_score * 0.4)

        return max(0, min(100, final_score))
