"""
X (Twitter) News & Injury Scraper Script

Scrapes current NFL and NCAAF news and injury updates from official X sources.

Setup:
    1. Get X API v2 credentials from https://developer.twitter.com/
    2. Set environment variables:
       - X_API_KEY (your API key)
       - X_API_SECRET (your API secret)
       - X_ACCESS_TOKEN (your access token)
       - X_ACCESS_TOKEN_SECRET (your access token secret)

Usage:
    uv run python scripts/scrapers/scrape_x_news.py --league nfl --type injury
    uv run python scripts/scrapers/scrape_x_news.py --league ncaaf --type news
    uv run python scripts/scrapers/scrape_x_news.py --league nfl --team KC
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.data_integration.x_news_scraper import XNewsScraper


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape X for NFL/NCAAF news")
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="nfl",
        help="League to scrape",
    )
    parser.add_argument(
        "--type",
        choices=["injury", "news", "all"],
        default="all",
        help="Content type to scrape",
    )
    parser.add_argument(
        "--team",
        help="Specific team to scrape (e.g., KC, DAL, LSU)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days back to search",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export results to JSON",
    )

    args = parser.parse_args()

    # Initialize scraper
    scraper = XNewsScraper()

    print("\n" + "=" * 70)
    print("X NEWS SCRAPER - NFL & NCAAF")
    print("=" * 70)

    if not await scraper.initialize():
        print("\n[ERROR] X API not configured!")
        print("\nTo use this scraper, you need X API v2 credentials:")
        print("  1. Go to https://developer.twitter.com/")
        print("  2. Create a project and get credentials")
        print("  3. Set environment variables:")
        print("     - X_API_KEY")
        print("     - X_API_SECRET")
        print("     - X_ACCESS_TOKEN")
        print("     - X_ACCESS_TOKEN_SECRET")
        print("\nFor now, you can still browse the scraper documentation or ")
        print("use other data sources (ESPN, NFL.com) that don't require API keys.")
        return

    try:
        posts = []

        if args.team:
            # Fetch team-specific posts
            print(f"\n[1] Fetching posts from {args.team} ({args.league.upper()})...")
            team_posts = await scraper.get_team_news(
                args.team, args.league, days=args.days
            )
            posts.extend(team_posts)
            print(f"[OK] Found {len(team_posts)} posts")

        else:
            # Fetch by type
            if args.type in ["injury", "all"]:
                print(f"\n[1] Fetching {args.league.upper()} injuries...")
                injury_posts = await scraper.get_league_news(
                    args.league,
                    source_type="injury",
                    days=args.days,
                )
                posts.extend(injury_posts)
                print(f"[OK] Found {len(injury_posts)} posts")

            if args.type in ["news", "all"]:
                print(f"\n[2] Fetching {args.league.upper()} news...")
                news_posts = await scraper.get_league_news(
                    args.league, source_type="news", days=args.days
                )
                posts.extend(news_posts)
                print(f"[OK] Found {len(news_posts)} posts")

        # Display results
        if posts:
            print(f"\n{'=' * 70}")
            print(f"RESULTS ({len(posts)} posts)")
            print(f"{'=' * 70}")

            for post in posts[:10]:
                print(f"\n@{post.author_handle}")
                print(f"  {post.text[:100]}")
                print(f"  Relevance: {post.relevance_score:.1%}")
                print(f"  Date: {post.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Engagement: {post.likes} likes, {post.retweets} retweets")

            if len(posts) > 10:
                print(f"\n... and {len(posts) - 10} more posts")

            # Export if requested
            if args.export:
                await scraper.export_posts(posts, args.league, args.type)

        else:
            print("\n[!] No posts found")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()

    finally:
        await scraper.close()
        print(f"\n{'=' * 70}")
        print("Done!")
        print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())
