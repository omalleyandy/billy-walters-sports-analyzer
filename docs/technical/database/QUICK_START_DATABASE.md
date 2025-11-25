# Quick Start: NFL Database & Data Collection

## TL;DR - 3 Steps to Get Started

### 1. Setup Database (One-Time)
```bash
uv run python scripts/database/setup_complete_schema.py --password "Omarley@2025"
```

### 2. Load Sample Data (Testing)
```bash
uv run python scripts/database/load_sample_nfl_data.py --password "Omarley@2025"
```

### 3. Verify & Test
```bash
# Test edge detection
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector

# Or check database
psql -U postgres -d sports_db -c "SELECT COUNT(*) FROM games;"
```

**Done!** Your database is ready.

---

## Command Reference

### Database Setup
```bash
# Complete setup (base schema + NFL extensions)
uv run python scripts/database/setup_complete_schema.py --password "Omarley@2025"

# Or just NFL extensions
uv run python scripts/database/setup_nfl_schema.py --password "Omarley@2025"
```

### Data Loading

#### Load Sample Data (for testing)
```bash
uv run python scripts/database/load_sample_nfl_data.py --password "Omarley@2025"
```

#### Load Real 2025 Data (when available)
```bash
# Collect from ESPN
uv run python scripts/database/collect_2025_nfl_season.py

# Load to database
uv run python scripts/database/load_2025_nfl_season.py --password "Omarley@2025"
```

#### Load Real 2024 Data (for reference)
```bash
# Collect from ESPN (if ESPN API working)
uv run python scripts/database/collect_2024_nfl_season.py

# Load to database
uv run python scripts/database/load_2025_nfl_season.py --password "Omarley@2025"
```

### Database Access

#### Via psql
```bash
# Connect
psql -U postgres -d sports_db

# List tables
\dt

# Show schema
\d games
```

#### Via Python
```bash
import psycopg2
conn = psycopg2.connect(
    dbname="sports_db",
    user="postgres",
    password="Omarley@2025",
    host="localhost",
    port=5432
)
```

---

## What's in the Database

### After Setup
- ✅ 12 tables (games, teams, power_ratings, odds, weather, injuries, etc.)
- ✅ 4 views (nfl_weekly_averages, nfl_team_rankings_by_week, etc.)
- ✅ Validation functions

### After Loading Sample Data
- ✅ 32 NFL teams
- ✅ 5 Week 12 games with scores
- ✅ 384 team statistics records (12 weeks × 32 teams)
- ✅ Ready for edge detection testing

### Currently Empty (Waiting for Data)
- Power ratings (load from `/power-ratings`)
- Odds (load from `/scrape-overtime`)
- Weather (load from AccuWeather)
- Injuries (load from ESPN)
- Bets (manual entry or auto-import)

---

## Common Tasks

### Run Edge Detection
```bash
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector
```

### Check Week 12 Games
```sql
SELECT home_team, away_team, home_score, away_score, game_date
FROM games
WHERE week = 12 AND season = 2025
ORDER BY game_date;
```

### Get Team Stats for Analysis
```sql
SELECT team_name, points_per_game, points_allowed_per_game, total_yards_per_game
FROM nfl_team_stats
WHERE week = 12 AND season_year = 2025
ORDER BY points_per_game DESC;
```

### Load More Sample Data
```bash
# Run the sample loader again
uv run python scripts/database/load_sample_nfl_data.py --password "Omarley@2025"
```

### Reset Everything
```bash
# WARNING: Deletes all data
dropdb sports_db
createdb sports_db
uv run python scripts/database/setup_complete_schema.py --password "Omarley@2025"
uv run python scripts/database/load_sample_nfl_data.py --password "Omarley@2025"
```

---

## Troubleshooting

### "password authentication failed"
Use correct password in commands:
```bash
--password "Omarley@2025"
```

### "table does not exist"
Run schema setup:
```bash
uv run python scripts/database/setup_complete_schema.py --password "Omarley@2025"
```

### "HTTP 500" errors
ESPN API is down. Use sample data instead:
```bash
uv run python scripts/database/load_sample_nfl_data.py --password "Omarley@2025"
```

### Can't connect to PostgreSQL
Check PostgreSQL is running:
```bash
psql -U postgres -c "SELECT 1;"
```

---

## File Locations

### Scripts
- Database setup: `scripts/database/setup_complete_schema.py`
- Data loading: `scripts/database/load_2025_nfl_season.py`
- Sample data: `scripts/database/load_sample_nfl_data.py`

### Documentation
- This file: `docs/QUICK_START_DATABASE.md`
- Full setup: `docs/NFL_2025_SETUP_COMPLETE.md`
- Troubleshooting: `docs/NFL_2025_SETUP_TROUBLESHOOTING.md`
- Database ready: `docs/NFL_2025_DATABASE_READY.md`

### Data Directories
- Collected data: `data/historical/nfl_2025/`
- Collected data: `data/historical/nfl_2024/`

---

## Next Steps

1. **For Testing**: Load sample data and run edge detection
   ```bash
   uv run python scripts/database/load_sample_nfl_data.py --password "Omarley@2025"
   uv run python -m walters_analyzer.valuation.billy_walters_edge_detector
   ```

2. **For Real Data**: Wait for ESPN API, then collect 2025 data
   ```bash
   uv run python scripts/database/collect_2025_nfl_season.py
   uv run python scripts/database/load_2025_nfl_season.py --password "Omarley@2025"
   ```

3. **For Analysis**: Add power ratings and odds
   ```bash
   /power-ratings
   /scrape-overtime
   /edge-detector
   ```

4. **For Results**: Track performance
   ```bash
   /clv-tracker
   /betting-card
   ```

---

## Connection Info

```
Host:     localhost
Port:     5432
Database: sports_db
User:     postgres
Password: Omarley@2025
```

That's it! Your database is ready to use.
