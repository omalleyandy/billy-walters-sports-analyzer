Generate weekly betting card with Billy Walters recommendations.

Usage: /betting-card [week] [output_format]

Examples:
- /betting-card (current week, all formats)
- /betting-card 11 excel
- /betting-card 11 json
- /betting-card 11 terminal

This command will:
1. Run complete edge detection analysis
2. Filter to actionable plays (edge ≥1.5 points)
3. Rank plays by edge size and confidence
4. Calculate Kelly Criterion bet sizes
5. Generate formatted betting card
6. Export to Excel/JSON/terminal

Billy Walters Betting Card Format:

```
================================================================
BILLY WALTERS WEEKLY BETTING CARD
Week 11 - 2025 NFL Season
Generated: 2025-11-13 Wednesday 2:30 PM
================================================================

=== MAX BETS (7+ points edge, 77% win rate) ===
None this week

=== STRONG PLAYS (4-7 points edge, 64% win rate) ===
1. Kansas City Chiefs -2.5 (vs Buffalo Bills)
   Edge: 5.2 points
   Kelly %: 3.0% of bankroll
   Unit Size: 3.0 units
   Expected Value: +14.2%
   Confidence: VERY HIGH (92%)
   Key Factors:
     - Power rating advantage: +3.5 pts
     - Injury advantage: +1.5 pts (BUF missing CB1, WR1)
     - Sharp action: 62% money on KC (public 45%)
     - Key number: Currently off 3, line may move
   Line Shop: Best at -2.5 (Circa, MGM)
   Timing: Bet now before line moves to -3

=== MODERATE PLAYS (2-4 points edge, 58% win rate) ===
2. Philadelphia Eagles -7 (at Dallas Cowboys)
   Edge: 3.8 points
   Kelly %: 2.0% of bankroll
   Unit Size: 2.0 units
   Expected Value: +8.4%
   Confidence: HIGH (85%)

3. UNDER 44.5 (San Francisco vs Seattle)
   Edge: 2.5 points
   Kelly %: 1.5% of bankroll
   Unit Size: 1.5 units
   Expected Value: +5.2%
   Confidence: MODERATE (72%)

=== LEAN PLAYS (1-2 points edge, 54% win rate) ===
4. Green Bay Packers +3 (at Minnesota Vikings)
   Edge: 1.8 points
   Kelly %: 1.0% of bankroll
   Unit Size: 1.0 unit
   Expected Value: +3.1%

================================================================
BETTING CARD SUMMARY
================================================================
Total Recommended Plays: 4
  - MAX (7+ pts): 0
  - STRONG (4-7 pts): 1
  - MODERATE (2-4 pts): 2
  - LEAN (1-2 pts): 1

Total Capital Allocation: 7.5% of bankroll
Expected Portfolio Return: +7.8%
Risk-Adjusted Kelly: Conservative 50% of full Kelly

Key Numbers This Week:
  - 3 games landing on -3 or +3: EXTRA VALUABLE
  - 2 games landing on -7 or +7: MONITOR MOVEMENT

Sharp Action Indicators:
  - 3 games showing reverse line movement
  - 2 games with steam move (2+ point move in <1 hour)

Weather Impacts:
  - GB @ MIN: 28°F, 18 MPH wind → UNDER lean
  - BUF @ KC: Dome game → No adjustment

================================================================
BETTING STRATEGY NOTES
================================================================
1. Line Shopping: Check Circa, MGM, Pinnacle for best prices
2. Timing: Favorites early, dogs late (general rule)
3. Key Numbers: Don't buy through 3 or 7 unless discounted
4. Bankroll: Start week with 100 units, bet 7.5 units total
5. CLV Tracking: Record lines now, compare to closing lines Sunday

Billy Walters Rules Reminder:
- Only bet when edge ≥1.5 points
- Respect position sizing (Kelly Criterion)
- Shop lines at 3+ sportsbooks
- Track CLV (closing line value) not win/loss
- Discipline > Impulse

================================================================
```

Excel Export Columns:
- Game ID
- Teams (Home @ Away)
- Bet Recommendation
- Current Line
- Your Line
- Edge (points)
- Edge Type (Spread/Total)
- Bet Size (% / units)
- Expected Value (%)
- Confidence (%)
- Key Factors (comma-separated)
- Best Sportsbook
- Line Movement (last 24h)
- Sharp Action (Y/N)
- Weather Impact
- Status (PENDING/PLACED/WON/LOST)
- Actual Line (when placed)
- Closing Line (for CLV tracking)
- Result
- ROI

JSON Export:
```json
{
  "week": 11,
  "season": 2025,
  "generated_at": "2025-11-13T14:30:00",
  "plays": [
    {
      "rank": 1,
      "game_id": "BUF_KC_2025_W11",
      "teams": {
        "home": "Kansas City Chiefs",
        "away": "Buffalo Bills"
      },
      "recommendation": {
        "side": "Kansas City Chiefs",
        "line": -2.5,
        "type": "spread"
      },
      "edge": {
        "points": 5.2,
        "category": "STRONG",
        "your_line": -7.7,
        "market_line": -2.5
      },
      "sizing": {
        "kelly_percent": 3.0,
        "units": 3.0,
        "expected_value": 14.2
      },
      "confidence": {
        "level": "VERY_HIGH",
        "percent": 92
      },
      "factors": [
        "Power rating advantage: +3.5",
        "Injury advantage: +1.5",
        "Sharp action: 62% money"
      ],
      "line_shopping": {
        "best_book": "Circa",
        "best_line": -2.5,
        "juice": -110
      },
      "timing": "Bet now before line moves to -3"
    }
  ],
  "summary": {
    "total_plays": 4,
    "capital_allocation_percent": 7.5,
    "expected_portfolio_return": 7.8,
    "by_category": {
      "MAX": 0,
      "STRONG": 1,
      "MODERATE": 2,
      "LEAN": 1
    }
  }
}
```

Saved Locations:
- Excel: cards/billy_walters_week_11_2025.xlsx
- JSON: data/current/betting_card_week_11.json
- Terminal: Displayed in console

Integration:
- Runs after /edge-detector
- Auto-opens Excel file (Windows)
- Syncs with CLV tracking spreadsheet
- Sends summary to logs for review
