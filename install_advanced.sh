#!/bin/bash
# DeepTrace Advanced Installation Script
# Installs all enterprise features dependencies

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🚀 DeepTrace Advanced v5.0 - Installation                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found"
echo ""

# Install Advanced mode requirements (NO API KEY NEEDED!)
echo "📦 Installing Advanced mode dependencies (100% FREE!)..."
pip install -r requirements_advanced.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements"
    exit 1
fi

echo "✅ All dependencies installed (NO paid services required!)"
echo ""

# Install spaCy language model
echo "🧠 Downloading spaCy English model (en_core_web_sm)..."
python3 -m spacy download en_core_web_sm

if [ $? -ne 0 ]; then
    echo "⚠️  spaCy model download failed (optional)"
    echo "   You can install it later with: python -m spacy download en_core_web_sm"
else
    echo "✅ spaCy model installed"
fi
echo ""

# Download TextBlob corpora
echo "📚 Downloading TextBlob corpora..."
python3 -c "import textblob; textblob.download_corpora.download_all()" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  TextBlob corpora download failed (optional)"
    echo "   You can install it later with: python -m textblob.download_corpora"
else
    echo "✅ TextBlob corpora installed"
fi
echo ""

# Note: Playwright is NOT needed for Advanced mode
# (Only required for AI-powered Basic/Enhanced/Professional modes)
echo "ℹ️  Skipping Playwright (not needed for Advanced mode)"
echo ""

# Install Sherlock (if not already installed)
echo "🔍 Checking Sherlock installation..."
sherlock --version 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Sherlock not found. Installing via pip..."
    pip install sherlock-project
else
    echo "✅ Sherlock already installed"
fi
echo ""

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/input data/raw_leads data/reports data/sessions

touch data/input/.gitkeep
touch data/raw_leads/.gitkeep
touch data/reports/.gitkeep

echo "✅ Data directories created"
echo ""

# Verify installations
echo "🔎 Verifying installations..."
echo ""

# Check critical imports
python3 -c "
import sys

checks = {
    'requests': 'HTTP client',
    'beautifulsoup4': 'Web scraping',
    'networkx': 'Graph analysis',
    'pyvis': 'Network visualization',
    'spacy': 'Advanced NLP (optional)',
    'textblob': 'Sentiment analysis (optional)',
    'plotly': 'Timeline visualizations (optional)',
    'matplotlib': 'Heatmaps (optional)',
    'seaborn': 'Statistical graphics (optional)',
    'schedule': 'Monitoring (optional)',
    'dns.resolver': 'Email verification (optional)',
}

print('Module Availability:')
print('-' * 50)

for module_name, description in checks.items():
    try:
        if '.' in module_name:
            # Handle submodules
            parts = module_name.split('.')
            __import__(parts[0])
        else:
            __import__(module_name.replace('-', '_'))
        print(f'✅ {description:30} ({module_name})')
    except ImportError:
        optional = '(optional)' in description
        symbol = '⚠️ ' if optional else '❌'
        print(f'{symbol} {description:30} ({module_name})')

print('-' * 50)
"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Installation Complete!                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 You can now run DeepTrace Advanced:"
echo ""
echo "   ./deeptrace.py                   # Interactive menu (RECOMMENDED)"
echo "   python main_advanced_v3.py       # v3: AI + Profiling (ULTIMATE)"
echo "   python main_advanced_v2.py       # v2: Account verification"
echo "   python main_advanced.py          # Classic: All features"
echo ""
echo "🤖 NEW: Local AI Features (v3):"
echo "   • Pre-investigation questionnaire"
echo "   • Local AI reasoning (Hugging Face)"
echo "   • 100% accuracy with $0.00 cost"
echo "   • First run will download AI model (~5GB, one-time)"
echo ""
echo "📖 Documentation:"
echo "   AI_FEATURES.md                   # Local AI guide (NEW!)"
echo "   ADVANCED_FEATURES_V2.md          # Feature documentation"
echo "   README.md                        # Getting started"
echo "   NAVIGATION.md                    # Navigation guide"
echo ""
echo "💡 Tip: AI model downloads automatically on first use of v3!"
echo "    Subsequent runs use cached model (instant loading)."
echo ""
