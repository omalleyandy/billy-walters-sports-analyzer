# NFL Data Collection Workflow

**League:** National Football League (NFL)
**Season:** 2025
**Last Updated:** 2025-11-25
**Status:** Production Ready

## Overview

Complete workflow for NFL data collection with **strictly separated output structure**. This guide ensures NFL data is never intermixed with NCAAF data.

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

**Collect all NFL data for the week:**

```bash
# Tuesday/Wednesday - before games
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# OR collect everything (recommended for weekly prep)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```

**During games (Sunday):**

```bash
# Get pregame odds first
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# Then monitor for 3 hours
uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 10800
```

---

## Complete Workflow

### Phase 1: Scheduled Collection (Tuesday 2:00 PM)

**Time Required:** ~5-7 minutes

This phase collects all baseline data before any games start.

#### Step 1: Overtime Pregame Odds (⚡ ~5 seconds)

```bash
echo "[1/5] Collecting Overtime pregame odds..."
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

**What it does:**
- Fetches all pregame odds from Overtime.ag
- Covers all NFL games for the week
- Includes moneylines, spreads, totals, props
- Stores in: `output/overtime/nfl/pregame/`

**Output:**
```
output/overtime/nfl/pregame/
├── 2025-01-12_pregame.json      # All games + odds
├── 2025-01-13_pregame.json
└── 2025-01-19_pregame.json      # TNF next week
```

#### Step 2: ESPN Team Statistics (📊 ~2 minutes)

```bash
echo "[2/5] Collecting ESPN team statistics..."
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl
```

**What it does:**
- Fetches offensive/defensive stats for all 32 NFL teams
- Includes PPG, YPG, efficiency metrics
- Updates weekly as season progresses

**Output:**
```
output/espn/nfl/
├── team_stats_2025_week12.parquet
├── team_stats_2025_week12.json
└── teams_reference.json           # Team IDs and names
```

#### Step 3: Massey Power Ratings (📊 ~1 minute)

```bash
echo "[3/5] Collecting Massey ratings..."
uv run python scripts/scrapers/scrape_massey_games.py
```

**What it does:**
- Fetches college and pro ratings from Massey
- Used for power rating calculations
- Both NFL and NCAAF (will be separated in next step)

**Output:**
```
output/massey/
├── nfl_ratings_2025_week12.json
├── ncaaf_ratings_2025_week12.json
└── ratings_2025_week12.parquet
```

#### Step 4: Weather for All NFL Stadiums (🌤️ <1 second)

```bash
echo "[4/5] Collecting weather data..."
python src/data/weather_client.py --league nfl
```

**What it does:**
- Gets current and forecasted weather for all 32 NFL stadiums
- Includes temperature, wind, precipitation
- Includes game-time weather for all scheduled games

**Output:**
```
output/weather/nfl/
├── game_forecasts_2025_week12.json
├── stadium_conditions_2025_week12.parquet
└── stadiums_reference.json        # Stadium locations
```

#### Step 5: Action Network Betting Lines (📱 ~2 minutes)

```bash
echo "[5/5] Collecting Action Network lines..."
uv run python scripts/scrapers/scrape_action_network_sitemap.py --nfl
```

**What it does:**
- Discovers all NFL games via sitemap
- Scrapes public betting lines
- Ensures complete coverage

**Output:**
```
output/action_network/nfl/
├── all_odds_2025_week12.json
├── game_lines_2025_week12.parquet
└── sportsbooks_reference.json
```

### Phase 2: Edge Detection (After Phase 1)

```bash
echo "[COMPLETE] Running edge detection..."
/edge-detector
```

This uses all collected data to find value opportunities.

### Phase 3: Game Day Collection (Sunday, before kickoff)

**Time Required:** ~5 seconds

```bash
# Get updated pregame odds
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

### Phase 4: Live Monitoring (During Games)

**Time Required:** 3+ hours (configurable)

```bash
# Monitor for 3 hours (10800 seconds)
uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 10800

# Optional: Monitor for longer periods on big game days
uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 28800  # 8 hours
```

**What it does:**
- Establishes live connection to Overtime.ag
- Streams real-time odds updates
- Captures line movement, injuries, prop updates
- Excellent for tracking sharp action and steam moves

**Output:**
```
output/overtime/nfl/live/
├── 2025-01-12_1000_stream.json    # Timestamped snapshots
├── 2025-01-12_1010_stream.json
├── 2025-01-12_1020_stream.json
└── ...
```

---

## Output Structure

### Directory Organization

All NFL data is **strictly organized under a single root:**

```
output/overtime/nfl/
├── pregame/                        # Pregame odds (Tuesday)
│   ├── 2025-01-12_pregame.json
│   ├── 2025-01-13_pregame.json
│   └── 2025-01-19_pregame.json
├── live/                           # Live updates (Sunday+)
│   ├── 2025-01-12_1000_stream.json
│   ├── 2025-01-12_1010_stream.json
│   └── 2025-01-12_1020_stream.json
└── archive/                        # Old files (auto-managed)
    └── 2024_season/

output/espn/nfl/
├── team_stats_2025_week12.parquet
├── team_stats_2025_week12.json
├── injuries_2025_week12.json
├── schedules_2025.json
└── teams_reference.json            # Team lookup

output/weather/nfl/
├── game_forecasts_2025_week12.json
├── stadium_conditions_2025_week12.parquet
└── stadiums_reference.json

output/action_network/nfl/
├── all_odds_2025_week12.json
├── game_lines_2025_week12.parquet
└── sportsbooks_reference.json

output/analysis/nfl/
├── edge_detection_2025_week12.json  # Betting opportunities
├── power_ratings_2025_week12.json   # Custom ratings
├── clv_tracking_2025.parquet        # Performance tracking
└── recommendations_2025_week12.json # Picks
```

### File Naming Convention

**Format:** `{component}_{sport}_{period}_{datetime|detail}.{ext}`

**Examples:**
- `pregame.json` - Pregame odds snapshot
- `2025-01-12_stream.json` - Game-day stream snapshot
- `team_stats_2025_week12.parquet` - Weekly team statistics
- `stadium_conditions_2025_week12.parquet` - Weather conditions
- `all_odds_2025_week12.json` - Weekly odds summary

---

## Data Verification

### Verify Collection Success

**Check file existence and size:**

```bash
# List recent NFL output files
ls -lth output/overtime/nfl/pregame/*.json | head -3
ls -lth output/espn/nfl/*.parquet
ls -lth output/weather/nfl/*.json
ls -lth output/action_network/nfl/*.json

# Verify file sizes (should not be 0 bytes)
find output -name "*nfl*" -type f -size 0
```

**Check data quality:**

```bash
# Validate JSON structure
python -m json.tool output/overtime/nfl/pregame/*.json > /dev/null && echo "Valid JSON"

# Check parquet files
python -c "
import pandas as pd
df = pd.read_parquet('output/espn/nfl/team_stats_2025_week12.parquet')
print(f'Teams: {len(df)}, Columns: {list(df.columns)[:5]}...')
"
```

### Expected Data Points

**Pregame Odds (Overtime API):**
- ✅ All 16 week + 2 playoff rounds
- ✅ Moneyline, spread, total for each game
- ✅ Live betting props
- ✅ ~50-100 KB per week

**ESPN Team Stats:**
- ✅ 32 NFL teams
- ✅ 20+ offensive/defensive metrics per team
- ✅ Updated weekly
- ✅ ~20-50 KB per week

**Weather:**
- ✅ All 32 stadium locations
- ✅ Game-time forecasts for all scheduled games
- ✅ Temperature, wind speed, precipitation
- ✅ ~10-30 KB per week

**Action Network:**
- ✅ All NFL games for the week
- ✅ Multiple sportsbook lines per game
- ✅ Props and alternative lines
- ✅ ~30-80 KB per week

---

## Troubleshooting

### Common Issues

#### "No NFL games found"

**Cause:** Off-season or incorrect league parameter

**Solution:**
```bash
# Verify current NFL season
python -c "import datetime; print(f'Week: {(datetime.date.today().isocalendar()[1] - 36) % 17}')"

# Check if data exists from last run
ls -la output/overtime/nfl/pregame/ | tail -5
```

#### "Connection timeout" from Overtime.ag

**Cause:** Network issue or Overtime server down

**Solution:**
```bash
# Test connectivity
curl -s https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering -d "sport=1" | head -50

# Wait 30 seconds and retry
sleep 30
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

#### NFL data is intermixed with NCAAF

**Cause:** Script collected both with `--nfl --ncaaf` flag or used wrong script

**Solution:**
```bash
# Check what was collected
ls output/*/nfl/ output/*/ncaaf/ 2>/dev/null | sort

# Collect NFL only (strict)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# Keep league separation going forward
# NFL collection: always use --nfl only, not --ncaaf
```

#### Weather API returning errors

**Cause:** Missing API key or invalid location

**Solution:**
```bash
# Check environment
echo $ACCUWEATHER_API_KEY  # Should not be empty
echo $OPENWEATHER_API_KEY  # Fallback if AccuWeather fails

# Test weather client directly
python -c "
import asyncio
from src.data import WeatherClient
async def test():
    async with WeatherClient() as client:
        weather = await client.get_forecast('green_bay', 'wi')
        print(weather)
asyncio.run(test())
"
```

---

## Performance Reference

### Speed Benchmarks

| Component | Time | Data Size | Notes |
|-----------|------|-----------|-------|
| Overtime API | <5 sec | ~100 KB | All weeks at once |
| ESPN Stats | ~2 min | ~50 KB | 32 teams |
| Weather | <1 sec | ~20 KB | Cached locations |
| Action Network | ~2 min | ~80 KB | Via sitemap |
| Hybrid Scraper | 30+ sec init | ~5 MB/hour | Real-time stream |
| Edge Detection | ~10 sec | ~50 KB output | Analysis only |

**Total Weekly Collection Time:** 5-7 minutes

### Parallel Execution

All components are independent except Edge Detection (which requires all inputs). You can run in parallel:

```bash
# Terminal 1: Odds
uv run python scripts/scrapers/scrape_overtime_api.py --nfl &

# Terminal 2: Stats
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl &

# Terminal 3: Weather
python src/data/weather_client.py --league nfl &

# Terminal 4: Action Network
uv run python scripts/scrapers/scrape_action_network_sitemap.py --nfl &

# Wait for all to complete
wait

# Then run edge detection
/edge-detector
```

---

## Weekly Workflow Checklist

### Tuesday 2:00 PM (Scheduled Collection)

- [ ] Run `/collect-all-data` or manual phase 1 workflow
- [ ] Verify all 5 data sources collected successfully
- [ ] Check file sizes and timestamps
- [ ] Run `/validate-data` to confirm quality
- [ ] Run `/edge-detector` to find opportunities
- [ ] Generate `/betting-card` with recommendations

### Sunday 12:00 PM (Before Kickoff)

- [ ] Quick odds refresh: `scrape_overtime_api.py --nfl`
- [ ] Check for line movement since Tuesday
- [ ] Review any new injury reports from ESPN
- [ ] Run `/edge-detector` with updated data

### Sunday 1:00 PM - 4:30 PM (Game Time)

- [ ] Start: `scrape_overtime_hybrid.py --duration 10800`
- [ ] Monitor for steam moves and sharp action
- [ ] Track injury developments
- [ ] Update any in-game adjustments

### Monday (Results & Analysis)

- [ ] Run `check_betting_results.py --league nfl`
- [ ] Calculate CLV and performance metrics
- [ ] Document edge accuracy
- [ ] Review missed opportunities

---

## Data Extraction & Integration

### Load into Analysis

```python
import pandas as pd
import json
from pathlib import Path

# Load NFL odds
with open('output/overtime/nfl/pregame/2025-01-12_pregame.json') as f:
    odds = json.load(f)

# Load team stats
stats_df = pd.read_parquet('output/espn/nfl/team_stats_2025_week12.parquet')

# Load weather
with open('output/weather/nfl/game_forecasts_2025_week12.json') as f:
    weather = json.load(f)

# Load edges found
with open('output/analysis/nfl/edge_detection_2025_week12.json') as f:
    edges = json.load(f)

# Combine for analysis
print(f"Odds: {len(odds)} games")
print(f"Stats: {len(stats_df)} teams")
print(f"Weather: {len(weather)} forecasts")
print(f"Edges: {len(edges)} opportunities")
```

### Export for External Tools

```bash
# Convert to CSV for Excel
python -c "
import pandas as pd

# Team stats to CSV
stats = pd.read_parquet('output/espn/nfl/team_stats_2025_week12.parquet')
stats.to_csv('output/espn/nfl/team_stats_2025_week12.csv', index=False)

# Weather to CSV
weather = pd.read_parquet('output/weather/nfl/stadium_conditions_2025_week12.parquet')
weather.to_csv('output/weather/nfl/stadium_conditions_2025_week12.csv', index=False)

print('Exported to CSV')
"
```

---

## Summary

**NFL Data Collection** is fully automated and produces:
- ✅ Well-organized output structure (no intermixing)
- ✅ Multiple data sources for comprehensive analysis
- ✅ Fast collection (~5 minutes weekly)
- ✅ Production-ready quality checks
- ✅ Easy extraction and integration
- ✅ Clear troubleshooting procedures

**Key Principle:** Keep NFL and NCAAF data strictly separated by directory structure and filename conventions.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-25
**Maintained By:** Billy Walters Sports Analyzer Team
