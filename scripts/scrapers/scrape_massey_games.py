#!/usr/bin/env python3
"""
Scrape Massey Ratings NFL and NCAAF Games

Usage:
    # Scrape NFL games
    uv run python scripts/scrapers/scrape_massey_games.py --league nfl

    # Scrape NCAAF games
    uv run python scripts/scrapers/scrape_massey_games.py --league ncaaf

    # Scrape both leagues
    uv run python scripts/scrapers/scrape_massey_games.py --league all
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.massey_ratings_scraper import MasseyRatingsScraper


async def scrape_games(league: str):
    """
    Scrape games for NFL or NCAAF

    Args:
        league: 'nfl' or 'ncaaf' or 'all'
    """
    scraper = MasseyRatingsScraper()

    print("=" * 70)
    print("MASSEY RATINGS GAMES SCRAPER")
    print("=" * 70)

    results = {}

    leagues_to_scrape = []
    if league == "all":
        leagues_to_scrape = ["nfl", "ncaaf"]
    else:
        leagues_to_scrape = [league]

    for lg in leagues_to_scrape:
        print(f"\nScraping {lg.upper()} games...")

        try:
            if lg == "nfl":
                games_data = await scraper.scrape_nfl_games(save=True)
            else:
                games_data = await scraper.scrape_ncaaf_games(save=True)

            results[lg] = {"success": True, "data": games_data}

        except Exception as e:
            print(f"  [ERROR] {e}")
            results[lg] = {"success": False, "error": str(e)}

    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)

    for lg, result in results.items():
        if result.get("success"):
            print(f"{lg.upper()}: Success")
        else:
            print(f"{lg.upper()}: FAILED - {result.get('error')}")

    return results


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Scrape Massey Ratings NFL/NCAAF games"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf", "all"],
        default="all",
        help="League to scrape (default: all)",
    )

    args = parser.parse_args()

    try:
        results = await scrape_games(league=args.league)

        # Return 0 if all succeeded, 1 if any failed
        if all(r.get("success", False) for r in results.values()):
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
    exit(asyncio.run(main()))
