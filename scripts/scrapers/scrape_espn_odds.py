#!/usr/bin/env python3
"""
Scrape ESPN NFL and NCAAF Betting Odds

Usage:
    # Scrape NFL odds
    uv run python scripts/scrapers/scrape_espn_odds.py --league nfl

    # Scrape NCAAF odds
    uv run python scripts/scrapers/scrape_espn_odds.py --league ncaaf

    # Scrape both leagues
    uv run python scripts/scrapers/scrape_espn_odds.py --league all
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.espn_api_client import ESPNAPIClient


def scrape_odds(league: str):
    """
    Scrape odds for NFL or NCAAF

    Args:
        league: 'nfl' or 'ncaaf' or 'all'
    """
    client = ESPNAPIClient()

    print("=" * 70)
    print(f"ESPN ODDS SCRAPER")
    print("=" * 70)

    results = {}

    leagues_to_scrape = []
    if league == "all":
        leagues_to_scrape = ["nfl", "ncaaf"]
    else:
        leagues_to_scrape = [league]

    for lg in leagues_to_scrape:
        print(f"\nFetching {lg.upper()} odds...")

        try:
            if lg == "nfl":
                odds = client.get_nfl_odds()
            else:
                odds = client.get_ncaaf_odds()

            items = odds.get("items", [])
            print(f"  Games with odds: {len(items)}")

            # Save using new output structure
            filepath = client.save_to_json(odds, data_type="odds", league=lg)

            # Show sample games with odds
            if items:
                print(f"\n  Sample games:")
                for item in items[:3]:
                    event_id = item.get("id", "Unknown")
                    odds_providers = item.get("odds", [])
                    print(f"    Event {event_id}: {len(odds_providers)} providers")

            results[lg] = {
                "success": True,
                "game_count": len(items),
                "filepath": filepath,
            }

        except Exception as e:
            print(f"  [ERROR] {e}")
            results[lg] = {"success": False, "error": str(e)}

    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)

    for lg, result in results.items():
        if result.get("success"):
            print(f"{lg.upper()}: {result['game_count']} games → {result['filepath']}")
        else:
            print(f"{lg.upper()}: FAILED - {result.get('error')}")

    return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Scrape ESPN NFL/NCAAF betting odds"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf", "all"],
        default="all",
        help="League to scrape (default: all)",
    )

    args = parser.parse_args()

    try:
        results = scrape_odds(league=args.league)

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
