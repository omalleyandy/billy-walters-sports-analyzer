#!/usr/bin/env python3
"""
NFL.com Official API Scraper

CLI script to fetch official NFL data from the NFL.com API discovered via
Chrome DevTools reverse engineering.

Coverage:
- Schedules: Game times, TV networks, locations (all weeks)
- News: Latest NFL articles (optional team filtering)
- Player Stats: Individual performance metrics

Billy Walters Integration:
- Authoritative NFL data (official source)
- Real-time game information
- Injury-related news
- Weekly schedule validation

Usage:
    # Get schedule for specific week
    uv run python scripts/scrapers/scrape_nfl_com.py --schedule --week 13

    # Get news for all teams
    uv run python scripts/scrapers/scrape_nfl_com.py --news

    # Get news for specific team
    uv run python scripts/scrapers/scrape_nfl_com.py --news --team buf

    # Get both schedule and news
    uv run python scripts/scrapers/scrape_nfl_com.py --schedule --news --week 13

Examples:
    # Current week schedule
    %(prog)s --schedule

    # Week 14 schedule
    %(prog)s --schedule --week 14

    # All NFL news (top 50)
    %(prog)s --news --limit 50

    # Buffalo Bills news only
    %(prog)s --news --team buf

    # Both schedule and news
    %(prog)s --schedule --news --week 13 --team buf
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.nfl_com_client import NFLComClient


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NFL.com Official API Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get schedule for current week
  %(prog)s --schedule

  # Get schedule for week 14
  %(prog)s --schedule --week 14

  # Get all NFL news (top 50 articles)
  %(prog)s --news --limit 50

  # Get Buffalo Bills news
  %(prog)s --news --team buf

  # Get schedule and news for week 13
  %(prog)s --schedule --news --week 13
        """,
    )

    # Data selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--schedule",
        action="store_true",
        help="Fetch NFL game schedule",
    )
    group.add_argument(
        "--news",
        action="store_true",
        help="Fetch latest NFL news articles",
    )

    # Schedule options
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        help="Week number (1-18). If not specified, uses current week",
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Season year (default: 2025)",
    )
    parser.add_argument(
        "--season-type",
        choices=["REG", "POST", "PRE"],
        default="REG",
        help="Season type: REG (regular), POST (playoffs), PRE (preseason). Default: REG",
    )

    # News options
    parser.add_argument(
        "--team",
        type=str,
        help="Team abbreviation for team-specific news (e.g., buf, nyj, ne)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum news articles to fetch. Default: 20",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/nfl_com"),
        help="Output directory. Default: output/nfl_com",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (except errors)",
    )

    args = parser.parse_args()

    # Initialize client
    client = NFLComClient(output_dir=args.output_dir)

    try:
        if not args.quiet:
            print("[*] NFL.com Official API Scraper")
            print("=" * 70)

        # Fetch schedule
        if args.schedule:
            if not args.quiet:
                print(f"[*] Fetching schedule (Season {args.season}, Week {args.week})")

            games = await client.get_schedule(
                season=args.season,
                week=args.week if args.week else 1,  # placeholder
                season_type=args.season_type,
            )

            if games and not args.quiet:
                print(f"[OK] Fetched {len(games)} games")
                for game in games[:3]:
                    print(
                        f"     {game.away_team} @ {game.home_team} "
                        f"({game.game_time.strftime('%Y-%m-%d %H:%M')})"
                    )
                if len(games) > 3:
                    print(f"     ... and {len(games) - 3} more games")

            # Save schedule
            if games:
                await client.save_schedule(
                    games, season=args.season, week=args.week or 1
                )
                if not args.quiet:
                    print(f"[OK] Saved schedule to {args.output_dir}")

        # Fetch news
        if args.news:
            team_str = f"for {args.team.upper()}" if args.team else "for all teams"
            if not args.quiet:
                print(f"[*] Fetching news {team_str} (limit: {args.limit})")

            articles = await client.get_team_news(
                team_abbr=args.team.lower() if args.team else None,
                limit=args.limit,
            )

            if articles and not args.quiet:
                print(f"[OK] Fetched {len(articles)} articles")
                for article in articles[:3]:
                    print(f"     - {article.title[:70]}")
                if len(articles) > 3:
                    print(f"     ... and {len(articles) - 3} more articles")

            # Save news
            if articles:
                await client.save_news(articles, team=args.team)
                if not args.quiet:
                    print(f"[OK] Saved articles to {args.output_dir}")

        if not args.quiet:
            print("\n" + "=" * 70)
            print("SCRAPING COMPLETE")
            print("=" * 70)

        return 0

    except KeyboardInterrupt:
        if not args.quiet:
            print("\n[INFO] Scraping interrupted by user")
        return 130

    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        await client.close()


if __name__ == "__main__":
    exit(asyncio.run(main()))
