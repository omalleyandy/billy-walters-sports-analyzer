Scrape pregame odds from Overtime.ag for NFL and NCAAF games.

**NEW METHOD (2025-11-11): Direct API Access - No Browser Required!**

This scraper uses a reverse-engineered API endpoint discovered via Chrome DevTools
ServiceCaller inspection (data/overtime_libs.js line 4278).

**Advantages:**
- No browser automation (Playwright) required
- No CloudFlare bypass needed
- No proxy configuration required
- No authentication required
- Fast (< 5 seconds vs 30+ seconds with Playwright)
- Works on all platforms
- Simple HTTP POST request

Usage: /scrape-overtime [options]

Examples:
- /scrape-overtime (scrape both NFL and NCAAF)
- /scrape-overtime --nfl (scrape NFL only)
- /scrape-overtime --ncaaf (scrape NCAAF only)

This command will:
1. Send HTTP POST to Overtime.ag API
2. Receive JSON response with all game lines
3. Convert to Billy Walters format
4. Save to organized output directories

**When to Run:**
You can run this ANYTIME! Results vary by timing:

- **Tuesday-Wednesday**: 14+ NFL games, 50+ NCAAF games (OPTIMAL - most lines available)
- **Thursday-Saturday**: Varies by week (some games available)
- **Sunday-Monday**: Few/no pregame lines (games in progress, use live scraper instead)

The scraper returns whatever lines are currently posted - 0 games is normal on Sunday/Monday.

**Command to Run (NEW - RECOMMENDED):**
```bash
# Both NFL and NCAAF
uv run python scripts/scrapers/scrape_overtime_api.py

# NFL only
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# NCAAF only
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
```

**Legacy Command (Browser-Based - DEPRECATED):**
```bash
uv run python scripts/archive/overtime_legacy/scrape_overtime_all.py --headless --convert --proxy ""
```

**Additional Options:**
- `--nfl` - Scrape NFL only
- `--ncaaf` - Scrape NCAAF only
- `--output PATH` - Custom output directory (default: output/overtime)
- `--no-save` - Don't save files (testing only)

**Output Files (NEW FORMAT):**
- **NFL**:
  - Raw: `output/overtime/nfl/pregame/api_raw_TIMESTAMP.json`
  - Walters: `output/overtime/nfl/pregame/api_walters_TIMESTAMP.json`
- **NCAAF**:
  - Raw: `output/overtime/ncaaf/pregame/api_raw_TIMESTAMP.json`
  - Walters: `output/overtime/ncaaf/pregame/api_walters_TIMESTAMP.json`

**Legacy Files (Browser-Based - DEPRECATED):**
- NFL: `output/overtime/nfl/pregame/overtime_nfl_*.json`
- NCAAF: `output/overtime/ncaaf/pregame/overtime_ncaaf_*.json`

**Data Extracted:**
- Current spread (home/away)
- Current total (over/under)
- Moneyline odds (home/away)
- Game time and rotation numbers
- Multiple periods (full game, halves, quarters)

**Billy Walters Format Conversion:**
- Converts rotation numbers to team names
- Standardizes odds format (American to decimal)
- Calculates implied probabilities
- Extracts opening lines (if available)
- Tracks line movements

**Troubleshooting:**
- **HTTP errors**: Check internet connection, API may be temporarily down
- **0 games found**: NORMAL on Sunday/Monday (games in progress, pregame lines pulled)
  - Try again Tuesday-Wednesday for optimal results
  - Or use live scraper for in-game odds during games
- **JSON decode errors**: Verify API response format hasn't changed

**Sports Covered:**
- NFL (National Football League)
- NCAAF (NCAA College Football)

**Technical Details (NEW API METHOD):**
- Endpoint: POST https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering
- Authentication: None required (public API)
- Format: JSON request/response
- Timeout: 30 seconds
- No browser, no CloudFlare bypass, no proxy needed

**API Payload Example:**
```json
{
  "sportType": "Football",
  "sportSubType": "NFL",
  "wagerType": "Straight Bet",
  "hoursAdjustment": 0,
  "periodNumber": 0,
  "gameNum": null,
  "parentGameNum": null,
  "teaserName": "",
  "requestMode": "G"
}
```

**Required Environment Variables:**
- None (API is public)

**Integration:**
- Step 6 in Billy Walters data collection workflow
- Runs after injuries and weather
- Feeds into edge detection analysis
- Critical for market line comparison
