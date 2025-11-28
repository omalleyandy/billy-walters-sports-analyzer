# X News Scraper - Daily Workflow Integration

**Status**: Ready for integration into `/collect-all-data` workflow
**Context**: X API Bearer Token authentication is working and tested

---

## Quick Start (Next Steps)

### Option 1: Test Before Adding to Workflow
Verify scraper works with your credentials:

```bash
# Check quota (no API call)
uv run python -c "
import asyncio
from walters_analyzer.data_integration.real_data_integrator import RealDataIntegrator

async def check():
    integrator = RealDataIntegrator()
    await integrator.initialize()
    status = integrator.x_news_scraper.get_quota_status()
    print(f'[OK] Quota: {status[\"remaining\"]}/{status[\"daily_limit\"]} available')
    await integrator.close()

asyncio.run(check())
"
```

### Option 2: Run CLI Scraper
```bash
# Note: First run will wait for rate limit (normal)
uv run python scripts/scrapers/scrape_x_news.py --league nfl --type injury --days 7
```

### Option 3: Add to `/collect-all-data` Workflow (Full Integration)

**Location**: `scripts/analysis/collect_all_data.py`

**Add this code** after ESPN data collection and before edge detection:

```python
# ============================================
# STEP 5: Collect X News and Injury Posts
# ============================================
logger.info("[5] Collecting X news and injuries...")

try:
    x_posts_nfl = await integrator.fetch_x_news(
        league="nfl",
        source_type="injury",
        days=7,
        min_relevance=0.7
    )
    logger.info(f"[OK] Collected {len(x_posts_nfl)} NFL injury posts")

    x_posts_ncaaf = await integrator.fetch_x_news(
        league="ncaaf",
        source_type="injury",
        days=7,
        min_relevance=0.7
    )
    logger.info(f"[OK] Collected {len(x_posts_ncaaf)} NCAAF injury posts")

    # Check quota status
    quota = integrator.x_news_scraper.get_quota_status()
    logger.info(
        f"[OK] X API quota: {quota['calls_today']}/{quota['daily_limit']} "
        f"({quota['remaining']} remaining)"
    )

except Exception as e:
    logger.warning(f"[WARNING] X News collection failed (non-fatal): {e}")
    logger.info("[INFO] Continuing with ESPN data only")
```

---

## Integration Architecture

### Data Flow in Daily Workflow

```
/collect-all-data
├─ [1] Massey Power Ratings
├─ [2] ESPN Team Statistics
├─ [3] Action Network Sharp Money
├─ [4] Weather Data
├─ [5] X News & Injuries  ← NEW (optional, gracefully fails)
├─ [6] Validate Data Quality
├─ [7] Edge Detection
└─ [8] Generate Betting Card
```

### Key Design Decisions

**Why X News is Step 5?**
- ✅ After core data (ESPN, Massey, weather)
- ✅ Before edge detection (so posts influence edges)
- ✅ Gracefully fails if API unavailable

**Graceful Failure**:
- If rate limit hit: System continues with cached data
- If quota exhausted: Returns empty list, no crash
- If auth fails: Returns empty list, no crash
- Edge detection proceeds without X data (but with ESPN data)

**Error Handling**:
```python
try:
    x_posts = await integrator.fetch_x_news(...)
except Exception as e:
    logger.warning(f"[WARNING] X News failed (non-fatal): {e}")
    # Continue with ESPN data
```

---

## Expected Behavior

### First Run (Tuesday, any time)
```
[OK] Fetching NFL injury posts from official sources (days: 7)
[WARNING] Rate limit exceeded. Sleeping for 820 seconds.
(Wait ~14 minutes)
[OK] Found 4 relevant NFL injury posts
[OK] Cached 4 posts for nfl_injury_7d (24-hour TTL)
[OK] API calls: 1/5

[OK] Fetching NCAAF injury posts from official sources (days: 7)
[WARNING] Rate limit exceeded. Sleeping for 820 seconds.
(Wait ~14 minutes)
[OK] Found 3 relevant NCAAF injury posts
[OK] Cached 3 posts for ncaaf_injury_7d (24-hour TTL)
[OK] API calls: 2/5

[OK] X API quota: 2/5 (3 remaining)
```

### Subsequent Runs (Same Day)
```
[OK] Using cached NFL injury posts (23h old)
[OK] Using cached NCAAF injury posts (23h old)
[OK] X API quota: 2/5 (3 remaining) - No new API calls
```

### Next Day
```
[Cache expired, fetching fresh data]
[OK] Found 5 relevant NFL injury posts
[OK] API calls: 1/5 (quota reset)
```

---

## Quota Management

### Daily Budget: 5 Calls
```
Example Tuesday-Friday Schedule:

TUESDAY:
  ├─ 1 call: NFL injuries
  └─ 1 call: NCAAF injuries
  Total: 2/5 used, 3 remaining

WEDNESDAY-FRIDAY:
  ├─ All calls use cache (24-hour TTL)
  ├─ No API costs
  └─ 3 calls reserved for breaking news

SATURDAY-SUNDAY:
  └─ Quota often available but typically closed market

MONDAY (Next Week):
  └─ Quota resets, repeat cycle
```

### Monthly Budget: ~60-80 Posts
```
20-25 API calls/month × 3-4 posts per call = 60-80 posts
Actual limit: 100 posts/month
Safety margin: 20-40 posts buffer
```

### Quota Status Command
Check anytime:
```python
quota = integrator.x_news_scraper.get_quota_status()
print(f"Calls today: {quota['calls_today']}/{quota['daily_limit']}")
print(f"Remaining: {quota['remaining']}")
print(f"Exhausted: {quota['exhausted']}")
print(f"Cached items: {quota['cached_items']}")
```

---

## E-Factor Integration

### How X News Affects Edges

**When injury post is found**:
1. Post fetched from @NFL, @AdamSchefter, etc.
2. Relevance scored (0.0-1.0 based on keywords)
3. High-relevance (0.7+) posts included in E-Factor
4. NewsDecayFunction applies time decay
5. Edge recalculated: e.g., DAL +3.5 → DAL +1.2

**Example Output**:
```
Game: KC @ DAL
Power Rating: KC +5.5

X News Impact:
  - @AdamSchefter: "Patrick Mahomes questionable with ankle injury"
  - Relevance: 0.95 (injury keywords: "injury", "ankle", "questionable")
  - E-Factor Adjustment: -4.0 pts (elite QB injury = high impact)

Final Edge: KC +5.5 - 4.0 = KC +1.5
```

---

## Troubleshooting

### Rate Limit Wait
**Symptom**: "Rate limit exceeded. Sleeping for 820 seconds"
**Why**: Free tier has 1 request per 15 minutes per endpoint
**Solution**: Normal behavior - system waits automatically
**When**: First API call of the session (then uses cache)

### Empty Results
**Symptom**: "[OK] Found 0 relevant posts"
**Reasons**:
1. No recent posts from official sources (normal)
2. Posts exist but don't match keywords (rare)
3. Cache available instead (check for cache message)
**Action**: Try again next day or check X directly (@NFL, @AdamSchefter)

### "Quota exhausted"
**Symptom**: "[WARNING] Daily quota exhausted"
**Why**: Made 5 API calls already today
**Solution**:
1. Use cached data (returned automatically)
2. Wait until tomorrow
3. 3 quota slots available for emergencies during the day
**Prevention**: Space calls throughout week (1-2 per day)

### "X API credentials not found"
**Symptom**: "[WARNING] X API credentials not found"
**Why**: X_BEARER_TOKEN not in .env file
**Solution**:
1. Check .env file exists in project root
2. Verify line: `X_BEARER_TOKEN=your_token_here`
3. No quotes needed around token
4. Save file and try again

---

## Implementation Checklist

### Pre-Integration Verification ✅ (Complete)
- [x] Bearer Token authentication working
- [x] Integration with RealDataIntegrator confirmed
- [x] Free tier endpoints accessible
- [x] Rate limiting handled correctly
- [x] Caching working (24-hour TTL)

### Integration Steps (Next)
- [ ] Add X scraper call to `/collect-all-data`
- [ ] Test with `python /collect-all-data` command
- [ ] Verify X posts appear in edge detection output
- [ ] Check E-Factor adjustments using X data

### Post-Integration Validation (After Integration)
- [ ] Full workflow runs without errors
- [ ] Edges change based on X posts
- [ ] Quota tracking shows accurate call counts
- [ ] Cache working (second run uses cache)
- [ ] Graceful failure if quota exhausted

---

## Quick Reference

### Commands
```bash
# Check if X scraper is working (no API call)
uv run python -c "
import asyncio
from walters_analyzer.data_integration.real_data_integrator import RealDataIntegrator
async def test():
    i = RealDataIntegrator()
    await i.initialize()
    s = i.x_news_scraper.get_quota_status()
    print(f'Quota: {s[\"remaining\"]}/{s[\"daily_limit\"]}')
    await i.close()
asyncio.run(test())
"

# Run scraper CLI
uv run python scripts/scrapers/scrape_x_news.py --league nfl --type injury --days 7

# Add to /collect-all-data
# See "Option 3: Add to /collect-all-data" section above
```

### Files to Reference
- `src/walters_analyzer/data_integration/x_news_scraper.py` - Scraper implementation
- `src/walters_analyzer/data_integration/real_data_integrator.py` - Integration layer
- `scripts/analysis/collect_all_data.py` - Where to add the workflow step
- `docs/guides/X_API_ACTIVATION_SUMMARY.md` - Full activation details

---

## Next Session Goals

1. **Add X scraper to `/collect-all-data`** - Integrate into daily workflow
2. **Test full workflow** - Run `/collect-all-data` and verify X posts collected
3. **Verify E-Factor impact** - Run `/edge-detector` and check edge adjustments
4. **Document results** - Add X news to weekly reports

---

**Status**: Ready for integration into daily workflow
**Time to implement**: 5-10 minutes
**Complexity**: Low (mostly copy-paste integration)
**Risk**: Very low (graceful failure if anything goes wrong)
