#!/usr/bin/env python3
"""
Display current odds for NFL games being monitored
"""
import asyncio
import sys
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass  # Already wrapped or not applicable

from walters_analyzer.feeds.market_data_client import OddsAPIClient
from walters_analyzer.config import get_settings

async def show_current_odds():
    """Fetch and display current NFL odds"""
    settings = get_settings()
    client = OddsAPIClient()

    print("Fetching current NFL odds...")
    odds = await client.get_odds('americanfootball_nfl')

    if not odds:
        print('No odds data available')
        return

    # Group by game
    games = defaultdict(list)
    for odd in odds:
        games[odd['game_id']].append(odd)

    print()
    print('=' * 80)
    print(f'CURRENT NFL ODDS - {len(games)} GAMES MONITORED')
    print('=' * 80)
    print()

    # Get sharp and public books from settings
    sharp_books = settings.skills.market_analysis.sharp_books
    public_books = settings.skills.market_analysis.public_books

    # Show first 5 games with detailed odds
    for i, (game_id, game_odds) in enumerate(list(games.items())[:5]):
        if i > 0:
            print()

        sample = game_odds[0]
        teams = sample['teams']

        print(f"{i+1}. {teams['away']} @ {teams['home']}")
        print('-' * 80)

        # Collect sharp book lines
        sharp_lines = []
        for odd in game_odds:
            book = odd['book']
            if book in sharp_books:
                spread = odd.get('markets', {}).get('spread', {})
                home_line = spread.get('home', {})
                if home_line.get('line') is not None:
                    sharp_lines.append({
                        'book': book,
                        'line': home_line['line'],
                        'price': home_line.get('price', 0)
                    })

        # Collect public book lines
        public_lines = []
        for odd in game_odds:
            book = odd['book']
            if book in public_books:
                spread = odd.get('markets', {}).get('spread', {})
                home_line = spread.get('home', {})
                if home_line.get('line') is not None:
                    public_lines.append({
                        'book': book,
                        'line': home_line['line'],
                        'price': home_line.get('price', 0)
                    })

        # Display sharp books
        if sharp_lines:
            print('SHARP BOOKS:')
            for line in sharp_lines:
                print(f"  {line['book']:<15} {line['line']:+6.1f} ({line['price']:+4d})")

            # Calculate average
            avg_sharp = sum(l['line'] for l in sharp_lines) / len(sharp_lines)
            print(f"  {'AVERAGE':<15} {avg_sharp:+6.1f}")
        else:
            print('SHARP BOOKS: No data available')

        print()

        # Display public books
        if public_lines:
            print('PUBLIC BOOKS:')
            for line in public_lines:
                print(f"  {line['book']:<15} {line['line']:+6.1f} ({line['price']:+4d})")

            # Calculate average
            avg_public = sum(l['line'] for l in public_lines) / len(public_lines)
            print(f"  {'AVERAGE':<15} {avg_public:+6.1f}")
        else:
            print('PUBLIC BOOKS: No data available')

        # Show divergence if both exist
        if sharp_lines and public_lines:
            divergence = avg_sharp - avg_public
            if abs(divergence) >= 0.5:
                print()
                print(f"  DIVERGENCE: {divergence:+.1f} points")
                if abs(divergence) >= settings.skills.market_analysis.alert_threshold:
                    print(f"  STATUS: ALERT THRESHOLD REACHED!")

    print()
    print('=' * 80)
    print(f'Showing 5 of {len(games)} games. All {len(games)} games are being monitored.')
    print(f'Alert threshold: {settings.skills.market_analysis.alert_threshold} points')
    print('=' * 80)

if __name__ == '__main__':
    asyncio.run(show_current_odds())
