# ESPN Enhancement Testing - Quick Start Guide

Get started validating ESPN team statistics impact on Billy Walters predictions in 5 minutes.

---

## TL;DR - Start Here

```bash
# 1. Run spread comparison (compare predictions with/without ESPN)
uv run python scripts/analysis/compare_espn_impact.py --league nfl --show-comparisons

# 2. Place a tracked bet with ESPN prediction
uv run python -m walters_analyzer.backtesting.clv_tracker add \
  --league nfl --week 12 --matchup "Buffalo @ KC" \
  --away-team "Buffalo Bills" --home-team "Kansas City Chiefs" \
  --pick "Buffalo" --opening-line 3.0 --size 2.0

# 3. Update closing line before game
uv run python -m walters_analyzer.backtesting.clv_tracker update-line \
  --bet-id NFL12_Buffalo_Bills_Kansas_City_Chiefs --closing-line 2.5

# 4. Settle the bet after game
uv run python -m walters_analyzer.backtesting.clv_tracker settle \
  --bet-id NFL12_Buffalo_Bills_Kansas_City_Chiefs --won --cash 1.82

# 5. View CLV summary
uv run python -m walters_analyzer.backtesting.clv_tracker summary --league nfl
```

---

## Step 1: Verify ESPN Integration is Active

Check that edge detector is using ESPN enhancement:

```bash
# Should see "Loading ESPN team statistics" in output
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector 2>&1 | grep -i espn
```

Expected output:
```
Loading ESPN team statistics for NFL
Enhanced 32 power ratings with ESPN data
```

✅ **If you see this**: ESPN integration is working

---

## Step 2: Run Spread Comparison (5 minutes)

This compares spread predictions **with and without** ESPN metrics.

```bash
# NFL spread comparison
uv run python scripts/analysis/compare_espn_impact.py --league nfl --show-comparisons
```

**What it does**:
- Loads Massey baseline power ratings
- Loads ESPN team statistics
- Enhances ratings with 90/10 formula
- Compares spread predictions
- Shows which games benefited most

**Expected output**:
```
ESPN IMPACT ANALYSIS REPORT
================================
League:                    NFL
Games Analyzed:            16
Average Spread Delta:      +0.43 points
Max Spread Delta:          +2.8 points
Games with Edge Improvement: 12 (75%)
Average Edge Improvement:  +0.62 points
```

**What to look for**:
- ✅ 60%+ games improved (shows ESPN is helpful)
- ✅ Average delta 0.3-1.5 points (normal range)
- ✅ Improvement fairly consistent (not random)

---

## Step 3: Start Tracking Bets (Real-Time CLV)

This tracks your actual betting performance with ESPN predictions.

### 3.1 Add a Bet

When you make a bet using ESPN-enhanced predictions:

```bash
uv run python -m walters_analyzer.backtesting.clv_tracker add \
  --league nfl \
  --week 12 \
  --matchup "Buffalo @ Kansas City" \
  --away-team "Buffalo Bills" \
  --home-team "Kansas City Chiefs" \
  --pick "Buffalo +3.0" \
  --type spread \
  --opening-line 3.0 \
  --size 2.0 \
  --odds -110
```

**Parameters**:
- `--league`: nfl or ncaaf
- `--week`: Week number
- `--pick`: Team you're backing
- `--opening-line`: Line at time of bet
- `--size`: Units wagered (1.0 = 1 unit)
- `--odds`: -110 standard, adjust if needed

### 3.2 Update Closing Line

Before game starts, update the closing line (what market closed at):

```bash
uv run python -m walters_analyzer.backtesting.clv_tracker update-line \
  --bet-id NFL12_Buffalo_Bills_Kansas_City_Chiefs \
  --closing-line 2.5
```

**Where to get closing line**:
- ESPN: Final odds before game
- Overtime.ag: Last posted spread
- Sportsbook app: Final line shown

### 3.3 Settle the Bet

After game finishes, record the result:

```bash
uv run python -m walters_analyzer.backtesting.clv_tracker settle \
  --bet-id NFL12_Buffalo_Bills_Kansas_City_Chiefs \
  --won \
  --score "27-24" \
  --cash 1.82
```

**Parameters**:
- `--bet-id`: Must match the ID created earlier
- `--won`: Include if you won (omit if lost)
- `--score`: Final score
- `--cash`: Amount won (for cash bets, omit for units)

---

## Step 4: View Your Results

### Summary View

```bash
uv run python -m walters_analyzer.backtesting.clv_tracker summary --league nfl
```

Output shows:
```
CLV ANALYSIS REPORT - NFL
================================
Total Bets:                8
Settled Bets:              6
Winning Bets:              5 (83%)
Total Wagered:             12.0
Total Won:                 13.64
Net Profit:                +1.64
ROI:                       +13.7%
Average CLV (per bet):     +0.27 units
Bets with Positive CLV:    4
Avg Positive CLV:          +0.51 units
```

### List All Bets

```bash
uv run python -m walters_analyzer.backtesting.clv_tracker list --league nfl
```

---

## Step 5: Historical Backtest (Optional)

Test how ESPN would have performed on past games:

```bash
# Backtest last 4 weeks
uv run python scripts/backtest/backtest_espn_enhancement.py \
  --league nfl \
  --weeks 4 \
  --show-results
```

Output:
```
ESPN ENHANCEMENT BACKTEST REPORT
================================
League:                    NFL
Period:                    2025-10-15 to 2025-11-20
Games Analyzed:            64

ACCURACY METRICS:
  Baseline avg error:      2.34 points
  Enhanced avg error:      2.15 points
  Improvement:             0.19 points (8.1% better)
  Games improved:          48 (75%)

CONSISTENCY:
  Improvement stdev:       0.48
  Consistent:              YES (80% improved)
```

---

## Complete Weekly Workflow

### Friday (Collection Day)

```bash
# 1. Collect all data (ESPN data collected automatically at 9 AM UTC)
/collect-all-data

# 2. Analyze ESPN impact
uv run python scripts/analysis/compare_espn_impact.py --league nfl --show-comparisons

# 3. Run edge detector with enhanced ratings
/edge-detector

# 4. Review edge detection results
cat output/edge_detection/edge_report.txt
```

### Before Games

```bash
# Review recommended picks based on enhanced ratings
cat output/edge_detection/nfl_edges_detected.jsonl | head -5

# Place bets with tracking
uv run python -m walters_analyzer.backtesting.clv_tracker add [options]

# Update closing lines
uv run python -m walters_analyzer.backtesting.clv_tracker update-line [options]
```

### After Games

```bash
# Settle bets
uv run python -m walters_analyzer.backtesting.clv_tracker settle [options]

# Review performance
uv run python -m walters_analyzer.backtesting.clv_tracker summary --league nfl

# Track trends over time
cat data/bets/active_bets.json | jq '.bets[] | {bet_id, win, closing_line_value}'
```

---

## Success Metrics

### What to Track Over Time

**Week 1-2** (Baseline):
- 8+ bets placed with ESPN predictions
- Establish baseline CLV (with/without ESPN)
- Look for positive trend

**Week 3-4** (Validation):
- 20+ bets accumulated
- ESPN CLV should exceed baseline
- Improvement direction clear

**Week 5+ (Proof)**:
- 40+ bets
- Consistent positive CLV
- Statistical significance >95%

### Target Results

| Metric | Target | Indicates |
|--------|--------|-----------|
| Spread comparison improvement | 60%+ | ESPN helps most games |
| Avg edge improvement | +0.5 to +1.0 | Meaningful change |
| CLV with ESPN | +0.2 to +0.5 | Real money improvement |
| Win rate improvement | 53%+ | Consistent edge |
| Consistency | Improvement in 70%+ games | Not random |

---

## Troubleshooting

### "No games found"

```bash
# Check if power ratings exist
ls -la data/current/massey_ratings_nfl.json

# Check if ESPN data exists
ls -la data/archive/raw/nfl/team_stats/current/
```

If files missing, run:
```bash
/collect-all-data
```

### "Spread comparison shows 0 change"

Possible causes:
1. ESPN data not loaded (check file freshness)
2. Team names don't match (check mapping)
3. Wrong path to ratings (verify file exists)

Debug:
```bash
# Check ESPN data is valid
uv run python -c "
from src.walters_analyzer.valuation.espn_integration import ESPNDataLoader
loader = ESPNDataLoader()
latest = loader.find_latest_team_stats('nfl')
if latest:
    stats = loader.load_team_stats(latest)
    print(f'Loaded {len(stats)} teams from ESPN')
"
```

### "CLV calculation seems wrong"

Check:
1. Opening line matches your actual bet
2. Closing line is before game start
3. Bet ID matches exactly (case-sensitive)
4. Win/loss recorded correctly

### "Backtest has no games"

Historical game data needs to exist:
```bash
# Create sample historical data or
# Run with recent week games instead
uv run python scripts/backtest/backtest_espn_enhancement.py --weeks 1 --league nfl
```

---

## File Locations

Important files for this workflow:

```
📊 Data Files:
  data/current/massey_ratings_nfl.json          (baseline ratings)
  data/archive/raw/nfl/team_stats/current/      (ESPN stats)

🎯 Tools:
  scripts/analysis/compare_espn_impact.py       (spread comparison)
  src/walters_analyzer/backtesting/clv_tracker.py  (CLV tracking)
  scripts/backtest/backtest_espn_enhancement.py (historical backtest)

📁 Results:
  output/espn_analysis/                         (comparison results)
  data/bets/active_bets.json                    (CLV tracking data)
  output/backtests/                             (backtest results)

📚 Documentation:
  docs/ESPN_Integration_Quick_Reference.md      (technical reference)
  docs/ESPN_ENHANCEMENT_TESTING_ROADMAP.md      (comprehensive plan)
```

---

## Next Steps

1. ✅ Verify ESPN integration is active
2. ✅ Run spread comparison
3. ✅ Start tracking bets with CLV
4. ✅ Collect 20+ settled bets
5. ✅ Run historical backtest
6. ✅ Compare real vs. historical results
7. ✅ Document findings and optimize

---

## Questions?

Refer to:
- **Technical Details**: `docs/ESPN_Integration_Quick_Reference.md`
- **Complete Roadmap**: `docs/ESPN_ENHANCEMENT_TESTING_ROADMAP.md`
- **Module Documentation**: See docstrings in source files

**Key Contacts**:
- ESPN Integration: `src/walters_analyzer/valuation/espn_integration.py`
- CLV System: `src/walters_analyzer/backtesting/clv_tracker.py`
- Edge Detector: `src/walters_analyzer/valuation/billy_walters_edge_detector.py`
