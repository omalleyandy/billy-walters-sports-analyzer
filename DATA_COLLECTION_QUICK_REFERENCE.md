# Data Collection Quick Reference

**Quick lookup guide for choosing the right data collection method. For detailed info, see [DATA_COLLECTION_ARCHITECTURE.md](docs/guides/DATA_COLLECTION_ARCHITECTURE.md)**

---

## One-Minute Decision Guide

### What are you collecting?

**OVERTIME ODDS:**
- Need data before Tuesday games? → `scrape_overtime_api.py` ⚡
- Monitoring during games? → `scrape_overtime_hybrid.py` 📊
- Pure real-time stream? → `overtime_signalr_client.py` 🌊

**ESPN DATA:**
- Teams, schedules, stats? → `espn_client.py` (AsyncESPNClient) ✅
- Using old `espn_api_client`? → Switch to `espn_client.py` 🔄

**ACTION NETWORK ODDS:**
- Have premium auth? → `action_network_client.py`
- Public data only? → `action_network_scraper.py`
- Need complete coverage? → `action_network_sitemap_scraper.py`

**WEATHER:**
- Most cases? → `weather_client.py` (handles fallback automatically)
- No config needed - it just works! 🌤️

---

## Method Comparison Matrix

### Overtime.ag Odds Collection

| Feature | API Client | Hybrid Scraper | WebSocket |
|---------|-----------|-----------------|-----------|
| **Speed** | <5 sec | 30+ sec | Real-time |
| **Features** | Pregame odds | Rich data + injuries | Stream only |
| **Auth** | Not needed | Required | Optional |
| **Browser** | No | Yes | No |
| **Best For** | Scheduled collection | Live monitoring | Advanced use |
| **Reliability** | 98%+ | 95%+ | 90%+ |
| **Setup** | Simple | Moderate | Complex |

**Recommendation:** Use API Client for Tuesday/Wednesday, Hybrid Scraper for game days

---

### Data Collection By Day/Time

```
TUESDAY/WEDNESDAY (Scheduled Collection - NFL)
├─ 2:00 PM: scrape_overtime_api.py --nfl                ⚡ <5 sec
├─ 2:05 PM: scrape_espn_team_stats.py --league nfl      📊 2 min
├─ 2:10 PM: scrape_massey_games.py                      📊 1 min
├─ 2:15 PM: weather_client.py --league nfl              🌤️ <1 sec
└─ 2:20 PM: scrape_action_network_sitemap.py --nfl      📱 2 min
Total time: ~7 minutes

TUESDAY/WEDNESDAY (Scheduled Collection - NCAAF)
├─ 2:30 PM: scrape_overtime_api.py --ncaaf              ⚡ <5 sec
├─ 2:35 PM: scrape_espn_team_stats.py --league ncaaf    📊 2 min
├─ 2:40 PM: scrape_massey_games.py --league college     📊 1 min
├─ 2:45 PM: weather_client.py --league ncaaf            🌤️ <1 sec
└─ 2:50 PM: scrape_action_network_sitemap.py --ncaaf    📱 2 min
Total time: ~7 minutes

SUNDAY (NFL Game Day)
├─ 12:00 PM: scrape_overtime_api.py --nfl               ⚡ Pregame odds
├─ 1:00 PM: scrape_overtime_hybrid.py --nfl --duration 10800  📊 For 3 hours
└─ After games: Run edge detection                      🎯

SATURDAY (NCAAF Game Day)
├─ 11:00 AM: scrape_overtime_api.py --ncaaf             ⚡ Pregame odds
├─ 12:00 PM: scrape_overtime_hybrid.py --ncaaf --duration 14400  📊 For 4 hours
└─ After games: Run edge detection                      🎯

CI/CD AUTOMATION
└─ Always use: scrape_overtime_api.py (--nfl or --ncaaf) ✅ Reliable, no browser
```

---

## Performance Quick Reference

### Speed Ranking (Fastest to Slowest)

```
1. weather_client.py              <1 sec
2. overtime_api_client.py         <5 sec
3. espn_client.py                 1-2 sec per team
4. massey_ratings_scraper.py      1-2 min
5. action_network_scraper.py      5-10 sec
6. overtime_hybrid_scraper.py     30+ sec
```

**Pro Tip:** Run weather + Overtime API first (super fast), then ESPN/Massey (can take longer)

---

## Setup Checklist

### Minimum Required (for pregame collection)

- [ ] `.env` file with no additional config needed
- [ ] ESPN data ready (no auth required)
- [ ] That's it! API client works with defaults

### Recommended (for live monitoring)

- [ ] `OV_CUSTOMER_ID` and `OV_PASSWORD` in .env (for hybrid scraper)
- [ ] `ACCUWEATHER_API_KEY` in .env (weather)

### Optional (for advanced features)

- [ ] `ACTION_USERNAME` and `ACTION_PASSWORD` (for auth client)
- [ ] `OPENWEATHER_API_KEY` (weather fallback)

---

## Common Workflows

### Quick Pregame Odds - NFL (Tuesday/Wednesday)

```bash
# 5 seconds - NFL odds only
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

### Quick Pregame Odds - NCAAF (Tuesday/Wednesday)

```bash
# 5 seconds - NCAAF odds only
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
```

### Complete Weekly Collection - NFL

```bash
# Tuesday 2:00 PM - comprehensive NFL data prep
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl
uv run python scripts/scrapers/scrape_massey_games.py
python src/data/weather_client.py --league nfl
uv run python scripts/scrapers/scrape_action_network_sitemap.py --nfl
```

### Complete Weekly Collection - NCAAF

```bash
# Wednesday 2:00 PM - comprehensive NCAAF data prep
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf
uv run python scripts/scrapers/scrape_massey_games.py --league college
python src/data/weather_client.py --league ncaaf
uv run python scripts/scrapers/scrape_action_network_sitemap.py --ncaaf
```

### Live Game Monitoring (NFL Sunday)

```bash
# Get pregame odds first
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# Then monitor for 3 hours during games
uv run python scripts/scrapers/scrape_overtime_hybrid.py --nfl --duration 10800
```

### Live Game Monitoring (NCAAF Saturday)

```bash
# Get pregame odds first
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Then monitor for 4 hours during games
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 14400
```

### CI/CD Pipeline

```bash
# Reliable, no browser needed, works on all platforms
# Collect NFL only
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# Then collect NCAAF only
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
```

---

## Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| "Connection timeout" | Check internet, try again in 30 seconds |
| "CloudFlare blocked" | Use hybrid scraper (handles CF) or wait for API |
| "No browser found" | Install Playwright: `uv add --dev playwright` |
| "Missing API key" | Check `.env` file has `ACCUWEATHER_API_KEY` |
| "ModuleNotFoundError" | Run `uv sync` to install dependencies |
| "Too slow" | Use `scrape_overtime_api.py` instead of hybrid |
| "Need real-time updates" | Use `overtime_hybrid_scraper.py` |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

---

## ESPN Client Note

### ⚠️ DEPRECATED: espn_api_client.py

**Don't use:** `from src.data.espn_api_client import ESPNAPIClient`

**Use instead:** `from src.data import AsyncESPNClient`

**Why:**
- AsyncESPNClient has retry logic and circuit breaker
- Handles rate limiting automatically
- Better error handling
- Async/await support for concurrency

Switching is simple - both have similar APIs!

---

## Where's the Detailed Stuff?

| Question | Document |
|----------|----------|
| "Tell me about the architecture" | [DATA_COLLECTION_ARCHITECTURE.md](docs/guides/DATA_COLLECTION_ARCHITECTURE.md) |
| "How do I use these clients?" | [DATA_COLLECTION_GUIDE.md](docs/guides/DATA_COLLECTION_GUIDE.md) |
| "What went wrong?" | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| "How are the scrapers organized?" | [AUDIT_SUMMARY.md](AUDIT_SUMMARY.md) |
| "What's the Billy Walters methodology?" | [BILLY_WALTERS_METHODOLOGY.md](docs/guides/BILLY_WALTERS_METHODOLOGY.md) |

---

## TL;DR - Just Tell Me What To Do

**IMPORTANT: Keep NFL and NCAAF Separate! See [LEAGUE_SEPARATION_GUIDE.md](docs/guides/LEAGUE_SEPARATION_GUIDE.md)**

### Tuesday (NFL Weekly Collection):
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl
python src/data/weather_client.py --league nfl
uv run python scripts/scrapers/scrape_action_network_sitemap.py --nfl
```

### Wednesday (NCAAF Weekly Collection):
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf
python src/data/weather_client.py --league ncaaf
uv run python scripts/scrapers/scrape_action_network_sitemap.py --ncaaf
```

### Sunday (NFL Game Day - 3 hour monitoring):
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
uv run python scripts/scrapers/scrape_overtime_hybrid.py --nfl --duration 10800
```

### Saturday (NCAAF Game Day - 4 hour monitoring):
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 14400
```

### After collection:
```bash
/edge-detector
```

### Everything else:
- ESPN data? Use `AsyncESPNClient` from `src.data`
- Weather? Use `WeatherClient` (just works)
- Action Network? Use `action_network_sitemap_scraper.py` with `--nfl` or `--ncaaf`

---

**Last Updated:** 2025-11-25
**Status:** UPDATED - Now enforces strict NFL/NCAAF separation

---

## Updates (2025-11-25)

**Major Changes:**
- Fixed all commands to enforce league separation (never use --nfl --ncaaf together)
- Added separate NFL and NCAAF workflows to TL;DR section
- Added weather collection to all workflows
- Added ESPN stats collection for both leagues in complete workflows
- Updated common workflows with explicit league parameters
- Added monitoring duration guidance (3 hrs NFL, 4 hrs NCAAF)
- Aligned all examples with LEAGUE_SEPARATION_GUIDE.md

**Why?** The quick reference was created before the league separation guide. These updates ensure all examples properly separate NFL and NCAAF data to prevent contamination.
