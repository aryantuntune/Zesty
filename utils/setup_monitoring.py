#!/usr/bin/env python3
"""
Monitoring Setup - Configure automated target monitoring
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitor import MonitoringSystem
from src.database import InvestigationDB

def print_banner():
    print("\n" + "="*70)
    print("🔔 DeepTrace Monitoring Setup")
    print("="*70 + "\n")

def list_monitors(monitor):
    """List all active monitors"""
    monitors = monitor.get_monitors()

    if not monitors:
        print("📭 No active monitors")
        return

    print(f"Active monitors: {len(monitors)}\n")
    print(f"{'ID':<30} {'Target':<20} {'Interval':<10} {'Alerts':<10}")
    print("-" * 70)

    for mon_id, mon in monitors.items():
        print(f"{mon_id[:30]:<30} {mon['target']:<20} {mon['interval']:<10} {mon['alerts_triggered']:<10}")

def add_monitor(monitor):
    """Add new monitor"""
    print("\n➕ Add New Monitor\n")

    target = input("Target username/name: ").strip()
    if not target:
        print("❌ Target required")
        return

    print("\nMonitoring interval:")
    print("1. Hourly")
    print("2. Daily (recommended)")
    print("3. Weekly")

    interval_choice = input("\nChoice (1-3): ").strip()

    intervals = {'1': 'hourly', '2': 'daily', '3': 'weekly'}
    interval = intervals.get(interval_choice, 'daily')

    print("\nAlert on (select multiple, comma-separated):")
    print("1. Bio change")
    print("2. Location change")
    print("3. Name change")
    print("4. New account discovered")

    alert_choice = input("\nChoices (e.g., 1,2,4): ").strip()

    alert_types = []
    if '1' in alert_choice:
        alert_types.append('bio_change')
    if '2' in alert_choice:
        alert_types.append('location_change')
    if '3' in alert_choice:
        alert_types.append('name_change')
    if '4' in alert_choice:
        alert_types.append('new_account')

    if not alert_types:
        alert_types = ['bio_change', 'new_account', 'location_change']

    monitor_id = monitor.add_monitor(
        target=target,
        interval=interval,
        alert_on=alert_types
    )

    print(f"\n✅ Monitor added: {monitor_id}")
    print(f"   Target: {target}")
    print(f"   Interval: {interval}")
    print(f"   Alerts: {', '.join(alert_types)}")

def remove_monitor(monitor):
    """Remove monitor"""
    monitor_id = input("\nEnter monitor ID to remove: ").strip()

    if not monitor_id:
        return

    if monitor_id in monitor.monitors:
        monitor.remove_monitor(monitor_id)
        print(f"✅ Monitor {monitor_id} removed")
    else:
        print("❌ Monitor not found")

def view_alerts(monitor):
    """View recent alerts"""
    alerts = monitor.get_alerts(limit=20)

    if not alerts:
        print("\n📭 No alerts")
        return

    print(f"\nRecent alerts ({len(alerts)}):\n")

    for alert in alerts:
        print(f"{'='*70}")
        print(f"🚨 {alert['type']}")
        print(f"Target: {alert['target']}")
        print(f"Time: {alert['timestamp']}")
        print(f"Details: {alert['details']}")

def start_monitoring(monitor):
    """Start monitoring service"""
    print("\n🚀 Starting monitoring service...")
    print("⚠️  This will run continuously. Press Ctrl+C to stop.\n")

    # Check if schedule is available
    try:
        import schedule
    except ImportError:
        print("❌ schedule library not installed")
        print("   Install with: pip install schedule")
        return

    confirm = input("Start monitoring now? (y/n): ").strip().lower()

    if confirm == 'y':
        print("\n🔍 Monitoring started...\n")

        # We can't actually run the investigation here without proper setup
        # This is a placeholder
        print("⚠️  Note: You need to integrate this with your investigation script")
        print("   See main_advanced.py for example usage")
        print("\n   To run actual monitoring, use:")
        print("   python -c \"from src.monitor import get_monitoring_system; ...\"")

def monitor_stats(monitor):
    """Show monitoring statistics"""
    monitors = monitor.get_monitors()

    if not monitors:
        print("\n📭 No monitors to show stats for")
        return

    print("\n📊 Monitoring Statistics:\n")

    for mon_id, mon in monitors.items():
        stats = monitor.get_monitor_statistics(mon_id)

        print(f"Target: {stats['target']}")
        print(f"  Uptime: {stats['uptime_days']} days")
        print(f"  Total checks: {stats['total_checks']}")
        print(f"  Alerts triggered: {stats['alerts_triggered']}")
        print(f"  Interval: {stats['interval']}")
        print(f"  Last check: {stats['last_check'] or 'Never'}")
        print()

def main():
    """Main monitoring setup"""
    print_banner()

    try:
        db = InvestigationDB()
        monitor = MonitoringSystem(db=db)
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return

    while True:
        print("\n" + "-"*70)
        print("\n1. List monitors")
        print("2. Add monitor")
        print("3. Remove monitor")
        print("4. View recent alerts")
        print("5. Monitoring statistics")
        print("6. Start monitoring service")
        print("\n0. Back to main menu")
        print("\n" + "-"*70)

        choice = input("\nChoice: ").strip()

        if choice == '1':
            list_monitors(monitor)

        elif choice == '2':
            add_monitor(monitor)

        elif choice == '3':
            remove_monitor(monitor)

        elif choice == '4':
            view_alerts(monitor)

        elif choice == '5':
            monitor_stats(monitor)

        elif choice == '6':
            start_monitoring(monitor)

        elif choice == '0':
            break

        else:
            print("❌ Invalid choice")

    db.close()
    print("\n✅ Done\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
