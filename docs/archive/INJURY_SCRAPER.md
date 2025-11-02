# ESPN Injury Report Scraper

## Overview

The ESPN Injury Scraper collects player injury data for college football (NCAAF) and NFL to inform betting decisions and gate logic in your Billy Walters-style analyzer.

**Why Injuries Matter:**
- Key player absences significantly impact point spreads and totals
- Injury status (Out, Doubtful, Questionable) helps filter bad bets
- Starting QB injuries can move lines 3-7 points
- Essential gate check before placing any wager

---

## Quick Start

### Run College Football Injury Scraper

```bash
# Using CLI
uv run walters-analyzer scrape-injuries --sport cfb

# Or use command JSON
uv run walters-analyzer scrape-injuries --sport cfb --output-dir data/injuries
```

### Run NFL Injury Scraper

```bash
uv run walters-analyzer scrape-injuries --sport nfl
```

---

## How It Works

### Data Sources

The scraper targets **ESPN's injury report pages**, which aggregate:
- Official team injury reports
- Practice participation status
- Game status updates (Out, Doubtful, Questionable, Probable)
- Injury types (Knee, Ankle, Concussion, etc.)

### Parsing Strategies

The spider uses **multiple fallback strategies** for maximum reliability:

1. **JSON Extraction** (Preferred)
   - Extracts embedded structured data from ESPN's page
   - Most reliable and complete

2. **DOM Parsing** (Fallback)
   - Parses injury tables and card layouts
   - Works when JSON is unavailable

3. **Text Pattern Matching** (Last Resort)
   - Uses regex to find player names and status
   - Catches edge cases

---

## Output Format

### Data Structure

Each injury report contains:

```json
{
  "source": "espn",
  "sport": "college_football",
  "league": "NCAAF",
  "collected_at": "2025-11-01T14:30:00+00:00",
  "team": "Alabama Crimson Tide",
  "team_abbr": "ALA",
  "player_name": "Jalen Milroe",
  "position": "QB",
  "injury_status": "Questionable",
  "injury_type": "Ankle",
  "date_reported": "2025-10-30",
  "game_date": "2025-11-02",
  "opponent": "LSU Tigers",
  "notes": "Limited in practice Wednesday"
}
```

### Injury Status Values

- **Out** - Definitely not playing (Impact: 100)
- **Doubtful** - Very unlikely to play (Impact: 75)
- **Questionable** - 50/50 chance (Impact: 50)
- **Day-to-Day** - Monitoring daily (Impact: 40)
- **Probable** - Likely to play (Impact: 25)

### Output Files

Data is saved to `data/injuries/` in two formats:

- **JSONL** - Line-delimited JSON for streaming
- **Parquet** - Columnar format for analytics

Example:
```
data/injuries/injuries-20251101-143000.jsonl
data/injuries/injuries-20251101-143000.parquet
```

---

## Integration with Gates

### Gate Logic Example

Use injury data to filter bets before placing:

```python
from walters_analyzer.gates import check_injury_gate

def validate_bet(game, injuries):
    """Check if key players are out."""
    
    # Get injuries for both teams
    away_injuries = [i for i in injuries if i["team"] == game["away"]]
    home_injuries = [i for i in injuries if i["team"] == game["home"]]
    
    # Critical position checks
    for injury in away_injuries + home_injuries:
        if injury["position"] == "QB" and injury["injury_status"] in ["Out", "Doubtful"]:
            return False, f"Starting QB {injury['player_name']} is {injury['injury_status']}"
    
    # Check impact score threshold
    total_impact = sum(i.get_impact_score() for i in away_injuries + home_injuries)
    if total_impact > 150:  # Threshold for too many injuries
        return False, f"Too many key injuries (impact: {total_impact})"
    
    return True, "Injury gate passed"
```

### Pre-Run Hook Integration

Add to your `hooks/pre-run.py`:

```python
import json
from pathlib import Path

def check_injuries(card):
    """Verify fresh injury data exists."""
    
    injury_files = list(Path("data/injuries").glob("injuries-*.jsonl"))
    if not injury_files:
        print("⚠️  No injury data found. Run: uv run walters-analyzer scrape-injuries")
        return False
    
    # Use most recent file
    latest = max(injury_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest) as f:
        injuries = [json.loads(line) for line in f]
    
    print(f"✓ Loaded {len(injuries)} injury reports from {latest.name}")
    
    # Check each game in the card
    for entry in card["entries"]:
        team = entry["team"]
        team_injuries = [i for i in injuries if team.lower() in i["team"].lower()]
        
        critical = [i for i in team_injuries if i["injury_status"] in ["Out", "Doubtful"]]
        if critical:
            print(f"⚠️  {team} has {len(critical)} critical injuries:")
            for inj in critical:
                print(f"   - {inj['player_name']} ({inj['position']}): {inj['injury_status']}")
    
    return True
```

---

## Configuration

### Environment Variables

```bash
# Override default ESPN URL
ESPN_INJURY_URL=https://www.espn.com/football/college-football/injuries

# Change sport/league
ESPN_SPORT=football
ESPN_LEAGUE=college-football  # or "nfl"
```

### Custom Output Directory

```bash
uv run walters-analyzer scrape-injuries --sport cfb --output-dir custom/path
```

---

## CLI Options

```
usage: walters-analyzer scrape-injuries [-h] [--sport {nfl,cfb}] [--output-dir OUTPUT_DIR]

options:
  -h, --help            show this help message and exit
  --sport {nfl,cfb}     Sport to scrape: nfl or cfb (college football) (default: cfb)
  --output-dir OUTPUT_DIR
                        Output directory for injury data (default: data/injuries)
```

---

## Examples

### Basic Usage

```bash
# Scrape NCAAF injuries
uv run walters-analyzer scrape-injuries --sport cfb

# Scrape NFL injuries
uv run walters-analyzer scrape-injuries --sport nfl
```

### Automated Weekly Collection

Add to your workflow:

```bash
# Saturday morning - before college games
0 8 * * 6 cd /path/to/project && uv run walters-analyzer scrape-injuries --sport cfb

# Sunday morning - before NFL games
0 8 * * 0 cd /path/to/project && uv run walters-analyzer scrape-injuries --sport nfl
```

### Combine with Odds Scraping

```bash
# Scrape pregame odds
uv run walters-analyzer scrape-overtime --sport cfb

# Scrape injuries
uv run walters-analyzer scrape-injuries --sport cfb

# Run your card with both datasets
uv run walters-analyzer wk-card --file cards/wk-card-2025-11-02.json
```

---

## Debugging

### Check Snapshots

The scraper saves debugging snapshots to `snapshots/`:

```
snapshots/espn_injury_page.png    - Full page screenshot
snapshots/espn_injury_text.txt    - Raw text extraction
snapshots/espn_injury_error.png   - Error state (if failure)
```

### Enable Debug Logging

```bash
# Run with verbose Scrapy logging
scrapy crawl espn_injuries -s LOG_LEVEL=DEBUG
```

### Inspect Raw Data

```bash
# View latest injury file
cat data/injuries/injuries-*.jsonl | jq .

# Count injuries by team
cat data/injuries/injuries-*.jsonl | jq -r .team | sort | uniq -c

# Find all QB injuries
cat data/injuries/injuries-*.jsonl | jq 'select(.position=="QB")'

# Critical injuries only
cat data/injuries/injuries-*.jsonl | jq 'select(.injury_status | test("Out|Doubtful"))'
```

---

## Position Impact Guidelines

### High Impact Positions (Football)

**College Football:**
- QB (Quarterback) - 7-10 point swing
- LT (Left Tackle) - 3-4 point swing  
- MLB (Middle Linebacker) - 2-3 point swing
- CB (Cornerback) - 2-3 point swing

**NFL:**
- QB - 5-7 point swing
- LT/RT - 2-3 point swing
- EDGE/DE - 2-3 point swing
- CB1 - 2-3 point swing

### Sample Gate Thresholds

```python
CRITICAL_POSITIONS = ["QB", "LT", "RT", "MLB", "CB"]

def is_bet_compromised(injuries):
    """Check if injuries make bet too risky."""
    
    for injury in injuries:
        # Auto-reject if starting QB is out
        if injury["position"] == "QB" and injury["injury_status"] == "Out":
            return True
        
        # Multiple critical injuries
        critical_count = len([
            i for i in injuries 
            if i["position"] in CRITICAL_POSITIONS 
            and i["injury_status"] in ["Out", "Doubtful"]
        ])
        
        if critical_count >= 3:
            return True
    
    return False
```

---

## Troubleshooting

### No Injuries Found

**Issue:** Scraper completes but finds 0 injuries

**Solutions:**
1. Check ESPN's page structure hasn't changed
2. Review `snapshots/espn_injury_page.png` to verify content loaded
3. ESPN may not have injury data yet early in the week
4. Try running on Wednesday+ when official reports are filed

### Playwright Not Installed

**Issue:** `playwright install` required

```bash
playwright install chromium
```

### Rate Limiting

**Issue:** ESPN blocking requests

**Solutions:**
- Enable `AUTOTHROTTLE` (already on by default)
- Add delays between requests
- Use proxy if needed:

```bash
export ESPN_PROXY=http://proxy:port
```

---

## Next Steps

1. **Weather Scraper** - Outdoor game conditions
2. **Steam Tracker** - Line movement detection
3. **CLV Calculator** - Compare open vs close
4. **Backtesting Engine** - Historical performance

Let me know which you'd like to tackle next, partner! 🎯

