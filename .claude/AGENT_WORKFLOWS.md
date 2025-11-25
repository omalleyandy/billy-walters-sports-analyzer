# Claude Agent Automated Workflows

This guide provides **directive-focused** instructions for autonomous agents working with the Billy Walters Sports Analyzer. Use this for automated decision-making and workflow orchestration.

---

## Decision Tree: Which Workflow to Use?

### Weekly Data Collection
**When:** Tuesday/Wednesday after Monday Night Football
**Trigger:** `/collect-all-data` slash command
**Process:**
1. Pre-flight validation: `.claude/hooks/pre_data_collection.py`
2. Six-step automated collection (power ratings → schedules → stats → injuries → weather → odds)
3. Post-flight validation: `.claude/hooks/post_data_collection.py`
4. Auto-trigger edge detection: `.claude/hooks/auto_edge_detector.py`

### Edge Detection
**When:** After fresh odds data collected (<5 minutes old)
**Decision Logic:**
```
IF odds_timestamp < 5 minutes ago:
    IF edge_detection_not_run_today:
        → Auto-trigger via auto_edge_detector.py
    ELSE:
        → Skip (already processed)
ELSE:
    → Run /scrape-overtime first to get fresh odds
```

### Individual Game Analysis
**When:** Deep dive on specific matchup needed
**Workflow:**
1. `/weather "Team Name" "YYYY-MM-DD HH:MM"` → Get weather impact
2. `/injury-report "Team Name" "NFL|NCAAF"` → Check injury status
3. `/team-stats "Team Name" "NFL|NCAAF"` → Review performance metrics
4. `/analyze-matchup` → Comprehensive analysis

### Live Game Monitoring (Optional)
**When:** Sunday during games (for line movement tracking)
**Method:** Overtime.ag hybrid scraper (browser + WebSocket)
**Command:** `uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 10800 --headless`
**Note:** Only use for live monitoring; use API client for pre-game odds

---

## Pre-Flight Validation Checklist

Before any data collection, verify:

- [ ] **Environment variables set**
  - `ACCUWEATHER_API_KEY` or `OPENWEATHER_API_KEY` (at least one)
  - `OV_CUSTOMER_ID` and `OV_PASSWORD` (for Overtime.ag)
  - `ACTION_USERNAME` and `ACTION_PASSWORD` (optional but recommended)

- [ ] **Output directories exist**
  - `data/current/` (power ratings, schedules, stats)
  - `output/overtime/nfl/pregame/` (NFL odds)
  - `output/overtime/ncaaf/pregame/` (NCAAF odds)
  - `output/edge_detection/` (edge reports)

- [ ] **Current NFL week detected**
  - Auto-detected via `get_nfl_week()` in `season_calendar.py`
  - Verify with `/current-week` slash command
  - Updates automatically each Thursday

- [ ] **API rate limits checked**
  - AccuWeather: 50 calls/day (Starter plan)
  - OpenWeather: 1000 calls/day (Free tier)
  - The Odds API: 500 calls/month (Free tier)

**Automation:** Run `python .claude/hooks/pre_data_collection.py`
- Exit code 0 = proceed
- Exit code 1 = stop (missing requirements)

---

## Post-Flight Validation Checklist

After data collection, verify:

- [ ] **Required files present** (minimum 5)
  - `data/current/nfl_power_ratings_week_{week}.json`
  - `output/overtime/nfl/pregame/api_walters_{timestamp}.json`
  - `data/current/nfl_schedules_week_{week}.json`
  - `data/current/nfl_injuries_week_{week}.json`
  - Weather data (optional but recommended)

- [ ] **Data quality score**
  - EXCELLENT: 5/5 files, odds <5 min old
  - GOOD: 4/5 files, odds <30 min old
  - FAIR: 3/5 files, odds <60 min old
  - POOR: <3 files or odds >60 min old

- [ ] **Odds data freshness**
  - Optimal: <5 minutes (auto-triggers edge detection)
  - Acceptable: <30 minutes (manual trigger)
  - Stale: >60 minutes (re-scrape recommended)

- [ ] **No missing API keys**
  - Check for "API key not found" warnings
  - Verify weather data has real values (not N/A)

**Automation:** Run `python .claude/hooks/post_data_collection.py [week]`
- Exit code 0 = success (data quality GOOD or EXCELLENT)
- Exit code 1 = failure (data quality POOR or missing files)

---

## Error Recovery Procedures

### AccuWeather API Failing

**Symptoms:**
- HTTP 301 redirect errors
- HTTP 403 Forbidden errors
- Weather data showing N/A values

**Diagnosis:**
```python
# Check 1: Verify HTTPS (not HTTP)
# File: src/data/accuweather_client.py:28
# Should be: BASE_URL = "https://dataservice.accuweather.com"

# Check 2: Test API connectivity
cd src && uv run python -c "
from data.accuweather_client import AccuWeatherClient
import asyncio, os

async def test():
    client = AccuWeatherClient(api_key=os.getenv('ACCUWEATHER_API_KEY'))
    await client.connect()
    key = await client.get_location_key('Green Bay', 'WI')
    print(f'AccuWeather working, location key: {key}')
    await client.close()

asyncio.run(test())
"
```

**Resolution:**
1. Verify HTTPS endpoint (not HTTP)
2. Check API key validity
3. Verify plan limits (Starter = 12-hour forecast max)
4. For games >12 hours away, uses current conditions (less accurate)
5. Fallback to OpenWeather if AccuWeather unavailable

### Overtime.ag Scraper Failing

**Symptoms:**
- 0 games found
- Authentication errors
- Timeout errors

**Diagnosis:**
```bash
# Check 1: Verify which scraper being used
# Primary (recommended): API client - fast, no auth
# Secondary (optional): Hybrid scraper - slow, requires auth

# Check 2: Verify timing
/current-week  # Check if games already started

# Check 3: Test API endpoint
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

**Resolution:**
1. **Primary method**: Use API client (10x faster, no auth required)
   - `uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf`
2. **Timing**: Run Tuesday-Wednesday for optimal results (fresh lines)
3. **Avoid**: Sunday during games (lines are down)
4. **Fallback**: Hybrid scraper only for live monitoring (requires credentials)

### Edge Detection Showing No Edges

**Symptoms:**
- Zero edges detected
- "No betting opportunities found"

**Diagnosis:**
```bash
# Check 1: Verify power ratings loaded
ls -la data/current/*power_ratings*.json

# Check 2: Check odds data format
cat output/overtime/nfl/pregame/api_walters_*.json | head -20

# Check 3: Confirm weather/injury data (optional)
ls -la data/current/*injuries*.json
```

**Resolution:**
1. Verify power ratings exist and are current week
2. Check odds data is Billy Walters format (standardized JSON)
3. Confirm weather/injury data loaded (improves accuracy)
4. Lower edge threshold temporarily for debugging
5. Check if market is efficient (small edges expected)

### Weather Data Async/Await Error (FIXED)

**Symptoms:**
- RuntimeWarning: coroutine never awaited
- Weather showing None for all games

**Resolution:**
✅ **Already fixed** in `billy_walters_edge_detector.py:1122-1127`
- Added `import asyncio`
- Wrapped weather API call with async helper
- Properly awaits AccuWeather client

**Verification:**
```bash
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector 2>&1 | Select-String "Weather for"
# Expected: Real temperature and wind data for outdoor stadiums
# Expected: None for indoor stadiums
```

---

## Integration with Existing Systems

### Claude Code System (.claude/)

**Hooks (Python - Automated validation):**
- `pre_data_collection.py` - Environment/directory validation before collection
- `post_data_collection.py` - Data quality scoring after collection
- `auto_edge_detector.py` - Monitors for fresh odds, auto-triggers detection

**Commands (Markdown - Interactive slash commands):**
- `/collect-all-data` - Complete 6-step data collection workflow
- `/edge-detector` - Billy Walters edge detection
- `/betting-card` - Generate weekly picks ranked by edge
- `/clv-tracker` - Track Closing Line Value performance
- `/weather`, `/injury-report`, `/team-stats` - Contextual analysis

**Usage Pattern:**
```bash
# Hooks run automatically (pre/post validation)
# Commands invoked manually by user or agent
/collect-all-data  # Triggers pre_data_collection.py → collection → post_data_collection.py
```

### Codex System (.codex/)

**PowerShell Automation:**
- `super-run.ps1` - Master orchestration script
- `commands/*.ps1` - 15+ PowerShell commands for batch operations
- `workflows/*.ps1` - Multi-step automated workflows

**Usage Pattern:**
```powershell
# PowerShell-based workflow orchestration
.codex/super-run.ps1 -Task full-workflow -Sport nfl -Bankroll 10000

# Complements Claude Code slash commands
# Use for batch operations and Windows-specific tasks
```

**System Relationship:**
- **Claude Code**: Python-based, async, cross-platform, AI-integrated
- **Codex**: PowerShell-based, Windows-focused, batch automation
- **Both**: Complementary systems, not competing

### Billy Walters Weekly Workflow (Complete)

**Tuesday/Wednesday (Data Collection):**
```bash
# 1. Complete data collection (all 6 steps automated)
/collect-all-data
# → Triggers: pre_data_collection.py (validation)
# → Runs: Power ratings → Schedules → Stats → Injuries → Weather → Odds
# → Triggers: post_data_collection.py (quality check)
# → Triggers: auto_edge_detector.py (if odds fresh)

# 2. Validate data quality
/validate-data
# → Checks: 5 required files present
# → Scores: EXCELLENT/GOOD/FAIR/POOR
# → Reports: Missing data or stale odds

# 3. Generate betting card (if edges detected)
/betting-card
# → Displays: Picks ranked by edge size
# → Shows: Kelly sizing, expected win rate
# → Highlights: MAX BET (7+ pts), STRONG (4-7 pts)

# 4. Track performance baseline
/clv-tracker
# → Initializes: Active bets tracking
# → Prepares: CLV calculation framework
```

**Thursday (Pre-TNF Refresh):**
```bash
# 1. Refresh odds for Thursday Night Football
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
# → Fast: ~5 seconds (API client)
# → Updates: Latest lines before TNF kickoff

# 2. Re-run edge detection with fresh odds
/edge-detector
# → Detects: Line movements
# → Identifies: New edges or disappeared edges
```

**Sunday (Game Day):**
```bash
# Option 1: Quick pre-game check (RECOMMENDED)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
/edge-detector
# → Fast: Get final lines before games
# → Simple: No live monitoring needed

# Option 2: Live monitoring (OPTIONAL - advanced)
uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 10800 --headless &
/clv-tracker
# → Real-time: Track line movements during games
# → Complex: Requires browser automation
# → Use case: Professional line movement tracking
```

**Post-Game (Results Tracking):**
```bash
/clv-tracker
# → Updates: Closing lines from Sunday
# → Calculates: CLV for each bet
# → Reports: Performance vs closing line
```

---

## Performance Optimizations

### Reduce API Calls

**Strategy: Cache frequently-used data**
```python
# Power ratings: Update weekly only
# ✅ Cache until next Sunday
cache_expiry = next_sunday_midnight

# Weather: Only outdoor stadiums
# ✅ Check stadium type before API call
if stadium.is_indoor:
    weather = None  # Skip API call
else:
    weather = await get_weather()  # Call API

# Odds: Use API client (not browser)
# ✅ 10x faster than browser automation
# API: ~5 seconds for 69 games
# Browser: ~30+ seconds for same data
```

**Expected Impact:**
- AccuWeather: ~16-20 calls per run (vs 32 if checking all teams)
- Overtime.ag: 1 API call (vs 30+ seconds browser automation)
- Power ratings: 1 fetch per week (vs daily re-calculation)

### Parallel Operations

**Strategy: Collect independent data simultaneously**
```python
import asyncio

# ✅ Run in parallel (no dependencies)
await asyncio.gather(
    collect_odds(),
    collect_weather(),
    collect_injuries()
)

# ❌ Don't run in parallel (dependent)
await collect_power_ratings()  # Must finish first
await run_edge_detection()     # Needs power ratings
```

**Expected Impact:**
- Total time: ~15 seconds (parallel) vs ~45 seconds (sequential)
- Bottleneck: API rate limits, not execution time

### Avoid Redundant Processing

**Strategy: Check before running expensive operations**
```python
# ✅ Check if edge detection already ran
edge_report = Path("output/edge_detection/edge_report.txt")
if edge_report.exists() and edge_report.stat().st_mtime > odds_timestamp:
    print("Edge detection already current")
    return

# ✅ Verify odds timestamp before re-running
odds_age = datetime.now() - odds_timestamp
if odds_age < timedelta(minutes=5):
    print("Odds are fresh, running edge detection")
else:
    print("Odds are stale, scrape new odds first")

# ✅ Use post-flight validation to prevent bad data
quality_score = validate_data_quality()
if quality_score == "POOR":
    print("Data quality too low, fix issues before edge detection")
    sys.exit(1)
```

**Expected Impact:**
- Prevents duplicate edge detection runs (~10 seconds saved)
- Avoids processing stale data (incorrect edges)
- Catches missing data before expensive operations

### Optimal Timing Strategy

**When to collect each data type:**

| Data Type | Optimal Timing | Freshness Required | Update Frequency |
|-----------|----------------|-------------------|------------------|
| Power Ratings | Sunday night/Monday | Weekly | After all games complete |
| Game Schedules | Tuesday | Weekly | When lines first post |
| Team Statistics | Tuesday/Wednesday | Weekly | Before edge detection |
| Injury Reports | Thursday + Sunday AM | Daily | Before lineup locks |
| Weather Forecasts | <12 hours before game | Hourly | Within AccuWeather window |
| Odds Data | Tuesday-Wednesday + Thursday + Sunday | Minutes | Before every edge detection |

**Rationale:**
- **Power Ratings**: Need complete game results (Sunday night earliest)
- **Odds**: Most accurate lines Tuesday-Wednesday (sharp money settles)
- **Weather**: AccuWeather Starter plan only provides 12-hour forecast
- **Injuries**: Updated throughout week (Thursday/Sunday most critical)

**Implementation:**
```python
# Tuesday/Wednesday: Complete data pipeline
/collect-all-data  # All 6 steps

# Thursday: Refresh odds + injuries only
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
/injury-report "Team Name" "NFL"
/edge-detector

# Sunday AM: Final check before games
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
/weather "Team Name" "YYYY-MM-DD HH:MM"  # For games <12 hours away
/edge-detector
```

---

## Agent Decision Patterns

### When to Auto-Trigger vs Manual

**Auto-Trigger (via hooks):**
- ✅ Pre-flight validation before data collection
- ✅ Post-flight validation after data collection
- ✅ Edge detection when fresh odds detected (<5 min)
- ✅ Data quality scoring

**Manual Trigger (user-initiated):**
- ✅ Individual game analysis (`/analyze-matchup`)
- ✅ Betting card generation (`/betting-card`)
- ✅ CLV tracking updates (`/clv-tracker`)
- ✅ Ad-hoc weather checks (`/weather`)

**Rationale:**
- Validation should always run (automated)
- Analysis requires user context (manual)
- Performance tracking is user-driven (manual)

### When to Use API Client vs Hybrid Scraper

**API Client (Primary - 95% of use cases):**
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```
- ✅ Pre-game odds collection
- ✅ Tuesday-Wednesday data gathering
- ✅ Thursday/Sunday refreshes
- ✅ 10x faster (5 seconds)
- ✅ No authentication required
- ✅ No browser overhead

**Hybrid Scraper (Secondary - 5% of use cases):**
```bash
uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 10800 --headless
```
- ✅ Live game monitoring (Sundays only)
- ✅ Real-time line movement tracking
- ✅ SignalR WebSocket updates
- ❌ Slower (30+ seconds)
- ❌ Requires authentication
- ❌ Browser automation overhead

**Decision Logic:**
```python
if game_in_progress and monitoring_line_movements:
    use_hybrid_scraper()  # Real-time updates
else:
    use_api_client()  # Fast, simple, reliable
```

### When to Recalculate Power Ratings

**Weekly Update (Recommended):**
```bash
# Every Sunday night or Monday after all games complete
/power-ratings
# → Fetches: Latest Massey composite ratings
# → Updates: 90/10 weighted formula (90% Massey, 10% previous)
# → Saves: data/current/nfl_power_ratings_week_{week}.json
```

**Mid-Week Update (Optional - only if major event):**
```bash
# Only if:
# - Star QB injured mid-week (adjust -4.5 points)
# - Trade deadline acquisition (significant talent change)
# - Coaching change (cultural/scheme impact)

# Otherwise: Skip (ratings are weekly, not daily)
```

**Rationale:**
- Power ratings based on completed games (need full week results)
- Massey composite updates Monday after NFL games
- Injuries handled separately (injury impact values, not power rating changes)
- Over-updating introduces noise, not accuracy

---

## Quick Reference: Command Priority

### High Priority (Run Weekly)
1. `/collect-all-data` - Complete data pipeline
2. `/validate-data` - Quality assurance
3. `/edge-detector` - Find betting opportunities
4. `/betting-card` - Generate picks

### Medium Priority (Run as Needed)
1. `/scrape-overtime` - Refresh odds (Thu/Sun)
2. `/weather` - Check game-time conditions (<12 hrs)
3. `/injury-report` - Verify injury status
4. `/clv-tracker` - Update performance

### Low Priority (Ad-Hoc)
1. `/analyze-matchup` - Deep dive specific game
2. `/team-stats` - Review team metrics
3. `/current-week` - Verify NFL week
4. `/odds-analysis` - Market inefficiency analysis

---

## Summary: Agent Optimization Principles

1. **Validate First**: Run pre-flight checks before expensive operations
2. **Cache Aggressively**: Don't recalculate what hasn't changed
3. **Parallelize**: Collect independent data simultaneously
4. **Check Timestamps**: Avoid reprocessing fresh data
5. **Use API Clients**: Prefer direct API over browser automation
6. **Fail Fast**: Exit on poor data quality, don't process bad data
7. **Time Wisely**: Collect each data type at optimal time
8. **Auto-Trigger Validation**: Manual trigger analysis
9. **Document Failures**: Use `/document-lesson` for new error patterns
10. **Monitor Performance**: Track execution time, API usage, success rate

---

**Last Updated**: 2025-11-24
**Maintained By**: Claude Code autonomous agent system
**Related Docs**:
- Development guidelines: `CLAUDE.md`
- Complete documentation: `docs/_INDEX.md`
- Troubleshooting: `TROUBLESHOOTING.md`
- Hooks reference: `.claude/hooks/README.md`
