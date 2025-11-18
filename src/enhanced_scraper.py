"""
Enhanced Scraper with Multiple Fallback Methods
Improves data extraction success rate with post/content extraction
"""

import requests
import re
from typing import Dict, Optional, List
from urllib.parse import urlparse
from datetime import datetime

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Try to import existing scraper
try:
    from .scrapers import AccountScraper
    BASE_SCRAPER_AVAILABLE = True
except (ImportError, AttributeError):
    BASE_SCRAPER_AVAILABLE = False

# Try to import logger
try:
    from .utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


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
        """Initialize enhanced scraper with fallback support"""
        # Try to initialize base scraper if available
        if BASE_SCRAPER_AVAILABLE:
            try:
                self.base_scraper = AccountScraper()
                logger.info("Base Selenium scraper initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize base scraper: {e}")
                self.base_scraper = None
        else:
            self.base_scraper = None
            logger.info("Base scraper not available, using fallback methods only")

        # Initialize requests session
        try:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            self.session = None

    def scrape_with_fallbacks(self, url: str) -> Dict:
        """
        Try multiple scraping methods until one succeeds

        Args:
            url: URL to scrape

        Returns:
            Account data dictionary
        """
        platform = self._detect_platform(url)

        # Method 1: Try existing Selenium scraper first (if available)
        if self.base_scraper:
            try:
                logger.debug(f"Attempting Selenium scrape: {url}")
                data = self.base_scraper.scrape_account(url)
                if self._has_useful_data(data):
                    data['scrape_method'] = 'selenium'
                    data['quality_score'] = self.score_data_quality(data)
                    logger.info(f"Selenium scrape successful: {url} (quality: {data['quality_score']})")
                    return data
            except Exception as e:
                logger.debug(f"Selenium failed for {url}: {e}")
        else:
            logger.debug(f"Selenium scraper not available for {url}")

        # Method 2: Try requests + BeautifulSoup (faster, no browser)
        try:
            logger.debug(f"Attempting static HTML scrape: {url}")
            data = self._scrape_with_requests(url, platform)
            if self._has_useful_data(data):
                data['scrape_method'] = 'requests'
                data['quality_score'] = self.score_data_quality(data)
                logger.info(f"Static scrape successful: {url} (quality: {data['quality_score']})")
                return data
        except Exception as e:
            logger.debug(f"Requests scrape failed for {url}: {e}")

        # Method 3: Platform-specific extraction
        try:
            logger.debug(f"Attempting platform-specific extraction: {url}")
            data = self._platform_specific_scrape(url, platform)
            if self._has_useful_data(data):
                data['scrape_method'] = 'platform_specific'
                data['quality_score'] = self.score_data_quality(data)
                logger.info(f"Platform-specific scrape successful: {url} (quality: {data['quality_score']})")
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
            'posts': [],
            'scrape_failed': True,
            'scrape_method': 'minimal',
            'quality_score': 0
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
        if not self.session:
            raise Exception("Session not initialized")

        if not BS4_AVAILABLE:
            raise Exception("BeautifulSoup not available")

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.debug(f"Request failed for {url}: {e}")
            raise

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

        # Try to extract name from common selectors (SPECIFIC ONLY - no generic fallbacks)
        name_selectors = [
            'h1.username', 'span.username', 'div.profile-name', 'h1.name',
            'div.user-profile-name', 'span.display-name', '[itemprop="name"]',
            'meta[property="profile:username"]'
        ]
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get('content') if elem.name == 'meta' else elem.get_text(strip=True)
                # Validate: reject page titles, site names, generic text
                if name and self._is_valid_username(name):
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

    def _is_valid_username(self, name: str) -> bool:
        """
        Validate username - reject page titles, site names, generic text

        Args:
            name: Extracted name to validate

        Returns:
            True if valid username, False if likely a page title
        """
        if not name or not isinstance(name, str):
            return False

        name = name.strip()

        # Too long = likely page title/description
        if len(name) > 100:
            return False

        # Reject common page title patterns
        rejected_patterns = [
            r'^search\s',  # "Search code, repositories..."
            r'subscribe to',  # "Subscribe to receive..."
            r'\s-\s(explore|discover|home|browse)',  # "Site - Explore"
            r'sign (in|up)',  # "Sign in/up"
            r'log(in|out)',  # "Login/Logout"
            r'create account',
            r'profile\s-\s',  # "Profile - "
            r'share your',  # "Share your videos..."
            r'\.\.\.$',  # Ends with "..."
            r'^(the\s)?(world|biggest|leading)',  # "The world's biggest..."
            r'see what .+ (has )?discovered',  # "See what X discovered"
            r'follow their',  # "Follow their code..."
        ]

        for pattern in rejected_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False

        # Reject if contains multiple sentences (page description)
        if name.count('.') > 2 or name.count('!') > 1:
            return False

        return True

    def _platform_specific_scrape(self, url: str, platform: str) -> Dict:
        """
        Use platform-specific extraction logic with post/content extraction

        Args:
            url: URL to scrape
            platform: Platform name

        Returns:
            Extracted data with posts/activity
        """
        data = {
            'url': url,
            'platform': platform,
            'name': None,
            'bio': None,
            'posts': []
        }

        if not self.session:
            logger.warning("Session not available for platform-specific scrape")
            return data

        # === GITHUB ===
        if 'github.com' in url:
            return self._scrape_github(url, data)

        # === YOUTUBE ===
        elif 'youtube.com' in url:
            return self._scrape_youtube(url, data)

        # === PINTEREST ===
        elif 'pinterest.com' in url:
            return self._scrape_pinterest(url, data)

        # === ACADEMIA.EDU ===
        elif 'academia.edu' in url:
            return self._scrape_academia(url, data)

        # === DISQUS ===
        elif 'disqus.com' in url:
            return self._scrape_disqus(url, data)

        return data

    def _scrape_github(self, url: str, data: Dict) -> Dict:
        """Extract GitHub profile with repos, languages, and activity"""
        try:
            # Extract username from URL (handle both profile and repo URLs)
            parts = url.rstrip('/').split('/')
            # Profile URL: github.com/username
            # Repo URL: github.com/username/repo
            # Find github.com and take the next part as username
            try:
                github_idx = [i for i, p in enumerate(parts) if 'github.com' in p][0]
                username = parts[github_idx + 1] if github_idx + 1 < len(parts) else None
            except (IndexError, ValueError):
                # Fallback to old method
                username = parts[-1] if parts else None

            if not username or username in ['', 'github.com']:
                logger.warning(f"Could not extract username from URL: {url}")
                return data

            # Get user profile
            api_url = f'https://api.github.com/users/{username}'
            response = self.session.get(api_url, timeout=10)

            if response.status_code == 200:
                gh_data = response.json()
                data['name'] = gh_data.get('name') or gh_data.get('login')
                data['bio'] = gh_data.get('bio')
                data['location'] = gh_data.get('location')
                data['followers'] = gh_data.get('followers')
                data['following'] = gh_data.get('following')
                data['public_repos'] = gh_data.get('public_repos')
                data['created_at'] = gh_data.get('created_at')
                data['company'] = gh_data.get('company')
                data['blog'] = gh_data.get('blog')

                # Get repositories (post-like content)
                repos_url = f'https://api.github.com/users/{username}/repos?sort=updated&per_page=10'
                repos_response = self.session.get(repos_url, timeout=10)

                if repos_response.status_code == 200:
                    repos = repos_response.json()
                    posts = []
                    languages = set()

                    for repo in repos[:10]:  # Limit to 10 most recent
                        post = {
                            'type': 'repository',
                            'title': repo.get('name'),
                            'description': repo.get('description'),
                            'language': repo.get('language'),
                            'stars': repo.get('stargazers_count', 0),
                            'forks': repo.get('forks_count', 0),
                            'created_at': repo.get('created_at'),
                            'updated_at': repo.get('updated_at'),
                            'topics': repo.get('topics', [])
                        }
                        posts.append(post)

                        # Track languages
                        if repo.get('language'):
                            languages.add(repo.get('language'))

                    data['posts'] = posts
                    data['languages'] = list(languages)
                    data['primary_language'] = list(languages)[0] if languages else None

                logger.info(f"GitHub full extraction: {username} ({len(data.get('posts', []))} repos)")
                return data

        except Exception as e:
            logger.debug(f"GitHub extraction failed: {e}")

        return data

    def _scrape_youtube(self, url: str, data: Dict) -> Dict:
        """Extract YouTube channel info with videos"""
        try:
            # Extract from HTML (API requires key)
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return data

            if not BS4_AVAILABLE:
                return data

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract channel name
            name_elem = soup.select_one('meta[property="og:title"]')
            if name_elem:
                name = name_elem.get('content', '')
                if self._is_valid_username(name):
                    data['name'] = name

            # Extract channel description
            desc_elem = soup.select_one('meta[property="og:description"]')
            if desc_elem:
                data['bio'] = desc_elem.get('content')

            # Extract subscriber count from page
            subs_pattern = re.search(r'(\d+(?:\.\d+)?[KM]?)\s+subscribers', response.text, re.IGNORECASE)
            if subs_pattern:
                data['followers'] = subs_pattern.group(1)

            # Try to extract video titles from page
            posts = []
            # Look for video titles in JSON-LD or page text
            video_pattern = re.findall(r'"title":"([^"]+)".*?"publishedTimeText".*?"simpleText":"([^"]+)"', response.text)
            for title, date in video_pattern[:10]:  # Limit to 10
                posts.append({
                    'type': 'video',
                    'title': title,
                    'published': date
                })

            if posts:
                data['posts'] = posts

            logger.info(f"YouTube extraction: {data.get('name')} ({len(posts)} videos)")

        except Exception as e:
            logger.debug(f"YouTube extraction failed: {e}")

        return data

    def _scrape_pinterest(self, url: str, data: Dict) -> Dict:
        """Extract Pinterest profile with pins"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return data

            if not BS4_AVAILABLE:
                return data

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract name
            name_elem = soup.select_one('meta[property="og:title"]')
            if name_elem:
                name = name_elem.get('content', '')
                # Clean Pinterest-specific patterns
                name = re.sub(r'\s*\|\s*Pinterest.*$', '', name, flags=re.IGNORECASE)
                if self._is_valid_username(name):
                    data['name'] = name

            # Extract bio
            desc_elem = soup.select_one('meta[property="og:description"]')
            if desc_elem:
                bio = desc_elem.get('content', '')
                # Clean generic Pinterest descriptions
                if not re.search(r'world.*biggest collection', bio, re.IGNORECASE):
                    data['bio'] = bio

            # Extract pins from page data
            posts = []
            pin_pattern = re.findall(r'"title":"([^"]+)".*?"board".*?"name":"([^"]+)"', response.text)
            for title, board in pin_pattern[:15]:  # Limit to 15
                posts.append({
                    'type': 'pin',
                    'title': title,
                    'board': board
                })

            if posts:
                data['posts'] = posts

            logger.info(f"Pinterest extraction: {data.get('name')} ({len(posts)} pins)")

        except Exception as e:
            logger.debug(f"Pinterest extraction failed: {e}")

        return data

    def _scrape_academia(self, url: str, data: Dict) -> Dict:
        """Extract Academia.edu profile with research papers"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return data

            if not BS4_AVAILABLE:
                return data

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract researcher name
            name_elem = soup.select_one('h1.ds-profile-name') or soup.select_one('[itemprop="name"]')
            if name_elem:
                name = name_elem.get_text(strip=True)
                if self._is_valid_username(name):
                    data['name'] = name

            # Extract bio/interests
            interests = []
            interest_elems = soup.select('.research-interests a, .ds-research-interests a')
            for elem in interest_elems:
                interests.append(elem.get_text(strip=True))

            if interests:
                data['bio'] = 'Research interests: ' + ', '.join(interests)
                data['research_interests'] = interests

            # Extract papers
            posts = []
            paper_elems = soup.select('.ds-work, .work-card')
            for paper in paper_elems[:10]:  # Limit to 10
                title_elem = paper.select_one('.ds-work--title, .work-card--title')
                if title_elem:
                    posts.append({
                        'type': 'paper',
                        'title': title_elem.get_text(strip=True)
                    })

            if posts:
                data['posts'] = posts

            logger.info(f"Academia.edu extraction: {data.get('name')} ({len(posts)} papers)")

        except Exception as e:
            logger.debug(f"Academia.edu extraction failed: {e}")

        return data

    def _scrape_disqus(self, url: str, data: Dict) -> Dict:
        """Extract Disqus profile with comments"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return data

            if not BS4_AVAILABLE:
                return data

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract username
            username_elem = soup.select_one('h2.profile-username, .username')
            if username_elem:
                name = username_elem.get_text(strip=True)
                if self._is_valid_username(name):
                    data['name'] = name

            # Extract bio
            bio_elem = soup.select_one('.profile-bio, .user-bio')
            if bio_elem:
                data['bio'] = bio_elem.get_text(strip=True)

            # Extract comment count
            stats_elem = soup.select_one('.profile-stat--comments, [data-stat="comments"]')
            if stats_elem:
                comment_text = stats_elem.get_text(strip=True)
                match = re.search(r'(\d+)', comment_text)
                if match:
                    data['total_comments'] = int(match.group(1))

            # Extract recent comments (posts)
            posts = []
            comment_elems = soup.select('.post-message, .comment-body')
            for comment in comment_elems[:10]:  # Limit to 10
                text = comment.get_text(strip=True)
                if len(text) > 10:  # Only substantial comments
                    posts.append({
                        'type': 'comment',
                        'text': text[:200]  # Truncate long comments
                    })

            if posts:
                data['posts'] = posts

            logger.info(f"Disqus extraction: {data.get('name')} ({len(posts)} comments)")

        except Exception as e:
            logger.debug(f"Disqus extraction failed: {e}")

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
            'academia.edu': 'academia',
            'artstation.com': 'artstation',
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
        Updated to account for post extraction and rich metadata

        Args:
            data: Scraped data dictionary

        Returns:
            Quality score 0-100
        """
        score = 0

        # Has valid name (not page title)
        if data.get('name'):
            name = data.get('name')
            if self._is_valid_username(name):
                score += 20
            else:
                score += 5  # Has name but it's likely a page title

        # Has bio/description
        if data.get('bio') or data.get('description'):
            bio_text = data.get('bio') or data.get('description')
            if len(bio_text) > 20:  # Substantial bio
                score += min(20, len(bio_text) // 15)

        # Has location
        if data.get('location'):
            score += 10

        # Has followers/social metrics
        if data.get('followers') or data.get('friends'):
            score += 10

        # Has posts/content (MAJOR QUALITY INDICATOR)
        posts = data.get('posts', [])
        if posts:
            score += min(30, len(posts) * 3)  # Up to 30 points for posts

        # Bonus: Platform-specific rich data
        # GitHub bonuses
        if data.get('languages'):
            score += 5
        if data.get('public_repos'):
            score += 5

        # Research bonuses
        if data.get('research_interests'):
            score += 5

        # Social engagement bonuses
        if data.get('company') or data.get('blog'):
            score += 3

        # Timestamps = temporal analysis possible
        if any('created_at' in str(post) or 'updated_at' in str(post) or 'published' in str(post)
               for post in posts):
            score += 5

        return min(100, score)
