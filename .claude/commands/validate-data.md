Validate data quality across all sources.

Usage: /validate-data [source] [week]

Examples:
- /validate-data (all sources, current week)
- /validate-data odds 11
- /validate-data injuries
- /validate-data all --detailed

This command will:
1. Check data completeness for all sources
2. Validate data ranges and formats
3. Cross-check consistency across sources
4. Generate data quality report
5. Alert on missing or invalid data

Data Sources Validated:

1. Power Ratings
   - All teams have ratings (0-100 range)
   - Ratings sum to correct average
   - No outliers beyond +/- 3 std dev
   - Updated within last 7 days

2. Game Schedules
   - All games for week present
   - Valid date/time formats
   - Teams exist in database
   - No duplicate games

3. Team Statistics
   - Stats within realistic ranges
   - All key metrics present
   - Matches ESPN official data
   - Season-to-date calculations correct

4. Injury Reports
   - Position values assigned
   - Status is valid (OUT/DOUBTFUL/QUESTIONABLE)
   - Recovery timelines present
   - Team totals calculated

5. Weather Forecasts
   - Temperature: -20°F to 130°F
   - Wind speed: 0-100 mph
   - Precipitation: 0-100%
   - Forecasts within 7 days of game

6. Odds Data
   - Spread: -50 to +50
   - Total: 20 to 100
   - Moneyline: -10000 to +10000
   - Opening lines present
   - Line movement tracked

Validation Rules (Billy Walters Standards):

Spread Validation:
```python
if abs(spread) > 30:
    alert("Unrealistic spread - check data source")
if spread == 0:
    alert("Pick'em game or missing data")
if spread lands on key number (3, 7):
    note("Extra valuable - track line movement")
```

Total Validation:
```python
if total < 30 or total > 70:
    alert("Unusual total - verify weather/injuries")
if total changed >5 points from open:
    alert("Major line movement - investigate")
```

Injury Validation:
```python
if QB out and line moved <3 points:
    alert("Market underreacting to QB injury")
if 3+ O-line out and total not adjusted:
    alert("O-line crisis not priced in")
```

Quality Scoring:
- 100%: Perfect data, all checks pass
- 90-99%: Excellent, minor issues
- 80-89%: Good, usable with caution
- 70-79%: Fair, some data missing
- <70%: Poor, do not use for analysis

Data Quality Report:
```
================================================================
DATA QUALITY VALIDATION REPORT
Week 11 - 2025 NFL Season
Validated: 2025-11-13 14:30:00
================================================================

POWER RATINGS
Status: EXCELLENT (98%)
- Teams: 32/32 ✓
- Ratings range: 72.3 to 94.8 ✓
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
- Issues: 4 injuries missing exact timeline
- Critical injuries flagged: 8 ✓
- Recommendation: Safe to use

WEATHER FORECASTS
Status: GOOD (85%)
- Games: 14/14 ✓
- Forecasts: 10/14 ✓
- Issues: 4 games >7 days out (no forecast yet)
- Impact: 3 games with weather factors ✓
- Recommendation: Usable, 4 games TBD

ODDS DATA (OVERTIME.AG)
Status: EXCELLENT (97%)
- Games: 14/14 ✓
- Spreads: 14/14 ✓
- Totals: 14/14 ✓
- Moneylines: 14/14 ✓
- Opening lines: 12/14 ⚠
- Issues: 2 games missing opening lines
- Recommendation: Safe to use, track line movement manually for 2 games

================================================================
CROSS-SOURCE VALIDATION
================================================================

Game Schedules vs Odds: 100% match ✓
Game Schedules vs Injuries: 100% match ✓
Power Ratings vs Teams: 100% match ✓
Weather vs Schedules: 71% match (4 games pending)

Inconsistencies Detected:
- None (all critical data consistent)

================================================================
OVERALL ASSESSMENT
================================================================

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

Recommendation: PROCEED with analysis
All critical data present and validated.

================================================================
```

Automated Alerts:
- Email/SMS if quality score <70%
- Slack notification if critical data missing
- Log to validation_logger
- Update dashboard status

Integration:
- Runs automatically after data collection
- Pre-flight check before edge detection
- Scheduled daily at 10 AM (check for updates)
- Validates before betting card generation

Billy Walters Data Standards:
"Garbage in, garbage out. Never bet on bad data.
If you're not 100% confident in your data, don't bet."

Action on Poor Data:
1. Re-scrape failed sources
2. Use fallback data sources
3. Exclude games with poor data quality
4. Alert analyst for manual review
5. Document data issues in log
