# CLI Reference - Billy Walters Sports Analyzer

This document provides comprehensive reference for all CLI commands in the Billy Walters Sports Analyzer.

## Table of Contents

### Analysis Commands
- [analyze-game](#analyze-game) - NEW! Full Billy Walters game analysis
- [wk-card](#wk-card) - Week card betting workflow

### Data Collection Commands
- [scrape-overtime](#scrape-overtime) - Scrape odds from overtime.ag
- [scrape-injuries](#scrape-injuries) - Scrape injury reports
- [scrape-highlightly](#scrape-highlightly) - Scrape data from Highlightly API

### Data Management Commands
- [view-odds](#view-odds) - View scraped odds data
- [monitor-sharp](#monitor-sharp) - Monitor sharp money movements

### TIER 1 Data Population Scripts
- [populate-team-trends](#populate-team-trends) - Calculate team streaks and desperation levels
- [populate-swe-weather](#populate-swe-weather) - Calculate weather-based SWE adjustments
- [scrape-practice-reports](#scrape-practice-reports) - Collect practice reports for Wednesday signal
- [populate-player-valuations](#populate-player-valuations) - Generate baseline player point values

---

## analyze-game

**NEW!** Analyze a single game using the complete Billy Walters methodology with bankroll-aware recommendations.

### Features
- Power rating-based predictions
- Injury impact analysis (point values)
- Key number detection (3, 7, 6, 10, 14)
- Kelly Criterion bankroll management
- Research integration (injuries, weather)
- Detailed recommendation output

### Usage

```bash
# Basic analysis with spread
uv run walters-analyzer analyze-game \
  --home "Philadelphia Eagles" \
  --away "Dallas Cowboys" \
  --spread -3.0

# Full analysis with research integration
uv run walters-analyzer analyze-game \
  --home "Kansas City Chiefs" \
  --away "Buffalo Bills" \
  --spread -2.5 \
  --home-price -105 \
  --away-price -115 \
  --venue "Arrowhead Stadium" \
  --date 2025-11-10 \
  --bankroll 10000 \
  --research
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--home` | string | Yes | - | Home team name |
| `--away` | string | Yes | - | Away team name |
| `--spread` | float | No | - | Current spread (home perspective) |
| `--total` | float | No | - | Current total |
| `--home-price` | int | No | -110 | Home spread price (American odds) |
| `--away-price` | int | No | -110 | Away spread price (American odds) |
| `--venue` | string | No | - | Stadium/venue for weather lookup |
| `--date` | string | No | - | Game date (YYYY-MM-DD format) |
| `--bankroll` | float | No | 10000.0 | Starting bankroll amount |
| `--research` | flag | No | false | Fetch live injury/weather data |

### Example Output

```
================================================================================
BILLY WALTERS GAME ANALYSIS
================================================================================

Matchup:  Dallas Cowboys @ Philadelphia Eagles
Spread:   Philadelphia Eagles -3.0 (-110/-110)

HOME TEAM INJURIES:
  Total Impact: +0.4 pts
  • Player Name (QB): -2.5 pts
  • Player Name (WR): -1.2 pts

AWAY TEAM INJURIES:
  Total Impact: +0.5 pts
  • Player Name (CB): -1.8 pts
  • Player Name (LB): -0.7 pts

ANALYSIS:
  Predicted Spread: +0.1
  Market Spread:    -3.0
  Edge:             +3.1 pts
  Confidence:       High Confidence

KEY NUMBER ALERTS:
  [!] Projection crosses 3 (moving toward the underdog)

================================================================================
RECOMMENDATION: High Confidence
================================================================================
Bet Type:      SPREAD
Team:          Philadelphia Eagles
Edge:          +3.1 pts
Win Prob:      64.0%
Stake:         3.00% ($300.00)

Notes:
  • Net injury advantage: +0.1 pts
  • Predicted spread +0.1 vs market -3.0
  • Projection crosses 3 (moving toward the underdog)
```

### Confidence Levels

| Edge (pts) | Confidence Level | Kelly Stake |
|-----------|------------------|-------------|
| < 1.0 | No Play | 0% |
| 1.0-1.9 | Slight Edge | 0.5-1.5% |
| 2.0-2.9 | Elevated Confidence | 1.5-3.0% |
| ≥ 3.0 | High Confidence | 3.0% (max) |

### Research Integration

When `--research` flag is used:
1. **Injury Data**: Fetches from ProFootballDoc cache or live scraping
2. **Weather Data**: Queries AccuWeather API for venue conditions
3. **Point Values**: Each injury assigned point impact based on position/status

---

## wk-card

Run or preview a week card JSON with betting entries.

### NEW Features
- `--show-bankroll` - Display Kelly Criterion stake recommendations
- `--bankroll` - Specify starting bankroll amount

### Usage

```bash
# Basic preview
uv run walters-analyzer wk-card --file cards/week10.json --dry-run

# With bankroll display
uv run walters-analyzer wk-card \
  --file cards/week10.json \
  --dry-run \
  --show-bankroll \
  --bankroll 10000
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--file` | path | Yes | - | Path to week card JSON |
| `--dry-run` | flag | No | false | Preview without placing bets |
| `--show-bankroll` | flag | No | false | Show Kelly stake percentages |
| `--bankroll` | float | No | 10000.0 | Starting bankroll amount |

### Example Output

```
Wk-Card 2025-11-10 | source=manual | dry_run=True | Bankroll=$10,000.00
- 101 Philadelphia Eagles vs Dallas Cowboys
  spread: Eagles -3.0 (size=2u, max_juice=-110) → 2.50% ($250.00)
  moneyline: Eagles (max_price=-150, size=1u) → 1.20% ($120.00)
```

---

## scrape-overtime

Scrape odds from overtime.ag sportsbook.

### Usage

```bash
# Scrape NFL pre-game odds
uv run walters-analyzer scrape-overtime --sport nfl

# Scrape live betting odds
uv run walters-analyzer scrape-overtime --sport nfl --live

# Custom output directory
uv run walters-analyzer scrape-overtime \
  --sport both \
  --output-dir data/custom_odds
```

### Arguments

| Argument | Type | Choices | Default | Description |
|----------|------|---------|---------|-------------|
| `--sport` | string | nfl, cfb, both | both | Sport to scrape |
| `--live` | flag | - | false | Scrape live odds |
| `--output-dir` | path | - | auto | Output directory |

---

## scrape-injuries

Scrape injury reports from ESPN.

### Usage

```bash
# Scrape NFL injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Scrape college football injuries
uv run walters-analyzer scrape-injuries --sport cfb

# Custom output directory
uv run walters-analyzer scrape-injuries \
  --sport nfl \
  --output-dir data/custom_injuries
```

### Arguments

| Argument | Type | Choices | Default | Description |
|----------|------|---------|---------|-------------|
| `--sport` | string | nfl, cfb | cfb | Sport to scrape |
| `--output-dir` | path | - | auto | Output directory |

---

## scrape-highlightly

Scrape data from Highlightly API (requires API key).

### Usage

```bash
# Scrape teams
uv run walters-analyzer scrape-highlightly \
  --endpoint teams \
  --sport nfl

# Scrape today's matches
uv run walters-analyzer scrape-highlightly \
  --endpoint matches \
  --sport nfl \
  --date 2025-11-08

# Scrape odds for a specific match
uv run walters-analyzer scrape-highlightly \
  --endpoint odds \
  --sport nfl \
  --match-id 12345 \
  --odds-type prematch
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--endpoint` | string | Yes | API endpoint (teams, matches, odds, etc.) |
| `--sport` | string | No | Sport (nfl, ncaaf, both) |
| `--date` | string | No | Date filter (YYYY-MM-DD) |
| `--match-id` | int | No | Match ID for specific game |
| `--team-id` | int | No | Team ID for statistics |
| `--odds-type` | string | No | Odds type (prematch, live) |

---

## view-odds

View scraped odds data with filtering and export options.

### Usage

```bash
# View latest odds
uv run walters-analyzer view-odds

# View today's games
uv run walters-analyzer view-odds --today

# Filter by team
uv run walters-analyzer view-odds \
  --team "Eagles" \
  --upcoming 7

# Export to CSV
uv run walters-analyzer view-odds \
  --sport nfl \
  --upcoming 7 \
  --export odds_export.csv
```

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--data-dir` | path | Data directory (default: data/overtime_live) |
| `--file` | path | Specific JSONL file to load |
| `--sport` | string | Filter by sport (nfl, college_football) |
| `--date` | string | Filter by date (YYYY-MM-DD) |
| `--today` | flag | Show today's games |
| `--upcoming` | int | Show games in next N days |
| `--team` | string | Filter by team name (partial match) |
| `--compare` | string | Compare lines for a team |
| `--summary` | flag | Show summary only |
| `--brief` | flag | Brief output (no odds details) |
| `--export` | path | Export to CSV file |

---

## monitor-sharp

Monitor market for sharp money movements.

### Usage

```bash
# Test connection
uv run walters-analyzer monitor-sharp --test

# Monitor NFL for 2 hours
uv run walters-analyzer monitor-sharp \
  --sport nfl \
  --duration 120

# Monitor specific game
uv run walters-analyzer monitor-sharp \
  --sport nfl \
  --game-id "chiefs_bills_2025-11-10" \
  --duration 60 \
  --interval 30
```

### Arguments

| Argument | Type | Choices | Default | Description |
|----------|------|---------|---------|-------------|
| `--sport` | string | nfl, ncaaf, nba, mlb, nhl | nfl | Sport to monitor |
| `--game-id` | string | - | - | Specific game to monitor |
| `--duration` | int | - | 120 | Duration in minutes |
| `--interval` | int | - | settings | Check interval in seconds |
| `--test` | flag | - | false | Test API connection |

---

## TIER 1 Data Population Scripts

### Overview

The following scripts populate TIER 1 critical tables in the database. These tables enhance edge detection with:
- **Team Trends**: Streaks, desperation levels, emotional factors
- **Weather SWE Factors**: Special/Weather/Emotional adjustments
- **Practice Reports**: Wednesday signal for injury tracking
- **Player Valuations**: Baseline point values for injury impact calculation

These scripts are designed to work with existing data (game results, weather data) and can be run independently or as part of the full data pipeline.

---

## populate-team-trends

Calculate team streaks, desperation levels, and emotional state from game results and standings.

### Purpose

Populates the `team_trends` table with:
- Win/loss streaks (direction and length)
- Recent form percentage (0.0-1.0)
- Playoff position and ranking
- Desperation level (0-10 scale)
- Emotional state inference (confident, neutral, desperate)

### Usage

```bash
# Populate NFL team trends for current week
uv run python scripts/data_population/populate_team_trends.py --league nfl --season 2025

# Populate specific week (Week 13)
uv run python scripts/data_population/populate_team_trends.py \
  --league nfl \
  --week 13 \
  --season 2025

# Populate NCAAF with verbose output
uv run python scripts/data_population/populate_team_trends.py \
  --league ncaaf \
  --season 2025 \
  --verbose
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--league` | string | Yes | - | League: nfl or ncaaf |
| `--week` | int | No | current | Week number (1-18 NFL, 1-15 NCAAF) |
| `--season` | int | No | 2025 | Season year |
| `--verbose` | flag | No | false | Show detailed progress |

### Data Calculated

| Field | Calculation | Range | Example |
|-------|-----------|-------|---------|
| `streak_direction` | W/L from last 6 games | W or L | W |
| `streak_length` | Consecutive wins/losses | 1-6 | 3 |
| `recent_form_pct` | Wins/(Wins+Losses) last 4 | 0.0-1.0 | 0.75 |
| `playoff_position` | Current standings rank | 1-16 | 2 |
| `desperation_level` | 0=clinched, 10=must-win | 0-10 | 5 |
| `emotional_state` | confident/neutral/desperate | string | confident |

### Example Output

```
Populating team trends for NFL Season 2025 Week 13
  Kansas City Chiefs (Team ID 1):
    - Streak: W3 (recent form: 0.75)
    - Playoff: Position 1 (Clinched)
    - Emotional: Confident (Desperation: 0)
  Buffalo Bills (Team ID 2):
    - Streak: L2 (recent form: 0.25)
    - Playoff: Position 7 (Edge)
    - Emotional: Neutral (Desperation: 5)

Completed: 32 teams processed, 32 trends inserted
```

### Dependencies

- **Requires**: `game_results` table with ATS data
- **Requires**: `team_standings` table with current playoff position
- **Uses**: Last 6 games to calculate streaks

---

## populate-swe-weather

Calculate weather-based Special/Weather/Emotional (SWE) adjustments for games.

### Purpose

Populates the `game_swe_factors` table with weather impact on game outcomes:
- Temperature impact (-2.0 to +1.0 pts)
- Wind impact (-1.5 to 0.0 pts)
- Precipitation impact (-2.0 to 0.0 pts)
- Total adjustment clamped to -3.0 to +1.0 pts
- Confidence level (0.9 - weather is measurable)

### Usage

```bash
# Populate weather factors for NFL current week
uv run python scripts/data_population/populate_swe_weather.py --league nfl --season 2025

# Populate specific week
uv run python scripts/data_population/populate_swe_weather.py \
  --league nfl \
  --week 13 \
  --season 2025 \
  --verbose

# Process past weeks (backfill)
uv run python scripts/data_population/populate_swe_weather.py \
  --league nfl \
  --week 1 \
  --weeks 13 \
  --season 2025
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--league` | string | Yes | - | League: nfl or ncaaf |
| `--week` | int | No | current | Starting week |
| `--weeks` | int | No | 1 | Number of weeks to process |
| `--season` | int | No | 2025 | Season year |
| `--verbose` | flag | No | false | Show detailed calculations |

### Weather Impact Rules

| Factor | Condition | Impact | Example |
|--------|-----------|--------|---------|
| Temperature | <20°F | -2.0 to -1.5 | Extreme cold |
| | 20-50°F | -1.5 to 0.0 | Cold |
| | 50-85°F | 0.0 | Comfortable |
| | >85°F | +0.5 to +1.0 | Hot |
| Wind | 0-10 mph | 0.0 to -0.5 | Light |
| | 10-20 mph | -0.5 to -1.5 | Moderate |
| | >20 mph | -1.5 to -2.5 | Strong |
| Precipitation | Clear | 0.0 | No impact |
| | Light rain/snow | -0.5 to -1.0 | Slight |
| | Heavy rain/snow | -1.5 to -2.0 | Significant |

### Example Output

```
Processing weather factors for NFL Season 2025 Week 13

Game: Kansas City @ Buffalo (2025-11-30)
  Temperature: 15°F → Impact: -1.5 pts
  Wind: 18 mph → Impact: -1.0 pts
  Precipitation: Light snow → Impact: -0.5 pts
  Total Adjustment: -3.0 pts (clamped from -3.0)
  Confidence: 0.90

Game: Dallas @ Philadelphia (2025-12-01)
  Temperature: 48°F → Impact: -0.5 pts
  Wind: 8 mph → Impact: 0.0 pts
  Precipitation: Clear → Impact: 0.0 pts
  Total Adjustment: -0.5 pts
  Confidence: 0.90

Completed: 14 games processed, 14 SWE factors inserted
```

### Dependencies

- **Requires**: `game_schedules` table with game dates/venues
- **Requires**: AccuWeather API for historical weather data
- **Optional**: Weather data in `weather_data` table (fallback to API)

---

## scrape-practice-reports

Collect practice participation reports from NFL.com for Wednesday signal detection.

### Purpose

Populates the `practice_reports` table with player participation data:
- Full Participation (FP), Limited (LP), Did Not Practice (DNP)
- Tracks changes day-by-day (Mon-Fri)
- Detects trends (improving, declining, stable)
- Wednesday participation is Billy Walters' key signal

### Usage

```bash
# Scrape current week practice reports
uv run python scripts/scrapers/scrape_practice_reports.py --week 13 --season 2025

# Scrape multiple weeks
uv run python scripts/scrapers/scrape_practice_reports.py \
  --week 1 \
  --weeks 13 \
  --season 2025

# Verbose output with detailed logging
uv run python scripts/scrapers/scrape_practice_reports.py \
  --week 13 \
  --season 2025 \
  --verbose
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--week` | int | No | current | Starting week |
| `--weeks` | int | No | 1 | Number of weeks to process |
| `--season` | int | No | 2025 | Season year |
| `--verbose` | flag | No | false | Show detailed scraping progress |

### Participation Status Mapping

| Status | Code | Severity | Sessions | Impact |
|--------|------|----------|----------|--------|
| Full Participation | FP | mild | 3/3 | Healthy |
| Limited Participation | LP | moderate | 2/3 | Questionable |
| Did Not Practice | DNP | severe | 0/3 | Probable/Out |

### Example Output

```
Scraping practice reports for NFL Week 13 Season 2025

Kansas City Chiefs:
  Patrick Mahomes (QB):
    Wed (2025-11-26): FP (Full Participation) - Mild
    Trend: stable
  Isiah Pacheco (RB):
    Mon (2025-11-24): DNP (Did Not Practice) - Severe
    Tue (2025-11-25): LP (Limited Participation) - Moderate
    Wed (2025-11-26): FP (Full Participation) - Mild
    Trend: improving ← KEY SIGNAL

Dallas Cowboys:
  Dak Prescott (QB):
    Wed (2025-11-26): LP (Limited Participation) - Moderate
    Trend: declining ← CAUTION

Completed: 32 teams, 285 players, 423 practice reports
Output: output/practice_reports/nfl/week_13_practices.json
```

### Implementation Status

- **Current**: Placeholder with NFL.com parsing logic
- **Next**: Playwright browser automation for live scraping
- **Data Flow**: NFL.com → JSON → practice_reports table

### Dependencies

- **Requires**: Schedule data with game dates (for dating practice reports)
- **Optional**: Playwright for live scraping (not required for current version)

---

## populate-player-valuations

Generate baseline player point values based on position and depth chart position.

### Purpose

Populates the `player_valuations` table with baseline impact values:
- Position tiers: elite, above_average, average
- Point values: 0.4 (reserve) to 4.5 (elite QB)
- Snap count: 100% (baseline assumption)
- Ready for weekly updates with actual snap counts

### Usage

```bash
# Generate baseline valuations for current season
uv run python scripts/data_population/populate_player_valuations_baseline.py \
  --league nfl \
  --season 2025

# Generate for NCAAF
uv run python scripts/data_population/populate_player_valuations_baseline.py \
  --league ncaaf \
  --season 2025

# Verbose output
uv run python scripts/data_population/populate_player_valuations_baseline.py \
  --league nfl \
  --season 2025 \
  --verbose
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--league` | string | Yes | - | League: nfl or ncaaf |
| `--season` | int | No | 2025 | Season year |
| `--verbose` | flag | No | false | Show detailed progress |

### Position Point Values

| Position | Elite | Above Average | Average | Use Case |
|----------|-------|----------------|---------|----------|
| QB | 4.5 | 3.5 | 2.5 | Tier 1 impact |
| RB | 2.0 | 1.8 | 1.2 | Starter advantage |
| WR | 1.5 | 1.2 | 0.8 | Group impact |
| TE | 1.5 | 1.2 | 0.8 | Premier value |
| OL | 1.0 | 0.8 | 0.5 | Cumulative |
| DL | 1.2 | 1.0 | 0.6 | Pass rush |
| LB | 1.0 | 0.8 | 0.5 | Run defense |
| DB | 0.8 | 0.6 | 0.4 | Coverage |
| K/P | 1.0/0.8 | 0.8/0.6 | 0.5/0.4 | Situational |

### Depth Chart Position Mapping

| Depth Position | Tier | Point Value | Notes |
|---|---|---|---|
| 1 | Elite | Position × elite factor | Starter |
| 2 | Above Average | Position × above_avg factor | Backup |
| 3+ | Average | Position × average factor | Third string |

### Example Output

```
Populating baseline player valuations for NFL 2025

Kansas City Chiefs (32 players):
  Patrick Mahomes (QB, Depth 1) → Point Value: 4.5
  Isiah Pacheco (RB, Depth 1) → Point Value: 2.0
  JuJu Smith-Schuster (WR, Depth 1) → Point Value: 1.5
  Travis Kelce (TE, Depth 1) → Point Value: 1.5

Dallas Cowboys (28 players):
  Dak Prescott (QB, Depth 1) → Point Value: 4.5
  Ezekiel Elliott (RB, Depth 2) → Point Value: 1.8
  CeeDee Lamb (WR, Depth 1) → Point Value: 1.5

Completed: 32 teams, 896 players
Output: All 896 player valuations inserted to database
```

### Data Model

```json
{
  "league_id": 1,
  "team_id": 1,
  "player_id": "mahomes_pat",
  "player_name": "Patrick Mahomes",
  "position": "QB",
  "season": 2025,
  "point_value": 4.5,
  "snap_count_pct": 100.0,
  "impact_rating": 4.5,
  "is_starter": true,
  "depth_chart_position": 1,
  "source": "depth_chart_baseline",
  "notes": "Baseline from 1 depth chart position"
}
```

### Integration with Injury Reports

When a player is injured:
1. Look up `point_value` from `player_valuations` table
2. Multiply by injury severity (0.5-1.0)
3. Add to total injury impact for the team
4. Use in edge detection adjustment (±10-20% confidence)

### Dependencies

- **Requires**: ESPN depth charts (currently mocked)
- **Optional**: Future integration with ESPN/PFF live depth charts
- **Updates**: Weekly snap counts will overlay this baseline

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# AccuWeather (for weather data)
ACCUWEATHER_API_KEY=your_key_here

# The Odds API (for sharp money monitoring)
ODDS_API_KEY=your_key_here

# Highlightly API (for odds tracking)
HIGHLIGHTLY_API_KEY=your_key_here
```

### Settings File

Customize behavior in `walters_analyzer/config/settings.py`:

```python
# Bankroll management
max_bet_pct = 3.0          # Maximum bet as % of bankroll
min_bet_pct = 0.5          # Minimum bet as % of bankroll
fractional_kelly = 0.5     # Use half-Kelly for safety

# Key numbers (NFL)
key_numbers = [3, 7, 6, 10, 14]

# Confidence thresholds
confidence_buckets = [
    (3.0, "High Confidence"),
    (2.0, "Elevated Confidence"),
    (1.0, "Slight Edge"),
]
```

---

## Best Practices

### 1. Daily Workflow

```bash
# Morning: Scrape fresh data
uv run walters-analyzer scrape-injuries --sport nfl
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --date $(date +%Y-%m-%d)

# Afternoon: Analyze games
uv run walters-analyzer analyze-game \
  --home "Team A" \
  --away "Team B" \
  --spread -3.5 \
  --research \
  --bankroll 10000

# Pre-game: Monitor for sharp moves
uv run walters-analyzer monitor-sharp --sport nfl --duration 60
```

### 2. Bankroll Management

- Start with fractional Kelly (50% of full Kelly)
- Max 3% of bankroll on any single bet
- Track performance and adjust over time
- Never chase losses

### 3. Research Integration

- Use `--research` flag for fresh injury/weather data
- Run scrapers daily to keep cache updated
- Verify critical injuries manually
- Check weather for outdoor games

### 4. Key Number Awareness

Pay special attention when analysis crosses key numbers:
- **3 & 7**: Most common NFL margins
- **6**: Two field goals
- **10**: Touchdown + field goal
- **14**: Two touchdowns

---

## Troubleshooting

### Missing Dependencies

```bash
# Install all optional dependencies
uv sync --all-extras

# Or install specific groups
uv pip install -e ".[scraping,mcp,ml]"
```

### API Key Issues

```bash
# Test AccuWeather
echo $ACCUWEATHER_API_KEY

# Test Odds API
uv run walters-analyzer monitor-sharp --test
```

### Encoding Issues (Windows)

If you see `UnicodeEncodeError`, ensure PowerShell uses UTF-8:

```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

## Support

For issues or questions:
1. Check this documentation
2. Review `docs/reports/INTEGRATION_ANALYSIS.md`
3. Check `AGENTS.md` for automation tips
4. Review logs in `logs/walters-analyzer.log`

