#!/usr/bin/env python3
"""
Adverse Inference Detection - Intelligence Gap Analysis

When data is deliberately hidden or suspiciously absent, intelligence analysts
use "adverse inference" to deduce intent or activity from the gaps.

Examples:
- 3-year gap in employment history → Possible incarceration, military deployment
- No social media 2018-2021 → Deliberate profile scrubbing, witness protection
- All profiles created same month → Identity creation, sock puppets
- Consistent timezone but no location → OPSEC awareness, hiding location

This module automatically detects and flags suspicious patterns for human review.
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
import requests

from .utils import setup_logger

logger = setup_logger(__name__)


class AdverseInferenceEngine:
    """
    Detects suspicious gaps, patterns, and anomalies in OSINT data.

    Professional OSINT tradecraft for identifying:
    - Temporal gaps (missing time periods)
    - Data scrubbing indicators
    - Sock puppet patterns
    - OpSec awareness indicators
    """

    def __init__(self):
        """Initialize adverse inference engine"""
        self.current_year = datetime.now().year

    def analyze(self, accounts: List[Dict], target_profile: Dict = None) -> Dict:
        """
        Perform complete adverse inference analysis.

        Args:
            accounts: List of discovered accounts
            target_profile: Optional target profile data

        Returns:
            Dict of detected anomalies and inferences
        """
        results = {
            'temporal_gaps': [],
            'scrubbing_indicators': [],
            'sock_puppet_indicators': [],
            'opsec_indicators': [],
            'anomalies': [],
            'risk_score': 0
        }

        if not accounts:
            return results

        # Detect temporal gaps
        results['temporal_gaps'] = self._detect_temporal_gaps(accounts)

        # Detect profile scrubbing
        results['scrubbing_indicators'] = self._detect_scrubbing(accounts)

        # Detect sock puppets
        results['sock_puppet_indicators'] = self._detect_sock_puppets(accounts)

        # Detect OpSec awareness
        results['opsec_indicators'] = self._detect_opsec_awareness(accounts)

        # Detect general anomalies
        results['anomalies'] = self._detect_anomalies(accounts)

        # Apply elimination logic to refine inferences
        results = self._apply_elimination_logic(results, accounts, target_profile)

        # Calculate overall risk score
        results['risk_score'] = self._calculate_risk_score(results)

        return results

    def _detect_temporal_gaps(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect suspicious time gaps in activity.

        Red flags:
        - Multi-year gaps in account creation
        - Sudden stops and restarts in activity
        - Profiles dormant for years then suddenly active
        """
        gaps = []

        # Extract account creation dates
        creation_dates = []
        for acc in accounts:
            if not acc:
                continue

            # Try to find creation date from posts
            posts = acc.get('posts', [])
            if posts:
                for post in posts:
                    date_fields = ['created_at', 'published', 'posted_at', 'timestamp']
                    for field in date_fields:
                        if post.get(field):
                            try:
                                # Parse date
                                date_str = post[field]
                                if isinstance(date_str, str):
                                    # Simple year extraction
                                    year_match = re.search(r'(20\d{2})', date_str)
                                    if year_match:
                                        year = int(year_match.group(1))
                                        creation_dates.append(year)
                                        break
                            except:
                                pass

        if len(creation_dates) >= 2:
            # Sort dates
            sorted_dates = sorted(set(creation_dates))

            # Find gaps > 2 years
            for i in range(len(sorted_dates) - 1):
                gap = sorted_dates[i + 1] - sorted_dates[i]
                if gap > 2:
                    # Verify gap with Wayback Machine
                    wayback_verification = self._verify_gap_with_wayback(
                        accounts,
                        sorted_dates[i],
                        sorted_dates[i + 1]
                    )

                    gap_entry = {
                        'type': 'multi_year_gap',
                        'start_year': sorted_dates[i],
                        'end_year': sorted_dates[i + 1],
                        'gap_years': gap,
                        'severity': 'HIGH' if gap > 5 else 'MEDIUM',
                        'wayback_verification': wayback_verification,
                        'inference': f"{gap}-year gap in online activity. "
                    }

                    # Enhanced inference based on Wayback verification
                    if wayback_verification.get('verified'):
                        if wayback_verification.get('profile_existed_during_gap'):
                            gap_entry['inference'] += (
                                f"Wayback Machine shows profile EXISTED during gap but was later DELETED. "
                                f"This indicates deliberate profile scrubbing or content removal. "
                                f"Snapshots found: {wayback_verification.get('snapshots_found', 0)}"
                            )
                            gap_entry['severity'] = 'CRITICAL'  # Deliberate scrubbing is very suspicious
                        else:
                            gap_entry['inference'] += (
                                f"Wayback Machine shows profile did NOT exist during gap (404 errors). "
                                f"This confirms genuine inactivity, not scrubbing. Possible causes: "
                                f"incarceration, military deployment, witness protection, or account not created yet."
                            )
                    else:
                        gap_entry['inference'] += (
                            f"Possible causes: incarceration, military deployment, witness protection, "
                            f"deliberate profile dormancy, or identity change."
                        )

                    gaps.append(gap_entry)

        # Check for recent dormancy
        if creation_dates:
            most_recent = max(creation_dates)
            years_dormant = self.current_year - most_recent

            if years_dormant > 2:
                gaps.append({
                    'type': 'recent_dormancy',
                    'last_activity': most_recent,
                    'years_dormant': years_dormant,
                    'severity': 'MEDIUM',
                    'inference': f"No public activity since {most_recent} ({years_dormant} years). "
                               f"Possible profile abandonment or migration to new identity."
                })

        return gaps

    def _detect_scrubbing(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect indicators of deliberate data scrubbing.

        Red flags:
        - Very minimal profiles (name only, no bio, no posts)
        - Empty bios when platform typically has them
        - Deleted post history (indicators)
        """
        scrubbing_indicators = []

        empty_profile_count = 0
        minimal_data_count = 0

        for acc in accounts:
            if not acc:
                continue

            platform = acc.get('platform', 'unknown')
            has_name = bool(acc.get('name'))
            has_bio = bool(acc.get('bio'))
            has_location = bool(acc.get('location'))
            has_posts = bool(acc.get('posts'))
            post_count = len(acc.get('posts', []))

            # Completely empty profile
            if not has_name and not has_bio and not has_location and not has_posts:
                empty_profile_count += 1

            # Minimal data (name only)
            if has_name and not has_bio and not has_location and post_count == 0:
                minimal_data_count += 1

        # Flag if >50% profiles are minimal
        total_accounts = len([a for a in accounts if a])
        if total_accounts > 0:
            minimal_percentage = (minimal_data_count / total_accounts) * 100

            if minimal_percentage > 50:
                scrubbing_indicators.append({
                    'type': 'mass_minimal_profiles',
                    'percentage': minimal_percentage,
                    'count': minimal_data_count,
                    'severity': 'HIGH',
                    'inference': f"{minimal_percentage:.0f}% of profiles have minimal data "
                               f"(name only, no bio/location/posts). This suggests either: "
                               f"(1) Deliberate profile scrubbing for privacy, "
                               f"(2) Sock puppet/bot accounts, or "
                               f"(3) Inactive/abandoned accounts."
                })

        return scrubbing_indicators

    def _detect_sock_puppets(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect indicators of sock puppet/fake accounts.

        Red flags:
        - All accounts created within same month
        - Identical bio patterns across platforms
        - Sequential usernames
        - Low-effort profiles (generic names, no personalization)
        """
        indicators = []

        # Check creation date clustering (if available)
        # This would require account creation dates which we may not have

        # Check for identical bios
        bios = [acc.get('bio', '') for acc in accounts if acc and acc.get('bio')]
        if len(bios) > 2:
            unique_bios = set(bios)
            if len(unique_bios) < len(bios) / 2:  # More than 50% duplicates
                indicators.append({
                    'type': 'duplicate_bios',
                    'unique_count': len(unique_bios),
                    'total_count': len(bios),
                    'severity': 'MEDIUM',
                    'inference': "Multiple accounts share identical bios. Possible automated "
                               "account creation or copy-paste profile setup."
                })

        # Check for sequential usernames (user1, user2, etc.)
        usernames = [acc.get('username', '') for acc in accounts if acc and acc.get('username')]
        if len(usernames) > 2:
            # Look for numeric sequences
            numbered_usernames = [u for u in usernames if re.search(r'\d+$', u)]
            if len(numbered_usernames) >= 3:
                indicators.append({
                    'type': 'numbered_usernames',
                    'count': len(numbered_usernames),
                    'examples': numbered_usernames[:3],
                    'severity': 'LOW',
                    'inference': "Multiple accounts use numbered suffixes (user1, user2, etc.). "
                               "May indicate automated account generation or sock puppets."
                })

        return indicators

    def _detect_opsec_awareness(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect indicators of operational security (OpSec) awareness.

        This is NOT necessarily malicious - security-conscious individuals
        practice good OpSec. But it indicates the subject is aware of OSINT
        and takes steps to limit exposure.

        Indicators:
        - No location data despite being on location-heavy platforms
        - Consistent timezone but hidden location
        - Privacy-focused usernames
        - Minimal personal information
        """
        indicators = []

        has_location_count = sum(1 for acc in accounts if acc and acc.get('location'))
        total_accounts = len([a for a in accounts if a])

        if total_accounts > 0:
            location_percentage = (has_location_count / total_accounts) * 100

            if location_percentage < 20 and total_accounts >= 3:
                indicators.append({
                    'type': 'location_privacy',
                    'percentage': location_percentage,
                    'severity': 'MEDIUM',
                    'inference': f"Only {location_percentage:.0f}% of profiles include location data. "
                               f"Subject demonstrates location privacy awareness. This is good OpSec "
                               f"practice but limits geolocation intelligence."
                })

        # Check for privacy-focused usernames
        privacy_keywords = ['anon', 'priv', 'secure', 'ghost', 'phantom', 'shadow', 'incognito']
        privacy_username_count = 0

        for acc in accounts:
            if acc and acc.get('username'):
                username_lower = acc['username'].lower()
                if any(keyword in username_lower for keyword in privacy_keywords):
                    privacy_username_count += 1

        if privacy_username_count > 0:
            indicators.append({
                'type': 'privacy_usernames',
                'count': privacy_username_count,
                'severity': 'LOW',
                'inference': f"{privacy_username_count} username(s) contain privacy-related keywords "
                           f"(anon, ghost, etc.). Indicates privacy consciousness or hacker culture affiliation."
            })

        return indicators

    def _detect_anomalies(self, accounts: List[Dict]) -> List[Dict]:
        """
        Detect general anomalies that don't fit other categories.

        Examples:
        - Single account with 1000+ posts vs all others with <10
        - Name variations across platforms (John Smith vs J. Sm1th)
        - Platform clustering (all accounts are tech platforms)
        """
        anomalies = []

        # Check post count distribution
        post_counts = [len(acc.get('posts', [])) for acc in accounts if acc]
        if post_counts and len(post_counts) > 2:
            avg_posts = sum(post_counts) / len(post_counts)
            max_posts = max(post_counts)

            # Outlier detection (10x average)
            if max_posts > avg_posts * 10 and avg_posts > 0:
                anomalies.append({
                    'type': 'post_count_outlier',
                    'max_posts': max_posts,
                    'avg_posts': avg_posts,
                    'severity': 'LOW',
                    'inference': f"One account has {max_posts} posts while average is {avg_posts:.0f}. "
                               f"This may be subject's primary/most active account."
                })

        # Check platform clustering
        platforms = [acc.get('platform', 'unknown') for acc in accounts if acc]
        platform_counts = defaultdict(int)
        for platform in platforms:
            platform_counts[platform] += 1

        # Tech platform clustering
        tech_platforms = {'github', 'stackoverflow', 'gitlab', 'bitbucket', 'hackernews'}
        tech_count = sum(1 for p in platforms if p.lower() in tech_platforms)

        if tech_count >= 3:
            anomalies.append({
                'type': 'tech_platform_clustering',
                'tech_platform_count': tech_count,
                'severity': 'LOW',
                'inference': f"Subject has {tech_count} accounts on technical platforms "
                           f"(GitHub, StackOverflow, etc.). Indicates software development "
                           f"or IT professional background."
            })

        return anomalies

    def _apply_elimination_logic(self, results: Dict, accounts: List[Dict], target_profile: Dict = None) -> Dict:
        """
        Apply deductive elimination logic to refine inferences.

        Professional Intelligence Analysis:
        Instead of just flagging suspicious patterns, apply logical reasoning to:
        1. Eliminate impossible scenarios
        2. Reduce probability of unlikely scenarios
        3. Add alternative explanations based on evidence

        Elimination Rules:
        - IF tech_platform_clustering AND temporal_gap THEN infer(graduate_school_or_bootcamp)
        - IF location_privacy AND opsec_keywords THEN increase_probability(security_professional)
        - IF minimal_profiles AND all_created_same_year THEN increase_probability(sock_puppets)
        - IF temporal_gap AND conference_activity THEN infer(career_transition)

        This is the "Sherlock Holmes" phase: "Once you eliminate the impossible,
        whatever remains, however improbable, must be the truth."

        Args:
            results: Current adverse inference results
            accounts: List of account dictionaries
            target_profile: Optional target profile data

        Returns:
            Updated results with elimination logic applied
        """
        results['elimination_analysis'] = []

        # Rule 1: Tech platform clustering + temporal gap → Graduate school/bootcamp
        tech_cluster = None
        for anomaly in results['anomalies']:
            if anomaly.get('type') == 'tech_platform_clustering':
                tech_cluster = anomaly
                break

        if tech_cluster:
            for gap in results['temporal_gaps']:
                gap_years = gap.get('gap_years', 0)
                if 2 <= gap_years <= 4:  # Graduate school is typically 2-4 years
                    results['elimination_analysis'].append({
                        'rule': 'tech_cluster_with_gap',
                        'finding': f"{gap_years}-year gap with {tech_cluster.get('tech_platform_count')} tech platforms",
                        'inference': f"Gap likely due to graduate school or coding bootcamp. "
                                   f"Subject transitioned into tech field after {gap.get('end_year')}.",
                        'probability': 0.7,
                        'impact': 'LOW',
                        'eliminates': ['incarceration', 'witness_protection']
                    })

        # Rule 2: Location privacy + OpSec keywords → Security professional
        location_privacy = None
        opsec_keywords = False

        for indicator in results['opsec_indicators']:
            if indicator.get('type') == 'location_privacy':
                location_privacy = indicator
            elif indicator.get('type') == 'privacy_usernames':
                opsec_keywords = True

        if location_privacy and opsec_keywords:
            results['elimination_analysis'].append({
                'rule': 'opsec_aware_professional',
                'finding': 'Location privacy + privacy-focused usernames',
                'inference': 'Subject demonstrates professional OpSec awareness. '
                           'Likely works in cybersecurity, privacy advocacy, or sensitive field. '
                           'This is good security hygiene, not necessarily malicious.',
                'probability': 0.6,
                'impact': 'LOW',
                'eliminates': ['unsophisticated_threat']
            })

        # Rule 3: Minimal profiles + same creation year → Sock puppets
        minimal_profile_indicator = None
        for indicator in results['scrubbing_indicators']:
            if indicator.get('type') == 'mass_minimal_profiles':
                minimal_profile_indicator = indicator
                break

        if minimal_profile_indicator:
            # Check if accounts were created in same year
            creation_years = []
            for acc in accounts:
                if acc and acc.get('created_at'):
                    # Extract year from created_at
                    created_at = str(acc['created_at'])
                    year_match = re.search(r'(20\d{2})', created_at)
                    if year_match:
                        creation_years.append(int(year_match.group(1)))

            if len(set(creation_years)) == 1 and len(creation_years) >= 3:
                results['elimination_analysis'].append({
                    'rule': 'minimal_profiles_same_year',
                    'finding': f"{len(creation_years)} minimal profiles created in {creation_years[0]}",
                    'inference': 'High probability of coordinated account creation. '
                               'Suggests sock puppets, bot network, or deliberate identity establishment.',
                    'probability': 0.8,
                    'impact': 'MEDIUM',
                    'eliminates': ['organic_growth']
                })

        # Rule 4: Post count outlier → Primary account identification
        primary_account = None
        for anomaly in results['anomalies']:
            if anomaly.get('type') == 'post_count_outlier':
                max_posts = anomaly.get('max_posts', 0)
                if max_posts > 50:
                    # Find which account has this many posts
                    for acc in accounts:
                        if acc and len(acc.get('posts', [])) == max_posts:
                            primary_account = acc.get('platform', 'unknown')
                            break

                    if primary_account:
                        results['elimination_analysis'].append({
                            'rule': 'primary_account_identified',
                            'finding': f"{primary_account} has {max_posts} posts vs average {anomaly.get('avg_posts', 0):.0f}",
                            'inference': f"{primary_account} is subject's primary platform. "
                                       f"Focus investigation here for most detailed intelligence.",
                            'probability': 0.9,
                            'impact': 'LOW',
                            'recommendation': f"Prioritize deep analysis of {primary_account} account"
                        })

        # Rule 5: Wayback verification eliminates scrubbing vs inactivity
        for gap in results['temporal_gaps']:
            wayback = gap.get('wayback_verification', {})
            if wayback.get('verified'):
                if not wayback.get('profile_existed_during_gap'):
                    results['elimination_analysis'].append({
                        'rule': 'wayback_confirms_inactivity',
                        'finding': f"Wayback Machine shows 404 errors during {gap.get('start_year')}-{gap.get('end_year')}",
                        'inference': 'Profile scrubbing hypothesis ELIMINATED. '
                                   'Subject genuinely was not active on platform during this period.',
                        'probability': 1.0,
                        'impact': 'LOW',
                        'eliminates': ['profile_scrubbing', 'content_deletion']
                    })

        # Rule 6: Tech stack indicates professional role
        all_tech_stacks = []
        for acc in accounts:
            if acc and acc.get('posts'):
                for post in acc['posts']:
                    if post.get('tech_stack'):
                        all_tech_stacks.extend(post['tech_stack'])

        if all_tech_stacks:
            unique_tech = set(all_tech_stacks)

            # Cloud engineer pattern
            cloud_techs = {'aws', 'gcp', 'azure'}
            if cloud_techs & unique_tech:
                results['elimination_analysis'].append({
                    'rule': 'cloud_engineer_pattern',
                    'finding': f"Cloud technologies detected: {', '.join(cloud_techs & unique_tech)}",
                    'inference': 'Subject works with cloud infrastructure. '
                               'Likely role: Cloud Engineer, DevOps, SRE, or Solutions Architect.',
                    'probability': 0.8,
                    'impact': 'LOW',
                    'professional_role': 'cloud_infrastructure'
                })

            # Database specialist pattern
            db_techs = {'postgresql', 'mysql', 'mongodb', 'redis'}
            if len(db_techs & unique_tech) >= 2:
                results['elimination_analysis'].append({
                    'rule': 'database_specialist_pattern',
                    'finding': f"Multiple database technologies: {', '.join(db_techs & unique_tech)}",
                    'inference': 'Subject has database expertise. '
                               'Likely role: Database Administrator, Backend Engineer, or Data Engineer.',
                    'probability': 0.7,
                    'impact': 'LOW',
                    'professional_role': 'database_specialist'
                })

        # Rule 7: Threat keywords indicate security research vs malicious
        all_threat_keywords = []
        for acc in accounts:
            if acc and acc.get('posts'):
                for post in acc['posts']:
                    if post.get('threat_keywords'):
                        all_threat_keywords.extend(post['threat_keywords'])

        if all_threat_keywords:
            # Check for educational/research context
            has_educational_context = False
            for acc in accounts:
                bio = acc.get('bio', '').lower() if acc else ''
                if any(kw in bio for kw in ['security researcher', 'pentester', 'bug bounty', 'ctf', 'educator', 'professor']):
                    has_educational_context = True
                    break

            if has_educational_context:
                results['elimination_analysis'].append({
                    'rule': 'threat_keywords_with_context',
                    'finding': f"Threat keywords detected ({len(set(all_threat_keywords))}) with security research context",
                    'inference': 'Threat keywords appear in legitimate security research context. '
                               'Subject likely works in offensive security, penetration testing, or security education. '
                               'MALICIOUS INTENT hypothesis REDUCED.',
                    'probability': 0.9,
                    'impact': 'LOW',
                    'eliminates': ['malicious_actor'],
                    'professional_role': 'security_researcher'
                })
            else:
                results['elimination_analysis'].append({
                    'rule': 'threat_keywords_without_context',
                    'finding': f"Threat keywords detected ({len(set(all_threat_keywords))}) WITHOUT clear research context",
                    'inference': 'Threat keywords present but no clear security research affiliation. '
                               'Could indicate: (1) Private security researcher, (2) Hobbyist hacker, '
                               '(3) Threat actor, or (4) CTF participant. REQUIRES HUMAN REVIEW.',
                    'probability': 0.6,
                    'impact': 'MEDIUM',
                    'recommendation': 'Manual review of threat keyword context required'
                })

        return results

    def _calculate_risk_score(self, results: Dict) -> int:
        """
        Calculate overall adverse inference risk score using Probability × Impact formula.

        Professional Intelligence Methodology:
        Instead of arbitrary severity points, we use:

        Risk Score = Σ (Probability × Impact) × 25

        Where:
        - Probability (0-1): How likely is the inference correct?
          - CONFIRMED: 1.0 (Wayback Machine verification, hard evidence)
          - PROBABLE: 0.75 (Strong indicators, corroborating evidence)
          - POSSIBLE: 0.5 (Single indicator, circumstantial)
          - SPECULATIVE: 0.25 (Weak evidence)

        - Impact (1-4): How serious is the finding if true?
          - CRITICAL: 4 (Deliberate deception, active threat)
          - HIGH: 3 (Significant security/privacy concern)
          - MEDIUM: 2 (Notable pattern requiring investigation)
          - LOW: 1 (Minor anomaly, low significance)

        Example:
        - Temporal gap with Wayback showing profile scrubbing:
          Probability = 1.0 (confirmed by Wayback)
          Impact = 4 (deliberate deception)
          Risk contribution = 1.0 × 4 × 25 = 100 points

        - Username with privacy keywords:
          Probability = 0.5 (could be coincidence)
          Impact = 1 (low significance)
          Risk contribution = 0.5 × 1 × 25 = 12.5 points

        Args:
            results: Adverse inference results

        Returns:
            Risk score 0-100
        """
        total_risk = 0.0

        # Temporal gaps - probability based on Wayback verification
        for gap in results['temporal_gaps']:
            # Determine probability
            wayback = gap.get('wayback_verification', {})
            if wayback.get('verified'):
                if wayback.get('profile_existed_during_gap'):
                    probability = 1.0  # CONFIRMED: Wayback shows scrubbing
                else:
                    probability = 0.75  # PROBABLE: Wayback shows genuine inactivity
            else:
                probability = 0.5  # POSSIBLE: No verification, circumstantial

            # Determine impact
            severity = gap.get('severity', 'MEDIUM')
            if severity == 'CRITICAL':
                impact = 4  # Deliberate scrubbing
            elif severity == 'HIGH':
                impact = 3  # Long gap or suspicious pattern
            elif severity == 'MEDIUM':
                impact = 2  # Moderate gap
            else:
                impact = 1  # Short gap or explained

            risk_contribution = probability * impact * 25
            total_risk += risk_contribution

        # Scrubbing indicators - high probability due to measurable data
        for indicator in results['scrubbing_indicators']:
            probability = 0.75  # PROBABLE: Based on statistical analysis

            severity = indicator.get('severity', 'MEDIUM')
            if severity == 'HIGH':
                impact = 3  # Mass scrubbing is serious
            elif severity == 'MEDIUM':
                impact = 2
            else:
                impact = 1

            risk_contribution = probability * impact * 25
            total_risk += risk_contribution

        # Sock puppet indicators - moderate probability (could be coincidence)
        for indicator in results['sock_puppet_indicators']:
            probability = 0.5  # POSSIBLE: Pattern-based, not confirmed

            severity = indicator.get('severity', 'MEDIUM')
            if severity == 'MEDIUM':
                impact = 2
            elif severity == 'LOW':
                impact = 1
            else:
                impact = 3

            risk_contribution = probability * impact * 25
            total_risk += risk_contribution

        # OpSec indicators - low probability (normal privacy-conscious behavior)
        for indicator in results['opsec_indicators']:
            probability = 0.25  # SPECULATIVE: Could be normal privacy

            severity = indicator.get('severity', 'MEDIUM')
            if severity == 'MEDIUM':
                impact = 2
            elif severity == 'LOW':
                impact = 1
            else:
                impact = 3

            risk_contribution = probability * impact * 25
            total_risk += risk_contribution

        # Anomalies - very low probability (often normal variation)
        for anomaly in results['anomalies']:
            probability = 0.25  # SPECULATIVE
            impact = 1  # LOW impact
            risk_contribution = probability * impact * 25
            total_risk += risk_contribution

        return min(int(total_risk), 100)

    def _verify_gap_with_wayback(self, accounts: List[Dict], start_year: int, end_year: int) -> Dict:
        """
        Verify temporal gaps using Wayback Machine (Internet Archive).

        Professional OSINT Tradecraft:
        - If profile exists in Wayback during gap → Profile was active but later deleted (SCRUBBING)
        - If profile shows 404 in Wayback during gap → Profile truly didn't exist (GENUINE INACTIVITY)

        This distinguishes between:
        1. Subject took a break from platform (genuine inactivity)
        2. Subject deleted old content to hide past activity (scrubbing)

        Example:
        - Twitter profile created 2015, posts until 2017, gap until 2020, resumes 2020
        - Wayback check for 2018-2019:
          - If snapshots show profile with content → Subject deleted 2017-2019 posts (SUSPICIOUS)
          - If snapshots show 404 → Account was deactivated (LESS SUSPICIOUS)

        Args:
            accounts: List of account dictionaries
            start_year: Start of gap
            end_year: End of gap

        Returns:
            Dictionary with verification results
        """
        verification = {
            'verified': False,
            'profile_existed_during_gap': False,
            'snapshots_found': 0,
            'sample_snapshots': [],
            'error': None
        }

        try:
            # Find accounts with profile URLs
            for account in accounts:
                if not account:
                    continue

                # Get profile URL
                profile_url = account.get('profile_url')
                if not profile_url:
                    # Try to construct from platform and username
                    platform = account.get('platform', '').lower()
                    username = account.get('username')
                    if platform and username:
                        # Construct URL based on platform
                        url_patterns = {
                            'twitter': f'https://twitter.com/{username}',
                            'github': f'https://github.com/{username}',
                            'linkedin': f'https://linkedin.com/in/{username}',
                            'instagram': f'https://instagram.com/{username}'
                        }
                        profile_url = url_patterns.get(platform)

                if not profile_url:
                    continue

                # Query Wayback Machine CDX API for snapshots during gap
                # CDX API: http://web.archive.org/cdx/search/cdx
                cdx_url = 'http://web.archive.org/cdx/search/cdx'
                params = {
                    'url': profile_url,
                    'from': str(start_year),
                    'to': str(end_year),
                    'output': 'json',
                    'fl': 'timestamp,statuscode,original',
                    'limit': 100
                }

                response = requests.get(cdx_url, params=params, timeout=10)

                if response.status_code == 200:
                    try:
                        snapshots = response.json()

                        # Skip header row if present
                        if snapshots and isinstance(snapshots[0], list) and snapshots[0][0] == 'timestamp':
                            snapshots = snapshots[1:]

                        if snapshots:
                            verification['verified'] = True
                            verification['snapshots_found'] = len(snapshots)

                            # Check status codes
                            # 200 = page existed, 404 = page not found
                            success_snapshots = []
                            for snapshot in snapshots:
                                if len(snapshot) >= 2:
                                    timestamp, statuscode = snapshot[0], snapshot[1]
                                    if statuscode.startswith('2'):  # 200, 201, etc.
                                        success_snapshots.append({
                                            'timestamp': timestamp,
                                            'year': int(timestamp[:4]) if len(timestamp) >= 4 else None
                                        })

                            if success_snapshots:
                                verification['profile_existed_during_gap'] = True
                                verification['sample_snapshots'] = success_snapshots[:5]  # Top 5
                                logger.info(
                                    f"Wayback verification: {profile_url} EXISTED during {start_year}-{end_year} "
                                    f"({len(success_snapshots)} snapshots found)"
                                )
                            else:
                                verification['profile_existed_during_gap'] = False
                                logger.info(
                                    f"Wayback verification: {profile_url} did NOT exist during {start_year}-{end_year} "
                                    f"(all snapshots returned 404)"
                                )

                            # Found verification for at least one account, return
                            return verification

                    except Exception as e:
                        logger.debug(f"Failed to parse Wayback response: {e}")
                        continue

        except Exception as e:
            verification['error'] = str(e)
            logger.debug(f"Wayback verification failed: {e}")

        return verification
