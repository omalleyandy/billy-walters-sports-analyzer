# Quick Start: Market Monitoring

Get started with live market data and sharp money detection in 5 minutes.

---

## Prerequisites

1. Python 3.9+ installed
2. Project set up with `uv`
3. The Odds API key (free tier is fine)

---

## Step 1: Get The Odds API Key

1. Go to https://the-odds-api.com/
2. Click "Sign Up" (free tier: 500 requests/month)
3. Confirm your email
4. Copy your API key from the dashboard

---

## Step 2: Configure Environment

Create `.env` file in project root:

```bash
# Copy the example
cp .env.example .env

# Edit .env and add your API key
# Windows:
notepad .env

# Or manually add this line:
ODDS_API_KEY=your_api_key_here
```

---

## Step 3: Test the Connection

Run the test script to verify everything is working:

```bash
# Test API connection
uv run python examples/test_market_monitor.py
```

This will:
- ✅ Test API connection
- ✅ Fetch sample odds data
- ✅ Show sharp vs public book lines
- ✅ (Optional) Run 2-minute monitoring test

---

## Step 4: Start Monitoring

### Test Mode (Verify Setup)

```bash
uv run walters-analyzer monitor-sharp --test
```

This will:
- Check your API key
- Fetch current NFL games
- Show a sample game
- Confirm everything is ready

### Monitor NFL Games

```bash
# Monitor for 2 hours
uv run walters-analyzer monitor-sharp --sport nfl --duration 120
```

### Monitor with Custom Settings

```bash
# Check every 15 seconds, monitor for 4 hours
uv run walters-analyzer monitor-sharp --sport nfl --interval 15 --duration 240
```

### Monitor Other Sports

```bash
# College Football
uv run walters-analyzer monitor-sharp --sport ncaaf

# NBA
uv run walters-analyzer monitor-sharp --sport nba

# MLB
uv run walters-analyzer monitor-sharp --sport mlb
```

---

## Step 5: Understanding Alerts

When sharp money is detected, you'll see alerts like this:

```
================================================================================
🚨 SHARP MONEY ALERT
================================================================================
Game:      Kansas City Chiefs @ Buffalo Bills
Direction: SHARP MONEY ON BILLS (line moved toward Chiefs)
Sharp Line Movement:  +1.2 points
Public Line Movement: +0.3 points
Divergence: +0.9 points
Current Sharp Line: -2.5
Confidence: 171%
Sharp Books: Pinnacle, Circa
Public Books: DraftKings, FanDuel, BetMGM
Time: 2025-11-07T14:30:00Z
================================================================================
```

**What this means:**
- Sharp books moved the line 1.2 points toward Bills
- Public books only moved 0.3 points
- This suggests sharp money is on the Bills
- The divergence (0.9 points) indicates market inefficiency

**Billy Walters Strategy:**
- Markets underreact to information by ~15%
- When sharp books move but public books don't = edge
- Confidence > 100% = movement exceeded alert threshold

---

## Step 6: Customize Settings

### Option 1: Environment Variables

Edit `.env`:

```bash
# Change alert threshold to 0.5 points
SKILLS__MARKET_ANALYSIS__ALERT_THRESHOLD=0.5

# Check every 15 seconds
SKILLS__MARKET_ANALYSIS__MONITOR_INTERVAL=15

# Add more sharp books
SKILLS__MARKET_ANALYSIS__SHARP_BOOKS=["Pinnacle", "Circa", "Bookmaker", "CRIS"]
```

### Option 2: Config File

Edit `.claude/claude-desktop-config.json`:

```json
{
  "skills": {
    "market-analysis": {
      "enabled": true,
      "config": {
        "sharp_books": ["Pinnacle", "Circa", "Bookmaker"],
        "public_books": ["DraftKings", "FanDuel", "BetMGM", "Caesars"],
        "alert_threshold": 0.5,
        "monitor_interval": 15
      }
    }
  }
}
```

---

## Common Use Cases

### 1. Pre-Game Monitoring (4 hours before kickoff)

```bash
# Start monitoring 4 hours before games
uv run walters-analyzer monitor-sharp --sport nfl --duration 240
```

Look for:
- Late injury news causing line movement
- Sharp money coming in on underdogs
- Reverse line movement (public on favorite, line moves toward underdog)

### 2. Game Day Monitoring

```bash
# Monitor all day on Sunday
uv run walters-analyzer monitor-sharp --sport nfl --duration 480
```

### 3. Specific Game Focus

```bash
# Monitor a single game (requires game ID from The Odds API)
uv run walters-analyzer monitor-sharp --game-id <game_id> --duration 120
```

---

## Alert Log

All alerts are saved to `logs/alerts.log` in JSON format:

```bash
# View recent alerts
tail -f logs/alerts.log

# Count alerts
cat logs/alerts.log | wc -l

# Filter by team
cat logs/alerts.log | grep "Chiefs"
```

---

## Interpreting Results

### High-Confidence Signals (> 150%)

- **Strong edge detected**
- Line movement significantly exceeds threshold
- Sharp books moving aggressively
- Action: Consider betting

### Medium-Confidence Signals (100-150%)

- **Moderate edge**
- Line movement at or above threshold
- Potential value
- Action: Wait for confirmation or bet small

### Low-Confidence Signals (< 100%)

- **Minor movement**
- Below alert threshold (shouldn't trigger)
- Action: Monitor only

---

## Troubleshooting

### "No odds data received"

**Causes:**
1. Invalid API key
2. No active games for that sport
3. API rate limit reached

**Solutions:**
- Check your API key in `.env`
- Verify sport has games today
- Check remaining quota at https://the-odds-api.com/account/

### "No alerts detected"

**This is normal!**
- Line movements take time to develop
- Sharp money doesn't appear every check
- Try monitoring during:
  - Friday/Saturday (NFL lines released)
  - 2-4 hours before game time (sharp money arrival)
  - After breaking injury news

### API Rate Limits

Free tier: 500 requests/month

**Calculate usage:**
- 1 check = 1 request
- Checking every 30 seconds = 120 requests/hour
- 2-hour session = 240 requests
- ~2 sessions per month on free tier

**Tip:** Use longer intervals (60 seconds) to conserve quota

---

## Next Steps

1. **Backtest your strategy**
   - Log alerts for a week
   - Track which alerts led to winning bets
   - Refine alert threshold

2. **Integrate with Billy Walters valuation**
   - Combine injury analysis with market monitoring
   - Cross-reference line movements with injury reports
   - Calculate true edge using both methods

3. **Automate notifications**
   - Set up webhook alerts (Discord, Slack, etc.)
   - Get real-time notifications on your phone
   - Never miss a sharp money signal

4. **Scale up**
   - Upgrade to paid tier for more requests
   - Monitor multiple sports simultaneously
   - Track closing line value (CLV)

---

## Pro Tips

1. **Best times to monitor:**
   - NFL: Thursday-Saturday (opening lines)
   - NFL: Sunday 9am-1pm ET (late sharp money)
   - NCAAF: Friday-Saturday mornings

2. **Focus on sharp books:**
   - Pinnacle moves fastest
   - Circa has low limits but sharp action
   - When both agree = strong signal

3. **Ignore small movements:**
   - < 0.5 points = noise
   - 0.5-1.0 points = minor edge
   - > 1.0 points = significant edge

4. **Track your results:**
   - Log every alert and bet
   - Calculate your ROI on alerts
   - Adjust threshold based on performance

---

## Questions?

Check the full documentation:
- `MARKET_DATA_INTEGRATION_GUIDE.md` - Complete integration guide
- `BILLY_WALTERS_METHODOLOGY.md` - Injury valuation methodology
- `CLAUDE.md` - Project commands and hooks

Or run:
```bash
uv run walters-analyzer monitor-sharp --help
```
