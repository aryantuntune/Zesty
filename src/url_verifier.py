"""
URL Verification Module
Verifies that URLs actually exist before processing them
Reduces false positives from Sherlock reconnaissance
"""

import requests
from typing import Dict, List, Optional
from urllib.parse import urlparse
import time

try:
    from .utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class URLVerifier:
    """
    Verifies URLs to filter false positives

    Features:
    - HTTP HEAD/GET requests to check if URL exists
    - Handles redirects properly
    - Respects rate limits
    - Caches results to avoid duplicate checks
    """

    def __init__(self, timeout: int = 10, rate_limit: float = 0.5):
        """
        Initialize URL verifier

        Args:
            timeout: Request timeout in seconds
            rate_limit: Delay between requests in seconds (to avoid rate limiting)
        """
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.verified_cache = {}  # Cache to avoid duplicate checks

        try:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    def verify_url(self, url: str) -> Dict:
        """
        Verify if URL exists and is accessible

        Args:
            url: URL to verify

        Returns:
            {
                'exists': bool,
                'status_code': int,
                'accessible': bool,
                'redirect_url': str (if redirected)
            }
        """
        # Check cache first
        if url in self.verified_cache:
            return self.verified_cache[url]

        result = {
            'exists': False,
            'status_code': None,
            'accessible': False,
            'redirect_url': None
        }

        try:
            # Try HEAD request first (faster, doesn't download content)
            response = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )

            result['status_code'] = response.status_code

            # Check if URL was redirected
            if response.url != url:
                result['redirect_url'] = response.url

            # Determine if account exists based on status code
            if response.status_code == 200:
                # Perfect! Account exists and is accessible
                result['exists'] = True
                result['accessible'] = True

            elif response.status_code in [401, 403]:
                # Account exists but requires auth or is private
                result['exists'] = True
                result['accessible'] = False

            elif response.status_code in [404, 410]:
                # Account definitely doesn't exist
                result['exists'] = False
                result['accessible'] = False

            elif response.status_code == 405:
                # HEAD not allowed, try GET
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                result['status_code'] = response.status_code
                result['exists'] = response.status_code not in [404, 410]
                result['accessible'] = response.status_code == 200

            else:
                # Other codes (500, 503, etc.) - assume exists but might be temp issue
                result['exists'] = True
                result['accessible'] = False

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout verifying {url}")
            # Timeout doesn't mean doesn't exist, might be slow server
            result['exists'] = True
            result['accessible'] = False

        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error for {url}")
            # Connection error might mean server down, not that account doesn't exist
            result['exists'] = True
            result['accessible'] = False

        except Exception as e:
            logger.debug(f"Error verifying {url}: {e}")
            # On unknown error, assume exists to avoid false negatives
            result['exists'] = True
            result['accessible'] = False

        # Cache the result
        self.verified_cache[url] = result

        return result

    def batch_verify(self, urls: List[str], show_progress: bool = True) -> Dict[str, Dict]:
        """
        Verify multiple URLs with rate limiting

        Args:
            urls: List of URLs to verify
            show_progress: Print progress updates

        Returns:
            Dictionary mapping URL -> verification result
        """
        if not urls:
            logger.warning("No URLs provided for verification")
            return {}

        results = {}
        total = len(urls)

        for i, url in enumerate(urls, 1):
            if not url or not isinstance(url, str):
                logger.warning(f"Invalid URL at index {i}: {url}")
                continue

            if show_progress and i % 10 == 0:
                logger.info(f"Verified {i}/{total} URLs...")

            results[url] = self.verify_url(url)

            # Rate limiting to avoid being blocked
            if i < total:  # Don't delay after last URL
                time.sleep(self.rate_limit)

        if show_progress:
            exists_count = sum(1 for r in results.values() if r.get('exists', False))
            logger.info(f"Verification complete: {exists_count}/{total} URLs exist")

        return results

    def filter_existing_urls(self, urls: List[str]) -> List[str]:
        """
        Filter list to only URLs that exist

        Args:
            urls: List of URLs to filter

        Returns:
            List of URLs that exist
        """
        if not urls:
            return []

        try:
            results = self.batch_verify(urls, show_progress=False)
            existing = [url for url, result in results.items() if result.get('exists', False)]
            logger.info(f"Filtered {len(urls)} URLs down to {len(existing)} existing URLs")
            return existing
        except Exception as e:
            logger.error(f"Error filtering URLs: {e}")
            # Return original list if verification fails (don't lose data)
            return urls

    def get_verification_stats(self) -> Dict:
        """
        Get statistics about verified URLs

        Returns:
            Statistics dictionary
        """
        total = len(self.verified_cache)
        exists = sum(1 for r in self.verified_cache.values() if r['exists'])
        accessible = sum(1 for r in self.verified_cache.values() if r['accessible'])
        not_found = sum(1 for r in self.verified_cache.values() if r['status_code'] in [404, 410])

        return {
            'total_verified': total,
            'exists': exists,
            'accessible': accessible,
            'not_found': not_found,
            'false_positive_rate': (not_found / total * 100) if total > 0 else 0
        }
