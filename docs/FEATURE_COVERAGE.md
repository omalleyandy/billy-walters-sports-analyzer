# Feature Coverage Matrix

Cross-references the project reports with the codebase so we can quickly see what is already implemented and which promises still need work.

| Feature / Promise | Source Report(s) | Code Location(s) | Status |
| --- | --- | --- | --- |
| Chrome DevTools Cloudflare bypass for overtime.ag odds | [CHROME_DEVTOOLS_BREAKTHROUGH.md](reports/CHROME_DEVTOOLS_BREAKTHROUGH.md) | `walters_analyzer/ingest/chrome_devtools_scraper.py`, `scripts/scrape_odds_mcp.py`, `.codex/commands/scrape-overtime.ps1` | ✅ Implemented – CLI exposes `scrape-overtime`, scraper reads DevTools snapshots |
| Injury extraction accuracy & Billy Walters valuation (519 players validated) | [_START_HERE.md](reports/_START_HERE.md), [DATA_QUALITY_REVIEW.md](reports/DATA_QUALITY_REVIEW.md) | `walters_analyzer/valuation/*`, `tests/test_text_extraction.py`, `scripts/collect_all_data.ps1` | ✅ Implemented – valuation core + tests in place |
| Week card workflow with gating + dry run / live modes | [_START_HERE.md](reports/_START_HERE.md), [README_INVESTIGATION_COMPLETE.md](reports/README_INVESTIGATION_COMPLETE.md) | `walters_analyzer/wkcard.py`, CLI `wk-card` command, `.codex/scripts/wk-card-adv.ps1` | ✅ Implemented – card loader, validator, CLI flags |
| Highlightly research feed (teams, bookmakers, odds) | [README_INVESTIGATION_COMPLETE.md](reports/README_INVESTIGATION_COMPLETE.md) | `walters_analyzer/feeds/highlightly_client.py`, CLI `scrape-highlightly`, `test_highlightly_integration.py` | ✅ Implemented – async client + tests |
| Power rating & injury-weighted backtests | [BACKTEST_RESULTS_SUMMARY.md](reports/BACKTEST_RESULTS_SUMMARY.md) | `walters_analyzer/backtest/power_rating_backtest.py`, `tests/test_scraper_backtest.py` | ✅ Implemented – reproduces doc metrics |
| Professional core analysis engine (`core/analyzer.py`, bankroll mgmt, EV calculator) | [INTEGRATION_ANALYSIS.md](reports/INTEGRATION_ANALYSIS.md) | `walters_analyzer/core/*` (new analyzer, bankroll, calculator, key number modules) | ✅ Implemented – new core package now ships with the repo |
| Research engine (AccuWeather, ProFootballDoc, Highlightly fusion) | [INTEGRATION_ANALYSIS.md](reports/INTEGRATION_ANALYSIS.md) | `.claude` tooling covers MCP hooks, but no `walters_analyzer/research` package yet | ⚠️ Pending – future work after core engine lands |
| Autonomy / MCP integration (Claude Desktop tools) | [INTEGRATION_ANALYSIS.md](reports/INTEGRATION_ANALYSIS.md), [_INVESTIGATION_AND_ORGANIZATION_COMPLETE.md](reports/_INVESTIGATION_AND_ORGANIZATION_COMPLETE.md) | `.claude/walters_mcp_server.py`, `.claude/walters_autonomous_agent.py`, `.claude/README.md` | ✅ Implemented outside the Python package (Claude tooling) |

> **How to use this file:** when a report lands in `docs/reports/` or `docs/reports/archive/`, add any new promises/features here and link them to the code that fulfills them. If the code does not exist yet, mark it ⚠️ and open a task so we can close the gap.
