# Overtime.ag Scraper - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Step 1: Setup (One-Time)
```powershell
# Install dependencies
uv sync

# Install browser for scraping
uv run playwright install chromium

# Copy environment template and add your credentials
cp env.template .env
# Edit .env and add your OV_CUSTOMER_ID and OV_CUSTOMER_PASSWORD
```

### Step 2: Run Your First Scrape
```powershell
# Scrape both NFL and College Football pre-game odds
uv run walters-analyzer scrape-overtime
```

That's it! Check `data/overtime_live/` for your results.

---

## 📋 Common Commands

### Pre-Game Odds (Main Use Case)
```powershell
# Both sports (default)
uv run walters-analyzer scrape-overtime

# NFL only
uv run walters-analyzer scrape-overtime --sport nfl

# College Football only
uv run walters-analyzer scrape-overtime --sport cfb
```

### Live Betting Odds
```powershell
# Currently live games
uv run walters-analyzer scrape-overtime --live
```

### Injury Reports (Critical for Gate Checks!)
```powershell
# College Football injuries (default)
uv run walters-analyzer scrape-injuries --sport cfb

# NFL injuries
uv run walters-analyzer scrape-injuries --sport nfl
```

💡 **Why scrape injuries?** Key player absences (especially QBs) can move lines 3-7 points. Always check injuries before betting!

---

## 📁 Output Files

### Odds Data

After each odds scrape, you'll find 3 files in `data/overtime_live/`:

1. **CSV** (`overtime-live-{timestamp}.csv`) 
   - Open in Excel
   - Easy to read and analyze
   - All odds in separate columns

2. **JSONL** (`overtime-live-{timestamp}.jsonl`)
   - One game per line
   - Full nested data structure
   - Easy to process programmatically

3. **Parquet** (`overtime-live-{timestamp}.parquet`)
   - Efficient columnar format
   - Best for data analysis with pandas/polars
   - Smallest file size

### Injury Data

After each injury scrape, you'll find 2 files in `data/injuries/`:

1. **JSONL** (`injuries-{timestamp}.jsonl`)
   - One injury per line
   - Player name, position, status, injury type
   - Easy to filter and process

2. **Parquet** (`injuries-{timestamp}.parquet`)
   - Efficient format for analytics
   - Best for combining with odds data

**Example injury record:**
```json
{
  "player_name": "Jalen Milroe",
  "position": "QB",
  "team": "Alabama Crimson Tide",
  "injury_status": "Questionable",
  "injury_type": "Ankle",
  "impact_score": 50
}
```

---

## 🔍 Example: View Your Data

### In Python
```python
import pandas as pd

# Read CSV
df = pd.read_csv('data/overtime_live/overtime-live-20251101-120000.csv')
print(df[['away_team', 'home_team', 'spread_away_line', 'spread_away_price']])

# Or read Parquet (faster for large files)
df = pd.read_parquet('data/overtime_live/overtime-live-20251101-120000.parquet')
```

### In Excel
1. Open the CSV file directly
2. Each game is one row
3. Odds are in separate columns for easy filtering/sorting

---

## ⚙️ Environment Variables

Edit your `.env` file with these required credentials:

```bash
OV_CUSTOMER_ID=your_customer_id_here
OV_CUSTOMER_PASSWORD=your_password_here
```

**Where to find these:**
1. Go to https://overtime.ag
2. Your customer ID is your login username
3. Use your account password

---

## 🐛 Troubleshooting

### "Login failed"
- Double-check your credentials in `.env`
- Try logging in manually at overtime.ag to verify they work
- Make sure there are no extra spaces in your `.env` file

### "scrapy command not found"
```powershell
uv sync  # Re-run to ensure all dependencies are installed
```

### "Browser not found"
```powershell
uv run playwright install chromium
```

### Want to see what's happening?
- Check `snapshots/` folder for debug screenshots
- Look at the console output for detailed logs

---

## 📊 What Data Do I Get?

For each game, you'll get:

**Game Info**
- Teams (home and away)
- Rotation numbers (e.g., "451-452")
- Date and time (e.g., "2025-11-02" and "1:00 PM ET")

**Betting Odds**
- **Spread**: Line and price for both teams
- **Total**: Over/Under line and prices
- **Moneyline**: Odds for both teams

**Example CSV Row:**
```
away_team: Chicago Bears
home_team: Cincinnati Bengals
rotation_number: 451-452
spread_away_line: -2.5
spread_away_price: -115
spread_home_line: +2.5
spread_home_price: -105
total_over_line: 51
total_over_price: -110
...
```

---

## 🎯 Pro Tips

1. **Schedule Regular Scrapes**: Use Windows Task Scheduler or cron to run scrapes automatically
2. **Compare Across Time**: Keep old files to track line movements
3. **Filter by Sport**: Use `--sport nfl` or `--sport cfb` for faster, focused scrapes
4. **Custom Output**: Use `--output-dir ./my_data` to organize by date or purpose

---

## 💡 Example Workflow

```powershell
# Wednesday/Thursday: Scrape injury reports
uv run walters-analyzer scrape-injuries --sport cfb

# Friday morning: Scrape pre-game odds
uv run walters-analyzer scrape-overtime --sport cfb

# Analyze injuries + odds together
# Filter out teams with key injuries (QB, OL, etc.)
# Identify value opportunities

# Saturday: Check live betting during games
uv run walters-analyzer scrape-overtime --live

# Compare pre-game vs live odds
# Track CLV (Closing Line Value)
```

---

## 📚 Need More Help?

- See `README.md` for detailed documentation
- Check `IMPLEMENTATION_SUMMARY.md` for technical details
- Review log output for specific error messages
- Inspect `snapshots/` folder for visual debugging

---

## ✅ Quick Checklist

Before running your first scrape:
- [ ] Installed dependencies (`uv sync`)
- [ ] Installed Playwright (`uv run playwright install chromium`)
- [ ] Created `.env` file from `env.template`
- [ ] Added your `OV_CUSTOMER_ID` and `OV_CUSTOMER_PASSWORD`
- [ ] Ready to run: `uv run walters-analyzer scrape-overtime`

**Happy scraping! 🎲**

