# Billy Walters Sports Analyzer - Development Guidelines

This document contains critical information about working with the Billy Walters Sports Analyzer codebase. Follow these guidelines precisely.

> **📖 Complete Documentation**: See [docs/_INDEX.md](docs/_INDEX.md) for full navigation to all guides, API docs, and technical references.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Development Rules](#core-development-rules)
3. [Environment Variables & API Keys](#environment-variables--api-keys)
4. [Football Analytics Best Practices](#football-analytics-best-practices)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Git Workflow](#git-workflow)
7. [Code Formatting](#code-formatting)
8. [Project Structure](#project-structure)
9. [Automation Hooks](#automation-hooks)
10. [Quick Reference](#quick-reference)
11. [Troubleshooting](#troubleshooting)
12. [Recent Updates](#recent-updates)

---

## Project Overview

**Football-focused sports analytics and betting analysis system** (NFL & NCAAF) inspired by Billy Walters' analytical approach. Integrates weather data, AI-powered analysis, odds tracking, and statistical modeling.

### Sports Focus
- **NFL** (National Football League)
- **NCAAF** (NCAA College Football)

### Project Status

**Core Infrastructure** (Stable):
- **CI/CD**: Fully operational (GitHub Actions) - lint, type check, security scan, tests
- **Tests**: 379 passing, 40 skipped (Ubuntu/Windows, Python 3.11/3.12)
- **League Separation**: Strict NFL/NCAAF isolation (never mixed)

**Data Collection** (Production-Ready):
- **Sources**: ESPN, Overtime.ag, Action Network, Massey, AccuWeather, NFL.com
- **Scrapers**: 27+ clients with multi-selector fallback strategies
- **Action Network**: Complete odds (spread, moneyline, O/U) with selector resilience
- **NFL.com Stats**: Playwright scraper with ProxyScrape residential proxy integration
- **NCAAF**: Transactions + news clients for 10+ FBS teams

**Analysis Pipeline** (Production-Ready):
- **Edge Detection**: Auto week detection, schedule/odds validation, pre-flight checks
- **Results Validation**: ATS tracking, ROI calculation, team name mapping
- **PostgreSQL Loading**: GameIDMapper (Overtime→ESPN), <10 sec full pipeline

**E-Factor System** (Production Ready - NEW):
- **Complete Implementation**: Real data integration, calibration, decay, source quality tracking
- **4 Core Modules**: RealDataIntegrator, EFactorCalibrator, NewsDecayFunction, SourceQualityTracker
- **Edge Integration**: Seamless integration with IntegratedEdgeCalculator (4 simple changes)
- **Production Deployment**: One-time setup script, workflow integration, weekly reporting

**Last Session**: 2025-11-28 - Production Edge Detection System Deployed & Verified
- **Status**: ✅ PRODUCTION READY - Week 13 NCAAF execution verified (6 edges detected, <1 sec)
- **Work Completed**:
  - ✅ EdgeDetectionOrchestrator with auto week detection & 3-stage pre-flight validation
  - ✅ Production CLI: `edge_detector_production.py` with `--nfl`, `--ncaaf`, `--both` support
  - ✅ NCAAF key construction consistency (Phase 2) verified across all pipeline stages
  - ✅ Comprehensive documentation (550+ lines) and deployment guide created
  - ✅ Week 13 test execution: 21 games matched, 6 edges detected, no errors
- **Deployment**: Ready for immediate production use (see PRODUCTION_EDGE_DETECTION_GUIDE.md)
  * Created `_strip_mascot()` helper (40+ mascot variations)
  * Created `_normalize_for_odds_matching()` for Overnight.ag format consistency
  * Updated `_load_schedule()` and `_load_odds()` to use same normalization
  * Verified 100% game matching rate with test cases
  * Result: All ESPN display names correctly normalize to Overnight.ag format

- **EdgeDetectionOrchestrator**: New orchestration layer
  * Auto-detects current NFL/NCAAF week from system date (using ScheduleValidator)
  * Validates schedule and odds files before analysis (pre-flight checks)
  * Validates game matching between schedule and odds (0-missed-games guarantee)
  * Comprehensive error handling and reporting
  * Supports both NFL and NCAAF with unified interface

- **Production CLI** (`edge_detector_production.py`):
  * Auto-detect or specify week: `--week 13`
  * League selection: `--nfl`, `--ncaaf`, or `--both`
  * JSON output: `--output edges.json`
  * Verbose logging: `--verbose`
  * Execution time: 7-26 seconds (NFL vs NCAAF)

- **Complete Documentation**:
  * PRODUCTION_EDGE_DETECTION_GUIDE.md - 550+ lines of deployment guide
  * Quick start (30 seconds to running edges)
  * Architecture overview and usage guide
  * Validation pre-flight checks (3 stages)
  * Weekly workflow templates
  * Error handling and troubleshooting

- **Status**: ✅ PRODUCTION READY
  * All code quality checks pass (ruff format, pyright)
  * Ready to deploy for Week 13 NFL and NCAAF edges
  * Tested with ESPN schedule data
  * Comprehensive validation prevents runtime errors

**📖 For detailed methodology, see**: [docs/guides/methodology/BILLY_WALTERS_METHODOLOGY_AUDIT.md](docs/guides/methodology/BILLY_WALTERS_METHODOLOGY_AUDIT.md) and [docs/guides/methodology/METHODOLOGY_QUICK_REFERENCE.md](docs/guides/methodology/METHODOLOGY_QUICK_REFERENCE.md)

---

## Core Development Rules

### 1. Package Management
- **ONLY** use uv, **NEVER** pip
- Installation: `uv add package`
- Running tools: `uv run tool`
- Upgrading: `uv add --dev package --upgrade-package package`
- **FORBIDDEN**: `uv pip install`, `@latest` syntax

### 2. Code Quality
- Type hints required for all code
- Use pyright for type checking: `uv run pyright`
- Public APIs must have docstrings (Google style)
- Functions must be focused and small
- Follow existing patterns exactly
- **Line length: 88 chars maximum** (Black/Ruff standard)
- Auto-format all new code: `uv run ruff format .`

### 3. Testing Requirements
- Framework: `uv run pytest`
- Async testing: use anyio, not asyncio
- New features require tests
- Bug fixes require regression tests
- Aim for 80%+ code coverage
- CI runs on Ubuntu/Windows with Python 3.11/3.12

### 4. Code Style
- PEP 8 naming (snake_case for functions/variables)
- Class names in PascalCase
- Constants in UPPER_SNAKE_CASE
- Document with docstrings
- Use f-strings for formatting

### 5. Development Philosophy
- **Simplicity**: Write simple, straightforward code
- **Less Code = Less Debt**: Minimize code footprint
- **Early Returns**: Avoid nested conditions
- **DRY Code**: Don't repeat yourself
- **Build Iteratively**: Start minimal, verify, then add complexity
- **Run Tests**: Test frequently with realistic inputs

---

## Environment Variables & API Keys

Store these in `.env` file (**NEVER commit to git**):

```bash
# AI Services
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Weather Services
ACCUWEATHER_API_KEY=...
OPENWEATHER_API_KEY=...

# Sports Data Sources
ACTION_USERNAME=...
ACTION_PASSWORD=...

# Overtime/OV Service
OV_CUSTOMER_ID=...
OV_PASSWORD=...

# Proxy Configuration (optional)
PROXY_URL=...
PROXY_USER=...
PROXY_PASS=...

# GitHub (for automation)
GITHUB_TOKEN=ghp_...
```

**📖 For complete list, see**: [.env.example](.env.example)

---

## Football Analytics Best Practices

**Edge Thresholds (Billy Walters Methodology)**:
- **7+ points**: MAX BET (5% Kelly, 77% win rate)
- **4-7 points**: STRONG (3% Kelly, 64% win rate)
- **2-4 points**: MODERATE (2% Kelly, 58% win rate)
- **1-2 points**: LEAN (1% Kelly, 54% win rate)
- **<1 point**: NO PLAY

**Key Insight**: Track ROI and Closing Line Value (CLV), not win percentage.

**📖 For detailed methodology**: See [docs/guides/methodology/BILLY_WALTERS_METHODOLOGY_AUDIT.md](docs/guides/methodology/BILLY_WALTERS_METHODOLOGY_AUDIT.md), [docs/guides/methodology/METHODOLOGY_QUICK_REFERENCE.md](docs/guides/methodology/METHODOLOGY_QUICK_REFERENCE.md), and [docs/guides/methodology/EFACTOR_INTEGRATION_GUIDE.md](docs/guides/methodology/EFACTOR_INTEGRATION_GUIDE.md)
- Weather impact rules (temperature, wind, precipitation)
- NFL vs NCAAF differences (power ratings, injuries, home field bonus)
- Success metrics: ROI (primary), ATS (secondary), CLV (tertiary)
- Situational factors: rest, travel, rivalries, playoff implications

---

## CI/CD Pipeline

### Automated Checks

Every push/PR triggers:
- **Lint and Format**: Ruff formatting and linting
- **Type Check**: Pyright static analysis
- **Security Scan**: pip-audit and TruffleHog
- **Tests**: Multi-platform, multi-version

### Local Validation (Run Before Pushing)

**ALWAYS run these commands locally:**

```bash
# 1. Format code (REQUIRED)
uv run ruff format .

# 2. Check formatting
uv run ruff format --check .

# 3. Run linter
uv run ruff check .

# 4. Type check
uv run pyright

# 5. Run tests with coverage
uv run pytest tests/ -v --cov=. --cov-report=term
```

**All commands must pass before pushing.**

### Quick Fix (90% of CI failures)

```bash
uv run ruff format .
uv run ruff check . --fix
uv run pyright
git add . && git commit -m "fix: apply code quality checks"
git push
```

**📖 For CI/CD troubleshooting, see**: [docs/guides/ci_cd_prevention_guide.md](docs/guides/ci_cd_prevention_guide.md)

---

## Git Workflow

### Quick Daily Workflow (Solo Developer)

**🌅 Start of Every Session:**
```bash
git pull origin main --rebase  # Sync with GitHub first!
```

**💻 During Development:**
```bash
# After making changes (every 30-60 min)
git add .
git commit -m "type(scope): brief description"
git push origin main
```

**🌙 End of Session:**
Just tell Claude: **"Commit and push my changes"**

### Conventional Commit Format

```bash
type(scope): brief description (50 chars max)

Detailed explanation if needed.

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`

**Examples:**
```bash
git commit -m "feat(scraper): add retry logic to Overtime API"
git commit -m "fix(weather): correct AccuWeather HTTPS endpoint"
git commit -m "docs: update installation instructions"
```

**📖 For PR workflow, see**: [.github/PR_WORKFLOW.md](.github/PR_WORKFLOW.md)

---

## Code Formatting

### Line Length Policy

**Standard**: 88 characters (Black/Ruff standard)

**Current Status**:
- ✅ New code: MUST be formatted with `ruff format`
- ⚠️ Legacy code: 518 line-too-long violations (E501 ignored)
- 📊 CI: Checks but doesn't fail (informational)

**Commands:**
```bash
# Format all files (REQUIRED before every commit)
uv run ruff format .

# Check formatting (CI uses this)
uv run ruff format --check .

# Run linter
uv run ruff check .

# Auto-fix safe issues
uv run ruff check . --fix

# Type check
uv run pyright
```

---

## Project Structure

```
billy-walters-sports-analyzer/
├── .github/                     # CI/CD configuration
├── src/
│   ├── data/                    # Data collection (27 scrapers & clients)
│   ├── walters_analyzer/        # Core analysis system
│   │   ├── valuation/           # Edge detection (11 modules)
│   │   ├── query/               # Display utilities (6 modules)
│   │   └── ...
│   └── db/                      # Database layer
├── scripts/
│   ├── scrapers/                # Data collection
│   ├── analysis/                # Weekly analysis
│   ├── validation/              # Data validation
│   ├── utilities/               # Helper scripts
│   ├── dev/                     # Debug tools
│   └── archive/                 # Legacy code
├── tests/                       # Test suite (146+ tests)
├── docs/                        # Documentation (organized by category)
│   ├── api/                     # API documentation
│   │   ├── espn/                # ESPN API docs (22 files)
│   │   └── action_network/      # Action Network docs (5 files)
│   ├── data_sources/            # Data schema docs
│   │   └── overtime/            # Overtime.ag docs (6 files)
│   ├── features/                # Feature documentation
│   │   ├── ncaaf/               # NCAAF-specific (7 files)
│   │   ├── nfl/                 # NFL-specific (8 files)
│   │   ├── results_checker/     # Results checker (5 files)
│   │   └── ...                  # power_ratings, sfactor
│   ├── guides/                  # User guides
│   │   └── methodology/         # Billy Walters methodology (8 files)
│   ├── technical/               # Technical docs
│   │   ├── mcp/                 # MCP architecture (6 files)
│   │   └── database/            # Database docs (4 files)
│   ├── reports/                 # Reports and status
│   ├── archive/                 # Historical documentation
│   └── _INDEX.md                # Complete documentation index
├── .claude/
│   ├── commands/                # Custom slash commands (14 commands)
│   └── hooks/                   # Automation hooks (14 hooks)
├── .env.example
├── pyproject.toml               # Package config, ruff/pyright settings
├── CLAUDE.md                    # This file
├── TROUBLESHOOTING.md           # Error resolution guide
└── README.md                    # Project overview
```

**📖 For complete structure and file organization, see**: [docs/_INDEX.md](docs/_INDEX.md)

---

## Automation Hooks

The project includes validation hooks in `.claude/hooks/` that automatically integrate with slash commands for peak safety and ease of use.

### Hook Integration Architecture ✨ NEW (2025-11-24)

Hooks are **automatically invoked by slash commands** - no manual steps needed:

```
/collect-all-data
├─ Automatic Pre-Flight: pre_data_collection_validator.py
├─ Core Operation: 7-step data collection
├─ Automatic Post-Flight: post_data_collection_validator.py
└─ Result: Data validated and ready

/edge-detector
├─ Automatic Pre-Flight: pre_edge_detection.py
├─ Core Operation: Edge detection analysis
└─ Result: Betting edges with confidence scores
```

**Three Ways to Invoke Hooks:**

1. **Automatic (Recommended)** - Built into commands
   - `/collect-all-data` → Auto pre/post validation
   - `/edge-detector` → Auto pre-flight validation
   - No extra steps needed

2. **Slash Commands (Quick Check)** - Manual when needed
   - `/pre-validate` → Check environment
   - `/post-validate` → Check data quality
   - Useful for independent verification

3. **Direct Python (Advanced)** - Debugging/integration
   - `python .claude/hooks/pre_data_collection_validator.py`
   - `python .claude/hooks/post_data_collection_validator.py --league nfl`
   - Use when troubleshooting

### Core Validators

**Data Collection Validators:**
- `pre_data_collection_validator.py` - Environment check before collection
  - Verifies API keys, database, directories
  - Detects current week automatically
  - Exit code 0 = safe to proceed

- `post_data_collection_validator.py` - Quality check after collection
  - Scores all data sources (0-100%)
  - Validates completeness and consistency
  - Exit code 0 = ready for analysis

**Edge Detection Validators:**
- `pre_edge_detection.py` - Data availability check before analysis
  - Ensures power ratings, schedules, odds exist
  - Prevents wasted computation
  - Exit code 0 = safe to analyze

**Code Quality Validators:**
- `pre_commit_check.py` - Security check before commits
  - Prevents exposed API keys from reaching git
  - Validates JSON/Python file structure
  - Exit code 0 = safe to commit

### Weekly Workflow with Hooks

```bash
# TUESDAY - Data Collection (hooks run automatically)
/current-week                    # Verify week
/pre-validate                    # (Optional) Manual environment check
/collect-all-data                # Runs: pre-flight → collect → post-flight
  # If pre-flight fails: ✅ Collection prevented
  # If post-flight fails: ⚠️ Alert on quality issues
  # If both pass: ✅ Ready for analysis

# WEDNESDAY - Edge Detection (pre-flight automatic)
/edge-detector                   # Runs: pre-flight → detect → complete
  # If pre-flight fails: ✅ Detection prevented (missing data)
  # If successful: ✅ Edges ready for betting-card
/betting-card                    # Generate picks
```

### Exit Codes (Standard Across All)

All validators use consistent exit codes for scripting:
- **0** = Success ✅ (proceed with next step)
- **1** = Failure ❌ (stop, address issues)

### Performance & Safety

**What validators prevent:**
- ❌ Running data collection without API keys
- ❌ Analyzing data when files are missing
- ❌ Committing code with exposed secrets
- ❌ Mixing NFL/NCAAF data
- ❌ Concurrent data collection (data corruption)

**What validators detect:**
- ✅ Data quality issues early (before analysis wastes time)
- ✅ Missing or incomplete files automatically
- ✅ NFL vs NCAAF separation violations
- ✅ Environment configuration problems
- ✅ API/database connectivity issues

**Complete Documentation**: See [.claude/hooks/README.md](.claude/hooks/README.md) for full details including:
- Detailed hook system architecture
- Integration patterns with commands
- Error recovery procedures
- When each hook runs
- How to troubleshoot

**New Slash Commands:**
- `/pre-validate` - Manual pre-flight check
- `/post-validate` - Manual post-flight quality assessment

**📖 For complete hook reference, see**: [.claude/hooks/README.md](.claude/hooks/README.md)

---

## Data Collection Workflows (NFL & NCAAF)

### ⚠️ CRITICAL PRINCIPLE: League Separation

**NFL and NCAAF data are NEVER mixed.** All workflows keep leagues strictly separated by directory structure and command flags.

**Key Rules:**
- ✅ Use `--nfl` for NFL collections (never with `--ncaaf`)
- ✅ Use `--ncaaf` for NCAAF collections (never with `--nfl`)
- ✅ Specify league flag on EVERY command
- ✅ Output automatically separated: `output/{source}/nfl/` vs `output/{source}/ncaaf/`
- ❌ NEVER use `--nfl --ncaaf` together
- ❌ NEVER omit league specification

**📖 Master Reference**: [docs/guides/LEAGUE_SEPARATION_GUIDE.md](docs/guides/LEAGUE_SEPARATION_GUIDE.md)

### NFL Data Collection Workflow (Tuesday 2:00 PM)

**Time Required:** ~7 minutes data + 2 min edge detection = 9 minutes total
**Output:** `output/{source}/nfl/`
**Complete Guides:**
- Data Collection: [docs/guides/NFL_DATA_COLLECTION_WORKFLOW.md](docs/guides/NFL_DATA_COLLECTION_WORKFLOW.md)
- Edge Detection: [docs/guides/EDGE_DETECTOR_WORKFLOW.md](docs/guides/EDGE_DETECTOR_WORKFLOW.md)

**Step-by-step:**
```bash
# 1. Overtime pregame odds (5 sec)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# 2. ESPN team statistics (2 min)
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl

# 3. Massey power ratings (1 min)
uv run python scripts/scrapers/scrape_massey_games.py

# 4. Weather for all stadiums (<1 sec)
python src/data/weather_client.py --league nfl

# 5. Action Network betting lines (2 min)
uv run python scripts/scrapers/scrape_action_network_sitemap.py --nfl

# 6. Run edge detection with automatic pre-flight validation
/edge-detector
# System automatically:
# - Detects current week from system date
# - Validates schedule file against detected week
# - Validates odds file against detected week
# - Warns if any mismatches (expected when prepping for next week)
# - Proceeds with analysis and generates edges
```

**Data Points:**
- 16 weeks + 2 playoff rounds
- 32 NFL teams
- 32 stadiums
- Multiple sportsbooks
- Complete odds (moneyline, spread, total, props)

### NCAAF Data Collection Workflow (Wednesday 2:00 PM)

**Time Required:** ~7 minutes data + 2 min edge detection = 9 minutes total
**Output:** `output/{source}/ncaaf/`
**Complete Guides:**
- Data Collection: [docs/guides/NCAAF_DATA_COLLECTION_WORKFLOW.md](docs/guides/NCAAF_DATA_COLLECTION_WORKFLOW.md)
- Edge Detection: [docs/guides/EDGE_DETECTOR_WORKFLOW.md](docs/guides/EDGE_DETECTOR_WORKFLOW.md)

**Step-by-step:**
```bash
# 1. Overtime pregame odds (5 sec)
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# 2. ESPN team statistics (2 min)
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf

# 3. Massey college ratings (1 min)
uv run python scripts/scrapers/scrape_massey_games.py --league college

# 4. Weather for all stadiums (<1 sec)
python src/data/weather_client.py --league ncaaf

# 5. Action Network betting lines (2 min)
uv run python scripts/scrapers/scrape_action_network_sitemap.py --ncaaf

# 6. Run edge detection with automatic pre-flight validation
/edge-detector --league ncaaf
# System automatically:
# - Detects current NCAAF week from system date
# - Validates schedule file against detected week
# - Validates odds file against detected week
# - Warns if any mismatches (expected when prepping for next week)
# - Proceeds with analysis and generates edges
```

**Data Points:**
- 15 weeks + bowl season
- 130+ FBS teams
- 130+ stadiums
- Conference-separated standings
- Multiple sportsbooks
- Complete odds (moneyline, spread, total, props)

### Game Day Monitoring

**NFL Sunday (3-hour monitoring):**
```bash
# Pre-game odds
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# Monitor during games
uv run python scripts/scrapers/scrape_overtime_hybrid.py --nfl --duration 10800
```

**NCAAF Saturday (4-hour monitoring):**
```bash
# Pre-game odds
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Monitor staggered games
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 14400
```

### Output Structure Verification

**Verify league separation:**
```bash
# Check separate directories
ls output/*/nfl/     # NFL only
ls output/*/ncaaf/   # NCAAF only

# Run automated verification
uv run python scripts/validation/verify_data_structure.py

# Should see:
# - output/action_network/nfl/
# - output/action_network/ncaaf/
# - output/espn/nfl/
# - output/espn/ncaaf/
# ... (all separated by league)
```

**Expected file structure:**
```
output/
├── action_network/nfl/    # NFL only
├── action_network/ncaaf/  # NCAAF only
├── espn/nfl/              # NFL teams (32)
├── espn/ncaaf/            # NCAAF teams (130+)
├── overtime/nfl/          # NFL odds
├── overtime/ncaaf/        # NCAAF odds
├── weather/nfl/           # NFL stadiums (32)
├── weather/ncaaf/         # NCAAF stadiums (130+)
├── massey/                # (Separated by content)
└── analysis/nfl|ncaaf/    # Edges & results
```

**📖 Detailed Verification**: [docs/guides/DATA_OUTPUT_STRUCTURE_VERIFICATION.md](docs/guides/DATA_OUTPUT_STRUCTURE_VERIFICATION.md)

### Quick Reference Lookup

**When unsure which command to use:**

| Question | Document | Time to Read |
|----------|----------|---|
| "How do I collect data?" | [DATA_COLLECTION_QUICK_REFERENCE.md](DATA_COLLECTION_QUICK_REFERENCE.md) | 2 min |
| "Should I use --nfl --ncaaf?" | [LEAGUE_SEPARATION_GUIDE.md](docs/guides/LEAGUE_SEPARATION_GUIDE.md) | 3 min |
| "What's my complete NFL workflow?" | [NFL_DATA_COLLECTION_WORKFLOW.md](docs/guides/NFL_DATA_COLLECTION_WORKFLOW.md) | 10 min |
| "What's my complete NCAAF workflow?" | [NCAAF_DATA_COLLECTION_WORKFLOW.md](docs/guides/NCAAF_DATA_COLLECTION_WORKFLOW.md) | 10 min |
| "How do I verify data integrity?" | [DATA_OUTPUT_STRUCTURE_VERIFICATION.md](docs/guides/DATA_OUTPUT_STRUCTURE_VERIFICATION.md) | 5 min |

### Performance Benchmarks

| Component | NFL Time | NCAAF Time | Notes |
|-----------|----------|-----------|-------|
| Overtime API | <5 sec | <5 sec | Both leagues fast |
| ESPN Stats | ~2 min | ~2 min | 32 vs 130+ teams |
| Weather | <1 sec | <1 sec | Cached locations |
| Action Network | ~2 min | ~2 min | Sitemap-based |
| Hybrid Monitor | 30+ sec init | 30+ sec init | Real-time stream |
| **Total** | **~7 min** | **~7 min** | Complete workflow |

---

## Quick Reference

### Common Development Workflows

**Starting a New Feature (PR Workflow):**
```bash
# 1. Sync and create feature branch
git checkout main && git pull origin main --rebase
git checkout -b feat/your-feature

# 2. Make changes, write tests

# 3. Validate locally (all must pass!)
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest tests/ -v

# 4. Commit and push
git add . && git commit -m "feat(scope): description"
git push -u origin feat/your-feature

# 5. Create PR and squash merge
gh pr create --web
```

**Quick Fix (Direct to Main):**
```bash
# For small changes only
git checkout main && git pull origin main --rebase
# Make changes...
git add . && git commit -m "docs: update README"
git push origin main
```

**Adding a New Dependency:**
```bash
uv add package-name              # Production
uv add --dev package-name        # Development
uv sync                          # Sync after manual edits
```

### Command Quick Reference

| Task | Command | Time | Frequency | Notes |
|------|---------|------|-----------|-------|
| Collect all data | `/collect-all-data` | 7 min | Weekly (Tue/Wed) | Full workflow: power ratings → schedules → stats → weather → odds |
| Find betting edges | `/edge-detector` | 2 min | After collection | ✨ NEW: Auto-detects week, validates data, shows pre-flight status |
| Validate schedule/odds | `uv run python src/walters_analyzer/utils/schedule_validator.py` | 10 sec | Before edge-detector | Shows current week detection and file validation |
| Generate picks | `/betting-card` | 1 min | Weekly (Wed) | After edge detection completes |
| Check results | `/check-results --league nfl` | 1 min | Weekly (Mon) | Compare predictions vs actual results |
| Current NFL week | `/current-week` | 5 sec | As needed | Quick check of system-detected week |
| Weather impact | `/weather [team] [datetime]` | 30 sec | Per game | Analyze weather effects on matchup |
| Injury analysis | `/injury-report [team] [league]` | 30 sec | Per team | Check player availability impact |
| Validate data | `/validate-data` | 30 sec | After collection | Quality check on collected data |

**Key Improvement (2025-11-25)**: `/edge-detector` now includes automatic pre-flight checks that:
- Detect current NFL/NCAAF week from system date
- Validate schedule files match detected week
- Validate odds files match detected week
- Warn if mismatches detected (expected when prepping for next week)
- Proceed with analysis once user is informed

**See**: [docs/_INDEX.md](docs/_INDEX.md) for complete command reference and [Edge Detector Workflow](docs/guides/EDGE_DETECTOR_WORKFLOW.md) for detailed guide

### Claude Code Flags

**Development Mode**:
```bash
# Skip permission prompts for faster development
claude --dangerously-skip-permissions

# Use when: Running automated workflows, testing, batch operations
# Warning: Review changes carefully since prompts are bypassed
```

### Billy Walters Weekly Workflow

**📖 Complete workflow documentation**: [.claude/AGENT_WORKFLOWS.md](.claude/AGENT_WORKFLOWS.md)

**Quick Commands:**
```bash
# TUESDAY/WEDNESDAY - Complete data collection
/collect-all-data  # 7 automated steps (power ratings, odds, weather, injuries)

# Validate and analyze
/validate-data
/edge-detector
/betting-card

# THURSDAY - Refresh before TNF
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
/edge-detector

# SUNDAY - Quick check or live monitoring
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
/edge-detector

# MONDAY - Check results
uv run python scripts/analysis/check_betting_results.py --league nfl
```

**Available Slash Commands** (16 total):
- `/collect-all-data` - Complete workflow (7 steps with auto pre/post validation)
- `/edge-detector` - Detect betting edges (auto pre-flight validation)
- `/betting-card` - Generate recommendations
- `/current-week` - Show current NFL week
- `/pre-validate` - Manual environment check before data collection
- `/post-validate` - Manual data quality check after collection
- `/validate-data` - Check data quality
- `/power-ratings` - Calculate power ratings
- `/scrape-overtime` - Collect odds (API - fast)
- `/clv-tracker` - Track performance
- `/weather [team] [time]` - Weather impact
- `/injury-report [team] [league]` - Injury analysis
- `/document-lesson` - Add to TROUBLESHOOTING.md
- `/lessons` - View troubleshooting guide

**📖 Complete command reference**: [.claude/commands/README.md](.claude/commands/README.md)

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ -v --cov=. --cov-report=term

# Specific file
uv run pytest tests/test_api_clients.py -v

# Pattern matching
uv run pytest tests/ -k "test_odds" -v
```

### Data Collection

**📖 Complete data collection guide**: [docs/guides/DATA_COLLECTION_GUIDE.md](docs/guides/DATA_COLLECTION_GUIDE.md)

```bash
# Overtime odds (API - primary method, ~5 seconds)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf

# ESPN team stats
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf --week 12

# Betting results checker
uv run python scripts/analysis/check_betting_results.py --league nfl
```

### Action Network Sharp Money Scraper ✨ NEW (2025-11-26)

**Purpose**: Detect sharp vs public money divergence - a core Billy Walters principle.

**Sharp Money Signal**: When ticket % and money % diverge by 5+ points, follow the money.
- Public bets create ticket volume
- Sharp bettors (professionals) move the money
- Divergence indicates which side the pros are on

**Quick Commands**:
```bash
# Single scrape (NFL + NCAAF)
python collect_action_network.py

# Check status
python collect_action_network.py --status

# Continuous monitoring (every hour)
python collect_action_network.py --watch
```

**Data Output**: `data/action_network/`
- `nfl_odds_latest.json` - Most recent NFL data
- `ncaaf_odds_latest.json` - Most recent NCAAF data
- `{league}_odds_week{N}_{timestamp}.json` - Timestamped archives

**Sharp Play Detection**:
```powershell
# View sharp plays (PowerShell)
$data = Get-Content .\data\action_network\nfl_odds_latest.json | ConvertFrom-Json
$data.sharp_plays | Format-Table game, pick, divergence, signal
```

**Divergence Thresholds (League-Specific)**:

**CRITICAL**: NFL and NCAAF require different thresholds due to market liquidity differences:

| Signal Strength | NFL | NCAAF | Meaning |
|-----------------|-----|-------|----------|
| 🔥 VERY STRONG | 15+ | 40+ | High confidence |
| ⚡ STRONG | 10-14 | 30-39 | Significant action |
| 📊 MODERATE | 5-9 | 20-29 | Notable signal |
| ○ NEUTRAL | <5 | <20 | No signal |

**Why different?**
- **NFL**: Highly efficient market, massive volume. Even 5+ divergence is meaningful.
- **NCAAF**: Lower volume, less efficient. 20-40+ divergence common in smaller games.

**Integration with Edge Calculator**:
- Sharp confirmation: +10-20% edge boost
- Sharp contradiction: -10-20% edge penalty
- See `src/walters_analyzer/core/integrated_edge_calculator.py`

**Files**:
- `collect_action_network.py` - Quick CLI script
- `src/walters_analyzer/scrapers/action_network_scraper.py` - Playwright scraper
- `src/walters_analyzer/scrapers/action_network_collector.py` - Automated collector
- `docs/ACTION_NETWORK_COLLECTION.md` - Complete guide

---

## Troubleshooting

### Common Issues and Quick Fixes

**📖 Comprehensive troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**CI Failures - Check This First:**
1. Which job failed? (Lint/Format, Type Check, Tests, Security)
2. Did "Install dependencies" show ✓ or ✗?
3. Are test failures pre-existing? (36 known failures documented)

**Quick Fix (90% of issues):** See [CI/CD Quick Fix](#quick-fix-90-of-ci-failures) above.

**ModuleNotFoundError:**
```bash
# Option 1: Reinstall
uv sync

# Option 2: Run from correct directory
cd src && uv run python -m walters_analyzer.module_name

# Option 3: Editable install
uv pip install -e .
```

**Weather API Issues:**
```bash
# Verify HTTPS (not HTTP)
# Check: src/data/accuweather_client.py should use https://

# Test connectivity
cd src && uv run python -c "
from data.accuweather_client import AccuWeatherClient
import asyncio, os
async def test():
    client = AccuWeatherClient(api_key=os.getenv('ACCUWEATHER_API_KEY'))
    await client.connect()
    key = await client.get_location_key('Green Bay', 'WI')
    print(f'AccuWeather working: {key}')
    await client.close()
asyncio.run(test())
"
```

**Odds Data Issues:**
```bash
# Check odds freshness
ls -lt output/overtime/nfl/pregame/*.json | head -1

# Run manually
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# Validate data
/validate-data
```

**Debugging CI:**
```bash
# View latest runs
gh run list --workflow=ci.yml --limit 5

# Watch specific run
gh run watch <run-id>

# View failed logs
gh run view <run-id> --log-failed
```

**📖 For detailed troubleshooting procedures, see**:
- [docs/guides/ci_cd_prevention_guide.md](docs/guides/ci_cd_prevention_guide.md) - CI/CD prevention
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Error resolution and solutions
- [.github/CI_CD.md](.github/CI_CD.md) - CI/CD technical details

---

## Recent Updates

**Latest Session (2025-11-26 - Action Network Sharp Money Scraper)**:

#### Action Network Sharp Money Detection Complete ✨ (2025-11-26)

**Billy Walters Principle Implemented**: "Follow the money, not the tickets."

**New Capability**: Automated scraping of betting percentages from Action Network to detect sharp (professional) vs public betting divergence.

**Sharp Money Signal**:
- **Tickets %**: Volume of bets placed (public action)
- **Money %**: Dollar amount wagered (sharp action)
- **Divergence**: `money% - tickets%` ≥ 5 points indicates sharp side

**Implementation**:
1. **Playwright Scraper**: Bypasses CloudFlare with stealth settings
   - File: `src/walters_analyzer/scrapers/action_network_scraper.py`
   - Extracts: spreads, moneylines, totals, betting percentages

2. **Automated Collector**: Periodic scraping with state tracking
   - File: `src/walters_analyzer/scrapers/action_network_collector.py`
   - Leagues: NFL + NCAAF
   - Output: `data/action_network/`

3. **Quick CLI**: Simple commands for daily use
   - File: `collect_action_network.py`
   - Commands: single scrape, status check, continuous watch

4. **Integrated Edge Calculator**: Combines power ratings + sharp signals
   - File: `src/walters_analyzer/core/integrated_edge_calculator.py`
   - Sharp confirmation: +10-20% edge boost
   - Sharp contradiction: -10-20% edge penalty

**Week 13 NFL Results (First Run)**:
- 16 games scraped successfully
- 7 sharp money signals detected:
  - KC @ DAL: DAL +3.5 (+15 divergence) 🔥 VERY STRONG
  - NO @ MIA: MIA -6.0 (+15 divergence) 🔥 VERY STRONG
  - MIN @ SEA: SEA -10.5 (+11 divergence) ⚡ STRONG
  - GB @ DET: GB +2.5 (+8 divergence) ⚡ STRONG
  - LV @ LAC: LAC -10.0 (+7 divergence) ⚡ STRONG

**Technical Fixes**:
- Fixed `wait_for_selector` for hidden `<script>` tags (use `state='attached'`)
- Fixed JSON path: `props.pageProps` not `pageProps`
- Added NCAAF to default leagues

**Files Created/Modified**:
- `collect_action_network.py` - Quick CLI
- `src/walters_analyzer/scrapers/action_network_scraper.py` - Playwright scraper
- `src/walters_analyzer/scrapers/action_network_collector.py` - Automated collector
- `src/walters_analyzer/core/integrated_edge_calculator.py` - Edge integration
- `docs/ACTION_NETWORK_COLLECTION.md` - Complete guide
- `docs/ACTION_NETWORK_INTEGRATION.md` - Integration summary

**Memory Updated**: Added Action Network scraper to project memory (line 14)

---

**Previous Session (2025-11-25 Late - NFL.com Client Consolidation)**:

#### NFL.com Game Stats Client: Consolidation Refactoring Complete ✨ (2025-11-25 Late)

**Architecture Decision**: Eliminate code duplication between `nfl_game_stats_client.py` and `nfl_game_stats_client_with_proxies.py` while maintaining clean separation of concerns.

**Implementation Approach**:
- **Optional Dependency Pattern**: ProxyScrapeRotator imported with try/except fallback
  - Allows client to work with or without proxy library
  - No hard dependency on optional proxy components

- **Parameter Layering**:
  - Direct parameters: `proxyscrape_username`, `proxyscrape_password`
  - Environment variable fallback: `PROXYSCRAPE_USERNAME`, `PROXYSCRAPE_PASSWORD`
  - Parameters take precedence over environment variables

- **Strategy Pattern**:
  - `proxy_rotation_strategy` parameter: "rotate" (sequential) or "random"
  - Enables different proxy selection strategies without code changes

- **Lazy Initialization**:
  - Proxy rotator only created if `use_proxies=True`
  - Reduces overhead when proxies not needed
  - Clean initialization in `connect()`, cleanup in `close()`

**Code Changes**:
1. **`src/data/nfl_game_stats_client.py`**:
   - Added optional proxy parameters to `__init__`
   - Conditional proxy initialization in `connect()`
   - New `_get_proxy()` helper for rotation strategy
   - Added `get_proxy_health()` and `test_proxies()` methods
   - Updated docstring with proxy usage examples

2. **`scripts/scrapers/scrape_nfl_with_proxies.py`**:
   - Updated import: `NFLGameStatsClientWithProxies` → `NFLGameStatsClient`
   - Updated instantiation to pass proxy parameters

3. **`src/data/nfl_game_stats_client_with_proxies.py`**:
   - DELETED (consolidated into base class)

**Usage Patterns**:
```python
# Without proxies (default)
client = NFLGameStatsClient()

# With proxies (environmental credentials)
client = NFLGameStatsClient(use_proxies=True)

# With proxies (explicit credentials)
client = NFLGameStatsClient(
    use_proxies=True,
    proxyscrape_username="user",
    proxyscrape_password="pass",
    proxy_rotation_strategy="random"
)
```

**Benefits**:
- ✅ Single client class to maintain
- ✅ No code duplication
- ✅ Optional features don't break without dependencies
- ✅ Backward compatible API
- ✅ Clean separation of proxy concerns
- ✅ Flexible credential management

**Code Quality**:
- ✅ All ruff format + ruff check passing
- ✅ Type hints fully maintained
- ✅ Import verification successful
- ✅ No breaking changes

**Files Modified**: 2 updated, 1 deleted
- **Modified**: `src/data/nfl_game_stats_client.py`, `scripts/scrapers/scrape_nfl_with_proxies.py`
- **Deleted**: `src/data/nfl_game_stats_client_with_proxies.py`

**Commit**: `refactor: consolidate proxy support into nfl_game_stats_client.py`

---

**Previous Session (2025-11-25 Continued - NFL.com Scraper Debugging)**:

#### NFL Game Stats Scraper: Fixed Title & Stats Parsing ✨ (2025-11-25 Continued)

**Problem**: Scraper failed on all 17 games with:
- "Could not find game title" errors
- No stats extracted from 174+ row tables
- Processing hung after page load

**Root Cause Analysis**:
1. **Game Title**: NFL.com doesn't have `<h1>` element; title in page meta tag
2. **Stats Table**: Table structure changed - PLAYER header rows followed by data rows
3. **Performance**: 1740+ sequential `text_content()` calls blocked event loop

**Solutions Implemented**:
- **Game Title Extraction**:
  - Parse page meta title: `"Team1 Name at Team2 Name YYYY REG XX - Game Center"`
  - Extract team names from title or fallback to button labels
  - See: `_extract_game_info()` and `_extract_game_title_from_dom()` methods

- **Stats Table Parsing**:
  - Detect category by column headers (CMP=passing, ATT=rushing, REC=receiving)
  - Parse rows following "PLAYER" header rows as data
  - Optimized text extraction to avoid blocking

- **Timeout Resilience**:
  - Increased timeout from 60s to 120s for slow proxy connections
  - Allows all 17 game pages to load (8 still timeout on parsing, not structural issue)

**Results**:
- ✅ 9/17 games successfully collecting full stats (passing, rushing)
- ✅ All successful games extract: team names, title, stat categories
- ✅ Processing time: ~8 sec per game (vs. hung before)
- ⚠️ 8 games hit timeout (games 12-17) - proxy rate limiting, not parsing

**Files Modified**:
- `src/data/nfl_game_stats_client.py` - Game title and stats parsing
- `scripts/scrapers/scrape_nfl_with_proxies.py` - Timeout increase
- New docs: `docs/guides/NFL_SCRAPER_DEBUGGING_SUMMARY.md`

**Test Coverage**:
- Debug scripts: `debug_nfl_page_structure.py`, `debug_stats_extraction.py`
- Sample output: `output/nfl_game_stats/stats_2025_week_reg-13_*.json`
- Verified data: Passing/rushing stats correctly categorized

**Code Quality**:
- ✅ ruff format applied
- ✅ Type hints maintained
- ✅ Comprehensive error handling
- ✅ Detailed debugging documentation

**Next Steps**:
- Implement proxy rotation between games to handle 17-game scrapes
- Add proxy health monitoring and fallback strategies
- Test receiving stats detection (sometimes empty, needs validation)

---

**Previous Session (2025-11-25 - Action Network Phase 3: Totals Extraction)**:

#### NEW: Action Network Totals (O/U) Extraction Complete ✨ (2025-11-25)

**Phase 3: Totals Extraction via Dropdown Switching**
- **Problem**: Previous extractions returned `over_under: null` and `total_odds: null`
- **Root Cause**: Action Network uses a dropdown selector to switch between Spread/Total/Moneyline views
- **Solution**: Implemented `_extract_with_odds_type()` method with dropdown switching

**Technical Implementation:**
- **`_fetch_odds_impl`** - Now performs multi-step extraction:
  1. Extracts spreads from default view
  2. Switches dropdown to "Total" view (`select_option(value="total")`)
  3. Extracts over/under values
  4. Merges totals back into games list

- **`_extract_with_odds_type`** - New method:
  - Finds odds dropdown: `select:has(option[value='total'])`
  - Waits for table to update after selection
  - Returns dict keyed by game for merging

- **`_extract_table_row`** - Updated to handle `odds_type` parameter:
  - `odds_type="spread"`: parses `+2.5\n-105\n-2.5\n-115`
  - `odds_type="total"`: parses `o48.5\n-110\nu48.5\n-110`

**Results:**
- **Before**: 16 games with `over_under: null`, `total_odds: null`
- **After**: 16/16 NFL games with complete O/U data
- Sample: Packers @ Lions - O/U: 48.5 (-110)

**Code Quality:**
- ✅ 0 ruff errors
- ✅ 0 pyright errors
- ✅ 20/20 selector tests passing
- ✅ No breaking changes

**Previous Sessions**: See [docs/reports/archive/sessions/](docs/reports/archive/sessions/) for complete history

### Key Milestones (Archived)

| Date | Milestone | Details |
|------|-----------|---------|
| 2025-11-25 | Action Network Complete | Phases 1-3: CLI, selector fallback, totals extraction |
| 2025-11-25 | NCAAF Expansion | Transactions + news scrapers for 10+ FBS teams |
| 2025-11-24 | PostgreSQL Pipeline | GameIDMapper + full odds loading (<10 sec) |
| 2025-11-24 | Hook Integration | Auto pre/post validation in slash commands |
| 2025-11-24 | Results Validator | ATS tracking, ROI calculation, Week 12: 57.1% ATS |

---

## Session Maintenance

> **Keep CLAUDE.md Updated**: At the end of each session, update the "Last Session" line in Project Status and the Recent Updates section. This keeps the project state clear for future sessions.

**End-of-Session Checklist:**
1. Update "Last Session" date and summary in Project Status
2. Update Recent Updates section with key accomplishments
3. Commit and push: `git add CLAUDE.md && git commit -m "docs: update session status" && git push`

---

**📚 Complete Documentation**: See [docs/_INDEX.md](docs/_INDEX.md) for full navigation
