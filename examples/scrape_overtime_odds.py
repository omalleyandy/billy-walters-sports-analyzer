"""
Example: Scraping NFL and NCAAF odds from Overtime.ag

This example demonstrates how to use the overtime_ag_client in your
Billy Walters Sports Analyzer project to fetch live betting odds.

The client:
1. Logs into Overtime.ag with your credentials (from .env)
2. Extracts game data from localStorage (primary method)
3. Falls back to HTML parsing if needed
4. Returns fully parsed OvertimeGame objects with UTC datetimes

All datetimes are automatically converted to UTC for consistency
across your Billy Walters analysis system.
"""

import asyncio
import json
from datetime import datetime

from overtime_ag_client.client import OvertimeClient
from overtime_ag_client.models import Sport


async def main():
    """Demonstrate overtime_ag_client usage."""

    # Initialize client (credentials from .env: OV_CUSTOMER_ID, OV_PASSWORD)
    async with OvertimeClient(headless=True) as client:
        print("[INFO] Overtime.ag Client initialized")
        print("[INFO] Connecting to Overtime.ag...\n")

        # Get NFL odds
        print("=" * 60)
        print("FETCHING NFL ODDS")
        print("=" * 60)

        nfl_scoreboard = await client.get_nfl_odds()

        print(f"[OK] Fetched {nfl_scoreboard.game_count} NFL games")
        print(f"[OK] Week: {nfl_scoreboard.week}")
        print(f"[OK] Scrape duration: {nfl_scoreboard.scrape_duration_ms}ms\n")

        # Display first game as example
        if nfl_scoreboard.games:
            game = nfl_scoreboard.games[0]
            print("Sample Game:")
            print(f"  Matchup: {game.matchup_display}")
            print(f"  Game Time: {game.game_datetime} (UTC)")
            print(f"  Local Time: {game.game_time} {game.game_timezone}")
            print(f"  Spread: {game.odds.home_spread_display}")
            print(f"  Total: {game.odds.total_display}")
            print(f"  Week: {game.week}\n")

        # Get NCAAF odds
        print("=" * 60)
        print("FETCHING NCAAF ODDS")
        print("=" * 60)

        ncaaf_scoreboard = await client.get_ncaaf_odds()

        print(f"[OK] Fetched {ncaaf_scoreboard.game_count} NCAAF games")
        print(f"[OK] Week: {ncaaf_scoreboard.week}")
        print(f"[OK] Scrape duration: {ncaaf_scoreboard.scrape_duration_ms}ms\n")

        # Using the data with Billy Walters system
        print("=" * 60)
        print("CONVERTING TO BILLY WALTERS FORMAT")
        print("=" * 60)

        # Convert games to Billy Walters format
        nfl_data = nfl_scoreboard.to_dataframe_dict()
        ncaaf_data = ncaaf_scoreboard.to_dataframe_dict()

        print(f"NFL games ready for analysis: {len(nfl_data)}")
        print(f"NCAAF games ready for analysis: {len(ncaaf_data)}\n")

        # Example: Get a specific game
        if nfl_scoreboard.games:
            game = nfl_scoreboard.games[0]
            print(f"Game details (to_betting_dict):")
            game_dict = game.to_betting_dict()

            # Show key fields
            key_fields = [
                "away_team",
                "home_team",
                "game_datetime",
                "game_timezone",
                "away_spread",
                "home_spread",
                "away_ml",
                "home_ml",
                "total",
            ]

            for field in key_fields:
                print(f"  {field}: {game_dict.get(field)}")

        print("\n[OK] Ready to feed into Billy Walters analysis pipeline!")


if __name__ == "__main__":
    asyncio.run(main())
