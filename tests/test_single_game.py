"""
Quick test: Single game stats extraction (no schedule parsing)
This tests the core functionality without the schedule page complexity.
"""

import asyncio
import logging
from src.data.nfl_game_stats_client import NFLGameStatsClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    """Test single game stats extraction."""
    client = NFLGameStatsClient(headless=False)  # Show browser for debugging

    try:
        await client.connect()

        # Test single game (latest game URL from Week 12)
        game_url = "https://www.nfl.com/games/bills-at-texans-2025-reg-12?tab=stats"

        print("\n" + "=" * 70)
        print("Testing Single Game Stats Extraction")
        print("=" * 70)
        print(f"Game: Bills @ Texans")
        print(f"URL: {game_url}")
        print("=" * 70 + "\n")

        stats = await client.get_game_stats(game_url)

        if stats:
            print("\nSUCCESS! Stats extracted:")
            print(f"  Away Team: {stats.get('away_team')}")
            print(f"  Home Team: {stats.get('home_team')}")
            print(f"  Score: {stats.get('score')}")
            print(f"  Teams with stats: {list(stats.get('teams_stats', {}).keys())}")

            # Export to file
            filepath = await client.export_stats({"games": [stats]})
            print(f"\nExported to: {filepath}")
            return 0

        else:
            print("\nFAILED! No stats extracted")
            return 1

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        await client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
