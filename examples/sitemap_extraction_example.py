#!/usr/bin/env python3
"""
Simple example showing how to extract URLs from gzipped sitemaps.

Key Concepts:
1. Sitemap Index XML → List of .gz sitemap URLs
2. Download .gz file → gzip.decompress() → XML content
3. Parse XML → Extract <url><loc> elements
"""

import gzip

import httpx
from lxml import etree


def extract_sitemap_urls(sitemap_index_url: str) -> list[str]:
    """
    Extract all URLs from a sitemap index with gzipped sitemaps.

    Args:
        sitemap_index_url: URL to sitemap_index.xml

    Returns:
        List of all page URLs found in the sitemaps
    """
    all_urls = []

    # HTTP client with user agent to avoid 403 errors
    client = httpx.Client(
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
        follow_redirects=True,
    )

    # XML namespace for sitemaps
    NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Step 1: Fetch sitemap index
    print(f"Fetching sitemap index: {sitemap_index_url}")
    response = client.get(sitemap_index_url)
    response.raise_for_status()

    # Step 2: Parse index to get .gz sitemap URLs
    root = etree.fromstring(response.content)
    sitemap_urls = root.xpath("//sm:sitemap/sm:loc/text()", namespaces=NS)
    print(f"Found {len(sitemap_urls)} sitemaps\n")

    # Step 3: Process each .gz sitemap
    for i, sitemap_url in enumerate(sitemap_urls, 1):
        print(f"[{i}/{len(sitemap_urls)}] {sitemap_url}")

        # Download .gz file
        response = client.get(sitemap_url)
        response.raise_for_status()

        # Decompress if gzipped
        if sitemap_url.endswith(".gz"):
            xml_content = gzip.decompress(response.content)
        else:
            xml_content = response.content

        # Parse XML and extract URLs
        sitemap_root = etree.fromstring(xml_content)
        urls = sitemap_root.xpath("//sm:url/sm:loc/text()", namespaces=NS)

        print(f"  → Extracted {len(urls)} URLs")
        all_urls.extend(urls)

    client.close()
    return all_urls


if __name__ == "__main__":
    # Example usage
    sitemap_url = "https://www.footballdb.com/sitemap_index.xml"

    try:
        urls = extract_sitemap_urls(sitemap_url)
        print(f"\n✅ Total URLs extracted: {len(urls):,}")

        # Show first 5
        print("\nFirst 5 URLs:")
        for url in urls[:5]:
            print(f"  {url}")

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error {e.response.status_code}: {e.response.reason_phrase}")
        print(
            "Tip: footballdb.com may block automated requests. "
            "Try using a proxy or rotating user agents."
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
