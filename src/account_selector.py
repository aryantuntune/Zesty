#!/usr/bin/env python3
"""
Account Selector - Interactive filtering of discovered accounts
Ensures we only analyze accounts belonging to the ACTUAL target
"""

from typing import List, Dict, Set
from .utils import setup_logger

logger = setup_logger(__name__)


class AccountSelector:
    """
    Interactive account selection system
    Helps users filter out false positives before deep analysis
    """

    def __init__(self):
        self.min_quality_score = 20  # Minimum quality threshold

    def score_account_quality(self, account: Dict) -> int:
        """
        Score account based on data richness (0-100)

        Args:
            account: Account data dictionary

        Returns:
            Quality score 0-100
        """
        if not account:
            return 0

        score = 0

        # Has name (20 points)
        if account.get('name'):
            score += 20

        # Has bio/description (30 points)
        bio = account.get('bio') or account.get('description')
        if bio:
            # Longer bio = better quality
            bio_length = len(str(bio))
            if bio_length > 50:
                score += 30
            elif bio_length > 20:
                score += 20
            else:
                score += 10

        # Has location (10 points)
        if account.get('location'):
            score += 10

        # Has followers/social metrics (15 points)
        if account.get('followers') or account.get('friends'):
            score += 15

        # Has posts/content (25 points)
        posts = account.get('posts', [])
        if posts:
            score += min(25, len(posts) * 5)

        return score

    def auto_filter_low_quality(
        self,
        accounts: List[Dict],
        min_score: int = None,
        show_filtered: bool = True
    ) -> List[Dict]:
        """
        Automatically filter out low-quality accounts

        Args:
            accounts: List of accounts to filter
            min_score: Minimum quality score (default: self.min_quality_score)
            show_filtered: Print filtered accounts

        Returns:
            List of high-quality accounts
        """
        if min_score is None:
            min_score = self.min_quality_score

        high_quality = []
        low_quality = []

        for account in accounts:
            if not account:
                continue

            score = self.score_account_quality(account)
            account['quality_score'] = score

            if score >= min_score:
                high_quality.append(account)
            else:
                low_quality.append(account)

        if show_filtered and low_quality:
            logger.info(f"🗑️  Filtered out {len(low_quality)} low-quality accounts:")
            for account in low_quality:
                url = account.get('url', 'Unknown')
                score = account.get('quality_score', 0)
                logger.info(f"   ❌ {url} (score: {score})")

        logger.info(f"✅ Kept {len(high_quality)}/{len(accounts)} high-quality accounts")

        return high_quality

    def categorize_by_quality(self, accounts: List[Dict]) -> Dict:
        """
        Categorize accounts by quality tier

        Args:
            accounts: List of accounts

        Returns:
            {
                'excellent': [],  # 80-100 score
                'good': [],       # 50-79 score
                'fair': [],       # 20-49 score
                'poor': []        # 0-19 score
            }
        """
        categorized = {
            'excellent': [],
            'good': [],
            'fair': [],
            'poor': []
        }

        for account in accounts:
            if not account:
                continue

            score = self.score_account_quality(account)
            account['quality_score'] = score

            if score >= 80:
                categorized['excellent'].append(account)
            elif score >= 50:
                categorized['good'].append(account)
            elif score >= 20:
                categorized['fair'].append(account)
            else:
                categorized['poor'].append(account)

        return categorized

    def display_account_preview(self, index: int, account: Dict, total: int) -> str:
        """
        Create a preview display for an account

        Args:
            index: Account number (1-based)
            account: Account data from scraper
            total: Total number of accounts

        Returns:
            Formatted preview string
        """
        url = account.get('url', 'Unknown')
        platform = account.get('platform', 'unknown')
        name = account.get('name', 'N/A')
        bio = account.get('bio', 'N/A')
        location = account.get('location', 'N/A')
        followers = account.get('followers', 'N/A')

        # Calculate quality score
        quality_score = account.get('quality_score') or self.score_account_quality(account)

        # Quality indicator
        if quality_score >= 80:
            quality_indicator = "🟢 EXCELLENT"
        elif quality_score >= 50:
            quality_indicator = "🟡 GOOD"
        elif quality_score >= 20:
            quality_indicator = "🟠 FAIR"
        else:
            quality_indicator = "🔴 POOR"

        # Truncate bio
        if bio and len(bio) > 150:
            bio = bio[:147] + "..."

        preview = f"""
{'='*70}
Account #{index}/{total} | Quality: {quality_indicator} ({quality_score}/100)
{'='*70}

🌐 Platform: {platform.upper()}
🔗 URL: {url}
👤 Name: {name}
📍 Location: {location}
👥 Followers: {followers}

📝 Bio:
{bio or '(No bio available)'}

{'='*70}
"""
        return preview

    def ask_user_confirmation(self, account: Dict, index: int, total: int) -> bool:
        """
        Ask user if this account belongs to target

        Returns:
            True if user confirms, False otherwise
        """
        print(self.display_account_preview(index, account, total))

        while True:
            response = input(f"\n❓ Is this the CORRECT target? (y/n/s=skip remaining/q=quit): ").strip().lower()

            if response == 'y':
                return True
            elif response == 'n':
                return False
            elif response == 's':
                return 'skip'
            elif response == 'q':
                return 'quit'
            else:
                print("❌ Invalid input. Please enter y, n, s, or q")

    def batch_display_accounts(self, accounts: List[Dict]) -> None:
        """
        Display all accounts in a summary table
        """
        print("\n" + "="*70)
        print("📋 DISCOVERED ACCOUNTS SUMMARY")
        print("="*70 + "\n")

        print(f"{'#':<4} {'Platform':<15} {'Name':<25} {'Location':<20}")
        print("-" * 70)

        for i, account in enumerate(accounts, 1):
            # Skip None accounts
            if account is None:
                print(f"{i:<4} {'unknown':<15} {'N/A':<25} {'N/A':<20}")
                continue

            platform = account.get('platform', 'unknown')[:14]
            name = (account.get('name') or 'N/A')[:24]
            location = (account.get('location') or 'N/A')[:19]

            print(f"{i:<4} {platform:<15} {name:<25} {location:<20}")

        print("-" * 70)
        print(f"\nTotal: {len(accounts)} accounts found\n")

    def quick_filter_by_criteria(self, accounts: List[Dict], target_name: str) -> Dict:
        """
        Quick filter accounts by common criteria

        Args:
            accounts: List of discovered accounts
            target_name: Original target name

        Returns:
            {
                'exact_match': [],      # Name exactly matches
                'partial_match': [],    # Name partially matches
                'no_name': []          # No name available
            }
        """
        categorized = {
            'exact_match': [],
            'partial_match': [],
            'no_name': []
        }

        target_lower = target_name.lower()

        for account in accounts:
            # Skip None accounts
            if account is None:
                continue

            name = (account.get('name') or '').lower()

            if not name:
                categorized['no_name'].append(account)
            elif name == target_lower:
                categorized['exact_match'].append(account)
            elif target_lower in name or name in target_lower:
                categorized['partial_match'].append(account)
            else:
                categorized['no_name'].append(account)

        return categorized

    def interactive_selection(
        self,
        accounts: List[Dict],
        target_name: str,
        auto_mode: bool = False
    ) -> List[Dict]:
        """
        Main interactive selection process

        Args:
            accounts: All discovered accounts
            target_name: Target name
            auto_mode: If True, skip confirmation for exact matches

        Returns:
            List of confirmed accounts
        """
        if not accounts:
            print("\n❌ No accounts found to select from")
            return []

        print("\n" + "="*70)
        # Filter out None accounts first
        accounts = [acc for acc in accounts if acc is not None]

        print("🎯 ACCOUNT VERIFICATION & SELECTION")
        print("="*70)
        print(f"\nTarget: {target_name}")
        print(f"Found: {len(accounts)} potential accounts")
        print("\nℹ️  We need to verify which accounts belong to the ACTUAL target.")
        print("   (Multiple people may share the same name!)")
        print("="*70 + "\n")

        # Show summary first
        self.batch_display_accounts(accounts)

        # Quick categorization
        categorized = self.quick_filter_by_criteria(accounts, target_name)

        print(f"📊 Quick Analysis:")
        print(f"   ✅ Exact name matches: {len(categorized['exact_match'])}")
        print(f"   ⚠️  Partial matches: {len(categorized['partial_match'])}")
        print(f"   ❓ No name data: {len(categorized['no_name'])}\n")

        # Selection mode
        print("Choose verification mode:")
        print("1. Manual - Review each account individually (RECOMMENDED)")
        print("2. Quick  - Auto-accept exact matches only")
        print("3. All    - Accept all accounts (NOT RECOMMENDED)")
        print("4. Custom - Select by account numbers\n")

        mode = input("Mode (1-4, default=1): ").strip() or '1'

        confirmed = []

        if mode == '1':
            # Manual review
            confirmed = self._manual_review(accounts)

        elif mode == '2':
            # Auto-accept exact matches
            confirmed = categorized['exact_match'].copy()
            print(f"\n✅ Auto-accepted {len(confirmed)} exact name matches")

            # Ask about partial matches
            if categorized['partial_match']:
                print(f"\n⚠️  Found {len(categorized['partial_match'])} partial matches")
                review = input("Review partial matches? (y/n): ").strip().lower()

                if review == 'y':
                    confirmed.extend(self._manual_review(categorized['partial_match']))

        elif mode == '3':
            # Accept all (dangerous!)
            print("\n⚠️  WARNING: Accepting ALL accounts without verification!")
            print("   This may include unrelated people with the same name.")
            confirm = input("\nAre you sure? (type 'yes' to confirm): ").strip()

            if confirm.lower() == 'yes':
                confirmed = accounts.copy()
                print(f"✅ Accepted all {len(confirmed)} accounts")
            else:
                print("❌ Cancelled. Switching to manual review...")
                confirmed = self._manual_review(accounts)

        elif mode == '4':
            # Custom selection
            confirmed = self._custom_selection(accounts)

        else:
            print("❌ Invalid mode. Using manual review...")
            confirmed = self._manual_review(accounts)

        # Summary
        print("\n" + "="*70)
        print("✅ SELECTION COMPLETE")
        print("="*70)
        print(f"\nConfirmed accounts: {len(confirmed)}/{len(accounts)}")
        print(f"Filtered out: {len(accounts) - len(confirmed)}")

        if confirmed:
            print("\n📋 Selected accounts:")
            for i, account in enumerate(confirmed, 1):
                platform = account.get('platform', 'unknown')
                url = account.get('url', '')
                print(f"   {i}. {platform}: {url}")
        else:
            print("\n⚠️  No accounts selected!")

        print("="*70 + "\n")

        return confirmed

    def _manual_review(self, accounts: List[Dict]) -> List[Dict]:
        """Manual review mode - check each account"""
        confirmed = []

        print("\n🔍 Starting manual review...")
        print("   (Review each account carefully)\n")

        for i, account in enumerate(accounts, 1):
            result = self.ask_user_confirmation(account, i, len(accounts))

            if result == True:
                confirmed.append(account)
                print(f"✅ Account #{i} CONFIRMED\n")
            elif result == False:
                print(f"❌ Account #{i} REJECTED\n")
            elif result == 'skip':
                print(f"\n⏩ Skipping remaining {len(accounts) - i} accounts...")
                break
            elif result == 'quit':
                print("\n⚠️  Exiting selection...")
                break

        return confirmed

    def _custom_selection(self, accounts: List[Dict]) -> List[Dict]:
        """Custom selection by account numbers"""
        print("\n📝 Custom Selection Mode")
        print(f"   Enter account numbers (1-{len(accounts)}), comma-separated")
        print(f"   Example: 1,3,5,7")
        print(f"   Or ranges: 1-5,8,10-12\n")

        while True:
            selection = input("Account numbers: ").strip()

            if not selection:
                print("❌ No selection provided")
                continue

            try:
                indices = self._parse_selection(selection, len(accounts))

                if not indices:
                    print("❌ No valid indices")
                    continue

                confirmed = [accounts[i-1] for i in indices]

                print(f"\n✅ Selected {len(confirmed)} accounts")
                return confirmed

            except Exception as e:
                print(f"❌ Invalid selection: {e}")
                print("   Try again or press Ctrl+C to cancel")

    def _parse_selection(self, selection: str, max_value: int) -> Set[int]:
        """
        Parse selection string into set of indices

        Examples:
            "1,2,3" -> {1, 2, 3}
            "1-5,8" -> {1, 2, 3, 4, 5, 8}
        """
        indices = set()

        parts = selection.split(',')

        for part in parts:
            part = part.strip()

            if '-' in part:
                # Range
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())

                for i in range(start, end + 1):
                    if 1 <= i <= max_value:
                        indices.add(i)
            else:
                # Single number
                num = int(part)
                if 1 <= num <= max_value:
                    indices.add(num)

        return indices

    def save_selection_log(self, confirmed: List[Dict], rejected: List[Dict], log_file: str):
        """
        Save selection decisions for audit trail
        """
        import json
        from datetime import datetime

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'confirmed': [acc.get('url') for acc in confirmed],
            'rejected': [acc.get('url') for acc in rejected],
            'confirmed_count': len(confirmed),
            'rejected_count': len(rejected)
        }

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Selection log saved to {log_file}")


# Convenience function
def select_accounts(accounts: List[Dict], target_name: str, auto_mode: bool = False) -> List[Dict]:
    """
    Interactive account selection

    Args:
        accounts: List of discovered accounts
        target_name: Target name for filtering
        auto_mode: If True, auto-accept exact matches

    Returns:
        List of user-confirmed accounts
    """
    selector = AccountSelector()
    return selector.interactive_selection(accounts, target_name, auto_mode)
