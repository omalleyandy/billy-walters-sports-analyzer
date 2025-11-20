#!/usr/bin/env python3
import asyncio, argparse, json, sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config_manager import get_config
    from logging_framework import get_logger
    from unified_betting_system_production import UnifiedBettingSystem
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print(f"[ERROR] Script location: {Path(__file__).parent}")
    sys.exit(1)

logger = get_logger("analyze_command")

async def analyze_edges(sport='all', min_edge=2.5, week=None, bankroll=None):
    print("\n" + "="*70)
    print("  ANALYZING BETTING EDGES")
    print("="*70)
    print(f"  Sport: {sport.upper()} | Min Edge: {min_edge}")
    if week: print(f"  Week: {week}")
    if bankroll: print(f"  Bankroll: ${bankroll:,.2f}")
    print("="*70 + "\n")
    
    try:
        config = get_config()
        if bankroll: config.betting.bankroll = bankroll
        system = UnifiedBettingSystem(config)
        
        print("[*] Collecting live data...")
        vegas_data, massey_data = await system.collect_all_data()
        
        print("[*] Analyzing for edges...")
        opportunities = system.find_edges(vegas_data, massey_data)
        
        print(f"\n[OK] Analysis complete: Found {len(opportunities)} opportunities\n")
        
        if opportunities:
            print("TOP OPPORTUNITIES:")
            print("-" * 70)
            for i, opp in enumerate(opportunities[:10], 1):
                print(f"\n  {i}. {opp.away_team} @ {opp.home_team}")
                print(f"     Bet: {opp.recommendation.upper()} {opp.bet_type.upper()}")
                print(f"     Edge: {opp.edge:+.1f} ({opp.edge_percentage:.1f}%)")
                print(f"     Size: {opp.kelly_size:.2%} of bankroll")
            
            output_file = Path("betting_data") / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_file.parent.mkdir(exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump({'timestamp': datetime.now().isoformat(), 'opportunities': len(opportunities), 'sport': sport}, f, indent=2)
            print(f"\n[OK] Analysis saved to: {output_file}")
        else:
            print("[!] No opportunities found with current criteria")
        return opportunities
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    parser = argparse.ArgumentParser(description='Analyze betting edges')
    parser.add_argument('--sport', default='all', choices=['all', 'nfl', 'cfb', 'nba'])
    parser.add_argument('--min-edge', type=float, default=2.5)
    parser.add_argument('--week', type=int)
    parser.add_argument('--bankroll', type=float)
    args = parser.parse_args()
    opportunities = asyncio.run(analyze_edges(args.sport, args.min_edge, args.week, args.bankroll))
    sys.exit(0 if opportunities else 1)

if __name__ == "__main__":
    main()
