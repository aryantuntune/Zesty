"""
Email Discovery & Verification: Find and verify email addresses
Extracts emails from content and verifies their validity
"""

import re
import socket
import dns.resolver
from typing import List, Set, Dict, Optional
from .utils import setup_logger

logger = setup_logger(__name__)

# Try to import DNS library
try:
    import dns.resolver
    DNS_AVAILABLE = True
    logger.info("DNS library available for email verification")
except ImportError:
    DNS_AVAILABLE = False
    logger.warning("dnspython not installed. Install with: pip install dnspython")


class EmailFinder:
    """
    Discover and verify email addresses

    Features:
    - Extract emails from text/HTML
    - Generate email variations
    - Validate email format
    - Verify DNS MX records
    - Domain verification
    """

    def __init__(self):
        self.use_dns = DNS_AVAILABLE

        # Common email pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )

        # Obfuscated email patterns
        self.obfuscated_patterns = [
            re.compile(r'\b([A-Za-z0-9._%+-]+)\s*\[?at\]?\s*([A-Za-z0-9.-]+)\s*\[?dot\]?\s*([A-Z|a-z]{2,})\b', re.IGNORECASE),
            re.compile(r'\b([A-Za-z0-9._%+-]+)\s*@\s*([A-Za-z0-9.-]+)\s*\.\s*([A-Z|a-z]{2,})\b'),
        ]

        # Common email domains
        self.common_domains = [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
            'icloud.com', 'protonmail.com', 'aol.com', 'zoho.com'
        ]

    def extract_emails(self, text: str) -> Set[str]:
        """
        Extract all email addresses from text

        Args:
            text: Text to search

        Returns:
            Set of email addresses found
        """
        if not text:
            return set()

        emails = set()

        # Find standard emails
        matches = self.email_pattern.findall(text)
        emails.update(matches)

        # Find obfuscated emails
        for pattern in self.obfuscated_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 3:
                    # Reconstruct email
                    email = f"{match[0]}@{match[1]}.{match[2]}"
                    emails.add(email.lower())

        # Clean and validate
        validated_emails = set()
        for email in emails:
            email = email.lower().strip()
            if self.validate_email_format(email):
                validated_emails.add(email)

        logger.info(f"Extracted {len(validated_emails)} emails from text")

        return validated_emails

    def validate_email_format(self, email: str) -> bool:
        """
        Validate email format (basic check)

        Args:
            email: Email address to validate

        Returns:
            True if valid format
        """
        if not email or '@' not in email:
            return False

        # Check length
        if len(email) > 320:  # Max email length
            return False

        # Split into local and domain parts
        try:
            local, domain = email.rsplit('@', 1)
        except ValueError:
            return False

        # Validate local part (before @)
        if not local or len(local) > 64:
            return False

        # Validate domain part
        if not domain or '.' not in domain:
            return False

        # Check for valid characters
        if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', email):
            return False

        return True

    def verify_domain(self, email: str) -> Dict:
        """
        Verify email domain has valid MX records

        Args:
            email: Email address to verify

        Returns:
            {
                'valid': bool,
                'mx_records': List[str],
                'domain': str,
                'error': str
            }
        """
        if not self.validate_email_format(email):
            return {
                'valid': False,
                'mx_records': [],
                'domain': '',
                'error': 'Invalid email format'
            }

        try:
            domain = email.split('@')[1]
        except:
            return {
                'valid': False,
                'mx_records': [],
                'domain': '',
                'error': 'Cannot extract domain'
            }

        if not self.use_dns:
            # Fallback: just check domain exists
            try:
                socket.gethostbyname(domain)
                return {
                    'valid': True,
                    'mx_records': [],
                    'domain': domain,
                    'error': None
                }
            except socket.gaierror:
                return {
                    'valid': False,
                    'mx_records': [],
                    'domain': domain,
                    'error': 'Domain does not exist'
                }

        # Check MX records
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(record.exchange) for record in mx_records]

            return {
                'valid': True,
                'mx_records': mx_hosts,
                'domain': domain,
                'error': None
            }

        except dns.resolver.NXDOMAIN:
            return {
                'valid': False,
                'mx_records': [],
                'domain': domain,
                'error': 'Domain does not exist'
            }
        except dns.resolver.NoAnswer:
            return {
                'valid': False,
                'mx_records': [],
                'domain': domain,
                'error': 'No MX records found'
            }
        except Exception as e:
            return {
                'valid': False,
                'mx_records': [],
                'domain': domain,
                'error': f'DNS error: {str(e)}'
            }

    def generate_email_variations(
        self,
        name: str,
        username: str = None,
        domains: List[str] = None
    ) -> List[str]:
        """
        Generate possible email variations

        Args:
            name: Full name (e.g., "John Doe")
            username: Username if known
            domains: List of domains to try (defaults to common ones)

        Returns:
            List of possible email addresses
        """
        if domains is None:
            domains = self.common_domains

        variations = []

        # Clean name
        name = name.lower().strip()
        parts = name.split()

        if not parts:
            return []

        # Name-based patterns
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]

            patterns = [
                f"{first}.{last}",
                f"{first}{last}",
                f"{first}_{last}",
                f"{first[0]}{last}",
                f"{first}{last[0]}",
                f"{last}.{first}",
                f"{last}{first}",
            ]

            for pattern in patterns:
                for domain in domains:
                    variations.append(f"{pattern}@{domain}")

        # Username-based
        if username:
            username_clean = re.sub(r'[^a-z0-9]', '', username.lower())

            for domain in domains:
                variations.append(f"{username_clean}@{domain}")

        # Remove duplicates
        variations = list(set(variations))

        logger.info(f"Generated {len(variations)} email variations")

        return variations

    def find_emails_in_account(self, account_data: Dict) -> Dict:
        """
        Find all emails associated with an account

        Args:
            account_data: Scraped account data

        Returns:
            {
                'found_emails': List[str],
                'verified_emails': List[str],
                'predicted_emails': List[str]
            }
        """
        found_emails = set()
        verified_emails = []
        predicted_emails = []

        # Extract from bio
        bio = account_data.get('bio', '')
        if bio:
            found_emails.update(self.extract_emails(bio))

        # Extract from other fields
        for field in ['description', 'about', 'contact', 'website']:
            text = account_data.get(field, '')
            if text:
                found_emails.update(self.extract_emails(str(text)))

        # Direct email field
        if 'email' in account_data and account_data['email']:
            email = account_data['email'].lower().strip()
            if self.validate_email_format(email):
                found_emails.add(email)

        # Verify found emails
        for email in found_emails:
            result = self.verify_domain(email)
            if result['valid']:
                verified_emails.append(email)

        # Generate predictions
        name = account_data.get('name', '')
        username = account_data.get('username', '')

        if name or username:
            predicted = self.generate_email_variations(
                name=name or username,
                username=username,
                domains=self.common_domains[:3]  # Top 3 domains
            )
            predicted_emails = predicted[:10]  # Top 10 predictions

        result = {
            'found_emails': list(found_emails),
            'verified_emails': verified_emails,
            'predicted_emails': predicted_emails
        }

        logger.info(f"Found {len(found_emails)} emails, verified {len(verified_emails)}")

        return result

    def search_email_accounts(self, email: str) -> List[str]:
        """
        Generate potential account URLs for an email

        Args:
            email: Email address

        Returns:
            List of potential profile URLs to check
        """
        if not self.validate_email_format(email):
            return []

        # Extract username from email
        username = email.split('@')[0]

        # Common platforms that might use this username
        platforms = [
            f"https://github.com/{username}",
            f"https://twitter.com/{username}",
            f"https://reddit.com/user/{username}",
            f"https://linkedin.com/in/{username}",
            f"https://instagram.com/{username}",
            f"https://facebook.com/{username}",
        ]

        logger.info(f"Generated {len(platforms)} potential URLs for {email}")

        return platforms

    def compare_emails(self, email1: str, email2: str) -> Dict:
        """
        Compare two emails for similarity

        Args:
            email1: First email
            email2: Second email

        Returns:
            {
                'same_domain': bool,
                'same_local': bool,
                'similarity_score': float,
                'likely_same_person': bool
            }
        """
        if not email1 or not email2:
            return {
                'same_domain': False,
                'same_local': False,
                'similarity_score': 0.0,
                'likely_same_person': False
            }

        email1 = email1.lower()
        email2 = email2.lower()

        # Exact match
        if email1 == email2:
            return {
                'same_domain': True,
                'same_local': True,
                'similarity_score': 1.0,
                'likely_same_person': True
            }

        # Extract parts
        local1, domain1 = email1.split('@')
        local2, domain2 = email2.split('@')

        same_domain = (domain1 == domain2)
        same_local = (local1 == local2)

        # Calculate similarity
        score = 0.0

        if same_domain:
            score += 0.3

        if same_local:
            score += 0.7
        else:
            # Partial local match
            # Check if one is substring of other
            if local1 in local2 or local2 in local1:
                score += 0.4
            # Check for similar patterns (john.doe vs johndoe)
            clean1 = re.sub(r'[^a-z0-9]', '', local1)
            clean2 = re.sub(r'[^a-z0-9]', '', local2)

            if clean1 == clean2:
                score += 0.5

        likely_same = score >= 0.6

        return {
            'same_domain': same_domain,
            'same_local': same_local,
            'similarity_score': round(score, 2),
            'likely_same_person': likely_same
        }


# Convenience function
def get_email_finder() -> EmailFinder:
    """Get email finder instance"""
    return EmailFinder()
