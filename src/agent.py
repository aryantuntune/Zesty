import asyncio
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from .utils import setup_logger
from .config import Config

try:
    from langchain_anthropic import ChatAnthropic
    from browser_use import Agent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

logger = setup_logger(__name__)


class InvestigatorAgent:
    """AI agent that uses browser automation to investigate URLs"""

    def __init__(self, headless: bool = True):
        if not AGENT_AVAILABLE:
            raise ImportError(
                "browser-use or langchain-anthropic not installed.\n"
                "Run: pip install browser-use langchain-anthropic"
            )

        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=Config.ANTHROPIC_API_KEY
        )
        self.headless = headless
        logger.info(f"Agent initialized (headless={headless})")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    async def analyze_url(
        self,
        url: str,
        mission_type: str = "PERSON"
    ) -> Dict[str, Any]:
        """
        Investigate a URL using browser automation and Claude

        Args:
            url: Target URL to analyze
            mission_type: Type of investigation (PERSON, GITHUB, PDF, etc.)

        Returns:
            Dictionary with extracted information
        """
        logger.info(f"Agent analyzing: {url} (type: {mission_type})")

        # Build task based on mission type
        if mission_type == "PERSON":
            task = f"""
Navigate to {url} and extract the following information in a structured format:

1. Full name of the person
2. Current job title and company
3. Location (city/country)
4. Email address (if visible)
5. Phone number (if visible)
6. Professional skills (technical and soft skills)
7. Education background
8. Bio/Description
9. OTHER SOCIAL MEDIA LINKS - This is critical! Look for:
   - Twitter/X handle
   - LinkedIn profile URL
   - GitHub username
   - Instagram handle
   - Personal website
   - Any other social links in bio or posts
10. Recent activity or posts (last 2-3 items)

IMPORTANT: Pay special attention to finding OTHER usernames and social links.
Return the information as a structured summary.
If the page requires login or is inaccessible, note that clearly.
"""
        elif mission_type == "GITHUB":
            task = f"""
Navigate to {url} and analyze this GitHub profile:

1. Username on GitHub
2. Real name (if available)
3. Email address (check commits, profile, README files)
4. Location (if listed)
5. Bio/Description
6. Website/blog links
7. OTHER SOCIAL LINKS (Twitter, LinkedIn, etc. in bio or profile)
8. Number of repositories
9. Top 3 most starred/popular repositories
10. Primary programming languages
11. Recent contribution activity

IMPORTANT: Extract ALL contact information and social media links.
Summarize the developer's expertise and focus areas.
"""
        elif mission_type == "PDF":
            task = f"""
Navigate to {url} (which should be a PDF or document):

1. Extract the document title
2. Identify the author(s)
3. Summarize the abstract or introduction (2-3 sentences)
4. List key topics or sections
5. Note any contact information

If it's not a PDF, describe what you found instead.
"""
        else:  # GENERIC
            task = f"""
Navigate to {url} and provide:

1. Page title and main purpose
2. Key information about the subject
3. Any contact details or social links
4. Summary of main content (3-4 sentences)
"""

        try:
            agent = Agent(
                task=task,
                llm=self.llm
            )

            result = await asyncio.wait_for(
                agent.run(),
                timeout=Config.AGENT_TIMEOUT
            )

            logger.info(f"Successfully analyzed {url}")

            return {
                "url": url,
                "status": "success",
                "data": str(result),
                "mission_type": mission_type
            }

        except asyncio.TimeoutError:
            logger.error(f"Agent timeout for {url}")
            return {
                "url": url,
                "status": "timeout",
                "data": "Analysis timed out",
                "mission_type": mission_type
            }
        except Exception as e:
            logger.error(f"Agent error for {url}: {str(e)}")
            return {
                "url": url,
                "status": "error",
                "data": f"Error: {str(e)}",
                "mission_type": mission_type
            }

    async def analyze_batch(
        self,
        urls: list,
        mission_type: str = "PERSON"
    ) -> list:
        """
        Analyze multiple URLs concurrently (with limits)

        Args:
            urls: List of URLs to analyze
            mission_type: Investigation type

        Returns:
            List of analysis results
        """
        logger.info(f"Starting batch analysis of {len(urls)} URLs")

        # Process in smaller batches to avoid overwhelming the system
        batch_size = 3
        all_results = []

        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}")

            tasks = [self.analyze_url(url, mission_type) for url in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_results.extend(results)

            # Small delay between batches
            if i + batch_size < len(urls):
                await asyncio.sleep(2)

        logger.info(f"Batch analysis complete. {len(all_results)} results.")
        return all_results

    def determine_mission_type(self, url: str) -> str:
        """Automatically determine the type of investigation based on URL"""
        url_lower = url.lower()

        if 'github.com' in url_lower:
            return 'GITHUB'
        elif url_lower.endswith('.pdf'):
            return 'PDF'
        elif any(platform in url_lower for platform in [
            'linkedin', 'twitter', 'facebook', 'instagram'
        ]):
            return 'PERSON'
        else:
            return 'GENERIC'
