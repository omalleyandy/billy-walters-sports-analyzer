# Power Rating System - Quick Reference

**Status:** ✅ Production Ready | **Validated:** 125 Real Games | **Accuracy:** 77.6%

---

## Quick Start

### Run Backtest
```bash
python scripts/run_power_rating_backtest.py
```

### Run Tests
```bash
python -m pytest tests/test_power_ratings.py tests/test_backtest.py -v
```

### Use in Code
```python
from walters_analyzer.valuation.core import BillyWaltersValuation

bw = BillyWaltersValuation(sport="NFL")
spread = bw.calculate_predicted_spread("Kansas City", "Buffalo")
print(f"Predicted: {spread:+.1f}")  # Returns: +3.5
```

---

## Files

| File | Purpose |
|------|---------|
| `walters_analyzer/valuation/power_ratings.py` | Core system (520 lines) |
| `walters_analyzer/backtest/power_rating_backtest.py` | Backtest engine (360 lines) |
| `tests/test_power_ratings.py` | Core tests (23 tests) |
| `tests/test_backtest.py` | Backtest tests (16 tests) |
| `scripts/run_power_rating_backtest.py` | Run backtest script |
| `data/nfl_2025_games_weeks_1_9.json` | Historical game data (125 games) |

---

## Results

```
Winner Accuracy:  77.6% (97/125 correct)
ATS Win Rate:     52.8% (66-59-0 record)
Mean Error:       8.48 points
Median Error:     5.70 points
Test Coverage:    39/39 tests passing (100%)
```

---

## Documentation

1. **POWER_RATING_SYSTEM_COMPLETE.md** - Full system documentation
2. **BACKTEST_VALIDATION_COMPLETE.md** - Detailed validation results
3. **POWER_RATING_BACKTEST_REPORT.md** - Generated backtest report
4. **IMPLEMENTATION_COMPLETE_SUMMARY.md** - Complete implementation summary

---

## What It Does

✅ Predicts NFL game spreads using Billy Walters' 90/10 formula  
✅ Updates team ratings based on actual results  
✅ Tracks prediction accuracy and performance metrics  
✅ Validates against real-world game data  
✅ Integrates with injury analysis and market data  

---

## Key Features

- **90/10 Formula:** `New Rating = 0.9 × Old + 0.1 × Performance`
- **Home Field Advantage:** 2.0 points
- **JSON Persistence:** Auto-save ratings after each game
- **Full History:** Track rating evolution over time
- **Backtesting:** Validate on historical data
- **Integration Ready:** Works with edge detection (coming next)

---

## Next Steps

With power ratings validated, ready to implement:
1. **Edge Detection System** - Compare our lines to market
2. **S-W-E Factor Calculator** - Situational adjustments
3. **Kelly Criterion** - Optimal bet sizing

---

**Created:** November 8, 2025  
**Validated:** 125 NFL 2025 games, Weeks 1-9 (Through November 7, 2025)  
**Status:** ✅ Ready for Production

