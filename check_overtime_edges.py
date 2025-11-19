"""
Overtime.ag Edge Verification Tool
Use this Wednesday mornings to verify edges before betting

INSTRUCTIONS:
1. Go to overtime.ag/sports#/nfl at 6:00 AM Wednesday
2. Find each game and note the spread
3. Fill in the "overtime_line" values below
4. Run: python check_overtime_edges.py
5. Only bet if edge >= 5.5%
"""

from billy_walters_edge_calculator import BillyWaltersEdgeCalculator
from datetime import datetime

# Initialize calculator
calc = BillyWaltersEdgeCalculator()

# Your current bankroll
BANKROLL = 20000.0

print("=" * 80)
print("OVERTIME.AG EDGE VERIFICATION - NFL WEEK 12")
print(f"Date: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
print(f"Bankroll: ${BANKROLL:,.0f}")
print("=" * 80)

# =============================================================================
# WEEK 12 GAMES - FILL IN OVERTIME.AG LINES BELOW
# =============================================================================

games = {
    "IND @ KC": {
        "our_line": 0.5,              # Our power rating: IND slight underdog
        "overtime_line": None,         # [*] FILL THIS IN WEDNESDAY!
        "sfactor_points": 11.25,       # IND bye week (+7.5) + motivation (+3.75)
        "game_time": "Sunday 1:00 PM ET",
        "notes": "Colts coming off bye, playoff push",
        "expected_line": "IND +3.5 to +4.0",
        "priority": "HIGH",
        "bet_timing": "Wednesday 6:00-7:00 AM PT"
    },
    
    "LAR @ TB": {
        "our_line": -3.0,             # Our power rating: LAR favorite by 3
        "overtime_line": None,         # [*] FILL THIS IN WEDNESDAY!
        "sfactor_points": 7.5,         # Revenge game (+3.75) + TB travel (+3.75)
        "game_time": "Sunday 8:20 PM ET (SNF)",
        "notes": "Rams revenge for playoff loss",
        "expected_line": "LAR -6.5",
        "priority": "HIGH",
        "bet_timing": "Wednesday 6:00-7:00 AM PT"
    },
    
    "CIN vs NE": {
        "our_line": -4.5,             # Our power rating: CIN favorite by 4.5
        "overtime_line": None,         # [*] FILL THIS IN WEDNESDAY!
        "sfactor_points": 5.0,         # Home field advantage
        "game_time": "Sunday 1:00 PM ET",
        "notes": "[WARNING] CONDITIONAL - Only if Ja'Marr Chase OUT",
        "expected_line": "CIN -6.0 to -7.0",
        "priority": "CONDITIONAL",
        "bet_timing": "Wednesday-Thursday (monitor Chase injury)"
    },
    
    "BUF @ HOU": {
        "our_line": -8.0,             # Our power rating: BUF big favorite
        "overtime_line": None,         # [*] FILL THIS IN THURSDAY!
        "sfactor_points": 3.75,        # BUF motivation
        "game_time": "Thursday 8:15 PM ET (TNF)",
        "notes": "[WARNING] CONDITIONAL - Only if C.J. Stroud OUT",
        "expected_line": "BUF -4.5 to -5.0",
        "priority": "CONDITIONAL",
        "bet_timing": "Thursday 4:00 AM PT (check Stroud status)"
    },
    
    "GB vs MIN": {
        "our_line": -0.5,             # Our power rating: GB slight favorite
        "overtime_line": None,         # [*] FILL THIS IN SATURDAY!
        "sfactor_points": 3.75,        # Home field
        "game_time": "Sunday 1:00 PM ET",
        "notes": "[WARNING] CONDITIONAL - Only if Josh Jacobs PLAYS",
        "expected_line": "GB -2.5",
        "priority": "CONDITIONAL",
        "bet_timing": "Saturday (check Jacobs status)"
    },
}

# =============================================================================
# EDGE CALCULATION AND RECOMMENDATIONS
# =============================================================================

print("\n" + "=" * 80)
print("EDGE ANALYSIS")
print("=" * 80)

qualified_bets = []
waiting_for_lines = []
rejected_bets = []

for game_name, data in games.items():
    print(f"\n{'='*80}")
    print(f"[NFL] {game_name}")
    print(f"{'='*80}")
    print(f"[*] Game Time: {data['game_time']}")
    print(f"[NOTE] Notes: {data['notes']}")
    print(f"[TIME] Bet Timing: {data['bet_timing']}")
    print(f"[TARGET] Priority: {data['priority']}")
    print(f"\n[CHART] ANALYSIS:")
    print(f"   Our Line: {data['our_line']:+.1f}")
    print(f"   Expected Overtime Line: {data['expected_line']}")
    
    if data["overtime_line"] is None:
        print(f"\n⏳ STATUS: WAITING FOR OVERTIME.AG LINE")
        print(f"   [*] Go to overtime.ag/sports#/nfl")
        print(f"   [*] Find {game_name}")
        print(f"   [*] Fill in overtime_line value in this script")
        waiting_for_lines.append(game_name)
        continue
    
    # Calculate edge with actual Overtime line
    result = calc.calculate_complete_edge(
        our_line=data['our_line'],
        market_line=data['overtime_line'],
        sfactor_points=data['sfactor_points']
    )
    
    print(f"   Actual Overtime Line: {data['overtime_line']:+.1f}")
    print(f"\n[INFO] EDGE BREAKDOWN:")
    print(f"   Base Edge: {result.base_edge_points:.1f} points")
    print(f"   S-Factor Adjustment: +{result.sfactor_adjustment_points:.2f} points")
    print(f"   Key Numbers Crossed: {result.crossed_key_numbers}")
    print(f"   Key Number Premium: +{result.key_number_premium_pct:.1f}%")
    print(f"\n[TARGET] TOTAL EDGE: {result.total_edge_pct:.1f}%")
    print(f"   Confidence: {result.confidence_level}")
    print(f"   [STAR] Star Rating: {result.star_rating}")
    
    # Calculate bet size
    bet_amount = result.recommended_bet_pct * BANKROLL
    bet_pct = result.recommended_bet_pct * 100
    
    # Decision logic
    print(f"\n[MONEY] BET SIZING:")
    print(f"   Recommended: ${bet_amount:.0f} ({bet_pct:.1f}% of bankroll)")
    print(f"   Risk: {bet_pct:.1f}% of ${BANKROLL:,.0f}")
    
    # Warnings
    if result.warnings:
        print(f"\n[WARNING]  WARNINGS:")
        for warning in result.warnings:
            print(f"   {warning}")
    
    # Final recommendation
    print(f"\n{'='*80}")
    if result.total_edge_pct >= 5.5 and result.star_rating > 0:
        print(f"[*] RECOMMENDATION: BET ${bet_amount:.0f}")
        print(f"{'='*80}")
        qualified_bets.append({
            'game': game_name,
            'amount': bet_amount,
            'edge': result.total_edge_pct,
            'stars': result.star_rating,
            'priority': data['priority']
        })
    else:
        print(f"[ERROR] RECOMMENDATION: NO BET (Edge below 5.5% minimum)")
        print(f"{'='*80}")
        rejected_bets.append({
            'game': game_name,
            'edge': result.total_edge_pct,
            'reason': 'Below minimum edge'
        })

# =============================================================================
# SUMMARY AND ACTION ITEMS
# =============================================================================

print("\n\n" + "=" * 80)
print("[LIST] BETTING SUMMARY")
print("=" * 80)

if waiting_for_lines:
    print(f"\n⏳ WAITING FOR LINES ({len(waiting_for_lines)} games):")
    for game in waiting_for_lines:
        print(f"   • {game}")
    print(f"\n   [*] Fill in overtime_line values and re-run this script")

if qualified_bets:
    print(f"\n[*] QUALIFIED BETS ({len(qualified_bets)} games):")
    total_risk = 0
    
    # Sort by priority (HIGH first, then CONDITIONAL)
    qualified_bets.sort(key=lambda x: (x['priority'] != 'HIGH', -x['edge']))
    
    for bet in qualified_bets:
        print(f"\n   [TARGET] {bet['game']}")
        print(f"      Amount: ${bet['amount']:.0f}")
        print(f"      Edge: {bet['edge']:.1f}%")
        print(f"      Stars: {bet['stars']} [STAR]")
        print(f"      Priority: {bet['priority']}")
        total_risk += bet['amount']
    
    print(f"\n{'='*80}")
    print(f"[MONEY] TOTAL RISK: ${total_risk:.0f} ({total_risk/BANKROLL*100:.1f}% of bankroll)")
    
    if total_risk / BANKROLL <= 0.15:
        print(f"[*] Within 15% weekly limit")
    else:
        print(f"[WARNING]  EXCEEDS 15% weekly limit - reduce bet sizes!")
    
    print(f"\n[NOTE] NEXT STEPS:")
    print(f"   1. Screenshot this output for records")
    print(f"   2. Go to overtime.ag/sports#/nfl")
    print(f"   3. Place bets in priority order (HIGH first)")
    print(f"   4. Verify lines haven't moved significantly")
    print(f"   5. Take confirmation screenshots")

if rejected_bets:
    print(f"\n[ERROR] REJECTED BETS ({len(rejected_bets)} games):")
    for bet in rejected_bets:
        print(f"   • {bet['game']}: Edge = {bet['edge']:.1f}% ({bet['reason']})")

if not qualified_bets and not waiting_for_lines:
    print(f"\n[WARNING]  NO QUALIFIED BETS THIS WEEK")
    print(f"   • All games below 5.5% minimum edge")
    print(f"   • Better to wait than force bets")
    print(f"   • Billy Walters: 'If you don't run out of money, you won't run out of things to bet on'")

print("\n" + "=" * 80)
print("[WARNING]  REMEMBER: Only bet if edge >= 5.5% AND all conditionals met!")
print("=" * 80)
print(f"\nScript completed at {datetime.now().strftime('%I:%M %p')}")
print("Good luck! [NFL][MONEY]\n")
