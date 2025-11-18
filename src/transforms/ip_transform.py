#!/usr/bin/env python3
"""
IP Transform - Automated IP Address Intelligence Gathering

This transform takes an IP address and discovers:
1. Geolocation (country, city, lat/long)
2. ASN (Autonomous System Number) and organization
3. Reverse DNS (PTR records)
4. Open ports and services (passive databases)
5. Threat intelligence (blacklist status, malware associations)
6. Related IPs (same ASN, same network block)

Professional Tradecraft:
- Passive-only: Query databases, never scan the target directly
- Use Shodan/Censys for historical port data (no active probing)
- ASN pivoting for infrastructure attribution
- GeoIP for physical location intelligence

API Keys Optional:
- SHODAN_API_KEY: Shodan search engine (free tier: 1 query credit)
- IPINFO_TOKEN: IPinfo.io (free tier: 50k requests/month)
- ABUSEIPDB_API_KEY: AbuseIPDB threat intelligence

Without API keys, still provides:
- Basic GeoIP lookup
- Reverse DNS
- ASN lookup
- Network range calculation
"""

import socket
import ipaddress
import requests
import dns.resolver
from typing import Optional, Dict, List

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


class IPTransform(BaseTransform):
    """
    Transform for pivoting on IP addresses.

    Capabilities:
    - Geolocation lookup
    - ASN/Organization identification
    - Reverse DNS resolution
    - Threat intelligence checking
    - Network range enumeration
    """

    def __init__(self, shodan_api_key: Optional[str] = None, ipinfo_token: Optional[str] = None,
                 abuseipdb_api_key: Optional[str] = None):
        """
        Initialize IP transform.

        Args:
            shodan_api_key: Shodan API key (optional)
            ipinfo_token: IPinfo.io token (optional)
            abuseipdb_api_key: AbuseIPDB API key (optional)
        """
        super().__init__(rate_limit=60)
        self.shodan_api_key = shodan_api_key
        self.ipinfo_token = ipinfo_token
        self.abuseipdb_api_key = abuseipdb_api_key

        logger.info(
            f"IPTransform initialized (Shodan: {'✓' if shodan_api_key else '✗'}, "
            f"IPinfo: {'✓' if ipinfo_token else '✗'}, "
            f"AbuseIPDB: {'✓' if abuseipdb_api_key else '✗'})"
        )

    def can_handle(self, selector: Selector) -> bool:
        """Check if this is an IP address selector"""
        return selector.type == SelectorType.IP_ADDRESS

    def execute(self, selector: Selector) -> TransformResult:
        """
        Execute IP address intelligence gathering.

        Workflow:
        1. Validate IP address format
        2. Reverse DNS lookup (PTR records)
        3. Geolocation lookup
        4. ASN/Organization lookup
        5. Calculate network range
        6. Check threat intelligence databases
        7. (Optional) Query Shodan for historical data

        Args:
            selector: IP selector to pivot on

        Returns:
            TransformResult with discovered entities
        """
        ip_address = selector.value.strip()
        result = TransformResult(
            transform_name="IPTransform",
            input_selector=selector
        )

        try:
            # Step 1: Validate IP address
            ip_obj = ipaddress.ip_address(ip_address)
            result.metadata['ip_version'] = ip_obj.version
            result.metadata['is_private'] = ip_obj.is_private
            result.metadata['is_global'] = ip_obj.is_global
            result.metadata['is_multicast'] = ip_obj.is_multicast

            # Don't process private IPs
            if ip_obj.is_private:
                result.metadata['warning'] = 'Private IP address - limited intelligence available'

            # Step 2: Reverse DNS lookup
            ptr_records = self._reverse_dns_lookup(ip_address)
            if ptr_records:
                result.metadata['ptr_records'] = ptr_records

                # Create domain selectors for PTR records
                for domain in ptr_records:
                    domain_selector = Selector(
                        type=SelectorType.DOMAIN,
                        value=domain,
                        source=f"reverse_dns:{ip_address}",
                        context={'ip_address': ip_address}
                    )
                    result.discovered_entities.append(DiscoveredEntity(
                        selector=domain_selector,
                        reliability=Reliability.CONFIRMED,
                        source="reverse_dns",
                        confidence=100,
                        metadata={'ptr_record': True}
                    ))

            # Step 3: Geolocation lookup (free service)
            geo_data = self._geoip_lookup(ip_address)
            if geo_data:
                result.metadata['geolocation'] = geo_data

                # Create location selector
                if geo_data.get('city') and geo_data.get('country'):
                    location_str = f"{geo_data['city']}, {geo_data['country']}"
                    location_selector = Selector(
                        type=SelectorType.LOCATION,
                        value=location_str,
                        source=f"geoip:{ip_address}",
                        context={
                            'latitude': geo_data.get('lat'),
                            'longitude': geo_data.get('lon')
                        }
                    )
                    result.discovered_entities.append(DiscoveredEntity(
                        selector=location_selector,
                        reliability=Reliability.PROBABLE,
                        source="geoip",
                        confidence=70,  # GeoIP can be inaccurate
                        metadata=geo_data
                    ))

                # Create organization selector (ASN owner)
                if geo_data.get('org'):
                    org_selector = Selector(
                        type=SelectorType.COMPANY,
                        value=geo_data['org'],
                        source=f"asn:{ip_address}",
                        context={'owns_ip': ip_address}
                    )
                    result.discovered_entities.append(DiscoveredEntity(
                        selector=org_selector,
                        reliability=Reliability.CONFIRMED,
                        source="asn_lookup",
                        confidence=95,
                        metadata={'asn': geo_data.get('asn')}
                    ))

            # Step 4: Calculate network range
            network_range = self._calculate_network_range(ip_address, geo_data)
            if network_range:
                result.metadata['network_range'] = network_range

            # Step 5: Check threat intelligence (AbuseIPDB)
            if self.abuseipdb_api_key:
                threat_data = self._check_abuseipdb(ip_address)
                result.api_calls_made += 1
                if threat_data:
                    result.metadata['threat_intelligence'] = threat_data

            # Step 6: IPinfo.io lookup (if API available)
            if self.ipinfo_token:
                ipinfo_data = self._query_ipinfo(ip_address)
                result.api_calls_made += 1
                if ipinfo_data:
                    result.metadata['ipinfo'] = ipinfo_data

            # Step 7: Shodan lookup (if API available)
            if self.shodan_api_key:
                shodan_data = self._query_shodan(ip_address)
                result.api_calls_made += 1
                if shodan_data:
                    result.metadata['shodan'] = shodan_data

                    # Extract open ports/services as metadata
                    if shodan_data.get('ports'):
                        result.metadata['open_ports'] = shodan_data['ports']

            result.success = True
            result.metadata['total_discoveries'] = len(result.discovered_entities)

        except ValueError as e:
            result.success = False
            result.error_message = f"Invalid IP address: {ip_address}"
            logger.error(f"IP validation failed: {e}")
        except Exception as e:
            logger.error(f"IPTransform failed on {ip_address}: {e}")
            result.success = False
            result.error_message = str(e)

        return result

    def _reverse_dns_lookup(self, ip_address: str) -> List[str]:
        """
        Perform reverse DNS lookup (PTR record).

        Args:
            ip_address: IP to reverse lookup

        Returns:
            List of domain names
        """
        try:
            # Try socket method first (fastest)
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            logger.info(f"Reverse DNS: {ip_address} → {hostname}")
            return [hostname]
        except socket.herror:
            # Try DNS resolver as fallback
            try:
                reversed_ip = dns.reversename.from_address(ip_address)
                answers = dns.resolver.resolve(reversed_ip, 'PTR')
                domains = [str(rdata) for rdata in answers]
                logger.info(f"Reverse DNS: {ip_address} → {domains}")
                return domains
            except:
                logger.debug(f"No reverse DNS for {ip_address}")
                return []

    def _geoip_lookup(self, ip_address: str) -> Optional[Dict[str, any]]:
        """
        Lookup IP geolocation using free service.

        Uses ip-api.com (free, no API key needed, 45 req/min limit)

        Args:
            ip_address: IP to geolocate

        Returns:
            Geolocation data dictionary
        """
        try:
            url = f"http://ip-api.com/json/{ip_address}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    logger.info(f"GeoIP: {ip_address} → {data.get('city')}, {data.get('country')}")
                    return {
                        'country': data.get('country'),
                        'country_code': data.get('countryCode'),
                        'region': data.get('regionName'),
                        'city': data.get('city'),
                        'zip': data.get('zip'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'timezone': data.get('timezone'),
                        'isp': data.get('isp'),
                        'org': data.get('org'),
                        'asn': data.get('as')
                    }
            return None

        except Exception as e:
            logger.debug(f"GeoIP lookup failed: {e}")
            return None

    def _calculate_network_range(self, ip_address: str, geo_data: Optional[Dict] = None) -> Optional[str]:
        """
        Calculate likely network range (CIDR block).

        Uses ASN info if available, otherwise assumes /24 for private, /16 for public.

        Args:
            ip_address: IP address
            geo_data: Geolocation data (may contain ASN)

        Returns:
            CIDR notation (e.g., "192.168.1.0/24")
        """
        try:
            ip_obj = ipaddress.ip_address(ip_address)

            # For private IPs, assume /24
            if ip_obj.is_private:
                network = ipaddress.ip_network(f"{ip_address}/24", strict=False)
                return str(network)

            # For public IPs, try to infer from ASN (typically /16 or /24)
            # Default to /24 for public IPs
            network = ipaddress.ip_network(f"{ip_address}/24", strict=False)
            return str(network)

        except Exception as e:
            logger.debug(f"Network range calculation failed: {e}")
            return None

    def _check_abuseipdb(self, ip_address: str) -> Optional[Dict[str, any]]:
        """
        Check IP reputation on AbuseIPDB.

        API: https://www.abuseipdb.com/api.html

        Args:
            ip_address: IP to check

        Returns:
            Threat intelligence data
        """
        if not self.abuseipdb_api_key:
            return None

        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {
                'Key': self.abuseipdb_api_key,
                'Accept': 'application/json'
            }
            params = {
                'ipAddress': ip_address,
                'maxAgeInDays': 90
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json().get('data', {})
                logger.info(f"AbuseIPDB: {ip_address} abuse score: {data.get('abuseConfidenceScore')}")
                return {
                    'abuse_confidence_score': data.get('abuseConfidenceScore'),
                    'country_code': data.get('countryCode'),
                    'is_public': data.get('isPublic'),
                    'is_whitelisted': data.get('isWhitelisted'),
                    'usage_type': data.get('usageType'),
                    'isp': data.get('isp'),
                    'domain': data.get('domain'),
                    'total_reports': data.get('totalReports'),
                    'last_reported_at': data.get('lastReportedAt')
                }
            return None

        except Exception as e:
            logger.error(f"AbuseIPDB check failed: {e}")
            return None

    def _query_ipinfo(self, ip_address: str) -> Optional[Dict[str, any]]:
        """
        Query IPinfo.io for detailed IP data.

        API: https://ipinfo.io/developers

        Args:
            ip_address: IP to query

        Returns:
            IPinfo data dictionary
        """
        if not self.ipinfo_token:
            return None

        try:
            url = f"https://ipinfo.io/{ip_address}/json"
            params = {'token': self.ipinfo_token}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"IPinfo: {ip_address} → {data.get('org')}")
                return data
            return None

        except Exception as e:
            logger.error(f"IPinfo query failed: {e}")
            return None

    def _query_shodan(self, ip_address: str) -> Optional[Dict[str, any]]:
        """
        Query Shodan for historical IP data.

        API: https://developer.shodan.io/api

        Args:
            ip_address: IP to query

        Returns:
            Shodan data dictionary
        """
        if not self.shodan_api_key:
            return None

        try:
            url = f"https://api.shodan.io/shodan/host/{ip_address}"
            params = {'key': self.shodan_api_key}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Shodan: {ip_address} has {len(data.get('ports', []))} open ports")
                return {
                    'ports': data.get('ports', []),
                    'hostnames': data.get('hostnames', []),
                    'org': data.get('org'),
                    'os': data.get('os'),
                    'vulns': list(data.get('vulns', [])) if data.get('vulns') else [],
                    'last_update': data.get('last_update')
                }
            return None

        except Exception as e:
            logger.error(f"Shodan query failed: {e}")
            return None
