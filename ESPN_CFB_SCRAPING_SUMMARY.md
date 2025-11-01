# ESPN College Football Scraping Project - Summary

## Project Overview

This project provides a comprehensive solution for scraping ESPN's college football data to support betting edge analysis for all 136 FBS teams.

---

## 📁 Project Structure

```
billy-walters-sports-analyzer/
├── ESPN_CFB_DATA_ANALYSIS.md          # Detailed data analysis & structure
├── ESPN_WILDCARD_URLS_GUIDE.md        # Wildcard URL explanation & usage
├── ESPN_CFB_SCRAPING_SUMMARY.md       # This file - Quick start guide
├── requirements_espn_scraper.txt      # Python dependencies
├── scripts/
│   └── espn_cfb_scraper.py           # Main scraping implementation
└── data/
    └── espn_cfb/                     # Output directory (created on first run)
        ├── teams/                    # Team rosters
        ├── stats/                    # Team statistics
        ├── games/                    # Game details
        ├── odds/                     # Betting lines
        └── rankings/                 # Rankings data
```

---

## 🎯 What This Project Does

### 1. Identifies All URLs
- **136 FBS teams** across 11 conferences
- **Main pages**: Schedule, Odds, Rankings, FPI, SP+, Stats
- **Team-specific pages**: Stats, Rosters, Schedules (with wildcards)
- **Game-specific pages**: Live scores, box scores, odds (with wildcards)

### 2. Explains Wildcard System
ESPN uses wildcards (`*`) in URLs that must be replaced with:
- **Team IDs**: Numeric identifiers (e.g., 228 = Clemson)
- **Game IDs**: Numeric identifiers (e.g., 401754577 = specific game)

Example wildcard expansion:
```
Template:  /college-football/team/_/id/*
Clemson:   /college-football/team/_/id/228
Alabama:   /college-football/team/_/id/333
Ohio St:   /college-football/team/_/id/194
```

### 3. Provides Working Scraper
A production-ready Python scraper that:
- Automatically discovers all 136 team IDs
- Scrapes team stats, rosters, and schedules
- Collects odds, rankings, and game data
- Saves everything in organized JSON format
- Uses browser automation (Playwright) for JavaScript-rendered content

---

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.9+
python --version

# Install dependencies
pip install -r requirements_espn_scraper.txt

# Install Playwright browsers
playwright install chromium
```

### Run the Scraper

**Option 1: Test with 5 teams (recommended first time)**
```bash
python scripts/espn_cfb_scraper.py
```

**Option 2: Scrape all 136 teams**
```python
# Edit scripts/espn_cfb_scraper.py, line in main():
await scraper.run_full_scrape(
    scrape_teams=True,
    teams_limit=None  # Change from 5 to None
)
```

**Option 3: Only scrape main pages (no teams)**
```python
await scraper.run_full_scrape(
    scrape_teams=False  # Skip team-level scraping
)
```

### Expected Output
```
data/espn_cfb/
├── teams_list.json              # All 136 teams with IDs
├── schedule.json                # Season schedule
├── fpi_data.json               # FPI ratings
├── teams/
│   ├── team_228_roster.json    # 136 roster files
├── stats/
│   ├── team_228_stats.json     # 136 stats files
├── odds/
│   └── odds_20251101_120000.json
└── rankings/
    └── rankings_20251101.json
```

---

## 📊 Complete URL List

### Main Pages (No Wildcards)
1. ✅ `https://www.espn.com/college-football/` - Homepage
2. ✅ `https://www.espn.com/college-football/scoreboard` - Scores
3. ✅ `https://www.espn.com/college-football/schedule` - Schedule
4. ✅ `https://www.espn.com/college-football/story/_/id/46128861/...` - SP+ Rankings
5. ✅ `https://www.espn.com/college-football/fpi` - FPI Ratings
6. ✅ `https://www.espn.com/college-football/standings` - Standings
7. ✅ `https://www.espn.com/college-football/stats` - Stats Overview
8. ✅ `https://www.espn.com/college-football/stats/_/view/team` - Team Stats
9. ✅ `https://www.espn.com/college-football/teams` - Teams List
10. ✅ `https://www.espn.com/college-football/odds` - Betting Odds
11. ✅ `https://www.espn.com/college-football/rankings` - Rankings

### Team Wildcard URLs (136 teams × 4 pages = 544 URLs)
12. ✅ `https://www.espn.com/college-football/team/_/id/*` - Team Page
13. ✅ `https://www.espn.com/college-football/team/stats/_/id/*` - Team Stats
14. ✅ `https://www.espn.com/college-football/team/stats/_/type/team/id/*` - Advanced Stats
15. ✅ `https://www.espn.com/college-football/team/roster/_/id/*` - Roster

### Game Wildcard URLs (Hundreds per season)
16. ✅ `https://www.espn.com/college-football/game/_/gameId/*` - Game Details

**Total Unique Data Sources**: 555+ URLs

---

## 🏈 All 136 FBS Team IDs

### Quick Reference by Conference

**ACC (17 teams)**: 103, 25, 228, 150, 52, 59, 97, 2390, 152, 153, 221, 2567, 24, 183, 258, 259, 154

**American (14 teams)**: 349, 2429, 151, 2226, 235, 2426, 249, 242, 58, 218, 2655, 202, 5, 2636

**Big 12 (16 teams)**: 9, 12, 252, 239, 2132, 38, 248, 66, 2305, 2306, 197, 2628, 2641, 2116, 254, 277

**Big Ten (18 teams)**: 356, 84, 2294, 120, 127, 130, 135, 158, 77, 194, 2483, 213, 2509, 164, 26, 30, 264, 275

**Conference USA (12 teams)**: 48, 2229, 55, 338, 2335, 2348, 2393, 2623, 166, 2534, 2638, 98

**FBS Independents (2 teams)**: 87, 41

**MAC (13 teams)**: 2006, 2050, 189, 2084, 2117, 2199, 2309, 113, 193, 2459, 195, 2649, 2711

**Mountain West (12 teams)**: 2005, 68, 36, 278, 62, 2440, 167, 21, 23, 2439, 328, 2751

**Pac-12 (2 teams)**: 204, 265

**SEC (16 teams)**: 333, 8, 2, 57, 61, 96, 99, 344, 142, 201, 145, 2579, 2633, 245, 251, 238

**Sun Belt (14 teams)**: 2026, 2032, 324, 290, 2247, 256, 309, 276, 295, 6, 2572, 326, 2653, 2433

*See `ESPN_CFB_DATA_ANALYSIS.md` for team names and full details*

---

## 🎲 Data for Betting Edge Analysis

### Statistical Data
- **Offensive Stats**: Points/game, yards/play, 3rd down %
- **Defensive Stats**: Points allowed, yards allowed
- **Special Teams**: FG%, punt avg, returns
- **Turnover Margin**: Critical predictor
- **Red Zone Efficiency**: Scoring %
- **Time of Possession**: Ball control

### Advanced Metrics
- **SP+ Ratings**: Predictive power ratings (offense + defense + tempo)
- **FPI Scores**: ESPN's Football Power Index with win probabilities
- **Strength of Schedule**: Opponent quality adjustment

### Situational Data
- **Home/Away Splits**: Performance differential by location
- **Weather Conditions**: Temperature, wind, precipitation impacts
- **Injury Reports**: Key player availability
- **Rest Days**: Days between games
- **Line Movement**: Sharp vs public money indicators
- **Public Betting %**: Fade or follow the public
- **Historical Trends**: Head-to-head records

### Betting Lines
- **Point Spreads**: Current and historical
- **Moneylines**: Win odds
- **Totals (Over/Under)**: Scoring projections
- **Line Movement History**: Track sharp money
- **Closing Line Value (CLV)**: Model validation

---

## 💡 Key Insights About Wildcards

### What Are Wildcards?
Wildcards (`*`) in URLs are placeholders that represent:
- **Team IDs**: Unique numeric identifiers for each team
- **Game IDs**: Unique numeric identifiers for each game

### Why Wildcards Matter
Without understanding wildcards, you'd only have access to 11 main pages.
WITH wildcard expansion, you gain access to:
- **544+ team-specific pages** (136 teams × 4 pages each)
- **Hundreds of game pages** (every game this season)
- **Total**: 555+ unique data sources

### How to Expand Wildcards
1. **Collect IDs**: Scrape teams page to get all 136 team IDs
2. **Substitute**: Replace `*` with each team ID
3. **Scrape**: Visit each expanded URL systematically

**Example**:
```python
# Template
url_template = "https://www.espn.com/college-football/team/stats/_/id/*"

# Expansion for Clemson (ID: 228)
url_clemson = url_template.replace("*", "228")
# Result: https://www.espn.com/college-football/team/stats/_/id/228

# Repeat for all 136 teams
for team_id in all_team_ids:
    url = url_template.replace("*", str(team_id))
    scrape(url)
```

---

## 📈 Use Cases for Betting Analysis

### 1. Pre-Game Analysis
- Compare team stats (offense vs defense matchup)
- Check injury reports for key players
- Analyze weather impact on totals
- Review SP+/FPI predictions vs market lines
- Identify value opportunities

### 2. Line Shopping
- Track odds movements across books
- Identify steam moves (sharp money)
- Find reverse line movement opportunities
- Calculate expected value (EV)

### 3. Model Building
- Train predictive models on historical data
- Validate with Closing Line Value (CLV)
- Backtest strategies
- Identify profitable patterns

### 4. Live Betting
- Compare live stats to pre-game expectations
- Track in-game momentum shifts
- Find value in live lines

---

## 🛠️ Customization Options

### Scraper Configuration
```python
# In espn_cfb_scraper.py

class ESPNCFBScraper:
    def __init__(self, output_dir: str = "data/espn_cfb"):
        # Change output directory
        self.output_dir = Path(output_dir)
        
    async def fetch_page(self, url: str, wait_for: Optional[str] = None):
        # Modify delays, timeouts, etc.
        await page.goto(url, wait_until="networkidle")
```

### Add New Data Sources
```python
async def scrape_new_data_source(self):
    """Add your custom scraping logic"""
    url = "https://www.espn.com/college-football/new-page"
    content = await self.fetch_page(url)
    # Parse and save data
```

### Filter by Conference
```python
# Scrape only SEC teams
sec_team_ids = [333, 8, 2, 57, 61, 96, 99, 344, 142, 201, 145, 2579, 2633, 245, 251, 238]

for team_id in sec_team_ids:
    await scraper.scrape_team_stats(team_id, team_name)
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `ESPN_CFB_DATA_ANALYSIS.md` | Comprehensive data structure analysis, all 136 team IDs, data fields, betting indicators |
| `ESPN_WILDCARD_URLS_GUIDE.md` | Detailed wildcard explanation, URL patterns, expansion examples, best practices |
| `ESPN_CFB_SCRAPING_SUMMARY.md` | This file - Quick start guide and overview |
| `scripts/espn_cfb_scraper.py` | Production-ready scraper implementation |
| `requirements_espn_scraper.txt` | Python dependencies |

---

## ⚠️ Important Notes

### Rate Limiting
- Be respectful: Use 1-2 second delays between requests
- ESPN may block aggressive scraping
- Consider using proxies for large-scale scraping

### Data Freshness
- **Odds**: Update every hour during game days
- **Stats**: Update after each game
- **Rankings**: Update weekly (Mondays/Tuesdays)
- **Rosters**: Update at season start

### Legal Considerations
- Review ESPN's Terms of Service
- Use data for personal analysis only
- Don't redistribute scraped data commercially
- Respect robots.txt

---

## 🎯 Next Steps

1. **Install dependencies**: `pip install -r requirements_espn_scraper.txt`
2. **Install Playwright**: `playwright install chromium`
3. **Test the scraper**: Run with 5 teams first
4. **Review the output**: Check `data/espn_cfb/` directory
5. **Customize as needed**: Modify scraper for your specific needs
6. **Build your models**: Use scraped data for betting analysis
7. **Automate updates**: Schedule daily/weekly scraping

---

## 📧 Support

For questions or issues:
1. Review the documentation files
2. Check the code comments in `espn_cfb_scraper.py`
3. Refer to the wildcard guide for URL patterns

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **Total FBS Teams** | 136 |
| **Conferences** | 11 |
| **Team URLs per team** | 4 |
| **Total Team URLs** | 544+ |
| **Main Pages** | 11 |
| **Game URLs** | Hundreds (varies by season) |
| **Total Scrapeable URLs** | 555+ |

---

**Project Status**: ✅ Complete and Ready to Use

**Last Updated**: November 1, 2025

---

## Quick Command Reference

```bash
# Install everything
pip install -r requirements_espn_scraper.txt
playwright install chromium

# Run test scrape (5 teams)
python scripts/espn_cfb_scraper.py

# View results
ls -R data/espn_cfb/

# Check team list
cat data/espn_cfb/teams_list.json

# Check a team's stats
cat data/espn_cfb/stats/team_228_stats.json
```

---

**All set! You now have complete documentation and a working scraper for all ESPN college football FBS data. 🏈📊**

