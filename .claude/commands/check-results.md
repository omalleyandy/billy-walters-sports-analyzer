# Check Results - Automated Betting Performance Tracking

Check actual game results and calculate betting performance for predictions made.

## Usage

```bash
/check-results [date] [sport] [league]
```

## Parameters

- **date** (optional): Date in YYYYMMDD format (default: today)
- **sport** (optional): `football` or `basketball` (default: football)
- **league** (optional): `nfl`, `ncaaf`, `nba`, `ncaab` (default: nfl)

## Examples

```bash
# Check today's NFL results
/check-results

# Check specific date NCAAF results
/check-results 20251112 football ncaaf

# Check yesterday's results
/check-results 20251111 football nfl
```

## What This Command Does

1. **Load Predictions** - Finds prediction file for specified date/league
2. **Fetch Actual Scores** - Gets final scores from ESPN API
3. **Calculate Performance:**
   - Against The Spread (ATS) record
   - Totals accuracy (Over/Under)
   - Straight-up winner predictions
   - Margin of victory accuracy
   - Total points prediction error
4. **Calculate ROI** - Based on Kelly sizing and actual bet outcomes
5. **Validate Methodology** - Edge calculations vs actual results
6. **Generate Report** - Complete performance analysis

## Output Format

The command will generate:

1. **Quick Summary:**
```
============================================================
BETTING PERFORMANCE REPORT - 2025-11-12 NCAAF
============================================================

ATS Record: 3-0 (100%)
Totals Record: 1-0 (100%)
ROI: +45.8%

Best Bet: Toledo -5.5 (WON by 7.5 points)
```

2. **Detailed Game Results:**
```
Game 1: Northern Illinois @ Massachusetts
  Predicted: NIU 18, UMass 12 (NIU by 6)
  Actual: NIU 23, UMass 14 (NIU by 9)
  Recommendation: UMass +9.0 (PUSH)
  Result: PUSH
  Margin Error: -3 points
```

3. **Performance Report File:**
   - Saves to: `docs/performance_reports/REPORT_[DATE]_[LEAGUE].md`
   - Includes all metrics and analysis
   - Ready for review

## Task Execution Steps

### Step 1: Load Predictions
```bash
# Look for prediction files in these locations:
# 1. maction_predictions_summary.md (recent sessions)
# 2. docs/predictions/PREDICTIONS_[DATE]_[LEAGUE].md
# 3. output/edge_detection/[league]_edges_detected.jsonl

# Extract:
# - Predicted scores
# - Recommended bets
# - Edge calculations
# - Kelly sizing
# - Confidence levels
```

### Step 2: Fetch Actual Scores
```bash
# Use ESPN Scoreboard API
uv run python -c "
import asyncio
from src.data.espn_ncaaf_scoreboard_client import ESPNNCAAFScoreboardClient

async def get_scores(date, league):
    client = ESPNNCAAFScoreboardClient()
    await client.connect()

    # Fetch scoreboard for date
    scoreboard = await client.get_scoreboard(
        date=date,
        groups=80 if league == 'ncaaf' else 50,  # 80=FBS, 50=NFL
        limit=400
    )

    # Extract final scores
    games = []
    for event in scoreboard['events']:
        # Parse scores and status
        games.append({
            'teams': [...],
            'scores': [...],
            'status': 'Final'
        })

    await client.close()
    return games

# Run async function
scores = asyncio.run(get_scores('[DATE]', '[LEAGUE]'))
"
```

### Step 3: Calculate ATS Performance
```python
# For each prediction with recommended bet:
for game in predictions:
    actual_margin = game['actual_away_score'] - game['actual_home_score']
    predicted_margin = game['predicted_away_score'] - game['predicted_home_score']

    # ATS calculation
    if game['recommended_bet'] == 'away':
        spread_line = game['spread_away']
        ats_result = (actual_margin + spread_line > 0)
    else:
        spread_line = game['spread_home']
        ats_result = (actual_margin + spread_line < 0)

    # Track: WIN, LOSS, PUSH
```

### Step 4: Calculate Totals Performance
```python
# For each total recommendation:
for game in predictions:
    actual_total = game['actual_away_score'] + game['actual_home_score']
    predicted_total = game['predicted_away_score'] + game['predicted_home_score']
    market_total = game['market_total']

    # O/U result
    if game['total_recommendation'] == 'OVER':
        ou_result = (actual_total > market_total)
    elif game['total_recommendation'] == 'UNDER':
        ou_result = (actual_total < market_total)

    # Prediction accuracy
    total_error = abs(actual_total - predicted_total)
```

### Step 5: Calculate ROI
```python
# Based on Kelly sizing and standard odds
bankroll = 10000  # $10,000 example

for bet in recommended_bets:
    risk_amount = bankroll * (bet['kelly_pct'] / 100)

    if bet['result'] == 'WIN':
        # Standard odds: -110 pays 0.909 to 1
        profit = risk_amount * 0.909
    elif bet['result'] == 'LOSS':
        profit = -risk_amount
    else:  # PUSH
        profit = 0

    total_wagered += risk_amount
    total_profit += profit

roi = (total_profit / total_wagered) * 100
```

### Step 6: Validate Edge Calculations
```python
# Compare predicted edge vs actual edge
for game in predictions:
    predicted_spread = game['predicted_spread']
    market_spread = game['market_spread']
    actual_margin = game['actual_margin']

    predicted_edge = abs(predicted_spread - market_spread)
    actual_edge = abs(actual_margin - market_spread)

    edge_accuracy = predicted_edge - actual_edge
```

### Step 7: Generate Performance Report
```bash
# Create comprehensive markdown report
# Save to: docs/performance_reports/REPORT_[DATE]_[LEAGUE].md

# Include:
# - Executive summary (ATS, ROI, key metrics)
# - Game-by-game results
# - Prediction accuracy analysis
# - Edge validation
# - Methodology lessons learned
# - Recommendations for improvement
```

## Example Workflow

```bash
# Tuesday night MACtion predictions made
/analyze-matchup "Toledo at Miami Ohio"
# Predictions saved: maction_predictions_summary.md

# Wednesday morning - check results
/check-results 20251112 football ncaaf

# Output:
# [*] Loading predictions from maction_predictions_summary.md
# [*] Fetching scores for 2025-11-12 NCAAF games
# [OK] Found 3 games with predictions
#
# Game 1: NIU @ UMass - Predicted: NIU by 6, Actual: NIU by 9
#   Bet: UMass +9.0 → PUSH
#
# Game 2: Buffalo @ CMU - Predicted: CMU by 4, Actual: CMU by 7
#   Bet: CMU -2.0 → WIN (+$227)
#
# Game 3: Toledo @ Miami OH - Predicted: Toledo by 13, Actual: Toledo by 10
#   Bet: Toledo -5.5 → WIN (+$318)
#
# ============================================================
# PERFORMANCE SUMMARY
# ============================================================
# ATS Record: 2-0-1 (67% win rate, excluding pushes: 100%)
# Totals Record: 1-0 (100%)
# Total Wagered: $900
# Total Profit: $545
# ROI: +60.6%
#
# [OK] Report saved: docs/performance_reports/REPORT_20251112_NCAAF.md
```

## Integration with Billy Walters System

This command tracks Billy Walters classification performance:

**STRONG PLAYS (4-7 point edge):**
- Expected Win Rate: 64%
- Kelly Sizing: 3-4%
- Example: Toledo -5.5 (3.5% Kelly)

**MODERATE PLAYS (2-4 point edge):**
- Expected Win Rate: 58%
- Kelly Sizing: 2-3%
- Example: CMU -2.0 (2.5% Kelly)

**LEANS (1-2 point edge):**
- Expected Win Rate: 54%
- Kelly Sizing: 1-2%
- Example: UMass +9.0 (1.5% Kelly)

## Error Handling

**No predictions found:**
```
[ERROR] No predictions found for 2025-11-12 NCAAF
[INFO] Check these locations:
  - maction_predictions_summary.md
  - docs/predictions/PREDICTIONS_20251112_NCAAF.md
```

**Games not final:**
```
[WARNING] 2 of 3 games not yet final
Game 1: Final
Game 2: In Progress (Q3, 5:23)
Game 3: Scheduled

[INFO] Partial results available
```

**Prediction format issues:**
```
[WARNING] Could not parse prediction for Game 2
[INFO] Manual entry required for complete report
```

## Files Generated

1. **Performance Report:** `docs/performance_reports/REPORT_[DATE]_[LEAGUE].md`
2. **CSV Export:** `docs/performance_reports/REPORT_[DATE]_[LEAGUE].csv`
3. **Updated Tracker:** `.claude/performance_tracker.json` (running totals)

## Future Enhancements

- [ ] Closing Line Value (CLV) tracking
- [ ] Sharp vs public money analysis
- [ ] Historical performance database
- [ ] Automated backtesting
- [ ] Performance dashboards
- [ ] Email/Slack notifications

---

**Task:** Execute the complete workflow to fetch scores, calculate performance, and generate a comprehensive report for the specified date/league.
