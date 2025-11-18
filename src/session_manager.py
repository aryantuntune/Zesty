"""
Session Manager: Handle authenticated access to social media
Maintains login sessions for platforms that require authentication
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from playwright.sync_api import sync_playwright
from .utils import setup_logger
from .config import Config

logger = setup_logger(__name__)


class SessionManager:
    """
    Manages authenticated sessions for social media platforms
    Stores cookies and session data to avoid repeated logins
    """

    def __init__(self, session_dir: Path = None):
        self.session_dir = session_dir or Config.DATA_DIR / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.credentials_file = Config.BASE_DIR / ".credentials.json"
        self.credentials = self._load_credentials()

        # Session state storage
        self.browser_contexts = {}

    def _load_credentials(self) -> Dict:
        """Load social media credentials from config file"""
        if not self.credentials_file.exists():
            logger.warning("No credentials file found. Create .credentials.json")
            return {}

        try:
            with open(self.credentials_file, 'r') as f:
                creds = json.load(f)
            logger.info(f"Loaded credentials for {len(creds)} platforms")
            return creds
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}

    def save_session(self, platform: str, context_state: dict):
        """Save browser context state for reuse"""
        session_file = self.session_dir / f"{platform}_session.json"
        try:
            with open(session_file, 'w') as f:
                json.dump(context_state, f)
            logger.info(f"Saved {platform} session")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def load_session(self, platform: str) -> Optional[dict]:
        """Load previously saved session"""
        session_file = self.session_dir / f"{platform}_session.json"
        if not session_file.exists():
            return None

        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def login_twitter(self, page):
        """
        Login to Twitter/X using credentials
        Handles the login flow automatically
        """
        if 'twitter' not in self.credentials:
            logger.warning("Twitter credentials not configured")
            return False

        creds = self.credentials['twitter']

        try:
            logger.info("Attempting Twitter login...")

            # Go to login page
            page.goto("https://twitter.com/i/flow/login")
            page.wait_for_timeout(2000)

            # Enter username
            username_input = page.locator('input[autocomplete="username"]')
            username_input.fill(creds['username'])
            page.keyboard.press('Enter')
            page.wait_for_timeout(2000)

            # Handle "unusual activity" verification if it appears
            if page.locator('text="Enter your phone number or username"').is_visible():
                logger.info("Twitter requesting verification...")
                page.locator('input[data-testid="ocfEnterTextTextInput"]').fill(creds['username'])
                page.keyboard.press('Enter')
                page.wait_for_timeout(2000)

            # Enter password
            password_input = page.locator('input[name="password"]')
            password_input.fill(creds['password'])
            page.keyboard.press('Enter')
            page.wait_for_timeout(3000)

            # Check if login successful
            if page.url.startswith("https://twitter.com/home"):
                logger.info("✅ Twitter login successful")
                return True
            else:
                logger.warning("Twitter login may have failed")
                return False

        except Exception as e:
            logger.error(f"Twitter login failed: {e}")
            return False

    def login_linkedin(self, page):
        """Login to LinkedIn"""
        if 'linkedin' not in self.credentials:
            logger.warning("LinkedIn credentials not configured")
            return False

        creds = self.credentials['linkedin']

        try:
            logger.info("Attempting LinkedIn login...")

            page.goto("https://www.linkedin.com/login")
            page.wait_for_timeout(2000)

            # Enter credentials
            page.fill('input#username', creds['email'])
            page.fill('input#password', creds['password'])
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)

            # Check for 2FA or captcha
            if "challenge" in page.url or "checkpoint" in page.url:
                logger.warning("LinkedIn requires 2FA/captcha - manual intervention needed")
                page.wait_for_timeout(30000)  # Wait for manual completion

            if "feed" in page.url or "mynetwork" in page.url:
                logger.info("✅ LinkedIn login successful")
                return True
            else:
                logger.warning("LinkedIn login may have failed")
                return False

        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            return False

    def login_instagram(self, page):
        """Login to Instagram"""
        if 'instagram' not in self.credentials:
            logger.warning("Instagram credentials not configured")
            return False

        creds = self.credentials['instagram']

        try:
            logger.info("Attempting Instagram login...")

            page.goto("https://www.instagram.com/accounts/login/")
            page.wait_for_timeout(2000)

            # Enter credentials
            page.fill('input[name="username"]', creds['username'])
            page.fill('input[name="password"]', creds['password'])
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)

            # Handle "Save Your Login Info" popup
            if page.locator('text="Save Your Login Info"').is_visible():
                page.click('text="Not Now"')
                page.wait_for_timeout(1000)

            # Handle notifications popup
            if page.locator('text="Turn on Notifications"').is_visible():
                page.click('text="Not Now"')
                page.wait_for_timeout(1000)

            if page.url == "https://www.instagram.com/":
                logger.info("✅ Instagram login successful")
                return True
            else:
                logger.warning("Instagram login may have failed")
                return False

        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            return False

    def login_facebook(self, page):
        """Login to Facebook"""
        if 'facebook' not in self.credentials:
            logger.warning("Facebook credentials not configured")
            return False

        creds = self.credentials['facebook']

        try:
            logger.info("Attempting Facebook login...")

            page.goto("https://www.facebook.com/login")
            page.wait_for_timeout(2000)

            page.fill('input#email', creds['email'])
            page.fill('input#pass', creds['password'])
            page.click('button[name="login"]')
            page.wait_for_timeout(3000)

            if "login" not in page.url:
                logger.info("✅ Facebook login successful")
                return True
            else:
                logger.warning("Facebook login may have failed")
                return False

        except Exception as e:
            logger.error(f"Facebook login failed: {e}")
            return False

    def auto_login(self, page, url: str) -> bool:
        """
        Automatically detect platform and login if needed

        Args:
            page: Playwright page object
            url: Target URL

        Returns:
            True if login successful or not needed
        """
        domain = url.lower()

        # Check if we need to login
        if 'twitter.com' in domain or 'x.com' in domain:
            return self.login_twitter(page)
        elif 'linkedin.com' in domain:
            return self.login_linkedin(page)
        elif 'instagram.com' in domain:
            return self.login_instagram(page)
        elif 'facebook.com' in domain:
            return self.login_facebook(page)
        else:
            # No login needed for this platform
            return True

    def create_credentials_template(self):
        """Create a template credentials file"""
        template = {
            "twitter": {
                "username": "your_twitter_username",
                "password": "your_twitter_password",
                "email": "your_email@example.com"
            },
            "linkedin": {
                "email": "your_linkedin_email@example.com",
                "password": "your_linkedin_password"
            },
            "instagram": {
                "username": "your_instagram_username",
                "password": "your_instagram_password"
            },
            "facebook": {
                "email": "your_facebook_email@example.com",
                "password": "your_facebook_password"
            }
        }

        template_file = Config.BASE_DIR / ".credentials.json.template"
        with open(template_file, 'w') as f:
            json.dump(template, f, indent=2)

        logger.info(f"Created credentials template: {template_file}")
        logger.info("Copy to .credentials.json and fill in your details")


# Initialize on import to create template if needed
def setup_credentials():
    """Helper to setup credentials file"""
    session_mgr = SessionManager()
    if not session_mgr.credentials_file.exists():
        session_mgr.create_credentials_template()
        print(f"\n⚠️  Credentials file not found!")
        print(f"Created template at: {session_mgr.credentials_file.parent}/.credentials.json.template")
        print(f"\nTo enable social media login:")
        print(f"1. Copy .credentials.json.template to .credentials.json")
        print(f"2. Fill in your social media credentials")
        print(f"3. Add .credentials.json to .gitignore (already done)\n")
