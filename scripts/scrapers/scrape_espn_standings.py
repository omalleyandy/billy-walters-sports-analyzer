#!/usr/bin/env python3
"""
Scrape ESPN NFL and NCAAF Standings

Usage:
    # Scrape NFL standings
    uv run python scripts/scrapers/scrape_espn_standings.py --league nfl

    # Scrape NCAAF standings
    uv run python scripts/scrapers/scrape_espn_standings.py --league ncaaf

    # Scrape both leagues
    uv run python scripts/scrapers/scrape_espn_standings.py --league all

    # Scrape with specific season
    uv run python scripts/scrapers/scrape_espn_standings.py --league nfl --season 2025
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.espn_api_client import ESPNAPIClient


def scrape_standings(league: str, season: int | None = None):
    """
    Scrape standings for NFL or NCAAF

    Args:
        league: 'nfl' or 'ncaaf' or 'all'
        season: Season year (optional)
    """
    client = ESPNAPIClient()

    print("=" * 70)
    print(f"ESPN STANDINGS SCRAPER")
    print("=" * 70)

    results = {}

    leagues_to_scrape = []
    if league == "all":
        leagues_to_scrape = ["nfl", "ncaaf"]
    else:
        leagues_to_scrape = [league]

    for lg in leagues_to_scrape:
        print(f"\nFetching {lg.upper()} standings...")
        if season:
            print(f"  Season: {season}")

        try:
            if lg == "nfl":
                standings = client.get_nfl_standings(season=season)
            else:
                standings = client.get_ncaaf_standings(season=season)

            # Save using new output structure
            filepath = client.save_to_json(
                standings, data_type="standings", league=lg
            )

            # Try to extract division/conference info
            children = standings.get("children", [])
            if children:
                print(f"  Divisions/Conferences: {len(children)}")
                for child in children[:3]:
                    name = child.get("name", "Unknown")
                    teams = child.get("standings", {}).get("entries", [])
                    print(f"    {name}: {len(teams)} teams")

            results[lg] = {"success": True, "filepath": filepath}

        except Exception as e:
            print(f"  [ERROR] {e}")
            results[lg] = {"success": False, "error": str(e)}

    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)

    for lg, result in results.items():
        if result.get("success"):
            print(f"{lg.upper()}: Saved -> {result['filepath']}")
        else:
            print(f"{lg.upper()}: FAILED - {result.get('error')}")

    return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Scrape ESPN NFL/NCAAF standings"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf", "all"],
        default="all",
        help="League to scrape (default: all)",
    )
    parser.add_argument(
        "--season",
        type=int,
        help="Season year (optional)",
    )

    args = parser.parse_args()

    try:
        results = scrape_standings(league=args.league, season=args.season)

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
    exit(main())
