# Overtime.ag NFL Scraper Integration Guide

## Overview

This guide documents the integration of the Overtime.ag NFL pre-game odds scraper into the Billy Walters Sports Analyzer system.

## Components

### 1. Core Scraper (`src/data/overtime_pregame_nfl_scraper.py`)

The main scraper that uses Playwright to extract NFL betting lines from Overtime.ag.

**Features:**
- Automatic login with credentials
- Extracts multiple betting periods (Game, 1st Half, 1st Quarter)
- Parses spreads, totals, and moneylines
- Account balance tracking
- Export to JSON format

**Key Classes:**
- `OvertimeNFLScraper` - Main scraper class
- `OvertimeGame` - Data model for scraped games
- `OvertimeAccount` - Account information model

### 2. Data Converter (`src/data/overtime_data_converter.py`)

Converts Overtime.ag data format to Billy Walters analyzer format.

**Features:**
- Team name normalization
- Odds format conversion
- Spread and total parsing
- Multi-period data handling

**Key Classes:**
- `OvertimeToWaltersConverter` - Main converter class

### 3. CLI Script (`scripts/scrape_overtime_nfl.py`)

Command-line interface for running the scraper.

## Installation

### Prerequisites

```bash
# Ensure Playwright is installed
uv add playwright
uv run playwright install chromium

# Or if using pip
pip install playwright
playwright install chromium
```

### Environment Variables

Add these to your `.env` file:

```bash
# Overtime.ag Credentials
OV_CUSTOMER_ID=your_customer_id
OV_PASSWORD=your_password

# Optional: Proxy Configuration
PROXY_URL=http://user:pass@proxy.example.com:8080
```

## Usage

### Basic Scraping

```bash
# Scrape with visible browser (for debugging)
uv run python scripts/scrape_overtime_nfl.py

# Scrape in headless mode
uv run python scripts/scrape_overtime_nfl.py --headless
```

### Convert to Walters Format

```bash
# Scrape and convert
uv run python scripts/scrape_overtime_nfl.py --headless --convert
```

### Save to Database

```bash
# Scrape, convert, and save to database
uv run python scripts/scrape_overtime_nfl.py --headless --convert --save-db
```

### Custom Output Directory

```bash
# Save to custom directory
uv run python scripts/scrape_overtime_nfl.py --output data/odds
```

### Using Proxy

```bash
# Use proxy for scraping
uv run python scripts/scrape_overtime_nfl.py \
    --headless \
    --proxy "http://user:pass@proxy.example.com:8080"
```

## Python API

### Using the Scraper Programmatically

```python
import asyncio
import os
from src.data.overtime_pregame_nfl_scraper import OvertimeNFLScraper

async def main():
    # Create scraper (credentials from environment variables)
    scraper = OvertimeNFLScraper(
        customer_id=os.getenv("OV_CUSTOMER_ID"),
        password=os.getenv("OV_PASSWORD"),
        headless=True,
        output_dir="output"
    )
    
    # Scrape data
    result = await scraper.scrape()
    
    # Access data
    print(f"Scraped {result['summary']['total_games']} games")
    for game in result['games']:
        print(f"{game['visitor']['teamName']} @ {game['home']['teamName']}")
        print(f"  Spread: {game['visitor']['spread']} / {game['home']['spread']}")
        print(f"  Total: {game['visitor']['total']} / {game['home']['total']}")

asyncio.run(main())
```

### Converting Data

```python
import json
from src.data.overtime_data_converter import convert_overtime_to_walters

# Load scraped data
with open("output/overtime_nfl_raw.json", "r") as f:
    overtime_data = json.load(f)

# Convert to Walters format
walters_data = convert_overtime_to_walters(overtime_data)

# Save converted data
with open("output/overtime_nfl_walters.json", "w") as f:
    json.dump(walters_data, f, indent=2, default=str)

print(f"Converted {walters_data['summary']['total_converted']} games")
```

## Data Format

### Raw Overtime Format

```json
{
  "scrape_metadata": {
    "timestamp": "2025-11-10T10:30:00",
    "source": "overtime.ag",
    "sport": "NFL",
    "scraper_version": "1.0.0"
  },
  "account_info": {
    "balance": "$-1,988.43",
    "available_balance": "$8,011.57",
    "pending": "$0.00"
  },
  "games": [
    {
      "league_week_info": "NFL WEEK 10 Monday, November 10th",
      "game_date": "Mon Nov 10",
      "game_time": "8:15 PM",
      "visitor": {
        "rotationNumber": "275",
        "teamName": "Philadelphia Eagles",
        "logoUrl": "https://overtime.ag/sports/assets_core/sport_types/Philadelphia_Eagles.png",
        "spread": "+1 -113",
        "total": "O 45½ -112"
      },
      "home": {
        "rotationNumber": "276",
        "teamName": "Green Bay Packers",
        "logoUrl": "https://overtime.ag/sports/assets_core/sport_types/Green_Bay_Packers.png",
        "spread": "-1 -107",
        "total": "U 45½ -108"
      },
      "period": "GAME",
      "scraped_at": "2025-11-10T10:30:00"
    }
  ],
  "summary": {
    "total_games": 1,
    "periods": ["GAME"],
    "unique_matchups": 1
  }
}
```

### Converted Walters Format

```json
{
  "metadata": {
    "source": "overtime.ag",
    "converted_at": "2025-11-10T10:30:00",
    "original_scrape_time": "2025-11-10T10:30:00",
    "converter_version": "1.0.0"
  },
  "games": [
    {
      "game_id": "PHI_GB_2025111",
      "league": "NFL",
      "away_team": {
        "name": "Philadelphia Eagles",
        "abbreviation": "PHI",
        "league": "NFL",
        "rotation_number": "275"
      },
      "home_team": {
        "name": "Green Bay Packers",
        "abbreviation": "GB",
        "league": "NFL",
        "rotation_number": "276"
      },
      "game_date": "2025-11-10T20:15:00",
      "odds": {
        "spread": 1.0,
        "spread_odds": -113,
        "over_under": 45.5,
        "total_odds": -112,
        "sportsbook": "overtime.ag",
        "timestamp": "2025-11-10T10:30:00"
      }
    }
  ],
  "summary": {
    "total_converted": 1,
    "conversion_rate": "100.0%"
  }
}
```

## Integration with Billy Walters System

### 1. Automated Daily Collection

Add to your daily scraping workflow:

```python
# In your data orchestrator
from src.data.overtime_pregame_nfl_scraper import OvertimeNFLScraper
from src.data.overtime_data_converter import convert_overtime_to_walters

async def collect_overtime_odds():
    """Collect Overtime.ag odds as part of daily workflow"""
    scraper = OvertimeNFLScraper(headless=True)
    overtime_data = await scraper.scrape()
    
    # Convert to Walters format
    walters_data = convert_overtime_to_walters(overtime_data)
    
    # Save to database
    for game in walters_data['games']:
        ingest_odds(game)
    
    return walters_data
```

### 2. Edge Detection Integration

Use scraped odds with Billy Walters edge detection:

```python
from walters_analyzer.valuation.billy_walters_edge_detector import detect_edges

# Get converted odds
walters_data = convert_overtime_to_walters(overtime_data)

# Run edge detection
edges = detect_edges(walters_data['games'])

# Find value opportunities
for edge in edges:
    if edge['value'] > 0.03:  # 3% edge
        print(f"VALUE FOUND: {edge['game']} - {edge['bet_type']}")
        print(f"  Edge: {edge['value']:.2%}")
        print(f"  Recommended bet: {edge['recommended_bet']}")
```

### 3. Monitoring Line Movements

Track odds changes over time:

```python
from datetime import datetime, timedelta

async def monitor_line_movements(hours=6):
    """Monitor line movements over time"""
    scraper = OvertimeNFLScraper(headless=True)
    
    start_time = datetime.now()
    movements = []
    
    while datetime.now() < start_time + timedelta(hours=hours):
        # Scrape current lines
        data = await scraper.scrape()
        movements.append(data)
        
        # Wait 30 minutes
        await asyncio.sleep(1800)
    
    # Analyze movements
    analyze_line_movements(movements)
```

## Troubleshooting

### Login Issues

**Problem:** Login fails or credentials not accepted

**Solution:**
1. Verify credentials in `.env` file
2. Check for security checks (CAPTCHA)
3. Try running in non-headless mode to see what's happening
4. Ensure account is active and has access

### Scraping Issues

**Problem:** No games extracted

**Solution:**
1. Run with `--headless=False` to see the browser
2. Check if NFL games are available at Overtime.ag
3. Verify you're looking at the correct betting period
4. Check network connectivity and proxy settings

### Conversion Issues

**Problem:** Data conversion fails

**Solution:**
1. Check that raw data format matches expected structure
2. Verify team names are in the mapping dictionary
3. Add custom team mappings if needed
4. Check odds format (spread and total strings)

### Proxy Issues

**Problem:** Proxy authentication fails

**Solution:**
1. Verify proxy credentials format: `http://user:pass@host:port`
2. Test proxy with a simple curl command first
3. Check if proxy supports HTTPS
4. Try different proxy providers if persistent issues

## Best Practices

### 1. Rate Limiting

Don't scrape too frequently to avoid being blocked:

```python
# Good: Scrape every 30-60 minutes
await asyncio.sleep(1800)  # 30 minutes

# Bad: Scrape every minute
await asyncio.sleep(60)  # Too frequent!
```

### 2. Error Handling

Always wrap scraping in try-except blocks:

```python
try:
    data = await scraper.scrape()
except Exception as e:
    logger.error(f"Scrape failed: {e}")
    # Send alert, retry later, etc.
```

### 3. Data Validation

Validate scraped data before using:

```python
def validate_odds(game):
    """Validate odds are reasonable"""
    spread = game['odds']['spread']
    total = game['odds']['over_under']
    
    assert -30 <= spread <= 30, f"Invalid spread: {spread}"
    assert 20 <= total <= 100, f"Invalid total: {total}"
```

### 4. Logging

Enable detailed logging for debugging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Advanced Usage

### Multi-Sport Support

Extend the scraper for other sports:

```python
class OvertimeMultiSportScraper(OvertimeNFLScraper):
    """Scraper supporting multiple sports"""
    
    async def scrape_nfl(self):
        # NFL scraping logic
        pass
    
    async def scrape_ncaaf(self):
        # NCAAF scraping logic
        pass
    
    async def scrape_nba(self):
        # NBA scraping logic  
        pass
```

### Live Odds Integration

Combine with live odds scraper:

```python
from src.data.overtime_pregame_nfl_scraper import OvertimeNFLScraper
from scrapers.overtime_live.spiders.overtime_live_spider import OvertimeLiveSpider

async def collect_all_odds():
    """Collect both pre-game and live odds"""
    
    # Pre-game odds
    pregame_scraper = OvertimeNFLScraper(headless=True)
    pregame_data = await pregame_scraper.scrape()
    
    # Live odds
    live_scraper = OvertimeLiveSpider()
    live_data = await live_scraper.scrape()
    
    # Combine and analyze
    return {
        "pregame": pregame_data,
        "live": live_data
    }
```

## Maintenance

### Updating Team Mappings

Add new teams to the converter:

```python
# In overtime_data_converter.py
TEAM_MAPPINGS = {
    "Philadelphia Eagles": "PHI",
    "Green Bay Packers": "GB",
    # Add new teams here
    "New Team Name": "NTN",
}
```

### Handling Site Changes

If Overtime.ag changes their HTML structure:

1. Run scraper in non-headless mode
2. Inspect the new HTML structure
3. Update CSS selectors in `_extract_games()` method
4. Test thoroughly before deploying

## Support

For issues or questions:
1. Check this documentation first
2. Review `LESSONS_LEARNED.md` for similar issues
3. Check GitHub issues
4. Contact project maintainers

## Changelog

### Version 1.0.0 (2025-11-10)
- Initial release
- NFL pre-game odds scraping
- Multi-period support (Game, 1H, 1Q)
- Account balance tracking
- Data conversion to Walters format
- CLI script
- Comprehensive documentation

