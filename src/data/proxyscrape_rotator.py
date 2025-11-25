"""
ProxyScrape Residential Proxy Rotator

Integrates ProxyScrape residential rotating proxies with Playwright
for NFL.com scraping with bot detection evasion.

Configuration:
    PROXYSCRAPE_API_KEY: Your ProxyScrape API key
    PROXYSCRAPE_FORMAT: "textplain" (default) or "json"

Usage:
    rotator = ProxyScrapeRotator(api_key="your-key")
    proxy_url = await rotator.get_next_proxy()
    # Use proxy_url with Playwright
"""

import asyncio
import json
import logging
import random
from typing import Optional
from datetime import datetime, timedelta

import aiohttp

logger = logging.getLogger(__name__)


class ProxyScrapeRotator:
    """Manage rotating residential proxies from ProxyScrape."""

    API_ENDPOINT = "https://api.proxyscrape.com/v2/"

    def __init__(
        self,
        api_key: str,
        format_type: str = "textplain",
        cache_ttl: int = 3600,
    ):
        """
        Initialize ProxyScrape rotator.

        Args:
            api_key: ProxyScrape API key
            format_type: "textplain" or "json"
            cache_ttl: Cache duration in seconds (default 1 hour)
        """
        self.api_key = api_key
        self.format_type = format_type
        self.cache_ttl = cache_ttl
        self._session: Optional[aiohttp.ClientSession] = None
        self._proxy_list: list[str] = []
        self._cache_time: Optional[datetime] = None
        self._current_index = 0

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

    async def _fetch_proxies(self) -> list[str]:
        """
        Fetch proxy list from ProxyScrape API.

        Returns:
            List of proxy URLs in format http://ip:port
        """
        if not self._session:
            await self.connect()

        try:
            params = {
                "request": "getproxies",
                "protocol": "http",
                "timeout": "5000",
                "ssl": "all",
                "anonymity": "all",
                "country": "all",
                "sort": "lastchecked",
                "format": self.format_type,
                "api_key": self.api_key,
            }

            logger.info("Fetching proxies from ProxyScrape API...")

            async with self._session.get(
                self.API_ENDPOINT,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    logger.error(f"API error: {resp.status}")
                    return []

                content = await resp.text()

                if self.format_type == "textplain":
                    # Format: ip:port\nip:port\n...
                    proxies = [
                        f"http://{line.strip()}"
                        for line in content.split("\n")
                        if line.strip()
                    ]
                else:
                    # JSON format
                    data = json.loads(content)
                    proxies = [
                        f"http://{p['ip']}:{p['port']}" for p in data.get("proxies", [])
                    ]

                logger.info(f"Fetched {len(proxies)} proxies from ProxyScrape")
                return proxies

        except Exception as e:
            logger.error(f"Error fetching proxies: {e}")
            return []

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
