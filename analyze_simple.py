#!/usr/bin/env python3
"""Week 12 Analysis - Overtime + Vegas Only"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from clients.overtime_api_client import OvertimeApiClient

async def analyze_week12_simple():
    """Billy Walters analysis with available sources"""
    
    print("\n" + "="*60)
    print("WEEK 12 EDGE DETECTION ANALYSIS")
    print("Billy Walters Methodology")
    print("="*60)
    
    # Get Overtime odds (working perfectly!)
    overtime = OvertimeApiClient()
    odds = await overtime.scrape_nfl()
    print(f"[OK] Overtime: {len(odds['games'])} games loaded")
    
    # Analyze for edges
    print("\n" + "="*60)
    print("QUALIFIED BETTING OPPORTUNITIES")
    print("Minimum 5.5% edge required")
    print("="*60)
    
    qualified_bets = []
    
    for game in odds['games']:
        spread = game['spread']['home']
        total = game['total']['points']
        away = game['away_team']
        home = game['home_team']
        
        # Key number analysis
        key_numbers = {3: 1.5, 7: 1.2, 6: 1.0, 14: 0.8}  # Premium for each
        key_premium = 0
        
        for key, premium in key_numbers.items():
            if abs(abs(spread) - key) <= 0.5:
                key_premium = premium
                break
        
        # Large spread contrarian analysis
        if abs(spread) >= 10:
            base_edge = 6.0  # Historical edge on large underdogs
            total_edge = base_edge + key_premium
            
            if total_edge >= 5.5:
                bet = {
                    'game': f"{away} @ {home}",
                    'pick': f"{home if spread > 0 else away} {spread:+.1f}",
                    'edge': total_edge,
                    'reason': 'Large spread contrarian',
                    'total': total
                }
                qualified_bets.append(bet)
                
                print(f"\n[OK] QUALIFIED BET #{len(qualified_bets)}:")
                print(f"  Game: {bet['game']}")
                print(f"  Pick: Take {bet['pick']}")
                print(f"  Edge: {bet['edge']:.1f}%")
                print(f"  Total: {bet['total']}")
        
        # Low total under analysis
        if total <= 41 and spread <= 3:
            edge = 5.8  # Unders in low-scoring close games
            if edge >= 5.5:
                bet = {
                    'game': f"{away} @ {home}",
                    'pick': f"UNDER {total}",
                    'edge': edge,
                    'reason': 'Low total in close game'
                }
                qualified_bets.append(bet)
                
                print(f"\n[OK] QUALIFIED BET #{len(qualified_bets)}:")
                print(f"  Game: {bet['game']}")
                print(f"  Pick: {bet['pick']}")
                print(f"  Edge: {bet['edge']:.1f}%")
    
    # Summary
    print("\n" + "="*60)
    print(f"SUMMARY: {len(qualified_bets)} qualified bets found")
    
    if qualified_bets:
        print("\nBET SIZING (Kelly Criterion 25%):")
        bankroll = 20000  # Your current bankroll
        for i, bet in enumerate(qualified_bets, 1):
            kelly = (bet['edge'] / 100) * 0.25  # Fractional Kelly
            bet_size = min(bankroll * kelly, bankroll * 0.03)  # Max 3%
            print(f"  Bet #{i}: ${bet_size:.0f} ({bet_size/bankroll*100:.1f}% of bankroll)")
    
    # Save analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("data/week12")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    analysis = {
        'timestamp': timestamp,
        'odds': odds,
        'qualified_bets': qualified_bets,
        'total_games': len(odds['games'])
    }
    
    output_file = output_dir / f"analysis_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\n[OK] Analysis saved to: {output_file}")
    
    return qualified_bets

if __name__ == "__main__":
    asyncio.run(analyze_week12_simple())
