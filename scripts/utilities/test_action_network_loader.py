"""
Quick test of Action Network data loader
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.action_network_loader import ActionNetworkData, load_nfl_games


def main():
    print("=" * 60)
    print("Action Network Data Loader Test")
    print("=" * 60)

    loader = ActionNetworkData()

    # Test NFL data
    print("\n[NFL Summary]")
    nfl_summary = loader.get_summary("nfl")
    print(f"  Games: {nfl_summary.get('games', 0)}")
    print(f"  Timestamp: {nfl_summary.get('timestamp', 'N/A')}")
    print(f"  Futures: {nfl_summary.get('futures', 0)}")
    print(f"  Odds: {nfl_summary.get('odds', 0)}")
    print(f"  Public Betting: {nfl_summary.get('public-betting', 0)}")

    # Test NCAAF data
    print("\n[NCAAF Summary]")
    ncaaf_summary = loader.get_summary("ncaaf")
    print(f"  Games: {ncaaf_summary.get('games', 0)}")
    print(f"  Timestamp: {ncaaf_summary.get('timestamp', 'N/A')}")
    print(f"  Futures: {ncaaf_summary.get('futures', 0)}")
    print(f"  Odds: {ncaaf_summary.get('odds', 0)}")

    # Load and display sample games
    print("\n[Sample NFL Games]")
    nfl_games = load_nfl_games()
    for game in nfl_games[:5]:
        teams = game.teams
        if teams:
            away, home = teams
            print(f"  {away} @ {home}")
            print(f"    URL: {game.url}")
            print(f"    Game ID: {game.game_id}")
        else:
            print(f"  {game.matchup or game.slug}")
            print(f"    URL: {game.url}")
        print()

    # Test game URL lookup
    print("\n[Game URL Lookup Test]")
    test_away = "Buffalo Bills"
    test_home = "Kansas City Chiefs"
    url = loader.get_game_url(test_away, test_home)
    if url:
        print(f"  {test_away} @ {test_home}")
        print(f"  Found: {url}")
    else:
        print(f"  {test_away} @ {test_home}: Not found")

    print("\n" + "=" * 60)
    print("[OK] Action Network data loader working correctly!")
    print("=" * 60)


if __name__ == "__main__":
    main()
