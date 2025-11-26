"""
CLI: Scrape NFL Game Stats from NFL.com

Fetches game statistics for all games in a given week from NFL.com.
Extracts team-by-team stats from the STATS tab.

Usage:
    # Week 12 stats (default)
    python scrape_nfl_game_stats.py

    # Specific week
    python scrape_nfl_game_stats.py --year 2025 --week reg-12

    # Show browser while scraping
    python scrape_nfl_game_stats.py --headless false

    # Custom output directory
    python scrape_nfl_game_stats.py --output output/my_stats
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.nfl_game_stats_client import NFLGameStatsClient

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape NFL.com game statistics for a week",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape_nfl_game_stats.py
  python scrape_nfl_game_stats.py --year 2025 --week reg-13
  python scrape_nfl_game_stats.py --headless false --verbose
        """,
    )

    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="NFL season year (default: 2025)",
    )

    parser.add_argument(
        "--week",
        type=str,
        default="reg-12",
        help="Week identifier (reg-12, reg-13, post-1, etc.) (default: reg-12)",
    )

    parser.add_argument(
        "--headless",
        type=str,
        default="true",
        choices=["true", "false"],
        help="Run browser in headless mode (default: true)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output/nfl_game_stats",
        help="Output directory for JSON files (default: output/nfl_game_stats)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Parse headless flag
    headless = args.headless.lower() == "true"

    logger.info("Starting NFL game stats scraper")
    logger.info(f"  Year: {args.year}")
    logger.info(f"  Week: {args.week}")
    logger.info(f"  Headless: {headless}")
    logger.info(f"  Output: {args.output}")

    client = NFLGameStatsClient(headless=headless)

    try:
        # Fetch stats for the week
        logger.info(f"Fetching stats for {args.year} week {args.week}...")
        stats = await client.get_week_stats(year=args.year, week=args.week)

        if not stats.get("games"):
            logger.warning("No game stats were collected")
            return 1

        # Export results
        logger.info(f"Collected stats for {len(stats['games'])} games")
        filepath = await client.export_stats(stats, args.output)

        logger.info(f"Stats exported to {filepath}")

        # Print summary
        print("\n" + "=" * 70)
        print("NFL GAME STATS SCRAPE COMPLETE")
        print("=" * 70)
        print(f"Games collected: {len(stats['games'])}")
        print(f"Output file: {filepath}")

        for game in stats["games"]:
            if "away_team" in game and "home_team" in game:
                away = game["away_team"]
                home = game["home_team"]
                print(f"  - {away} @ {home}")

        return 0

    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        return 1

    finally:
        await client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
