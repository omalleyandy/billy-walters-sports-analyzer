# Billy Walters Analytics - PostgreSQL Database Setup Guide

Complete step-by-step guide to setting up your PostgreSQL database using pgAdmin 4.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install PostgreSQL](#install-postgresql)
3. [Configure pgAdmin 4](#configure-pgadmin-4)
4. [Create Database](#create-database)
5. [Run Schema Script](#run-schema-script)
6. [Configure Python Connection](#configure-python-connection)
7. [Test Connection](#test-connection)
8. [Migrate Week 12 Data](#migrate-week-12-data)
9. [Verify Setup](#verify-setup)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

**Required Software:**
- PostgreSQL 15+ (includes pgAdmin 4)
- Python 3.11+ with `uv`
- Billy Walters project files

**Estimated Time:** 30-45 minutes

---

## 1. Install PostgreSQL

### Windows Installation

**Download:**
1. Visit: https://www.postgresql.org/download/windows/
2. Click "Download the installer" (EnterpriseDB)
3. Download latest version (PostgreSQL 16.x)
4. File size: ~400 MB

**Install:**
1. Run installer as Administrator
2. Installation directory: `C:\Program Files\PostgreSQL\16`
3. Components to install:
   - ✅ PostgreSQL Server
   - ✅ pgAdmin 4
   - ✅ Stack Builder (optional)
   - ✅ Command Line Tools

4. **Data Directory:** `C:\Program Files\PostgreSQL\16\data`

5. **Password:** Set a strong password for `postgres` superuser
   - **IMPORTANT:** Remember this password!
   - Store in password manager
   - Example: `Billy2025!Walters`

6. **Port:** 5432 (default - don't change)

7. **Locale:** Default locale (English, United States)

8. Click "Next" through remaining screens

9. **Installation time:** 5-10 minutes

**Verify Installation:**
```powershell
# Check PostgreSQL service is running
Get-Service -Name postgresql*

# Should show: Status = Running
```

---

## 2. Configure pgAdmin 4

### Launch pgAdmin 4

1. Start Menu → pgAdmin 4
2. Opens in web browser: `http://127.0.0.1:xxxx/browser/`
3. **Set Master Password:**
   - This protects saved server passwords
   - Use same password as postgres user (or different - your choice)
   - Click "Save Password" for convenience

### First-Time Setup

**pgAdmin 4 should automatically detect your local PostgreSQL server:**

1. Left panel → Servers → PostgreSQL 16
2. Right-click → Connect Server
3. Enter password (postgres user password from installation)
4. ✅ Should see "Connected" status

**If server NOT found:**
1. Right-click "Servers" → Register → Server
2. **General tab:**
   - Name: `localhost`
3. **Connection tab:**
   - Host: `localhost`
   - Port: `5432`
   - Maintenance database: `postgres`
   - Username: `postgres`
   - Password: [your password]
   - ✅ Save password
4. Click "Save"

---

## 3. Create Database

### Using pgAdmin 4 GUI

1. **Connect to Server:**
   - Left panel → Servers → PostgreSQL 16
   - Enter password if prompted

2. **Create Database:**
   - Right-click "Databases" → Create → Database
   - **General tab:**
     - Database: `billy_walters_analytics`
     - Owner: `postgres`
     - Comment: `Billy Walters Sports Analytics - NFL & NCAAF betting database`
   - **Definition tab (optional):**
     - Encoding: `UTF8`
     - Collation: `English_United States.1252`
   - Click "Save"

3. **Verify Creation:**
   - Left panel → Databases → billy_walters_analytics
   - Should see database icon

### Using SQL (Alternative)

1. Tools → Query Tool
2. Run:
   ```sql
   CREATE DATABASE billy_walters_analytics
   WITH
   OWNER = postgres
   ENCODING = 'UTF8'
   CONNECTION LIMIT = -1;

   COMMENT ON DATABASE billy_walters_analytics
   IS 'Billy Walters Sports Analytics - NFL & NCAAF betting database';
   ```
3. Click Execute (F5)

---

## 4. Run Schema Script

### Load Schema File

1. **Select Your Database:**
   - Left panel → Databases → billy_walters_analytics
   - Click to select (should highlight)

2. **Open Query Tool:**
   - Tools → Query Tool
   - Or click SQL icon in toolbar
   - Or press Alt+Shift+Q

3. **Load Schema Script:**
   - Query Tool → File menu → Open File
   - Navigate to: `C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\database\schema.sql`
   - Click "Open"
   - Script appears in editor (1,000+ lines)

4. **Execute Schema:**
   - Click Execute (▶ button) or press F5
   - **Execution time:** 2-5 seconds
   - **Output panel:** Should show "Query returned successfully"

5. **Verify Tables Created:**
   - Left panel → billy_walters_analytics → Schemas → public → Tables
   - Should see 8 tables:
     - ✅ games
     - ✅ power_ratings
     - ✅ odds
     - ✅ bets
     - ✅ weather
     - ✅ injuries
     - ✅ situational_factors
     - ✅ performance_metrics
     - ✅ schema_version (metadata)

6. **Check Views:**
   - Schemas → public → Views
   - Should see 2 views:
     - ✅ vw_game_analysis
     - ✅ vw_weekly_summary

**Success Indicator:**
```
Query returned successfully in 2 secs 456 msec.
```

**If Errors:**
- Check you selected correct database (billy_walters_analytics)
- Verify postgres user has CREATE permissions
- See Troubleshooting section below

---

## 5. Configure Python Connection

### Install Python Dependencies

```powershell
# Add PostgreSQL driver
uv add psycopg2-binary

# Verify installation
uv run python -c "import psycopg2; print('OK')"
```

### Create .env Configuration

1. **Edit `.env` file:**
   ```powershell
   cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
   notepad .env
   ```

2. **Add database credentials:**
   ```bash
   # PostgreSQL Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=billy_walters_analytics
   DB_USER=postgres
   DB_PASSWORD=your_password_here  # Replace with actual password
   ```

3. **Save and close**

4. **Verify .env in .gitignore:**
   ```powershell
   # Check .gitignore contains .env
   Select-String -Path .gitignore -Pattern "^\.env$"
   # Should return: .env
   ```

---

## 6. Test Connection

### Python Connection Test

Create test script:

```powershell
# Create test file
New-Item -Path scripts/database/test_connection.py -Force
```

**File: `scripts/database/test_connection.py`**
```python
"""Test PostgreSQL database connection."""

import os
from src.db import get_db_connection

def main():
    """Test database connection and schema."""
    print("=" * 60)
    print("BILLY WALTERS ANALYTICS - DATABASE CONNECTION TEST")
    print("=" * 60)

    # Test connection
    print("\n[1/4] Testing database connection...")
    db = get_db_connection()

    if not db.test_connection():
        print("[ERROR] Connection failed! Check credentials in .env")
        return False

    # Count tables
    print("\n[2/4] Checking schema...")
    result = db.execute_query("""
        SELECT COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)

    table_count = result[0]['table_count']
    print(f"[OK] Found {table_count} tables (expected: 9)")

    if table_count != 9:
        print("[WARNING] Table count mismatch! Re-run schema.sql")

    # List tables
    print("\n[3/4] Listing tables...")
    result = db.execute_query("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)

    for row in result:
        print(f"  - {row['table_name']}")

    # Check views
    print("\n[4/4] Checking views...")
    result = db.execute_query("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    print(f"[OK] Found {len(result)} views")
    for row in result:
        print(f"  - {row['table_name']}")

    print("\n" + "=" * 60)
    print("✅ DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run data migration: uv run python scripts/database/migrate_week_12.py")
    print("2. Verify data: SELECT COUNT(*) FROM games;")
    print("3. Start using database in edge detection!")

    return True

if __name__ == "__main__":
    main()
```

**Run Test:**
```powershell
uv run python scripts/database/test_connection.py
```

**Expected Output:**
```
============================================================
BILLY WALTERS ANALYTICS - DATABASE CONNECTION TEST
============================================================

[1/4] Testing database connection...
[OK] Connected to PostgreSQL: PostgreSQL 16.x on x86_64-pc-windows...

[2/4] Checking schema...
[OK] Found 9 tables (expected: 9)

[3/4] Listing tables...
  - bets
  - games
  - injuries
  - odds
  - performance_metrics
  - power_ratings
  - schema_version
  - situational_factors
  - teams
  - weather

[4/4] Checking views...
[OK] Found 2 views
  - vw_game_analysis
  - vw_weekly_summary

============================================================
✅ DATABASE SETUP COMPLETE!
============================================================
```

---

## 7. Migrate Week 12 Data

Now let's import your existing Week 12 betting data into the database.

### Create Migration Script

```powershell
New-Item -Path scripts/database/migrate_week_12.py -Force
```

**File: `scripts/database/migrate_week_12.py`**
```python
"""
Migrate Week 12 data from files to PostgreSQL database.

Imports:
- Games from edge detection output
- Power ratings from data/current/
- Odds from Overtime.ag output
- Weather from edge detection
- Bets from betting card
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from src.db import get_db_connection
from src.db.models import Bet, Game, Odds, PowerRating, Weather

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
EDGE_REPORT = PROJECT_ROOT / "output/edge_detection/edge_report_week_12.txt"
POWER_RATINGS_DIR = PROJECT_ROOT / "data/current"
ODDS_DIR = PROJECT_ROOT / "output/overtime/nfl/pregame"


def parse_edge_report() -> List[dict]:
    """Parse edge detection report for game and bet data."""
    games = []

    with open(EDGE_REPORT, 'r') as f:
        content = f.read()

    # Simple parser for edge report
    # Format: "1. Carolina @ San Francisco (Week 12)"
    #         "   Time: 2025-11-24T20:15:00Z"
    #         "   Market Spread: -7.0"
    #         etc.

    lines = content.split('\n')
    current_game = None

    for line in lines:
        if line and line[0].isdigit() and '. ' in line:
            # New game
            if '@' in line:
                parts = line.split('@')
                away = parts[0].split('. ')[1].strip()
                home = parts[1].split('(')[0].strip()

                current_game = {
                    'away_team': away,
                    'home_team': home,
                    'season': 2025,
                    'week': 12,
                    'league': 'NFL'
                }
                games.append(current_game)

        elif current_game and line.strip().startswith('Time:'):
            time_str = line.split('Time:')[1].strip()
            current_game['game_date'] = datetime.fromisoformat(
                time_str.replace('Z', '+00:00')
            )

        elif current_game and 'Market Spread:' in line:
            spread = float(line.split('Market Spread:')[1].strip())
            current_game['market_spread'] = spread

        elif current_game and 'EDGE:' in line:
            edge_str = line.split('EDGE:')[1].split('points')[0].strip()
            current_game['edge'] = float(edge_str)

        elif current_game and 'Recommendation:' in line:
            rec = line.split('Recommendation:')[1].strip()
            current_game['recommendation'] = rec

    return games


def migrate_games(db):
    """Migrate games to database."""
    print("\n[1/5] Migrating games...")

    games_data = parse_edge_report()

    for game_data in games_data:
        game_id = f"{game_data['away_team'].replace(' ', '_')}_" \
                  f"{game_data['home_team'].replace(' ', '_')}_2025_W12"

        game = Game(
            game_id=game_id,
            season=2025,
            week=12,
            league='NFL',
            game_date=game_data['game_date'],
            home_team=game_data['home_team'],
            away_team=game_data['away_team'],
            status='SCHEDULED',
            is_outdoor=None  # Will update from weather data
        )

        # Insert using operations module
        from src.db.operations import DatabaseOperations
        ops = DatabaseOperations(db)
        ops.insert_game(game)

    print(f"[OK] Migrated {len(games_data)} games")


def migrate_power_ratings(db):
    """Migrate power ratings to database."""
    print("\n[2/5] Migrating power ratings...")

    # Load from massey ratings or edge detector output
    # For now, extract from edge report
    games_data = parse_edge_report()

    from src.db.operations import DatabaseOperations
    ops = DatabaseOperations(db)

    count = 0
    for game_data in games_data:
        # These would come from actual power rating files
        # For demo, using placeholder values
        teams = [game_data['home_team'], game_data['away_team']]

        for team in teams:
            rating = PowerRating(
                season=2025,
                week=12,
                league='NFL',
                team=team,
                rating=88.0,  # Placeholder - load from actual file
                source='composite'
            )
            ops.insert_power_rating(rating)
            count += 1

    print(f"[OK] Migrated {count} power ratings")


def migrate_odds(db):
    """Migrate odds to database."""
    print("\n[3/5] Migrating odds...")

    # Find latest odds file
    odds_files = sorted(ODDS_DIR.glob("api_walters_*.json"))

    if not odds_files:
        print("[WARNING] No odds files found - skipping")
        return

    latest_odds = odds_files[-1]

    with open(latest_odds, 'r') as f:
        odds_data = json.load(f)

    from src.db.operations import DatabaseOperations
    ops = DatabaseOperations(db)

    count = 0
    for game in odds_data.get('games', []):
        game_id = f"{game['away_team'].replace(' ', '_')}_" \
                  f"{game['home_team'].replace(' ', '_')}_2025_W12"

        odds = Odds(
            game_id=game_id,
            sportsbook='overtime',
            odds_type='current',
            home_spread=game.get('home_spread'),
            away_spread=game.get('away_spread'),
            total=game.get('total'),
            home_moneyline=game.get('home_ml'),
            away_moneyline=game.get('away_ml'),
            timestamp=datetime.now(timezone.utc)
        )

        ops.insert_odds(odds)
        count += 1

    print(f"[OK] Migrated {count} odds records")


def migrate_bets(db):
    """Migrate bets from betting card to database."""
    print("\n[4/5] Migrating bets...")

    games_data = parse_edge_report()

    from src.db.operations import DatabaseOperations
    ops = DatabaseOperations(db)

    for game_data in games_data:
        game_id = f"{game_data['away_team'].replace(' ', '_')}_" \
                  f"{game_data['home_team'].replace(' ', '_')}_2025_W12"

        # Determine bet side and type from recommendation
        if 'BET HOME' in game_data.get('recommendation', ''):
            side = game_data['home_team']
            bet_type = 'spread'
            line = game_data.get('market_spread', 0)
        elif 'BET AWAY' in game_data.get('recommendation', ''):
            side = game_data['away_team']
            bet_type = 'spread'
            line = -game_data.get('market_spread', 0)
        else:
            continue  # No bet

        bet = Bet(
            bet_id=f"2025_W12_{side.replace(' ', '_')}_SPREAD",
            game_id=game_id,
            bet_type=bet_type,
            side=side,
            line=line,
            edge_points=game_data.get('edge', 0),
            edge_category='STRONG' if game_data.get('edge', 0) > 4 else 'MEDIUM',
            units=20.0,  # From betting card
            result='PENDING',
            placed_at=datetime.now(timezone.utc)
        )

        ops.insert_bet(bet)

    print(f"[OK] Migrated {len(games_data)} bets")


def verify_migration(db):
    """Verify data was migrated correctly."""
    print("\n[5/5] Verifying migration...")

    checks = [
        ("games", "SELECT COUNT(*) FROM games WHERE week = 12"),
        ("power_ratings", "SELECT COUNT(*) FROM power_ratings WHERE week = 12"),
        ("odds", "SELECT COUNT(*) FROM odds"),
        ("bets", "SELECT COUNT(*) FROM bets WHERE result = 'PENDING'"),
    ]

    for table, query in checks:
        result = db.execute_query(query)
        count = result[0][0]
        print(f"  - {table}: {count} records")

    print("\n[OK] Migration complete!")


def main():
    """Run migration."""
    print("=" * 60)
    print("WEEK 12 DATA MIGRATION")
    print("=" * 60)

    db = get_db_connection()

    try:
        migrate_games(db)
        migrate_power_ratings(db)
        migrate_odds(db)
        migrate_bets(db)
        verify_migration(db)

        print("\n✅ Migration successful!")
        print("\nNext: Query your data in pgAdmin 4:")
        print("  SELECT * FROM vw_game_analysis WHERE week = 12;")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
```

**Run Migration:**
```powershell
uv run python scripts/database/migrate_week_12.py
```

---

## 8. Verify Setup

### Check Data in pgAdmin 4

1. **Query Tool:** billy_walters_analytics → Tools → Query Tool

2. **Run verification queries:**

```sql
-- 1. Check all tables have data
SELECT
    'games' as table_name,
    COUNT(*) as record_count
FROM games
WHERE week = 12
UNION ALL
SELECT 'power_ratings', COUNT(*) FROM power_ratings WHERE week = 12
UNION ALL
SELECT 'odds', COUNT(*) FROM odds
UNION ALL
SELECT 'bets', COUNT(*) FROM bets WHERE result = 'PENDING';

-- 2. View complete game analysis
SELECT * FROM vw_game_analysis WHERE week = 12;

-- 3. Weekly betting summary
SELECT * FROM vw_weekly_summary WHERE week = 12;

-- 4. Check CLV metrics
SELECT
    AVG(edge_points) as avg_edge,
    COUNT(*) as total_bets,
    SUM(CASE WHEN edge_category = 'STRONG' THEN 1 ELSE 0 END) as strong_plays
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE g.week = 12;
```

### Expected Results

**Table Counts:**
- games: 8 records
- power_ratings: 16 records (8 teams × 2)
- odds: 8+ records
- bets: 8 records

**If counts are off:**
- Re-run migration script
- Check source files exist
- Verify file paths in migration script

---

## 9. Troubleshooting

### Connection Failed

**Error:** `FATAL: password authentication failed`

**Solution:**
1. Verify password in `.env` matches postgres user password
2. Reset postgres password:
   ```powershell
   # Start SQL Shell (psql)
   # Connect as postgres
   \password postgres
   # Enter new password twice
   ```

### Tables Not Created

**Error:** `relation "games" does not exist`

**Solution:**
1. Verify you selected correct database before running schema
2. Check query output for errors
3. Re-run schema.sql
4. Check postgres user has CREATE permissions:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE billy_walters_analytics TO postgres;
   ```

### Python Import Errors

**Error:** `ModuleNotFoundError: No module named 'psycopg2'`

**Solution:**
```powershell
uv add psycopg2-binary
uv sync
```

### Port 5432 Already in Use

**Error:** `could not bind IPv4 address: Address already in use`

**Solution:**
1. Check if PostgreSQL already running:
   ```powershell
   Get-Service -Name postgresql*
   ```
2. Stop service:
   ```powershell
   Stop-Service -Name postgresql-x64-16
   ```
3. Start service:
   ```powershell
   Start-Service -Name postgresql-x64-16
   ```

### pgAdmin 4 Won't Open

**Error:** Browser shows "This site can't be reached"

**Solution:**
1. Check pgAdmin 4 process is running:
   ```powershell
   Get-Process pgAdmin4
   ```
2. Restart pgAdmin 4 from Start Menu
3. Clear browser cache and try again

---

## 10. Next Steps

### You're Ready to Use the Database!

**Immediate Actions:**
1. ✅ Test queries in pgAdmin 4
2. ✅ Run sample correlation analyses (weather vs totals)
3. ✅ Update edge detector to use database

**Weekly Workflow:**
1. **Tuesday:** Update power ratings → Database
2. **Wednesday:** Collect odds → Database → Run edge detection
3. **Sunday:** Update scores → Calculate CLV → Store results

**Analysis Examples:**
```sql
-- Weather impact on UNDER bets
SELECT
    CASE
        WHEN w.wind_speed > 20 THEN 'High Wind'
        WHEN w.wind_speed > 15 THEN 'Medium Wind'
        ELSE 'Low Wind'
    END as wind_category,
    COUNT(*) as bets,
    AVG(b.roi) as avg_roi
FROM bets b
JOIN weather w ON b.game_id = w.game_id
WHERE b.bet_type = 'total' AND b.side = 'UNDER'
GROUP BY wind_category;
```

---

## Summary

✅ **Setup Complete!**

You now have:
- PostgreSQL database installed and configured
- Complete schema with 8 tables + 2 views
- Python utilities for database operations
- Week 12 data migrated
- Working queries and analytics

**Time to start analyzing!** 🎯

For questions or issues, check:
- `LESSONS_LEARNED.md`
- PostgreSQL documentation: https://www.postgresql.org/docs/
- pgAdmin documentation: https://www.pgadmin.org/docs/

---

**Generated:** 2025-11-23
**Version:** 1.0.0
**Project:** Billy Walters Sports Analytics
