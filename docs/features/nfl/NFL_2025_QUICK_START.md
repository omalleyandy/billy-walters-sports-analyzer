# NFL 2025 Data Collection - Quick Start Guide

**Time to complete**: ~5 minutes (collection) + ~2 minutes (loading) = 7 minutes total

## Prerequisites
- PostgreSQL running (`sports_db` database)
- Python 3.11+ with uv package manager
- Network connection (ESPN API access)

## Quick Start (Copy-Paste Ready)

### Step 1: Apply Database Schema (1 minute)
```bash
# Add NFL-specific tables to PostgreSQL
psql -U postgres -d sports_db -f database/nfl_extensions.sql
```

**Success indicator**: Command completes without error

### Step 2: Collect NFL Data (3 minutes)
```bash
# Collect all 18 weeks of NFL 2025 season
uv run python scripts/database/collect_2025_nfl_season.py
```

**What you'll see**:
```
[INFO] 2025 NFL SEASON DATA COLLECTOR
[INFO] Starting 2025 NFL season collection (weeks 1-18)
[INFO] ================================================================================
[INFO] WEEK 1 OF 18
[INFO] Found 14 games for Week 1
[INFO] [01/14] KC@BUF... [OK]
[INFO] [02/14] ... (continues for all games)
[INFO] Week 1 Complete: 14/14 games, 28 team stats
```

**Success indicator**: All 18 weeks complete with ~272 total games

### Step 3: Load to PostgreSQL (2 minutes)
```bash
# Load collected data into database
uv run python scripts/database/load_2025_nfl_season.py
```

**What you'll see**:
```
[INFO] Connected to PostgreSQL
[INFO] Loading from: data/historical/nfl_2025
[INFO] ================================================================================
[INFO] WEEK 1 OF 18
[INFO] Games: 14/14 loaded
[INFO] Team Stats: 28/28 loaded
[INFO] Week 1 Complete: 14 games, 28 team stats
...
[INFO] 2025 NFL HISTORICAL SEASON LOAD COMPLETE!
[INFO] Games: 272 loaded, 0 errors
```

**Success indicator**: 272 games + ~576 team stats loaded with 0 errors

### Step 4: Verify Data (1 minute)
```bash
# Check games were loaded
psql -U postgres -d sports_db -c "
  SELECT week, COUNT(*) as games FROM games
  WHERE league='NFL' AND season=2025
  GROUP BY week ORDER BY week;
"

# Expected: 18 rows with games per week
```

**Success indicator**: 18 rows, with games distributed across all weeks

## Done! 🎉

Your database now contains:
- ✅ **272 NFL games** (weeks 1-18, 2025 season)
- ✅ **576 team statistics records** (32 teams × 18 weeks)
- ✅ **All required fields** for power rating calculations
- ✅ **Indexed for fast queries** (analytical queries <100ms)

## Next Steps

### Option A: Use in Power Ratings (Recommended)
```bash
# Update edge detector to use team statistics
# See: docs/NFL_2025_DATA_COLLECTION.md § "Power Rating Enhancement"
```

### Option B: Run Weekly Updates
```bash
# Every Tuesday after new games are posted:
uv run python scripts/database/collect_2025_nfl_season.py --week CURRENT_WEEK
uv run python scripts/database/load_2025_nfl_season.py
```

### Option C: Query the Data
```bash
# Sample queries
psql -U postgres -d sports_db << EOF

-- Top offenses (PPG)
SELECT team_abbr, team_name, week, points_per_game
FROM nfl_team_stats
WHERE season_year=2025 AND week=18
ORDER BY points_per_game DESC
LIMIT 10;

-- Best defenses (PAPG)
SELECT team_abbr, team_name, week, points_allowed_per_game
FROM nfl_team_stats
WHERE season_year=2025 AND week=18
ORDER BY points_allowed_per_game ASC
LIMIT 10;

-- Yards differential leaders
SELECT team_abbr, week,
       (total_yards_per_game - total_yards_allowed_per_game) as yards_diff
FROM nfl_team_stats
WHERE season_year=2025 AND week=18
ORDER BY yards_diff DESC
LIMIT 10;

EOF
```

## Troubleshooting

### ❌ "Connection refused" (PostgreSQL)
```bash
# Start PostgreSQL
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql
# Windows: services.msc > PostgreSQL > Start
```

### ❌ "Table does not exist"
```bash
# Reapply schema extensions
psql -U postgres -d sports_db -f database/nfl_extensions.sql
```

### ❌ "No games found"
```bash
# Check current week (can't collect future games)
python -c "from src.walters_analyzer.season_calendar import get_nfl_week; print(f'Current NFL week: {get_nfl_week()}')"

# Retry collection if network issue
uv run python scripts/database/collect_2025_nfl_season.py
```

### ❌ "0 games loaded"
```bash
# Check if collection was successful
ls -lh data/historical/nfl_2025/nfl_games_week_*.json

# Should show 18 files, each 50-200KB
# If missing, re-run collection
uv run python scripts/database/collect_2025_nfl_season.py
```

## File Locations

**Collector Script**: `scripts/database/collect_2025_nfl_season.py`
**Loader Script**: `scripts/database/load_2025_nfl_season.py`
**Schema**: `database/nfl_extensions.sql`
**Collected Data**: `data/historical/nfl_2025/nfl_games_week_*.json`
**Documentation**: `docs/NFL_2025_DATA_COLLECTION.md`

## Data Summary

| Metric | Value |
|--------|-------|
| Total Games | 272 |
| Regular Seasons Weeks | 18 |
| Games per Week | 14-17 |
| Teams Tracked | 32 |
| Total Team-Week Records | 576 |
| Data Points per Game | 20+ |
| Data Points per Team-Week | 17 |
| **Total Data Points** | **~15,000+** |

## Key Statistics Available

**Per Game**:
- Team records (W-L-T)
- Scores and margins
- Venue information (stadium, indoor/outdoor)
- Broadcast network

**Per Team-Week**:
- Offensive stats (PPG, passing/rushing yards)
- Defensive stats (points/yards allowed)
- Advanced metrics (turnover margin, 3rd down %)

## What's Different from NCAAF

| Feature | NFL | NCAAF |
|---------|-----|-------|
| Season Weeks | 18 | 16 |
| Games per Week | 14-17 | 50-60 |
| Teams | 32 | 136 |
| Schedule | Balanced, regional primetime | Varied, conference-dependent |
| Data Source | ESPN public API | ESPN public API |
| Collection Time | ~3 minutes | ~4 minutes |
| Total Records | 272 games + 576 stats | 900+ games + 2,176 stats |

## Support

For detailed information, see: `docs/NFL_2025_DATA_COLLECTION.md`

For issues, check: `LESSONS_LEARNED.md`

For methodology, see: `CLAUDE.md` § "Football Analytics Best Practices"
