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

### Daily Development
```bash
# Start session
git pull origin main --rebase

# During session (every 30-60 min)
git add .
git commit -m "type(scope): brief description"
git push origin main
```

### Commit Format
```
type(scope): brief description (50 chars max)

Detailed explanation if needed.

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`

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

### Session: 2025-11-28 - Weekly Task Automation Complete

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

**Output Format** (`output/overtime/{league}/pregame/api_walters_*.json`):
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

---

## Session Summary: 2025-11-28 (Session 2)

### What Was Accomplished

**Overtime.ag API Client Enhancement - COMPLETE**
1. ✅ Enhanced `OvertimeApiClient` (v2.0.0 → v2.1.0)
2. ✅ Added proper UTC datetime parsing from .NET timestamps
3. ✅ Added Eastern Time conversion for display
4. ✅ Added timezone info field (`America/New_York`)
5. ✅ Added week extraction from NFL comments
6. ✅ Maintained backward compatibility with edge detector

**Integration Decision**
- ✅ Chose internal API client over external browser-based client
- Internal: ~2-3 sec, no auth, reliable
- External: ~70 sec, requires login, has timeout bugs

**Production Validation**
- ✅ NFL Week 13: 8 edges detected
- ✅ NCAAF Week 14: 11 edges detected
- ✅ Full pipeline tested end-to-end

### Edge Detection Results (Current Week)

**NFL Week 13** (8 edges):
| # | Matchup | Edge | Strength | Bet |
|---|---------|------|----------|-----|
| 1 | New Orleans @ Miami | 9.6 pts | VERY_STRONG | HOME |
| 2 | NY Giants @ New England | 8.9 pts | VERY_STRONG | HOME |
| 3 | San Francisco @ Cleveland | 8.1 pts | VERY_STRONG | AWAY |
| 4 | Chicago @ Philadelphia | 8.0 pts | VERY_STRONG | HOME |
| 5 | Denver @ Washington | 7.3 pts | VERY_STRONG | AWAY |

**NCAAF Week 14** (11 edges):
| # | Matchup | Edge | Strength | Bet |
|---|---------|------|----------|-----|
| 1 | Central Florida @ BYU | 19.4 pts | VERY_STRONG | AWAY |
| 2 | Arizona @ Arizona State | 16.5 pts | VERY_STRONG | HOME |
| 3 | Ohio State @ Michigan | 11.9 pts | VERY_STRONG | HOME |
| 4 | Mississippi @ Miss State | 11.8 pts | VERY_STRONG | HOME |
| 5 | Texas Tech @ West Virginia | 10.0 pts | VERY_STRONG | HOME |

### Key Files Modified

**Enhanced**:
- `src/data/overtime_api_client.py` - Added datetime/week parsing (v2.1.0)

**Documentation**:
- `CLAUDE.md` - Added API client docs and current edges

### Production Checklist

- ✅ Overtime.ag API client enhanced (v2.1.0)
- ✅ Proper UTC/ET datetime parsing
- ✅ Week extraction working (NFL)
- ✅ Edge detection pipeline validated
- ✅ NFL Week 13: 8 edges
- ✅ NCAAF Week 14: 11 edges
- ✅ Automated tasks configured
- ✅ Documentation updated

**System Ready for Production Use**
