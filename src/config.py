import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration and environment setup for DeepTrace"""

    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Ethical & Operational Settings
    ETHICAL_MODE = True      # Respects robots.txt and rate limits
    HEADLESS = False         # Set False to watch browser (demo mode)
    MAX_LEADS = 5            # Limit leads to process (save API costs)

    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    INPUT_DIR = DATA_DIR / "input"
    RAW_LEADS_DIR = DATA_DIR / "raw_leads"
    REPORTS_DIR = DATA_DIR / "reports"

    # Rate Limiting
    REQUESTS_PER_MINUTE = 10
    SHERLOCK_TIMEOUT = 10  # Timeout per site (seconds) - increased from 5
    SHERLOCK_TOTAL_TIMEOUT = 300  # Total Sherlock timeout (5 minutes) - NEW!
    AGENT_TIMEOUT = 60

    @classmethod
    def validate(cls):
        """Validates configuration and creates necessary directories"""
        # Check API key
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "CRITICAL: ANTHROPIC_API_KEY not found in environment.\n"
                "Create a .env file with: ANTHROPIC_API_KEY=sk-ant-..."
            )

        # Create directories if they don't exist
        for directory in [cls.INPUT_DIR, cls.RAW_LEADS_DIR, cls.REPORTS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

        return True

    @classmethod
    def validate_independent(cls):
        """Validates configuration without requiring API key (for independent mode)"""
        # Create directories if they don't exist
        for directory in [cls.INPUT_DIR, cls.RAW_LEADS_DIR, cls.REPORTS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

        return True

    @classmethod
    def get_target_image_path(cls):
        """Returns path to target.jpg if it exists"""
        target_path = cls.INPUT_DIR / "target.jpg"
        return target_path if target_path.exists() else None
