#!/usr/bin/env python3
"""
Action Network Sitemap Scraper

Reverse-engineers Action Network's sitemap structure to extract game URLs
using Chrome DevTools techniques. Crawls nested sitemap_index.xml, parses
content categories, and outputs structured data for NFL/NCAAF analysis.

Key Features:
- Async/await pattern for performance
- Regex pattern matching for URL extraction
- Intelligent category parsing
- JSONL output format
- Proxy support for stealth
"""

import os
import re
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Set
from pathlib import Path
from urllib.parse import urlparse

import httpx
import lxml.etree as etree
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class ActionNetworkSitemapScraper:
    """Scrapes Action Network sitemaps to extract game URLs and metadata."""

    def __init__(self, output_base: str = "output/action_network"):
        """
        Initialize scraper.

        Args:
            output_base: Base output directory
        """
        self.base_url = "https://www.actionnetwork.com"
        self.sitemap_index_url = f"{self.base_url}/sitemap.xml"
        self.sitemap_general_url = f"{self.base_url}/sitemap-general.xml"

        self.output_base = output_base
        self._ensure_output_dirs()

        # Regex patterns for URL extraction
        self.nfl_game_pattern = re.compile(r"/nfl-game/", re.IGNORECASE)
        self.ncaaf_game_pattern = re.compile(r"/ncaaf-game/", re.IGNORECASE)

        # Content categories to extract
        self.nfl_categories = {
            "futures": re.compile(r"/nfl/futures", re.IGNORECASE),
            "sports-betting-dfs-strategy-nfl-nba-information-news": (
                re.compile(r"/sports-betting.*nfl|/nfl.*strategy", re.IGNORECASE)
            ),
            "teasers-nfl-betting-tips-over-under-total": re.compile(
                (
                    r"/nfl.*teaser|/nfl.*tips|/nfl.*over-under|"
                    r"/nfl.*total"
                ),
                re.IGNORECASE,
            ),
            "odds": re.compile(r"/nfl/odds", re.IGNORECASE),
            "public-betting": re.compile(
                r"/nfl.*public|/nfl.*betting", re.IGNORECASE
            ),
        }

        self.ncaaf_categories = {
            "futures": re.compile(r"/ncaaf/futures", re.IGNORECASE),
            "odds": re.compile(r"/ncaaf/odds", re.IGNORECASE),
        }

        # HTTP client with stealth headers
        self.client = None
        self.proxy_url = os.getenv("PROXY_URL")
        self.proxy_auth = None

        if self.proxy_url:
            proxy_user = os.getenv("PROXY_USER")
            proxy_pass = os.getenv("PROXY_PASS")
            if proxy_user and proxy_pass:
                self.proxy_auth = (proxy_user, proxy_pass)

        # Track collected URLs
        self.nfl_games: Set[str] = set()
        self.ncaaf_games: Set[str] = set()
        self.nfl_category_pages: Dict[str, Set[str]] = {
            cat: set() for cat in self.nfl_categories
        }
        self.ncaaf_category_pages: Dict[str, Set[str]] = {
            cat: set() for cat in self.ncaaf_categories
        }

    def _ensure_output_dirs(self) -> None:
        """Create output directories."""
        dirs = [
            self.output_base,
            f"{self.output_base}/nfl",
            f"{self.output_base}/ncaaf",
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    async def _get_http_client(self) -> httpx.AsyncClient:
        """
        Get HTTP client with stealth headers.

        Returns:
            Configured AsyncClient
        """
        if self.client is None:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/xml, text/xml, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            proxies = None
            if self.proxy_url:
                proxies = self.proxy_url
                if self.proxy_auth:
                    user, password = self.proxy_auth
                    # httpx format: http://user:pass@host:port
                    proxies = self.proxy_url.replace(
                        "://", f"://{user}:{password}@", 1
                    )

            self.client = httpx.AsyncClient(
                headers=headers,
                timeout=30,
                proxies=proxies,
                verify=False,
            )

        return self.client

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

    async def fetch_xml(self, url: str) -> Optional[str]:
        """
        Fetch XML content with stealth headers.

        Args:
            url: URL to fetch

        Returns:
            XML content or None if failed
        """
        try:
            client = await self._get_http_client()
            logger.info(f"Fetching: {url}")
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            logger.info(f"[OK] Status {response.status_code}: {url}")
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error fetching {url}: {e}")
            return None

    def parse_sitemap_index(self, xml_content: str) -> List[str]:
        """
        Parse sitemap index XML to extract sitemap URLs.

        Args:
            xml_content: XML content string

        Returns:
            List of sitemap URLs
        """
        try:
            root = etree.fromstring(xml_content.encode("utf-8"))

            # Handle namespace
            ns_url = "http://www.sitemaps.org/schemas/sitemap/0.9"
            ns = {"sm": ns_url}
            sitemap_urls = [
                elem.text for elem in root.findall(".//sm:loc", ns)
                if elem.text
            ]

            logger.info(f"Found {len(sitemap_urls)} sitemaps in index")
            return sitemap_urls
        except etree.XMLSyntaxError as e:
            logger.error(f"Failed to parse XML: {e}")
            return []

    def parse_sitemap_urls(self, xml_content: str) -> List[str]:
        """
        Parse sitemap XML to extract URLs.

        Args:
            xml_content: XML content string

        Returns:
            List of URLs
        """
        try:
            root = etree.fromstring(xml_content.encode("utf-8"))

            # Handle namespace
            ns_url = "http://www.sitemaps.org/schemas/sitemap/0.9"
            ns = {"sm": ns_url}
            urls = [
                elem.text for elem in root.findall(".//sm:loc", ns)
                if elem.text
            ]

            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
        except etree.XMLSyntaxError as e:
            logger.error(f"Failed to parse XML: {e}")
            return []

    def categorize_nfl_url(self, url: str) -> Optional[str]:
        """
        Categorize NFL URL based on path patterns.

        Args:
            url: URL to categorize

        Returns:
            Category name or None
        """
        for category, pattern in self.nfl_categories.items():
            if pattern.search(url):
                return category
        return None

    def categorize_ncaaf_url(self, url: str) -> Optional[str]:
        """
        Categorize NCAAF URL based on path patterns.

        Args:
            url: URL to categorize

        Returns:
            Category name or None
        """
        for category, pattern in self.ncaaf_categories.items():
            if pattern.search(url):
                return category
        return None

    def process_urls(self, urls: List[str]) -> None:
        """
        Process URLs and categorize them.

        Args:
            urls: List of URLs to process
        """
        for url in urls:
            # Check for NFL games
            if self.nfl_game_pattern.search(url):
                self.nfl_games.add(url)
                logger.debug(f"[NFL GAME] {url}")
            # Check for NCAAF games
            elif self.ncaaf_game_pattern.search(url):
                self.ncaaf_games.add(url)
                logger.debug(f"[NCAAF GAME] {url}")

            # Categorize NFL pages
            nfl_category = self.categorize_nfl_url(url)
            if nfl_category:
                self.nfl_category_pages[nfl_category].add(url)
                logger.debug(f"[NFL {nfl_category.upper()}] {url}")

            # Categorize NCAAF pages
            ncaaf_category = self.categorize_ncaaf_url(url)
            if ncaaf_category:
                self.ncaaf_category_pages[ncaaf_category].add(url)
                logger.debug(f"[NCAAF {ncaaf_category.upper()}] {url}")

    async def scrape_sitemap_index(self) -> None:
        """Scrape the sitemap index and all nested sitemaps."""
        logger.info("=" * 70)
        logger.info("ACTION NETWORK SITEMAP SCRAPER")
        logger.info("=" * 70)

        # Fetch sitemap index
        xml_content = await self.fetch_xml(self.sitemap_index_url)
        if not xml_content:
            logger.error("Failed to fetch sitemap index")
            return

        # Parse sitemaps from index
        sitemap_urls = self.parse_sitemap_index(xml_content)

        if not sitemap_urls:
            logger.error("No sitemaps found in index")
            return

        # Fetch general sitemap (primary data source)
        logger.info("\n[PRIORITY] Fetching general sitemap...")
        general_xml = await self.fetch_xml(self.sitemap_general_url)
        if general_xml:
            urls = self.parse_sitemap_urls(general_xml)
            self.process_urls(urls)
        else:
            logger.warning("Failed to fetch general sitemap")

        # Fetch other sitemaps
        for sitemap_url in sitemap_urls:
            if sitemap_url == self.sitemap_general_url:
                continue  # Already processed

            logger.info(f"\n[NESTED] Fetching: {sitemap_url}")
            xml_content = await self.fetch_xml(sitemap_url)
            if xml_content:
                urls = self.parse_sitemap_urls(xml_content)
                self.process_urls(urls)
            else:
                logger.warning(f"Failed to fetch: {sitemap_url}")

            # Rate limit between requests
            await asyncio.sleep(0.5)

    def _build_jsonl_record(
        self, url: str, league: str, content_type: str, category: Optional[str]
    ) -> Dict:
        """
        Build JSONL record.

        Args:
            url: Page URL
            league: 'nfl' or 'ncaaf'
            content_type: 'game' or 'category'
            category: Content category (if applicable)

        Returns:
            JSONL record dict
        """
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")

        return {
            "url": url,
            "league": league,
            "content_type": content_type,
            "category": category,
            "path": parsed_url.path,
            "path_parts": path_parts,
            "slug": path_parts[-1] if path_parts else None,
            "scraped_at": datetime.now().isoformat(),
            "domain": parsed_url.netloc,
        }

    def save_results(self) -> None:
        """Save collected URLs to JSONL files."""
        logger.info("\n" + "=" * 70)
        logger.info("SAVING RESULTS")
        logger.info("=" * 70)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save NFL games
        if self.nfl_games:
            nfl_games_file = (
                f"{self.output_base}/nfl/games_{timestamp}.jsonl"
            )
            with open(nfl_games_file, "w") as f:
                for url in sorted(self.nfl_games):
                    record = self._build_jsonl_record(
                        url, "nfl", "game", None
                    )
                    f.write(json.dumps(record) + "\n")
            logger.info(
                f"[OK] Saved {len(self.nfl_games)} NFL games to "
                f"{nfl_games_file}"
            )

        # Save NCAAF games
        if self.ncaaf_games:
            ncaaf_games_file = (
                f"{self.output_base}/ncaaf/games_{timestamp}.jsonl"
            )
            with open(ncaaf_games_file, "w") as f:
                for url in sorted(self.ncaaf_games):
                    record = self._build_jsonl_record(
                        url, "ncaaf", "game", None
                    )
                    f.write(json.dumps(record) + "\n")
            logger.info(
                f"[OK] Saved {len(self.ncaaf_games)} NCAAF games to "
                f"{ncaaf_games_file}"
            )

        # Save NFL category pages
        for category, urls in self.nfl_category_pages.items():
            if urls:
                category_file = (
                    f"{self.output_base}/nfl/{category}_{timestamp}.jsonl"
                )
                with open(category_file, "w") as f:
                    for url in sorted(urls):
                        record = self._build_jsonl_record(
                            url, "nfl", "category", category
                        )
                        f.write(json.dumps(record) + "\n")
                logger.info(
                    f"[OK] Saved {len(urls)} NFL {category} to "
                    f"{category_file}"
                )

        # Save NCAAF category pages
        for category, urls in self.ncaaf_category_pages.items():
            if urls:
                category_file = (
                    f"{self.output_base}/ncaaf/"
                    f"{category}_{timestamp}.jsonl"
                )
                with open(category_file, "w") as f:
                    for url in sorted(urls):
                        record = self._build_jsonl_record(
                            url, "ncaaf", "category", category
                        )
                        f.write(json.dumps(record) + "\n")
                logger.info(
                    f"[OK] Saved {len(urls)} NCAAF {category} to "
                    f"{category_file}"
                )

        # Save summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "nfl_games": len(self.nfl_games),
            "ncaaf_games": len(self.ncaaf_games),
            "nfl_categories": {
                cat: len(urls) for cat, urls in self.nfl_category_pages.items()
            },
            "ncaaf_categories": {
                cat: len(urls) for cat, urls in self.ncaaf_category_pages.items()
            },
        }

        summary_file = f"{self.output_base}/scrape_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("\n[SUMMARY]")
        logger.info(f"  NFL Games: {summary['nfl_games']}")
        logger.info(f"  NCAAF Games: {summary['ncaaf_games']}")
        logger.info(f"  Summary saved to: {summary_file}")

    async def run(self) -> None:
        """Execute complete scraping workflow."""
        try:
            await self.scrape_sitemap_index()
            self.save_results()
            logger.info("\n[SUCCESS] Scraping complete!")
        except Exception as e:
            logger.error(f"[ERROR] Scraping failed: {e}", exc_info=True)
        finally:
            await self.close()


async def main():
    """Main entry point."""
    scraper = ActionNetworkSitemapScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
