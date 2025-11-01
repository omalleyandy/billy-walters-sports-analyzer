# Walters Analyzer (WSA)

Canonical, uv-based repo scaffold so we stay in sync. One env per project.
This repo includes:
- **CLI**: `walters-analyzer` with `wk-card` and `scrape-overtime` commands
- **Cards**: JSON snapshots in `./cards/`
- **Scrapers**: Overtime.ag spider for NFL and College Football odds (Scrapy + Playwright)
- **Claude**: `/commands` and `/hooks` placeholders
- **Env**: `env.template` for required keys

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
