# 🧭 DeepTrace Navigation Guide

Quick reference for finding your way around DeepTrace!

---

## 🚀 Quick Start

### For First-Time Users:
```bash
# 1. Install (one command!)
./install_advanced.sh

# 2. Test
./test_advanced.py

# 3. Run interactive menu
./deeptrace.py
```

### For Returning Users:
```bash
# Direct launch (skip menu)
python main_advanced.py           # Advanced mode (RECOMMENDED)
python main_independent.py        # Independent mode
python main_lite.py               # Lite mode
```

---

## 📂 Project Structure

### 🎯 Main Entry Points

| File | Purpose | When to Use |
|------|---------|-------------|
| **deeptrace.py** | Interactive menu | First-time, browsing features |
| **main_advanced.py** | Advanced investigation | Production use (RECOMMENDED) |
| **main_independent.py** | Independent investigation | Alternative to Advanced |
| **main_lite.py** | Lite investigation | Quick basic search |

### 💚 FREE Modes (No API Key)

| File | Accounts Found | Features | Use When |
|------|----------------|----------|----------|
| **main_advanced.py** | 20-30 | 11 enterprise features | **Always (best!)** |
| **main_independent.py** | 15-20 | Platform scrapers | Alternative |
| **main_lite.py** | 3-5 | Basic search | Quick lookup |

### 💰 PAID Modes (Require API Key - NOT RECOMMENDED)

| File | Cost | Use When |
|------|------|----------|
| main.py | $0.15/run | You need AI reasoning |
| main_enhanced.py | $0.15/run | AI + pivoting |
| main_professional.py | $0.15/run | AI + social login |

**Note:** Advanced mode (FREE) is better than paid modes! See [COST_COMPARISON.md](COST_COMPARISON.md)

---

## 🛠️ Utilities

Located in `utils/` directory:

| Script | Purpose | Access Via |
|--------|---------|------------|
| **view_database.py** | Browse investigations | Menu option 7 |
| **setup_monitoring.py** | Configure alerts | Menu option 8 |
| **configure.py** | System settings | Menu option 9 |

---

## 📚 Documentation

### For Beginners:
1. **README.md** - Start here!
2. **README_ADVANCED.md** - Why Advanced mode is FREE and awesome
3. **QUICKSTART_ADVANCED.md** - 5-minute tutorial

### For Advanced Users:
4. **ADVANCED_FEATURES_V2.md** - Complete technical documentation
5. **FULLY_INDEPENDENT.md** - How it works without API
6. **COST_COMPARISON.md** - FREE vs PAID analysis

### For Developers:
7. **IMPROVEMENTS.md** - Roadmap & suggestions
8. **NAVIGATION.md** - This file!

---

## 🔧 Installation & Setup

| Task | Command | When |
|------|---------|------|
| Install everything | `./install_advanced.sh` | First time |
| Verify installation | `./test_advanced.py` | After install |
| Update dependencies | `pip install -r requirements_advanced.txt` | Updates available |
| Download models | `python -m spacy download en_core_web_sm` | spaCy missing |

---

## 📊 Core Modules (`src/` directory)

### Essential (Used by all modes):
- **config.py** - Configuration
- **utils.py** - Helper functions
- **dragnet.py** - Sherlock + Google Dorks

### FREE Modes Only:
- **scrapers.py** - Platform-specific scrapers
- **behavioral.py** - Behavioral analysis
- **pivot.py** - Smart pivoting

### Advanced Mode Only (11 modules):
- **database.py** - SQLite persistence
- **nlp_engine.py** - Advanced NLP (spaCy)
- **temporal_analyzer.py** - Activity patterns
- **graph_analyzer.py** - Social network analysis
- **tone_analyzer.py** - Sentiment analysis
- **monitor.py** - Automated monitoring
- **ml_username_gen.py** - ML username generation
- **timeline_viz.py** - Plotly timelines
- **heatmap_viz.py** - Activity heatmaps
- **email_finder.py** - Email discovery
- **wayback.py** - Historical analysis

### PAID Modes Only:
- **agent.py** - Claude AI agent
- **session_manager.py** - Social login (Professional mode)

---

## 📁 Data Directories

| Directory | Purpose | Auto-Created |
|-----------|---------|--------------|
| `data/` | All data storage | ✅ |
| `data/input/` | Target photos (optional) | ✅ |
| `data/raw_leads/` | Sherlock output | ✅ |
| `data/reports/` | Investigation reports | ✅ |
| `data/deeptrace.db` | SQLite database | Auto |
| `data/monitors.json` | Monitoring config | Auto |
| `data/alerts.json` | Alert history | Auto |

---

## 🎯 Common Tasks

### Run an Investigation:
```bash
# Option 1: Interactive menu
./deeptrace.py
# Choose option 1 (Advanced)

# Option 2: Direct
python main_advanced.py
# Enter target when prompted
```

### View Past Investigations:
```bash
# Option 1: Via menu
./deeptrace.py
# Choose option 7

# Option 2: Direct
python utils/view_database.py
```

### Setup Monitoring:
```bash
# Option 1: Via menu
./deeptrace.py
# Choose option 8

# Option 2: Direct
python utils/setup_monitoring.py
```

### Configure System:
```bash
# Option 1: Via menu
./deeptrace.py
# Choose option 9

# Option 2: Direct
python utils/configure.py
```

### Check Installation:
```bash
# Option 1: Via menu
./deeptrace.py
# Choose option 11

# Option 2: Direct
./test_advanced.py
```

---

## 🗺️ Decision Tree

**Choose your path:**

```
START
 │
 ├─ First time user?
 │   └─ YES → Run ./install_advanced.sh → ./deeptrace.py
 │   └─ NO  → Continue
 │
 ├─ Want interactive menu?
 │   └─ YES → ./deeptrace.py
 │   └─ NO  → Continue
 │
 ├─ Have API key?
 │   └─ YES → Still use Advanced mode (it's better!)
 │   └─ NO  → Continue
 │
 ├─ Which mode?
 │   ├─ Best results? → python main_advanced.py ⭐
 │   ├─ Alternative? → python main_independent.py
 │   └─ Quick lookup? → python main_lite.py
 │
 └─ View results → data/reports/
```

---

## 🆘 Troubleshooting

### Can't find module:
```bash
# Reinstall dependencies
./install_advanced.sh
```

### Database error:
```bash
# Delete corrupted database
rm data/deeptrace.db
# Run investigation again
```

### API key error (ignore if using Advanced mode):
```bash
# Advanced mode doesn't need API key!
# Just run: python main_advanced.py
```

### Sherlock not found:
```bash
pip install sherlock-project
```

### spaCy model missing:
```bash
python -m spacy download en_core_web_sm
```

---

## 💡 Pro Tips

1. **Always use Advanced mode** - It's FREE and better than paid modes!

2. **Check database first** - Cached results are 70% faster

3. **Use monitoring for long-term tracking** - Set and forget

4. **Export reports early** - Don't lose your findings

5. **Run test_advanced.py after updates** - Verify everything works

---

## 🔗 Quick Links

| Need | Go To |
|------|-------|
| Installation help | [QUICKSTART_ADVANCED.md](QUICKSTART_ADVANCED.md) |
| Cost questions | [COST_COMPARISON.md](COST_COMPARISON.md) |
| Feature docs | [ADVANCED_FEATURES_V2.md](ADVANCED_FEATURES_V2.md) |
| How it works | [FULLY_INDEPENDENT.md](FULLY_INDEPENDENT.md) |
| Future plans | [IMPROVEMENTS.md](IMPROVEMENTS.md) |
| General info | [README.md](README.md) |

---

## 📞 Support

**Found a bug?**
- Check existing issues
- Create new issue with details

**Have a question?**
- Check documentation first
- Search closed issues
- Open new discussion

**Want to contribute?**
- Read [IMPROVEMENTS.md](IMPROVEMENTS.md)
- Pick a feature
- Submit PR!

---

**Remember:** When in doubt, run `./deeptrace.py` for the interactive menu! 🎯
