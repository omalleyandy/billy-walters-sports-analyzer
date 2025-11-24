Complete data collection for current NFL + NCAAF week - all sources in correct order.

Usage: /collect-all-data [options]

Examples:
- /collect-all-data (auto-detect current week for both leagues)
- /collect-all-data --league nfl (NFL only)
- /collect-all-data --league ncaaf (NCAAF only)
- /collect-all-data --week 11 (explicit week for both leagues)
- /collect-all-data --week 13 --league ncaaf (explicit NCAAF week)

This command executes the complete Billy Walters data collection workflow for both NFL and NCAAF:

Step 1: Power Ratings (Foundation)
- Massey Ratings scraper
- ESPN Power Rankings
- Historical ratings from database

Step 2: Game Schedules (Know What to Analyze)
- ESPN scoreboard API
- Game dates, times, locations
- Current scores if games started

Step 3: Team Statistics (Adjust Power Ratings)
- ESPN team stats API
- Offensive/defensive metrics
- Season-to-date performance

Step 4: Injury Reports (CRITICAL Billy Walters Factor)
- ESPN injury scraper
- NFL official injury reports
- Position-specific impact calculations
- Recovery timeline tracking

Step 5: Weather Forecasts (Game Context) - ✅ FIXED 2025-11-12
- AccuWeather API (primary) - Now working correctly with async/await
- OpenWeather API (fallback)
- Game-time forecasts (real temperature, wind speed, conditions)
- Indoor vs outdoor stadium (indoor returns None, saves API calls)
- Uses your ACCUWEATHER_API_KEY from .env
- ~8-10 API calls per run (only outdoor stadiums)

Step 6: Odds Data & Sharp Action (Market Lines) - **UPDATED 2025-11-23**
- Overtime.ag API (primary) - Direct API access, no browser required
  - Method: scrape_overtime_api.py
  - Speed: ~5 seconds for NFL + NCAAF
  - No authentication required
  - No CloudFlare/proxy issues
  - 100% data quality verified
  - Recommended: docs/overtime_devtools_analysis_results.md

- Action Network Sitemap (NEW 2025-11-23) - Game URLs & Sharp Action
  - Method: scrape_action_network_sitemap.py
  - Output: 18 NFL games, 120 NCAAF games
  - Categories: futures, odds, public-betting, strategy, teasers
  - Format: JSONL with full URL metadata
  - Data loader: src/data/action_network_loader.py
  - Integration: Ready for Billy Walters pipeline

- Hybrid scraper (optional, for live games only)
  - Method: scrape_overtime_hybrid.py
  - Use case: Sunday live monitoring
  - Not needed for pre-game workflow

Step 7: Billy Walters Analysis
- NFL edge detection (spreads) - uses billy_walters_edge_detector.py
- NFL edge detection (totals) - separate totals analysis
- NCAAF edge detection (NEW 2025-11-23) - uses ncaaf_edge_detector.py
- Injury impact calculations (position-specific for each league)
- Weather adjustments (league-specific thresholds)
- Value opportunity identification (both NFL and NCAAF)

Billy Walters Methodology Order:
1. Foundation (Power Ratings) → establish baseline
2. Context (Stats, Injuries, Weather) → adjust for game specifics
3. Market Analysis (Odds) → compare your line vs market
4. Edge Detection → identify betting value

Data Quality Checks:
- Validates all data sources
- Quality scoring (0-100%)
- Completeness checks
- Cross-source validation
- Alert on missing/invalid data

Output:
- Complete data summary report
- Validation results per source
- Data quality scores
- Collection duration
- Error log (if any)
- Next steps recommendations

Saved Data Locations:

NFL:
- data/current/nfl_week_N_games.json
- data/current/nfl_week_N_teams.json
- data/current/nfl_week_N_injuries.json
- data/current/nfl_week_N_weather.json
- data/current/nfl_week_N_odds_action.json
- output/overtime/nfl/pregame/api_walters_TIMESTAMP.json
- output/edge_detection/nfl_edges_detected_week_N.jsonl

NCAAF:
- data/current/ncaaf_week_N_games.json
- data/current/ncaaf_week_N_teams.json
- data/current/ncaaf_week_N_injuries.json
- data/current/ncaaf_week_N_weather.json
- output/overtime/ncaaf/pregame/api_walters_TIMESTAMP.json
- output/edge_detection/ncaaf_edges_detected_week_N.jsonl

Recommended Timing (Manual Execution):
Run this command Tuesday-Wednesday for best results:
- New week lines post after Monday Night Football
- Fresh injury reports
- Weather forecasts available
- Optimal for weekly analysis
- NOTE: No scheduled automation - run manually on-demand when ready
