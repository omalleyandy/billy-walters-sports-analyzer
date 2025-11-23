"""
Test NFL.com API Client

Tests the NFL.com client with discovered API endpoints.
Run this after using DevTools to find real endpoints.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.nfl_com_client import NFLComClient, get_nfl_schedule, get_nfl_news


async def test_schedule():
    """Test schedule API"""
    print("\n" + "=" * 60)
    print("Testing NFL Schedule API")
    print("=" * 60)

    # Test Week 12, 2025 (current week)
    games = await get_nfl_schedule(season=2025, week=12)

    if games:
        print(f"\n✅ Found {len(games)} games for 2025 Week 12")
        for game in games[:3]:  # Show first 3
            print(f"\n  {game.away_team} @ {game.home_team}")
            print(f"  Time: {game.game_time}")
            print(f"  Stadium: {game.stadium}")
            print(f"  Network: {game.network or 'TBD'}")
            print(f"  Status: {game.game_status}")
    else:
        print("\n⚠️  No games found (API endpoint may need updating)")
        print("    Use DevTools guide to find real endpoint")


async def test_news():
    """Test news API"""
    print("\n" + "=" * 60)
    print("Testing NFL News API")
    print("=" * 60)

    # Test general news
    news = await get_nfl_news(limit=5)

    if news:
        print(f"\n✅ Found {len(news)} news articles")
        for article in news[:3]:
            print(f"\n  {article.title}")
            print(f"  Team: {article.team or 'League-wide'}")
            print(f"  Category: {article.category}")
            print(f"  Published: {article.published_at}")
            print(f"  URL: {article.url}")
    else:
        print("\n⚠️  No news found (API endpoint may need updating)")
        print("    Use DevTools guide to find real endpoint")


async def test_full_client():
    """Test full client lifecycle"""
    print("\n" + "=" * 60)
    print("Testing Full NFL.com Client")
    print("=" * 60)

    client = NFLComClient()
    await client.connect()

    try:
        # Test schedule
        print("\n[1/2] Fetching schedule...")
        games = await client.get_schedule(season=2025, week=12)
        print(f"      Found {len(games)} games")

        if games:
            # Save schedule
            filepath = await client.save_schedule(games, season=2025, week=12)
            print(f"      Saved to: {filepath}")

        # Test news
        print("\n[2/2] Fetching news...")
        news = await client.get_team_news(team_abbr="KC", limit=10)
        print(f"      Found {len(news)} Kansas City news articles")

        if news:
            # Save news
            filepath = await client.save_news(news, team="KC")
            print(f"      Saved to: {filepath}")

        print("\n" + "=" * 60)
        print("✅ Client test complete!")
        print("=" * 60)

    finally:
        await client.close()


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("NFL.com API Client Test Suite")
    print("=" * 70)
    print("\nNOTE: This client uses placeholder API endpoints.")
    print("Use docs/guides/NFL_COM_DEVTOOLS_GUIDE.md to discover real endpoints.")
    print("Then update src/data/nfl_com_client.py with actual URLs.")

    # Run tests
    await test_schedule()
    await test_news()
    await test_full_client()

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. Follow DevTools guide to find real API endpoints")
    print("2. Update nfl_com_client.py with discovered URLs")
    print("3. Run this test again to validate")
    print("4. Integrate into /collect-all-data workflow")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
