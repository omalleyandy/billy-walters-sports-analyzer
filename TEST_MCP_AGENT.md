# Testing the MCP Agent - Quick Start

## Quick Test Scenarios

### Test 1: Basic MCP Connection (1 minute)

**In Claude Desktop, try:**

```
Can you check if the chrome-devtools MCP server is available?
List the available MCP tools.
```

**Expected Output:**
- `mcp_chrome-devtools_navigate_page`
- `mcp_chrome-devtools_take_snapshot`
- `mcp_chrome-devtools_evaluate_script`

### Test 2: Navigate to Overtime.ag (2 minutes)

**Prompt:**

```
Navigate to https://overtime.ag/sports/ using the chrome-devtools MCP.
Tell me if the page loads successfully and what you see.
```

**Expected Result:**
- Page loads in ~2 seconds
- Should see NFL games listed
- No Cloudflare blocking

### Test 3: Extract Odds Data (5 minutes)

**Prompt:**

```
Please extract NFL odds data:

1. Navigate to https://overtime.ag/sports/
2. Take a snapshot of the page
3. Save the snapshot to ./snapshots/test_snapshot.txt
4. Show me a preview of what data you found
```

**Expected Output:**
- Snapshot saved successfully
- Shows rotation numbers (e.g., 109-110)
- Shows team names (e.g., Raiders vs Broncos)
- Shows spreads, moneylines, totals

### Test 4: Run the Full Scraper (10 minutes)

**Prompt:**

```
Run the complete odds scraper workflow:

1. Navigate to https://overtime.ag/sports/
2. Take a snapshot
3. Save to ./snapshots/latest.txt
4. Run: uv run python scrape_odds_mcp.py ./snapshots/latest.txt
5. Show me the summary of games found
6. List the output files created
```

**Expected Output:**
```
[SUCCESS] Saved 14 games to:
  - JSONL: nfl-odds-20251107-143022.jsonl
  - JSON:  nfl-odds-20251107-143022.json
  - CSV:   nfl-odds-20251107-143022.csv

NFL ODDS SCRAPING SUMMARY - 14 GAMES
================================================================================

2025-11-09 (10 games):
  251 | 9:30 AM         | Atlanta Falcons           @ Indianapolis Colts
       |                 | Spread: +6.5 / -6.5
  ...
```

### Test 5: Billy Walters Analysis (15 minutes)

**Prerequisites:**
- Odds data scraped (from Test 4)
- Injury data available (or skip injury gates)

**Prompt:**

```
Run the Billy Walters injury analysis:

1. Check what odds data files exist in data/odds/nfl/
2. Check what injury data exists in data/injuries/nfl/
3. Run: uv run python analyze_games_with_injuries.py
4. Show me the top 5 betting opportunities
5. Explain the edge calculations
```

**Expected Output:**
```
🏈 BILLY WALTERS BETTING SIGNALS

TOP OPPORTUNITIES:

1. Browns @ Jets
   Edge: 2.7 points
   Confidence: High
   Reasoning:
   - Jets QB hamstring: -1.8 pts (70% capacity)
   - Jets WR1 out: -1.5 pts
   - Market underreaction: +0.6 pts
   Kelly Size: 1.8% bankroll
```

### Test 6: Autonomous Agent - Full Pipeline (20 minutes)

**This is the ultimate test - let Claude work autonomously:**

```
Please act as an autonomous betting analysis agent. Complete this workflow:

STEP 1: DATA COLLECTION
- Navigate to overtime.ag and scrape current NFL odds
- Save to the appropriate data directory
- Verify data quality

STEP 2: INJURY DATA CHECK
- Check for recent injury data in data/injuries/nfl/
- If older than 24 hours, recommend refreshing with:
  uv run walters-analyzer scrape-injuries --sport nfl

STEP 3: BILLY WALTERS ANALYSIS
- Run the combined injury + odds analysis
- Identify games with edge > 2 points
- Calculate position-specific impacts
- Detect market inefficiencies

STEP 4: GENERATE REPORT
- List top 5 betting opportunities
- Show edge calculations
- Display Kelly bet sizing
- Include confidence levels and reasoning

STEP 5: SAVE REPORT
- Save analysis to logs/betting_signals_{date}.md
- Include timestamp and data sources

Work autonomously and report back when complete.
```

**Expected Behavior:**
- Claude runs all steps without asking for permission
- Handles errors gracefully (e.g., if no games are available)
- Saves results to files
- Provides a comprehensive final report

## Troubleshooting Common Issues

### Issue: "MCP server not found"

**Solution:**
1. Check Claude Desktop config is correct
2. Restart Claude Desktop
3. Look for MCP server icons in Claude Desktop UI

### Issue: "Cannot navigate to page"

**Solution:**
1. Ensure Chrome is installed
2. Check internet connection
3. Try navigating manually to verify overtime.ag is accessible

### Issue: "No games found in snapshot"

**Reasons:**
- Not during NFL season (September - February)
- Wrong page URL
- Page layout changed

**Solution:**
1. Check overtime.ag manually in your browser
2. Verify games are visible on the site
3. Check the snapshot file content

### Issue: "scrape_odds_mcp.py not found"

**Solution:**
```bash
# Ensure you're in the project root
cd /home/user/billy-walters-sports-analyzer

# Verify file exists
ls -l scrape_odds_mcp.py

# Run with full path
uv run python ./scrape_odds_mcp.py ./snapshots/latest.txt
```

### Issue: "No injury data found"

**Solution:**
```bash
# Scrape fresh injury data
uv run walters-analyzer scrape-injuries --sport nfl

# Verify data exists
ls -l data/injuries/nfl/
```

## Test Data Files

For testing without live scraping, you can use existing snapshot:

```bash
# Check if test snapshots exist
ls -l snapshots/

# Example: Use existing snapshot
uv run python scrape_odds_mcp.py snapshots/overtime_live_text.txt
```

## Validation Checklist

After running tests, verify:

- [ ] MCP server connects successfully
- [ ] Chrome launches and navigates to overtime.ag
- [ ] Snapshots are saved to `snapshots/` directory
- [ ] Scraper extracts game data (14+ games expected)
- [ ] Data saved to `data/odds/nfl/` in JSONL, JSON, CSV formats
- [ ] Billy Walters analysis runs without errors
- [ ] Reports show edge calculations and betting signals
- [ ] Kelly sizing is calculated correctly (0.5-3% range)

## Performance Benchmarks

| Task | Expected Time | Status |
|------|---------------|--------|
| MCP connection check | < 5 seconds | ✓ |
| Navigate to overtime.ag | ~2 seconds | ✓ |
| Take snapshot | ~1 second | ✓ |
| Parse odds data | ~2 seconds | ✓ |
| Billy Walters analysis | ~5 seconds | ✓ |
| Full pipeline | < 30 seconds | ✓ |

## Next Steps After Testing

1. **Schedule Daily Runs**: Set up cron job for automatic scraping
2. **Paper Trading**: Track signals vs. outcomes for validation
3. **Backtesting**: Validate methodology with historical data
4. **Optimization**: Tune injury multipliers and position values
5. **Production**: Deploy automated betting signal system

## Support

If you encounter issues:
1. Check `logs/` directory for error messages
2. Review `CHROME_DEVTOOLS_BREAKTHROUGH.md` for technical details
3. Verify environment with: `uv run pytest tests/ -v`
4. Test individual components separately

---

**Ready to Test!** Start with Test 1 and work your way through the scenarios.
