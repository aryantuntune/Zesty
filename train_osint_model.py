#!/usr/bin/env python3
"""
Fine-tune AI model for OSINT tasks
Trains the model on investigation-specific examples
"""

import os
import json
from datetime import datetime
from typing import List, Dict
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import sys

sys.path.insert(0, 'src')
from utils import setup_logger

logger = setup_logger(__name__)


class OSINTModelTrainer:
    """
    Fine-tune language models for OSINT tasks
    """

    def __init__(
        self,
        base_model: str = "microsoft/phi-2",
        output_dir: str = "data/models/osint-specialist"
    ):
        """
        Initialize trainer

        Args:
            base_model: Base model to fine-tune
            output_dir: Where to save fine-tuned model
        """
        self.base_model = base_model
        self.output_dir = output_dir

        self.tokenizer = None
        self.model = None
        self.training_data = []

    def load_base_model(self):
        """Load base model for fine-tuning"""
        print(f"📥 Loading base model: {self.base_model}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model,
            trust_remote_code=True
        )

        # Set padding token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )

        print("✅ Base model loaded!")

    def create_osint_training_data(self) -> List[Dict]:
        """
        Create synthetic training data for OSINT tasks

        This creates example Q&A pairs for:
        1. Bio analysis (is this the target?)
        2. Account comparison (same person?)
        3. Username prediction

        Returns:
            List of training examples
        """

        print("\n🎓 Creating OSINT training dataset...")

        training_examples = []

        # ================================================================
        # TASK 1: Bio Analysis Examples
        # ================================================================

        bio_examples = [
            # Positive matches
            {
                "target": {"name": "John Smith", "location": "San Francisco", "occupation": "Software Engineer", "skills": ["Python", "ML"]},
                "bio": "Software engineer from SF. Love Python and machine learning. Building cool stuff.",
                "is_match": True,
                "confidence": 95,
                "reasoning": "Perfect match: SF location, software engineer occupation, Python and ML skills mentioned."
            },
            {
                "target": {"name": "Sarah Johnson", "location": "New York", "occupation": "Designer", "skills": ["UI/UX", "Figma"]},
                "bio": "Product designer based in NYC. Figma enthusiast. Making beautiful interfaces.",
                "is_match": True,
                "confidence": 90,
                "reasoning": "Strong match: NYC matches New York, designer occupation, Figma skill mentioned."
            },
            {
                "target": {"name": "Mike Chen", "location": "Seattle", "occupation": "Data Scientist", "skills": ["Python", "TensorFlow"]},
                "bio": "Data scientist @ Amazon in Seattle. Python, TensorFlow, PyTorch. Love hiking.",
                "is_match": True,
                "confidence": 98,
                "reasoning": "Excellent match: Seattle location, data scientist occupation, Python and TensorFlow skills, Amazon is major Seattle employer."
            },

            # Negative matches (false positives)
            {
                "target": {"name": "John Smith", "location": "San Francisco", "occupation": "Software Engineer", "skills": ["Python", "ML"]},
                "bio": "High school student from Ohio. Love gaming and anime.",
                "is_match": False,
                "confidence": 5,
                "reasoning": "No match: Different location (Ohio vs SF), different occupation (student vs engineer), no relevant skills."
            },
            {
                "target": {"name": "Sarah Johnson", "location": "New York", "occupation": "Designer", "skills": ["UI/UX", "Figma"]},
                "bio": "Marketing manager in Los Angeles. Social media expert.",
                "is_match": False,
                "confidence": 10,
                "reasoning": "Poor match: Wrong location (LA vs NYC), wrong occupation (marketing vs design), no design skills mentioned."
            },

            # Partial matches (ambiguous)
            {
                "target": {"name": "Alex Wong", "location": "Toronto", "occupation": "Developer", "skills": ["JavaScript", "React"]},
                "bio": "Developer in Canada. Building web apps.",
                "is_match": True,
                "confidence": 65,
                "reasoning": "Moderate match: Canada includes Toronto, developer matches, but no specific JS/React mentioned."
            },
        ]

        for example in bio_examples:
            prompt = self._format_bio_analysis_prompt(example["target"], example["bio"])
            response = json.dumps({
                "is_match": example["is_match"],
                "confidence": example["confidence"],
                "reasoning": example["reasoning"]
            }, indent=2)

            training_examples.append({
                "text": f"{prompt}\n\nAnalysis:\n{response}"
            })

        # ================================================================
        # TASK 2: Account Comparison Examples
        # ================================================================

        comparison_examples = [
            # Same person
            {
                "account1": {"platform": "GitHub", "name": "johnsmith", "bio": "Software dev from SF", "location": "San Francisco"},
                "account2": {"platform": "LinkedIn", "name": "John Smith", "bio": "Software Engineer at Google, SF Bay Area", "location": "San Francisco, CA"},
                "same_person": True,
                "confidence": 92,
                "reasoning": "High likelihood same person: Name similarity, both in SF, both software-related, consistent professional context."
            },
            {
                "account1": {"platform": "Twitter", "name": "sarah_designs", "bio": "UI/UX designer. NYC.", "location": "New York"},
                "account2": {"platform": "Dribbble", "name": "sarahdesigns", "bio": "Product designer based in Brooklyn", "location": "Brooklyn, NY"},
                "same_person": True,
                "confidence": 88,
                "reasoning": "Likely same person: Similar usernames, both design-focused, Brooklyn is in NYC, consistent profession."
            },

            # Different people
            {
                "account1": {"platform": "GitHub", "name": "johnsmith", "bio": "Student developer learning Python", "location": "India"},
                "account2": {"platform": "LinkedIn", "name": "John Smith", "bio": "Senior VP at Goldman Sachs", "location": "New York"},
                "same_person": False,
                "confidence": 5,
                "reasoning": "Different people: Student vs senior executive, different countries, vastly different career stages."
            },
        ]

        for example in comparison_examples:
            prompt = self._format_comparison_prompt(example["account1"], example["account2"])
            response = json.dumps({
                "same_person": example["same_person"],
                "confidence": example["confidence"],
                "reasoning": example["reasoning"]
            }, indent=2)

            training_examples.append({
                "text": f"{prompt}\n\nAnalysis:\n{response}"
            })

        # ================================================================
        # TASK 3: Username Generation Examples
        # ================================================================

        username_examples = [
            {
                "name": "John Smith",
                "interests": ["Photography", "Gaming"],
                "skills": ["Python", "ML"],
                "usernames": ["johnsmith_photos", "gamer_john", "jsmith_dev", "johnsmith_ml", "pythonsmith", "john.smith", "smithjohn", "johnsmith123"]
            },
            {
                "name": "Sarah Chen",
                "interests": ["Travel", "Food"],
                "skills": ["Design", "UX"],
                "usernames": ["sarahchen_travels", "foodie_sarah", "sarah.chen", "sarahchen_design", "uxsarah", "chensarah", "sarahchen", "sarah_ux"]
            },
        ]

        for example in username_examples:
            prompt = f"""Generate username variations for: {example['name']}

Context:
- Interests: {', '.join(example['interests'])}
- Skills: {', '.join(example['skills'])}

Generate realistic usernames (one per line):
"""
            response = '\n'.join(example['usernames'])

            training_examples.append({
                "text": f"{prompt}\n{response}"
            })

        print(f"✅ Created {len(training_examples)} training examples")

        return training_examples

    def _format_bio_analysis_prompt(self, target: Dict, bio: str) -> str:
        """Format bio analysis prompt"""
        return f"""Analyze if this social media bio matches the target profile.

TARGET PROFILE:
- Name: {target.get('name')}
- Location: {target.get('location')}
- Occupation: {target.get('occupation')}
- Skills: {', '.join(target.get('skills', []))}

ACCOUNT BIO:
{bio}

Does this bio belong to the target? Consider:
1. Location mentions
2. Professional background
3. Skills/technologies
4. Interests/hobbies

Answer in JSON format:
{{
    "is_match": true/false,
    "confidence": 0-100,
    "reasoning": "brief explanation"
}}"""

    def _format_comparison_prompt(self, acc1: Dict, acc2: Dict) -> str:
        """Format account comparison prompt"""
        return f"""Compare these two social media accounts. Are they the same person?

ACCOUNT 1:
- Platform: {acc1.get('platform')}
- Name: {acc1.get('name')}
- Bio: {acc1.get('bio')}
- Location: {acc1.get('location')}

ACCOUNT 2:
- Platform: {acc2.get('platform')}
- Name: {acc2.get('name')}
- Bio: {acc2.get('bio')}
- Location: {acc2.get('location')}

Consider:
1. Name similarity
2. Location consistency
3. Bio content overlap
4. Professional context

Answer in JSON:
{{
    "same_person": true/false,
    "confidence": 0-100,
    "reasoning": "explanation"
}}"""

    def prepare_dataset(self, examples: List[Dict]) -> Dataset:
        """
        Prepare dataset for training

        Args:
            examples: List of training examples

        Returns:
            HuggingFace Dataset
        """
        print("\n📦 Preparing dataset...")

        # Tokenize examples
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                padding="max_length",
                truncation=True,
                max_length=512
            )

        dataset = Dataset.from_list(examples)
        tokenized_dataset = dataset.map(tokenize_function, batched=True)

        print(f"✅ Dataset ready: {len(tokenized_dataset)} examples")

        return tokenized_dataset

    def train(
        self,
        training_data: Dataset,
        epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-5
    ):
        """
        Fine-tune the model

        Args:
            training_data: Prepared dataset
            epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
        """

        print("\n🎯 Starting fine-tuning...")
        print(f"   Epochs: {epochs}")
        print(f"   Batch size: {batch_size}")
        print(f"   Learning rate: {learning_rate}")

        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            overwrite_output_dir=True,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            save_steps=100,
            save_total_limit=2,
            learning_rate=learning_rate,
            warmup_steps=10,
            logging_steps=10,
            fp16=torch.cuda.is_available(),  # Use mixed precision on GPU
            logging_dir=f"{self.output_dir}/logs",
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # Causal LM, not masked LM
        )

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=training_data,
            data_collator=data_collator,
        )

        # Train!
        print("\n🚀 Training in progress...")
        trainer.train()

        print("\n✅ Training complete!")

    def save_model(self):
        """Save fine-tuned model"""
        print(f"\n💾 Saving model to: {self.output_dir}")

        self.model.save_pretrained(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)

        print("✅ Model saved!")
        print(f"\n📁 Saved to: {self.output_dir}")
        print("\nTo use this model:")
        print(f"   ai = LocalAI(model_name='{self.output_dir}')")

    def run_full_training(self, epochs: int = 3):
        """
        Complete training pipeline

        Args:
            epochs: Number of training epochs
        """

        print("="*70)
        print("🎓 OSINT MODEL FINE-TUNING")
        print("="*70)

        # Step 1: Load base model
        self.load_base_model()

        # Step 2: Create training data
        training_examples = self.create_osint_training_data()

        # Step 3: Prepare dataset
        dataset = self.prepare_dataset(training_examples)

        # Step 4: Train
        self.train(dataset, epochs=epochs)

        # Step 5: Save
        self.save_model()

        print("\n" + "="*70)
        print("🎉 TRAINING COMPLETE!")
        print("="*70)
        print("\n✅ Your OSINT-specialized model is ready!")
        print(f"\n📁 Location: {self.output_dir}")
        print("\n🚀 Usage:")
        print("   1. Edit src/local_ai.py")
        print(f"   2. Change model_name to: '{self.output_dir}'")
        print("   3. Run: python main_advanced_v3.py")
        print("\n💡 The fine-tuned model should be better at OSINT tasks!")


def create_custom_training_data(json_file: str) -> List[Dict]:
    """
    Load custom training data from JSON file

    Format:
    [
        {
            "prompt": "Question or task...",
            "response": "Expected answer..."
        },
        ...
    ]

    Args:
        json_file: Path to JSON training data

    Returns:
        Training examples
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    return [{"text": f"{ex['prompt']}\n{ex['response']}"} for ex in data]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fine-tune AI model for OSINT")
    parser.add_argument(
        "--base-model",
        default="microsoft/phi-2",
        help="Base model to fine-tune"
    )
    parser.add_argument(
        "--output-dir",
        default="data/models/osint-specialist",
        help="Output directory for fine-tuned model"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--custom-data",
        help="Path to custom training data JSON file (optional)"
    )
    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Quick test with 1 epoch (for testing)"
    )

    args = parser.parse_args()

    # Create trainer
    trainer = OSINTModelTrainer(
        base_model=args.base_model,
        output_dir=args.output_dir
    )

    # Custom training data if provided
    if args.custom_data:
        print(f"\n📂 Loading custom training data from: {args.custom_data}")
        trainer.load_base_model()
        examples = create_custom_training_data(args.custom_data)
        dataset = trainer.prepare_dataset(examples)
        epochs = 1 if args.quick_test else args.epochs
        trainer.train(dataset, epochs=epochs)
        trainer.save_model()
    else:
        # Use built-in OSINT examples
        epochs = 1 if args.quick_test else args.epochs
        trainer.run_full_training(epochs=epochs)

    print("\n✨ Done!")
