# Root Directory Cleanup Plan

## Current State: 78 files, 24 directories in root

## Proposed Organization

### 1. KEEP IN ROOT (Essential project files)
```
.env, .env.example        # Environment config
.gitignore, .gitattributes # Git config
pyproject.toml, uv.lock   # Package management
pytest.ini                # Test config
README.md                 # Project documentation
CLAUDE.md                 # AI assistant context
START_HERE.md             # Onboarding guide
```

### 2. MOVE TO scripts/ (Active utility scripts)
```
analyze_edges.py          → scripts/analysis/
analyze_edges_simple.py   → scripts/analysis/
analyze_simple.py         → scripts/analysis/
analyze_divergence.py     → scripts/analysis/
check_status.py           → scripts/utilities/
check_overtime_edges.py   → scripts/analysis/
clv_simple.py             → scripts/clv/
clv_track.py              → scripts/clv/
collect_odds.py           → scripts/scrapers/
collect_action_network.py → scripts/scrapers/
scrape_data.py            → scripts/scrapers/
simulate_betting.py       → scripts/backtest/
start_monitor.py          → scripts/monitoring/
view_opportunities.py     → scripts/utilities/
```

### 3. MOVE TO scripts/weekly/ (Week-specific scripts - reusable templates)
```
analyze_week12.py              → scripts/weekly/
example_week12_analysis.py     → scripts/weekly/
scrape_week12_odds.py          → scripts/weekly/
update_power_ratings_week12.py → scripts/weekly/
week12_analysis_working.py     → scripts/weekly/
week12_clv_recorder.py         → scripts/weekly/
week12_clv_updater.py          → scripts/weekly/
week12_collector.py            → scripts/weekly/
week12_line_monitor.py         → scripts/weekly/
week12_quick.py                → scripts/weekly/
```

### 4. MOVE TO scripts/data_collection/ (Data collectors)
```
collect_nfl_data_comprehensive.py → scripts/data_collection/
collect_nfl_data_improved.py      → scripts/data_collection/
nfl_team_data.py                  → scripts/data_collection/
```

### 5. MOVE TO archive/ (Old/deprecated/one-off files)
```
.env.backup                       → archive/env/
.env_master                       → archive/env/
env.template                      → archive/env/
pyproject.toml.bak.*              → archive/
fix_imports.py                    → archive/
diagnose_mcp.py                   → archive/diagnostics/
diagnose_nfl_structure.py         → archive/diagnostics/
mark_ratings_updated.py           → archive/
new_extract_function.txt          → archive/
nul                               → DELETE
sfactor_test_output.txt           → archive/test_outputs/
sfactor_test_results.txt          → archive/test_outputs/
signalr_test.log                  → archive/test_outputs/
test_output.txt                   → archive/test_outputs/
status_report.txt                 → archive/
scraper_output.log                → archive/logs/
overtime_screenshot.png           → archive/screenshots/
overtime_text_nfl_*.txt           → archive/snapshots/
python_file_inventory*.txt        → archive/
agent_memory.json                 → archive/
```

### 6. MOVE TO docs/ (Documentation)
```
AUDIT_SUMMARY.md                      → docs/audits/
DOCS_AUDIT.md                         → docs/audits/
DOCS_PHASE2.md                        → docs/audits/
DOCS_PHASE3.md                        → docs/audits/
IMPLEMENTATION_SUMMARY.md             → docs/
DATABASE_LOADING_SUMMARY.md           → docs/database/
DATA_COLLECTION_QUICK_REFERENCE.md    → docs/
ESPN_ENHANCEMENT_DEPLOYMENT_STATUS.txt → docs/status/
NCAAF_2025_HISTORICAL_DATA_STATUS.txt  → docs/status/
TROUBLESHOOTING.md                    → docs/
```

### 7. MOVE TO scripts/setup/ (Setup & config scripts)
```
setup_mcp.ps1             → scripts/setup/
test_analyzer.bat         → scripts/setup/
test_mcp.bat              → scripts/setup/
test_mcp_server.ps1       → scripts/setup/
test_system.bat           → scripts/setup/
test_single_game.py       → scripts/setup/
```

### 8. CONSOLIDATE (Reference modules that should be in src/)
```
billy_walters_edge_calculator.py  → Consider moving to src/walters_analyzer/core/
billy_walters_risk_config.py      → Consider moving to src/walters_analyzer/config/
```

### 9. DELETE (Unnecessary files)
```
nul                       # Empty/garbage file
requirements.txt          # Using pyproject.toml instead
scrapy.cfg                # Not using Scrapy
__pycache__/              # Should be in .gitignore
```

### 10. DIRECTORIES TO CONSOLIDATE
```
log/ + logs/              → Merge into logs/
output/                   → Keep (for generated files)
data/                     → Keep (for data files)
database/                 → Keep (for DB files)
snapshots/                → Move to archive/snapshots/
vendor/                   → Keep if needed, otherwise archive
```

## Final Clean Root Structure
```
billy-walters-sports-analyzer/
├── .env, .env.example    # Environment
├── .git/, .github/       # Git
├── .vscode/              # Editor config
├── pyproject.toml        # Package config
├── uv.lock               # Lock file
├── pytest.ini            # Test config
├── README.md             # Main docs
├── CLAUDE.md             # AI context
├── START_HERE.md         # Onboarding
├── src/                  # Source code (THE package)
├── tests/                # Test suite
├── scripts/              # Utility scripts (organized)
├── docs/                 # Documentation
├── data/                 # Data files
├── database/             # Database files
├── logs/                 # Log files
├── output/               # Generated output
├── archive/              # Old/deprecated files
└── examples/             # Example usage
```

## Execution Order
1. Create new subdirectories
2. Move documentation files
3. Move scripts by category
4. Move archive files
5. Delete garbage files
6. Remove empty directories
7. Update any imports if needed
