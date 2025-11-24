# NFL 2025 Historical Data Collection System

## Overview

This document describes the complete NFL 2025 historical data collection system for Billy Walters sports analytics. The system automatically extracts all game data, team statistics, and venue information from ESPN APIs and stores it in PostgreSQL for power rating calculations and edge detection analysis.

## What Gets Collected

### Per Game Data (272 games total - 17 avg per week × 18 weeks)
- **Game Identification**: Game ID, ESPN Event ID, date, week, season
- **Teams**: Home/away team names, abbreviations, IDs
- **Scores**: Final scores (NULL until game is played)
- **Records**: Win/loss/tie records for each team at time of game
- **Venue**: Stadium name, indoor/outdoor flag
- **Metadata**: Game status, broadcast network, attendance

### Team Weekly Statistics (32 teams × 18 weeks = 576 records)
- **Offensive Metrics**: Points per game, total yards, passing/rushing yards
- **Defensive Metrics**: Points allowed per game, yards allowed (total, passing, rushing)
- **Advanced Stats**: Turnover margin, 3rd down percentage, takeaways/giveaways

**Data Format**: Cumulative through the given week (e.g., Week 5 stats = average through 5 games)

## System Architecture

### Three-Component Design

```
┌─────────────────────────────────────────────────────────┐
│ 1. ESPN API DATA COLLECTION                             │
│    (collect_2025_nfl_season.py)                        │
│    - Async HTTP requests to ESPN's public APIs         │
│    - 18 weeks of NFL schedule and statistics           │
│    - ~0.2 second rate limiting per request             │
│    - Output: 18 JSON files (nfl_games_week_*.json)     │
└──────────────┬──────────────────────────────────────────┘
               │
               ├─ /data/historical/nfl_2025/ (collected data)
               │  ├─ nfl_games_week_1_2025_*.json
               │  ├─ nfl_games_week_2_2025_*.json
               │  └─ ... nfl_games_week_18_2025_*.json
               │
┌──────────────▼──────────────────────────────────────────┐
│ 2. DATABASE SCHEMA EXTENSION                            │
│    (database/nfl_extensions.sql)                       │
│    - Creates nfl_team_stats table                      │
│    - Adds analytical views                             │
│    - Creates validation functions                      │
└──────────────┬──────────────────────────────────────────┘
               │
               ├─ PostgreSQL: sports_db
               │  ├─ games (272 NFL games added)
               │  └─ nfl_team_stats (576 team-week records)
               │
┌──────────────▼──────────────────────────────────────────┐
│ 3. DATABASE LOADER & VALIDATION                         │
│    (load_2025_nfl_season.py)                           │
│    - Bulk inserts from JSON → PostgreSQL               │
│    - ON CONFLICT upserts for idempotency               │
│    - Data quality validation                           │
│    - Verification queries                              │
└──────────────┬──────────────────────────────────────────┘
               │
               └─ ✅ Ready for Power Rating & Edge Detection
```

## Step-by-Step Usage

### Step 1: Prepare Database Schema

Before collecting data, add the NFL-specific tables to your database:

```bash
# Connect to PostgreSQL and apply the extensions
psql -U postgres -d sports_db -f database/nfl_extensions.sql

# Verify the table was created
psql -U postgres -d sports_db -c "\dt nfl_team_stats"
```

**What This Does**:
- Creates `nfl_team_stats` table for team statistics storage
- Creates analytical views for power rating enhancement
- Adds validation functions for data quality checking
- Creates optimized indexes for query performance

### Step 2: Collect NFL Data (Weeks 1-18)

#### Option A: Collect Full Season (Recommended)

```bash
# Collect all 18 weeks of NFL 2025 season
uv run python scripts/database/collect_2025_nfl_season.py

# Output: 18 JSON files in data/historical/nfl_2025/
# Time: ~2-3 minutes (rate-limited, includes team stats fetches)
# Status: Logs show progress for each week
```

**What This Does**:
1. Fetches schedule and game results for each week (ESPN API)
2. Extracts game data: teams, scores, records, venue
3. Fetches team statistics for both teams in each game
4. Saves all data to JSON files (one per week)
5. Creates summary file with collection metadata

#### Option B: Collect Specific Week

```bash
# Collect only Week 12
uv run python scripts/database/collect_2025_nfl_season.py --week 12

# Output: Single JSON file nfl_games_week_12_2025_*.json
# Time: ~30 seconds
```

#### Option C: Collect Week Range

```bash
# Collect Weeks 8-14
uv run python scripts/database/collect_2025_nfl_season.py --start-week 8 --end-week 14

# Output: 7 JSON files (weeks 8-14)
# Time: ~1 minute
```

### Step 3: Verify Collected Data

```bash
# Check what was collected
ls -lh data/historical/nfl_2025/

# View sample of Week 1 data
python -c "
import json
with open('data/historical/nfl_2025/nfl_games_week_1_2025_*.json'.glob()[0]) as f:
    data = json.load(f)
    print(f'Games: {len(data[\"games\"])}')
    print(f'Team Stats: {len(data[\"team_stats\"])}')
    print(f'Sample Game: {data[\"games\"][0][\"away_team\"]}@{data[\"games\"][0][\"home_team\"]}')
"
```

### Step 4: Load Data to PostgreSQL

#### Load Full Season (Recommended)

```bash
# Load all collected weeks to PostgreSQL
uv run python scripts/database/load_2025_nfl_season.py

# Expected output:
# [OK] Connected to PostgreSQL
# Loading from: data/historical/nfl_2025
# WEEK 1 OF 18
# [OK] 14 games loaded
# ... (weeks 2-18)
# [OK] Total games loaded: 272
# 2025 NFL HISTORICAL SEASON LOAD COMPLETE!
```

#### Load with Custom Database Parameters

```bash
uv run python scripts/database/load_2025_nfl_season.py \
    --dbname sports_db \
    --user postgres \
    --password your_password \
    --host localhost \
    --port 5432
```

### Step 5: Validate Data Quality

```bash
# Query: Check games loaded
psql -U postgres -d sports_db -c "
    SELECT week, COUNT(*) as games,
           COUNT(DISTINCT home_team) as teams
    FROM games
    WHERE league='NFL' AND season=2025
    GROUP BY week
    ORDER BY week;
"

# Expected: 18 rows, weeks 1-18, varying games per week

# Query: Check team stats coverage
psql -U postgres -d sports_db -c "
    SELECT week, COUNT(DISTINCT team_abbr) as teams
    FROM nfl_team_stats
    WHERE season_year=2025
    GROUP BY week
    ORDER BY week;
"

# Expected: 18 rows, ~32 unique teams per week

# Query: Sample games
psql -U postgres -d sports_db -c "
    SELECT week, home_team, away_team, home_score, away_score, status
    FROM games
    WHERE league='NFL' AND season=2025
    LIMIT 10;
"

# Query: Use validation function
psql -U postgres -d sports_db -c "
    SELECT * FROM validate_nfl_team_stats(2025, 12);
"

# Query: Check coverage statistics
psql -U postgres -d sports_db -c "
    SELECT * FROM check_nfl_coverage(2025, 12);
"
```

## Data Quality Standards

### Games Table
- **Coverage**: 272 games (17-18 games per week average)
- **Required Fields**: game_id, season, week, league, home_team, away_team, game_date, status
- **Game Status States**: SCHEDULED, IN_PROGRESS, FINAL
- **Nullable Fields**: home_score, away_score (NULL until game played)

### Team Statistics Table
- **Coverage**: ~32 teams per week × 18 weeks = 576 records
- **Required Fields**: team_abbr, team_name, week, season_year
- **Data Completeness**: 90%+ (some teams may lack detailed stats)
- **Nullable Fields**: Offensive/defensive metrics (populated from ESPN API)

### Completeness Thresholds
- **Excellent**: 95-100% fields populated
- **Good**: 80-94% fields populated
- **Fair**: 60-79% fields populated
- **Poor**: <60% fields populated

## File Organization

```
data/historical/nfl_2025/
├── nfl_games_week_1_2025_20251124_150456.json
├── nfl_games_week_2_2025_20251124_150512.json
├── ... (weeks 3-18)
└── nfl_2025_season_collection_summary_20251124_150456.json

# Each week file contains:
{
    "season": 2025,
    "week": 1,
    "league": "NFL",
    "timestamp": "2025-11-24T15:04:56",
    "games": [
        {
            "game_id": "KC_BUF_2025_W1",
            "espn_event_id": "...",
            "week": 1,
            "home_team": "Kansas City Chiefs",
            "away_team": "Buffalo Bills",
            "home_score": null,  // Not played yet or final
            "away_score": null,
            "stadium": "GEHA Field at Arrowhead Stadium",
            "is_outdoor": true,
            "status": "SCHEDULED",
            ...
        }
    ],
    "team_stats": [
        {
            "team_abbr": "KC",
            "team_name": "Kansas City Chiefs",
            "week": 1,
            "points_per_game": 28.5,
            "points_allowed_per_game": 18.2,
            "total_yards_per_game": 385.4,
            ...
        }
    ]
}
```

## Power Rating Enhancement

These NFL team statistics enhance Billy Walters power ratings:

### 1. Offensive Efficiency Rating
```python
offensive_adjustment = (team_ppg - league_avg_ppg) * 0.15
# Example: 28.5 PPG vs 24.2 league avg = +0.64 pts adjustment
```

### 2. Defensive Efficiency Rating
```python
defensive_adjustment = (league_avg_papg - team_papg) * 0.15
# Example: League avg 24.2 vs 18.2 PAPG = +0.90 pts adjustment
```

### 3. Yards Differential
```python
yards_adjustment = (team_tyd - team_tyal) / 1000 * 0.05
# Example: 385.4 YD vs 325.6 YA = +3.0 yards diff (+0.15 pts)
```

### 4. Recent Form Adjustment
```python
recent_form = (current_week_ppg - previous_week_ppg) * 0.10
# Example: Week 5 scored 31, Week 4 scored 27 = +0.4 pts
```

### Enhanced Power Rating Formula
```python
enhanced_rating = base_rating +
    offensive_adjustment +
    defensive_adjustment +
    yards_adjustment +
    recent_form_adjustment
```

## Troubleshooting

### Problem: "No games found for Week X"
**Cause**: Week not yet happened or ESPN API temporarily unavailable
**Solution**:
- Check current NFL week: `python -c "from src.walters_analyzer.season_calendar import get_nfl_week; print(get_nfl_week())"`
- Retry collection in 1-2 minutes
- Check ESPN.com directly for schedule

### Problem: "Failed to connect to database"
**Cause**: PostgreSQL not running or credentials incorrect
**Solution**:
- Verify PostgreSQL is running: `psql --version && psql -U postgres -c "SELECT 1"`
- Check database exists: `psql -l | grep sports_db`
- Verify credentials in environment or command args
- Create database if needed: `createdb -U postgres sports_db`

### Problem: "Table 'nfl_team_stats' does not exist"
**Cause**: Database schema extensions not applied
**Solution**:
```bash
# Apply NFL schema extensions
psql -U postgres -d sports_db -f database/nfl_extensions.sql

# Verify table exists
psql -U postgres -d sports_db -c "\dt nfl_team_stats"
```

### Problem: "0 games loaded"
**Cause**: No JSON files found in data directory
**Solution**:
- Verify collection completed: `ls -la data/historical/nfl_2025/nfl_games_week_*.json`
- Check for errors in collection: Review console output for [ERROR] messages
- Re-run collector for missing weeks

### Problem: "JSON parsing error"
**Cause**: Corrupted or incomplete JSON file
**Solution**:
- Check file is valid JSON: `python -m json.tool data/historical/nfl_2025/nfl_games_week_1_2025_*.json > /dev/null`
- Delete corrupted file and re-collect: `rm data/historical/nfl_2025/nfl_games_week_1_2025_*.json`
- Re-run collector for that week

## Performance Characteristics

### Collection Performance
- **Total Time**: ~3 minutes for all 18 weeks
- **Per Week**: ~10 seconds (14-16 games + 32 team stats fetches)
- **API Calls**: ~560 HTTP requests (games + team stats)
- **Rate Limiting**: 0.2 seconds between requests (140 req/min sustainable)

### Database Load Performance
- **Total Time**: ~2 minutes for all 18 weeks
- **Games Insertion**: 272 games in ~30 seconds
- **Team Stats Insertion**: 576 records in ~90 seconds
- **Verification**: ~10 seconds

### Query Performance
```sql
-- Index lookup (should be <1ms)
SELECT * FROM games
WHERE league='NFL' AND season=2025 AND week=12;

-- Team stats by week (should be <10ms)
SELECT * FROM nfl_team_stats
WHERE season_year=2025 AND week=12;

-- Analytical views (should be <100ms)
SELECT * FROM nfl_weekly_averages
WHERE season_year=2025;
```

## Integration with Billy Walters Workflow

### Weekly Update Process
```bash
# Tuesday: Collect latest NFL data
uv run python scripts/database/collect_2025_nfl_season.py --week CURRENT_WEEK

# Load to database
uv run python scripts/database/load_2025_nfl_season.py

# Update power ratings
/power-ratings

# Detect edges
/edge-detector

# Generate betting card
/betting-card
```

### Historical Analysis
```bash
# Collect all 18 weeks
uv run python scripts/database/collect_2025_nfl_season.py

# Load to database
uv run python scripts/database/load_2025_nfl_season.py

# Backtest entire season
uv run python scripts/backtest/backtest_season.py --league nfl --season 2025

# Analyze CLV performance
/clv-tracker
```

## Database Schema Details

### Games Table (NFL-specific fields)
```sql
CREATE TABLE games (
    game_id VARCHAR(50) PRIMARY KEY,
    season INT,
    week INT,
    league VARCHAR(10) CHECK (league IN ('NFL', 'NCAAF')),
    game_date TIMESTAMP,
    home_team VARCHAR(100),
    away_team VARCHAR(100),
    home_score INT,
    away_score INT,
    final_margin INT,
    total_points INT,
    status VARCHAR(20),
    stadium VARCHAR(100),
    is_outdoor BOOLEAN,
    is_neutral_site BOOLEAN
);

-- NFL typically has:
-- - No neutral site games (except occasional international games)
-- - 14-17 games per week (scheduling variations)
-- - 1 Thursday Night Football, 1 Monday Night Football per week
```

### NFL Team Stats Table (New)
```sql
CREATE TABLE nfl_team_stats (
    id SERIAL PRIMARY KEY,
    team_abbr VARCHAR(10),
    team_name VARCHAR(100),
    week INT CHECK (week BETWEEN 1 AND 18),
    season_year INT,

    -- Offensive stats (per game averages)
    points_per_game DECIMAL(5,2),
    total_points INT,
    passing_yards_per_game DECIMAL(7,2),
    rushing_yards_per_game DECIMAL(7,2),
    total_yards_per_game DECIMAL(7,2),

    -- Defensive stats (per game averages)
    points_allowed_per_game DECIMAL(5,2),
    passing_yards_allowed_per_game DECIMAL(7,2),
    rushing_yards_allowed_per_game DECIMAL(7,2),
    total_yards_allowed_per_game DECIMAL(7,2),

    -- Advanced stats
    turnover_margin INT,
    third_down_pct DECIMAL(5,2),
    takeaways INT,
    giveaways INT,

    CONSTRAINT unique_nfl_team_week UNIQUE (team_abbr, week, season_year)
);
```

## API Endpoints Used

### ESPN APIs (All Public, No Authentication Required)

**Games & Schedule**:
```
GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
    ?week={week}
    &seasontype=2
    &season=2025
```

**Team Statistics**:
```
GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_abbr}/statistics
```

**Advantages**:
- ✅ No authentication required
- ✅ Reliable and stable
- ✅ Well-documented structure
- ✅ Fast responses (<1 second)
- ✅ No rate limits for reasonable usage

## Command Reference

```bash
# Collect data
uv run python scripts/database/collect_2025_nfl_season.py              # Full season
uv run python scripts/database/collect_2025_nfl_season.py --week 12    # Single week
uv run python scripts/database/collect_2025_nfl_season.py --start-week 8 --end-week 14  # Range

# Load to database
uv run python scripts/database/load_2025_nfl_season.py                 # Full load
uv run python scripts/database/load_2025_nfl_season.py --data-dir data/historical/nfl_2025

# Database schema
psql -U postgres -d sports_db -f database/nfl_extensions.sql          # Add NFL tables
psql -U postgres -d sports_db -c "SELECT * FROM games WHERE league='NFL';"  # Query games
psql -U postgres -d sports_db -c "SELECT * FROM nfl_team_stats WHERE season_year=2025 AND week=12;"  # Query stats

# Validation
psql -U postgres -d sports_db -c "SELECT * FROM validate_nfl_team_stats(2025, 12);"
psql -U postgres -d sports_db -c "SELECT * FROM check_nfl_coverage(2025, 12);"
```

## What's Next

### Recommended Next Steps

1. **Collect All 18 Weeks** (Week 1 through current week)
   ```bash
   uv run python scripts/database/collect_2025_nfl_season.py
   ```

2. **Load to PostgreSQL**
   ```bash
   uv run python scripts/database/load_2025_nfl_season.py
   ```

3. **Enhance Power Ratings** with collected team statistics
   - Update edge detector to use nfl_team_stats
   - Implement offensive/defensive efficiency adjustments
   - Add recent form adjustments

4. **Run Weekly Updates** to keep data current
   - Tuesday: Collect current week
   - Load to database
   - Run edge detection

### Future Enhancements
- [ ] Automatic weekly data collection via cron
- [ ] Injury data integration
- [ ] Weather data integration
- [ ] Line movement tracking from collected odds
- [ ] Parquet export for analytics
- [ ] Jupyter notebook templates for analysis

## Support & Troubleshooting

For issues or questions:
1. Check this document (FAQ section above)
2. Review console output for specific error messages
3. Check LESSONS_LEARNED.md for similar issues
4. Examine database validation functions output

## References

- [NFL Schedule & Scores](https://www.espn.com/nfl/schedule)
- [ESPN API Documentation](https://www.espn.com/apis)
- [Billy Walters Methodology](docs/CLAUDE.md § "Football Analytics Best Practices")
- [Power Rating Calculation](src/walters_analyzer/valuation/billy_walters_edge_detector.py)
