#!/usr/bin/env python3
"""
Base Transform Class - Foundation for Automated Pivoting

This module defines the abstract interface that all transforms must implement.
Transforms are modular intelligence gathering functions that take a "selector"
(e.g., email, username) and return discovered entities.

Professional OSINT Architecture:
    Input Selector → Transform Execution → Output Entities

Example Flow:
    Email: "john@example.com"
    → EmailTransform
    → Outputs: [Domain("example.com"), BreachRecord("2019-LinkedIn"), Name("John Smith")]

Each output includes:
- Data reliability score (CONFIRMED/PROBABLE/POSSIBLE/UNVERIFIED)
- Source provenance (which API/database provided it)
- Timestamp of discovery
- Confidence percentage
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SelectorType(Enum):
    """Types of selectors that can be pivoted on"""
    EMAIL = "email"
    USERNAME = "username"
    PHONE = "phone"
    DOMAIN = "domain"
    IP_ADDRESS = "ip"
    NAME = "name"
    COMPANY = "company"
    LOCATION = "location"
    URL = "url"
    HASH = "hash"  # File hash, password hash, etc.


class Reliability(Enum):
    """
    Data reliability scoring based on intelligence standards.

    CONFIRMED: Verified by 3+ independent sources or direct observation
    PROBABLE: Verified by 2 sources or single authoritative source
    POSSIBLE: Single source, no contradictions
    UNVERIFIED: Raw data, not yet validated
    """
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    POSSIBLE = "POSSIBLE"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class Selector:
    """
    Represents an input data point for pivoting.

    Attributes:
        type: The type of selector (email, username, etc.)
        value: The actual value (e.g., "john@example.com")
        source: Where this selector came from (e.g., "github_profile")
        context: Additional metadata about discovery
        discovered_at: When this selector was found
    """
    type: SelectorType
    value: str
    source: str = "unknown"
    context: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.type.value}:{self.value}"

    def __hash__(self):
        return hash((self.type, self.value))

    def __eq__(self, other):
        if not isinstance(other, Selector):
            return False
        return self.type == other.type and self.value == other.value


@dataclass
class DiscoveredEntity:
    """
    Represents a discovered piece of intelligence.

    Attributes:
        selector: The new selector discovered
        reliability: Reliability score (CONFIRMED/PROBABLE/POSSIBLE/UNVERIFIED)
        source: Which transform/API discovered this
        confidence: Percentage confidence (0-100)
        metadata: Additional data about this entity
        timestamp: When this was discovered
    """
    selector: Selector
    reliability: Reliability
    source: str
    confidence: int  # 0-100
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'type': self.selector.type.value,
            'value': self.selector.value,
            'reliability': self.reliability.value,
            'source': self.source,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'discovered_from': self.selector.source
        }


@dataclass
class TransformResult:
    """
    Standardized output from a transform execution.

    Attributes:
        transform_name: Name of the transform that ran
        input_selector: What was pivoted on
        discovered_entities: List of new selectors found
        execution_time: How long the transform took (seconds)
        success: Whether the transform completed successfully
        error_message: If failed, what went wrong
        api_calls_made: How many API calls were consumed
        metadata: Additional information about execution
    """
    transform_name: str
    input_selector: Selector
    discovered_entities: List[DiscoveredEntity] = field(default_factory=list)
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    api_calls_made: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self):
        """Return count of discovered entities"""
        return len(self.discovered_entities)

    def get_selectors(self) -> List[Selector]:
        """Extract just the selectors for further pivoting"""
        return [entity.selector for entity in self.discovered_entities]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'transform': self.transform_name,
            'input': str(self.input_selector),
            'discovered_count': len(self.discovered_entities),
            'entities': [e.to_dict() for e in self.discovered_entities],
            'execution_time': self.execution_time,
            'success': self.success,
            'error': self.error_message,
            'api_calls': self.api_calls_made,
            'metadata': self.metadata
        }


class BaseTransform(ABC):
    """
    Abstract base class for all transforms.

    All transforms must implement:
    - can_handle(): Check if this transform applies to a selector type
    - execute(): Run the transform and return discovered entities

    Provides:
    - Rate limiting
    - Error handling
    - Retry logic
    - Execution timing
    - API call tracking
    """

    def __init__(self, api_key: Optional[str] = None, rate_limit: int = 60):
        """
        Initialize transform.

        Args:
            api_key: Optional API key for external services
            rate_limit: Max requests per minute (default: 60)
        """
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()

        # Track statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_api_calls = 0

        logger.info(f"{self.__class__.__name__} initialized (rate_limit={rate_limit}/min)")

    @abstractmethod
    def can_handle(self, selector: Selector) -> bool:
        """
        Check if this transform can process the given selector.

        Args:
            selector: The input selector to check

        Returns:
            True if this transform can handle this selector type
        """
        pass

    @abstractmethod
    def execute(self, selector: Selector) -> TransformResult:
        """
        Execute the transform on the input selector.

        This is the core method that performs the intelligence gathering.
        Must be implemented by each specific transform.

        Args:
            selector: The input data point to pivot on

        Returns:
            TransformResult containing discovered entities
        """
        pass

    def _enforce_rate_limit(self):
        """Enforce rate limiting to avoid API bans"""
        current_time = time.time()

        # Reset counter if we're in a new minute
        if current_time - self.request_window_start > 60:
            self.request_count = 0
            self.request_window_start = current_time

        # If we've hit the limit, wait
        if self.request_count >= self.rate_limit:
            sleep_time = 60 - (current_time - self.request_window_start)
            if sleep_time > 0:
                logger.warning(f"{self.__class__.__name__} rate limit hit, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = time.time()

        self.request_count += 1

    def run(self, selector: Selector, retry_count: int = 3) -> TransformResult:
        """
        Execute transform with error handling, retries, and timing.

        Args:
            selector: Input selector to pivot on
            retry_count: How many times to retry on failure (default: 3)

        Returns:
            TransformResult with discovered entities or error info
        """
        self.total_executions += 1
        start_time = time.time()

        # Check if we can handle this selector
        if not self.can_handle(selector):
            return TransformResult(
                transform_name=self.__class__.__name__,
                input_selector=selector,
                success=False,
                error_message=f"Cannot handle selector type: {selector.type.value}",
                execution_time=time.time() - start_time
            )

        # Execute with retries
        last_exception = None
        for attempt in range(retry_count):
            try:
                # Enforce rate limiting
                self._enforce_rate_limit()

                # Execute the transform
                logger.debug(f"{self.__class__.__name__} executing on {selector}")
                result = self.execute(selector)

                # Record timing
                result.execution_time = time.time() - start_time

                # Update statistics
                if result.success:
                    self.successful_executions += 1
                    self.total_api_calls += result.api_calls_made
                    logger.info(
                        f"{self.__class__.__name__} discovered {len(result)} entities "
                        f"from {selector.value} in {result.execution_time:.2f}s"
                    )
                else:
                    self.failed_executions += 1
                    logger.warning(f"{self.__class__.__name__} failed: {result.error_message}")

                return result

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"{self.__class__.__name__} attempt {attempt + 1}/{retry_count} failed: {e}"
                )

                # Exponential backoff
                if attempt < retry_count - 1:
                    backoff = 2 ** attempt
                    time.sleep(backoff)

        # All retries failed
        self.failed_executions += 1
        return TransformResult(
            transform_name=self.__class__.__name__,
            input_selector=selector,
            success=False,
            error_message=f"Failed after {retry_count} attempts: {last_exception}",
            execution_time=time.time() - start_time
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get transform execution statistics"""
        return {
            'transform': self.__class__.__name__,
            'total_executions': self.total_executions,
            'successful': self.successful_executions,
            'failed': self.failed_executions,
            'success_rate': (self.successful_executions / self.total_executions * 100)
                           if self.total_executions > 0 else 0,
            'total_api_calls': self.total_api_calls,
            'avg_api_calls_per_execution': (self.total_api_calls / self.total_executions)
                                           if self.total_executions > 0 else 0
        }
