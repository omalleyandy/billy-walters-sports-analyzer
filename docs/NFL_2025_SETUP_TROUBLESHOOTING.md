# NFL 2025 Data Collection - Setup Troubleshooting

## Issue 1: ESPN API Returns HTTP 500

**What You're Seeing:**
```
HTTP Request: GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?week=1&seasontype=2&season=2025 "HTTP/1.1 500 Internal Server Error"
```

**Root Causes:**
1. ESPN API temporarily down (transient issue)
2. Rate limiting (ESPN blocks fast repeated requests)
3. Invalid parameters for 2025 season (API might not have 2025 data yet)
4. Network/firewall issues

**Solutions (Try in Order):**

### Solution A: Wait and Retry (Most Common)
ESPN's site API sometimes has intermittent issues. The 500 errors appear to be transient:

```bash
# Wait 30 seconds and try again
Start-Sleep -Seconds 30
uv run python scripts/database/collect_2025_nfl_season.py
```

### Solution B: Reduce Rate (Add Delay Between Requests)
Edit `scripts/database/collect_2025_nfl_season.py` line ~150, change:
```python
# OLD: No delay
# NEW: Add 1 second delay between requests
await asyncio.sleep(1.0)  # Add this before each API call
```

### Solution C: Check 2025 Season is Valid
Test if ESPN has 2025 data available:

```bash
# Test endpoint directly
$response = Invoke-RestMethod -Uri "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?week=1&seasontype=2&season=2025" -Method Get
$response.events.Count  # Should show number of games
```

If ESPN doesn't have 2025 data yet, you may need to use 2024 season data instead.

### Solution D: Use Alternative NFL API
If ESPN continues to fail, consider using:
- **Pro Football Reference API** (more reliable)
- **NFL.com official stats** (requires authentication)
- **Fallback to 2024 season data** (known working)

---

## Issue 2: PostgreSQL Password Authentication Failed

**What You're Seeing:**
```
FATAL: password authentication failed for user "postgres"
```

**Root Cause:**
The loader script uses hardcoded password `"postgres"` (line 30), but your PostgreSQL uses a different password.

**Solutions:**

### Solution A: Pass Password as Command-Line Argument (Recommended)
```bash
uv run python scripts/database/load_2025_nfl_season.py --password "YOUR_ACTUAL_PASSWORD"

# Example
uv run python scripts/database/load_2025_nfl_season.py --password "Omarley@2025"
```

### Solution B: Use Environment Variable
```bash
# Set environment variable
$env:DB_PASSWORD = "Omarley@2025"

# Run script (it will read from env)
uv run python scripts/database/load_2025_nfl_season.py
```

### Solution C: Edit Script Defaults
Edit `scripts/database/load_2025_nfl_season.py` line 30:
```python
# OLD
password: str = "postgres",

# NEW
password: str = "Omarley@2025",
```

### Solution D: Check PostgreSQL Connection
```bash
# Test PostgreSQL connection directly
psql -U postgres -d sports_db -c "SELECT version();"

# If password prompt appears, type your password
```

---

## Issue 3: PowerShell Line Continuation Syntax

**What You're Seeing:**
```
error: unrecognized arguments: \
'#' is not recognized as an internal or external command
```

**Root Cause:**
PowerShell uses different syntax for comments and line continuation than bash.

**Solutions:**

### Solution A: Use Backtick for Line Continuation (PowerShell)
```powershell
# CORRECT - Use backtick (`) for line continuation
uv run python scripts/database/load_2025_nfl_season.py `
  --password "Omarley@2025" `
  --data-dir "data/historical"

# CORRECT - No comments with arguments
# Use comments on separate lines:
# Step 1: Apply database schema
psql -U postgres -d sports_db -f database/nfl_extensions.sql

# Step 2: Collect NFL data
uv run python scripts/database/collect_2025_nfl_season.py
```

### Solution B: Use bash for Complex Scripts
```bash
# Switch to bash (if available)
bash

# Now you can use backslash and #
uv run python scripts/database/load_2025_nfl_season.py \
  --password "Omarley@2025" \
  --data-dir "data/historical"
```

---

## Complete Working Workflow

**For Windows PowerShell:**

```powershell
# 1. Start fresh
$ErrorActionPreference = "Continue"

# 2. Verify PostgreSQL is running
psql -U postgres -d sports_db -c "SELECT 1;"

# 3. Apply database schema
Write-Host "Step 1: Creating database tables..."
psql -U postgres -d sports_db -f database/nfl_extensions.sql

# 4. Collect 2025 NFL data (may show 500 errors - retry if needed)
Write-Host "Step 2: Collecting NFL 2025 data..."
uv run python scripts/database/collect_2025_nfl_season.py

# 5. Load data to PostgreSQL
Write-Host "Step 3: Loading data to PostgreSQL..."
uv run python scripts/database/load_2025_nfl_season.py `
  --password "Omarley@2025" `
  --dbname "sports_db"

# 6. Verify data loaded
Write-Host "Step 4: Verifying data..."
psql -U postgres -d sports_db -c "SELECT COUNT(*) FROM games WHERE league='NFL';"
```

---

## Recommended Actions (in order)

1. **Wait 30 seconds** → Retry ESPN API (most 500 errors are transient)
2. **If still failing** → Check ESPN has 2025 season data
3. **If ESPN unavailable** → Use 2024 season data instead
4. **For database** → Always pass `--password` argument
5. **For PowerShell** → Use backtick (`) not backslash (\)

---

## Files That Need Attention

- `scripts/database/collect_2025_nfl_season.py` - ESPN API timeout/retry logic
- `scripts/database/load_2025_nfl_season.py` - Password handling
- `database/nfl_extensions.sql` - Table schema (should be fine)

---

## Next Steps

Once data collection succeeds:

1. Load data to PostgreSQL: `uv run python scripts/database/load_2025_nfl_season.py`
2. Verify in database: `psql -U postgres -d sports_db -c "SELECT COUNT(*) FROM games;"`
3. Use for power ratings: The data will be ready for Billy Walters analysis
