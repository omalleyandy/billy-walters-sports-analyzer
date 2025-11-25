# Edge Detector Workflow Guide

## Overview

The Billy Walters Edge Detector now includes **automatic schedule validation** to ensure you're analyzing the correct week's games. This guide explains the workflow, pre-flight checks, and how to use the system correctly.

## Key Principle: Date/Week Alignment

**The system validates that:**
1. Your current system date matches the week you want to analyze
2. The schedule file contains games for that week
3. The odds data matches the schedule week
4. All data sources are aligned before edge detection begins

This prevents the critical error we discovered: analyzing the wrong week's games with mismatched team matchups.

---

## Pre-Flight Checks

Before running edge detection, the system performs automatic validation:

### What Gets Checked

```
1. Current System Date Detection
   └─ Uses built-in week date ranges (e.g., Week 13 = Nov 27 - Dec 3)

2. Schedule File Validation
   └─ Reads latest ESPN schedule file
   └─ Extracts game dates
   └─ Determines which week the schedule covers

3. Odds File Validation
   └─ Reads latest Overtime.ag odds file
   └─ Extracts game times
   └─ Determines which week the odds cover

4. Cross-Validation
   └─ Compares detected week vs schedule week vs odds week
   └─ Issues warnings if mismatches detected
```

### Example Output

```
================================================================================
PRE-FLIGHT SCHEDULE VALIDATION
================================================================================

Current Date: 2025-11-24 19:49:23
Detected Week: Week 12

Latest Schedule: schedule_nfl_20251124_192224.json
Schedule covers dates: 2025-11-27 to 2025-12-02
[WARNING] Schedule week 13 does not match detected week 12

Latest Odds: api_walters_20251124_191725.json
Odds cover game times: 11/27 13:00 to 12/01 20:15
[WARNING] Odds week 13 does not match detected week 12

================================================================================
[OK] All pre-flight checks passed - ready for edge detection
================================================================================

SCHEDULE WARNING: You are analyzing Week 13 games, but the current
date indicates Week 12. Ensure this is intentional.

ODDS WARNING: Odds are for Week 13, but detected week is 12.
This mismatch may indicate stale data.

[PROCEEDING] Starting edge detection with validated schedule...
```

---

## How to Use

### Standard Workflow (Recommended)

**For upcoming week's games (e.g., Tuesday analyzing Thursday games):**

```bash
# Just run it - system auto-detects current week
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector
```

The system will:
1. Detect current date is Week 12 (if running before Nov 27)
2. Find latest schedule (Week 13 games)
3. Find latest odds (Week 13 games)
4. Issue warnings about the mismatch (intentional - you're prep analyzing)
5. Proceed with Week 13 edge detection

### Advanced: Explicit Week Override

If you need to analyze a different week than current:

```python
# Edit the validator call in main() to force a week
# (This is for special cases only - document why!)
```

---

## Understanding Warnings

### "Schedule week X does not match detected week Y"

**Meaning:** Your schedule file is for a different week than today's date.

**When it's OK:**
- You're prepping for next week's games
- Running analysis in advance

**When it's a problem:**
- You intended to analyze this week but got last week's schedule
- Data collection didn't refresh properly

**Fix:**
```bash
# Re-run data collection to get latest schedule
uv run python scripts/scrapers/scrape_espn_schedule.py --league nfl --week 13
```

### "Odds week X does not match detected week Y"

**Meaning:** Your odds file is for a different week than your schedule.

**When it's OK:**
- Same as above - intentionally prepping

**When it's a problem:**
- Odds are from old data (stale)
- Schedule was refreshed but odds weren't
- Different leagues (NFL vs NCAAF)

**Fix:**
```bash
# Refresh odds data
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

---

## Week Date Reference

### NFL 2025 Season

```
Week 1   : Sept  4 - Sept 10
Week 2   : Sept 11 - Sept 17
...
Week 12  : Nov 20 - Nov 26
Week 13  : Nov 27 - Dec 3    ← Currently relevant
Week 14  : Dec 4  - Dec 10
...
Week 18  : Jan 1  - Jan 7

Playoffs : Jan 10 - Feb 1
```

### NCAAF 2025 Season

```
Week 1   : Aug 28 - Sept 3
Week 2   : Sept 4 - Sept 10
...
Week 13  : Nov 20 - Nov 26
Week 14  : Nov 25 - Dec 3    ← Overlaps with NFL Week 13!
...
Week 15  : Dec 4  - Dec 10

Bowl Season : Dec 20 - Jan 12
```

---

## Pre-Flight Check Components

### ScheduleValidator Class

Located in: `src/walters_analyzer/utils/schedule_validator.py`

**Key Methods:**

```python
# Detect current week from system date
validator = ScheduleValidator()
week_num, week_label = validator.detect_current_nfl_week()
# Returns: (13, "Week 13")

# Validate schedule file matches week
det_week, sched_week, is_match = validator.validate_schedule_week(
    schedule_file, league="nfl"
)

# Validate odds file matches week
det_week, odds_week, is_match = validator.validate_odds_week(
    odds_file, league="nfl"
)

# Get complete pre-flight report
report = validator.get_pre_flight_report(league="nfl")
```

---

## Integration with Edge Detector

### Edge Detector Main Function

The `main()` function in `billy_walters_edge_detector.py` now:

1. **Imports ScheduleValidator**
   ```python
   from walters_analyzer.utils.schedule_validator import ScheduleValidator
   ```

2. **Runs Pre-Flight Checks**
   ```python
   validator = ScheduleValidator()
   nfl_report = validator.get_pre_flight_report(league="nfl")
   ```

3. **Issues Warnings (if needed)**
   ```python
   if not nfl_report["schedule_validation"]["is_match"]:
       logger.warning(f"SCHEDULE WARNING: ...")
   ```

4. **Proceeds with Edge Detection**
   ```python
   detector = BillyWaltersEdgeDetector()
   # ... rest of analysis
   ```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Edge Detector Main Function                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Schedule Validator          │
        │  - Detect current week       │
        │  - Parse schedule dates      │
        │  - Parse odds dates          │
        │  - Compare & validate        │
        └──────────────┬───────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
    ┌──────────────┐        ┌──────────────┐
    │ Match OK     │        │ Mismatch     │
    │ (Proceed)    │        │ (Warn User)  │
    └──────┬───────┘        └──────┬───────┘
           │                       │
           │       ┌───────────────┘
           │       │
           ▼       ▼
    ┌─────────────────────────────────────┐
    │ Load Data & Run Edge Detection      │
    │ - Load odds (Overtime.ag)           │
    │ - Load power ratings (Massey/Prop)  │
    │ - Analyze games                     │
    │ - Generate edges & reports          │
    └─────────────────────────────────────┘
```

---

## Troubleshooting

### Scenario 1: "I want to analyze Week 13, but I'm running this on Nov 24"

**Solution:** This is normal and expected. The system warns you but proceeds.

```
SCHEDULE WARNING: You are analyzing Week 13 games, but the current
date indicates Week 12. Ensure this is intentional.

[PROCEEDING] Starting edge detection with validated schedule...
```

**This is correct behavior** - you're prepping for the coming week.

---

### Scenario 2: "The odds are from last week"

**Symptom:**
```
ODDS WARNING: Odds are for Week 12, but detected week is 13.
This mismatch may indicate stale data.
```

**Fix:**
```bash
# Refresh the odds data
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# Then re-run edge detection
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector
```

---

### Scenario 3: "Schedule has different games than what I see on ESPN.com"

**Cause:** Schedule file is stale (from previous day)

**Fix:**
```bash
# Fetch latest schedule
uv run python scripts/scrapers/scrape_espn_schedule.py --league nfl --week 13

# Verify with pre-flight check
uv run python src/walters_analyzer/utils/schedule_validator.py

# Re-run edge detector
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector
```

---

## Weekly Workflow

### Tuesday Before Thursday Games (NFL Week 13)

```bash
# 1. Collect all current data
uv run python scripts/scrapers/scrape_espn_schedule.py --league nfl --week 13
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
uv run python scripts/scrapers/scrape_massey_games.py
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl

# 2. Run pre-flight validation (standalone)
uv run python src/walters_analyzer/utils/schedule_validator.py

# 3. Run edge detection (auto-validates + analyzes)
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector

# 4. Review warnings and edges
# (System shows if week mismatch is intentional or problematic)
```

---

## FAQ

**Q: Should I run edge detection before or after the week starts?**

A: You can run it either way. The system validates and warns you:
- Before: "You're analyzing Week 13, but it's Week 12" (prep work - OK)
- After: "You're analyzing Week 13, and it's Week 13" (live analysis - OK)

Both are fine if intentional.

---

**Q: What if the warnings show a different week than I expect?**

A: Check your data:
1. Run `schedule_validator.py` standalone
2. Review the "Schedule covers dates" output
3. If wrong, re-run data collection for your target week

---

**Q: Can I manually override the week detection?**

A: Yes, but document why:
1. Edit the `validator` call in `main()`
2. Hardcode the week you want
3. Add a comment explaining why

Example:
```python
# OVERRIDE: Using Week 13 for historical analysis (request from Andy)
week_override = 13
nfl_report["detected_week"] = week_override
```

---

**Q: Does this work for NCAAF too?**

A: Yes! The validator supports both:
```bash
# Check NCAAF schedule validation
uv run python src/walters_analyzer/utils/schedule_validator.py
# (Shows both NFL and NCAAF sections)
```

---

## References

- **Schedule Validator**: `src/walters_analyzer/utils/schedule_validator.py`
- **Edge Detector (with pre-flight)**: `src/walters_analyzer/valuation/billy_walters_edge_detector.py`
- **Data Collection Guides**: `docs/guides/NFL_DATA_COLLECTION_WORKFLOW.md`, `NCAAF_DATA_COLLECTION_WORKFLOW.md`

