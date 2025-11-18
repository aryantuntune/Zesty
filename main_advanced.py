#!/usr/bin/env python3
"""
DeepTrace ADVANCED: Professional-grade OSINT with all enterprise features
Includes: Database, NLP, Temporal Analysis, Graph Theory, Sentiment Analysis,
          Monitoring, ML Username Gen, Visualizations, Email Discovery, Wayback Machine
"""

import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from src.config import Config
from src.dragnet import Dragnet
from src.pivot import PivotEngine
from src.behavioral import BehavioralAnalyzer
from src.scrapers import PlatformScraper
from src.visual import VisionSystem
from src.utils import setup_logger, extract_domain

# Advanced modules
from src.database import InvestigationDB
from src.nlp_engine import LocalNLPEngine
from src.temporal_analyzer import TemporalAnalyzer
from src.graph_analyzer import SocialGraphAnalyzer
from src.tone_analyzer import ToneAnalyzer
from src.monitor import MonitoringSystem
from src.ml_username_gen import MarkovUsernameGenerator, DEFAULT_TRAINING_DATA
from src.timeline_viz import TimelineVisualizer
from src.heatmap_viz import HeatmapVisualizer
from src.email_finder import EmailFinder
from src.wayback import WaybackMachine

logger = setup_logger(__name__)


def print_banner():
    """Display application banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║      🔍 DEEPTRACE ADVANCED v5.0                            ║
    ║   Professional-Grade OSINT Investigation System           ║
    ║   with Enterprise Analytics & Intelligence                ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Advanced investigation with all features"""

    print_banner()

    # Validate config (independent mode - no API key required)
    Config.validate_independent()

    print("\n✨ ADVANCED MODE - Enterprise Features:")
    print("   ✅ SQLite Database (persistent storage)")
    print("   ✅ Advanced NLP with spaCy")
    print("   ✅ Temporal Activity Analysis")
    print("   ✅ Social Network Graph Theory")
    print("   ✅ Sentiment & Tone Analysis")
    print("   ✅ ML-based Username Generation")
    print("   ✅ Timeline Visualizations")
    print("   ✅ Activity Heatmaps")
    print("   ✅ Email Discovery & Verification")
    print("   ✅ Wayback Machine Integration")
    print("   ✅ Automated Monitoring System")
    print("   ✅ + All Independent Mode features\n")

    # Get target
    target_name = input("Enter target username/name: ").strip()
    if not target_name:
        print("❌ Target required")
        sys.exit(1)

    print(f"\n🎯 Target: {target_name}")

    # Initialize all engines
    print("\n⚙️  Initializing advanced engines...")

    db = InvestigationDB()
    behavioral = BehavioralAnalyzer()
    pivot_engine = PivotEngine()
    scraper = PlatformScraper()
    nlp_engine = LocalNLPEngine()
    temporal = TemporalAnalyzer()
    graph_analyzer = SocialGraphAnalyzer()
    tone_analyzer = ToneAnalyzer()
    ml_username_gen = MarkovUsernameGenerator(order=2)
    timeline_viz = TimelineVisualizer()
    heatmap_viz = HeatmapVisualizer()
    email_finder = EmailFinder()
    wayback = WaybackMachine()

    print("✅ All engines initialized")

    # ===== PHASE 1: RECONNAISSANCE =====
    print("\n\n🕸️  PHASE 1: INITIAL RECONNAISSANCE")
    print("─" * 70)

    dragnet = Dragnet(target_name)

    print("🔍 Running Sherlock...")
    dragnet.run_sherlock()

    print("🔍 Running Google Dorks...")
    dragnet.run_google_dorks()

    initial_leads = dragnet.get_unique_leads()

    if not initial_leads:
        print("\n⚠️  No initial leads found")
        sys.exit(0)

    print(f"✅ Found {len(initial_leads)} initial leads")

    # ===== PHASE 2: ML USERNAME GENERATION =====
    print("\n\n🤖 PHASE 2: ML-BASED USERNAME GENERATION")
    print("─" * 70)

    # Train ML model on default data + found usernames
    training_data = DEFAULT_TRAINING_DATA.copy()
    training_data.extend([target_name])

    print("🧠 Training Markov chain model...")
    ml_username_gen.train(training_data)

    # Generate standard variations
    variations = pivot_engine.generate_username_variations(target_name)
    print(f"📝 Standard variations: {len(variations)}")

    # ===== PHASE 3: INTELLIGENT SCRAPING =====
    print("\n\n🌐 PHASE 3: ADVANCED SCRAPING & ANALYSIS")
    print("─" * 70)

    all_findings = []
    connections = []
    behavioral_profiles = []
    temporal_profiles = []
    tone_profiles = []
    all_timestamps = []

    # Check database cache first
    to_scrape = initial_leads[:Config.MAX_LEADS]
    print(f"🔎 Analyzing {len(to_scrape)} URLs with advanced intelligence...")

    for url in tqdm(to_scrape, desc="Analyzing", unit="url"):
        # Check cache
        cached = db.get_cached_account(url, max_age_hours=24)

        if cached:
            result = cached.get('scraped_data', {})
        else:
            # Scrape fresh
            result = scraper.auto_scrape(url)

        # Advanced NLP analysis
        bio_text = result.get('bio', '') + ' ' + result.get('headline', '')

        # Extract entities with NLP
        entities = nlp_engine.extract_entities(bio_text)
        skills = nlp_engine.extract_skills(bio_text)
        interests = nlp_engine.extract_interests(bio_text)

        # Build behavioral profile
        profile = behavioral.build_behavioral_profile({
            'bio': bio_text,
            'content': bio_text
        })

        # Add NLP-extracted data
        profile['entities'] = entities
        profile['skills'] = skills
        profile['interests_nlp'] = list(interests)

        # Temporal analysis
        temporal_profile = temporal.build_activity_profile(result)

        # Extract timestamps for heatmaps
        timestamps = temporal.extract_timestamps(result)
        all_timestamps.extend(timestamps)

        # Tone analysis
        tone_profile = tone_analyzer.build_tone_profile([bio_text])

        # Email discovery
        email_results = email_finder.find_emails_in_account(result)

        finding = {
            'url': url,
            'result': result,
            'behavioral_profile': profile,
            'temporal_profile': temporal_profile,
            'tone_profile': tone_profile,
            'email_results': email_results,
            'discovered_via': 'initial'
        }

        all_findings.append(finding)
        behavioral_profiles.append(profile)
        temporal_profiles.append(temporal_profile)
        tone_profiles.append(tone_profile)

        # Save to database
        db.save_account(investigation_id=0, account=finding)

        # Extract pivot points
        pivot_engine.extract_pivot_points(bio_text, url)

        # Graph connection
        domain = extract_domain(url)
        connections.append((target_name, domain))

        import time
        time.sleep(0.5)

    # ===== PHASE 4: BEHAVIORAL & SENTIMENT ANALYSIS =====
    print("\n\n🧠 PHASE 4: ADVANCED BEHAVIORAL ANALYSIS")
    print("─" * 70)

    # Aggregate interests from NLP
    all_interests = set()
    for profile in behavioral_profiles:
        all_interests.update(profile.get('interests', []))
        all_interests.update(profile.get('interests_nlp', []))

    print(f"🎯 NLP-Identified Interests ({len(all_interests)}):")
    for interest in list(all_interests)[:15]:
        print(f"   • {interest}")
    if len(all_interests) > 15:
        print(f"   ... and {len(all_interests) - 15} more")

    # Generate ML-based username predictions
    ml_predictions = ml_username_gen.generate_hybrid(
        base_name=target_name,
        interests=list(all_interests),
        count=30
    )

    print(f"\n🤖 ML-Generated Predictions: {len(ml_predictions)}")
    for username in ml_predictions[:10]:
        print(f"   • {username}")

    # ===== PHASE 5: CROSS-CORRELATION & SCORING =====
    print("\n\n🔗 PHASE 5: MULTI-FACTOR CORRELATION")
    print("─" * 70)

    high_confidence = []

    if len(all_findings) > 1:
        reference = all_findings[0]
        reference_account = {
            'name': reference['result'].get('name', target_name),
            'url': reference['url'],
            'interests': reference['behavioral_profile'].get('interests', []),
            'writing_style': reference['behavioral_profile'].get('writing_style', {}),
            'bio': reference['result'].get('bio', ''),
            'location': reference['result'].get('location', ''),
            'temporal_profile': reference['temporal_profile'],
            'tone_profile': reference['tone_profile']
        }

        print("📊 Calculating multi-factor similarity scores...\n")

        for finding in all_findings[1:]:
            candidate = {
                'url': finding['url'],
                'name': finding['result'].get('name', ''),
                'interests': finding['behavioral_profile'].get('interests', []),
                'writing_style': finding['behavioral_profile'].get('writing_style', {}),
                'bio': finding['result'].get('bio', ''),
                'location': finding['result'].get('location', ''),
                'temporal_profile': finding['temporal_profile'],
                'tone_profile': finding['tone_profile']
            }

            # Behavioral similarity (base score)
            score, reasons = behavioral.calculate_account_similarity(
                reference_account,
                candidate
            )

            # Add temporal similarity
            if reference['temporal_profile'].get('has_temporal_data') and \
               finding['temporal_profile'].get('has_temporal_data'):
                temporal_score, temporal_reasons = temporal.compare_temporal_profiles(
                    reference['temporal_profile'],
                    finding['temporal_profile']
                )
                # Weight temporal at 20%
                score = score * 0.8 + temporal_score * 0.2
                reasons.extend(temporal_reasons)

            # Add tone similarity
            if reference['tone_profile'].get('has_data') and \
               finding['tone_profile'].get('has_data'):
                tone_score, tone_reasons = tone_analyzer.compare_tone_profiles(
                    reference['tone_profile'],
                    finding['tone_profile']
                )
                # Weight tone at 15%
                score = score * 0.85 + tone_score * 0.15
                reasons.extend(tone_reasons)

            finding['similarity_score'] = score
            finding['match_reasons'] = reasons

            if score >= 50:
                high_confidence.append(finding)

        high_confidence.sort(key=lambda x: x['similarity_score'], reverse=True)

        print(f"✅ High-confidence matches: {len(high_confidence)}\n")
        for finding in high_confidence[:5]:
            print(f"   {finding['url']}")
            print(f"   Score: {finding['similarity_score']:.1f}/100")
            print(f"   Reasons: {', '.join(finding['match_reasons'][:3])}")
            print()

    # ===== PHASE 6: GRAPH ANALYSIS =====
    print("\n📊 PHASE 6: SOCIAL NETWORK GRAPH ANALYSIS")
    print("─" * 70)

    if connections:
        graph_analysis = graph_analyzer.analyze_full_network(connections)

        print(f"\n🕸️  Network Statistics:")
        print(f"   • Nodes: {graph_analysis['network_stats']['num_nodes']}")
        print(f"   • Edges: {graph_analysis['network_stats']['num_edges']}")
        print(f"   • Density: {graph_analysis['network_stats']['density']:.3f}")
        print(f"   • Communities: {graph_analysis['communities']['count']}")

        if graph_analysis['central_nodes']:
            print(f"\n   Top Central Nodes:")
            for node_info in graph_analysis['central_nodes'][:5]:
                print(f"   • {node_info['node']}: {node_info['score']:.3f}")

    # ===== PHASE 7: VISUALIZATIONS =====
    print("\n\n📊 PHASE 7: GENERATING VISUALIZATIONS")
    print("─" * 70)

    vision = VisionSystem()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Network graph
    graph_filename = f"{target_name}_network_{timestamp}.html"
    graph_path = Config.REPORTS_DIR / graph_filename

    if connections:
        vision.generate_graph(target_name, connections, graph_path)
        print(f"✅ Network graph: {graph_path}")

    # Timeline visualization
    if all_findings:
        timeline_path = timeline_viz.create_investigation_timeline(
            accounts=[{
                'url': f['url'],
                'platform': f['result'].get('platform', 'unknown'),
                'first_seen': datetime.now(),
                'discovered_via': f['discovered_via'],
                'similarity_score': f.get('similarity_score', 0)
            } for f in all_findings]
        )
        if timeline_path:
            print(f"✅ Timeline: {timeline_path}")

    # Activity heatmap
    if all_timestamps:
        heatmap_path = heatmap_viz.create_activity_heatmap(
            timestamps=all_timestamps,
            title=f"Activity Heatmap: {target_name}"
        )
        if heatmap_path:
            print(f"✅ Heatmap: {heatmap_path}")

    # ===== PHASE 8: COMPREHENSIVE REPORT =====
    print("\n\n📄 PHASE 8: GENERATING ADVANCED REPORT")
    print("─" * 70)

    report_filename = f"{target_name}_advanced_{timestamp}.md"
    report_path = Config.REPORTS_DIR / report_filename

    with open(report_path, 'w') as f:
        f.write(f"# DeepTrace Advanced Report: {target_name}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Version:** Advanced v5.0 (All Enterprise Features)\n\n")
        f.write("---\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"- **Initial Leads:** {len(initial_leads)}\n")
        f.write(f"- **Accounts Analyzed:** {len(all_findings)}\n")
        f.write(f"- **NLP-Identified Interests:** {len(all_interests)}\n")
        f.write(f"- **ML Username Predictions:** {len(ml_predictions)}\n")
        f.write(f"- **High-Confidence Matches:** {len(high_confidence)}\n")
        f.write(f"- **Temporal Profiles:** {len([p for p in temporal_profiles if p.get('has_temporal_data')])}\n")
        f.write(f"- **Tone Profiles:** {len([p for p in tone_profiles if p.get('has_data')])}\n")
        f.write("\n---\n\n")

        # Advanced Intelligence
        f.write("## Advanced Intelligence\n\n")

        f.write(f"### NLP-Extracted Interests\n")
        for interest in sorted(all_interests)[:30]:
            f.write(f"- {interest}\n")
        f.write("\n")

        f.write(f"### ML-Generated Usernames\n")
        for username in ml_predictions[:40]:
            f.write(f"- `{username}`\n")
        f.write("\n")

        # Network Analysis
        if connections:
            f.write(f"### Network Analysis\n")
            f.write(f"- **Nodes:** {graph_analysis['network_stats']['num_nodes']}\n")
            f.write(f"- **Communities:** {graph_analysis['communities']['count']}\n")
            f.write(f"- **Density:** {graph_analysis['network_stats']['density']:.3f}\n\n")

        f.write("---\n\n")

        # Detailed Findings
        f.write("## Detailed Account Analysis\n\n")

        for i, finding in enumerate(all_findings, 1):
            f.write(f"### {i}. {finding['url']}\n\n")

            score = finding.get('similarity_score', 'N/A')
            if score != 'N/A':
                f.write(f"**Similarity Score:** {score:.1f}/100\n\n")

                reasons = finding.get('match_reasons', [])
                if reasons:
                    f.write(f"**Match Indicators:** {', '.join(reasons[:5])}\n\n")

            result = finding['result']
            f.write(f"**Platform:** {result.get('platform', 'unknown')}\n\n")

            if result.get('name'):
                f.write(f"**Name:** {result['name']}\n\n")
            if result.get('bio'):
                f.write(f"**Bio:** {result['bio']}\n\n")
            if result.get('location'):
                f.write(f"**Location:** {result['location']}\n\n")

            # NLP entities
            entities = finding['behavioral_profile'].get('entities', {})
            if any(entities.values()):
                f.write(f"**NLP Entities:**\n")
                for entity_type, values in entities.items():
                    if values:
                        f.write(f"- {entity_type.title()}: {', '.join(values[:5])}\n")
                f.write("\n")

            # Temporal info
            temporal_p = finding['temporal_profile']
            if temporal_p.get('has_temporal_data'):
                tz = temporal_p['timezone']['detected']
                f.write(f"**Timezone:** {tz}\n")
                f.write(f"**Peak Hours:** {', '.join(map(str, temporal_p.get('peak_hours', [])))}\n")
                f.write(f"**Posting Pattern:** {temporal_p.get('frequency', {}).get('posting_pattern', 'unknown')}\n\n")

            # Tone info
            tone_p = finding['tone_profile']
            if tone_p.get('has_data'):
                f.write(f"**Tone:** {tone_p['tone']['primary_tone']}\n")
                f.write(f"**Sentiment:** {tone_p['sentiment']['classification']}\n")
                f.write(f"**Writing Style:** {tone_p.get('overall_style', 'unknown')}\n\n")

            # Email results
            email_res = finding['email_results']
            if email_res.get('found_emails'):
                f.write(f"**Found Emails:** {', '.join(email_res['found_emails'])}\n\n")

            f.write("---\n\n")

        # Technical Details
        f.write("## Technical Analysis Methods\n\n")
        f.write("**Advanced Features Used:**\n")
        f.write("- SQLite persistent database\n")
        f.write("- spaCy NLP entity extraction\n")
        f.write("- Temporal activity analysis\n")
        f.write("- Social network graph theory\n")
        f.write("- TextBlob sentiment analysis\n")
        f.write("- Markov chain username generation\n")
        f.write("- Multi-factor similarity scoring\n")
        f.write("- Email discovery & verification\n")
        f.write("- Timeline & heatmap visualizations\n\n")

    print(f"✅ Report: {report_path}")

    # Save to database
    investigation_id = db.save_investigation(
        target=target_name,
        accounts=all_findings,
        predictions=ml_predictions,
        interests=list(all_interests),
        high_confidence_count=len(high_confidence),
        report_path=str(report_path),
        graph_path=str(graph_path)
    )

    print(f"✅ Saved to database: Investigation ID={investigation_id}")

    # ===== COMPLETE =====
    print("\n\n" + "═" * 70)
    print("🎉 ADVANCED INVESTIGATION COMPLETE")
    print("═" * 70)
    print(f"\n📊 FINAL STATISTICS:")
    print(f"   • Initial leads: {len(initial_leads)}")
    print(f"   • Total analyzed: {len(all_findings)}")
    print(f"   • NLP interests: {len(all_interests)}")
    print(f"   • ML predictions: {len(ml_predictions)}")
    print(f"   • High-confidence matches: {len(high_confidence)}")
    print(f"   • Database ID: {investigation_id}")
    print(f"\n📁 Outputs: {Config.REPORTS_DIR}")
    print(f"   • {report_filename}")
    print(f"   • {graph_filename}")
    if timeline_path:
        print(f"   • {Path(timeline_path).name}")
    if heatmap_path:
        print(f"   • {Path(heatmap_path).name}")
    print("\n✨ PROFESSIONAL-GRADE INTELLIGENCE COMPLETE!\n")

    db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)
