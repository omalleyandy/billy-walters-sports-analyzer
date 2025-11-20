#!/usr/bin/env python3
"""
Week 12 CLV Bet Tracker
Record all Week 12 bets for CLV tracking
"""

import sys
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from src.walters_analyzer.models.clv_tracking_module import CLVTracking
from src.walters_analyzer.utils.clv_storage import CLVStorage


def record_week12_bets():
    """Record all Week 12 recommended bets for CLV tracking"""
    
    storage = CLVStorage(Path("data") / "clv")
    
    print("\n" + "="*70)
    print("WEEK 12 CLV BET RECORDING")
    print("Recording recommended bets from Week 12 analysis")
    print("="*70 + "\n")
    
    # Week 12 bets from comprehensive analysis
    bets = [
        {
            'game_id': 'IND_KC',
            'away': 'Indianapolis Colts',
            'home': 'Kansas City Chiefs',
            'bet_type': 'spread',
            'side': 'away',
            'opening_line': 3.5,  # IND +3.5
            'edge': 8.2,
            'stake': 500,
            'confidence': 'HIGH',
            'rec_id': 'WEEK12_IND_KC'
        },
        {
            'game_id': 'LAR_TB',
            'away': 'Los Angeles Rams',
            'home': 'Tampa Bay Buccaneers',
            'bet_type': 'spread',
            'side': 'away',
            'opening_line': -6.5,  # LAR -6.5
            'edge': 6.8,
            'stake': 400,
            'confidence': 'MEDIUM-HIGH',
            'rec_id': 'WEEK12_LAR_TB'
        },
        {
            'game_id': 'CIN_NE',
            'away': 'New England Patriots',
            'home': 'Cincinnati Bengals',
            'bet_type': 'spread',
            'side': 'home',
            'opening_line': 7.0,  # CIN +7.0 (NE -7.0)
            'edge': 5.9,
            'stake': 300,
            'confidence': 'MEDIUM',
            'rec_id': 'WEEK12_CIN_NE'
        },
        {
            'game_id': 'SEA_TEN',
            'away': 'Seattle Seahawks',
            'home': 'Tennessee Titans',
            'bet_type': 'spread',
            'side': 'away',
            'opening_line': -13.5,  # SEA -13.5
            'edge': 6.0,
            'stake': 300,
            'confidence': 'MEDIUM',
            'rec_id': 'WEEK12_SEA_TEN'
        }
    ]
    
    print(f"Recording {len(bets)} bets...\n")
    
    bankroll = 20000  # Standard bankroll
    
    for i, bet in enumerate(bets, 1):
        # Calculate stake fraction
        stake_fraction = bet['stake'] / bankroll
        
        # Create CLV tracking record
        tracking = CLVTracking(
            recommendation_id=bet['rec_id'],
            game_id=bet['game_id'],
            opening_line=bet['opening_line'],
            bet_side=bet['side'],
            bet_type=bet['bet_type'],
            edge_percentage=bet['edge'],
            bankroll=bankroll,
            stake_fraction=stake_fraction,
            notes=f"{bet['away']} @ {bet['home']} | Edge: {bet['edge']}% | Confidence: {bet['confidence']}"
        )
        
        # Save to storage
        storage.save_bet(tracking)
        
        # Display confirmation
        side_name = bet['away'] if bet['side'] == 'away' else bet['home']
        line_display = f"{side_name} {bet['opening_line']:+.1f}"
        
        print(f"[{i}] RECORDED: {bet['game_id']}")
        print(f"    Pick: {line_display}")
        print(f"    Edge: {bet['edge']:.1f}%")
        print(f"    Stake: ${bet['stake']} ({stake_fraction*100:.1f}% of bankroll)")
        print(f"    ID: {bet['rec_id']}")
        print()
    
    # Show summary
    print("="*70)
    print("RECORDING COMPLETE")
    print("="*70)
    total_exposure = sum(b['stake'] for b in bets)
    avg_edge = sum(b['edge'] for b in bets) / len(bets)
    
    print(f"Total Bets: {len(bets)}")
    print(f"Total Exposure: ${total_exposure} ({total_exposure/bankroll*100:.1f}% of ${bankroll})")
    print(f"Average Edge: {avg_edge:.1f}%")
    print()
    
    # Show next steps
    print("NEXT STEPS:")
    print("1. Start line monitoring:")
    print("   python week12_line_monitor.py --interval 300")
    print()
    print("2. When lines close (game time), update closing lines:")
    print("   python week12_clv_updater.py update-closing")
    print()
    print("3. After games finish, update results:")
    print("   python week12_clv_updater.py update-results")
    print()
    print("4. View CLV summary:")
    print("   python week12_clv_updater.py summary")
    print()


if __name__ == "__main__":
    try:
        record_week12_bets()
    except Exception as e:
        print(f"\n[ERROR] Failed to record bets: {e}")
        import traceback
        traceback.print_exc()
