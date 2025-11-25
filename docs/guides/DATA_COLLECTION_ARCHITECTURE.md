# Data Collection Architecture Guide

Comprehensive reference for understanding and using the multi-method data collection infrastructure in Billy Walters Sports Analyzer.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Philosophy](#design-philosophy)
3. [Data Source Methods](#data-source-methods)
4. [Method Selection Decision Tree](#method-selection-decision-tree)
5. [Integration Patterns](#integration-patterns)
6. [Performance Characteristics](#performance-characteristics)
7. [Duplicate Detection & Cleanup](#duplicate-detection--cleanup)

---

## Architecture Overview

The data collection system is organized in **4 layers**:

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 4: Orchestrators (high-level workflows)                 │
│ • data_orchestrator.py - coordinates all collection           │
│ • live_odds_monitor.py - monitors during games                │
└─────────────────────────┬─────────────────────────────────────┘
                          │
┌───────────────────────────────────────────────────────────────┐
│ Layer 3: Processors & Validators (data transformation)        │
│ • espn_ncaaf_normalizer.py - standardizes ESPN data           │
│ • overtime_data_converter.py - converts to standard format    │
│ • overtime_signalr_parser.py - parses WebSocket messages      │
│ • validated_*.py - quality validation wrappers                │
└─────────────────────────┬─────────────────────────────────────┘
                          │
┌───────────────────────────────────────────────────────────────┐
│ Layer 2: Collection Methods (raw data fetching)               │
│ • HTTP Clients (async with retry/circuit breaker)             │
│ • Playwright Scrapers (browser automation)                    │
│ • WebSocket Clients (SignalR real-time)                       │
│ • API Clients (direct REST endpoints)                         │
└─────────────────────────┬─────────────────────────────────────┘
                          │
┌───────────────────────────────────────────────────────────────┐
│ Layer 1: Infrastructure (network & health)                    │
│ • health_monitor.py - success rate tracking & alerting        │
│ • proxy_manager.py - intelligent proxy handling               │
│ • web_fetch_client.py - general HTTP with retry logic         │
│ • network_analyzer.py - traffic inspection                    │
└───────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Intentional Variety** - Multiple methods per data source serve different use cases
2. **Layered Abstraction** - Separation of concerns enables flexibility
3. **Resilience** - Built-in retry logic, circuit breakers, fallbacks
4. **Validation** - Quality checks at each layer
5. **Monitoring** - Health tracking without intrusiveness

---

## Design Philosophy

### Why Multiple Methods Per Source?

Different scenarios require different approaches:

- **Speed**: Direct API calls beat browser automation
- **Real-time Updates**: WebSocket streams beat polling
- **Authentication**: Some methods require auth, others don't
- **Reliability**: Fallback options when primary fails
- **Feature Richness**: Different endpoints provide different data

### This is NOT Redundancy

The multiple methods in your codebase are **intentionally complementary**, not redundant:

| Method Type | Use Case | Speed | Features | Auth |
|-------------|----------|-------|----------|------|
| API Client | Scheduled collection | Fast | Basic | Optional |
| Hybrid Scraper | Extended monitoring | Slower | Rich | Required |
| WebSocket | Real-time updates | Very fast | Limited | Optional |
| Playwright | Public data | Slow | Rich | Optional |

---

## Data Source Methods

### OVERTIME.AG ODDS - 3 Working Methods

#### Method 1: Direct API Client (RECOMMENDED for speed)

**File:** `src/data/overtime_api_client.py`
**Script:** `scripts/scrapers/scrape_overtime_api.py`

**What it does:**
- Sends POST request to `https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering`
- Returns all pregame odds in single call
- No browser automation required
- No authentication needed for public odds

**Advantages:**
- ⚡ Ultra-fast: <5 seconds for NFL + NCAAF
- 🔄 No CloudFlare bypasses needed
- 🌐 Works on all platforms (Windows/Linux/Mac)
- 📊 Complete odds coverage in one request

**Disadvantages:**
- 📱 Limited to pregame odds (no live tracking)
- 🔌 No real-time updates

**Best for:**
- **Tuesday/Wednesday scheduled collection** (recommended)
- Data collection before games start
- Quick updates during business hours
- CI/CD pipelines (reliable, no browser needed)

**Usage:**
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```

**Output:**
```
output/overtime/nfl/pregame/
output/overtime/ncaaf/pregame/
```

---

#### Method 2: Hybrid Scraper with SignalR (RECOMMENDED for features)

**Files:**
- `src/data/overtime_hybrid_scraper.py` (main orchestrator)
- `src/data/overtime_signalr_client.py` (WebSocket client)
- `src/data/overtime_signalr_parser.py` (message parsing)

**What it does:**
- Uses Playwright for initial page load and authentication
- Establishes SignalR WebSocket connection for real-time updates
- Receives live odds updates as games progress
- Comprehensive data including injury updates, props, lines

**Advantages:**
- 📊 Rich feature set (injuries, props, moneylines, spreads)
- 🔄 Real-time updates during games
- 🎯 Can track line movement over time
- 📱 Mobile-like experience (full site features)

**Disadvantages:**
- 🐢 Slower initial connection (browser startup)
- 🔐 Requires authentication (credentials in .env)
- 💾 Higher memory usage (browser process)
- 🪟 Windows-specific quirks possible

**Best for:**
- **Live game monitoring** (recommended)
- Extended monitoring sessions (3+ hours)
- Tracking line movement throughout day
- Deep analytics requiring rich data

**Usage:**
```bash
uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 600
```

**Output:**
```
output/overtime/nfl/live/
output/overtime/ncaaf/live/
```

**Configuration:**
```bash
# Required in .env
OV_CUSTOMER_ID=your_id
OV_PASSWORD=your_password
```

---

#### Method 3: SignalR WebSocket Only (REAL-TIME ONLY)

**File:** `src/data/overtime_signalr_client.py`

**What it does:**
- Direct WebSocket connection to SignalR endpoint
- Receives real-time messages as they occur
- Lightweight, no browser automation

**Advantages:**
- ⚡ Fastest for real-time (no browser overhead)
- 💾 Minimal memory usage
- 🎯 Pure data stream (no UI parsing)

**Disadvantages:**
- 🔐 Requires valid SignalR connection token
- 📊 Less feature-rich than hybrid method
- 🔌 Connection can drop without fallback

**Best for:**
- **Pure real-time streaming** (advanced use only)
- Custom applications needing live data
- Minimal resource consumption scenarios

---

### OVERTIME.AG DECISION TREE

```
Need Overtime odds?
│
├─ Scheduled Tuesday/Wednesday collection?
│  └─ Use: overtime_api_client.py ⚡ (fastest)
│
├─ During games (tracking line movement)?
│  └─ Use: overtime_hybrid_scraper.py 📊 (most features)
│
└─ Pure live stream (advanced)?
   └─ Use: overtime_signalr_client.py 🌊 (WebSocket)
```

**Recommended Primary Workflow:**
1. Tuesday/Wednesday: Use `overtime_api_client.py` for pregame odds
2. Sunday (NFL)/Saturday (NCAAF) during games: Use `overtime_hybrid_scraper.py`
3. Advanced monitoring: Mix methods as needed

---

### ESPN DATA - 2 Clients (One Preferred)

#### DUPLICATE ALERT: espn_api_client.py is DEPRECATED

**❌ DO NOT USE:** `src/data/espn_api_client.py`
**✅ USE INSTEAD:** `src/data/espn_client.py`

**Why espn_client.py is superior:**
- ✅ Async/await (better concurrency)
- ✅ Automatic retry with exponential backoff
- ✅ Circuit breaker pattern (prevents cascading failures)
- ✅ Rate limiting (respects ESPN's API)
- ✅ Superior error handling

**Migration Status:**
- `espn_api_client.py` marked DEPRECATED with migration path
- All new code must use `espn_client.py`
- Consider archiving the old client in future session

---

#### ESPN Method: AsyncESPNClient (Only Option)

**File:** `src/data/espn_client.py`

**What it does:**
- Async HTTP client for ESPN APIs (NFL + NCAAF)
- Supports teams, schedules, standings, statistics, rosters
- Automatic retry with exponential backoff
- Circuit breaker after 5 consecutive failures
- Rate limiting (0.5s between requests)

**Advantages:**
- ⚡ Fast async operations
- 🔄 Automatic retries
- 🛡️ Circuit breaker protection
- 📊 Comprehensive endpoints
- 🔓 No authentication required

**Disadvantages:**
- 📊 Public data only (no premium endpoints)
- 🚦 Rate limited

**Best for:**
- Team data collection
- Schedule fetching
- Statistics gathering
- Standings updates

**Usage:**
```python
async with ESPNClient() as client:
    teams = await client.get_teams("NFL")
    scoreboard = await client.get_scoreboard("NFL", week=10)
    stats = await client.get_team_stats("NFL", team_id)
```

---

### ACTION NETWORK ODDS - 3 Complementary Methods

#### NOT A DUPLICATE - These Serve Different Purposes

**Method 1: HTTP Client (Authenticated)**

**File:** `src/data/action_network_client.py`

**What it does:**
- Direct HTTP requests to Action Network API endpoints
- Requires authentication (username/password)
- Fetches odds data in structured format

**Best for:**
- Premium subscribers with direct API access
- Programmatic access to authenticated features
- Integration with automated systems

**Requires:**
```bash
ACTION_USERNAME=...
ACTION_PASSWORD=...
```

---

#### Method 2: Playwright Scraper (Public Data)

**File:** `src/data/action_network_scraper.py`

**What it does:**
- Browser automation to extract public odds
- Parses HTML pages (no authentication required)
- Works with publicly visible betting lines

**Best for:**
- Free access to public odds
- Testing without authentication
- Fallback when API unavailable

**Advantages:**
- 🔓 No authentication required
- 📊 Access to public data

---

#### Method 3: Sitemap Scraper (Discovery)

**File:** `src/data/action_network_sitemap_scraper.py`

**What it does:**
- Uses XML sitemap to discover all available pages
- Ensures complete coverage of all games
- Prevents missing any betting lines

**Best for:**
- Comprehensive data collection
- Ensuring no games are missed
- Data quality validation

**Usage:**
```bash
uv run python scripts/scrapers/scrape_action_network_sitemap.py
```

---

#### ACTION NETWORK DECISION TREE

```
Need Action Network odds?
│
├─ Have premium authentication?
│  └─ Use: action_network_client.py (HTTP)
│
├─ Public data only?
│  └─ Use: action_network_scraper.py (Playwright)
│
└─ Need complete coverage?
   └─ Use: action_network_sitemap_scraper.py (Discovery)
```

---

### WEATHER DATA - 2 Providers (Primary + Fallback)

#### Provider 1: AccuWeather (PRIMARY)

**File:** `src/data/accuweather_client.py`

**Features:**
- More detailed forecasts
- Better accuracy
- Requires API key

**Set up:**
```bash
ACCUWEATHER_API_KEY=...
```

---

#### Provider 2: OpenWeather (FALLBACK)

**File:** `src/data/openweather_client.py`

**Features:**
- Free tier available
- Automatic fallback when AccuWeather fails
- Good coverage

**Set up:**
```bash
OPENWEATHER_API_KEY=...
```

---

#### Weather Strategy

**File:** `src/data/weather_client.py` (abstraction layer)

Automatically handles:
1. Try AccuWeather first
2. If fails, try OpenWeather
3. If both fail, return None
4. Transparent to caller

**Decision Tree:**
```
Get weather for game?
│
├─ Both services configured?
│  └─ WeatherClient handles fallback ✅
│
├─ Only AccuWeather?
│  └─ Use AccuWeatherClient directly
│
└─ Only OpenWeather?
   └─ Use OpenWeatherClient directly
```

---

## Method Selection Decision Tree

### Daily Decision Matrix

| Scenario | Method | Why |
|----------|--------|-----|
| **Before Tuesday games** | `scrape_overtime_api.py` | Fast, pregame odds essential |
| **Before Wednesday games** | `scrape_overtime_api.py` | Same as above |
| **Sunday morning (NFL)** | `scrape_overtime_api.py` | Get pregame odds before kickoff |
| **Sunday during games** | `scrape_overtime_hybrid.py` | Track line movement, monitor updates |
| **Saturday during NCAAF** | `scrape_overtime_hybrid.py` | Extended monitoring, lots of games |
| **After game starts** | `scrape_overtime_live.py` | Live odds tracking |
| **Team stats needed** | ESPN client | Power ratings, W-L records |
| **Injury updates** | ESPN injury scraper | Player status changes |
| **Betting market check** | Action Network sitemap | Complete odds discovery |
| **CI/CD automation** | `overtime_api_client.py` | Reliable, no browser needed |

---

## Integration Patterns

### Pattern 1: Scheduled Weekly Collection

**Recommended workflow:**

```python
# Tuesday 2:00 PM
async def tuesday_collection():
    # 1. Get Overtime pregame odds (fastest)
    nfl_odds = await overtime_api_client.fetch_nfl_odds()
    ncaaf_odds = await overtime_api_client.fetch_ncaaf_odds()

    # 2. Get ESPN team data
    async with ESPNClient() as espn:
        nfl_teams = await espn.get_teams("NFL")
        ncaaf_teams = await espn.get_teams("NCAAF")

    # 3. Get weather for all games
    weather_data = await weather_client.get_all_forecasts(games)

    # 4. Validate quality
    validated = validate_all_data()

    return validated
```

---

### Pattern 2: Live Game Monitoring

**Recommended workflow:**

```python
# Sunday 1:00 PM (NFL) or Saturday 12:00 PM (NCAAF)
async def live_monitoring():
    # Use hybrid scraper for rich real-time data
    monitor = OvertimeHybridScraper()

    # Monitor for 3-4 hours (NFL full slate)
    await monitor.start_monitoring(
        duration_hours=4,
        leagues=["NFL"],
        update_interval_seconds=10  # New odds every 10s
    )

    # Track line movement
    # Detect sharp action
    # Monitor injury updates
```

---

### Pattern 3: Data Quality Validation

```python
# After any collection
async def validate_collection(data):
    # ESPN validation
    espn_validator = ESPNDataValidator()
    validated_espn, espn_report = espn_validator.validate_teams(data)

    # Action Network validation
    action_validator = ActionNetworkValidator()
    validated_action, action_report = action_validator.validate_odds(data)

    # Overall quality
    if espn_report.quality_score < 80:
        log_warning("ESPN data quality below threshold")

    if action_report.quality_score < 85:
        log_warning("Odds data quality below threshold")

    return validated_espn, validated_action
```

---

## Performance Characteristics

### Speed Comparison (Approximate)

| Method | Speed | Notes |
|--------|-------|-------|
| `overtime_api_client.py` | <5 seconds | Both leagues at once |
| `espn_client.py` | 1-2 seconds/team | Depends on team count |
| `overtime_hybrid_scraper.py` | 30+ seconds | Browser startup overhead |
| `action_network_scraper.py` | 5-10 seconds | Depends on page count |
| `weather_client.py` | <1 second | Cached locations |

### Resource Usage

| Client | Memory | CPU | Network |
|--------|--------|-----|---------|
| API clients | ~50MB | Low | Moderate |
| Playwright scraper | ~300-500MB | High | Moderate |
| WebSocket client | ~100MB | Low | Continuous |

### Reliability

| Method | Success Rate | Fallback |
|--------|--------------|----------|
| Overtime API | 98%+ | Hybrid scraper |
| ESPN client | 96%+ | Cached data |
| Action Network HTTP | 92%+ | Playwright scraper |
| Weather | 99%+ | Automated provider fallback |

---

## Duplicate Detection & Cleanup

### Current Status: MOSTLY CLEAN

#### DUPLICATE IDENTIFIED & MARKED

✅ **espn_api_client.py** → Marked DEPRECATED
- Inferior version of `espn_client.py`
- Lacks async, retry logic, circuit breaker
- Recommendation: Archive in next cleanup session

**No other duplicates found.** The multiple methods for other sources are intentional and complementary.

#### Cleanup Roadmap

**Completed:**
1. ✅ Added deprecation notice to `espn_api_client.py`
2. ✅ Documented migration path to `espn_client.py`

**Future work** (can be deferred):
1. Archive `espn_api_client.py` to `src/data/archive/`
2. Clean up archived Overtime legacy code (7 files already in archive)
3. Review all imports and update to use `espn_client.py`

---

## Summary: Which Method to Use

| When | What | Why |
|------|------|-----|
| **Scheduled collection** | `overtime_api_client.py` | Fastest, most reliable |
| **Live game monitoring** | `overtime_hybrid_scraper.py` | Real-time + features |
| **Quick testing** | `overtime_api_client.py` | No setup needed |
| **CI/CD pipelines** | `overtime_api_client.py` | No browser required |
| **Comprehensive odds** | Action Network sitemap | Ensures complete coverage |
| **Team/stat data** | ESPN client (`espn_client.py`) | Only working option |
| **Weather** | `weather_client.py` | Auto-handles fallback |

---

## Next Steps

1. ✅ Review this guide
2. ✅ Update your `/edge-detector` command to use `overtime_api_client.py`
3. ✅ Consider deferring `ESPN api_client.py` archival (low priority)
4. ✅ Document any custom workflows specific to your use cases

---

**Last Updated:** 2025-11-24
**Architecture Status:** Clean and intentional - minimal duplicates, good separation of concerns
**Maintenance Priority:** Low - system is stable and well-designed
