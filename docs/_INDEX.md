# Billy Walters Sports Analyzer - Documentation Index

This index provides quick navigation to all project documentation organized by topic.

## Getting Started

### Quick Start
- [Quick Start Guide](guides/QUICKSTART.md) - Get running in 5 minutes
- [Overtime Quick Start](guides/OVERTIME_QUICKSTART.md) - Overtime.ag scraping guide
- [Windows Setup Guide](guides/WINDOWS_SETUP_GUIDE.md) - Windows installation
- [Data Collection Guide](guides/DATA_COLLECTION_GUIDE.md) - Complete data collection workflow

### Installation & Configuration
- [GitHub Workflow Guide](guides/GITHUB_WORKFLOW_GUIDE.md) - Git and GitHub setup
- [CLI Reference](guides/CLI_REFERENCE.md) - Command-line interface usage

## Core Methodology

### Billy Walters Analysis
- [Billy Walters Methodology](guides/BILLY_WALTERS_METHODOLOGY.md) - Core betting principles
- [Billy Walters PRD v1.5](guides/billy_walters_analytics_prd_v1.5.md) - Product requirements
- [Advanced Master Class Sections](advanced-master-class-section-1.md) - Deep dive tutorials (5 sections)

### Analysis Tools
- [Edge Detection](../src/walters_analyzer/valuation/billy_walters_edge_detector.py) - Detect betting edges
- [Power Ratings](guides/README_POWER_RATINGS.md) - Power rating system
- [Feature Coverage](FEATURE_COVERAGE.md) - Available analysis features

## Data Collection

### Scrapers & APIs
- [Overtime.ag Hybrid Scraper](OVERTIME_HYBRID_SCRAPER.md) - **PRIMARY** odds source (Playwright + SignalR)
- [ESPN NCAAF Scoreboard](ESPN_NCAAF_SCOREBOARD.md) - College football scores
- [Action Network Setup](api/ACTION_NETWORK_SETUP.md) - Action Network integration
- [API Integration Guide](api/API_INTEGRATION_GUIDE.md) - General API integration

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
- [Lessons Learned](../LESSONS_LEARNED.md) - Troubleshooting and solutions
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

### Technical Guides
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
- [Example Output](guides/EXAMPLE_OUTPUT.md) - Expected output formats
- [Data Validation Guide](DATA_VALIDATION_GUIDE.md) - Quality standards

## Reports & History

### Active Reports
- [Feature Coverage](FEATURE_COVERAGE.md) - Current feature status
- [API Integration Complete](API_INTEGRATION_COMPLETE.md) - Integration milestones

### Archived Reports
- [Agent Optimization 2025-11-23](reports/AGENT_OPTIMIZATION_2025-11-23.md) - Agent documentation restructure & performance optimization
- [Sessions Archive](reports/archive/sessions/) - Development session notes
- [Week Archives](reports/archive/) - Week-by-week analysis history
- [Development Phases](reports/archive/) - Historical development reports

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

### I want to understand the system
1. [Development Guidelines](../CLAUDE.md)
2. [Architecture](ARCHITECTURE.md)
3. [Feature Coverage](FEATURE_COVERAGE.md)

### I need to troubleshoot
1. [CI/CD Prevention Guide](guides/ci_cd_prevention_guide.md) - Prevent failures before they happen
2. [CI Dependency Fix 2025-11-23](CI_DEPENDENCY_FIX_2025-11-23.md) - ✅ How to interpret CI failures
3. [Lessons Learned](../LESSONS_LEARNED.md) - Historical troubleshooting
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

## Document Status Legend

- ✅ **Current** - Up-to-date, actively maintained
- 🔄 **Needs Update** - Partially outdated, scheduled for revision
- 📦 **Archived** - Historical reference only
- 🚧 **In Progress** - Under active development

---

**Last Updated**: 2025-11-23
**Project Status**: Production-ready with active development
**New**: Agent automation workflows guide added (.claude/AGENT_WORKFLOWS.md)

For the most current development guidelines, always refer to [CLAUDE.md](../CLAUDE.md).
