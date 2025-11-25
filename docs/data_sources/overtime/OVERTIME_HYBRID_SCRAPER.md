# Overtime.ag Hybrid Scraper Documentation

## Overview

The **Overtime.ag Hybrid Scraper** combines two complementary technologies to provide complete odds coverage:

1. **Playwright** - Browser automation for authentication and pre-game odds scraping
2. **SignalR** - WebSocket real-time updates for live odds during games

This hybrid approach gives you the best of both worlds:
- Static pre-game lines for initial analysis
- Real-time live updates during games for in-play opportunities

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Overtime.ag Hybrid Scraper                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  PHASE 1: Playwright (Static Pre-Game)                   │
│  ┌─────────────────────────────────────────────┐        │
│  │ 1. Launch Chromium browser                   │        │
│  │ 2. Navigate to overtime.ag/sports            │        │
│  │ 3. Login with OV_CUSTOMER_ID/OV_PASSWORD    │        │
│  │ 4. Extract account balance                   │        │
│  │ 5. Click NFL section                         │        │
│  │ 6. Parse spreads, totals, moneylines        │        │
│  │ 7. Extract for GAME, 1H, 1Q periods         │        │
│  └─────────────────────────────────────────────┘        │
│                       ↓                                   │
│  PHASE 2: SignalR (Real-Time Live)                       │
│  ┌─────────────────────────────────────────────┐        │
│  │ 1. Connect to wss://ws.ticosports.com       │        │
│  │ 2. Subscribe as authenticated customer      │        │
│  │ 3. Subscribe to NFL sport feed              │        │
│  │ 4. Listen for events:                        │        │
│  │    - gameUpdate (team names, scores)        │        │
│  │    - linesUpdate (betting lines changes)    │        │
│  │    - oddsUpdate (odds movements)            │        │
│  │    - scoreUpdate (live score changes)       │        │
│  │ 5. Parse to Billy Walters format            │        │
│  │ 6. Keep connection alive with pings         │        │
│  └─────────────────────────────────────────────┘        │
│                       ↓                                   │
│  PHASE 3: Merge & Save                                   │
│  ┌─────────────────────────────────────────────┐        │
│  │ 1. Combine pre-game + live updates          │        │
│  │ 2. Convert to Billy Walters format          │        │
│  │ 3. Save to output/overtime/nfl/              │        │
│  │ 4. Ready for edge detection                 │        │
│  └─────────────────────────────────────────────┘        │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Files Created

### Core Implementation

**`src/data/overtime_hybrid_scraper.py`**
- Main scraper class combining Playwright + SignalR
- Handles authentication, navigation, and WebSocket connection
- Manages two-phase scraping workflow
- Automatic reconnection on disconnect

**`src/data/overtime_signalr_parser.py`**
- Parses SignalR WebSocket messages to Billy Walters format
- Handles different event types: gameUpdate, linesUpdate, oddsUpdate, scoreUpdate
- Merges incremental updates into complete game data
- Validates and normalizes odds formats

**`scripts/scrape_overtime_hybrid.py`**
- Command-line interface for running the hybrid scraper
- Configurable parameters (headless, duration, proxy)
- Error handling and progress reporting
- Example usage and best practices

## Installation

The hybrid scraper requires these dependencies (already in your project):

```bash
# Install dependencies
uv add playwright signalrcore pydantic

# Install Playwright browsers
uv run playwright install chromium
```

## Environment Variables

Required in `.env` file:

```bash
# Overtime.ag credentials (required)
OV_CUSTOMER_ID=your_customer_id
OV_PASSWORD=your_password

# Proxy (optional)
PROXY_URL=http://user:pass@proxy:port
PROXY_USER=username
PROXY_PASS=password
```

## Usage

### Basic Usage

```bash
# Default: 2 minutes of SignalR listening
uv run python scripts/scrape_overtime_hybrid.py
```

### Extended Listening (During Live Games)

```bash
# Listen for 30 minutes during Sunday games
uv run python scripts/scrape_overtime_hybrid.py --duration 1800

# Listen for entire game (3+ hours)
uv run python scripts/scrape_overtime_hybrid.py --duration 10800
```

### Pre-Game Only (No SignalR)

```bash
# Just scrape static lines, skip live updates
uv run python scripts/scrape_overtime_hybrid.py --no-signalr
```

### Production Mode (Headless)

```bash
# Run in background without browser window
uv run python scripts/scrape_overtime_hybrid.py --headless --duration 3600
```

### With Custom Proxy

```bash
# Use specific proxy instead of smart proxy
uv run python scripts/scrape_overtime_hybrid.py --proxy "http://user:pass@proxy:port"
```

### Custom Output Directory

```bash
# Save to different location
uv run python scripts/scrape_overtime_hybrid.py --output "data/odds/nfl"
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--customer-id` | Overtime.ag customer ID | `OV_CUSTOMER_ID` env var |
| `--password` | Overtime.ag password | `OV_PASSWORD` env var |
| `--proxy` | Proxy URL with credentials | Smart proxy (auto) |
| `--no-proxy` | Disable proxy completely | False |
| `--headless` | Run browser without GUI | False |
| `--output` | Output directory path | `output/overtime/nfl` |
| `--no-signalr` | Skip real-time updates | False |
| `--duration` | SignalR listen time (seconds) | 120 |

## Output Format

The scraper saves a JSON file with this structure:

```json
{
  "metadata": {
    "source": "overtime.ag",
    "scraper": "hybrid (playwright + signalr)",
    "scraped_at": "2025-11-11T12:00:00",
    "version": "1.0.0"
  },
  "account": {
    "balance": "$1,234.56",
    "available": "$1,000.00",
    "pending": "$234.56"
  },
  "pregame": {
    "games": [
      {
        "game_id": "12345",
        "visitor": {
          "name": "Philadelphia Eagles",
          "rotation": 101,
          "spread": -3.5,
          "spread_odds": -110,
          "moneyline": -170,
          "total": 47.5
        },
        "home": {
          "name": "Green Bay Packers",
          "rotation": 102,
          "spread": 3.5,
          "spread_odds": -110,
          "moneyline": 150,
          "total": 47.5
        },
        "period": "GAME",
        "is_live": false,
        "scraped_at": "2025-11-11T12:00:00"
      }
    ],
    "count": 15
  },
  "live": {
    "updates": [
      {
        "timestamp": "2025-11-11T15:30:00",
        "type": "linesUpdate",
        "data": {
          "gameId": 12345,
          "lines": {
            "visitor": {"spread": -4.0, "spreadOdds": -115},
            "home": {"spread": 4.0, "spreadOdds": -105}
          }
        }
      },
      {
        "timestamp": "2025-11-11T15:35:00",
        "type": "scoreUpdate",
        "data": {
          "gameId": 12345,
          "score": {"visitor": 7, "home": 0},
          "quarter": "Q1",
          "timeRemaining": "8:32"
        }
      }
    ],
    "count": 127
  }
}
```

## SignalR Event Types

The SignalR WebSocket sends these event types:

### 1. gameUpdate
Full game state (teams, scores, status)

```json
{
  "gameId": 12345,
  "visitor": {"name": "Philadelphia Eagles", "rotation": 101},
  "home": {"name": "Green Bay Packers", "rotation": 102},
  "status": "live",
  "score": {"visitor": 14, "home": 21},
  "quarter": "Q2",
  "timeRemaining": "5:32"
}
```

### 2. linesUpdate
Betting line changes (spread, total, moneyline)

```json
{
  "gameId": 12345,
  "lines": {
    "visitor": {
      "spread": -3.5,
      "spreadOdds": -110,
      "moneyline": -170,
      "total": 47.5
    },
    "home": {
      "spread": 3.5,
      "spreadOdds": -110,
      "moneyline": 150,
      "total": 47.5
    }
  }
}
```

### 3. oddsUpdate
Odds movements (American odds format changes)

```json
{
  "gameId": 12345,
  "odds": {
    "visitor": {"spread": -115, "moneyline": -180},
    "home": {"spread": -105, "moneyline": 160}
  }
}
```

### 4. scoreUpdate
Live score changes during game

```json
{
  "gameId": 12345,
  "score": {"visitor": 14, "home": 21},
  "quarter": "Q2",
  "timeRemaining": "5:32"
}
```

## Optimal Timing

### Pre-Game Scraping
**Best Times:**
- Tuesday: 12 PM - 6 PM ET (lines post after Monday Night Football)
- Wednesday: 12 PM - 6 PM ET (sharp action settles)
- Thursday: Before 8 PM ET (before Thursday Night Football)

**Worst Times:**
- Sunday: 1 PM - 11 PM ET (games in progress, lines down)
- Monday: 8 PM - 11 PM ET (Monday Night Football in progress)

### Live Updates (SignalR)
**Best Times:**
- Sunday: 1 PM - 11 PM ET (afternoon and evening games)
- Monday: 8 PM - 11 PM ET (Monday Night Football)
- Thursday: 8 PM - 11 PM ET (Thursday Night Football)

**Duration Recommendations:**
- Quick test: 2 minutes (`--duration 120`)
- Single game: 3-4 hours (`--duration 12000`)
- Full Sunday slate: 10+ hours (`--duration 36000`)

## Integration with Billy Walters Workflow

### 1. Collect Pre-Game Data (Tuesday-Wednesday)

```bash
# Scrape pre-game lines
uv run python scripts/scrape_overtime_hybrid.py --no-signalr --headless

# Run edge detection
/edge-detector

# Generate betting card
/betting-card
```

### 2. Monitor Live Games (Sunday)

```bash
# Start live monitoring during games
uv run python scripts/scrape_overtime_hybrid.py --duration 10800 --headless

# In separate terminal: Track CLV
/clv-tracker
```

### 3. Post-Game Analysis

```bash
# Update closing lines and scores
/clv-tracker --update-all

# Document lessons learned
/document-lesson
```

## Troubleshooting

### SignalR Not Connecting

**Symptom:** "SignalR connection failed" or no live updates received

**Solutions:**
1. Check credentials are correct: `echo $OV_CUSTOMER_ID`
2. Verify network allows WebSocket: Test in browser DevTools
3. Try without proxy: `--no-proxy`
4. Check firewall allows outbound WebSocket connections

### No Pre-Game Lines Found

**Symptom:** 0 games found during Playwright phase

**Solutions:**
1. Check timing: Lines only available Tuesday-Thursday
2. Verify login succeeded: Look for "Login successful" message
3. Run in non-headless mode to see page: Remove `--headless`
4. Check NFL section loaded: Look for "NFL-Game" text on page

### SignalR Receives No Updates

**Symptom:** Connected but 0 live updates after several minutes

**Solutions:**
1. Verify games are actually live: Check ESPN/NFL.com
2. Check subscription worked: Look for "Subscribing to customer and NFL"
3. Try longer duration: Use `--duration 600` (10 minutes)
4. Verify correct hub/event names: May need to reverse-engineer actual event names

### Authentication Failures

**Symptom:** "Login failed" or "credentials invalid"

**Solutions:**
1. Verify credentials in `.env`: `cat .env | grep OV_`
2. Try logging in manually in browser to verify account
3. Check for special characters in password (may need escaping)
4. Ensure OV_CUSTOMER_ID is numeric (not email)

## Advanced Usage

### Custom Event Handlers

Modify `overtime_hybrid_scraper.py` to add custom SignalR event handlers:

```python
# Add new event handler
self.signalr_connection.on("myCustomEvent", self._on_custom_event)

def _on_custom_event(self, data: Any) -> None:
    """Handler for custom event"""
    print(f"Custom event: {data}")
```

### Parsing New Message Formats

Modify `overtime_signalr_parser.py` to handle new message structures:

```python
@staticmethod
def parse_custom_event(data: Dict[str, Any]) -> Optional[BillyWaltersGame]:
    """Parse custom SignalR event"""
    # Your parsing logic here
    pass
```

### Automated Monitoring

Run hybrid scraper on a schedule (e.g., every Sunday during games):

```bash
# In cron or Task Scheduler
# Every Sunday at 1 PM, listen for 10 hours
0 13 * * 0 cd /path/to/project && uv run python scripts/scrape_overtime_hybrid.py --duration 36000 --headless
```

## Performance Considerations

### Memory Usage
- Playwright: ~200-300 MB per browser instance
- SignalR: ~10-20 MB for connection
- Each update stored in memory: ~1-5 KB
- 1000 updates ≈ 5 MB memory

**Recommendation:** For long-running scrapes (>2 hours), periodically save and clear `self.live_updates` list.

### Network Usage
- Playwright initial: ~2-5 MB per scrape
- SignalR keep-alive pings: ~100 bytes every 10 seconds
- Each odds update: ~500-2000 bytes
- 1 hour of updates ≈ 5-10 MB

**Recommendation:** Use `--headless` in production to reduce bandwidth.

### CPU Usage
- Playwright rendering: 5-15% CPU
- SignalR listening: <1% CPU
- Parsing updates: <1% CPU

**Recommendation:** Headless mode reduces CPU by ~50%.

## Security Best Practices

1. **Never commit credentials**: Always use `.env` file
2. **Use environment variables**: Reference `$OV_CUSTOMER_ID`, never hardcode
3. **Rotate passwords**: Change Overtime.ag password every 90 days
4. **Secure proxy credentials**: If using proxy, ensure credentials are encrypted
5. **Limit account permissions**: Use betting account, not admin account

## Testing

### Test Pre-Game Scraping (No Games Required)

```bash
# Test Playwright phase only (works anytime)
uv run python scripts/scrape_overtime_hybrid.py --no-signalr
```

### Test SignalR Connection (No Games Required)

```bash
# Test SignalR phase for 30 seconds
uv run python -c "
import asyncio
from src.data.overtime_signalr_client import OvertimeSignalRClient

async def test():
    client = OvertimeSignalRClient()
    client.start(duration=30)

asyncio.run(test())
"
```

### Full Integration Test (Requires Live Games)

```bash
# Run during Sunday games for 5 minutes
uv run python scripts/scrape_overtime_hybrid.py --duration 300
```

## Comparison: Hybrid vs. Individual Scrapers

| Feature | Hybrid | Playwright Only | SignalR Only |
|---------|--------|-----------------|--------------|
| Pre-game lines | ✓ | ✓ | ✗ |
| Live updates | ✓ | ✗ | ✓ |
| Account info | ✓ | ✓ | ✗ |
| Authentication | ✓ | ✓ | ✓ |
| Line movements | ✓ | ✗ | ✓ |
| Historical data | ✓ | ✓ | ✗ |
| Real-time alerts | ✓ | ✗ | ✓ |
| Complexity | Medium | Low | Low |
| Resource usage | High | Medium | Low |

**Recommendation:** Use hybrid scraper for comprehensive coverage during live games. Use Playwright-only for pre-game analysis.

## Future Enhancements

Potential improvements for future development:

1. **Auto-discovery of SignalR events**: Reverse-engineer actual event names
2. **Line movement detection**: Alert on significant odds changes (>2 points)
3. **CLV tracking integration**: Automatically update CLV when lines move
4. **Multi-sport support**: Extend to NCAAF, NBA, MLB
5. **Database storage**: Save updates to SQLite for historical analysis
6. **Web dashboard**: Real-time visualization of line movements
7. **Sharp action detection**: Identify professional money moves
8. **Arbitrage opportunities**: Cross-book odds comparison

## Resources

- **Playwright Docs**: https://playwright.dev/python/
- **SignalR Protocol**: https://docs.microsoft.com/en-us/aspnet/core/signalr/
- **signalrcore Library**: https://github.com/mandrewcito/signalrcore
- **Billy Walters Methodology**: See `CLAUDE.md` for core principles

## Support

If you encounter issues:

1. Check `LESSONS_LEARNED.md` for similar problems
2. Review this documentation thoroughly
3. Run with `--no-headless` to see browser behavior
4. Enable verbose logging in `overtime_hybrid_scraper.py`
5. Use `/document-lesson` to capture solutions for future reference

## License

Part of the Billy Walters Sports Analyzer project.
For educational and research purposes only.
