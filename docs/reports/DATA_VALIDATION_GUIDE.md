# Data Quality Assurance Guide

## Overview

The Billy Walters system includes comprehensive data validation to ensure edge detection is based on accurate, complete data. **Garbage in, garbage out** - never run analysis on unvalidated data.

## Validation Script

**Location:** `scripts/validation/validate_all_data_sources.py`

**Purpose:** Validates ALL data sources before feeding into edge detection:
1. Overtime odds (spreads, totals, moneylines)
2. Massey power ratings
3. Weather forecasts
4. Injury reports
5. Team name consistency

## Usage

### Basic Commands

```bash
# NFL validation (complete)
uv run python scripts/validation/validate_all_data_sources.py --league nfl --week 10

# NCAAF validation (complete)
uv run python scripts/validation/validate_all_data_sources.py --league ncaaf --week 12

# Skip optional sources
uv run python scripts/validation/validate_all_data_sources.py --league nfl --skip-weather --skip-injuries
```

### Via Slash Command

```bash
# Validates current data
/validate-data
```

## What Gets Validated

### 1. Overtime Odds Data

**Checks:**
- File exists and is < 24 hours old
- Contains games (not empty)
- Team names are valid (3+ characters, alphanumeric)
- Spread lines are numeric and reasonable (-50 to +50)
- Spread prices are valid American odds (-1000 to +1000)
- Totals are within expected range (NFL: 20-70, NCAAF: 25-90)
- Moneyline prices are valid integers
- Home/away spreads are inverse (sum to 0)

**Common Errors:**
- `No games found` - Scraped during games (Sunday evening) or outside betting window
- `Spreads not inverse` - Data corruption, rescrape needed
- `Invalid team name` - Mapping issue between Overtime and Massey

### 2. Massey Power Ratings

**Checks:**
- File exists and is < 7 days old
- Expected team count (NFL: 32, NCAAF: 130+)
- All teams have rating values
- Ratings are numeric
- Ratings within expected range (NFL: 0-15, NCAAF: 20-90)
- No missing or null values

**Common Errors:**
- `Missing rating field` - File structure mismatch (NFL uses "rating", NCAAF uses "powerRating")
- `Rating outside expected range` - Team having exceptional season or data error

### 3. Weather Data (Optional)

**Checks:**
- Temperature in realistic range (-20°F to 120°F)
- Wind speed reasonable (0-60 MPH)
- Valid forecast timing

**Common Warnings:**
- `Weather file not found` - Expected for games >7 days away or indoor stadiums
- `Temperature seems unrealistic` - May indicate Fahrenheit/Celsius confusion

### 4. Injury Data (Optional)

**Checks:**
- Player names present
- Positions valid (QB, RB, WR, TE, OL, DL, LB, CB, S, K, P)
- Status valid (OUT, DOUBTFUL, QUESTIONABLE, PROBABLE, IR)
- Impact points in range (0-10)

**Common Warnings:**
- `Injury file not found` - Expected early in week before official reports
- `Unknown position` - Defensive lineman listed as "DE" instead of "DL"

### 5. Team Name Consistency

**Checks:**
- Team mapping file exists
- All teams have valid abbreviations
- Consistency across Overtime odds and Massey ratings

**Common Errors:**
- `Team mapping file not found` - Need to create mapping for new league
- `Invalid abbreviation` - Mapping has empty or single-character value

## Output Format

```
==========================================================================================
BILLY WALTERS DATA QUALITY ASSURANCE REPORT
==========================================================================================
League: NFL
Week: 10
Timestamp: 2025-11-11 02:10:53

[OK] OVERTIME ODDS: PASSED
  Validated 14 games from overtime_nfl_odds_20251110_163851.json

[OK] MASSEY RATINGS: PASSED
  Validated 32 teams from nfl_ratings_20251109_050042.json

[OK] WEATHER: PASSED
  Warnings: 1
    - Weather file not found (expected for games >7 days away)

[OK] INJURIES: PASSED
  Warnings: 1
    - Injury file not found (expected early in week)

[OK] TEAM MAPPING: PASSED
  Validated 32 team mappings

==========================================================================================
SUMMARY
==========================================================================================
Total Checks: 5
Passed: 5
Failed: 0
Warnings: 2

[OK] ALL VALIDATION CHECKS PASSED
Data is ready for edge detection analysis
==========================================================================================
```

## Exit Codes

- **0 (Success):** All checks passed or passed with warnings
- **1 (Failed):** One or more critical errors detected

## Integration with Billy Walters Workflow

### Recommended Workflow

```bash
# Tuesday/Wednesday: Data collection
/collect-all-data

# STEP 1: Validate data quality (CRITICAL)
/validate-data

# If validation passed:
# STEP 2: Run edge detection
/edge-detector

# STEP 3: Generate betting card
/betting-card
```

### Automated Validation

The validation runs automatically in:
1. **Post-data collection hook** (`.claude/hooks/post_data_collection.py`)
2. **Before edge detection** (optional pre-flight check)

## Troubleshooting Common Issues

### "No games found in odds file"

**Cause:** Overtime scraper ran during games or outside betting window

**Solution:**
```bash
# Rescrape odds (best time: Tuesday-Thursday 12 PM - 6 PM ET)
/scrape-overtime
```

### "Massey ratings stale (>7 days old)"

**Cause:** Massey composite not updated recently

**Solution:**
```bash
# Rescrape Massey ratings
/scrape-massey
```

### "Team name mismatch between sources"

**Cause:** Different naming conventions (e.g., "LA Rams" vs "Los Angeles Rams")

**Solution:**
Edit team mapping file:
- NFL: `src/data/nfl_team_mappings.json`
- NCAAF: `src/data/ncaaf_team_mappings.json`

### "Weather forecast missing"

**Cause:** Game is >7 days away or indoor stadium

**Action:** No action needed if:
- Game >7 days away (forecast not available yet)
- Indoor stadium (weather irrelevant)

**Action required if:**
- Game <7 days away and outdoor stadium
- Solution: Manually run weather check

```bash
python check_gameday_weather.py "Team Name" "YYYY-MM-DD HH:MM"
```

## Data Quality Standards

### Billy Walters Quality Thresholds

**EXCELLENT (95-100%)**
- All data sources present
- All validations passed
- No warnings
- → PROCEED with confidence

**GOOD (85-94%)**
- All critical sources present
- Minor warnings only
- → PROCEED with caution

**FAIR (70-84%)**
- Some data missing
- Multiple warnings
- → REVIEW manually before proceeding

**POOR (<70%)**
- Critical data missing
- Multiple errors
- → DO NOT PROCEED - Fix errors first

### Critical vs Optional Data

**Critical (Must Pass):**
- Overtime odds (spreads, totals)
- Massey power ratings
- Team name consistency

**Optional (Warnings OK):**
- Weather forecasts (games >7 days away)
- Injury reports (early in week)

## Extending the Validator

To add new validation checks:

1. Add validator function in `scripts/validation/validate_all_data_sources.py`
2. Call from `main()` function
3. Add new data source to `DataQualityReport`
4. Update documentation

Example:
```python
def validate_new_data_source(report: DataQualityReport) -> bool:
    """Validate new data source"""
    print("Validating New Data Source...")

    # Your validation logic

    report.total_checks += 1
    report.mark_passed("new_source")
    return True
```

## Best Practices

1. **Always validate before edge detection**
   - Prevents garbage-in-garbage-out scenarios
   - Catches data corruption early
   - Ensures consistent quality

2. **Review warnings**
   - Warnings may indicate stale data
   - Some warnings are expected (e.g., weather >7 days out)
   - Others require action (e.g., odds data 48+ hours old)

3. **Fix errors before proceeding**
   - Never run edge detection with validation errors
   - Rescrape failed sources
   - Verify data integrity

4. **Document new issues**
   - Use `/document-lesson` for new data quality issues
   - Update LESSONS_LEARNED.md
   - Improve validator to catch similar issues

5. **Automate where possible**
   - Use hooks for automatic validation
   - Schedule regular validation checks
   - Alert on quality degradation

## Billy Walters Principle

> "In sports betting, data quality is everything. A 1% edge with perfect data beats a 3% edge with garbage data. Never compromise on validation."

---

**Related Documentation:**
- `.claude/commands/validate-data.md` - Slash command documentation
- `LESSONS_LEARNED.md` - Historical data quality issues
- `.claude/hooks/post_data_collection.py` - Automated validation
