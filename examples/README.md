# 🎓 DeepTrace Examples & Tutorials

This directory contains example scripts and tutorials for DeepTrace features.

---

## 📚 Available Examples

### 1. `change_ai_model.py` - AI Model Configuration

Learn how to select and configure different AI models.

```bash
cd examples
python change_ai_model.py
```

**Covers:**
- Using default Phi-2 model
- Switching to TinyLlama (faster)
- Using Mistral-7B (most powerful)
- Loading fine-tuned models
- Testing bio analysis
- Custom cache directories

---

## 🚀 Quick Start

### Run an Example

```bash
cd examples
python change_ai_model.py
```

### Run All Examples

```python
# In the menu, select option 0
Choice (0-6): 0
```

---

## 📖 Documentation

For complete guides, see:

- **AI_MODEL_GUIDE.md** - Complete AI model guide
- **AI_FEATURES.md** - Local AI features documentation
- **README_ADVANCED.md** - Advanced mode guide

---

## 🎯 Common Use Cases

### Use Case 1: Quick Investigation (Limited Hardware)

```python
from src.local_ai import LocalAI

# Use TinyLlama for speed
ai = LocalAI(model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
```

### Use Case 2: Critical Investigation (Best Quality)

```python
# Use Mistral-7B for maximum accuracy
ai = LocalAI(model_name="mistralai/Mistral-7B-Instruct-v0.2")
```

### Use Case 3: Production (Balanced)

```python
# Use Phi-2 (default) - best balance
ai = LocalAI()  # Uses microsoft/phi-2
```

### Use Case 4: Specialized OSINT

```python
# Use your fine-tuned model
ai = LocalAI(model_name="data/models/osint-specialist")
```

---

## 🛠️ Creating Your Own Examples

### Template

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '../src')

from local_ai import LocalAI

def my_example():
    # Your code here
    ai = LocalAI()
    # Test something...

if __name__ == "__main__":
    my_example()
```

### Save and Run

```bash
# Save as examples/my_example.py
chmod +x examples/my_example.py
python examples/my_example.py
```

---

## 📝 Notes

- All examples assume you're in the `examples/` directory
- Models download automatically on first use (~5GB for Phi-2)
- GPU is optional but makes inference 10x faster
- See parent directory docs for complete guides

---

## 🆘 Need Help?

**Getting started:** Check `../AI_MODEL_GUIDE.md`

**AI not working:** Run `../test_advanced.py` to verify installation

**Model too slow:** Try TinyLlama instead of Phi-2

**Out of memory:** Use a smaller model or disable AI

---

Happy investigating! 🚀
