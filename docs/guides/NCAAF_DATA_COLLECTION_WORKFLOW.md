# NCAAF Data Collection Workflow

**League:** National Collegiate Athletic Association Football (NCAAF)
**Season:** 2025
**Last Updated:** 2025-11-25
**Status:** Production Ready

## Overview

Complete workflow for NCAAF (College Football) data collection with **strictly separated output structure**. This guide ensures NCAAF data is never intermixed with NFL data.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Complete Workflow](#complete-workflow)
3. [Output Structure](#output-structure)
4. [Data Verification](#data-verification)
5. [Troubleshooting](#troubleshooting)
6. [Performance Reference](#performance-reference)

---

## Quick Start

### One-Command Collection

**Collect all NCAAF data for the week:**

```bash
# Wednesday/Thursday - before games
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# OR collect everything (recommended for weekly prep)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```

**During games (Saturday):**

```bash
# Get pregame odds first
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Then monitor for 4 hours (typical Saturday slate)
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 14400
```

---

## Complete Workflow

### Phase 1: Scheduled Collection (Wednesday 2:00 PM)

**Time Required:** ~5-7 minutes

This phase collects all baseline data before any games start.

#### Step 1: Overtime Pregame Odds (⚡ ~5 seconds)

```bash
echo "[1/5] Collecting Overtime pregame odds..."
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
```

**What it does:**
- Fetches all pregame odds from Overtime.ag for NCAAF
- Covers all FBS (FD I) games for the week
- Includes moneylines, spreads, totals, props
- Stores in: `output/overtime/ncaaf/pregame/`

**Output:**
```
output/overtime/ncaaf/pregame/
├── 2025-09-06_pregame.json      # All games + odds
├── 2025-09-13_pregame.json
└── 2025-09-20_pregame.json
```

**Coverage:**
- ~15-20 games per Saturday
- Multiple betting tiers (sharp action, public money)
- Props and alternative lines
- ~100-200 KB per week

#### Step 2: ESPN Team Statistics (📊 ~2 minutes)

```bash
echo "[2/5] Collecting ESPN team statistics..."
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf
```

**What it does:**
- Fetches offensive/defensive stats for all FBS teams
- Includes PPG, YPG, efficiency metrics
- Tracks wins, losses, and records
- Updates weekly as season progresses

**Output:**
```
output/espn/ncaaf/
├── team_stats_2025_week1.parquet
├── team_stats_2025_week1.json
├── teams_reference.json          # Team IDs, names, conferences
├── injuries_2025_week1.json      # Key player injuries
└── schedules_2025.json           # Full season schedule
```

**Data Points:**
- ~130 FBS teams
- 20+ offensive/defensive metrics per team
- Conference standings
- Home/away splits
- ~50-100 KB per week

#### Step 3: Massey Power Ratings (📊 ~1 minute)

```bash
echo "[3/5] Collecting Massey ratings..."
uv run python scripts/scrapers/scrape_massey_games.py --league college
```

**What it does:**
- Fetches college power ratings from Massey Ratings
- Industry standard for NCAAF rankings
- Used for power rating calculations and comparisons
- Includes both FBS and lower divisions (filtered to FBS only)

**Output:**
```
output/massey/
├── ncaaf_ratings_2025_week1.json
├── college_rankings_2025_week1.parquet
└── massey_comparison_2025_week1.json
```

**Coverage:**
- All FBS teams ranked
- SOS (Strength of Schedule)
- Efficiency ratings
- ~20-40 KB per week

#### Step 4: Weather for All College Stadiums (🌤️ ~2 seconds)

```bash
echo "[4/5] Collecting weather data..."
python src/data/weather_client.py --league ncaaf --fbs-only
```

**What it does:**
- Gets current and forecasted weather for all FBS stadiums
- Includes temperature, wind, precipitation, humidity
- Game-time forecasts for all scheduled games
- Regional weather patterns for travel impacts

**Output:**
```
output/weather/ncaaf/
├── game_forecasts_2025_week1.json
├── stadium_conditions_2025_week1.parquet
├── stadiums_reference.json       # Stadium locations, climate zones
└── regional_weather_2025_week1.json
```

**Coverage:**
- 130+ FBS stadiums
- Elevation and climate zone data
- Historical weather patterns
- ~20-50 KB per week

#### Step 5: Action Network Betting Lines (📱 ~3 minutes)

```bash
echo "[5/5] Collecting Action Network lines..."
uv run python scripts/scrapers/scrape_action_network_sitemap.py --ncaaf
```

**What it does:**
- Discovers all NCAAF games via sitemap
- Scrapes public betting lines from major sportsbooks
- Ensures complete coverage of all games
- Captures line movements and steam indicators

**Output:**
```
output/action_network/ncaaf/
├── all_odds_2025_week1.json
├── game_lines_2025_week1.parquet
├── sportsbooks_reference.json    # Sportsbooks covered
└── steam_tracking_2025_week1.json
```

**Coverage:**
- All FBS matchups
- Multiple sportsbooks (DraftKings, FanDuel, BetMGM, etc.)
- Spread, moneyline, total
- Props and alt lines
- ~30-100 KB per week

### Phase 2: Edge Detection (After Phase 1)

```bash
echo "[COMPLETE] Running edge detection..."
/edge-detector --league ncaaf
```

This uses all collected NCAAF data to find value opportunities specific to college football.

### Phase 3: Game Day Collection (Saturday, before kickoff)

**Time Required:** ~5 seconds

```bash
# Get updated pregame odds
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Check injury updates
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf
```

### Phase 4: Live Monitoring (During Games)

**Time Required:** 4+ hours (configurable, longer than NFL due to staggered starts)

```bash
# Monitor for 4 hours (14400 seconds) - typical Saturday slate
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 14400

# Extended monitoring (some games go to evening)
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 21600  # 6 hours

# Full day monitoring (games 10am to 10pm)
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 43200  # 12 hours
```

**What it does:**
- Establishes live connection to Overtime.ag for college games
- Streams real-time odds updates as games progress
- Captures line movement from sharp bettors
- Monitors injury updates and game conditions
- Excellent for tracking steam moves across all time slots

**Output:**
```
output/overtime/ncaaf/live/
├── 2025-09-06_1000_stream.json    # 10:00 AM snapshot
├── 2025-09-06_1010_stream.json    # 10:10 AM snapshot
├── 2025-09-06_1020_stream.json    # 10:20 AM snapshot
├── 2025-09-06_1300_stream.json    # 1:00 PM snapshot
├── 2025-09-06_1630_stream.json    # 4:30 PM snapshot
└── ...
```

**Note:** College football has staggered start times (morning, afternoon, evening, night games), so monitoring windows are longer than NFL.

---

## Output Structure

### Directory Organization

All NCAAF data is **strictly organized under a single root:**

```
output/overtime/ncaaf/
├── pregame/                        # Pregame odds (Wednesday)
│   ├── 2025-09-06_pregame.json
│   ├── 2025-09-13_pregame.json
│   └── 2025-09-20_pregame.json
├── live/                           # Live updates (Saturday+)
│   ├── 2025-09-06_1000_stream.json
│   ├── 2025-09-06_1010_stream.json
│   ├── 2025-09-06_1300_stream.json
│   └── 2025-09-06_2200_stream.json
└── archive/                        # Old files (auto-managed)
    └── 2024_season/

output/espn/ncaaf/
├── team_stats_2025_week1.parquet
├── team_stats_2025_week1.json
├── injuries_2025_week1.json
├── schedules_2025.json             # Full season schedule
├── standings_2025_week1.json        # Conference standings
└── teams_reference.json            # Team lookup (130+ FBS)

output/weather/ncaaf/
├── game_forecasts_2025_week1.json
├── stadium_conditions_2025_week1.parquet
├── regional_weather_2025_week1.json
└── stadiums_reference.json

output/action_network/ncaaf/
├── all_odds_2025_week1.json
├── game_lines_2025_week1.parquet
├── steam_tracking_2025_week1.json
└── sportsbooks_reference.json

output/analysis/ncaaf/
├── edge_detection_2025_week1.json  # Betting opportunities
├── power_ratings_2025_week1.json   # Custom ratings
├── clv_tracking_2025.parquet       # Performance tracking
├── conference_edges_2025_week1.json # By conference
└── recommendations_2025_week1.json # Picks
```

### File Naming Convention

**Format:** `{component}_{sport}_{period}_{datetime|detail}.{ext}`

**Examples:**
- `pregame.json` - Pregame odds snapshot
- `2025-09-06_stream.json` - Game-day stream snapshot
- `team_stats_2025_week1.parquet` - Weekly team statistics
- `stadium_conditions_2025_week1.parquet` - Weather conditions
- `all_odds_2025_week1.json` - Weekly odds summary
- `conference_edges_2025_week1.json` - Separated by conference

---

## Data Verification

### Verify Collection Success

**Check file existence and size:**

```bash
# List recent NCAAF output files
ls -lth output/overtime/ncaaf/pregame/*.json | head -3
ls -lth output/espn/ncaaf/*.parquet
ls -lth output/weather/ncaaf/*.json
ls -lth output/action_network/ncaaf/*.json

# Verify file sizes (should not be 0 bytes)
find output -name "*ncaaf*" -type f -size 0
```

**Check data quality:**

```bash
# Validate JSON structure
python -m json.tool output/overtime/ncaaf/pregame/*.json > /dev/null && echo "Valid JSON"

# Check parquet files and team count
python -c "
import pandas as pd
df = pd.read_parquet('output/espn/ncaaf/team_stats_2025_week1.parquet')
print(f'Teams: {len(df)} (expected ~130 FBS), Columns: {len(df.columns)}')"

# Verify conferences are represented
python -c "
import pandas as pd, json
with open('output/espn/ncaaf/teams_reference.json') as f:
    teams = json.load(f)
conferences = set(t.get('conference', 'Unknown') for t in teams)
print(f'Conferences: {len(conferences)}')
for conf in sorted(conferences)[:10]:
    print(f'  - {conf}')
"
```

### Expected Data Points

**Pregame Odds (Overtime API):**
- ✅ 14-15 weeks of regular season
- ✅ 2-4 bowl games per week late season
- ✅ 15-20 games per Saturday
- ✅ Moneyline, spread, total for each game
- ✅ Live betting props
- ✅ ~100-200 KB per week

**ESPN Team Stats:**
- ✅ ~130 FBS teams (major programs)
- ✅ 20+ offensive/defensive metrics per team
- ✅ Conference standings tracked
- ✅ Home/away splits
- ✅ ~50-100 KB per week

**Massey Ratings:**
- ✅ All FBS teams ranked
- ✅ SOS (Strength of Schedule)
- ✅ Efficiency ratings
- ✅ ~20-40 KB per week

**Weather:**
- ✅ All 130+ FBS stadium locations
- ✅ Game-time forecasts for all scheduled games
- ✅ Temperature, wind, precipitation, humidity
- ✅ Elevation and climate zone data
- ✅ ~20-50 KB per week

**Action Network:**
- ✅ All NCAAF games for the week
- ✅ Multiple sportsbook lines per game
- ✅ Props and alternative lines
- ✅ Steam tracking (early line vs current)
- ✅ ~30-100 KB per week

---

## Troubleshooting

### Common Issues

#### "No NCAAF games found"

**Cause:** Off-season (December-August) or incorrect league parameter

**Solution:**
```bash
# Verify NCAAF season dates
python -c "import datetime; week = (datetime.date.today().isocalendar()[1] - 36) % 17; print(f'Current week: {week} (1=Sept, 15=Dec)')"

# Check if data exists
ls -la output/overtime/ncaaf/pregame/ | tail -5

# Or try next week's date
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf --date 2025-09-13
```

#### "Only 5-10 games collected" (expected 15-20)

**Cause:** Week with bye weeks or between seasons

**Solution:**
```bash
# Check how many teams have games this week
python -c "
import json
with open('output/espn/ncaaf/schedules_2025.json') as f:
    schedule = json.load(f)
# Count games for this week
"

# This is normal - bye weeks reduce game count
# Continue with collection as-is
```

#### "Connection timeout" from Overtime.ag

**Cause:** Network issue or Overtime server down

**Solution:**
```bash
# Test connectivity
curl -s https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering -d "sport=2" | head -50

# Wait 30 seconds and retry
sleep 30
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
```

#### NCAAF data is intermixed with NFL

**Cause:** Script collected both with `--nfl --ncaaf` flag or used wrong script

**Solution:**
```bash
# Check what was collected
ls output/*/nfl/ output/*/ncaaf/ 2>/dev/null | sort

# Collect NCAAF only (strict)
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Keep league separation going forward
# NCAAF collection: always use --ncaaf only, not --nfl
```

#### Injuries not showing up

**Cause:** ESPN may not have injury data during off-season or data delay

**Solution:**
```bash
# Check if ESPN has injury data
python -c "
import json
with open('output/espn/ncaaf/injuries_2025_week1.json') as f:
    injuries = json.load(f)
print(f'Injuries recorded: {len(injuries)}')"

# If empty, this is normal for off-season
# If during season, wait for ESPN to update (usually 1-2 hours after games)
```

#### Weather API returning errors

**Cause:** Missing API key or invalid stadium location

**Solution:**
```bash
# Check environment
echo $ACCUWEATHER_API_KEY  # Should not be empty

# Test weather client with a known stadium
python -c "
import asyncio
from src.data import WeatherClient
async def test():
    async with WeatherClient() as client:
        weather = await client.get_forecast('tuscaloosa', 'al')
        print(weather)
asyncio.run(test())
"

# If issue persists, check stadiums_reference.json for correct location names
```

---

## Performance Reference

### Speed Benchmarks

| Component | Time | Data Size | Notes |
|-----------|------|-----------|-------|
| Overtime API | <5 sec | ~150 KB | All weeks at once |
| ESPN Stats | ~2 min | ~80 KB | 130+ teams |
| Weather | ~2 sec | ~30 KB | More stadiums than NFL |
| Action Network | ~3 min | ~100 KB | Via sitemap |
| Hybrid Scraper | 30+ sec init | ~10 MB/hour | Real-time stream |
| Edge Detection | ~15 sec | ~100 KB output | More games than NFL |

**Total Weekly Collection Time:** 6-8 minutes

### Parallel Execution

All components are independent except Edge Detection (which requires all inputs). You can run in parallel:

```bash
# Terminal 1: Odds
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf &

# Terminal 2: Stats
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf &

# Terminal 3: Weather
python src/data/weather_client.py --league ncaaf &

# Terminal 4: Action Network
uv run python scripts/scrapers/scrape_action_network_sitemap.py --ncaaf &

# Terminal 5: Massey
uv run python scripts/scrapers/scrape_massey_games.py --league college &

# Wait for all to complete
wait

# Then run edge detection
/edge-detector --league ncaaf
```

---

## Weekly Workflow Checklist

### Wednesday 2:00 PM (Scheduled Collection)

- [ ] Run `/collect-all-data` or manual phase 1 workflow
- [ ] Verify all 5 NCAAF data sources collected successfully
- [ ] Check file sizes (should be ~100KB+ per component)
- [ ] Run `/validate-data` to confirm quality
- [ ] Run `/edge-detector --league ncaaf` to find opportunities
- [ ] Generate `/betting-card --league ncaaf` with recommendations

### Saturday 10:00 AM (Before Kickoff)

- [ ] Quick odds refresh: `scrape_overtime_api.py --ncaaf`
- [ ] Check for line movement since Wednesday
- [ ] Review any new injury reports from ESPN
- [ ] Run `/edge-detector --league ncaaf` with updated data
- [ ] Check weather for outdoor stadiums

### Saturday 11:00 AM - 11:00 PM (Game Time)

- [ ] Start: `scrape_overtime_hybrid.py --ncaaf --duration 43200` (if full day)
- [ ] Or: `scrape_overtime_hybrid.py --ncaaf --duration 14400` (4 hours for afternoon slate)
- [ ] Monitor for steam moves and sharp action
- [ ] Track injury developments (key player impacts larger in college)
- [ ] Update any in-game adjustments

### Monday (Results & Analysis)

- [ ] Run `check_betting_results.py --league ncaaf`
- [ ] Calculate CLV and performance metrics
- [ ] Document edge accuracy by conference
- [ ] Review missed opportunities
- [ ] Analyze which conferences had best edges

---

## Data Extraction & Integration

### Load into Analysis

```python
import pandas as pd
import json
from pathlib import Path

# Load NCAAF odds
with open('output/overtime/ncaaf/pregame/2025-09-06_pregame.json') as f:
    odds = json.load(f)

# Load team stats
stats_df = pd.read_parquet('output/espn/ncaaf/team_stats_2025_week1.parquet')

# Load weather
with open('output/weather/ncaaf/game_forecasts_2025_week1.json') as f:
    weather = json.load(f)

# Load edges found
with open('output/analysis/ncaaf/edge_detection_2025_week1.json') as f:
    edges = json.load(f)

# Load conference breakdowns
with open('output/analysis/ncaaf/conference_edges_2025_week1.json') as f:
    conf_edges = json.load(f)

# Combine for analysis
print(f"Odds: {len(odds)} games")
print(f"Stats: {len(stats_df)} teams")
print(f"Weather: {len(weather)} forecasts")
print(f"Edges: {len(edges)} opportunities")
print(f"By Conference: {list(conf_edges.keys())}")
```

### Export for External Tools

```bash
# Convert to CSV for Excel
python -c "
import pandas as pd

# Team stats to CSV
stats = pd.read_parquet('output/espn/ncaaf/team_stats_2025_week1.parquet')
stats.to_csv('output/espn/ncaaf/team_stats_2025_week1.csv', index=False)

# Weather to CSV
weather = pd.read_parquet('output/weather/ncaaf/stadium_conditions_2025_week1.parquet')
weather.to_csv('output/weather/ncaaf/stadium_conditions_2025_week1.csv', index=False)

# Edge detection to CSV
import json
with open('output/analysis/ncaaf/edge_detection_2025_week1.json') as f:
    edges = json.load(f)
edges_df = pd.DataFrame(edges)
edges_df.to_csv('output/analysis/ncaaf/edge_detection_2025_week1.csv', index=False)

print('Exported to CSV')
"
```

### Query by Conference

```python
import pandas as pd
import json

# Load teams with conference info
with open('output/espn/ncaaf/teams_reference.json') as f:
    teams = json.load(f)

# Group by conference
by_conf = {}
for team in teams:
    conf = team.get('conference', 'Other')
    if conf not in by_conf:
        by_conf[conf] = []
    by_conf[conf].append(team['name'])

# Example: Get all SEC teams
sec_teams = by_conf.get('SEC', [])
print(f"SEC Teams: {sec_teams}")

# Load stats and filter
stats = pd.read_parquet('output/espn/ncaaf/team_stats_2025_week1.parquet')
# (Assuming stats has a 'conference' column)
sec_stats = stats[stats['conference'] == 'SEC'].sort_values('points_per_game', ascending=False)
print(sec_stats[['team', 'points_per_game', 'points_allowed_per_game']].head(10))
```

---

## Conference Considerations

College football differs from NFL in several ways that affect analysis:

### Power Conference vs FBS

```
Power 5: SEC, Big Ten, ACC, Big 12, Pac-12
Group of Five: American, MAC, Mountain West, Mid-American, Sun Belt, etc.
Independent: Notre Dame, Army, Liberty, New Mexico State, etc.

Note: Pac-12 dissolving in 2025 - teams moving to other conferences
```

### Strength of Schedule

College football SOS varies dramatically. A 6-6 team from a power conference may be stronger than an 8-4 team from a mid-tier conference.

```python
# Compare teams accounting for SOS
import json
with open('output/massey/ncaaf_ratings_2025_week1.json') as f:
    massey = json.load(f)

# Look for 'sos' or 'strength_of_schedule' field
# Higher SOS teams get credit for tough schedules
```

### Player Development Curve

College teams improve/decline through the season as freshmen develop and injuries accumulate. Track trajectory, not just current stats.

```bash
# Compare week-to-week stats
python -c "
import pandas as pd
import glob

# Load multiple weeks
stats_files = glob.glob('output/espn/ncaaf/team_stats_*.parquet')
stats_files.sort()

# Compare same team across weeks
team_stats = []
for file in stats_files[-3:]:  # Last 3 weeks
    df = pd.read_parquet(file)
    team_stats.append(df[df['team'] == 'Alabama'])

# Plot trajectory
print('Alabama progression (last 3 weeks):')
for i, stats in enumerate(team_stats):
    print(f'  Week {i+1}: {stats[\"points_per_game\"].values}')
"
```

---

## Summary

**NCAAF Data Collection** is fully automated and produces:
- ✅ Well-organized output structure (no intermixing with NFL)
- ✅ Multiple data sources for comprehensive analysis
- ✅ Fast collection (~6 minutes weekly)
- ✅ 130+ FBS team coverage
- ✅ Conference-aware organization
- ✅ Production-ready quality checks
- ✅ Easy extraction and integration

**Key Principles:**
1. Keep NCAAF and NFL data strictly separated by directory structure
2. Account for conference differences in analysis
3. Track team trajectory (development, injuries)
4. Use strength of schedule in rating calculations
5. Monitor longer during games (staggered start times)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-25
**Maintained By:** Billy Walters Sports Analyzer Team
