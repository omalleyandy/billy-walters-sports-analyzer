# Walters Analyzer (WSA)

Canonical, uv-based repo scaffold so we stay in sync. One env per project.
This repo includes:
- **CLI**: `walters-analyzer` with `wk-card`, `scrape-overtime`, and `scrape-injuries` commands
- **Billy Walters Valuation System**: Sophisticated injury impact analysis with position-specific valuations, injury multipliers, and market inefficiency detection
- **Cards**: JSON snapshots in `./cards/`
- **Scrapers**: 
  - Overtime.ag spider for NFL and College Football odds (Scrapy + Playwright)
  - ESPN injury report scraper for player status tracking
- **Claude**: `/commands` and `/hooks` placeholders
- **Env**: `env.template` for required keys

## Billy Walters Methodology

This system implements Billy Walters' sophisticated approach to injury impact analysis:

- **Position-Specific Valuations**: Elite QB = 3.5-4.5 pts, Elite RB = 2.5 pts, WR1 = 1.8 pts, etc.
- **Injury Capacity Multipliers**: OUT = 0%, Questionable = 92%, Hamstring = 70%, Ankle = 80%
- **Market Inefficiency Detection**: Markets typically underreact by 15% to injuries
- **Position Group Crisis Analysis**: Multiple injuries to same unit compound (O-line, secondary, etc.)
- **Recovery Timeline Tracking**: Hamstring = 14 days, Ankle = 10 days, ACL = 270 days
- **Historical Win Rates**: 3+ point edge = 64% win rate, 2-3 pts = 58%, 1-2 pts = 54%

### Key Advantages Over Generic Systems

| Generic Approach | Billy Walters Approach |
|-----------------|------------------------|
| "QB OUT! (+10 pts)" | "Mahomes ankle: 65% capacity (-1.2 of 3.5 pts)" |
| "High injuries - be cautious" | "Edge: 3.2 pts. Historical: 64% win rate. Bet 2% bankroll" |
| Position counts only | Specific point spread impacts |
| No market analysis | Market inefficiency detection |
| No bet sizing | Kelly Criterion bet sizing |

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
Copy `env.template` to `.env` and fill in your credentials:
```bash
cp env.template .env
# Edit .env with your overtime.ag credentials
```

Required environment variables:
- `OV_CUSTOMER_ID`: Your overtime.ag customer ID
- `OV_CUSTOMER_PASSWORD`: Your overtime.ag password

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

### Billy Walters Analysis Scripts

Two powerful analysis scripts using the Billy Walters methodology:

```bash
# Combined game + injury analysis (MAIN TOOL)
uv run python analyze_games_with_injuries.py

# Position-based injury analysis
uv run python analyze_injuries_by_position.py
```

**What You Get:**
- Specific point spread impacts (not generic scores)
- Injury capacity percentages (Questionable = 92%, Hamstring = 70%)
- Market inefficiency detection (15% underreaction factor)
- Position group crisis alerts (O-line depleted, secondary crisis)
- Recovery timeline estimates
- Betting recommendations with historical win rates
- Kelly Criterion bet sizing (0.5-3% of bankroll)

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

# Live betting spider
scrapy crawl overtime_live

# With custom settings
scrapy crawl pregame_odds -a sport=nfl -s OVERTIME_OUT_DIR=./custom_output
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

## Collaboration Permissions Quick Checklist

- Keep the repository private and restrict collaborators to the two active maintainers.
- Issue fine-grained personal access tokens (PATs) scoped only to `billy-walters-sports-analyzer` when command-line or API access is required.
- Grant PAT permissions strictly aligned with needed features (e.g., contents, issues, pull requests, workflows, administration).
- Audit PATs and GitHub App installations periodically, revoking any tokens or integrations that are no longer in use.
