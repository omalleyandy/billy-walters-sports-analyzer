Run Billy Walters edge detection analysis to identify betting value.

Usage: /edge-detector [game_id] [type]

Examples:
- /edge-detector (all games, spreads and totals)
- /edge-detector BUF_KC spread
- /edge-detector all totals
- /edge-detector 11 (week 11, all games)

This command will:
1. Load current power ratings
2. Calculate predicted spread/total for each game
3. Compare predictions to market lines
4. Identify edges (your line vs market line)
5. Apply Billy Walters betting thresholds
6. Generate betting recommendations with confidence

Billy Walters Edge Detection Process:

Step 1: Calculate Your Line
- Power Rating Differential + Home Field Advantage + Adjustments
- Example: KC (92) vs BUF (90) at KC
- Base spread: 92 - 90 = 2 points
- HFA (KC Arrowhead): +2.5 points
- Your line: KC -4.5

Step 2: Apply Contextual Adjustments
- Injuries: Position-specific point values
- Weather: Wind/temp/precip impact
- Rest advantage: Bye week, Thursday night
- Divisional game: +0.5 intensity factor
- Revenge game: Motivational edge

Step 3: Compare to Market
- Your line: KC -4.5
- Market line: KC -2.5
- Edge: 2 points (favors KC)

Step 4: Billy Walters Betting Thresholds
- 7+ points: MAX BET (5% Kelly, 77% win rate historical)
- 4-7 points: STRONG (3% Kelly, 64% win rate)
- 2-4 points: MODERATE (2% Kelly, 58% win rate)
- 1-2 points: LEAN (1% Kelly, 54% win rate)
- <1 point: NO PLAY (52% win rate, not profitable)

Step 5: Key Number Analysis
- Landing on 3 or 7: +8% or +6% value
- Buying half point onto 3 or 7: Only at right price
- Key numbers: 3, 7, 6, 10, 14 (in order of importance)

Edge Types Detected:

1. Spread Edges
- Favorite undervalued by market
- Underdog overvalued
- Key number proximity

2. Total Edges
- Weather-adjusted over/under
- Injury-adjusted scoring
- Pace of play mismatch

3. Market Inefficiencies
- Public overreaction (sharp fade)
- Injury underpriced
- Weather not factored
- Line movement against public

Output Includes:
- All games with calculated edges
- Edge size (points)
- Betting recommendation (MAX/STRONG/MODERATE/LEAN/NO PLAY)
- Confidence level (0-100%)
- Kelly Criterion bet size (% of bankroll)
- Expected value (%)
- Historical win rate for this edge size
- Key factors driving the edge
- Sharp action indicators
- Line movement analysis

Billy Walters Rules:
1. Only bet when edge ≥1.5 points (54%+ win rate)
2. Size bets according to edge (Kelly Criterion)
3. Respect key numbers (3 and 7)
4. Shop for best line (every half point matters)
5. Track Closing Line Value (CLV) as success metric

Report Format:
```
BILLY WALTERS EDGE DETECTION REPORT
Week 11 - 2025 NFL Season
Generated: 2025-11-13 14:30:00

=== STRONG PLAYS (4-7 points edge) ===
Game: KC vs BUF
Your Line: KC -4.5
Market Line: KC -2.5
Edge: 2.0 points (favors KC)
Recommendation: MODERATE PLAY
Kelly %: 2.0% of bankroll
Expected Value: +5.8%
Historical Win Rate: 58%
Key Factors:
  - Injury advantage: KC +1.5 pts (BUF missing CB1, WR1)
  - Weather neutral: Indoor stadium
  - Sharp action: 45% public, 62% money (sharp on KC)
  - Line movement: Opened KC -3.0, moved to -2.5 (fade public)
Confidence: HIGH (85%)

[Additional games...]
```

Integration:
- Automatically runs after /collect-all-data
- Saves results to data/current/edge_detection_week_N.json
- Exports Excel report with betting card
- Logs to CLV tracking spreadsheet
