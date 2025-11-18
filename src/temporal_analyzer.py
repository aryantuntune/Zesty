"""
Temporal Activity Analyzer: Timezone detection and activity pattern analysis
Identifies when users are most active to fingerprint behavior
"""

from datetime import datetime, timezone
from typing import List, Dict, Tuple, Set
from collections import Counter, defaultdict
import re
import statistics
from .utils import setup_logger

logger = setup_logger(__name__)


class TemporalAnalyzer:
    """
    Analyzes temporal patterns in user activity
    - Detects likely timezone based on posting times
    - Identifies peak activity hours
    - Finds active days of the week
    - Measures posting consistency
    """

    def __init__(self):
        self.timezone_map = {
            'PST': -8, 'PDT': -7,
            'MST': -7, 'MDT': -6,
            'CST': -6, 'CDT': -5,
            'EST': -5, 'EDT': -4,
            'GMT': 0, 'UTC': 0,
            'BST': 1, 'CET': 1,
            'IST': 5.5, 'JST': 9,
            'AEST': 10, 'AEDT': 11
        }

    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse various timestamp formats

        Supports:
        - ISO 8601: 2024-01-15T14:30:00Z
        - Human readable: Jan 15, 2024 at 2:30 PM
        - Relative: 2h ago, 3d ago
        - Unix timestamp: 1705329000
        """
        if not timestamp_str:
            return None

        timestamp_str = timestamp_str.strip()

        try:
            # ISO 8601
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

            # Unix timestamp
            if timestamp_str.isdigit():
                return datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)

            # Relative times (2h ago, 3d ago, etc.)
            relative_match = re.match(r'(\d+)\s*([smhd])\s*ago', timestamp_str, re.IGNORECASE)
            if relative_match:
                value, unit = relative_match.groups()
                value = int(value)

                now = datetime.now(timezone.utc)

                if unit.lower() == 's':
                    return now.replace(second=now.second - value)
                elif unit.lower() == 'm':
                    return now.replace(minute=now.minute - value)
                elif unit.lower() == 'h':
                    return now.replace(hour=now.hour - value)
                elif unit.lower() == 'd':
                    return now.replace(day=now.day - value)

            # Common date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%b %d, %Y at %I:%M %p', '%d %b %Y %H:%M']:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue

        except Exception as e:
            logger.debug(f"Failed to parse timestamp '{timestamp_str}': {e}")

        return None

    def extract_timestamps(self, content: Dict) -> List[datetime]:
        """
        Extract all timestamps from scraped content

        Looks for:
        - Tweet timestamps
        - Post timestamps
        - Comment timestamps
        - Last updated times
        """
        timestamps = []

        # Check common fields (added 'updated_at' and 'published' for our new scraper)
        fields_to_check = ['created_at', 'posted_at', 'timestamp', 'date', 'published_at', 'updated_at', 'published']

        for field in fields_to_check:
            if field in content:
                ts = self.parse_timestamp(str(content[field]))
                if ts:
                    timestamps.append(ts)

        # Check for lists of posts/tweets
        if 'posts' in content and isinstance(content['posts'], list):
            for post in content['posts']:
                if isinstance(post, dict):
                    for field in fields_to_check:
                        if field in post:
                            ts = self.parse_timestamp(str(post[field]))
                            if ts:
                                timestamps.append(ts)

        if 'tweets' in content and isinstance(content['tweets'], list):
            for tweet in content['tweets']:
                if isinstance(tweet, dict):
                    for field in fields_to_check:
                        if field in tweet:
                            ts = self.parse_timestamp(str(tweet[field]))
                            if ts:
                                timestamps.append(ts)

        return timestamps

    def detect_timezone(self, timestamps: List[datetime]) -> Tuple[str, float]:
        """
        Detect likely timezone based on activity patterns

        Returns:
            (timezone_name, confidence_score)
        """
        if not timestamps or len(timestamps) < 5:
            return ('Unknown', 0.0)

        # Extract hours (assuming UTC initially)
        hours = [ts.hour for ts in timestamps if ts]

        if not hours:
            return ('Unknown', 0.0)

        # Find peak hour
        hour_counts = Counter(hours)
        peak_hour = hour_counts.most_common(1)[0][0]

        # Common activity patterns by timezone
        # People usually post during: 9-12 AM, 6-11 PM
        timezone_hypotheses = {
            'PST/PDT': (9, 12, 18, 23),  # California
            'EST/EDT': (9, 12, 18, 23),  # New York
            'GMT/UTC': (9, 12, 18, 23),  # London
            'IST': (9, 12, 18, 23),      # India
            'JST': (9, 12, 18, 23),      # Japan
        }

        # Calculate offset that best fits the data
        # Assuming people are most active 9 AM - 11 PM local time
        avg_hour = statistics.mean(hours)

        # If average is around 12-14 UTC, likely EST/PST users posting in evening
        # If average is around 6-8 UTC, likely Asian timezone users

        if 18 <= avg_hour <= 23 or 0 <= avg_hour <= 2:
            # Late night UTC = daytime US
            timezone = 'EST/EDT (UTC-5/-4)'
            confidence = 0.7
        elif 6 <= avg_hour <= 14:
            # Morning/afternoon UTC = evening Asia
            timezone = 'IST (UTC+5:30)'
            confidence = 0.7
        elif 15 <= avg_hour <= 17:
            # Afternoon UTC = morning US
            timezone = 'PST/PDT (UTC-8/-7)'
            confidence = 0.7
        else:
            timezone = 'GMT/UTC (UTC+0)'
            confidence = 0.5

        # Increase confidence if there's a clear peak
        if hour_counts.most_common(1)[0][1] > len(hours) * 0.3:
            confidence += 0.2

        confidence = min(confidence, 1.0)

        return (timezone, confidence)

    def get_peak_hours(self, timestamps: List[datetime]) -> List[int]:
        """
        Get top 3 most active hours

        Returns:
            List of hours (0-23)
        """
        if not timestamps:
            return []

        hours = [ts.hour for ts in timestamps if ts]
        hour_counts = Counter(hours)

        # Top 3 hours
        peak_hours = [hour for hour, count in hour_counts.most_common(3)]

        return peak_hours

    def get_active_days(self, timestamps: List[datetime]) -> List[str]:
        """
        Get most active days of the week

        Returns:
            List of day names
        """
        if not timestamps:
            return []

        days = [ts.strftime('%A') for ts in timestamps if ts]
        day_counts = Counter(days)

        # Days with above-average activity
        avg_activity = sum(day_counts.values()) / len(day_counts) if day_counts else 0

        active_days = [day for day, count in day_counts.items() if count >= avg_activity]

        return active_days

    def calculate_posting_frequency(self, timestamps: List[datetime]) -> Dict:
        """
        Calculate posting frequency metrics

        Returns:
            {
                'total_posts': int,
                'avg_posts_per_day': float,
                'posting_pattern': str  # 'frequent', 'moderate', 'sporadic'
            }
        """
        if not timestamps or len(timestamps) < 2:
            return {
                'total_posts': len(timestamps),
                'avg_posts_per_day': 0,
                'posting_pattern': 'unknown'
            }

        # Sort timestamps
        sorted_ts = sorted([ts for ts in timestamps if ts])

        # Calculate time span
        time_span = sorted_ts[-1] - sorted_ts[0]
        days = max(time_span.days, 1)

        avg_per_day = len(sorted_ts) / days

        # Classify pattern
        if avg_per_day > 5:
            pattern = 'frequent'
        elif avg_per_day > 1:
            pattern = 'moderate'
        else:
            pattern = 'sporadic'

        return {
            'total_posts': len(sorted_ts),
            'avg_posts_per_day': round(avg_per_day, 2),
            'posting_pattern': pattern,
            'time_span_days': days
        }

    def analyze_activity_consistency(self, timestamps: List[datetime]) -> Dict:
        """
        Measure how consistent posting behavior is

        Returns:
            {
                'consistency_score': float,  # 0-1
                'has_routine': bool,
                'gaps': List[int]  # Days with no activity
            }
        """
        if not timestamps or len(timestamps) < 3:
            return {
                'consistency_score': 0.0,
                'has_routine': False,
                'gaps': []
            }

        sorted_ts = sorted([ts for ts in timestamps if ts])

        # Calculate gaps between posts (in hours)
        gaps = []
        for i in range(1, len(sorted_ts)):
            gap = (sorted_ts[i] - sorted_ts[i-1]).total_seconds() / 3600
            gaps.append(gap)

        # Calculate standard deviation of gaps
        if len(gaps) > 1:
            std_dev = statistics.stdev(gaps)
            mean_gap = statistics.mean(gaps)

            # Lower coefficient of variation = more consistent
            cv = std_dev / mean_gap if mean_gap > 0 else float('inf')

            # Convert to 0-1 score (lower cv = higher consistency)
            consistency_score = max(0, 1 - (cv / 10))

            # Has routine if posts are regular (cv < 2)
            has_routine = cv < 2.0
        else:
            consistency_score = 0.0
            has_routine = False

        # Find gaps > 24 hours
        long_gaps = [int(gap / 24) for gap in gaps if gap > 24]

        return {
            'consistency_score': round(consistency_score, 2),
            'has_routine': has_routine,
            'gaps_over_24h': long_gaps[:10]  # Top 10 longest gaps
        }

    def build_activity_profile(self, scraped_data: Dict) -> Dict:
        """
        Build complete temporal activity profile

        Args:
            scraped_data: Data from platform scraper

        Returns:
            Complete activity analysis
        """
        timestamps = self.extract_timestamps(scraped_data)

        if not timestamps:
            logger.info("No timestamps found in scraped data")
            return {
                'has_temporal_data': False,
                'reason': 'No timestamps found'
            }

        # Perform all analyses
        timezone, tz_confidence = self.detect_timezone(timestamps)
        peak_hours = self.get_peak_hours(timestamps)
        active_days = self.get_active_days(timestamps)
        frequency = self.calculate_posting_frequency(timestamps)
        consistency = self.analyze_activity_consistency(timestamps)

        profile = {
            'has_temporal_data': True,
            'sample_size': len(timestamps),
            'timezone': {
                'detected': timezone,
                'confidence': tz_confidence
            },
            'peak_hours': peak_hours,
            'active_days': active_days,
            'frequency': frequency,
            'consistency': consistency,
            'analysis_timestamp': datetime.now().isoformat()
        }

        logger.info(f"Built temporal profile: {timezone}, {len(timestamps)} timestamps")

        return profile

    def compare_temporal_profiles(self, profile1: Dict, profile2: Dict) -> Tuple[float, List[str]]:
        """
        Compare two temporal profiles for similarity

        Returns:
            (similarity_score, match_reasons)
            Score: 0-100
        """
        score = 0
        reasons = []

        if not profile1.get('has_temporal_data') or not profile2.get('has_temporal_data'):
            return (0, ['Insufficient temporal data'])

        # Timezone match (20 points)
        if profile1['timezone']['detected'] == profile2['timezone']['detected']:
            score += 20
            reasons.append(f"Same timezone ({profile1['timezone']['detected']})")

        # Peak hours overlap (25 points)
        peak1 = set(profile1.get('peak_hours', []))
        peak2 = set(profile2.get('peak_hours', []))

        if peak1 and peak2:
            overlap = len(peak1.intersection(peak2))
            peak_score = (overlap / 3) * 25  # Max 3 peak hours
            score += peak_score

            if overlap > 0:
                reasons.append(f"{overlap} matching peak hours")

        # Active days overlap (15 points)
        days1 = set(profile1.get('active_days', []))
        days2 = set(profile2.get('active_days', []))

        if days1 and days2:
            day_overlap = len(days1.intersection(days2))
            day_score = (day_overlap / 7) * 15
            score += day_score

            if day_overlap > 3:
                reasons.append(f"{day_overlap} matching active days")

        # Posting pattern match (20 points)
        pattern1 = profile1.get('frequency', {}).get('posting_pattern')
        pattern2 = profile2.get('frequency', {}).get('posting_pattern')

        if pattern1 == pattern2:
            score += 20
            reasons.append(f"Same posting pattern ({pattern1})")

        # Consistency similarity (20 points)
        cons1 = profile1.get('consistency', {}).get('consistency_score', 0)
        cons2 = profile2.get('consistency', {}).get('consistency_score', 0)

        if cons1 and cons2:
            cons_diff = abs(cons1 - cons2)
            cons_score = max(0, 20 - (cons_diff * 20))
            score += cons_score

            if cons_diff < 0.2:
                reasons.append("Similar posting consistency")

        return (round(score, 1), reasons)


# Convenience function
def get_temporal_analyzer() -> TemporalAnalyzer:
    """Get temporal analyzer instance"""
    return TemporalAnalyzer()
