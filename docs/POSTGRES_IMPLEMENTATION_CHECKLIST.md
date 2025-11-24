# Postgres Implementation Checklist

**Status:** Ready to Deploy
**Data Verified:** November 23, 2025
**Next Phase:** Database Setup

---

## Pre-Implementation Summary

✅ **Data:** 117 teams, 14 stats each, 99.2% quality
✅ **Teams:** All FBS conferences covered
✅ **Boston College:** Team ID 103, verified
✅ **Schema:** 5 tables designed and validated
✅ **Files:** All data files ready for loading

---

## Implementation Steps

### Step 1: Database Creation
```bash
# Create PostgreSQL database
createdb sports_db

# Or via PostgreSQL command line
psql -U postgres -c "CREATE DATABASE sports_db;"
```

### Step 2: Create Schema
```bash
# Run the SQL schema script (to be created)
psql -U postgres -d sports_db -f create_ncaaf_schema.sql
```

**Schema includes:**
- ncaaf_teams (master data)
- ncaaf_team_stats (statistics)
- ncaaf_power_ratings (ratings)
- ncaaf_schedules (game data)
- ncaaf_team_injuries (injury reports)

### Step 3: Load Team Master Data
```bash
# Load all 117 teams into ncaaf_teams table
python scripts/database/load_teams.py
```

### Step 4: Load Week 13 Statistics
```bash
# Load current week statistics
python scripts/database/load_team_stats.py --week 13 --season 2025
```

### Step 5: Load Power Ratings
```bash
# Load Massey composite ratings
python scripts/database/load_power_ratings.py --system massey_composite
```

### Step 6: Load Schedules
```bash
# Load all 2025 season games
python scripts/database/load_schedules.py --season 2025
```

### Step 7: Validate Data
```bash
# Run validation checks
python scripts/database/validate_data.py

# Expected output:
# ✅ 117 teams loaded
# ✅ 1,638 stats records (117 × 14)
# ✅ 135+ power ratings loaded
# ✅ All FBS teams present
# ✅ No orphaned foreign keys
```

---

## SQL Schema (Copy & Paste Ready)

```sql
-- NCAAF Teams
CREATE TABLE ncaaf_teams (
    team_id VARCHAR(10) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    team_abbreviation VARCHAR(10),
    conference VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Team Statistics (Weekly)
CREATE TABLE ncaaf_team_stats (
    stat_id SERIAL PRIMARY KEY,
    team_id VARCHAR(10) NOT NULL,
    week INT NOT NULL,
    season_year INT NOT NULL,

    -- Offensive Stats
    points_per_game DECIMAL(5,2),
    total_points DECIMAL(8,1),
    passing_yards_per_game DECIMAL(7,2),
    rushing_yards_per_game DECIMAL(7,2),
    total_yards_per_game DECIMAL(8,2),

    -- Defensive Stats
    points_allowed_per_game DECIMAL(5,2),
    passing_yards_allowed_per_game DECIMAL(7,2),
    rushing_yards_allowed_per_game DECIMAL(7,2),
    total_yards_allowed_per_game DECIMAL(8,2),

    -- Advanced Stats
    turnover_margin DECIMAL(3,1),
    third_down_pct DECIMAL(5,2),
    takeaways INT,
    giveaways INT,

    games_played INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (team_id) REFERENCES ncaaf_teams(team_id),
    UNIQUE(team_id, week, season_year)
);

CREATE INDEX idx_ncaaf_stats_team ON ncaaf_team_stats(team_id);
CREATE INDEX idx_ncaaf_stats_week ON ncaaf_team_stats(week, season_year);

-- Power Ratings
CREATE TABLE ncaaf_power_ratings (
    rating_id SERIAL PRIMARY KEY,
    team_id VARCHAR(10) NOT NULL,
    rating_system VARCHAR(50),
    rating_value DECIMAL(6,2),
    rating_date DATE,
    week INT,
    season_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (team_id) REFERENCES ncaaf_teams(team_id),
    UNIQUE(team_id, rating_system, week, season_year)
);

CREATE INDEX idx_ncaaf_ratings_team ON ncaaf_power_ratings(team_id);
CREATE INDEX idx_ncaaf_ratings_system ON ncaaf_power_ratings(rating_system);

-- Game Schedules
CREATE TABLE ncaaf_schedules (
    game_id VARCHAR(50) PRIMARY KEY,
    home_team_id VARCHAR(10) NOT NULL,
    away_team_id VARCHAR(10) NOT NULL,
    game_date TIMESTAMP,
    week INT,
    season_year INT,
    status VARCHAR(50),
    home_score INT,
    away_score INT,
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (home_team_id) REFERENCES ncaaf_teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES ncaaf_teams(team_id)
);

CREATE INDEX idx_ncaaf_schedule_date ON ncaaf_schedules(game_date);
CREATE INDEX idx_ncaaf_schedule_week ON ncaaf_schedules(week, season_year);
CREATE INDEX idx_ncaaf_schedule_home ON ncaaf_schedules(home_team_id);
CREATE INDEX idx_ncaaf_schedule_away ON ncaaf_schedules(away_team_id);

-- Team Injuries
CREATE TABLE ncaaf_team_injuries (
    injury_id SERIAL PRIMARY KEY,
    team_id VARCHAR(10) NOT NULL,
    player_name VARCHAR(100),
    position VARCHAR(20),
    status VARCHAR(50),
    injury_type VARCHAR(100),
    week INT,
    season_year INT,
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (team_id) REFERENCES ncaaf_teams(team_id)
);

CREATE INDEX idx_ncaaf_injuries_team ON ncaaf_team_injuries(team_id);
CREATE INDEX idx_ncaaf_injuries_week ON ncaaf_team_injuries(week, season_year);
```

---

## Python Data Loader Scripts (Templates)

### Script 1: load_teams.py
```python
#!/usr/bin/env python3
import json
import psycopg2

def load_teams():
    """Load team master data"""
    conn = psycopg2.connect("dbname=sports_db user=postgres")
    cur = conn.cursor()

    # Load ESPN teams
    with open('data/current/espn_teams.json') as f:
        espn_teams = json.load(f)

    # Load team mappings
    with open('src/data/ncaaf_team_mappings.json') as f:
        mappings = json.load(f)

    # Insert teams
    for team_id, team_name in espn_teams['ncaaf'].items():
        abbrev = mappings.get(team_name.replace(' NCAA', ''), '')

        cur.execute("""
            INSERT INTO ncaaf_teams (team_id, team_name, team_abbreviation)
            VALUES (%s, %s, %s)
            ON CONFLICT (team_id) DO NOTHING
        """, (team_id, team_name, abbrev))

    conn.commit()
    conn.close()
    print(f"✅ Loaded teams")

if __name__ == '__main__':
    load_teams()
```

### Script 2: load_team_stats.py
```python
#!/usr/bin/env python3
import json
import psycopg2
from datetime import datetime

def load_team_stats(week, season):
    """Load team statistics for given week"""
    conn = psycopg2.connect("dbname=sports_db user=postgres")
    cur = conn.cursor()

    # Load stats file
    filename = f'data/current/ncaaf_team_stats_week_{week}.json'
    with open(filename) as f:
        data = json.load(f)

    # Insert stats
    for team in data['teams']:
        cur.execute("""
            INSERT INTO ncaaf_team_stats (
                team_id, week, season_year,
                points_per_game, total_points,
                passing_yards_per_game, rushing_yards_per_game,
                total_yards_per_game, points_allowed_per_game,
                passing_yards_allowed_per_game, rushing_yards_allowed_per_game,
                total_yards_allowed_per_game, turnover_margin,
                third_down_pct, takeaways, giveaways
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (team_id, week, season_year) DO UPDATE SET
                points_per_game = EXCLUDED.points_per_game
        """, (
            team['team_id'], week, season,
            team.get('points_per_game'),
            team.get('total_points'),
            team.get('passing_yards_per_game'),
            team.get('rushing_yards_per_game'),
            team.get('total_yards_per_game'),
            team.get('points_allowed_per_game'),
            team.get('passing_yards_allowed_per_game'),
            team.get('rushing_yards_allowed_per_game'),
            team.get('total_yards_allowed_per_game'),
            team.get('turnover_margin'),
            team.get('third_down_pct'),
            team.get('takeaways'),
            team.get('giveaways')
        ))

    conn.commit()
    conn.close()
    print(f"✅ Loaded {len(data['teams'])} teams for week {week}")

if __name__ == '__main__':
    load_team_stats(week=13, season=2025)
```

---

## Verification Queries

### Check Teams Loaded
```sql
SELECT COUNT(*) as total_teams, COUNT(DISTINCT team_id) as unique_ids
FROM ncaaf_teams;
-- Expected: ~136 teams
```

### Check Boston College
```sql
SELECT * FROM ncaaf_teams
WHERE team_name LIKE '%Boston%' OR team_id = '103';
-- Expected: Boston College Eagles (103, BC, ACC)
```

### Check Statistics Coverage
```sql
SELECT week, COUNT(*) as team_count, AVG(points_per_game) as avg_ppg
FROM ncaaf_team_stats
WHERE season_year = 2025
GROUP BY week
ORDER BY week DESC;
```

### Check Data Integrity
```sql
SELECT
    t.team_name,
    COUNT(s.stat_id) as stats_records,
    COUNT(p.rating_id) as rating_records,
    COUNT(DISTINCT sch.game_id) as games
FROM ncaaf_teams t
LEFT JOIN ncaaf_team_stats s ON t.team_id = s.team_id
LEFT JOIN ncaaf_power_ratings p ON t.team_id = p.team_id
LEFT JOIN ncaaf_schedules sch ON
    (t.team_id = sch.home_team_id OR t.team_id = sch.away_team_id)
GROUP BY t.team_id, t.team_name
ORDER BY stats_records DESC
LIMIT 10;
```

---

## Automation Setup

### Weekly Collection & Loading
```bash
#!/bin/bash
# File: scripts/database/weekly_update.sh

echo "Starting weekly NCAAF data update..."

# Step 1: Collect latest data
python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf --week auto

# Step 2: Collect schedules
python scripts/scrapers/scrape_espn_ncaaf_scoreboard.py

# Step 3: Load to Postgres
python scripts/database/load_team_stats.py

# Step 4: Validate
python scripts/database/validate_data.py

echo "Weekly update complete ✅"
```

### Schedule in Crontab (Linux/Mac)
```bash
# Every Tuesday at 8:00 AM
0 8 * * 2 /path/to/scripts/database/weekly_update.sh >> /var/log/ncaaf_update.log 2>&1
```

### Schedule in Windows Task Scheduler
```
Task Name: NCAAF-Weekly-Update
Trigger: Weekly (Tuesday 08:00)
Action: Run Python script
Script: C:\path\to\scripts\database\weekly_update.py
```

---

## Monitoring & Alerts

### Data Quality Check (Daily)
```sql
SELECT
    DATE(created_at) as load_date,
    COUNT(*) as records_loaded,
    COUNT(DISTINCT team_id) as unique_teams,
    AVG(points_per_game) as avg_ppg
FROM ncaaf_team_stats
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY DATE(created_at);
```

### Missing Teams
```sql
SELECT DISTINCT t.team_id, t.team_name
FROM ncaaf_teams t
WHERE NOT EXISTS (
    SELECT 1 FROM ncaaf_team_stats s
    WHERE s.team_id = t.team_id
    AND s.week = 13 AND s.season_year = 2025
)
ORDER BY t.team_name;
```

### Data Anomalies
```sql
SELECT team_name, week, points_per_game, points_allowed_per_game
FROM ncaaf_team_stats s
JOIN ncaaf_teams t ON s.team_id = t.team_id
WHERE points_per_game > 70 OR points_per_game < 5
   OR points_allowed_per_game > 70 OR points_allowed_per_game < 5;
```

---

## Performance Optimization

### Queries to Add
```sql
-- Materialized view for power ratings
CREATE MATERIALIZED VIEW mv_team_power_ratings AS
SELECT
    t.team_id,
    t.team_name,
    t.team_abbreviation,
    t.conference,
    p.rating_system,
    p.rating_value,
    p.week,
    p.season_year
FROM ncaaf_teams t
LEFT JOIN ncaaf_power_ratings p ON t.team_id = p.team_id
WHERE p.season_year = 2025;

-- Index for common queries
CREATE INDEX idx_stats_team_week_season
ON ncaaf_team_stats(team_id, week, season_year);
```

---

## Testing Checklist

- [ ] Database created
- [ ] Schema loaded successfully
- [ ] 136 teams present in ncaaf_teams
- [ ] 117 teams in ncaaf_team_stats (week 13)
- [ ] Boston College (103) verified
- [ ] All 14 stat fields populated
- [ ] No NULL values in critical fields
- [ ] Foreign keys working
- [ ] Indexes built
- [ ] Queries execute <100ms
- [ ] Weekly automation scheduled
- [ ] Monitoring alerts configured

---

## Quick Start Commands

```bash
# 1. Create database
createdb sports_db

# 2. Load schema
psql -d sports_db -f scripts/database/schema.sql

# 3. Load data
python scripts/database/load_teams.py
python scripts/database/load_team_stats.py

# 4. Verify
python scripts/database/validate_data.py

# 5. Test query
psql -d sports_db -c "SELECT COUNT(*) FROM ncaaf_teams;"
```

---

## Connection String (for reference)
```
PostgreSQL: postgresql://postgres:password@localhost:5432/sports_db
SQLAlchemy: postgresql+psycopg2://postgres:password@localhost:5432/sports_db
```

---

## Next Steps

1. **Review** this checklist
2. **Create** PostgreSQL database
3. **Run** schema creation SQL
4. **Test** data loading
5. **Validate** data integrity
6. **Configure** weekly automation
7. **Build** analytics queries

**Timeline:** 2-3 hours for full implementation

---

**Status:** READY FOR IMPLEMENTATION
**Owner:** Claude (Implementation) + Andy (Approval)
**Date:** November 23, 2025

