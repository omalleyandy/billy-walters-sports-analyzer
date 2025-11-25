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
- **Tests**: 146+ tests passing (multi-platform) + 18 results checker + 35 NCAAF edge detector
- **Code Quality**: Automated linting and type checking
- **Security**: Vulnerability scanning and secret detection
- **Data Sources**: ESPN, Overtime.ag, Action Network, Massey, AccuWeather
- **Edge Detection**: Production-ready for NFL & NCAAF
- **Results Validation**: Complete betting results checker system
- **Last Session**: 2025-11-24 - Documentation reorganization (125+ files migrated)

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

The project includes 14 automation hooks in `.claude/hooks/` for validation and automation.

**Core Hooks:**
- `pre_data_collection.py` - Validates environment before data collection
- `post_data_collection.py` - Validates data quality after collection (EXCELLENT/GOOD/FAIR/POOR)
- `pre_edge_detection.py` - Validates required data before edge detection
- `auto_edge_detector.py` - Auto-triggers edge detection when new odds detected
- `pre_commit_check.py` - Validates code for security (no exposed API keys)

**Usage:**
```bash
# Before data collection
python .claude/hooks/pre_data_collection.py
/collect-all-data
python .claude/hooks/post_data_collection.py

# Before committing code
python .claude/hooks/pre_commit_check.py
git add . && git commit -m "feat: description"
```

**Complete Documentation**: See [.claude/hooks/README.md](.claude/hooks/README.md) for full details on all 14 hooks, integration patterns, and error recovery procedures.

**Use in Documentation Updates:**
```bash
# After creating new reports/docs
python .claude/hooks/auto_index_updater.py --auto
git add docs/_INDEX.md CLAUDE.md
git commit -m "docs: update index with new reports"
```

**📖 For complete hook reference, see**: [.claude/hooks/](. claude/hooks/)

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

| Task | Command | Time | Frequency |
|------|---------|------|-----------|
| Collect all data | `/collect-all-data` | 5 min | Weekly (Tue/Wed) |
| Find betting edges | `/edge-detector` | 2 min | After collection |
| Generate picks | `/betting-card` | 1 min | Weekly (Wed) |
| Check results | `/check-results --league nfl` | 1 min | Weekly (Mon) |
| Current NFL week | `/current-week` | 5 sec | As needed |
| Weather impact | `/weather [team] [datetime]` | 30 sec | Per game |
| Injury analysis | `/injury-report [team] [league]` | 30 sec | Per team |
| Validate data | `/validate-data` | 30 sec | After collection |

**See**: [docs/_INDEX.md](docs/_INDEX.md) for complete command reference

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

**Latest Session (2025-11-23)**: ESPN Data QA Testing - 56/56 tests passed (100%), APPROVED FOR PRODUCTION

**Previous Sessions**: See [docs/reports/archive/sessions/](docs/reports/archive/sessions/) for complete history

---

**📚 Complete Documentation**: See [docs/_INDEX.md](docs/_INDEX.md) for full navigation
