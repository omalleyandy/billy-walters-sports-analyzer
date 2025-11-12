"""
Proxy Manager - Smart proxy handling with automatic fallback

This module provides intelligent proxy management for the overtime scrapers:
- Tests proxy connectivity before use
- Automatically falls back to direct connection if proxy fails
- Caches proxy status to avoid repeated tests
- Provides clear logging of proxy status

Author: Billy Walters Sports Analyzer
"""

import os
from typing import Optional
from datetime import datetime, timedelta
import httpx
from dotenv import load_dotenv

load_dotenv()


class ProxyManager:
    """
    Manages proxy configuration with automatic fallback.

    Features:
    - Tests proxy before use
    - Caches test results for 5 minutes
    - Falls back to no-proxy if authentication fails
    - Clear status reporting
    """

    def __init__(self):
        self.proxy_url: Optional[str] = None
        self.last_test_time: Optional[datetime] = None
        self.last_test_result: bool = False
        self.cache_duration = timedelta(minutes=5)

        # Load from environment
        self._load_proxy_from_env()

    def _load_proxy_from_env(self) -> None:
        """Load proxy configuration from environment variables"""
        # Check multiple env vars (prioritize OVERTIME_PROXY)
        self.proxy_url = os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")

    def test_proxy(self, force: bool = False) -> bool:
        """
        Test if proxy is working.

        Args:
            force: Force re-test even if cached result exists

        Returns:
            True if proxy works, False otherwise
        """
        # Return cached result if recent
        if not force and self.last_test_time:
            age = datetime.now() - self.last_test_time
            if age < self.cache_duration:
                return self.last_test_result

        # No proxy configured
        if not self.proxy_url:
            self.last_test_result = False
            self.last_test_time = datetime.now()
            return False

        # Test proxy
        print(f"Testing proxy: {self.proxy_url[:40]}...")

        try:
            response = httpx.get(
                "https://ipinfo.io/json", proxy=self.proxy_url, timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Proxy working!")
                print(f"  IP: {data.get('ip')}")
                print(f"  Location: {data.get('city')}, {data.get('country')}")

                self.last_test_result = True
                self.last_test_time = datetime.now()
                return True

            elif response.status_code == 407:
                print("[ERROR] Proxy authentication failed (407)")
                print("  Credentials invalid or expired")
                self.last_test_result = False
                self.last_test_time = datetime.now()
                return False

            else:
                print(f"[ERROR] Proxy returned status: {response.status_code}")
                self.last_test_result = False
                self.last_test_time = datetime.now()
                return False

        except httpx.ProxyError as e:
            print(f"[ERROR] Proxy error: {e}")
            self.last_test_result = False
            self.last_test_time = datetime.now()
            return False

        except Exception as e:
            print(f"[ERROR] Unexpected error testing proxy: {e}")
            self.last_test_result = False
            self.last_test_time = datetime.now()
            return False

    def get_proxy(self, test_first: bool = True) -> Optional[str]:
        """
        Get proxy URL if working, None otherwise.

        Args:
            test_first: Test proxy before returning

        Returns:
            Proxy URL if working, None to use direct connection
        """
        if not self.proxy_url:
            return None

        if test_first:
            if self.test_proxy():
                return self.proxy_url
            else:
                print("[WARNING] Proxy failed - using direct connection")
                return None

        return self.proxy_url

    def get_playwright_proxy_config(self, test_first: bool = True) -> Optional[dict]:
        """
        Get Playwright proxy configuration.

        Args:
            test_first: Test proxy before returning config

        Returns:
            Dict with proxy config for Playwright, or None for direct connection
        """
        proxy_url = self.get_proxy(test_first=test_first)

        if proxy_url:
            return {"server": proxy_url}

        return None

    def disable_proxy_env_vars(self) -> None:
        """Temporarily disable proxy environment variables"""
        os.environ["PROXY_URL"] = ""
        os.environ["OVERTIME_PROXY"] = ""
        self.proxy_url = None
        print("[INFO] Proxy disabled for this session")


# Global instance
_proxy_manager = ProxyManager()


def get_proxy_manager() -> ProxyManager:
    """Get the global proxy manager instance"""
    return _proxy_manager


if __name__ == "__main__":
    # Test the proxy manager
    pm = ProxyManager()

    print("=" * 70)
    print("Proxy Manager Test")
    print("=" * 70)
    print()

    proxy = pm.get_proxy(test_first=True)

    if proxy:
        print()
        print(f"[OK] Proxy ready: {proxy[:40]}...")
    else:
        print()
        print("[INFO] No proxy available - will use direct connection")

    print()
    print("=" * 70)
