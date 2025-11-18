"""
Platform-Specific Scrapers: Extract data without login or AI
Each platform has custom extraction logic
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from .utils import setup_logger

logger = setup_logger(__name__)


class PlatformScraper:
    """Scrapes social media platforms WITHOUT login"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def scrape_github(self, username: str) -> Dict:
        """
        Scrape GitHub profile - NO LOGIN NEEDED
        Public profiles are fully accessible
        """
        try:
            url = f"https://github.com/{username}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 404:
                return {'status': 'not_found', 'platform': 'github'}

            soup = BeautifulSoup(response.content, 'html.parser')

            data = {
                'status': 'success',
                'platform': 'github',
                'username': username,
                'url': url,
                'name': '',
                'bio': '',
                'location': '',
                'website': '',
                'email': '',
                'repos': 0,
                'followers': 0,
                'following': 0,
                'social_links': [],
                'interests': []
            }

            # Extract name
            name_elem = soup.find('span', {'itemprop': 'name'})
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)

            # Extract bio
            bio_elem = soup.find('div', {'class': 'p-note user-profile-bio'})
            if bio_elem:
                data['bio'] = bio_elem.get_text(strip=True)

            # Extract location
            location_elem = soup.find('span', {'itemprop': 'homeLocation'})
            if location_elem:
                data['location'] = location_elem.get_text(strip=True)

            # Extract website
            website_elem = soup.find('a', {'itemprop': 'url'})
            if website_elem:
                data['website'] = website_elem.get('href', '')

            # Extract email from profile or repos
            email_elem = soup.find('a', {'itemprop': 'email'})
            if email_elem:
                data['email'] = email_elem.get_text(strip=True)

            # Extract stats
            stats = soup.find_all('span', {'class': 'text-bold color-fg-default'})
            if len(stats) >= 2:
                try:
                    data['repos'] = int(stats[0].get_text(strip=True))
                except:
                    pass

            # Extract social links from bio
            links = soup.find_all('a', {'class': 'Link--primary'})
            for link in links:
                href = link.get('href', '')
                if any(platform in href for platform in ['twitter', 'linkedin', 'instagram', 'facebook']):
                    data['social_links'].append(href)

            # Extract interests from pinned repos
            pinned = soup.find_all('span', {'class': 'repo-language-color'})
            languages = [p.find_next('span').get_text(strip=True) for p in pinned if p.find_next('span')]
            data['interests'] = languages[:5]

            logger.info(f"Successfully scraped GitHub: {username}")
            return data

        except Exception as e:
            logger.error(f"GitHub scraping error: {e}")
            return {'status': 'error', 'platform': 'github', 'error': str(e)}

    def scrape_twitter_nitter(self, username: str) -> Dict:
        """
        Scrape Twitter using Nitter (NO LOGIN NEEDED!)
        Nitter is a free Twitter frontend that doesn't require auth
        """
        nitter_instances = [
            'https://nitter.net',
            'https://nitter.it',
            'https://nitter.1d4.us',
        ]

        for instance in nitter_instances:
            try:
                url = f"{instance}/{username}"
                response = self.session.get(url, timeout=10)

                if response.status_code == 404:
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')

                data = {
                    'status': 'success',
                    'platform': 'twitter',
                    'username': username,
                    'url': f"https://twitter.com/{username}",
                    'name': '',
                    'bio': '',
                    'location': '',
                    'website': '',
                    'tweets': 0,
                    'followers': 0,
                    'following': 0,
                    'interests': [],
                    'recent_tweets': []
                }

                # Extract profile info
                profile_card = soup.find('div', {'class': 'profile-card'})
                if profile_card:
                    name_elem = profile_card.find('a', {'class': 'profile-card-fullname'})
                    if name_elem:
                        data['name'] = name_elem.get_text(strip=True)

                    bio_elem = profile_card.find('p', {'class': 'profile-bio'})
                    if bio_elem:
                        data['bio'] = bio_elem.get_text(strip=True)

                # Extract stats
                stats = soup.find('ul', {'class': 'profile-statlist'})
                if stats:
                    stat_items = stats.find_all('li', {'class': 'profile-stat'})
                    for item in stat_items:
                        label = item.find('span', {'class': 'profile-stat-header'})
                        value = item.find('span', {'class': 'profile-stat-num'})
                        if label and value:
                            label_text = label.get_text(strip=True).lower()
                            try:
                                val = int(value.get_text(strip=True).replace(',', ''))
                                if 'tweet' in label_text:
                                    data['tweets'] = val
                                elif 'following' in label_text:
                                    data['following'] = val
                                elif 'follower' in label_text:
                                    data['followers'] = val
                            except:
                                pass

                # Extract recent tweets for interest analysis
                tweets = soup.find_all('div', {'class': 'tweet-content'}, limit=5)
                for tweet in tweets:
                    tweet_text = tweet.get_text(strip=True)
                    data['recent_tweets'].append(tweet_text)

                    # Extract hashtags as interests
                    hashtags = re.findall(r'#(\w+)', tweet_text)
                    data['interests'].extend(hashtags)

                data['interests'] = list(set(data['interests']))[:10]

                logger.info(f"Successfully scraped Twitter via Nitter: {username}")
                return data

            except Exception as e:
                logger.debug(f"Nitter instance {instance} failed: {e}")
                continue

        return {'status': 'not_found', 'platform': 'twitter'}

    def scrape_linkedin_public(self, username: str) -> Dict:
        """
        Scrape LinkedIn public profile - NO LOGIN NEEDED
        Uses public profile URLs
        """
        try:
            url = f"https://www.linkedin.com/in/{username}"

            # Try direct access first
            response = self.session.get(url, timeout=10)

            soup = BeautifulSoup(response.content, 'html.parser')

            data = {
                'status': 'success',
                'platform': 'linkedin',
                'username': username,
                'url': url,
                'name': '',
                'headline': '',
                'location': '',
                'connections': 0,
                'skills': [],
                'interests': []
            }

            # LinkedIn blocks scraping, but we can get basic info from meta tags
            # Extract from Open Graph tags
            og_title = soup.find('meta', {'property': 'og:title'})
            if og_title:
                data['name'] = og_title.get('content', '').split('|')[0].strip()

            og_description = soup.find('meta', {'property': 'og:description'})
            if og_description:
                data['headline'] = og_description.get('content', '')

            # Alternative: Use Google cache
            google_cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
            try:
                cache_response = self.session.get(google_cache_url, timeout=10)
                cache_soup = BeautifulSoup(cache_response.content, 'html.parser')

                # Extract from cached version
                text_content = cache_soup.get_text()

                # Look for location patterns
                location_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2,})', text_content)
                if location_match:
                    data['location'] = location_match.group(1)

            except:
                pass

            logger.info(f"Scraped LinkedIn public profile: {username}")
            return data

        except Exception as e:
            logger.error(f"LinkedIn scraping error: {e}")
            return {'status': 'error', 'platform': 'linkedin', 'error': str(e)}

    def scrape_reddit(self, username: str) -> Dict:
        """
        Scrape Reddit profile - NO LOGIN NEEDED
        Reddit allows public profile access
        """
        try:
            url = f"https://www.reddit.com/user/{username}/about.json"
            response = self.session.get(url, timeout=10)

            if response.status_code == 404:
                return {'status': 'not_found', 'platform': 'reddit'}

            json_data = response.json()
            user_data = json_data.get('data', {})

            data = {
                'status': 'success',
                'platform': 'reddit',
                'username': username,
                'url': f"https://www.reddit.com/user/{username}",
                'name': user_data.get('name', ''),
                'karma': user_data.get('total_karma', 0),
                'created': user_data.get('created_utc', 0),
                'is_gold': user_data.get('is_gold', False),
                'interests': []
            }

            # Get recent posts to extract interests
            posts_url = f"https://www.reddit.com/user/{username}/submitted.json?limit=10"
            posts_response = self.session.get(posts_url, timeout=10)

            if posts_response.status_code == 200:
                posts_data = posts_response.json()
                for post in posts_data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    subreddit = post_data.get('subreddit', '')
                    if subreddit:
                        data['interests'].append(subreddit)

            data['interests'] = list(set(data['interests']))[:10]

            logger.info(f"Successfully scraped Reddit: {username}")
            return data

        except Exception as e:
            logger.error(f"Reddit scraping error: {e}")
            return {'status': 'error', 'platform': 'reddit', 'error': str(e)}

    def scrape_instagram_public(self, username: str) -> Dict:
        """
        Scrape Instagram public profile - LIMITED WITHOUT LOGIN
        Can get basic info from public profiles
        """
        try:
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url, timeout=10)

            soup = BeautifulSoup(response.content, 'html.parser')

            data = {
                'status': 'success',
                'platform': 'instagram',
                'username': username,
                'url': url,
                'name': '',
                'bio': '',
                'posts': 0,
                'followers': 0,
                'following': 0
            }

            # Extract from meta tags (Instagram provides some data here)
            og_title = soup.find('meta', {'property': 'og:title'})
            if og_title:
                title_parts = og_title.get('content', '').split('•')
                if len(title_parts) >= 3:
                    try:
                        data['followers'] = int(re.sub(r'[^\d]', '', title_parts[0]))
                        data['following'] = int(re.sub(r'[^\d]', '', title_parts[1]))
                        data['posts'] = int(re.sub(r'[^\d]', '', title_parts[2]))
                    except:
                        pass

            og_description = soup.find('meta', {'property': 'og:description'})
            if og_description:
                desc = og_description.get('content', '')
                # Format: "XXX Followers, XXX Following, XXX Posts - See Instagram photos..."
                if '-' in desc:
                    data['bio'] = desc.split('-', 1)[1].strip()

            logger.info(f"Scraped Instagram public: {username}")
            return data

        except Exception as e:
            logger.error(f"Instagram scraping error: {e}")
            return {'status': 'error', 'platform': 'instagram', 'error': str(e)}

    def auto_scrape(self, url: str) -> Dict:
        """
        Automatically detect platform and scrape
        """
        url_lower = url.lower()

        if 'github.com' in url_lower:
            username = url.split('github.com/')[-1].split('/')[0]
            return self.scrape_github(username)

        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            username = url.split('/')[-1].split('?')[0]
            return self.scrape_twitter_nitter(username)

        elif 'linkedin.com' in url_lower:
            username = url.split('/in/')[-1].split('/')[0].split('?')[0]
            return self.scrape_linkedin_public(username)

        elif 'reddit.com' in url_lower:
            username = url.split('/user/')[-1].split('/')[0]
            return self.scrape_reddit(username)

        elif 'instagram.com' in url_lower:
            username = url.split('instagram.com/')[-1].split('/')[0]
            return self.scrape_instagram_public(username)

        else:
            # Generic scraping
            return self.generic_scrape(url)

    def generic_scrape(self, url: str) -> Dict:
        """Generic scraping for unknown platforms"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            title = soup.find('title')
            title_text = title.get_text() if title else ''

            meta_desc = soup.find('meta', {'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''

            text_content = soup.get_text()
            preview = ' '.join(text_content.split())[:500]

            return {
                'status': 'success',
                'platform': 'unknown',
                'url': url,
                'title': title_text,
                'description': description,
                'preview': preview
            }

        except Exception as e:
            return {'status': 'error', 'platform': 'unknown', 'error': str(e)}
