# PostgreSQL Data Loading Workflow

**Date Created**: 2025-11-24
**Status**: ✅ Production Ready
**Last Update**: 2025-11-24 - Completed GameIDMapper integration and full odds loading

---

## Overview

This document describes the complete PostgreSQL data loading workflow, from data collection to database insertion. The system automatically:

1. **Collects data** from ESPN, Overtime.ag, AccuWeather, and other sources
2. **Maps game IDs** between different data systems (Overtime.ag ↔ ESPN)
3. **Populates database tables** with normalized, deduplicated data
4. **Validates referential integrity** with foreign key constraints

---

## Architecture

### Data Flow

```
ESPN Schedules (Collected)
    ↓
espn_schedules table
    ↓
GameIDMapper.populate_games_table()
    ↓
games table (with league column)
    ↓
Odds/Weather inserts (with valid FK references)
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **GameIDMapper** | Maps Overtime.ag IDs to ESPN IDs | `scripts/database/game_id_mapper.py` |
| **DataLoader** | Loads JSON files into PostgreSQL | `scripts/database/load_collected_data_to_db.py` |
| **Database Connection** | Connection pooling and context management | `src/db/connection.py` |

---

## Game ID Mapping System

### The Problem

Different data sources use different game ID systems:

- **ESPN**: `401772891` (used in ESPN API, schedules, ESPN scoreboard)
- **Overtime.ag**: `114570440` (used in their API)
- **Games Table**: Expects ESPN-style IDs with foreign key constraints

### The Solution: GameIDMapper

The `GameIDMapper` class provides intelligent fuzzy matching:

**Primary Strategy**: Exact match by team names + date
```python
home_team = "Detroit Lions"
away_team = "Green Bay Packers"
game_date = 2025-11-27
→ ESPN ID: 401772891 (from cache)
```

**Fallback Strategy**: Fuzzy match with date tolerance (2 days)
```python
# Handles timezone differences:
# Overtime.ag: 11/27/2025 20:20 (local time)
# ESPN: 11/28/2025 01:20 (ET)
→ Still matches because of 2-day tolerance
```

### Key Features

✅ **Fast lookup**: ~100K games cached in memory
✅ **Timezone-aware**: 2-day tolerance handles date offsets
✅ **Fallback matching**: Tries 3 strategies before giving up
✅ **Error reporting**: Clear warnings for unmapped games
✅ **Theater-specific**: Handles Thu/Sun/Mon night games correctly

### Success Rate

- **NFL Week 13**: 15/15 games (100%)
- **NCAAF**: Results pending first full week

---

## Database Tables & Loading

### ESPN_SCHEDULES Table

**Source**: ESPN API (via `/collect-all-data`)
**Purpose**: Master schedule reference for all weeks
**Columns**: game_id, season, week, league, home_team, away_team, game_date, stadium, city, state, etc.

**Load Process**:
```bash
DataLoader.load_schedules()
  ↓
Reads: data/current/nfl_week_13_games.json
  ↓
Inserts to: espn_schedules table
  ↓
ON CONFLICT DO NOTHING (skip duplicates)
  ↓
Result: 16 NFL games loaded per week
```

### GAMES Table

**Source**: Copied from espn_schedules
**Purpose**: Games with league column for foreign key references
**Columns**: game_id, season, week, league, home_team, away_team, game_date

**Load Process**:
```bash
GameIDMapper.populate_games_table(season=2025, week=13, league='NFL')
  ↓
SELECT * FROM espn_schedules WHERE season=2025 AND week=13 AND league='NFL'
  ↓
INSERT INTO games (game_id, season, week, league, home_team, away_team, game_date)
  ↓
ON CONFLICT DO NOTHING
  ↓
Result: 16 NFL games in games table
```

**Why Separate Tables?**
- `espn_schedules`: All historical data, used for validation
- `games`: Current week data with league column for FK constraints
- Prevents foreign key violations from incomplete data

### ODDS Table

**Source**: Overtime.ag API (via `/collect-all-data`)
**Purpose**: Betting odds with game references
**Columns**: game_id (FK), sportsbook, odds_type, home_spread, away_spread, home_moneyline, away_moneyline, total, timestamp

**Load Process**:
```bash
DataLoader.load_odds()
  ↓
Reads: output/overtime/nfl/pregame/api_walters_*.json
  ↓
Extracts game data:
  - Overtime.ag ID: 114570440
  - Teams: Baltimore Ravens (home) vs Cincinnati Bengals (away)
  - Date/time: 11/27/2025 20:20
  ↓
Maps Overtime ID → ESPN ID:
  - GameIDMapper.map_overtime_to_espn(...)
  - Result: 401772930
  ↓
Extracts odds from nested dict format:
  - Spread: {home: -3.5, away: 3.5}
  - Moneyline: {home: -145, away: 125}
  - Total: {points: 26.0}
  ↓
Inserts to: odds table
  - game_id: 401772930 (ESPN ID)
  - home_spread: -3.5
  - away_spread: 3.5
  - home_moneyline: -145
  - away_moneyline: 125
  - total: 26.0
  ↓
ON CONFLICT DO NOTHING
  ↓
Result: 15 NFL games with odds loaded per week
```

**Data Structure Handling**:

Overtime.ag API returns nested dictionaries:
```json
{
  "spread": {"home": -2.5, "away": 2.5},
  "moneyline": {"home": -145, "away": 125},
  "total": {"points": 49.0}
}
```

Loader extracts:
```python
home_spread = spread_data.get("home")      # -2.5
away_spread = spread_data.get("away")      # 2.5
moneyline_home = ml_data.get("home")       # -145
moneyline_away = ml_data.get("away")       # 125
total = total_data.get("points")           # 49.0
```

### ESPN_TEAM_STATS Table

**Source**: ESPN API (via `/collect-all-data`)
**Purpose**: Weekly team statistics
**Columns**: season, week, league, team, points_per_game, points_allowed_per_game, turnover_margin, data_source, created_at, updated_at

**Load Process**:
```bash
DataLoader.load_team_stats()
  ↓
Reads: data/current/nfl_team_stats_week_13.json
  ↓
Extracts: team_name, PPG, PA/G, turnover margin
  ↓
Inserts to: espn_team_stats
  ↓
ON CONFLICT DO NOTHING
  ↓
Result: 32 NFL teams loaded per week
```

### WEATHER Table (Planned)

**Source**: AccuWeather (via `/collect-all-data`)
**Purpose**: Game-day weather forecasts
**Columns**: game_id (FK), temperature, feels_like, wind_speed, humidity, precipitation_chance, weather_category, source, timestamp

**Current Status**: ⚠️ Data collected but not loaded to database
- Data is available in JSON: `data/current/weather_forecasts_*.json`
- Issue: Each city can have multiple games in different weeks
- Solution needed: Game-specific weather mapping

---

## Complete Data Loading Workflow

### Step-by-Step Process

#### 1. Data Collection (5-7 minutes)

Run `/collect-all-data` which executes:

```bash
# Step 1: ESPN schedules
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl
→ Saves: data/current/nfl_week_13_games.json
→ Contains: 16 NFL Week 13 games

# Step 2: Team statistics
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl
→ Saves: data/current/nfl_team_stats_week_13.json
→ Contains: 32 NFL team stats

# Step 3: Overtime odds
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
→ Saves: output/overtime/nfl/pregame/api_walters_TIMESTAMP.json
→ Contains: 15 NFL games with full odds

# Step 4: Weather
python src/data/weather_client.py --league nfl
→ Saves: data/current/weather_forecasts_TIMESTAMP.json
→ Contains: 6+ NFL stadium weather forecasts

# Step 5: Power ratings
uv run python scripts/scrapers/scrape_massey_games.py
→ Saves: data/current/massey_ratings_TIMESTAMP.json
→ Contains: Team power ratings
```

#### 2. Database Loading (< 1 minute)

Run data loader:

```bash
uv run python scripts/database/load_collected_data_to_db.py --week 13 --league nfl
```

**Internal process**:

```
[0/4] Load schedules
  ↓ Reads espn_schedules JSON
  ↓ Inserts 16 games into espn_schedules table
  ↓ Result: 16 records

[0/4] Populate games table
  ↓ Copies espn_schedules → games (filters by week/league)
  ↓ Inserts 16 games into games table
  ↓ Result: 16 records with league column

[2/4] Load team stats
  ↓ Reads team_stats JSON
  ↓ Inserts 32 team records into espn_team_stats
  ↓ Result: 32 records

[3/4] Load weather
  ↓ Reads weather JSON
  ↓ Processes 6 cities
  ↓ Skips database insertion (ambiguity: city → game mapping)
  ↓ Result: 0 records (data available in JSON)

[4/4] Load odds
  ↓ Reads Overtime.ag odds JSON
  ↓ For each game:
    - Extract Overtime.ag ID and teams
    - Parse game date (handles MM/DD/YYYY HH:MM format)
    - Map to ESPN ID using GameIDMapper
    - Extract spread/moneyline/total from nested dicts
    - Insert to odds table with ESPN game_id
  ↓ Result: 15 records (all games mapped successfully)

SUMMARY:
  Schedules: 16 records
  Games: 16 records
  Team Stats: 32 records
  Odds: 15 records
  Errors: 0
  Status: [OK] All data loaded successfully!
```

---

## Weekly Execution

### Tuesday: Data Collection

```bash
# 1. Run data collection
/collect-all-data

# 2. Load to database
uv run python scripts/database/load_collected_data_to_db.py --week 13 --league nfl

# 3. Verify (optional)
SELECT COUNT(*) FROM odds WHERE game_id IN (
  SELECT game_id FROM games WHERE week=13 AND league='NFL'
);
→ Should return: 15 (all games)
```

### Wednesday: Edge Detection

```bash
# Edge detection automatically uses current week's odds
/edge-detector

# Uses data from:
# - games table (Schedule)
# - odds table (Betting lines)
# - power_ratings table (Ratings)
# - espn_team_stats table (Statistics)
```

---

## Verification & Validation

### Quick Verification Queries

**Check games loaded**:
```sql
SELECT COUNT(*) FROM games
WHERE season=2025 AND week=13 AND league='NFL';
→ Expected: 16
```

**Check odds loaded**:
```sql
SELECT COUNT(*) FROM odds o
JOIN games g ON o.game_id = g.game_id
WHERE g.season=2025 AND g.week=13 AND g.league='NFL';
→ Expected: 15 (each game gets 1 odds record)
```

**Check team stats loaded**:
```sql
SELECT COUNT(*) FROM espn_team_stats
WHERE season=2025 AND week=13 AND league='NFL';
→ Expected: 32
```

**Check specific game example**:
```sql
SELECT g.home_team, g.away_team, o.home_spread, o.away_spread, o.total
FROM games g
LEFT JOIN odds o ON g.game_id = o.game_id
WHERE g.season=2025 AND g.week=13 AND g.league='NFL'
AND g.home_team LIKE '%Baltimore%';
→ Expected:
  Baltimore Ravens | Cincinnati Bengals | -3.5 | 3.5 | 26.0
```

**Check game ID mapping**:
```sql
SELECT game_id, home_team, away_team, game_date
FROM games
WHERE season=2025 AND week=13 AND league='NFL'
AND home_team LIKE '%Detroit%';
→ Expected:
  401772891 | Detroit Lions | Green Bay Packers | 2025-11-27 18:00:00
```

---

## Error Handling

### Common Issues & Solutions

#### Issue: "Game ID not found" warnings

**Cause**: Overtime.ag game doesn't match ESPN schedule (different teams/dates)
**Solution**: Check that teams match exactly and dates are within 2 days
**Result**: Game skipped (error count incremented, continues processing)

#### Issue: "No odds files found"

**Cause**: `/collect-all-data` didn't run or odds scraper failed
**Solution**: Check `output/overtime/nfl/pregame/` directory for api_walters_*.json files
**Result**: Odds loading returns False, no odds inserted

#### Issue: Foreign key constraint violations

**Cause**: Trying to insert odds with game_id that doesn't exist in games table
**Solution**: Always run `populate_games_table()` BEFORE loading odds
**Result**: ON CONFLICT DO NOTHING prevents errors

#### Issue: Duplicate key violations

**Cause**: Running loader twice on same week
**Solution**: ON CONFLICT DO NOTHING clause prevents errors
**Result**: Second run inserts 0 records (all duplicates), no errors

---

## Performance

### Benchmarks (Week 13 NFL)

| Operation | Duration | Notes |
|-----------|----------|-------|
| Load schedules (16 games) | <1 sec | CSV insert |
| Populate games table | <1 sec | SELECT + INSERT from espn_schedules |
| Load team stats (32 teams) | <1 sec | CSV insert |
| Map odds (15 games) | 2-5 sec | Includes fuzzy matching |
| Total load time | **< 10 seconds** | All 4 steps combined |

### Database Stats

- **Tables**: 6 main tables (games, odds, weather, espn_team_stats, espn_schedules, power_ratings)
- **Current data**: Week 13 NFL complete
- **Game ID cache**: ~100K games loaded into memory
- **Average query**: <100ms (with indexes)

---

## File Structure

```
scripts/database/
├── game_id_mapper.py              (265 lines)
│   ├── _load_espn_schedules()     - Cache all ESPN games
│   ├── map_overtime_to_espn()     - Map Overtime IDs to ESPN IDs
│   ├── get_stadium_from_city()    - Map cities to stadiums
│   ├── find_game_by_teams_and_date() - Fuzzy matching with tolerance
│   └── populate_games_table()     - Copy schedules to games table
│
└── load_collected_data_to_db.py   (540+ lines)
    ├── load_schedules()           - ESPN schedules
    ├── load_team_stats()          - Team statistics
    ├── load_weather()             - Weather data (skipped)
    ├── load_odds()                - Overtime.ag odds with ID mapping
    └── populate_games_table()     - Populate games table

src/db/
└── connection.py
    └── get_db_connection()        - PostgreSQL connection pool
```

---

## Next Steps

### Short Term (This Week)
- ✅ Complete GameIDMapper integration
- ✅ Enable full odds loading
- ✅ Populate games table
- [ ] Test with Week 14 data
- [ ] Monitor for edge cases

### Medium Term (Next 2 Weeks)
- [ ] Implement weather table loading (resolve city→game ambiguity)
- [ ] Add database validation hooks
- [ ] Create weekly data quality reports
- [ ] Add retry logic for failed mappings

### Long Term (Next Month)
- [ ] Standardize on ESPN game IDs across all sources
- [ ] Create game_id lookup table for archival
- [ ] Implement automated weekly sync
- [ ] Build data warehouse for historical analysis

---

## References

- [GameIDMapper](../../../scripts/database/game_id_mapper.py) - Implementation
- [DataLoader](../../../scripts/database/load_collected_data_to_db.py) - Implementation
- [Database Setup Guide](DATABASE_SETUP_GUIDE.md) - PostgreSQL setup
- [CLAUDE.md](../../../CLAUDE.md) - Development guidelines
- [Data Collection Guide](../guides/DATA_COLLECTION_GUIDE.md) - Data sources

---

**Last Updated**: 2025-11-24
**Status**: Production Ready
**Maintained By**: Claude + Andy (Dynamite Duo)
