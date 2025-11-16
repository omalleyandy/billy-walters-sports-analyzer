# NFL Subagent Quick Checklist (Dynamic Week Detection)

**Quick Reference** for parallel data collection workflow

**Note**: System automatically detects current NFL week. Use `get_nfl_week()` from `src/walters_analyzer/season_calendar.py`.

---

## Pre-Flight

- [ ] Get current NFL week: `from walters_analyzer.season_calendar import get_nfl_week; week = get_nfl_week()`
- [ ] Verify NFL season is active (week is not None)
- [ ] Check week date range: `from walters_analyzer.season_calendar import get_week_date_range, League; start, end = get_week_date_range(week, League.NFL)`
- [ ] Confirm all API keys available: AccuWeather, ESPN, Overtime.ag
- [ ] Check output directories exist: `data/current/`, `output/overtime/nfl/pregame/`
- [ ] Load previous week's power ratings: `data/power_ratings_nfl_2025.json`

---

## Subagent Assignments

### ✅ Subagent 1: Schedule & Game Info
**Output**: `data/current/nfl_week_{week}_schedule.json`

- [ ] Pull official NFL fixtures for current week
- [ ] Confirm no postponements
- [ ] Add stadium info (critical: `is_dome` flag)
- [ ] Calculate travel distances
- [ ] Log previous week opponents/results
- [ ] Flag situational factors (divisional, rivalry, etc.)
- [ ] **Deliver**: JSON with 16 games

### ✅ Subagent 2: Betting Lines
**Output**: `output/overtime/nfl/pregame/api_walters_week_{week}_{timestamp}.csv`

- [ ] Query Overtime.ag API for current NFL week
- [ ] Extract full market: spread, total, ML, 1H lines
- [ ] Record opening lines (if available)
- [ ] Calculate book margin
- [ ] Timestamp all data (UTC)
- [ ] **Deliver**: CSV + JSON backup

### ✅ Subagent 3: Weather Data
**Output**: `data/current/nfl_week_{week}_weather.json`

- [ ] Load schedule to identify games
- [ ] Skip dome stadiums (`weather: null`)
- [ ] Fetch weather for outdoor stadiums (<12hr: hourly, >12hr: current)
- [ ] Calculate Billy Walters adjustments:
  - [ ] Temperature: <20°F=-4pts, 20-25°F=-3pts, 25-32°F=-2pts, 32-40°F=-1pt
  - [ ] Wind: >20mph=-5pts, 15-20mph=-3pts, 10-15mph=-1pt
  - [ ] Precipitation: Snow>60%=-5pts, Rain>60%=-3pts
- [ ] Flag weather-sensitive thresholds (wind≥15mph, precip>60%)
- [ ] **Deliver**: JSON with weather + adjustments

### ✅ Subagent 4: Team Situational Analysis
**Output**: `data/current/nfl_week_{week}_team_situational.json`

- [ ] Update power ratings (Billy Walters 90/10 formula)
- [ ] Collect current season metrics:
  - [ ] EPA/play, success rate, explosive play rate
  - [ ] Pace (plays/game), turnover margin
  - [ ] Penalties, special teams DVOA
- [ ] Calculate S-factors:
  - [ ] Rest advantage (bye=+3pts, 8+ days=+1pt, <6 days=-1pt)
  - [ ] Travel penalty (>1500mi=-1.5pts, 1000-1500mi=-1pt, 500-1000mi=-0.5pts)
  - [ ] Consecutive road games (3+=1pt)
  - [ ] Short week, divisional, rivalry, revenge, lookahead, letdown
- [ ] Apply S-factor caps: ±2.0pts per team, ±3.0pts net per game
- [ ] **Deliver**: JSON with updated ratings + S-factors

### ✅ Subagent 5: Player Situational Analysis
**Output**: `data/current/nfl_week_{week}_player_situational.json`

- [ ] Identify key units per team: QB, OL, CB, RB, WR
- [ ] Collect player efficiency metrics (EPA, PFF grades, snap %)
- [ ] Map to Billy Walters injury values (use `PlayerValuation` class)
- [ ] Track usage changes (snap % vs 3-week average)
- [ ] Calculate cumulative player impact (cap: ≤3.0pts per team)
- [ ] **Deliver**: JSON with player data + point values

### ✅ Subagent 6: Injury Reports
**Output**: `data/current/nfl_week_{week}_injuries.json`

- [ ] Pull official NFL injury reports (Wednesday/Thursday/Friday)
- [ ] Categorize status: Out, Doubtful, Questionable, Probable
- [ ] Map to Billy Walters point values (use `InjuryImpactCalculator`)
- [ ] Apply injury caps: ≤3.0pts per team, ≤5.0pts net per game
- [ ] Cross-reference beat reports for practice updates
- [ ] Calculate cumulative impact with status multipliers:
  - [ ] Out: 100% value
  - [ ] Doubtful: 75% value
  - [ ] Questionable: 0% value (uncertain)
  - [ ] Probable: 0% value
- [ ] **Deliver**: JSON with injuries + point impacts

---

## Post-Collection Validation

### File Verification
```python
from walters_analyzer.season_calendar import get_nfl_week
week = get_nfl_week()

# Check all files exist
- [ ] `data/current/nfl_week_{week}_schedule.json` exists and valid JSON
- [ ] `output/overtime/nfl/pregame/api_walters_week_{week}_{timestamp}.csv` exists and valid CSV
- [ ] `data/current/nfl_week_{week}_weather.json` exists and valid JSON
- [ ] `data/current/nfl_week_{week}_team_situational.json` exists and valid JSON
- [ ] `data/current/nfl_week_{week}_player_situational.json` exists and valid JSON
- [ ] `data/current/nfl_week_{week}_injuries.json` exists and valid JSON
```

### Data Quality Checks
- [ ] All 16 games present in all files (game_id matches)
- [ ] All power ratings updated (check `last_updated` timestamp)
- [ ] All S-factors within caps (±2.0 per team, ±3.0 net)
- [ ] All injury impacts within caps (≤3.0 per team, ≤5.0 net)
- [ ] All weather data for outdoor stadiums (domes have `weather: null`)
- [ ] All betting lines have spread, total, moneyline

---

## Integration & Edge Detection

### Load Data
```bash
# Verify all files present
ls -la data/current/nfl_week_11_*.json
ls -la output/overtime/nfl/pregame/api_walters_week_11_*.csv
```

### Run Edge Detector
```bash
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector
```

### Expected Outputs
```python
week = get_nfl_week()
- [ ] `output/edge_detection/nfl_edges_detected_week_{week}.jsonl` (spread edges)
- [ ] `output/edge_detection/nfl_totals_detected_week_{week}.jsonl` (total edges)
- [ ] `output/edge_detection/edge_report_week_{week}.txt` (formatted report)
```

### Generate Betting Card
- [ ] Review edge report for minimum 3.5-point edges
- [ ] Apply Kelly Criterion (25% fractional, max 3% per bet)
- [ ] Rank by edge strength (7+ pts = MAX BET, 4-7 pts = STRONG, etc.)
- [ ] Track CLV (closing line value) for each bet

---

## Billy Walters Methodologies Applied

### Power Ratings
- ✅ 90/10 update formula: `New = (Old × 0.90) + (Game Result × 0.10)`
- ✅ Home field advantage: +2.0 to +2.5 points (stadium-dependent)

### S-Factor Adjustments
- ✅ Maximum per team: ±2.0 points
- ✅ Maximum net per game: ±3.0 points
- ✅ Common factors: Rest, travel, divisional, rivalry, revenge, lookahead, letdown

### Injury Point Values (from Billy Walters tables)
- ✅ Elite QB: 4.5 points
- ✅ Elite RB: 2.5 points
- ✅ Elite WR1: 1.8 points
- ✅ Elite LT/RT: 1.5 points
- ✅ Elite CB: 1.2 points
- ✅ Maximum per team: 3.0 points total

### Weather Adjustments
- ✅ Temperature: <20°F=-4pts, 20-25°F=-3pts, 25-32°F=-2pts, 32-40°F=-1pt
- ✅ Wind: >20mph=-5pts total, 15-20mph=-3pts, 10-15mph=-1pt
- ✅ Precipitation: Snow>60%=-5pts, Rain>60%=-3pts
- ✅ Wind spread adjustment: >15mph=-0.5pts (favors rushing team)

### Edge Thresholds
- ✅ Minimum edge: 3.5 points
- ✅ Key numbers: 3 (8% value), 7 (6% value)
- ✅ Kelly Criterion: 25% fractional, max 3% per bet

---

## Critical Integration Points

### Game ID Format
**Standard**: `NFL_2025_11_{AWAY}_{HOME}`
- Example: `NFL_2025_11_BUF_KC` (Buffalo @ Kansas City)
- **MUST match across all 6 files** for proper reconciliation

### Team Name Normalization
**Standard**: Use full city name (e.g., "Kansas City", not "KC" or "Chiefs")
- Map from abbreviations using `TEAM_NAME_MAP` in edge detector
- Consistent naming critical for power rating lookups

### Timestamp Format
**Standard**: ISO 8601 UTC (e.g., `2025-11-13T10:00:00Z`)
- All `scraped_at` fields must be timezone-aware UTC
- Game times in local timezone with offset (e.g., `2025-11-17T20:20:00-06:00`)

### Point Value Caps
- **S-Factor**: ±2.0 per team, ±3.0 net per game
- **Injuries**: ≤3.0 per team, ≤5.0 net per game
- **Player Impact**: ≤3.0 per team (separate from injuries)
- **Total Adjustments**: All caps must be enforced before edge calculation

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Missing game in schedule | Check NFL.com directly, verify week number |
| Weather API 12hr limit | Use OpenWeather API for games >12 hours away |
| Power rating errors | Verify previous week's ratings loaded, check game results |
| Injury value discrepancies | Check `src/walters_analyzer/valuation/injury_impacts.py` |
| Integration failures | Verify JSON format, check file paths, ensure game_id matches |

---

**Checklist Version**: 1.0  
**Last Updated**: 2025-11-13  
**Status**: Ready for use
