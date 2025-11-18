# DeepTrace - Quick Start Guide

## Installation

### Step 1: Install Python Dependencies

DeepTrace requires Python 3.8+ and several OSINT libraries. Install them using:

```bash
pip install -r requirements_advanced.txt
```

**Key Dependencies Added**:
- `python-whois` - WHOIS record retrieval
- `pyOpenSSL` - SSL/TLS certificate analysis
- `dnspython` - DNS enumeration
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing

### Step 2: Download spaCy Language Model (Optional but Recommended)

For advanced NLP analysis, download the English language model:

```bash
python -m spacy download en_core_web_sm
```

### Step 3: Verify Installation

Test that all imports work:

```bash
python -c "import whois; import OpenSSL; import dns.resolver; print('✅ All dependencies installed successfully!')"
```

---

## Running DeepTrace

### Basic Usage

```bash
python main_advanced_v3.py
```

Then enter a target username when prompted.

### What to Expect

DeepTrace will execute **14 investigation modules**:

1. **Sherlock Username Search** - Find accounts across 500+ platforms
2. **Web Presence Discovery** - Google dorking and web search
3. **Enhanced Profile Scraping** - Extract bios, posts, metadata
4. **NLP Analysis** - Sentiment, topics, personality traits
5. **Email Discovery** - Find associated email addresses
6. **Automated Pivot Engine** - **NEW!** 5 transform types:
   - Email → HIBP breaches, MX records, Gravatar
   - Username → Platform enumeration, variations
   - Domain → WHOIS, DNS, subdomains, **Historical DNS**, **WHOIS History**
   - Phone → Carrier, geolocation
   - IP → GeoIP, ASN, reverse DNS, **Reverse IP Lookup**
7. **3-Source Verification** - Intelligence community reliability standards
8. **Adverse Inference Detection** - Gap analysis with **Wayback Machine verification**
9. **Operational Security Warnings** - PASSIVE/ACTIVE technique classification
10. **Network Graph** - Relationship visualization
11. **Timeline Analysis** - Activity patterns over time
12. **Heatmap Visualization** - Platform activity density
13. **Intelligence Report Generation** - TLP-classified markdown dossier
14. **Export** - JSON, CSV, HTML formats

---

## New Features (Latest Commit)

### 🚀 Deep Infrastructure Pivoting

**Reverse IP Lookup** - Find other domains sharing the same IP
- APIs: HackerTarget (free), ViewDNS (free), Shodan (optional)
- Use case: Phishing infrastructure attribution

**Historical Passive DNS** - Track domain IP changes over time
- API: SecurityTrails (50 free queries/month)
- Use case: "example.com was on GoDaddy 2018 → AWS 2020"

**WHOIS History** - Pre-privacy registrant data
- API: WhoisXMLAPI (paid) or Wayback Machine (free)
- Use case: Bypass current privacy protection with historical records

### 🔍 GitHub Deep Analysis

**Dependency Scanning** - Extract tech stack from repositories
- Scans: requirements.txt, package.json, Gemfile, go.mod, Dockerfile, etc.
- Intelligence value: "Django 1.11" → Poor security hygiene

**Threat Keyword Detection** - Offensive security indicators
- Keywords: RDP, VNC, Admin, Credential, 0-day, Exploit, Mimikatz, etc.
- Context-aware: Security researcher vs threat actor

### ⏰ Wayback Machine Temporal Verification

- Verifies activity gaps using Internet Archive
- Profile existed during gap → **CRITICAL** (deliberate scrubbing)
- Profile 404 during gap → **MEDIUM** (genuine inactivity)

### 📊 Probabilistic Risk Scoring

**Formula**: `Risk = Σ (Probability × Impact) × 25`

**Probability Levels**:
- CONFIRMED: 1.0 (Wayback verification)
- PROBABLE: 0.75 (Strong indicators)
- POSSIBLE: 0.5 (Circumstantial)
- SPECULATIVE: 0.25 (Weak evidence)

**Impact Levels**:
- CRITICAL: 4 (Deliberate deception)
- HIGH: 3 (Security concern)
- MEDIUM: 2 (Investigation needed)
- LOW: 1 (Minor anomaly)

### 🧠 Elimination Logic Engine

7 deductive reasoning rules to refine inferences:

1. **Tech cluster + gap** → Graduate school/bootcamp
2. **Location privacy + OpSec** → Security professional
3. **Minimal profiles + same year** → Sock puppets
4. **Post count outlier** → Primary account ID
5. **Wayback verification** → Eliminates scrubbing hypothesis
6. **Cloud tech stack** → Professional role (DevOps/SRE)
7. **Threat keywords + context** → Security researcher vs malicious

---

## Optional API Keys (100% Optional!)

DeepTrace works **perfectly fine without any API keys**. However, for enhanced capabilities:

### Free Tier APIs (Recommended)

```bash
# Create .env file (optional)
SECURITYTRAILS_API_KEY=your_key_here    # 50 queries/month FREE
HIBP_API_KEY=your_key_here              # 1 req/1.5s FREE
HUNTER_API_KEY=your_key_here            # 25 searches/month FREE
```

**Get Free API Keys**:
- SecurityTrails: https://securitytrails.com/corp/api (Sign up → Free tier)
- Have I Been Pwned: https://haveibeenpwned.com/API/Key (Donate $3.50/month)
- Hunter.io: https://hunter.io/api (100 searches/month FREE)

### Paid APIs (Entirely Optional)

- **Shodan** ($59/month) - Advanced infrastructure scanning
- **WhoisXMLAPI** ($49/month) - Historical WHOIS records
- **AbuseIPDB** (Free tier: 1000 checks/day)

---

## Output

DeepTrace generates:

1. **Console Output** - Real-time progress with 14 modules
2. **Markdown Report** - `reports/target_TIMESTAMP_report.md` (TLP:AMBER)
3. **JSON Export** - `exports/target_TIMESTAMP.json` (machine-readable)
4. **HTML Graph** - `graphs/target_TIMESTAMP_graph.html` (interactive)
5. **Timeline PNG** - `timelines/target_TIMESTAMP_timeline.png`
6. **Heatmap PNG** - `heatmaps/target_TIMESTAMP_heatmap.png`

---

## Troubleshooting

### ModuleNotFoundError: No module named 'whois'

```bash
pip install python-whois
```

### ModuleNotFoundError: No module named 'OpenSSL'

```bash
pip install pyOpenSSL
```

### ModuleNotFoundError: No module named 'dns'

```bash
pip install dnspython
```

### spaCy model not found

```bash
python -m spacy download en_core_web_sm
```

### ImportError: face_recognition

Face recognition is optional. Comment it out in `requirements_advanced.txt`:

```
# face_recognition>=1.3.0
```

---

## Professional OSINT Tradecraft

DeepTrace follows intelligence community best practices:

✅ **Passive-First Approach** - All transforms are DNS/WHOIS (no HTTP to target)
✅ **3-Source Verification** - CONFIRMED requires 3+ independent sources
✅ **Adverse Inference** - Deduce intent from missing data
✅ **OpSec Classification** - PASSIVE/SEMI-PASSIVE/ACTIVE/DESTRUCTIVE
✅ **TLP Classification** - RED/AMBER/GREEN/WHITE information sharing
✅ **Provenance Tracking** - Full attribution chains

---

## Support

- **Issues**: https://github.com/aryantuntune/Zesty/issues
- **Documentation**: See `reports/` folder for example outputs
- **Updates**: Pull latest changes with `git pull`

---

## Legal Notice

DeepTrace is for **authorized security research, penetration testing, CTF competitions, and educational purposes only**.

**Prohibited Uses**:
- Unauthorized surveillance or stalking
- Harassment or doxxing
- Violation of platform Terms of Service
- Any illegal activity

Users are responsible for compliance with applicable laws (GDPR, CCPA, CFAA, etc.).

---

**Enjoy professional-grade OSINT!** 🔍🕵️
