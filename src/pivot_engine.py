#!/usr/bin/env python3
"""
Pivot Engine - Automated Intelligence Pivoting Orchestration

This module orchestrates automated pivoting across all transform modules.
It takes initial selectors (email, username, etc.) and recursively discovers
related intelligence by chaining transforms.

Architecture:
    Initial Selector (Email)
    → EmailTransform
    → Discovers: Domain, Name, Breach Records
    → DomainTransform on Domain
    → Discovers: IP Address, WHOIS Data
    → IPTransform on IP
    → Discovers: Geolocation, ASN
    (and so on...)

Professional OSINT Workflow:
1. Breadth-First Pivoting: Discover all immediate connections before going deeper
2. Depth Limiting: Prevent infinite loops (max 3-5 hops)
3. Selector Deduplication: Don't process the same selector twice
4. Provenance Tracking: Record full chain of discovery
5. Reliability Scoring: Prioritize high-confidence pivots

Configuration:
- max_depth: How many hops to pivot (default: 3)
- max_selectors: Maximum total selectors to process (default: 100)
- parallel_execution: Run transforms in parallel (default: True)
- reliability_threshold: Minimum reliability to pivot on (default: POSSIBLE)
"""

import time
from typing import List, Dict, Set, Optional, Tuple
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime

from .transforms.base_transform import (
    BaseTransform,
    Selector,
    SelectorType,
    DiscoveredEntity,
    TransformResult,
    Reliability
)
from .transforms.email_transform import EmailTransform
from .transforms.username_transform import UsernameTransform
from .transforms.domain_transform import DomainTransform
from .transforms.phone_transform import PhoneTransform
from .transforms.ip_transform import IPTransform
from .utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class PivotChain:
    """
    Represents a complete pivot chain from initial selector to final discovery.

    Example: Email → Domain → IP → Geolocation
    """
    selectors: List[Selector] = field(default_factory=list)
    depth: int = 0

    def __str__(self):
        chain = " → ".join([f"{s.type.value}:{s.value[:20]}" for s in self.selectors])
        return f"[Depth {self.depth}] {chain}"


@dataclass
class PivotResult:
    """
    Complete result of pivot engine execution.

    Contains:
    - All discovered entities
    - Execution statistics
    - Pivot chains (provenance)
    - Transform results
    """
    initial_selectors: List[Selector]
    discovered_entities: List[DiscoveredEntity] = field(default_factory=list)
    transform_results: List[TransformResult] = field(default_factory=list)
    pivot_chains: List[PivotChain] = field(default_factory=list)

    # Statistics
    total_selectors_processed: int = 0
    total_api_calls: int = 0
    execution_time: float = 0.0
    max_depth_reached: int = 0

    # Breakdown by transform
    transform_stats: Dict[str, Dict] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting"""
        return {
            'initial_selectors': [str(s) for s in self.initial_selectors],
            'total_discoveries': len(self.discovered_entities),
            'total_selectors_processed': self.total_selectors_processed,
            'total_api_calls': self.total_api_calls,
            'execution_time': self.execution_time,
            'max_depth_reached': self.max_depth_reached,
            'transform_stats': self.transform_stats,
            'pivot_chains': [str(chain) for chain in self.pivot_chains[:10]],  # Top 10
            'entities_by_type': self._count_by_type(),
            'entities_by_reliability': self._count_by_reliability()
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count discovered entities by type"""
        counts = defaultdict(int)
        for entity in self.discovered_entities:
            counts[entity.selector.type.value] += 1
        return dict(counts)

    def _count_by_reliability(self) -> Dict[str, int]:
        """Count discovered entities by reliability"""
        counts = defaultdict(int)
        for entity in self.discovered_entities:
            counts[entity.reliability.value] += 1
        return dict(counts)


class PivotEngine:
    """
    Orchestrates automated pivoting across all transforms.

    Professional OSINT Features:
    - Breadth-first search for complete coverage
    - Depth limiting to prevent runaway pivots
    - Deduplication to avoid redundant work
    - Reliability filtering for quality control
    - Parallel execution for performance
    - Provenance tracking for attribution
    """

    def __init__(self,
                 max_depth: int = 3,
                 max_selectors: int = 100,
                 parallel_execution: bool = True,
                 max_workers: int = 5,
                 reliability_threshold: Reliability = Reliability.POSSIBLE,
                 api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize pivot engine.

        Args:
            max_depth: Maximum pivot depth (hops)
            max_selectors: Maximum total selectors to process
            parallel_execution: Run transforms in parallel
            max_workers: Thread pool size for parallel execution
            reliability_threshold: Minimum reliability to pivot on
            api_keys: Dictionary of API keys for transforms
        """
        self.max_depth = max_depth
        self.max_selectors = max_selectors
        self.parallel_execution = parallel_execution
        self.max_workers = max_workers
        self.reliability_threshold = reliability_threshold

        # Initialize transforms
        api_keys = api_keys or {}
        self.transforms: List[BaseTransform] = [
            EmailTransform(
                hibp_api_key=api_keys.get('HIBP_API_KEY'),
                hunter_api_key=api_keys.get('HUNTER_API_KEY')
            ),
            UsernameTransform(),
            DomainTransform(
                securitytrails_api_key=api_keys.get('SECURITYTRAILS_API_KEY'),
                shodan_api_key=api_keys.get('SHODAN_API_KEY'),
                whoisxml_api_key=api_keys.get('WHOISXML_API_KEY')
            ),
            PhoneTransform(
                numverify_api_key=api_keys.get('NUMVERIFY_API_KEY')
            ),
            IPTransform(
                shodan_api_key=api_keys.get('SHODAN_API_KEY'),
                ipinfo_token=api_keys.get('IPINFO_TOKEN'),
                abuseipdb_api_key=api_keys.get('ABUSEIPDB_API_KEY')
            )
        ]

        # Track processed selectors to avoid loops
        self.processed_selectors: Set[Selector] = set()

        # Track pivot chains for provenance
        self.pivot_chains: List[PivotChain] = []

        logger.info(
            f"PivotEngine initialized: max_depth={max_depth}, max_selectors={max_selectors}, "
            f"transforms={len(self.transforms)}, parallel={'ON' if parallel_execution else 'OFF'}"
        )

    def pivot(self, initial_selectors: List[Selector]) -> PivotResult:
        """
        Execute automated pivoting starting from initial selectors.

        Algorithm:
        1. Initialize queue with initial selectors at depth 0
        2. While queue not empty and limits not reached:
           a. Dequeue next selector
           b. Find applicable transforms
           c. Execute transforms (parallel or sequential)
           d. Collect discovered entities
           e. Enqueue new selectors at depth+1
        3. Return aggregated results

        Args:
            initial_selectors: List of starting selectors

        Returns:
            PivotResult with all discoveries and statistics
        """
        start_time = time.time()

        # Initialize result
        result = PivotResult(initial_selectors=initial_selectors)

        # Initialize queue with initial selectors at depth 0
        # Queue items: (selector, depth, parent_chain)
        queue: deque = deque()
        for selector in initial_selectors:
            queue.append((selector, 0, PivotChain(selectors=[selector], depth=0)))

        logger.info(f"Starting pivot on {len(initial_selectors)} initial selectors")

        # Process queue
        while queue and result.total_selectors_processed < self.max_selectors:
            # Dequeue next selector
            selector, depth, chain = queue.popleft()

            # Skip if already processed
            if selector in self.processed_selectors:
                logger.debug(f"Skipping already processed selector: {selector}")
                continue

            # Skip if max depth reached
            if depth > self.max_depth:
                logger.debug(f"Max depth reached for: {selector}")
                continue

            # Mark as processed
            self.processed_selectors.add(selector)
            result.total_selectors_processed += 1

            logger.info(f"Processing [{result.total_selectors_processed}/{self.max_selectors}] "
                       f"depth={depth}: {selector}")

            # Find applicable transforms
            applicable_transforms = [t for t in self.transforms if t.can_handle(selector)]

            if not applicable_transforms:
                logger.debug(f"No transforms available for {selector.type}")
                continue

            # Execute transforms
            transform_results = self._execute_transforms(applicable_transforms, selector)
            result.transform_results.extend(transform_results)

            # Process results
            for transform_result in transform_results:
                # Update statistics
                result.total_api_calls += transform_result.api_calls_made

                # Track transform stats
                transform_name = transform_result.transform_name
                if transform_name not in result.transform_stats:
                    result.transform_stats[transform_name] = {
                        'executions': 0,
                        'discoveries': 0,
                        'api_calls': 0,
                        'avg_execution_time': 0
                    }

                stats = result.transform_stats[transform_name]
                stats['executions'] += 1
                stats['discoveries'] += len(transform_result.discovered_entities)
                stats['api_calls'] += transform_result.api_calls_made
                stats['avg_execution_time'] = (
                    (stats['avg_execution_time'] * (stats['executions'] - 1) +
                     transform_result.execution_time) / stats['executions']
                )

                # Process discovered entities
                for entity in transform_result.discovered_entities:
                    # Add to results
                    result.discovered_entities.append(entity)

                    # Create new pivot chain
                    new_chain = PivotChain(
                        selectors=chain.selectors + [entity.selector],
                        depth=depth + 1
                    )
                    result.pivot_chains.append(new_chain)

                    # Enqueue if meets reliability threshold and not at max depth
                    if (entity.reliability.value >= self.reliability_threshold.value and
                        depth < self.max_depth):
                        queue.append((entity.selector, depth + 1, new_chain))
                        logger.debug(f"Enqueued for pivoting: {entity.selector}")

            # Update max depth reached
            result.max_depth_reached = max(result.max_depth_reached, depth)

        # Finalize results
        result.execution_time = time.time() - start_time

        logger.info(
            f"Pivot complete: {result.total_selectors_processed} selectors processed, "
            f"{len(result.discovered_entities)} entities discovered, "
            f"{result.total_api_calls} API calls, "
            f"{result.execution_time:.2f}s"
        )

        return result

    def _execute_transforms(self, transforms: List[BaseTransform],
                           selector: Selector) -> List[TransformResult]:
        """
        Execute transforms on selector (parallel or sequential).

        Args:
            transforms: List of transforms to execute
            selector: Selector to pivot on

        Returns:
            List of transform results
        """
        if self.parallel_execution and len(transforms) > 1:
            return self._execute_parallel(transforms, selector)
        else:
            return self._execute_sequential(transforms, selector)

    def _execute_sequential(self, transforms: List[BaseTransform],
                           selector: Selector) -> List[TransformResult]:
        """Execute transforms sequentially"""
        results = []
        for transform in transforms:
            try:
                result = transform.run(selector)
                results.append(result)
            except Exception as e:
                logger.error(f"Transform {transform.__class__.__name__} failed: {e}")
        return results

    def _execute_parallel(self, transforms: List[BaseTransform],
                         selector: Selector) -> List[TransformResult]:
        """Execute transforms in parallel using thread pool"""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all transform tasks
            future_to_transform = {
                executor.submit(transform.run, selector): transform
                for transform in transforms
            }

            # Collect results as they complete
            for future in as_completed(future_to_transform):
                transform = future_to_transform[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Transform {transform.__class__.__name__} failed: {e}")

        return results

    def get_statistics(self) -> Dict[str, any]:
        """Get pivot engine statistics"""
        transform_stats = {}
        for transform in self.transforms:
            transform_stats[transform.__class__.__name__] = transform.get_statistics()

        return {
            'total_selectors_processed': len(self.processed_selectors),
            'transform_statistics': transform_stats,
            'configuration': {
                'max_depth': self.max_depth,
                'max_selectors': self.max_selectors,
                'parallel_execution': self.parallel_execution,
                'reliability_threshold': self.reliability_threshold.value
            }
        }
