"""
Account utility functions for safe handling of account dictionaries
"""

from typing import List, Dict, Optional, Any


def filter_none_accounts(accounts: List[Optional[Dict]]) -> List[Dict]:
    """
    Filter out None values from account lists

    Args:
        accounts: List of account dictionaries (may contain None)

    Returns:
        List of valid account dictionaries (None values removed)
    """
    return [acc for acc in accounts if acc is not None]


def safe_get(account: Optional[Dict], key: str, default: Any = None) -> Any:
    """
    Safely get value from account dictionary, handling None accounts

    Args:
        account: Account dictionary (may be None)
        key: Key to retrieve
        default: Default value if key not found or account is None

    Returns:
        Value from account or default
    """
    if account is None:
        return default
    return account.get(key, default)


def is_valid_account(account: Optional[Dict]) -> bool:
    """
    Check if account is valid (not None and has minimum required fields)

    Args:
        account: Account dictionary to check

    Returns:
        True if account is valid, False otherwise
    """
    if account is None:
        return False

    # Must have at least a URL or platform
    return bool(account.get('url') or account.get('platform'))


def process_accounts_safely(accounts: List[Optional[Dict]],
                           processor_func,
                           skip_invalid: bool = True) -> List:
    """
    Process accounts with automatic None filtering

    Args:
        accounts: List of account dictionaries
        processor_func: Function to apply to each account
        skip_invalid: Skip None accounts if True, otherwise raise error

    Returns:
        List of processed results
    """
    results = []

    for account in accounts:
        if account is None:
            if skip_invalid:
                continue
            else:
                raise ValueError("Encountered None account in processing")

        try:
            result = processor_func(account)
            results.append(result)
        except Exception as e:
            # Log error but continue processing
            print(f"Warning: Error processing account: {e}")
            continue

    return results
