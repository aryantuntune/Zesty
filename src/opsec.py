#!/usr/bin/env python3
"""
Operational Security (OpSec) Warning System

Alerts analysts when investigation actions may compromise operational security
or leave traces that notify the target.

Professional OSINT Tradecraft:
- PASSIVE: Safe, no target notification (DNS queries, breach database checks)
- ACTIVE: Leaves logs on target systems (HTTP requests, port scans)
- DESTRUCTIVE: Never used in OSINT (exploitation, DoS attacks)

This module classifies all investigation techniques and warns before active probing.
"""

from enum import Enum
from typing import List, Dict
from .utils import setup_logger

logger = setup_logger(__name__)


class OpSecLevel(Enum):
    """Operation security levels"""
    PASSIVE = "PASSIVE"      # No contact with target
    SEMI_PASSIVE = "SEMI_PASSIVE"  # Third-party queries (may be logged)
    ACTIVE = "ACTIVE"        # Direct target contact (leaves logs)
    DESTRUCTIVE = "DESTRUCTIVE"  # Never use in OSINT


class OpSecWarning:
    """Operational security warning system"""

    def __init__(self):
        """Initialize OpSec classifier"""

        # Classify investigation techniques by OpSec level
        self.technique_classification = {
            # PASSIVE (Safe - no target contact)
            'passive_dns_lookup': OpSecLevel.PASSIVE,
            'whois_query': OpSecLevel.PASSIVE,
            'breach_database_check': OpSecLevel.PASSIVE,
            'google_dorking': OpSecLevel.PASSIVE,
            'certificate_transparency': OpSecLevel.PASSIVE,
            'shodan_lookup': OpSecLevel.PASSIVE,  # Historical data only
            'geoip_lookup': OpSecLevel.PASSIVE,

            # SEMI-PASSIVE (Third-party, may be logged elsewhere)
            'sherlock_enumeration': OpSecLevel.SEMI_PASSIVE,  # Hits platforms
            'hunter_io_lookup': OpSecLevel.SEMI_PASSIVE,
            'wayback_machine': OpSecLevel.SEMI_PASSIVE,

            # ACTIVE (Leaves logs on target)
            'http_request_to_profile': OpSecLevel.ACTIVE,
            'selenium_scraping': OpSecLevel.ACTIVE,
            'api_call_to_platform': OpSecLevel.ACTIVE,
            'email_validation_smtp': OpSecLevel.ACTIVE,  # Triggers SMTP logs
            'port_scan': OpSecLevel.ACTIVE,  # Never use this
            'vulnerability_scan': OpSecLevel.DESTRUCTIVE  # NEVER use

        }

    def get_technique_level(self, technique: str) -> OpSecLevel:
        """Get OpSec level for a technique"""
        return self.technique_classification.get(
            technique,
            OpSecLevel.ACTIVE  # Default to ACTIVE (safest assumption)
        )

    def warn_before_action(self, technique: str) -> Dict:
        """
        Generate warning before performing action.

        Args:
            technique: Name of investigation technique

        Returns:
            Dict with warning info
        """
        level = self.get_technique_level(technique)

        warning = {
            'technique': technique,
            'level': level.value,
            'safe': level in [OpSecLevel.PASSIVE, OpSecLevel.SEMI_PASSIVE],
            'message': '',
            'recommendation': ''
        }

        if level == OpSecLevel.PASSIVE:
            warning['message'] = f"✅ PASSIVE: {technique} is safe (no target contact)"
            warning['recommendation'] = "Proceed without OpSec concerns"

        elif level == OpSecLevel.SEMI_PASSIVE:
            warning['message'] = f"⚠️  SEMI-PASSIVE: {technique} contacts third parties"
            warning['recommendation'] = "Low risk but may appear in third-party logs"

        elif level == OpSecLevel.ACTIVE:
            warning['message'] = f"🔴 ACTIVE: {technique} will contact target directly"
            warning['recommendation'] = ("⚠️  WARNING: This action will leave logs on target's server "
                                       "(IP address, timestamp, user-agent). Consider: "
                                       "(1) Use VPN/proxy, (2) Use disposable VM, "
                                       "(3) Check if passive alternative exists.")

        elif level == OpSecLevel.DESTRUCTIVE:
            warning['message'] = f"❌ DESTRUCTIVE: {technique} is PROHIBITED"
            warning['recommendation'] = "NEVER use destructive techniques in OSINT investigations"

        return warning

    def get_passive_alternatives(self, technique: str) -> List[str]:
        """
        Suggest passive alternatives to active techniques.

        Args:
            technique: Active technique being considered

        Returns:
            List of passive alternatives
        """
        alternatives = {
            'http_request_to_profile': [
                'Use cached data from Wayback Machine',
                'Use Sherlock (checks are distributed across many IPs)',
                'Search for leaked/archived profile data in breach databases'
            ],
            'selenium_scraping': [
                'Use cached screenshots from archive sites',
                'Use third-party APIs (Hunter.io, Pipl, etc.)',
                'Check if profile is indexed in search engines (Google Cache)'
            ],
            'email_validation_smtp': [
                'Use haveibeenpwned for breach presence (confirms existence)',
                'Check MX records only (passive DNS query)',
                'Use Hunter.io email verifier (third-party)'
            ],
            'port_scan': [
                'Use Shodan/Censys historical data (already scanned)',
                'Use passive DNS to find infrastructure',
                'Query certificate transparency logs for SSL/TLS info'
            ]
        }

        return alternatives.get(technique, ["No passive alternative available - proceed with caution"])

    def generate_opsec_report(self, techniques_used: List[str]) -> str:
        """
        Generate OpSec report for investigation.

        Args:
            techniques_used: List of techniques used in investigation

        Returns:
            Formatted OpSec report
        """
        report = "="*70 + "\n"
        report += "OPERATIONAL SECURITY (OPSEC) REPORT\n"
        report += "="*70 + "\n\n"

        # Count by level
        passive_count = 0
        semi_passive_count = 0
        active_count = 0

        for technique in techniques_used:
            level = self.get_technique_level(technique)
            if level == OpSecLevel.PASSIVE:
                passive_count += 1
            elif level == OpSecLevel.SEMI_PASSIVE:
                semi_passive_count += 1
            elif level == OpSecLevel.ACTIVE:
                active_count += 1

        report += f"📊 Investigation Footprint:\n"
        report += f"   • PASSIVE techniques: {passive_count}\n"
        report += f"   • SEMI-PASSIVE techniques: {semi_passive_count}\n"
        report += f"   • ACTIVE techniques: {active_count}\n\n"

        if active_count > 0:
            report += "⚠️  WARNING: Active techniques used. Target may be aware of investigation.\n"
            report += "   Recommended: Review logs, use VPN, consider operational security protocol.\n\n"
        else:
            report += "✅ All techniques were passive or semi-passive. Low risk of target notification.\n\n"

        report += "Detailed Breakdown:\n"
        for technique in techniques_used:
            level = self.get_technique_level(technique)
            report += f"   • {technique}: {level.value}\n"

        report += "\n" + "="*70 + "\n"

        return report
