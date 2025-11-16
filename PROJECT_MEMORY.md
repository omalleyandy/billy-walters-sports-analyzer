# Billy Walters Sports Analyzer - Project Memory
**Last Updated**: November 15, 2025

## 🎯 Current System Status

### Active Season Tracking
- **NFL**: Week 11 (November 14-20, 2025)
- **NCAAF FBS**: Week 12 (November 15-21, 2025)
- **Tracking**: Fully automated via `season_calendar.py`

### Current Implementation Version
- **System Version**: v0.8.0 Beta
- **Instructions Version**: 2.0 (Dynamic Week Tracking)
- **Season Calendar**: Enhanced with NCAAF support

---

## 📅 Dynamic Week Tracking System

### Overview
Implemented November 15, 2025 to eliminate hardcoded week references and enable automatic week detection for both NFL and NCAAF seasons.

### Key Module: `src/walters_analyzer/season_calendar.py`

**Capabilities**:
- Automatic current week detection for NFL (1-18)
- Automatic current week detection for NCAAF FBS (0-14)
- Season phase tracking (offseason, preseason, regular, playoffs, championship)
- Date range calculation for any week
- Human-readable status formatting

**Usage Pattern**:
```python
from walters_analyzer.season_calendar import get_nfl_week, get_ncaaf_week

# Get current weeks (returns None if season inactive)
nfl_week = get_nfl_week()      # e.g., 11
ncaaf_week = get_ncaaf_week()  # e.g., 12

# Validate before analysis
if nfl_week is None:
    print("NFL season not active")
    exit(1)
```

**Command Line Check**:
```bash
cd src && uv run python -m walters_analyzer.season_calendar
```

### Why This Matters

**Before (Hardcoded)**:
- Week 5 referenced throughout codebase
- Manual updates required each week
- Risk of analyzing wrong week's games
- No validation mechanism

**After (Dynamic)**:
- Current week auto-detected from current date
- No manual updates needed
- Built-in validation prevents wrong-week analysis
- Multi-league support (NFL + NCAAF)

### Integration Points

**Required in ALL analysis scripts**:
1. Import season calendar functions
2. Get current week before any analysis
3. Validate week is not None (season active)
4. Use current week for data fetching/analysis

**Example Integration**:
```python
from walters_analyzer.season_calendar import get_nfl_week, format_season_status, League

# Start of script
current_week = get_nfl_week()
if current_week is None:
    print("⚠️ NFL regular season not active")
    exit(1)

print(f"✅ Analyzing {format_season_status(league=League.NFL)}")
print(f"   Current Week: {current_week}")

# Rest of analysis using current_week...
```

---

## 🗂️ Key Files & Documentation

### Core Implementation Files
1. **src/walters_analyzer/season_calendar.py** - Week detection engine
2. **PROJECT_INSTRUCTIONS_V2.md** - Updated instructions with dynamic weeks
3. **DYNAMIC_WEEK_TRACKING_SUMMARY.md** - Implementation details

### Main Documentation
- **README.md** - Primary project documentation
- **PROJECT_INSTRUCTIONS_V2.md** - AI assistant operating instructions
- **.claude/README.md** - MCP server and autonomous agent guide

### Methodology Documents
All Billy Walters methodology files in `/mnt/project/`:
- `billy_walters_nfl_power_ratings_system.md`
- `billy_walters_methodology_audit.md`
- `billy_walters_cheat_card.md`
- Plus 30+ supporting methodology files

---

## 💡 Critical System Principles

### 1. Accuracy Over Speed
- Always validate current week FIRST
- Verify schedules against official sources
- Double-check all calculations
- Flag uncertainties explicitly

### 2. Mathematical Rigor
- Every bet needs quantified edge (minimum 5.5%)
- Show all calculations transparently
- Use Billy Walters formulas (90/10, S-factors, Kelly)
- No recommendations without math backing

### 3. Risk Management (Sacred Rules)
- Never exceed 3% on single bet
- Never exceed 15% weekly total exposure
- Stop-loss at 10% weekly drawdown
- Use fractional Kelly at 25%

### 4. Process Over Results
- Don't judge on <100 bets
- Track Closing Line Value (CLV) as primary metric
- Analyze process failures, not outcome failures
- Trust the math during losing streaks

### 5. Weekly Validation Workflow
```bash
# MANDATORY: Before any weekly analysis
1. cd src && uv run python -m walters_analyzer.season_calendar
2. Verify current week matches your analysis target
3. Fetch schedules for verified week only
4. Cross-reference for bye weeks
5. Proceed with analysis
```

---

## 📊 Data Sources & Infrastructure

### Active Data Sources
- **overtime.ag**: Live odds via Chrome DevTools
- **Massey Ratings**: Power ratings via Playwright
- **ESPN**: Schedules, stats, injury reports
- **AccuWeather**: Game-day weather conditions
- **Highlightly**: Advanced analytics (optional)

### Data Organization
```
data/
├── injuries/
│   ├── nfl/        # NFL injury reports
│   └── ncaaf/      # NCAAF injury reports
├── odds/
│   ├── nfl/        # NFL betting lines
│   └── ncaaf/      # NCAAF betting lines
├── power_ratings/
│   ├── nfl_2025_week_01.json → nfl_2025_week_11.json
│   └── ncaaf_2025_week_11.json
└── current/        # Latest data snapshots
```

### Output Organization
```
output/
├── overtime/       # overtime.ag scraped data
├── unified/        # Combined data sets
├── billy_walters/  # Analysis outputs
└── weekly_reports/ # Generated reports
```

---

## 🔧 Development Tools & Commands

### Package Management
```bash
uv sync                  # Core dependencies
uv sync --extra ai       # All AI/ML features
uv sync --extra mcp      # Claude Desktop integration
uv sync --extra ml       # Machine learning
uv sync --extra research # Research APIs
uv sync --extra dev      # Development tools
```

### Testing
```bash
uv run pytest tests/ -v                           # All tests
uv run pytest tests/ --cov=walters_analyzer       # With coverage
uv run pytest tests/test_season_calendar.py -v    # Specific module
```

### Analysis Commands
```bash
# Quick game analysis
uv run walters-analyzer analyze-game \
  --home "Kansas City Chiefs" \
  --away "Buffalo Bills" \
  --spread -2.5 \
  --research \
  --bankroll 10000

# Week card analysis
uv run walters-analyzer wk-card \
  --file ./cards/wk-card-current.json \
  --dry-run \
  --show-bankroll

# Data scraping
uv run walters-analyzer scrape-overtime --sport nfl
uv run walters-analyzer scrape-injuries --sport nfl
```

---

## 🎯 Current Focus Areas

### Completed (v0.8.0)
- ✅ Dynamic week tracking (Nov 15, 2025)
- ✅ MCP server integration
- ✅ Autonomous agent with reasoning chains
- ✅ Chrome DevTools scraping
- ✅ Billy Walters methodology implementation
- ✅ ML infrastructure (XGBoost, scikit-learn)

### In Progress
- 🔧 Test suite completion (52/58 passing)
- 🔧 Code consolidation (duplicate directories)
- 🔧 Root directory organization

### Next Steps
1. Complete test coverage to 100%
2. Consolidate duplicate code directories
3. Implement automated weekly reports
4. Enhanced backtesting with larger samples
5. Production deployment guide

---

## 📈 Performance Tracking

### Sample Size Requirements
- **Minimum**: 100 bets for statistical validity
- **Current**: Building toward 100-bet sample
- **Target Win Rate**: 54-57% long-term
- **Target ROI**: 5-8% sustainable

### Key Metrics
1. **CLV (Closing Line Value)**: Primary success indicator
2. **Win Rate**: Secondary (variance-heavy short-term)
3. **Process Adherence**: Methodology compliance
4. **Risk Management**: Limit compliance

### Historical Performance
- NFL Week 10: 5-2-1 (62.5% win rate, 40.43% ROI)
- Note: Small sample, expect regression to mean

---

## 🔐 Security & Configuration

### Environment Variables
```bash
# Required
OV_CUSTOMER_ID=your_overtime_id
OV_CUSTOMER_PASSWORD=your_overtime_password

# Optional
PROXY_URL=http://user:pass@proxy:port
ACCUWEATHER_API_KEY=your_key
HIGHLIGHTLY_API_KEY=your_key
WALTERS_API_KEY=your_key
```

### Data Privacy
- All data stored locally
- No cloud dependencies for core features
- API keys managed via .env (not committed)
- Proxy recommended for IP protection

---

## 🚀 Quick Reference Commands

### Daily Workflow
```bash
# 1. Check current week
cd src && uv run python -m walters_analyzer.season_calendar

# 2. Scrape latest data
uv run walters-analyzer scrape-overtime --sport nfl
uv run walters-analyzer scrape-injuries --sport nfl

# 3. Analyze opportunities
uv run walters-analyzer analyze-game \
  --home "Team A" --away "Team B" --spread -3.5

# 4. Review and place bets (manual decision)
```

### Weekly Setup
```bash
# Sunday night: Update power ratings
cd scripts && uv run python weekly_power_rating_update.py

# Tuesday: Generate week card
# Review opportunities and create betting card

# Wednesday-Thursday: Place favorite bets
# Saturday: Place underdog bets
```

### Maintenance
```bash
# Update dependencies
uv sync --upgrade

# Run tests
uv run pytest tests/ -v

# Organize documentation
uv run python scripts/organize_docs.py

# Check system status
uv run walters-analyzer --version
```

---

## 📝 Notes for Future Sessions

### When Starting New Analysis
1. ✅ Always verify current week first
2. ✅ Check data freshness (<24 hours)
3. ✅ Validate power ratings updated
4. ✅ Confirm no bye weeks in analysis
5. ✅ Review bankroll before sizing bets

### When Debugging Issues
1. Check season_calendar output
2. Verify .env configuration
3. Review logs in ./logs directory
4. Check snapshots/ for scraping issues
5. Validate data schema in output files

### When Adding Features
1. Read PROJECT_INSTRUCTIONS_V2.md first
2. Check Billy Walters methodology alignment
3. Write tests before implementation
4. Update documentation
5. Run full test suite

### When Evaluating Performance
1. Verify sample size ≥100 bets
2. Calculate CLV percentage
3. Review process adherence
4. Check risk management compliance
5. Analyze trends, not single weeks

---

## 🔄 Change Log

### November 15, 2025
- **Added**: Dynamic week tracking system
- **Enhanced**: season_calendar.py with NCAAF support
- **Created**: PROJECT_INSTRUCTIONS_V2.md
- **Removed**: All hardcoded Week 5 references
- **Updated**: Project memory file (this file)

### November 12, 2025
- NFL Week 10 performance: 5-2-1 (62.5% win rate)
- Implemented overtime.ag API integration
- Completed power rating backfill

### November 6-11, 2025
- Completed Phase 7 (Automation)
- Completed Phase 6 (Interactive mode)
- Completed Phase 5 (AI-Enhanced scraper)
- MCP server integration
- Autonomous agent implementation

---

**Remember**: This system emphasizes **accuracy over speed**, **process over results**, and **risk management above all**. Trust the math, follow the methodology, and let the large sample size prove the edge.

**Version**: 2.0  
**Last Review**: November 15, 2025  
**Next Review**: End of 2025 NFL Regular Season
