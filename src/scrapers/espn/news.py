"""
ESPN News & Blog Client

Fetches NFL team news articles from ESPN blog pages using Playwright for
JavaScript rendering. Extracts article metadata, summaries, and key information
affecting team strength (injuries, trades, coaching changes).

Usage:
    client = ESPNNewsClient()
    await client.connect()

    # Get recent news for a team
    news = await client.get_team_news("buf", limit=10)

    # Get all NFL team news
    all_news = await client.get_all_nfl_news(limit=5)

    await client.close()

Article Categories (detected from content):
    - Injury News: Player injuries, rehabilitation
    - Trades & Transactions: Personnel changes
    - Coaching: Coach hires/fires, strategy changes
    - Roster Moves: Signings, releases, waivers
    - Game Analysis: Team performance, strategy
    - Player Spotlights: Individual player news
    - Team News: General team updates
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import Browser, Page, async_playwright

logger = logging.getLogger(__name__)


# NFL team ID and abbreviation mapping
NFL_TEAMS = {
    "atl": {"name": "atlanta-falcons", "full_name": "Atlanta Falcons"},
    "buf": {"name": "buffalo-bills", "full_name": "Buffalo Bills"},
    "chi": {"name": "chicago-bears", "full_name": "Chicago Bears"},
    "cin": {"name": "cincinnati-bengals", "full_name": "Cincinnati Bengals"},
    "cle": {"name": "cleveland-browns", "full_name": "Cleveland Browns"},
    "dal": {"name": "dallas-cowboys", "full_name": "Dallas Cowboys"},
    "den": {"name": "denver-broncos", "full_name": "Denver Broncos"},
    "det": {"name": "detroit-lions", "full_name": "Detroit Lions"},
    "gb": {"name": "green-bay-packers", "full_name": "Green Bay Packers"},
    "hou": {"name": "houston-texans", "full_name": "Houston Texans"},
    "ind": {"name": "indianapolis-colts", "full_name": "Indianapolis Colts"},
    "jax": {"name": "jacksonville-jaguars", "full_name": "Jacksonville Jaguars"},
    "kc": {"name": "kansas-city-chiefs", "full_name": "Kansas City Chiefs"},
    "lar": {"name": "los-angeles-rams", "full_name": "Los Angeles Rams"},
    "lac": {"name": "los-angeles-chargers", "full_name": "Los Angeles Chargers"},
    "lv": {"name": "las-vegas-raiders", "full_name": "Las Vegas Raiders"},
    "mia": {"name": "miami-dolphins", "full_name": "Miami Dolphins"},
    "min": {"name": "minnesota-vikings", "full_name": "Minnesota Vikings"},
    "ne": {"name": "new-england-patriots", "full_name": "New England Patriots"},
    "no": {"name": "new-orleans-saints", "full_name": "New Orleans Saints"},
    "nyg": {"name": "new-york-giants", "full_name": "New York Giants"},
    "nyj": {"name": "new-york-jets", "full_name": "New York Jets"},
    "phi": {"name": "philadelphia-eagles", "full_name": "Philadelphia Eagles"},
    "pit": {"name": "pittsburgh-steelers", "full_name": "Pittsburgh Steelers"},
    "sf": {"name": "san-francisco-49ers", "full_name": "San Francisco 49ers"},
    "sea": {"name": "seattle-seahawks", "full_name": "Seattle Seahawks"},
    "tb": {"name": "tampa-bay-buccaneers", "full_name": "Tampa Bay Buccaneers"},
    "ten": {"name": "tennessee-titans", "full_name": "Tennessee Titans"},
    "was": {"name": "washington-commanders", "full_name": "Washington Commanders"},
}


class ESPNNewsClient:
    """
    ESPN News & Blog API client.

    Fetches NFL team news articles from ESPN blog pages using Playwright
    for JavaScript rendering. Extracts article titles, summaries, publication
    dates, and content categories.
    """

    BASE_URL = "https://www.espn.com/blog"
    TIMEOUT = 20000  # 20 seconds for page load

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 20000,
        max_articles: int = 50,
    ):
        """
        Initialize ESPN News client.

        Args:
            headless: Run browser in headless mode (no UI)
            timeout: Page load timeout in milliseconds
            max_articles: Maximum articles to extract per team
        """
        self.headless = headless
        self.timeout = timeout
        self.max_articles = max_articles
        self.browser: Optional[Browser] = None

    async def connect(self) -> None:
        """Launch browser for Playwright."""
        if self.browser is None:
            playwright = async_playwright()
            self.pw = await playwright.start()
            self.browser = await self.pw.chromium.launch(headless=self.headless)
            logger.info("ESPN News Client browser launched")

    async def close(self) -> None:
        """Close browser."""
        if self.browser:
            await self.browser.close()
            await self.pw.stop()
            self.browser = None
            logger.info("ESPN News Client browser closed")

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def get_team_news(self, team_abbr: str, limit: int = 20) -> dict:
        """
        Get recent news articles for a specific NFL team.

        Args:
            team_abbr: Team abbreviation (e.g., 'buf' for Buffalo Bills)
            limit: Maximum number of articles to retrieve

        Returns:
            Dictionary with team info and articles list
        """
        team_abbr_lower = team_abbr.lower()

        if team_abbr_lower not in NFL_TEAMS:
            raise ValueError(f"Unknown team abbreviation: {team_abbr}")

        team_info = NFL_TEAMS[team_abbr_lower]
        url = f"{self.BASE_URL}/{team_info['name']}"

        logger.info(f"Fetching news for {team_info['full_name']}")

        articles = await self._fetch_articles(url, limit)

        return {
            "team_abbr": team_abbr_lower,
            "team_name": team_info["full_name"],
            "articles": articles,
            "article_count": len(articles),
            "fetched_at": datetime.now().isoformat(),
        }

    async def get_all_nfl_news(self, limit: int = 10) -> dict:
        """
        Get recent news for all 32 NFL teams.

        Args:
            limit: Maximum articles per team

        Returns:
            Dictionary with all teams' news
        """
        all_news = {}

        for team_abbr in sorted(NFL_TEAMS.keys()):
            try:
                result = await self.get_team_news(team_abbr, limit)
                all_news[team_abbr] = result
            except Exception as e:
                logger.error(f"Error fetching news for {team_abbr}: {e}")
                all_news[team_abbr] = {
                    "error": str(e),
                    "articles": [],
                }

        return all_news

    async def _fetch_articles(self, url: str, limit: int) -> list[dict]:
        """
        Fetch articles from team blog page.

        Args:
            url: Team blog page URL
            limit: Maximum articles to extract

        Returns:
            List of article dictionaries
        """
        if not self.browser:
            raise RuntimeError("Browser not connected. Call connect() first.")

        page = await self.browser.new_page()
        articles = []

        try:
            # Navigate to team blog page
            await page.goto(
                url,
                timeout=self.timeout,
                wait_until="domcontentloaded",
            )

            # Wait for JS to render content
            await page.wait_for_timeout(2000)

            # Extract article links
            article_links = await self._extract_article_links(page)

            logger.info(f"Found {len(article_links)} article links on {url}")

            # Process articles up to limit
            for i, (title, link) in enumerate(article_links[:limit], 1):
                try:
                    article = await self._fetch_article_content(page, link, title)
                    if article:
                        articles.append(article)
                    logger.debug(
                        f"  [{i}/{min(limit, len(article_links))}] "
                        f"Extracted: {title[:60]}"
                    )
                except Exception as e:
                    logger.warning(f"Error extracting article {link}: {e}")
                    continue

        finally:
            await page.close()

        return articles

    async def _extract_article_links(self, page: Page) -> list[tuple[str, str]]:
        """
        Extract article titles and links from blog page.

        Args:
            page: Playwright page object

        Returns:
            List of (title, url) tuples
        """
        article_links = []

        # Find all links that look like articles
        links = await page.query_selector_all("a[href*='espn.com']")

        for link in links:
            try:
                href = await link.get_attribute("href")
                text = await link.text_content()

                if not href or not text:
                    continue

                # Look for article URLs (contain /story/ or /article/)
                if any(x in href.lower() for x in ["/story/", "/article/", "/blog/"]):
                    # Clean up text (remove extra whitespace)
                    clean_text = " ".join(text.split())

                    # Skip duplicate links and short titles
                    if len(clean_text) > 10 and clean_text not in [
                        link[0] for link in article_links
                    ]:
                        article_links.append((clean_text, href))

                        # Stop after finding enough
                        if len(article_links) >= self.max_articles:
                            break

            except Exception as e:
                logger.debug(f"Error extracting link: {e}")
                continue

        return article_links

    async def _fetch_article_content(
        self, page: Page, url: str, title: str
    ) -> Optional[dict]:
        """
        Fetch full article content.

        Args:
            page: Current page (reuse to avoid multiple navigations)
            url: Article URL
            title: Article title (already extracted)

        Returns:
            Article dictionary or None if extraction fails
        """
        try:
            # Navigate to article (use same page to save resources)
            await page.goto(
                url,
                timeout=self.timeout,
                wait_until="domcontentloaded",
            )

            await page.wait_for_timeout(1000)

            # Extract article metadata
            author = await self._extract_author(page)
            publish_date = await self._extract_date(page)
            summary = await self._extract_summary(page)
            content = await self._extract_article_text(page)

            # Determine content category
            category = self._categorize_article(title, summary, content)

            return {
                "title": title,
                "url": url,
                "author": author,
                "published_date": publish_date,
                "summary": summary,
                "content": content,
                "category": category,
            }

        except Exception as e:
            logger.warning(f"Error fetching article content from {url}: {e}")
            return None

    async def _extract_author(self, page: Page) -> Optional[str]:
        """Extract article author."""
        try:
            author = await page.query_selector('[data-testid="author"]')
            if author:
                return await author.text_content()
        except:
            pass
        return None

    async def _extract_date(self, page: Page) -> Optional[str]:
        """Extract article publication date."""
        try:
            # Try common date patterns
            date_elem = await page.query_selector(
                "time, [class*='date'], [class*='Date']"
            )
            if date_elem:
                text = await date_elem.text_content()
                return text.strip()
        except:
            pass
        return None

    async def _extract_summary(self, page: Page) -> Optional[str]:
        """Extract article summary/excerpt."""
        try:
            # Look for summary paragraph
            summary = await page.query_selector(
                "[class*='summary'], [class*='Summary'], p:first-of-type"
            )
            if summary:
                text = await summary.text_content()
                return text.strip()
        except:
            pass
        return None

    async def _extract_article_text(self, page: Page) -> str:
        """Extract full article text content."""
        try:
            # Get article body
            article = await page.query_selector("article, [class*='Article']")
            if article:
                text = await article.text_content()
                return text.strip()
        except:
            pass

        # Fallback to page text
        text = await page.text_content()
        return text.strip()[:2000]  # First 2000 chars

    @staticmethod
    def _categorize_article(title: str, summary: Optional[str], content: str) -> str:
        """
        Categorize article based on content.

        Args:
            title: Article title
            summary: Article summary
            content: Article content

        Returns:
            Category name
        """
        text = f"{title} {summary or ''} {content}".lower()

        categories = {
            "Injury News": [
                "injur",
                "out",
                "rehab",
                "recover",
                "sideline",
                "knee",
                "shoulder",
                "hamstring",
                "torn",
            ],
            "Trades & Transactions": [
                "trade",
                "traded",
                "acquisition",
                "acquire",
                "deal",
                "agreement",
                "contract",
            ],
            "Coaching": [
                "coach",
                "hire",
                "hired",
                "fire",
                "fired",
                "offensive",
                "defensive",
                "strategy",
            ],
            "Roster Moves": [
                "sign",
                "signed",
                "release",
                "released",
                "waive",
                "waived",
                "practice squad",
            ],
            "Game Analysis": [
                "game",
                "win",
                "loss",
                "performance",
                "dominant",
                "defeat",
                "playoff",
            ],
            "Player Spotlight": [
                "spotlight",
                "profile",
                "player",
                "career",
                "achievement",
                "record",
            ],
        }

        # Score each category
        scores = {}
        for category, keywords in categories.items():
            score = sum(text.count(kw) for kw in keywords)
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores, key=scores.get)
        return "Team News"

    async def save_news_json(self, news_data: dict, output_dir: Path) -> Path:
        """
        Save raw news data to JSON file.

        Args:
            news_data: News dictionary
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_nfl_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(news_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved news: {filepath}")
        return filepath
