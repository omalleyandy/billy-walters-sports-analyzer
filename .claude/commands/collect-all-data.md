Complete data collection for current NFL week - all sources in correct order.

Usage: /collect-all-data [week]

Examples:
- /collect-all-data (auto-detect current week)
- /collect-all-data 11
- /collect-all-data 11 --no-odds (skip odds if APIs down)

This command executes the complete Billy Walters data collection workflow:

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

Step 5: Weather Forecasts (Game Context)
- AccuWeather API (primary)
- OpenWeather API (fallback)
- Game-time forecasts
- Indoor vs outdoor stadium

Step 6: Odds Data (Market Lines) - **UPDATED 2025-11-11: Now using API method**
- Overtime.ag API (primary) - NEW: Direct API access, no browser required
- Action Network scraper (sharp action)
- Opening lines
- Current lines
- Line movement tracking
- Fast (< 5 seconds vs 30+ seconds with browser)

Step 7: Billy Walters Analysis
- Edge detection (spreads)
- Edge detection (totals)
- Injury impact calculations
- Weather adjustments
- Value opportunity identification

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
- data/current/nfl_week_N_games.json
- data/current/nfl_week_N_teams.json
- data/current/nfl_week_N_injuries.json
- data/current/nfl_week_N_weather.json
- data/current/nfl_week_N_odds_action.json
- output/overtime_nfl_walters_TIMESTAMP.json

Recommended Timing (Manual Execution):
Run this command Tuesday-Wednesday for best results:
- New week lines post after Monday Night Football
- Fresh injury reports
- Weather forecasts available
- Optimal for weekly analysis
- NOTE: No scheduled automation - run manually on-demand when ready
