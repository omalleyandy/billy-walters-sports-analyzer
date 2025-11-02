
# Backtesting & Validation Guide

Complete guide to validating your Billy Walters sports betting methodology using historical data and the backtesting framework.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup & Data Collection](#setup--data-collection)
4. [Running Backtests](#running-backtests)
5. [Validating Week 9 Predictions](#validating-week-9-predictions)
6. [Comparing with Massey Ratings](#comparing-with-massey-ratings)
7. [Performance Metrics](#performance-metrics)
8. [Optimization](#optimization)

---

## Overview

The backtesting framework allows you to:

- **Validate strategy performance** on historical NFL data (2020-2024)
- **Calculate comprehensive metrics**: ROI, Sharpe ratio, CLV, max drawdown
- **Optimize parameters**: Find optimal edge thresholds and factor weights
- **Compare predictions**: Benchmark against Massey Ratings and market consensus
- **Detect biases**: Identify systematic errors in your model
- **Test statistical significance**: Ensure results aren't due to chance

---

## Architecture

### Database Schema

The historical database (`data/historical/historical_games.db`) contains:

```
games           # Historical game results (scores, dates, teams)
odds            # Opening and closing lines from sportsbooks
injuries        # Historical injury reports
weather         # Historical weather conditions
predictions     # Your model's predictions for backtesting
results         # Actual bet outcomes vs predictions
```

### Backtesting Engine

The engine simulates betting on historical games:

1. **Load historical game** (date, teams, final score)
2. **Get opening odds** (what you would have bet)
3. **Calculate power ratings** (as of that date)
4. **Apply S/W/E factors** (situational, weather, emotional)
5. **Generate prediction** (final margin, bet recommendation)
6. **Calculate bet result** (did it win? what was the CLV?)
7. **Track performance** (update bankroll, record metrics)

---

## Setup & Data Collection

### Step 1: Initialize Database

The database is automatically created when you run collection scripts.

```bash
# Check database structure
python -c "from walters_analyzer.historical_db import HistoricalDatabase; db = HistoricalDatabase(); print('Database initialized')"
```

### Step 2: Collect Historical Games

Scrape historical NFL game results from ESPN:

```bash
# Collect 2020-2024 seasons
python scripts/collect_historical_games.py --sport nfl --start-season 2020 --end-season 2024

# Dry run (preview without saving)
python scripts/collect_historical_games.py --sport nfl --start-season 2023 --end-season 2023 --dry-run

# Collect specific week
python scripts/collect_historical_games.py --sport nfl --start-season 2024 --end-season 2024 --week 9
```

### Step 3: Collect Historical Odds

**Option A: Pro Football Reference (automated)**

```bash
# Collect odds from PFR
python scripts/collect_historical_odds.py --source pfr --start-season 2020 --end-season 2024
```

**Option B: Manual CSV Import (recommended for accuracy)**

1. Download historical odds from:
   - [Sports Odds History](https://www.sportsoddshistory.com)
   - [Sportsbookreview](https://www.sportsbookreviewsonline.com/scoresoddsarchives/nfl/nfl.htm)
   - [The Odds API](https://the-odds-api.com) (requires API key)

2. Import CSV:

```bash
python scripts/collect_historical_odds.py --source csv --csv-path path/to/historical_odds.csv --start-season 2020 --end-season 2024
```

**Expected CSV Format:**

```csv
Week,GameDate,AwayTeam,HomeTeam,OpenSpread,OpenAwayPrice,OpenHomePrice,CloseSpread,CloseAwayPrice,CloseHomePrice,OpenTotal,CloseTotal
1,2024-09-05,BAL,KC,-3,-110,-110,-2.5,-110,-110,46.5,47.0
```

### Step 4: Verify Data

```python
from walters_analyzer.historical_db import HistoricalDatabase

db = HistoricalDatabase()

# Check games
games = db.get_games(season=2023)
print(f"2023 games: {len(games)}")

# Check odds
for game in games[:5]:
    odds = db.get_odds(game['game_id'], is_closing=True)
    print(f"{game['away_team']} @ {game['home_team']}: {len(odds)} odds entries")

db.close()
```

---

## Running Backtests

### Basic Backtest

Run the standard backtest on historical data:

```bash
python scripts/run_backtest.py run \
    --start-season 2020 \
    --end-season 2023 \
    --min-edge 2.0 \
    --max-edge 10.0 \
    --bankroll 10000
```

**Output:**

```
==================================================================
BILLY WALTERS METHODOLOGY BACKTEST
==================================================================

Season 2020
--------------------------------------------------------------
Season 2020 Summary:
  Games analyzed: 256
  Bets placed: 47
  Wins: 27
  Win rate: 57.4%
  ROI: 8.3%
  Profit: $3,892.00
  Ending bankroll: $13,892.00

...

==================================================================
BACKTEST COMPLETE
==================================================================
Total games analyzed: 1024
Total bets placed: 189
Win rate: 55.6%
ROI: 7.2%
Total profit: $13,608.00
Final bankroll: $23,608.00
Sharpe ratio: 1.42
Max drawdown: 12.3%
Average CLV: +0.87 points
```

### Save Detailed Report

```bash
python scripts/run_backtest.py run \
    --start-season 2020 \
    --end-season 2023 \
    --output reports/backtest_2020_2023.txt
```

The report includes:
- Overall performance metrics
- Risk metrics (Sharpe, drawdown)
- CLV analysis
- Performance by star rating
- Every individual bet result

---

## Validating Week 9 Predictions

Use the validation script to compare your Week 9 CSV predictions with recalculated values using current data.

### Step 1: Run Validation

```bash
python scripts/validate_week9_edges.py \
    --csv-path "C:\Users\omall\Downloads\week9_edges_actual_only.csv" \
    --output reports/week9_validation.txt
```

### Step 2: Review Validation Report

The report shows:

```
==================================================================
WEEK 9 EDGE VALIDATION REPORT
==================================================================

OVERALL VALIDATION SUMMARY
--------------------------------------------------------------
Total games analyzed: 13
Average edge difference: 0.34 points
Bet side agreement: 12/13 (92.3%)

Agreement Distribution:
  Strong (<0.5 pts): 9 (69.2%)
  Good (0.5-1.0 pts): 3 (23.1%)
  Moderate (1.0-2.0 pts): 1 (7.7%)
  Weak (>2.0 pts): 0 (0.0%)

GAME-BY-GAME VALIDATION
--------------------------------------------------------------

DET @ MIN (SUN-1ET)
  Agreement: STRONG
  CSV Edge: 4.96 pts | Recalc Edge: 5.12 pts | Diff: +0.16 pts
  CSV Bet: DET (home) | Recalc Bet: DET (home)
  CSV Stake: $600.00 | Recalc Stake: $610.00 | Diff: +$10.00
  CSV Win%: 66.7% | Recalc Win%: 67.2% | Diff: +0.5%

...

RECOMMENDATIONS
--------------------------------------------------------------
✓ Edge calculations are highly consistent. CSV predictions validated.
✓ Bet side recommendations are highly consistent.
```

### Step 3: Scrape Live Data (Optional)

To validate with truly live odds/injuries/weather:

```bash
# Scrape current odds
uv run walters-analyzer scrape-overtime --sport nfl

# Scrape current injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Scrape weather for Week 9 venues
uv run walters-analyzer scrape-weather

# Then re-run validation with --scrape-live flag
python scripts/validate_week9_edges.py \
    --csv-path "week9_edges.csv" \
    --scrape-live \
    --output reports/week9_live_validation.txt
```

---

## Comparing with Massey Ratings

Massey Ratings is one of the most respected college football and NFL prediction systems. Compare your edges against theirs for validation.

### Step 1: Scrape Massey Predictions

```bash
# Scrape all Massey data (ratings + games)
uv run walters-analyzer scrape-massey --data-type all

# Or just game predictions
uv run walters-analyzer scrape-massey --data-type games
```

This saves to: `data/massey_ratings/games_YYYYMMDD_HHMMSS.csv`

### Step 2: Run Comparison

```bash
python scripts/compare_massey_week9.py \
    --csv-path "C:\Users\omall\Downloads\week9_edges_actual_only.csv" \
    --massey-path "data/massey_ratings/games_20241101_120000.csv" \
    --output reports/week9_massey_comparison.txt
```

### Step 3: Review Comparison Report

```
==================================================================
WEEK 9: BILLY WALTERS vs MASSEY RATINGS COMPARISON
==================================================================

OVERALL COMPARISON SUMMARY
--------------------------------------------------------------
Total games: 13
Games with Massey data: 13
Side agreement: 10/13 (76.9%)

Spread Agreement Distribution:
  Strong (<1.0 pts): 5 (38.5%)
  Good (1.0-2.0 pts): 4 (30.8%)
  Moderate (2.0-3.0 pts): 3 (23.1%)
  Weak (>3.0 pts): 1 (7.7%)

GAME-BY-GAME COMPARISON
--------------------------------------------------------------

MIN @ DET (SUN-1ET)
  Market line: -8.5
  Billy Walters spread: -13.46 (Edge: 4.96 pts)
  Billy Walters bet: DET (home)
  Massey spread: -11.2 (Edge: 2.70 pts)
  Spread difference: 2.26 pts
  Agreement: MODERATE | Side agreement: YES

...

HIGHEST CONFIDENCE BETS (Both models agree):
--------------------------------------------------------------
  MIN @ DET: DET (home) (4.96 pt edge)
  CAR @ GB: GB (home) (6.15 pt edge)
  TEN @ LAC: LAC (home) (6.04 pt edge)
```

---

## Performance Metrics

The backtest engine calculates comprehensive performance metrics:

### Core Metrics

- **ROI (Return on Investment)**: Total profit / Total staked × 100
- **Win Rate**: Winning bets / Total bets × 100
- **Total Profit**: Sum of all bet profits/losses
- **Sharpe Ratio**: Risk-adjusted return (higher is better, >1.0 is good)
- **Max Drawdown**: Largest peak-to-trough decline in bankroll

### CLV Metrics

- **Average CLV**: Average closing line value in points
  - Positive CLV = You bet better than closing line
  - **Target: +0.5 points or higher**
- **CLV Positive Rate**: Percentage of bets with positive CLV
  - **Target: >60%**

### Streak Tracking

- **Longest Win Streak**: Maximum consecutive wins
- **Longest Lose Streak**: Maximum consecutive losses

### Performance by Star Rating

Breakdown of metrics by bet size (star rating):

```
0.5 stars: 15 bets, 53.3% win rate, +2.1% ROI
1.0 stars: 42 bets, 54.8% win rate, +5.4% ROI
1.5 stars: 38 bets, 55.3% win rate, +6.8% ROI
2.0 stars: 27 bets, 59.3% win rate, +12.3% ROI
2.5 stars: 12 bets, 66.7% win rate, +18.9% ROI
3.0 stars: 5 bets, 80.0% win rate, +31.2% ROI
```

---

## Optimization

### Optimize Edge Threshold

Find the optimal minimum edge threshold for bet placement:

```bash
python scripts/run_backtest.py optimize \
    --start-season 2020 \
    --end-season 2023 \
    --min-threshold 1.0 \
    --max-threshold 8.0 \
    --step 0.5
```

**Output:**

```
Testing threshold: 1.0 points
  ROI: 2.3%, Bets: 347, Sharpe: 0.82

Testing threshold: 1.5 points
  ROI: 3.9%, Bets: 268, Sharpe: 1.05

Testing threshold: 2.0 points
  ROI: 7.2%, Bets: 189, Sharpe: 1.42

Testing threshold: 2.5 points
  ROI: 9.8%, Bets: 142, Sharpe: 1.68

Testing threshold: 3.0 points
  ROI: 11.4%, Bets: 98, Sharpe: 1.79

...

Optimal threshold: 3.0 points
ROI: 11.4%
Total bets: 98
```

### Walk-Forward Cross-Validation

Test strategy robustness with out-of-sample validation:

```bash
python scripts/run_backtest.py walk-forward \
    --start-season 2018 \
    --end-season 2023 \
    --train-window 2 \
    --test-window 1
```

This trains on 2 seasons and tests on the following season, rolling forward:

```
Fold 1: Train 2018-2019, Test 2020
Fold 2: Train 2019-2020, Test 2021
Fold 3: Train 2020-2021, Test 2022
Fold 4: Train 2021-2022, Test 2023
```

### Analyze Results for Biases

Detect systematic biases in your predictions:

```bash
python scripts/run_backtest.py analyze --season 2023
```

**Output:**

```
STATISTICAL SIGNIFICANCE TEST
--------------------------------------------------------------
Results are statistically significant at 95% confidence level.
P-value: 0.0123
Mean profit per bet: $72.14
95% CI: $31.45 to $112.83

BIAS DETECTION
--------------------------------------------------------------

Home Bets:
  Count: 94
  Win rate: 54.3%
  ROI: 6.8%

Away Bets:
  Count: 95
  Win rate: 56.8%
  ROI: 7.6%

Favorites (>3 point lines):
  Count: 67
  Win rate: 58.2%
  ROI: 9.3%

Underdogs (≤3 point lines):
  Count: 122
  Win rate: 53.3%
  ROI: 5.4%

BENCHMARK COMPARISON
--------------------------------------------------------------

vs. RANDOM:
  Strategy ROI: 7.2%
  Benchmark ROI: -4.8%
  Improvement: +12.0%
  Outperforms: YES

vs. FAVORITES:
  Strategy ROI: 7.2%
  Benchmark ROI: -8.0%
  Improvement: +15.2%
  Outperforms: YES
```

---

## Best Practices

### 1. Data Quality

- **Use multiple odds sources** for historical lines
- **Verify game results** against multiple sources (ESPN, PFR)
- **Check for missing data** before running backtests

### 2. Realistic Assumptions

- **Use opening odds** for bet simulation (not closing)
- **Account for juice** (-110 standard, some bets may be worse)
- **Include all bets** (don't cherry-pick winning periods)

### 3. Statistical Rigor

- **Minimum sample size**: 100+ bets for meaningful conclusions
- **Test significance**: Use statistical tests to validate results
- **Cross-validate**: Use walk-forward to avoid overfitting
- **Compare benchmarks**: Always compare to naive strategies

### 4. Continuous Improvement

- **Regular backtests**: Run monthly on new data
- **Track live CLV**: Compare your bets to closing lines
- **Adjust factors**: Optimize S/W/E weights based on results
- **Document changes**: Keep a model changelog

---

## Troubleshooting

### "No games found in database"

```bash
# Verify database exists
ls data/historical/

# Re-run game collection
python scripts/collect_historical_games.py --sport nfl --start-season 2023 --end-season 2023
```

### "No odds data for games"

```bash
# Check odds in database
python -c "from walters_analyzer.historical_db import HistoricalDatabase; db = HistoricalDatabase(); odds = db.get_odds('espn_401547413'); print(len(odds))"

# Import odds from CSV
python scripts/collect_historical_odds.py --source csv --csv-path path/to/odds.csv
```

### "Backtest results differ from CSV predictions"

This is expected! The backtest simulates real-time betting:

- **Power ratings evolve** week-to-week in backtesting
- **Data availability differs** (historical vs. current)
- **CSV may use final/adjusted data** not available pre-game

The goal is to validate the **methodology**, not match exact numbers.

---

## Next Steps

1. **Collect 5 years of historical data** (2020-2024)
2. **Run comprehensive backtest** on full dataset
3. **Validate Week 9 predictions** against CSV
4. **Compare with Massey Ratings** for Week 9
5. **Analyze results** for biases and significance
6. **Optimize edge threshold** based on results
7. **Make informed betting decisions** with validated model

---

## Support

For issues or questions:

- Check existing tests: `tests/test_backtest_*.py`
- Review example outputs: `reports/`
- Consult Billy Walters methodology: `docs/METHODOLOGY.md`
