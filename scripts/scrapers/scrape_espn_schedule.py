#!/usr/bin/env python3
"""
Scrape ESPN NFL and NCAAF Schedules

Usage:
    # Scrape NFL schedule for specific week
    uv run python scripts/scrapers/scrape_espn_schedule.py --league nfl --week 10

    # Scrape NCAAF schedule
    uv run python scripts/scrapers/scrape_espn_schedule.py --league ncaaf --week 12

    # Scrape both leagues
    uv run python scripts/scrapers/scrape_espn_schedule.py --league all
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.espn_api_client import ESPNAPIClient


def scrape_schedule(league: str, week: int | None = None, season: int | None = None):
    """
    Scrape schedule for NFL or NCAAF

    Args:
        league: 'nfl' or 'ncaaf' or 'all'
        week: Week number (optional)
        season: Season year (optional)
    """
    client = ESPNAPIClient()

    print("=" * 70)
    print(f"ESPN SCHEDULE SCRAPER")
    print("=" * 70)

    results = {}

    leagues_to_scrape = []
    if league == "all":
        leagues_to_scrape = ["nfl", "ncaaf"]
    else:
        leagues_to_scrape = [league]

    for lg in leagues_to_scrape:
        print(f"\nFetching {lg.upper()} schedule...")
        if week:
            print(f"  Week: {week}")

        try:
            if lg == "nfl":
                schedule = client.get_nfl_schedule(week=week, season_type=2)
            else:
                schedule = client.get_ncaaf_schedule(week=week)

            events = schedule.get("events", [])
            print(f"  Games found: {len(events)}")

            # Save using new output structure
            filepath = client.save_to_json(
                schedule, data_type="schedule", league=lg
            )

            results[lg] = {
                "success": True,
                "game_count": len(events),
                "filepath": filepath,
            }

            # Show sample games
            if events:
                print(f"\n  Sample games:")
                for event in events[:3]:
                    comps = event.get("competitions", [{}])[0]
                    teams = comps.get("competitors", [])
                    if len(teams) >= 2:
                        away = teams[0].get("team", {}).get("displayName", "Team 1")
                        home = teams[1].get("team", {}).get("displayName", "Team 2")
                        date = comps.get("date", "")
                        print(f"    {away} @ {home} - {date}")

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
        description="Scrape ESPN NFL/NCAAF schedules"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf", "all"],
        default="all",
        help="League to scrape (default: all)",
    )
    parser.add_argument(
        "--week",
        type=int,
        help="Week number (optional)",
    )
    parser.add_argument(
        "--season",
        type=int,
        help="Season year (optional)",
    )

    args = parser.parse_args()

    try:
        results = scrape_schedule(
            league=args.league, week=args.week, season=args.season
        )

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
