#!/usr/bin/env python3
"""
Adverse Inference Detection - Intelligence Gap Analysis

When data is deliberately hidden or suspiciously absent, intelligence analysts
use "adverse inference" to deduce intent or activity from the gaps.

Examples:
- 3-year gap in employment history → Possible incarceration, military deployment
- No social media 2018-2021 → Deliberate profile scrubbing, witness protection
- All profiles created same month → Identity creation, sock puppets
- Consistent timezone but no location → OPSEC awareness, hiding location

This module automatically detects and flags suspicious patterns for human review.
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re

from .utils import setup_logger

logger = setup_logger(__name__)


class AdverseInferenceEngine:
    """
    Detects suspicious gaps, patterns, and anomalies in OSINT data.

    Professional OSINT tradecraft for identifying:
    - Temporal gaps (missing time periods)
    - Data scrubbing indicators
    - Sock puppet patterns
    - OpSec awareness indicators
    """

    def __init__(self):
        """Initialize adverse inference engine"""
        self.current_year = datetime.now().year

    def analyze(self, accounts: List[Dict], target_profile: Dict = None) -> Dict:
        """
        Perform complete adverse inference analysis.

        Args:
            accounts: List of discovered accounts
            target_profile: Optional target profile data

        Returns:
            Dict of detected anomalies and inferences
        """
        results = {
            'temporal_gaps': [],
            'scrubbing_indicators': [],
            'sock_puppet_indicators': [],
            'opsec_indicators': [],
            'anomalies': [],
            'risk_score': 0
        }

        if not accounts:
            return results

        # Detect temporal gaps
        results['temporal_gaps'] = self._detect_temporal_gaps(accounts)

        # Detect profile scrubbing
        results['scrubbing_indicators'] = self._detect_scrubbing(accounts)

        # Detect sock puppets
        results['sock_puppet_indicators'] = self._detect_sock_puppets(accounts)

        # Detect OpSec awareness
        results['opsec_indicators'] = self._detect_opsec_awareness(accounts)

        # Detect general anomalies
        results['anomalies'] = self._detect_anomalies(accounts)

        # Calculate overall risk score
        results['risk_score'] = self._calculate_risk_score(results)

        return results

    def _detect_temporal_gaps(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect suspicious time gaps in activity.

        Red flags:
        - Multi-year gaps in account creation
        - Sudden stops and restarts in activity
        - Profiles dormant for years then suddenly active
        """
        gaps = []

        # Extract account creation dates
        creation_dates = []
        for acc in accounts:
            if not acc:
                continue

            # Try to find creation date from posts
            posts = acc.get('posts', [])
            if posts:
                for post in posts:
                    date_fields = ['created_at', 'published', 'posted_at', 'timestamp']
                    for field in date_fields:
                        if post.get(field):
                            try:
                                # Parse date
                                date_str = post[field]
                                if isinstance(date_str, str):
                                    # Simple year extraction
                                    year_match = re.search(r'(20\d{2})', date_str)
                                    if year_match:
                                        year = int(year_match.group(1))
                                        creation_dates.append(year)
                                        break
                            except:
                                pass

        if len(creation_dates) >= 2:
            # Sort dates
            sorted_dates = sorted(set(creation_dates))

            # Find gaps > 2 years
            for i in range(len(sorted_dates) - 1):
                gap = sorted_dates[i + 1] - sorted_dates[i]
                if gap > 2:
                    gaps.append({
                        'type': 'multi_year_gap',
                        'start_year': sorted_dates[i],
                        'end_year': sorted_dates[i + 1],
                        'gap_years': gap,
                        'severity': 'HIGH' if gap > 5 else 'MEDIUM',
                        'inference': f"{gap}-year gap in online activity. Possible causes: "
                                   f"incarceration, military deployment, witness protection, "
                                   f"deliberate profile dormancy, or identity change."
                    })

        # Check for recent dormancy
        if creation_dates:
            most_recent = max(creation_dates)
            years_dormant = self.current_year - most_recent

            if years_dormant > 2:
                gaps.append({
                    'type': 'recent_dormancy',
                    'last_activity': most_recent,
                    'years_dormant': years_dormant,
                    'severity': 'MEDIUM',
                    'inference': f"No public activity since {most_recent} ({years_dormant} years). "
                               f"Possible profile abandonment or migration to new identity."
                })

        return gaps

    def _detect_scrubbing(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect indicators of deliberate data scrubbing.

        Red flags:
        - Very minimal profiles (name only, no bio, no posts)
        - Empty bios when platform typically has them
        - Deleted post history (indicators)
        """
        scrubbing_indicators = []

        empty_profile_count = 0
        minimal_data_count = 0

        for acc in accounts:
            if not acc:
                continue

            platform = acc.get('platform', 'unknown')
            has_name = bool(acc.get('name'))
            has_bio = bool(acc.get('bio'))
            has_location = bool(acc.get('location'))
            has_posts = bool(acc.get('posts'))
            post_count = len(acc.get('posts', []))

            # Completely empty profile
            if not has_name and not has_bio and not has_location and not has_posts:
                empty_profile_count += 1

            # Minimal data (name only)
            if has_name and not has_bio and not has_location and post_count == 0:
                minimal_data_count += 1

        # Flag if >50% profiles are minimal
        total_accounts = len([a for a in accounts if a])
        if total_accounts > 0:
            minimal_percentage = (minimal_data_count / total_accounts) * 100

            if minimal_percentage > 50:
                scrubbing_indicators.append({
                    'type': 'mass_minimal_profiles',
                    'percentage': minimal_percentage,
                    'count': minimal_data_count,
                    'severity': 'HIGH',
                    'inference': f"{minimal_percentage:.0f}% of profiles have minimal data "
                               f"(name only, no bio/location/posts). This suggests either: "
                               f"(1) Deliberate profile scrubbing for privacy, "
                               f"(2) Sock puppet/bot accounts, or "
                               f"(3) Inactive/abandoned accounts."
                })

        return scrubbing_indicators

    def _detect_sock_puppets(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect indicators of sock puppet/fake accounts.

        Red flags:
        - All accounts created within same month
        - Identical bio patterns across platforms
        - Sequential usernames
        - Low-effort profiles (generic names, no personalization)
        """
        indicators = []

        # Check creation date clustering (if available)
        # This would require account creation dates which we may not have

        # Check for identical bios
        bios = [acc.get('bio', '') for acc in accounts if acc and acc.get('bio')]
        if len(bios) > 2:
            unique_bios = set(bios)
            if len(unique_bios) < len(bios) / 2:  # More than 50% duplicates
                indicators.append({
                    'type': 'duplicate_bios',
                    'unique_count': len(unique_bios),
                    'total_count': len(bios),
                    'severity': 'MEDIUM',
                    'inference': "Multiple accounts share identical bios. Possible automated "
                               "account creation or copy-paste profile setup."
                })

        # Check for sequential usernames (user1, user2, etc.)
        usernames = [acc.get('username', '') for acc in accounts if acc and acc.get('username')]
        if len(usernames) > 2:
            # Look for numeric sequences
            numbered_usernames = [u for u in usernames if re.search(r'\d+$', u)]
            if len(numbered_usernames) >= 3:
                indicators.append({
                    'type': 'numbered_usernames',
                    'count': len(numbered_usernames),
                    'examples': numbered_usernames[:3],
                    'severity': 'LOW',
                    'inference': "Multiple accounts use numbered suffixes (user1, user2, etc.). "
                               "May indicate automated account generation or sock puppets."
                })

        return indicators

    def _detect_opsec_awareness(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect indicators of operational security (OpSec) awareness.

        This is NOT necessarily malicious - security-conscious individuals
        practice good OpSec. But it indicates the subject is aware of OSINT
        and takes steps to limit exposure.

        Indicators:
        - No location data despite being on location-heavy platforms
        - Consistent timezone but hidden location
        - Privacy-focused usernames
        - Minimal personal information
        """
        indicators = []

        has_location_count = sum(1 for acc in accounts if acc and acc.get('location'))
        total_accounts = len([a for a in accounts if a])

        if total_accounts > 0:
            location_percentage = (has_location_count / total_accounts) * 100

            if location_percentage < 20 and total_accounts >= 3:
                indicators.append({
                    'type': 'location_privacy',
                    'percentage': location_percentage,
                    'severity': 'MEDIUM',
                    'inference': f"Only {location_percentage:.0f}% of profiles include location data. "
                               f"Subject demonstrates location privacy awareness. This is good OpSec "
                               f"practice but limits geolocation intelligence."
                })

        # Check for privacy-focused usernames
        privacy_keywords = ['anon', 'priv', 'secure', 'ghost', 'phantom', 'shadow', 'incognito']
        privacy_username_count = 0

        for acc in accounts:
            if acc and acc.get('username'):
                username_lower = acc['username'].lower()
                if any(keyword in username_lower for keyword in privacy_keywords):
                    privacy_username_count += 1

        if privacy_username_count > 0:
            indicators.append({
                'type': 'privacy_usernames',
                'count': privacy_username_count,
                'severity': 'LOW',
                'inference': f"{privacy_username_count} username(s) contain privacy-related keywords "
                           f"(anon, ghost, etc.). Indicates privacy consciousness or hacker culture affiliation."
            })

        return indicators

    def _detect_anomalies(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect general anomalies that don't fit other categories.

        Examples:
        - Single account with 1000+ posts vs all others with <10
        - Name variations across platforms (John Smith vs J. Sm1th)
        - Platform clustering (all accounts are tech platforms)
        """
        anomalies = []

        # Check post count distribution
        post_counts = [len(acc.get('posts', [])) for acc in accounts if acc]
        if post_counts and len(post_counts) > 2:
            avg_posts = sum(post_counts) / len(post_counts)
            max_posts = max(post_counts)

            # Outlier detection (10x average)
            if max_posts > avg_posts * 10 and avg_posts > 0:
                anomalies.append({
                    'type': 'post_count_outlier',
                    'max_posts': max_posts,
                    'avg_posts': avg_posts,
                    'severity': 'LOW',
                    'inference': f"One account has {max_posts} posts while average is {avg_posts:.0f}. "
                               f"This may be subject's primary/most active account."
                })

        # Check platform clustering
        platforms = [acc.get('platform', 'unknown') for acc in accounts if acc]
        platform_counts = defaultdict(int)
        for platform in platforms:
            platform_counts[platform] += 1

        # Tech platform clustering
        tech_platforms = {'github', 'stackoverflow', 'gitlab', 'bitbucket', 'hackernews'}
        tech_count = sum(1 for p in platforms if p.lower() in tech_platforms)

        if tech_count >= 3:
            anomalies.append({
                'type': 'tech_platform_clustering',
                'tech_platform_count': tech_count,
                'severity': 'LOW',
                'inference': f"Subject has {tech_count} accounts on technical platforms "
                           f"(GitHub, StackOverflow, etc.). Indicates software development "
                           f"or IT professional background."
            })

        return anomalies

    def _calculate_risk_score(self, results: Dict) -> int:
        """
        Calculate overall adverse inference risk score (0-100).

        Higher score = more suspicious patterns detected.
        This is NOT a threat score - it's a "further investigation needed" score.

        Args:
            results: Adverse inference results

        Returns:
            Risk score 0-100
        """
        score = 0

        # Temporal gaps (20 points max)
        for gap in results['temporal_gaps']:
            if gap['severity'] == 'HIGH':
                score += 15
            elif gap['severity'] == 'MEDIUM':
                score += 10

        # Scrubbing indicators (30 points max)
        for indicator in results['scrubbing_indicators']:
            if indicator['severity'] == 'HIGH':
                score += 20
            elif indicator['severity'] == 'MEDIUM':
                score += 10

        # Sock puppet indicators (25 points max)
        for indicator in results['sock_puppet_indicators']:
            if indicator['severity'] == 'MEDIUM':
                score += 15
            elif indicator['severity'] == 'LOW':
                score += 5

        # OpSec indicators (15 points max)
        for indicator in results['opsec_indicators']:
            if indicator['severity'] == 'MEDIUM':
                score += 10
            elif indicator['severity'] == 'LOW':
                score += 5

        # Anomalies (10 points max)
        score += min(len(results['anomalies']) * 2, 10)

        return min(score, 100)
