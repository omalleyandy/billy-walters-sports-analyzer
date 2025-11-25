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
- **CI/CD**: Fully operational (GitHub Actions)
- **Tests**: 379 tests passing, 40 skipped (multi-platform)
- **Code Quality**: Automated linting and type checking
- **Security**: Vulnerability scanning and secret detection
- **Data Sources**: ESPN, Overtime.ag, Action Network, Massey, AccuWeather
- **Edge Detection**: ✨ Production-ready with automatic schedule validation
- **Pre-Flight Checks**: Automatic week detection & data source validation
- **Results Validation**: ✨ Complete NFL results validator with ATS tracking (NEW 2025-11-24)
- **NFL Scoreboard**: ✨ ESPN API client for fetching game scores by week (NEW 2025-11-24)
- **PostgreSQL Data Loading**: ✨ Complete GameIDMapper + full odds loading (NEW 2025-11-24)
  - GameIDMapper: Maps Overtime.ag IDs to ESPN IDs with 2-day fuzzy matching
  - Odds Loading: Extracts nested dict format and inserts with valid FK references
  - Games Table: Populated with league column for proper constraints
  - Performance: Complete pipeline in <10 seconds, 100% success rate (15/15 NFL games)
- **League Separation**: Strict NFL/NCAAF isolation (never mixed)
- **Data Collection**: Optimized for both NFL & NCAAF workflows
- **NCAAF Expansion**: ✨ Complete transactions and news scrapers (NEW 2025-11-25)
  - Transactions: espn_ncaaf_transactions_client.py (360 lines, 10+ teams)
  - News: espn_ncaaf_news_client.py (380 lines, Playwright-based)
  - CLI: scrape_espn_ncaaf_transactions.py, scrape_espn_ncaaf_news.py
- **Action Network Live Odds CLI**: ✨ Phase 1 implementation complete (NEW 2025-11-25)
  - scrape_action_network_live.py (239 lines, fully featured CLI)
  - Unlocks 370+ lines of ActionNetworkClient functionality
  - Supports --nfl, --ncaaf, --no-headless, --quiet, configurable retries
  - Production-ready with proper exit codes and logging
- **Action Network Multi-Selector Fallback**: ✨ Phase 2 defensive enhancements (NEW 2025-11-25)
  - action_network_client.py enhanced with _try_selectors() method
  - action_network_selectors.json (16 selector groups, 3-4 variants each)
  - test_action_network_selectors.py (20 tests, 100% passing)
  - Cascading selector strategy: specific CSS → generic wildcards → fallbacks
  - Prevents silent failures from Action Network CSS-in-JS class changes
  - Automatic fallback logging for early detection of UI changes
- **Action Network Integrated in Data Workflow**: ✨ Workflow documentation updated (NEW 2025-11-25)
  - Added to .claude/commands/collect-all-data.md Step 6
  - Integrated as optional real-time odds alternative
  - Output locations documented for NFL/NCAAF separation
- **NFL.com API Wrapper**: ✨ CLI created for official NFL data (NEW 2025-11-25)
  - scrape_nfl_com.py with schedule and news support
  - Note: API endpoints return 401 (authentication required)
- **Last Session**: 2025-11-25 - Action Network Phase 1+2 complete, Multi-selector fallbacks, Selector validation tests, Type checking (0 errors)

**📖 For detailed methodology, see**: [docs/guides/BILLY_WALTERS_METHODOLOGY.md](docs/guides/BILLY_WALTERS_METHODOLOGY.md)

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

**📖 For detailed methodology**: See [docs/guides/BILLY_WALTERS_METHODOLOGY.md](docs/guides/BILLY_WALTERS_METHODOLOGY.md)
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

**Available Slash Commands** (14 total):
- `/power-ratings` - Calculate power ratings
- `/scrape-overtime` - Collect odds (API - fast)
- `/collect-all-data` - Complete workflow (all 7 steps)
- `/edge-detector` - Detect betting edges
- `/betting-card` - Generate recommendations
- `/clv-tracker` - Track performance
- `/validate-data` - Check data quality
- `/weather [team] [time]` - Weather impact
- `/injury-report [team] [league]` - Injury analysis
- `/current-week` - Show current NFL week
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

---

## Troubleshooting

### Common Issues and Quick Fixes

**📖 Comprehensive troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**CI Failures - Check This First:**
1. Which job failed? (Lint/Format, Type Check, Tests, Security)
2. Did "Install dependencies" show ✓ or ✗?
3. Are test failures pre-existing? (36 known failures documented)

**Quick Fix (90% of issues):**
```bash
uv run ruff format .
uv run ruff check . --fix
uv run pyright
git add . && git commit -m "fix: apply code quality checks"
git push
```

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

**Latest Session (2025-11-25 - Action Network Phase 1+2 Complete)**:

#### NEW: Action Network Live Odds & Selector Resilience Complete ✨ (2025-11-25)

**Phase 1: CLI Wrapper - Unlocked Unused Functionality**
- **New File**: `scripts/scrapers/scrape_action_network_live.py` (239 lines)
- **Purpose**: CLI wrapper for ActionNetworkClient to unlock 370+ lines of Playwright automation
- **Features**:
  - `--nfl`, `--ncaaf` flags (both default if neither specified)
  - `--no-headless` for debugging (visible browser)
  - `--quiet` mode for automation
  - `--max-retries` (configurable, default 3)
  - `--rate-limit` (configurable, default 2.0s)
  - `--output-dir` (default `output/action_network`)
  - Timestamped JSON output per league
  - Standard exit codes (0=success, 130=interrupted, 1=error)
- **Code Quality**: ✅ 0 ruff errors, 0 pyright errors
- **Status**: Production-ready, fully tested

**Phase 2: Multi-Selector Fallback - Defensive Enhancement**
- **Updated**: `src/data/action_network_client.py` (added ~150 lines)
  - New method: `_try_selectors()` - cascading selector matcher
  - Strategies: CSS-in-JS classes → class wildcards → XPath → text-based
  - Automatic logging of fallback usage for early UI change detection
  - Integrated into `_login()` and `_fetch_odds_impl()`
  - Backward compatible (no breaking changes)

- **New File**: `src/data/action_network_selectors.json` (120 lines)
  - 16 selector groups with 3-4 variants each
  - Externalizes selectors for maintenance
  - Version tracking + last_validated timestamp
  - Comprehensive documentation on CSS-in-JS brittleness
  - Fallback strategy clearly documented
  - Ready for weekly selector health checks

- **New File**: `tests/test_action_network_selectors.py` (280 lines)
  - 20 comprehensive tests (100% passing) ✅
  - Test Classes:
    - TestSelectorConfiguration (6 tests) - Config loading & structure
    - TestSelectorFallbackLogic (2 tests) - _try_selectors method
    - TestSelectorConfigValidation (3 tests) - Content validation
    - TestSelectorCoverage (3 tests) - Required elements
    - TestSelectorMaintenance (3 tests) - Version tracking
    - Plus XPath & precedence tests
  - Detects selector changes before production failures

**Workflow Integration**
- Updated `.claude/commands/collect-all-data.md`
  - Added Action Network Live Odds as Step 6 option
  - Documented as optional real-time odds alternative
  - Output locations documented for NFL/NCAAF
  - Integration with edge detection pipeline shown

**Code Quality Results**:
- ✅ All code formatted (ruff): 562 lines
- ✅ All tests passing: 20/20 selector tests
- ✅ Type checking clean: 0 errors, 0 warnings
- ✅ No breaking changes
- ✅ Backward compatible

**Key Achievements**:
- ✅ Unlocked 370+ lines of ActionNetworkClient functionality
- ✅ Prevented silent failures from CSS selector changes
- ✅ Externalized selectors for easier maintenance
- ✅ Added comprehensive validation testing
- ✅ Production-ready defensive enhancements
- ✅ Integrated into data collection workflow

---

**Previous Session (2025-11-25 - Phase 4 NCAAF Expansion & Integration Audits)**:

#### Phase 4 Work Complete - NCAAF Expansion & Integration Audits ✨ (2025-11-25)

**NCAAF Data Collection Expansion**:
- **NCAAF Transactions Client** (`src/data/espn_ncaaf_transactions_client.py` - 360 lines)
  - Parallel implementation to NFL client (clean separation)
  - Supports 10+ major FBS teams (Alabama, LSU, Ohio State, Clemson, Georgia, Texas, Oklahoma, USC, Florida, Texas A&M)
  - Transaction types: Transfer In/Out, Coaching, Recruiting, Eligibility, Injury
  - CLI wrapper: `scripts/scrapers/scrape_espn_ncaaf_transactions.py`
  - Tested: Alabama extraction successful (output saved)

- **NCAAF News Client** (`src/data/espn_ncaaf_news_client.py` - 380 lines)
  - Playwright-based browser automation (matches NFL news client pattern)
  - Team-specific news categories: Recruiting, Coaching, Injuries, Transfers, Game Analysis
  - CLI wrapper: `scripts/scrapers/scrape_espn_ncaaf_news.py`
  - Full context manager support + error handling

- **CLI Integration**:
  - `--team`, `--teams`, `--all-teams` options (consistent with NFL)
  - `--output-dir` for custom locations
  - `--quiet` mode for automation
  - Timestamped JSON output files

**Action Network Integration Audit** (1,614 lines across 4 files):
- ✅ `action_network_client.py` (390 lines): Quality Playwright client with login, rate limiting, retry logic
- ✅ `action_network_scraper.py` (499 lines): Legacy network interception scraper (appears experimental)
- ✅ `action_network_sitemap_scraper.py` (463 lines): Production-ready sitemap parser with URL categorization
- ✅ `action_network_loader.py` (262 lines): Data models and JSONL parsing infrastructure

**Audit Findings**:
- ⚠️ **Gap**: No CLI wrapper for `action_network_client.py` (370 lines of quality code unused from CLI)
- ⚠️ **Risk**: CSS selectors hardcoded in client (Action Network UI changes could break scraper)
- ✅ **Strength**: Dual scraping approaches (browser automation + sitemap catalog) provide flexibility
- 📋 **Recommendation**: Create CLI wrapper for live odds scraping, implement selector validation tests

**NFL.com API Integration**:
- **Created CLI Wrapper** (`scripts/scrapers/scrape_nfl_com.py`)
  - Supports `--schedule` (game times, networks, scores)
  - Supports `--news` (team-specific articles)
  - Options: `--week`, `--team`, `--limit`

- **API Status**: 401 Unauthorized
  - NFL API endpoints require browser authentication headers
  - Current implementation uses static headers (insufficient)
  - **Next Step**: Implement Playwright session capture (see `scripts/dev/capture_nfl_api_headers.py`)

**Code Quality**:
- ✅ All new code formatted with `ruff format`
- ✅ Type checking passed: 0 errors, 0 warnings
- ✅ Follows existing patterns and conventions
- ✅ Full docstrings on public APIs

**Files Added (1,522 lines)**:
- src/data/espn_ncaaf_transactions_client.py (360 lines)
- src/data/espn_ncaaf_news_client.py (380 lines)
- scripts/scrapers/scrape_espn_ncaaf_transactions.py (145 lines)
- scripts/scrapers/scrape_espn_ncaaf_news.py (180 lines)
- scripts/scrapers/scrape_nfl_com.py (130 lines)
- output/espn/transactions/ncaaf/transactions_ncaaf_*.json (tested output)

**League Separation Maintained**:
- NCAAF modules separate from NFL (no cross-contamination)
- Separate team mappings
- Separate output directories
- Consistent CLI patterns

---

**Latest Session (2025-11-24 - Continued)**:

#### NEW: PostgreSQL Data Loading Workflow Complete ✨ (2025-11-24)
**Full end-to-end data loading pipeline from collection to database**

- **GameIDMapper** (`scripts/database/game_id_mapper.py` - 265 lines)
  - Intelligent mapping between Overtime.ag and ESPN game IDs
  - Fuzzy matching with 2-day date tolerance (handles timezone differences)
  - Cached lookup for fast performance (~100K games in memory)
  - Success rate: 100% on NFL Week 13 (15/15 games)

- **Enhanced Data Loader** (`scripts/database/load_collected_data_to_db.py`)
  - Integrated GameIDMapper for game ID conversion
  - Fixed odds extraction from nested dict format
    - Spread: {home: -2.5, away: 2.5}
    - Moneyline: {home: -145, away: 125}
    - Total: {points: 49.0}
  - Added date parsing for multiple formats (MM/DD/YYYY HH:MM, ISO, etc.)
  - Added populate_games_table() to copy espn_schedules with league column
  - ON CONFLICT DO NOTHING gracefully handles duplicates

- **Database Results (Week 13 NFL)**
  - Schedules: 16 records loaded
  - Games table: 16 records populated
  - Team stats: 32 records loaded
  - Odds: 15 games with complete betting data (spread, moneyline, total)
  - Errors: 0
  - Total load time: <10 seconds

- **Documentation Created**
  - `docs/technical/database/POSTGRES_DATA_LOADING_WORKFLOW.md` - Complete 400+ line guide
  - Updated `docs/_INDEX.md` with new Database & Data Storage section
  - Updated `CLAUDE.md` with latest features

**Key Technical Achievements:**
- ✅ Resolved game ID mismatch between Overtime.ag and ESPN
- ✅ Implemented fuzzy matching with 2-day tolerance
- ✅ Extracted nested dict odds format correctly
- ✅ Populated games table with proper league column
- ✅ Achieved 100% success rate on all 15 NFL Week 13 games
- ✅ Complete workflow documented and ready for production

**Example:** Baltimore Ravens (HOME -3.5) vs Cincinnati Bengals (AWAY +3.5)
- Overtime.ag ID: 114570442 → ESPN ID: 401772930
- Spread: -3.5 / 3.5
- Moneyline: -145 / 125
- Total: 26.0 (1st half)

---

#### Previous: Hook System Integration with Slash Commands ✨
- **Integrated Validators into Slash Commands**
  - `/collect-all-data` now runs automatic pre/post-flight validation
  - `/edge-detector` now runs automatic pre-flight validation
  - Validators prevent unsafe operations (missing API keys, data, etc.)
  - Exit codes standardized: 0 = success, 1 = failure

- **New Slash Commands for Manual Checks**
  - `/pre-validate` - Check environment before data collection
  - `/post-validate` - Check data quality after collection
  - Useful for independent verification or troubleshooting

- **Hook System Documentation**
  - `.claude/hooks/README.md` - Updated with system architecture diagram
  - Shows how hooks integrate with commands automatically
  - Explains three invocation methods (automatic, manual slash commands, direct Python)
  - Entry points clearly documented

- **Commands Reference Updated**
  - `.claude/commands/README.md` - Version 2.2 with validator integration
  - Updated `/collect-all-data`, `/edge-detector` with pre/post-flight details
  - Added `/pre-validate`, `/post-validate` to Quick Start table
  - Updated recommended weekly workflow to show validation points

- **CLAUDE.md Updated**
  - New "Hook Integration Architecture" section
  - Shows automatic validation workflow clearly
  - Documents three ways to invoke hooks
  - Weekly workflow timeline with validation points
  - Exit codes explained for scripting

**Key Result:** Validators now transparent to user - validation happens automatically in background without extra commands needed.

---

#### Earlier: NFL Scoreboard Client & Results Validator ✨
- **NFL Scoreboard Client** (`src/data/espn_nfl_scoreboard_client.py`)
  - Fetches actual game scores from ESPN API for any week (1-18)
  - Auto-detects current week from system date
  - Parses ESPN's "competitors" array format correctly
  - Saves scores to JSON for offline analysis
  - Ready for full season score tracking

- **Results Validator** (`src/walters_analyzer/results/results_validator.py`)
  - Compares edge detection predictions vs actual game results
  - Calculates ATS (Against The Spread) performance metrics
  - Computes ROI based on Kelly sizing
  - Team name ↔ abbreviation conversion (all 32 NFL teams)
  - Generates detailed markdown performance reports
  - Ready for ongoing season tracking

- **Week 12 Validation Complete**
  - Successfully matched 8 predictions to actual scores
  - **ATS Record**: 4 Wins - 3 Losses (57.1% win rate)
  - **ROI**: +13.0% (positive return on investment)
  - **Avg Confidence**: 66.4 points
  - Demonstrated system works end-to-end
  - See: [docs/guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md](docs/guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md)

#### Key Files Added:
- `src/data/espn_nfl_scoreboard_client.py` - ESPN scoreboard API client
- `src/walters_analyzer/results/results_validator.py` - Results validation engine
- `output/nfl_scores/scores_2025_week_12.json` - Week 12 actual scores
- `docs/guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md` - Complete workflow guide

**Key Improvements:**
- ✅ Automated results validation (no manual score checking)
- ✅ Direct ESPN API integration (reliable data source)
- ✅ Week-by-week performance tracking enabled
- ✅ Full season CLV calculation framework ready
- ✅ Historical score fetching for any completed week
- ✅ Clear separation between Week 12 validation and Week 13 prep

**Next Steps**: Run `/collect-all-data` on Tuesday (Week 13 prep) to continue automated workflow

**Previous Sessions**: See [docs/reports/archive/sessions/](docs/reports/archive/sessions/) for complete history

---

## Session Maintenance

> **Keep CLAUDE.md Updated**: At the end of each session, update the "Last Session" line in Project Status and the Recent Updates section. This keeps the project state clear for future sessions.

**End-of-Session Checklist:**
1. Update "Last Session" date and summary in Project Status
2. Update Recent Updates section with key accomplishments
3. Commit and push: `git add CLAUDE.md && git commit -m "docs: update session status" && git push`

---

**📚 Complete Documentation**: See [docs/_INDEX.md](docs/_INDEX.md) for full navigation
