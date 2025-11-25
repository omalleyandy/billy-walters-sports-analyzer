# Billy Walters Sports Analyzer - Documentation Index

This index provides quick navigation to all project documentation organized by topic.

**Last Update**: 2025-11-25 - Action Network Phase 3: Complete totals (O/U) extraction via dropdown switching

---

## Quick Start - Choose Your Path

### New User? Start Here (5 minutes)
**Goal**: Get the system running and collect your first week of data

1. **Setup** (2 min)
   - Install: `uv sync --all-extras --dev`
   - Configure: Copy `.env.example` to `.env`, add API keys
   - Verify: `uv run python -c "import src; print('OK')"`

2. **First Data Collection** (3 min)
   - Run: `/collect-all-data`
   - Validates: Power ratings, schedules, odds, weather, injuries
   - Output: `data/current/` and `output/edge_detection/`

**Next**: See [Weekly Workflow](#weekly-workflow) below

### Weekly Bettor? Use This (30 min/week)
**Goal**: Tuesday-Sunday workflow for finding betting edges

- **Tuesday (10 min)**: `/collect-all-data` - Complete data collection
- **Wednesday (10 min)**: `/edge-detector` + `/betting-card` - Find value
- **Thursday (5 min)**: `/scrape-overtime` - Refresh odds before TNF
- **Sunday (5 min)**: `/check-results` - Track performance

**Details**: See [Weekly Results Workflow](features/results_checker/WEEKLY_RESULTS_WORKFLOW.md)

### Developer? Start Here
**Goal**: Understand system architecture and contribute code

1. **Read**: [CLAUDE.md](../CLAUDE.md) - Core development rules
2. **Review**: [Architecture](technical/ARCHITECTURE.md) - System design
3. **Setup**: [CI/CD Prevention](guides/ci_cd_prevention_guide.md)
4. **Contribute**: [Git Workflow](../.github/GIT_WORKFLOW_GUIDE.md)

**Next**: [Testing & Quality](#testing--quality) section below

### Agent/Automation? Start Here
**Goal**: Automate data collection and edge detection

1. **Read**: [Agent Workflows](../.claude/AGENT_WORKFLOWS.md)
2. **Setup**: Configure hooks (`.claude/hooks/`)
3. **Test**: Run `/collect-all-data` with validation
4. **Monitor**: Track data quality scores

**Next**: [Billy Walters Workflow Commands](#commands) section below

---

## Command Quick Reference

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

**Optimal Schedule**: Tuesday (collect) → Wednesday (analyze) → Thursday (refresh) → Sunday (results)

---

## Most Common Questions

**Q: How do I get started quickly?**
→ See [Quick Start - Choose Your Path](#quick-start---choose-your-path) above

**Q: What's the optimal weekly schedule?**
→ Tue (collect) → Wed (analyze) → Thu (refresh) → Sun (results)

**Q: How do I ensure I'm analyzing the correct week's games?**
→ See [Edge Detector Workflow](guides/EDGE_DETECTOR_WORKFLOW.md) - automatic pre-flight validation ensures correct week

**Q: What does the edge detector pre-flight validation check?**
→ Validates: (1) Current system date, (2) Schedule file week, (3) Odds file week, (4) Cross-validates all sources

**Q: How do I check my betting performance?**
→ `/check-results --league nfl` (see [Betting Results Checker](features/results_checker/BETTING_RESULTS_CHECKER.md))

**Q: Why did my CI check fail?**
→ See [CI/CD Prevention Guide](guides/ci_cd_prevention_guide.md#prevention-checklist)

**Q: Where is the database documentation?**
→ **Start here**: [PostgreSQL Data Loading Workflow](technical/database/POSTGRES_DATA_LOADING_WORKFLOW.md) (NEW - 2025-11-24)
→ Also see: [Database Setup Guide](technical/database/DATABASE_SETUP_GUIDE.md) and [Quick Start Database](technical/database/QUICK_START_DATABASE.md)

**Q: How do I interpret edge detection results?**
→ 7+ pts = MAX BET, 4-7 = STRONG, 2-4 = MODERATE, 1-2 = LEAN, <1 = NO PLAY

---

## Getting Started

### Quick Start
- [Windows Setup Guide](guides/quickstart_windows_setup.md) - Windows installation & setup
- [MCP Setup Quick Start](guides/quickstart_mcp_setup.md) - Node.js & MCP Inspector setup
- [Weekly Workflow Quick Start](guides/quickstart_weekly_workflow.md) - Tuesday-Sunday betting workflow
- [Wednesday Workflow Quick Start](guides/quickstart_wednesday_workflow.md) - Mid-week analysis guide
- [Overtime Quick Start](guides/OVERTIME_QUICKSTART.md) - Overtime.ag scraping guide
- [Data Collection Guide](guides/DATA_COLLECTION_GUIDE.md) - Complete data collection workflow

### Installation & Configuration
- [GitHub Workflow Guide](guides/GITHUB_WORKFLOW_GUIDE.md) - Git and GitHub setup
- [CLI Reference](guides/CLI_REFERENCE.md) - Command-line interface usage

## Core Methodology

### Billy Walters Analysis
- [Billy Walters Methodology](guides/BILLY_WALTERS_METHODOLOGY.md) - Core betting principles
- [Billy Walters PRD v1.5](guides/billy_walters_analytics_prd_v1.5.md) - Product requirements
- [Advanced Master Class Sections](guides/methodology/) - Deep dive tutorials (5 sections)
- **See Also**: CLAUDE.md § "Football Analytics Best Practices" for weekly workflow

### Analysis Tools

#### Edge Detection (NEW - 2025-11-25)
**Automatic schedule validation ensures you're analyzing the correct week's games.**

- **[Edge Detector Workflow](guides/EDGE_DETECTOR_WORKFLOW.md)** - **START HERE** - Complete guide to pre-flight checks, schedule validation, and workflow integration
- [Edge Detection Implementation](../src/walters_analyzer/valuation/billy_walters_edge_detector.py) - Detect betting edges (NFL & NCAAF)
- [Schedule Validator System](../src/walters_analyzer/utils/schedule_validator.py) - Automatic week detection and cross-validation
- **Key Features:**
  - ✅ Automatic detection of current NFL/NCAAF week from system date
  - ✅ Validates schedule files against detected week
  - ✅ Validates odds files against detected week
  - ✅ Cross-validates all data sources before analysis
  - ✅ Clear warnings for week mismatches
  - ✅ Prevents analyzing wrong week's games

#### Other Analysis Tools
- [NCAAF Edge Detection Design](features/ncaaf/NCAAF_EDGE_DETECTION_DESIGN.md) - Architecture and implementation plan for college football edges
- [Power Ratings](features/power_ratings/) - Power rating system documentation
- [Feature Coverage](technical/FEATURE_COVERAGE.md) - Available analysis features
- **Reference**: CLAUDE.md § "Billy Walters Workflow Commands & Hooks" for all commands

## Data Collection

### League-Specific Workflows (NEW - 2025-11-25)

**CRITICAL**: NFL and NCAAF data are collected separately and never mixed.

- [LEAGUE SEPARATION GUIDE](guides/LEAGUE_SEPARATION_GUIDE.md) - **START HERE** - Master reference for keeping NFL/NCAAF data isolated
- [NFL Data Collection Workflow](guides/NFL_DATA_COLLECTION_WORKFLOW.md) - Complete Tuesday workflow for NFL (7 minutes, ~7 components)
- [NCAAF Data Collection Workflow](guides/NCAAF_DATA_COLLECTION_WORKFLOW.md) - Complete Wednesday workflow for NCAAF (7 minutes, ~7 components)
- [Data Collection Quick Reference](../DATA_COLLECTION_QUICK_REFERENCE.md) - Quick lookup guide with examples
- [Data Collection Architecture](guides/DATA_COLLECTION_ARCHITECTURE.md) - System design and method selection
- [Output Structure Verification](guides/DATA_OUTPUT_STRUCTURE_VERIFICATION.md) - Validation tools to ensure data integrity
- **Performance**: NFL ~7min, NCAAF ~7min (both tuned for optimal speed)

### Scrapers & APIs
- [API Integration Details](api/API_INTEGRATION_DETAILS.md) - **COMPREHENSIVE** - All API technical details (Weather, ESPN, Overtime, Action Network)
- [Overtime.ag Hybrid Scraper](data_sources/overtime/OVERTIME_HYBRID_SCRAPER.md) - **PRIMARY** odds source (Playwright + SignalR)
- [ESPN Documentation](api/espn/) - ESPN API integration (22 documents)
- [Action Network Quality Report](api/action_network/ACTION_NETWORK_DATA_QUALITY_REPORT.md) - ✅ Data assurance (512 records, 100% quality)
- [Action Network Setup](api/ACTION_NETWORK_SETUP.md) - Integration guide
- [API Integration Guide](api/API_INTEGRATION_GUIDE.md) - General API integration
- **Quick Reference**: CLAUDE.md § "Environment Variables & API Keys" for credentials setup

### Action Network Live Odds Scraper ✨ NEW (2025-11-25)
**Complete live odds extraction with spread, totals (O/U), and moneyline data.**

**Components:**
- **ActionNetworkClient** (`src/data/action_network_client.py`)
  - Playwright-based browser automation with login
  - Multi-selector fallback for CSS resilience
  - Dropdown switching for totals extraction
  - Rate limiting and retry logic

- **CLI Wrapper** (`scripts/scrapers/scrape_action_network_live.py`)
  - `--nfl`, `--ncaaf` flags for league selection
  - `--no-headless` for debugging
  - JSON output with timestamps

**Phase 3: Totals Extraction (NEW)**
- Automatic dropdown switching from "Spread" to "Total" view
- Parses over/under format: `o48.5\n-110\nu48.5\n-110`
- Merges totals back into game data
- 16/16 NFL games with complete O/U data

**Sample Output:**
```json
{
  "away_team": "Packers",
  "home_team": "Lions",
  "spread": 2.5,
  "spread_odds": -105,
  "over_under": 48.5,
  "total_odds": -110,
  "moneyline_away": -108,
  "moneyline_home": -112
}
```

**Usage:**
```bash
# Scrape NFL with visible browser (debugging)
uv run python scripts/scrapers/scrape_action_network_live.py --nfl --no-headless

# Scrape both leagues silently
uv run python scripts/scrapers/scrape_action_network_live.py --nfl --ncaaf --quiet
```

**Key Features:**
- ✅ Complete odds: spread + totals + moneyline
- ✅ Multi-selector fallback for UI resilience
- ✅ Dropdown switching for totals view
- ✅ 20/20 selector validation tests passing
- ✅ Production-ready with proper exit codes

## Performance & Results Checking

### NFL Scoreboard Client & Results Validator ✨ NEW (2025-11-24)
Complete automated system for fetching NFL game scores and validating edge detection predictions.

**Components:**
- **NFL Scoreboard Client** (`src/data/espn_nfl_scoreboard_client.py`)
  - Fetches actual game scores from ESPN API for any week (1-18)
  - Auto-detects current NFL week from system date
  - Supports historical score retrieval for entire season
  - JSON output for offline analysis

- **Results Validator** (`src/walters_analyzer/results/results_validator.py`)
  - Compares edge predictions vs actual game results
  - Calculates ATS (Against The Spread) performance
  - Computes ROI based on Kelly sizing
  - Team name ↔ abbreviation mapping (32 NFL teams)
  - Generates detailed markdown reports

**Week 12 Validation Results:**
- **Predictions**: 8 edge detection predictions
- **ATS Record**: 4 Wins - 3 Losses (57.1% win rate)
- **ROI**: +13.0% (positive return on investment)
- **Average Confidence**: 66.4 points
- **Status**: ✅ System fully operational

**Usage Example:**
```python
from walters_analyzer.results.results_validator import ResultsValidator

validator = ResultsValidator()
results = await validator.validate_week(12)
stats = validator.calculate_performance_stats(results)
report = await validator.generate_report(results, 12)
await validator.save_report(report, 12)
```

**Documentation**: [Week 12 Closeout & Week 13 Setup](guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md) - Complete workflow with results

**Key Features:**
- ✅ Automatic week detection from system date
- ✅ ESPN API integration for reliable scores
- ✅ Prediction-to-score matching with team mapping
- ✅ ATS, ROI, and confidence metrics
- ✅ Ready for full season tracking
- ✅ Historical score fetching capability

### Betting Results Checker ✅ (2025-11-23)
The complete system for evaluating betting predictions against actual game results, calculating performance metrics, and generating comprehensive reports.

**Documentation:**
- [Betting Results Checker](features/results_checker/BETTING_RESULTS_CHECKER.md) - **START HERE** - Complete user guide with examples, calculation details, troubleshooting
- [Results Checker Implementation Summary](features/results_checker/RESULTS_CHECKER_IMPLEMENTATION_SUMMARY.md) - Technical overview of architecture and components
- [Weekly Results Workflow](features/results_checker/WEEKLY_RESULTS_WORKFLOW.md) - Integration guide for Billy Walters workflow (Tuesday-Sunday schedule)

**Key Features:**
- ✅ ESPN API integration (NFL & NCAAF scores)
- ✅ Edge detection prediction parsing (JSONL format)
- ✅ ATS calculation (WIN/LOSS/PUSH)
- ✅ ROI computation (standard -110 vig)
- ✅ Margin error tracking (prediction accuracy)
- ✅ Comprehensive markdown reports (saved to `docs/performance_reports/`)

**Quick Start:**
```bash
# Check current week NFL results (auto-detects week)
uv run python scripts/analysis/check_betting_results.py --league nfl

# Check specific NCAAF week
uv run python scripts/analysis/check_betting_results.py --league ncaaf --week 13
```

**Test Status:** 18/18 tests passing (100% coverage)
**Integration:** Ready for production weekly workflow
**Reference**: CLAUDE.md § "Betting Results Checker Integration" for usage details

### Data Sources
- [NFL Injuries](data_sources/injuries_nfl.md) - NFL injury data schema
- [NCAAF Injuries](data_sources/injuries_ncaaf.md) - College football injury data
- [NFL Odds](data_sources/odds_nfl.md) - NFL betting odds format
- [NCAAF Odds](data_sources/odds_ncaaf.md) - College football odds format
- [Overtime.ag Documentation](data_sources/overtime/) - Odds source (6 documents)
- [Data Validation Guide](reports/DATA_VALIDATION_GUIDE.md) - Validate data quality

### Weather Integration
- [Weather Alerts](features/weather_alerts.md) - Weather impact analysis
- [W-Factor Calibration](../src/walters_analyzer/valuation/weather_impact.py) - Weather adjustment calculations

## Database & Data Storage

### PostgreSQL Data Loading (NEW - 2025-11-24) ✨
**Complete end-to-end data loading pipeline from collection to database**

- **[PostgreSQL Data Loading Workflow](technical/database/POSTGRES_DATA_LOADING_WORKFLOW.md)** - **START HERE** - Complete guide covering:
  - GameIDMapper: Intelligent game ID mapping between Overtime.ag and ESPN
  - Data flow: Collection → JSON → Database insertion
  - Table schemas: espn_schedules, games, odds, team_stats
  - Week-by-week workflow: Tuesday collection → Wednesday analysis
  - Verification queries and error handling
  - Performance benchmarks and next steps

- [Database Setup Guide](technical/database/DATABASE_SETUP_GUIDE.md) - PostgreSQL installation and schema creation
- [Quick Start Database](technical/database/QUICK_START_DATABASE.md) - 5-minute database setup
- [PostgreSQL Implementation Complete](technical/database/POSTGRES_IMPLEMENTATION_COMPLETE.md) - Technical implementation details

**Key Features (NEW):**
- ✅ **GameIDMapper**: Maps Overtime.ag game IDs to ESPN IDs with 2-day fuzzy matching
  - Handles timezone differences (Thursday/Sunday/Monday night games)
  - 100% success rate on NFL Week 13 (15/15 games)
  - Fast cached lookup (~100K games in memory)
- ✅ **Full Odds Loading**: Extracts nested dict odds format and stores with valid FK references
  - Handles spread: {home: -2.5, away: 2.5}
  - Handles moneyline: {home: -145, away: 125}
  - Handles total: {points: 49.0}
- ✅ **Games Table Population**: Copies schedules with league column for FK constraints
- ✅ **Data Verification**: ON CONFLICT DO NOTHING handles duplicates gracefully
- ✅ **Complete Pipeline**: Collection → Load → Validation in < 10 seconds

**Example Results (Week 13 NFL):**
- Schedules: 16 records
- Games table: 16 records
- Team stats: 32 records
- Odds: 15 records with complete betting data
- Errors: 0

## Development

### Core Documentation
- [Development Guidelines](../CLAUDE.md) - **PRIMARY** development guide
- [Agent Workflows](../.claude/AGENT_WORKFLOWS.md) - Autonomous agent automation guide
- [Troubleshooting Guide](../TROUBLESHOOTING.md) - Error resolution and solutions
- [Architecture](technical/ARCHITECTURE.md) - System architecture overview
- [CI/CD Documentation](../.github/CI_CD.md) - Continuous integration setup

### CI/CD Troubleshooting
- [CI/CD Prevention Guide](guides/ci_cd_prevention_guide.md) - ✅ **Comprehensive** - Prevent CI failures (formatting, types, tests)
- [CI Fix Archives](archive/fixes/) - Historical CI/CD fix documentation
- [Local Validation Checklist](guides/ci_cd_prevention_guide.md#prevention-checklist) - Run before every commit

### MCP Architecture
- [MCP Quick Start](technical/mcp/MCP_QUICK_START.md) - **START HERE** - 5-minute overview
- [MCP Architecture](technical/mcp/MCP_ARCHITECTURE.md) - Complete technical architecture (35+ pages)
- [MCP Phase 1 Implementation](technical/mcp/MCP_PHASE1_IMPLEMENTATION.md) - Step-by-step implementation guide
- [MCP Before/After Comparison](technical/mcp/MCP_BEFORE_AFTER.md) - Visual comparison and benefits
- [Existing MCP Server](../.claude/walters_mcp_server.py) - Current implementation (basic)

### Technical Guides & Troubleshooting
- [Testing Guide](guides/TESTING_GUIDE.md) - pytest framework and test execution
- [MCP Diagnostic Guide](guides/mcp_diagnostic_guide.md) - MCP server troubleshooting
- [Live Odds Scraper Guide](guides/LIVE_ODDS_SCRAPER_GUIDE.md) - Betting odds collection
- [Overtime Edge Detection Guide](guides/CHECK_OVERTIME_EDGES_GUIDE.md) - Finding betting edges in Overtime data
- [Monitor Setup Guide](guides/MONITOR_SETUP_GUIDE.md) - System monitoring configuration
- [Monitoring Reference](guides/monitoring_reference.md) - Monitoring best practices
- [Web Fetch Client](api/web_fetch_client.md) - HTTP client documentation

### Architecture & Technical Design
- [HTML Structure Analysis](technical/HTML_STRUCTURE_ANALYSIS.md) - overtime.ag HTML parsing reference
- [Dynamic Week Tracking](technical/DYNAMIC_WEEK_TRACKING.md) - Week detection system design
- [ESPN Roadmap](technical/ESPN_ROADMAP_CHECKLIST.md) - ESPN data integration implementation plan

### Developer Utilities
- [PowerShell Commands](utilities/powershell_commands.md) - Windows system commands reference

### Example Output
- [Example Edge Detection Output](guides/EXAMPLE_OUTPUT.md) - Sample output showing what users will see

### Legacy Technical References
- [Scraper Quick Reference](guides/SCRAPER_QUICK_REFERENCE.md) - All scrapers at a glance
- [Overtime Scraping Schedule](data_sources/overtime/OVERTIME_SCRAPING_SCHEDULE.md) - Optimal scraping times
- [Overtime Hybrid Scraper Details](data_sources/overtime/OVERTIME_HYBRID_SCRAPER.md) - Technical implementation
- [Overtime Technical Reference](guides/OVERTIME_TECHNICAL_REFERENCE.md) - Advanced details

### Scripts & Utilities
- **Scrapers**: `scripts/scrapers/` - Active data collection scripts
- **Analysis**: `scripts/analysis/` - Weekly analysis and edge detection
- **Validation**: `scripts/validation/` - Data quality checks
- **Dev Tools**: `scripts/dev/` - Debug and development utilities
- **Archive**: `scripts/archive/` - Legacy code (reference only)

## Testing & Quality

### Testing
- [Test Suite](../tests/) - 146+ test cases
- [Integration Tests](../tests/integration/) - End-to-end testing
- [Unit Tests](../tests/unit/) - Component testing
- [Validation Scripts](../scripts/validation/) - Data validation

### Quality Assurance
- [ESPN Data QA Report](reports/ESPN_DATA_QA_REPORT_2025-11-23.md) - ✅ **COMPLETE** - 56/56 tests passed (all 6 components)
- [ESPN Data QA Quick Reference](api/espn/ESPN_DATA_QA_QUICK_REFERENCE.md) - Test execution guide and troubleshooting
- [ESPN Data QA Test Inventory](api/espn/ESPN_DATA_QA_TEST_INVENTORY.md) - Detailed test listing by component
- [ESPN Data QA Deliverables](api/espn/ESPN_DATA_QA_DELIVERABLES.md) - Summary of QA testing deliverables
- [Example Output](guides/EXAMPLE_OUTPUT.md) - Expected output formats
- [Data Validation Guide](reports/DATA_VALIDATION_GUIDE.md) - Quality standards

## Week 12 Analysis (Current)

### Active Analysis
- [Week 12 Edge Detection](../output/edge_detection/week_12_edge_analysis.json) - 4 edges identified
- [Week 12 Injury-Adjusted Analysis](../output/edge_detection/week_12_injury_adjusted_edges.json) - Position-specific impacts
- **Final Plays**: CAR+4.0 (STRONG), DAL-1.5 (STRONG), TB+4.0 (MODERATE), CLE removed (QB out)
- **Reference**: CLAUDE.md § "Recent Updates (2025-11-23)" for complete session notes

### Weather Analysis (Week 12)
- [Week 12 Weather Data](../data/current/nfl_week_12_weather_corrected.json) - 7 outdoor stadiums (no extreme conditions)

## Reports & History

### Active Reports
- [Feature Coverage](technical/FEATURE_COVERAGE.md) - Current feature status
- [API Integration Complete](technical/API_INTEGRATION_COMPLETE.md) - Integration milestones
- [Action Network Quality Assurance](api/action_network/ACTION_NETWORK_DATA_QUALITY_REPORT.md) - ✅ 100% data quality validation

### Recent Session Notes (2025-11-23)
- [CLAUDE.md § Recent Updates](../CLAUDE.md#recent-updates-2025-11-12-to-2025-11-23) - AccuWeather fixes, Week 12 analysis, Action Network validation
- **NEW**: [ESPN Data QA Testing](reports/ESPN_DATA_QA_REPORT_2025-11-23.md) - ✅ Comprehensive QA of all 6 ESPN data collection components (56 tests, 100% pass rate)

### Archived Reports
- [Agent Optimization 2025-11-23](reports/AGENT_OPTIMIZATION_2025-11-23.md) - Agent documentation restructure
- [Sessions Archive](reports/archive/sessions/) - Development session notes
- [Week Archives](reports/archive/) - Week-by-week analysis history

## Project Organization

### Directory Structure
```
billy-walters-sports-analyzer/
├── src/
│   ├── data/                    # 27 data clients & scrapers
│   ├── walters_analyzer/        # Core analysis system
│   │   ├── valuation/           # Edge detection (11 modules)
│   │   ├── query/               # Display utilities (6 modules)
│   │   ├── backtest/            # Backtesting framework
│   │   └── ...
│   └── db/                      # Database layer
├── scripts/
│   ├── scrapers/                # Data collection
│   ├── analysis/                # Weekly analysis
│   ├── validation/              # Data validation
│   ├── utilities/               # Helper scripts
│   ├── dev/                     # Debug tools
│   └── archive/                 # Legacy code
├── tests/
│   ├── integration/             # Integration tests
│   └── unit/                    # Unit tests
├── docs/                        # Documentation (this directory)
│   ├── api/                     # API documentation
│   │   ├── espn/                # ESPN API docs (22 files)
│   │   └── action_network/      # Action Network docs (5 files)
│   ├── data_sources/            # Data schema docs
│   │   └── overtime/            # Overtime.ag docs (6 files)
│   ├── features/                # Feature documentation
│   │   ├── ncaaf/               # NCAAF-specific docs (7 files)
│   │   ├── nfl/                 # NFL-specific docs (8 files)
│   │   ├── power_ratings/       # Power rating docs (3 files)
│   │   ├── results_checker/     # Results checker docs (5 files)
│   │   └── sfactor/             # Situational factors (7 files)
│   ├── guides/                  # User guides
│   │   └── methodology/         # Billy Walters methodology (8 files)
│   ├── technical/               # Technical documentation
│   │   ├── database/            # Database docs (4 files)
│   │   ├── devtools/            # Chrome DevTools docs (2 files)
│   │   └── mcp/                 # MCP architecture docs (6 files)
│   ├── reports/                 # Reports and status
│   └── archive/                 # Historical documentation
│       ├── sessions/            # Session summaries
│       ├── fixes/               # Bug fix documentation
│       └── ...                  # Other archived docs
└── .claude/                     # Claude Code configuration
    ├── commands/                # Custom slash commands (14 commands)
    └── hooks/                   # Automation hooks (14 hooks)
```

## Quick Links by Task

### I want to collect betting odds
1. [Overtime Hybrid Scraper](data_sources/overtime/OVERTIME_HYBRID_SCRAPER.md)
2. [Overtime Quick Start](guides/OVERTIME_QUICKSTART.md)
3. [Scraper Quick Reference](guides/SCRAPER_QUICK_REFERENCE.md)

### I want to analyze games
1. [Billy Walters Methodology](guides/BILLY_WALTERS_METHODOLOGY.md)
2. [CLI Reference](guides/CLI_REFERENCE.md) - `/edge-detector`, `/betting-card`
3. [Power Ratings](features/power_ratings/)

### I want to check betting results
1. [Betting Results Checker](features/results_checker/BETTING_RESULTS_CHECKER.md) - Complete guide with examples
2. [Weekly Results Workflow](features/results_checker/WEEKLY_RESULTS_WORKFLOW.md) - Integration with Billy Walters workflow
3. [Results Checker Implementation](features/results_checker/RESULTS_CHECKER_IMPLEMENTATION_SUMMARY.md) - Technical overview

### I want to understand the system
1. [Development Guidelines](../CLAUDE.md)
2. [Architecture](technical/ARCHITECTURE.md)
3. [Feature Coverage](technical/FEATURE_COVERAGE.md)

### I need to troubleshoot
1. [CI/CD Prevention Guide](guides/ci_cd_prevention_guide.md) - Prevent failures before they happen
2. [CI Fix Archives](archive/fixes/) - Historical CI/CD fix documentation
3. [Troubleshooting Guide](../TROUBLESHOOTING.md) - Error resolution and solutions
4. [CI/CD Troubleshooting](../.github/CI_CD.md) - Technical CI/CD details
5. [Data Validation Guide](reports/DATA_VALIDATION_GUIDE.md) - Data quality issues

### I want to contribute
1. [Development Guidelines](../CLAUDE.md)
2. [GitHub Workflow Guide](guides/GITHUB_WORKFLOW_GUIDE.md)
3. [CI/CD Documentation](../.github/CI_CD.md)

### I want to build MCP servers
1. [MCP Quick Start](technical/mcp/MCP_QUICK_START.md) - Understand MCP in 5 minutes
2. [MCP Before/After](technical/mcp/MCP_BEFORE_AFTER.md) - See the benefits
3. [MCP Phase 1 Implementation](technical/mcp/MCP_PHASE1_IMPLEMENTATION.md) - Start building (4-6 hours)
4. [MCP Architecture](technical/mcp/MCP_ARCHITECTURE.md) - Full technical details

## External Resources

- **Billy Walters**: "Gambler: Secrets from a Life at Risk" (book)
- **NFL Data**: Pro Football Reference, NFL.com, ESPN
- **NCAAF Data**: Sports Reference CFB, ESPN, NCAA.com
- **Weather**: NOAA, Weather.gov, AccuWeather, OpenWeather
- **Python Libraries**: pandas, numpy, scikit-learn, httpx, pydantic, anthropic, openai

## Archived Documentation

Historical documentation is organized in `docs/archive/`:

- **Sessions**: `archive/sessions/` - Development session summaries (13+ archived)
- **Week-Specific**: `archive/week_specific/` - Week 12/13 analysis & guides
- **Phases**: `archive/phases/` - Completed phase implementations
- **Old Quick Start Variants**: `archive/old_quickstart_variants/` - Superseded by unified guides
- **Versions**: `archive/versions/` - Old configuration files and instruction versions
- **Setup**: `archive/setup/` - Completed setup tasks and Windows migration docs
- **Status**: `archive/status/` - Historical status reports
- **Fixes**: `archive/fixes/` - Bug fix documentation (CI/CD fixes, rating fixes, etc.)
- **Reviews**: `archive/reviews/` - Code review notes
- **Q&A**: `archive/q_and_a/` - Historical questions and answers
- **Raw Data**: `archive/raw_data/` - Large raw data files (e.g., HTML source dumps)
- **Unclear**: `archive/unclear/` - Files with uncertain purpose

**Note**: All currently-active documentation is in organized subdirectories: `docs/api/`, `docs/features/`, `docs/guides/`, `docs/technical/`, `docs/data_sources/`.

## Document Status Legend

- ✅ **Current** - Up-to-date, actively maintained
- 🔄 **Needs Update** - Partially outdated, scheduled for revision
- 📦 **Archived** - Historical reference only
- 🚧 **In Progress** - Under active development

---

**Last Updated**: 2025-11-25
**Project Status**: Production-ready with active development
**Documentation Reorganization**: Phase 4 complete! 125+ files migrated from docs root to categorized subdirectories. Root directory now contains only `_INDEX.md` and `README.md`.

**New Structure Summary**:
- `api/espn/` - 22 ESPN docs
- `api/action_network/` - 5 Action Network docs
- `features/ncaaf/` - 7 NCAAF docs
- `features/nfl/` - 8 NFL docs
- `features/sfactor/` - 7 Situational Factor docs
- `features/results_checker/` - 5 Results Checker docs
- `features/power_ratings/` - 3 Power Rating docs
- `technical/mcp/` - 6 MCP docs
- `technical/database/` - 4 Database docs
- `data_sources/overtime/` - 6 Overtime docs
- `guides/methodology/` - 8 Billy Walters methodology docs
- `archive/sessions/` - 13+ session reports
- `archive/fixes/` - CI/CD and bug fix docs

For the most current development guidelines, always refer to [CLAUDE.md](../CLAUDE.md).
