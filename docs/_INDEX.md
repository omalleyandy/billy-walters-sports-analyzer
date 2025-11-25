# Billy Walters Sports Analyzer - Documentation Index

This index provides quick navigation to all project documentation organized by topic.

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

**Details**: See [Weekly Results Workflow](WEEKLY_RESULTS_WORKFLOW.md)

### Developer? Start Here
**Goal**: Understand system architecture and contribute code

1. **Read**: [CLAUDE.md](../CLAUDE.md) - Core development rules
2. **Review**: [Architecture](ARCHITECTURE.md) - System design
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

**Q: How do I check my betting performance?**
→ `/check-results --league nfl` (see [Betting Results Checker](BETTING_RESULTS_CHECKER.md))

**Q: Why did my CI check fail?**
→ See [CI/CD Prevention Guide](guides/ci_cd_prevention_guide.md#prevention-checklist)

**Q: Where is the database documentation?**
→ [Database Setup Guide](DATABASE_SETUP_GUIDE.md) and [Quick Start Database](QUICK_START_DATABASE.md)

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
- [Advanced Master Class Sections](advanced-master-class-section-1.md) - Deep dive tutorials (5 sections)
- **See Also**: CLAUDE.md § "Football Analytics Best Practices" for weekly workflow

### Analysis Tools
- [Edge Detection](../src/walters_analyzer/valuation/billy_walters_edge_detector.py) - Detect betting edges (NFL)
- [NCAAF Edge Detection Design](NCAAF_EDGE_DETECTION_DESIGN.md) - **NEW** ✨ Architecture and implementation plan for college football edges (separate from NFL)
- [Power Ratings](guides/README_POWER_RATINGS.md) - Power rating system
- [Feature Coverage](FEATURE_COVERAGE.md) - Available analysis features
- **Reference**: CLAUDE.md § "Billy Walters Workflow Commands & Hooks" for all commands

## Data Collection

### Scrapers & APIs
- [API Integration Details](api/API_INTEGRATION_DETAILS.md) - **COMPREHENSIVE** - All API technical details (Weather, ESPN, Overtime, Action Network)
- [Overtime.ag Hybrid Scraper](OVERTIME_HYBRID_SCRAPER.md) - **PRIMARY** odds source (Playwright + SignalR)
- [ESPN NCAAF Scoreboard](ESPN_NCAAF_SCOREBOARD.md) - College football scores
- [Action Network Quality Report](ACTION_NETWORK_DATA_QUALITY_REPORT.md) - ✅ Data assurance (512 records, 100% quality)
- [Action Network Setup](api/ACTION_NETWORK_SETUP.md) - Integration guide
- [API Integration Guide](api/API_INTEGRATION_GUIDE.md) - General API integration
- **Quick Reference**: CLAUDE.md § "Environment Variables & API Keys" for credentials setup

## Performance & Results Checking

### Betting Results Checker ✅ NEW (2025-11-23)
The complete system for evaluating betting predictions against actual game results, calculating performance metrics, and generating comprehensive reports.

**Documentation:**
- [Betting Results Checker](BETTING_RESULTS_CHECKER.md) - **START HERE** - Complete user guide with examples, calculation details, troubleshooting
- [Results Checker Implementation Summary](RESULTS_CHECKER_IMPLEMENTATION_SUMMARY.md) - Technical overview of architecture and components
- [Weekly Results Workflow](WEEKLY_RESULTS_WORKFLOW.md) - Integration guide for Billy Walters workflow (Tuesday-Sunday schedule)

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
- [Data Validation Guide](DATA_VALIDATION_GUIDE.md) - Validate data quality

### Weather Integration
- [Weather Alerts](features/weather_alerts.md) - Weather impact analysis
- [W-Factor Calibration](../src/walters_analyzer/valuation/weather_impact.py) - Weather adjustment calculations

## Development

### Core Documentation
- [Development Guidelines](../CLAUDE.md) - **PRIMARY** development guide
- [Agent Workflows](../.claude/AGENT_WORKFLOWS.md) - **NEW** ✨ Autonomous agent automation guide
- [Troubleshooting Guide](../TROUBLESHOOTING.md) - Error resolution and solutions
- [Architecture](ARCHITECTURE.md) - System architecture overview
- [CI/CD Documentation](../.github/CI_CD.md) - Continuous integration setup

### CI/CD Troubleshooting
- [CI/CD Prevention Guide](guides/ci_cd_prevention_guide.md) - ✅ **Comprehensive** - Prevent CI failures (formatting, types, tests)
- [CI Dependency Fix 2025-11-23](CI_DEPENDENCY_FIX_2025-11-23.md) - ✅ **RESOLVED** - How to interpret CI failures correctly
- [Local Validation Checklist](guides/ci_cd_prevention_guide.md#prevention-checklist) - Run before every commit

### MCP Architecture (NEW) 🆕
- [MCP Quick Start](MCP_QUICK_START.md) - **START HERE** - 5-minute overview
- [MCP Architecture](MCP_ARCHITECTURE.md) - Complete technical architecture (35+ pages)
- [MCP Phase 1 Implementation](MCP_PHASE1_IMPLEMENTATION.md) - Step-by-step implementation guide
- [MCP Before/After Comparison](MCP_BEFORE_AFTER.md) - Visual comparison and benefits
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
- [Scraper Quick Reference](SCRAPER_QUICK_REFERENCE.md) - All scrapers at a glance
- [Overtime Scraping Schedule](OVERTIME_SCRAPING_SCHEDULE.md) - Optimal scraping times
- [Overtime Hybrid Scraper Details](OVERTIME_HYBRID_SCRAPER.md) - Technical implementation
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
- [ESPN Data QA Quick Reference](ESPN_DATA_QA_QUICK_REFERENCE.md) - Test execution guide and troubleshooting
- [ESPN Data QA Test Inventory](ESPN_DATA_QA_TEST_INVENTORY.md) - Detailed test listing by component
- [ESPN Data QA Deliverables](ESPN_DATA_QA_DELIVERABLES.md) - Summary of QA testing deliverables
- [Example Output](guides/EXAMPLE_OUTPUT.md) - Expected output formats
- [Data Validation Guide](DATA_VALIDATION_GUIDE.md) - Quality standards

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
- [Feature Coverage](FEATURE_COVERAGE.md) - Current feature status
- [API Integration Complete](API_INTEGRATION_COMPLETE.md) - Integration milestones
- [Action Network Quality Assurance](ACTION_NETWORK_DATA_QUALITY_REPORT.md) - ✅ 100% data quality validation

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
│   ├── guides/                  # User guides
│   ├── api/                     # API documentation
│   ├── data_sources/            # Data schema docs
│   ├── features/                # Feature documentation
│   └── reports/archive/         # Historical reports
└── .claude/                     # Claude Code configuration
    ├── commands/                # Custom slash commands (14 commands)
    └── hooks/                   # Automation hooks (3 hooks)
```

## Quick Links by Task

### I want to collect betting odds
1. [Overtime Hybrid Scraper](OVERTIME_HYBRID_SCRAPER.md)
2. [Overtime Quick Start](guides/OVERTIME_QUICKSTART.md)
3. [Scraper Quick Reference](SCRAPER_QUICK_REFERENCE.md)

### I want to analyze games
1. [Billy Walters Methodology](guides/BILLY_WALTERS_METHODOLOGY.md)
2. [CLI Reference](guides/CLI_REFERENCE.md) - `/edge-detector`, `/betting-card`
3. [Power Ratings](guides/README_POWER_RATINGS.md)

### I want to check betting results
1. [Betting Results Checker](BETTING_RESULTS_CHECKER.md) - Complete guide with examples
2. [Weekly Results Workflow](WEEKLY_RESULTS_WORKFLOW.md) - Integration with Billy Walters workflow
3. [Results Checker Implementation](RESULTS_CHECKER_IMPLEMENTATION_SUMMARY.md) - Technical overview

### I want to understand the system
1. [Development Guidelines](../CLAUDE.md)
2. [Architecture](ARCHITECTURE.md)
3. [Feature Coverage](FEATURE_COVERAGE.md)

### I need to troubleshoot
1. [CI/CD Prevention Guide](guides/ci_cd_prevention_guide.md) - Prevent failures before they happen
2. [CI Dependency Fix 2025-11-23](CI_DEPENDENCY_FIX_2025-11-23.md) - ✅ How to interpret CI failures
3. [Troubleshooting Guide](../TROUBLESHOOTING.md) - Error resolution and solutions
4. [CI/CD Troubleshooting](../.github/CI_CD.md) - Technical CI/CD details
5. [Data Validation Guide](DATA_VALIDATION_GUIDE.md) - Data quality issues

### I want to contribute
1. [Development Guidelines](../CLAUDE.md)
2. [GitHub Workflow Guide](guides/GITHUB_WORKFLOW_GUIDE.md)
3. [CI/CD Documentation](../.github/CI_CD.md)

### I want to build MCP servers (NEW) 🆕
1. [MCP Quick Start](MCP_QUICK_START.md) - Understand MCP in 5 minutes
2. [MCP Before/After](MCP_BEFORE_AFTER.md) - See the benefits
3. [MCP Phase 1 Implementation](MCP_PHASE1_IMPLEMENTATION.md) - Start building (4-6 hours)
4. [MCP Architecture](MCP_ARCHITECTURE.md) - Full technical details

## External Resources

- **Billy Walters**: "Gambler: Secrets from a Life at Risk" (book)
- **NFL Data**: Pro Football Reference, NFL.com, ESPN
- **NCAAF Data**: Sports Reference CFB, ESPN, NCAA.com
- **Weather**: NOAA, Weather.gov, AccuWeather, OpenWeather
- **Python Libraries**: pandas, numpy, scikit-learn, httpx, pydantic, anthropic, openai

## Archived Documentation

Historical documentation is organized in `docs/archive/`:

- **Sessions**: `archive/sessions/` - Development session summaries (8 archived)
- **Week-Specific**: `archive/week_specific/` - Week 12/13 analysis & guides (9 archived, includes Phase 3 additions)
- **Phases**: `archive/phases/` - Completed phase implementations (4 archived)
- **Old Quick Start Variants**: `archive/old_quickstart_variants/` - Superseded by unified guides (2 archived)
- **Versions**: `archive/versions/` - Old configuration files and instruction versions (3 archived)
- **Setup**: `archive/setup/` - Completed setup tasks (1 archived)
- **Status**: `archive/status/` - Historical status reports (2 archived)
- **Fixes**: `archive/fixes/` - Bug fix documentation (2 archived)
- **Reviews**: `archive/reviews/` - Code review notes (1 archived)
- **Q&A**: `archive/q_and_a/` - Historical questions and answers (1 archived)
- **Unclear**: `archive/unclear/` - Files with uncertain purpose (1 archived)

**Note**: All currently-active documentation is at root level or in `docs/guides/`, `docs/api/`, `docs/technical/`, `docs/utilities/`, etc.

## Document Status Legend

- ✅ **Current** - Up-to-date, actively maintained
- 🔄 **Needs Update** - Partially outdated, scheduled for revision
- 📦 **Archived** - Historical reference only
- 🚧 **In Progress** - Under active development

---

**Last Updated**: 2025-11-24
**Project Status**: Production-ready with active development
**Documentation Reorganization**: Phase 3 complete! Technical docs moved to `docs/technical/`, utilities organized, archives complete. Root directory: 60 → 7 files (88% reduction)

For the most current development guidelines, always refer to [CLAUDE.md](../CLAUDE.md).
