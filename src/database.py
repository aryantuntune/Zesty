"""
Investigation Database: Persistence layer for DeepTrace
Stores all investigations, accounts, and tracks changes over time
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .utils import setup_logger
from .config import Config

logger = setup_logger(__name__)


class InvestigationDB:
    """SQLite database for storing investigation history and results"""

    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Config.DATA_DIR / "deeptrace.db"

        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self.create_tables()
        logger.info(f"Database initialized: {db_path}")

    def create_tables(self):
        """Create database schema"""

        # Investigations table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                num_accounts INTEGER,
                num_predictions INTEGER,
                high_confidence_matches INTEGER,
                interests TEXT,
                report_path TEXT,
                graph_path TEXT
            )
        ''')

        # Accounts table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investigation_id INTEGER,
                url TEXT UNIQUE,
                platform TEXT,
                username TEXT,
                name TEXT,
                bio TEXT,
                location TEXT,
                email TEXT,
                followers INTEGER,
                following INTEGER,
                scraped_data TEXT,
                similarity_score REAL,
                match_reasons TEXT,
                discovered_via TEXT,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (investigation_id) REFERENCES investigations(id)
            )
        ''')

        # Account changes table (track evolution)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS account_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                field TEXT,
                old_value TEXT,
                new_value TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        ''')

        # Activity patterns table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                peak_hours TEXT,
                active_days TEXT,
                timezone TEXT,
                pattern_type TEXT,
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        ''')

        # Create indexes for performance
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_accounts_url ON accounts(url)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_investigations_target ON investigations(target)')

        self.conn.commit()
        logger.info("Database tables created/verified")

    def save_investigation(
        self,
        target: str,
        accounts: List[Dict],
        predictions: List[str],
        interests: List[str],
        high_confidence_count: int,
        report_path: str = None,
        graph_path: str = None
    ) -> int:
        """
        Save investigation results to database

        Returns:
            investigation_id
        """
        cursor = self.conn.execute('''
            INSERT INTO investigations
            (target, num_accounts, num_predictions, high_confidence_matches, interests, report_path, graph_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            target,
            len(accounts),
            len(predictions),
            high_confidence_count,
            json.dumps(interests),
            report_path,
            graph_path
        ))

        investigation_id = cursor.lastrowid

        # Save all accounts
        for account in accounts:
            self.save_account(investigation_id, account)

        self.conn.commit()
        logger.info(f"Investigation saved: ID={investigation_id}, target={target}, accounts={len(accounts)}")

        return investigation_id

    def save_account(self, investigation_id: int, account: Dict):
        """Save individual account to database"""

        result = account.get('result', {})
        profile = account.get('behavioral_profile', {})

        # Check if account exists
        existing = self.get_account_by_url(account['url'])

        if existing:
            # Account exists - check for changes
            self._detect_and_save_changes(existing, account)

            # Update account
            self.conn.execute('''
                UPDATE accounts SET
                    name = ?, bio = ?, location = ?, email = ?,
                    followers = ?, following = ?,
                    scraped_data = ?, similarity_score = ?,
                    match_reasons = ?, last_updated = ?
                WHERE url = ?
            ''', (
                result.get('name'),
                result.get('bio'),
                result.get('location'),
                result.get('email'),
                result.get('followers', 0),
                result.get('following', 0),
                json.dumps(result),
                account.get('similarity_score'),
                json.dumps(account.get('match_reasons', [])),
                datetime.now(),
                account['url']
            ))
        else:
            # New account - insert
            self.conn.execute('''
                INSERT INTO accounts
                (investigation_id, url, platform, username, name, bio, location, email,
                 followers, following, scraped_data, similarity_score, match_reasons, discovered_via)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                investigation_id,
                account['url'],
                result.get('platform', 'unknown'),
                result.get('username', ''),
                result.get('name', ''),
                result.get('bio', ''),
                result.get('location', ''),
                result.get('email', ''),
                result.get('followers', 0),
                result.get('following', 0),
                json.dumps(result),
                account.get('similarity_score'),
                json.dumps(account.get('match_reasons', [])),
                account.get('discovered_via', 'initial')
            ))

        self.conn.commit()

    def _detect_and_save_changes(self, old_account: Dict, new_account: Dict):
        """Detect what changed and save to account_changes table"""

        result = new_account.get('result', {})

        fields_to_track = ['name', 'bio', 'location', 'followers', 'following']

        for field in fields_to_track:
            old_value = old_account.get(field)
            new_value = result.get(field)

            if old_value != new_value and new_value is not None:
                self.conn.execute('''
                    INSERT INTO account_changes (account_id, field, old_value, new_value)
                    VALUES (?, ?, ?, ?)
                ''', (old_account['id'], field, str(old_value), str(new_value)))

                logger.info(f"Change detected for {old_account['url']}: {field} changed")

    def get_account_by_url(self, url: str) -> Optional[Dict]:
        """Retrieve account by URL"""
        cursor = self.conn.execute('SELECT * FROM accounts WHERE url = ?', (url,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_cached_account(self, url: str, max_age_hours: int = 24) -> Optional[Dict]:
        """
        Get cached account data if recent enough

        Returns:
            Account dict or None if too old/doesn't exist
        """
        cursor = self.conn.execute('''
            SELECT * FROM accounts
            WHERE url = ?
            AND datetime(last_updated) > datetime('now', '-{} hours')
        '''.format(max_age_hours), (url,))

        row = cursor.fetchone()

        if row:
            account = dict(row)
            account['scraped_data'] = json.loads(account['scraped_data'])
            logger.info(f"Cache HIT: {url} (age < {max_age_hours}h)")
            return account

        logger.info(f"Cache MISS: {url}")
        return None

    def get_investigation_history(self, target: str) -> List[Dict]:
        """Get all investigations for a target"""
        cursor = self.conn.execute('''
            SELECT * FROM investigations
            WHERE target = ?
            ORDER BY timestamp DESC
        ''', (target,))

        return [dict(row) for row in cursor.fetchall()]

    def get_account_changes(self, url: str) -> List[Dict]:
        """Get change history for an account"""
        cursor = self.conn.execute('''
            SELECT ac.* FROM account_changes ac
            JOIN accounts a ON ac.account_id = a.id
            WHERE a.url = ?
            ORDER BY ac.detected_at DESC
        ''', (url,))

        return [dict(row) for row in cursor.fetchall()]

    def save_activity_pattern(
        self,
        url: str,
        peak_hours: List[int],
        active_days: List[int],
        timezone: str,
        pattern_type: str
    ):
        """Save temporal activity pattern for account"""

        account = self.get_account_by_url(url)
        if not account:
            logger.warning(f"Cannot save pattern - account not found: {url}")
            return

        self.conn.execute('''
            INSERT INTO activity_patterns
            (account_id, peak_hours, active_days, timezone, pattern_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            account['id'],
            json.dumps(peak_hours),
            json.dumps(active_days),
            timezone,
            pattern_type
        ))

        self.conn.commit()
        logger.info(f"Activity pattern saved for {url}")

    def get_statistics(self) -> Dict:
        """Get database statistics"""

        stats = {}

        # Total investigations
        cursor = self.conn.execute('SELECT COUNT(*) as count FROM investigations')
        stats['total_investigations'] = cursor.fetchone()['count']

        # Total accounts
        cursor = self.conn.execute('SELECT COUNT(*) as count FROM accounts')
        stats['total_accounts'] = cursor.fetchone()['count']

        # Accounts by platform
        cursor = self.conn.execute('''
            SELECT platform, COUNT(*) as count
            FROM accounts
            GROUP BY platform
            ORDER BY count DESC
        ''')
        stats['accounts_by_platform'] = [dict(row) for row in cursor.fetchall()]

        # Total changes tracked
        cursor = self.conn.execute('SELECT COUNT(*) as count FROM account_changes')
        stats['total_changes'] = cursor.fetchone()['count']

        return stats

    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("Database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions

def get_db() -> InvestigationDB:
    """Get database instance"""
    return InvestigationDB()
