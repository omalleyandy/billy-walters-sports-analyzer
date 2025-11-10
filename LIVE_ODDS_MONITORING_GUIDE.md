# Live Odds Monitoring System - User Guide

## Overview

Automated system for tracking NFL betting lines in real-time, detecting sharp action, and capturing line movements. Built for the Billy Walters betting methodology.

## Quick Start

### Get Instant Odds (One-Time Check)

```bash
/in-play-matchup-now Steelers Chargers
```

**Output:**
- Current spread, total, moneyline
- Line movements since last check
- Timestamp and API quota

**Use Cases:**
- Quick check before kickoff
- Verify closing line
- Spot check during commercial breaks

### Start Continuous Monitoring

```bash
/in-play-matchup-interval Chiefs Broncos
```

**What Happens:**
- Checks odds every 15 minutes (default)
- Alerts on movements ≥ 0.5 points
- Saves complete history
- Runs until Ctrl+C

**Use Cases:**
- Pre-game sharp money tracking (start 4 hours before)
- Live game monitoring
- Waiting for optimal number (3, 7, 10)

### Scrape All Games

```bash
/scrape-live-odds
```

**Output:**
- All 15 upcoming NFL games
- Full odds (spread, total, ML)
- Line movement detection
- Saved in multiple formats

---

## Features

### 1. Real-Time Odds Tracking

**Data Source**: The Odds API
- Professional sportsbooks (FanDuel, DraftKings, etc.)
- Updates every minute
- Multiple market types
- 500 API calls/month (free tier)

**Markets Tracked**:
- Spreads with prices
- Totals (Over/Under)
- Moneylines

### 2. Line Movement Detection

**Threshold**: ±0.5 points triggers alert

**Spread Movements**:
- Toward favorite = Public money
- Toward dog = Sharp money
- Example: LAC -4.5 → -3.5 (sharp on Steelers)

**Total Movements**:
- UP = Over action or weather
- DOWN = Under action or injuries
- Example: 36.5 → 33.5 (major under movement)

### 3. Historical Tracking

**Storage Location**:
```
data/odds/monitoring/[team1]_vs_[team2].json
```

**Includes**:
- Every odds snapshot
- Timestamps
- Movement calculations
- Complete audit trail

**Use For**:
- Post-game CLV analysis
- Identifying sharp patterns
- Backtesting strategies

---

## Command Reference

### `/in-play-matchup-now`

**Syntax**:
```bash
/in-play-matchup-now [team1] [team2]
```

**Examples**:
```bash
/in-play-matchup-now Steelers Chargers
/in-play-matchup-now KC Denver
/in-play-matchup-now Lions Eagles
```

**Options**:
- Team names can be partial ("Chiefs" or "KC")
- Order doesn't matter
- Case insensitive

**Output Format**:
```
INSTANT ODDS CHECK - STEELERS vs CHARGERS
Current odds as of 2025-11-09 18:35:25:

Pittsburgh Steelers @ Los Angeles Chargers
  Spread: +3.5 (-120) / -3.5 (-110)
  Total: O/U 33.5 (-110/-120)
  ML: +165 / -215

Line movement since last check:
  Total: -3.0 (significant DOWN movement)
```

---

### `/in-play-matchup-interval`

**Syntax**:
```bash
/in-play-matchup-interval [team1] [team2] [interval_minutes]
```

**Examples**:
```bash
# Default 15-minute intervals
/in-play-matchup-interval Chiefs Broncos

# Custom 5-minute intervals (more aggressive)
/in-play-matchup-interval Eagles Packers 5

# Custom 30-minute intervals (conservative)
/in-play-matchup-interval Lions Eagles 30
```

**Options**:
- `interval_minutes` - Time between checks (default: 15)
- Shorter intervals = more API calls
- Press Ctrl+C to stop gracefully

**Output Format**:
```
LIVE ODDS MONITOR - CHIEFS vs BRONCOS
Interval: 900 seconds (15 minutes)
Press Ctrl+C to stop

[2025-11-09 18:40:00] Check #1
[API] Fetched 15 games (quota: 380/500)

Kansas City Chiefs @ Denver Broncos
  Spread: -3.5 (-110) / +3.5 (-110)
  Total: O/U 44.5 (-105/-115)
  ML: -190 / +160

Next check in 900 seconds...

[2025-11-09 18:55:00] Check #2
[ALERT] SIGNIFICANT LINE MOVEMENT DETECTED!
  Spread: +0.5 (toward dog)
```

---

### `/scrape-live-odds`

**Syntax**:
```bash
/scrape-live-odds
```

**No Arguments Needed** - Scrapes all games

**Output**:
- 15 upcoming NFL games
- Current odds for each
- Line movement report
- Files saved to `data/odds/nfl/`

**File Formats**:
- `.json` - Full structured data
- `.jsonl` - One game per line
- `.csv` - Spreadsheet compatible

---

## Billy Walters Strategies

### 1. Closing Line Value (CLV)

**Goal**: Beat the closing line

**Strategy**:
1. Monitor game starting 4 hours before kickoff
2. Track line movements
3. Enter when you get your number
4. Compare entry to closing line (kickoff)

**Example**:
- You want Chiefs -3
- Line opens at -3.5
- Monitor every 15 minutes
- Line moves to -3 at 2 hours before kickoff
- You bet Chiefs -3
- Closing line: Chiefs -3.5
- CLV = +0.5 points (excellent)

### 2. Reverse Line Movement

**What It Means**: Line moves opposite to public betting percentages

**Example**:
- 70% of bets on Chargers -4.5
- Line moves to Chargers -3.5
- Indicates sharp money on Steelers
- Bet Steelers +3.5

**How to Detect**:
```bash
# Monitor every 15 minutes
/in-play-matchup-interval Steelers Chargers

# Watch for alerts
[ALERT] Spread: +1.0 (toward dog)
```

### 3. Key Number Hunting

**Key Numbers**: 3, 7, 10, 14 (most common NFL margins)

**Strategy**:
1. Target game with spread near key number
2. Monitor for line to cross the key
3. Take the better side of the key

**Example**:
- Line: Ravens -6.5
- Monitor for movement to -7
- If line goes to -7, bet Browns +7
- Now you have the key number

### 4. Steam Move Following

**What Is Steam**: Rapid line movement from sharp action

**How to Catch**:
1. Monitor multiple games
2. Watch for 1+ point move in < 15 minutes
3. Follow the steam immediately

**Tools**:
```bash
# Monitor multiple games in parallel
/in-play-matchup-interval Chiefs Broncos &
/in-play-matchup-interval Lions Eagles &
/in-play-matchup-interval Ravens Browns &
```

---

## API Usage & Limits

### The Odds API

**Free Tier**:
- 500 requests/month
- Resets monthly
- Real-time odds updates

**Current Usage**: 378/500 (122 remaining)

**Cost Per Operation**:
- `/in-play-matchup-now` = 1 call
- `/scrape-live-odds` = 1 call
- Monitoring at 15-min intervals = 4 calls/hour

**Budget Example**:
- Monitor 1 game for 4 hours = 16 calls
- Monitor 3 games for 4 hours = 48 calls
- Daily scrapes (4x/day) = 120 calls/month
- Balance = 332 calls for monitoring

### Upgrade Options

If you need more calls:
- **$29/month** = 5,000 requests
- **$79/month** = 15,000 requests
- **Custom** = Contact theoddsapi.com

---

## File Organization

### Generated Files

```
data/
├── odds/
│   ├── nfl/
│   │   ├── nfl-odds-20251109-182739.json    # Full scrapes
│   │   ├── nfl-odds-20251109-182739.jsonl   # Line-by-line
│   │   └── nfl-odds-20251109-182739.csv     # Spreadsheet
│   └── monitoring/
│       ├── Chiefs_vs_Broncos.json           # Interval tracking
│       ├── Lions_vs_Eagles.json
│       └── Steelers_vs_Chargers.json
```

### Data Retention

**Full Scrapes**: Keep forever for backtesting

**Monitoring Files**: Keep for CLV analysis, then archive after season

**Recommended Cleanup**:
```bash
# Archive old monitoring data
mv data/odds/monitoring/*.json data/odds/archive/2024/

# Keep full scrapes
# (Used for line movement analysis)
```

---

## Troubleshooting

### "Game not found"

**Cause**: Team name doesn't match

**Solution**: Use partial names
```bash
# Instead of "New England Patriots"
/in-play-matchup-now Patriots Jets

# Instead of "Kansas City Chiefs"
/in-play-matchup-now KC Denver
```

### "API quota exceeded"

**Cause**: Used all 500 monthly calls

**Solutions**:
1. Wait for monthly reset
2. Increase monitoring intervals (15min → 30min)
3. Upgrade to paid plan
4. Prioritize critical games only

### "No significant movement"

**Cause**: Lines are stable (normal)

**Not an Error**: Most lines don't move much

**What to Do**:
- Keep monitoring
- Movements happen closer to kickoff
- Sharp action often comes 2-4 hours before game

---

## Best Practices

### Pre-Game Monitoring

**4 Hours Before Kickoff**:
```bash
/in-play-matchup-interval Chiefs Broncos 15
```

**Key Objectives**:
- Identify sharp action
- Wait for your number
- Track CLV opportunity

### Live Game Monitoring

**During Game**:
```bash
/in-play-matchup-interval Lions Eagles 5
```

**Key Objectives**:
- Live betting opportunities
- Quarter-by-quarter movements
- Injury impact detection

### Post-Game Analysis

**After Game**:
1. Review monitoring file
2. Calculate CLV for your bets
3. Identify patterns
4. Improve next time

```bash
# Review complete history
cat data/odds/monitoring/Chiefs_vs_Broncos.json
```

---

## Next Steps

### Integration with Billy Walters System

1. **Power Ratings** - Compare odds to your power ratings
2. **Edge Detection** - Find games with 3.5+ point edge
3. **Kelly Sizing** - Calculate optimal bet size
4. **CLV Tracking** - Measure long-term performance

### Automation

Consider automating:
- Pre-game monitoring (start 4 hours before)
- Alert notifications (Telegram, email)
- CLV calculation (compare entry to close)
- Daily reports (best opportunities)

---

## Support

**Documentation**: This guide
**Commands**: `/help` for all slash commands
**Issues**: Check `CLAUDE.md` for troubleshooting
**API Status**: https://theoddsapi.com/status

---

## Summary

You now have a professional-grade live odds monitoring system:

✅ Instant odds checks on demand
✅ Automated 15-minute interval tracking
✅ Line movement detection and alerts
✅ Complete historical tracking
✅ Billy Walters methodology integration
✅ API-based (no browser automation)

**Next**: Try monitoring tonight's games and tracking line movements!
