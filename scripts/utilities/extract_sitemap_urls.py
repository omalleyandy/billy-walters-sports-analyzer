#!/usr/bin/env python3
"""
Extract all URLs from a sitemap index containing gzipped sitemap files.

Usage:
    uv run python scripts/utilities/extract_sitemap_urls.py

This script:
1. Fetches the sitemap index XML
2. Extracts all .gz sitemap URLs
3. Downloads and decompresses each .gz file
4. Parses the XML to extract all page URLs
5. Saves to output/sitemap_urls.txt
"""

import gzip
import os
import sys
import time
from pathlib import Path
from typing import List, Set

import httpx
from dotenv import load_dotenv
from lxml import etree

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class SitemapExtractor:
    """Extract URLs from sitemap index with gzipped sitemaps."""

    def __init__(
        self, sitemap_index_url: str, timeout: int = 60, use_proxy: bool = True
    ):
        """
        Initialize the sitemap extractor.

        Args:
            sitemap_index_url: URL to the sitemap index XML
            timeout: Request timeout in seconds
            use_proxy: Whether to use proxy from environment
        """
        self.sitemap_index_url = sitemap_index_url
        self.timeout = timeout

        # Build client configuration
        client_kwargs = {
            "timeout": timeout,
            "headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            },
            "follow_redirects": True,
        }

        # Add proxy if configured
        if use_proxy:
            proxy_url = os.getenv("PROXY_URL")
            if proxy_url:
                print(f"[OK] Using proxy: {proxy_url.split('@')[-1]}")
                client_kwargs["proxies"] = proxy_url
            else:
                print("[WARNING] Proxy enabled but PROXY_URL not set in .env")

        self.session = httpx.Client(**client_kwargs)

        # Verify proxy if enabled
        if use_proxy and os.getenv("PROXY_URL"):
            self._verify_proxy()

    def _verify_proxy(self) -> None:
        """Verify proxy is working by checking IP."""
        try:
            print("Verifying proxy connection...")
            response = self.session.get("https://ipinfo.io/json", timeout=10)
            if response.status_code == 200:
                ip_info = response.json()
                ip = ip_info.get("ip", "unknown")
                city = ip_info.get("city", "unknown")
                region = ip_info.get("region", "unknown")
                country = ip_info.get("country", "unknown")
                print(f"[OK] Proxy verified: {ip} ({city}, {region}, {country})")
            else:
                print(f"[WARNING] Proxy check failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"[WARNING] Could not verify proxy: {e}")

    def fetch_url(self, url: str, max_retries: int = 5) -> bytes:
        """
        Fetch URL content as bytes with retry logic.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Response content as bytes

        Raises:
            httpx.HTTPStatusError: If all retries fail
        """
        print(f"Fetching: {url}")

        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.get(url)
                response.raise_for_status()
                return response.content

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code

                # Retry on specific error codes
                if status_code in (403, 407, 429, 500, 502, 503, 504):
                    if attempt < max_retries:
                        # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                        delay = 2**attempt
                        print(
                            f"  [{attempt}/{max_retries}] "
                            f"HTTP {status_code} - Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        print(f"  [ERROR] Failed after {max_retries} retries")
                        raise

                # Don't retry on other status codes
                raise

            except Exception as e:
                if attempt < max_retries:
                    delay = 2**attempt
                    print(
                        f"  [{attempt}/{max_retries}] "
                        f"Error: {e} - Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise

        raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts")

    def parse_sitemap_index(self, xml_content: bytes) -> List[str]:
        """
        Parse sitemap index to extract sitemap URLs.

        Args:
            xml_content: XML content as bytes

        Returns:
            List of sitemap URLs (may include .gz files)
        """
        root = etree.fromstring(xml_content)

        # Handle XML namespaces
        namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Extract all <loc> elements from <sitemap> entries
        sitemap_urls = root.xpath("//sm:sitemap/sm:loc/text()", namespaces=namespaces)

        print(f"Found {len(sitemap_urls)} sitemaps in index")
        return sitemap_urls

    def decompress_gzip(self, gzip_content: bytes) -> bytes:
        """
        Decompress gzipped content.

        Args:
            gzip_content: Gzipped bytes

        Returns:
            Decompressed bytes
        """
        return gzip.decompress(gzip_content)

    def parse_sitemap(self, xml_content: bytes) -> List[str]:
        """
        Parse sitemap XML to extract page URLs.

        Args:
            xml_content: XML content as bytes

        Returns:
            List of page URLs
        """
        root = etree.fromstring(xml_content)

        namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Extract all <loc> elements from <url> entries
        urls = root.xpath("//sm:url/sm:loc/text()", namespaces=namespaces)

        return urls

    def extract_all_urls(self) -> Set[str]:
        """
        Extract all URLs from sitemap index and child sitemaps.

        Returns:
            Set of unique page URLs
        """
        all_urls: Set[str] = set()

        # Step 1: Fetch and parse sitemap index
        index_content = self.fetch_url(self.sitemap_index_url)
        sitemap_urls = self.parse_sitemap_index(index_content)

        # Step 2: Process each sitemap
        for i, sitemap_url in enumerate(sitemap_urls, 1):
            print(f"\n[{i}/{len(sitemap_urls)}] Processing: {sitemap_url}")

            try:
                # Respectful delay between requests (not for first request)
                if i > 1:
                    time.sleep(1)

                # Fetch sitemap (gzipped or plain XML)
                sitemap_content = self.fetch_url(sitemap_url)

                # Decompress if .gz file
                if sitemap_url.endswith(".gz"):
                    print("  Decompressing gzip...")
                    sitemap_content = self.decompress_gzip(sitemap_content)

                # Parse XML and extract URLs
                urls = self.parse_sitemap(sitemap_content)
                print(f"  Extracted {len(urls):,} URLs")

                all_urls.update(urls)

            except Exception as e:
                print(f"  ERROR: {e}")
                continue

        return all_urls

    def close(self) -> None:
        """Close HTTP session."""
        self.session.close()


def main() -> None:
    """Main execution."""
    # Configuration
    SITEMAP_INDEX_URL = "https://www.footballdb.com/sitemap_index.xml"
    OUTPUT_FILE = Path("output/sitemap_urls.txt")

    print("=" * 70)
    print("FootballDB.com Sitemap URL Extractor")
    print("=" * 70)
    print(f"\nSitemap Index: {SITEMAP_INDEX_URL}")
    print(f"Output File: {OUTPUT_FILE}")
    print()

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Extract URLs
    extractor = SitemapExtractor(SITEMAP_INDEX_URL)
    try:
        all_urls = extractor.extract_all_urls()

        # Save to file
        print(f"\n{'=' * 70}")
        print(f"Total unique URLs extracted: {len(all_urls):,}")
        print(f"Saving to: {OUTPUT_FILE}")

        with OUTPUT_FILE.open("w") as f:
            for url in sorted(all_urls):
                f.write(f"{url}\n")

        print(f"✅ Saved {len(all_urls):,} URLs to {OUTPUT_FILE}")

        # Show sample URLs
        print(f"\n{'=' * 70}")
        print("Sample URLs (first 10):")
        print("-" * 70)
        for url in sorted(all_urls)[:10]:
            print(f"  {url}")

        if len(all_urls) > 10:
            print(f"  ... ({len(all_urls) - 10:,} more)")

        # Categorize URLs by pattern
        print(f"\n{'=' * 70}")
        print("URL Categories:")
        print("-" * 70)

        categories = {}
        for url in all_urls:
            # Extract path pattern (e.g., /players/, /teams/, /games/)
            path = url.replace("https://www.footballdb.com", "")
            category = path.split("/")[1] if len(path.split("/")) > 1 else "root"
            categories[category] = categories.get(category, 0) + 1

        for category, count in sorted(
            categories.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  /{category}/: {count:,} URLs")

    finally:
        extractor.close()


if __name__ == "__main__":
    main()
