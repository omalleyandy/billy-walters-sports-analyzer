# Billy Walters Analytics - Database Package

PostgreSQL database for systematic sports betting analytics.

---

## 📁 Files in This Directory

| File | Description | Size |
|------|-------------|------|
| `schema.sql` | Complete database schema (8 tables + 2 views) | ~1000 lines |
| `sample_queries.sql` | 60+ analytical SQL queries | ~700 lines |
| `README.md` | This file | - |

---

## 🚀 Quick Start

### 1. Install PostgreSQL + pgAdmin 4

**Windows:**
- Download: https://www.postgresql.org/download/windows/
- Install PostgreSQL 16.x (includes pgAdmin 4)
- Set `postgres` user password (remember it!)
- Port: 5432 (default)

**Verify:**
```powershell
Get-Service -Name postgresql*
# Should show: Status = Running
```

### 2. Create Database

**In pgAdmin 4:**
1. Connect to localhost server
2. Right-click "Databases" → Create → Database
3. Name: `billy_walters_analytics`
4. Owner: `postgres`
5. Save

**Or via SQL:**
```sql
CREATE DATABASE billy_walters_analytics
WITH OWNER = postgres ENCODING = 'UTF8';
```

### 3. Run Schema

**In pgAdmin 4 Query Tool:**
1. Select `billy_walters_analytics` database
2. Tools → Query Tool (Alt+Shift+Q)
3. File → Open → `schema.sql`
4. Execute (F5)
5. Verify: Should see 9 tables + 2 views

**Expected tables:**
- games
- power_ratings
- odds
- bets
- weather
- injuries
- situational_factors
- performance_metrics
- teams

### 4. Configure Python

**Add to `.env` file:**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=billy_walters_analytics
DB_USER=postgres
DB_PASSWORD=your_password_here
```

**Install driver:**
```powershell
uv add psycopg2-binary
```

### 5. Test Connection

```powershell
uv run python scripts/database/test_connection.py
```

**Expected output:**
```
[OK] Connected to PostgreSQL
[OK] Found 9 tables
[OK] Found 2 views
✅ DATABASE SETUP COMPLETE!
```

### 6. Migrate Week 12 Data

```powershell
uv run python scripts/database/migrate_week_12.py
```

---

## 📊 Database Schema Overview

### Core Tables

**games** - Game schedule and results
- Primary key: `game_id` (e.g., "BUF_KC_2025_W12")
- Stores: Teams, scores, date, venue
- Links to: All other tables via `game_id`

**power_ratings** - Weekly team ratings
- Composite ratings from Massey, ESPN
- Updates: Weekly (Tuesday)
- Used for: Edge detection

**odds** - Line movements
- Opening, current, closing lines
- Multiple sportsbooks
- Used for: CLV tracking

**bets** - Our betting plays
- Bet details, sizing, results
- Edge analysis, CLV calculation
- Used for: Performance tracking

**weather** - Game conditions
- Temperature, wind, precipitation
- Billy Walters adjustments
- Used for: Total/spread correlation

**injuries** - Player status
- Position-specific impact values
- Billy Walters methodology
- Used for: Edge detection

**situational_factors** - SWEF analysis
- Rest, travel, emotion, fundamentals
- Used for: Advanced edge detection

**performance_metrics** - Weekly/seasonal stats
- Win rate, ROI, CLV averages
- Aggregated by week/season
- Used for: Dashboard, reporting

### Views

**vw_game_analysis** - Complete game data
- Combines all tables
- One row per game
- Use for: Comprehensive analysis

**vw_weekly_summary** - Performance summary
- Aggregates betting results by week
- Use for: Quick weekly review

---

## 🔍 Common Queries

### Check Data

```sql
-- Verify Week 12 data loaded
SELECT COUNT(*) FROM games WHERE week = 12;  -- Should be 8+

-- View all games with edges
SELECT * FROM vw_game_analysis WHERE week = 12;

-- Weekly summary
SELECT * FROM vw_weekly_summary WHERE week = 12;
```

### CLV Analysis

```sql
-- Average CLV by week
SELECT
    week,
    ROUND(AVG(clv), 2) as avg_clv,
    COUNT(*) as bets
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE clv IS NOT NULL
GROUP BY week
ORDER BY week DESC;
```

### Weather Impact

```sql
-- Wind impact on UNDER bets
SELECT
    CASE
        WHEN wind_speed > 20 THEN 'High Wind'
        WHEN wind_speed > 15 THEN 'Medium Wind'
        ELSE 'Low Wind'
    END as wind_category,
    COUNT(*) as bets,
    ROUND(AVG(roi), 2) as avg_roi
FROM bets b
JOIN weather w ON b.game_id = w.game_id
WHERE b.bet_type = 'total' AND b.side = 'UNDER'
GROUP BY wind_category;
```

**More queries:** See `sample_queries.sql` (60+ examples)

---

## 🔗 Python Usage

### Connect to Database

```python
from src.db import get_db_connection

db = get_db_connection()
```

### Execute Queries

```python
# Get all Week 12 games
games = db.execute_query("""
    SELECT * FROM games WHERE week = 12
""")

for game in games:
    print(f"{game['away_team']} @ {game['home_team']}")
```

### Insert Data

```python
from src.db import DatabaseOperations
from src.db.models import Bet

ops = DatabaseOperations(db)

bet = Bet(
    bet_id="2025_W12_GB_SPREAD",
    game_id="MIN_GB_2025_W12",
    bet_type="spread",
    side="Green Bay",
    line=-6.5,
    edge_points=9.1,
    edge_category="STRONG",
    units=25.0,
    result="PENDING"
)

ops.insert_bet(bet)
```

### Use Context Manager

```python
with db.get_cursor(commit=True) as cursor:
    cursor.execute("""
        UPDATE bets
        SET result = 'WIN', profit_loss = 90.91, roi = 9.09
        WHERE bet_id = %s
    """, ("2025_W12_GB_SPREAD",))
```

---

## 📚 Documentation

**Complete Setup Guide:**
`docs/technical/database/DATABASE_SETUP_GUIDE.md` - Step-by-step instructions with screenshots

**Python API:**
- `src/db/connection.py` - Database connection manager
- `src/db/models.py` - Pydantic data models
- `src/db/operations.py` - CRUD operations

**SQL Reference:**
- `database/schema.sql` - Table definitions
- `database/sample_queries.sql` - Analytical queries

---

## 🎯 Billy Walters Workflow Integration

### Weekly Workflow

**Tuesday (Power Ratings):**
```python
from src.db import DatabaseOperations, get_db_connection
from src.db.models import PowerRating

db = get_db_connection()
ops = DatabaseOperations(db)

# Load from Massey/ESPN
for team, rating in power_ratings.items():
    ops.insert_power_rating(PowerRating(
        season=2025, week=13, league='NFL',
        team=team, rating=rating, source='composite'
    ))
```

**Wednesday (Odds Collection):**
```python
from src.db.models import Odds

# After scraping Overtime.ag
for game in games:
    ops.insert_odds(Odds(
        game_id=game['id'],
        sportsbook='overtime',
        odds_type='current',
        home_spread=game['spread'],
        total=game['total'],
        timestamp=datetime.now(timezone.utc)
    ))
```

**Sunday (Results Update):**
```python
# After games finish
for bet_id, result, profit in results:
    ops.update_bet_result(
        bet_id=bet_id,
        result=result,  # 'WIN', 'LOSS', 'PUSH'
        profit_loss=profit,
        closing_line=closing_line  # For CLV calculation
    )
```

### Analytics

**CLV Dashboard:**
```sql
SELECT
    week,
    AVG(clv) as avg_clv,
    COUNT(*) as bets,
    SUM(CASE WHEN clv > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as positive_clv_pct
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE season = 2025
GROUP BY week
ORDER BY week DESC;
```

**Weather Correlation:**
```sql
SELECT
    w.weather_category,
    COUNT(*) as games,
    AVG(b.roi) as avg_roi
FROM bets b
JOIN weather w ON b.game_id = w.game_id
WHERE b.bet_type = 'total'
GROUP BY w.weather_category;
```

---

## ⚠️ Troubleshooting

### Connection Failed

**Error:** `FATAL: password authentication failed`

**Fix:**
1. Check `.env` file has correct password
2. Verify postgres service running: `Get-Service postgresql*`
3. Test in pgAdmin 4 first

### Tables Not Found

**Error:** `relation "games" does not exist`

**Fix:**
1. Verify you selected `billy_walters_analytics` database (not `postgres`)
2. Re-run `schema.sql`
3. Check pgAdmin 4 → billy_walters_analytics → Schemas → public → Tables

### Python Import Error

**Error:** `ModuleNotFoundError: No module named 'psycopg2'`

**Fix:**
```powershell
uv add psycopg2-binary
uv sync
```

---

## 🔐 Security

**Never commit:**
- `.env` file (contains DB_PASSWORD)
- Database dumps with personal data
- Connection strings with credentials

**Best practices:**
- Use `.env` for all credentials
- Verify `.env` in `.gitignore`
- Use strong postgres password
- Limit database access to localhost (unless remote access needed)

---

## 📈 Next Steps

1. ✅ Complete setup (follow `docs/technical/database/DATABASE_SETUP_GUIDE.md`)
2. ✅ Run test connection
3. ✅ Migrate Week 12 data
4. ✅ Run sample queries
5. ⏳ Integrate with edge detector
6. ⏳ Build CLV tracking dashboard
7. ⏳ Create weekly automation

---

**Need Help?**
- Setup guide: `docs/technical/database/DATABASE_SETUP_GUIDE.md`
- Lessons learned: `LESSONS_LEARNED.md`
- PostgreSQL docs: https://www.postgresql.org/docs/
- pgAdmin docs: https://www.pgadmin.org/docs/

**Generated:** 2025-11-23
**Version:** 1.0.0
