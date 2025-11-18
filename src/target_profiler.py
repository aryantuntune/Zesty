#!/usr/bin/env python3
"""
Target Profiler - Pre-investigation questionnaire
Gathers intel from user to narrow down search and filter false positives
"""

from typing import Dict, List, Set
from .utils import setup_logger

logger = setup_logger(__name__)


class TargetProfiler:
    """
    Interactive questionnaire to build target profile
    Helps narrow down search and filter out false positives
    """

    def __init__(self):
        self.profile = {}

    def print_header(self):
        """Display profiler header"""
        print("\n" + "="*70)
        print("🎯 TARGET PROFILER - Pre-Investigation Intelligence")
        print("="*70)
        print("\nℹ️  Let's gather some information about your target.")
        print("   This will help us filter out false positives and find the RIGHT person!")
        print("   (Press Enter to skip any question)\n")
        print("="*70 + "\n")

    def ask_basic_info(self) -> Dict:
        """Ask basic demographic information"""
        print("📋 BASIC INFORMATION\n")

        # Full name
        full_name = input("1. Full name (e.g., Aryan Tuntune): ").strip()
        if not full_name:
            print("   ⚠️  Target name is required!")
            return None

        # Name variations
        print(f"\n2. Known name variations/nicknames for {full_name}?")
        print("   (e.g., 'Aryan, Aryan T, AT')")
        variations = input("   Variations (comma-separated): ").strip()
        name_variations = [v.strip() for v in variations.split(',') if v.strip()] if variations else []

        # Age range
        print("\n3. Age range? (helps filter people with same name)")
        print("   a) Under 18")
        print("   b) 18-25")
        print("   c) 26-35")
        print("   d) 36-50")
        print("   e) 50+")
        print("   f) Unknown")
        age_range = input("   Choice (a-f): ").strip().lower()

        age_map = {
            'a': 'under_18',
            'b': '18-25',
            'c': '26-35',
            'd': '36-50',
            'e': '50+',
            'f': 'unknown'
        }
        age_range = age_map.get(age_range, 'unknown')

        # Gender
        print("\n4. Gender? (helps with name disambiguation)")
        print("   a) Male")
        print("   b) Female")
        print("   c) Other")
        print("   d) Unknown")
        gender = input("   Choice (a-d): ").strip().lower()

        gender_map = {
            'a': 'male',
            'b': 'female',
            'c': 'other',
            'd': 'unknown'
        }
        gender = gender_map.get(gender, 'unknown')

        return {
            'full_name': full_name,
            'name_variations': name_variations,
            'age_range': age_range,
            'gender': gender
        }

    def ask_location_info(self) -> Dict:
        """Ask location information"""
        print("\n\n📍 LOCATION INFORMATION\n")

        # Current location
        current_location = input("5. Current city/country (e.g., 'Mumbai, India'): ").strip()

        # Previous locations
        print("\n6. Previous locations? (helps track if they moved)")
        print("   (e.g., 'Delhi, Bangalore')")
        prev_locations = input("   Previous locations (comma-separated): ").strip()
        previous_locations = [loc.strip() for loc in prev_locations.split(',') if loc.strip()] if prev_locations else []

        # Timezone
        print("\n7. Known timezone? (helps verify account activity patterns)")
        print("   (e.g., 'IST', 'EST', 'PST')")
        timezone = input("   Timezone: ").strip()

        return {
            'current_location': current_location,
            'previous_locations': previous_locations,
            'timezone': timezone
        }

    def ask_online_presence(self) -> Dict:
        """Ask about known online presence"""
        print("\n\n🌐 ONLINE PRESENCE\n")

        print("8. Which platforms do you KNOW they use?")
        print("   (This helps us prioritize platforms)")
        print("\n   Select all that apply (comma-separated numbers):")
        print("   1. GitHub")
        print("   2. LinkedIn")
        print("   3. Twitter/X")
        print("   4. Instagram")
        print("   5. Facebook")
        print("   6. Reddit")
        print("   7. YouTube")
        print("   8. TikTok")
        print("   9. Medium")
        print("   10. Stack Overflow")
        print("   11. Other")

        platforms = input("\n   Platforms (e.g., 1,2,3): ").strip()

        platform_map = {
            '1': 'github',
            '2': 'linkedin',
            '3': 'twitter',
            '4': 'instagram',
            '5': 'facebook',
            '6': 'reddit',
            '7': 'youtube',
            '8': 'tiktok',
            '9': 'medium',
            '10': 'stackoverflow'
        }

        known_platforms = [platform_map[p.strip()] for p in platforms.split(',')
                          if p.strip() in platform_map] if platforms else []

        # Known usernames
        print("\n9. Known usernames on ANY platform?")
        print("   (e.g., 'aryantuntune, aryan_dev, aryan123')")
        usernames = input("   Usernames (comma-separated): ").strip()
        known_usernames = [u.strip() for u in usernames.split(',') if u.strip()] if usernames else []

        # Email addresses
        print("\n10. Known email addresses?")
        print("    (e.g., 'aryan@gmail.com')")
        emails = input("    Emails (comma-separated): ").strip()
        known_emails = [e.strip() for e in emails.split(',') if e.strip()] if emails else []

        return {
            'known_platforms': known_platforms,
            'known_usernames': known_usernames,
            'known_emails': known_emails
        }

    def ask_professional_info(self) -> Dict:
        """Ask professional/educational information"""
        print("\n\n💼 PROFESSIONAL/EDUCATIONAL INFO\n")

        # Occupation
        print("11. Occupation/Field? (helps filter by bio keywords)")
        print("    (e.g., 'Software Engineer', 'Student', 'Marketing')")
        occupation = input("    Occupation: ").strip()

        # Company
        print("\n12. Current or past companies/organizations?")
        print("    (e.g., 'Google, Microsoft, Stanford')")
        companies = input("    Companies (comma-separated): ").strip()
        companies_list = [c.strip() for c in companies.split(',') if c.strip()] if companies else []

        # Skills/Technologies
        print("\n13. Known skills/technologies?")
        print("    (e.g., 'Python, Machine Learning, Django')")
        skills = input("    Skills (comma-separated): ").strip()
        skills_list = [s.strip() for s in skills.split(',') if s.strip()] if skills else []

        # Education
        print("\n14. Educational institution?")
        print("    (e.g., 'MIT', 'Stanford', 'IIT Bombay')")
        education = input("    Institution: ").strip()

        return {
            'occupation': occupation,
            'companies': companies_list,
            'skills': skills_list,
            'education': education
        }

    def ask_interests_hobbies(self) -> Dict:
        """Ask about interests and hobbies"""
        print("\n\n🎯 INTERESTS & HOBBIES\n")

        print("15. Known interests/hobbies?")
        print("    (e.g., 'Photography, Gaming, Marvel, Anime')")
        interests = input("    Interests (comma-separated): ").strip()
        interests_list = [i.strip() for i in interests.split(',') if i.strip()] if interests else []

        print("\n16. Favorite topics they talk about?")
        print("    (e.g., 'Technology, Travel, Food')")
        topics = input("    Topics (comma-separated): ").strip()
        topics_list = [t.strip() for t in topics.split(',') if t.strip()] if topics else []

        return {
            'interests': interests_list,
            'topics': topics_list
        }

    def ask_additional_context(self) -> Dict:
        """Ask for any additional context"""
        print("\n\n📝 ADDITIONAL CONTEXT\n")

        print("17. Anything else that might help identify them?")
        print("    (e.g., 'Has a tech blog', 'Open source contributor', 'Twitch streamer')")
        additional = input("    Additional info: ").strip()

        print("\n18. Why are you investigating this target?")
        print("    (This helps us understand the use case)")
        print("    a) Background check")
        print("    b) Reconnecting with someone")
        print("    c) Security research")
        print("    d) Hiring/Recruitment")
        print("    e) Other")
        purpose = input("    Purpose (a-e): ").strip().lower()

        purpose_map = {
            'a': 'background_check',
            'b': 'reconnecting',
            'c': 'security_research',
            'd': 'recruitment',
            'e': 'other'
        }
        purpose = purpose_map.get(purpose, 'other')

        return {
            'additional_info': additional,
            'investigation_purpose': purpose
        }

    def build_profile(self, interactive: bool = True) -> Dict:
        """
        Build complete target profile

        Args:
            interactive: If True, ask questions. If False, return minimal profile.

        Returns:
            Complete target profile dictionary
        """
        if not interactive:
            return {'minimal': True}

        self.print_header()

        # Gather all information
        basic = self.ask_basic_info()

        if not basic:
            return None

        location = self.ask_location_info()
        online = self.ask_online_presence()
        professional = self.ask_professional_info()
        interests = self.ask_interests_hobbies()
        additional = self.ask_additional_context()

        # Combine into profile
        self.profile = {
            **basic,
            **location,
            **online,
            **professional,
            **interests,
            **additional
        }

        # Show summary
        self.print_summary()

        return self.profile

    def print_summary(self):
        """Print profile summary for confirmation"""
        print("\n\n" + "="*70)
        print("📊 TARGET PROFILE SUMMARY")
        print("="*70 + "\n")

        print(f"🎯 Name: {self.profile.get('full_name', 'N/A')}")

        if self.profile.get('name_variations'):
            print(f"   Variations: {', '.join(self.profile['name_variations'])}")

        print(f"👤 Age: {self.profile.get('age_range', 'unknown')}")
        print(f"⚧  Gender: {self.profile.get('gender', 'unknown')}")

        if self.profile.get('current_location'):
            print(f"📍 Location: {self.profile['current_location']}")

        if self.profile.get('known_platforms'):
            print(f"🌐 Known Platforms: {', '.join(self.profile['known_platforms'])}")

        if self.profile.get('known_usernames'):
            print(f"👥 Known Usernames: {', '.join(self.profile['known_usernames'])}")

        if self.profile.get('occupation'):
            print(f"💼 Occupation: {self.profile['occupation']}")

        if self.profile.get('skills'):
            print(f"🛠️  Skills: {', '.join(self.profile['skills'][:5])}")

        if self.profile.get('interests'):
            print(f"🎯 Interests: {', '.join(self.profile['interests'][:5])}")

        print("\n" + "="*70)

        confirm = input("\n✅ Does this look correct? (y/n): ").strip().lower()

        if confirm != 'y':
            print("\n⚠️  Profile cancelled. Please restart investigation.")
            return None

        print("\n✅ Profile confirmed! Starting investigation...\n")

    def filter_accounts_by_profile(self, accounts: List[Dict]) -> List[Dict]:
        """
        Filter accounts based on target profile

        Args:
            accounts: List of discovered accounts

        Returns:
            Filtered list of accounts that match profile
        """
        if not self.profile:
            return accounts

        filtered = []

        for account in accounts:
            if not account:
                continue
            score = self.calculate_profile_match_score(account)

            if score >= 30:  # Threshold: 30% match
                account['profile_match_score'] = score
                filtered.append(account)

        # Sort by match score
        filtered.sort(key=lambda x: x.get('profile_match_score', 0), reverse=True)

        logger.info(f"Profile filter: {len(accounts)} → {len(filtered)} accounts")

        return filtered

    def calculate_profile_match_score(self, account: Dict) -> float:
        """
        Calculate how well an account matches the target profile

        Returns:
            Score 0-100
        """
        # Handle None account
        if not account:
            return 0

        score = 0
        max_score = 0

        # Location match (20 points)
        max_score += 20
        if self.profile.get('current_location'):
            account_location = (account.get('location') or '').lower()
            if account_location and self.profile['current_location'].lower() in account_location:
                score += 20
            elif account_location and any(loc.lower() in account_location
                                         for loc in self.profile.get('previous_locations', [])):
                score += 10

        # Platform match (15 points)
        max_score += 15
        if self.profile.get('known_platforms'):
            account_platform = (account.get('platform') or '').lower()
            if account_platform in self.profile['known_platforms']:
                score += 15

        # Skills/occupation match (25 points)
        max_score += 25
        if self.profile.get('skills') or self.profile.get('occupation'):
            bio = (account.get('bio') or '').lower()

            # Check skills
            if self.profile.get('skills'):
                skill_matches = sum(1 for skill in self.profile['skills']
                                   if skill.lower() in bio)
                score += min(15, skill_matches * 5)

            # Check occupation
            if self.profile.get('occupation'):
                if self.profile['occupation'].lower() in bio:
                    score += 10

        # Company/education match (20 points)
        max_score += 20
        if self.profile.get('companies') or self.profile.get('education'):
            bio = (account.get('bio') or '').lower()

            if self.profile.get('companies'):
                company_matches = sum(1 for company in self.profile['companies']
                                     if company.lower() in bio)
                score += min(15, company_matches * 5)

            if self.profile.get('education'):
                if self.profile['education'].lower() in bio:
                    score += 5

        # Interest match (20 points)
        max_score += 20
        if self.profile.get('interests'):
            bio = (account.get('bio') or '').lower()
            interest_matches = sum(1 for interest in self.profile['interests']
                                  if interest.lower() in bio)
            score += min(20, interest_matches * 5)

        # Normalize to 0-100
        if max_score > 0:
            score = (score / max_score) * 100

        return score

    def generate_search_hints(self) -> Dict:
        """
        Generate search optimization hints from profile

        Returns:
            Dictionary of search hints
        """
        hints = {
            'priority_platforms': [],
            'must_have_keywords': [],
            'exclude_keywords': [],
            'location_filter': None
        }

        # Priority platforms
        if self.profile.get('known_platforms'):
            hints['priority_platforms'] = self.profile['known_platforms']

        # Must-have keywords
        keywords = []
        if self.profile.get('occupation'):
            keywords.append(self.profile['occupation'].lower())
        if self.profile.get('skills'):
            keywords.extend([s.lower() for s in self.profile['skills'][:3]])
        hints['must_have_keywords'] = keywords

        # Location filter
        if self.profile.get('current_location'):
            hints['location_filter'] = self.profile['current_location']

        # Age-based exclusions
        if self.profile.get('age_range') == 'under_18':
            hints['exclude_keywords'] = ['ceo', 'director', 'senior', 'lead']
        elif self.profile.get('age_range') == '50+':
            hints['exclude_keywords'] = ['student', 'intern', 'junior']

        return hints


# Convenience function
def build_target_profile(interactive: bool = True) -> Dict:
    """
    Build target profile through interactive questionnaire

    Args:
        interactive: If True, ask questions. If False, skip profiling.

    Returns:
        Target profile dictionary
    """
    profiler = TargetProfiler()
    return profiler.build_profile(interactive=interactive)
