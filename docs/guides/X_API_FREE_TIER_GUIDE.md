# X API Free Tier Operational Guide

**Status**: Operational within free tier constraints
**Date**: 2025-11-28
**Purpose**: Guidelines for running X News Scraper within free tier rate limits

---

## Quick Summary

The X API free tier is **severely rate-limited** but usable for low-frequency monitoring:

- **Recent Search (tweets/search/recent)**: 1 request per 15 minutes
- **User Lookup**: 1-3 requests per 24 hours depending on endpoint
- **Post Cap**: 100 posts retrieved per month
- **Monthly Limit**: Roughly 3-5 API calls per day maximum

**Strategy**: Cache aggressively, fetch once daily, avoid real-time monitoring

---

## Free Tier Rate Limits (Official)

### Search & Tweet Endpoints

| Endpoint | Limit | Reset Period | Use Case |
|----------|-------|--------------|----------|
| `GET /2/tweets/search/recent` | 1 request | 15 minutes | Search for tweets by keywords |
| `GET /2/users/by/username/:username` | 3 requests | 15 minutes | Look up account info |
| `GET /2/users/:id` | 1 request | 24 hours | Get user by ID |
| `GET /2/tweets/:id` | 1 request | 15 minutes | Get specific tweet |
| `GET /2/users/:id/tweets` | 1 request | 15 minutes | Get user's recent tweets |

### Key Constraints

**Total Posts Retrieved**: 100 per month (not per call, but monthly aggregate)
- ~3-4 posts per day average
- Sharply limits data collection volume

**Authentication**: Free tier limits apply per app, not per user
- Only 1 app per project allowed
- Rate limits are app-wide, not per API key

---

## Optimized Architecture for Free Tier

### Strategy 1: Daily Batch Collection

**Goal**: Maximize data within rate limits

```
Monday-Friday (business days):
  └─ 09:00 AM (EST) - Single daily search
     └─ Search for key injury sources (1 request)
     └─ Cache results for 24 hours
     └─ ~3-4 posts retrieved
     └─ Cost: 1 API call/day

Saturday-Sunday (market closed):
  └─ Skip - save API quota for next week
```

**Monthly Quota**:
- 5 business days × 4 weeks = 20 working days
- 20 requests × ~3-4 posts each = 60-80 posts/month
- **Well within 100 post limit**

### Strategy 2: Keyword-Focused Search

**Limit searches to highest-signal keywords only**:

```python
# Free tier search strategy
CRITICAL_KEYWORDS = [
    # Injuries (highest priority)
    "out",
    "ACL",
    "surgery",

    # Trades (game-changing)
    "trade",
    "traded",

    # Coaching (season-altering)
    "fired",
    "hired",
]

# Do NOT search for:
# - Weather updates
# - General game news
# - Low-impact roster moves
# - Player rumors
```

**Why**: Each search = 1 request. Narrow focus → fewer searches needed

---

## Modified X News Scraper for Free Tier

### Changes Required

The current scraper fetches from multiple sources daily. For free tier, we need to:

1. **Reduce frequency**: Daily instead of continuous
2. **Limit searches**: Only critical keywords
3. **Cache aggressively**: 24-hour cache minimum
4. **Batch requests**: Combine multiple leagues in one search

### Updated fetch_x_news() Configuration

```python
async def fetch_x_news_freetier(
    league: str = "nfl",
    source_type: str = "injury",  # Only fetch injuries first
):
    """
    Fetch X news optimized for free tier (1 request per 15 min).

    Strategy:
    - One search per day for critical keywords
    - Cache for 24 hours minimum
    - Skip non-breaking news
    """

    # Check cache first (24-hour TTL)
    cache_key = f"{league}_{source_type}_cache"
    if self._is_cache_fresh(cache_key, hours=24):
        logger.info(f"[OK] Using cached {league} {source_type} data")
        return self.cache[cache_key]

    # Only proceed if we haven't hit rate limit
    if self._api_quota_exhausted():
        logger.warning("[WARNING] API quota exhausted for today")
        return []

    # Make single search request
    try:
        posts = await self.x_news_scraper.get_league_news(
            league,
            source_type=source_type,
            days=1,  # Only last 24 hours
            max_results=10,  # Limit results
        )

        # Cache for next 24 hours
        self.cache[cache_key] = posts
        self._record_api_call(league, source_type)

        return posts

    except tweepy.TweepyException as e:
        if "429" in str(e):
            logger.error("[ERROR] Rate limit hit - wait 15 minutes")
        raise
```

### Quota Tracking

Add simple quota tracking to the scraper:

```python
class XNewsScraper:
    def __init__(self):
        # ... existing code ...
        self.api_calls_today = []
        self.daily_limit = 5  # Conservative for free tier

    def _record_api_call(self, league: str, source_type: str):
        """Track API calls made today."""
        now = datetime.now()
        self.api_calls_today.append({
            "timestamp": now,
            "league": league,
            "type": source_type,
        })

        # Log remaining quota
        remaining = self.daily_limit - len(self.api_calls_today)
        logger.info(f"[OK] API calls: {len(self.api_calls_today)}/{self.daily_limit}")
        logger.info(f"[OK] Remaining today: {remaining}")

    def _api_quota_exhausted(self) -> bool:
        """Check if daily quota exceeded."""
        # Clean old calls (older than 24h)
        cutoff = datetime.now() - timedelta(hours=24)
        self.api_calls_today = [
            c for c in self.api_calls_today
            if c["timestamp"] > cutoff
        ]

        return len(self.api_calls_today) >= self.daily_limit
```

---

## Recommended Usage Schedule

### Weekly NFL (Week 13)

```
TUESDAY 09:00 AM (EST)
  └─ Fetch NFL injuries
     Search: "@NFL OR @AdamSchefter" + injury keywords
     Cost: 1 request, ~3-4 posts
     Frequency: Once per week

FRIDAY 09:00 AM (EST) (Optional - if breaking news expected)
  └─ Fetch NFL news
     Search: "@NFL" + trade/coaching keywords
     Cost: 1 request, ~3-4 posts
     Frequency: Only on high-impact weeks
```

### Weekly NCAAF (Week 14)

```
WEDNESDAY 09:00 AM (EST)
  └─ Fetch NCAAF injuries
     Search: "@ESPNCollegeFB OR @Brett_McMurphy" + keywords
     Cost: 1 request, ~3-4 posts
     Frequency: Once per week
```

**Total**: 2-4 API calls per week (well within free tier)

---

## Caching Strategy (Critical for Free Tier)

### Cache Configuration

```python
CACHE_CONFIG = {
    "league_injuries": {
        "ttl_hours": 24,
        "refresh_on_major_event": True,
    },
    "league_news": {
        "ttl_hours": 24,
        "refresh_on_major_event": True,
    },
    "user_lookup": {
        "ttl_hours": 168,  # Weekly (7 days)
        "refresh_never": True,  # Never auto-refresh
    },
}
```

### Cache Expiration

```python
def _is_cache_fresh(
    self,
    cache_key: str,
    hours: int = 24
) -> bool:
    """Check if cached data is still valid."""
    if cache_key not in self.cache:
        return False

    cached_data = self.cache[cache_key]
    age_hours = (datetime.now() - cached_data["timestamp"]).total_seconds() / 3600

    return age_hours < hours
```

**Cache savings**: ~95% reduction in API calls after initial 1-week ramp-up

---

## Monthly API Budget

### Example: NFL Only (Conservative)

| Day | Action | Requests | Total |
|-----|--------|----------|-------|
| Mon-Fri (Week 1) | Fetch injuries | 5 × 1 | 5 |
| Mon-Fri (Week 2) | Fetch injuries | 5 × 1 | 5 |
| Mon-Fri (Week 3) | Fetch injuries | 5 × 1 | 5 |
| Mon-Fri (Week 4) | Fetch injuries | 5 × 1 | 5 |
| **Monthly Total** | - | - | **20 requests** |
| **Posts Retrieved** | ~3-4 per request | - | **60-80 posts** |
| **Monthly Limit** | - | - | **100 posts** |
| **Utilization** | - | - | **60-80%** ✓ |

**Safe with significant buffer remaining for unplanned fetches**

---

## Error Handling for Rate Limits

### 429 (Too Many Requests)

```python
async def fetch_x_news_with_retry(self, league: str):
    """Fetch with automatic rate limit handling."""
    try:
        return await self.fetch_x_news_freetier(league)

    except tweepy.TooManyRequests as e:
        logger.error(
            "[ERROR] Rate limit hit (429). "
            f"Wait 15 minutes before next request."
        )
        # Log the timestamp for manual retry
        self.rate_limit_timestamp = datetime.now()
        return []

    except tweepy.Unauthorized as e:
        logger.error(f"[ERROR] API credentials invalid: {e}")
        return []
```

### Graceful Degradation

If rate limited:
1. Use cached data (24+ hours old is acceptable)
2. Skip X news integration for this run
3. Continue with ESPN/NFL.com data
4. Log warning, don't crash

---

## Integration with RealDataIntegrator

### Modified fetch_x_news() for Free Tier

```python
async def fetch_x_news(
    self,
    league: str = "nfl",
    source_type: str = "injury",
    days: int = 1,  # Only 1 day for free tier
    min_relevance: float = 0.8,  # Higher threshold
) -> List[Dict[str, Any]]:
    """Fetch X news within free tier constraints."""

    if not self.x_news_scraper:
        return []

    # Check if quota exhausted
    if self.x_news_scraper._api_quota_exhausted():
        logger.warning("[WARNING] X API quota exhausted for today")
        logger.warning("[INFO] Using cached X data if available")
        return self._get_cached_x_news(league, source_type)

    # Fetch fresh data (costs 1 API call)
    try:
        posts = await self.x_news_scraper.get_league_news(
            league,
            source_type=source_type,
            days=days,
            max_results=10,  # Strict limit
        )

        # Filter for high relevance (0.8+)
        filtered = [p for p in posts if p.relevance_score >= min_relevance]
        logger.info(
            f"[OK] Fetched {len(filtered)}/{len(posts)} "
            f"high-relevance X posts for {league}"
        )

        return [p.to_dict() for p in filtered]

    except Exception as e:
        logger.warning(f"[WARNING] X fetch failed: {e}")
        return self._get_cached_x_news(league, source_type)
```

---

## Upgrade Path (If Needed)

### When to Upgrade

If you find that free tier is insufficient, consider:

| Tier | Cost | Limits | When to Use |
|------|------|--------|------------|
| **Free** | $0 | 1 req/15min, 100 posts/mo | Occasional checking |
| **Basic** | $100/mo | 500,000 posts/month | Daily monitoring |
| **Pro** | $5,000/mo | 50M posts/month | Real-time monitoring |

### Upgrade Strategy

1. Start with free tier (current setup)
2. Monitor actual API usage for 1-2 months
3. If approaching limits, upgrade to Basic
4. Basic tier allows hourly checks instead of daily

---

## Implementation Checklist

- [ ] Add quota tracking to XNewsScraper
- [ ] Implement 24-hour cache with TTL
- [ ] Modify fetch_x_news() to check quota before API call
- [ ] Add rate limit error handling (429 responses)
- [ ] Set daily limit to 5 API calls maximum
- [ ] Log all API calls for monitoring
- [ ] Gracefully degrade if rate limited
- [ ] Document actual usage monthly
- [ ] Alert if approaching 100 post/month limit
- [ ] Test with real API credentials

---

## Current Status

**X News Scraper** is implemented and integrated with RealDataIntegrator.

**Modifications needed** for free tier:
1. Add quota tracking ✗ (pending)
2. Implement cache TTL ✗ (pending)
3. Update API call limits ✗ (pending)
4. Add rate limit error handling ✗ (pending)

---

## References

- [X API Rate Limits Documentation](https://docs.x.com/x-api/fundamentals/rate-limits)
- [X API Getting Started](https://docs.x.com/x-api/getting-started/about-x-api)
- [Understanding Free Tier Rate Limits](https://devcommunity.x.com/t/specifics-about-the-new-free-tier-rate-limits/229761)

---

**Status**: Ready for free tier operation with modifications
**Next**: Implement quota tracking and caching in XNewsScraper
