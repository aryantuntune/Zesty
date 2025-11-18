import subprocess
import os
import json
from pathlib import Path
from typing import List
from .utils import setup_logger, RateLimiter, deduplicate_leads
from .config import Config

try:
    from googlesearch import search
except ImportError:
    search = None

logger = setup_logger(__name__)


class Dragnet:
    """OSINT reconnaissance using Sherlock and Google Dorks"""

    def __init__(self, target: str):
        self.target = target
        self.leads: List[str] = []
        self.rate_limiter = RateLimiter(calls_per_minute=Config.REQUESTS_PER_MINUTE)

    def run_sherlock(self) -> bool:
        """Execute Sherlock to find social media accounts"""
        logger.info(f"Launching Sherlock for target: {self.target}")

        # Sanitize filename
        safe_target = self.target.replace(' ', '_').replace('/', '_')
        output_file = Config.RAW_LEADS_DIR / f"{safe_target}_sherlock.txt"

        try:
            # Use longer timeout (5 minutes for 300+ sites)
            # Use python -m sherlock_project to work without PATH
            import sys
            result = subprocess.run(
                [
                    sys.executable, "-m", "sherlock_project",
                    self.target,
                    "--timeout", str(Config.SHERLOCK_TIMEOUT),
                    "--print-found",
                    "--output", str(output_file)
                ],
                capture_output=True,
                text=True,
                timeout=Config.SHERLOCK_TOTAL_TIMEOUT  # 5 minutes instead of 60 seconds
            )

            # Parse output file
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and line.startswith('http'):
                            self.leads.append(line)

                logger.info(f"Sherlock found {len(self.leads)} accounts")
                return True
            else:
                logger.warning("Sherlock output file not created")
                # Check stdout for results
                if result.stdout and 'http' in result.stdout:
                    logger.info("Parsing results from stdout")
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line and line.startswith('http'):
                            self.leads.append(line)
                    if self.leads:
                        return True
                return False

        except FileNotFoundError:
            logger.error(
                "Sherlock not installed. Run: pip install sherlock-project"
            )
            return False
        except subprocess.TimeoutExpired:
            logger.warning(f"Sherlock timed out after {Config.SHERLOCK_TOTAL_TIMEOUT}s")

            # Even if timeout, check if output file has partial results
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and line.startswith('http'):
                            self.leads.append(line)

                if self.leads:
                    logger.info(f"Found {len(self.leads)} accounts before timeout")
                    return True

            return False
        except Exception as e:
            logger.error(f"Sherlock error: {str(e)}")
            return False

    def run_google_dorks(self) -> bool:
        """Use Google Dorks to find additional information"""
        if search is None:
            logger.warning("googlesearch-python not installed, skipping Google Dorks")
            return False

        logger.info("Running Google Dorks reconnaissance")

        dork_queries = [
            f'site:linkedin.com/in "{self.target}"',
            f'site:github.com "{self.target}"',
            f'site:twitter.com "{self.target}"',
            f'site:facebook.com "{self.target}"',
            f'site:instagram.com "{self.target}"',
        ]

        dork_results = []

        try:
            for i, query in enumerate(dork_queries, 1):
                self.rate_limiter.wait()  # Respect rate limits
                try:
                    logger.debug(f"Running dork query {i}/{len(dork_queries)}: {query[:50]}...")
                    results = list(search(query, num_results=3, sleep_interval=3, lang='en'))
                    dork_results.extend(results)
                    logger.debug(f"  Found {len(results)} results")
                except Exception as e:
                    logger.debug(f"Dork query failed for '{query[:50]}...': {str(e)}")
                    # Don't stop on individual query failures
                    continue

            # Deduplicate and filter
            dork_results = list(set(dork_results))

            self.leads.extend(dork_results)
            logger.info(f"Google Dorks found {len(dork_results)} additional leads")

            # Return True even if no results (it ran successfully)
            return True

        except Exception as e:
            logger.error(f"Google Dorks error: {str(e)}")
            logger.warning("Google may be rate-limiting or blocking automated searches")
            return False

    def add_manual_urls(self, urls: List[str]):
        """
        Add URLs manually (fallback if Sherlock/Dorks fail)

        Args:
            urls: List of URLs to add
        """
        for url in urls:
            url = url.strip()
            if url and url.startswith('http'):
                self.leads.append(url)
        logger.info(f"Added {len(urls)} manual URLs")

    def get_unique_leads(self) -> List[str]:
        """Return deduplicated list of URLs"""
        unique = deduplicate_leads(self.leads)
        logger.info(f"Total unique leads: {len(unique)}")
        return unique

    def save_leads(self, filename: str = None):
        """Save leads to file for later analysis"""
        if filename is None:
            filename = f"{self.target}_all_leads.txt"

        filepath = Config.RAW_LEADS_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            for lead in self.get_unique_leads():
                f.write(f"{lead}\n")

        logger.info(f"Leads saved to {filepath}")
