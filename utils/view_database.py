#!/usr/bin/env python3
"""
Database Viewer - Browse past investigations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import InvestigationDB
from datetime import datetime

def print_banner():
    print("\n" + "="*70)
    print("📊 DeepTrace Database Viewer")
    print("="*70 + "\n")

def format_timestamp(ts_str):
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts_str

def view_all_investigations(db):
    """List all investigations"""
    investigations = db.conn.execute("""
        SELECT id, target, timestamp, num_accounts, high_confidence_matches
        FROM investigations
        ORDER BY timestamp DESC
        LIMIT 50
    """).fetchall()

    if not investigations:
        print("📭 No investigations found in database.")
        return

    print(f"Found {len(investigations)} investigations:\n")
    print(f"{'ID':<5} {'Target':<20} {'Date':<20} {'Accounts':<10} {'High Conf.':<10}")
    print("-" * 70)

    for inv in investigations:
        print(f"{inv['id']:<5} {inv['target']:<20} {format_timestamp(inv['timestamp']):<20} "
              f"{inv['num_accounts']:<10} {inv['high_confidence_matches']:<10}")

def view_investigation_detail(db, inv_id):
    """View detailed investigation"""
    inv = db.conn.execute("""
        SELECT * FROM investigations WHERE id = ?
    """, (inv_id,)).fetchone()

    if not inv:
        print(f"❌ Investigation {inv_id} not found.")
        return

    print("\n" + "="*70)
    print(f"Investigation #{inv['id']}: {inv['target']}")
    print("="*70 + "\n")

    print(f"📅 Date: {format_timestamp(inv['timestamp'])}")
    print(f"🎯 Target: {inv['target']}")
    print(f"📊 Accounts found: {inv['num_accounts']}")
    print(f"✅ High confidence matches: {inv['high_confidence_matches']}")

    if inv['interests']:
        import json
        try:
            interests = json.loads(inv['interests'])
            print(f"\n🎯 Interests ({len(interests)}):")
            for interest in interests[:20]:
                print(f"   • {interest}")
            if len(interests) > 20:
                print(f"   ... and {len(interests) - 20} more")
        except:
            pass

    if inv['predictions']:
        import json
        try:
            predictions = json.loads(inv['predictions'])
            print(f"\n🤖 ML Predictions ({len(predictions)}):")
            for pred in predictions[:15]:
                print(f"   • {pred}")
            if len(predictions) > 15:
                print(f"   ... and {len(predictions) - 15} more")
        except:
            pass

    if inv['report_path']:
        print(f"\n📄 Report: {inv['report_path']}")

    if inv['graph_path']:
        print(f"🕸️  Graph: {inv['graph_path']}")

    # Get accounts
    accounts = db.conn.execute("""
        SELECT url, platform, similarity_score, name
        FROM accounts
        WHERE investigation_id = ?
        ORDER BY similarity_score DESC
        LIMIT 20
    """, (inv_id,)).fetchall()

    if accounts:
        print(f"\n🔗 Top Accounts ({len(accounts)}):")
        print(f"\n{'Platform':<15} {'Score':<10} {'Name':<25} {'URL':<40}")
        print("-" * 70)

        for acc in accounts:
            score = f"{acc['similarity_score']:.1f}" if acc['similarity_score'] else "N/A"
            name = (acc['name'] or 'Unknown')[:24]
            url = (acc['url'] or '')[:39]
            print(f"{acc['platform']:<15} {score:<10} {name:<25} {url:<40}")

def search_by_target(db, target):
    """Search investigations by target"""
    investigations = db.get_investigation_history(target)

    if not investigations:
        print(f"📭 No investigations found for '{target}'")
        return

    print(f"\nFound {len(investigations)} investigations for '{target}':\n")

    for inv in investigations:
        print(f"Investigation #{inv['id']} - {format_timestamp(inv['timestamp'])}")
        print(f"  Accounts: {inv['num_accounts']}, High confidence: {inv['high_confidence_matches']}")
        print()

def show_stats(db):
    """Show database statistics"""
    stats = db.conn.execute("""
        SELECT
            COUNT(*) as total_investigations,
            SUM(num_accounts) as total_accounts,
            AVG(num_accounts) as avg_accounts,
            SUM(high_confidence_matches) as total_high_conf
        FROM investigations
    """).fetchone()

    print("\n📈 Database Statistics:\n")
    print(f"Total investigations: {stats['total_investigations']}")
    print(f"Total accounts found: {stats['total_accounts']}")
    print(f"Average accounts per investigation: {stats['avg_accounts']:.1f}")
    print(f"Total high-confidence matches: {stats['total_high_conf']}")

    # Most investigated targets
    top_targets = db.conn.execute("""
        SELECT target, COUNT(*) as count
        FROM investigations
        GROUP BY target
        ORDER BY count DESC
        LIMIT 5
    """).fetchall()

    if top_targets:
        print("\n🎯 Most investigated targets:")
        for target in top_targets:
            print(f"   • {target['target']}: {target['count']} investigations")

def main():
    """Main database viewer"""
    print_banner()

    try:
        db = InvestigationDB()
    except Exception as e:
        print(f"❌ Failed to open database: {e}")
        print("\nMake sure you've run at least one investigation first!")
        return

    while True:
        print("\n" + "-"*70)
        print("\n1. View all investigations")
        print("2. View investigation details")
        print("3. Search by target")
        print("4. Database statistics")
        print("\n0. Back to main menu")
        print("\n" + "-"*70)

        choice = input("\nChoice: ").strip()

        if choice == '1':
            view_all_investigations(db)

        elif choice == '2':
            inv_id = input("\nEnter investigation ID: ").strip()
            try:
                view_investigation_detail(db, int(inv_id))
            except ValueError:
                print("❌ Invalid ID")

        elif choice == '3':
            target = input("\nEnter target name: ").strip()
            if target:
                search_by_target(db, target)

        elif choice == '4':
            show_stats(db)

        elif choice == '0':
            break

        else:
            print("❌ Invalid choice")

    db.close()
    print("\n✅ Database closed\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
