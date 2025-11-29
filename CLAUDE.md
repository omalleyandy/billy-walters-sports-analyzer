# Billy Walters Sports Analyzer - Development Guidelines

Football-focused sports analytics system (NFL & NCAAF) using Billy Walters' methodology. Complete infrastructure for edge detection, CLV tracking, and automated weekly orchestration.

> **📖 Complete Documentation**: See [docs/_INDEX.md](docs/_INDEX.md) for full guides, API docs, and technical references.

---

## Quick Start

### Weekly Automated Tasks (Windows Task Scheduler)
```powershell
# Setup (run once as Administrator)
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
.\scripts\automation\setup_weekly_tasks.ps1

# Tasks created:
# - Tuesday 2:00 PM: NFL edge detection
# - Wednesday 2:00 PM: NCAAF edge detection
# - Monday 3:00 PM: Results checking & CLV tracking
```

### Manual Edge Detection
```bash
# NFL edges for current week
uv run python scripts/analysis/edge_detector_production.py --nfl --verbose

# NCAAF edges for current week
uv run python scripts/analysis/edge_detector_production.py --ncaaf --verbose

# Both leagues
uv run python scripts/analysis/edge_detector_production.py --both --verbose
```

### Output Locations
```
output/
├── edge_detection/           # Detected betting edges (JSONL format)
├── clv_tracking/             # Betting records and CLV metrics
├── action_network/           # Sharp money signals (Action Network)
├── espn/nfl/ & /ncaaf/       # Team statistics
├── overtime/nfl/ & /ncaaf/   # Pregame odds (API client v2.1.0)
├── weather/nfl/ & /ncaaf/    # Stadium weather data
└── massey/                   # Power ratings
```

### Fetch Fresh Odds (Optional - Auto-fetched by Edge Detection)
```bash
# Fetch latest odds from Overtime.ag (fast API, no browser needed)
uv run python -c "
import asyncio
from src.data.overtime_api_client import OvertimeApiClient
async def fetch():
    client = OvertimeApiClient()
    await client.scrape_nfl()
    await client.scrape_ncaaf()
asyncio.run(fetch())
"
```

---

## Core Development Rules

### 1. Package Management
- **ONLY** use `uv`, **NEVER** pip
- Install: `uv add package`
- Run tools: `uv run command`
- Dev deps: `uv add --dev package`

### 2. Code Quality
- Type hints required
- Use `pyright` for type checking: `uv run pyright`
- Line length: 88 chars (Black/Ruff standard)
- Auto-format: `uv run ruff format .`

### 3. Testing
- Framework: `uv run pytest`
- Async testing: use `anyio`, not `asyncio`
- Run before pushing: `uv run pytest tests/ -v --cov=.`

### 4. Code Style
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Public APIs: Google-style docstrings

---

## Environment Variables & API Keys

Create `.env` file (never commit):

```bash
# AI Services
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Weather
ACCUWEATHER_API_KEY=...

# Sports Data
ACTION_USERNAME=...
ACTION_PASSWORD=...
OV_CUSTOMER_ID=...
OV_PASSWORD=...

# Optional: Proxies
PROXY_URL=...
PROXY_USER=...
PROXY_PASS=...
```

See `.env.example` for complete list.

---

## CI/CD Pipeline

### Local Validation (Run Before Every Push)
```bash
# 1. Format code
uv run ruff format .

# 2. Check formatting
uv run ruff format --check .

# 3. Lint
uv run ruff check .

# 4. Type check
uv run pyright

# 5. Run tests
uv run pytest tests/ -v --cov=.
```

All must pass. Quick fix for 90% of CI failures:
```bash
uv run ruff format .
uv run ruff check . --fix
```

---

## Git Workflow

### Automated Git Management
**You don't touch git. Claude handles it completely.**

- After every code change, Claude automatically commits to `main`
- Commits follow conventional commit format with clear, descriptive messages
- Pushes happen immediately after each commit
- No feature branches - everything goes direct to `main`

### Commit Format (Automated)
```
type(scope): description

Detailed explanation of changes.

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`

Just ask for changes. Git happens automatically.

---

## Project Structure

```
src/
├── data/                      # Data collection (27+ scrapers)
├── walters_analyzer/
│   ├── valuation/             # Edge detection (11 modules)
│   ├── workflows/             # Orchestration (4 modules)
│   └── query/                 # Display utilities
└── db/                        # Database layer

scripts/
├── automation/                # Task Scheduler setup
│   ├── setup_weekly_tasks.ps1 # Create 3 automated tasks
│   └── cleanup_tasks.ps1      # Remove tasks
├── analysis/                  # Weekly analysis scripts
├── scrapers/                  # Data collection
└── validation/                # Data validation

output/                        # Results (organized by data source)
tests/                         # Test suite (146+ tests)
docs/                          # Complete documentation
.claude/                       # Automation hooks & commands
```

---

## Automation Setup

### What's Automated (Windows Task Scheduler)

Three scheduled tasks run automatically every week:

| Task | Day/Time | Command | Output |
|------|----------|---------|--------|
| NFL Edges | Tuesday 2:00 PM | `edge_detector_production.py --nfl` | `edge_detection/` |
| NCAAF Edges | Wednesday 2:00 PM | `edge_detector_production.py --ncaaf` | `edge_detection/` |
| CLV Tracking | Monday 3:00 PM | `check_betting_results.py` | Results logs |

### How It Works

1. **Setup Script**: `scripts/automation/setup_weekly_tasks.ps1`
   - Creates wrapper scripts in `scripts/temp/`
   - Registers 3 tasks with Windows Task Scheduler
   - Auto-detects system week and validates data

2. **Wrapper Scripts**: `scripts/temp/task_*.ps1`
   - Execute from project root directory
   - Use `uv run python` for proper environment
   - Log output to system Event Viewer

3. **Pre-flight Validation**
   - Schedule file validation (correct week)
   - Odds file validation (matching week)
   - Missing data warnings (prevents wasted computation)

### Verify Tasks Created

```powershell
# List all Billy Walters tasks
schtasks /query | findstr "BillyWalters"

# Check specific task status
schtasks /query /tn "BillyWalters-Weekly-NFL-Edges-Tuesday" /fo list /v
```

### Manual Task Execution

```powershell
# Run immediately (don't wait for schedule)
Start-ScheduledTask -TaskName "BillyWalters-Weekly-NFL-Edges-Tuesday"

# Remove all tasks if needed
.\scripts\automation\cleanup_tasks.ps1
```

---

## Billy Walters Methodology

### Edge Thresholds
- **7+ points**: MAX BET (5% Kelly, 77% win rate)
- **4-7 points**: STRONG (3% Kelly, 64% win rate)
- **2-4 points**: MODERATE (2% Kelly, 58% win rate)
- **1-2 points**: LEAN (1% Kelly, 54% win rate)
- **<1 point**: NO PLAY

### Success Metrics (In Order)
1. **CLV (Closing Line Value)** - Primary metric (did we beat the closing odds?)
2. **ATS (Against The Spread)** - Win percentage
3. **ROI** - Return on investment

### Key Principle
"Follow the money, not the tickets" - Sharp money integration via Action Network divergence (5%+ = signal)

### Integration Points
- **Power Ratings**: Base edge calculation
- **Sharp Money**: Confirmation/contradiction adjustment (±10-20% confidence)
- **Dynamic Adjustments**: Weather, injuries, situational factors
- **CLV Tracking**: Performance measurement against closing odds

---

## Troubleshooting

### Common Issues

**Edge Detection Returns 0 Edges**
- Check: Odds file exists for current week
- Check: Schedule file exists for current week
- Check: Team names match across ESPN → Overnight.ag → Massey

**Task Fails with Error Code 267011**
- Old `--full` flag used (replace with `--verbose`)
- Update: `scripts/temp/task_*.ps1` files manually
- Re-run: `.\scripts\automation\setup_weekly_tasks.ps1` as Administrator

**PowerShell Get-ScheduledTask Error**
- Known issue: `Get-ScheduledTask` has quirk reading certain XML
- Verify with: `schtasks /query /tn "TaskName"` instead
- Tasks work fine despite error

**Missing Dependencies**
```bash
uv sync --all-extras --dev
```

---

## Development Philosophy

- **Simplicity**: Write clear, straightforward code
- **Less Code = Less Debt**: Minimize footprint, maximum functionality
- **Early Returns**: Avoid nested conditions
- **DRY Code**: Don't repeat yourself
- **Minimal Changes**: Only modify code related to the task
- **Build Iteratively**: Start minimal, verify, then add complexity
- **Test Frequently**: Validate with realistic inputs

---

## Recent Updates

### Session: 2025-11-28 (Session 4) - SQLite Migration & Raw Data Pipeline Complete

**Status**: ✅ DATABASE MIGRATION COMPLETE - PostgreSQL → SQLite, 19 tables implemented

**Changes**:
- ✅ **Migrated PostgreSQL to SQLite** (zero infrastructure required)
  - Refactored DatabaseConnection (psycopg2 → sqlite3)
  - Updated all 50+ SQL queries (PostgreSQL → SQLite syntax)
  - Changed placeholders (%s → ?)
  - Added row_factory for dict-like access

- ✅ **Designed Raw Data Collection Schema** (19 tables total)
  - 8 betting/edge tables (edges, clv_plays, edge_sessions, clv_sessions, games, leagues, teams, odds)
  - 11 raw data tables (game_schedules, game_results, team_stats, player_stats, team_standings, power_ratings, betting_odds, sharp_money_signals, weather_data, injury_reports, news_articles, collection_sessions)

- ✅ **Created Data Validation Layer**
  - 12 Pydantic models for type-safe data
  - 25+ CRUD operations for raw data
  - Foreign key constraints & referential integrity
  - 16 optimized indexes for performance

- ✅ **Gap Analysis vs Billy Walters PRD v1.5**
  - Analyzed 10 missing data categories
  - Identified 4 TIER 1 critical tables for next phase
  - Prioritized by impact on Billy Walters methodology

- ✅ **Created Migration Utility**
  - Convert JSON edges/CLV plays to SQLite
  - Usage: `python scripts/migration/migrate_to_sqlite.py --league ncaaf --all-weeks`

**Files Changed**: 9 files (connection.py, models.py, operations.py, schema.sql, __init__.py, + 4 new files)
**Tests Passing**: All 146+ tests (no regressions)
**Git**: 4 commits to main with detailed messages

### Previous: Session 2025-11-28 (Session 3) - Automated Git Management Configured

**Status**: ✅ AUTOMATIC GIT WORKFLOWS ENABLED - All commits handled by Claude

**Status**: ✅ PRODUCTION READY - All three automated tasks configured and tested

**Work Completed**:
1. **PowerShell Setup Script** (`setup_weekly_tasks.ps1`)
   - Creates 3 scheduled tasks (NFL Tue, NCAAF Wed, CLV Mon)
   - Generates wrapper scripts in `scripts/temp/`
   - Proper time formatting for Task Scheduler XML
   - Auto cleanup of old tasks

2. **Wrapper Script System**
   - External PowerShell scripts avoid quote escaping issues
   - Prepend `uv run` to all python commands
   - Set working directory to project root
   - Clean Task Scheduler XML generation

3. **Command Corrections**
   - Replaced `--full` flag with `--verbose`
   - Added proper `uv run` wrapping
   - Tested all three tasks manually
   - Confirmed exit code 0 (success) for NFL task

4. **Testing & Verification**
   - NFL task: Last Result 0 (success) ✅
   - NCAAF task: Executes without argument errors ✅
   - CLV task: Ready and configured ✅
   - All tasks show Status: Ready in Task Scheduler

**Files Created/Modified**:
- `scripts/automation/setup_weekly_tasks.ps1` - Fixed time parsing, added wrapper script generation
- `scripts/automation/cleanup_tasks.ps1` - Task removal utility
- `scripts/temp/task_*.ps1` - 3 wrapper scripts (auto-generated)

**Deployment Instructions**:
```powershell
# Run once as Administrator
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
.\scripts\automation\setup_weekly_tasks.ps1
```

---

## Quick Command Reference

| Task | Command | Time |
|------|---------|------|
| Current week detection | `uv run python src/walters_analyzer/utils/schedule_validator.py` | <10 sec |
| NFL edges | `uv run python scripts/analysis/edge_detector_production.py --nfl --verbose` | 7-26 sec |
| NCAAF edges | `uv run python scripts/analysis/edge_detector_production.py --ncaaf --verbose` | 7-26 sec |
| Both leagues | `uv run python scripts/analysis/edge_detector_production.py --both --verbose` | 7-26 sec |
| Check results | `uv run python scripts/analysis/check_betting_results.py --league nfl` | <5 sec |
| Run all tests | `uv run pytest tests/ -v` | 30-60 sec |
| Format code | `uv run ruff format .` | <10 sec |
| Type check | `uv run pyright` | 10-20 sec |

---

## For Complete Details

- **Methodology**: [docs/guides/methodology/BILLY_WALTERS_METHODOLOGY_AUDIT.md](docs/guides/methodology/BILLY_WALTERS_METHODOLOGY_AUDIT.md)
- **Edge Detection**: [docs/guides/EDGE_DETECTOR_WORKFLOW.md](docs/guides/EDGE_DETECTOR_WORKFLOW.md)
- **Data Collection**: [docs/guides/DATA_COLLECTION_QUICK_REFERENCE.md](docs/guides/DATA_COLLECTION_QUICK_REFERENCE.md)
- **All Documentation**: [docs/_INDEX.md](docs/_INDEX.md)

---

**Last Updated**: 2025-11-28 (Session 2 Complete)
**Status**: ✅ PRODUCTION READY

---

## Data Collection Orchestration

### Complete Data Pipeline (Both Leagues)

Run `/collect-all-data` for complete weekly data collection, or use individual commands:

| Data Source | NFL Command | NCAAF Command | Output Path |
|-------------|-------------|---------------|-------------|
| **Power Ratings** | `update_power_ratings_from_massey.py` | Same (both leagues) | `data/current/{league}_power_ratings.json` |
| **Odds** | Overtime API (auto) | Overtime API (auto) | `output/overtime/{league}/pregame/{league}_odds_*.json` |
| **Schedule** | `scrape_massey_games.py --league nfl` | `scrape_massey_games.py --league ncaaf` | `data/current/{league}_week_N_games.json` |
| **Team Stats** | `scrape_espn_team_stats.py --nfl` | `scrape_espn_team_stats.py --ncaaf` | `output/espn/stats/{league}/` |
| **Injuries** | ESPN (NFL only) | N/A | `data/current/nfl_week_N_injuries.json` |
| **Weather** | AccuWeather (outdoor) | AccuWeather (outdoor) | `data/current/{league}_week_N_weather.json` |
| **X News** | `scrape_x_news_integrated.py` | Same | `output/x_news/integrated/` |
| **Action Network** | `scrape_action_network_live.py --nfl` | `scrape_action_network_live.py --ncaaf` | `output/action_network/{league}/` |

### Session Start Data Check

When you start a session, the hook automatically checks data freshness:

```
======================================================================
BILLY WALTERS SESSION START
======================================================================
Current Week: NFL Week 13 | NCAAF Week 14

NFL Data Status:
  [OK] Power Ratings: 0.4h old (FRESH)
  [OK] Odds: 0.2h old (FRESH)
  [OK] Schedule: 12.0h old (FRESH)
  [X] Injuries: MISSING
  [X] Weather: MISSING

NCAAF Data Status:
  [OK] Power Ratings: 12.0h old (FRESH)
  [OK] Odds: 0.2h old (FRESH)
  [OK] Schedule: 12.0h old (FRESH)

Data Gaps:
  [!] NFL Week 13 missing: injuries, weather
======================================================================
```

---

## Database Architecture (SQLite - 2025-11-28)

### Core Components

**Connection Layer** (`src/db/connection.py`):
```python
DatabaseConnection.get_connection() -> sqlite3.Connection
# Features:
# - File-based storage (zero infrastructure)
# - Automatic schema initialization
# - Row factory for dict-like access
# - Connection pooling (optional)
```

**Data Models** (`src/db/models.py`):
- League, Team, Game, Edge, CLVPlay, EdgeSession, CLVSession, PowerRating, Odds, Bet, Weather, Injury, SituationalFactors, PerformanceMetrics

**Raw Data Models** (`src/db/raw_data_models.py`):
- GameSchedule, GameResult, TeamStats, PlayerStats, TeamStandings, PowerRating, BettingOdds, SharpMoneySignal, WeatherData, InjuryReport, NewsArticle, CollectionSession

**Database Operations** (`src/db/operations.py`):
- Edge detection & insertion
- CLV play tracking & results
- Session metadata management

**Raw Data Operations** (`src/db/raw_data_operations.py`):
- 25+ CRUD methods for raw data collection
- Schedule/result loading
- Team stats aggregation
- Power ratings from multiple sources
- Weather & injury integration

### Schema Overview (19 tables, 16 indexes)

```
Betting & Analysis Tables (8):
├── edges - Detected betting opportunities
├── clv_plays - Betting records with CLV tracking
├── edge_sessions - Metadata for edge detection runs
├── clv_sessions - Metadata for CLV tracking runs
├── games - Game matchups
├── leagues - League reference (NFL, NCAAF)
├── teams - Team reference data
└── odds - Historical betting odds

Raw Data Collection Tables (11):
├── game_schedules - Game dates, venues, status
├── game_results - Final scores, ATS, O/U results
├── team_stats - Offensive, defensive, special teams (37+ fields)
├── player_stats - Individual player performance (18+ fields)
├── team_standings - Records, rankings, point differential
├── power_ratings - Massey & custom power ratings
├── betting_odds - Multi-source odds history
├── sharp_money_signals - Action Network divergence analysis
├── weather_data - Game-day weather conditions
├── injury_reports - Player injury status & impact
└── news_articles - Team news & relevant articles
└── collection_sessions - Data collection metadata
```

### Data Flow Architecture

```
Collection Phase (27 scrapers/APIs):
├── ESPN (team stats, schedules, results)
├── Massey Ratings (power ratings)
├── Action Network (sharp money signals)
├── AccuWeather (weather data)
├── Overtime.ag (betting odds)
├── X/Twitter (news & sentiment)
└── NFL.com (injury reports)
      ↓
Validation Phase (Pydantic models):
├── Type checking
├── Constraint validation
├── Null handling
└── Data quality checks
      ↓
Storage Phase (SQLite):
├── Insert to raw data tables
├── Enforce foreign keys
├── Update collection sessions
└── Log errors & warnings
      ↓
Analysis Phase (Edge Detection):
├── Power ratings calculation
├── Edge detection (90/10 Billy Walters formula)
├── Injury impact adjustment
├── Weather factor adjustment
└── CLV tracking
```

---

## Data Sources & APIs

### Overtime.ag API Client (v2.1.0)
The internal `OvertimeApiClient` is the primary odds source:

| Feature | Status | Notes |
|---------|--------|-------|
| Direct API (no browser) | ✅ | POST to `Offering.asmx/GetSportOffering` |
| Speed | ~2-3 sec/league | vs ~70 sec for browser scraper |
| Auth Required | No | Public API endpoint |
| UTC DateTime | ✅ | Parsed from .NET timestamp |
| Week Extraction | ✅ | From NFL comments field |
| Timezone Info | ✅ | America/New_York (ET) |

**Output Format** (`output/overtime/{league}/pregame/{league}_odds_*.json`):
```json
{
  "metadata": {"source": "overtime.ag", "week": 13, "converter_version": "2.1.0"},
  "games": [{
    "away_team": "Arizona Cardinals",
    "home_team": "Tampa Bay Buccaneers",
    "game_datetime_utc": "2025-11-30T18:00:01+00:00",
    "game_datetime_et": "2025-11-30T13:00:01-05:00",
    "timezone": "America/New_York",
    "week": 13,
    "spread": {"home": -3.5, "home_odds": -113},
    "total": {"points": 44.5}
  }]
}
```

### AccuWeather Integration (v1.1.0)
Weather API with smart datetime parsing:

| Feature | Status | Notes |
|---------|--------|-------|
| DateTime Parsing | ✅ | Handles ISO, US format, simple format |
| Indoor Detection | ✅ | Skips dome stadiums |
| Rate Limiting | ✅ | 1 req/sec |
| Hourly Forecast | ✅ | 12h (starter plan limit) |

**Supported DateTime Formats**:
- ISO: `2025-11-30T18:00:01+00:00`
- US: `11/30/2025 1:00 PM`
- Simple: `2025-11-30 18:00`

---

## Next Phase: TIER 1 Critical Tables

### 4 Tables Identified for Implementation (Priority Order)

Based on gap analysis against Billy Walters PRD v1.5, these 4 tables are critical to complete the system:

**1. `player_valuations` (TIER 1 - CRITICAL)**
- **Purpose**: Calculate injury impact using player point values
- **Fields**: player_id, position, team_id, season, point_value, snap_count_pct, impact_rating
- **Integration**: Used by injury_reports to determine severity adjustment
- **Impact**: Can't properly assess injury consequences without this

**2. `practice_reports` (TIER 1 - CRITICAL)**
- **Purpose**: Track Wednesday practice status (Billy's key signal)
- **Fields**: player_id, team_id, week, day_of_week, status, severity, trend
- **Integration**: Feeds into injury reports & confidence adjustments
- **Impact**: Billy specifically tracks "Wednesday = lock" signal

**3. `game_swe_factors` (TIER 1 - CRITICAL)**
- **Purpose**: Special/Weather/Emotional factor tracking
- **Fields**: game_id, special_factor, weather_factor, emotional_factor, notes
- **Integration**: Adjusts power ratings (±10-20% adjustments)
- **Impact**: Core to Billy's spread calculation formula

**4. `team_trends` (TIER 1 - CRITICAL)**
- **Purpose**: Track streaks, playoff picture, emotional factors
- **Fields**: team_id, season, week, streak_direction, streak_length, playoff_position, emotional_state
- **Integration**: Used for confidence adjustments & play selection
- **Impact**: Contextual factors for bet recommendation

### Coming in Next Conversation

A new, focused conversation will implement these 4 tables with:
- ✅ Complete table schemas
- ✅ Pydantic models for validation
- ✅ CRUD operations (25+ methods)
- ✅ Integration with existing system
- ✅ Usage examples
- ✅ Testing & validation

---

## Session Summary: 2025-11-28 (Session 3)

### What Was Accomplished

**1. Hooks & Slash Commands Configuration**
- ✅ Fixed hook file references (`pre_data_collection.py` → `pre_data_collection_validator.py`)
- ✅ Added `/scrape-x-news` slash command
- ✅ Added post-tool hooks for `/scrape-overtime` and `/scrape-x-news`
- ✅ Updated slash command permissions in `settings.local.json`

**2. Overtime Output Filename Standardization**
- ✅ Changed `api_walters_*.json` → `nfl_odds_*.json` (NFL)
- ✅ Changed `api_walters_*.json` → `ncaaf_odds_*.json` (NCAAF)
- ✅ Updated all consumers: edge detectors, schedule validator, hooks

**3. Weather API Integration Fix**
- ✅ Fixed datetime parsing error (`str` vs `datetime` type mismatch)
- ✅ Added `_parse_game_time()` method to AccuWeather client
- ✅ Supports multiple formats: ISO, US, simple
- ✅ Edge detectors now prefer `game_datetime_utc` field

**4. Session Start Hook Enhancement**
- ✅ Added NCAAF week detection
- ✅ Expanded data source checks (injuries, weather, team stats, ESPN)
- ✅ Organized output by league (NFL/NCAAF)
- ✅ Added "Data Gaps" summary section

### Files Modified

| File | Changes |
|------|---------|
| `src/data/overtime_api_client.py` | Output filenames: `{league}_odds_*.json` |
| `src/data/accuweather_client.py` | Added `_parse_game_time()`, updated `get_game_weather()` signature |
| `src/walters_analyzer/valuation/ncaaf_edge_detector.py` | Use `game_datetime_utc` for weather |
| `src/walters_analyzer/valuation/billy_walters_edge_detector.py` | Use `game_datetime_utc` for weather |
| `src/walters_analyzer/utils/schedule_validator.py` | Dynamic odds filename pattern |
| `.claude/hooks/session_start.py` | NCAAF week, expanded data checks, data gaps |
| `.claude/hooks/auto_edge_detector.py` | Updated odds filename patterns |
| `.claude/settings.local.json` | Fixed hook references, added permissions |
| `.claude/commands/scrape-x-news.md` | New slash command |

### Edge Detection Results (Current Week)

**NCAAF Week 14** (12 edges with weather):
| # | Matchup | Edge | Strength | Bet |
|---|---------|------|----------|-----|
| 1 | Charlotte @ Tulane | 20.5 pts | VERY_STRONG | HOME |
| 2 | Notre Dame @ Stanford | 20.0 pts | VERY_STRONG | AWAY |
| 3 | UCLA @ USC | 11.6 pts | VERY_STRONG | HOME |
| 4 | Alabama @ Auburn | 9.4 pts | VERY_STRONG | AWAY |
| 5 | Central Florida @ BYU | 8.4 pts | VERY_STRONG | AWAY |

### Production Checklist

- ✅ Hooks configured and validated
- ✅ Slash commands updated
- ✅ Overtime output standardized (`{league}_odds_*.json`)
- ✅ Weather API datetime parsing fixed
- ✅ Session start shows data gaps
- ✅ Edge detection working with weather adjustments
- ✅ Both leagues (NFL/NCAAF) fully supported

**System Ready for Production Use**
