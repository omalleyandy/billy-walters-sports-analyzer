#!/usr/bin/env python3
"""Fetch NFL and NCAAF schedules for specific weeks"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from data.espn_api_client import ESPNAPIClient


async def fetch_schedules(nfl_week: int, ncaaf_week: int):
    """Fetch schedules for both leagues"""
    client = ESPNAPIClient()

    # Fetch NFL schedule
    print(f"\nFetching NFL Week {nfl_week} schedule...")
    try:
        nfl_games = await client.get_games("nfl", 2025, nfl_week)
        print(f"[OK] Found {len(nfl_games)} NFL games")

        print("\nNFL Week 13 Games:")
        print("=" * 80)
        for game in nfl_games:
            away = game.get("away_team", "TBD")
            home = game.get("home_team", "TBD")
            date = game.get("date", "TBD")
            print(f"  {away:25s} @ {home:25s} | {date}")
    except Exception as e:
        print(f"[ERROR] NFL schedule fetch failed: {e}")
        nfl_games = []

    # Fetch NCAAF schedule
    print(f"\nFetching NCAAF Week {ncaaf_week} schedule...")
    try:
        ncaaf_games = await client.get_games("ncaaf", 2025, ncaaf_week)
        print(f"[OK] Found {len(ncaaf_games)} NCAAF games")

        print("\nNCAAF Week 14 Games (sample):")
        print("=" * 80)
        for game in ncaaf_games[:10]:  # Show first 10
            away = game.get("away_team", "TBD")
            home = game.get("home_team", "TBD")
            date = game.get("date", "TBD")
            print(f"  {away:25s} @ {home:25s} | {date}")
        if len(ncaaf_games) > 10:
            print(f"  ... and {len(ncaaf_games) - 10} more games")
    except Exception as e:
        print(f"[ERROR] NCAAF schedule fetch failed: {e}")
        ncaaf_games = []

    await client.close()

    return nfl_games, ncaaf_games


if __name__ == "__main__":
    nfl_week = 13
    ncaaf_week = 14

    nfl_games, ncaaf_games = asyncio.run(fetch_schedules(nfl_week, ncaaf_week))

    print(f"\n" + "=" * 80)
    print(f"SUMMARY: {len(nfl_games)} NFL games, {len(ncaaf_games)} NCAAF games")
    print("=" * 80)
