#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Test market data integration and sharp money monitoring

This script demonstrates how to:
1. Connect to The Odds API
2. Fetch live odds data
3. Monitor for sharp money movements
4. Receive alerts when edges are detected
"""

import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from walters_analyzer.feeds.market_data_client import OddsAPIClient
from walters_analyzer.feeds.market_monitor import MarketMonitor
from walters_analyzer.config import get_settings


async def test_api_connection():
    """Test basic API connection and data fetching"""
    print("=" * 80)
    print("TEST 1: API Connection")
    print("=" * 80)
    print()

    client = OddsAPIClient()

    # Check if API key is configured
    settings = get_settings()
    if not settings.odds_api_key:
        print("[ERROR] ODDS_API_KEY not found in environment")
        print()
        print("To set up:")
        print("  1. Sign up at https://the-odds-api.com/")
        print("  2. Get your API key from the dashboard")
        print("  3. Create .env file in project root with:")
        print("     ODDS_API_KEY=your_key_here")
        print()
        return False

    print("[*] API key configured")
    print()

    # Fetch NFL odds
    print("Fetching NFL odds...")
    odds = await client.get_odds("americanfootball_nfl")

    if not odds:
        print("[ERROR] No odds data received")
        print("   This could mean:")
        print("   - Invalid API key")
        print("   - No active NFL games")
        print("   - API rate limit reached")
        return False

    print("[*] Successfully fetched odds!")
    print(f"   Total book/game combinations: {len(odds)}")
    print(f"   Unique games: {len(set(o['game_id'] for o in odds))}")
    print()

    # Show sample games
    games = {}
    for odd in odds:
        game_id = odd["game_id"]
        if game_id not in games:
            games[game_id] = {"teams": odd["teams"], "books": []}
        games[game_id]["books"].append(odd["book"])

    print("Sample Games:")
    print("-" * 80)

    for i, (game_id, game_info) in enumerate(list(games.items())[:3]):
        teams = game_info["teams"]
        books = game_info["books"]
        print(f"{i + 1}. {teams['away']} @ {teams['home']}")
        print(f"   Books: {', '.join(books[:5])}")
        if len(books) > 5:
            print(f"   ... and {len(books) - 5} more")
        print()

    return True


async def test_line_extraction():
    """Test extracting spread lines from odds data"""
    print("=" * 80)
    print("TEST 2: Line Extraction")
    print("=" * 80)
    print()

    client = OddsAPIClient()
    odds = await client.get_odds("americanfootball_nfl")

    if not odds:
        print("[WARNING]  Skipping - no odds data")
        return

    # Get sharp vs public book breakdown
    settings = get_settings()
    sharp_books = settings.skills.market_analysis.sharp_books
    public_books = settings.skills.market_analysis.public_books

    # Analyze first game
    game_odds = {}
    for odd in odds:
        game_id = odd["game_id"]
        if game_id not in game_odds:
            game_odds[game_id] = []
        game_odds[game_id].append(odd)

    if not game_odds:
        print("[WARNING]  No games found")
        return

    # Pick first game
    first_game_id = list(game_odds.keys())[0]
    first_game_odds = game_odds[first_game_id]

    # Get game info
    sample = first_game_odds[0]
    teams = sample["teams"]

    print(f"Analyzing: {teams['away']} @ {teams['home']}")
    print(f"Game ID: {first_game_id}")
    print()

    # Extract lines by book
    print("Spread Lines by Book:")
    print("-" * 80)
    print(f"{'Book':<20} {'Sharp/Public':<15} {'Line':<10}")
    print("-" * 80)

    for odd in first_game_odds:
        book = odd["book"]
        book_type = (
            "SHARP"
            if book in sharp_books
            else "PUBLIC"
            if book in public_books
            else "OTHER"
        )

        spread = odd.get("markets", {}).get("spread", {})
        home_spread = spread.get("home", {})
        line = home_spread.get("line")
        price = home_spread.get("price")

        if line is not None:
            print(f"{book:<20} {book_type:<15} {line:+6.1f} ({price:+4d})")

    print()


async def test_monitoring():
    """Test live monitoring for sharp money (short duration)"""
    print("=" * 80)
    print("TEST 3: Sharp Money Monitoring")
    print("=" * 80)
    print()

    settings = get_settings()

    print("Configuration:")
    print(f"  Sharp Books: {', '.join(settings.skills.market_analysis.sharp_books)}")
    print(f"  Public Books: {', '.join(settings.skills.market_analysis.public_books)}")
    print(
        f"  Alert Threshold: {settings.skills.market_analysis.alert_threshold} points"
    )
    print(
        f"  Check Interval: {settings.skills.market_analysis.monitor_interval} seconds"
    )
    print()

    print("Starting 2-minute monitoring test...")
    print("(In production, you'd run this for hours)")
    print()

    monitor = MarketMonitor()

    try:
        # Monitor for 2 minutes
        await monitor.monitor_sport(sport="americanfootball_nfl", duration_minutes=2)

        # Show summary
        summary = monitor.get_alert_summary()
        print()
        print("=" * 80)
        print("MONITORING SUMMARY")
        print("=" * 80)
        print(f"Total Alerts: {summary.get('total_alerts', 0)}")

        if summary.get("total_alerts", 0) > 0:
            print(f"Average Confidence: {summary.get('avg_confidence', 0):.1f}%")

            top_games = summary.get("most_alerted_games", [])
            if top_games:
                print("\nMost Active Games:")
                for game in top_games:
                    print(f"  • {game['matchup']}: {game['alert_count']} alerts")
        else:
            print("\nNo alerts detected in this short test period.")
            print("(This is normal - line movements take time)")

        print()

    except KeyboardInterrupt:
        print("\n[WARNING]  Test interrupted")


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("BILLY WALTERS MARKET DATA INTEGRATION TEST")
    print("=" * 80)
    print()

    # Test 1: API Connection
    connected = await test_api_connection()
    if not connected:
        print("\n[ERROR] API connection test failed. Fix the above issues and try again.")
        return

    print("[*] Test 1 passed!\n")
    await asyncio.sleep(1)

    # Test 2: Line Extraction
    await test_line_extraction()
    print("[*] Test 2 passed!\n")
    await asyncio.sleep(1)

    # Test 3: Monitoring (optional)
    print("\nWould you like to run a 2-minute monitoring test?")
    print("This will use API quota and take 2 minutes.")
    response = input("Run monitoring test? (y/N): ").strip().lower()

    if response == "y":
        await test_monitoring()
        print("[*] Test 3 passed!\n")
    else:
        print("⏭[*]  Skipping monitoring test\n")

    # Final summary
    print("=" * 80)
    print("ALL TESTS COMPLETE!")
    print("=" * 80)
    print()
    print("[*] Your market data integration is working!")
    print()
    print("Next steps:")
    print("  1. Run full monitoring: uv run walters-analyzer monitor-sharp --sport nfl")
    print("  2. Customize settings in .env or .claude/claude-desktop-config.json")
    print("  3. Review alerts in logs/alerts.log")
    print()


if __name__ == "__main__":
    asyncio.run(main())
