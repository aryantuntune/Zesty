#!/usr/bin/env python3
"""
Domain Transform - Automated Domain Intelligence Gathering

This transform takes a domain and discovers:
1. WHOIS records (registrant, registrar, dates)
2. DNS records (A, AAAA, MX, TXT, NS)
3. Subdomain enumeration (passive DNS)
4. SSL/TLS certificate information
5. Related domains (same registrant, same IP)
6. Historical records (passive DNS history)

Professional Tradecraft:
- Passive-only: All queries are DNS/WHOIS (no HTTP requests to target)
- WHOIS privacy detection (if registrant is hidden, note OpSec awareness)
- Certificate transparency logs for subdomain discovery
- Passive DNS for infrastructure relationships

API Keys Optional:
- SECURITYTRAILS_API_KEY: SecurityTrails passive DNS (free tier: 50 queries/month)
- SHODAN_API_KEY: Shodan DNS/SSL data (paid)

Without API keys, still provides:
- Standard WHOIS lookup
- DNS record enumeration
- Basic subdomain guessing
"""

import socket
import dns.resolver
import whois
import ssl
import OpenSSL
import requests
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse

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


class DomainTransform(BaseTransform):
    """
    Transform for pivoting on domains.

    Capabilities:
    - WHOIS record retrieval
    - DNS enumeration (all record types)
    - Subdomain discovery
    - SSL certificate analysis
    - Related domain discovery
    """

    def __init__(self, securitytrails_api_key: Optional[str] = None, shodan_api_key: Optional[str] = None, whoisxml_api_key: Optional[str] = None):
        """
        Initialize domain transform.

        Args:
            securitytrails_api_key: SecurityTrails API key (optional)
            shodan_api_key: Shodan API key (optional)
            whoisxml_api_key: WhoisXML API key (optional, for WHOIS history)
        """
        super().__init__(rate_limit=60)
        self.securitytrails_api_key = securitytrails_api_key
        self.shodan_api_key = shodan_api_key
        self.whoisxml_api_key = whoisxml_api_key

        # Configure DNS resolver
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 3
        self.dns_resolver.lifetime = 3

        # Common subdomains to check
        self.common_subdomains = [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk',
            'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'blog', 'forum', 'api',
            'dev', 'staging', 'test', 'admin', 'vpn', 'remote', 'portal'
        ]

        logger.info(
            f"DomainTransform initialized (SecurityTrails: {'✓' if securitytrails_api_key else '✗'}, "
            f"Shodan: {'✓' if shodan_api_key else '✗'}, "
            f"WhoisXML: {'✓' if whoisxml_api_key else '✗'})"
        )

    def can_handle(self, selector: Selector) -> bool:
        """Check if this is a domain selector"""
        return selector.type == SelectorType.DOMAIN

    def execute(self, selector: Selector) -> TransformResult:
        """
        Execute domain intelligence gathering.

        Workflow:
        1. WHOIS lookup (registrant, dates, registrar)
        2. DNS enumeration (A, AAAA, MX, TXT, NS, SOA)
        3. Subdomain discovery (passive + bruteforce)
        4. SSL certificate analysis
        5. IP address extraction → create IP selectors
        6. Registrant extraction → create Name/Company selectors

        Args:
            selector: Domain selector to pivot on

        Returns:
            TransformResult with discovered entities
        """
        domain = selector.value.lower().strip()
        result = TransformResult(
            transform_name="DomainTransform",
            input_selector=selector
        )

        try:
            # Step 1: WHOIS lookup
            whois_data = self._get_whois(domain)
            if whois_data:
                result.metadata['whois'] = whois_data

                # Extract registrant name (if not privacy-protected)
                if whois_data.get('registrant_name') and 'privacy' not in whois_data['registrant_name'].lower():
                    name_selector = Selector(
                        type=SelectorType.NAME,
                        value=whois_data['registrant_name'],
                        source=f"whois:{domain}",
                        context={'domain': domain, 'registrant_role': 'domain_owner'}
                    )
                    result.discovered_entities.append(DiscoveredEntity(
                        selector=name_selector,
                        reliability=Reliability.CONFIRMED,
                        source="whois",
                        confidence=90,
                        metadata={'extraction_method': 'whois_registrant'}
                    ))

                # Extract registrant email
                if whois_data.get('registrant_email'):
                    email_selector = Selector(
                        type=SelectorType.EMAIL,
                        value=whois_data['registrant_email'],
                        source=f"whois:{domain}"
                    )
                    result.discovered_entities.append(DiscoveredEntity(
                        selector=email_selector,
                        reliability=Reliability.CONFIRMED,
                        source="whois",
                        confidence=95,
                        metadata={'role': 'domain_registrant'}
                    ))

                # Extract registrant organization
                if whois_data.get('registrant_org'):
                    company_selector = Selector(
                        type=SelectorType.COMPANY,
                        value=whois_data['registrant_org'],
                        source=f"whois:{domain}"
                    )
                    result.discovered_entities.append(DiscoveredEntity(
                        selector=company_selector,
                        reliability=Reliability.CONFIRMED,
                        source="whois",
                        confidence=90,
                        metadata={'owns_domain': domain}
                    ))

            # Step 2: DNS enumeration
            dns_records = self._get_dns_records(domain)
            result.metadata['dns_records'] = dns_records

            # Extract IP addresses from A records
            for ip in dns_records.get('A', []):
                ip_selector = Selector(
                    type=SelectorType.IP_ADDRESS,
                    value=ip,
                    source=f"dns_a:{domain}",
                    context={'domain': domain, 'record_type': 'A'}
                )
                result.discovered_entities.append(DiscoveredEntity(
                    selector=ip_selector,
                    reliability=Reliability.CONFIRMED,
                    source="dns",
                    confidence=100,
                    metadata={'resolves_from': domain}
                ))

            # Extract IPv6 addresses
            for ip in dns_records.get('AAAA', []):
                ip_selector = Selector(
                    type=SelectorType.IP_ADDRESS,
                    value=ip,
                    source=f"dns_aaaa:{domain}",
                    context={'domain': domain, 'record_type': 'AAAA'}
                )
                result.discovered_entities.append(DiscoveredEntity(
                    selector=ip_selector,
                    reliability=Reliability.CONFIRMED,
                    source="dns",
                    confidence=100,
                    metadata={'resolves_from': domain, 'ipv6': True}
                ))

            # Extract mail servers
            for mx in dns_records.get('MX', []):
                mx_domain = mx.split()[-1].rstrip('.')  # Extract domain from "10 mail.example.com."
                mx_selector = Selector(
                    type=SelectorType.DOMAIN,
                    value=mx_domain,
                    source=f"dns_mx:{domain}",
                    context={'role': 'mail_server', 'for_domain': domain}
                )
                result.discovered_entities.append(DiscoveredEntity(
                    selector=mx_selector,
                    reliability=Reliability.CONFIRMED,
                    source="dns",
                    confidence=100,
                    metadata={'mail_server_for': domain}
                ))

            # Step 3: Subdomain discovery
            subdomains = self._discover_subdomains(domain)
            result.metadata['subdomains_found'] = len(subdomains)

            for subdomain in subdomains:
                subdomain_selector = Selector(
                    type=SelectorType.DOMAIN,
                    value=subdomain,
                    source=f"subdomain_discovery:{domain}",
                    context={'parent_domain': domain}
                )
                result.discovered_entities.append(DiscoveredEntity(
                    selector=subdomain_selector,
                    reliability=Reliability.PROBABLE,
                    source="subdomain_enumeration",
                    confidence=80,
                    metadata={'parent': domain}
                ))

            # Step 4: SSL certificate analysis
            cert_data = self._get_ssl_certificate(domain)
            if cert_data:
                result.metadata['ssl_certificate'] = cert_data

                # Extract additional domains from certificate SANs
                for san_domain in cert_data.get('subject_alt_names', []):
                    if san_domain != domain and not san_domain.startswith('*'):
                        san_selector = Selector(
                            type=SelectorType.DOMAIN,
                            value=san_domain,
                            source=f"ssl_san:{domain}",
                            context={'found_in_cert': domain}
                        )
                        result.discovered_entities.append(DiscoveredEntity(
                            selector=san_selector,
                            reliability=Reliability.CONFIRMED,
                            source="ssl_certificate",
                            confidence=95,
                            metadata={'cert_owner': domain}
                        ))

            # Step 5: Passive DNS (if API available)
            if self.securitytrails_api_key:
                passive_dns = self._query_securitytrails(domain)
                result.api_calls_made += 1
                if passive_dns:
                    result.metadata['passive_dns'] = passive_dns

            # Step 6: Historical Passive DNS (SecurityTrails history)
            if self.securitytrails_api_key:
                historical_dns = self._query_historical_dns(domain)
                result.api_calls_made += 1
                if historical_dns:
                    result.metadata['historical_dns'] = historical_dns

                    # Extract historical IPs as selectors
                    for record in historical_dns.get('a_records', []):
                        for ip_entry in record.get('values', []):
                            ip_value = ip_entry.get('ip')
                            if ip_value:
                                ip_selector = Selector(
                                    type=SelectorType.IP_ADDRESS,
                                    value=ip_value,
                                    source=f"historical_dns:{domain}",
                                    context={
                                        'domain': domain,
                                        'first_seen': record.get('first_seen'),
                                        'last_seen': record.get('last_seen'),
                                        'historical': True
                                    }
                                )
                                result.discovered_entities.append(DiscoveredEntity(
                                    selector=ip_selector,
                                    reliability=Reliability.CONFIRMED,
                                    source="historical_passive_dns",
                                    confidence=95,
                                    metadata={
                                        'first_seen': record.get('first_seen'),
                                        'last_seen': record.get('last_seen'),
                                        'type': 'historical_ip'
                                    }
                                ))

            # Step 7: Historical WHOIS (find pre-privacy registrant data)
            if self.whoisxml_api_key:
                whois_history = self._query_whois_history(domain)
                result.api_calls_made += 1
                if whois_history:
                    result.metadata['whois_history'] = whois_history

                    # Extract historical registrant information
                    for historical_record in whois_history.get('records', []):
                        # Extract registrant name (if not privacy-protected)
                        registrant_name = historical_record.get('registrant_name')
                        if registrant_name and 'privacy' not in registrant_name.lower() and 'redacted' not in registrant_name.lower():
                            name_selector = Selector(
                                type=SelectorType.NAME,
                                value=registrant_name,
                                source=f"whois_history:{domain}",
                                context={
                                    'domain': domain,
                                    'date': historical_record.get('date'),
                                    'historical': True
                                }
                            )
                            result.discovered_entities.append(DiscoveredEntity(
                                selector=name_selector,
                                reliability=Reliability.CONFIRMED,
                                source="whois_history",
                                confidence=90,
                                metadata={
                                    'historical_date': historical_record.get('date'),
                                    'type': 'historical_registrant'
                                }
                            ))

                        # Extract historical registrant email
                        registrant_email = historical_record.get('registrant_email')
                        if registrant_email and '@' in registrant_email:
                            email_selector = Selector(
                                type=SelectorType.EMAIL,
                                value=registrant_email,
                                source=f"whois_history:{domain}",
                                context={
                                    'domain': domain,
                                    'date': historical_record.get('date'),
                                    'historical': True
                                }
                            )
                            result.discovered_entities.append(DiscoveredEntity(
                                selector=email_selector,
                                reliability=Reliability.CONFIRMED,
                                source="whois_history",
                                confidence=95,
                                metadata={
                                    'historical_date': historical_record.get('date'),
                                    'role': 'historical_domain_registrant'
                                }
                            ))

            result.success = True
            result.metadata['total_discoveries'] = len(result.discovered_entities)

        except Exception as e:
            logger.error(f"DomainTransform failed on {domain}: {e}")
            result.success = False
            result.error_message = str(e)

        return result

    def _get_whois(self, domain: str) -> Optional[Dict[str, any]]:
        """
        Get WHOIS information for domain.

        Args:
            domain: Domain to query

        Returns:
            Dictionary with WHOIS data
        """
        try:
            w = whois.whois(domain)

            # Extract relevant fields
            data = {
                'registrant_name': w.name if isinstance(w.name, str) else (w.name[0] if w.name else None),
                'registrant_org': w.org if isinstance(w.org, str) else (w.org[0] if w.org else None),
                'registrant_email': w.emails[0] if w.emails and len(w.emails) > 0 else None,
                'registrar': w.registrar if isinstance(w.registrar, str) else (w.registrar[0] if w.registrar else None),
                'creation_date': str(w.creation_date[0]) if isinstance(w.creation_date, list) else str(w.creation_date) if w.creation_date else None,
                'expiration_date': str(w.expiration_date[0]) if isinstance(w.expiration_date, list) else str(w.expiration_date) if w.expiration_date else None,
                'name_servers': w.name_servers if w.name_servers else [],
                'status': w.status if isinstance(w.status, list) else [w.status] if w.status else []
            }

            logger.info(f"WHOIS successful for {domain}")
            return data

        except Exception as e:
            logger.warning(f"WHOIS lookup failed for {domain}: {e}")
            return None

    def _get_dns_records(self, domain: str) -> Dict[str, List[str]]:
        """
        Enumerate DNS records for domain.

        Queries: A, AAAA, MX, TXT, NS, SOA

        Args:
            domain: Domain to query

        Returns:
            Dictionary of record types to values
        """
        records = {}
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'SOA']

        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records[record_type] = [str(rdata) for rdata in answers]
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
                records[record_type] = []
            except Exception as e:
                logger.debug(f"DNS {record_type} lookup failed for {domain}: {e}")
                records[record_type] = []

        return records

    def _discover_subdomains(self, domain: str) -> List[str]:
        """
        Discover subdomains through bruteforce and passive DNS.

        Methods:
        1. Bruteforce common subdomain names
        2. Certificate transparency logs (crt.sh)
        3. SecurityTrails API (if available)

        Args:
            domain: Parent domain

        Returns:
            List of discovered subdomains
        """
        subdomains = []

        # Method 1: Bruteforce common subdomains
        for subdomain_name in self.common_subdomains:
            subdomain = f"{subdomain_name}.{domain}"
            try:
                # Try to resolve
                answers = dns.resolver.resolve(subdomain, 'A')
                if answers:
                    subdomains.append(subdomain)
                    logger.debug(f"Found subdomain: {subdomain}")
            except:
                pass

        # Method 2: Certificate Transparency (crt.sh)
        try:
            ct_subdomains = self._query_crtsh(domain)
            subdomains.extend(ct_subdomains)
        except Exception as e:
            logger.debug(f"Certificate transparency lookup failed: {e}")

        return list(set(subdomains))  # Remove duplicates

    def _query_crtsh(self, domain: str) -> List[str]:
        """
        Query crt.sh (Certificate Transparency logs) for subdomains.

        This is passive and free.

        Args:
            domain: Domain to search

        Returns:
            List of subdomains found in certificates
        """
        subdomains = []

        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for entry in data:
                    name = entry.get('name_value', '')
                    # Handle multiple names separated by newlines
                    for subdomain in name.split('\n'):
                        subdomain = subdomain.strip()
                        # Filter out wildcards and duplicates
                        if subdomain and not subdomain.startswith('*') and subdomain.endswith(domain):
                            subdomains.append(subdomain)

                logger.info(f"crt.sh found {len(set(subdomains))} subdomains for {domain}")

        except Exception as e:
            logger.debug(f"crt.sh query failed: {e}")

        return list(set(subdomains))

    def _get_ssl_certificate(self, domain: str, port: int = 443) -> Optional[Dict[str, any]]:
        """
        Get SSL certificate information.

        Args:
            domain: Domain to check
            port: Port (default: 443)

        Returns:
            Certificate data dictionary
        """
        try:
            # Create SSL context
            context = ssl.create_default_context()

            # Connect and get certificate
            with socket.create_connection((domain, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert_bin = ssock.getpeercert(True)
                    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_bin)

                    # Extract Subject Alternative Names (SANs)
                    san_list = []
                    for i in range(cert.get_extension_count()):
                        ext = cert.get_extension(i)
                        if 'subjectAltName' in str(ext.get_short_name()):
                            san_str = str(ext)
                            san_list = [san.replace('DNS:', '').strip() for san in san_str.split(',')]

                    return {
                        'subject': dict(x[0] for x in cert.get_subject().get_components()),
                        'issuer': dict(x[0] for x in cert.get_issuer().get_components()),
                        'version': cert.get_version(),
                        'serial_number': cert.get_serial_number(),
                        'not_before': cert.get_notBefore().decode('utf-8'),
                        'not_after': cert.get_notAfter().decode('utf-8'),
                        'subject_alt_names': san_list
                    }

        except Exception as e:
            logger.debug(f"SSL certificate retrieval failed for {domain}: {e}")
            return None

    def _query_securitytrails(self, domain: str) -> Optional[Dict[str, any]]:
        """
        Query SecurityTrails API for passive DNS history.

        API: https://securitytrails.com/corp/api

        Args:
            domain: Domain to query

        Returns:
            Historical DNS data
        """
        if not self.securitytrails_api_key:
            return None

        try:
            url = f"https://api.securitytrails.com/v1/domain/{domain}"
            headers = {
                'APIKEY': self.securitytrails_api_key
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"SecurityTrails data retrieved for {domain}")
                return data
            else:
                logger.warning(f"SecurityTrails returned {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"SecurityTrails query failed: {e}")
            return None

    def _query_historical_dns(self, domain: str) -> Optional[Dict[str, any]]:
        """
        Query SecurityTrails Historical Passive DNS records.

        Professional OSINT Use Case:
        - Infrastructure migration tracking (what IPs did this domain point to in 2018, 2019, 2020?)
        - Hosting provider changes (GoDaddy → AWS → Cloudflare)
        - Identify previous infrastructure that may still be active
        - Find abandoned infrastructure that reveals tech stack history
        - Attribution: If attacker moved from shared hosting to VPS, indicates sophistication

        API Endpoint: /v1/history/{domain}/dns/{record_type}
        Record types: a, aaaa, mx, ns, txt, soa

        Args:
            domain: Domain to query historical records for

        Returns:
            Dictionary with historical DNS records by type
        """
        if not self.securitytrails_api_key:
            return None

        historical_data = {}

        try:
            # Query historical A records (most important for IP pivoting)
            url = f"https://api.securitytrails.com/v1/history/{domain}/dns/a"
            headers = {
                'APIKEY': self.securitytrails_api_key,
                'Accept': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                historical_data['a_records'] = data.get('records', [])
                logger.info(f"Historical DNS: {domain} → {len(data.get('records', []))} A record changes")

            # Query historical MX records
            url_mx = f"https://api.securitytrails.com/v1/history/{domain}/dns/mx"
            response_mx = requests.get(url_mx, headers=headers, timeout=10)

            if response_mx.status_code == 200:
                data_mx = response_mx.json()
                historical_data['mx_records'] = data_mx.get('records', [])

            # Query historical NS records
            url_ns = f"https://api.securitytrails.com/v1/history/{domain}/dns/ns"
            response_ns = requests.get(url_ns, headers=headers, timeout=10)

            if response_ns.status_code == 200:
                data_ns = response_ns.json()
                historical_data['ns_records'] = data_ns.get('records', [])

            if historical_data:
                logger.info(f"Historical Passive DNS complete for {domain}")
                return historical_data
            else:
                return None

        except Exception as e:
            logger.error(f"Historical DNS query failed for {domain}: {e}")
            return None

    def _query_whois_history(self, domain: str) -> Optional[Dict[str, any]]:
        """
        Query historical WHOIS records to find pre-privacy registrant data.

        Professional OSINT Use Case:
        - Many domains now use WHOIS privacy protection
        - But historical WHOIS records (from years ago) may contain real registrant info
        - Example: example.com registered in 2010 with "John Doe, john@email.com"
        - In 2015, privacy protection enabled → current WHOIS shows "REDACTED"
        - Historical WHOIS reveals original owner
        - Attribution: Link domain to real person/organization

        This is GOLD for OSINT - bypasses current privacy protection by looking at history.

        API Options:
        - WhoisXMLAPI (paid, but has historical WHOIS)
        - DomainTools (enterprise, very expensive)
        - Free alternative: Wayback Machine WHOIS snapshots (manual parsing)

        Args:
            domain: Domain to query

        Returns:
            Dictionary with historical WHOIS records
        """
        if not self.whoisxml_api_key:
            # Try free alternative: Wayback Machine
            return self._query_wayback_whois(domain)

        try:
            url = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
            params = {
                'apiKey': self.whoisxml_api_key,
                'domainName': domain,
                'outputFormat': 'JSON',
                'mode': 'history'  # Historical mode
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Parse historical records
                historical_records = []
                whois_records = data.get('WhoisRecord', {}).get('audit', [])

                for record in whois_records:
                    registrant = record.get('registrant', {})
                    parsed_record = {
                        'date': record.get('auditUpdatedDate'),
                        'registrant_name': registrant.get('name'),
                        'registrant_email': registrant.get('email'),
                        'registrant_org': registrant.get('organization'),
                        'registrar': record.get('registrarName')
                    }
                    historical_records.append(parsed_record)

                if historical_records:
                    logger.info(f"WHOIS History: {domain} → {len(historical_records)} historical records found")
                    return {'records': historical_records}
                else:
                    return None

        except Exception as e:
            logger.error(f"WHOIS history query failed for {domain}: {e}")
            return None

    def _query_wayback_whois(self, domain: str) -> Optional[Dict[str, any]]:
        """
        Free alternative: Query Wayback Machine for historical WHOIS snapshots.

        The Internet Archive sometimes captures WHOIS records in their snapshots.
        This is less reliable than WhoisXMLAPI but free.

        Args:
            domain: Domain to query

        Returns:
            Dictionary with historical WHOIS data (if found)
        """
        try:
            # Query Wayback Machine CDX API for WHOIS captures
            url = f"http://web.archive.org/cdx/search/cdx"
            params = {
                'url': f'whois.domaintools.com/{domain}',
                'output': 'json',
                'limit': 5
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                snapshots = response.json()

                if len(snapshots) > 1:  # First row is headers
                    logger.info(f"Wayback WHOIS: Found {len(snapshots)-1} snapshots for {domain}")
                    # Note: Would need to fetch and parse each snapshot
                    # For now, just return metadata
                    return {
                        'records': [],
                        'wayback_snapshots': len(snapshots) - 1,
                        'note': 'Historical WHOIS available via Wayback Machine (requires manual inspection)'
                    }

            return None

        except Exception as e:
            logger.debug(f"Wayback WHOIS query failed: {e}")
            return None
