#!/usr/bin/env python3
"""
Complete odds scraper using Chrome DevTools MCP
Bypasses Cloudflare and extracts all NFL betting odds from overtime.ag
"""

import json
from pathlib import Path
from datetime import datetime

from walters_analyzer.ingest.chrome_devtools_scraper import ChromeDevToolsOddsExtractor


# NOTE: This script requires MCP chrome-devtools to be running
# It will be called by the agent which has access to the MCP tools
# For manual use, you'll need to:
# 1. Start Chrome DevTools MCP server
# 2. Navigate to overtime.ag/sports/
# 3. Take snapshot
# 4. Pass snapshot to this script


def scrape_all_nfl_odds(snapshot_file: str = None) -> list[dict]:
    """
    Scrape all NFL odds from Chrome DevTools snapshot
    
    Args:
        snapshot_file: Path to saved snapshot file (optional)
        
    Returns:
        List of games in Billy Walters format
    """
    # If snapshot file provided, read it
    if snapshot_file:
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot_text = f.read()
    else:
        # This will be filled by agent with MCP snapshot
        raise ValueError("snapshot_file required. Use agent execution for live scraping.")
    
    extractor = ChromeDevToolsOddsExtractor()
    games = extractor.extract_games_from_snapshot(snapshot_text)
    
    return games


def save_games(games: list[dict], output_dir: str = None, sport: str = "nfl"):
    """
    Save extracted games in multiple formats
    
    Args:
        games: List of game dicts
        output_dir: Custom output directory (optional)
        sport: "nfl" or "ncaaf" for default directory selection
    """
    if output_dir is None:
        output_dir = f"data/odds/{sport}"
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Save as JSONL (one game per line)
    jsonl_file = output_path / f"nfl-odds-{timestamp}.jsonl"
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for game in games:
            f.write(json.dumps(game) + '\n')
    
    # Save as pretty JSON for review
    json_file = output_path / f"nfl-odds-{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent=2)
    
    # Save as CSV (flattened)
    csv_file = output_path / f"nfl-odds-{timestamp}.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        # CSV header
        headers = [
            "source", "sport", "league", "collected_at", "game_key",
            "rotation_number", "event_date", "event_time",
            "away_team", "home_team",
            "away_spread_line", "away_spread_price",
            "home_spread_line", "home_spread_price",
            "over_line", "over_price",
            "under_line", "under_price",
            "away_moneyline", "home_moneyline"
        ]
        f.write(','.join(headers) + '\n')
        
        # CSV rows
        for game in games:
            teams = game.get('teams', {})
            markets = game.get('markets', {})
            spread = markets.get('spread', {})
            total = markets.get('total', {})
            ml = markets.get('moneyline', {})
            
            row = [
                game.get('source', ''),
                game.get('sport', ''),
                game.get('league', ''),
                game.get('collected_at', ''),
                game.get('game_key', ''),
                game.get('rotation_number', ''),
                game.get('event_date', ''),
                game.get('event_time', ''),
                teams.get('away', ''),
                teams.get('home', ''),
                spread.get('away', {}).get('line', '') if spread.get('away') else '',
                spread.get('away', {}).get('price', '') if spread.get('away') else '',
                spread.get('home', {}).get('line', '') if spread.get('home') else '',
                spread.get('home', {}).get('price', '') if spread.get('home') else '',
                total.get('over', {}).get('line', '') if total.get('over') else '',
                total.get('over', {}).get('price', '') if total.get('over') else '',
                total.get('under', {}).get('line', '') if total.get('under') else '',
                total.get('under', {}).get('price', '') if total.get('under') else '',
                ml.get('away', {}).get('price', '') if ml.get('away') else '',
                ml.get('home', {}).get('price', '') if ml.get('home') else '',
            ]
            f.write(','.join(str(v) for v in row) + '\n')
    
    print(f"\n[SUCCESS] Saved {len(games)} games to:")
    print(f"  - JSONL: {jsonl_file.name}")
    print(f"  - JSON:  {json_file.name}")
    print(f"  - CSV:   {csv_file.name}")
    
    return jsonl_file, json_file, csv_file


def display_summary(games: list[dict]):
    """Display summary of scraped games"""
    print("\n" + "=" * 80)
    print(f"  NFL ODDS SCRAPING SUMMARY - {len(games)} GAMES")
    print("=" * 80)
    
    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    for game in games:
        date = game.get('event_date', 'Unknown')
        by_date[date].append(game)
    
    for date in sorted(by_date.keys()):
        games_on_date = by_date[date]
        print(f"\n{date} ({len(games_on_date)} games):")
        
        for game in games_on_date:
            teams = game['teams']
            rot = game['rotation_number']
            time = game.get('event_time', '')
            
            print(f"  {rot} | {time:15} | {teams['away']:25} @ {teams['home']}")
            
            # Show spreads
            spread = game['markets']['spread']
            if spread.get('away') and spread.get('home'):
                away_line = spread['away'].get('line')
                home_line = spread['home'].get('line')
                print(f"       | {'':15} | Spread: {away_line:+5.1f} / {home_line:+5.1f}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Read from snapshot file
        snapshot_file = sys.argv[1]
        print(f"Loading snapshot from: {snapshot_file}")
        
        games = scrape_all_nfl_odds(snapshot_file)
        
        if games:
            save_games(games)
            display_summary(games)
        else:
            print("ERROR: No games extracted from snapshot", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python scrape_odds_mcp.py <snapshot_file>", file=sys.stderr)
        print("  or run via agent with MCP chrome-devtools", file=sys.stderr)
        sys.exit(1)

