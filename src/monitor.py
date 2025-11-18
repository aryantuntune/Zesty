"""
Automated Monitoring System: Schedule periodic investigations and detect changes
Tracks targets over time and alerts on significant changes
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Callable, Optional
from .utils import setup_logger
from .config import Config

logger = setup_logger(__name__)

# Try to import schedule
try:
    import schedule
    SCHEDULE_AVAILABLE = True
    logger.info("Schedule library available for automated monitoring")
except ImportError:
    SCHEDULE_AVAILABLE = False
    logger.warning("Schedule not installed. Install with: pip install schedule")


class MonitoringSystem:
    """
    Automated monitoring and alerting system

    Features:
    - Schedule periodic re-checks
    - Detect profile changes
    - Alert on new accounts discovered
    - Track monitoring history
    """

    def __init__(self, db=None):
        self.db = db  # InvestigationDB instance
        self.monitors_file = Config.DATA_DIR / "monitors.json"
        self.alerts_file = Config.DATA_DIR / "alerts.json"

        # Load existing monitors
        self.monitors = self._load_monitors()

        # Alert handlers (extensible)
        self.alert_handlers = []

        # Default: console and file alerts
        self.add_alert_handler(self._console_alert)
        self.add_alert_handler(self._file_alert)

    def _load_monitors(self) -> Dict:
        """Load monitoring configurations from file"""
        if self.monitors_file.exists():
            try:
                with open(self.monitors_file, 'r') as f:
                    monitors = json.load(f)
                logger.info(f"Loaded {len(monitors)} monitors")
                return monitors
            except Exception as e:
                logger.error(f"Failed to load monitors: {e}")
                return {}
        return {}

    def _save_monitors(self):
        """Save monitoring configurations to file"""
        try:
            with open(self.monitors_file, 'w') as f:
                json.dump(self.monitors, f, indent=2)
            logger.info("Monitors saved")
        except Exception as e:
            logger.error(f"Failed to save monitors: {e}")

    def add_monitor(
        self,
        target: str,
        interval: str = 'daily',
        alert_on: List[str] = None
    ) -> str:
        """
        Add a target to monitoring

        Args:
            target: Target username/name
            interval: 'hourly', 'daily', 'weekly'
            alert_on: List of change types to alert on
                ['bio_change', 'new_account', 'location_change', 'name_change']

        Returns:
            monitor_id
        """
        if alert_on is None:
            alert_on = ['bio_change', 'new_account', 'location_change', 'name_change']

        monitor_id = f"{target}_{int(time.time())}"

        monitor = {
            'target': target,
            'interval': interval,
            'alert_on': alert_on,
            'created_at': datetime.now().isoformat(),
            'last_check': None,
            'check_count': 0,
            'alerts_triggered': 0
        }

        self.monitors[monitor_id] = monitor
        self._save_monitors()

        logger.info(f"Added monitor: {target} ({interval})")

        return monitor_id

    def remove_monitor(self, monitor_id: str):
        """Remove a monitor"""
        if monitor_id in self.monitors:
            del self.monitors[monitor_id]
            self._save_monitors()
            logger.info(f"Removed monitor: {monitor_id}")

    def get_monitors(self) -> Dict:
        """Get all active monitors"""
        return self.monitors

    def add_alert_handler(self, handler: Callable):
        """
        Add custom alert handler

        Handler signature: handler(alert_data: Dict)
        """
        self.alert_handlers.append(handler)

    def _console_alert(self, alert_data: Dict):
        """Default console alert handler"""
        print("\n" + "="*60)
        print("🚨 DEEPTRACE ALERT")
        print("="*60)
        print(f"Target: {alert_data['target']}")
        print(f"Type: {alert_data['type']}")
        print(f"Time: {alert_data['timestamp']}")
        print(f"\nDetails: {alert_data['details']}")
        print("="*60 + "\n")

    def _file_alert(self, alert_data: Dict):
        """Save alert to file"""
        try:
            # Load existing alerts
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r') as f:
                    alerts = json.load(f)
            else:
                alerts = []

            # Add new alert
            alerts.append(alert_data)

            # Save
            with open(self.alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2)

            logger.info(f"Alert saved to {self.alerts_file}")

        except Exception as e:
            logger.error(f"Failed to save alert: {e}")

    def trigger_alert(self, target: str, alert_type: str, details: str):
        """
        Trigger an alert

        Args:
            target: Target name
            alert_type: Type of alert
            details: Alert details
        """
        alert_data = {
            'target': target,
            'type': alert_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        # Call all alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        logger.info(f"Alert triggered: {target} - {alert_type}")

    def check_target(self, target: str, investigation_func: Callable) -> Dict:
        """
        Check a target for changes

        Args:
            target: Target name
            investigation_func: Function to run investigation
                Signature: func(target: str) -> Dict

        Returns:
            {
                'changes_detected': bool,
                'changes': List[str],
                'new_data': Dict
            }
        """
        logger.info(f"Checking target: {target}")

        # Run investigation
        new_data = investigation_func(target)

        # Get historical data from database
        if self.db:
            history = self.db.get_investigation_history(target)
        else:
            history = []

        changes = []

        if not history:
            # First check - no comparison
            logger.info(f"First check for {target} - no historical data")
            return {
                'changes_detected': False,
                'changes': ['First check - baseline established'],
                'new_data': new_data
            }

        # Compare with last investigation
        last_investigation = history[0]

        # Check for new accounts
        if self.db:
            # Get accounts from last investigation
            # This would require extending the database to store investigation-account relationships
            pass

        # Placeholder: Detect changes
        # In real implementation, compare new_data with last_investigation

        return {
            'changes_detected': len(changes) > 0,
            'changes': changes,
            'new_data': new_data
        }

    def run_scheduled_check(self, monitor_id: str, investigation_func: Callable):
        """
        Run a scheduled check for a monitor

        Args:
            monitor_id: Monitor ID
            investigation_func: Investigation function
        """
        if monitor_id not in self.monitors:
            logger.warning(f"Monitor not found: {monitor_id}")
            return

        monitor = self.monitors[monitor_id]
        target = monitor['target']
        alert_on = monitor['alert_on']

        logger.info(f"Running scheduled check: {target}")

        # Check target
        result = self.check_target(target, investigation_func)

        # Update monitor
        monitor['last_check'] = datetime.now().isoformat()
        monitor['check_count'] += 1

        # Trigger alerts if changes detected
        if result['changes_detected']:
            for change in result['changes']:
                # Determine change type
                change_type = 'unknown'

                if 'bio' in change.lower():
                    change_type = 'bio_change'
                elif 'location' in change.lower():
                    change_type = 'location_change'
                elif 'name' in change.lower():
                    change_type = 'name_change'
                elif 'new account' in change.lower():
                    change_type = 'new_account'

                # Alert if configured
                if change_type in alert_on or 'unknown' in alert_on:
                    self.trigger_alert(target, change_type, change)
                    monitor['alerts_triggered'] += 1

        self._save_monitors()

        logger.info(f"Scheduled check complete: {target}")

    def start_monitoring(self, investigation_func: Callable):
        """
        Start continuous monitoring (blocking)

        Args:
            investigation_func: Function to run investigations
        """
        if not SCHEDULE_AVAILABLE:
            logger.error("Schedule library not available. Cannot start monitoring.")
            print("❌ Install schedule library: pip install schedule")
            return

        # Schedule all monitors
        for monitor_id, monitor in self.monitors.items():
            interval = monitor['interval']
            target = monitor['target']

            # Create job
            job = lambda mid=monitor_id: self.run_scheduled_check(mid, investigation_func)

            if interval == 'hourly':
                schedule.every().hour.do(job)
            elif interval == 'daily':
                schedule.every().day.at("09:00").do(job)
            elif interval == 'weekly':
                schedule.every().week.do(job)
            else:
                logger.warning(f"Unknown interval: {interval}")

            logger.info(f"Scheduled: {target} ({interval})")

        print("\n🔍 DeepTrace Monitoring Started")
        print(f"Monitoring {len(self.monitors)} targets")
        print("Press Ctrl+C to stop\n")

        # Run scheduler
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring stopped by user")
            logger.info("Monitoring stopped")

    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """
        Get recent alerts

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of alerts (most recent first)
        """
        if not self.alerts_file.exists():
            return []

        try:
            with open(self.alerts_file, 'r') as f:
                alerts = json.load(f)

            # Sort by timestamp (most recent first)
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)

            return alerts[:limit]

        except Exception as e:
            logger.error(f"Failed to load alerts: {e}")
            return []

    def get_monitor_statistics(self, monitor_id: str) -> Dict:
        """
        Get statistics for a monitor

        Returns:
            {
                'target': str,
                'total_checks': int,
                'alerts_triggered': int,
                'uptime_days': int,
                'last_check': str
            }
        """
        if monitor_id not in self.monitors:
            return {}

        monitor = self.monitors[monitor_id]

        # Calculate uptime
        created = datetime.fromisoformat(monitor['created_at'])
        uptime = (datetime.now() - created).days

        return {
            'target': monitor['target'],
            'total_checks': monitor['check_count'],
            'alerts_triggered': monitor['alerts_triggered'],
            'uptime_days': uptime,
            'last_check': monitor['last_check'],
            'interval': monitor['interval']
        }


# Convenience function
def get_monitoring_system(db=None) -> MonitoringSystem:
    """Get monitoring system instance"""
    return MonitoringSystem(db=db)
