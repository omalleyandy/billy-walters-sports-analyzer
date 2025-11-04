# Quick Guide: Viewing Overtime.ag Odds

## 🚀 Quick Commands

### View All NFL Games
```bash
uv run walters-analyzer view-odds --sport nfl
```

### View Today's Games
```bash
uv run walters-analyzer view-odds --today
```

### View Upcoming Games (Next 7 Days)
```bash
uv run walters-analyzer view-odds --upcoming
```

### Search for a Specific Team
```bash
uv run walters-analyzer view-odds --team "Cowboys"
uv run walters-analyzer view-odds --team "Cardinals"
```

### Compare Lines for a Team
```bash
uv run walters-analyzer view-odds --compare "Cowboys"
```

### View Summary
```bash
uv run walters-analyzer view-odds --summary
```

---

## 📋 All Available Commands

### Basic Viewing

```bash
# View all scraped games (latest file)
uv run walters-analyzer view-odds

# View only NFL games
uv run walters-analyzer view-odds --sport nfl

# View only College Football games
uv run walters-analyzer view-odds --sport college_football

# View specific data file
uv run walters-analyzer view-odds --file data/overtime_live/overtime-live-20251103-120640.jsonl
```

### Filtering by Date

```bash
# Today's games
uv run walters-analyzer view-odds --today

# Upcoming games (next 7 days)
uv run walters-analyzer view-odds --upcoming

# Upcoming games (next 3 days)
uv run walters-analyzer view-odds --upcoming 3

# Specific date
uv run walters-analyzer view-odds --date 2025-11-03
```

### Filtering by Team

```bash
# Search by team name (partial match, case-insensitive)
uv run walters-analyzer view-odds --team "Arizona"
uv run walters-analyzer view-odds --team "Cardinals"
uv run walters-analyzer view-odds --team "Cowboys"

# Combine with sport filter
uv run walters-analyzer view-odds --sport nfl --team "Cowboys"

# Combine with date filter
uv run walters-analyzer view-odds --today --team "Cardinals"
```

### Analysis & Comparison

```bash
# Compare betting lines for a team across games
uv run walters-analyzer view-odds --compare "Cowboys"
uv run walters-analyzer view-odds --compare "Arizona Cardinals"

# Show summary statistics
uv run walters-analyzer view-odds --summary
```

### Output Formats

```bash
# Brief output (no detailed odds)
uv run walters-analyzer view-odds --brief

# Export to CSV
uv run walters-analyzer view-odds --sport nfl --export nfl_odds.csv

# Export filtered results
uv run walters-analyzer view-odds --team "Cowboys" --export cowboys_odds.csv
```

---

## 🎯 Common Use Cases

### Scenario 1: Check Today's NFL Games
```bash
uv run walters-analyzer view-odds --sport nfl --today
```

**Output:**
```
📂 Loaded 15 games from overtime-live-20251103-120640.jsonl

📅 Today's games:

Found 1 game(s):

================================================================================
🏈 ARIZONA CARDINALS @ DALLAS COWBOYS
   Rotation: 475-476
   📅 2025-11-03 at 8:15 PM ET

   📊 SPREAD:
      ARIZONA CARDINALS               +3.5  (-113)
      DALLAS COWBOYS                  -3.5  (-107)

   🎯 TOTAL:
      OVER                            54.0  (-103)
      UNDER                           54.0  (-117)
```

---

### Scenario 2: Find All Games for Your Team
```bash
uv run walters-analyzer view-odds --team "Cardinals" --upcoming 14
```

**Shows:** All Cardinals games in the next 2 weeks with betting lines

---

### Scenario 3: Compare Line Movement (if you scraped multiple times)
```bash
uv run walters-analyzer view-odds --compare "Cowboys"
```

**Output:**
```
📈 LINE COMPARISON FOR 'COWBOYS':
================================================================================
2025-11-03 8:15 PM ET    | vs ARIZONA CARDINALS      | -3.5 (-107)
2025-11-10 1:00 PM ET    | @ PHILADELPHIA EAGLES     | +6.5 (-110)
2025-11-17 4:25 PM ET    | vs HOUSTON TEXANS         | -2.5 (-115)
```

---

### Scenario 4: Export to Spreadsheet
```bash
uv run walters-analyzer view-odds --sport nfl --upcoming 7 --export this_week_nfl.csv
```

**Result:** CSV file with all NFL games this week, ready for Excel/Google Sheets

---

## 📊 Output Explanation

### Spread Display
```
📊 SPREAD:
   ARIZONA CARDINALS               +3.5  (-113)
   DALLAS COWBOYS                  -3.5  (-107)
```

- **+3.5**: Cardinals are 3.5-point underdogs
- **-113**: You need to bet $113 to win $100 (11.3% juice)
- **-3.5**: Cowboys are 3.5-point favorites
- **-107**: You need to bet $107 to win $100

### Total Display
```
🎯 TOTAL:
   OVER                            54.0  (-103)
   UNDER                           54.0  (-117)
```

- **OVER 54.0**: Bet on combined score > 54 points
- **UNDER 54.0**: Bet on combined score < 54 points
- Prices: American odds format (negative = favorite)

### Moneyline Display
```
💰 MONEYLINE:
   ARIZONA CARDINALS               (+150)
   DALLAS COWBOYS                  (-180)
```

- **+150**: Bet $100 to win $150 (underdog)
- **-180**: Bet $180 to win $100 (favorite)

---

## 🔄 Workflow Example

### Complete Betting Research Workflow

```bash
# Step 1: Scrape latest odds
uv run walters-analyzer scrape-overtime --sport nfl

# Step 2: View summary
uv run walters-analyzer view-odds --sport nfl --summary

# Step 3: Check today's games
uv run walters-analyzer view-odds --today

# Step 4: Research specific matchup
uv run walters-analyzer view-odds --team "Cardinals"

# Step 5: Compare historical lines
uv run walters-analyzer view-odds --compare "Cardinals"

# Step 6: Export for deeper analysis
uv run walters-analyzer view-odds --sport nfl --upcoming 3 --export analysis.csv
```

---

## 🛠️ Advanced Usage

### Combining Multiple Filters
```bash
# NFL games today featuring Cowboys
uv run walters-analyzer view-odds --sport nfl --today --team "Cowboys"

# College football games this week
uv run walters-analyzer view-odds --sport college_football --upcoming 7

# Export specific team's upcoming games
uv run walters-analyzer view-odds --team "Arizona" --upcoming 14 --export cardinals.csv
```

### Working with Specific Files
```bash
# Compare current odds to yesterday's
uv run walters-analyzer view-odds --file data/overtime_live/overtime-live-20251102-*.jsonl --team "Cowboys"
uv run walters-analyzer view-odds --file data/overtime_live/overtime-live-20251103-*.jsonl --team "Cowboys"
```

### Python Script Integration
```python
from walters_analyzer.query import OddsViewer

# Load latest odds
viewer = OddsViewer()
viewer.load_latest(sport="nfl")

# Filter for specific team
cowboys_games = viewer.filter_by_team("Cowboys")

# Display
viewer.display_games(cowboys_games)

# Or access raw data
for game in cowboys_games:
    spread = game['markets']['spread']
    print(f"Cowboys spread: {spread}")
```

---

## 📝 Tips & Best Practices

### 1. Scrape Regularly
```bash
# Scrape every few hours to track line movement
*/3 * * * * cd /path/to/project && uv run walters-analyzer scrape-overtime --sport nfl
```

### 2. Use Brief Mode for Quick Checks
```bash
# Quick overview without detailed odds
uv run walters-analyzer view-odds --today --brief
```

### 3. Export for Historical Analysis
```bash
# Save each scrape with timestamp for line movement tracking
uv run walters-analyzer scrape-overtime --sport nfl
uv run walters-analyzer view-odds --sport nfl --export "nfl_odds_$(date +%Y%m%d_%H%M%S).csv"
```

### 4. Combine with Billy Walters Gates
```bash
# After viewing odds, check against your betting card
uv run walters-analyzer view-odds --team "Cardinals"
uv run walters-analyzer wk-card --file ./cards/wk-card-2025-11-03.json --dry-run
```

---

## 🚨 Troubleshooting

### No games found
```bash
❌ No games found. Run scraper first:
   uv run walters-analyzer scrape-overtime --sport nfl
```

**Solution:** Scrape data first before viewing

### Wrong sport
```bash
# Make sure sport name matches
--sport nfl              # ✅ Correct
--sport college_football # ✅ Correct
--sport cfb              # ❌ Wrong (use college_football)
```

### Team not found
```bash
# Use partial team name
--team "Cardinals"       # ✅ Finds "ARIZONA CARDINALS"
--team "ARI"            # ❌ Might not match
--team "Arizona"        # ✅ Also works
```

---

## 🎓 Learning More

- **Data Quality:** See `DATA_QUALITY_REVIEW.md`
- **Scraper Details:** See `SCRAPER_USAGE.md`
- **HTML Mapping:** See `HTML_DATA_MAPPING.md`
- **Full Review:** See `REVIEW_SUMMARY.md`

---

## 💡 Pro Tips

1. **Line Shopping**: Compare overtime.ag lines with other books
2. **Track Movement**: Scrape multiple times per day to see how lines move
3. **Steam Chasing**: Look for sudden line moves (sharp action)
4. **Closing Line Value**: Compare your bet to the closing line
5. **Gate Validation**: Use with `wk-card` commands for disciplined betting

**Happy Betting! 🎰📊**

