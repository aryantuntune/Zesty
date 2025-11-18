import logging
import time
from pathlib import Path
from typing import List

def setup_logger(name: str, log_file: str = "deeptrace.log") -> logging.Logger:
    """Configure logging with both file and console output"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class RateLimiter:
    """Simple rate limiter to avoid hammering APIs"""

    def __init__(self, calls_per_minute: int = 10):
        self.delay = 60 / calls_per_minute
        self.last_call = 0

    def wait(self):
        """Wait if necessary to maintain rate limit"""
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_call = time.time()


def clean_url(url: str) -> str:
    """Remove tracking parameters and clean URL"""
    return url.split('?')[0].strip()


def extract_domain(url: str) -> str:
    """Extract domain from URL for graph visualization"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain if domain else "unknown"
    except Exception:
        return "unknown"


def deduplicate_leads(leads: List[str]) -> List[str]:
    """Remove duplicate URLs while preserving order"""
    seen = set()
    unique_leads = []
    for lead in leads:
        cleaned = clean_url(lead)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique_leads.append(cleaned)
    return unique_leads
