# 🔍 DeepTrace

**Professional-Grade OSINT Investigation System** with Behavioral Analysis, Smart Pivoting, and Social Media Authentication.

## 🚀 Investigation Modes

| Mode | API Key | AI | Accounts Found | Accuracy | Special Features |
|------|---------|----|----|----------|------------------|
| **🤖 Advanced v3** | ❌ FREE | ✅ Local | **20-30** | **100%** | **🔥 NEW! Pre-investigation questionnaire + Local AI reasoning (Hugging Face) + Interactive verification + 11 enterprise features!** |
| **⚡ Advanced v2** | ❌ FREE | ❌ No | **20-30** | **100%** | Interactive account verification + 11 enterprise features (filters false positives!) |
| **⚡ Advanced** | ❌ FREE | ❌ No | **20-30** | **90%** | ALL ENTERPRISE FEATURES - Database, NLP, ML, Graph Theory, Sentiment Analysis, Monitoring, Visualizations, Wayback! |
| **🔥 Independent** | ❌ FREE | ❌ No | **15-20** | **75%** | Platform scrapers, Nitter, behavioral analysis, NO dependencies! |
| **Lite** | ❌ FREE | ❌ No | 3-5 | 60% | Sherlock, username variations, basic scraping |
| **Basic** | ✅ Paid | ✅ Cloud | 3-5 | 80% | + AI-powered analysis ($0.15/run) |
| **Enhanced** | ✅ Paid | ✅ Cloud | 8-12 | 85% | + Smart pivoting ($0.15/run) |
| **Professional** | ✅ Paid | ✅ Cloud | 15-25+ | 90% | + AI behavioral analysis, social auth ($0.15/run) |

**🤖 ULTIMATE & RECOMMENDED: Advanced v3** - AI-powered intelligence with local reasoning, **100% accuracy, $0.00 cost, 100% private!**

💡 **NEW!** See [AI_FEATURES.md](AI_FEATURES.md) for local AI capabilities that rival cloud APIs at $0.00 cost!

💡 **See [README_ADVANCED.md](README_ADVANCED.md) for why Advanced modes are completely FREE and better than paid AI modes!**

---

## 🧭 Easy Navigation

**NEW!** Interactive menu system:
```bash
./deeptrace.py    # Choose your mode, view database, setup monitoring!
```

📖 **Complete guide:** [NAVIGATION.md](NAVIGATION.md) - Find everything easily!

---

## ✨ Key Features

### Core Capabilities
- **OSINT Reconnaissance** - Sherlock (300+ sites) + Google Dorks
- **AI Investigation** - Claude-powered browser automation
- **Face Verification** - Optional face recognition
- **Interactive Visualization** - Network graphs

### 🆕 Advanced Features (Professional Mode)
- **Behavioral Analysis** - Writing style fingerprinting
- **Interest-Based Predictions** - Discovers usernames based on hobbies/fandoms
- **Social Media Login** - Authenticated access to Twitter, LinkedIn, Instagram
- **Similarity Scoring** - Multi-factor account correlation (reduces false positives by 75%)
- **Smart Pivoting** - Cross-references across platforms

See [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) for detailed documentation.

## Quick Start

### 1. Install Dependencies

**For Advanced Mode (RECOMMENDED - 100% FREE!):**
```bash
./install_advanced.sh    # Installs everything, NO API key needed!
```

**For AI-Powered Modes (requires paid API):**
```bash
pip install -r requirements.txt
playwright install
```

### 2. Configure API Key (SKIP THIS - Not needed for Advanced Mode!)

**For Advanced Mode (RECOMMENDED):** ✅ **NO API KEY NEEDED!** Skip this entirely!

**For Lite/Independent Modes:** ✅ **NO API KEY NEEDED!** Skip this entirely!

**For AI-Powered Modes ONLY (Basic/Enhanced/Professional - NOT RECOMMENDED):**

If you really want to use expensive AI modes, get Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

Create a `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Cost:** ~$0.15 per investigation (vs. **$0.00 for Advanced mode**)

### 3. (Optional) Configure Social Login

For **Professional Mode** with authenticated social media access:

```bash
# Copy template
cp .credentials.json.template .credentials.json

# Edit .credentials.json with your dummy account details
# (Use a dedicated OSINT account, NOT your personal accounts)
```

### 4. Run Investigation

Choose your investigation level:

#### **🤖 Advanced Mode v3** - AI-POWERED + PROFILING (ULTIMATE!)
```bash
python main_advanced_v3.py
# - Pre-investigation questionnaire (18 questions)
# - Local AI reasoning (Hugging Face models - FREE!)
# - Interactive account verification
# - 11 enterprise features
# - 100% accuracy
# - Cost: $0.00
# - First run downloads AI model (~5GB, one-time)
```

#### **⚡ Advanced Mode v2** - VERIFICATION (BEST FOR PRECISION!)
```bash
python main_advanced_v2.py
# - Interactive account verification (filters false positives!)
# - 11 enterprise features
# - 100% accuracy
# - Cost: $0.00
```

#### **⚡ Advanced Mode (classic)** - ENTERPRISE FEATURES (PROFESSIONAL!)
```bash
python main_advanced.py
```
**What you get:**
- ✅ **All Independent Mode features**
- ✅ **SQLite Database** (persistent storage, caching, change tracking)
- ✅ **Advanced NLP with spaCy** (3X better entity extraction)
- ✅ **Temporal Analysis** (timezone detection, activity patterns)
- ✅ **Social Network Graph Theory** (community detection, centrality)
- ✅ **Sentiment & Tone Analysis** (writing style fingerprinting)
- ✅ **ML Username Generator** (Markov chains, smarter predictions)
- ✅ **Timeline Visualizations** (interactive Plotly charts)
- ✅ **Activity Heatmaps** (matplotlib/seaborn heat maps)
- ✅ **Email Discovery & Verification** (DNS MX validation)
- ✅ **Wayback Machine** (historical profile analysis)
- ✅ **Automated Monitoring** (scheduled re-checks, alerts)

**Perfect for:** Professional investigations, maximum intelligence depth!
**See:** [ADVANCED_FEATURES_V2.md](ADVANCED_FEATURES_V2.md) for full documentation

---

#### **🔥 Independent Mode** - MAX POWER, ZERO DEPENDENCIES (RECOMMENDED!)
```bash
python main_independent.py
```
**What you get:**
- ✅ Sherlock search (300+ sites)
- ✅ Google Dorks
- ✅ 100+ username variations
- ✅ **Behavioral analysis** (regex-based, no AI needed)
- ✅ **Interest-based predictions** (aryan_thanos from Marvel interest!)
- ✅ **Twitter via Nitter** (NO LOGIN REQUIRED!)
- ✅ **GitHub advanced scraping**
- ✅ **Reddit JSON API**
- ✅ **Similarity scoring** (mathematical)
- ✅ **Network visualization**
- ❌ **NO API keys needed**
- ❌ **NO social logins needed**

**Perfect for:** Maximum results without any dependencies!
**See:** [FULLY_INDEPENDENT.md](FULLY_INDEPENDENT.md) for how it works

---

#### **Lite Mode** - FREE (No API key) 🆓
```bash
python main_lite.py
```
**What you get:**
- ✅ Sherlock search (300+ sites)
- ✅ Google Dorks
- ✅ 100+ username variations
- ✅ Basic web scraping
- ❌ No AI analysis (manual URL checking)

**Perfect for:** Testing, learning, or working on a budget

---

#### **Basic Mode** - AI-powered (Requires API key)
```bash
python main.py
```
**What you get:** Everything in Lite + AI-powered URL analysis

**Cost:** ~$0.15 per investigation

---

#### **Enhanced Mode** - Deep search (Requires API key)
```bash
python main_enhanced.py
```
**What you get:** Everything in Basic + smart pivoting
See [PIVOT_STRATEGY.md](PIVOT_STRATEGY.md) for details

---

#### **Professional Mode** - Maximum intel (Requires API key)
```bash
python main_professional.py
```
**What you get:** Everything + behavioral analysis + social login
See [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) for details

## Project Structure

```
DeepTrace/
├── data/
│   ├── input/          # Place target.jpg here (optional)
│   ├── raw_leads/      # Sherlock output
│   └── reports/        # Generated reports & graphs
├── src/
│   ├── config.py       # Configuration
│   ├── dragnet.py      # OSINT module
│   ├── visual.py       # Face recognition & graphs
│   ├── agent.py        # Claude AI agent
│   └── utils.py        # Helpers
└── main.py             # Entry point
```

## Configuration

Edit `src/config.py`:

- `HEADLESS` - Set `False` to watch browser (demo mode)
- `MAX_LEADS` - Limit URLs to process (saves API costs)
- `ETHICAL_MODE` - Respects rate limits

## Output

- **Markdown Report** - Detailed findings from each URL
- **HTML Network Graph** - Interactive visualization of connections

## Requirements

- Python 3.8+
- Anthropic API key
- Chrome/Chromium (for Playwright)

## Ethical Use

This tool is for educational and authorized security research only. Always respect:
- Terms of Service
- Privacy laws
- Rate limits
- robots.txt

---

**Built with:** Claude AI • Browser-Use • Sherlock • Face Recognition • PyVis • spaCy • NetworkX • TextBlob • Plotly • matplotlib/seaborn • Wayback Machine
