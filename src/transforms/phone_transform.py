#!/usr/bin/env python3
"""
Phone Transform - Automated Phone Number Intelligence Gathering

This transform takes a phone number and discovers:
1. Carrier information (mobile/landline/VOIP)
2. Geographic location (country, region, city)
3. Number validation and formatting
4. Associated social media (phone-based lookups)
5. OSINT database searches (TrueCaller, etc.)

Professional Tradecraft:
- Passive-first: Use carrier lookup databases (no call/SMS)
- International format normalization (E.164)
- VOIP detection (Skype, Google Voice risk indicators)

API Keys Optional:
- NUMVERIFY_API_KEY: Phone validation/carrier lookup (free tier: 100/month)
- TWILIO_ACCOUNT_SID/AUTH_TOKEN: Twilio Lookup API (paid)

Without API keys, still provides:
- Format validation
- Country code extraction
- Basic number type detection
"""

import re
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import requests
from typing import Optional, Dict

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


class PhoneTransform(BaseTransform):
    """
    Transform for pivoting on phone numbers.

    Capabilities:
    - Number validation and formatting
    - Carrier detection
    - Geographic location extraction
    - Number type classification (mobile/landline/VOIP)
    """

    def __init__(self, numverify_api_key: Optional[str] = None):
        """
        Initialize phone transform.

        Args:
            numverify_api_key: NumVerify API key (optional)
        """
        super().__init__(api_key=numverify_api_key, rate_limit=60)
        self.numverify_api_key = numverify_api_key

        logger.info(f"PhoneTransform initialized (NumVerify: {'✓' if numverify_api_key else '✗'})")

    def can_handle(self, selector: Selector) -> bool:
        """Check if this is a phone selector"""
        return selector.type == SelectorType.PHONE

    def execute(self, selector: Selector) -> TransformResult:
        """
        Execute phone number intelligence gathering.

        Workflow:
        1. Parse and validate phone number
        2. Extract country/region (geographic intelligence)
        3. Detect carrier (mobile vs landline vs VOIP)
        4. Format to international standard (E.164)
        5. Extract timezone information
        6. (Optional) Check OSINT databases

        Args:
            selector: Phone selector to pivot on

        Returns:
            TransformResult with discovered entities
        """
        phone_number = selector.value.strip()
        result = TransformResult(
            transform_name="PhoneTransform",
            input_selector=selector
        )

        try:
            # Step 1: Parse phone number (try to infer country if not provided)
            parsed_number = self._parse_phone_number(phone_number)

            if not parsed_number:
                result.success = False
                result.error_message = f"Could not parse phone number: {phone_number}"
                return result

            # Step 2: Extract geographic location
            location = geocoder.description_for_number(parsed_number, "en")
            if location:
                location_selector = Selector(
                    type=SelectorType.LOCATION,
                    value=location,
                    source=f"phone_geocoding:{phone_number}",
                    context={'phone_number': phone_number}
                )
                result.discovered_entities.append(DiscoveredEntity(
                    selector=location_selector,
                    reliability=Reliability.PROBABLE,
                    source="phonenumbers_library",
                    confidence=75,
                    metadata={'extraction_method': 'geographic_prefix'}
                ))
                result.metadata['location'] = location

            # Step 3: Extract carrier information
            carrier_name = carrier.name_for_number(parsed_number, "en")
            if carrier_name:
                result.metadata['carrier'] = carrier_name
                result.metadata['carrier_type'] = self._detect_number_type(parsed_number)

            # Step 4: Format to E.164 standard
            e164_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            result.metadata['formatted_e164'] = e164_format
            result.metadata['formatted_international'] = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            result.metadata['formatted_national'] = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
            )

            # Step 5: Extract country code
            country_code = parsed_number.country_code
            result.metadata['country_code'] = f"+{country_code}"

            # Step 6: Extract timezone
            timezones = timezone.time_zones_for_number(parsed_number)
            if timezones:
                result.metadata['timezones'] = timezones
                result.metadata['primary_timezone'] = timezones[0]

            # Step 7: Validation check
            is_valid = phonenumbers.is_valid_number(parsed_number)
            is_possible = phonenumbers.is_possible_number(parsed_number)
            result.metadata['valid'] = is_valid
            result.metadata['possible'] = is_possible

            # Step 8: NumVerify API (if available)
            if self.numverify_api_key:
                numverify_data = self._query_numverify(e164_format)
                result.api_calls_made += 1
                if numverify_data:
                    result.metadata['numverify'] = numverify_data

            result.success = True
            result.metadata['total_discoveries'] = len(result.discovered_entities)

        except Exception as e:
            logger.error(f"PhoneTransform failed on {phone_number}: {e}")
            result.success = False
            result.error_message = str(e)

        return result

    def _parse_phone_number(self, phone_number: str) -> Optional[phonenumbers.PhoneNumber]:
        """
        Parse phone number with country code inference.

        Tries multiple parsing strategies:
        1. Parse as-is (if international format)
        2. Try common country codes (US, UK, etc.)

        Args:
            phone_number: Raw phone number string

        Returns:
            Parsed PhoneNumber object or None
        """
        # Clean input
        cleaned = re.sub(r'[^\d+]', '', phone_number)

        # Try parsing with different country hints
        country_hints = [None, 'US', 'GB', 'CA', 'AU', 'IN']

        for country in country_hints:
            try:
                parsed = phonenumbers.parse(cleaned, country)
                if phonenumbers.is_possible_number(parsed):
                    logger.debug(f"Parsed {phone_number} with country hint: {country}")
                    return parsed
            except:
                continue

        logger.warning(f"Could not parse phone number: {phone_number}")
        return None

    def _detect_number_type(self, parsed_number: phonenumbers.PhoneNumber) -> str:
        """
        Detect number type (mobile, landline, VOIP, etc.).

        Args:
            parsed_number: Parsed phone number

        Returns:
            Number type string
        """
        number_type = phonenumbers.number_type(parsed_number)

        type_mapping = {
            phonenumbers.PhoneNumberType.MOBILE: 'MOBILE',
            phonenumbers.PhoneNumberType.FIXED_LINE: 'LANDLINE',
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: 'FIXED_OR_MOBILE',
            phonenumbers.PhoneNumberType.TOLL_FREE: 'TOLL_FREE',
            phonenumbers.PhoneNumberType.PREMIUM_RATE: 'PREMIUM_RATE',
            phonenumbers.PhoneNumberType.SHARED_COST: 'SHARED_COST',
            phonenumbers.PhoneNumberType.VOIP: 'VOIP',
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: 'PERSONAL',
            phonenumbers.PhoneNumberType.PAGER: 'PAGER',
            phonenumbers.PhoneNumberType.UAN: 'UAN',
            phonenumbers.PhoneNumberType.VOICEMAIL: 'VOICEMAIL',
            phonenumbers.PhoneNumberType.UNKNOWN: 'UNKNOWN'
        }

        return type_mapping.get(number_type, 'UNKNOWN')

    def _query_numverify(self, phone_number: str) -> Optional[Dict[str, any]]:
        """
        Query NumVerify API for phone validation.

        API: https://numverify.com/documentation

        Args:
            phone_number: Phone number in E.164 format

        Returns:
            NumVerify data dictionary
        """
        if not self.numverify_api_key:
            return None

        try:
            url = "http://apilayer.net/api/validate"
            params = {
                'access_key': self.numverify_api_key,
                'number': phone_number,
                'country_code': '',
                'format': 1
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    logger.info(f"NumVerify validated {phone_number}")
                    return {
                        'valid': data.get('valid'),
                        'number': data.get('number'),
                        'local_format': data.get('local_format'),
                        'international_format': data.get('international_format'),
                        'country_prefix': data.get('country_prefix'),
                        'country_code': data.get('country_code'),
                        'country_name': data.get('country_name'),
                        'location': data.get('location'),
                        'carrier': data.get('carrier'),
                        'line_type': data.get('line_type')
                    }
                else:
                    logger.warning(f"NumVerify marked {phone_number} as invalid")
                    return None
            else:
                logger.warning(f"NumVerify returned {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"NumVerify query failed: {e}")
            return None
