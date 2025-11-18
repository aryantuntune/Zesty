"""
Enhanced Scraper with Multiple Fallback Methods
Improves data extraction success rate
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from urllib.parse import urlparse
from .utils import setup_logger
from .scrapers import AccountScraper  # Import existing scraper

logger = setup_logger(__name__)


class EnhancedScraper:
    """
    Multi-method scraper with intelligent fallbacks

    Methods (in order of attempt):
    1. Existing Selenium-based scraper (JavaScript support)
    2. Requests + BeautifulSoup (fast, static content)
    3. Platform-specific extractors
    4. Minimal extraction (at least get something)
    """

    def __init__(self):
        self.base_scraper = AccountScraper()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_with_fallbacks(self, url: str) -> Dict:
        """
        Try multiple scraping methods until one succeeds

        Args:
            url: URL to scrape

        Returns:
            Account data dictionary
        """
        platform = self._detect_platform(url)

        # Method 1: Try existing Selenium scraper first
        try:
            logger.debug(f"Attempting Selenium scrape: {url}")
            data = self.base_scraper.scrape_account(url)
            if self._has_useful_data(data):
                data['scrape_method'] = 'selenium'
                logger.info(f"✅ Selenium scrape successful: {url}")
                return data
        except Exception as e:
            logger.debug(f"Selenium failed for {url}: {e}")

        # Method 2: Try requests + BeautifulSoup (faster, no browser)
        try:
            logger.debug(f"Attempting static HTML scrape: {url}")
            data = self._scrape_with_requests(url, platform)
            if self._has_useful_data(data):
                data['scrape_method'] = 'requests'
                logger.info(f"✅ Static scrape successful: {url}")
                return data
        except Exception as e:
            logger.debug(f"Requests scrape failed for {url}: {e}")

        # Method 3: Platform-specific extraction
        try:
            logger.debug(f"Attempting platform-specific extraction: {url}")
            data = self._platform_specific_scrape(url, platform)
            if self._has_useful_data(data):
                data['scrape_method'] = 'platform_specific'
                logger.info(f"✅ Platform-specific scrape successful: {url}")
                return data
        except Exception as e:
            logger.debug(f"Platform-specific scrape failed for {url}: {e}")

        # Method 4: Minimal extraction (better than nothing)
        logger.warning(f"All scrape methods failed for {url}, returning minimal data")
        return {
            'url': url,
            'platform': platform,
            'name': None,
            'bio': None,
            'location': None,
            'followers': None,
            'scrape_failed': True,
            'scrape_method': 'minimal'
        }

    def _scrape_with_requests(self, url: str, platform: str) -> Dict:
        """
        Scrape using requests + BeautifulSoup (no JavaScript)

        Args:
            url: URL to scrape
            platform: Detected platform

        Returns:
            Extracted data
        """
        response = self.session.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Generic extraction patterns
        data = {
            'url': url,
            'platform': platform,
            'name': None,
            'bio': None,
            'location': None,
            'followers': None,
            'posts': []
        }

        # Try to extract name from common selectors
        name_selectors = [
            'h1.username', 'span.username', 'div.profile-name',
            'h1', 'meta[property="og:title"]', 'title'
        ]
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get('content') if elem.name == 'meta' else elem.get_text(strip=True)
                if name and len(name) < 100:  # Sanity check
                    data['name'] = name
                    break

        # Try to extract bio
        bio_selectors = [
            'div.bio', 'p.bio', 'div.description', 'meta[property="og:description"]',
            'meta[name="description"]'
        ]
        for selector in bio_selectors:
            elem = soup.select_one(selector)
            if elem:
                bio = elem.get('content') if elem.name == 'meta' else elem.get_text(strip=True)
                if bio and len(bio) > 10:  # Sanity check
                    data['bio'] = bio
                    break

        # Try to extract location
        location_selectors = ['span.location', 'div.location', '[itemprop="location"]']
        for selector in location_selectors:
            elem = soup.select_one(selector)
            if elem:
                data['location'] = elem.get_text(strip=True)
                break

        # Try to extract follower count
        follower_selectors = ['span.followers', 'div.follower-count', '[data-followers]']
        for selector in follower_selectors:
            elem = soup.select_one(selector)
            if elem:
                followers_text = elem.get('data-followers') or elem.get_text(strip=True)
                try:
                    data['followers'] = int(followers_text.replace(',', '').replace('K', '000'))
                except:
                    data['followers'] = followers_text
                break

        return data

    def _platform_specific_scrape(self, url: str, platform: str) -> Dict:
        """
        Use platform-specific extraction logic

        Args:
            url: URL to scrape
            platform: Platform name

        Returns:
            Extracted data
        """
        data = {
            'url': url,
            'platform': platform,
            'name': None,
            'bio': None
        }

        # GitHub specific
        if 'github.com' in url:
            username = url.rstrip('/').split('/')[-1]
            # Try GitHub API (public, no auth needed)
            try:
                api_url = f'https://api.github.com/users/{username}'
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    gh_data = response.json()
                    data['name'] = gh_data.get('name') or gh_data.get('login')
                    data['bio'] = gh_data.get('bio')
                    data['location'] = gh_data.get('location')
                    data['followers'] = gh_data.get('followers')
                    data['public_repos'] = gh_data.get('public_repos')
                    return data
            except:
                pass

        # Add more platform-specific extractors here
        # YouTube, Twitter/X, LinkedIn, etc.

        return data

    def _detect_platform(self, url: str) -> str:
        """
        Detect platform from URL

        Args:
            url: URL to analyze

        Returns:
            Platform name
        """
        domain = urlparse(url).netloc.lower()

        platform_map = {
            'github.com': 'github',
            'twitter.com': 'twitter',
            'x.com': 'twitter',
            'facebook.com': 'facebook',
            'instagram.com': 'instagram',
            'linkedin.com': 'linkedin',
            'youtube.com': 'youtube',
            'reddit.com': 'reddit',
            'tiktok.com': 'tiktok',
            'pinterest.com': 'pinterest',
            'mastodon': 'mastodon',
            'disqus.com': 'disqus',
            'pastebin.com': 'pastebin',
            'gumroad.com': 'gumroad',
        }

        for key, value in platform_map.items():
            if key in domain:
                return value

        return 'unknown'

    def _has_useful_data(self, data: Dict) -> bool:
        """
        Check if scraped data has any useful information

        Args:
            data: Scraped data dictionary

        Returns:
            True if data is useful, False otherwise
        """
        if not data:
            return False

        # Must have at least one of these fields
        useful_fields = ['name', 'bio', 'description', 'location', 'followers', 'posts']
        for field in useful_fields:
            value = data.get(field)
            if value:
                # Check if it's not just empty/None
                if isinstance(value, str) and len(value.strip()) > 0:
                    return True
                elif isinstance(value, (list, int)) and value:
                    return True

        return False

    def score_data_quality(self, data: Dict) -> int:
        """
        Score the quality of scraped data (0-100)

        Args:
            data: Scraped data dictionary

        Returns:
            Quality score 0-100
        """
        score = 0

        # Has name
        if data.get('name'):
            score += 20

        # Has bio/description
        if data.get('bio') or data.get('description'):
            bio_text = data.get('bio') or data.get('description')
            score += min(30, len(bio_text) // 10)  # Longer bio = better

        # Has location
        if data.get('location'):
            score += 10

        # Has followers/social metrics
        if data.get('followers') or data.get('friends'):
            score += 15

        # Has posts/content
        posts = data.get('posts', [])
        if posts:
            score += min(25, len(posts) * 5)

        return min(100, score)
