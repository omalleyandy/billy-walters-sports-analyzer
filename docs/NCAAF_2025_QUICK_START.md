# 2025 NCAAF Historical Data - Quick Start Guide

**Estimated Total Time:** 20-30 minutes (15-20 min collection + 5-10 min loading)

---

## One-Command Quick Start

```bash
# Step 1: Collect data (15-20 minutes)
uv run python scripts/database/collect_2025_ncaaf_season.py

# Step 2: Load into database (5-10 minutes)
uv run python scripts/database/load_2025_historical_stats.py

# Step 3: Verify results
psql -U postgres -d sports_db -c \
  "SELECT week, COUNT(*) FROM ncaaf_team_stats \
   WHERE season_year = 2025 GROUP BY week ORDER BY week;"
```

---

## What Gets Created

### Data Files (17 total)
```
data/historical/ncaaf_2025/
├── ncaaf_team_stats_week_1_2025_TIMESTAMP.json     (136 teams)
├── ncaaf_team_stats_week_2_2025_TIMESTAMP.json     (136 teams)
├── ...
├── ncaaf_team_stats_week_16_2025_TIMESTAMP.json    (136 teams)
└── ncaaf_2025_season_collection_summary_TIMESTAMP.json
```

### Database Records (2,176 total)
```
ncaaf_team_stats table:
- 136 teams × 16 weeks = 2,176 records
- Includes Boston College (Team ID 103)
- Each record has 14 statistical fields
```

---

## Detailed Steps

### Prerequisites

1. **PostgreSQL Database Ready**
   ```bash
   # Create database
   createdb sports_db -U postgres

   # Create schema
   psql -U postgres -d sports_db -f scripts/database/create_ncaaf_schema.sql

   # Load 136 FBS teams
   uv run python scripts/database/load_teams.py
   ```

2. **Team Reference File**
   ```bash
   # Verify teams file exists
   ls data/current/espn_teams.json
   ```

### Step 1: Collect Season Data

**Command:**
```bash
uv run python scripts/database/collect_2025_ncaaf_season.py
```

**What Happens:**
- Loads 136 FBS team references
- Fetches statistics from ESPN API for each team
- Processes weeks 1-16 sequentially
- Saves JSON file for each week
- Creates season summary

**Expected Output:**
```
[INFO] Loaded 136 team references
[INFO] Starting 2025 NCAAF season collection (weeks 1-16)
[INFO] Teams: 136 FBS teams
[INFO] Output: data/historical/ncaaf_2025
================================================================================
WEEK 1 OF 16
================================================================================
[INFO] Collecting Week 1 data for 136 teams...
[  1/136] Boston College Eagles... [OK]
[  2/136] Ohio State Buckeyes... [OK]
...
[136/136] Colgate Raiders... [OK]
[OK] Saved: data/historical/ncaaf_2025/ncaaf_team_stats_week_1_2025_...
Week 1 Complete: 136/136 teams
...
[INFO] 2025 NCAAF season collection complete!
```

**Duration:** 15-20 minutes

### Step 2: Load into PostgreSQL

**Command:**
```bash
uv run python scripts/database/load_2025_historical_stats.py
```

**What Happens:**
- Connects to PostgreSQL database
- Reads week JSON files from disk
- Inserts records into ncaaf_team_stats table
- Handles duplicates with INSERT ON CONFLICT
- Verifies Boston College data

**Expected Output:**
```
[OK] Connected to PostgreSQL
Loading from: data/historical/ncaaf_2025/
================================================================================
WEEK 1 OF 16
================================================================================
[INFO] Loading Week 1 data...
[INFO] Loading from: data/historical/ncaaf_2025/ncaaf_team_stats_week_1_...
[  1/136] Boston College Eagles
[  2/136] Ohio State Buckeyes
...
[136/136] Colgate Raiders
Week 1 Complete: 136/136 teams loaded
...
[OK] Total records loaded: 2176
Records by week:
  Week 1: 136 teams
  Week 2: 136 teams
  ...
  Week 16: 136 teams
[OK] Boston College (ID 103) verified: 16 weeks loaded
[INFO] 2025 NCAAF historical season load complete!
```

**Duration:** 5-10 minutes

### Step 3: Verify Results

**Check Total Records:**
```bash
psql -U postgres -d sports_db -c \
  "SELECT COUNT(*) FROM ncaaf_team_stats WHERE season_year = 2025;"
```

**Expected:** `2176`

**Check By Week:**
```bash
psql -U postgres -d sports_db << EOF
SELECT week, COUNT(*) as teams
FROM ncaaf_team_stats
WHERE season_year = 2025
GROUP BY week
ORDER BY week;
EOF
```

**Expected Output:**
```
 week | teams
------+-------
    1 |   136
    2 |   136
    3 |   136
   ...
   16 |   136
(16 rows)
```

**Check Boston College (Team ID 103):**
```bash
psql -U postgres -d sports_db << EOF
SELECT week, team_name, points_per_game,
       points_allowed_per_game, turnover_margin
FROM ncaaf_team_stats
WHERE team_id = '103' AND season_year = 2025
ORDER BY week;
EOF
```

**Expected:** 16 rows with complete statistics

---

## Data Structure

Each team record contains:

| Field | Type | Description |
|-------|------|-------------|
| team_id | VARCHAR | Team identifier (e.g., '103' for Boston College) |
| team_name | VARCHAR | Full team name (e.g., 'Boston College Eagles') |
| week | INT | Week number (1-16) |
| season_year | INT | Season year (2025) |
| games_played | FLOAT | Games played in week |
| points_per_game | FLOAT | Offensive scoring average |
| passing_yards_per_game | FLOAT | Average passing yards |
| rushing_yards_per_game | FLOAT | Average rushing yards |
| total_yards_per_game | FLOAT | Total offensive yards average |
| points_allowed_per_game | FLOAT | Defensive points allowed average |
| passing_yards_allowed_per_game | FLOAT | Passing defense average |
| rushing_yards_allowed_per_game | FLOAT | Rushing defense average |
| total_yards_allowed_per_game | FLOAT | Total defense average |
| turnover_margin | FLOAT | Giveaways minus takeaways |
| third_down_pct | FLOAT | Third down conversion percentage |
| takeaways | INT | Turnovers forced |
| giveaways | INT | Turnovers committed |

---

## Boston College Verification

After loading, verify Boston College data:

```bash
psql -U postgres -d sports_db << EOF
\x on
SELECT *
FROM ncaaf_team_stats
WHERE team_id = '103' AND season_year = 2025 AND week = 1;
\x off
EOF
```

**Expected Result:**
- Team ID: 103
- Team Name: Boston College Eagles
- Season: 2025
- Week: 1
- All 14 statistical fields populated with real data

---

## Troubleshooting

### Error: "Teams file not found"

**Fix:**
```bash
# Verify teams file exists
ls data/current/espn_teams.json

# If not found, load teams first
uv run python scripts/database/load_teams.py
```

### Error: "Failed to connect to database"

**Fix:**
```bash
# Verify PostgreSQL running
psql -U postgres -c "SELECT 1;"

# Create database if missing
createdb sports_db -U postgres

# Create schema
psql -U postgres -d sports_db -f scripts/database/create_ncaaf_schema.sql
```

### Error: "No data file found for Week X"

**Fix:**
```bash
# Verify collection created files
ls -lah data/historical/ncaaf_2025/

# Re-run collector
uv run python scripts/database/collect_2025_ncaaf_season.py
```

### Error: "relation ncaaf_team_stats does not exist"

**Fix:**
```bash
# Create schema
psql -U postgres -d sports_db -f scripts/database/create_ncaaf_schema.sql

# Verify table created
psql -U postgres -d sports_db -c "\dt ncaaf_team_stats;"
```

---

## FAQ

**Q: How long does this take?**
A: Total 20-30 minutes (collection 15-20 min, loading 5-10 min, verification <1 min)

**Q: Can I re-run collection?**
A: Yes, it will overwrite previous files. Each run creates timestamped files.

**Q: Can I re-run loading?**
A: Yes, INSERT ON CONFLICT handles duplicates. Safe to re-run multiple times.

**Q: What if collection fails mid-week?**
A: Collected weeks are saved. Re-run to continue from where it stopped.

**Q: Can I load only specific weeks?**
A: Yes, manually run collector with `--start-week` and `--end-week` parameters.

**Q: Is Boston College (Team ID 103) included?**
A: Yes, verified during collection and loading. Query results confirm presence.

**Q: What statistical fields are included?**
A: 14 fields: 5 offensive, 4 defensive, 5 advanced metrics (turnovers, 3rd down %, etc.)

---

## Next Steps

### Immediate
1. Verify load completed (check results above)
2. Query specific team data
3. Use stats in edge detection

### Integration
```python
# Use in edge detection
from src.walters_analyzer.valuation.ncaaf_edge_detector import detect_edges

# Stats available for power rating enhancement
# Edge detector uses: PPG, PAPG, turnover margin, yards per game
```

### Weekly Updates
```bash
# Add Week 17 data (if playoff week exists)
uv run python scripts/database/collect_2025_ncaaf_season.py --start-week 17 --end-week 17
uv run python scripts/database/load_2025_historical_stats.py
```

---

## Complete Workflow Summary

| Step | Command | Time | Output |
|------|---------|------|--------|
| 1. Collect | `collect_2025_ncaaf_season.py` | 15-20 min | 16 JSON files (data/historical/ncaaf_2025/) |
| 2. Load | `load_2025_historical_stats.py` | 5-10 min | 2,176 records in ncaaf_team_stats |
| 3. Verify | SQL query | <1 min | Confirmation of load success |
| **Total** | | **20-30 min** | **All 136 teams, weeks 1-16** |

---

## Documentation

- **Full Documentation:** `docs/NCAAF_2025_HISTORICAL_DATA_SYSTEM.md`
- **Database Schema:** `scripts/database/create_ncaaf_schema.sql`
- **Boston College Example:** `docs/BOSTON_COLLEGE_DATA_EXAMPLE.md`
- **PostgreSQL Setup:** `docs/POSTGRES_IMPLEMENTATION_COMPLETE.md`

---

**Status:** ✅ Ready to Execute
**Created:** November 24, 2025
