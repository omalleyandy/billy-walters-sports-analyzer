#!/usr/bin/env python3
"""
Display all NFL odds for specific dates (e.g., November 9-10, 2025)
"""

import asyncio
import sys
from collections import defaultdict
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    import io

    try:
        if hasattr(sys.stdout, "buffer") and not isinstance(
            sys.stdout, io.TextIOWrapper
        ):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
    except (AttributeError, ValueError, OSError):
        pass

from walters_analyzer.feeds.market_data_client import OddsAPIClient
from walters_analyzer.config import get_settings


async def show_week_odds(target_dates=None):
    """
    Fetch and display NFL odds for specific dates

    Args:
        target_dates: List of date strings like ['2025-11-09', '2025-11-10']
    """
    settings = get_settings()
    client = OddsAPIClient()

    print("Fetching NFL odds from The Odds API...")
    print()

    odds = await client.get_odds("americanfootball_nfl")

    if not odds:
        print("No odds data available")
        return

    # Group by game
    games = defaultdict(list)
    for odd in odds:
        games[odd["game_id"]].append(odd)

    # Filter by dates if specified
    filtered_games = {}
    if target_dates:
        from datetime import timezone, timedelta

        target_date_strs = [str(d) for d in target_dates]
        print(f"Filtering for games on: {', '.join(target_date_strs)}")
        print()

        for game_id, game_odds in games.items():
            if game_odds:
                commence_time = game_odds[0].get("commence_time", "")

                # Convert UTC time to ET before extracting date
                try:
                    dt_utc = datetime.fromisoformat(
                        commence_time.replace("Z", "+00:00")
                    )
                    et_offset = timedelta(hours=-5)
                    dt_et = dt_utc.astimezone(timezone(et_offset))
                    game_date = dt_et.strftime("%Y-%m-%d")
                except:
                    # Fallback to UTC date if conversion fails
                    game_date = (
                        commence_time.split("T")[0] if "T" in commence_time else ""
                    )

                if game_date in target_date_strs:
                    filtered_games[game_id] = game_odds
    else:
        filtered_games = games

    if not filtered_games:
        from datetime import timezone, timedelta

        print(f"No games found for the specified dates: {', '.join(target_dates)}")
        print()
        print("Available game dates (ET):")
        all_dates = set()
        for game_id, game_odds in games.items():
            if game_odds:
                commence_time = game_odds[0].get("commence_time", "")

                # Convert UTC time to ET before extracting date
                try:
                    dt_utc = datetime.fromisoformat(
                        commence_time.replace("Z", "+00:00")
                    )
                    et_offset = timedelta(hours=-5)
                    dt_et = dt_utc.astimezone(timezone(et_offset))
                    game_date = dt_et.strftime("%Y-%m-%d")
                except:
                    game_date = (
                        commence_time.split("T")[0] if "T" in commence_time else ""
                    )

                if game_date:
                    all_dates.add(game_date)

        for date in sorted(all_dates):
            print(f"  - {date}")
        return

    # Get sharp and public books from settings
    sharp_books = settings.skills.market_analysis.sharp_books
    public_books = settings.skills.market_analysis.public_books

    print("=" * 100)
    print(f"NFL ODDS - {len(filtered_games)} GAMES")
    print("=" * 100)
    print()

    # Sort games by commence time
    sorted_games = sorted(
        filtered_games.items(),
        key=lambda x: x[1][0].get("commence_time", "") if x[1] else "",
    )

    for i, (game_id, game_odds) in enumerate(sorted_games):
        if i > 0:
            print()
            print("-" * 100)
            print()

        sample = game_odds[0]
        teams = sample["teams"]

        # Parse commence time
        commence = sample.get("commence_time", "Unknown")
        try:
            from datetime import timezone, timedelta

            # Parse UTC time and convert to ET (UTC-5)
            dt_utc = datetime.fromisoformat(commence.replace("Z", "+00:00"))
            et_offset = timedelta(hours=-5)
            dt_et = dt_utc.astimezone(timezone(et_offset))
            game_time = dt_et.strftime("%A, %B %d at %I:%M %p ET")
        except:
            game_time = commence

        print(f"{i + 1}. {teams['away']} @ {teams['home']}")
        print(f"   Kickoff: {game_time}")
        print()

        # Collect all spreads by book
        all_spreads = {}
        for odd in game_odds:
            book = odd["book"]
            spread = odd.get("markets", {}).get("spread", {})
            home_line = spread.get("home", {})

            if home_line.get("line") is not None:
                all_spreads[book] = {
                    "line": home_line["line"],
                    "price": home_line.get("price", 0),
                }

        # Separate by book type
        sharp_spreads = {k: v for k, v in all_spreads.items() if k in sharp_books}
        public_spreads = {k: v for k, v in all_spreads.items() if k in public_books}
        other_spreads = {
            k: v
            for k, v in all_spreads.items()
            if k not in sharp_books and k not in public_books
        }

        # Display sharp books
        if sharp_spreads:
            print("   SHARP BOOKS:")
            for book, data in sorted(sharp_spreads.items()):
                print(f"      {book:<20} {data['line']:+6.1f} ({data['price']:+4d})")

            avg_sharp = sum(d["line"] for d in sharp_spreads.values()) / len(
                sharp_spreads
            )
            print(f"      {'SHARP CONSENSUS':<20} {avg_sharp:+6.1f}")
        else:
            print("   SHARP BOOKS: Not available (Premium tier required)")

        print()

        # Display public books
        if public_spreads:
            print("   PUBLIC BOOKS:")
            for book, data in sorted(public_spreads.items()):
                print(f"      {book:<20} {data['line']:+6.1f} ({data['price']:+4d})")

            avg_public = sum(d["line"] for d in public_spreads.values()) / len(
                public_spreads
            )
            print(f"      {'PUBLIC CONSENSUS':<20} {avg_public:+6.1f}")
        else:
            print("   PUBLIC BOOKS: No data")

        print()

        # Display other books
        if other_spreads:
            print("   OTHER BOOKS:")
            for book, data in sorted(other_spreads.items()):
                print(f"      {book:<20} {data['line']:+6.1f} ({data['price']:+4d})")

        # Calculate line variance
        if all_spreads:
            all_lines = [d["line"] for d in all_spreads.values()]
            min_line = min(all_lines)
            max_line = max(all_lines)
            variance = max_line - min_line

            if variance >= 1.0:
                print()
                print(f"   LINE VARIANCE: {variance:.1f} points")
                print(f"   Range: {min_line:+.1f} to {max_line:+.1f}")

                # Find best books for each side
                best_away = max(all_spreads.items(), key=lambda x: x[1]["line"])
                best_home = min(all_spreads.items(), key=lambda x: x[1]["line"])

                print(
                    f"   Best for {teams['away']}: {best_away[0]} ({best_away[1]['line']:+.1f})"
                )
                print(
                    f"   Best for {teams['home']}: {best_home[0]} ({best_home[1]['line']:+.1f})"
                )

                if variance >= 1.5:
                    print()
                    print("   ** SIGNIFICANT VARIANCE - POSSIBLE MIDDLE OPPORTUNITY **")

        # Show divergence if both sharp and public exist
        if sharp_spreads and public_spreads:
            divergence = avg_sharp - avg_public
            if abs(divergence) >= 0.5:
                print()
                print(f"   SHARP vs PUBLIC DIVERGENCE: {divergence:+.1f} points")
                if abs(divergence) >= settings.skills.market_analysis.alert_threshold:
                    print("   ** ALERT THRESHOLD EXCEEDED **")
                    if divergence > 0:
                        print(f"   Indication: Sharp money may be on {teams['away']}")
                    else:
                        print(f"   Indication: Sharp money may be on {teams['home']}")

    print()
    print("=" * 100)
    print(f"Total games: {len(filtered_games)}")
    print("Data source: The Odds API")
    print(f"Alert threshold: {settings.skills.market_analysis.alert_threshold} points")
    print("=" * 100)


if __name__ == "__main__":
    # Default to November 9-10, 2025
    target_dates = ["2025-11-09", "2025-11-10"]

    if len(sys.argv) > 1:
        # Allow custom dates: python show_week_odds.py 2025-11-09 2025-11-10
        target_dates = sys.argv[1:]

    asyncio.run(show_week_odds(target_dates))
