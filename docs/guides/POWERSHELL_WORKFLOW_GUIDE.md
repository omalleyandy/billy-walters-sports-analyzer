# PowerShell Workflow Guide

**Quick Reference for Running Billy Walters Data Collection from PowerShell**

---

## Overview

The PowerShell script `scripts/dev/collect_all_data_weekly.ps1` provides a complete data collection workflow including the new X News integration.

This is the **PowerShell equivalent** of the Claude Code `/collect-all-data` command.

---

## Quick Start

### Run Complete Data Collection (Both Leagues)
```powershell
.\scripts\dev\collect_all_data_weekly.ps1
```

### Run NFL Only
```powershell
.\scripts\dev\collect_all_data_weekly.ps1 -League nfl
```

### Run NCAAF Only
```powershell
.\scripts\dev\collect_all_data_weekly.ps1 -League ncaaf
```

---

## What the Script Does

**8 Automated Steps:**

1. **Massey Power Ratings** - Foundation for all analysis
2. **ESPN Team Stats (NFL)** - Offensive/defensive metrics
3. **ESPN Team Stats (NCAAF)** - College team statistics
4. **X News & Injury Posts** ⭐ **NEW** - Breaking news from @NFL, @AdamSchefter, etc.
5. **Weather Data** - Real-time forecasts for outdoor stadiums
6. **Overtime.ag Odds** - Market lines from both sportsbooks
7. **Edge Detection (NFL)** - Spread and totals analysis
8. **Edge Detection (NCAAF)** - College football analysis

---

## Output Locations

After running the script, find your data here:

| Data Type | Location |
|-----------|----------|
| Power Ratings | `output/massey/` |
| Team Statistics | `output/espn/stats/` |
| X News Posts | `output/x_news/integrated/` |
| Weather | `output/weather/` |
| Betting Odds | `output/overtime/` |
| Edges & Picks | `output/edge_detection/` |

---

## Key Features

### ✅ X News Integration (NEW - STEP 5)
- Automatically collects breaking news from official X sources
- Free tier implementation (5 calls/day, 24-hour caching)
- Automatic E-Factor adjustments to edges
- Example: Mahomes injury → KC edge reduced by ~7 points

### ✅ Color-Coded Output
- **Magenta**: Headers and section breaks
- **Yellow**: Current step being executed
- **Green**: Success messages
- **Cyan**: Information and next steps
- **Red**: Errors and warnings

### ✅ Progress Tracking
- Step-by-step execution
- Summary report at the end
- Success/failure count
- File location references

### ✅ Error Handling
- Captures failures for each step
- Continues execution even if one step fails
- Reports all failures in summary

---

## Usage Examples

### Weekly Data Collection (Tuesday)
```powershell
# Collect all data for both leagues
.\scripts\dev\collect_all_data_weekly.ps1

# Review the summary
# Check output/edge_detection/ for edges with X News impact
```

### NFL-Only Analysis (Quicker)
```powershell
# Just collect NFL data
.\scripts\dev\collect_all_data_weekly.ps1 -League nfl

# Fast execution (~15 minutes with X News first-call wait)
```

### NCAAF-Only Analysis
```powershell
# Just collect NCAAF data
.\scripts\dev\collect_all_data_weekly.ps1 -League ncaaf
```

---

## Understanding the Output

### Successful Run
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BILLY WALTERS SPORTS ANALYZER
  Complete Weekly Data Collection
  Date: 2025-11-28 14:30
  League: BOTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] Massey Power Ratings
    Running: uv run python scripts/scrapers/scrape_massey_games.py
[OK] Massey Power Ratings complete

[2] ESPN Team Stats (NFL)
    Running: uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl
[OK] ESPN Team Stats (NFL) complete

[4] X News & Injury Posts (NEW - STEP 5)
    Breaking news from @NFL, @AdamSchefter, @FieldYates + NCAAF sources
    Running: uv run python scripts/scrapers/scrape_x_news_integrated.py --all
[OK] X News & Injury Posts (NEW - STEP 5) complete

... (continues for all steps)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  COLLECTION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Completed: 8
  [OK] Massey Power Ratings
  [OK] ESPN Team Stats (NFL)
  [OK] ESPN Team Stats (NCAAF)
  [OK] X News & Injury Posts (NEW - STEP 5)
  [OK] Weather Data
  [OK] Overtime.ag Odds
  [OK] Edge Detection (NFL)
  [OK] Edge Detection (NCAAF)

Data locations:
  • Power ratings: output/massey/
  • Team stats: output/espn/stats/
  • X News posts: output/x_news/integrated/
  • Weather data: output/weather/
  • Odds data: output/overtime/
  • Edge detection: output/edge_detection/

Next steps:
  1. Review edge detection results
  2. Check X News impact on edges
  3. Generate betting recommendations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [SUCCESS] All data collection steps completed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### If X News is Waiting for Rate Limit
```
[4] X News & Injury Posts (NEW - STEP 5)
    Breaking news from @NFL, @AdamSchefter, @FieldYates + NCAAF sources
    Running: uv run python scripts/scrapers/scrape_x_news_integrated.py --all

Rate limit exceeded. Sleeping for 873 seconds...  (normal - this is X API free tier)
[OK] X News & Injury Posts (NEW - STEP 5) complete
```

This is **normal and expected** on the first API call. The system automatically waits and retries.

---

## X News Integration Details

### What X News Collects
- **Official NFL sources**: @NFL, @NFL_Motive
- **Breaking news**: @AdamSchefter, @FieldYates
- **College football**: @ESPNCollegeFB, @Brett_McMurphy

### How It Influences Edges
```
Before X News:
  KC vs BUF
  Predicted: KC -2.0
  Market: KC -2.5
  Edge: 0.5 pts (NO PLAY)

X Post: "@AdamSchefter: Patrick Mahomes out with ankle injury"
  Impact: -7.0 points (elite QB loss)

After X News:
  Adjusted Predicted: KC -2.0 - 7.0 = KC -9.0
  Market: KC -2.5
  NEW EDGE: 6.5 pts AGAINST KC (BET BUFFALO!)
  Recommendation: STRONG
```

### Free Tier Constraints
- **5 API calls/day maximum** (conservative enforcement)
- **100 posts/month limit** (rarely hit with this schedule)
- **24-hour caching** (95% API savings after first call)
- **1 request per 15 minutes** (free tier rate limit)

The system automatically:
- ✅ Waits for rate limits
- ✅ Caches results for 24 hours
- ✅ Prevents quota exhaustion
- ✅ Falls back gracefully if quota exceeded

---

## Troubleshooting

### "X News & Injury Posts" Step Seems to Hang
**This is normal!** The free tier allows only 1 request per 15 minutes.
- System is waiting automatically
- Check for: `Rate limit exceeded. Sleeping for X seconds...`
- Let it complete (~15 minutes on first call)
- Subsequent runs use cache (< 3 seconds)

### Script Won't Run (Permission Denied)
```powershell
# If you get "cannot be loaded because running scripts is disabled..."
# Run this once to enable scripts:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Some Steps Show [ERROR]
- Check that your `.env` file has all required API keys
- Verify internet connection
- Check specific error message in output
- Some errors are non-critical (ESPN scrapers may warn if unavailable)

### X News Shows 0/5 Quota Used
This is correct! It means:
- ✅ Bearer Token is valid
- ✅ X API is reachable
- ✅ No calls made yet today
- Ready to collect X News posts

---

## Recommended Weekly Schedule

### Tuesday (2:00 PM)
```powershell
# Run complete data collection
.\scripts\dev\collect_all_data_weekly.ps1

# This collects:
# - Fresh power ratings
# - Current team stats
# - X News posts (breaking injuries)
# - Weather forecasts
# - Latest odds
# - Edge detection analysis
```

### Wednesday (9:00 AM)
```powershell
# Review results from Tuesday
# Check output/edge_detection/ for picks

# Optional: Run NFL only for quick update
.\scripts\dev\collect_all_data_weekly.ps1 -League nfl
```

---

## Next Steps After Running Script

1. **Review Edges**
   - Check `output/edge_detection/nfl_edges_detected.jsonl`
   - Look for 7+ point edges (MAX BET candidates)
   - Check X News impact on edges

2. **Check X News Impact**
   - Find posts in `output/x_news/integrated/x_news_*.json`
   - See how breaking news influenced edge calculations
   - Compare edges with/without X News adjustments

3. **Generate Picks**
   - Use edges to identify betting opportunities
   - Apply Kelly Criterion sizing
   - Track Closing Line Value (CLV) for performance

---

## Documentation Reference

- [X News Workflow Integration](X_NEWS_WORKFLOW_INTEGRATION.md) - How X News works daily
- [X News Daily Workflow](X_NEWS_DAILY_WORKFLOW.md) - Scheduling and integration
- [STEP 6 Integration Complete](STEP_6_INTEGRATION_COMPLETE.md) - X News in workflow
- [STEP 7 E-Factor Verification](STEP_7_EFACTOR_VERIFICATION_COMPLETE.md) - Edge detection
- [X News Integration Complete Index](X_NEWS_INTEGRATION_COMPLETE_INDEX.md) - Master index

---

## Commands Reference

### Check X News Quota (No API Call)
```powershell
uv run python scripts/scrapers/scrape_x_news_integrated.py --quota-status
```

### Collect X News Only
```powershell
uv run python scripts/scrapers/scrape_x_news_integrated.py --all
uv run python scripts/scrapers/scrape_x_news_integrated.py --league nfl
uv run python scripts/scrapers/scrape_x_news_integrated.py --league ncaaf
```

### Run Edge Detection Only
```powershell
uv run python src/walters_analyzer/valuation/billy_walters_edge_detector.py --league nfl
uv run python src/walters_analyzer/valuation/ncaaf_edge_detector.py --league ncaaf
```

### Collect Specific Data
```powershell
# Massey ratings
uv run python scripts/scrapers/scrape_massey_games.py

# ESPN stats
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl

# Weather
uv run python -m src.data.weather_client --league nfl

# Odds
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```

---

## Quick Command Cheat Sheet

```powershell
# Complete workflow (both leagues)
.\scripts\dev\collect_all_data_weekly.ps1

# NFL only
.\scripts\dev\collect_all_data_weekly.ps1 -League nfl

# NCAAF only
.\scripts\dev\collect_all_data_weekly.ps1 -League ncaaf

# Check X News quota
uv run python scripts/scrapers/scrape_x_news_integrated.py --quota-status

# Collect X News manually
uv run python scripts/scrapers/scrape_x_news_integrated.py --all

# Run edge detection
uv run python src/walters_analyzer/valuation/billy_walters_edge_detector.py --league nfl
```

---

## System Status

✅ **X News Integration**: Complete and verified
✅ **PowerShell Workflow**: Ready for production
✅ **E-Factor System**: Active and updating edges
✅ **Free Tier**: Optimized (5 calls/day, 24-hour cache)

**Ready to**: Run weekly data collection and generate betting picks!

---

**Last Updated**: 2025-11-28
**Status**: PRODUCTION READY