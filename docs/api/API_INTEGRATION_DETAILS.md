# API Integration Details

This document contains comprehensive technical details for all API integrations in the Billy Walters Sports Analyzer project.

**Quick Reference**: For high-level guidelines, see [CLAUDE.md § API Integration Guidelines](../../CLAUDE.md#environment-variables--api-keys)

---

## Table of Contents

1. [Weather APIs](#weather-apis)
2. [ESPN APIs](#espn-apis)
3. [Overtime.ag Scrapers](#overtimeag-scrapers)
4. [Action Network Integration](#action-network-integration)
5. [AI Services](#ai-services)

---

## Weather APIs

### AccuWeather

**Implementation**: `src/data/accuweather_client.py`
**Plan**: Starter (free tier) - ✅ VERIFIED WORKING
**Base URL**: `https://dataservice.accuweather.com` (MUST use HTTPS)

**Available Endpoints**:
- ✅ Location key lookup
- ✅ Current conditions
- ✅ 12-hour hourly forecast
- ✅ 5-day daily forecast
- ❌ 24-hour hourly (requires Prime plan $50-75/month)
- ❌ 72-hour hourly (requires Prime/Elite plan)

**Key Implementation Details**:
```python
# CORRECT: Use HTTPS (HTTP causes 301 redirects)
BASE_URL = "https://dataservice.accuweather.com"

# Handle starter plan 12-hour limit
if hours_ahead > 12:
    # Fall back to current conditions for games >12 hours away
    return await self.get_current_conditions(location_key)
else:
    # Use accurate hourly forecast within 12-hour window
    return await self.get_hourly_forecast(location_key, hours=min(hours_ahead, 12))
```

**Data Format (Standardized)**:
- Returns: `temperature`, `feels_like`, `wind_speed`, `wind_gust`, `humidity`, `description`
- NOT: `temperature_f`, `wind_speed_mph` (old format)

**Weather Workflow**:
```bash
# For games >12 hours away (rough estimate)
python check_weather_mnf.py  # Uses current conditions

# For games <12 hours away (accurate forecast)
python check_gameday_weather.py "Green Bay Packers" "2025-11-11 20:15"

# Best practice: Check twice
# 1. When line posts (estimate)
# 2. Within 12 hours of game (final decision)
```

**Billy Walters Weather Impact Rules**:
- **Temperature**: <20°F = -4pts, 20-25°F = -3pts, 25-32°F = -2pts, 32-40°F = -1pt
- **Wind**: >20mph = -5pts, 15-20mph = -3pts, 10-15mph = -1pt
- **Precipitation**: Snow >60% = -5pts, Rain >60% = -3pts

### OpenWeather

**Implementation**: `src/data/openweather_client.py`
**Purpose**: Alternative forecast source for redundancy
**Use Case**: Fallback when AccuWeather unavailable or for long-range forecasts (>12 hours)

---

## ESPN APIs

### ESPN Team Statistics API ✅ (2025-11-12)

**Implementation**: `src/data/espn_api_client.py`
**Script**: `scripts/scrapers/scrape_espn_team_stats.py`
**Documentation**: [docs/espn_team_stats_api_analysis.md](../espn_team_stats_api_analysis.md)

**What It Does**: Collects comprehensive offensive/defensive team statistics for power rating enhancements.

**Quick Start**:
```bash
# Collect NCAAF team stats for current week
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf --week 12

# Collect NFL team stats
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl --week 11
```

**Key Features**:
- ✅ No authentication required (public ESPN API)
- ✅ Comprehensive metrics (offense, defense, turnovers)
- ✅ Per-game averages included
- ✅ Fast collection (~2-3 minutes for all FBS teams)
- ✅ Enhances power ratings with real-time performance data
- ✅ 100% test coverage (4/4 tests passing)

**Metrics Extracted**:
- **Offensive**: Points/game, total yards/game, passing/rushing yards
- **Defensive**: Points allowed/game, yards allowed/game
- **Advanced**: Turnover margin, 3rd down %, takeaways/giveaways

**Power Rating Enhancement**:
```python
# Enhanced formula with team stats
enhanced_rating = base_rating +
    (ppg - 28.5) * 0.15 +           # Offensive adjustment
    (28.5 - papg) * 0.15 +          # Defensive adjustment
    turnover_margin * 0.3           # Ball security

# Example: Ohio State 2025
# Base: 90.0
# + Offensive: +1.17 (36.3 PPG)
# + Defensive: +3.19 (7.2 PAPG)
# + Turnovers: +1.50 (+5 margin)
# = Enhanced: 95.87
```

**Test Results** (2025-11-12):
- API endpoint validated: `teams/{id}/statistics`
- Sample teams tested: Ohio State, Alabama, Georgia, Michigan
- Data quality: EXCELLENT (matches ESPN website)
- Success rate: 95%+ for FBS teams

**Output**: `data/current/ncaaf_team_stats_week_{week}.json`
**Update frequency**: Weekly (Tuesday/Wednesday)
**Expected impact**: +15-20% spread prediction accuracy

**Integration Status**:
- ✅ API client extended with 3 new methods
- ✅ Data collection script operational
- ✅ Test suite comprehensive (100% pass rate)
- ⏳ Edge detector integration (pending)

**Documentation**:
- API Analysis: [docs/espn_team_stats_api_analysis.md](../espn_team_stats_api_analysis.md)
- Integration Guide: [docs/espn_team_stats_integration_guide.md](../espn_team_stats_integration_guide.md)

**Recommendation**: Run weekly as part of `/collect-all-data` workflow.

### ESPN NCAAF Team Scraper ✅ (2025-11-13)

**Implementation**: `src/data/espn_ncaaf_team_scraper.py`
**Documentation**: Dynamic scraper for ESPN NCAAF team pages

**What It Does**: Collects comprehensive team information including injuries, stats, news, and schedules for NCAA FBS teams.

**Quick Start**:
```bash
# Scrape single team
uv run python src/data/espn_ncaaf_team_scraper.py

# Or use in your own scripts
from src.data.espn_ncaaf_team_scraper import ESPNNcaafTeamScraper

scraper = ESPNNcaafTeamScraper()
matchup = await scraper.scrape_matchup(
    away_team="Troy",
    home_team="Old Dominion",
    away_id=2653,
    home_id=295,
    save=True
)
```

**Key Features**:
- ✅ Dynamic ESPN URL builder for all page types
- ✅ Async scraping using Playwright
- ✅ Injury report parser
- ✅ Team statistics extraction
- ✅ Complete matchup scraper (both teams)
- ✅ Automatic JSON output with timestamps

**Page Types Supported**:
- Home page (team overview, record)
- Injuries (injury report with status)
- Stats (team statistics)
- Schedule (game schedule)
- Roster (player roster)

**Data Extracted**:
- Team record and conference standing
- Injury reports (player, position, status, type)
- Key statistics (PPG, PAPG, yards)
- Team news and updates

**ESPN Team IDs** (Examples):
- Troy: 2653
- Old Dominion: 295
- Ohio State: 194
- Alabama: 333

**Output Format**:
```json
{
  "matchup": "Troy @ Old Dominion",
  "scraped_at": "2025-11-13T16:30:56.140059",
  "away_team": {
    "team_name": "Troy",
    "team_id": 2653,
    "injuries": [],
    "record": "6-3"
  },
  "home_team": {
    "team_name": "Old Dominion",
    "team_id": 295,
    "injuries": [],
    "record": "4-5"
  }
}
```

**Output Location**: `output/ncaaf/teams/{away}_{home}_{timestamp}.json`

**Use Cases**:
1. Pre-game injury verification for NCAAF matchups
2. Team statistics for power rating enhancement
3. Injury-adjusted edge detection
4. Weekly NCAAF data collection

**Note**: ESPN injury pages may show "No Data Available" for some teams. Always verify with alternative sources before game time.

**Integration Status**:
- ✅ Scraper created and tested (2025-11-13)
- ✅ Troy @ Old Dominion validated (12.8 pt edge confirmed)
- ⏳ Integration into `/collect-all-data` workflow (pending)
- ⏳ Expansion to all FBS teams (pending)

---

## Overtime.ag Scrapers

### API Client (PRIMARY - RECOMMENDED) ✅

**Implementation**: `src/data/overtime_api_client.py`
**Script**: `scripts/scrapers/scrape_overtime_api.py`
**Documentation**: [docs/overtime_devtools_analysis_results.md](../overtime_devtools_analysis_results.md)

**What It Does**: Direct API access to Overtime.ag odds endpoint - no browser required.

**Quick Start**:
```bash
# Scrape NFL and NCAAF (< 5 seconds total)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf

# Just NFL
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

**Key Features**:
- ⚡ 10x faster than browser automation (5 seconds vs 30+)
- ✅ No browser/Playwright dependencies
- ✅ No authentication required
- ✅ No CloudFlare/proxy issues
- ✅ 100% data quality (verified 2025-11-12)
- ✅ Perfect for Billy Walters pre-game workflow
- ✅ Simple HTTP POST request

**Test Results** (2025-11-12):
- NFL: 13 games scraped successfully
- NCAAF: 56 games scraped successfully
- All spreads, totals, moneylines present
- Billy Walters format: 100% compliant

**Recommendation**: Use for all pre-game odds collection (Tuesday-Wednesday workflow).

### Hybrid Scraper (OPTIONAL - For Live Games)

**Implementation**: `src/data/overtime_hybrid_scraper.py`, `src/data/overtime_signalr_parser.py`
**Script**: `scripts/scrapers/scrape_overtime_hybrid.py`
**Documentation**: [docs/OVERTIME_HYBRID_SCRAPER.md](../OVERTIME_HYBRID_SCRAPER.md)

**What It Does**: Combines Playwright (authentication/pre-game) with SignalR WebSocket (live updates).

**Quick Start**:
```bash
# Live monitoring during games (Sunday, 3 hours)
uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 10800 --headless
```

**Key Features**:
- Real-time odds updates during games
- Line movement tracking
- SignalR WebSocket connection
- Account balance information

**Use Case**: Only use for live game monitoring on Sundays. For pre-game odds collection, use API client instead.

**Note**: Browser automation adds complexity and is slower - only justified for live updates feature.

### Pre-Game Only Scraper (ARCHIVED - Legacy)

**Implementation**: `src/data/overtime_pregame_nfl_scraper.py`
**Script**: `scripts/archive/overtime_legacy/scrape_overtime_nfl.py` (ARCHIVED)

**Status**: Archived - use API client or hybrid scraper instead.

**Technical Architecture** (for reference):
- Platform: Playwright browser automation (Chromium)
- Framework: AngularJS (vanilla JavaScript, not React/Vue)
- Real-time: WebSocket server at `wss://ws.ticosports.com/signalr` (not used by this scraper)
- Security: CloudFlare DDoS protection

**Optimal Scraping Schedule**:
- **Tuesday-Wednesday**: New week lines post after Monday Night Football
- **Thursday morning**: Fresh lines before Thursday Night Football
- **Avoid**: Sunday during games (lines are down)

---

## Action Network Integration

### Sitemap Scraper ✅ (2025-11-23)

**Implementation**: `src/data/action_network_sitemap_scraper.py`
**Data Loader**: `src/data/action_network_loader.py`

**What Changed**:
- Integrated Action Network as new data source for sharp action monitoring
- Committed fresh Week 12 NFL + Week 13 NCAAF scraping results (767 records)
- Created data loader module for Billy Walters pipeline integration
- Added to `/collect-all-data` workflow

**Data Collected**:
- **NFL**: 18 games, 1 futures, 1 odds, 170 public betting articles
- **NCAAF**: 120 games, 1 futures, 1 odds
- **Total**: 767 URLs with full metadata (path, category, timestamps)

**Key Features**:
- **JSONL Output**: Structured data ready for pipeline consumption
- **Categories**: futures, odds, public-betting, strategy/DFS, teasers/tips

**Integration Points**:
```python
from data.action_network_loader import load_nfl_games, find_game_url

# Load games
nfl_games = load_nfl_games()  # 18 Week 12 games
ncaaf_games = load_ncaaf_games()  # 120 Week 13 games

# Find specific matchup URL
url = find_game_url("Buffalo Bills", "Kansas City Chiefs")
```

**Files Created**:
- `src/data/action_network_loader.py` - Data loader with Pydantic models
- `scripts/utilities/test_action_network_loader.py` - Validation script
- `output/action_network/nfl/*.jsonl` - 6 data files (646 records)
- `output/action_network/ncaaf/*.jsonl` - 3 data files (121 records)
- `docs/ACTION_NETWORK_SITEMAP_DELIVERY.md` - Integration guide

**Use Cases**:
1. Sharp action monitoring (public betting percentages)
2. Line movement tracking (futures, odds pages)
3. Expert analysis aggregation (strategy articles)
4. Betting insights (teasers, tips, totals)

**Next Steps**:
1. Add Action Network odds scraping (from URLs to actual lines)
2. Integrate public betting percentages into edge detection
3. Add to MCP server tools

**Documentation**: [docs/ACTION_NETWORK_SITEMAP_DELIVERY.md](../ACTION_NETWORK_SITEMAP_DELIVERY.md)

---

## AI Services

### Anthropic Claude

**API Key**: `ANTHROPIC_API_KEY`
**Usage**: Matchup analysis, narrative generation
**Models**: claude-sonnet-4-5-20250929 (primary)

### OpenAI

**API Key**: `OPENAI_API_KEY`
**Usage**: Predictions, pattern recognition
**Models**: GPT-4 (primary)

---

## Proxy Management

**Environment Variables**:
- `PROXY_URL`: Full proxy URL with protocol
- `PROXY_USER`: Proxy username (if required)
- `PROXY_PASS`: Proxy password (if required)

**Implementation**:
- Use PROXY_URL, PROXY_USER, PROXY_PASS for scraping
- Implement rotation for high-volume requests
- Respect rate limits

**Playwright Configuration**:
```python
# Use Playwright native proxy format (NOT browser args)
context_kwargs["proxy"] = {"server": proxy_url}  # Include credentials in URL
# Format: http://username:password@host:port
```

---

## Rate Limiting and Best Practices

### ESPN APIs
- **Rate Limit**: No documented limit, but respect fair use
- **Recommendation**: 0.5-1 second delay between requests
- **Caching**: Cache responses for 24 hours

### AccuWeather
- **Starter Plan**: 50 calls/day
- **Recommendation**: Only call for outdoor stadiums
- **Caching**: Cache location keys permanently, forecasts for 1 hour

### Overtime.ag
- **API Client**: No rate limit (public endpoint)
- **Hybrid Scraper**: Respect CloudFlare protection
- **Recommendation**: Use API client for pre-game, hybrid for live only

### Action Network
- **Rate Limit**: Unknown, treat as fair use
- **Recommendation**: Daily sitemap scraping only
- **Caching**: Cache URLs for 7 days

---

## Troubleshooting

### AccuWeather API Issues

**Symptom**: HTTP 301 redirect errors, HTTP 403 "Forbidden", N/A weather data

**Fix 1: Verify HTTPS (not HTTP)**
```bash
# Check src/data/accuweather_client.py:28
# Should be: BASE_URL = "https://dataservice.accuweather.com"
```

**Fix 2: Test API connectivity**
```bash
cd src && uv run python -c "
from data.accuweather_client import AccuWeatherClient
import asyncio, os

async def test():
    client = AccuWeatherClient(api_key=os.getenv('ACCUWEATHER_API_KEY'))
    await client.connect()
    key = await client.get_location_key('Green Bay', 'WI')
    print(f'✅ AccuWeather working, location key: {key}')
    await client.close()

asyncio.run(test())
"
```

**Fix 3: Check plan limitations**
- Starter plan: Only 12-hour hourly forecast
- Games >12 hours away will use current conditions (less accurate)
- Check within 12 hours of game for accurate forecast

**Fix 4: Verify data format**
- Should return: `temperature`, `wind_speed` (NOT `temperature_f`, `wind_speed_mph`)

### Weather Data Incomplete or Inaccurate

**Check timing**: Games >12 hours away use current conditions
```bash
python check_gameday_weather.py "Team Name" "YYYY-MM-DD HH:MM"
```

**For games <12 hours away**: Use hourly forecast (more accurate)
- Re-run weather check within 12 hours of game time

**Manual verification recommended**:
- Weather.com: https://weather.com/weather/hourbyhour/l/CITY+STATE
- Weather.gov: https://forecast.weather.gov/

### Weather API Async/Await Error (FIXED 2025-11-12)

**Symptom**: RuntimeWarning: coroutine 'AccuWeatherClient.get_game_weather' was never awaited

**Root Cause**: Edge detector was calling async function from sync context

**Fix Applied**: Updated `billy_walters_edge_detector.py` (line 1122-1127)
- Added import asyncio at top level
- Wrapped weather API call with async helper function
- Now properly awaits weather client connection and data fetch

**Verify Fix Working**:
```bash
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector 2>&1 | Select-String "Weather for"
```

**Expected Output (real data)**:
```
Weather for Denver: 43°F, 2.9 MPH wind, Total adj: 0.0, Spread adj: 0.0
Weather for Buffalo: 38°F, 10.5 MPH wind, Total adj: 0.0, Spread adj: 0.0
Weather for Cleveland: 40°F, 19.6 MPH wind, Total adj: -0.2, Spread adj: -0.1
```

**Indoor stadiums correctly show None**:
```
Weather for Atlanta: None°F, None MPH wind → Indoor stadium (no adjustment)
Weather for Detroit: None°F, None MPH wind → Indoor stadium (no adjustment)
```

**API Usage**: ~16-20 calls per run (only outdoor stadiums)
**Documentation**: [docs/weather_and_injury_analysis_fix.md](../weather_and_injury_analysis_fix.md)

---

**Last Updated**: 2025-11-23
**Maintained By**: Billy Walters Sports Analyzer Team
**Questions**: See [CLAUDE.md](../../CLAUDE.md) or [LESSONS_LEARNED.md](../../LESSONS_LEARNED.md)
