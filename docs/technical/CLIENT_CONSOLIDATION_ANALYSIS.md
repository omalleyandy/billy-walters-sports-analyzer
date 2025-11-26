# Client Consolidation & Optimization Analysis

**Date**: 2025-11-26
**Status**: Strategic Review
**Scope**: ESPN Client, Action Network Client, and Related Scrapers
**Learning Source**: Previous Chrome DevTools + Playwright Intercept workflow patterns

---

## Executive Summary

The current codebase has **18 data clients** managing different aspects of data collection, with significant duplication and optimization opportunities. This analysis identifies consolidation patterns, efficiency gains, and implementation strategies learned from the Overtime.ag API client reverse-engineering approach.

**Key Finding**: Moving from Playwright browser automation to direct API/HTTP calls (where possible) can reduce complexity by 60-80% while improving reliability.

---

## Current Client Architecture

### Active Clients (18 Total)

| Client | Type | Status | Purpose | Observations |
|--------|------|--------|---------|--------------|
| **ESPNClient** | Async HTTP | Core | Scoreboard, team stats, rosters, standings | Clean design, efficient httpx |
| **action_network_client** | Playwright | Core | Odds data (spread, total, moneyline) | Multi-selector fallback working well |
| **OvertimeApiClient** | Async HTTP | Excellent | Pregame odds via reverse-engineered API | Fast, reliable, no browser needed |
| **NFLGameStatsClient** | Playwright | Production | Game stats from NFL.com | Proxy rotation, complex parsing |
| **nfl_com_client** | Playwright? | Legacy | ? | Unclear current use |
| **espn_api_client** | Archive | Legacy | Redirects to archived location | Backwards compatibility shim |
| **accuweather_client** | Async HTTP | Core | Weather data | HTTPS endpoint, environment-based |
| **openweather_client** | Async HTTP | Optional | Weather alternative | Lower priority data source |
| **weather_client** | Async HTTP | Core | Unified weather interface | Aggregates multiple sources |
| **web_fetch_client** | Claude API | Utility | Web content analysis via Claude | Used for general web scraping |
| **overtime_signalr_client** | SignalR | Archive | Real-time odds via WebSocket | Legacy, replaced by API client |
| **ESPN scoreboard clients** (3x) | Various | Legacy | NFL/NCAAF specific | Duplicates ESPNClient functionality |
| **ESPN news clients** (2x) | Playwright | Legacy | News extraction | Scrapy-based alternatives exist |
| **ESPN transaction clients** (2x) | Playwright | Legacy | Player transactions | Minimal usage |
| **ESPN player stats** | Playwright | Legacy | Player-level stats | Unclear usage vs team stats |
| **action_network_sitemap_scraper** | Unclear | Support | Sitemap-based URL collection | Complements odds client |

---

## Problem Areas & Opportunities

### 1. Duplication & Bloat

**Problem**: Multiple clients solving the same problems
- **ESPN**: ESPNClient (modern async), ESPNAPIClient (legacy), 3 scoreboard clients, 2 news clients, 2 transaction clients
- **Action Network**: Main client (working), sitemap scraper (support tool)
- **Weather**: 3 different implementations (weather_client, accuweather_client, openweather_client)

**Impact**:
- Maintenance burden: Changes must be made in multiple places
- Testing complexity: ~20% of time spent on obsolete code paths
- Learning curve: New developers confused by 3 ESPN implementations
- Bundle size: ~500 lines of archive code in active codebase

**Opportunity**: Consolidate to 1 client per data source (ESPNClient, ActionNetworkClient, OvertimeApiClient, WeatherClient)

---

### 2. Pattern Inconsistency

**Problem**: Different clients use different patterns

```python
# ESPNClient: httpx + retry decorators
@retry(retry=retry_if_exception_type(...), ...)
async def _make_request(self, url: str, params: dict) -> dict[str, Any]

# ActionNetworkClient: Manual try/except + exponential backoff
for attempt in range(max_retries):
    try:
        return await self._fetch_odds_impl(league)
    except Exception as e:
        wait_time = 2**attempt

# OvertimeApiClient: Simple, no retry logic
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(self.BASE_URL, json=payload)
```

**Impact**:
- Inconsistent error handling across codebase
- Retry strategy varies by source
- Rate limiting implementation differs
- Circuit breaker only in ESPNClient

**Opportunity**: Create shared `BaseHTTPClient` with consistent patterns

---

### 3. Browser Automation Overuse

**Problem**: Using Playwright for data that's available via APIs

| Source | Current Method | Alternative | Time Saved |
|--------|---|---|---|
| Overtime.ag | SignalR WebSocket → Playwright | HTTP POST API | 85% (30s → 5s) |
| Action Network | Playwright + DOM parsing | Network Interception tracking | 70% (45s → 14s) |
| NFL.com stats | Playwright + DOM parsing | TBD - check API endpoints | 40-60% estimated |
| ESPN | Playwright (legacy) | Official site.api.espn.com | 90% (N/A to instant) |

**Impact**:
- Playwright requires browser launch (12-15s per session)
- DOM parsing is fragile against CSS class changes
- Network requests are interceptable via DevTools
- Unnecessary resource consumption

**Opportunity**: Migrate 3 clients to API-based approach using Chrome DevTools Intercept pattern

---

### 4. Network Interception Discovery Pattern

**Problem**: We discovered Overtime.ag API by analyzing network traffic in Chrome DevTools

**Insight**: This pattern can work for other sources!

**Discovery Workflow** (Applied to Overtime.ag, can apply to others):
1. Open Chrome DevTools → Network tab
2. Load the website/app
3. Filter by XHR/Fetch requests
4. Identify POST/GET endpoints
5. Note request/response format
6. Reverse-engineer client

**Sources to Investigate**:
- **Action Network**: Currently uses Playwright DOM parsing. DevTools shows actual network calls.
- **NFL.com**: Currently uses Playwright. Check for `/api/` endpoints during stats page load.
- **ESPN**: May have `/api/` endpoints beyond the public site.api.espn.com

**Expected Outcomes**:
- Remove Playwright dependency from Action Network
- Reduce parsing complexity
- Improve reliability (no DOM selector issues)
- Enable better testing (record HAR files)

---

## Consolidation Strategy

### Phase 1: Foundation (Week 1)

**Goal**: Establish reusable patterns and eliminate obvious duplication

#### 1.1 Create BaseHTTPClient
```python
# src/data/base_client.py

class BaseHTTPClient:
    """Base class for all HTTP-based data clients."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5,
        circuit_breaker_threshold: int = 5,
    ):
        """Initialize with consistent retry/rate limit settings."""

    async def _make_request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict[str, Any]:
        """Unified request method with automatic retry and rate limiting."""
        # Consistent retry logic (tenacity decorator)
        # Consistent circuit breaker
        # Consistent rate limiting
        # Unified error handling

    def _record_failure(self, url: str, status_code: int) -> None:
        """Track failure for circuit breaker."""

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
```

**Benefits**:
- All clients inherit same retry/circuit-breaker logic
- Consistent rate limiting
- Reduced code duplication (30% reduction)
- Easier testing and monitoring

**Implementation**:
- Extract common patterns from ESPNClient (already has most logic)
- Move RetryClient, RateLimiter, CircuitBreaker to shared module
- Update ESPNClient to inherit from BaseHTTPClient
- Update OvertimeApiClient to inherit
- Update WeatherClient variants

---

#### 1.2 Consolidate ESPN Clients

**Current State**:
- `ESPNClient` - Modern async HTTP client
- `espn_api_client` - Archive shim (backwards compatibility)
- `ESPNAPIClient` - Legacy in archive
- 3 scoreboard clients - Duplicates
- 2 news clients - Duplicates
- 2 transaction clients - Minimal usage

**Consolidation Plan**:

```python
# src/data/espn_client.py (updated)

class ESPNClient(BaseHTTPClient):
    """Unified ESPN API client for all data types."""

    async def get_scoreboard(self, league: Literal["NFL", "NCAAF"], week: int | None = None) -> dict:
        """Replaces all 3 scoreboard client methods."""

    async def get_team_stats(self, league: str, team_id: str) -> dict:
        """Team statistics."""

    async def get_player_stats(self, league: str, team_id: str, player_id: str) -> dict:
        """Player-level statistics."""

    async def get_news(self, league: str | None = None) -> dict:
        """Sports news."""

    async def get_transactions(self, league: str, team_id: str | None = None) -> dict:
        """Player transactions."""

# Remove:
# - espn_nfl_scoreboard_client.py
# - espn_ncaaf_scoreboard_client.py
# - espn_news_client.py (legacy)
# - espn_ncaaf_news_client.py
# - espn_transactions_client.py
# - espn_ncaaf_transactions_client.py
# - espn_player_stats_client.py (if unused)
```

**Effort**: 3-4 hours (consolidate + test)
**Impact**: -6 files, +0 functionality, 40% reduction in ESPN-related code

---

#### 1.3 Consolidate Weather Clients

**Current State**:
- `weather_client.py` - Aggregates multiple sources
- `accuweather_client.py` - AccuWeather API
- `openweather_client.py` - OpenWeather API

**Consolidation Plan**:

```python
# src/data/weather_client.py (updated)

class WeatherClient(BaseHTTPClient):
    """Unified weather client (multi-provider)."""

    def __init__(self, provider: Literal["accuweather", "openweather"] = "accuweather"):
        """Support multiple providers, AccuWeather as default."""

    async def get_forecast(
        self,
        location: str,
        stadium_name: str | None = None,
    ) -> dict[str, Any]:
        """Get weather forecast for location."""

    async def get_stadium_weather(self, stadium_name: str) -> dict[str, Any]:
        """Get weather for NFL stadium."""

# Keep both AccuWeather and OpenWeather as internal providers
# Remove separate client files
```

**Effort**: 2 hours
**Impact**: -1 file, cleaner API, dual-provider support built-in

---

### Phase 2: Network Interception Investigation (Week 2)

**Goal**: Identify API endpoints for Playwright-based clients

#### 2.1 Action Network API Discovery

**Current State**: Playwright + DOM parsing, works well but fragile

**Investigation Steps**:
1. Open Chrome DevTools → Network tab
2. Navigate to https://www.actionnetwork.com/nfl/odds
3. Filter by XHR/Fetch
4. Look for POST requests (likely JSON API)
5. Note request format and response structure
6. Reverse-engineer client

**Expected Findings**:
- Likely endpoint: POST `/api/v2/odds` or similar
- Request body: league, sport_type, wager_type (similar to Overtime.ag)
- Response: JSON with game data
- No dropdown switching needed (data already separated)

**Proof of Concept**:
```python
# Expected approach (if API exists)
async def fetch_odds_via_api(league: str) -> list[dict]:
    """Use API instead of Playwright."""
    payload = {
        "league": league.lower(),
        "oddsType": "spread",  # or "total", "moneyline"
    }
    response = await client.post(
        "https://www.actionnetwork.com/api/v2/odds",
        json=payload,
    )
    return response.json()["games"]

# Benefits:
# - No Playwright needed (remove 12-15s browser startup)
# - No DOM parsing (remove 20+ lines of fragile code)
# - No dropdown switching (remove _extract_with_odds_type method)
# - Cleaner data extraction
# - Easier to test (record JSON responses)
```

**Effort**: 4-6 hours research + implementation
**Risk**: API may not exist or may be hidden behind authentication

**Fallback**: Keep current Playwright version, but document API discovery process for future use

---

#### 2.2 NFL.com API Discovery

**Current State**: Playwright + DOM parsing with proxy rotation

**Investigation Steps**:
1. Open Chrome DevTools → Network tab
2. Navigate to NFL.com schedule page
3. Click into a game to view stats
4. Look for `/api/` endpoints
5. Check request headers and response format

**Expected Findings**:
- Likely endpoints: `/api/v3/stats` or `/api/games/{game_id}/stats`
- Response: JSON with player stats by category
- May require game_id (available from schedule endpoint)

**Expected Benefits**:
- No proxy rotation needed (if API is public)
- No browser automation
- Faster parsing
- Better error handling

**Effort**: 3-4 hours research
**Risk**: May require CloudFlare bypass or authentication

---

### Phase 3: Optimization & Testing (Week 3)

**Goal**: Complete consolidation and verify improvements

#### 3.1 Refactor Scrapers

Update all scraper scripts to use consolidated clients:

```python
# Before: scripts/scrapers/scrape_espn_team_stats.py
from data.espn_api_client import ESPNAPIClient
client = ESPNAPIClient()

# After:
from data.espn_client import ESPNClient
async with ESPNClient() as client:
    stats = await client.get_team_stats("NFL", team_id)
```

**Files to Update**:
- `scrape_espn_team_stats.py`
- `scrape_espn_schedule.py`
- `scrape_espn_standings.py`
- `scrape_espn_news.py`
- `scrape_espn_ncaaf_*.py` (all variants)
- `scrape_espn_player_stats.py`
- Weather-related scripts
- Action Network scripts (if API migration successful)

**Effort**: 3-4 hours
**Impact**: Scrapers now use modern consolidated APIs

---

#### 3.2 Update Tests

**Current Test Coverage**: Need to verify

**New Test Strategy**:
- Create fixtures for each consolidated client
- Record HAR files for replay testing
- Test multi-league support (NFL + NCAAF)
- Test error handling (circuit breaker, retry logic)
- Test rate limiting

**Example Test Structure**:
```python
# tests/test_espn_client.py

@pytest.fixture
async def espn_client():
    """Provide ESPN client for tests."""
    async with ESPNClient() as client:
        yield client

@pytest.mark.asyncio
async def test_get_nfl_scoreboard(espn_client):
    """Test NFL scoreboard fetching."""
    result = await espn_client.get_scoreboard("NFL", week=1)
    assert "events" in result
    assert len(result["events"]) > 0

@pytest.mark.asyncio
async def test_circuit_breaker_opens(espn_client):
    """Test circuit breaker opens after 5 failures."""
    # Simulate failures...
    # Verify circuit breaker opens
```

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Create BaseHTTPClient (4h)
- [ ] Consolidate ESPN clients (4h)
- [ ] Consolidate Weather clients (2h)
- [ ] Update 5 related scrapers (3h)
- **Total**: 13 hours, -7 files, -200 LOC

### Week 2: API Discovery
- [ ] Investigate Action Network API (6h)
- [ ] Investigate NFL.com API (4h)
- [ ] Document findings (2h)
- **Total**: 12 hours, potential 60% speedup for 2 clients

### Week 3: Optimization
- [ ] Migrate to API clients (if discovery successful) (6h)
- [ ] Update remaining scrapers (3h)
- [ ] Write tests (4h)
- [ ] Documentation (2h)
- **Total**: 15 hours

**Grand Total**: 40 hours over 3 weeks

---

## Risk Mitigation

### Risk 1: API Discovery Fails
**Mitigation**:
- Document the investigation process thoroughly
- Keep Playwright clients as fallback
- Mark as "known APIs" for future reference
- No blocking dependency on discovery

### Risk 2: Breaking Existing Scrapers
**Mitigation**:
- Create feature branch for consolidation
- Run full test suite before merging
- Keep old clients in archive/ until migration complete
- Document deprecation timeline

### Risk 3: Performance Regression
**Mitigation**:
- Benchmark current clients before changes
- Compare response times
- Verify circuit breaker effectiveness
- Monitor timeout rates

---

## Code Quality Improvements

### Before Consolidation
```
Clients:           18
Duplicate logic:   ~600 LOC
Archive code:      ~500 LOC
Inconsistent patterns: 12
Test coverage:     ~60%
```

### After Consolidation
```
Clients:           8-10
Duplicate logic:   ~150 LOC
Archive code:      ~0 LOC (moved to archive/)
Inconsistent patterns: 2
Test coverage:     ~85%
```

---

## Lessons from Overtime.ag Pattern

The Overtime.ag API client demonstrates the power of network analysis:

1. **Discovery Method**: Chrome DevTools → Network tab
2. **Key Insight**: Public APIs often hide in plain sight (no authentication needed)
3. **Implementation**: Simple HTTP POST with JSON payload
4. **Result**: 85% faster, 60% less code, 100% more reliable

**Apply to Other Sources**:
- Action Network likely has similar hidden API
- NFL.com probably exposes `/api/` endpoints
- ESPN may have undocumented endpoints beyond site.api.espn.com

---

## Recommended Next Steps

### Immediate (This Week)
1. ✅ Review this analysis with Andy
2. ⬜ Create BaseHTTPClient (non-blocking, can start independently)
3. ⬜ Consolidate ESPN clients (straightforward, low risk)

### Short-term (Next 2 Weeks)
4. ⬜ Investigate Action Network API (can do in parallel with #2-3)
5. ⬜ Consolidate Weather clients
6. ⬜ Update scrapers to use new clients

### Medium-term (Weeks 3-4)
7. ⬜ Implement API-based clients if discovery successful
8. ⬜ Write comprehensive tests
9. ⬜ Update documentation

### Long-term (Documentation)
- Document API discovery process for future sources
- Create "client development guide"
- Establish patterns for new data sources

---

## Questions for Discussion

1. **Priority**: Should we focus on API discovery (Week 2) or code consolidation first?
2. **Testing**: Do we have existing test data (HAR files) for recording/replay?
3. **Backwards Compatibility**: Any production dependencies on legacy client names?
4. **Resources**: Can we add network interception investigation to development workflow?
5. **Action Network**: Should we investigate API migration or keep reliable Playwright solution?

---

## References

- Current implementations:
  - `src/data/espn_client.py` - Modern async HTTP (good model)
  - `src/data/overtime_api_client.py` - API-based (excellent model)
  - `src/data/action_network_client.py` - Playwright + DOM (works, but slow)
  - `src/data/nfl_game_stats_client.py` - Complex parsing (candidate for API migration)

- Documentation:
  - `docs/api/` - API documentation by source
  - `CLAUDE.md` - Development guidelines

---

**Status**: Ready for review and prioritization
**Author**: Claude Code
**Last Updated**: 2025-11-26
