# E-Factor Quick Start Guide

**Goal**: Get real E-Factors running in 10 minutes

---

## 1. Initialize Real Data (2 min)

```python
import asyncio
from walters_analyzer.data_integration.real_data_integrator import RealDataIntegrator

async def main():
    # Create integrator
    integrator = RealDataIntegrator()
    await integrator.initialize()

    # Fetch injuries for your team
    injuries = await integrator.fetch_nfl_injuries("DAL")
    print(f"Injuries: {injuries.data if injuries else 'None'}")

    # Fetch for all teams (takes 15 sec)
    all_teams = await integrator.fetch_all_nfl_teams(data_type="injuries")
    print(f"Fetched: {len(all_teams)} teams")

    await integrator.close()

asyncio.run(main())
```

**Output**:
```
Injuries: {'injuries': [...], 'team': 'DAL'}
Fetched: 32 teams
```

---

## 2. Apply Decay to Old News (1 min)

```python
from walters_analyzer.core.efactor_decay import NewsDecayFunction

decay = NewsDecayFunction()

# Your QB went down 5 days ago, impact was -8.0 pts
current_impact = decay.apply_decay(
    original_impact=-8.0,
    days_elapsed=5,
    event_type="key_player_out"
)

print(f"Original: -8.0 pts")
print(f"After 5 days: {current_impact:.1f} pts")
print(f"Decay: {(1 - current_impact / -8.0) * 100:.0f}%")

# Get confidence boost for fresh news
confidence = decay.get_recency_confidence(
    days_since_news=0,
    signal_strength="VERY_STRONG"
)
print(f"Fresh signal confidence boost: {confidence:+.0%}")
```

**Output**:
```
Original: -8.0 pts
After 5 days: -6.3 pts
Decay: 21%
Fresh signal confidence boost: +20%
```

---

## 3. Track Source Quality (2 min)

```python
from walters_analyzer.core.efactor_source_quality import SourceQualityTracker

tracker = SourceQualityTracker()

# Record what ESPN said vs what actually happened
tracker.record_observation(
    source_name="espn_injuries",
    event_id="DAL_QB_W13",
    event_type="injury",
    observation={"player": "Dak", "status": "out", "prognosis": "8 weeks"},
    actual_outcome={"player": "Dak", "status": "out", "days_out": 7},
    accuracy_score=0.9,  # 8 vs 7 days is pretty close
    latency_hours=0.5
)

# Get quality score
score = tracker.get_source_score("espn_injuries")
print(f"ESPN Quality Score: {score.overall_score:.2f}/1.0")

# Adjust your confidence based on source quality
confidence = tracker.get_confidence_adjustment(["espn_injuries"])
print(f"Adjusted Confidence: {confidence:.2f}")
```

**Output**:
```
ESPN Quality Score: 0.88/1.0
Adjusted Confidence: 0.89
```

---

## 4. Record Predictions (2 min)

```python
import asyncio
from walters_analyzer.core.efactor_calibration import EFactorCalibrator

async def main():
    calibrator = EFactorCalibrator()
    await calibrator.initialize()

    # Record your prediction BEFORE the game
    await calibrator.record_prediction(
        game_id="KC@DAL_W13",
        week=13,
        team="DAL",
        league="nfl",
        predicted_edge_pct=8.5,
        efactor_adjustment=-3.0,  # QB injury adjusted it down
        efactor_sources=["injury_qb"],
        confidence_level="MEDIUM"
    )

    print("✓ Prediction recorded")

    await calibrator.close()

asyncio.run(main())
```

---

## 5. Record Outcomes (1 min)

```python
import asyncio
from walters_analyzer.core.efactor_calibration import EFactorCalibrator

async def main():
    calibrator = EFactorCalibrator()
    await calibrator.initialize()

    # After the game: Record what actually happened
    await calibrator.record_outcome(
        game_id="KC@DAL_W13",
        actual_result="LOSS",      # Your pick lost
        actual_margin=-2.5,        # DAL lost by 2.5
        closing_line_value=-0.02   # -2% return on that bet
    )

    print("✓ Outcome recorded")

    # Get report
    report = await calibrator.get_calibration_report()
    print(f"ATS: {report.ats_win_rate:.1f}%")
    print(f"ROI: {report.roi_per_bet_pct:+.2f}%")

    await calibrator.close()

asyncio.run(main())
```

**Output**:
```
✓ Outcome recorded
ATS: 58.3%
ROI: +1.25%
```

---

## 6. Get Full Report (1 min)

```python
import asyncio
from walters_analyzer.core.efactor_calibration import EFactorCalibrator

async def main():
    calibrator = EFactorCalibrator()
    await calibrator.initialize()

    # Print full report
    await calibrator.print_report(league="nfl", weeks=4)

    # Export to JSON
    await calibrator.export_report("output/calibration.json")

    await calibrator.close()

asyncio.run(main())
```

**Output**:
```
======================================================================
E-FACTOR CALIBRATION REPORT - NFL
======================================================================

📊 OVERVIEW:
  Predictions: 47
  Outcomes: 45
  Sample Size: 45/47

📈 EDGE ACCURACY:
  Predicted Edge (avg): +7.2%
  Actual Margin (avg): +6.8%
  RMSE: 3.1pts

🎯 ATS PERFORMANCE:
  Win Rate: 58.3% (26-18-1)
  Total Bets: 45
  ROI: +1.25% per bet

📰 E-FACTOR IMPACT:
  Average Adjustment: +1.5 pts
  Max Adjustment: +8.0 pts
  Min Adjustment: -6.5 pts

🔍 SOURCE QUALITY:
  nfl_injuries: 92.0%
  espn_injuries: 88.0%
  espn_news: 72.0%

💡 RECOMMENDATIONS:
  • Good edge accuracy (RMSE: 3.1pts)
  • Excellent ATS record (58.3%). Model is working well.
  • Source 'nfl_injuries' performing well (92%). Consider increasing weight.
```

---

## Common Patterns

### Pattern 1: Daily Check

```python
# Every morning, check if you have fresh data
async def check_today():
    integrator = RealDataIntegrator()
    await integrator.initialize()

    # Check source health
    health = integrator.get_source_health()
    for source, stats in health.items():
        if stats['success_rate'] < 90:
            print(f"WARNING: {source} success rate is {stats['success_rate']:.0f}%")

    await integrator.close()
```

### Pattern 2: Weekly Analysis

```python
# Every Wednesday, analyze the week
async def analyze_week(week_num):
    integrator = RealDataIntegrator()
    await integrator.initialize()

    # Fetch all data
    injuries = await integrator.fetch_all_nfl_teams("injuries")
    news = await integrator.fetch_all_nfl_teams("news")

    # Export for edge detection
    await integrator.export_data(week=week_num, league="nfl")

    # Run edge detector (built-in command)
    # /edge-detector --league nfl

    await integrator.close()
```

### Pattern 3: Monthly Review

```python
# Last day of month, review everything
async def monthly_review():
    calibrator = EFactorCalibrator()
    await calibrator.initialize()

    # Get last 4 weeks
    report = await calibrator.get_calibration_report(weeks=4)

    # Print and export
    await calibrator.print_report(weeks=4)
    await calibrator.export_report(f"output/monthly_{datetime.now().strftime('%Y%m')}.json")

    # Check which sources are working
    quality = SourceQualityTracker()
    quality.print_report()

    await calibrator.close()
```

---

## Key Commands

```bash
# Check if everything is working
uv run python -c "
from walters_analyzer.data_integration.real_data_integrator import RealDataIntegrator
import asyncio
async def test():
    i = RealDataIntegrator()
    await i.initialize()
    h = i.get_source_health()
    for s, _ in list(h.items())[:2]:
        print(f'✓ {s}')
    await i.close()
asyncio.run(test())
"

# View decay curves
uv run python src/walters_analyzer/core/efactor_decay.py

# View source quality
uv run python src/walters_analyzer/core/efactor_source_quality.py

# View calibration
uv run python src/walters_analyzer/core/efactor_calibration.py
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No data returned` | Check Internet, verify API keys in `.env` |
| `Low confidence` | Check source quality score (< 0.70 = low) |
| `Stale data` | Clear cache or wait for fresh data |
| `Source failing` | Check `get_source_health()` for error rates |

---

## Next Steps

1. **Week 1**: Run daily data collection
2. **Week 2**: Record predictions and outcomes
3. **Week 4**: Generate first calibration report
4. **Week 8**: Review and adjust decay parameters
5. **Month 3**: Full production deployment

---

**For full documentation**: See [EFACTOR_PRODUCTION_SYSTEM.md](EFACTOR_PRODUCTION_SYSTEM.md)

**Key Files**:
- Real Data: `src/walters_analyzer/data_integration/real_data_integrator.py`
- Decay: `src/walters_analyzer/core/efactor_decay.py`
- Calibration: `src/walters_analyzer/core/efactor_calibration.py`
- Quality: `src/walters_analyzer/core/efactor_source_quality.py`
