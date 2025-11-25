Run Billy Walters edge detection analysis for NFL and NCAAF to identify betting value with automatic pre-flight validation.

Usage: /edge-detector [options]

Examples:
- /edge-detector (both NFL and NCAAF, auto-detect weeks)
- /edge-detector --league nfl (NFL only)
- /edge-detector --league ncaaf (NCAAF only)
- /edge-detector --league nfl --week 11 (NFL week 11)
- /edge-detector --league ncaaf --week 13 (NCAAF week 13)
- /edge-detector BUF_KC spread (specific NFL game)

**Pre-Flight Validation (Automatic)** ✨ NEW
Before edge detection begins, automatic validation ensures:
- ✅ Power ratings exist (foundation required)
- ✅ Game schedule present for detected/specified week
- ✅ Odds data available (Overtime.ag)
- ✅ All required data sources collected
- ✅ Exit code 0 = Safe to proceed with analysis
- ❌ Exit code 1 = Missing required data, analysis halted with details

If validation fails, detailed error shows which data is missing and how to fix it.

This command will:
1. Load current power ratings (NFL 70-100 scale, NCAAF 60-105 scale)
2. Calculate predicted spread/total for each game (league-specific)
3. Compare predictions to market lines
4. Identify edges (your line vs market line)
5. Apply Billy Walters betting thresholds (same thresholds, league-specific edges)
6. Generate betting recommendations with confidence
7. Apply league-specific situational factors
8. Calculate position-specific injury impacts

Billy Walters Edge Detection Process:

Step 1: Calculate Your Line
- Power Rating Differential + Home Field Advantage + Adjustments
- Example: KC (92) vs BUF (90) at KC
- Base spread: 92 - 90 = 2 points
- HFA (KC Arrowhead): +2.5 points
- Your line: KC -4.5

Step 2: Apply Contextual Adjustments
- Injuries: Position-specific point values (0.0 for Questionable, full value for OUT)
- Weather: Wind/temp/precip impact (FIXED 2025-11-12 - now fetching real data)
  - Uses AccuWeather API for outdoor stadiums
  - Indoor stadiums correctly return None (no adjustment)
  - Example: Cleveland 19.6 MPH wind → -0.2 total, -0.1 spread
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


NCAAF Edge Detection (NEW - 2025-11-23)
- Power rating scale: 60-105 (vs NFL 70-100)
- Home field advantage: +3.5 pts (vs NFL +3.0)
- QB injury impact: 5.0 pts (vs NFL 4.5)
- RB injury impact: 3.5 pts (vs NFL 2.5)
- Weather thresholds: Larger than NFL (6.0 for high wind vs 5.0)
- Situational factors: 30+ rivalries, conference games, playoff implications
- Position-specific injury values: 8 positions with depth-based values
- Output: output/edge_detection/ncaaf_edges_detected_week_N.jsonl

NFL vs NCAAF Adjustments:
- Roster depth: NCAAF has lower depth, backups worse quality
- Conference strength: More variation in NCAAF
- Travel impacts: Higher for NCAAF due to student-athlete restrictions
- Bowl eligibility: Drives emotional plays in NCAAF
- Transfer portal: Affects team composition in NCAAF

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
  - Weather neutral: Indoor stadium (Arrowhead is outdoor, but conditions good)
  - Weather data: Real-time from AccuWeather API (temp, wind, precip)
  - Sharp action: 45% public, 62% money (sharp on KC)
  - Line movement: Opened KC -3.0, moved to -2.5 (fade public)
Confidence: HIGH (85%)

[Additional games...]
```

Manual Pre-Flight Check:
If you want to verify required data before running edge detection:
```bash
python .claude/hooks/pre_edge_detection.py
```
This shows which data is available and ready for analysis.

Integration:
- Can run automatically after /collect-all-data (if post-flight validation passes)
- Runs pre-flight validation automatically before analysis begins
- Saves results to output/edge_detection/nfl_edges_detected_week_N.jsonl
- Exports markdown report with betting recommendations
- Logs performance to tracking database for CLV calculation
