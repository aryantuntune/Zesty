#!/usr/bin/env python3
"""
Email Transform - Automated Email Intelligence Gathering

This transform takes an email address and discovers:
1. Breach records (haveibeenpwned API)
2. Email validation (syntax, domain MX records)
3. Company/domain extraction
4. Public exposure (Hunter.io, RocketReach - optional)
5. Associated social media (Gravatar hash, email-based lookups)

Professional Tradecraft:
- Passive-first: Check breach databases before active validation
- MX record validation is passive (DNS query, no email sent)
- Gravatar hash lookup is passive (no notification to target)

API Keys Required (Optional):
- HIBP_API_KEY: haveibeenpwned.com (paid, $3.50/month for breach data)
- HUNTER_API_KEY: hunter.io (free tier: 25 searches/month)

Without API keys, still provides:
- Email syntax validation
- Domain extraction
- MX record verification
"""

import re
import hashlib
import dns.resolver
import requests
from typing import List, Optional
from datetime import datetime

from .base_transform import (
    BaseTransform,
    TransformResult,
    Selector,
    SelectorType,
    DiscoveredEntity,
    Reliability
)
from ..utils import setup_logger

logger = setup_logger(__name__)


class EmailTransform(BaseTransform):
    """
    Transform for pivoting on email addresses.

    Capabilities:
    - Breach database lookup (haveibeenpwned)
    - Email validation (syntax + MX records)
    - Company domain extraction
    - Gravatar profile discovery
    - Email reputation checking
    """

    def __init__(self, hibp_api_key: Optional[str] = None, hunter_api_key: Optional[str] = None):
        """
        Initialize email transform.

        Args:
            hibp_api_key: haveibeenpwned API key (optional, for breach checks)
            hunter_api_key: Hunter.io API key (optional, for email finding)
        """
        super().__init__(api_key=hibp_api_key, rate_limit=60)
        self.hibp_api_key = hibp_api_key
        self.hunter_api_key = hunter_api_key

        # Configure DNS resolver
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 3
        self.dns_resolver.lifetime = 3

        logger.info(
            f"EmailTransform initialized (HIBP: {'✓' if hibp_api_key else '✗'}, "
            f"Hunter: {'✓' if hunter_api_key else '✗'})"
        )

    def can_handle(self, selector: Selector) -> bool:
        """Check if this is an email selector"""
        return selector.type == SelectorType.EMAIL

    def execute(self, selector: Selector) -> TransformResult:
        """
        Execute email intelligence gathering.

        Workflow:
        1. Validate email syntax
        2. Extract domain → create Domain selector
        3. Check MX records (passive validation)
        4. Query breach databases (HIBP)
        5. Check Gravatar for profile
        6. (Optional) Query Hunter.io for company/social media

        Args:
            selector: Email selector to pivot on

        Returns:
            TransformResult with discovered entities
        """
        email = selector.value.lower().strip()
        result = TransformResult(
            transform_name="EmailTransform",
            input_selector=selector
        )

        try:
            # Step 1: Validate syntax
            if not self._is_valid_email_syntax(email):
                result.success = False
                result.error_message = f"Invalid email syntax: {email}"
                return result

            # Step 2: Extract domain
            domain = email.split('@')[1]
            domain_selector = Selector(
                type=SelectorType.DOMAIN,
                value=domain,
                source=f"email_domain:{email}",
                context={'extracted_from_email': email}
            )
            result.discovered_entities.append(DiscoveredEntity(
                selector=domain_selector,
                reliability=Reliability.CONFIRMED,
                source="email_parsing",
                confidence=100,
                metadata={'extraction_method': 'email_split'}
            ))

            # Step 3: Validate MX records (passive check)
            mx_valid, mx_records = self._check_mx_records(domain)
            if mx_valid:
                result.metadata['mx_validation'] = 'PASS'
                result.metadata['mx_records'] = mx_records
                result.metadata['email_deliverable'] = 'PROBABLE'
            else:
                result.metadata['mx_validation'] = 'FAIL'
                result.metadata['email_deliverable'] = 'UNLIKELY'
                logger.warning(f"No MX records for {domain} - email likely invalid")

            # Step 4: Check breach databases (HIBP)
            if self.hibp_api_key:
                breaches = self._check_hibp_breaches(email)
                result.api_calls_made += 1

                for breach in breaches:
                    # Create selector for each breach
                    breach_selector = Selector(
                        type=SelectorType.URL,  # Breach as a "source" URL
                        value=breach['Name'],
                        source=f"hibp_breach:{email}",
                        context={
                            'breach_date': breach.get('BreachDate'),
                            'breach_description': breach.get('Description', ''),
                            'compromised_data': breach.get('DataClasses', []),
                            'is_verified': breach.get('IsVerified', False),
                            'is_sensitive': breach.get('IsSensitive', False)
                        }
                    )
                    result.discovered_entities.append(DiscoveredEntity(
                        selector=breach_selector,
                        reliability=Reliability.CONFIRMED if breach.get('IsVerified') else Reliability.PROBABLE,
                        source="haveibeenpwned",
                        confidence=95 if breach.get('IsVerified') else 75,
                        metadata={
                            'breach_name': breach['Name'],
                            'breach_date': breach.get('BreachDate'),
                            'data_classes': breach.get('DataClasses', []),
                            'affected_accounts': breach.get('PwnCount', 'Unknown')
                        }
                    ))

                result.metadata['breach_count'] = len(breaches)
                result.metadata['breached'] = len(breaches) > 0

                # Extract potential passwords/usernames from paste data
                pastes = self._check_hibp_pastes(email)
                result.api_calls_made += 1
                result.metadata['paste_count'] = len(pastes)
            else:
                logger.debug("HIBP API key not configured, skipping breach check")
                result.metadata['breach_check'] = 'SKIPPED (No API key)'

            # Step 5: Check Gravatar (passive, no API key needed)
            gravatar_data = self._check_gravatar(email)
            if gravatar_data:
                # Gravatar profile URL
                gravatar_selector = Selector(
                    type=SelectorType.URL,
                    value=gravatar_data['profile_url'],
                    source=f"gravatar:{email}",
                    context={
                        'display_name': gravatar_data.get('displayName'),
                        'avatar_url': gravatar_data.get('thumbnailUrl'),
                        'profile_urls': gravatar_data.get('urls', [])
                    }
                )
                result.discovered_entities.append(DiscoveredEntity(
                    selector=gravatar_selector,
                    reliability=Reliability.PROBABLE,
                    source="gravatar",
                    confidence=80,
                    metadata=gravatar_data
                ))

                # Extract name if available
                if gravatar_data.get('displayName'):
                    name_selector = Selector(
                        type=SelectorType.NAME,
                        value=gravatar_data['displayName'],
                        source=f"gravatar:{email}"
                    )
                    result.discovered_entities.append(DiscoveredEntity(
                        selector=name_selector,
                        reliability=Reliability.POSSIBLE,
                        source="gravatar",
                        confidence=65,
                        metadata={'from_gravatar': True}
                    ))

            # Step 6: Hunter.io lookup (optional)
            if self.hunter_api_key:
                hunter_data = self._check_hunter_io(email)
                result.api_calls_made += 1
                if hunter_data:
                    result.metadata['hunter_data'] = hunter_data
                    # Extract company, social profiles, etc.
                    if hunter_data.get('company'):
                        company_selector = Selector(
                            type=SelectorType.COMPANY,
                            value=hunter_data['company'],
                            source=f"hunter_io:{email}"
                        )
                        result.discovered_entities.append(DiscoveredEntity(
                            selector=company_selector,
                            reliability=Reliability.PROBABLE,
                            source="hunter_io",
                            confidence=80,
                            metadata={'verified': hunter_data.get('verified', False)}
                        ))

            result.success = True
            result.metadata['email_valid'] = mx_valid
            result.metadata['total_discoveries'] = len(result.discovered_entities)

        except Exception as e:
            logger.error(f"EmailTransform failed on {email}: {e}")
            result.success = False
            result.error_message = str(e)

        return result

    def _is_valid_email_syntax(self, email: str) -> bool:
        """
        Validate email syntax using regex.

        RFC 5322 compliant pattern (simplified).
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _check_mx_records(self, domain: str) -> tuple[bool, List[str]]:
        """
        Check if domain has valid MX records (passive DNS query).

        Args:
            domain: Domain to check

        Returns:
            (has_mx_records, list_of_mx_servers)
        """
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_servers = [str(mx.exchange) for mx in mx_records]
            logger.debug(f"MX records for {domain}: {mx_servers}")
            return True, mx_servers
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            logger.debug(f"No MX records for {domain}")
            return False, []
        except Exception as e:
            logger.warning(f"MX lookup failed for {domain}: {e}")
            return False, []

    def _check_hibp_breaches(self, email: str) -> List[dict]:
        """
        Query haveibeenpwned for breach records.

        API Documentation: https://haveibeenpwned.com/API/v3

        Args:
            email: Email to check

        Returns:
            List of breach dictionaries
        """
        if not self.hibp_api_key:
            return []

        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {
            'hibp-api-key': self.hibp_api_key,
            'user-agent': 'DeepTrace-OSINT'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                breaches = response.json()
                logger.info(f"HIBP: {email} found in {len(breaches)} breaches")
                return breaches
            elif response.status_code == 404:
                logger.info(f"HIBP: {email} not found in any breaches")
                return []
            else:
                logger.warning(f"HIBP API returned {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"HIBP breach check failed: {e}")
            return []

    def _check_hibp_pastes(self, email: str) -> List[dict]:
        """
        Query haveibeenpwned for paste exposures.

        Args:
            email: Email to check

        Returns:
            List of paste dictionaries
        """
        if not self.hibp_api_key:
            return []

        url = f"https://haveibeenpwned.com/api/v3/pasteaccount/{email}"
        headers = {
            'hibp-api-key': self.hibp_api_key,
            'user-agent': 'DeepTrace-OSINT'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                pastes = response.json()
                logger.info(f"HIBP: {email} found in {len(pastes)} pastes")
                return pastes
            elif response.status_code == 404:
                return []
            else:
                logger.warning(f"HIBP paste API returned {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"HIBP paste check failed: {e}")
            return []

    def _check_gravatar(self, email: str) -> Optional[dict]:
        """
        Check if email has a Gravatar profile (passive).

        Uses MD5 hash of email to query Gravatar API.
        This is passive - no notification sent to target.

        Args:
            email: Email to check

        Returns:
            Gravatar profile data or None
        """
        try:
            # Generate Gravatar hash (MD5 of lowercase trimmed email)
            email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
            profile_url = f"https://www.gravatar.com/{email_hash}.json"

            response = requests.get(profile_url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data and 'entry' in data and len(data['entry']) > 0:
                    profile = data['entry'][0]
                    logger.info(f"Gravatar profile found for {email}")
                    return {
                        'profile_url': f"https://www.gravatar.com/{email_hash}",
                        'displayName': profile.get('displayName'),
                        'thumbnailUrl': profile.get('thumbnailUrl'),
                        'urls': [url.get('value') for url in profile.get('urls', [])],
                        'accounts': profile.get('accounts', [])
                    }
            return None

        except Exception as e:
            logger.debug(f"Gravatar check failed: {e}")
            return None

    def _check_hunter_io(self, email: str) -> Optional[dict]:
        """
        Query Hunter.io for email information.

        API: https://hunter.io/api-documentation/v2#email-verifier

        Args:
            email: Email to verify

        Returns:
            Hunter.io data or None
        """
        if not self.hunter_api_key:
            return None

        url = "https://api.hunter.io/v2/email-verifier"
        params = {
            'email': email,
            'api_key': self.hunter_api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json().get('data', {})
                logger.info(f"Hunter.io result for {email}: {data.get('result')}")
                return {
                    'result': data.get('result'),  # deliverable/undeliverable/risky
                    'score': data.get('score'),  # 0-100
                    'company': data.get('sources', [{}])[0].get('domain') if data.get('sources') else None,
                    'verified': data.get('result') == 'deliverable',
                    'sources': data.get('sources', [])
                }
            else:
                logger.warning(f"Hunter.io returned {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Hunter.io check failed: {e}")
            return None
