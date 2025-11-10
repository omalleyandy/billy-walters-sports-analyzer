# Market Data Feeds Module

Real-time market data integration for sharp money detection and line movement tracking.

---

## Overview

This module provides live market data feeds from multiple sportsbooks to detect market inefficiencies and sharp money movements based on Billy Walters' methodology.

### Key Principles

1. **Markets underreact to information by ~15%**
2. **Sharp books move faster than public books**
3. **Reverse line movement = sharp money indicator**
4. **Track divergence between sharp and public books**

---

## Module Structure

```
walters_analyzer/feeds/
├── __init__.py              # Module exports
├── market_data_client.py    # API clients for odds data
├── market_monitor.py        # Sharp money detection engine
└── README.md               # This file
```

---

## market_data_client.py

### Classes

#### `MarketDataFeed` (Abstract Base Class)

Base class for all market data feed clients.

```python
from walters_analyzer.feeds import MarketDataFeed

class MyBookClient(MarketDataFeed):
    async def get_odds(self, sport: str, game_id: Optional[str] = None):
        # Implementation
        pass

    async def get_line_history(self, game_id: str, market: str = "spread"):
        # Implementation
        pass
```

#### `OddsAPIClient`

Client for The Odds API (https://the-odds-api.com/)

**Features:**
- Aggregates 40+ sportsbooks
- Free tier: 500 requests/month
- Returns normalized odds format

**Usage:**

```python
from walters_analyzer.feeds import OddsAPIClient
import asyncio

async def fetch_nfl_odds():
    client = OddsAPIClient()
    odds = await client.get_odds("americanfootball_nfl")

    for odd in odds:
        print(f"{odd['book']}: {odd['teams']['away']} @ {odd['teams']['home']}")

asyncio.run(fetch_nfl_odds())
```

**Sport Keys:**
- `americanfootball_nfl` - NFL
- `americanfootball_ncaaf` - College Football
- `basketball_nba` - NBA
- `baseball_mlb` - MLB
- `icehockey_nhl` - NHL

#### `PinnacleClient`

Client for Pinnacle (sharp book).

**Requirements:**
- Funded Pinnacle account
- API credentials

**Usage:**

```python
from walters_analyzer.feeds import PinnacleClient
import asyncio

async def fetch_pinnacle():
    client = PinnacleClient()
    odds = await client.get_odds("nfl")
    # Returns normalized odds format

asyncio.run(fetch_pinnacle())
```

#### `DraftKingsClient`

Placeholder for DraftKings (no public API).

**Note:** DraftKings doesn't offer a public API. Use The Odds API instead, which includes DraftKings data.

### Normalized Odds Format

All clients return odds in this standard format:

```python
{
    'book': str,                    # "Pinnacle", "DraftKings", etc.
    'game_id': str,                 # Unique game identifier
    'sport': str,                   # "americanfootball_nfl", etc.
    'teams': {
        'away': str,                # Away team name
        'home': str                 # Home team name
    },
    'commence_time': str,           # ISO 8601 timestamp
    'markets': {
        'spread': {
            'away': {
                'line': float,      # e.g., +3.5
                'price': int        # e.g., -110
            },
            'home': {
                'line': float,      # e.g., -3.5
                'price': int        # e.g., -110
            }
        },
        'total': {
            'over': {
                'line': float,      # e.g., 47.5
                'price': int        # e.g., -110
            },
            'under': {
                'line': float,      # e.g., 47.5
                'price': int        # e.g., -110
            }
        },
        'moneyline': {
            'away': {'price': int}, # e.g., +150
            'home': {'price': int}  # e.g., -170
        }
    },
    'timestamp': str                # When data was fetched
}
```

---

## market_monitor.py

### Classes

#### `MarketMonitor`

Monitors line movements across sharp and public books to detect sharp money.

**Key Methods:**

##### `monitor_sport(sport, duration_minutes, check_interval)`

Monitor all games for a sport.

```python
from walters_analyzer.feeds import MarketMonitor
import asyncio

async def monitor_nfl():
    monitor = MarketMonitor()

    # Monitor NFL for 2 hours, check every 30 seconds
    await monitor.monitor_sport(
        sport="americanfootball_nfl",
        duration_minutes=120,
        check_interval=30
    )

    # Get summary
    summary = monitor.get_alert_summary()
    print(f"Total alerts: {summary['total_alerts']}")

asyncio.run(monitor_nfl())
```

##### `monitor_game(game_id, sport, duration_minutes)`

Monitor a specific game.

```python
async def monitor_specific_game():
    monitor = MarketMonitor()

    await monitor.monitor_game(
        game_id="abc123",
        sport="americanfootball_nfl",
        duration_minutes=60
    )

asyncio.run(monitor_specific_game())
```

##### `get_alert_summary()`

Get summary of all detected alerts.

```python
summary = monitor.get_alert_summary()

# Returns:
{
    'total_alerts': int,
    'alerts_by_type': dict,
    'most_alerted_games': list,
    'avg_confidence': float
}
```

### Alert Format

When sharp money is detected, alerts are generated in this format:

```python
{
    'type': 'sharp_money',
    'game_id': str,
    'teams': {
        'away': str,
        'home': str
    },
    'sharp_movement': float,        # Sharp book line movement
    'public_movement': float,       # Public book line movement
    'divergence': float,            # Difference between movements
    'current_sharp_line': float,    # Current sharp consensus line
    'current_public_line': float,   # Current public consensus line
    'direction': str,               # Human-readable direction
    'confidence': float,            # 0-100+ (can exceed 100)
    'timestamp': str,               # ISO 8601
    'books_analyzed': {
        'sharp': list,              # Sharp books in snapshot
        'public': list              # Public books in snapshot
    }
}
```

### Detection Logic

The monitor detects sharp money using this algorithm:

1. **Separate books by type:**
   - Sharp: Pinnacle, Circa, Bookmaker (from settings)
   - Public: DraftKings, FanDuel, BetMGM (from settings)

2. **Calculate average lines:**
   - Sharp consensus = average of sharp book lines
   - Public consensus = average of public book lines

3. **Track movement:**
   - Compare current snapshot to previous snapshot
   - Calculate line movement for sharp and public books

4. **Detect divergence:**
   - If sharp movement >= threshold AND differs from public movement
   - Generate alert with confidence based on movement size

5. **Send alerts:**
   - Console output (if enabled)
   - Log to file (if enabled)
   - Webhook (if configured)

---

## Configuration

Settings are loaded from `walters_analyzer.config`:

```python
from walters_analyzer.config import get_settings

settings = get_settings()

# Market analysis settings
sharp_books = settings.skills.market_analysis.sharp_books
# Default: ["Pinnacle", "Circa", "Bookmaker"]

public_books = settings.skills.market_analysis.public_books
# Default: ["DraftKings", "FanDuel", "BetMGM"]

alert_threshold = settings.skills.market_analysis.alert_threshold
# Default: 0.7 points

monitor_interval = settings.skills.market_analysis.monitor_interval
# Default: 30 seconds
```

### Customize via .env

```bash
SKILLS__MARKET_ANALYSIS__SHARP_BOOKS=["Pinnacle", "Circa", "CRIS"]
SKILLS__MARKET_ANALYSIS__ALERT_THRESHOLD=0.5
SKILLS__MARKET_ANALYSIS__MONITOR_INTERVAL=15
```

### Customize via config file

Edit `.claude/claude-desktop-config.json`:

```json
{
  "skills": {
    "market-analysis": {
      "config": {
        "sharp_books": ["Pinnacle", "Circa"],
        "alert_threshold": 0.5
      }
    }
  }
}
```

---

## Integration Examples

### Example 1: Combine with Injury Analysis

```python
from walters_analyzer.feeds import OddsAPIClient, MarketMonitor
from walters_analyzer.valuation import BillyWaltersValuation
import asyncio

async def integrated_analysis():
    # Get current odds
    client = OddsAPIClient()
    odds = await client.get_odds("americanfootball_nfl")

    # Get Billy Walters injury valuation
    bw = BillyWaltersValuation()

    for game_odds_list in group_by_game(odds):
        game = game_odds_list[0]
        teams = game['teams']

        # Calculate injury impact
        injury_edge = bw.analyze_game(
            home_team=teams['home'],
            away_team=teams['away'],
            # ... injury data
        )

        # Get current market price
        avg_line = calculate_avg_line(game_odds_list)

        # Compare
        expected_line = injury_edge['edge_analysis']['expected_line_movement']
        actual_line = avg_line

        edge = expected_line - actual_line

        if abs(edge) > 1.0:
            print(f"EDGE FOUND: {teams['away']} @ {teams['home']}")
            print(f"Expected: {expected_line:.1f}")
            print(f"Actual: {actual_line:.1f}")
            print(f"Edge: {edge:+.1f} points")

asyncio.run(integrated_analysis())
```

### Example 2: Custom Alert Handler

```python
from walters_analyzer.feeds import MarketMonitor

class CustomMonitor(MarketMonitor):
    def _send_alert(self, alert: dict):
        # Call parent implementation
        super()._send_alert(alert)

        # Add custom handling
        if alert['confidence'] > 150:
            # Send SMS notification
            send_sms(f"HIGH CONFIDENCE ALERT: {alert['direction']}")

        # Log to database
        save_to_database(alert)

        # Update dashboard
        update_realtime_dashboard(alert)
```

### Example 3: Backtest Historical Alerts

```python
import json
from pathlib import Path

# Read alert log
alerts = []
with open('logs/alerts.log', 'r') as f:
    for line in f:
        alerts.append(json.loads(line))

# Analyze performance
for alert in alerts:
    game_id = alert['game_id']
    direction = alert['direction']

    # Look up game result
    result = get_game_result(game_id)

    # Check if alert was correct
    if result['winner'] in direction:
        print(f"✅ Correct: {alert['teams']['away']} @ {alert['teams']['home']}")
    else:
        print(f"❌ Wrong: {alert['teams']['away']} @ {alert['teams']['home']}")
```

---

## Testing

Run the test script:

```bash
uv run python examples/test_market_monitor.py
```

This will:
1. Test API connection
2. Fetch and display sample odds
3. Show sharp vs public line breakdown
4. (Optional) Run 2-minute monitoring test

---

## API Rate Limits

### The Odds API

**Free Tier:**
- 500 requests/month
- ~16 requests/day
- Good for testing and light usage

**Paid Tiers:**
- Standard: $50/mo (5,000 requests)
- Professional: $200/mo (25,000 requests)

**Calculate Usage:**
- Monitoring interval: 30 seconds = 120 requests/hour
- 2-hour session = 240 requests
- Free tier = ~2 sessions/month

**Tip:** Use 60-second intervals to conserve quota

---

## Error Handling

All clients handle errors gracefully:

```python
from walters_analyzer.feeds import OddsAPIClient
import asyncio

async def safe_fetch():
    client = OddsAPIClient()

    try:
        odds = await client.get_odds("americanfootball_nfl")

        if not odds:
            print("No data received - check API key and game schedule")
            return

        # Process odds...

    except Exception as e:
        print(f"Error: {e}")
        # Fallback logic...

asyncio.run(safe_fetch())
```

---

## Contributing

When adding new data sources:

1. Extend `MarketDataFeed` abstract base class
2. Implement required methods: `get_odds()`, `get_line_history()`
3. Return data in normalized format
4. Add to `__init__.py` exports
5. Update `get_client()` factory function
6. Document in this README

---

## Future Enhancements

- [ ] Historical line movement tracking
- [ ] Public betting percentage data
- [ ] Steam move detection (rapid line changes)
- [ ] Closing line value (CLV) calculation
- [ ] Multi-sport simultaneous monitoring
- [ ] Machine learning edge prediction
- [ ] Webhook notifications (Discord, Slack, Telegram)
- [ ] Real-time dashboard UI

---

## References

- The Odds API: https://the-odds-api.com/
- Pinnacle API: https://pinnacleapi.github.io/
- Billy Walters Methodology: `../BILLY_WALTERS_METHODOLOGY.md`
- Market Integration Guide: `../MARKET_DATA_INTEGRATION_GUIDE.md`
