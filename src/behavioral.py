"""
Behavioral Analysis Engine: Advanced username discovery and account matching
Goes beyond simple username variations to identify accounts based on behavior patterns
"""

import re
from typing import List, Dict, Set, Tuple
from collections import Counter
from .utils import setup_logger

logger = setup_logger(__name__)


class BehavioralAnalyzer:
    """
    Advanced account correlation using behavioral fingerprinting
    Analyzes: writing style, interests, patterns, timing, content themes
    """

    def __init__(self):
        self.interest_keywords = set()
        self.writing_patterns = {}
        self.content_themes = []
        self.behavioral_fingerprint = {}

    # ========== WRITING STYLE ANALYSIS ==========

    def analyze_writing_style(self, text: str) -> Dict:
        """
        Extract writing style fingerprint

        Features:
        - Average sentence length
        - Punctuation patterns
        - Capitalization style
        - Emoji usage
        - Slang/abbreviations
        - Vocabulary complexity
        """
        if not text:
            return {}

        style = {
            'avg_sentence_length': 0,
            'emoji_count': 0,
            'exclamation_usage': 0,
            'question_usage': 0,
            'caps_ratio': 0,
            'url_count': 0,
            'hashtag_count': 0,
            'mention_count': 0
        }

        # Sentence length
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            style['avg_sentence_length'] = sum(len(s.split()) for s in sentences) / len(sentences)

        # Emoji count (basic detection)
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+",
            flags=re.UNICODE
        )
        style['emoji_count'] = len(emoji_pattern.findall(text))

        # Punctuation patterns
        style['exclamation_usage'] = text.count('!')
        style['question_usage'] = text.count('?')

        # Capitalization
        if len(text) > 0:
            style['caps_ratio'] = sum(1 for c in text if c.isupper()) / len(text)

        # Social media patterns
        style['url_count'] = len(re.findall(r'https?://\S+', text))
        style['hashtag_count'] = len(re.findall(r'#\w+', text))
        style['mention_count'] = len(re.findall(r'@\w+', text))

        return style

    def compare_writing_styles(self, style1: Dict, style2: Dict) -> float:
        """
        Compare two writing style fingerprints
        Returns similarity score (0-100)
        """
        if not style1 or not style2:
            return 0.0

        score = 0.0
        comparisons = 0

        # Compare sentence length (within 20% is similar)
        if 'avg_sentence_length' in style1 and 'avg_sentence_length' in style2:
            s1, s2 = style1['avg_sentence_length'], style2['avg_sentence_length']
            if s1 > 0 and s2 > 0:
                diff = abs(s1 - s2) / max(s1, s2)
                if diff < 0.2:
                    score += 15
                comparisons += 1

        # Compare emoji usage
        if style1['emoji_count'] > 0 and style2['emoji_count'] > 0:
            score += 10
            comparisons += 1
        elif style1['emoji_count'] == 0 and style2['emoji_count'] == 0:
            score += 5
            comparisons += 1

        # Compare punctuation style
        if abs(style1['exclamation_usage'] - style2['exclamation_usage']) < 3:
            score += 10

        return score

    # ========== INTEREST & THEME EXTRACTION ==========

    def extract_interests(self, text: str) -> Set[str]:
        """
        Extract interests, hobbies, fandoms from text

        Looks for:
        - Tech stack (Python, React, AI, etc.)
        - Hobbies (gaming, photography, music)
        - Pop culture references (Marvel, Star Wars, anime)
        - Sports teams
        """
        interests = set()

        # Technology interests
        tech_keywords = [
            'python', 'javascript', 'react', 'node', 'java', 'golang', 'rust',
            'ai', 'ml', 'machine learning', 'deep learning', 'nlp',
            'blockchain', 'web3', 'crypto', 'devops', 'cloud', 'aws', 'kubernetes',
            'flutter', 'dart', 'swift', 'kotlin', 'android', 'ios'
        ]

        # Pop culture & fandoms
        pop_culture = [
            'marvel', 'mcu', 'thanos', 'avengers', 'iron man', 'spiderman',
            'star wars', 'mandalorian', 'anime', 'naruto', 'one piece',
            'gaming', 'gamer', 'valorant', 'league', 'fortnite', 'minecraft',
            'photography', 'travel', 'fitness', 'gym', 'coding', 'music'
        ]

        text_lower = text.lower()

        for keyword in tech_keywords + pop_culture:
            if keyword in text_lower:
                interests.add(keyword)
                self.interest_keywords.add(keyword)

        # Extract hashtags as interests
        hashtags = re.findall(r'#(\w+)', text)
        interests.update(hashtag.lower() for hashtag in hashtags)

        return interests

    def generate_interest_based_usernames(self, interests: Set[str], base_name: str = "") -> List[str]:
        """
        Generate username predictions based on interests

        Example:
        Interests: ['thanos', 'marvel', 'python']
        Base: 'aryan'

        Generates:
        - aryan_thanos
        - thanos_aryan
        - aryan_marvel
        - python_aryan
        - aryanthedev (from 'python' -> 'dev')
        """
        if not interests:
            return []

        usernames = []

        # Get name parts
        name_parts = re.findall(r'[a-zA-Z]+', base_name.lower())

        for interest in interests:
            interest_clean = re.sub(r'[^a-z0-9]', '', interest.lower())

            if len(interest_clean) < 3:
                continue

            for name_part in name_parts:
                # Different combination patterns
                usernames.extend([
                    f"{name_part}_{interest_clean}",
                    f"{interest_clean}_{name_part}",
                    f"{name_part}{interest_clean}",
                    f"{interest_clean}{name_part}",
                    f"{name_part}.{interest_clean}",
                    f"{name_part}-{interest_clean}",
                ])

            # Standalone interest-based usernames
            usernames.extend([
                interest_clean,
                f"{interest_clean}123",
                f"{interest_clean}_official",
                f"the{interest_clean}",
            ])

        # Map interests to related terms
        interest_mappings = {
            'python': ['pythonista', 'pydev', 'snakecoder'],
            'javascript': ['jsdev', 'webdev'],
            'ai': ['aiml', 'artificialintelligence'],
            'marvel': ['mcu', 'marvelite'],
            'thanos': ['madbulletin', 'titanscion'],
            'gaming': ['gamer', 'gamingaddict'],
            'photography': ['photographer', 'photoartist'],
        }

        for interest in interests:
            if interest in interest_mappings:
                for mapped in interest_mappings[interest]:
                    for name_part in name_parts:
                        usernames.append(f"{name_part}_{mapped}")
                        usernames.append(f"{mapped}_{name_part}")

        return list(set(usernames))  # Remove duplicates

    # ========== TEMPORAL & BEHAVIORAL PATTERNS ==========

    def extract_activity_patterns(self, posts: List[Dict]) -> Dict:
        """
        Analyze posting behavior patterns

        Extracts:
        - Posting times
        - Posting frequency
        - Content types (links, images, text)
        - Engagement patterns
        """
        if not posts:
            return {}

        patterns = {
            'post_count': len(posts),
            'avg_length': 0,
            'link_ratio': 0,
            'image_ratio': 0,
        }

        total_length = 0
        link_count = 0
        image_count = 0

        for post in posts:
            content = post.get('content', '')
            total_length += len(content)

            if 'http' in content:
                link_count += 1
            if post.get('has_image', False):
                image_count += 1

        if posts:
            patterns['avg_length'] = total_length / len(posts)
            patterns['link_ratio'] = link_count / len(posts)
            patterns['image_ratio'] = image_count / len(posts)

        return patterns

    # ========== ADVANCED CORRELATION ==========

    def calculate_account_similarity(
        self,
        account1: Dict,
        account2: Dict
    ) -> Tuple[float, List[str]]:
        """
        Calculate comprehensive similarity score between two accounts

        Returns:
            (score, reasons) where score is 0-100
        """
        score = 0.0
        reasons = []

        # 1. Name matching (30 points max)
        if account1.get('name') and account2.get('name'):
            name1 = account1['name'].lower()
            name2 = account2['name'].lower()

            if name1 == name2:
                score += 30
                reasons.append("Exact name match")
            elif name1 in name2 or name2 in name1:
                score += 20
                reasons.append("Partial name match")

        # 2. Location matching (15 points)
        if account1.get('location') and account2.get('location'):
            loc1 = account1['location'].lower()
            loc2 = account2['location'].lower()

            if loc1 == loc2:
                score += 15
                reasons.append("Same location")
            elif any(part in loc2 for part in loc1.split(',')):
                score += 10
                reasons.append("Similar location")

        # 3. Interest overlap (20 points max)
        interests1 = set(account1.get('interests', []))
        interests2 = set(account2.get('interests', []))

        if interests1 and interests2:
            overlap = interests1.intersection(interests2)
            if overlap:
                overlap_ratio = len(overlap) / max(len(interests1), len(interests2))
                interest_score = min(20, overlap_ratio * 20)
                score += interest_score
                reasons.append(f"Shared interests: {', '.join(list(overlap)[:3])}")

        # 4. Writing style similarity (15 points)
        if 'writing_style' in account1 and 'writing_style' in account2:
            style_score = self.compare_writing_styles(
                account1['writing_style'],
                account2['writing_style']
            )
            if style_score > 0:
                score += min(15, style_score)
                reasons.append("Similar writing style")

        # 5. Cross-references (20 points)
        if account1.get('url') in str(account2.get('bio', '')):
            score += 20
            reasons.append("Direct cross-reference found")

        return score, reasons

    def rank_candidate_accounts(
        self,
        known_account: Dict,
        candidates: List[Dict]
    ) -> List[Tuple[Dict, float, List[str]]]:
        """
        Rank candidate accounts by similarity to known account

        Returns:
            List of (account, score, reasons) sorted by score
        """
        ranked = []

        for candidate in candidates:
            score, reasons = self.calculate_account_similarity(known_account, candidate)
            ranked.append((candidate, score, reasons))

        # Sort by score (highest first)
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    # ========== COMPREHENSIVE ANALYSIS ==========

    def build_behavioral_profile(self, account_data: Dict) -> Dict:
        """
        Build complete behavioral profile from account data

        Args:
            account_data: Dict with 'content', 'bio', 'posts', etc.

        Returns:
            Comprehensive behavioral fingerprint
        """
        profile = {
            'interests': set(),
            'writing_style': {},
            'activity_patterns': {},
            'themes': []
        }

        # Extract from bio
        bio = account_data.get('bio', '')
        if bio:
            profile['interests'].update(self.extract_interests(bio))
            profile['writing_style'] = self.analyze_writing_style(bio)

        # Extract from posts
        posts = account_data.get('posts', [])
        if posts:
            all_content = ' '.join(p.get('content', '') for p in posts)
            profile['interests'].update(self.extract_interests(all_content))
            profile['activity_patterns'] = self.extract_activity_patterns(posts)

        # Convert set to list for JSON serialization
        profile['interests'] = list(profile['interests'])

        return profile


def demo_behavioral_analysis():
    """Demo showing behavioral analysis in action"""
    analyzer = BehavioralAnalyzer()

    # Example account 1
    account1 = {
        'name': 'Aryan Tuntune',
        'location': 'Mumbai, India',
        'bio': 'Flutter dev 📱 | Love Marvel movies 🦸 | Python enthusiast 🐍',
        'interests': ['flutter', 'python', 'marvel'],
        'writing_style': {
            'avg_sentence_length': 8.5,
            'emoji_count': 3,
            'exclamation_usage': 2
        }
    }

    # Example account 2 (different username but same person)
    account2 = {
        'name': 'Aryan T',
        'location': 'Mumbai',
        'bio': 'Mobile dev | MCU fan | Coding in Python & Dart',
        'interests': ['python', 'dart', 'mcu', 'marvel'],
        'writing_style': {
            'avg_sentence_length': 7.0,
            'emoji_count': 0,
            'exclamation_usage': 1
        }
    }

    score, reasons = analyzer.calculate_account_similarity(account1, account2)

    print(f"Similarity Score: {score}/100")
    print(f"Reasons: {reasons}")

    # Generate interest-based usernames
    usernames = analyzer.generate_interest_based_usernames(
        account1['interests'],
        'aryan'
    )

    print(f"\nPredicted usernames based on interests:")
    print(usernames[:15])


if __name__ == "__main__":
    demo_behavioral_analysis()
