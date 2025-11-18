"""
Sentiment & Tone Analyzer: Emotional tone and sentiment analysis
Analyzes writing style, sentiment, and emotional patterns
"""

from typing import Dict, List, Tuple
import re
from collections import Counter
from .utils import setup_logger

logger = setup_logger(__name__)

# Try to import TextBlob
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
    logger.info("TextBlob available for sentiment analysis")
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not installed. Install with: pip install textblob")


class ToneAnalyzer:
    """
    Analyzes sentiment and tone of text

    Features:
    - Sentiment analysis (positive/negative/neutral)
    - Subjectivity detection (factual vs. opinionated)
    - Tone classification (professional, casual, humorous, etc.)
    - Emotional pattern matching
    """

    def __init__(self):
        self.use_textblob = TEXTBLOB_AVAILABLE

        # Tone indicators (keyword-based fallback)
        self.tone_keywords = {
            'professional': {
                'pleased', 'regarding', 'furthermore', 'therefore', 'however',
                'consequently', 'nevertheless', 'sincerely', 'respectfully'
            },
            'casual': {
                'yeah', 'nope', 'gonna', 'wanna', 'kinda', 'sorta',
                'cool', 'awesome', 'sweet', 'dude', 'hey'
            },
            'humorous': {
                'lol', 'lmao', 'haha', 'rofl', 'hilarious', 'funny',
                'joke', 'kidding', 'sarcasm', '😂', '🤣'
            },
            'technical': {
                'algorithm', 'implementation', 'function', 'debug', 'optimize',
                'compile', 'database', 'api', 'framework', 'repository'
            },
            'enthusiastic': {
                'amazing', 'fantastic', 'incredible', 'awesome', 'love',
                'excited', 'thrilled', 'brilliant', '!!!', '!!'
            },
            'negative': {
                'hate', 'terrible', 'awful', 'horrible', 'worst', 'sucks',
                'disappointed', 'frustrated', 'annoyed', 'angry'
            }
        }

        # Emoticon patterns
        self.emoticons = {
            'positive': [':)', ':-)', ':D', ':-D', '^_^', '^-^', ':3'],
            'negative': [':(', ':-(', 'D:', ':-/', ':-|'],
            'playful': [';)', ';-)', ':P', ':-P', ':p', 'xD']
        }

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text

        Returns:
            {
                'polarity': float,  # -1 to 1 (negative to positive)
                'subjectivity': float,  # 0 to 1 (objective to subjective)
                'classification': str  # 'positive', 'negative', 'neutral'
            }
        """
        if not text:
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'classification': 'neutral'
            }

        if self.use_textblob:
            return self._analyze_sentiment_textblob(text)
        else:
            return self._analyze_sentiment_keywords(text)

    def _analyze_sentiment_textblob(self, text: str) -> Dict:
        """Sentiment analysis using TextBlob"""
        try:
            blob = TextBlob(text)

            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Classify
            if polarity > 0.1:
                classification = 'positive'
            elif polarity < -0.1:
                classification = 'negative'
            else:
                classification = 'neutral'

            return {
                'polarity': round(polarity, 2),
                'subjectivity': round(subjectivity, 2),
                'classification': classification
            }

        except Exception as e:
            logger.warning(f"TextBlob sentiment analysis failed: {e}")
            return self._analyze_sentiment_keywords(text)

    def _analyze_sentiment_keywords(self, text: str) -> Dict:
        """Keyword-based sentiment analysis (fallback)"""
        text_lower = text.lower()

        # Count positive/negative words
        positive_words = {'good', 'great', 'awesome', 'excellent', 'love', 'happy',
                         'wonderful', 'fantastic', 'amazing', 'best', 'like', 'enjoy'}

        negative_words = {'bad', 'terrible', 'awful', 'hate', 'worst', 'horrible',
                         'disappointing', 'poor', 'dislike', 'sad', 'angry', 'frustrated'}

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        # Calculate polarity
        total = positive_count + negative_count
        if total > 0:
            polarity = (positive_count - negative_count) / total
        else:
            polarity = 0.0

        # Check for opinion indicators (subjectivity)
        opinion_indicators = {'think', 'feel', 'believe', 'opinion', 'seems', 'probably',
                            'might', 'should', 'would', 'could'}

        opinion_count = sum(1 for word in opinion_indicators if word in text_lower)
        subjectivity = min(opinion_count / 10, 1.0)  # Normalize

        # Classification
        if polarity > 0.2:
            classification = 'positive'
        elif polarity < -0.2:
            classification = 'negative'
        else:
            classification = 'neutral'

        return {
            'polarity': round(polarity, 2),
            'subjectivity': round(subjectivity, 2),
            'classification': classification
        }

    def detect_tone(self, text: str) -> Dict:
        """
        Detect overall tone of text

        Returns:
            {
                'primary_tone': str,
                'tone_scores': Dict[str, float],
                'confidence': float
            }
        """
        if not text:
            return {
                'primary_tone': 'unknown',
                'tone_scores': {},
                'confidence': 0.0
            }

        text_lower = text.lower()
        tone_scores = {}

        # Calculate score for each tone
        for tone, keywords in self.tone_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            tone_scores[tone] = score

        # Normalize scores
        total = sum(tone_scores.values())
        if total > 0:
            for tone in tone_scores:
                tone_scores[tone] = round(tone_scores[tone] / total, 2)

        # Find primary tone
        if tone_scores:
            primary_tone = max(tone_scores.items(), key=lambda x: x[1])
            confidence = primary_tone[1]
            primary_tone = primary_tone[0]
        else:
            primary_tone = 'neutral'
            confidence = 0.0

        return {
            'primary_tone': primary_tone,
            'tone_scores': tone_scores,
            'confidence': round(confidence, 2)
        }

    def analyze_formality(self, text: str) -> Dict:
        """
        Analyze formality level

        Returns:
            {
                'formality_score': float,  # 0-1 (casual to formal)
                'level': str  # 'very_casual', 'casual', 'neutral', 'formal', 'very_formal'
            }
        """
        if not text:
            return {
                'formality_score': 0.5,
                'level': 'neutral'
            }

        text_lower = text.lower()

        # Formal indicators
        formal_indicators = {
            'contractions': 0,  # Fewer contractions = more formal
            'slang': 0,
            'technical_terms': 0,
            'sentence_length': 0,
            'punctuation': 0
        }

        # Check for contractions (casual)
        contractions = ["n't", "'ll", "'re", "'ve", "'d", "'m", "gonna", "wanna"]
        formal_indicators['contractions'] = sum(1 for c in contractions if c in text_lower)

        # Check for slang (casual)
        slang_words = {'yeah', 'nope', 'yep', 'cool', 'dude', 'bro', 'lol', 'omg'}
        formal_indicators['slang'] = sum(1 for word in slang_words if word in text_lower)

        # Check for technical/formal terms
        formal_words = {'therefore', 'furthermore', 'however', 'consequently',
                       'nevertheless', 'regarding', 'pursuant'}
        formal_indicators['technical_terms'] = sum(1 for word in formal_words if word in text_lower)

        # Sentence length (longer = more formal)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            formal_indicators['sentence_length'] = 1 if avg_length > 15 else 0

        # Calculate formality score
        casual_score = formal_indicators['contractions'] + formal_indicators['slang']
        formal_score = formal_indicators['technical_terms'] + formal_indicators['sentence_length']

        total = casual_score + formal_score
        if total > 0:
            formality_score = formal_score / total
        else:
            formality_score = 0.5  # Neutral

        # Classify
        if formality_score > 0.8:
            level = 'very_formal'
        elif formality_score > 0.6:
            level = 'formal'
        elif formality_score > 0.4:
            level = 'neutral'
        elif formality_score > 0.2:
            level = 'casual'
        else:
            level = 'very_casual'

        return {
            'formality_score': round(formality_score, 2),
            'level': level
        }

    def detect_emoticons(self, text: str) -> Dict:
        """
        Detect and analyze emoticons/emojis

        Returns:
            {
                'count': int,
                'types': Dict[str, int],
                'emotional_expression': str
            }
        """
        emoticon_counts = {
            'positive': 0,
            'negative': 0,
            'playful': 0
        }

        for emotion_type, emoticons in self.emoticons.items():
            for emoticon in emoticons:
                emoticon_counts[emotion_type] += text.count(emoticon)

        total = sum(emoticon_counts.values())

        # Emoji pattern (Unicode emoji range)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+",
            flags=re.UNICODE
        )

        emojis = emoji_pattern.findall(text)
        total += len(emojis)

        # Determine emotional expression
        if total == 0:
            expression = 'unexpressive'
        elif emoticon_counts['positive'] > emoticon_counts['negative']:
            expression = 'cheerful'
        elif emoticon_counts['negative'] > emoticon_counts['positive']:
            expression = 'upset'
        elif emoticon_counts['playful'] > 0:
            expression = 'playful'
        else:
            expression = 'neutral'

        return {
            'count': total,
            'types': emoticon_counts,
            'emotional_expression': expression
        }

    def build_tone_profile(self, texts: List[str]) -> Dict:
        """
        Build comprehensive tone profile from multiple texts

        Args:
            texts: List of text samples (bios, posts, comments)

        Returns:
            Complete tone analysis profile
        """
        if not texts:
            return {
                'has_data': False,
                'reason': 'No text provided'
            }

        # Combine all texts
        combined_text = ' '.join(texts)

        # Analyze each component
        sentiment = self.analyze_sentiment(combined_text)
        tone = self.detect_tone(combined_text)
        formality = self.analyze_formality(combined_text)
        emoticons = self.detect_emoticons(combined_text)

        # Aggregate sentiment across all texts
        sentiments = [self.analyze_sentiment(text)['classification'] for text in texts]
        sentiment_distribution = Counter(sentiments)

        profile = {
            'has_data': True,
            'sample_size': len(texts),
            'sentiment': sentiment,
            'sentiment_distribution': dict(sentiment_distribution),
            'tone': tone,
            'formality': formality,
            'emoticons': emoticons,
            'overall_style': self._classify_overall_style(sentiment, tone, formality)
        }

        logger.info(f"Built tone profile: {tone['primary_tone']}, {sentiment['classification']}")

        return profile

    def _classify_overall_style(self, sentiment: Dict, tone: Dict, formality: Dict) -> str:
        """
        Classify overall writing style

        Returns:
            Style classification string
        """
        primary_tone = tone['primary_tone']
        sentiment_class = sentiment['classification']
        formality_level = formality['level']

        # Combine characteristics
        if primary_tone == 'professional' and formality_level in ['formal', 'very_formal']:
            return 'professional'
        elif primary_tone == 'casual' and sentiment_class == 'positive':
            return 'friendly'
        elif primary_tone == 'humorous':
            return 'humorous'
        elif primary_tone == 'technical':
            return 'technical'
        elif primary_tone == 'enthusiastic' and sentiment_class == 'positive':
            return 'enthusiastic'
        elif sentiment_class == 'negative':
            return 'critical'
        else:
            return 'balanced'

    def compare_tone_profiles(self, profile1: Dict, profile2: Dict) -> Tuple[float, List[str]]:
        """
        Compare two tone profiles for similarity

        Returns:
            (similarity_score, match_reasons)
            Score: 0-100
        """
        score = 0
        reasons = []

        if not profile1.get('has_data') or not profile2.get('has_data'):
            return (0, ['Insufficient tone data'])

        # Sentiment similarity (25 points)
        sent1 = profile1['sentiment']['classification']
        sent2 = profile2['sentiment']['classification']

        if sent1 == sent2:
            score += 25
            reasons.append(f"Same sentiment ({sent1})")

        # Polarity similarity (15 points)
        pol1 = profile1['sentiment']['polarity']
        pol2 = profile2['sentiment']['polarity']

        pol_diff = abs(pol1 - pol2)
        pol_score = max(0, 15 - (pol_diff * 15))
        score += pol_score

        # Tone similarity (25 points)
        tone1 = profile1['tone']['primary_tone']
        tone2 = profile2['tone']['primary_tone']

        if tone1 == tone2:
            score += 25
            reasons.append(f"Same tone ({tone1})")

        # Formality similarity (20 points)
        form1 = profile1['formality']['level']
        form2 = profile2['formality']['level']

        if form1 == form2:
            score += 20
            reasons.append(f"Same formality level ({form1})")

        # Overall style match (15 points)
        style1 = profile1.get('overall_style', '')
        style2 = profile2.get('overall_style', '')

        if style1 == style2:
            score += 15
            reasons.append(f"Same writing style ({style1})")

        return (round(score, 1), reasons)


# Convenience function
def get_tone_analyzer() -> ToneAnalyzer:
    """Get tone analyzer instance"""
    return ToneAnalyzer()
