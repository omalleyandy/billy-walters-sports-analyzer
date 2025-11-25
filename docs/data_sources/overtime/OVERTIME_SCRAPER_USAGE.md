# Overtime.ag Scraper Usage Guide

## Overview

This guide explains how to use the Overtime.ag scrapers to collect **real betting data** for NFL games. Understanding when and how to run these scrapers is critical for data quality.

## Two Scrapers Available

### 1. Pre-Game NFL Scraper
**File**: [src/data/overtime_pregame_nfl_scraper.py](../src/data/overtime_pregame_nfl_scraper.py)
**Script**: [scripts/scrape_overtime_nfl.py](../scripts/scrape_overtime_nfl.py)
**Purpose**: Scrape pre-game betting lines (spreads, totals, moneylines)
**Data**: Game, 1st Half, 1st Quarter lines

### 2. Live Odds Scraper (Scrapy)
**File**: [scrapers/overtime_live/spiders/overtime_live_spider.py](../scrapers/overtime_live/spiders/overtime_live_spider.py)
**Purpose**: Scrape live in-game betting lines (NCAAF focus)
**Data**: Live game state, spreads, totals, moneylines

---

## Critical: When to Scrape

### OPTIMAL SCRAPING WINDOW

**Best Times** (Tuesday-Thursday, 12 PM - 6 PM ET):
- Lines post after Monday Night Football ends (usually Tuesday morning)
- All Week N games available before Thursday Night Football
- Maximum data availability
- Stable odds before sharp action moves lines

**Why This Window?**
- Monday Night Football completes Week N-1
- Sportsbooks post Week N lines Tuesday morning
- Thursday Night Football (Week N) starts Thursday ~8:20 PM ET
- Window: ~2.5 days of clean data

### AVOID THESE TIMES

**Sunday/Monday Evenings (6 PM - 11 PM ET)**:
- Games in progress
- Pre-game lines **removed from site**
- Only live betting available (different interface)
- **Result: 0 games found** (expected behavior)

**Friday-Sunday**:
- Lines may be taken down or heavily moved
- Sharp action distorts lines
- Less reliable for baseline power ratings

---

## Pre-Game NFL Scraper Usage

### Basic Usage

```bash
# Scrape with visible browser (recommended for testing)
uv run python scripts/scrape_overtime_nfl.py

# Scrape in headless mode (production)
uv run python scripts/scrape_overtime_nfl.py --headless

# Scrape and convert to Billy Walters format
uv run python scripts/scrape_overtime_nfl.py --headless --convert

# Scrape, convert, and save to database
uv run python scripts/scrape_overtime_nfl.py --headless --convert --save-db
```

### Advanced Options

```bash
# Custom output directory
uv run python scripts/scrape_overtime_nfl.py --output data/odds

# Disable proxy (use direct connection)
uv run python scripts/scrape_overtime_nfl.py --proxy ""

# Specify credentials (overrides .env)
uv run python scripts/scrape_overtime_nfl.py --customer-id YOUR_ID --password YOUR_PASS
```

### What the Scraper Does

1. **Login**: Authenticates with Overtime.ag credentials
2. **Navigate**: Goes to NFL betting section (NFL-Game/1H/2H/Qrts)
3. **Extract Account Info**: Gets balance, available balance, pending
4. **Scrape Lines**: Extracts spreads, totals, moneylines for:
   - Full Game
   - 1st Half
   - 1st Quarter
5. **Validate**: Checks data quality (team names, odds present)
6. **Save**: Outputs JSON with metadata and validation results

### Output Files

**Raw Overtime Format**:
```
output/overtime_nfl_odds_YYYYMMDD_HHMMSS.json
```

**Billy Walters Format** (with `--convert`):
```
output/overtime_nfl_walters_YYYYMMDD_HHMMSS.json
```

### Sample Output (Valid Data)

```json
{
  "scrape_metadata": {
    "timestamp": "2025-11-12T14:30:00",
    "source": "overtime.ag",
    "sport": "NFL",
    "scraper_version": "1.0.0",
    "data_validation": {
      "is_valid": true,
      "warnings": [],
      "game_count": 14,
      "has_odds": true,
      "has_team_names": true
    }
  },
  "games": [
    {
      "visitor": {
        "teamName": "Kansas City Chiefs",
        "rotationNumber": "401",
        "spread": "-3 -110",
        "total": "O 47.5 -110",
        "moneyLine": "-165"
      },
      "home": {
        "teamName": "Buffalo Bills",
        "rotationNumber": "402",
        "spread": "+3 -110",
        "total": "U 47.5 -110",
        "moneyLine": "+145"
      }
    }
  ]
}
```

### Sample Output (No Games - Expected During Games)

```json
{
  "scrape_metadata": {
    "data_validation": {
      "is_valid": false,
      "warnings": [
        "No games found - may be outside betting window"
      ],
      "game_count": 0
    }
  },
  "games": []
}
```

---

## Live Odds Scraper Usage

### Basic Usage

```bash
# Run Scrapy spider
cd scrapers/overtime_live
uv run scrapy crawl overtime_live -o ../../output/overtime_live.json

# Run with custom settings
uv run scrapy crawl overtime_live \
  -o ../../output/overtime_live.json \
  -s PLAYWRIGHT_LAUNCH_OPTIONS='{"headless": false}'
```

### What the Scraper Does

1. **Proxy Test**: Verifies proxy connectivity (if configured)
2. **Login**: Authenticates with Overtime.ag
3. **Navigate**: Goes to live betting section
4. **API Extraction** (preferred): Calls Offering.asmx API endpoints
5. **DOM Fallback**: Parses iframe if API fails
6. **Filter**: Attempts to select Football -> NCAAF
7. **Extract**: Pulls team names, spreads, totals, moneylines, game state

### Output Format

```json
{
  "source": "overtime.ag",
  "sport": "college_football",
  "league": "NCAAF",
  "collected_at": "2025-11-12T19:30:00",
  "game_key": "clemson_vs_louisville",
  "teams": {
    "away": "Clemson Tigers",
    "home": "Louisville Cardinals"
  },
  "state": {
    "quarter": 3,
    "clock": "08:42"
  },
  "markets": {
    "spread": {
      "away": {"line": -7.5, "price": -110},
      "home": {"line": 7.5, "price": -110}
    },
    "total": {
      "over": {"line": 52.5, "price": -110},
      "under": {"line": 52.5, "price": -110}
    },
    "moneyline": {
      "away": {"price": -340},
      "home": {"price": +280}
    }
  },
  "is_live": true
}
```

---

## Data Validation

Both scrapers now include **automatic data validation** to detect issues:

### Pre-Game NFL Scraper Validation

**Checks**:
- Games found (> 0)
- Team names present
- Betting lines present (spread, total, or moneyline)

**Warnings**:
- "No games found - may be outside betting window"
- "No valid team names found"
- "No betting lines found - games may have started"

### Live Odds Scraper Validation

**Checks**:
- Games emitted (> 0)
- Market data present
- Team names valid

**Output Messages**:
```
NO GAMES FOUND - Possible Reasons:
  1. Games are currently in progress (lines removed)
  2. Outside betting window (pre-game lines not posted yet)
  3. Sport filter not applied correctly
  4. Site structure changed

OPTIMAL SCRAPING TIMES:
  - Tuesday-Thursday: 12PM-6PM ET (new week lines)
  - Avoid: Sunday/Monday evenings (games in progress)
```

---

## Troubleshooting

### Problem: 0 Games Found

**Diagnosis**:
```bash
# Check scraper output for warnings
uv run python scripts/scrape_overtime_nfl.py 2>&1 | grep -A5 "WARNING"

# Look for diagnostic messages:
# "No betting buttons found!"
# "This is normal during games (Sunday/Monday evenings)"
```

**Solutions**:
1. **Check the time**: Are games currently in progress?
2. **Run Tuesday-Thursday**: Optimal window for pre-game lines
3. **Check site manually**: Login to overtime.ag and verify games are visible
4. **Review snapshots**: Check debug output for page content

### Problem: Proxy Authentication Failed

**Diagnosis**:
```
[ERROR] Proxy error: 407 Proxy Authentication Required
```

**Solutions**:
1. Verify proxy credentials in `.env`
2. Test proxy directly:
   ```bash
   uv run python src/data/proxy_manager.py
   ```
3. Disable proxy temporarily:
   ```bash
   uv run python scripts/scrape_overtime_nfl.py --proxy ""
   ```

### Problem: Login Failed

**Diagnosis**:
```
Login failed: Could not find login button
```

**Solutions**:
1. Verify credentials in `.env`:
   ```
   OV_CUSTOMER_ID=your_customer_id
   OV_PASSWORD=your_password
   ```
2. Check if credentials expired
3. Run with visible browser to see error:
   ```bash
   uv run python scripts/scrape_overtime_nfl.py
   ```

### Problem: Data Format Issues

**Diagnosis**:
```json
{
  "visitor": {
    "teamName": "401 Kansas City Chiefs",
    "spread": null
  }
}
```

**Solutions**:
1. Site structure may have changed
2. Check scraper selectors in code:
   - [overtime_pregame_nfl_scraper.py:352-403](../src/data/overtime_pregame_nfl_scraper.py#L352-L403)
3. Run with visible browser to inspect page
4. Check snapshots for debugging

---

## Best Practices

### 1. Schedule Scraping Properly

**Recommended Cron Schedule**:
```bash
# Tuesday 2 PM ET (new week lines)
0 14 * * 2 cd /path/to/analyzer && uv run python scripts/scrape_overtime_nfl.py --headless --convert

# Wednesday 2 PM ET (verify lines stable)
0 14 * * 3 cd /path/to/analyzer && uv run python scripts/scrape_overtime_nfl.py --headless --convert

# Thursday 12 PM ET (before TNF)
0 12 * * 4 cd /path/to/analyzer && uv run python scripts/scrape_overtime_nfl.py --headless --convert
```

### 2. Validate Data Quality

Always check validation results:
```python
with open('output/overtime_nfl_odds_latest.json') as f:
    data = json.load(f)
    validation = data['scrape_metadata']['data_validation']

    if not validation['is_valid']:
        print("WARNING: Data quality issues detected")
        print(f"Warnings: {validation['warnings']}")
```

### 3. Monitor for Changes

Overtime.ag may update their site structure. If scrapers suddenly stop working:

1. Check snapshots: `snapshots/overtime_live_initial.png`
2. Review debug output: Look for element counts
3. Inspect page manually: Use browser DevTools
4. Update selectors: Modify scraper code if needed

### 4. Use Version Control

Always review scraped data before committing:
```bash
# Check latest scrape
cat output/overtime_nfl_odds_*.json | jq '.summary'

# Verify game count is reasonable (typically 14-16 NFL games per week)
```

---

## Integration with Billy Walters System

### Workflow

1. **Scrape** (Tuesday-Thursday):
   ```bash
   uv run python scripts/scrape_overtime_nfl.py --headless --convert
   ```

2. **Validate** (automatic):
   - Check `data_validation.is_valid`
   - Review warnings

3. **Edge Detection** (trigger after valid scrape):
   ```bash
   /edge-detector
   ```

4. **Betting Card** (generate picks):
   ```bash
   /betting-card
   ```

5. **CLV Tracking** (monitor performance):
   ```bash
   /clv-tracker
   ```

### Automated via Hooks

The scraper integrates with automation hooks:

**Pre-Collection Hook**: [.claude/hooks/pre_data_collection.py](../.claude/hooks/pre_data_collection.py)
- Validates environment (credentials, directories)
- Checks current NFL week
- Prevents scraping with missing config

**Post-Collection Hook**: [.claude/hooks/post_data_collection.py](../.claude/hooks/post_data_collection.py)
- Validates scraped data quality
- Checks freshness (<24 hours)
- Scores data: EXCELLENT/GOOD/FAIR/POOR

**Auto Edge Detector**: [.claude/hooks/auto_edge_detector.py](../.claude/hooks/auto_edge_detector.py)
- Monitors for new odds data
- Triggers edge detection automatically
- Prevents redundant processing

---

## FAQ

### Q: Why am I getting 0 games on Sunday evening?

**A**: This is **expected and normal**. Games are in progress and pre-game lines are removed from the site. Scrape Tuesday-Thursday instead.

### Q: How often should I scrape?

**A**: **Once per day during the optimal window** (Tuesday-Thursday). Scraping more frequently provides minimal value and may trigger rate limits.

### Q: What if proxy fails?

**A**: The scraper uses **smart proxy management** with automatic fallback. If the proxy fails the connectivity test, it switches to a direct connection automatically.

### Q: Can I scrape without login?

**A**: **No**. Overtime.ag requires authentication to view betting lines. You must have valid credentials in `.env`.

### Q: How do I know if I have real data?

**A**: Check the validation results:
```json
"data_validation": {
  "is_valid": true,
  "has_odds": true,
  "has_team_names": true,
  "game_count": 14
}
```

If `is_valid: false`, review warnings and timing.

### Q: What's the difference between pre-game and live scrapers?

**A**:
- **Pre-game**: Scrapes lines before games start (Tuesday-Thursday optimal)
- **Live**: Scrapes in-game lines during games (Sunday/Saturday during games)

They target different interfaces on Overtime.ag.

---

## Next Steps

1. **Test Pre-Game Scraper** (Tuesday-Thursday):
   ```bash
   uv run python scripts/scrape_overtime_nfl.py
   ```

2. **Verify Data Quality**:
   - Check output file
   - Review validation results
   - Confirm game count (14-16 expected for NFL)

3. **Integrate with Workflow**:
   ```bash
   /collect-all-data  # Includes Overtime scraping
   /edge-detector     # Analyze lines
   /betting-card      # Generate picks
   ```

4. **Monitor Performance**:
   - Track CLV (Closing Line Value)
   - Review edge detection results
   - Adjust timing if needed

---

## Support

**Issues**:
- File path errors → Check working directory
- Login failures → Verify credentials in `.env`
- 0 games found → Check timing (Tuesday-Thursday optimal)
- Proxy errors → Test proxy with `proxy_manager.py`

**Documentation**:
- [Overtime Integration Guide](OVERTIME_INTEGRATION_COMPLETE.md)
- [Technical Reference](OVERTIME_TECHNICAL_REFERENCE.md)
- [Lessons Learned](../LESSONS_LEARNED.md)

**Code References**:
- Pre-game scraper: [src/data/overtime_pregame_nfl_scraper.py](../src/data/overtime_pregame_nfl_scraper.py)
- Live scraper: [scrapers/overtime_live/spiders/overtime_live_spider.py](../scrapers/overtime_live/spiders/overtime_live_spider.py)
- Proxy manager: [src/data/proxy_manager.py](../src/data/proxy_manager.py)
