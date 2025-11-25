"""
ESPN NCAAF News & Blog Scraper

Fetches college football team news articles from ESPN blog pages using Playwright.
Extracts article titles, dates, content summaries, and categories for team strength
analysis.

Usage:
    client = ESPNNCAAFNewsClient()

    # Get news for one team
    news = await client.get_team_news("alabama")

    # Get news for multiple teams
    news = await client.get_all_ncaaf_news()

Categories:
    - Injury News: Player injuries and health updates
    - Recruiting: Recruiting commitments and transfers
    - Coaching: Coaching hires, fires, and changes
    - Game Analysis: Game recaps and analysis
    - Transfer Portal: Portal entries and exits
    - Player Spotlight: Player profile and feature content
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


# NCAAF teams for news scraping
NCAAF_TEAMS = {
    "alabama": {"slug": "alabama-crimson-tide", "full_name": "Alabama Crimson Tide"},
    "lsu": {"slug": "lsu-tigers", "full_name": "LSU Tigers"},
    "ohiostate": {
        "slug": "ohio-state-buckeyes",
        "full_name": "Ohio State Buckeyes",
    },
    "clemson": {"slug": "clemson-tigers", "full_name": "Clemson Tigers"},
    "georgia": {"slug": "georgia-bulldogs", "full_name": "Georgia Bulldogs"},
    "texas": {"slug": "texas-longhorns", "full_name": "Texas Longhorns"},
    "oklahoma": {"slug": "oklahoma-sooners", "full_name": "Oklahoma Sooners"},
    "usc": {"slug": "usc-trojans", "full_name": "USC Trojans"},
    "florida": {"slug": "florida-gators", "full_name": "Florida Gators"},
    "texas-am": {"slug": "texas-am-aggies", "full_name": "Texas A&M Aggies"},
}


class ESPNNCAAFNewsClient:
    """
    ESPN NCAAF News Scraper Client.

    Fetches college football team news articles from ESPN using Playwright
    for JavaScript rendering.
    """

    BASE_URL = "https://www.espn.com/college-football/team/news"

    def __init__(self, headless: bool = True, max_articles: int = 10):
        """
        Initialize ESPN NCAAF News client.

        Args:
            headless: Run browser in headless mode
            max_articles: Maximum articles to fetch per team
        """
        self.headless = headless
        self.max_articles = max_articles
        self._browser = None
        self._page = None

    async def connect(self) -> None:
        """Initialize Playwright browser."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def get_team_news(self, team_abbr: str, limit: Optional[int] = None) -> dict:
        """
        Get news articles for a specific NCAAF team.

        Args:
            team_abbr: Team abbreviation (e.g., 'alabama')
            limit: Maximum articles (uses instance default if not specified)

        Returns:
            Dictionary with team info and articles
        """
        if team_abbr.lower() not in NCAAF_TEAMS:
            raise ValueError(f"Unknown team abbreviation: {team_abbr}")

        team_info = NCAAF_TEAMS[team_abbr.lower()]
        max_articles = limit or self.max_articles

        url = f"{self.BASE_URL}/_/slug/{team_info['slug']}"

        logger.info(f"Fetching news for {team_info['full_name']}")

        articles = await self._fetch_team_news_page(url, max_articles)

        return {
            "team_abbr": team_abbr.lower(),
            "team_name": team_info["full_name"],
            "articles": articles,
            "article_count": len(articles),
            "fetched_at": datetime.now().isoformat(),
        }

    async def _fetch_team_news_page(self, url: str, limit: int) -> list[dict]:
        """
        Fetch and parse team news page.

        Args:
            url: Team news page URL
            limit: Maximum articles to extract

        Returns:
            List of article dictionaries
        """
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await self._page.wait_for_timeout(2000)  # Wait for JavaScript rendering

            articles = await self._extract_article_links()

            # Extract content from article pages (limit to first N)
            result = []
            for article_url in articles[:limit]:
                try:
                    article_data = await self._fetch_article_content(article_url)
                    if article_data:
                        result.append(article_data)
                except Exception as e:
                    logger.warning(f"Failed to fetch article {article_url}: {e}")
                    continue

            logger.info(f"Extracted {len(result)} articles")
            return result

        except Exception as e:
            logger.error(f"Error fetching team news page: {e}")
            return []

    async def _extract_article_links(self) -> list[str]:
        """
        Extract article URLs from news page.

        Returns:
            List of article URLs
        """
        try:
            # Find all links that look like article links
            article_links = await self._page.eval_on_selector_all(
                "a[href*='/college-football/story/'],"
                "a[href*='/college-football/article/'],"
                "a[href*='/college-football/blog/']",
                "elements => elements.map(e => e.href)",
            )

            # Remove duplicates and limit
            unique_links = list(set(article_links))[: self.max_articles]
            logger.debug(f"Found {len(unique_links)} article links")
            return unique_links

        except Exception as e:
            logger.warning(f"Error extracting article links: {e}")
            return []

    async def _fetch_article_content(self, url: str) -> Optional[dict]:
        """
        Fetch article content from URL.

        Args:
            url: Article URL

        Returns:
            Article dictionary or None
        """
        try:
            # Navigate to article
            await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await self._page.wait_for_timeout(1000)

            # Extract article data
            article_data = await self._page.evaluate(
                """() => {
                const title = document.querySelector('h1')?.innerText;
                const author = document.querySelector('[data-testid="byline-author"]')?.innerText ||
                              document.querySelector('.author')?.innerText;
                const date = document.querySelector('[data-testid="publish-date"]')?.innerText ||
                            document.querySelector('.publish-date')?.innerText;
                const summary = document.querySelector('article p')?.innerText ||
                               document.querySelector('.article-summary')?.innerText;
                const content = document.querySelector('article')?.innerText ||
                               document.querySelector('.article-body')?.innerText;

                return {title, author, date, summary, content};
            }"""
            )

            if not article_data.get("title"):
                return None

            # Categorize article
            category = self._categorize_article(article_data.get("content", ""))

            return {
                "title": article_data.get("title", ""),
                "author": article_data.get("author"),
                "date": article_data.get("date"),
                "summary": article_data.get("summary"),
                "content": article_data.get("content"),
                "category": category,
                "url": url,
            }

        except Exception as e:
            logger.warning(f"Error fetching article content from {url}: {e}")
            return None

    @staticmethod
    def _categorize_article(content: str) -> str:
        """
        Categorize article based on content.

        Args:
            content: Article content text

        Returns:
            Category name
        """
        content_lower = content.lower()

        categories = {
            "Injury News": [
                "injur",
                "rehab",
                "recover",
                "knee",
                "shoulder",
                "ankle",
            ],
            "Recruiting": [
                "recruit",
                "commit",
                "transfer",
                "portal",
                "sign",
                "class of",
            ],
            "Coaching": [
                "coach",
                "hire",
                "fire",
                "offensive coordinator",
                "defensive coordinator",
            ],
            "Game Analysis": [
                "game",
                "win",
                "loss",
                "performance",
                "playoff",
                "bowl",
            ],
            "Transfer Portal": ["transfer", "portal", "enter portal", "exit portal"],
            "Player Spotlight": [
                "spotlight",
                "profile",
                "player",
                "athlete",
                "feature",
                "q&a",
            ],
        }

        for category, keywords in categories.items():
            if any(keyword in content_lower for keyword in keywords):
                return category

        return "Team News"

    async def get_all_ncaaf_news(self, limit: Optional[int] = None) -> dict:
        """
        Get news for all NCAAF teams.

        Args:
            limit: Maximum articles per team

        Returns:
            Dictionary with all teams' news
        """
        all_news = {}

        for team_abbr in sorted(NCAAF_TEAMS.keys()):
            try:
                result = await self.get_team_news(team_abbr, limit=limit)
                all_news[team_abbr] = result
            except Exception as e:
                logger.error(f"Error fetching news for {team_abbr}: {e}")
                all_news[team_abbr] = {
                    "error": str(e),
                    "articles": [],
                }

        return all_news

    async def save_news_json(
        self,
        news_data: dict,
        output_dir: Path,
    ) -> Path:
        """
        Save news data to JSON file.

        Args:
            news_data: News dictionary
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_ncaaf_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(news_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved news: {filepath}")
        return filepath
