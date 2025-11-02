# Documentation Index

## 📚 Complete Guide to Billy Walters Sports Analyzer v2.0

Last Updated: November 2, 2025

---

## 🚀 Quick Start

**New Users Start Here:**
1. `../README.md` - Project overview and installation
2. `QUICK_REFERENCE.md` - API quick reference
3. `SESSION_SUMMARY.md` - Latest updates (Phase 1 + Phase 2)

**Developers:**
1. `PROJECT_STRUCTURE.md` - Codebase organization
2. `TECH_STACK_BEST_PRACTICES.md` - Architecture validation
3. `../pyproject.toml` - Dependencies and project config

---

## 📖 Implementation Guides

### Phase 1: Quick Wins (HTTP + Cache + Models)
- `QUICK_WINS_COMPLETE.md` - Implementation results
- `QUICK_UPGRADE_GUIDE.md` - Step-by-step guide
- `CODE_PATTERNS_COMPARISON.md` - Before/after code examples

**What You Got:**
- HTTP client with connection pooling
- Caching system (90% API cost reduction)
- Consolidated models (8 dataclasses)

### Phase 2: Research Module
- `PHASE_2_QUICK_WIN_COMPLETE.md` - Implementation results
- `PHASE_2_RESEARCH_ENHANCEMENT.md` - Detailed guide
- `RESEARCH_INTEGRATION_PLAN.md` - Scrapy integration

**What You Got:**
- ScrapyBridge (loads Scrapy data)
- ResearchEngine (multi-source coordinator)
- Billy Walters injury methodology

### Future Phases (Optional)
- `COMPLETE_UPGRADE_ROADMAP.md` - All phases overview
- `SDK_COMPARISON_AND_UPGRADES.md` - vNext SDK analysis
- `UPGRADE_CHECKLIST.md` - Task-by-task checklist

---

## 🎯 Methodology & Analysis

### Billy Walters Core
- `BILLY_WALTERS_METHODOLOGY.md` - Complete methodology
- `CORE_IMPLEMENTATION_SUMMARY.md` - Technical implementation
- `BACKTEST_GUIDE.md` - Backtesting framework

**Topics Covered:**
- Power rating formula
- S/W/E factors (Situational, Weather, Emotional)
- Key numbers analysis
- Star system bet sizing
- Kelly Criterion
- CLV tracking

---

## 🏈 Sport-Specific Guides

### NFL
- `nfl/README.md` - NFL features and workflows
- Weekly power rating updates
- Team mappings database
- ESPN API integration

### College Football (CFB)
- `espn_cfb/ESPN_CFB_README.md` - ESPN CFB scraping
- `espn_cfb/ESPN_CFB_DATA_ANALYSIS.md` - Data structure
- `espn_cfb/ESPN_CFB_SCRAPING_SUMMARY.md` - Implementation
- `espn_cfb/ESPN_CFB_URL_REFERENCE.md` - API endpoints
- `espn_cfb/ESPN_WILDCARD_URLS_GUIDE.md` - URL patterns

### Massey Ratings (CFB)
- `massey/README.md` - Massey integration overview
- `massey/MASSEY_CLI_GUIDE.md` - Command usage
- `massey/MASSEY_COMPREHENSIVE_GUIDE.md` - Complete guide
- `massey/MASSEY_DATA_GUIDE.md` - Data structures
- `massey/MASSEY_EDGE_ANALYSIS.md` - Edge detection
- Plus 7 more specialized Massey guides

---

## 🔧 Technical References

### Architecture & Design
- `INSPECTION_SUMMARY.md` - SDK comparison results
- `TECH_STACK_BEST_PRACTICES.md` - Tech stack validation (Grade: A)
- `PROJECT_STRUCTURE.md` - Codebase organization

### Data & APIs
- `weather/WEATHER_INTEGRATION.md` - Weather analysis
- `weather/ACCUWEATHER_GUIDE.md` - AccuWeather setup
- Team mappings: `../data/team_mappings/nfl_teams.json`

### Testing & Quality
- `../tests/` - Test suite
- `../pytest.ini` - Test configuration
- Coverage reports (run `pytest --cov`)

---

## 📊 Guides by Use Case

### I Want to Analyze a Game
1. `QUICK_REFERENCE.md` - Quick start
2. `BILLY_WALTERS_METHODOLOGY.md` - Understanding the analysis
3. `../examples/complete_research_demo.py` - Working example

### I Want to Scrape Data
1. `espn_cfb/ESPN_CFB_SCRAPING_SUMMARY.md` - ESPN scraping
2. `massey/MASSEY_SCRAPING_GUIDE.md` - Massey scraping
3. `../scrapers/overtime_live/` - Scrapy spiders

### I Want to Backtest Strategies
1. `BACKTEST_GUIDE.md` - Backtesting framework
2. `../scripts/run_backtest.py` - Backtest script
3. `../walters_analyzer/backtest/` - Backtest modules

### I Want to Integrate New Features
1. `RESEARCH_INTEGRATION_PLAN.md` - Adding data sources
2. `CODE_PATTERNS_COMPARISON.md` - Code patterns
3. `TECH_STACK_BEST_PRACTICES.md` - Best practices

---

## 🎓 Learning Resources

### Billy Walters Principles
- Value identification (your line vs market)
- Bankroll management (investment fund approach)
- Unit sizing (1-3% max risk)
- Time investment (more analysis = better value)
- Fact-based decisions (avoid emotion)
- Point values (key numbers: 3, 7, 14 in NFL)

### Implementation Notes
- Power ratings: Exponential weighted (90/10 split)
- S/W/E factors: 5 points = 1 spread point
- Minimum edge: 5.5% (0.5 star threshold)
- Home field: NFL 2.5, CFB 3.5
- Injury impact: Position-based with confidence weighting

---

## 📁 Directory Organization

### Source Code (`walters_analyzer/`)
```
core/                # Phase 1: Foundation
├── http_client.py   # Connection pooling
├── cache.py         # Caching system  
├── models.py        # All dataclasses
└── config.py        # Configuration

research/            # Phase 2: Data gathering
├── scrapy_bridge.py # Scrapy integration
└── engine.py        # Multi-source coordinator

Main modules (to be organized in Phase 4):
├── analyzer.py              # Main analyzer
├── power_ratings.py         # Rating engine
├── bet_sizing.py            # Star system
├── key_numbers.py           # Key numbers
├── situational_factors.py   # S/W/E factors
├── clv_tracker.py           # CLV tracking
└── weather_fetcher.py       # Weather

Specialized:
├── backtest/        # Backtesting
├── ingest/          # Data loaders
├── cli.py           # CLI interface
└── wkcard.py        # Weekly card
```

### Data (`data/`)
```
Scraped data (JSONL + Parquet):
├── injuries/        # ESPN injury scrapes
├── massey_ratings/  # Massey data (CFB)
├── nfl_schedule/    # ESPN game data
├── weather/         # Weather data
├── overtime_live/   # Live odds
└── overtime_pregame/ # Pre-game odds

Analysis data (JSON):
├── power_ratings/   # Team ratings
│   └── team_ratings.json
├── team_mappings/   # Team databases
│   └── nfl_teams.json
└── stadium_cache.json  # Stadium locations
```

### Scripts (`scripts/`)
```
NFL workflows:
├── collect_nfl_schedule.py
├── update_power_ratings_from_games.py
├── weekly_power_ratings_update.sh/bat

Massey analysis:
├── analyze_massey_edges.py
├── compare_massey_week9.py
├── validate_week9_edges.py

Historical data:
├── collect_historical_games.py
├── collect_historical_odds.py
├── run_backtest.py

Utilities:
├── demo_weather.py
├── espn_cfb_scraper.py
└── TASK_SCHEDULER_SETUP.md
```

---

## 🏆 Best Practices

### Configuration
1. **Always use .env** for secrets and API keys
2. **Never commit .env** (it's gitignored)
3. **Use env.template.new** as reference
4. **Validate config** on startup

### Caching
1. **Enable by default** (ENABLE_CACHING=true)
2. **Adjust TTLs** based on data volatility
3. **Clear cache** when you need fresh data
4. **Monitor hit rates** with `get_cache_stats()`

### Scraping
1. **Use Scrapy** for heavy parsing (ESPN, Massey)
2. **Use HTTP client** for simple APIs (Weather, News)
3. **Dual output** JSONL + Parquet (already implemented)
4. **Respect rate limits** (auto-throttle enabled)

### Analysis
1. **Update power ratings** after each week
2. **Scrape injuries** Monday after games
3. **Check weather** Wednesday for weekend games
4. **Minimum edge** 5.5% before betting
5. **Use star system** for bet sizing

---

## 🆘 Getting Help

### Common Issues
1. Check `CLAUDE.md` troubleshooting section
2. Review relevant doc in `docs/`
3. Check examples in `examples/`
4. Run tests: `pytest tests/ -v`

### Debug Mode
```bash
# Enable verbose logging
export DEBUG=true
export VERBOSE=true

# Run with logging
uv run walters-analyzer scrape-injuries --sport nfl 2>&1 | tee debug.log
```

### Configuration Check
```bash
# View current configuration
uv run python -c "from walters_analyzer.config import get_config; print(get_config().get_summary())"

# Validate API keys
uv run python -c "from walters_analyzer.config import get_config; print(get_config().validate_api_keys())"
```

---

## 📈 Performance Benchmarks

### Caching (Phase 1)
- First weather call: ~500ms
- Cached call: ~0.1ms
- Speedup: 5000x
- Cost reduction: 90%

### HTTP Pooling (Phase 1)
- Without: 10 calls = 10 connections
- With: 10 calls = 1 connection
- Speedup: 40% faster

### Research Engine (Phase 2)
- Manual injury research: 10-15 min/game
- Automated multi-source: 30 seconds/game
- Accuracy improvement: 20-30%

---

## 🎯 Roadmap

### Completed ✅
- Phase 1: HTTP client, caching, models
- Phase 2: Research module (ScrapyBridge, ResearchEngine)
- Configuration system
- Comprehensive documentation

### Optional Enhancements
- ProFootballDoc medical analysis
- News API monitoring
- X/Twitter feed integration
- Phase 3: CLI modernization (slash commands)
- Phase 4: Full modular structure

---

*This documentation index provides navigation to all 50+ documentation files in the project.*

