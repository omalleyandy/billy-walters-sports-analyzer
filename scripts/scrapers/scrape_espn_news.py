#!/usr/bin/env python3
"""
Scrape ESPN News Posts

Usage:
    # Scrape ESPN news posts
    uv run python scripts/scrapers/scrape_espn_news.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.espn_api_client import ESPNAPIClient


def scrape_news():
    """
    Scrape ESPN news posts

    Returns:
        Dictionary with scraping results
    """
    client = ESPNAPIClient()

    print("=" * 70)
    print(f"ESPN NEWS SCRAPER")
    print("=" * 70)

    print("\nFetching ESPN news posts...")

    try:
        news = client.get_espn_news_posts()

        # Save using new output structure (no league subdirectory for news)
        filepath = client.save_to_json(news, data_type="news")

        # Try to extract post count
        items = news.get("items", [])
        if items:
            print(f"  Posts found: {len(items)}")
            print(f"\n  Sample posts:")
            for item in items[:3]:
                title = item.get("title", "No title")
                date = item.get("pubDate", "No date")
                print(f"    {title} - {date}")

        result = {
            "success": True,
            "post_count": len(items) if items else 0,
            "filepath": filepath,
        }

    except Exception as e:
        print(f"  [ERROR] {e}")
        result = {"success": False, "error": str(e)}

    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)

    if result.get("success"):
        print(f"News: {result['post_count']} posts → {result['filepath']}")
    else:
        print(f"News: FAILED - {result.get('error')}")

    return result


def main():
    """Main entry point"""
    try:
        result = scrape_news()

        if result.get("success"):
            return 0
        else:
            return 1

    except KeyboardInterrupt:
        print("\n\n[INFO] Scraping interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n[ERROR] Scraping failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
