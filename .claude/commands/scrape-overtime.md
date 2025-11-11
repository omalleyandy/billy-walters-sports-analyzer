Scrape live odds from Overtime.ag for NFL games.

Usage: /scrape-overtime [options]

Examples:
- /scrape-overtime (default: headless, with conversion)
- /scrape-overtime --visible (show browser)
- /scrape-overtime --no-proxy (skip proxy, current working config)

This command will:
1. Launch Playwright browser (Chromium)
2. Authenticate with Overtime.ag credentials
3. Navigate to NFL betting section
4. Extract all available game lines
5. Convert to Billy Walters format
6. Optionally save to database

Overtime.ag Technical Details:
- Platform: AngularJS (vanilla JavaScript)
- Real-time: WebSocket (wss://ws.ticosports.com/signalr)
- Security: CloudFlare DDoS protection
- Authentication: OV_CUSTOMER_ID + OV_PASSWORD

Critical Selectors (for maintenance):
- Login button: 'a.btn-signup' (use JavaScript click, element hidden)
- NFL section: 'label' containing "NFL-Game/1H/2H/Qrts"
- Team names: 'h4' with pattern '{rotation_number} {team_name}'
- Betting buttons: 'button[ng-click*="SendLineToWager"]'
- Account info: '[href*="dailyFigures"]'

Data Extracted:
- Current spread (home/away)
- Current total (over/under)
- Moneyline odds (home/away)
- Game time
- Rotation numbers
- Multiple sportsbooks (if available)

Billy Walters Format Conversion:
- Converts rotation numbers to team names
- Standardizes odds format (American to decimal)
- Calculates implied probabilities
- Extracts opening lines (if available)
- Tracks line movements

Optimal Scraping Schedule:
- Tuesday-Wednesday: New week lines post after MNF
- Thursday morning: Fresh lines before TNF
- AVOID Sunday: Games in progress, lines down

Output Files:
1. Raw format: output/overtime_nfl_raw_TIMESTAMP.json
2. Billy Walters format: output/overtime_nfl_walters_TIMESTAMP.json
3. Database: odds table (if --save-db flag)

Example Output (Billy Walters Format):
```json
{
  "scraped_at": "2025-11-13T14:30:00",
  "week": 11,
  "sport": "NFL",
  "games": [
    {
      "game_id": "BUF_KC_2025_W11",
      "home_team": "Kansas City Chiefs",
      "away_team": "Buffalo Bills",
      "game_time": "2025-11-17T13:00:00",
      "spread": {
        "home": -2.5,
        "away": 2.5,
        "juice": -110
      },
      "total": {
        "over": 47.5,
        "under": 47.5,
        "juice": -110
      },
      "moneyline": {
        "home": -135,
        "away": 115
      },
      "opening_lines": {
        "spread": -3.5,
        "total": 48.5
      },
      "line_movement": {
        "spread_change": 1.0,
        "total_change": -1.0
      }
    }
  ]
}
```

Troubleshooting:
- Login fails: Update credentials in .env (OV_CUSTOMER_ID, OV_PASSWORD)
- 0 games found: Run Tuesday-Thursday (lines down during games)
- Proxy errors: Use --no-proxy flag (current working state)
- Windows Unicode errors: Output cleaned automatically

Command Options:
--headless: Run browser in background (default: True)
--convert: Convert to Billy Walters format (default: True)
--save-db: Save to database (default: False)
--proxy "": Skip proxy (recommended, default)
--output DIR: Custom output directory

Required Environment Variables:
- OV_CUSTOMER_ID (from .env)
- OV_PASSWORD (from .env)

Integration:
- Step 6 in Billy Walters data collection workflow
- Runs after injuries and weather
- Feeds into edge detection analysis
- Critical for market line comparison
