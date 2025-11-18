"""
Pivot Engine: Cross-reference and discover related accounts
This is what separates amateur OSINT from professional investigations
"""

import re
import requests
from typing import Dict, List, Set, Optional
from urllib.parse import urlparse
from .utils import setup_logger, extract_domain

try:
    from googlesearch import search
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

logger = setup_logger(__name__)


class PivotEngine:
    """
    Discovers related accounts by pivoting on extracted information
    Uses: names, emails, phone numbers, locations, profile pictures
    """

    def __init__(self):
        self.pivot_points: Dict[str, Set[str]] = {
            'names': set(),
            'emails': set(),
            'phones': set(),
            'locations': set(),
            'profile_images': set(),
            'usernames': set(),
            'websites': set(),
            'social_handles': set()
        }
        self.discovered_urls: Set[str] = set()

    def extract_pivot_points(self, text: str, url: str = None) -> Dict[str, List[str]]:
        """
        Extract pivot points from text (bio, profile, posts)

        Returns dict of pivot points found
        """
        extracted = {
            'names': [],
            'emails': [],
            'phones': [],
            'usernames': [],
            'social_handles': []
        }

        # Extract emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        extracted['emails'] = list(set(emails))

        # Extract phone numbers (various formats)
        phones = re.findall(
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            text
        )
        extracted['phones'] = [p[0] if isinstance(p, tuple) else p for p in phones]

        # Extract usernames (common patterns)
        # Matches @username or username in common formats
        usernames = re.findall(r'@([A-Za-z0-9_]{3,15})\b', text)
        extracted['usernames'] = list(set(usernames))

        # Extract social media handles from URLs in text
        social_patterns = {
            'twitter': r'twitter\.com/([A-Za-z0-9_]+)',
            'instagram': r'instagram\.com/([A-Za-z0-9_.]+)',
            'linkedin': r'linkedin\.com/in/([A-Za-z0-9-]+)',
            'github': r'github\.com/([A-Za-z0-9-]+)',
            'facebook': r'facebook\.com/([A-Za-z0-9.]+)',
        }

        for platform, pattern in social_patterns.items():
            handles = re.findall(pattern, text, re.IGNORECASE)
            for handle in handles:
                extracted['social_handles'].append(f"{platform}:{handle}")

        # Extract potential names (capitalized words, 2-3 words)
        name_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b'
        names = re.findall(name_pattern, text)
        extracted['names'] = list(set(names))

        # Store in global pivot points
        for key, values in extracted.items():
            if key in self.pivot_points:
                self.pivot_points[key].update(values)

        return extracted

    def generate_username_variations(self, username: str) -> List[str]:
        """
        Generate common username variations

        Examples:
            "aryantuntune" -> ["aryan_tuntune", "aryan-tuntune", "aryan.tuntune", etc.]
        """
        variations = [username]  # Original

        # Common separators
        separators = ['_', '-', '.', '']

        # Try to split on capital letters or numbers
        # e.g., "AryanTuntune" -> ["Aryan", "Tuntune"]
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|\d+', username)

        if len(parts) > 1:
            for sep in separators:
                variations.append(sep.join(parts).lower())
                variations.append(sep.join(parts))  # Keep original case

        # Try to split on underscores/hyphens if they exist
        for sep in ['_', '-', '.']:
            if sep in username:
                parts = username.split(sep)
                for new_sep in separators:
                    variations.append(new_sep.join(parts))

        # Add common suffixes
        common_suffixes = ['', '_official', '_real', '123', '1', '_']
        for suffix in common_suffixes:
            variations.append(username + suffix)

        # Add numbers at the end (common pattern)
        for num in ['1', '12', '123', '01', '99']:
            variations.append(username + num)

        return list(set(variations))  # Remove duplicates

    def search_by_email(self, email: str) -> List[str]:
        """
        Search for accounts associated with an email
        Uses Google dorks and common patterns
        """
        if not GOOGLE_AVAILABLE:
            logger.warning("Google search not available")
            return []

        logger.info(f"Pivoting on email: {email}")

        queries = [
            f'"{email}"',
            f'"{email}" (site:github.com OR site:linkedin.com OR site:twitter.com)',
            f'"{email}" profile',
            f'"{email}" contact'
        ]

        results = []
        for query in queries:
            try:
                for url in search(query, num_results=5, sleep_interval=2):
                    results.append(url)
                    self.discovered_urls.add(url)
            except Exception as e:
                logger.debug(f"Email search failed: {e}")

        return results

    def search_by_name(self, full_name: str, context: str = "") -> List[str]:
        """
        Search by real name with optional context (location, company, skills)

        Args:
            full_name: Person's real name
            context: Additional info like "Flutter developer Mumbai"
        """
        if not GOOGLE_AVAILABLE:
            return []

        logger.info(f"Pivoting on name: {full_name}")

        queries = [
            f'"{full_name}" {context}',
            f'"{full_name}" (site:linkedin.com OR site:github.com)',
            f'"{full_name}" profile',
            f'"{full_name}" {context} contact',
        ]

        results = []
        for query in queries[:2]:  # Limit to avoid rate limits
            try:
                for url in search(query, num_results=5, sleep_interval=2):
                    results.append(url)
                    self.discovered_urls.add(url)
            except Exception as e:
                logger.debug(f"Name search failed: {e}")

        return results

    def reverse_image_search(self, image_url: str) -> List[str]:
        """
        Perform reverse image search to find other profiles with same picture

        Note: This is a simplified version. Production would use:
        - Google Images API
        - TinEye API
        - PimEyes (face-specific)
        """
        logger.info(f"Reverse image search for: {image_url}")

        # Google reverse image search URL
        google_search_url = f"https://www.google.com/searchbyimage?image_url={image_url}"

        # In production, you'd:
        # 1. Submit image to reverse search API
        # 2. Parse results
        # 3. Return matching profiles

        # For now, we log the capability
        logger.info(f"Image search URL: {google_search_url}")

        return [google_search_url]

    def find_related_accounts(
        self,
        initial_username: str,
        extracted_data: Dict
    ) -> Dict[str, List[str]]:
        """
        Main pivot function: takes initial findings and discovers related accounts

        Args:
            initial_username: Original username searched
            extracted_data: Dict containing names, emails, etc. from agent analysis

        Returns:
            Dict of pivot strategies and discovered URLs
        """
        logger.info(f"Starting pivot analysis for: {initial_username}")

        results = {
            'username_variations': [],
            'email_based': [],
            'name_based': [],
            'image_based': [],
            'social_links': []
        }

        # Strategy 1: Username variations
        variations = self.generate_username_variations(initial_username)
        logger.info(f"Generated {len(variations)} username variations")
        results['username_variations'] = variations

        # Strategy 2: Email-based search
        if 'emails' in extracted_data:
            for email in extracted_data['emails']:
                email_urls = self.search_by_email(email)
                results['email_based'].extend(email_urls)

        # Strategy 3: Name-based search
        if 'names' in extracted_data and extracted_data['names']:
            for name in extracted_data['names']:
                # Build context from other data
                context = ""
                if 'skills' in extracted_data:
                    context += " ".join(extracted_data['skills'][:3])
                if 'location' in extracted_data:
                    context += " " + extracted_data['location']

                name_urls = self.search_by_name(name, context)
                results['name_based'].extend(name_urls)

        # Strategy 4: Profile image reverse search
        if 'profile_image' in extracted_data:
            image_urls = self.reverse_image_search(extracted_data['profile_image'])
            results['image_based'] = image_urls

        # Strategy 5: Follow social media links directly
        if 'social_links' in extracted_data:
            results['social_links'] = extracted_data['social_links']

        return results

    def cross_validate(self, accounts: List[Dict]) -> List[Dict]:
        """
        Cross-validate multiple accounts to confirm they belong to same person

        Validation signals:
        - Same name across accounts
        - Same location
        - Same profile picture (face recognition)
        - Cross-references (one profile links to another)
        - Similar bio/description
        - Overlapping skills
        """
        logger.info(f"Cross-validating {len(accounts)} accounts")

        validated = []
        confidence_scores = []

        for account in accounts:
            confidence = 0
            reasons = []

            # Check name consistency
            names_in_account = account.get('names', [])
            if names_in_account:
                # Compare with other accounts
                for other in accounts:
                    if other == account:
                        continue
                    other_names = other.get('names', [])
                    if any(name in other_names for name in names_in_account):
                        confidence += 30
                        reasons.append("Name match across accounts")
                        break

            # Check location consistency
            if 'location' in account:
                for other in accounts:
                    if other == account:
                        continue
                    if other.get('location') == account['location']:
                        confidence += 20
                        reasons.append("Location match")
                        break

            # Check for cross-references
            if 'social_links' in account:
                for link in account['social_links']:
                    for other in accounts:
                        if other.get('url') in link:
                            confidence += 40
                            reasons.append("Direct cross-reference")
                            break

            account['confidence'] = confidence
            account['validation_reasons'] = reasons

            if confidence >= 50:  # Threshold for "likely same person"
                validated.append(account)

        return sorted(validated, key=lambda x: x['confidence'], reverse=True)

    def get_summary(self) -> str:
        """Generate summary of pivot analysis"""
        summary = "## Pivot Analysis Summary\n\n"
        summary += f"**Total Pivot Points Discovered:**\n"
        for key, values in self.pivot_points.items():
            if values:
                summary += f"- {key.title()}: {len(values)}\n"
                summary += f"  {', '.join(list(values)[:5])}\n"

        summary += f"\n**Total URLs Discovered via Pivoting:** {len(self.discovered_urls)}\n"

        return summary
