# Action Network Data Collection Guide

## Overview

The Action Network scraper collects real-time betting odds with **public vs sharp money percentages** - a critical component of the Billy Walters methodology.

### What We Collect

| Data Point | Description | Billy Walters Use |
|------------|-------------|-------------------|
| Consensus Spread | Aggregated line across books | Compare to our power ratings |
| Tickets % | % of total bets placed | Public betting indicator |
| Money % | % of actual dollars wagered | Sharp money indicator |
| Opening Line | Line when market opened | Track line movement |
| Moneyline | Win odds for each team | Alternative betting options |
| Totals | Over/under points | Secondary betting market |

### Sharp Money Detection

**Billy Walters Principle**: "When tickets and money diverge significantly, follow the money."

- **Tickets > Money** = Public side (fade this)
- **Money > Tickets** = Sharp side (follow this)

#### League-Specific Thresholds

**CRITICAL**: NFL and NCAAF markets have different liquidity levels, requiring separate divergence thresholds:

| Signal Strength | NFL Threshold | NCAAF Threshold | Meaning |
|-----------------|---------------|-----------------|----------|
| **Moderate** | 5+ divergence | 20+ divergence | Worth monitoring |
| **Strong** | 10+ divergence | 30+ divergence | Significant signal |
| **Very Strong** | 15+ divergence | 40+ divergence | High confidence |

**Why the difference?**
- **NFL**: Highly efficient market with massive betting volume. Even 5-point divergence is meaningful.
- **NCAAF**: Lower betting volume, less efficient market. Games routinely show 20-40+ divergence due to lopsided action on smaller games.

**Example**: A +25 divergence in NFL would be extremely rare and very strong. The same +25 divergence in NCAAF is moderate - just means sharps are betting one side in a low-volume game.

---

## Quick Start

### Single Scrape (Most Common)

```powershell
# From project root
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Quick scrape
python collect_action_network.py

# Check status
python collect_action_network.py --status
```

### View Latest Sharp Plays

```powershell
# PowerShell one-liner to view sharp plays
$data = Get-Content .\data\action_network\nfl_odds_latest.json | ConvertFrom-Json
$data.sharp_plays | Format-Table game, pick, divergence, signal
```

### Continuous Monitoring

```powershell
# Run continuous collection (every hour)
python collect_action_network.py --watch

# Or with custom interval (every 30 minutes)
python src\walters_analyzer\scrapers\action_network_collector.py --continuous --interval 30
```

---

## Full CLI Reference

```powershell
# Single scrape
python src\walters_analyzer\scrapers\action_network_collector.py --once

# Continuous collection (default 4 hours)
python src\walters_analyzer\scrapers\action_network_collector.py --continuous

# Custom interval (2 hours = 120 minutes)
python src\walters_analyzer\scrapers\action_network_collector.py --continuous --interval 120

# Show status
python src\walters_analyzer\scrapers\action_network_collector.py --status

# Cleanup old files (keep 14 days)
python src\walters_analyzer\scrapers\action_network_collector.py --cleanup --days 14

# Show browser (for debugging)
python src\walters_analyzer\scrapers\action_network_collector.py --once --no-headless
```

---

## Data Files

### Location
```
data/action_network/
├── nfl_odds_latest.json          # Most recent NFL data
├── nfl_odds_week13_20251126_*.json  # Timestamped archives
├── ncaaf_odds_latest.json        # Most recent NCAAF data
└── .collector_state.json         # Collection state tracking
```

### JSON Structure

```json
{
  "source": "action_network",
  "league": "nfl",
  "week": 13,
  "scraped_at": "2025-11-26T12:00:00",
  "game_count": 16,
  "divergence_thresholds": {
    "moderate": 5,
    "strong": 10,
    "very_strong": 15
  },
  "games": [
    {
      "game_id": 256733,
      "away_team": "GB",
      "home_team": "DET",
      "spread": {
        "home": {"value": -2.5, "odds": -115, "tickets_pct": 52, "money_pct": 44},
        "away": {"value": 2.5, "odds": -105, "tickets_pct": 48, "money_pct": 56}
      },
      "opening_spread": -2.5,
      "line_movement": 0,
      "sharp_side": "GB"
    }
  ],
  "sharp_plays": [
    {
      "game": "GB @ DET",
      "pick": "GB +2.5",
      "tickets_pct": 48,
      "money_pct": 56,
      "divergence": 8,
      "signal": "SHARP",
      "signal_strength": "MODERATE"
    }
  ]
}
```

---

## Windows Task Scheduler Setup

For automated periodic collection:

### 1. Create Batch File

Save as `collect_action_network.bat`:
```batch
@echo off
cd /d C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
call .venv\Scripts\activate
python collect_action_network.py >> logs\action_network_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1
```

### 2. Schedule Task

```powershell
# Create scheduled task (runs every 4 hours during betting windows)
$action = New-ScheduledTaskAction -Execute "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\collect_action_network.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "8:00AM" -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration (New-TimeSpan -Hours 16)
Register-ScheduledTask -TaskName "ActionNetworkCollector" -Action $action -Trigger $trigger -Description "Collect Action Network betting data"
```

### Recommended Schedule

| Day | Times | Reason |
|-----|-------|--------|
| Tuesday | 8am, 12pm | Early lines posted |
| Wednesday | 8am, 12pm, 4pm | Line movement |
| Thursday | 8am, 12pm, 4pm | TNF prep |
| Friday | 8am, 12pm | Line shopping |
| Saturday | 8am, 12pm, 4pm, 8pm | Final moves |
| Sunday | 8am, 12pm, 4pm | Game day |

---

## Troubleshooting

### CloudFlare Blocking

If scrapes fail with "CloudFlare challenge detected":

1. **Try non-headless mode**: `--no-headless`
2. **Increase wait time**: Edit scraper to add longer delays
3. **Manual fallback**: Use browser DevTools to capture `__NEXT_DATA__`

### No Games Found

If scrape returns 0 games:

1. Check if Action Network has games listed (off-season?)
2. Try with `--no-headless` to see what's happening
3. Check `data/action_network/error_screenshot.png`

### Import Errors

```powershell
# Ensure playwright is installed
pip install playwright
playwright install chromium
```

---

## Integration with Billy Walters System

### Recommended Workflow

1. **Morning (8am)**: Collect fresh odds
2. **Analyze edges**: Combine with power ratings
3. **Check sharp signals**: Review divergence plays
4. **Track CLV**: Record any bets placed
5. **Pre-game (2 hours before)**: Final line check

### Combining with Power Ratings

```python
from walters_analyzer.scrapers.action_network_parser import ActionNetworkParser
from walters_analyzer.core.edge_calculator import EdgeCalculator

# Load Action Network data
parser = ActionNetworkParser()
games = parser.parse_file('data/action_network/nfl_odds_latest.json')

# For each game, calculate edge
for game in games:
    # Get our power rating prediction
    our_line = power_ratings.predict_spread(game.away_team, game.home_team)
    
    # Calculate edge
    edge = our_line - game.spread_line
    
    # Boost confidence if sharps agree
    if game.sharp_spread_side and edge > 0:
        if game.sharp_spread_side == game.home_team and our_line < 0:
            confidence_boost = 1.2  # Sharps confirm our side
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `action_network_scraper.py` | Core Playwright scraper |
| `action_network_collector.py` | Automated collection manager |
| `action_network_parser.py` | JSON data parser |
| `collect_action_network.py` | Quick CLI script |

---

## Next Steps

After setting up collection:

1. ✅ **Step 1: Automate collection** (DONE)
2. ⬜ **Step 2: Integrate with edge calculator** - Combine sharp signals with power ratings
3. ⬜ **Step 3: Track CLV** - Record bets and measure closing line value
4. ⬜ **Step 4: Build historical database** - Backtest sharp money signals
