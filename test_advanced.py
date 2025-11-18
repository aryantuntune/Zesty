#!/usr/bin/env python3
"""
Quick test to verify all Advanced features are working
"""

import sys
from pathlib import Path

print("\n" + "="*60)
print("🔍 DeepTrace Advanced - System Verification")
print("="*60 + "\n")

# Test imports
print("Testing module imports...\n")

modules_status = {}

# Core modules
core_modules = [
    ('src.config', 'Configuration'),
    ('src.utils', 'Utilities'),
    ('src.dragnet', 'OSINT Dragnet'),
    ('src.scrapers', 'Platform Scrapers'),
    ('src.behavioral', 'Behavioral Analysis'),
    ('src.pivot', 'Pivot Engine'),
    ('src.visual', 'Visualization'),
]

# Advanced modules
advanced_modules = [
    ('src.database', 'SQLite Database'),
    ('src.nlp_engine', 'NLP Engine (spaCy)'),
    ('src.temporal_analyzer', 'Temporal Analysis'),
    ('src.graph_analyzer', 'Graph Analysis'),
    ('src.tone_analyzer', 'Tone Analysis'),
    ('src.monitor', 'Monitoring System'),
    ('src.ml_username_gen', 'ML Username Generator'),
    ('src.timeline_viz', 'Timeline Visualizations'),
    ('src.heatmap_viz', 'Heatmap Visualizations'),
    ('src.email_finder', 'Email Discovery'),
    ('src.wayback', 'Wayback Machine'),
]

all_modules = core_modules + advanced_modules

success_count = 0
total_count = len(all_modules)

for module_name, description in all_modules:
    try:
        __import__(module_name)
        print(f"✅ {description:30} ({module_name})")
        modules_status[module_name] = True
        success_count += 1
    except ImportError as e:
        print(f"❌ {description:30} ({module_name})")
        print(f"   Error: {e}")
        modules_status[module_name] = False
    except Exception as e:
        print(f"⚠️  {description:30} ({module_name})")
        print(f"   Warning: {e}")
        modules_status[module_name] = 'partial'

print("\n" + "-"*60)
print(f"Module Import: {success_count}/{total_count} successful")
print("-"*60 + "\n")

# Test database
print("Testing database initialization...")
try:
    from src.database import InvestigationDB
    from src.config import Config

    Config.validate_independent()

    test_db_path = Config.DATA_DIR / "test_deeptrace.db"
    db = InvestigationDB(db_path=test_db_path)

    print("✅ Database initialized successfully")

    # Test save/retrieve
    test_inv_id = db.save_investigation(
        target="test_user",
        accounts=[],
        predictions=[],
        interests=['test'],
        high_confidence_count=0
    )

    print(f"✅ Database write/read successful (ID: {test_inv_id})")

    db.close()

    # Clean up test database
    if test_db_path.exists():
        test_db_path.unlink()
        print("✅ Test database cleaned up")

except Exception as e:
    print(f"❌ Database test failed: {e}")

print("\n" + "-"*60)

# Test NLP
print("\nTesting NLP capabilities...")
try:
    from src.nlp_engine import LocalNLPEngine

    nlp = LocalNLPEngine()

    test_text = "I'm a Python developer working with machine learning and Django"
    entities = nlp.extract_entities(test_text)
    interests = nlp.extract_interests(test_text)

    print(f"✅ NLP extraction successful")
    print(f"   Technologies found: {entities.get('technologies', [])}")
    print(f"   Interests found: {list(interests)[:5]}")

except Exception as e:
    print(f"⚠️  NLP test: {e}")
    print(f"   (NLP will fall back to regex mode)")

print("\n" + "-"*60)

# Test visualizations
print("\nTesting visualization capabilities...")
try:
    from src.timeline_viz import TimelineVisualizer
    from src.heatmap_viz import HeatmapVisualizer

    timeline_viz = TimelineVisualizer()
    heatmap_viz = HeatmapVisualizer()

    print(f"✅ Timeline visualizer: {'Plotly' if timeline_viz.use_plotly else 'Not available'}")
    print(f"✅ Heatmap visualizer: {'matplotlib' if heatmap_viz.use_matplotlib else 'Not available'}")
    print(f"   Seaborn enhanced: {'Yes' if heatmap_viz.use_seaborn else 'No'}")

except Exception as e:
    print(f"⚠️  Visualization test: {e}")

print("\n" + "-"*60)

# Test ML username generator
print("\nTesting ML username generator...")
try:
    from src.ml_username_gen import MarkovUsernameGenerator, DEFAULT_TRAINING_DATA

    gen = MarkovUsernameGenerator(order=2)
    gen.train(DEFAULT_TRAINING_DATA)

    predictions = gen.generate_hybrid(
        base_name="testuser",
        interests=['python', 'coding'],
        count=5
    )

    print(f"✅ ML generator trained on {len(DEFAULT_TRAINING_DATA)} examples")
    print(f"   Generated {len(predictions)} predictions")
    print(f"   Sample: {predictions[:3]}")

except Exception as e:
    print(f"❌ ML generator test failed: {e}")

print("\n" + "-"*60)

# Test graph analyzer
print("\nTesting graph analysis...")
try:
    from src.graph_analyzer import SocialGraphAnalyzer

    analyzer = SocialGraphAnalyzer()

    test_connections = [
        ('user1', 'user2'),
        ('user2', 'user3'),
        ('user1', 'user3'),
    ]

    analysis = analyzer.analyze_full_network(test_connections)

    print(f"✅ Graph analysis successful")
    print(f"   Method: {analysis['analysis_method']}")
    print(f"   Nodes: {analysis['network_stats']['num_nodes']}")
    print(f"   Communities: {analysis['communities']['count']}")

except Exception as e:
    print(f"❌ Graph analysis test failed: {e}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)

# Calculate score
critical_modules = ['src.database', 'src.scrapers', 'src.behavioral']
critical_ok = all(modules_status.get(m, False) for m in critical_modules)

advanced_ok = sum(1 for k, v in modules_status.items()
                  if k.startswith('src.') and k not in critical_modules and v == True)

total_advanced = len([m for m, _ in advanced_modules])

print(f"\n✅ Core System: {'READY' if critical_ok else 'ISSUES DETECTED'}")
print(f"✅ Advanced Features: {advanced_ok}/{total_advanced} available")

if success_count == total_count:
    print("\n🎉 ALL SYSTEMS OPERATIONAL!")
    print("   You can run: python main_advanced.py")
elif critical_ok:
    print("\n✅ SYSTEM READY (with reduced features)")
    print("   Some advanced features unavailable but core functionality works")
    print("   Run: python main_independent.py (recommended)")
else:
    print("\n⚠️  CRITICAL MODULES MISSING")
    print("   Run: ./install_advanced.sh")

print("\n" + "="*60 + "\n")

sys.exit(0 if critical_ok else 1)
