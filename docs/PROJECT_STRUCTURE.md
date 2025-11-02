# Project Structure Guide

## 📁 Complete Directory Structure

### Overview

```
billy-walters-sports-analyzer/
├── 📦 walters_analyzer/         # Main Python package
├── 🕷️ scrapers/                  # Scrapy spiders
├── 📊 data/                      # Data storage
├── 📜 scripts/                   # Utility scripts
├── 🧪 tests/                     # Test suite
├── 📚 docs/                      # Documentation
├── 💡 examples/                  # Example code
├── 🎴 cards/                     # Weekly betting cards
├── ⚙️ commands/                  # JSON command definitions
├── 🪝 hooks/                     # Pre/post-run hooks
├── 📸 snapshots/                 # Debug screenshots
├── 🔧 Configuration files        # pyproject.toml, .env, etc.
└── 📖 README files               # README.md, CLAUDE.md
```

---

## 📦 Package: `walters_analyzer/`

**Purpose:** Main Python package with all analysis logic

### Core Module (Phase 1) ✅
```
walters_analyzer/core/
├── __init__.py         # Module exports
├── http_client.py      # Async HTTP with connection pooling
├── cache.py            # Caching system with decorators
├── models.py           # All dataclasses (8 models)
└── config.py           # NEW: Configuration management
```

**Exports:**
- `async_get()`, `async_post()` - HTTP requests
- `@cache_weather_data()`, `@cache_injury_data()` - Caching
- `TeamRating`, `BetRecommendation`, `InjuryReport` - Models
- `get_config()` - Configuration access

### Research Module (Phase 2) ✅
```
walters_analyzer/research/
├── __init__.py          # Module exports
├── scrapy_bridge.py     # Scrapy → ResearchEngine connector
└── engine.py            # Multi-source research coordinator
```

**Exports:**
- `ScrapyBridge` - Load Scrapy data, convert to models
- `ResearchEngine` - Multi-source injury/weather analysis

### Backtest Module
```
walters_analyzer/backtest/
├── __init__.py
├── engine.py            # Backtest execution
├── metrics.py           # Performance metrics
└── validation.py        # Result validation
```

### Main Modules
```
walters_analyzer/
├── analyzer.py              # BillyWaltersAnalyzer (main class)
├── power_ratings.py         # PowerRatingEngine
├── bet_sizing.py            # BetSizingCalculator (Star + Kelly)
├── key_numbers.py           # KeyNumberCalculator
├── situational_factors.py   # SWEFactorCalculator
├── clv_tracker.py           # CLVTracker (closing line value)
├── weather_fetcher.py       # fetch_game_weather()
├── weather_pipeline.py      # WeatherDataPipeline
├── nfl_data.py              # NFL utilities (team mappings)
├── historical_db.py         # Historical data storage
├── cli.py                   # CLI entry point
└── wkcard.py                # Weekly card analysis
```

### Ingest Module
```
walters_analyzer/ingest/
└── overtime_loader.py       # Load overtime.ag data
```

---

## 🕷️ Scrapers: `scrapers/`

**Purpose:** Scrapy project for web scraping

```
scrapers/
├── overtime_live/               # Main Scrapy project
│   ├── spiders/
│   │   ├── espn_injury_spider.py     # ESPN injuries (Playwright)
│   │   ├── massey_ratings_spider.py  # Massey Ratings (CFB)
│   │   ├── overtime_live_spider.py   # Live betting odds
│   │   └── pregame_odds_spider.py    # Pre-game odds
│   │
│   ├── items.py                 # Dataclass items
│   │   ├── InjuryReportItem
│   │   ├── WeatherReportItem
│   │   ├── MasseyRatingItem
│   │   └── BettingOddsItem
│   │
│   ├── pipelines.py             # Data processing pipelines
│   │   ├── CSVPipeline
│   │   ├── InjuryPipeline       # JSONL + Parquet
│   │   └── MasseyRatingsPipeline
│   │
│   ├── selectors.py             # CSS/XPath selectors
│   └── settings.py              # Scrapy configuration
│
├── vi_spider/                   # Alternate spider (VI)
│   └── spiders/
│       └── vi_matchups.py
│
└── __init__.py
```

**Key Features:**
- Playwright integration for JS-heavy sites
- Dual output: JSONL (streaming) + Parquet (analytics)
- orjson for fast JSON serialization
- Auto-throttling for politeness

---

## 📊 Data: `data/`

**Purpose:** All scraped and generated data

```
data/
├── injuries/                       # ESPN injury scrapes
│   ├── injuries-YYYYMMDD-HHMMSS.jsonl
│   └── injuries-YYYYMMDD-HHMMSS.parquet
│
├── massey_ratings/                 # Massey Ratings (CFB)
│   ├── massey-YYYYMMDD-HHMMSS.jsonl
│   ├── massey-games-YYYYMMDD-HHMMSS.csv
│   ├── massey-games-YYYYMMDD-HHMMSS.parquet
│   └── massey-ratings-YYYYMMDD-HHMMSS.parquet
│
├── nfl_schedule/                   # ESPN API game data
│   ├── nfl_week1_2025_*.json
│   ├── nfl_week1_2025_*.jsonl
│   └── ... (18 weeks)
│
├── power_ratings/                  # Team power ratings
│   └── team_ratings.json          # Main ratings file
│
├── weather/                        # AccuWeather data
│   ├── weather-YYYYMMDD-HHMMSS.jsonl
│   └── weather-YYYYMMDD-HHMMSS.parquet
│
├── overtime_live/                  # Live betting odds
│   ├── overtime-live-YYYYMMDD-HHMMSS.jsonl
│   └── overtime-live-YYYYMMDD-HHMMSS.parquet
│
├── overtime_pregame/               # Pre-game odds
│
├── team_mappings/                  # Team databases
│   └── nfl_teams.json             # NFL team metadata
│
└── stadium_cache.json              # Stadium locations
```

**Data Lifecycle:**
1. **Scrape:** Scrapy spiders → JSONL + Parquet
2. **Load:** ScrapyBridge or direct file read
3. **Analyze:** ResearchEngine → ComprehensiveAnalysis
4. **Store:** Power ratings, CLV tracking

---

## 📜 Scripts: `scripts/`

**Purpose:** Utility and automation scripts

```
scripts/
├── NFL Workflows
│   ├── collect_nfl_schedule.py              # ESPN API scraper
│   ├── update_power_ratings_from_games.py   # Rating updater
│   ├── weekly_power_ratings_update.sh       # Linux/Mac automation
│   ├── weekly_power_ratings_update.bat      # Windows manual
│   └── weekly_power_ratings_update_auto.bat # Windows auto-detect

├── Massey Analysis
│   ├── analyze_massey_edges.py              # Edge detection
│   ├── compare_massey_week9.py              # Week comparison
│   └── validate_week9_edges.py              # Validation

├── Historical Data
│   ├── collect_historical_games.py          # Game collection
│   ├── collect_historical_odds.py           # Odds collection
│   └── run_backtest.py                      # Backtesting

├── Utilities
│   ├── demo_weather.py                      # Weather demo
│   ├── espn_cfb_scraper.py                  # CFB scraper
│   ├── repair-venv.ps1                      # venv repair (Windows)
│   └── wsl-clean-venv.ps1                   # venv clean (WSL)

└── Documentation
    ├── TASK_SCHEDULER_SETUP.md              # Windows automation
    └── update_log.txt                       # Automation logs
```

---

## 🧪 Tests: `tests/`

**Purpose:** Test suite for validation

```
tests/
├── conftest.py                  # Pytest configuration
├── test_power_ratings.py        # Power rating tests
├── test_key_numbers.py          # Key number tests
├── test_swe_factors.py          # S/W/E factor tests
├── test_injury_items.py         # Injury item tests
├── test_injury_pipeline.py      # Pipeline tests
├── test_parsing.py              # Parser tests
└── test_smoke.py                # Smoke tests
```

**Run Tests:**
```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_power_ratings.py -v

# With coverage
pytest tests/ --cov=walters_analyzer --cov-report=html
```

---

## 📚 Docs: `docs/`

**Purpose:** Comprehensive documentation

### Current Organization (50+ files)
```
docs/
├── README.md                    # THIS FILE - Documentation index
├── PROJECT_STRUCTURE.md         # Structure guide (this doc)
│
├── Phase 1 & 2 Implementation
│   ├── SESSION_SUMMARY.md              # Latest updates
│   ├── QUICK_REFERENCE.md              # API quick reference
│   ├── QUICK_WINS_COMPLETE.md          # Phase 1 results
│   ├── PHASE_2_QUICK_WIN_COMPLETE.md   # Phase 2 results
│   ├── QUICK_UPGRADE_GUIDE.md          # Implementation guide
│   ├── CODE_PATTERNS_COMPARISON.md     # Code examples
│   ├── RESEARCH_INTEGRATION_PLAN.md    # Scrapy integration
│   └── TECH_STACK_BEST_PRACTICES.md    # Tech validation
│
├── Planning & Analysis
│   ├── INSPECTION_SUMMARY.md           # vNext SDK review
│   ├── SDK_COMPARISON_AND_UPGRADES.md  # Detailed comparison
│   ├── COMPLETE_UPGRADE_ROADMAP.md     # All phases
│   └── UPGRADE_CHECKLIST.md            # Task checklist
│
├── Methodology
│   ├── BILLY_WALTERS_METHODOLOGY.md    # Core principles
│   ├── CORE_IMPLEMENTATION_SUMMARY.md  # Technical details
│   └── BACKTEST_GUIDE.md               # Backtesting
│
├── Domain-Specific
│   ├── nfl/
│   │   └── README.md                   # NFL features
│   ├── espn_cfb/                       # 6 CFB guides
│   ├── massey/                         # 12 Massey guides
│   └── weather/                        # 2 weather guides
│
└── archive/                            # Historical docs
    └── *.md                            # 8 archived guides
```

**Suggested Reorganization:** See "docs/ Cleanup Plan" below

---

## 💡 Examples: `examples/`

**Purpose:** Working code examples

```
examples/
├── complete_research_demo.py        # Phase 1 + Phase 2 demo
├── quick_wins_demo.py               # Phase 1 demo
├── test_scrapy_bridge.py            # ScrapyBridge demo
└── complete_workflow_example.py     # Original workflow
```

**Run Examples:**
```bash
# Phase 1 + Phase 2 demo
uv run python examples/complete_research_demo.py

# Test ScrapyBridge with your data
uv run python examples/test_scrapy_bridge.py
```

---

## ⚙️ Configuration Files

```
Root Directory:
├── pyproject.toml           # Project metadata, dependencies
├── scrapy.cfg               # Scrapy project config
├── pytest.ini               # Pytest configuration
├── .gitignore               # Git ignore patterns
├── .env.template (old)      # Original template
├── env.template.new         # NEW: Comprehensive template
├── .env                     # Your config (create from template)
├── README.md                # Project README
├── CLAUDE.md                # Command reference (updated)
└── requirements*.txt        # Legacy requirements (use pyproject.toml)
```

**Main Config:** `walters_analyzer/config.py`
- Loads from .env automatically
- Provides defaults for all settings
- Type-safe configuration access

---

## 🎯 Data Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                     Data Sources                            │
└────────────────────────────────────────────────────────────┘
   │
   ├─→ ESPN (Games, Injuries) → Scrapy Spider → JSONL + Parquet
   ├─→ Massey (CFB Ratings) → Scrapy Spider → CSV + Parquet
   ├─→ Overtime.ag (Odds) → Scrapy Spider → JSONL + Parquet
   ├─→ AccuWeather (Weather) → HTTP Client → JSONL + Parquet
   ├─→ ProFootballDoc (Medical) → HTTP Client → Cache
   └─→ News API (Breaking) → HTTP Client → Cache
   │
   ▼
┌────────────────────────────────────────────────────────────┐
│                  Phase 1: Foundation                        │
│  - HTTP Client (connection pooling)                        │
│  - Caching (90% cost reduction)                            │
│  - Models (unified data structures)                        │
└────────────────────────────────────────────────────────────┘
   │
   ▼
┌────────────────────────────────────────────────────────────┐
│                  Phase 2: Research                          │
│  - ScrapyBridge (loads Scrapy data)                        │
│  - ResearchEngine (multi-source coordinator)               │
└────────────────────────────────────────────────────────────┘
   │
   ▼
┌────────────────────────────────────────────────────────────┐
│              Billy Walters Analysis Engine                  │
│  - Power Ratings (exponential weighted)                    │
│  - S/W/E Factors (situational/weather/emotional)           │
│  - Key Numbers (3, 7, 14 in NFL)                          │
│  - Bet Sizing (Star System + Kelly)                       │
└────────────────────────────────────────────────────────────┘
   │
   ▼
┌────────────────────────────────────────────────────────────┐
│                    Output & Tracking                        │
│  - BetRecommendation (sized bets)                          │
│  - CLV Tracking (closing line value)                       │
│  - Performance Reports                                     │
└────────────────────────────────────────────────────────────┘
```

---

## 📂 Directory Purpose Guide

### `/walters_analyzer/` - Core Package
**What:** Main Python package  
**When to modify:** Adding new analysis features  
**Key files:** `analyzer.py`, `power_ratings.py`, `bet_sizing.py`

### `/scrapers/` - Web Scraping
**What:** Scrapy spiders and pipelines  
**When to modify:** Adding new data sources, updating scrapers  
**Key files:** `spiders/*.py`, `pipelines.py`

### `/data/` - Data Storage
**What:** All scraped and generated data  
**When to modify:** Never (auto-generated)  
**Size:** Can grow large (JSONL + Parquet)  
**Backup:** Recommended for `power_ratings/`, `team_mappings/`

### `/scripts/` - Automation
**What:** Helper scripts and automation  
**When to modify:** Customizing workflows  
**Key files:** `collect_nfl_schedule.py`, `update_power_ratings_from_games.py`

### `/tests/` - Test Suite
**What:** Unit and integration tests  
**When to modify:** Adding new features (write tests!)  
**Run:** `pytest tests/ -v`

### `/docs/` - Documentation
**What:** All project documentation (50+ files)  
**When to modify:** Adding features, updating guides  
**Index:** `docs/README.md`

### `/examples/` - Code Examples
**What:** Working example scripts  
**When to modify:** Adding new examples for features  
**Run:** `uv run python examples/<script>.py`

### `/cards/` - Betting Cards
**What:** Weekly betting card JSON files  
**When to modify:** Each week (new card)  
**Format:** See `wk-card-2025-10-31.json` for structure

### `/commands/` - JSON Commands
**What:** Pre-defined commands in JSON format  
**When to modify:** Adding new commands  
**Usage:** Quick copy-paste for common tasks

### `/snapshots/` - Debug Output
**What:** Scrapy screenshots, debug files  
**When to modify:** Never (auto-generated)  
**Purpose:** Troubleshooting scraper issues

---

## 🔧 Configuration Files

### `pyproject.toml` (Primary)
**Purpose:** Project metadata and dependencies  
**Tool:** uv (modern Python package manager)  
**Key sections:**
- `[project]` - Name, version, description
- `dependencies` - Required packages
- `[project.scripts]` - CLI entry points
- `[project.optional-dependencies]` - Optional extras

### `.env` (Secrets & Config)
**Purpose:** Environment variables and API keys  
**Template:** `env.template.new`  
**Security:** ⚠️ NEVER commit (gitignored)  
**Key settings:**
- API keys (AccuWeather, News API, etc.)
- Bankroll settings
- Feature flags
- Cache TTLs

### `scrapy.cfg`
**Purpose:** Scrapy project configuration  
**Settings:** Points to `scrapers.overtime_live.settings`  
**Rarely modified:** Only if changing Scrapy structure

### `pytest.ini`
**Purpose:** Test configuration  
**Settings:** Test paths, markers, options

---

## 🗂️ File Naming Conventions

### Scraped Data Files
```
{type}-{YYYYMMDD}-{HHMMSS}.{format}

Examples:
- injuries-20251101-143052.jsonl
- massey-games-20251101-104817.parquet
- weather-20251101-095726.jsonl
```

**Benefits:**
- Chronological sorting
- Easy to find latest
- No overwriting
- Timestamp audit trail

### NFL Schedule Files
```
nfl_week{N}_{YYYY}_{timestamp}.{format}

Examples:
- nfl_week9_2025_1730494800.json
- nfl_week9_2025_1730494800.jsonl
```

### Code Files
```
{descriptive_name}.py

Examples:
- power_ratings.py (not ratings.py)
- situational_factors.py (not swe.py)
- espn_injury_spider.py (not injury.py)
```

**Principle:** Descriptive over brief

---

## 🧹 Cleanup Recommendations

### Files to Keep
✅ All Python modules  
✅ Configuration files  
✅ Documentation  
✅ Tests  
✅ Examples  
✅ Team mappings (`data/team_mappings/`)  
✅ Power ratings (`data/power_ratings/team_ratings.json`)  

### Files to Archive/Delete (Optional)
⚠️ Old scraped data (> 30 days)  
⚠️ Debug snapshots (after issues resolved)  
⚠️ Backup files (*.backup after verified)  
⚠️ Update logs (scripts/update_log.txt after reviewing)  

### Files Already Gitignored
- `.env` - Secrets
- `.venv/` - Virtual environment
- `__pycache__/` - Python cache
- `.pytest_cache/` - Test cache
- `data/**/*.jsonl` - Large data files
- `data/**/*.parquet` - Compressed data
- `*.log` - Log files

---

## 🎯 Best Practices

### Adding New Features
1. **Models:** Add to `walters_analyzer/core/models.py`
2. **HTTP calls:** Use `async_get()` from `core.http_client`
3. **Caching:** Add decorator from `core.cache`
4. **Config:** Add to `config.py` and `env.template.new`
5. **Tests:** Write tests in `tests/`
6. **Docs:** Update relevant doc in `docs/`
7. **Examples:** Add example in `examples/`

### Naming Conventions
- **Modules:** `lowercase_with_underscores.py`
- **Classes:** `PascalCase`
- **Functions:** `lowercase_with_underscores`
- **Constants:** `UPPERCASE_WITH_UNDERSCORES`
- **Private:** `_leading_underscore`

### Imports
```python
# Standard library
import os
from pathlib import Path
from typing import Dict, List

# Third-party
import scrapy
from rich.console import Console

# Local - absolute imports
from walters_analyzer.core import async_get, cache_weather_data
from walters_analyzer.research import ResearchEngine

# Local - relative imports (within package)
from ..core.models import TeamRating
from .scrapy_bridge import ScrapyBridge
```

### Documentation
- **Code:** Docstrings for all public functions/classes
- **Types:** Type hints throughout
- **Examples:** Include usage examples in docstrings
- **Updates:** Update docs when changing functionality

---

## 🔐 Security Best Practices

### API Keys
1. **Never commit** API keys or credentials
2. **Use .env** for all secrets
3. **Rotate keys** periodically
4. **Use separate keys** for dev/prod

### Credentials
1. **Strong passwords** for betting sites
2. **Two-factor** authentication where available
3. **Separate accounts** for testing

### Data Privacy
1. **Don't commit** personal betting data
2. **Gitignore** sensitive files
3. **Anonymize** data in examples/docs

---

## 📊 Monitoring & Maintenance

### Weekly Checklist
- [ ] Update power ratings (Monday after games)
- [ ] Scrape injuries (Monday/Tuesday)
- [ ] Fetch weather (Wednesday for weekend)
- [ ] Verify data quality (check for anomalies)
- [ ] Review CLV performance

### Monthly Checklist
- [ ] Review cache hit rates (optimize TTLs)
- [ ] Check API usage (stay within limits)
- [ ] Archive old data (> 30 days)
- [ ] Update team mappings (roster changes)
- [ ] Review power rating trends

### Seasonal Checklist
- [ ] Backfill season data (after playoffs)
- [ ] Reset power ratings (new season)
- [ ] Update team mappings (roster/coaching changes)
- [ ] Review methodology (incorporate learnings)
- [ ] Archive last season's data

---

## 🚀 Deployment Checklist

### New Environment Setup
1. Clone repository
2. Copy `env.template.new` → `.env`
3. Add API keys to `.env`
4. Run `uv sync`
5. Run `playwright install chromium`
6. Test: `pytest tests/`
7. Backfill data: `uv run walters-analyzer backfill-nfl-season`

### Automation Setup (Windows)
1. Follow `scripts/TASK_SCHEDULER_SETUP.md`
2. Test scripts manually first
3. Create scheduled task
4. Monitor `scripts/update_log.txt`

---

## 📞 Getting Help

### Documentation
1. Start with `docs/README.md` (index)
2. Check `docs/QUICK_REFERENCE.md` (API reference)
3. Review relevant domain guide (`nfl/`, `massey/`, etc.)

### Debugging
1. Enable debug mode: `DEBUG=true` in `.env`
2. Check logs: `scripts/update_log.txt`
3. Run tests: `pytest tests/ -v`
4. View config: `uv run python -c "from walters_analyzer.config import get_config; print(get_config().get_summary())"`

### Common Issues
- **Import errors:** Run `uv sync`
- **API errors:** Check `.env` keys
- **Scraper fails:** Check `snapshots/` for screenshots
- **Stale data:** Clear cache or re-scrape

---

*Complete structure guide for Billy Walters Sports Analyzer v2.0*

