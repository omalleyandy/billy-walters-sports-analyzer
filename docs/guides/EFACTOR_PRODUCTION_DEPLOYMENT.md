# E-Factor Production Deployment Guide

**Last Updated**: 2025-11-28
**Status**: Ready for Phase 1 Deployment
**Time to Deploy**: ~5 minutes

---

## Quick Start (5 minutes)

**One-time setup:**
```bash
# Deploy to production (initializes all components)
uv run python scripts/deployment/deploy_efactor.py --league nfl

# Verify deployment
ls -la output/efactor/
# Should show: calibration.db, data/, reports/
```

**That's it!** E-Factor system is now ready for production use.

---

## Phase 1: Weekly Workflow (Current)

### Tuesday - Data Collection & Edge Detection

**Step 1: Collect All Data** (7 minutes)
```bash
/collect-all-data
# Automatically includes E-Factor data collection:
# - Injuries from ESPN/NFL.com
# - News from ESPN, transactions clients
# - Weather for all stadiums
# - Odds from Action Network
# - Power ratings from Massey
```

**Step 2: Run Edge Detection** (2 minutes)
```bash
/edge-detector
# Automatically integrates E-Factor:
# - Fetches news/injury data
# - Applies decay to old news
# - Adjusts edges by E-Factor impact
# - Shows E-Factor contribution to each pick
```

**Step 3: Record Predictions** (10 seconds per game)
```bash
# For each pick you make
uv run python scripts/deployment/record_prediction.py \
    --game KC@DAL \
    --week 13 \
    --edge 5.5 \
    --efactor -2.0 \
    --sources espn_injuries,espn_news

# Or batch script it (see Advanced section)
```

### Sunday-Monday - Record Outcomes

**Step 4: Record Results** (30 seconds per game)
```bash
# After each game finishes
uv run python scripts/deployment/record_outcome.py \
    --game KC@DAL \
    --result WIN \
    --margin 3.5 \
    --clv 0.05
```

### Weekly Review - Calibration Report

**Step 5: Generate Report** (1 minute)
```bash
# Generate calibration report
uv run python scripts/deployment/calibration_report.py --weeks 1

# Sample output:
# E-FACTOR CALIBRATION REPORT - NFL
# ===================================
#
# 📊 OVERVIEW:
#   Predictions: 16
#   Outcomes: 16
#   Sample Size: 16/16
#
# 📈 EDGE ACCURACY:
#   Predicted Edge (avg): +3.2%
#   Actual Margin (avg): +2.8%
#   RMSE: 2.4 pts
#
# 🎯 ATS PERFORMANCE:
#   Win Rate: 62.5% (10-6-0)
#   Total Bets: 16
#   ROI: +1.85% per bet
#
# 📰 E-FACTOR IMPACT:
#   Average Adjustment: -1.2 pts
#   Max Adjustment: -8.0 pts
#   Min Adjustment: +0.5 pts
#
# 🔍 SOURCE QUALITY:
#   espn_injuries: 95.0%
#   espn_news: 88.0%
#
# 💡 RECOMMENDATIONS:
#   • E-Factors have good impact. Continue current weighting.
#   • ESPN Injuries performing well (95%). Increase weight slightly.
```

---

## Deployment Scripts Reference

### 1. deploy_efactor.py

**Purpose**: One-time initialization of E-Factor system

**What it does**:
- Creates output directories
- Initializes Real Data Integrator
- Creates SQLite calibration database
- Tests all components
- Prints deployment summary

**Usage**:
```bash
uv run python scripts/deployment/deploy_efactor.py --league nfl
uv run python scripts/deployment/deploy_efactor.py --league ncaaf
```

**Output**:
```
E-FACTOR PRODUCTION DEPLOYMENT
✓ Created: output/efactor
✓ Real Data Integrator initialized
✓ Calibration DB created: output/efactor/calibration.db
✓ Decay function working: -8.0 → -5.9 pts, confidence: +20%
✓ Source quality tracker working: ESPN score = 0.85
✓ Edge calculator with E-Factor support initialized

E-Factor system deployed successfully!
📁 Output directory: output/efactor
📊 Calibration DB: output/efactor/calibration.db
📈 Data cache: output/efactor/data
📋 Reports: output/efactor/reports
```

### 2. record_prediction.py

**Purpose**: Record edge prediction before game

**When to use**: Immediately after generating picks

**Usage**:
```bash
# Single game
uv run python scripts/deployment/record_prediction.py \
    --game KC@DAL \
    --week 13 \
    --edge 5.5 \
    --efactor -2.0 \
    --sources espn_injuries,espn_news

# Parameters:
# --game: Game ID (e.g., KC@DAL, LSU@BAMA)
# --week: Week number (1-18 for NFL, 1-15 for NCAAF)
# --edge: Predicted edge percentage (e.g., 5.5)
# --efactor: E-Factor adjustment in points (e.g., -2.0)
# --sources: Comma-separated list of E-Factor sources
# --league: "nfl" or "ncaaf"
```

**Output**:
```
✓ Recorded prediction: KC@DAL Week 13, edge=+5.5%, E-Factor=-2.0pts
```

### 3. record_outcome.py

**Purpose**: Record game result after game finishes

**When to use**: After all games in week are complete

**Usage**:
```bash
uv run python scripts/deployment/record_outcome.py \
    --game KC@DAL \
    --result WIN \
    --margin 3.5 \
    --clv 0.05

# Parameters:
# --game: Game ID
# --result: WIN, LOSS, or PUSH
# --margin: Actual point margin (positive if prediction won)
# --clv: Closing Line Value (closing odds minus what you bet)
# --league: "nfl" or "ncaaf"
```

**Output**:
```
✓ Recorded outcome: KC@DAL WIN, margin=+3.5, CLV=+0.05
  ATS: 62.5% (10-6)
  ROI: +1.85%
  E-Factor impact: -1.2 pts avg
```

### 4. calibration_report.py

**Purpose**: Weekly calibration analysis and recommendations

**When to use**: After all outcomes are recorded for week

**Usage**:
```bash
# Weekly report
uv run python scripts/deployment/calibration_report.py --weeks 1

# Monthly report
uv run python scripts/deployment/calibration_report.py --weeks 4

# Export to JSON
uv run python scripts/deployment/calibration_report.py --weeks 1 --export
```

**Output**: Pretty-printed calibration metrics with recommendations

---

## Advanced: Batch Recording Script

Create `scripts/deployment/batch_record_predictions.py` for recording multiple games at once:

```python
"""Batch record predictions from picks output."""
import asyncio
import json
from pathlib import Path
from record_prediction import record_prediction

async def batch_record(picks_file: str, league: str = "nfl") -> None:
    """Record predictions from picks JSON file."""
    picks = json.loads(Path(picks_file).read_text())

    for pick in picks["picks"]:
        await record_prediction(
            game=pick["game"],
            week=pick["week"],
            edge=pick["edge_pct"],
            efactor=pick.get("efactor_adjustment", 0.0),
            sources=",".join(pick.get("efactor_sources", [])),
            league=league
        )
        print(f"✓ Recorded: {pick['game']}")

# Usage:
# uv run python scripts/deployment/batch_record_predictions.py \
#     --file output/picks_week13.json --league nfl
```

---

## Integration Points

### 1. /collect-all-data Workflow

Currently integrates:
- Power ratings collection
- Schedule validation
- Odds collection
- Weather collection
- **NEW: E-Factor data fetching** (injuries, news)

### 2. /edge-detector Workflow

Currently includes:
- Base edge calculation
- S-Factor adjustment
- Key numbers adjustment
- Sharp money integration
- **NEW: E-Factor adjustment** (auto-fetches data, applies decay, adjusts edges)

### 3. Data Storage

```
output/
├── efactor/
│   ├── calibration.db        # SQLite predictions/outcomes
│   ├── data/
│   │   ├── injuries_cache/
│   │   ├── news_cache/
│   │   └── source_health.json
│   └── reports/
│       ├── calibration_nfl_weeks1.json
│       ├── calibration_ncaaf_weeks1.json
│       └── source_quality_report.json
```

---

## Phase 2 Timeline (Weeks 2-4)

Once Phase 1 is stable:

### Week 2-3: Calibration Stabilization
- Record all predictions consistently
- Record all outcomes after games
- Review weekly reports
- Adjust E-Factor weights if needed

### Week 4: First Major Review
- Full calibration report on 3 weeks of data
- Analyze source quality scores
- Review E-Factor impact distribution
- Validate decay parameters

---

## Phase 3 Timeline (Month 2)

### Weeks 5-8: Parameter Tuning
- Based on calibration data, fine-tune:
  - Decay parameters (half-lives per event type)
  - Source quality weights
  - E-Factor confidence adjustments
  - Overall edge impact scaling

### End of Month: Generate Recommendations
- Analyze which E-Factors help most
- Identify best/worst data sources
- Calculate per-source ROI contribution
- Recommend weight changes for Phase 4

---

## Phase 4 Timeline (Month 3+)

### Full Production Automation
- Automated daily E-Factor data collection
- Automated prediction recording (from /edge-detector)
- Automated outcome recording (from results checker)
- Automated weekly calibration reports
- Automated parameter adjustments

---

## Troubleshooting

### Error: "No injury data available"

**Cause**: Data source temporarily down

**Solution**: System gracefully degrades
- Falls back to ESPN if NFL.com fails
- Returns None if all sources fail
- Edge detection continues without E-Factor

**To debug**:
```bash
uv run python -c "
import asyncio
from walters_analyzer.data_integration.real_data_integrator import RealDataIntegrator

async def test():
    integrator = RealDataIntegrator()
    await integrator.initialize()
    health = integrator.get_source_health()
    for name, stats in health.items():
        print(f'{name}: {stats[\"success_rate\"]:.0f}%')
    await integrator.close()

asyncio.run(test())
"
```

### Error: "calibration.db locked"

**Cause**: Another process has database open

**Solution**: Close other Python processes or wait 30 seconds

### Edge with E-Factor seems wrong

**Debug steps**:
```bash
# 1. Check decay is working
uv run python -c "
from walters_analyzer.core.efactor_decay import NewsDecayFunction
decay = NewsDecayFunction()
impact = decay.apply_decay(-8.0, 3, event_type='key_player_out')
print(f'Decay test: -8.0 → {impact:.1f}')
"

# 2. Check source quality
uv run python scripts/deployment/calibration_report.py

# 3. Check real data fetching
uv run python -c "
import asyncio
from walters_analyzer.data_integration.real_data_integrator import RealDataIntegrator

async def test():
    integrator = RealDataIntegrator()
    await integrator.initialize()
    data = await integrator.fetch_nfl_injuries('DAL')
    print(f'DAL injuries: {data}')
    await integrator.close()

asyncio.run(test())
"
```

---

## Success Criteria (Phase 1)

Track these metrics weekly:

| Metric | Target | Status |
|--------|--------|--------|
| Data collection success rate | 95%+ | [Monitor] |
| Predictions recorded | 100% of picks | [Monitor] |
| Outcomes recorded | 100% of games | [Monitor] |
| E-Factor availability | 90%+ | [Monitor] |
| Calibration report generation | 100% | [Monitor] |
| Average E-Factor impact | -3 to +3 pts | [Monitor] |

---

## Next Steps

1. **Run deployment script**:
   ```bash
   uv run python scripts/deployment/deploy_efactor.py --league nfl
   ```

2. **Verify output directory**:
   ```bash
   ls -la output/efactor/
   ```

3. **Run this week's /collect-all-data**:
   ```bash
   /collect-all-data
   ```

4. **Generate edge detector picks**:
   ```bash
   /edge-detector
   ```

5. **Record predictions**:
   ```bash
   uv run python scripts/deployment/record_prediction.py \
       --game [TEAM1]@[TEAM2] --week [W] --edge [E] --efactor [EF]
   ```

6. **After week completes, record outcomes and review**:
   ```bash
   uv run python scripts/deployment/record_outcome.py ...
   uv run python scripts/deployment/calibration_report.py --weeks 1
   ```

---

**Ready to deploy?** Run: `uv run python scripts/deployment/deploy_efactor.py --league nfl`
