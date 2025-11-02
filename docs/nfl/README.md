# NFL Power Ratings System

Complete implementation of Billy Walters' NFL power ratings methodology using exponential weighted formulas and ESPN API integration.

## Table of Contents
- [Overview](#overview)
- [System Components](#system-components)
- [Data Files](#data-files)
- [Workflows](#workflows)
- [CLI Commands](#cli-commands)
- [Automation](#automation)
- [Integration](#integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

The NFL Power Ratings System implements Billy Walters' proven methodology for evaluating team strength throughout the season. The system:

- Scrapes game data from ESPN API
- Applies exponential weighted formula (90/10 split)
- Accounts for home field advantage (2.5 points NFL)
- Tracks rating history for trend analysis
- Integrates with S/W/E factors for complete analysis
- Fully automated via Windows Task Scheduler

### Billy Walters Formula

**New Rating** = (Old Rating × 0.9) + (True Game Performance × 0.1)

**True Performance** = Score Differential + Opponent Rating + Injury Differential - Home Field Adjustment

---

## System Components

### Core Modules

#### `walters_analyzer/nfl_data.py`
Team standardization and data conversion utilities.

**Key Functions**:
```python
normalize_team_name(espn_abbr: str) -> str
    # Convert ESPN abbreviation to full team name
    # Example: "KC" → "Kansas City Chiefs"

are_divisional_opponents(team1: str, team2: str) -> bool
    # Check if two teams are in the same division
    # Used for S/W/E factor adjustments

nfl_game_to_game_results(game: NFLGame) -> tuple[GameResult, GameResult]
    # Convert NFLGame to two GameResult objects
    # One for home team, one for away team
```

**Data Structures**:
- `NFL_TEAMS` - 32 team mappings (abbreviation → full name)
- `NFL_DIVISIONS` - Division assignments for all teams
- `NFL_DOME_STADIUMS` - List of indoor stadiums (weather irrelevant)

#### `walters_analyzer/power_ratings.py`
Core rating engine implementing Billy Walters' formula.

**PowerRatingEngine Class**:
```python
class PowerRatingEngine:
    def update_rating(self, game_result: GameResult) -> TeamRating:
        # Apply exponential weighted formula
        # new_rating = (old × 0.9) + (performance × 0.1)

    def get_rating(self, team: str, sport: str = "nfl") -> TeamRating:
        # Retrieve current rating for a team

    def get_all_ratings(self, sport: str = "nfl") -> List[TeamRating]:
        # Get all team ratings, sorted by rating
```

### Scraping Scripts

#### `scripts/collect_nfl_schedule.py`
ESPN API scraper for NFL game data.

**ESPNNFLScraper Class**:
- Async HTTP requests with `aiohttp` for speed
- Single week or range scraping
- Dual output format (JSON + JSONL)
- Automatic team name normalization
- Completed games filtering

**Usage**:
```bash
# Single week
python scripts/collect_nfl_schedule.py --week 9 --season 2025

# Multiple weeks (backfill)
python scripts/collect_nfl_schedule.py --start-week 1 --end-week 9 --season 2025
```

#### `scripts/update_power_ratings_from_games.py`
Processes scraped game data into power ratings.

**PowerRatingsUpdater Class**:
- Loads JSONL game files
- Processes games sequentially (order matters!)
- Updates ratings for both teams
- Shows top N teams
- Saves to JSON

**Usage**:
```bash
# Single file
python scripts/update_power_ratings_from_games.py --file data/nfl_schedule/week9.jsonl

# Directory with specific weeks
python scripts/update_power_ratings_from_games.py --dir data/nfl_schedule --weeks 1 2 3 4 5
```

### Automation Scripts

#### Windows Batch Files

**`scripts/weekly_power_ratings_update_auto.bat`**:
- Auto-detects current NFL week based on date
- Task Scheduler compatible
- Logs to `scripts/update_log.txt`
- Exit codes: 0 (success), 1 (failure)

**`scripts/weekly_power_ratings_update.bat`**:
- Manual week number entry
- Useful for testing
- Same error logging

See [Automation](#automation) section for Task Scheduler setup.

---

## Data Files

### Team Mappings
**Location**: `data/team_mappings/nfl_teams.json`

**Structure**:
```json
{
  "teams": {
    "KC": {
      "full_name": "Kansas City Chiefs",
      "location": "Kansas City",
      "nickname": "Chiefs",
      "division": "AFC West",
      "conference": "AFC"
    },
    ...
  },
  "divisions": {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    ...
  },
  "dome_stadiums": [
    "Allegiant Stadium",
    "AT&T Stadium",
    ...
  ]
}
```

**Purpose**:
- Standardize team names from ESPN API
- Division rivalry detection
- Weather impact assessment (dome vs outdoor)

### Power Ratings
**Location**: `data/power_ratings/team_ratings.json`

**Structure**:
```json
{
  "ratings": {
    "nfl:kansas city chiefs": {
      "team": "Kansas City Chiefs",
      "sport": "nfl",
      "rating": 11.36,
      "games_played": 18,
      "rating_history": [0.0, 2.5, 5.1, 7.8, 9.2, 10.5, 11.36],
      "last_updated": "2025-11-01T21:22:50"
    },
    ...
  }
}
```

**Features**:
- `rating` - Current power rating
- `games_played` - Sample size indicator
- `rating_history` - Week-by-week progression
- `last_updated` - Timestamp for freshness check

### Game Data
**Location**: `data/nfl_schedule/`

**Dual Format Per Week**:
1. **JSON** (`nfl_week9_2025_20251101_185606.json`) - Pretty-printed, human-readable
2. **JSONL** (`nfl_week9_2025_20251101_185606.jsonl`) - Line-delimited, streaming-friendly

**JSONL Entry Structure**:
```json
{
  "game_id": "401671754",
  "season": 2025,
  "week": 9,
  "home_team": "Miami Dolphins",
  "away_team": "Baltimore Ravens",
  "home_score": 10,
  "away_score": 31,
  "is_completed": true,
  "status": "Final",
  "is_dome": false,
  "spread": {
    "favorite": "BAL",
    "line": -9.5
  },
  "timestamp": "2025-11-01T21:22:48Z"
}
```

**Why JSONL**:
- Streaming processing (one game at a time)
- Easy to append new games
- Smaller memory footprint for large datasets

---

## Workflows

### Initial Setup (One-Time)

**1. Backfill Historical Data**

Scrape all games from Week 1 to current week:

```bash
uv run walters-analyzer backfill-nfl-season --season 2025 --end-week 9
```

This command:
- Scrapes Weeks 1-9 from ESPN API
- Processes games sequentially (order matters!)
- Builds initial power ratings
- Saves to `data/power_ratings/team_ratings.json`

**Expected Output**:
```
NFL Season Backfill: 2025
Weeks 1 through 9
============================================================

STEP 1: Scraping game data from ESPN API...
Week 1: 16 games found
Week 2: 16 games found
...

STEP 2: Updating power ratings...
Processing 135 games...
  [OK] Baltimore Ravens 31 @ Miami Dolphins 10
    Miami Dolphins: -8.35
    Baltimore Ravens: 10.85
...

============================================================
[SUCCESS] Backfill Complete!
============================================================

Top 10 NFL Power Ratings
============================================================
Rank   Team                           Rating     Games
------------------------------------------------------------
1      Kansas City Chiefs             11.36      18
2      Indianapolis Colts             11.80      18
3      Los Angeles Rams                8.14      16
...
```

### Weekly Update (Automated)

**Tuesday Morning Automation**:

Task Scheduler automatically runs:
```batch
scripts\weekly_power_ratings_update_auto.bat
```

**What it does**:
1. Auto-detects current week based on date
2. Scrapes latest games from ESPN API
3. Updates power ratings
4. Logs success/failure to `scripts\update_log.txt`

**Manual Weekly Update**:

```bash
# After Week 10 games complete (Monday night)
uv run walters-analyzer weekly-nfl-update --week 10
```

**Output**:
```
Weekly NFL Update: Week 10, 2025
============================================================

STEP 1: Scraping game data from ESPN API...
Found 14 games for Week 10

STEP 2: Updating power ratings...
Processing 14 games...
  [OK] Los Angeles Chargers 27 @ Tennessee Titans 17
  [OK] Minnesota Vikings 21 @ Jacksonville Jaguars 14
...

Top 10 NFL Power Ratings
============================================================
1      Kansas City Chiefs             11.56
2      Indianapolis Colts             11.92
...

[SUCCESS] Weekly Update Complete!
```

### Manual Workflow (Step-by-Step)

**For greater control, run steps separately**:

**Step 1 - Scrape Games**:
```bash
uv run walters-analyzer scrape-nfl-schedule --week 10 --season 2025
```

**Step 2 - Update Ratings**:
```bash
uv run walters-analyzer update-power-ratings --dir data/nfl_schedule --weeks 10
```

**Step 3 - View Results**:
```bash
uv run walters-analyzer update-power-ratings --dir data/nfl_schedule --weeks 10 --show-top 15
```

---

## CLI Commands

### `backfill-nfl-season`

Backfill historical data for entire season.

```bash
uv run walters-analyzer backfill-nfl-season --season 2025 --end-week 9
```

**Options**:
- `--season` - Season year (default: 2025)
- `--start-week` - First week to collect (default: 1)
- `--end-week` - Last week to collect (required)
- `--skip-scrape` - Skip scraping, only update ratings from existing data
- `--output-dir` - Data directory (default: data/nfl_schedule)

### `weekly-nfl-update`

Single week workflow: scrape + update ratings.

```bash
uv run walters-analyzer weekly-nfl-update --week 10 --season 2025
```

**Options**:
- `--week` - Week number to process (required)
- `--season` - Season year (default: 2025)
- `--show-top` - Show top N teams (default: 10)

### `scrape-nfl-schedule`

Scrape NFL schedule/scores from ESPN API.

```bash
uv run walters-analyzer scrape-nfl-schedule --week 10 --season 2025
```

**Options**:
- `--season` - NFL season year (default: 2025)
- `--week` - Single week to scrape (1-18)
- `--start-week` - Start week for backfill (default: 1)
- `--end-week` - End week for backfill (default: 18)
- `--output-dir` - Output directory (default: data/nfl_schedule)

### `update-power-ratings`

Update Billy Walters power ratings from game data.

```bash
uv run walters-analyzer update-power-ratings --dir data/nfl_schedule --weeks 1 2 3 4 5
```

**Options**:
- `--file` - Single JSONL file to process
- `--dir` - Directory containing JSONL files
- `--weeks` - Specific weeks to process (e.g., --weeks 1 2 3)
- `--ratings-file` - Power ratings file path (default: data/power_ratings/team_ratings.json)
- `--show-top` - Show top N teams after update (default: 10)
- `--quiet` - Minimal output

---

## Automation

### Windows Task Scheduler Setup

**Complete Guide**: See `scripts/TASK_SCHEDULER_SETUP.md`

**Quick PowerShell Setup**:

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction `
    -Execute "C:\Users\YOUR_USER\Documents\python_projects\billy-walters-sports-analyzer\scripts\weekly_power_ratings_update_auto.bat" `
    -WorkingDirectory "C:\Users\YOUR_USER\Documents\python_projects\billy-walters-sports-analyzer"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At 6:00AM
$trigger.EndBoundary = "2026-02-15T06:00:00"  # End after Super Bowl

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 15)

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "Billy Walters NFL Weekly Update" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Automatically updates NFL power ratings every Tuesday at 6 AM"
```

**Verify Task**:
```cmd
schtasks /query /tn "Billy Walters NFL Weekly Update" /fo list /v
```

**Check Logs**:
```cmd
type scripts\update_log.txt
```

### Linux/Mac (Cron) Setup

**Edit crontab**:
```bash
crontab -e
```

**Add entry** (runs every Tuesday at 6 AM):
```bash
0 6 * * 2 cd /path/to/billy-walters-sports-analyzer && ./scripts/weekly_power_ratings_update.sh
```

---

## Integration

### S/W/E Factors

Power ratings provide the **base prediction**. Enhance with situational factors:

**Example Workflow**:
```python
from walters_analyzer.power_ratings import PowerRatingEngine
from walters_analyzer.situational_factors import SituationalFactors

# Get base prediction from power ratings
engine = PowerRatingEngine()
chiefs_rating = engine.get_rating("Kansas City Chiefs")  # 11.36
dolphins_rating = engine.get_rating("Miami Dolphins")    # -8.35

# Base prediction: Chiefs favored by (11.36 - (-8.35)) + 2.5 (HFA) = 22.21 points

# Add S/W/E adjustments
swe = SituationalFactors()
weather_adj = swe.calculate_weather("Miami", dome=False)  # -2.0 (rain)
rest_adj = swe.calculate_rest(chiefs_rest_days=7, dolphins_rest_days=4)  # +1.5
emotional_adj = swe.calculate_emotional("rivalry")  # +0.5

# Final prediction: 22.21 - 2.0 + 1.5 + 0.5 = 22.21 points
# Market spread: Chiefs -18.5
# Edge: 22.21 - 18.5 = 3.71 points (potential bet opportunity)
```

### Key Numbers

Check if prediction crosses NFL key numbers:

```python
from walters_analyzer.key_numbers import NFLKeyNumbers

kn = NFLKeyNumbers()
prediction = 22.21
market = 18.5

# Check key numbers between prediction and market
crossed = kn.get_crossed_numbers(market, prediction)
# Returns: [21, 20] - valuable key numbers crossed

# Calculate edge bonus
edge_with_key = kn.calculate_key_number_value(abs(prediction - market), crossed)
# Adds bonus for crossing 21 and 20
```

### Bet Sizing

Use star system based on edge percentage:

```python
from walters_analyzer.bet_sizing import calculate_stars

edge_percent = ((22.21 - 18.5) / 18.5) * 100  # 20.05%

stars = calculate_stars(edge_percent)
# Returns: 3.0 stars (maximum) for 20%+ edge

# Bet size based on bankroll
bankroll = 100000
unit_size = 1000  # 1% of bankroll
bet_amount = stars * unit_size  # $3,000
```

---

## Troubleshooting

### Common Issues

**Issue**: "No games found for week N"
- **Cause**: Week hasn't started or ESPN API timing
- **Solution**: Wait until games are completed (check ESPN.com)
- **Workaround**: Manually check `--week` parameter

**Issue**: "Team not found in mappings"
- **Cause**: New team or ESPN changed abbreviation
- **Solution**: Update `data/team_mappings/nfl_teams.json`
- **Example**: Add new entry for team

**Issue**: "Unicode encoding error on Windows"
- **Cause**: Console doesn't support Unicode characters
- **Solution**: Already fixed - all output uses ASCII ([OK], [SUCCESS], [ERROR])

**Issue**: "Ratings not updating"
- **Cause**: Games not marked as completed in ESPN API
- **Solution**: Run update after all games final (Monday/Tuesday)
- **Check**: Visit ESPN.com to verify game status

**Issue**: "Task Scheduler not running"
- **Cause**: Computer off or user not logged in
- **Solution**: Configure "Run whether user is logged on or not"
- **Alternative**: Use "Run only when user is logged in" (requires login)

**Issue**: "Duplicate schedule files"
- **Cause**: Multiple backfill runs
- **Solution**: Run cleanup command
```bash
# Use slash command
/cleanup-duplicates

# Or manually delete old files from data/nfl_schedule/
```

### Validation Checks

**Pre-Flight Validation**:
```bash
# Check all systems ready
uv run python -c "
import os, json
from pathlib import Path

# Check .env
env_ok = Path('.env').exists()
print(f'✓ .env file: {\"OK\" if env_ok else \"MISSING\"}')

# Check power ratings
ratings_ok = Path('data/power_ratings/team_ratings.json').exists()
print(f'✓ Power ratings: {\"OK\" if ratings_ok else \"MISSING\"}')

# Check team mappings
mappings_ok = Path('data/team_mappings/nfl_teams.json').exists()
print(f'✓ Team mappings: {\"OK\" if mappings_ok else \"MISSING\"}')
"
```

**Post-Update Validation**:
```bash
# Verify ratings file updated
python -c "
from pathlib import Path
from datetime import datetime

ratings_file = Path('data/power_ratings/team_ratings.json')
age = (datetime.now().timestamp() - ratings_file.stat().st_mtime)

if age < 300:  # Less than 5 minutes
    print(f'✓ Ratings updated {int(age)} seconds ago')
else:
    print(f'⚠ Ratings last updated {int(age/60)} minutes ago')
"
```

**Data Quality Check**:
```bash
# Check team count
python -c "
import json
ratings = json.load(open('data/power_ratings/team_ratings.json'))
count = len(ratings['ratings'])
print(f'Teams in ratings: {count}')
if count < 30:
    print('⚠ WARNING: Expected 30+ teams')
"
```

### Quick Reference

```bash
# View current top 10
uv run python -c "import json; r=json.load(open('data/power_ratings/team_ratings.json')); [print(f'{i}. {k.split(\":\" )[1]}: {v[\"rating\"]:.2f}') for i, (k, v) in enumerate(sorted(r['ratings'].items(), key=lambda x: x[1]['rating'], reverse=True)[:10], 1)]"

# Count scraped games
dir /B /S data\nfl_schedule\*.jsonl | find /C ".jsonl"

# View update log
type scripts\update_log.txt

# Check Task Scheduler
schtasks /query /tn "Billy Walters NFL Weekly Update" /fo list /v | findstr /C:"Last Run" /C:"Next Run" /C:"Status"
```

---

## Additional Resources

- **Main Documentation**: [../../CLAUDE.md](../../CLAUDE.md)
- **Billy Walters Methodology**: [../BILLY_WALTERS_METHODOLOGY.md](../BILLY_WALTERS_METHODOLOGY.md)
- **Task Scheduler Setup**: [../../scripts/TASK_SCHEDULER_SETUP.md](../../scripts/TASK_SCHEDULER_SETUP.md)
- **Power Ratings Module**: [../../walters_analyzer/power_ratings.py](../../walters_analyzer/power_ratings.py)
- **NFL Data Utilities**: [../../walters_analyzer/nfl_data.py](../../walters_analyzer/nfl_data.py)

---

**Last Updated**: 2025-11-01
**Season**: 2025 NFL Regular Season
**Automated**: Windows Task Scheduler (Tuesdays @ 6 AM)
