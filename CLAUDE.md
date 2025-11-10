# Billy Walters Sports Analyzer - Development Guidelines

This document contains critical information about working with the Billy Walters Sports Analyzer codebase. Follow these guidelines precisely.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [How to Use This Document](#how-to-use-this-document)
3. [Core Development Rules](#core-development-rules)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Git Workflow](#git-workflow)
6. [Code Formatting](#code-formatting)
7. [Environment Variables & API Keys](#environment-variables--api-keys)
8. [Football Analytics Best Practices](#football-analytics-best-practices)
9. [API Integration Guidelines](#api-integration-guidelines)
10. [Project Structure](#project-structure)
11. [Quick Reference](#quick-reference)
12. [Development Session Best Practices](#development-session-best-practices)
13. [Resources](#resources)

---

## Project Overview

This is a **football-focused sports analytics and betting analysis system** (NFL & NCAAF) inspired by Billy Walters' analytical approach. The project integrates weather data, AI-powered analysis, odds tracking, and statistical modeling to provide comprehensive insights for informed decision-making.

### Sports Focus
- **NFL** (National Football League)
- **NCAAF** (NCAA College Football)

### Existing Components
- **MCP Server** (walters_mcp_server.py) - Model Context Protocol server for tool integration
- **Autonomous Agent** (walters_autonomous_agent.py) - Automated analysis agent
- **PRD** (billy_walters_analytics_prd.md) - Product requirements document

### Project Status
- **CI/CD**: Fully operational with GitHub Actions
- **Tests**: 146 tests passing (multi-platform, multi-version)
- **Code Quality**: Automated linting and type checking
- **Security**: Automated vulnerability scanning and secret detection
- **Documentation**: Complete development guidelines and lessons learned
- **Legacy Code**: Pragmatic configuration allows CI while incrementally improving code quality

## How to Use This Document

**For New Development Sessions:**
1. Review relevant sections based on your task
2. Check **Quick Reference** for common workflows
3. Consult **Troubleshooting** section if you encounter issues
4. Reference **LESSONS_LEARNED.md** for similar past problems

**Before Making Changes:**
1. Read **Core Development Rules** (critical)
2. Review **CI/CD Pipeline** section
3. Follow **Git Workflow** process
4. Use **Local Validation** commands before pushing

**When Something Breaks:**
1. Check **Troubleshooting** section in this file
2. Review **LESSONS_LEARNED.md** for similar issues
3. Check `.github/CI_CD.md` for CI/CD specific problems
4. Document new issues using `/document-lesson` command

**This Document Contains:**
- Development rules and best practices
- Complete CI/CD integration guide
- Step-by-step workflows
- Quick reference commands
- Troubleshooting guide
- Project structure and organization

## Documentation System

This project maintains comprehensive documentation across multiple files:

### Primary Documents

**CLAUDE.md (This File)**
- **Purpose**: Single source of truth for development guidelines
- **Audience**: Developers (human and AI)
- **Content**: Rules, workflows, best practices, quick reference
- **Update When**: Adding new patterns, solving common issues, changing standards
- **Location**: Project root

**LESSONS_LEARNED.md**
- **Purpose**: Troubleshooting guide and institutional knowledge
- **Audience**: Developers debugging issues
- **Content**: Session-by-session problem solving with root causes and solutions
- **Update When**: Solving non-trivial problems, debugging CI/CD, major refactoring
- **Location**: Project root
- **How to Update**: Use `/document-lesson` command

**.github/CI_CD.md**
- **Purpose**: Technical CI/CD documentation
- **Audience**: DevOps, CI/CD maintainers
- **Content**: Workflow architecture, configuration details, troubleshooting
- **Update When**: Changing workflows, adding checks, modifying actions
- **Location**: `.github/` directory

**README.md**
- **Purpose**: Project overview and quick start
- **Audience**: New users, external stakeholders
- **Content**: What the project does, installation, basic usage
- **Update When**: Features change, installation process updates
- **Location**: Project root

### Supporting Documentation

**.env.example**
- Template for required environment variables
- Update when adding new API integrations

**pyproject.toml**
- Package configuration
- Ruff and Pyright settings (with inline comments)

**.github/BRANCH_PROTECTION_SETUP.md**
- Step-by-step branch protection configuration
- Reference for GitHub repository settings

### Documentation Principles

1. **Single Source of Truth**: Each topic has one authoritative location
2. **Cross-Reference**: Documents link to each other for related topics
3. **Keep Current**: Update documentation with code changes
4. **Be Specific**: Include file paths, line numbers, error messages
5. **Show Examples**: Provide code snippets and command examples
6. **Explain Why**: Document rationale, not just what

### When to Update What

| Situation | Update |
|-----------|--------|
| Solved a bug | LESSONS_LEARNED.md |
| New development pattern | CLAUDE.md |
| Changed CI workflow | .github/CI_CD.md |
| Added feature | README.md |
| New API integration | .env.example, CLAUDE.md |
| Configuration change | pyproject.toml (comments), CLAUDE.md |
| Common issue solved | CLAUDE.md (Troubleshooting), LESSONS_LEARNED.md |

## Core Development Rules

### 1. Package Management
- ONLY use uv, NEVER pip
- Installation: `uv add package`
- Running tools: `uv run tool`
- Upgrading: `uv add --dev package --upgrade-package package`
- FORBIDDEN: `uv pip install`, `@latest` syntax

### 2. Code Quality
- Type hints required for all code
- Use pyright for type checking
  - Run `uv run pyright` after every change and fix resulting errors
- Public APIs must have docstrings
- Functions must be focused and small
- Follow existing patterns exactly
- Line length: 88 chars maximum

### 3. Testing Requirements
- Framework: `uv run pytest`
- Async testing: use anyio, not asyncio
- Coverage: test edge cases and errors
- New features require tests
- Bug fixes require regression tests
- Test with realistic NFL/NCAAF data and edge cases
- CI runs tests on Ubuntu and Windows with Python 3.11 and 3.12
- Aim for 80%+ code coverage

**Running Tests:**
```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ -v --cov=. --cov-report=term

# Run specific test file
uv run pytest tests/test_api_clients.py -v

# Run tests matching pattern
uv run pytest tests/ -k "test_odds" -v
```

### 4. Code Style
- PEP 8 naming (snake_case for functions/variables)
- Class names in PascalCase
- Constants in UPPER_SNAKE_CASE
- Document with docstrings
- Use f-strings for formatting

## Environment Variables & API Keys

### Required Environment Variables

Store these in .env file (NEVER commit to git):

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
OV_LOGIN_URL=...
OV_STORAGE_STATE=...
OVERTIME_START_URL=...
OVERTIME_OUT_DIR=...
OVERTIME_PROXY=...
OVERTIME_LIVE_URL=...
OVERTIME_COMP=...

# Proxy Configuration
PROXY_URL=...
PROXY_USER=...
PROXY_PASS=...

# GitHub (for automation)
GITHUB_TOKEN=ghp_...

# Other Services
HIGHLIGHTLY_API_KEY=...

## MCP Server Integration

Your project includes a custom MCP server (walters_mcp_server.py) that provides:
- Sports data tools
- Weather integration
- Odds analysis capabilities
- AI-powered predictions

### Using the MCP Server

Start the MCP server:
`uv run python .claude/walters_mcp_server.py`

The server exposes tools that Claude Code can use via the Model Context Protocol.

## Autonomous Agent

The walters_autonomous_agent.py provides automated analysis capabilities:
- Scheduled game analysis
- Automated odds monitoring
- Weather impact calculations
- Value opportunity detection

## Football Analytics Best Practices

### 1. NFL-Specific Considerations
- **Week numbering**: Handle bye weeks correctly
- **Playoff formats**: Different playoff structure than regular season
- **Roster changes**: Track trades, injuries, suspensions
- **Home field advantage**: Quantify and factor in
- **Division games**: Historical rivalry and performance patterns
- **Weather impact**: Critical for outdoor stadiums (Buffalo, Green Bay, etc.)

### 2. NCAAF-Specific Considerations
- **Conference alignments**: Track conference changes
- **Bowl games**: Different dynamics than regular season
- **Talent disparity**: Larger skill gaps between teams
- **Home field advantage**: Often more significant than NFL
- **Roster turnover**: High due to graduations and transfers
- **Strength of schedule**: Varies widely across conferences

### 3. Weather Impact Analysis
- Wind speed >15 mph significantly affects passing
- Temperature <32°F affects ball handling
- Precipitation reduces scoring
- Track indoor vs outdoor stadium

### 4. Odds Analysis
- Store odds in decimal format for calculations
- Track line movements (opening line vs closing line)
- Monitor sharp action indicators
- Calculate implied probability vs true probability
- Identify value opportunities (positive expected value)

## API Integration Guidelines

### Weather APIs
- AccuWeather: 5-day forecasts, detailed conditions
- OpenWeather: Alternative forecast source, historical data
- Use both for redundancy and cross-validation

### AI Services
- Anthropic Claude: Matchup analysis, narrative generation
- OpenAI: Predictions, pattern recognition

### Sports Data
- Overtime API: Game data, scores, schedules
- Action Network: Betting lines, sharp action, odds movements

### Proxy Management
- Use PROXY_URL, PROXY_USER, PROXY_PASS for scraping
- Implement rotation for high-volume requests
- Respect rate limits

## Data Models

Use Pydantic for all data models:
- Game, Team, Stadium
- WeatherConditions
- OddsMovement
- PlayerStats
- League enum (NFL/NCAAF)

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment.

### Automated Checks

Every push and pull request triggers:
- **Lint and Format**: Ruff formatting and linting checks
- **Type Check**: Pyright static type analysis
- **Security Scan**: pip-audit and TruffleHog secret detection
- **Tests**: Multi-platform (Ubuntu/Windows), multi-version (Python 3.11/3.12)

### Local Validation (Run Before Pushing)

**Always run these commands locally before pushing:**

```bash
# 1. Format code
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

All commands must pass before pushing to ensure CI succeeds.

### Tool Configuration

**Ruff Configuration** (`pyproject.toml:109-147`):
- Excludes: `.claude`, `.codex`, `data/_tmp`, `review` directories
- Line length: 88 characters
- Pragmatic ignores for legacy code (E722, F401, F821, F841)
- Format on save recommended

**Pyright Configuration** (`pyproject.toml:149-189`):
- Includes only: `src`, `scrapers`, `scripts`, `tests`, `examples`
- Basic type checking mode for legacy code
- Lenient mode (most type errors suppressed for now)
- Will gradually increase strictness as code improves

### Branch Protection

The `main` branch is protected with the following requirements:
- All CI checks must pass before merge
- Pull request review required
- Cannot force push to main

### CI/CD Documentation

See `.github/CI_CD.md` for comprehensive CI/CD documentation including:
- Workflow configuration details
- Troubleshooting guide
- Adding new CI checks
- Dependabot configuration

## Git Workflow

### Development Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make Changes and Test Locally**
   - Write code
   - Run local validation commands (see CI/CD section above)
   - Ensure all checks pass

3. **Commit with Conventional Commits**
   ```bash
   git commit -m "feat(scope): brief description"
   ```

   Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

4. **Push and Create Pull Request**
   ```bash
   git push origin feat/your-feature-name
   ```
   - Open PR on GitHub
   - Wait for CI checks to pass
   - Request review
   - Address feedback

5. **Merge to Main**
   - All CI checks must be green
   - At least one approval required
   - Use "Squash and merge" for clean history

### Commit Message Format

```
type(scope): brief description

Detailed explanation of changes made.

- Key change 1
- Key change 2

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Examples:**
- `feat(data): add ESPN injury scraper`
- `fix(edge-detection): correct power rating calculation`
- `docs: update installation instructions`
- `refactor(tests): consolidate test utilities`

## Code Formatting

### Ruff
```bash
# Format all files
uv run ruff format .

# Check formatting (CI uses this)
uv run ruff format --check .

# Run linter
uv run ruff check .

# Auto-fix safe issues
uv run ruff check . --fix
```

### Type Checking
```bash
# Run pyright type checker
uv run pyright

# Check specific file
uv run pyright src/specific_file.py
```

**Note:** Pyright is configured in lenient mode for legacy code. Focus on:
- Adding type hints to new code
- Fixing type errors in code you touch
- Gradually improving legacy code

## Security & Privacy

- NEVER commit API keys or credentials
- Add .env, .env.* to .gitignore
- Use environment variables for all sensitive data
- Rotate API keys if accidentally exposed

## Project Structure

billy-walters-sports-analyzer/
├── .github/                     # CI/CD configuration
│   ├── workflows/
│   │   └── ci.yml              # Main CI/CD pipeline
│   ├── dependabot.yml          # Dependency updates
│   ├── CI_CD.md                # CI/CD documentation
│   └── BRANCH_PROTECTION_SETUP.md
├── src/
│   ├── data/                    # Data collection (27 scrapers & clients)
│   │   ├── accuweather_client.py
│   │   ├── espn_api_client.py
│   │   ├── overtime_signalr_client.py
│   │   └── ...
│   ├── walters_analyzer/        # Core analysis system
│   │   ├── valuation/           # Edge detection & analysis (11 modules)
│   │   │   ├── billy_walters_edge_detector.py
│   │   │   ├── billy_walters_totals_detector.py
│   │   │   ├── analyze_games_with_injuries.py
│   │   │   └── analyze_injuries_by_position.py
│   │   ├── query/               # Display utilities (6 modules)
│   │   │   ├── check_game.py
│   │   │   ├── show_current_odds.py
│   │   │   └── watch_alerts.py
│   │   ├── backtest/            # Backtesting framework
│   │   ├── config/              # Configuration
│   │   ├── core/                # Core system
│   │   ├── feeds/               # Data feeds
│   │   ├── ingest/              # Data ingestion
│   │   └── research/            # Research tools
│   └── db/                      # Database layer
├── scripts/                     # Operational scripts
│   ├── analysis/                # Weekly analysis (8 scripts)
│   ├── validation/              # Data validation (3 scripts)
│   ├── backtest/                # Backtesting (2 scripts)
│   ├── utilities/               # Helper scripts (5 scripts)
│   └── dev/                     # Development/deployment (14 scripts)
├── tests/                       # Test suite (146 tests)
│   └── test_validation_integration.py
├── examples/                    # Example scripts
├── scrapers/                    # Scrapy spiders
│   └── overtime_live/
├── .claude/                     # Claude Code configuration
│   ├── walters_mcp_server.py   # MCP server
│   ├── walters_autonomous_agent.py
│   ├── billy_walters_analytics_prd.md
│   ├── hooks/                   # Git hooks and validators
│   └── commands/                # Custom slash commands
├── .env.example
├── .gitignore
├── pyproject.toml               # Package config (includes ruff/pyright)
├── uv.lock                      # Dependency lockfile
├── CLAUDE.md                    # This file
├── LESSONS_LEARNED.md           # Development lessons
└── README.md

### Directory Guidelines

**When adding new files:**
- Data scrapers/clients → `src/data/`
- Edge detection/analysis → `src/walters_analyzer/valuation/`
- Query/display utilities → `src/walters_analyzer/query/`
- Weekly analysis scripts → `scripts/analysis/`
- Data validation → `scripts/validation/`
- Backtesting → `scripts/backtest/`
- Helper utilities → `scripts/utilities/`
- Dev/deployment → `scripts/dev/`
- Tests → `tests/`
- Examples → `examples/`

## Responsible Use

This is an analytical tool for educational/research purposes only.
Always gamble responsibly and within legal jurisdictions.

## Quick Reference

### Common Development Workflows

**Starting a New Feature:**
```bash
# 1. Create feature branch
git checkout -b feat/your-feature

# 2. Install/update dependencies
uv sync --all-extras --dev

# 3. Make changes, write tests
# ...

# 4. Validate locally (all must pass!)
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest tests/ -v --cov=.

# 5. Commit and push
git add .
git commit -m "feat(scope): description"
git push origin feat/your-feature

# 6. Open PR on GitHub
```

**Adding a New Dependency:**
```bash
# Production dependency
uv add package-name

# Development dependency
uv add --dev package-name

# With version constraint
uv add "package-name>=1.0.0"

# Sync after manual pyproject.toml edits
uv sync
```

**Running Analysis Scripts:**
```bash
# Weekly game analysis
uv run python scripts/analysis/analyze_week.py

# Edge detection
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector

# Check specific game
uv run python -m walters_analyzer.query.check_game --game-id "123"

# Monitor live odds
uv run python -m walters_analyzer.query.watch_alerts
```

**Debugging CI Failures:**
```bash
# View latest CI run
gh run list --workflow=ci.yml --limit 5

# Watch specific run
gh run watch <run-id>

# View failed logs
gh run view <run-id> --log-failed

# Run exact CI checks locally
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest tests/ -v --cov=. --cov-report=xml
```

**Checking Current NFL Week:**
```bash
# Use custom slash command
/current-week

# Or run directly
uv run python -m walters_analyzer.season_calendar
```

### Important File Locations

**Configuration:**
- `pyproject.toml` - Package config, ruff/pyright settings
- `.env` - Environment variables (NOT in git)
- `.env.example` - Template for required env vars

**CI/CD:**
- `.github/workflows/ci.yml` - CI pipeline
- `.github/CI_CD.md` - CI/CD documentation
- `.github/dependabot.yml` - Dependency updates

**Documentation:**
- `CLAUDE.md` - This file (development guidelines)
- `LESSONS_LEARNED.md` - Troubleshooting and lessons
- `README.md` - Project overview

**Claude Code:**
- `.claude/walters_mcp_server.py` - MCP server
- `.claude/walters_autonomous_agent.py` - Autonomous agent
- `.claude/hooks/` - Git hooks and validators
- `.claude/commands/` - Custom slash commands

### Troubleshooting

**"ModuleNotFoundError" when running scripts:**
```bash
# Option 1: Reinstall package
uv sync

# Option 2: Run from src directory
cd src && uv run python -m walters_analyzer.module_name

# Option 3: Install in editable mode
uv pip install -e .
```

**CI failing on type check:**
- Check `pyproject.toml` pyright configuration
- Run `uv run pyright` locally to see errors
- Most errors suppressed for legacy code (see LESSONS_LEARNED.md)

**CI failing on lint:**
- Run `uv run ruff format .` to auto-format
- Run `uv run ruff check .` to see issues
- Run `uv run ruff check . --fix` to auto-fix safe issues

**Tests failing locally but pass in CI:**
- Check Python version (CI uses 3.11 and 3.12)
- Ensure all dependencies installed: `uv sync --all-extras --dev`
- Check for OS-specific issues (CI tests Ubuntu and Windows)

### Getting Help

1. Check `LESSONS_LEARNED.md` for similar issues
2. Check `.github/CI_CD.md` for CI/CD questions
3. Review relevant section in this file
4. Check GitHub Issues for known problems
5. Use `/document-lesson` to add new lessons learned

## Development Session Best Practices

### Starting a Session

**1. Sync with Latest Changes**
```bash
# Pull latest from main
git pull origin main

# Update dependencies
uv sync --all-extras --dev

# Verify CI is passing
gh run list --workflow=ci.yml --limit 3
```

**2. Review Recent Changes**
```bash
# Check recent commits
git log --oneline -10

# Check if any new lessons learned
tail -50 LESSONS_LEARNED.md

# Check Dependabot PRs
gh pr list --author app/dependabot
```

**3. Set Up Your Task**
- Create feature branch
- Review relevant documentation sections
- Run tests to ensure baseline is green

### During Development

**Best Practices:**
- **Commit Often**: Small, focused commits are easier to review and revert
- **Test Locally**: Run validation commands before every commit
- **Document as You Go**: Use inline comments for complex logic
- **Follow Patterns**: Match existing code style and architecture
- **Ask Questions**: Use `/document-lesson` if you solve something tricky

**Validation Checklist (Before Every Commit):**
- [ ] Code formatted: `uv run ruff format .`
- [ ] Linting passes: `uv run ruff check .`
- [ ] Type check passes: `uv run pyright`
- [ ] Tests pass: `uv run pytest tests/ -v`
- [ ] No secrets in staged files: `git diff --cached`

### Ending a Session

**1. Clean Up Your Work**
```bash
# Commit any remaining changes
git status
git add .
git commit -m "work-in-progress: description"

# Push to your branch (backup)
git push origin your-branch-name
```

**2. Document What You Learned**
```bash
# If you solved a tricky problem
/document-lesson

# Add to LESSONS_LEARNED.md with:
# - Problem description
# - Root cause
# - Solution implemented
# - Prevention tips
```

**3. Update Project State**
- Sync CLAUDE.md if you discovered new patterns
- Update README.md if project scope changed
- Commit documentation updates separately

**4. Prepare for Next Session**
- Leave clear TODO comments in code
- Update GitHub issues with progress
- Note any blockers or questions

### When CI/CD Fails

**Systematic Debugging Process:**

1. **Identify Which Check Failed**
   ```bash
   gh run view <run-id> --log-failed
   ```

2. **Reproduce Locally**
   - Run the exact same command CI uses
   - Check if it fails locally
   - If it passes locally, check for environment differences

3. **Common Fixes**
   - **Lint failures**: Run `uv run ruff format .` and `uv run ruff check . --fix`
   - **Type check failures**: Check if new code needs type hints or pyright exclusions
   - **Test failures**: Run `uv run pytest tests/ -v --cov=.` and fix failing tests
   - **Security scan failures**: Check for accidentally committed secrets

4. **If Still Stuck**
   - Check `LESSONS_LEARNED.md` for similar CI failures
   - Review `.github/CI_CD.md` troubleshooting section
   - Check if configuration in `pyproject.toml` needs updating

5. **Document the Solution**
   - Use `/document-lesson` to capture the fix
   - Include what failed, why it failed, and how you fixed it
   - Update CLAUDE.md if it's a common issue

### Maintaining Documentation

**Keep Documentation Current:**

**CLAUDE.md (This File):**
- Update when adding new development patterns
- Add to Quick Reference when you create useful commands
- Update Troubleshooting when you solve new issues
- Keep project structure current

**LESSONS_LEARNED.md:**
- Document every non-trivial problem you solve
- Include root cause analysis
- Provide prevention tips
- Update after each significant debugging session

**README.md:**
- Update when project features change
- Keep installation instructions current
- Update examples if APIs change

**Code Comments:**
- Document why, not what
- Explain non-obvious decisions
- Add TODO comments for known issues
- Link to GitHub issues for context

### Working with Legacy Code

This project has legacy code that doesn't meet current standards. Our approach:

**Philosophy:**
- Don't block on legacy issues
- Fix what you touch
- Improve incrementally
- Document patterns to avoid

**Practical Guidelines:**
1. **New Code**: Must pass strict linting and type checking
2. **Modified Code**: Fix issues in files you're editing
3. **Legacy Code**: Leave alone unless it breaks
4. **Configuration**: Keep pragmatic ignores in `pyproject.toml`

**Tracking Improvement:**
- Monitor ruff/pyright error counts over time
- Quarterly review of ignored rules
- Remove ignores as code improves
- Celebrate when strictness can be increased

### Using Custom Commands

**Available Slash Commands:**
- `/document-lesson` - Add entry to LESSONS_LEARNED.md
- `/current-week` - Show current NFL week and schedule

**Creating New Commands:**
1. Create `.claude/commands/your-command.md`
2. Add description and prompt
3. Test with `/your-command`
4. Document in this section

## Resources

- Billy Walters' Principles: Information edge, statistical modeling, disciplined bankroll management
- NFL Data: Pro Football Reference, NFL.com, ESPN
- NCAAF Data: Sports Reference CFB, ESPN, NCAA.com
- Weather: NOAA, Weather.gov
- Python Libraries: pandas, numpy, scikit-learn, httpx, pydantic, anthropic, openai
- GitHub Actions: https://docs.github.com/en/actions
- Ruff Documentation: https://docs.astral.sh/ruff/
- Pyright Documentation: https://github.com/microsoft/pyright
