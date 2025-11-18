#!/usr/bin/env python3
"""
Local AI Engine - Hugging Face model for local AI reasoning
Provides on-device inference for intelligent account verification
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    pipeline
)
from .utils import setup_logger

logger = setup_logger(__name__)


class LocalAI:
    """
    Local AI reasoning engine using Hugging Face models
    Provides on-device AI capabilities for account verification
    """

    def __init__(self, model_name: str = "microsoft/phi-2", cache_dir: str = "data/models"):
        """
        Initialize local AI with pre-trained model

        Args:
            model_name: Hugging Face model identifier
                - "microsoft/phi-2" (2.7B params, good reasoning)
                - "TinyLlama/TinyLlama-1.1B-Chat-v1.0" (1.1B params, faster)
                - "distilbert-base-uncased" (66M params, classification only)
            cache_dir: Directory to cache downloaded models
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Model components
        self.tokenizer = None
        self.model = None
        self.text_generator = None
        self.classifier = None

        # Load model lazily on first use
        self._model_loaded = False

    def load_model(self):
        """Load model into memory (lazy loading)"""
        if self._model_loaded:
            return

        logger.info(f"Loading model: {self.model_name}...")
        logger.info("This may take 1-2 minutes on first run (downloads ~5GB)")

        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                trust_remote_code=True
            )

            # Load model with optimizations
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )

            if self.device == "cpu":
                self.model = self.model.to(self.device)

            # Create text generation pipeline
            self.text_generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.95
            )

            self._model_loaded = True
            logger.info("✅ Model loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.warning("Falling back to rule-based analysis")
            self._model_loaded = False

    def analyze_account_bio(self, bio: str, target_profile: Dict) -> Dict:
        """
        Analyze if account bio matches target profile

        Args:
            bio: Account bio/description text
            target_profile: Target profile from profiler

        Returns:
            {
                'is_match': bool,
                'confidence': float (0-100),
                'reasoning': str,
                'extracted_info': dict
            }
        """
        if not bio:
            return {
                'is_match': False,
                'confidence': 0,
                'reasoning': 'No bio available',
                'extracted_info': {}
            }

        # Try AI analysis first
        if self._model_loaded:
            try:
                return self._ai_analyze_bio(bio, target_profile)
            except Exception as e:
                logger.warning(f"AI analysis failed, using rule-based: {e}")

        # Fallback to rule-based
        return self._rule_based_bio_analysis(bio, target_profile)

    def _ai_analyze_bio(self, bio: str, profile: Dict) -> Dict:
        """AI-powered bio analysis"""
        self.load_model()

        # Construct prompt
        prompt = self._build_bio_analysis_prompt(bio, profile)

        # Generate response
        response = self.text_generator(
            prompt,
            max_new_tokens=256,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id
        )[0]['generated_text']

        # Extract answer from response
        result = self._parse_bio_analysis_response(response)
        return result

    def _build_bio_analysis_prompt(self, bio: str, profile: Dict) -> str:
        """Build prompt for bio analysis"""
        prompt = f"""Analyze if this social media bio matches the target profile.

TARGET PROFILE:
- Name: {profile.get('full_name', 'N/A')}
- Location: {profile.get('current_location', 'N/A')}
- Occupation: {profile.get('occupation', 'N/A')}
- Skills: {', '.join(profile.get('skills', [])[:5])}
- Interests: {', '.join(profile.get('interests', [])[:5])}

ACCOUNT BIO:
{bio}

Does this bio belong to the target? Consider:
1. Location mentions
2. Professional background
3. Skills/technologies
4. Interests/hobbies
5. Writing style

Answer in JSON format:
{{
    "is_match": true/false,
    "confidence": 0-100,
    "reasoning": "brief explanation",
    "extracted_info": {{
        "location": "if mentioned",
        "occupation": "if mentioned",
        "interests": ["list"]
    }}
}}

Analysis:"""
        return prompt

    def _parse_bio_analysis_response(self, response: str) -> Dict:
        """Parse AI response for bio analysis"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result

        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")

        # Fallback: basic sentiment
        return {
            'is_match': True,
            'confidence': 50,
            'reasoning': 'AI analysis inconclusive',
            'extracted_info': {}
        }

    def _rule_based_bio_analysis(self, bio: str, profile: Dict) -> Dict:
        """Fallback rule-based bio analysis"""
        bio_lower = bio.lower()
        score = 0
        max_score = 0
        matches = []

        # Check location (30 points)
        max_score += 30
        if profile.get('current_location'):
            location = profile['current_location'].lower()
            if location in bio_lower:
                score += 30
                matches.append(f"location: {profile['current_location']}")
            elif any(loc.lower() in bio_lower for loc in profile.get('previous_locations', [])):
                score += 15
                matches.append("previous location")

        # Check occupation (25 points)
        max_score += 25
        if profile.get('occupation'):
            if profile['occupation'].lower() in bio_lower:
                score += 25
                matches.append(f"occupation: {profile['occupation']}")

        # Check skills (25 points)
        max_score += 25
        if profile.get('skills'):
            skill_matches = [s for s in profile['skills'] if s.lower() in bio_lower]
            if skill_matches:
                score += min(25, len(skill_matches) * 8)
                matches.append(f"skills: {', '.join(skill_matches[:3])}")

        # Check interests (20 points)
        max_score += 20
        if profile.get('interests'):
            interest_matches = [i for i in profile['interests'] if i.lower() in bio_lower]
            if interest_matches:
                score += min(20, len(interest_matches) * 7)
                matches.append(f"interests: {', '.join(interest_matches[:3])}")

        # Calculate confidence
        confidence = (score / max_score * 100) if max_score > 0 else 50

        return {
            'is_match': confidence >= 40,
            'confidence': confidence,
            'reasoning': f"Matched: {', '.join(matches)}" if matches else "No clear matches",
            'extracted_info': {}
        }

    def compare_accounts(self, account1: Dict, account2: Dict) -> Dict:
        """
        Determine if two accounts belong to same person

        Args:
            account1, account2: Account dictionaries with bio, name, etc.

        Returns:
            {
                'same_person': bool,
                'confidence': float (0-100),
                'reasoning': str
            }
        """
        if self._model_loaded:
            try:
                return self._ai_compare_accounts(account1, account2)
            except Exception as e:
                logger.warning(f"AI comparison failed, using rule-based: {e}")

        return self._rule_based_comparison(account1, account2)

    def _ai_compare_accounts(self, acc1: Dict, acc2: Dict) -> Dict:
        """AI-powered account comparison"""
        self.load_model()

        prompt = f"""Compare these two social media accounts. Are they the same person?

ACCOUNT 1:
- Platform: {acc1.get('platform', 'unknown')}
- Name: {acc1.get('name', 'N/A')}
- Bio: {acc1.get('bio', 'N/A')}
- Location: {acc1.get('location', 'N/A')}

ACCOUNT 2:
- Platform: {acc2.get('platform', 'unknown')}
- Name: {acc2.get('name', 'N/A')}
- Bio: {acc2.get('bio', 'N/A')}
- Location: {acc2.get('location', 'N/A')}

Consider:
1. Name similarity
2. Bio content overlap
3. Location consistency
4. Writing style
5. Mentioned interests/skills

Answer in JSON:
{{
    "same_person": true/false,
    "confidence": 0-100,
    "reasoning": "explanation"
}}

Analysis:"""

        response = self.text_generator(
            prompt,
            max_new_tokens=200,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id
        )[0]['generated_text']

        return self._parse_comparison_response(response)

    def _parse_comparison_response(self, response: str) -> Dict:
        """Parse AI comparison response"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse comparison: {e}")

        return {
            'same_person': False,
            'confidence': 50,
            'reasoning': 'AI analysis inconclusive'
        }

    def _rule_based_comparison(self, acc1: Dict, acc2: Dict) -> Dict:
        """Fallback rule-based comparison"""
        score = 0
        reasons = []

        # Name similarity (40 points)
        name1 = (acc1.get('name') or '').lower()
        name2 = (acc2.get('name') or '').lower()

        if name1 and name2:
            if name1 == name2:
                score += 40
                reasons.append("exact name match")
            elif name1 in name2 or name2 in name1:
                score += 25
                reasons.append("partial name match")

        # Location consistency (30 points)
        loc1 = (acc1.get('location') or '').lower()
        loc2 = (acc2.get('location') or '').lower()

        if loc1 and loc2:
            if loc1 == loc2:
                score += 30
                reasons.append("same location")
            elif loc1 in loc2 or loc2 in loc1:
                score += 15
                reasons.append("related locations")

        # Bio similarity (30 points)
        bio1 = (acc1.get('bio') or '').lower()
        bio2 = (acc2.get('bio') or '').lower()

        if bio1 and bio2:
            # Count common words (excluding common stopwords)
            words1 = set(bio1.split())
            words2 = set(bio2.split())
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}

            common_words = (words1 & words2) - stopwords
            if len(common_words) >= 5:
                score += 30
                reasons.append(f"{len(common_words)} common keywords")
            elif len(common_words) >= 2:
                score += 15
                reasons.append(f"{len(common_words)} common keywords")

        return {
            'same_person': score >= 50,
            'confidence': min(100, score),
            'reasoning': ', '.join(reasons) if reasons else 'No significant matches'
        }

    def generate_username_variations(self, base_name: str, profile: Dict, count: int = 10) -> List[str]:
        """
        Generate intelligent username variations

        Args:
            base_name: Base username/name
            profile: Target profile for context
            count: Number of variations to generate

        Returns:
            List of username variations
        """
        if self._model_loaded:
            try:
                return self._ai_generate_usernames(base_name, profile, count)
            except Exception as e:
                logger.warning(f"AI username generation failed: {e}")

        # Fallback to rule-based from ml_username_gen.py
        return self._rule_based_usernames(base_name, count)

    def _ai_generate_usernames(self, base_name: str, profile: Dict, count: int) -> List[str]:
        """AI-powered username generation"""
        self.load_model()

        interests = ', '.join(profile.get('interests', [])[:3])
        skills = ', '.join(profile.get('skills', [])[:3])

        prompt = f"""Generate {count} creative username variations for: {base_name}

Context:
- Interests: {interests}
- Skills: {skills}
- Age range: {profile.get('age_range', 'unknown')}

Common patterns:
- Add numbers: username123
- Add underscores: user_name
- Professional: firstname.lastname
- Hobby-based: gamer_username
- Year: username2024

Generate {count} realistic usernames (one per line):
"""

        response = self.text_generator(
            prompt,
            max_new_tokens=150,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id
        )[0]['generated_text']

        # Extract usernames from response
        lines = response.split('\n')
        usernames = []
        for line in lines:
            line = line.strip()
            if line and len(line) <= 30 and line.replace('_', '').replace('.', '').isalnum():
                usernames.append(line)

        return usernames[:count]

    def _rule_based_usernames(self, base_name: str, count: int) -> List[str]:
        """Fallback rule-based username generation"""
        import random

        variations = []
        name_lower = base_name.lower().replace(' ', '')

        # Pattern 1: Add numbers
        for i in range(3):
            variations.append(f"{name_lower}{random.randint(1, 999)}")

        # Pattern 2: Add underscores
        parts = base_name.lower().split()
        if len(parts) >= 2:
            variations.append('_'.join(parts))
            variations.append(parts[0] + '_' + parts[-1][0])

        # Pattern 3: Professional
        if len(parts) >= 2:
            variations.append(f"{parts[0]}.{parts[-1]}")

        # Pattern 4: Add year
        for year in [2024, 2023, 2022]:
            variations.append(f"{name_lower}{year}")

        # Pattern 5: Common suffixes
        for suffix in ['dev', 'official', 'real', 'hq']:
            variations.append(f"{name_lower}{suffix}")

        return list(set(variations))[:count]

    def summarize_investigation(self, accounts: List[Dict], profile: Dict) -> str:
        """
        Generate human-readable investigation summary

        Args:
            accounts: List of discovered accounts
            profile: Target profile

        Returns:
            Natural language summary
        """
        if self._model_loaded:
            try:
                return self._ai_summarize(accounts, profile)
            except Exception as e:
                logger.warning(f"AI summarization failed: {e}")

        return self._rule_based_summary(accounts, profile)

    def _ai_summarize(self, accounts: List[Dict], profile: Dict) -> str:
        """AI-powered investigation summary"""
        self.load_model()

        accounts_text = "\n".join([
            f"- {acc.get('platform', 'unknown')}: {acc.get('name', 'N/A')} ({acc.get('url', '')})"
            for acc in accounts[:10]
        ])

        prompt = f"""Summarize this OSINT investigation in 3-4 sentences.

TARGET: {profile.get('full_name', 'Unknown')}
ACCOUNTS FOUND: {len(accounts)}

Discovered accounts:
{accounts_text}

Write a professional summary highlighting:
1. Number of accounts found
2. Main platforms discovered
3. Key insights about the target
4. Overall confidence

Summary:"""

        response = self.text_generator(
            prompt,
            max_new_tokens=200,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id
        )[0]['generated_text']

        # Extract summary (text after "Summary:")
        if "Summary:" in response:
            summary = response.split("Summary:")[-1].strip()
            return summary

        return response

    def _rule_based_summary(self, accounts: List[Dict], profile: Dict) -> str:
        """Fallback rule-based summary"""
        name = profile.get('full_name', 'the target')
        count = len(accounts)

        platforms = {}
        for acc in accounts:
            platform = acc.get('platform', 'unknown')
            platforms[platform] = platforms.get(platform, 0) + 1

        top_platforms = sorted(platforms.items(), key=lambda x: x[1], reverse=True)[:3]
        platform_text = ', '.join([f"{p} ({c})" for p, c in top_platforms])

        summary = f"Investigation of {name} discovered {count} accounts across {len(platforms)} platforms. "
        summary += f"Primary presence: {platform_text}. "

        if count >= 10:
            summary += f"High online visibility suggests active digital footprint."
        elif count >= 5:
            summary += f"Moderate online presence detected."
        else:
            summary += f"Limited public online presence."

        return summary

    def get_model_info(self) -> Dict:
        """Get information about loaded model"""
        return {
            'model_name': self.model_name,
            'loaded': self._model_loaded,
            'device': self.device,
            'cuda_available': torch.cuda.is_available(),
            'cache_dir': str(self.cache_dir)
        }


# Convenience functions
def create_local_ai(model_name: str = "microsoft/phi-2") -> LocalAI:
    """
    Create LocalAI instance

    Recommended models:
    - "microsoft/phi-2" - Best reasoning (2.7B params, ~5GB download)
    - "TinyLlama/TinyLlama-1.1B-Chat-v1.0" - Faster (1.1B params, ~2GB)

    Args:
        model_name: Hugging Face model identifier

    Returns:
        LocalAI instance
    """
    return LocalAI(model_name=model_name)
