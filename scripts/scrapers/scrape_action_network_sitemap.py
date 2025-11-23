#!/usr/bin/env python3
"""
Action Network Sitemap Scraper - Execution Script

Collects NFL and NCAAF game URLs and content categories from Action Network
sitemaps using advanced DevTools techniques.

Usage:
    uv run python scripts/scrapers/scrape_action_network_sitemap.py

Output:
    output/action_network/nfl/games_*.jsonl
    output/action_network/ncaaf/games_*.jsonl
    output/action_network/nfl/{category}_*.jsonl
    output/action_network/ncaaf/{category}_*.jsonl
    output/action_network/scrape_summary_*.json
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.action_network_sitemap_scraper import ActionNetworkSitemapScraper


async def main():
    """Main entry point."""
    scraper = ActionNetworkSitemapScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
