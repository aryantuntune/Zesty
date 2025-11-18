"""
Wayback Machine Integration: Access historical versions of web pages
Retrieve archived snapshots and track profile evolution over time
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .utils import setup_logger

logger = setup_logger(__name__)


class WaybackMachine:
    """
    Interface to Internet Archive's Wayback Machine

    Features:
    - Query available snapshots
    - Retrieve archived pages
    - Compare historical versions
    - Track profile changes over time
    """

    def __init__(self):
        self.api_base = "http://archive.org/wayback/available"
        self.cdx_api = "http://web.archive.org/cdx/search/cdx"
        self.wayback_base = "http://web.archive.org/web"

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def get_available_snapshots(self, url: str, limit: int = 10) -> List[Dict]:
        """
        Get list of available snapshots for a URL

        Args:
            url: URL to query
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshots with timestamps
        """
        logger.info(f"Querying Wayback Machine for: {url}")

        self._rate_limit()

        try:
            # Query CDX API for all snapshots
            params = {
                'url': url,
                'output': 'json',
                'limit': limit,
                'fl': 'timestamp,statuscode,original',
                'filter': 'statuscode:200'  # Only successful captures
            }

            response = requests.get(self.cdx_api, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if not data or len(data) < 2:  # First row is header
                logger.info(f"No snapshots found for {url}")
                return []

            # Parse snapshots (skip header row)
            snapshots = []

            for row in data[1:]:
                timestamp_str = row[0]  # Format: YYYYMMDDhhmmss
                status_code = row[1]
                original_url = row[2]

                # Parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                except:
                    continue

                snapshot = {
                    'timestamp': timestamp,
                    'timestamp_str': timestamp_str,
                    'url': original_url,
                    'archive_url': f"{self.wayback_base}/{timestamp_str}/{original_url}",
                    'status_code': status_code
                }

                snapshots.append(snapshot)

            logger.info(f"Found {len(snapshots)} snapshots for {url}")

            return snapshots

        except requests.RequestException as e:
            logger.error(f"Wayback Machine API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error querying Wayback Machine: {e}")
            return []

    def get_closest_snapshot(self, url: str, target_date: datetime = None) -> Optional[Dict]:
        """
        Get snapshot closest to a target date

        Args:
            url: URL to query
            target_date: Target date (defaults to now)

        Returns:
            Snapshot info or None
        """
        if target_date is None:
            target_date = datetime.now()

        logger.info(f"Finding snapshot closest to {target_date.strftime('%Y-%m-%d')}")

        self._rate_limit()

        try:
            # Format timestamp for API
            timestamp = target_date.strftime('%Y%m%d')

            params = {
                'url': url,
                'timestamp': timestamp
            }

            response = requests.get(self.api_base, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if 'archived_snapshots' not in data:
                logger.info("No snapshots available")
                return None

            if 'closest' not in data['archived_snapshots']:
                logger.info("No closest snapshot found")
                return None

            closest = data['archived_snapshots']['closest']

            if not closest.get('available'):
                return None

            # Parse timestamp
            timestamp_str = closest['timestamp']
            timestamp_dt = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')

            snapshot = {
                'timestamp': timestamp_dt,
                'timestamp_str': timestamp_str,
                'url': closest['url'],
                'archive_url': closest['url'],
                'status_code': closest.get('status', '200')
            }

            logger.info(f"Found snapshot from {timestamp_dt.strftime('%Y-%m-%d')}")

            return snapshot

        except Exception as e:
            logger.error(f"Error finding closest snapshot: {e}")
            return None

    def retrieve_archived_page(self, archive_url: str) -> Optional[str]:
        """
        Retrieve content from archived page

        Args:
            archive_url: Wayback Machine archive URL

        Returns:
            Page HTML or None
        """
        logger.info(f"Retrieving archived page: {archive_url}")

        self._rate_limit()

        try:
            response = requests.get(archive_url, timeout=30)
            response.raise_for_status()

            logger.info("Successfully retrieved archived page")

            return response.text

        except requests.RequestException as e:
            logger.error(f"Failed to retrieve archived page: {e}")
            return None

    def get_historical_profile(self, url: str, months_ago: int = 6) -> List[Dict]:
        """
        Get historical snapshots at regular intervals

        Args:
            url: Profile URL
            months_ago: How many months back to search

        Returns:
            List of snapshots with content
        """
        logger.info(f"Getting historical profile for {url} ({months_ago} months)")

        # Get all available snapshots
        all_snapshots = self.get_available_snapshots(url, limit=100)

        if not all_snapshots:
            return []

        # Filter to one snapshot per month
        cutoff_date = datetime.now() - timedelta(days=months_ago * 30)

        # Group by month
        monthly_snapshots = {}

        for snapshot in all_snapshots:
            if snapshot['timestamp'] < cutoff_date:
                continue

            month_key = snapshot['timestamp'].strftime('%Y-%m')

            if month_key not in monthly_snapshots:
                monthly_snapshots[month_key] = snapshot

        # Sort by date
        selected_snapshots = sorted(
            monthly_snapshots.values(),
            key=lambda x: x['timestamp']
        )

        logger.info(f"Selected {len(selected_snapshots)} monthly snapshots")

        return selected_snapshots

    def compare_snapshots(
        self,
        snapshot1: Dict,
        snapshot2: Dict,
        extractor_func = None
    ) -> Dict:
        """
        Compare two snapshots to detect changes

        Args:
            snapshot1: Older snapshot
            snapshot2: Newer snapshot
            extractor_func: Function to extract data from HTML
                Signature: func(html: str) -> Dict

        Returns:
            {
                'changes_detected': bool,
                'changes': List[str],
                'old_data': Dict,
                'new_data': Dict
            }
        """
        logger.info("Comparing snapshots")

        # Retrieve both pages
        html1 = self.retrieve_archived_page(snapshot1['archive_url'])
        html2 = self.retrieve_archived_page(snapshot2['archive_url'])

        if not html1 or not html2:
            return {
                'changes_detected': False,
                'changes': [],
                'old_data': {},
                'new_data': {},
                'error': 'Failed to retrieve one or both snapshots'
            }

        # Extract data if extractor provided
        if extractor_func:
            try:
                data1 = extractor_func(html1)
                data2 = extractor_func(html2)
            except Exception as e:
                logger.error(f"Data extraction failed: {e}")
                return {
                    'changes_detected': False,
                    'changes': [],
                    'old_data': {},
                    'new_data': {},
                    'error': f'Extraction error: {e}'
                }
        else:
            # Simple comparison
            data1 = {'content': html1}
            data2 = {'content': html2}

        # Detect changes
        changes = []

        for key in data1.keys():
            if key in data2:
                if data1[key] != data2[key]:
                    changes.append(f"{key} changed")

        # Check for new fields
        for key in data2.keys():
            if key not in data1:
                changes.append(f"{key} added")

        result = {
            'changes_detected': len(changes) > 0,
            'changes': changes,
            'old_data': data1,
            'new_data': data2,
            'time_diff_days': (snapshot2['timestamp'] - snapshot1['timestamp']).days
        }

        logger.info(f"Comparison complete: {len(changes)} changes detected")

        return result

    def track_profile_evolution(
        self,
        url: str,
        extractor_func = None,
        months: int = 12
    ) -> List[Dict]:
        """
        Track how a profile has evolved over time

        Args:
            url: Profile URL
            extractor_func: Function to extract profile data
            months: Number of months to analyze

        Returns:
            List of {timestamp, data, changes_from_previous}
        """
        logger.info(f"Tracking profile evolution: {url}")

        # Get historical snapshots
        snapshots = self.get_historical_profile(url, months_ago=months)

        if len(snapshots) < 2:
            logger.info("Not enough snapshots to track evolution")
            return []

        evolution = []

        for i, snapshot in enumerate(snapshots):
            # Retrieve and extract data
            html = self.retrieve_archived_page(snapshot['archive_url'])

            if not html:
                continue

            if extractor_func:
                try:
                    data = extractor_func(html)
                except Exception as e:
                    logger.error(f"Extraction failed for snapshot {i}: {e}")
                    continue
            else:
                data = {'raw_html_length': len(html)}

            # Compare with previous
            changes = []
            if i > 0 and evolution:
                prev_data = evolution[-1]['data']

                for key in data.keys():
                    if key in prev_data:
                        if data[key] != prev_data[key]:
                            changes.append(key)

            evolution.append({
                'timestamp': snapshot['timestamp'],
                'archive_url': snapshot['archive_url'],
                'data': data,
                'changes_from_previous': changes
            })

        logger.info(f"Tracked {len(evolution)} points in profile evolution")

        return evolution


# Convenience function
def get_wayback_machine() -> WaybackMachine:
    """Get Wayback Machine instance"""
    return WaybackMachine()
