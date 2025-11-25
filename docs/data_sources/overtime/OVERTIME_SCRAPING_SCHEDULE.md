# Overtime.ag Scraping Schedule Guide

**IMPORTANT:** This is a timing guidance document for MANUAL execution. There are NO scheduled or automated scrapers running on Tuesday or any other day. All scraping is 100% on-demand and must be manually triggered.

## Problem Solved

**Issue:** Overtime scraper returns 0 games
**Root Cause:** Scraping at wrong times (during games or before lines post)
**Solution:** Follow optimal scraping timing guidance below (manual execution)

## TL;DR - When to Scrape

✅ **BEST TIMES:**
- **Tuesday afternoon (12 PM - 6 PM)** - Week+1 lines just posted
- **Wednesday (all day)** - Stable lines, full markets
- **Thursday morning (before 6 PM)** - Fresh lines before TNF

❌ **WORST TIMES:**
- **Sunday after 1 PM** - Games in progress, lines pulled
- **Monday after 8 PM** - Monday Night Football in progress
- **Tuesday before 12 PM** - Lines not posted yet

## Complete Weekly Schedule

### SUNDAY
- **Before 1 PM:** ✅ GOOD (today's games lines still available)
- **After 1 PM:** ❌ BAD (games in progress, markets closed)
- **Status:** Week N games being played

### MONDAY
- **Before 8 PM:** ⚠️ SUBOPTIMAL (only TNF or Week N+1 early lines)
- **After 8 PM:** ❌ BAD (Monday Night Football in progress)
- **Status:** Week N concluding with MNF

### TUESDAY
- **Before 12 PM:** ⚠️ SUBOPTIMAL (lines not posted yet - wait!)
- **12 PM - 6 PM:** ✅ **OPTIMAL** (Week N+1 lines just posted)
- **After 6 PM:** ✅ GOOD (Week N+1 lines available)
- **Status:** Week N+1 lines go live

### WEDNESDAY
- **All Day:** ✅ **OPTIMAL** (full betting markets, stable lines)
- **Status:** Week N+1 lines active and stable

### THURSDAY
- **Before 6 PM:** ✅ **OPTIMAL** (good time before TNF)
- **6 PM - 8 PM:** ⚠️ SUBOPTIMAL (TNF game starting soon)
- **After 8 PM:** ❌ BAD (Thursday Night Football in progress)
- **Status:** Week N+1 TNF game tonight

### FRIDAY
- **All Day:** ✅ GOOD (full betting markets)
- **Status:** Week N+1 lines available

### SATURDAY
- **Before 1 PM:** ✅ GOOD (before games start)
- **After 1 PM:** ⚠️ SUBOPTIMAL (college games may be in progress)
- **Status:** Week N+1 approaching

## Billy Walters Weekly Workflow

### **TUESDAY** (Optimal Data Collection Day)

**Morning (before noon):**
```bash
# Check if timing is good
uv run python scripts/utilities/check_scraping_timing.py
# Will show: [WARN] SUBOPTIMAL - wait until 12 PM
```

**Afternoon (12 PM - 6 PM):** ← **BEST TIME**
```bash
# 1. Check timing
uv run python scripts/utilities/check_scraping_timing.py
# Should show: [OK] OPTIMAL

# 2. Scrape odds
/scrape-overtime

# 3. Scrape power ratings
/scrape-massey

# 4. Validate data
/validate-data
```

### **WEDNESDAY** (Analysis Day)

```bash
# 1. Complete data collection
/collect-all-data

# 2. Validate quality
/validate-data

# 3. Run edge detection
/edge-detector

# 4. Generate betting card
/betting-card
```

### **THURSDAY** (Pre-TNF Refresh)

**Morning:**
```bash
# Refresh odds before TNF
/scrape-overtime

# Re-run edge detection with fresh lines
/edge-detector
```

### **SUNDAY** (Performance Tracking)

**Before games:**
```bash
# Track closing line value
/clv-tracker
```

## Pre-Scrape Timing Check

**Always check timing before scraping:**

```bash
uv run python scripts/utilities/check_scraping_timing.py
```

**Exit Codes:**
- `0` = OPTIMAL (go ahead and scrape)
- `1` = SUBOPTIMAL (can scrape but results may be limited)
- `2` = BAD (don't scrape - lines unavailable)

## Why Timing Matters

### Lines Are Pulled During Games

Sportsbooks remove pre-game lines when games start because:
- Lines would change rapidly during play
- They don't want pre-game action on live games
- Only live betting markets are available during games

### Lines Post After Games Complete

Week N+1 lines typically post:
- **After Monday Night Football ends** (~11 PM - midnight Monday)
- **Tuesday morning processing** (bookmakers set lines overnight)
- **Tuesday afternoon availability** (12 PM - 6 PM lines go live)

## Troubleshooting

### "0 games found" on Tuesday morning

**Problem:** Scraped before lines posted
**Time:** Tuesday 2-11 AM
**Solution:** Wait until Tuesday afternoon (12 PM+)

```bash
# Check current timing status
uv run python scripts/utilities/check_scraping_timing.py

# If SUBOPTIMAL, wait and try again at 2 PM
```

### "0 games found" on Sunday evening

**Problem:** Scraped during games
**Time:** Sunday after 1 PM
**Solution:** Wait until Tuesday afternoon

**Why:** Week N games in progress, Week N+1 lines not posted yet

### "0 games found" on Monday night

**Problem:** Scraped during Monday Night Football
**Time:** Monday after 8 PM
**Solution:** Wait until Tuesday afternoon (12 PM+)

## Manual Verification

Before assuming scraper is broken:

1. **Check timing:**
   ```bash
   uv run python scripts/utilities/check_scraping_timing.py
   ```

2. **Check manually on website:**
   - Go to https://overtime.ag
   - Login with credentials
   - Click "Football" → "NFL-Game/1H/2H/Qrts"
   - Verify games are displayed

3. **If games visible but scraper fails:**
   - Technical issue (HTML structure changed)
   - Session/auth problem
   - Selector mismatch

4. **If no games visible on website:**
   - Timing issue (wait for lines to post)
   - Betting window closed
   - Check back Tuesday afternoon

## Automation Recommendations

### ⚠️ **DO NOT** Auto-Scrape on Schedule

**Bad approach:**
```bash
# DON'T DO THIS - will fail most of the time
0 * * * * /scrape-overtime  # Every hour (BAD)
```

**Why:** Lines are only available specific times, auto-scraping wastes resources

### ✅ **DO** Manual Scraping at Optimal Times

**Good approach:**
```bash
# Tuesday afternoon - manually triggered
/scrape-overtime  # After checking timing first
```

### ✅ **DO** Use Timing Check Before Auto-Scrape

**Better automated approach:**
```bash
# Only scrape if timing check passes
if uv run python scripts/utilities/check_scraping_timing.py; then
    /scrape-overtime
else
    echo "Suboptimal time, skipping scrape"
fi
```

## Summary

| Day | Time | Status | Action |
|-----|------|--------|--------|
| **Tuesday** | **12 PM - 6 PM** | ✅ **OPTIMAL** | **Scrape now!** |
| Wednesday | All day | ✅ OPTIMAL | Scrape if needed |
| Thursday | Before 6 PM | ✅ OPTIMAL | Scrape if needed |
| Tuesday | Before 12 PM | ⚠️ SUBOPTIMAL | Wait until noon |
| Thursday | After 8 PM | ❌ BAD | Don't scrape (TNF) |
| Sunday | After 1 PM | ❌ BAD | Don't scrape (games) |
| Monday | After 8 PM | ❌ BAD | Don't scrape (MNF) |

**Golden Rule:** When in doubt, check timing first with the validator script.

## Related Documentation

- `test_overtime_scraper_timing.md` - Investigation notes
- `OVERTIME_QUICKSTART.md` - Scraper usage guide
- `docs/guides/OVERTIME_SCRAPER_USAGE.md` - Technical documentation
