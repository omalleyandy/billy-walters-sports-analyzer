# Market Data Integration Guide

Complete guide to customizing market analysis settings and integrating live market data feeds.

---

## Part 1: Customizing Market Analysis Settings

There are **3 ways** to customize settings, listed from highest to lowest priority:

### Method 1: Environment Variables (Highest Priority)

Create a `.env` file in your project root:

```bash
# Market Analysis Settings
SKILLS__MARKET_ANALYSIS__SHARP_BOOKS=["Pinnacle", "Circa", "Bookmaker", "CRIS"]
SKILLS__MARKET_ANALYSIS__PUBLIC_BOOKS=["DraftKings", "FanDuel", "BetMGM", "Caesars"]
SKILLS__MARKET_ANALYSIS__ALERT_THRESHOLD=0.5
SKILLS__MARKET_ANALYSIS__MONITOR_INTERVAL=15

# Autonomous Agent Settings
AUTONOMOUS_AGENT__INITIAL_BANKROLL=25000.0
AUTONOMOUS_AGENT__MAX_BET_PERCENTAGE=2.5
AUTONOMOUS_AGENT__CONFIDENCE_THRESHOLD=0.70

# Logging
LOG_LEVEL=debug
```

**Pros**: Easy to change, won't be committed to Git, environment-specific
**Cons**: Nested settings use double underscores which can be verbose

### Method 2: MCP Config File (Medium Priority)

Edit `.claude/claude-desktop-config.json`:

```json
{
  "skills": {
    "market-analysis": {
      "enabled": true,
      "config": {
        "sharp_books": ["Pinnacle", "Circa", "Bookmaker", "CRIS"],
        "public_books": ["DraftKings", "FanDuel", "BetMGM", "Caesars", "PointsBet"],
        "alert_threshold": 0.5,
        "monitor_interval": 15
      }
    }
  },
  "autonomousAgent": {
    "enabled": false,
    "config": {
      "initial_bankroll": 25000.0,
      "max_bet_percentage": 2.5,
      "confidence_threshold": 0.70
    }
  }
}
```

**Pros**: Structured, easy to read, IDE autocomplete
**Cons**: Changes require editing JSON

### Method 3: Programmatic (Code-Level)

```python
from walters_analyzer.config import get_settings

# Load and modify settings
settings = get_settings()

# Customize market analysis
settings.skills.market_analysis.sharp_books = ["Pinnacle", "Circa", "CRIS"]
settings.skills.market_analysis.alert_threshold = 0.5

# Customize autonomous agent
settings.autonomous_agent.initial_bankroll = 25000.0
settings.autonomous_agent.max_bet_percentage = 2.5

# Access settings
print(f"Sharp books: {settings.skills.market_analysis.sharp_books}")
print(f"Bankroll: ${settings.autonomous_agent.initial_bankroll:,.2f}")
```

**Pros**: Full control, dynamic changes
**Cons**: Requires code changes, not persistent

---

## Part 2: Integrating Live Market Data Feeds

### Current Architecture

The system currently uses **file-based** data from Overtime.ag scrapers:

```
scrapers/overtime_live/
  └── overtime_live_spider.py    # Scrapes odds to JSONL files
data/overtime_live/
  └── overtime-live-*.jsonl      # Scraped odds data
walters_analyzer/query/
  └── odds_viewer.py             # Queries scraped data
```

### Integration Points for Live Feeds

To add **live market data feeds**, you need to implement data sources for:

1. **Sharp books**: Pinnacle, Circa, Bookmaker
2. **Public books**: DraftKings, FanDuel, BetMGM

---

## Step-by-Step: Adding a Live Data Feed

### Step 1: Create a Market Data Client

Create `walters_analyzer/feeds/market_data_client.py`:

```python
"""
Live market data feed client
"""
from typing import Dict, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod
import httpx
from walters_analyzer.config import get_settings


class MarketDataFeed(ABC):
    """Abstract base class for market data feeds"""

    def __init__(self, book_name: str):
        self.book_name = book_name
        self.settings = get_settings()

    @abstractmethod
    async def get_odds(self, sport: str, game_id: Optional[str] = None) -> List[Dict]:
        """Fetch current odds for a sport or specific game"""
        pass

    @abstractmethod
    async def get_line_history(self, game_id: str, market: str = "spread") -> List[Dict]:
        """Get historical line movements for a game"""
        pass


class PinnacleClient(MarketDataFeed):
    """Pinnacle (sharp book) data feed"""

    def __init__(self):
        super().__init__("Pinnacle")
        self.base_url = self.settings.data_connections.pinnacle_api_endpoint
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_odds(self, sport: str, game_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch Pinnacle odds

        API Docs: https://pinnacleapi.github.io/
        """
        endpoint = f"{self.base_url}/v1/sports/{sport}/markets"

        headers = {
            "Authorization": f"Bearer {self.settings.pinnacle_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.get(endpoint, headers=headers)
            response.raise_for_status()

            data = response.json()
            return self._normalize_odds(data)

        except httpx.HTTPError as e:
            print(f"Error fetching Pinnacle odds: {e}")
            return []

    async def get_line_history(self, game_id: str, market: str = "spread") -> List[Dict]:
        """Get Pinnacle line movement history"""
        # Implementation depends on Pinnacle's API
        pass

    def _normalize_odds(self, raw_data: Dict) -> List[Dict]:
        """
        Normalize Pinnacle API response to standard format

        Standard format:
        {
            'book': 'Pinnacle',
            'game_id': '12345',
            'sport': 'nfl',
            'teams': {'away': 'Team A', 'home': 'Team B'},
            'markets': {
                'spread': {
                    'away': {'line': -3.5, 'price': -110},
                    'home': {'line': 3.5, 'price': -110}
                },
                'total': {...},
                'moneyline': {...}
            },
            'timestamp': '2025-11-07T12:00:00Z'
        }
        """
        normalized = []
        # Parse raw_data and convert to standard format
        # Implementation depends on API structure
        return normalized


class DraftKingsClient(MarketDataFeed):
    """DraftKings (public book) data feed"""

    def __init__(self):
        super().__init__("DraftKings")
        self.base_url = self.settings.data_connections.draftkings_api_endpoint
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_odds(self, sport: str, game_id: Optional[str] = None) -> List[Dict]:
        """Fetch DraftKings odds"""
        # Similar implementation to Pinnacle
        pass

    async def get_line_history(self, game_id: str, market: str = "spread") -> List[Dict]:
        """Get DraftKings line movement history"""
        pass


class OddsAPIClient(MarketDataFeed):
    """
    The Odds API - Aggregates multiple books
    https://the-odds-api.com/
    """

    def __init__(self):
        super().__init__("OddsAPI")
        self.base_url = "https://api.the-odds-api.com/v4"
        self.api_key = self.settings.odds_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_odds(self, sport: str, game_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch odds from The Odds API

        Example:
            client = OddsAPIClient()
            odds = await client.get_odds("americanfootball_nfl")
        """
        endpoint = f"{self.base_url}/sports/{sport}/odds"

        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "spreads,totals,h2h",
            "oddsFormat": "american"
        }

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()
            return self._normalize_odds(data)

        except httpx.HTTPError as e:
            print(f"Error fetching odds: {e}")
            return []

    def _normalize_odds(self, raw_data: List[Dict]) -> List[Dict]:
        """Normalize Odds API response"""
        normalized = []

        for game in raw_data:
            # Extract bookmaker odds
            for bookmaker in game.get("bookmakers", []):
                book_name = bookmaker.get("title")

                normalized_game = {
                    'book': book_name,
                    'game_id': game.get('id'),
                    'sport': game.get('sport_key'),
                    'teams': {
                        'away': game.get('away_team'),
                        'home': game.get('home_team')
                    },
                    'markets': self._extract_markets(bookmaker.get('markets', [])),
                    'timestamp': datetime.utcnow().isoformat()
                }

                normalized.append(normalized_game)

        return normalized

    def _extract_markets(self, markets: List[Dict]) -> Dict:
        """Extract spread, total, and moneyline from markets"""
        result = {}

        for market in markets:
            market_key = market.get('key')
            outcomes = market.get('outcomes', [])

            if market_key == 'spreads':
                result['spread'] = {
                    'away': {'line': outcomes[0].get('point'), 'price': outcomes[0].get('price')},
                    'home': {'line': outcomes[1].get('point'), 'price': outcomes[1].get('price')}
                }
            elif market_key == 'totals':
                result['total'] = {
                    'over': {'line': outcomes[0].get('point'), 'price': outcomes[0].get('price')},
                    'under': {'line': outcomes[1].get('point'), 'price': outcomes[1].get('price')}
                }
            elif market_key == 'h2h':
                result['moneyline'] = {
                    'away': {'price': outcomes[0].get('price')},
                    'home': {'price': outcomes[1].get('price')}
                }

        return result
```

### Step 2: Create Market Monitor

Create `walters_analyzer/feeds/market_monitor.py`:

```python
"""
Real-time market monitoring for sharp money detection
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from walters_analyzer.config import get_settings
from walters_analyzer.feeds.market_data_client import (
    PinnacleClient,
    DraftKingsClient,
    OddsAPIClient
)


class MarketMonitor:
    """
    Monitor line movements across sharp and public books
    to detect reverse line movement and sharp money
    """

    def __init__(self):
        self.settings = get_settings()
        self.sharp_clients = self._init_sharp_clients()
        self.public_clients = self._init_public_clients()
        self.line_history = defaultdict(list)

    def _init_sharp_clients(self) -> List:
        """Initialize clients for sharp books"""
        clients = []
        sharp_books = self.settings.skills.market_analysis.sharp_books

        if "Pinnacle" in sharp_books:
            clients.append(PinnacleClient())

        # Add other sharp book clients as needed

        return clients

    def _init_public_clients(self) -> List:
        """Initialize clients for public books"""
        clients = []
        public_books = self.settings.skills.market_analysis.public_books

        if "DraftKings" in public_books:
            clients.append(DraftKingsClient())

        # Add other public book clients

        return clients

    async def monitor_game(self, game_id: str, duration_minutes: int = 60):
        """
        Monitor a specific game for line movements

        Args:
            game_id: Game identifier
            duration_minutes: How long to monitor
        """
        interval = self.settings.skills.market_analysis.monitor_interval
        end_time = datetime.now() + timedelta(minutes=duration_minutes)

        print(f"Monitoring game {game_id} for {duration_minutes} minutes...")

        while datetime.now() < end_time:
            # Fetch from sharp books
            sharp_odds = await self._fetch_sharp_odds(game_id)

            # Fetch from public books
            public_odds = await self._fetch_public_odds(game_id)

            # Analyze for reverse line movement
            alert = self._detect_sharp_money(game_id, sharp_odds, public_odds)

            if alert:
                self._send_alert(alert)

            # Wait before next check
            await asyncio.sleep(interval)

    async def _fetch_sharp_odds(self, game_id: str) -> List[Dict]:
        """Fetch odds from all sharp books"""
        tasks = [
            client.get_odds("nfl", game_id)
            for client in self.sharp_clients
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        odds = []
        for result in results:
            if isinstance(result, list):
                odds.extend(result)

        return odds

    async def _fetch_public_odds(self, game_id: str) -> List[Dict]:
        """Fetch odds from all public books"""
        tasks = [
            client.get_odds("nfl", game_id)
            for client in self.public_clients
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        odds = []
        for result in results:
            if isinstance(result, list):
                odds.extend(result)

        return odds

    def _detect_sharp_money(
        self,
        game_id: str,
        sharp_odds: List[Dict],
        public_odds: List[Dict]
    ) -> Optional[Dict]:
        """
        Detect reverse line movement (sharp money indicator)

        Returns alert dict if sharp money detected, None otherwise
        """
        # Store current odds
        self.line_history[game_id].append({
            'timestamp': datetime.now(),
            'sharp': sharp_odds,
            'public': public_odds
        })

        # Need at least 2 data points to detect movement
        if len(self.line_history[game_id]) < 2:
            return None

        # Get previous and current data
        previous = self.line_history[game_id][-2]
        current = self.line_history[game_id][-1]

        # Calculate average sharp book line
        prev_sharp_line = self._avg_spread_line(previous['sharp'])
        curr_sharp_line = self._avg_spread_line(current['sharp'])

        # Calculate line movement
        line_movement = curr_sharp_line - prev_sharp_line

        # Check if movement exceeds alert threshold
        threshold = self.settings.skills.market_analysis.alert_threshold

        if abs(line_movement) >= threshold:
            return {
                'game_id': game_id,
                'movement': line_movement,
                'direction': 'SHARP MONEY ON HOME' if line_movement > 0 else 'SHARP MONEY ON AWAY',
                'sharp_line': curr_sharp_line,
                'timestamp': datetime.now().isoformat(),
                'confidence': min(abs(line_movement) / threshold, 1.0) * 100
            }

        return None

    def _avg_spread_line(self, odds_list: List[Dict]) -> float:
        """Calculate average spread line from multiple books"""
        lines = []

        for odds in odds_list:
            spread = odds.get('markets', {}).get('spread', {})
            home_line = spread.get('home', {}).get('line')

            if home_line is not None:
                lines.append(home_line)

        return sum(lines) / len(lines) if lines else 0.0

    def _send_alert(self, alert: Dict):
        """Send alert to configured channels"""
        channels = self.settings.monitoring.alert_channels

        # Console alert
        if channels.console:
            print("\n" + "=" * 80)
            print("🚨 SHARP MONEY ALERT")
            print("=" * 80)
            print(f"Game: {alert['game_id']}")
            print(f"Direction: {alert['direction']}")
            print(f"Line Movement: {alert['movement']:+.1f}")
            print(f"Current Sharp Line: {alert['sharp_line']:.1f}")
            print(f"Confidence: {alert['confidence']:.0f}%")
            print(f"Time: {alert['timestamp']}")
            print("=" * 80 + "\n")

        # File alert
        if channels.file:
            import json
            from pathlib import Path

            log_file = Path(channels.file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(log_file, 'a') as f:
                f.write(json.dumps(alert) + "\n")

        # Webhook alert (if configured)
        if channels.webhook:
            # Send to webhook
            pass


# Example usage
async def main():
    """Example: Monitor NFL games for sharp money"""
    monitor = MarketMonitor()

    # Monitor a specific game for 2 hours
    await monitor.monitor_game("game_12345", duration_minutes=120)


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Update Configuration

Add API credentials to `.env`:

```bash
# The Odds API
ODDS_API_KEY=your_api_key_here

# Pinnacle (if you have access)
PINNACLE_API_KEY=your_pinnacle_key

# DraftKings (if you have access)
DRAFTKINGS_API_KEY=your_dk_key
```

Update `walters_analyzer/config/settings.py` to include API keys:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # API Keys for live data
    odds_api_key: Optional[str] = Field(default=None, alias='ODDS_API_KEY')
    pinnacle_api_key: Optional[str] = Field(default=None, alias='PINNACLE_API_KEY')
    draftkings_api_key: Optional[str] = Field(default=None, alias='DRAFTKINGS_API_KEY')
```

### Step 4: Integrate with CLI

Add CLI command in `walters_analyzer/cli.py`:

```python
@app.command()
def monitor_sharp_money(
    sport: str = typer.Option("nfl", help="Sport to monitor"),
    game_id: Optional[str] = typer.Option(None, help="Specific game ID"),
    duration: int = typer.Option(120, help="Duration in minutes")
):
    """Monitor market for sharp money movements"""
    import asyncio
    from walters_analyzer.feeds.market_monitor import MarketMonitor

    monitor = MarketMonitor()

    if game_id:
        asyncio.run(monitor.monitor_game(game_id, duration))
    else:
        print("Monitoring all games...")
        # Implementation for monitoring all games
```

---

## Recommended Data Providers

### 1. The Odds API (Easiest)
- **URL**: https://the-odds-api.com/
- **Cost**: Free tier (500 requests/month), Paid ($50-$200/mo)
- **Books**: 40+ including Pinnacle, DraftKings, FanDuel, BetMGM
- **Coverage**: NFL, NCAAF, NBA, MLB, NHL, Soccer
- **Pros**: Easy integration, multiple books, line history
- **Cons**: Rate limits, costs can add up

### 2. Pinnacle API (Sharp Book)
- **URL**: https://pinnacleapi.github.io/
- **Cost**: Free with funded account
- **Books**: Pinnacle only (but it's the sharpest)
- **Pros**: Direct sharp book access, free, real-time
- **Cons**: Need funded account, single book only

### 3. Action Network API
- **URL**: https://www.actionnetwork.com/
- **Cost**: Paid ($100+/mo)
- **Features**: Line movements, public betting percentages, sharp money indicators
- **Pros**: Built-in sharp vs public analysis
- **Cons**: Expensive

### 4. Don Best / SportsDataIO
- **URL**: https://sportsdata.io/
- **Cost**: Custom pricing ($500+/mo)
- **Features**: Real-time odds, line movements, injury data
- **Pros**: Professional-grade, very reliable
- **Cons**: Expensive, enterprise-focused

---

## Quick Start: Using The Odds API

1. **Sign up**: https://the-odds-api.com/
2. **Get API key**: Copy from dashboard
3. **Add to .env**:
   ```bash
   ODDS_API_KEY=your_key_here
   ```
4. **Test connection**:
   ```python
   from walters_analyzer.feeds.market_data_client import OddsAPIClient
   import asyncio

   async def test():
       client = OddsAPIClient()
       odds = await client.get_odds("americanfootball_nfl")
       print(f"Found {len(odds)} games")
       for game in odds[:3]:
           print(f"{game['teams']['away']} @ {game['teams']['home']}")

   asyncio.run(test())
   ```

5. **Monitor for sharp money**:
   ```bash
   uv run walters-analyzer monitor-sharp-money --sport nfl --duration 120
   ```

---

## Next Steps

1. ✅ Choose a data provider (recommend starting with The Odds API)
2. ✅ Create the market data client (use code above)
3. ✅ Set up monitoring with alerts
4. ✅ Integrate with your betting workflow
5. ✅ Backtest to validate sharp money signals

---

## Testing Without Live Data

For testing, you can use **mock data**:

```python
# Enable mock data in .env
DEVELOPMENT__MOCK_DATA=true

# Or in code
from walters_analyzer.config import get_settings
settings = get_settings()
settings.development.mock_data = True
```

This will simulate line movements for testing the monitoring system.

---

## Questions?

- **Q**: Which data provider should I use?
- **A**: Start with The Odds API (easiest). Upgrade to Don Best if you're betting serious money ($10k+ bankroll).

- **Q**: How often should I poll for odds?
- **A**: 15-30 seconds is ideal. More frequent = higher costs and rate limits.

- **Q**: Do I need access to all books?
- **A**: No. Just 1-2 sharp books (Pinnacle, Circa) and 2-3 public books (DK, FD, MGM) is sufficient.

- **Q**: Can I use this for live betting?
- **A**: Yes, but you need sub-second latency. The Odds API has 5-10 second delays. Direct book APIs are better for live betting.
