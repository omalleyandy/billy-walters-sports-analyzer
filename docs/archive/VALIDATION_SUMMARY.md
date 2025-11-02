# Week 9 Validation & Backtesting Framework - Summary

**Created:** November 1, 2025
**Purpose:** Validate Week 9 NFL edge calculations and build comprehensive backtesting infrastructure

---

## 🎯 What Was Built

### 1. Historical Database System (`walters_analyzer/historical_db.py`)

A complete SQLite database system for storing and querying historical data:

**Tables:**
- `games` - Historical game results (scores, dates, venues)
- `odds` - Opening and closing lines from sportsbooks
- `injuries` - Historical injury reports
- `weather` - Historical weather conditions
- `predictions` - Model predictions for backtesting
- `results` - Actual bet outcomes vs predictions

**Features:**
- Full CRUD operations for all data types
- Indexed queries for fast retrieval
- Support for multiple sports (NFL/CFB)
- Track power ratings evolution over time

### 2. Data Collection Scripts

**`scripts/collect_historical_games.py`**
- Scrapes NFL game results from ESPN API
- Supports 2020-2024 seasons (or custom range)
- Can fetch entire seasons or specific weeks
- Includes playoff games
- Stores scores, venues, and metadata

**`scripts/collect_historical_odds.py`**
- Scrapes historical odds from Pro Football Reference
- Supports CSV import from multiple sources
- Captures opening and closing lines
- Tracks line movements
- Multiple sportsbook support

### 3. Comprehensive Backtesting Engine (`walters_analyzer/backtest/`)

**`engine.py` - Core Backtesting Engine**
- Simulates week-by-week betting on historical games
- Updates power ratings dynamically as season progresses
- Applies S/W/E factors based on historical context
- Calculates edges and generates bet recommendations
- Tracks bankroll, P&L, and CLV
- Records all predictions and results

**`metrics.py` - Performance Metrics**
- ROI (Return on Investment)
- Win rate and profit/loss
- Sharpe ratio (risk-adjusted returns)
- Maximum drawdown
- CLV (Closing Line Value) statistics
- Performance breakdown by star rating
- Performance breakdown by month/season
- Longest win/lose streaks

**`validation.py` - Strategy Validator**
- Walk-forward cross-validation
- Edge threshold optimization (grid search)
- Statistical significance testing
- Bias detection (home/away, favorite/underdog)
- Benchmark comparisons (random, always favorites, etc.)

### 4. Week 9 Validation Tools

**`scripts/validate_week9_edges.py`**
- Loads Week 9 predictions from your CSV
- Recalculates edges using current power ratings
- Compares CSV predictions vs recalculated values
- Identifies discrepancies in edge calculations
- Validates bet side recommendations
- Generates detailed validation report

**Features:**
- Game-by-game comparison
- Agreement level classification (Strong/Good/Moderate/Weak)
- Stake validation
- Win probability comparison
- Actionable recommendations

**`scripts/compare_massey_week9.py`**
- Loads Week 9 Billy Walters predictions
- Compares with Massey Ratings predictions
- Identifies agreement/disagreement zones
- Highlights highest confidence bets (both models agree)
- Benchmarks your edges against proven system

### 5. Backtesting CLI (`scripts/run_backtest.py`)

Complete command-line interface for backtesting:

**Commands:**
```bash
# Run standard backtest
run_backtest.py run --start-season 2020 --end-season 2023

# Run walk-forward validation
run_backtest.py walk-forward --train-window 2 --test-window 1

# Optimize edge threshold
run_backtest.py optimize --min-threshold 1.0 --max-threshold 8.0

# Analyze results for biases
run_backtest.py analyze --season 2023
```

### 6. Comprehensive Documentation

**`docs/BACKTEST_GUIDE.md`** - 600+ line guide covering:
- Complete architecture overview
- Step-by-step setup instructions
- Data collection procedures
- Running backtests
- Validating predictions
- Comparing with Massey
- Performance metrics explained
- Optimization techniques
- Best practices
- Troubleshooting

---

## 📊 Your Week 9 Data Analysis

Based on your CSV (`week9_edges_actual_only.csv`):

### Games Analyzed: 13 NFL Week 9 matchups

**Top 3 Strongest Edges:**
1. **GB vs CAR** (-12.5): 6.15 point edge, HOME bet
2. **LAC vs TEN** (-9.5): 6.04 point edge, HOME bet
3. **DET vs MIN** (-8.5): 4.96 point edge, HOME bet

**Edge Distribution:**
- 6+ point edges: 3 games (strong bets)
- 4-6 point edges: 5 games (good bets)
- 2-4 point edges: 4 games (moderate bets)
- <2 point edges: 1 game (marginal bet)

**Factors Considered:**
- Power ratings (14.84 to -10.40 points)
- Travel distance (251 to 2,547 miles)
- Travel fatigue adjustments (0 to 0.45 pts)
- Timezone adjustments (0 to 0.25 pts)
- Divisional matchups (5 of 13 games)

---

## 🚀 Quick Start Guide

### Immediate Actions (Validate Week 9)

**1. Validate Week 9 CSV Against Current Data**

```bash
python scripts/validate_week9_edges.py \
    --csv-path "C:\Users\omall\Downloads\week9_edges_actual_only.csv" \
    --output "reports/week9_validation.txt"
```

This will:
- Recalculate edges using your current power ratings
- Compare with CSV predictions
- Identify any discrepancies
- Provide go/no-go recommendations

**2. Compare with Massey Ratings**

```bash
# First, scrape latest Massey predictions
uv run walters-analyzer scrape-massey --data-type games

# Then compare
python scripts/compare_massey_week9.py \
    --csv-path "C:\Users\omall\Downloads\week9_edges_actual_only.csv" \
    --massey-path "data/massey_ratings/games_*.csv" \
    --output "reports/week9_massey_comparison.txt"
```

This will:
- Compare your edges vs Massey's proven system
- Identify agreement/disagreement zones
- Highlight highest confidence bets

**3. Scrape Live Week 9 Data**

```bash
# Scrape current odds
uv run walters-analyzer scrape-overtime --sport nfl

# Scrape current injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Scrape weather forecasts
uv run walters-analyzer scrape-weather
```

### Medium-Term Actions (Build Historical Database)

**4. Collect Historical Game Data**

```bash
# Collect 2020-2024 NFL seasons
python scripts/collect_historical_games.py \
    --sport nfl \
    --start-season 2020 \
    --end-season 2024
```

Expected time: ~5-10 minutes
Expected games: ~1,300 games (5 seasons × ~270 games/season)

**5. Collect Historical Odds**

**Option A:** Use Pro Football Reference (automated, but may be incomplete)

```bash
python scripts/collect_historical_odds.py \
    --source pfr \
    --start-season 2020 \
    --end-season 2024
```

**Option B:** Manual CSV Import (recommended for accuracy)

1. Download historical odds from:
   - https://www.sportsoddshistory.com/nfl-game-season/
   - https://sportsbookreviewsonline.com/scoresoddsarchives/nfl/

2. Import:

```bash
python scripts/collect_historical_odds.py \
    --source csv \
    --csv-path "path/to/historical_nfl_odds.csv" \
    --start-season 2020 \
    --end-season 2024
```

### Long-Term Actions (Validate Strategy)

**6. Run Comprehensive Backtest**

```bash
python scripts/run_backtest.py run \
    --start-season 2020 \
    --end-season 2023 \
    --min-edge 2.0 \
    --bankroll 10000 \
    --output "reports/backtest_full.txt"
```

This will:
- Test your Billy Walters methodology on 4 years of data
- Calculate ROI, Sharpe ratio, CLV, max drawdown
- Show performance by star rating
- Generate detailed bet-by-bet report

**7. Optimize Edge Threshold**

```bash
python scripts/run_backtest.py optimize \
    --start-season 2020 \
    --end-season 2023 \
    --min-threshold 1.0 \
    --max-threshold 8.0 \
    --step 0.5
```

This will:
- Test different edge thresholds (1.0, 1.5, 2.0, ... 8.0 points)
- Find optimal threshold that maximizes ROI
- Show trade-off between bet frequency and profitability

**8. Analyze for Biases**

```bash
python scripts/run_backtest.py analyze --season 2023
```

This will:
- Test statistical significance of results
- Detect home/away biases
- Detect favorite/underdog biases
- Compare to benchmark strategies

---

## 📈 Expected Outcomes

### If Model is Valid:

✅ **ROI: 5-15%** (after juice)
✅ **Win Rate: 54-58%** (need 52.38% to break even at -110)
✅ **Positive CLV: +0.5 to +2.0 points** (beating closing line)
✅ **Sharpe Ratio: >1.0** (good risk-adjusted returns)
✅ **Statistical significance: p < 0.05**
✅ **Agreement with Massey: >70%** (side agreement)

### Red Flags to Watch For:

⚠️ **ROI: <3%** → Model may not have real edge
⚠️ **Win Rate: <53%** → Not covering juice
⚠️ **Negative CLV** → Betting worse than closing line (bad sign)
⚠️ **Sharpe Ratio: <0.5** → High volatility relative to returns
⚠️ **p-value: >0.05** → Results could be due to luck
⚠️ **Disagreement with Massey: >50%** → Methodology may need review

---

## 🎓 Key Learnings & Best Practices

### 1. Data Quality is Critical

- **Use multiple odds sources** - Single source may have errors
- **Verify game results** - Check scores against multiple sites
- **Track data freshness** - Old data = bad predictions

### 2. CLV is King

- **Closing Line Value (CLV)** is the #1 indicator of betting skill
- If your average CLV is positive, you're beating the market
- Target: **+0.5 points or better**
- Track this religiously for every bet

### 3. Sample Size Matters

- Need **100+ bets minimum** for statistical confidence
- Don't judge strategy on 1 week or 1 month
- Use walk-forward validation to avoid overfitting

### 4. Biases Are Real

- Everyone has biases (home teams, favorites, certain situations)
- Run bias analysis regularly
- Adjust strategy based on findings

### 5. Compare to Benchmarks

- Always compare to:
  - Random betting (-4.8% ROI at -110 juice)
  - Always betting favorites (-8% historical ROI)
  - Massey Ratings (proven system)
  - Market closing lines (CLV)

### 6. Optimize Conservatively

- Don't overfit to historical data
- Use walk-forward validation
- Keep edge thresholds reasonable (2-3+ points)
- Higher threshold = fewer bets but higher ROI

---

## 📁 Files Created

### Core Infrastructure
```
walters_analyzer/
├── historical_db.py                 # Database management
└── backtest/
    ├── __init__.py
    ├── engine.py                    # Backtesting engine
    ├── metrics.py                   # Performance metrics
    └── validation.py                # Strategy validation

scripts/
├── collect_historical_games.py      # ESPN game scraper
├── collect_historical_odds.py       # Odds collector
├── run_backtest.py                  # Backtesting CLI
├── validate_week9_edges.py          # Week 9 validator
└── compare_massey_week9.py          # Massey comparison

docs/
└── BACKTEST_GUIDE.md                # Complete documentation

data/historical/
└── historical_games.db              # SQLite database (created on first run)
```

---

## 🔄 Workflow Summary

### Weekly Betting Workflow (Production)

```
Week N-1 (before games)
│
├─ Scrape odds (overtime.ag)
├─ Scrape injuries (ESPN)
├─ Scrape weather (AccuWeather)
├─ Scrape Massey predictions
│
├─ Calculate power ratings
├─ Calculate S/W/E factors
├─ Generate edge calculations
├─ Create betting card CSV
│
├─ Validate edges (compare with Massey)
├─ Review bet recommendations
├─ Place bets (gates passed)
│
Week N (during/after games)
│
├─ Track results
├─ Calculate CLV vs closing lines
├─ Update power ratings
└─ Log to CLV tracker
```

### Monthly Validation Workflow

```
End of Month
│
├─ Collect completed games data
├─ Add to historical database
│
├─ Run backtest on new data
├─ Calculate monthly performance
│
├─ Analyze for biases
├─ Check statistical significance
│
├─ Review factor weights
├─ Optimize edge thresholds
│
└─ Adjust strategy if needed
```

---

## ✅ Implementation Status

### ✅ Completed (Ready to Use)

- [x] Historical database schema
- [x] Game data collection (ESPN API)
- [x] Odds data collection (PFR + CSV import)
- [x] Complete backtesting engine
- [x] Performance metrics calculation
- [x] Strategy validation tools
- [x] Week 9 validation script
- [x] Massey comparison script
- [x] Comprehensive CLI
- [x] Full documentation

### ⏳ Pending (Optional Enhancements)

- [ ] Historical injury data backfill (could scrape past ESPN reports)
- [ ] Historical weather data backfill (could use historical weather APIs)
- [ ] Multi-source odds aggregation (DraftKings, FanDuel APIs)
- [ ] Real-time line movement tracking
- [ ] Automated daily scraping (Task Scheduler/cron)
- [ ] Web dashboard for results visualization
- [ ] Monte Carlo simulation for confidence intervals

### 🎯 Ready for Production

The current implementation is **production-ready** for:
1. ✅ Validating Week 9 predictions
2. ✅ Backtesting historical performance
3. ✅ Optimizing strategy parameters
4. ✅ Comparing with Massey Ratings
5. ✅ Detecting biases and weaknesses

---

## 🆘 Getting Help

### Documentation
- **Full Guide:** `docs/BACKTEST_GUIDE.md`
- **Methodology:** `docs/METHODOLOGY.md` (if exists)
- **Commands:** `CLAUDE.md`

### Quick Reference
```bash
# See all backtest commands
python scripts/run_backtest.py --help

# See validation options
python scripts/validate_week9_edges.py --help

# See Massey comparison options
python scripts/compare_massey_week9.py --help
```

### Troubleshooting
- Check database: `data/historical/historical_games.db`
- Check data files: `data/massey_ratings/`, `data/overtime_live/`
- Verify CSV format matches expected schema
- Ensure all dependencies installed: `uv sync`

---

## 🎉 Next Steps

### This Weekend (Week 9):

1. ✅ **Validate your Week 9 CSV** against current data
2. ✅ **Compare with Massey** for confidence check
3. ✅ **Scrape live data** (odds/injuries/weather)
4. ✅ **Make informed betting decisions**

### This Month:

5. **Collect historical data** (2020-2024)
6. **Run full backtest** on 4+ years
7. **Analyze results** for biases and significance
8. **Optimize parameters** based on findings

### Ongoing:

9. **Track CLV** for every bet
10. **Monthly backtests** with new data
11. **Refine strategy** based on learnings
12. **Document changes** and results

---

## 📊 Success Metrics

Track these metrics monthly:

| Metric | Target | Your Result |
|--------|--------|-------------|
| ROI | >5% | ___ |
| Win Rate | >54% | ___ |
| Avg CLV | >+0.5 pts | ___ |
| Sharpe Ratio | >1.0 | ___ |
| Positive CLV % | >60% | ___ |
| Agreement w/ Massey | >70% | ___ |

If you hit these targets consistently over 100+ bets, your model has real edge.

---

**Good luck with Week 9! 🏈💰**

*Remember: Past performance doesn't guarantee future results. Bet responsibly.*
