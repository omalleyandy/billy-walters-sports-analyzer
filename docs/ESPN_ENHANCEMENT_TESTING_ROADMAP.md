# ESPN Enhancement Testing Roadmap

## Overview

This document outlines the complete plan for validating ESPN team statistics impact on Billy Walters power rating calculations through real-world testing and historical backtesting.

**Timeline**: Friday 9 AM UTC automated collection → Progressive validation through real games → Historical backtesting for statistical significance

---

## Phase 1: Real-Time Data Collection & Monitoring

### 1.1 Automated Collection (Friday 9 AM UTC)

**Status**: ✅ Production Ready

ESPN data collected automatically by production orchestrator every Friday at 9 AM UTC:
```
ESPN Production Orchestrator
  ↓ (Tue/Fri 9 AM UTC)
📁 data/archive/raw/ncaaf/team_stats/current/
  ↓
✅ team_stats_week_{week}.json (latest 2 weeks)
✅ Full API response with all team metrics
```

**Collected Metrics**:
- Points Per Game (PPG) - offensive efficiency
- Points Allowed Per Game (PAPG) - defensive strength
- Turnover Margin - ball security
- Yards Per Game - offensive productivity
- Yards Allowed Per Game - defensive depth

**Verification Commands**:
```bash
# Check latest ESPN data
ls -lt data/archive/raw/ncaaf/team_stats/current/*.json | head -1

# Validate data format
uv run python -c "
import json
with open('data/archive/raw/ncaaf/team_stats/current/team_stats_*.json') as f:
    data = json.load(f)
    teams = [t['team_name'] for t in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])]
    print(f'Teams in latest: {len(teams)}')
"
```

---

## Phase 2: Spread Comparison Framework

### 2.1 Baseline vs. Enhanced Predictions

**Tool**: `scripts/analysis/compare_espn_impact.py`

Compares spread predictions from:
1. **Baseline** (Massey ratings only - historical)
2. **Enhanced** (Massey 90% + ESPN 10% - recent form)

**How It Works**:

```python
from walters_analyzer.valuation.billy_walters_edge_detector import BillyWaltersEdgeDetector

# Baseline predictions (no ESPN)
detector_baseline = BillyWaltersEdgeDetector()
detector_baseline.load_massey_ratings("output/massey/ratings.json", league="nfl")
# Baseline spreads ready

# Enhanced predictions (with ESPN)
detector_enhanced = BillyWaltersEdgeDetector()
detector_enhanced.load_massey_ratings("output/massey/ratings.json", league="nfl")
detector_enhanced.load_espn_team_stats(league="nfl")
detector_enhanced.enhance_power_ratings_with_espn(league="nfl")
# Enhanced spreads ready

# Compare
spread_differences = detector_baseline.ratings - detector_enhanced.ratings
```

### 2.2 Running Spread Comparison

**Quick Start**:
```bash
# NFL spread comparison
uv run python scripts/analysis/compare_espn_impact.py --league nfl --show-comparisons

# NCAAF spread comparison
uv run python scripts/analysis/compare_espn_impact.py --league ncaaf --show-comparisons
```

**Expected Output**:
```
ESPN IMPACT ANALYSIS REPORT
================================
League:                    NFL
Games Analyzed:            16
Average Spread Delta:      +0.43 points
Max Spread Delta:          +2.8 points
Games with Edge Improvement: 12 (75%)
Average Edge Improvement:  +0.62 points
Largest Improvement:       +2.2 points
Largest Degradation:       -0.8 points
```

### 2.3 Interpretation

**Expected Patterns**:
- Average spread delta: ±0.5 to ±1.5 points (normal volatility)
- Edge improvement: 60-80% of games show positive impact
- Consistency: Same direction most of the time (good signal)

**Red Flags**:
- Spread deltas >3 points (might indicate data quality issue)
- <50% games improved (might indicate wrong weighting)
- Random direction changes (indicates overfitting)

---

## Phase 3: CLV Impact Tracking

### 3.1 CLV (Closing Line Value) Fundamentals

**What It Is**: Difference between opening and closing odds at bet placement

**Billy Walters Success Metric**: CLV is more important than win/loss percentage
- Professional average: +1.5 CLV per bet
- Elite bettors: +2.0 CLV per bet
- Measuring: Units won relative to line movements

**Why It Matters for ESPN**:
- Shows if enhanced predictions are better than market
- Eliminates randomness from individual results
- Measures consistent edge over time

### 3.2 CLV Tracking Implementation

**Tool**: `src/walters_analyzer/backtesting/clv_tracker.py`

**Basic Usage**:

```bash
# Add a bet with ESPN prediction
uv run python -m walters_analyzer.backtesting.clv_tracker add \
  --league nfl \
  --week 12 \
  --matchup "Buffalo @ KC" \
  --away-team "Buffalo Bills" \
  --home-team "Kansas City Chiefs" \
  --pick "Buffalo Bills +3.0" \
  --opening-line 3.0 \
  --size 2.0 \
  --odds -110

# Update closing line (before game)
uv run python -m walters_analyzer.backtesting.clv_tracker update-line \
  --bet-id NFL12_Buffalo_Bills_Kansas_City_Chiefs \
  --closing-line 2.5

# Settle the bet (after game)
uv run python -m walters_analyzer.backtesting.clv_tracker settle \
  --bet-id NFL12_Buffalo_Bills_Kansas_City_Chiefs \
  --won \
  --score "27-24" \
  --cash 1.82

# View summary
uv run python -m walters_analyzer.backtesting.clv_tracker summary --league nfl
```

### 3.3 CLV Metrics to Track

| Metric | Target | Calculation |
|--------|--------|-------------|
| **CLV per bet** | +1.5 to +2.0 | (Closing Odds - Opening Odds) × Units |
| **% Positive CLV** | 60%+ | Bets where line moved in our favor |
| **Avg Positive CLV** | +2.0 or higher | Average CLV on winning bets |
| **ROI** | 15-25%+ | (Net Profit / Total Wagered) |
| **ESPN CLV Impact** | +0.3 to +0.5 | CLV improvement from enhanced predictions |

### 3.4 Expected Results

**Week 1-2** (Baseline establishment):
- 8-16 bets placed
- Establish baseline CLV (with and without ESPN)
- Look for consistency in direction

**Week 3-4** (Pattern confirmation):
- 20-30 bets total
- ESPN advantage should be clear
- Start statistical significance testing

**Week 8-12** (Conclusive data):
- 60-100 bets total
- Statistical significance >95% confidence
- Clear ROI comparison available

---

## Phase 4: Historical Backtesting

### 4.1 Backtesting Framework

**Tool**: `scripts/backtest/backtest_espn_enhancement.py`

Simulates ESPN enhancement impact on historical games to measure:
- Spread prediction accuracy improvement
- Edge detection quality
- Consistency across different game types

### 4.2 Running Historical Backtest

```bash
# Backtest last 4 weeks of games
uv run python scripts/backtest/backtest_espn_enhancement.py \
  --league nfl \
  --weeks 4 \
  --show-results

# Backtest NCAAF last 6 weeks
uv run python scripts/backtest/backtest_espn_enhancement.py \
  --league ncaaf \
  --weeks 6
```

### 4.3 Expected Output

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

EDGE METRICS:
  Baseline avg edge:       -0.22 points
  Enhanced avg edge:       +0.41 points
  Edge improvement:        +0.63 points

CONSISTENCY:
  Improvement stdev:       0.48
  Consistent:              YES (80% improved)
```

### 4.4 Interpreting Results

**Good Signs**:
- ✅ 70%+ of games improved
- ✅ Average error reduction 0.1-0.3 points
- ✅ Edge improvement consistent
- ✅ Standard deviation <0.5

**Concerning Signs**:
- ❌ <60% of games improved
- ❌ Error increases >0.1 points
- ❌ High volatility (stdev >1.0)
- ❌ Results vary by season/week

---

## Phase 5: Complete Workflow Integration

### 5.1 Updated /collect-all-data Workflow

```
Step 1: Power Ratings (Massey composite)
Step 2: Game Schedules (ESPN API)
Step 3: Team Statistics (ESPN API) ← ESPN DATA
Step 4: Injury Reports (ESPN/NFL)
Step 5: Weather Forecasts (AccuWeather)
Step 6: Odds Data (Overtime.ag API)
Step 7: Edge Detection (USES ENHANCED RATINGS)
Step 8: Spread Comparison (NEW: Compare impact)
Step 9: CLV Tracking (NEW: Track performance)
```

### 5.2 Running Complete Workflow

```bash
# Step 1-6: Data collection
/collect-all-data

# Step 7: Edge detection (auto-triggers with enhanced ratings)
/edge-detector

# Step 8: Analyze ESPN impact
uv run python scripts/analysis/compare_espn_impact.py --league nfl --show-comparisons

# Step 9: View CLV tracking
uv run python -m walters_analyzer.backtesting.clv_tracker summary --league nfl
```

### 5.3 Expected Timing

**Friday 9 AM UTC**: ESPN data collection completes
- ESPN stats loaded into edge detector
- Power ratings enhanced automatically
- ~5 minute integration

**Friday 12 PM UTC**: Ready for analysis
- Run spread comparison
- Validate enhancement consistency
- Check for data quality issues

**Before games**: Place bets with enhanced predictions
- Use enhanced spreads for decisions
- Track CLV as games settle

**Post-game**: Analyze results
- Calculate CLV
- Update tracking database
- Validate against baseline

---

## Phase 6: Validation Checklist

### Pre-Launch Validation

- [ ] ESPN data loads without errors
- [ ] Power ratings enhance correctly (Massey preserved as baseline)
- [ ] 90/10 weighting applied properly
- [ ] Spread comparison runs successfully
- [ ] CLV tracking stores data correctly
- [ ] Backtest framework executes without errors
- [ ] All three comparison methods show consistent results

### During Operations

- [ ] ESPN data collected every Friday
- [ ] Enhancement happens automatically in edge detector
- [ ] Spread comparisons show < 1 point average delta
- [ ] CLV improves with ESPN predictions
- [ ] Historical backtests align with real results
- [ ] No data quality issues detected

### Weekly Review Checklist

- [ ] Check ESPN data freshness
- [ ] Review spread comparison delta
- [ ] Analyze CLV per bet trends
- [ ] Validate consistency across games
- [ ] Look for degradation or improvement patterns
- [ ] Update any team-specific weighting if needed

---

## Success Criteria

### Minimum Success Threshold

✅ **Phase 2 (Spread Comparison)**:
- Run without errors ✅
- Show consistent direction (60%+ same) ✅
- Average delta 0.3-1.5 points ✅

✅ **Phase 3 (CLV Tracking)**:
- Track 20+ bets consistently
- ESPN predictions CLV > baseline
- Positive improvement trend visible

✅ **Phase 4 (Historical Backtest)**:
- 70%+ of games improved
- Average error reduction 0.1-0.3 points
- Results statistically significant

### Optimal Success Threshold

🎯 **Complete Implementation**:
- Spread comparison: 75%+ improvement
- CLV improvement: +0.3 to +0.5 per bet
- Backtest: 80%+ games better, 95% confidence
- Real-world: Measurable edge in live betting

---

## Debugging & Troubleshooting

### "ESPN data not loading"

```bash
# Check if files exist
ls -la data/archive/raw/nfl/team_stats/current/

# Check file format
uv run python -c "
import json
with open('data/archive/raw/nfl/team_stats/current/team_stats_*.json') as f:
    data = json.load(f)
    print('Valid JSON structure')
"

# Re-run production orchestrator
uv run python scripts/dev/espn_production_orchestrator.py --league nfl --force
```

### "Spread comparison shows no change"

Possible causes:
1. ESPN data not loaded → Check file freshness
2. No team name matches → Check team name consistency
3. Wrong power rating path → Verify Massey ratings file exists

```bash
# Debug team name mapping
uv run python -c "
from src.walters_analyzer.valuation.espn_integration import ESPNDataLoader
loader = ESPNDataLoader()
latest = loader.find_latest_team_stats('nfl')
stats = loader.load_team_stats(latest)
print('ESPN teams:', list(stats.keys())[:5])
"
```

### "CLV tracking not calculating correctly"

- Verify odds format (decimal vs American)
- Check line movement direction
- Ensure final score entered correctly
- Validate bet_id format matches

### "Backtest shows negative improvement"

Possible issues:
1. 90/10 weighting too aggressive (try 80/20)
2. Stale ESPN data used in backtest
3. Historical games missing ESPN metrics
4. Team name mapping errors

---

## Next Optimization Opportunities

After validation, consider:

1. **Weight Optimization**: Test 80/20, 85/15 formulas
2. **Position-Specific Metrics**: Adjust by injury status
3. **Game Context**: Week-based weighting changes
4. **Tempo Impact**: Possession-based efficiency adjustments
5. **Weather Integration**: Combine with weather impact
6. **Season Adjustment**: Update weights mid-season

---

## File References

| File | Purpose |
|------|---------|
| `scripts/analysis/compare_espn_impact.py` | Spread comparison tool |
| `src/walters_analyzer/backtesting/clv_tracker.py` | CLV tracking system |
| `scripts/backtest/backtest_espn_enhancement.py` | Historical backtesting |
| `src/walters_analyzer/valuation/espn_integration.py` | ESPN data loading |
| `docs/ESPN_Integration_Quick_Reference.md` | Quick reference guide |

---

## Commands Quick Reference

```bash
# Data Collection
/collect-all-data              # Complete automated collection

# Edge Detection
/edge-detector                 # Run with enhanced ratings

# Analysis
uv run python scripts/analysis/compare_espn_impact.py --league nfl --show-comparisons

# CLV Tracking
uv run python -m walters_analyzer.backtesting.clv_tracker add [options]
uv run python -m walters_analyzer.backtesting.clv_tracker summary --league nfl

# Historical Backtest
uv run python scripts/backtest/backtest_espn_enhancement.py --league nfl --weeks 4 --show-results

# Check Current Week
/current-week
```

---

## Summary

This roadmap enables comprehensive validation of ESPN enhancement impact through:

1. **Automated Collection** (Friday 9 AM UTC)
2. **Real-Time Spread Comparison** (consistent measurements)
3. **CLV Tracking** (performance validation)
4. **Historical Backtesting** (statistical proof)
5. **Complete Integration** (production ready)

Expected outcome: **Measurable improvement in edge detection quality and CLV per bet with ESPN metrics integrated into power ratings.**
