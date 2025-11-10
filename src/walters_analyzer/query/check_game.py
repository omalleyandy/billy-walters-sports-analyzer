#!/usr/bin/env python3
"""
Quick odds checker for specific teams or games
Usage: python check_game.py "Chiefs"
"""

import asyncio
import sys
from collections import defaultdict

from walters_analyzer.feeds.market_data_client import OddsAPIClient
from walters_analyzer.config import get_settings


async def check_game(search_term):
    """Find and display odds for games matching search term"""
    settings = get_settings()
    client = OddsAPIClient()

    print(f"Searching for: {search_term}")
    print("Fetching NFL odds...\n")

    odds = await client.get_odds("americanfootball_nfl")

    if not odds:
        print("No odds data available")
        return

    # Group by game
    games = defaultdict(list)
    for odd in odds:
        games[odd["game_id"]].append(odd)

    # Search for matching games
    search_lower = search_term.lower()
    matching_games = []

    for game_id, game_odds in games.items():
        sample = game_odds[0]
        teams = sample["teams"]
        away = teams.get("away", "").lower()
        home = teams.get("home", "").lower()

        if search_lower in away or search_lower in home:
            matching_games.append((game_id, game_odds))

    if not matching_games:
        print(f"No games found matching '{search_term}'")
        print("\nTip: Try searching for:")
        print("  - Team city (e.g., 'Kansas', 'Buffalo')")
        print("  - Team name (e.g., 'Chiefs', 'Bills')")
        return

    # Display matching games
    sharp_books = settings.skills.market_analysis.sharp_books
    public_books = settings.skills.market_analysis.public_books

    print(f"Found {len(matching_games)} matching game(s):\n")
    print("=" * 80)

    for idx, (game_id, game_odds) in enumerate(matching_games):
        if idx > 0:
            print("\n" + "=" * 80)

        sample = game_odds[0]
        teams = sample["teams"]

        print(f"\n{teams['away']} @ {teams['home']}")
        print("-" * 80)

        # Get commence time
        commence = sample.get("commence_time", "Unknown")
        print(f"Kickoff: {commence}")
        print()

        # Collect sharp and public lines
        sharp_lines = []
        public_lines = []
        other_lines = []

        for odd in game_odds:
            book = odd["book"]
            spread = odd.get("markets", {}).get("spread", {})
            home_line = spread.get("home", {})

            if home_line.get("line") is not None:
                line_data = {
                    "book": book,
                    "line": home_line["line"],
                    "price": home_line.get("price", 0),
                }

                if book in sharp_books:
                    sharp_lines.append(line_data)
                elif book in public_books:
                    public_lines.append(line_data)
                else:
                    other_lines.append(line_data)

        # Display sharp books
        if sharp_lines:
            print("SHARP BOOKS:")
            for line in sharp_lines:
                print(
                    f"  {line['book']:<20} {line['line']:+6.1f} ({line['price']:+4d})"
                )
            avg_sharp = sum(l["line"] for l in sharp_lines) / len(sharp_lines)
            print(f"  {'SHARP CONSENSUS':<20} {avg_sharp:+6.1f}")
        else:
            print("SHARP BOOKS: No data (Pinnacle, Circa, Bookmaker not available)")

        print()

        # Display public books
        if public_lines:
            print("PUBLIC BOOKS:")
            for line in public_lines:
                print(
                    f"  {line['book']:<20} {line['line']:+6.1f} ({line['price']:+4d})"
                )
            avg_public = sum(l["line"] for l in public_lines) / len(public_lines)
            print(f"  {'PUBLIC CONSENSUS':<20} {avg_public:+6.1f}")
        else:
            print("PUBLIC BOOKS: Data available")

        print()

        # Show all other books
        if other_lines:
            print("OTHER BOOKS:")
            for line in other_lines[:5]:  # Show first 5
                print(
                    f"  {line['book']:<20} {line['line']:+6.1f} ({line['price']:+4d})"
                )
            if len(other_lines) > 5:
                print(f"  ... and {len(other_lines) - 5} more books")

        # Calculate and display divergence
        if sharp_lines and public_lines:
            divergence = avg_sharp - avg_public
            print()
            print("-" * 80)
            print("ANALYSIS:")
            print(f"  Sharp vs Public Divergence: {divergence:+.2f} points")

            if abs(divergence) < 0.3:
                print("  Status: Lines are aligned (no edge)")
            elif abs(divergence) < settings.skills.market_analysis.alert_threshold:
                print("  Status: Minor divergence (watch)")
            else:
                print("  Status: SIGNIFICANT DIVERGENCE! (alert threshold exceeded)")
                if divergence > 0:
                    print(f"  Indication: Sharp money may be on {teams['away']}")
                else:
                    print(f"  Indication: Sharp money may be on {teams['home']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_game.py <team_name>")
        print()
        print("Examples:")
        print("  python check_game.py Chiefs")
        print("  python check_game.py Buffalo")
        print("  python check_game.py Ravens")
        sys.exit(1)

    search_term = " ".join(sys.argv[1:])
    asyncio.run(check_game(search_term))
