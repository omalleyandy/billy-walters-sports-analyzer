"""
NFL.com Game Stats Scraper with ProxyScrape Residential Proxies

Enhanced version of NFLGameStatsClient that uses rotating residential
proxies to bypass bot detection and rate limiting.

Usage:
    from src.data.nfl_game_stats_client_with_proxies import (
        NFLGameStatsClientWithProxies,
    )
    import os

    username = os.getenv("PROXYSCRAPE_USERNAME")
    password = os.getenv("PROXYSCRAPE_PASSWORD")
    client = NFLGameStatsClientWithProxies(
        proxyscrape_username=username,
        proxyscrape_password=password,
        use_proxies=True,
    )

    try:
        await client.connect()
        stats = await client.get_week_stats(year=2025, week="reg-12")
    finally:
        await client.close()
"""

import asyncio
import logging
import os
from typing import Optional

from playwright.async_api import async_playwright

from .nfl_game_stats_client import NFLGameStatsClient
from .proxyscrape_rotator import ProxyScrapeRotator

logger = logging.getLogger(__name__)


class NFLGameStatsClientWithProxies(NFLGameStatsClient):
    """
    NFL.com Game Stats Scraper with ProxyScrape residential proxy support.

    Extends base NFLGameStatsClient with:
    - Rotating residential proxies
    - Intelligent proxy selection
    - Proxy health monitoring
    - Fallback to direct connection if proxies fail
    """

    def __init__(
        self,
        headless: bool = True,
        proxyscrape_username: Optional[str] = None,
        proxyscrape_password: Optional[str] = None,
        use_proxies: bool = True,
        proxy_rotation_strategy: str = "rotate",  # "rotate" or "random"
    ):
        """
        Initialize NFL scraper with ProxyScrape residential proxy support.

        Uses direct gateway credentials (rp.scrapegw.com:6060) which
        automatically manages 20 rotating residential proxies.

        Args:
            headless: Run browser in headless mode
            proxyscrape_username: ProxyScrape username (PROXYSCRAPE_USERNAME
                env var)
            proxyscrape_password: ProxyScrape password (PROXYSCRAPE_PASSWORD
                env var)
            use_proxies: Enable proxy rotation
            proxy_rotation_strategy: "rotate" (sequential) or "random"
        """
        super().__init__(headless=headless)

        self.use_proxies = use_proxies
        self.proxy_strategy = proxy_rotation_strategy

        # Try to get credentials from parameters or environment
        if not proxyscrape_username:
            proxyscrape_username = os.getenv("PROXYSCRAPE_USERNAME")
        if not proxyscrape_password:
            proxyscrape_password = os.getenv("PROXYSCRAPE_PASSWORD")

        # Initialize proxy rotator with credentials
        if use_proxies:
            try:
                if proxyscrape_username and proxyscrape_password:
                    self.proxy_rotator = ProxyScrapeRotator(
                        username=proxyscrape_username,
                        password=proxyscrape_password,
                    )
                    logger.info("Proxy rotator initialized (20 rotating proxies)")
                else:
                    self.proxy_rotator = None
                    logger.warning(
                        "Proxy support enabled but no credentials found. "
                        "Set PROXYSCRAPE_USERNAME + PROXYSCRAPE_PASSWORD "
                        "environment variables. Falling back to direct "
                        "connection."
                    )
            except Exception as e:
                logger.error(f"Error initializing proxy rotator: {e}")
                self.proxy_rotator = None
        else:
            self.proxy_rotator = None

    async def connect(self) -> None:
        """Initialize browser and proxy rotator."""
        try:
            # Initialize proxy rotator if enabled
            if self.proxy_rotator:
                await self.proxy_rotator.connect()
                logger.info("Proxy rotator initialized")

            # Initialize browser
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )

            # Create page with proxy if available
            page_context = {
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "viewport": {"width": 1920, "height": 1080},
            }

            # Add proxy to context if available
            if self.proxy_rotator:
                proxy = await self._get_proxy()
                if proxy:
                    # Playwright requires separate username/password fields
                    # for HTTP proxy auth
                    page_context["proxy"] = {
                        "server": proxy,
                        "username": self.proxy_rotator.username,
                        "password": self.proxy_rotator.password,
                    }
                    logger.info(f"Using proxy: {proxy}")

            self._page = await self._browser.new_page(**page_context)

            logger.info("NFL Game Stats client connected with proxy support")

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    async def close(self) -> None:
        """Close browser and proxy rotator."""
        try:
            if self._page:
                await self._page.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            if self.proxy_rotator:
                await self.proxy_rotator.close()

            logger.info("NFL Game Stats client closed")

        except Exception as e:
            logger.error(f"Error closing client: {e}")

    async def _get_proxy(self) -> Optional[str]:
        """
        Get proxy based on configured strategy.

        Returns:
            Proxy URL or None
        """
        if not self.proxy_rotator:
            return None

        try:
            if self.proxy_strategy == "random":
                return await self.proxy_rotator.get_random_proxy()
            else:
                return await self.proxy_rotator.get_next_proxy()

        except Exception as e:
            logger.error(f"Error getting proxy: {e}")
            return None

    async def get_week_stats(
        self,
        year: int = 2025,
        week: str = "reg-12",
        max_retries: int = 3,
    ) -> dict:
        """
        Get all game stats for a week with proxy rotation.

        Automatically retries with new proxy if request fails.

        Args:
            year: NFL season year
            week: Week identifier
            max_retries: Maximum retry attempts per game

        Returns:
            Dictionary with all games and stats for the week
        """
        if not self._page:
            await self.connect()

        schedule_url = f"{self.BASE_URL}/schedules/{year}/by-week/{week}"
        logger.info(f"Fetching schedule from {schedule_url}")

        # Try to navigate with retries
        for attempt in range(max_retries):
            try:
                await self._page.goto(
                    schedule_url,
                    wait_until="networkidle",
                    timeout=120000,
                )
                await asyncio.sleep(2)
                break

            except Exception as e:
                logger.warning(
                    f"Schedule fetch attempt {attempt + 1}/{max_retries} failed: {e}"
                )

                if attempt < max_retries - 1:
                    # Get new proxy for retry
                    if self.proxy_rotator:
                        new_proxy = await self._get_proxy()
                        if new_proxy:
                            logger.info("Retrying with new proxy...")
                            # Proxy change requires new page/context
                            await self._page.close()
                            user_agent = (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/120.0.0.0 Safari/537.36"
                            )
                            self._page = await self._browser.new_page(
                                user_agent=user_agent,
                                viewport={"width": 1920, "height": 1080},
                                proxy={
                                    "server": new_proxy,
                                    "username": self.proxy_rotator.username,
                                    "password": self.proxy_rotator.password,
                                },
                            )

                    await asyncio.sleep(5)
                else:
                    raise

        # Extract game links
        game_links = await self._extract_game_links()
        logger.info(f"Found {len(game_links)} games in week {week}")

        # Fetch stats for each game
        week_stats = {
            "year": year,
            "week": week,
            "games": [],
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "proxy_info": {
                "enabled": self.use_proxies,
                "strategy": self.proxy_strategy,
            },
        }

        for idx, game_url in enumerate(game_links, 1):
            try:
                logger.info(f"Fetching stats for game {idx}/{len(game_links)}")

                # Try game stats with retries and proxy rotation
                game_stats = None
                for attempt in range(max_retries):
                    try:
                        game_stats = await self.get_game_stats(game_url)
                        if game_stats:
                            break

                    except Exception as e:
                        logger.warning(
                            f"Game fetch attempt {attempt + 1}/{max_retries} "
                            f"failed: {e}"
                        )

                        if attempt < max_retries - 1 and self.proxy_rotator:
                            # Rotate to new proxy
                            new_proxy = await self._get_proxy()
                            if new_proxy:
                                logger.info("Retrying game with new proxy...")
                                await self._page.close()
                                user_agent = (
                                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/120.0.0.0 Safari/537.36"
                                )
                                self._page = await self._browser.new_page(
                                    user_agent=user_agent,
                                    viewport={"width": 1920, "height": 1080},
                                    proxy={
                                        "server": new_proxy,
                                        "username": self.proxy_rotator.username,
                                        "password": self.proxy_rotator.password,
                                    },
                                )
                            await asyncio.sleep(5)

                if game_stats:
                    week_stats["games"].append(game_stats)

                # Rate limiting between games
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error fetching stats for {game_url}: {e}")

        return week_stats

    async def get_proxy_health(self) -> dict:
        """
        Get health report of proxy system.

        Returns:
            Dictionary with health metrics
        """
        if not self.proxy_rotator:
            return {"enabled": False}

        return await self.proxy_rotator.get_health_report()

    async def test_proxies(self, limit: int = 5) -> dict:
        """
        Test proxies to find working ones.

        Args:
            limit: Maximum proxies to test

        Returns:
            Dictionary with test results
        """
        if not self.proxy_rotator:
            logger.warning("Proxy rotator not available")
            return {}

        await self.proxy_rotator.connect()

        try:
            # Fetch proxies
            proxies = await self.proxy_rotator._fetch_proxies()

            if not proxies:
                logger.warning("No proxies available")
                return {}

            # Test limited number
            proxies_to_test = proxies[:limit]
            logger.info(f"Testing {len(proxies_to_test)} proxies...")

            results = {}
            for proxy in proxies_to_test:
                working = await self.proxy_rotator.test_proxy(proxy)
                results[proxy] = working
                await asyncio.sleep(1)

            return results

        finally:
            await self.proxy_rotator.close()
