#!/usr/bin/env python3
"""
ESPN NFL News & Blog Scraper

CLI script to fetch NFL team news articles from ESPN blog pages.
Extracts article titles, dates, content summaries, and categories
for team strength analysis.

Usage:
    # Get news for one team
    uv run python scripts/scrapers/scrape_espn_news.py --team buf

    # Get news for multiple teams
    uv run python scripts/scrapers/scrape_espn_news.py --teams buf nyj ne

    # Get news for all 32 NFL teams
    uv run python scripts/scrapers/scrape_espn_news.py --all-teams

    # Get more articles per team
    uv run python scripts/scrapers/scrape_espn_news.py --all-teams --limit 20

    # Run in visible browser (for debugging)
    uv run python scripts/scrapers/scrape_espn_news.py --team buf --no-headless

Examples:
    # Buffalo Bills only
    %(prog)s --team buf

    # All AFC East
    %(prog)s --teams buf nyj ne mia

    # Entire league
    %(prog)s --all-teams

    # Custom output directory
    %(prog)s --all-teams --output-dir custom/path

    # More articles per team
    %(prog)s --all-teams --limit 20 --output-dir news/detailed
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.espn_news_client import ESPNNewsClient, NFL_TEAMS


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ESPN NFL News & Blog Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get news for Buffalo Bills
  %(prog)s --team buf

  # Get all AFC East teams
  %(prog)s --teams buf nyj ne mia

  # Get all 32 teams
  %(prog)s --all-teams

  # Save to custom location
  %(prog)s --all-teams --output-dir news/nfl

  # Get more articles per team
  %(prog)s --all-teams --limit 20
        """,
    )

    # Team selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--team",
        type=str,
        help="Single team abbreviation (e.g., buf, nyj, ne)",
    )
    group.add_argument(
        "--teams",
        type=str,
        nargs="+",
        help="Multiple team abbreviations (e.g., buf nyj ne mia)",
    )
    group.add_argument(
        "--all-teams",
        action="store_true",
        help="Scrape all 32 NFL teams",
    )

    # Scraper options
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum articles per team. Default: 10",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (for debugging)",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/espn/news/nfl"),
        help="Output directory. Default: output/espn/news/nfl",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (except errors)",
    )

    args = parser.parse_args()

    # Determine teams to scrape
    teams_to_scrape = []

    if args.team:
        teams_to_scrape = [args.team.lower()]
    elif args.teams:
        teams_to_scrape = [t.lower() for t in args.teams]
    elif args.all_teams:
        teams_to_scrape = sorted(NFL_TEAMS.keys())

    # Validate team abbreviations
    invalid_teams = [t for t in teams_to_scrape if t not in NFL_TEAMS]
    if invalid_teams:
        print(f"[ERROR] Invalid team abbreviations: {', '.join(invalid_teams)}")
        return 1

    # Initialize client
    client = ESPNNewsClient(
        headless=not args.no_headless,
        max_articles=args.limit,
    )
    await client.connect()

    try:
        if not args.quiet:
            print("[*] ESPN NFL News & Blog Scraper")
            print("=" * 70)

        all_results = {}
        total_articles = 0

        # Fetch news for each team
        for team_abbr in teams_to_scrape:
            try:
                if not args.quiet:
                    team_full = NFL_TEAMS[team_abbr]["full_name"]
                    print(f"[*] Fetching {team_full}...")

                result = await client.get_team_news(
                    team_abbr, limit=args.limit
                )
                all_results[team_abbr] = result
                total_articles += result["article_count"]

                if not args.quiet:
                    article_count = result["article_count"]
                    print(f"    [OK] {article_count} articles found")
                    if article_count > 0 and article_count <= 3:
                        for article in result["articles"][:3]:
                            print(
                                f"         - {article['title'][:60]}"
                                f" ({article.get('category', 'Team News')})"
                            )

            except Exception as e:
                print(f"[ERROR] Failed to fetch {team_abbr}: {e}")
                all_results[team_abbr] = {
                    "error": str(e),
                    "articles": [],
                }

        # Save aggregated results
        if not args.quiet:
            print(f"\n[*] Saving results...")

        output_file = await client.save_news_json(all_results, args.output_dir)

        if not args.quiet:
            print("\n" + "=" * 70)
            print("NEWS SCRAPING COMPLETE")
            print("=" * 70)
            successful_teams = len(
                [r for r in all_results.values() if "error" not in r]
            )
            print(f"Teams scraped: {successful_teams}")
            print(f"Total articles: {total_articles}")
            print(f"Saved to: {output_file}")

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
