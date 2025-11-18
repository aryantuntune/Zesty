#!/usr/bin/env python3
"""
Example: How to change the AI model in DeepTrace

This shows different ways to select and configure AI models
"""

import sys
sys.path.insert(0, '../src')

from local_ai import LocalAI


# ================================================================
# EXAMPLE 1: Use default model (Phi-2)
# ================================================================

def example_default_model():
    """Use default Phi-2 model"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Default Model (Phi-2)")
    print("="*70 + "\n")

    # Create AI with default settings
    ai = LocalAI()

    print(f"Model: {ai.model_name}")
    print(f"Device: {ai.device}")
    print(f"Loaded: {ai._model_loaded}")

    # Model loads lazily on first use
    print("\n✅ AI engine ready (model will load on first use)")


# ================================================================
# EXAMPLE 2: Use TinyLlama (faster, smaller)
# ================================================================

def example_tinyllama():
    """Use TinyLlama for faster inference"""
    print("\n" + "="*70)
    print("EXAMPLE 2: TinyLlama (Faster)")
    print("="*70 + "\n")

    # Create AI with TinyLlama
    ai = LocalAI(model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0")

    print(f"Model: {ai.model_name}")
    print("Size: 1.1B parameters (~2GB download)")
    print("Speed: 2-3x faster than Phi-2")
    print("Quality: 80% of Phi-2's capabilities")

    print("\n✅ Good for quick investigations or limited hardware")


# ================================================================
# EXAMPLE 3: Use Mistral-7B (most powerful)
# ================================================================

def example_mistral():
    """Use Mistral-7B for best reasoning"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Mistral-7B (Most Powerful)")
    print("="*70 + "\n")

    # Create AI with Mistral-7B
    ai = LocalAI(model_name="mistralai/Mistral-7B-Instruct-v0.2")

    print(f"Model: {ai.model_name}")
    print("Size: 7B parameters (~14GB download)")
    print("RAM: 32GB recommended")
    print("GPU: 16GB VRAM highly recommended")
    print("Quality: Best reasoning available")

    print("\n✅ Use for critical investigations with powerful hardware")


# ================================================================
# EXAMPLE 4: Use fine-tuned model
# ================================================================

def example_finetuned():
    """Use your own fine-tuned model"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Fine-Tuned OSINT Specialist")
    print("="*70 + "\n")

    # Create AI with fine-tuned model
    ai = LocalAI(model_name="../data/models/osint-specialist")

    print(f"Model: {ai.model_name}")
    print("Type: Fine-tuned for OSINT tasks")
    print("Training: Specialized on investigation examples")

    print("\n✅ Best accuracy for OSINT-specific tasks")
    print("⚠️  Must run train_osint_model.py first!")


# ================================================================
# EXAMPLE 5: Test AI analysis
# ================================================================

def example_bio_analysis():
    """Test bio analysis with AI"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Bio Analysis")
    print("="*70 + "\n")

    # Create AI
    ai = LocalAI()

    # Target profile
    target_profile = {
        'full_name': 'John Smith',
        'current_location': 'San Francisco',
        'occupation': 'Software Engineer',
        'skills': ['Python', 'Machine Learning']
    }

    # Account bio to analyze
    bio = "Software developer from SF. Love Python and ML. Building cool stuff."

    print("Target Profile:")
    print(f"  Name: {target_profile['full_name']}")
    print(f"  Location: {target_profile['current_location']}")
    print(f"  Occupation: {target_profile['occupation']}")
    print(f"  Skills: {', '.join(target_profile['skills'])}")

    print("\nAccount Bio:")
    print(f"  '{bio}'")

    print("\n🤖 AI Analysis:")
    print("  Analyzing... (this will load model on first run)")

    try:
        # Analyze bio
        result = ai.analyze_account_bio(bio, target_profile)

        print(f"\n  Match: {result['is_match']}")
        print(f"  Confidence: {result['confidence']:.1f}%")
        print(f"  Reasoning: {result['reasoning']}")

    except Exception as e:
        print(f"\n  ⚠️  Analysis failed: {e}")
        print("  (Model may not be downloaded yet)")


# ================================================================
# EXAMPLE 6: Custom model path
# ================================================================

def example_custom_path():
    """Use custom model cache directory"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Custom Cache Directory")
    print("="*70 + "\n")

    # Create AI with custom cache
    ai = LocalAI(
        model_name="microsoft/phi-2",
        cache_dir="../data/my_models"  # Custom location
    )

    print(f"Model: {ai.model_name}")
    print(f"Cache: {ai.cache_dir}")

    print("\n✅ Model will be downloaded to custom directory")
    print("   Useful for managing disk space or multiple installations")


# ================================================================
# MAIN
# ================================================================

def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("🤖 DeepTrace AI Model Examples")
    print("="*70)

    print("\nThese examples show how to configure AI models.")
    print("Choose which to run:\n")

    print("1. Default Model (Phi-2)")
    print("2. TinyLlama (Faster)")
    print("3. Mistral-7B (Most Powerful)")
    print("4. Fine-Tuned Model")
    print("5. Bio Analysis Test")
    print("6. Custom Cache Directory")
    print("\n0. Run All\n")

    choice = input("Choice (0-6): ").strip()

    examples = {
        '1': example_default_model,
        '2': example_tinyllama,
        '3': example_mistral,
        '4': example_finetuned,
        '5': example_bio_analysis,
        '6': example_custom_path,
    }

    if choice == '0':
        # Run all
        for ex in examples.values():
            ex()
    elif choice in examples:
        examples[choice]()
    else:
        print("\n❌ Invalid choice")

    print("\n" + "="*70)
    print("✨ Done! Check AI_MODEL_GUIDE.md for more details.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
