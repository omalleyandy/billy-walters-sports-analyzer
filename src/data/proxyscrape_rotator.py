"""
ProxyScrape Residential Proxy Rotator

Integrates ProxyScrape residential rotating proxies with Playwright
for NFL.com scraping with bot detection evasion.

Uses direct gateway credentials (rp.scrapegw.com:6060) which automatically
manages 20 rotating residential proxies. No API key needed.

Configuration:
    PROXYSCRAPE_USERNAME: Your username (e.g., "5iwdzupyp3mzyv6-country-us")
    PROXYSCRAPE_PASSWORD: Your password (e.g., "29eplg6c8ctwjrs")

Usage:
    rotator = ProxyScrapeRotator(
        username="your-username",
        password="your-password"
    )

    proxy_url = await rotator.get_next_proxy()
    # Use proxy_url with Playwright
"""

import asyncio
import logging
import random
from typing import Optional
from datetime import datetime, timedelta

import aiohttp

logger = logging.getLogger(__name__)


class ProxyScrapeRotator:
    """Manage rotating residential proxies from ProxyScrape."""

    GATEWAY_HOST = "rp.scrapegw.com"
    GATEWAY_PORT = 6060

    def __init__(
        self,
        username: str,
        password: str,
        cache_ttl: int = 3600,
        num_rotating_proxies: int = 20,
    ):
        """
        Initialize ProxyScrape rotator with direct gateway credentials.

        Args:
            username: ProxyScrape username (e.g., "5iwdzupyp3mzyv6-country-us")
            password: ProxyScrape password (e.g., "29eplg6c8ctwjrs")
            cache_ttl: Cache duration in seconds (default 1 hour)
            num_rotating_proxies: Number of rotating proxies at gateway
                                 (default 20 - matches ProxyScrape default)
        """
        if not username or not password:
            raise ValueError("username and password are required")

        self.username = username
        self.password = password
        self.num_rotating_proxies = num_rotating_proxies
        self.cache_ttl = cache_ttl
        self._session: Optional[aiohttp.ClientSession] = None
        self._proxy_list: list[str] = []
        self._cache_time: Optional[datetime] = None
        self._current_index = 0

        logger.info("ProxyScrapeRotator initialized (direct gateway mode)")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP session."""
        self._session = aiohttp.ClientSession()
        logger.info("ProxyScrape rotator connected")

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            logger.info("ProxyScrape rotator closed")

    def _generate_direct_proxies(self) -> list[str]:
        """
        Generate proxy list using direct gateway credentials.

        For direct mode (rp.scrapegw.com:6060), the gateway automatically
        rotates through 20 residential proxies. We generate the same proxy
        URL multiple times to simulate rotation.

        Returns:
            List of proxy URLs with auth: http://user:pass@host:port
        """
        proxy_auth = f"{self.username}:{self.password}"
        proxy_url = f"http://{proxy_auth}@{self.GATEWAY_HOST}:{self.GATEWAY_PORT}"

        # Generate list with same proxy repeated (gateway handles rotation)
        proxies = [proxy_url] * self.num_rotating_proxies

        logger.info(
            f"Generated {len(proxies)} proxy references "
            f"(gateway manages {self.num_rotating_proxies} rotating IPs)"
        )
        return proxies

    async def _fetch_proxies(self) -> list[str]:
        """
        Generate proxy list from direct gateway credentials.

        Returns:
            List of proxy URLs in format http://user:pass@host:port
        """
        return self._generate_direct_proxies()

    async def get_next_proxy(self) -> Optional[str]:
        """
        Get next proxy in rotation.

        Implements smart caching with TTL and automatic refresh.

        Returns:
            Proxy URL in format "http://ip:port" or None if unavailable
        """
        # Check if cache is expired
        if not self._proxy_list or self._is_cache_expired():
            self._proxy_list = await self._fetch_proxies()
            self._cache_time = datetime.now()

            if not self._proxy_list:
                logger.warning("No proxies available")
                return None

        # Rotate to next proxy
        if self._current_index >= len(self._proxy_list):
            self._current_index = 0

        proxy = self._proxy_list[self._current_index]
        self._current_index += 1

        logger.info(f"Proxy rotation: {self._current_index}/{len(self._proxy_list)}")
        return proxy

    async def get_random_proxy(self) -> Optional[str]:
        """
        Get random proxy (instead of rotating).

        Returns:
            Proxy URL in format "http://ip:port" or None if unavailable
        """
        # Refresh if expired
        if not self._proxy_list or self._is_cache_expired():
            self._proxy_list = await self._fetch_proxies()
            self._cache_time = datetime.now()

        if not self._proxy_list:
            logger.warning("No proxies available")
            return None

        proxy = random.choice(self._proxy_list)
        logger.info(f"Selected random proxy: {proxy.split('@')[-1][:30]}...")
        return proxy

    async def test_proxy(self, proxy: str) -> bool:
        """
        Test if proxy is working.

        Args:
            proxy: Proxy URL to test

        Returns:
            True if proxy works, False otherwise
        """
        if not self._session:
            await self.connect()

        try:
            async with self._session.get(
                "https://httpbin.org/ip",
                proxy=proxy,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"Proxy test passed: {data.get('origin')}")
                    return True
                else:
                    logger.warning(f"Proxy test failed: {resp.status}")
                    return False

        except Exception as e:
            logger.warning(f"Proxy test error: {e}")
            return False

    def _is_cache_expired(self) -> bool:
        """Check if proxy cache has expired."""
        if not self._cache_time:
            return True

        age = datetime.now() - self._cache_time
        expired = age > timedelta(seconds=self.cache_ttl)

        if expired:
            logger.info("Proxy cache expired, will refresh")

        return expired

    async def test_all_proxies(self) -> dict[str, bool]:
        """
        Test all proxies in current list.

        Returns:
            Dictionary with proxy URL as key and test result as value
        """
        if not self._proxy_list:
            logger.warning("No proxies to test")
            return {}

        logger.info(f"Testing {len(self._proxy_list)} proxies...")
        results = {}

        for proxy in self._proxy_list:
            result = await self.test_proxy(proxy)
            results[proxy] = result
            await asyncio.sleep(1)  # Rate limit tests

        working = sum(1 for v in results.values() if v)
        logger.info(f"Results: {working}/{len(results)} proxies working")

        return results

    async def get_health_report(self) -> dict:
        """
        Get health report of proxy system.

        Returns:
            Dictionary with health metrics
        """
        return {
            "total_proxies": len(self._proxy_list),
            "current_index": self._current_index,
            "cache_age": (
                (datetime.now() - self._cache_time).total_seconds()
                if self._cache_time
                else None
            ),
            "cache_ttl": self.cache_ttl,
            "cache_expired": self._is_cache_expired(),
        }
