# Post-Flight Validation - Verify Data Quality After Collection

Comprehensive post-flight validation to ensure data collection completed successfully and data quality is acceptable for analysis.

## Usage

```bash
/post-validate [league] [week] [options]
```

## Parameters

- **league** (optional): `nfl`, `ncaaf`, or `all` (default: auto-detect)
- **week** (optional): Week number (default: current week)
- **--detailed** (optional): Show detailed quality report

## Examples

```bash
# Validate current week for auto-detected league
/post-validate

# Validate NFL data for current week
/post-validate nfl

# Validate NCAAF week 13
/post-validate ncaaf 13

# Detailed quality report for NFL
/post-validate nfl --detailed
```

## What This Command Does

Runs comprehensive post-flight validation that checks:

1. **Data Completeness**
   - All required files collected (schedules, odds, weather, injuries, team stats)
   - Correct number of games for week
   - All teams represented in data

2. **Data Quality Scoring**
   - Each data source scored 0-100%
   - EXCELLENT (90-100%): Safe to use
   - GOOD (80-89%): Usable with caution
   - FAIR (70-79%): Some data missing
   - POOR (<70%): Do not use for analysis

3. **Data Ranges & Formats**
   - Spreads: -50 to +50 (realistic range)
   - Totals: 20 to 100 (realistic range)
   - Temperatures: -20°F to 130°F
   - Wind speeds: 0-100 mph
   - Dates/times properly formatted
   - Team abbreviations valid

4. **Cross-Source Validation**
   - Game schedules match odds data
   - Schedule matches injury reports
   - All teams in schedule have ratings
   - Weather matches game locations

5. **League Separation**
   - NFL and NCAAF data strictly separated
   - No mixing of leagues
   - Output directories have correct league prefixes

## Exit Codes

- **0** = Data validated, ready for analysis ✅
  - Quality score 80%+
  - All critical data present
  - No blocking issues
  - Ready for edge detection

- **1** = Data quality issues found ⚠️
  - Quality score <80%
  - Some data missing or invalid
  - Manual review recommended
  - See detailed report for issues

## Quality Scoring Examples

### EXCELLENT Quality (95%)
```
[OK] All required files present (6/6)
[OK] Game schedules match odds (14/14)
[OK] All teams have power ratings (32/32)
[OK] Weather data available (12/14 - indoor stadiums OK)
[OK] Injury reports complete (128/128 players)
[OK] Data ranges valid (all checks passed)

Quality: EXCELLENT (95%)
Recommendation: READY FOR ANALYSIS
```

### GOOD Quality (87%)
```
[OK] Game schedules match odds (14/14)
[OK] Power ratings available (32/32)
[WARN] Weather incomplete (10/14 forecasts)
  → 4 games >7 days out (forecasts not available yet)
  → This is normal, not a data issue
[OK] Injury reports (124/128 complete)
[OK] Data ranges valid

Quality: GOOD (87%)
Recommendation: READY FOR ANALYSIS
Note: Weather for 4 future games will update automatically
```

### FAIR Quality (76%)
```
[WARN] Missing schedule data (12/14 games)
[WARN] Incomplete odds (11/14 games have spreads)
[OK] Power ratings available (32/32)
[ERROR] Injury reports very sparse (20/128)

Quality: FAIR (76%)
Recommendation: INVESTIGATE BEFORE ANALYSIS
Action:
- Re-run data collection (sometimes scrapers timeout)
- Check data source credentials
- Verify internet connectivity
```

## Output Example

```
============================================================
POST-FLIGHT VALIDATION - Week 12 NFL
============================================================

POWER RATINGS
Status: EXCELLENT (98%)
- Teams: 32/32 ✓
- Ratings range: 72.3 to 94.8 (valid)
- Last updated: 2 hours ago ✓
- Issues: None
- Recommendation: Safe to use

GAME SCHEDULES
Status: PERFECT (100%)
- Games: 14/14 ✓
- Dates valid: 14/14 ✓
- Teams valid: 28/28 ✓
- Issues: None
- Recommendation: Safe to use

TEAM STATISTICS
Status: GOOD (88%)
- Teams: 32/32 ✓
- Stats completeness: 28/32 ✓
- Issues: 4 teams missing red zone data
- Recommendation: Usable, note missing data

INJURY REPORTS
Status: EXCELLENT (96%)
- Teams: 32/32 ✓
- Position values: 124/128 ✓
- Recovery timelines: 120/128 ✓
- Critical injuries: 8 flagged ✓
- Issues: 4 injuries missing exact timeline
- Recommendation: Safe to use

WEATHER FORECASTS
Status: GOOD (85%)
- Games: 14/14 ✓
- Forecasts: 10/14 ✓
- Issues: 4 games >7 days out (no forecast yet)
- Weather factors: 3 games affected
- Recommendation: Usable, 4 games TBD

ODDS DATA
Status: EXCELLENT (97%)
- Games: 14/14 ✓
- Spreads: 14/14 ✓
- Totals: 14/14 ✓
- Moneylines: 14/14 ✓
- Opening lines: 12/14 ⚠️
- Issues: 2 games missing opening lines
- Recommendation: Safe to use, track line movement manually

============================================================
CROSS-SOURCE VALIDATION
============================================================

Game Schedules vs Odds: 100% match ✓
Game Schedules vs Injuries: 100% match ✓
Power Ratings vs Teams: 100% match ✓
Weather vs Schedules: 71% match (4 games pending)

Inconsistencies Detected: None (all critical data consistent)

============================================================
OVERALL ASSESSMENT
============================================================

Data Quality Score: 93% (EXCELLENT)

Readiness for Analysis:
- Edge Detection: READY ✓
- Betting Card Generation: READY ✓
- Billy Walters Analysis: READY ✓

Warnings:
- 4 weather forecasts pending (games >7 days out)
- 2 opening lines missing (use current as proxy)

Blockers:
- None

Recommendation: PROCEED WITH ANALYSIS
All critical data present and validated.

Next Steps:
1. Run: /edge-detector
2. Run: /betting-card
3. Review and place bets
```

## Common Issues & Resolutions

### Low Quality Score (<70%)
```
Action:
1. Identify which data source has low quality
2. Check if APIs were down or rate-limited
3. Manually update failed source:
   uv run python scripts/scrapers/scrape_overtime_api.py --nfl
4. Re-run: /post-validate
```

### Missing Weather Data
```
Status: Normal (especially for games >7 days out)
Action: None required - forecasts will update automatically
Note: Indoor stadiums don't need weather data (None is correct)
```

### Incomplete Injury Reports
```
Action:
1. Verify ESPN injury page is accessible
2. Check if team has multiple injuries
3. Re-scrape: uv run python scripts/scrapers/scrape_espn_injuries.py --nfl
4. Re-validate: /post-validate nfl
```

### Schedule/Odds Mismatch
```
Action:
1. Check if current week detected correctly: /current-week
2. Verify both files are for same week
3. Re-collect odds: /scrape-overtime --nfl
4. Re-validate: /post-validate nfl
```

## Quality Standards (Billy Walters)

**"Never bet on bad data"** - Billy Walters

Minimum acceptable quality per source:
- Power Ratings: 95% (essential foundation)
- Game Schedules: 100% (critical - no games missing)
- Odds Data: 95% (spreads/totals must be complete)
- Injury Reports: 80% (position values most important)
- Weather: 70% (pending forecasts are OK)

## Related Commands

- `/collect-all-data` - Run before this to collect data
- `/pre-validate` - Pre-flight check before data collection
- `/edge-detector` - Run after this passes for edge detection
- `/validate-data` - Alternative comprehensive validation
- `/current-week` - Verify current week number

## Manual Alternative

If you prefer to run post-flight validation manually:

```bash
python .claude/hooks/post_data_collection_validator.py --league nfl
```

This runs the same checks and is useful for detailed diagnostics.

---

**When to Run:** After data collection completes (`/collect-all-data`)
**Time Required:** 30-60 seconds
**Frequency:** Always after collection (automatic in workflow)
