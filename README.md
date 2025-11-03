# Billy Walters Sports Analyzer

**A complete sports betting research platform implementing Billy Walters' proven methodology from his Advanced Masterclass.**

## Overview

This project implements the **complete Billy Walters sports betting system**, combining:

### Core Billy Walters Methodology (NEW!)
1. **Power Rating Engine** - Exponential weighted team ratings updated after every game
2. **S/W/E Factor System** - Situational, Weather, and Emotional adjustments
3. **Key Number Analysis** - NFL/CFB key number value and half-point calculations
4. **Star System & Bet Sizing** - Risk-managed bet sizing (0.5-3.0 stars based on edge)
5. **CLV Tracking** - Closing Line Value validation to measure long-term skill

### Data Collection Infrastructure
- **Odds Scraping**: Overtime.ag spider for NFL and College Football odds (Scrapy + Playwright)
- **Injury Reports**: ESPN scraper for player status tracking
- **Weather Analysis**: AccuWeather API integration for game conditions
- **Power Ratings**: Massey Ratings scraper for objective benchmarking

### Features
- **Automated Analysis**: Complete game analysis combining power ratings, S/W/E factors, and key numbers
- **Bet Recommendations**: Automatic bet sizing based on calculated edge percentage
- **Performance Tracking**: SQLite database tracking CLV, ROI, and performance by star rating
- **Scientific Validation**: Comprehensive test suite validating all statistical models

---

## Quick Start: Billy Walters Methodology

```python
from walters_analyzer.analyzer import BillyWaltersAnalyzer
from walters_analyzer.situational_factors import GameContext

# Initialize analyzer
analyzer = BillyWaltersAnalyzer(bankroll=10000)

# Create game context with S/W/E factors
context = GameContext(
    team="Alabama", opponent="LSU", sport="cfb", is_home=False,
    is_rivalry=True, playoff_implications="seeding",
    wind_speed_mph=12, temperature_f=68
)

# Analyze game
analysis = analyzer.analyze_game(
    away_team="Alabama", home_team="LSU", sport="cfb",
    market_spread=-3.0, game_context=context, game_date="2024-11-09"
)

# Get recommendation
if analysis.should_bet:
    rec = analysis.recommendation
    print(f"{rec.stars}⭐ BET {rec.side.upper()} ${rec.bet_amount:,.2f}")
    print(f"Edge: {rec.edge_percentage:.1f}% | CLV will validate this bet")
```

See [**Billy Walters Methodology Guide**](docs/BILLY_WALTERS_METHODOLOGY.md) for complete documentation.

---

## Setup

### 1. Install Dependencies
```powershell
# Windows PowerShell
uv sync
uv sync --extra scraping  # Optional: additional scraping utilities
```

```bash
# WSL/Linux
uv sync
uv sync --extra scraping  # Optional: additional scraping utilities
```

### 2. Install Playwright Browsers
```powershell
# Required for web scraping
uv run playwright install chromium
```

### 3. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

**Important:** Never commit your `.env` file. It's gitignored and contains your actual secrets.

The settings loader (`walters_analyzer.settings`) reads `.env` via python-dotenv and
provides sensible defaults. Update the values that matter for your workflow:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `OV_CUSTOMER_ID` | ✅ | – | Overtime.ag login |
| `OV_CUSTOMER_PASSWORD` | ✅ | – | Overtime.ag login |
| `ACCUWEATHER_API_KEY` | ✅ | – | Weather research API (primary) |
| `OPENWEATHER_API_KEY` | Optional | – | Backup weather data source |
| `BANKROLL` | Optional | `10000.0` | Starting bankroll for bet sizing |
| `KELLY_FRACTION` | Optional | `0.25` | Fractional Kelly for bankroll growth |
| `MAX_BET_PERCENTAGE` | Optional | `0.03` | Safety cap per wager |
| `MINIMUM_EDGE_PERCENTAGE` | Optional | `5.5` | Minimum edge to trigger a bet |
| `CACHE_TTL_WEATHER` | Optional | `1800` | Weather cache lifetime (seconds) |
| `ENABLE_WEB_FETCH` | Optional | `true` | Toggle external fetches during research |
| `PROXY_URL` | Optional | – | Outbound proxy for Playwright/Scrapy |

## Usage

### WK-Card (Betting Card Analysis)
```powershell
# Preview card (dry-run)
uv run walters-analyzer wk-card --file .\cards\wk-card-2025-10-31.json --dry-run

# Execute card
uv run walters-analyzer wk-card --file .\cards\wk-card-2025-10-31.json
```

### Scrape Overtime.ag Odds

#### Pre-Game Odds
```powershell
# Scrape both NFL and College Football (default)
uv run walters-analyzer scrape-overtime

# Scrape NFL only
uv run walters-analyzer scrape-overtime --sport nfl

# Scrape College Football only
uv run walters-analyzer scrape-overtime --sport cfb

# Custom output directory
uv run walters-analyzer scrape-overtime --output-dir ./my_data
```

#### Live Betting Odds
```powershell
# Scrape live betting odds
uv run walters-analyzer scrape-overtime --live
```

### Scrape ESPN Injury Reports

Critical for gate checks - track player injury status (Out, Doubtful, Questionable, Probable):

```powershell
# Scrape College Football injuries (default)
uv run walters-analyzer scrape-injuries --sport cfb

# Scrape NFL injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Custom output directory
uv run walters-analyzer scrape-injuries --sport cfb --output-dir ./injury_data
```

**Why Injuries Matter:**
- Key player absences significantly impact point spreads
- Starting QB injuries can move lines 3-7 points
- Essential gate check before placing any wager

See [INJURY_SCRAPER.md](INJURY_SCRAPER.md) for complete documentation, gate integration examples, and position impact guidelines.

### Scrape Massey Ratings (College Football Power Ratings)

Collect objective power ratings, game predictions, and matchup analysis to identify betting edges:

```powershell
# Scrape everything (ratings + games)
uv run walters-analyzer scrape-massey

# Scrape only team power ratings
uv run walters-analyzer scrape-massey --data-type ratings

# Scrape only game predictions
uv run walters-analyzer scrape-massey --data-type games

# Specify season
uv run walters-analyzer scrape-massey --season 2025

# Custom output directory
uv run walters-analyzer scrape-massey --output-dir ./massey_data
```

**Why Massey Ratings Matter:**
- **Objective benchmark**: Mathematical model free from human bias
- **Find edges**: Compare Massey spreads to market odds (2+ pt discrepancy = opportunity)
- **Validate your model**: Cross-reference your predictions against proven system
- **Billy Walters methodology**: Use multiple data sources to identify market inefficiencies

**Data Collected:**
- Team power ratings (overall, offensive, defensive)
- Predicted scores, spreads, and totals for all games
- Win probabilities and confidence levels
- Strength of schedule (SoS) metrics

See [MASSEY_RATINGS.md](MASSEY_RATINGS.md) for complete documentation, edge detection strategies, and integration with Billy Walters principles.

### Fetch Weather Data (AccuWeather API)

Critical for outdoor games - weather impacts scoring, passing efficiency, and field goals:

```powershell
# Fetch weather for entire betting card
uv run walters-analyzer scrape-weather --card ./cards/wk-card-2025-10-31.json

# Fetch weather for single stadium
uv run walters-analyzer scrape-weather --stadium "Lambeau Field" --location "Green Bay, WI" --sport nfl

# Indoor stadium (weather irrelevant)
uv run walters-analyzer scrape-weather --stadium "US Bank Stadium" --location "Minneapolis, MN" --dome

# Custom output directory
uv run walters-analyzer scrape-weather --card ./cards/wk-card.json --output-dir ./weather_data
```

**Why Weather Matters:**
- Wind >15mph drastically reduces passing efficiency and FG accuracy
- Precipitation affects ball handling, reduces scoring by 3-7 points
- Temperature extremes impact player performance
- Billy Walters methodology emphasizes weather as a critical betting edge

**Weather Impact Score (0-100):**
- 0-20: Minimal impact
- 21-50: Moderate (adjust totals 1-3 points)
- 51-75: High (significant adjustment needed)
- 76-100: Extreme (consider skipping bet or heavy Under)

See [WEATHER_ANALYZER.md](WEATHER_ANALYZER.md) for complete Billy Walters weather methodology, case studies, and advanced usage.

### Output Files
Scraped data is saved to `data/overtime_live/` (or custom directory) in three formats:
- **JSONL**: `overtime-live-{timestamp}.jsonl` - Line-delimited JSON
- **Parquet**: `overtime-live-{timestamp}.parquet` - Columnar format for analytics
- **CSV**: `overtime-live-{timestamp}.csv` - Flattened spreadsheet format

### Data Schema
Each game record includes:
- `source`: "overtime.ag"
- `sport`: "nfl" or "college_football"
- `league`: "NFL" or "NCAAF"
- `rotation_number`: e.g., "451-452"
- `event_date`: ISO date (e.g., "2025-11-02")
- `event_time`: Game time with timezone (e.g., "1:00 PM ET")
- `away_team`, `home_team`: Team names
- `spread_away_line`, `spread_away_price`: Spread for away team
- `spread_home_line`, `spread_home_price`: Spread for home team
- `total_over_line`, `total_over_price`: Over total
- `total_under_line`, `total_under_price`: Under total
- `moneyline_away_price`, `moneyline_home_price`: Moneyline odds
- `is_live`: Boolean (true for live betting, false for pre-game)
- `quarter`, `clock`: Game state for live betting

## Direct Scrapy Commands (Advanced)

```powershell
# Pre-game odds spider
scrapy crawl pregame_odds -a sport=both

# Live betting spider (single scrape)
scrapy crawl overtime_live

# Live betting with continuous monitoring (10-second intervals)
scrapy crawl overtime_live -a monitor=10

# With custom settings
scrapy crawl pregame_odds -a sport=nfl -s OVERTIME_OUT_DIR=./custom_output
```

### Live Odds Monitoring Mode

The overtime_live spider now supports **continuous monitoring** with CDP network interception:

```bash
# Monitor odds continuously with 10-second refresh
uv run scrapy crawl overtime_live -a monitor=10

# Single scrape (default behavior)
uv run scrapy crawl overtime_live
```

**Features:**
- 🔄 **Automatic Refresh**: Polls for odds updates at your specified interval
- 📡 **CDP Network Interception**: Captures API responses for debugging
- 📊 **Odds Change Detection**: Automatically logs spread/total/moneyline changes
- 🎨 **Colored Console Output**: Real-time alerts for odds movements
- 💾 **Multiple Storage Options**: SQLite (default) or Redis for distributed tracking

**Monitoring Output:**
- API responses: `data/overtime_live/api_response_*.json`
- Odds changes: `data/overtime_live/odds_changes_{date}.csv`
- Change tracking DB: `data/overtime_live/odds_changes.db` (SQLite)

### Odds Change Tracking

Track line movements automatically with the `OddsChangeTrackerPipeline`:

**Default (SQLite):**
```bash
# No configuration needed - SQLite is used automatically
uv run scrapy crawl overtime_live -a monitor=10
```

**Optional (Redis):**
```bash
# Enable in .env for distributed tracking
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**Change Detection:**
- Spread line movements
- Total (over/under) adjustments
- Moneyline price changes
- Timestamped CSV logs for analysis

**Example Change Log:**
```csv
timestamp,game_key,game,market,field,old_value,new_value
2024-11-03T18:30:00,alabama_lsu,Alabama @ LSU,spread,away_line,-3.0,-3.5
2024-11-03T18:30:00,alabama_lsu,Alabama @ LSU,total,over_line,47.5,48.0
```

## Troubleshooting

### Login Issues
- Ensure `OV_CUSTOMER_ID` and `OV_CUSTOMER_PASSWORD` are set in `.env`
- Check that credentials are correct by logging in manually at https://overtime.ag
- Check logs for "Login successful" message

### Playwright Issues
- Run `uv run playwright install chromium` if you see browser errors
- On WSL, you may need: `sudo apt install libgbm1 libgtk-3-0 libasound2`

### Scraping Issues
- Check `snapshots/` directory for debug screenshots
- Review logs for timeout or selector errors
- Ensure stable internet connection

### Weather API Issues
- Ensure `ACCUWEATHER_API_KEY` is set in `.env`
- Free tier limited to 50 calls/day
- Check API status at https://developer.accuweather.com/

## Core Billy Walters Modules

### Power Ratings Engine
**File**: `walters_analyzer/power_ratings.py`

Implements Billy Walters' exponential weighted rating system:
```python
from walters_analyzer.power_ratings import PowerRatingEngine, GameResult

engine = PowerRatingEngine()
game = GameResult("Alabama", "LSU", 42, 35, True, "cfb", "2024-11-09")
rating = engine.update_rating(game)

# Predict spreads
spread = engine.calculate_predicted_spread("LSU", "Alabama", "cfb")
```

**Key Features:**
- 90/10 exponential weighting formula
- Home field adjustments (NFL: 2.5, CFB: 3.5)
- Opponent strength accounting
- Injury differential integration
- Persistent JSON storage

### S/W/E Factor System
**File**: `walters_analyzer/situational_factors.py`

Calculate Situational, Weather, and Emotional factors:
```python
from walters_analyzer.situational_factors import SWEFactorCalculator, GameContext

context = GameContext(
    team="Alabama", opponent="LSU", sport="cfb", is_home=False,
    is_rivalry=True, wind_speed_mph=22, playoff_implications="seeding"
)

calculator = SWEFactorCalculator()
factors = calculator.calculate_all_factors(context)
# Returns spread adjustment (5 points = 1 point spread)
```

**Key Features:**
- Rest advantage/disadvantage (1-3 points)
- Travel fatigue (1-3 points)
- Game importance (rivalry, divisional, conference)
- Weather impact (wind, precipitation, temperature)
- Playoff motivation (2-5 points)

### Key Number Analysis
**File**: `walters_analyzer/key_numbers.py`

NFL/CFB key number value calculations:
```python
from walters_analyzer.key_numbers import KeyNumberCalculator

calc = KeyNumberCalculator()

# Calculate edge crossing key numbers
analysis = calc.calculate_edge_value(
    your_line=-2.5, market_line=-3.5, sport='nfl'
)
# NFL 3 = 8% value, 7 = 6% value

# Should you buy half-point?
buy = calc.should_buy_half_point(-3.0, price_diff=20, sport='nfl')
# Returns True if value > cost
```

**Key Features:**
- NFL key numbers (3=8%, 7=6%, 6/10/14=4-5%)
- CFB key numbers (different distribution)
- Half-point value calculations
- Optimal bet timing ("favorites early, dogs late")

### Star System & Bet Sizing
**File**: `walters_analyzer/bet_sizing.py`

Convert edge to star rating and bet size:
```python
from walters_analyzer.bet_sizing import BetSizingCalculator

calc = BetSizingCalculator(bankroll=10000)
sizing = calc.calculate_bet_size(edge_percentage=0.08, price=-110)

# 8% edge = 1.0 star = 1% bankroll ($100)
```

**Star Thresholds:**
- 15%+ edge → 3.0 stars → 3% bankroll
- 13-15% → 2.5 stars → 2.5% bankroll
- 11-13% → 2.0 stars → 2% bankroll
- 9-11% → 1.5 stars → 1.5% bankroll
- 7-9% → 1.0 stars → 1% bankroll
- 5.5-7% → 0.5 stars → 0.5% bankroll
- <5.5% → NO BET

### CLV Tracker
**File**: `walters_analyzer/clv_tracker.py`

Track Closing Line Value and validate your model:
```python
from walters_analyzer.clv_tracker import CLVTracker

tracker = CLVTracker()

# Log bet
bet_id = tracker.log_bet(
    game="Cowboys @ Giants", sport="nfl", bet_type="spread",
    your_line=-3.0, opening_line=-2.5, stars=1.0, bet_amount=100
)

# Update closing line
tracker.update_closing_line(bet_id, closing_line=-3.5)
# CLV = -3.5 - (-3.0) = -0.5 (you beat the close!)

# Update result
tracker.update_result(bet_id, result="win", profit=90.91)

# Get stats
stats = tracker.get_clv_stats()
# Average CLV, % beating close, win rate
```

**Performance Metrics:**
- CLV by bet (closing - your line)
- ROI (total profit / total wagered)
- Win rate by star rating
- Performance by bet type (spread/total/ML)
- Sharpe ratio (risk-adjusted returns)

### Master Analyzer
**File**: `walters_analyzer/analyzer.py`

Unified interface integrating all components:
```python
from walters_analyzer.analyzer import BillyWaltersAnalyzer

analyzer = BillyWaltersAnalyzer(bankroll=10000)

# Complete game analysis
analysis = analyzer.analyze_game(
    away_team="Alabama", home_team="LSU", sport="cfb",
    market_spread=-3.0, game_context=context
)

# Place bet if recommended
if analysis.should_bet:
    bet_id = analyzer.place_bet(analysis, game_date="2024-11-09")

# Update after game
analyzer.update_game_result(bet_id, closing_line=-3.5,
                            actual_result="win", profit=90.91)

# Performance report
print(analyzer.get_performance_report())
```

---

## Testing

Comprehensive test suite validates all core components:

```powershell
# Run all tests
uv run pytest

# Run specific module tests
uv run pytest tests/test_power_ratings.py
uv run pytest tests/test_swe_factors.py
uv run pytest tests/test_key_numbers.py

# Run with coverage
uv run pytest --cov=walters_analyzer --cov-report=html
```

**Test Coverage:**
- Power rating calculations and persistence
- S/W/E factor calculations
- Key number edge detection
- Bet sizing and Kelly Criterion
- CLV tracking and statistics

---

## Example Workflow

See [`examples/complete_workflow_example.py`](examples/complete_workflow_example.py) for a complete demonstration:

```powershell
uv run python examples/complete_workflow_example.py
```

This example shows:
1. Building power ratings from historical games
2. Analyzing a game with S/W/E factors
3. Calculating edge with key numbers
4. Generating bet recommendation with star sizing
5. Logging bet and tracking CLV
6. Updating results and performance metrics

---

## Documentation

### Billy Walters Methodology
- **[BILLY_WALTERS_METHODOLOGY.md](docs/BILLY_WALTERS_METHODOLOGY.md)** - Complete methodology guide with formulas and examples

### Data Collection
- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup and first scrape guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical details of scraper implementation
- **[INJURY_SCRAPER.md](INJURY_SCRAPER.md)** - Injury report scraper documentation
- **[WEATHER_ANALYZER.md](WEATHER_ANALYZER.md)** - Weather analysis using Billy Walters methodology
- **[MASSEY_RATINGS.md](MASSEY_RATINGS.md)** - Massey Ratings scraper and edge detection
- **[EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)** - Sample outputs and data formats

### Automation
- **[CLAUDE.md](CLAUDE.md)** - Commands and hooks for automation

---

## Project Structure

```
billy-walters-sports-analyzer/
├── walters_analyzer/           # Core Billy Walters modules
│   ├── power_ratings.py        # Power rating engine
│   ├── situational_factors.py  # S/W/E factor system
│   ├── key_numbers.py          # Key number analysis
│   ├── bet_sizing.py           # Star system & Kelly Criterion
│   ├── clv_tracker.py          # CLV tracking database
│   ├── analyzer.py             # Master analyzer
│   ├── cli.py                  # Command-line interface
│   ├── wkcard.py               # Betting card loader
│   ├── weather_fetcher.py      # AccuWeather API
│   └── weather_pipeline.py     # Weather data pipeline
├── scrapers/                   # Web scraping infrastructure
│   └── overtime_live/          # Scrapy project
│       ├── spiders/            # Scraper spiders
│       │   ├── overtime_live_spider.py
│       │   ├── pregame_odds_spider.py
│       │   ├── espn_injury_spider.py
│       │   └── massey_ratings_spider.py
│       ├── items.py            # Data models
│       ├── pipelines.py        # Export pipelines
│       └── settings.py         # Scrapy configuration
├── tests/                      # Test suite
│   ├── test_power_ratings.py
│   ├── test_swe_factors.py
│   ├── test_key_numbers.py
│   └── ...
├── examples/                   # Example scripts
│   └── complete_workflow_example.py
├── docs/                       # Documentation
│   └── BILLY_WALTERS_METHODOLOGY.md
├── data/                       # Data storage
│   ├── power_ratings/          # Team ratings JSON
│   ├── bets/                   # CLV tracking database
│   ├── overtime_live/          # Scraped odds
│   ├── injuries/               # Injury reports
│   ├── weather/                # Weather data
│   └── massey_ratings/         # Power ratings
└── cards/                      # Betting cards
```

---

## Philosophy: Billy Walters Principles

This project embodies Billy Walters' core principles:

1. **Data-Driven Decision Making**
   - Power ratings built from game results
   - Objective benchmarks (Massey Ratings)
   - Statistical validation (CLV tracking)

2. **Systematic Approach**
   - Consistent methodology (S/W/E factors)
   - Repeatable process (automated analysis)
   - No emotional decisions

3. **Risk Management**
   - Star system bet sizing
   - Fractional Kelly Criterion
   - Never risk more than edge justifies

4. **Long-Term Thinking**
   - CLV validation over short-term results
   - Bankroll management
   - Continuous improvement through testing

5. **Edge Detection**
   - Key number analysis
   - Market inefficiency identification
   - Multiple data source validation

> **"The goal is not to win every bet. The goal is to have an edge and let the math work over time."** - Billy Walters

---

## Contributing

This is a statistical research project. Contributions welcome for:
- Backtesting framework
- Additional statistical models
- Data source integrations
- Test coverage improvements

---

## License

MIT License - See LICENSE file for details

---

## Disclaimer

This software is for educational and research purposes only. Sports betting involves risk. Always gamble responsibly and within your means.

## Codex Setup
- Codex starts in this repo via `~/.codexrc`
- Project rules: `CLAUDE.md`
- Codex workflow guide: `docs/CODEX_WORKFLOW.md`
- Hooks: `hooks/*.sh` (run `.codex/preflight.sh` before committing)
- Project commands: `commands/*` (e.g., `./commands/bootstrap`, `./commands/wk-card`)
