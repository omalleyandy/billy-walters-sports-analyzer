Scrape current live odds from The Odds API for all NFL games.

This command fetches the latest betting odds (spread, total, moneyline) for all upcoming NFL games using The Odds API - fast, reliable, no browser automation needed.

## What This Does

1. **Fetches live odds** - Queries The Odds API for current NFL lines
2. **Extracts all markets** - Spreads, totals, and moneylines
3. **Detects movements** - Compares to previous scrape
4. **Saves multiple formats** - JSONL, JSON, and CSV
5. **Displays summary** - Shows all games with current odds

## Output Location

Data is saved to:
- NFL: `data/odds/nfl/nfl-odds-[timestamp].json`
- NCAAF: `data/odds/ncaaf/ncaaf-odds-[timestamp].json`

## What Gets Scraped

For each game:
- **Teams**: Away and home team names
- **Rotation Numbers**: Standard betting identifiers
- **Spread**: Point spread lines and prices (+/-110 typical)
- **Total**: Over/Under lines and prices
- **Moneyline**: Win odds for each team
- **Game Info**: Date, time, event details

## Quality Checks

After scraping, automatic validation checks:
- ✅ All required fields present
- ✅ Spread lines are inverse (+9.0 / -9.0)
- ✅ Total lines match (O/U same number)
- ✅ Prices are reasonable (-500 to +500 for spreads)
- ✅ No missing or null critical data
- ✅ Proper timestamp and rotation number format

## Usage Examples

```bash
# Simple: Just scrape current odds
/scrape-live-odds

# View validation report after scraping
uv run python src/walters_analyzer/validate_odds.py --latest

# Export to specific format
# (CSV format is automatically created)
```

## Behind the Scenes

Uses **The Odds API**:
- Official sports odds data provider
- Real-time updates from multiple sportsbooks
- Clean, validated data structure
- 500 API calls per month (125 remaining)
- No browser automation needed

## Troubleshooting

If scraping fails:
1. Check ODDS_API_KEY is set in environment
2. Verify internet connection
3. Check API quota (500 calls/month)
4. Visit theoddsapi.com to check status

## Related Commands

- `/in-play-matchup-now` - Get instant odds for specific matchup
- `/in-play-matchup-interval` - Monitor matchup every 15 minutes
- `/analyze-matchup` - Deep dive Billy Walters analysis
- `/current-week` - Check what NFL week we're in

## Notes

- API limited to 500 calls/month (free tier)
- Each scrape uses 1 API call
- Data is for research and analysis only
- Odds from multiple sharp and public books

Execute:
```bash
uv run python scrape_odds_api.py
```
