"""
ML-based Username Generator: Markov chain-based username prediction
Learns patterns from known usernames to generate realistic variations
"""

import random
import re
from typing import List, Set, Dict
from collections import defaultdict, Counter
from .utils import setup_logger

logger = setup_logger(__name__)


class MarkovUsernameGenerator:
    """
    Generate usernames using Markov chains

    Features:
    - Learn patterns from existing usernames
    - Generate statistically likely variations
    - Character-level and word-level models
    - Contextual username generation
    """

    def __init__(self, order: int = 2):
        """
        Args:
            order: Markov chain order (2 = bigrams, 3 = trigrams)
        """
        self.order = order
        self.char_model = defaultdict(Counter)  # Character-level model
        self.word_model = defaultdict(Counter)  # Word-level model
        self.trained = False

    def train(self, usernames: List[str]):
        """
        Train Markov models on existing usernames

        Args:
            usernames: List of known usernames
        """
        if not usernames:
            logger.warning("No usernames provided for training")
            return

        logger.info(f"Training on {len(usernames)} usernames")

        # Train character-level model
        for username in usernames:
            username = username.lower()

            # Add start/end markers
            padded = '^' * self.order + username + '$'

            # Build n-gram model
            for i in range(len(padded) - self.order):
                context = padded[i:i+self.order]
                next_char = padded[i+self.order]
                self.char_model[context][next_char] += 1

        # Train word-level model (for usernames with separators)
        for username in usernames:
            # Split on separators
            parts = re.split(r'[_\-.]', username.lower())

            if len(parts) > 1:
                # Add start/end markers
                parts = ['^'] * self.order + parts + ['$']

                # Build n-gram model
                for i in range(len(parts) - self.order):
                    context = tuple(parts[i:i+self.order])
                    next_word = parts[i+self.order]
                    self.word_model[context][next_word] += 1

        self.trained = True
        logger.info(f"Training complete: {len(self.char_model)} character patterns, "
                   f"{len(self.word_model)} word patterns")

    def generate_char_based(self, max_length: int = 15, count: int = 10) -> List[str]:
        """
        Generate usernames using character-level Markov model

        Args:
            max_length: Maximum username length
            count: Number of usernames to generate

        Returns:
            List of generated usernames
        """
        if not self.trained:
            logger.warning("Model not trained. Call train() first.")
            return []

        usernames = set()

        attempts = 0
        max_attempts = count * 10

        while len(usernames) < count and attempts < max_attempts:
            attempts += 1

            # Start with initial context
            username = '^' * self.order

            for _ in range(max_length):
                context = username[-self.order:]

                if context not in self.char_model:
                    break

                # Get possible next characters
                possibilities = self.char_model[context]

                # Weighted random choice
                total = sum(possibilities.values())
                rand = random.randint(1, total)

                cumulative = 0
                next_char = None

                for char, count in possibilities.items():
                    cumulative += count
                    if cumulative >= rand:
                        next_char = char
                        break

                # End if we hit the end marker
                if next_char == '$':
                    break

                username += next_char

            # Remove start markers
            username = username.replace('^', '')

            # Validate
            if 3 <= len(username) <= max_length and username.isalnum():
                usernames.add(username)

        return list(usernames)

    def generate_word_based(self, separator: str = '_', count: int = 10) -> List[str]:
        """
        Generate usernames using word-level Markov model

        Args:
            separator: Separator to use between words
            count: Number of usernames to generate

        Returns:
            List of generated usernames
        """
        if not self.trained or not self.word_model:
            logger.warning("Word model not trained or empty")
            return []

        usernames = set()

        attempts = 0
        max_attempts = count * 10

        while len(usernames) < count and attempts < max_attempts:
            attempts += 1

            # Start with initial context
            parts = ['^'] * self.order

            for _ in range(5):  # Max 5 parts
                context = tuple(parts[-self.order:])

                if context not in self.word_model:
                    break

                # Get possible next words
                possibilities = self.word_model[context]

                # Weighted random choice
                total = sum(possibilities.values())
                rand = random.randint(1, total)

                cumulative = 0
                next_word = None

                for word, count in possibilities.items():
                    cumulative += count
                    if cumulative >= rand:
                        next_word = word
                        break

                # End if we hit the end marker
                if next_word == '$':
                    break

                parts.append(next_word)

            # Remove markers and join
            parts = [p for p in parts if p != '^']

            if len(parts) >= 2:
                username = separator.join(parts)

                # Validate
                if len(username) <= 30:
                    usernames.add(username)

        return list(usernames)

    def generate_hybrid(
        self,
        base_name: str,
        interests: List[str] = None,
        count: int = 20
    ) -> List[str]:
        """
        Generate usernames combining Markov chains with context

        Args:
            base_name: Base username/name
            interests: List of interests/keywords
            count: Number of usernames to generate

        Returns:
            List of generated usernames
        """
        usernames = set()

        # Character-based variations
        if self.trained:
            char_based = self.generate_char_based(count=count//2)
            usernames.update(char_based)

            # Word-based variations
            word_based = self.generate_word_based(count=count//2)
            usernames.update(word_based)

        # Combine with base name
        base_clean = re.sub(r'[^a-z0-9]', '', base_name.lower())

        if self.trained:
            # Generate suffixes using char model
            for i in range(count//4):
                suffix = self._generate_suffix(length=random.randint(3, 6))
                if suffix:
                    usernames.add(f"{base_clean}{suffix}")
                    usernames.add(f"{base_clean}_{suffix}")

            # Generate prefixes
            for i in range(count//4):
                prefix = self._generate_prefix(length=random.randint(3, 6))
                if prefix:
                    usernames.add(f"{prefix}{base_clean}")
                    usernames.add(f"{prefix}_{base_clean}")

        # Combine with interests
        if interests:
            for interest in interests[:5]:
                interest_clean = re.sub(r'[^a-z0-9]', '', interest.lower())

                usernames.add(f"{base_clean}_{interest_clean}")
                usernames.add(f"{interest_clean}_{base_clean}")
                usernames.add(f"{base_clean}{interest_clean}")

                # With numbers
                for num in [random.randint(1, 99), random.randint(100, 999)]:
                    usernames.add(f"{base_clean}_{interest_clean}{num}")
                    usernames.add(f"{interest_clean}_{base_clean}{num}")

        return list(usernames)[:count]

    def _generate_suffix(self, length: int = 5) -> str:
        """Generate a suffix using character model"""
        if not self.trained:
            return ""

        # Start from common suffix patterns
        suffix = ""

        for _ in range(length):
            if len(suffix) < self.order:
                context = ('^' * (self.order - len(suffix))) + suffix
            else:
                context = suffix[-self.order:]

            if context not in self.char_model:
                break

            possibilities = self.char_model[context]
            total = sum(possibilities.values())

            if total == 0:
                break

            rand = random.randint(1, total)
            cumulative = 0

            for char, count in possibilities.items():
                cumulative += count
                if cumulative >= rand:
                    if char != '$':
                        suffix += char
                    break

        return suffix if suffix.isalnum() else ""

    def _generate_prefix(self, length: int = 5) -> str:
        """Generate a prefix using character model"""
        # Similar to suffix but builds forward
        return self._generate_suffix(length)

    def score_username_likelihood(self, username: str) -> float:
        """
        Score how likely a username is based on learned patterns

        Args:
            username: Username to score

        Returns:
            Likelihood score (0-1, higher = more likely)
        """
        if not self.trained:
            return 0.5

        username = username.lower()
        padded = '^' * self.order + username + '$'

        total_score = 0
        count = 0

        # Calculate average n-gram probability
        for i in range(len(padded) - self.order):
            context = padded[i:i+self.order]
            next_char = padded[i+self.order]

            if context in self.char_model:
                char_counts = self.char_model[context]
                total = sum(char_counts.values())

                if next_char in char_counts:
                    prob = char_counts[next_char] / total
                    total_score += prob
                    count += 1

        if count == 0:
            return 0.0

        avg_score = total_score / count

        return avg_score

    def filter_likely_usernames(
        self,
        usernames: List[str],
        threshold: float = 0.3
    ) -> List[str]:
        """
        Filter usernames by likelihood score

        Args:
            usernames: List of candidate usernames
            threshold: Minimum likelihood score (0-1)

        Returns:
            Filtered list of likely usernames
        """
        if not self.trained:
            return usernames

        scored = [(u, self.score_username_likelihood(u)) for u in usernames]

        # Filter by threshold
        filtered = [u for u, score in scored if score >= threshold]

        # Sort by score
        filtered_scored = [(u, self.score_username_likelihood(u)) for u in filtered]
        filtered_scored.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Filtered {len(usernames)} → {len(filtered)} usernames (threshold={threshold})")

        return [u for u, score in filtered_scored]


# Convenience function
def get_ml_username_generator(training_usernames: List[str] = None) -> MarkovUsernameGenerator:
    """
    Get ML username generator instance

    Args:
        training_usernames: Optional list of usernames to train on

    Returns:
        Trained generator instance
    """
    generator = MarkovUsernameGenerator(order=2)

    if training_usernames:
        generator.train(training_usernames)

    return generator


# Default training data (common username patterns)
DEFAULT_TRAINING_DATA = [
    'john_doe', 'jane_smith', 'mike_jones', 'sarah_wilson',
    'alex_brown', 'chris_davis', 'pat_miller', 'sam_garcia',
    'techguru', 'codewizard', 'dev_master', 'python_ninja',
    'data_scientist', 'ml_engineer', 'web_developer', 'designer_pro',
    'gamer_legend', 'pro_player', 'stream_king', 'esports_champion',
    'photo_artist', 'music_lover', 'travel_bug', 'food_critic',
    'fitness_freak', 'gym_rat', 'runner_daily', 'yoga_master',
    'marvel_fan', 'dc_comics', 'star_wars', 'anime_otaku',
    'crypto_trader', 'stock_guru', 'invest_smart', 'finance_wizard',
]
