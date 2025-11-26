#!/usr/bin/env python3
"""
Quick command to scrape Action Network odds.

Usage:
    python collect_action_network.py           # Single NFL scrape
    python collect_action_network.py --status  # Check status
    python collect_action_network.py --watch   # Continuous monitoring
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walters_analyzer.scrapers.action_network_collector import ActionNetworkCollector


async def main():
    if '--status' in sys.argv:
        collector = ActionNetworkCollector()
        status = collector.get_status()
        
        print("\n🎰 ACTION NETWORK COLLECTOR STATUS")
        print("=" * 50)
        print(f"Last Scrape: {status['last_scrape'] or 'Never'}")
        print(f"Total Scrapes: {status['scrape_count']}")
        print(f"Data Files: {status['data_files']}")
        
        if status['latest_data']:
            print("\n📊 Latest Data:")
            for league, data in status['latest_data'].items():
                print(f"  {league.upper()}: {data['game_count']} games, {data['sharp_plays']} sharp plays")
        return
    
    if '--watch' in sys.argv:
        print("🔄 Starting continuous monitoring (Ctrl+C to stop)...")
        collector = ActionNetworkCollector(interval_minutes=60)  # Every hour
        await collector.run_continuous()
        return
    
    # Default: single scrape
    print("\n🎰 SCRAPING ACTION NETWORK ODDS...")
    print("=" * 50)
    
    collector = ActionNetworkCollector()
    result = await collector.run_once()
    
    if result['success']:
        print("\n✅ SCRAPE SUCCESSFUL!")
        for league, data in result['results'].items():
            if data['success']:
                print(f"\n{league.upper()}:")
                print(f"  Games: {data['game_count']}")
                print(f"  Sharp Plays: {data['sharp_plays']}")
                
                # Show sharp plays if any
                if data['sharp_plays'] > 0:
                    # Load the file to show plays
                    import json
                    latest_file = Path(data['filepath']).parent / f'{league}_odds_latest.json'
                    if latest_file.exists():
                        with open(latest_file) as f:
                            odds_data = json.load(f)
                        print("\n🎯 SHARP MONEY SIGNALS:")
                        for play in odds_data.get('sharp_plays', [])[:5]:
                            print(f"  • {play['game']}: {play['pick']} ({play['divergence']:+d} div)")
    else:
        print(f"\n❌ Scrape failed: {result.get('error')}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
