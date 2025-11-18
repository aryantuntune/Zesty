"""
Local NLP Engine: Advanced text analysis using spaCy
Runs entirely offline, no API calls
"""

import re
from typing import List, Dict, Set
from collections import Counter
from .utils import setup_logger

logger = setup_logger(__name__)

# Try to import spaCy
try:
    import spacy
    SPACY_AVAILABLE = True

    # Try to load model
    try:
        nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model loaded successfully")
    except OSError:
        logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
        SPACY_AVAILABLE = False
        nlp = None
except ImportError:
    logger.warning("spaCy not installed. Install with: pip install spacy")
    SPACY_AVAILABLE = False
    nlp = None


class LocalNLPEngine:
    """
    Advanced NLP analysis using spaCy (offline)
    Falls back to regex if spaCy unavailable
    """

    def __init__(self):
        self.nlp = nlp
        self.spacy_available = SPACY_AVAILABLE

        # Extended keyword databases
        self.tech_keywords = {
            # Programming languages
            'python', 'javascript', 'java', 'csharp', 'c++', 'cpp', 'c#', 'ruby', 'php',
            'swift', 'kotlin', 'dart', 'go', 'golang', 'rust', 'typescript', 'scala',

            # Frameworks/Libraries
            'react', 'angular', 'vue', 'nodejs', 'node.js', 'django', 'flask', 'fastapi',
            'spring', 'express', 'flutter', 'react native', 'tensorflow', 'pytorch', 'keras',

            # Technologies
            'ai', 'ml', 'machine learning', 'deep learning', 'nlp', 'computer vision',
            'blockchain', 'web3', 'cryptocurrency', 'cloud', 'aws', 'azure', 'gcp',
            'docker', 'kubernetes', 'devops', 'cicd', 'microservices',

            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',

            # Mobile
            'android', 'ios', 'mobile development', 'app development'
        }

        self.pop_culture_keywords = {
            # Movies/TV
            'marvel', 'mcu', 'avengers', 'iron man', 'spiderman', 'batman', 'superman',
            'star wars', 'mandalorian', 'harry potter', 'lord of the rings', 'game of thrones',

            # Anime/Manga
            'anime', 'manga', 'naruto', 'one piece', 'dragon ball', 'attack on titan',

            # Gaming
            'gaming', 'gamer', 'esports', 'valorant', 'league of legends', 'lol', 'dota',
            'fortnite', 'minecraft', 'call of duty', 'cod', 'apex legends', 'overwatch',

            # Music
            'music', 'musician', 'producer', 'dj', 'rapper', 'singer',

            # Other
            'photography', 'photographer', 'travel', 'traveler', 'fitness', 'gym',
            'cooking', 'foodie', 'reading', 'writing', 'blogging'
        }

        self.all_keywords = self.tech_keywords.union(self.pop_culture_keywords)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using spaCy NER
        Falls back to regex if spaCy unavailable
        """
        if not text:
            return {'technologies': [], 'organizations': [], 'locations': [], 'persons': []}

        if self.spacy_available and self.nlp:
            return self._extract_entities_spacy(text)
        else:
            return self._extract_entities_regex(text)

    def _extract_entities_spacy(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using spaCy"""
        doc = self.nlp(text)

        entities = {
            'technologies': [],
            'organizations': [],
            'locations': [],
            'persons': []
        }

        # Named Entity Recognition
        for ent in doc.ents:
            if ent.label_ == "ORG":
                entities['organizations'].append(ent.text)
            elif ent.label_ == "GPE" or ent.label_ == "LOC":
                entities['locations'].append(ent.text)
            elif ent.label_ == "PERSON":
                entities['persons'].append(ent.text)

        # Technology extraction (custom logic)
        text_lower = text.lower()
        for tech in self.tech_keywords:
            if tech in text_lower:
                entities['technologies'].append(tech)

        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _extract_entities_regex(self, text: str) -> Dict[str, List[str]]:
        """Fallback: Extract entities using regex"""
        entities = {
            'technologies': [],
            'organizations': [],
            'locations': [],
            'persons': []
        }

        text_lower = text.lower()

        # Extract technologies
        for keyword in self.all_keywords:
            if keyword in text_lower:
                entities['technologies'].append(keyword)

        # Basic location extraction (capitalized place names)
        location_pattern = r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,?\s*(?:India|USA|UK|Canada|China)?)\b'
        locations = re.findall(location_pattern, text)
        entities['locations'] = list(set(locations))

        return entities

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract technical skills from text
        """
        if not text:
            return []

        skills = []
        text_lower = text.lower()

        # Technology skills
        for tech in self.tech_keywords:
            if tech in text_lower:
                skills.append(tech)

        # Use spaCy for better extraction if available
        if self.spacy_available and self.nlp:
            doc = self.nlp(text)

            # Look for noun chunks that are skills
            for chunk in doc.noun_chunks:
                chunk_lower = chunk.text.lower()

                # Patterns like "experience in X", "expert in X"
                if any(word in chunk_lower for word in ['development', 'programming', 'developer', 'engineer']):
                    skills.append(chunk.text)

        return list(set(skills))

    def extract_interests(self, text: str) -> Set[str]:
        """
        Extract interests (tech + pop culture)
        Enhanced version of behavioral.py extract_interests
        """
        if not text:
            return set()

        interests = set()
        text_lower = text.lower()

        # Keyword matching
        for keyword in self.all_keywords:
            if keyword in text_lower:
                interests.add(keyword)

        # Hashtag extraction
        hashtags = re.findall(r'#(\w+)', text)
        interests.update(tag.lower() for tag in hashtags)

        # Use spaCy for better context understanding
        if self.spacy_available and self.nlp:
            doc = self.nlp(text)

            # Extract subjects of sentences (often interests)
            for token in doc:
                if token.dep_ == "nsubj" and token.pos_ == "NOUN":
                    if len(token.text) > 3:  # Filter short words
                        interests.add(token.text.lower())

        return interests

    def analyze_writing_complexity(self, text: str) -> Dict:
        """
        Analyze writing complexity
        """
        if not text:
            return {'complexity': 'unknown'}

        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        analysis = {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'complexity': 'simple'
        }

        # Determine complexity
        if analysis['avg_word_length'] > 6 and analysis['avg_sentence_length'] > 20:
            analysis['complexity'] = 'complex'
        elif analysis['avg_word_length'] > 5 and analysis['avg_sentence_length'] > 15:
            analysis['complexity'] = 'moderate'

        # If spaCy available, do deeper analysis
        if self.spacy_available and self.nlp:
            doc = self.nlp(text)

            # Count complex structures
            subordinate_clauses = sum(1 for token in doc if token.dep_ in ["advcl", "acl", "relcl"])

            if subordinate_clauses > len(sentences) * 0.3:
                analysis['complexity'] = 'complex'

        return analysis

    def extract_key_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extract key phrases from text
        """
        if not text:
            return []

        if self.spacy_available and self.nlp:
            doc = self.nlp(text)

            # Extract noun chunks as key phrases
            noun_chunks = [chunk.text for chunk in doc.noun_chunks]

            # Count frequency
            phrase_counts = Counter(noun_chunks)

            # Return top N
            return [phrase for phrase, count in phrase_counts.most_common(top_n)]
        else:
            # Fallback: extract capitalized phrases
            phrases = re.findall(r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b', text)
            return list(set(phrases))[:top_n]

    def compare_vocabulary(self, text1: str, text2: str) -> float:
        """
        Compare vocabulary overlap between two texts
        Returns similarity score 0-1
        """
        if not text1 or not text2:
            return 0.0

        # Tokenize
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))

        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has'}

        words1 = words1 - stopwords
        words2 = words2 - stopwords

        # Calculate Jaccard similarity
        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0


# Convenience function
def get_nlp_engine() -> LocalNLPEngine:
    """Get NLP engine instance"""
    return LocalNLPEngine()
