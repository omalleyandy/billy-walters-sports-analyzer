# Billy Walters Sports Analyzer - Quick Reference Card

## 🎯 Most Common Commands

### Scraping
```bash
# Scrape NFL pregame odds
uv run walters-analyzer scrape-overtime --sport nfl

# Scrape College Football odds
uv run walters-analyzer scrape-overtime --sport cfb

# Scrape both
uv run walters-analyzer scrape-overtime --sport both
```

### Viewing Odds
```bash
# View all NFL games
uv run walters-analyzer view-odds --sport nfl

# View today's games
uv run walters-analyzer view-odds --today

# Search for a team
uv run walters-analyzer view-odds --team "Cowboys"

# Compare lines for a team
uv run walters-analyzer view-odds --compare "Cowboys"
```

### Quick Scripts (shortcuts)
```bash
# View NFL odds (shortcut)
./commands/view-odds-nfl.sh

# View today's games (shortcut)
./commands/view-odds-today.sh

# Search for team (shortcut)
./commands/view-odds-team.sh "Cowboys"
```

### Betting Cards
```bash
# Preview a card (dry run)
uv run walters-analyzer wk-card --file ./cards/wk-card-2025-11-03.json --dry-run

# Execute a card (live)
uv run walters-analyzer wk-card --file ./cards/wk-card-2025-11-03.json
```

---

## 📚 Full Command Reference

| Command | Description |
|---------|-------------|
| `scrape-overtime` | Scrape odds from overtime.ag |
| `view-odds` | View scraped odds (query & display) |
| `scrape-injuries` | Scrape injury reports from ESPN |
| `wk-card` | Run/preview a betting card |

---

## 🎨 View Odds Options

| Option | Description | Example |
|--------|-------------|---------|
| `--sport nfl` | Filter by NFL | `view-odds --sport nfl` |
| `--sport college_football` | Filter by CFB | `view-odds --sport college_football` |
| `--today` | Show today's games | `view-odds --today` |
| `--upcoming [DAYS]` | Show upcoming games | `view-odds --upcoming 7` |
| `--date YYYY-MM-DD` | Filter by date | `view-odds --date 2025-11-03` |
| `--team "NAME"` | Search by team | `view-odds --team "Cowboys"` |
| `--compare "TEAM"` | Compare lines | `view-odds --compare "Cowboys"` |
| `--summary` | Show summary only | `view-odds --summary` |
| `--brief` | Hide detailed odds | `view-odds --brief` |
| `--export FILE` | Export to CSV | `view-odds --export odds.csv` |

---

## 💡 Common Workflows

### Daily Research
```bash
# 1. Scrape latest odds
uv run walters-analyzer scrape-overtime --sport nfl

# 2. Check today's games
uv run walters-analyzer view-odds --today

# 3. Research your team
uv run walters-analyzer view-odds --team "Cardinals"
```

### Line Shopping
```bash
# Compare lines across different scrapes
uv run walters-analyzer view-odds --compare "Cowboys"
```

### Preparing Betting Card
```bash
# 1. View odds
uv run walters-analyzer view-odds --upcoming 3

# 2. Create card (manually edit JSON)

# 3. Dry run to test gates
uv run walters-analyzer wk-card --file cards/my-card.json --dry-run

# 4. Execute if gates pass
uv run walters-analyzer wk-card --file cards/my-card.json
```

---

## 🔍 Example Outputs

### View NFL Odds
```bash
$ uv run walters-analyzer view-odds --sport nfl

📂 Loaded 15 games from overtime-live-20251103-120640.jsonl

Found 15 game(s):

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

### Compare Lines
```bash
$ uv run walters-analyzer view-odds --compare "Cowboys"

📈 LINE COMPARISON FOR 'COWBOYS':
================================================================================
2025-11-03 8:15 PM ET    | vs ARIZONA CARDINALS      | -3.5 (-107)
2025-11-10 1:00 PM ET    | @ PHILADELPHIA EAGLES     | +6.5 (-110)
```

### Summary
```bash
$ uv run walters-analyzer view-odds --summary

📊 LOADED GAMES SUMMARY:
================================================================================
Total Games: 45

NFL: 15 games
  - 2025-11-03: 1 games
  - 2025-11-10: 14 games

COLLEGE FOOTBALL: 30 games
  - 2025-11-09: 25 games
  - 2025-11-10: 5 games
```

---

## 📂 File Locations

| Type | Location |
|------|----------|
| Scraped Odds | `data/overtime_live/overtime-live-*.{jsonl,parquet,csv}` |
| Injury Data | `data/injuries/injuries-*.{jsonl,parquet}` |
| Betting Cards | `cards/wk-card-*.json` |
| Commands | `commands/*.sh` |
| Snapshots | `snapshots/*.png` |

---

## 🛠️ Validation & Testing

```bash
# Validate scraped data
python3 scripts/validate_overtime_data.py data/overtime_live/overtime-live-*.jsonl

# Run unit tests
python3 tests/test_pregame_scraper_validation.py
```

---

## 📖 Documentation

| File | Purpose |
|------|---------|
| `ODDS_QUERY_GUIDE.md` | Complete guide to viewing odds |
| `SCRAPER_USAGE.md` | How to scrape overtime.ag |
| `DATA_QUALITY_REVIEW.md` | Technical scraper validation |
| `HTML_DATA_MAPPING.md` | HTML → JSON mapping reference |
| `REVIEW_SUMMARY.md` | Executive summary |
| `QUICK_REFERENCE.md` | This file |

---

## 🆘 Getting Help

```bash
# Show all commands
uv run walters-analyzer --help

# Help for specific command
uv run walters-analyzer view-odds --help
uv run walters-analyzer scrape-overtime --help
uv run walters-analyzer wk-card --help
```

---

## ⚡ Power User Tips

1. **Alias frequently used commands:**
   ```bash
   alias view-nfl="uv run walters-analyzer view-odds --sport nfl"
   alias view-today="uv run walters-analyzer view-odds --today"
   ```

2. **Pipe to less for long output:**
   ```bash
   uv run walters-analyzer view-odds --sport nfl | less
   ```

3. **Combine with grep:**
   ```bash
   uv run walters-analyzer view-odds --brief | grep "COWBOYS"
   ```

4. **Schedule regular scraping:**
   ```bash
   # Crontab: Scrape every 3 hours during the day
   0 */3 * * * cd /path/to/project && uv run walters-analyzer scrape-overtime --sport nfl
   ```

5. **Export and analyze in Excel:**
   ```bash
   uv run walters-analyzer view-odds --upcoming 7 --export weekly.csv
   # Open weekly.csv in Excel/Google Sheets
   ```

---

**For detailed usage, see `ODDS_QUERY_GUIDE.md`**

