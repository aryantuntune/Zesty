"""
Professional OSINT Intelligence Report Generator
Formats findings as actionable intelligence dossiers with risk assessment
"""

from typing import Dict, List, Tuple
from datetime import datetime
from collections import Counter
import re

try:
    from .utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class IntelligenceReportGenerator:
    """
    Generates professional OSINT intelligence reports with:
    - TLP classification
    - Threat assessment
    - Vulnerability analysis
    - Pattern of Life (POL)
    - Risk scoring
    - Actionable recommendations
    """

    def __init__(self):
        self.classification_levels = {
            'RED': 'Personal Use Only - Do Not Share',
            'AMBER': 'Limited Disclosure - Need to Know',
            'GREEN': 'Community Sharing Permitted',
            'WHITE': 'Unlimited Distribution'
        }

    def generate_dossier(
        self,
        target_name: str,
        accounts: List[Dict],
        behavioral_profiles: List[Dict],
        temporal_patterns: List[Dict],
        graph_metrics: Dict,
        nlp_results: List[Dict],
        investigation_id: int,
        pivot_result=None,
        verification_results=None,
        adverse_results=None,
        opsec_report=None
    ) -> str:
        """
        Generate complete intelligence dossier

        Args:
            target_name: Subject's name
            accounts: Enriched account data
            behavioral_profiles: Behavioral analysis results
            temporal_patterns: Temporal analysis results
            graph_metrics: Network analysis results
            nlp_results: NLP entity extraction results
            investigation_id: Investigation ID
            pivot_result: Automated pivot discoveries (optional)
            verification_results: 3-source verification results (optional)
            adverse_results: Adverse inference analysis (optional)
            opsec_report: Operational security assessment (optional)

        Returns:
            Formatted intelligence report (markdown)
        """
        report = []

        # Header
        report.append(self._generate_header(target_name, investigation_id))

        # Executive Summary
        threat_level, summary = self._generate_executive_summary(
            target_name, accounts, behavioral_profiles, temporal_patterns
        )
        report.append(summary)

        # Subject Profile (PII)
        report.append(self._generate_subject_profile(target_name, accounts, nlp_results))

        # Digital Footprint Analysis
        report.append(self._generate_digital_footprint(accounts))

        # Pattern of Life
        report.append(self._generate_pattern_of_life(accounts, temporal_patterns, behavioral_profiles))

        # Vulnerability Assessment
        report.append(self._generate_vulnerability_assessment(accounts, target_name))

        # Network Analysis
        report.append(self._generate_network_analysis(graph_metrics, accounts))

        # Pivot Intelligence (if available)
        if pivot_result:
            report.append(self._generate_pivot_intelligence(pivot_result))

        # 3-Source Verification (if available)
        if verification_results:
            report.append(self._generate_verification_section(verification_results))

        # Adverse Inference Analysis (if available)
        if adverse_results:
            report.append(self._generate_adverse_inference_section(adverse_results))

        # OpSec Assessment (if available)
        if opsec_report:
            report.append(self._generate_opsec_section(opsec_report))

        # Strategic Recommendations
        report.append(self._generate_recommendations(accounts, threat_level))

        # Evidence Log
        report.append(self._generate_evidence_log(accounts))

        return '\n\n'.join(report)

    def _generate_header(self, target_name: str, investigation_id: int) -> str:
        """Generate report header with TLP classification"""
        timestamp = datetime.now().strftime('%d %b %Y %H:%M UTC')

        return f"""# INTELLIGENCE DOSSIER: SUBJECT ASSESSMENT

**PROJECT CODE:** DEEPTRACE-{investigation_id}
**DATE:** {timestamp}
**CLASSIFICATION:** TLP:AMBER (Limited Disclosure)
**PREPARED BY:** DeepTrace Advanced OSINT Unit
**STATUS:** FINAL

---"""

    def _generate_executive_summary(
        self,
        target_name: str,
        accounts: List[Dict],
        behavioral_profiles: List[Dict],
        temporal_patterns: List[Dict]
    ) -> Tuple[str, str]:
        """Generate executive summary with threat assessment"""

        # Calculate threat level
        threat_level, risk_factors = self._calculate_threat_level(accounts, behavioral_profiles)

        # Platform breakdown
        platform_counts = Counter(acc.get('platform', 'unknown') for acc in accounts if acc)
        primary_platforms = [f"{platform} ({count})" for platform, count in platform_counts.most_common(3)]

        # Exposure assessment
        public_accounts = sum(1 for acc in accounts if acc and not acc.get('private', False))
        exposure_pct = (public_accounts / max(len(accounts), 1)) * 100

        # Extract key insights
        total_posts = sum(len(acc.get('posts', [])) for acc in accounts if acc)
        has_location = any(acc.get('location') for acc in accounts if acc)
        has_timestamps = any(p.get('has_temporal_data', False) for p in temporal_patterns if p)

        summary = f"""## 1. EXECUTIVE SUMMARY

**Subject:** {target_name}
**Threat Level:** **{threat_level}** ({', '.join(risk_factors[:2]) if risk_factors else 'Standard Profile'})

**Synopsis:**
The subject maintains a digital footprint across {len(accounts)} verified platforms. Primary presence: {', '.join(primary_platforms)}. Analysis reveals {exposure_pct:.0f}% of accounts are publicly accessible, with {total_posts} content items extracted for behavioral analysis.

**Key Findings:**

"""

        # Add specific risk findings
        findings = []

        if has_location:
            findings.append("📍 **Location Disclosure:** Geolocation data found in public profiles")

        if total_posts > 20:
            findings.append(f"📊 **High Content Volume:** {total_posts} public posts/repos available for pattern analysis")

        if has_timestamps:
            findings.append("⏰ **Temporal Patterns:** Activity timestamps enable routine mapping")

        # Tech stack exposure
        all_languages = []
        for acc in accounts:
            if acc and acc.get('languages'):
                all_languages.extend(acc.get('languages', []))
        if all_languages:
            findings.append(f"💻 **Technology Stack:** {len(set(all_languages))} programming languages/tools identified")

        # Research interests (academic exposure)
        research_interests = []
        for acc in accounts:
            if acc and acc.get('research_interests'):
                research_interests.extend(acc.get('research_interests', []))
        if research_interests:
            findings.append(f"🎓 **Academic Profile:** Research interests disclosed ({len(research_interests)} topics)")

        if not findings:
            findings.append("✓ **Limited Exposure:** Minimal public information disclosed")

        for finding in findings:
            summary += f"- {finding}\n"

        summary += "\n**Intelligence Confidence:** " + self._calculate_confidence(accounts)

        return threat_level, summary

    def _calculate_threat_level(self, accounts: List[Dict], behavioral_profiles: List[Dict]) -> Tuple[str, List[str]]:
        """
        Calculate threat level based on exposure factors

        Returns:
            (threat_level, risk_factors)
            threat_level: CRITICAL, HIGH, MEDIUM, LOW
        """
        risk_score = 0
        risk_factors = []

        # Factor 1: Number of public accounts
        if len(accounts) >= 10:
            risk_score += 30
            risk_factors.append("High Platform Diversity")
        elif len(accounts) >= 5:
            risk_score += 20
            risk_factors.append("Moderate Platform Presence")

        # Factor 2: Location disclosure
        if any(acc.get('location') for acc in accounts if acc):
            risk_score += 25
            risk_factors.append("Location Exposed")

        # Factor 3: High content volume (more data for social engineering)
        total_posts = sum(len(acc.get('posts', [])) for acc in accounts if acc)
        if total_posts > 50:
            risk_score += 20
            risk_factors.append("High Content Volume")
        elif total_posts > 20:
            risk_score += 10

        # Factor 4: Real name used
        if any(acc.get('name') and len(acc.get('name', '').split()) > 1 for acc in accounts if acc):
            risk_score += 15
            risk_factors.append("Real Name Disclosed")

        # Factor 5: Professional profile (higher value target)
        if any('github' in acc.get('platform', '') or 'linkedin' in acc.get('platform', '') for acc in accounts if acc):
            risk_score += 10
            risk_factors.append("Professional Profile Active")

        # Determine threat level
        if risk_score >= 70:
            return "CRITICAL", risk_factors
        elif risk_score >= 50:
            return "HIGH", risk_factors
        elif risk_score >= 30:
            return "MEDIUM", risk_factors
        else:
            return "LOW", risk_factors

    def _calculate_confidence(self, accounts: List[Dict]) -> str:
        """Calculate intelligence confidence score"""
        total_data_points = 0
        for acc in accounts:
            if not acc:
                continue
            if acc.get('name'):
                total_data_points += 1
            if acc.get('bio'):
                total_data_points += 2
            if acc.get('location'):
                total_data_points += 2
            total_data_points += len(acc.get('posts', []))

        avg_per_account = total_data_points / max(len(accounts), 1)

        if avg_per_account >= 5:
            return "🟢 HIGH (Comprehensive data collected)"
        elif avg_per_account >= 2:
            return "🟡 MEDIUM (Adequate data for assessment)"
        else:
            return "🔴 LOW (Limited data - recommend additional collection)"

    def _generate_subject_profile(self, target_name: str, accounts: List[Dict], nlp_results: List[Dict]) -> str:
        """Generate PII profile section"""

        profile = f"""## 2. SUBJECT PROFILE (PII)

**Full Name:** {target_name}

"""

        # Extract real name from accounts
        real_names = set()
        for acc in accounts:
            if acc and acc.get('name') and len(acc.get('name', '').split()) > 1:
                real_names.add(acc.get('name'))

        if real_names:
            profile += f"**Confirmed Identity:** {', '.join(real_names)}\n\n"

        # Extract locations
        locations = set()
        for acc in accounts:
            if acc and acc.get('location'):
                locations.add(acc.get('location'))

        if locations:
            profile += "**Known Locations:**\n"
            for loc in locations:
                profile += f"- {loc}\n"
            profile += "\n"

        # Extract companies/organizations
        companies = set()
        for acc in accounts:
            if acc and acc.get('company'):
                companies.add(acc.get('company'))

        if companies:
            profile += "**Affiliated Organizations:**\n"
            for comp in companies:
                profile += f"- {comp}\n"
            profile += "\n"

        # Extract email/contact (from public profiles)
        emails = set()
        for acc in accounts:
            if acc and acc.get('email'):
                emails.add(acc.get('email'))
            # Extract from bio (handle None values)
            bio = acc.get('bio') if acc else None
            bio = bio if bio is not None else ''  # Convert None to empty string
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            found_emails = re.findall(email_pattern, bio)
            emails.update(found_emails)

        if emails:
            profile += "**Contact Information:**\n"
            for email in emails:
                # Sanitize for safety
                sanitized = email.replace('@', '[at]').replace('.', '[dot]')
                profile += f"- {sanitized} (Confirmed)\n"
            profile += "\n"

        # Known aliases/usernames
        usernames = set()
        for acc in accounts:
            if acc and acc.get('username'):
                usernames.add(acc.get('username'))
            # Also check URL for username
            url = acc.get('url', '') if acc else ''
            if url:
                parts = url.split('/')
                if len(parts) > 0:
                    potential_username = parts[-1]
                    if potential_username and len(potential_username) < 30:
                        usernames.add(potential_username)

        if usernames:
            profile += "**Known Aliases/Handles:**\n"
            for username in list(usernames)[:10]:
                profile += f"- {username}\n"

        return profile

    def _generate_digital_footprint(self, accounts: List[Dict]) -> str:
        """Generate digital footprint matrix"""

        footprint = """## 3. DIGITAL FOOTPRINT ANALYSIS

### A. Social Media Matrix

| Platform | Handle | Status | Risk Score | Posts | Notes |
|----------|--------|--------|------------|-------|-------|
"""

        for acc in accounts:
            if not acc:
                continue

            platform = acc.get('platform', 'unknown').upper()
            url = acc.get('url', '')
            handle = url.split('/')[-1] if '/' in url else 'N/A'

            # Status
            status = "Private" if acc.get('private', False) else "Public"

            # Risk score
            risk_score = self._calculate_account_risk(acc)

            # Post count
            post_count = len(acc.get('posts', []))

            # Notes
            notes = []
            if acc.get('location'):
                notes.append("Location disclosed")
            if post_count > 10:
                notes.append(f"{post_count} posts analyzed")
            if acc.get('followers', 0) > 1000:
                notes.append("High follower count")

            notes_str = "; ".join(notes) if notes else "Standard profile"

            footprint += f"| {platform} | {handle} | {status} | {risk_score} | {post_count} | {notes_str} |\n"

        return footprint

    def _calculate_account_risk(self, account: Dict) -> str:
        """Calculate risk score for individual account"""
        risk = 0

        if account.get('location'):
            risk += 30
        if len(account.get('posts', [])) > 20:
            risk += 25
        if account.get('followers', 0) > 100:
            risk += 15
        if account.get('email') or account.get('phone'):
            risk += 20
        if account.get('name'):
            risk += 10

        if risk >= 60:
            return "🔴 HIGH"
        elif risk >= 30:
            return "🟠 MEDIUM"
        else:
            return "🟢 LOW"

    def _generate_pattern_of_life(self, accounts: List[Dict], temporal_patterns: List[Dict], behavioral_profiles: List[Dict]) -> str:
        """Generate Pattern of Life analysis"""

        pol = """## 4. PATTERN OF LIFE (POL) ANALYSIS

"""

        # Extract activity patterns from temporal data
        peak_hours = []
        active_days = []

        for pattern in temporal_patterns:
            if pattern and isinstance(pattern, dict):
                if pattern.get('peak_hours'):
                    peak_hours.extend(pattern.get('peak_hours', []))
                if pattern.get('active_days'):
                    active_days.extend(pattern.get('active_days', []))

        if peak_hours:
            hour_counts = Counter(peak_hours)
            pol += "**Activity Schedule:**\n"
            pol += f"- Primary active hours: {', '.join(f'{h}:00' for h, _ in hour_counts.most_common(3))}\n"

        if active_days:
            day_counts = Counter(active_days)
            pol += f"- Most active days: {', '.join(d for d, _ in day_counts.most_common(3))}\n"

        pol += "\n"

        # Extract interests/routines from behavioral data
        all_interests = []
        for profile in behavioral_profiles:
            if profile and isinstance(profile, dict):
                all_interests.extend(profile.get('interests', []))

        if all_interests:
            interest_counts = Counter(all_interests)
            pol += "**Interests & Activities:**\n"
            for interest, count in interest_counts.most_common(5):
                pol += f"- {interest.title()} ({count} references across platforms)\n"
            pol += "\n"

        # Extract tech stack (professional intel)
        tech_stack = set()
        for acc in accounts:
            if acc and acc.get('languages'):
                tech_stack.update(acc.get('languages', []))

        if tech_stack:
            pol += "**Technology Proficiency:**\n"
            for tech in tech_stack:
                pol += f"- {tech}\n"
            pol += "\n"

        # Extract research interests (academic intel)
        research = set()
        for acc in accounts:
            if acc and acc.get('research_interests'):
                research.update(acc.get('research_interests', []))

        if research:
            pol += "**Research/Academic Interests:**\n"
            for topic in research:
                pol += f"- {topic}\n"

        return pol

    def _generate_vulnerability_assessment(self, accounts: List[Dict], target_name: str) -> str:
        """Generate vulnerability and OpSec assessment"""

        vuln = """## 5. VULNERABILITY ASSESSMENT

"""

        vulnerabilities = []

        # Check for PII exposure
        exposed_location = any(acc.get('location') for acc in accounts if acc)
        if exposed_location:
            locations = [acc.get('location') for acc in accounts if acc and acc.get('location')]
            vulnerabilities.append({
                'severity': 'HIGH',
                'title': 'Geolocation Disclosure',
                'description': f"Subject's location ({', '.join(set(locations))}) is publicly visible on {len(locations)} platform(s).",
                'recommendation': 'Enable location privacy settings or remove location data from profiles.'
            })

        # Check for email exposure
        emails_found = []
        for acc in accounts:
            if acc and acc.get('email'):
                emails_found.append(acc.get('email'))
            bio = acc.get('bio') if acc else None
            bio = bio if bio is not None else ''  # Convert None to empty string
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            found = re.findall(email_pattern, bio)
            emails_found.extend(found)

        if emails_found:
            vulnerabilities.append({
                'severity': 'MEDIUM',
                'title': 'Email Address Exposed',
                'description': f"{len(set(emails_found))} email address(es) found in public profiles or posts.",
                'recommendation': 'Remove email from public bios. Use contact forms instead of direct email disclosure.'
            })

        # Check for high post volume (social engineering risk)
        total_posts = sum(len(acc.get('posts', [])) for acc in accounts if acc)
        if total_posts > 30:
            vulnerabilities.append({
                'severity': 'MEDIUM',
                'title': 'High Content Volume',
                'description': f"{total_posts} public posts/repos provide extensive data for social engineering attacks.",
                'recommendation': 'Review post history and remove sensitive personal information or outdated content.'
            })

        # Check for username consistency (correlation risk)
        usernames = [target_name.lower().replace(' ', '')]
        platforms_with_consistent_username = 0
        for acc in accounts:
            if acc:
                url = acc.get('url', '')
                for username in usernames:
                    if username in url.lower():
                        platforms_with_consistent_username += 1
                        break

        if platforms_with_consistent_username >= 3:
            vulnerabilities.append({
                'severity': 'LOW',
                'title': 'Username Correlation',
                'description': f"Consistent username across {platforms_with_consistent_username} platforms enables easy account correlation.",
                'recommendation': 'Consider using different usernames across platforms to reduce correlation risk.'
            })

        # Generate vulnerability list
        if vulnerabilities:
            for i, vuln_item in enumerate(vulnerabilities, 1):
                severity_color = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }
                color = severity_color.get(vuln_item['severity'], '⚪')

                vuln += f"### {color} Vulnerability #{i}: {vuln_item['title']} ({vuln_item['severity']})\n\n"
                vuln += f"**Finding:** {vuln_item['description']}\n\n"
                vuln += f"**Recommendation:** {vuln_item['recommendation']}\n\n"
        else:
            vuln += "✅ **No critical vulnerabilities identified.** Subject maintains adequate OpSec posture.\n"

        return vuln

    def _generate_network_analysis(self, graph_metrics: Dict, accounts: List[Dict]) -> str:
        """Generate network/relationship analysis"""

        network = """## 6. NETWORK & ASSOCIATIONS

"""

        if graph_metrics and graph_metrics.get('network_stats'):
            stats = graph_metrics.get('network_stats', {})
            network += f"**Network Density:** {stats.get('density', 0):.1%}\n"
            network += f"**Connected Platforms:** {stats.get('num_nodes', 0)}\n"
            network += f"**Cross-Platform Links:** {stats.get('num_edges', 0)}\n\n"

            central_nodes = graph_metrics.get('central_nodes', [])
            if central_nodes:
                network += "**Hub Platforms (Highest Activity):**\n"
                for platform, score in central_nodes[:3]:
                    network += f"- {platform}: {score:.2f} centrality\n"
                network += "\n"
        else:
            network += "*Network analysis unavailable - insufficient cross-platform data*\n\n"

        # Extract mentioned relationships (from bios/posts)
        relationships = []
        for acc in accounts:
            if not acc:
                continue
            bio = acc.get('bio')
            bio = bio if bio is not None else ''  # Convert None to empty string
            # Look for relationship indicators
            if re.search(r'(father|mother|brother|sister|husband|wife|partner)', bio, re.IGNORECASE):
                relationships.append(f"{acc.get('platform', 'unknown')}: Family relationships mentioned in bio")
            if re.search(r'(work|colleague|team|company)', bio, re.IGNORECASE):
                relationships.append(f"{acc.get('platform', 'unknown')}: Professional relationships indicated")

        if relationships:
            network += "**Relationship Indicators:**\n"
            for rel in relationships[:5]:
                network += f"- {rel}\n"

        return network

    def _generate_pivot_intelligence(self, pivot_result) -> str:
        """Generate automated pivot intelligence section"""

        pivot_intel = f"""## 6.5 AUTOMATED PIVOT INTELLIGENCE

**Breadth-First OSINT Discovery** *(Professional Transform Chain)*

"""

        # Summary statistics
        pivot_intel += f"**Execution Summary:**\n"
        pivot_intel += f"- Selectors Processed: {pivot_result.total_selectors_processed}\n"
        pivot_intel += f"- Entities Discovered: {len(pivot_result.discovered_entities)}\n"
        pivot_intel += f"- Maximum Depth: {pivot_result.max_depth_reached} hops\n"
        pivot_intel += f"- API Calls: {pivot_result.total_api_calls}\n"
        pivot_intel += f"- Execution Time: {pivot_result.execution_time:.2f}s\n\n"

        # Discoveries by type
        entity_counts = pivot_result.to_dict()['entities_by_type']
        if entity_counts:
            pivot_intel += "**Discoveries by Type:**\n"
            for entity_type, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
                pivot_intel += f"- {entity_type.upper()}: {count}\n"
            pivot_intel += "\n"

        # Reliability distribution
        reliability_counts = pivot_result.to_dict()['entities_by_reliability']
        if reliability_counts:
            pivot_intel += "**Data Reliability Distribution:**\n"
            for reliability, count in sorted(reliability_counts.items()):
                pivot_intel += f"- {reliability}: {count} entities\n"
            pivot_intel += "\n"

        # Key discoveries (CONFIRMED entities only)
        confirmed_discoveries = [
            entity for entity in pivot_result.discovered_entities
            if entity.reliability.value == 'CONFIRMED'
        ]

        if confirmed_discoveries:
            pivot_intel += "**High-Confidence Discoveries (CONFIRMED):**\n\n"

            # Group by type
            by_type = {}
            for entity in confirmed_discoveries[:20]:  # Top 20
                entity_type = entity.selector.type.value
                if entity_type not in by_type:
                    by_type[entity_type] = []
                by_type[entity_type].append(entity)

            for entity_type, entities in sorted(by_type.items()):
                pivot_intel += f"*{entity_type.upper()}:*\n"
                for entity in entities[:5]:  # Top 5 per type
                    pivot_intel += f"- {entity.selector.value} (Source: {entity.source}, "
                    pivot_intel += f"Confidence: {entity.confidence}%)\n"

                    # Add metadata if important
                    if entity_type == 'domain' and entity.metadata.get('resolves_from'):
                        pivot_intel += f"  → Resolves from: {entity.metadata['resolves_from']}\n"
                    elif entity_type == 'email' and entity.metadata.get('breach_count'):
                        pivot_intel += f"  → Found in {entity.metadata['breach_count']} breaches\n"
                    elif entity_type == 'location' and entity.metadata.get('latitude'):
                        pivot_intel += f"  → Lat/Long: {entity.metadata['latitude']}, {entity.metadata['longitude']}\n"

                pivot_intel += "\n"

        # Transform performance
        if pivot_result.transform_stats:
            pivot_intel += "**Transform Performance:**\n"
            for transform_name, stats in pivot_result.transform_stats.items():
                pivot_intel += f"- {transform_name}: {stats['discoveries']} discoveries, "
                pivot_intel += f"{stats['executions']} executions, "
                pivot_intel += f"{stats['api_calls']} API calls\n"
            pivot_intel += "\n"

        # Sample pivot chains (provenance)
        if pivot_result.pivot_chains:
            pivot_intel += "**Sample Pivot Chains (Provenance):**\n"
            for chain in pivot_result.pivot_chains[:5]:  # Top 5 chains
                pivot_intel += f"- {str(chain)}\n"
            pivot_intel += "\n"

        pivot_intel += "*Note: Automated pivoting uses professional OSINT transforms including breach databases, WHOIS, DNS enumeration, GeoIP, and carrier lookups.*\n"

        return pivot_intel

    def _generate_verification_section(self, verification_results: Dict) -> str:
        """Generate 3-source verification section"""
        section = "## 6.6 DATA RELIABILITY & SOURCE VERIFICATION\n\n"
        section += "**3-Source Verification Standards Applied**\n\n"

        # Count by verification level
        levels = {}
        for field, result in verification_results.items():
            level = result.verification_level.value
            if level not in levels:
                levels[level] = []
            levels[level].append((field, result))

        for level in ['CONFIRMED', 'PROBABLE', 'POSSIBLE', 'UNVERIFIED', 'CONTRADICTED']:
            if level in levels:
                section += f"**{level}:** {len(levels[level])} data points\n"
                for field, result in levels[level][:3]:  # Top 3 per level
                    section += f"- {field.title()}: {result.value} (Sources: {', '.join(result.sources)})\n"
                section += "\n"

        return section

    def _generate_adverse_inference_section(self, adverse_results: Dict) -> str:
        """Generate adverse inference analysis section"""
        section = "## 6.7 ADVERSE INFERENCE & INTELLIGENCE GAPS\n\n"
        section += f"**Risk Score:** {adverse_results['risk_score']}/100\n\n"

        if adverse_results['temporal_gaps']:
            section += "**Temporal Gaps:**\n"
            for gap in adverse_results['temporal_gaps']:
                section += f"- {gap['type']}: {gap['inference']}\n"
            section += "\n"

        if adverse_results['scrubbing_indicators']:
            section += "**Profile Scrubbing Indicators:**\n"
            for indicator in adverse_results['scrubbing_indicators']:
                section += f"- {indicator['type']}: {indicator['inference']}\n"
            section += "\n"

        if adverse_results['opsec_indicators']:
            section += "**OpSec Awareness Indicators:**\n"
            for indicator in adverse_results['opsec_indicators']:
                section += f"- {indicator['type']}: {indicator['inference']}\n"
            section += "\n"

        return section

    def _generate_opsec_section(self, opsec_report: str) -> str:
        """Generate operational security section"""
        section = "## 6.8 OPERATIONAL SECURITY ASSESSMENT\n\n"
        section += opsec_report
        return section

    def _generate_recommendations(self, accounts: List[Dict], threat_level: str) -> str:
        """Generate strategic recommendations"""

        recommendations = f"""## 7. STRATEGIC RECOMMENDATIONS

**Threat Level: {threat_level}**

### Immediate Actions Required:

"""

        actions = []

        # Location privacy
        if any(acc.get('location') for acc in accounts if acc):
            actions.append("🔒 **Sanitize Location Data:** Remove or generalize location information on all public profiles (city-level instead of precise addresses).")

        # Public posts
        total_posts = sum(len(acc.get('posts', [])) for acc in accounts if acc)
        if total_posts > 30:
            actions.append(f"📝 **Content Audit:** Review {total_posts} public posts and remove any containing PII, schedules, or sensitive technical details.")

        # Email exposure
        if any(acc.get('email') for acc in accounts if acc):
            actions.append("📧 **Email Privacy:** Remove email addresses from public profiles. Use platform messaging or contact forms.")

        # OpSec training
        if len(accounts) > 5:
            actions.append("🎓 **OpSec Training:** Subject maintains extensive digital presence. Recommend operational security training for personal information management.")

        if not actions:
            actions.append("✅ **Maintain Current Posture:** No immediate actions required. Continue monitoring for new account creation or data exposure.")

        for action in actions:
            recommendations += f"\n{action}\n"

        recommendations += "\n### Long-Term Monitoring:\n\n"
        recommendations += "- Periodic OSINT audits (quarterly recommended)\n"
        recommendations += "- Alert setup for new public accounts or data breaches\n"
        recommendations += "- Regular review of privacy settings across all platforms\n"

        return recommendations

    def _generate_evidence_log(self, accounts: List[Dict]) -> str:
        """Generate evidence/source log"""

        evidence = """## 8. APPENDIX: EVIDENCE LOG

*All findings are based on publicly accessible information. Archive links provided for verification.*

"""

        for i, acc in enumerate(accounts, 1):
            if not acc:
                continue

            url = acc.get('url', 'N/A')
            platform = acc.get('platform', 'unknown').upper()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')

            evidence += f"\n**[{i}] {platform} Profile**\n"
            evidence += f"- Source URL: `{url}`\n"
            evidence += f"- Accessed: {timestamp}\n"
            evidence += f"- Archive: [archive.is/pending]\n"

            # Note key findings from this source
            findings = []
            if acc.get('location'):
                findings.append(f"Location: {acc.get('location')}")
            if acc.get('name'):
                findings.append(f"Name: {acc.get('name')}")
            if len(acc.get('posts', [])) > 0:
                findings.append(f"Content: {len(acc.get('posts', []))} posts extracted")

            if findings:
                evidence += f"- Key Data: {', '.join(findings)}\n"

        evidence += "\n---\n\n"
        evidence += "*Report generated by DeepTrace Advanced v3 - Professional OSINT Platform*\n"
        evidence += "*For questions or additional analysis, contact investigation team*\n"

        return evidence
