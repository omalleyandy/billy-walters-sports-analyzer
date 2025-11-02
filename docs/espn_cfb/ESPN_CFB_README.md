# ESPN College Football FBS Data Scraper 🏈

> **Comprehensive web scraping solution for all 136 FBS college football teams on ESPN**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🎯 What This Project Does

This project provides everything you need to systematically scrape ESPN's college football data for **all 136 FBS teams**, including:

✅ **Team Statistics** - Offensive, defensive, and special teams stats  
✅ **Player Rosters** - Complete rosters with positions, classes, measurements  
✅ **Game Data** - Scores, box scores, play-by-play, odds  
✅ **Power Ratings** - SP+, FPI, and other predictive metrics  
✅ **Betting Lines** - Spreads, totals, moneylines, line movements  
✅ **Rankings** - AP Poll, Coaches Poll, CFP rankings  
✅ **Schedules** - Full season schedules with game IDs  

---

## 📚 Complete Documentation

| Document | Description | Best For |
|----------|-------------|----------|
| **[ESPN_CFB_INDEX.md](ESPN_CFB_INDEX.md)** | Master index and navigation | Finding the right doc |
| **[ESPN_CFB_SCRAPING_SUMMARY.md](ESPN_CFB_SCRAPING_SUMMARY.md)** ⭐ | Quick start guide | First-time users |
| **[ESPN_WILDCARD_URLS_GUIDE.md](ESPN_WILDCARD_URLS_GUIDE.md)** | Wildcard URL system explained | Understanding URLs |
| **[ESPN_CFB_DATA_ANALYSIS.md](ESPN_CFB_DATA_ANALYSIS.md)** | Data structure & availability | Data analysts |
| **[ESPN_CFB_URL_REFERENCE.md](ESPN_CFB_URL_REFERENCE.md)** | Quick lookup tables | Developers |

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_espn_scraper.txt
playwright install chromium
```

### 2. Run the Scraper (Test Mode)
```bash
python scripts/espn_cfb_scraper.py
```
*This will scrape 5 teams by default for testing*

### 3. Check Output
```bash
ls -R data/espn_cfb/
```

### 4. Customize (Optional)
Edit `scripts/espn_cfb_scraper.py` to:
- Scrape all 136 teams (change `teams_limit=None`)
- Change output directory
- Add custom data sources

---

## 🔍 Understanding Wildcards

ESPN uses **wildcards** (`*`) in URLs that represent variable IDs:

### Team ID Wildcards
```
Template:  /college-football/team/stats/_/id/*
Example:   /college-football/team/stats/_/id/228    (Clemson)
           /college-football/team/stats/_/id/333    (Alabama)
           /college-football/team/stats/_/id/194    (Ohio State)
```

### Game ID Wildcards
```
Template:  /college-football/game/_/gameId/*
Example:   /college-football/game/_/gameId/401754577
```

**Result**: Instead of just 11 static pages, you get access to **555+ unique URLs**!

---

## 📊 Coverage

### Teams by Conference

| Conference | Teams | Example Team IDs |
|------------|-------|------------------|
| ACC | 17 | 228 (Clemson), 59 (GT), 2390 (Miami) |
| American | 14 | 235 (Memphis), 2655 (Tulane) |
| Big 12 | 16 | 251 (Texas), 2641 (Texas Tech) |
| Big Ten | 18 | 194 (Ohio State), 130 (Michigan) |
| Conference USA | 12 | 2348 (Louisiana Tech) |
| FBS Independents | 2 | 87 (Notre Dame), 41 (UConn) |
| MAC | 13 | 2649 (Toledo), 195 (Ohio) |
| Mountain West | 12 | 68 (Boise State), 2439 (UNLV) |
| Pac-12 | 2 | 204 (Oregon State), 265 (Wazzu) |
| SEC | 16 | 333 (Alabama), 61 (Georgia) |
| Sun Belt | 14 | 2026 (App State), 309 (Louisiana) |

**Total: 136 FBS Teams**

---

## 📁 Output Structure

```
data/espn_cfb/
├── teams_list.json              # All 136 teams with metadata
├── schedule.json                # Current season schedule  
├── fpi_data.json               # FPI power ratings
├── teams/
│   ├── team_228_roster.json    # Player rosters (136 files)
│   └── ...
├── stats/
│   ├── team_228_stats.json     # Team statistics (136 files)
│   └── ...
├── games/
│   ├── game_401754577.json     # Game details (100s of files)
│   └── ...
├── odds/
│   ├── odds_20251101_120000.json  # Betting odds snapshots
│   └── ...
└── rankings/
    ├── rankings_20251101.json  # Weekly rankings
    └── ...
```

---

## 💡 Use Cases

### ⚡ Pre-Game Analysis
- Compare team offensive vs defensive matchups
- Analyze injury impact on key players
- Check weather conditions for totals
- Compare SP+/FPI predictions vs betting lines

### 📈 Line Shopping
- Track odds movements across time
- Identify steam moves (sharp money)
- Find reverse line movement opportunities
- Calculate expected value (EV)

### 🤖 Model Building
- Train predictive models on historical data
- Validate models with Closing Line Value (CLV)
- Backtest betting strategies
- Identify profitable betting patterns

### 🎯 Live Betting
- Compare live stats to pre-game expectations
- Track in-game momentum
- Find value in live betting lines

---

## 🎓 Example: Scraping SEC Teams

```python
from scripts.espn_cfb_scraper import ESPNCFBScraper

# SEC team IDs
sec_teams = {
    "Alabama": 333,
    "Georgia": 61,
    "LSU": 99,
    "Texas": 251,
    # ... 12 more SEC teams
}

scraper = ESPNCFBScraper()
await scraper.initialize_browser()

for team_name, team_id in sec_teams.items():
    # Get team stats
    stats = await scraper.scrape_team_stats(team_id, team_name)
    
    # Get roster
    roster = await scraper.scrape_team_roster(team_id, team_name)
    
    print(f"✅ Scraped {team_name}")

await scraper.close_browser()
```

---

## 🔧 Configuration Options

### Scrape All 136 Teams
```python
# In espn_cfb_scraper.py, modify main():
await scraper.run_full_scrape(
    scrape_teams=True,
    teams_limit=None  # None = all teams
)
```

### Scrape Only Main Pages
```python
await scraper.run_full_scrape(
    scrape_teams=False  # Skip individual teams
)
```

### Change Output Directory
```python
scraper = ESPNCFBScraper(output_dir="my_custom_directory")
```

---

## 📊 Data Available

### Team-Level Data
- Offensive statistics (points, yards, efficiency)
- Defensive statistics (points allowed, turnovers)
- Special teams (FG%, punt/kick returns)
- Complete player rosters with details
- Season schedule with game IDs

### Game-Level Data
- Live/final scores
- Box scores and play-by-play
- Team and player statistics
- Betting lines (spread, total, moneyline)
- Weather conditions
- Injuries and key player availability

### Ratings & Rankings
- SP+ offensive and defensive ratings
- FPI scores and win probabilities
- AP Poll, Coaches Poll rankings
- CFP (College Football Playoff) rankings
- Strength of schedule metrics

---

## ⚠️ Best Practices

### Respectful Scraping
- ✅ Use 1-2 second delays between requests
- ✅ Identify your scraper with User-Agent
- ✅ Respect robots.txt
- ✅ Don't overwhelm servers
- ❌ Don't scrape during peak hours

### Data Management
- ✅ Validate data after scraping
- ✅ Handle missing fields gracefully
- ✅ Cross-reference with multiple sources
- ✅ Version your data snapshots
- ✅ Document data collection timestamps

### Legal Considerations
- ✅ Review ESPN's Terms of Service
- ✅ Use data for personal analysis only
- ❌ Don't redistribute data commercially
- ❌ Don't claim data as your own

---

## 🛠️ Troubleshooting

### Playwright Installation Issues
```bash
# Force reinstall browsers
playwright install chromium --force

# Check installation
playwright --version
```

### Scraping Errors
```python
# Increase delays if getting rate limited
await asyncio.sleep(2)  # Instead of 1 second

# Add retry logic
for attempt in range(3):
    try:
        data = await scraper.fetch_page(url)
        break
    except Exception as e:
        if attempt == 2:
            raise
        await asyncio.sleep(5)
```

### Data Validation
```python
# Check for missing fields
if not stats.get('offensive_stats'):
    logger.warning(f"Missing offensive stats for team {team_id}")

# Verify team IDs
assert len(teams) == 136, f"Expected 136 teams, got {len(teams)}"
```

---

## 📈 Project Statistics

| Metric | Value |
|--------|-------|
| **FBS Teams Covered** | 136 |
| **Conferences** | 11 |
| **Static URLs** | 11 |
| **Team URLs** | 544 (136 × 4) |
| **Game URLs (per season)** | 300-400 |
| **Total URLs** | 855-955 |
| **Documentation Pages** | 20+ |
| **Lines of Code** | 500+ |

---

## 🚦 Update Recommendations

| Data Type | Frequency | Importance |
|-----------|-----------|------------|
| **Odds** | Hourly (game days) | 🔴 Critical |
| **Scores** | Real-time (game days) | 🔴 Critical |
| **Injuries** | Daily | 🟡 High |
| **Team Stats** | After each game | 🟡 High |
| **Rankings** | Weekly (Mon/Tue) | 🟢 Medium |
| **Rosters** | Seasonal | 🟢 Medium |

---

## 📝 Sample Data Output

### teams_list.json
```json
{
  "228": {
    "id": "228",
    "name": "Clemson Tigers",
    "conference": "ACC",
    "url": "https://www.espn.com/college-football/team/_/id/228"
  }
}
```

### team_228_stats.json
```json
{
  "team_id": "228",
  "team_name": "Clemson Tigers",
  "offensive_stats": {
    "points_per_game": "35.2",
    "yards_per_game": "425.7",
    "third_down_pct": "45.2%"
  },
  "defensive_stats": {
    "points_allowed": "18.5",
    "yards_allowed": "315.2"
  }
}
```

---

## 🎯 Roadmap

- [x] Complete URL documentation
- [x] Working scraper implementation
- [x] All 136 team IDs mapped
- [x] Comprehensive guides
- [ ] Add historical data scraping
- [ ] Implement data caching
- [ ] Build analysis dashboard
- [ ] Add bet tracking features

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional data sources
- Better error handling
- Performance optimizations
- New analysis features
- Documentation improvements

---

## 📄 License

This project is for educational and personal use only. Respect ESPN's Terms of Service and copyright.

---

## 🔗 Quick Links

- **Start Here**: [ESPN_CFB_SCRAPING_SUMMARY.md](ESPN_CFB_SCRAPING_SUMMARY.md)
- **Understand Wildcards**: [ESPN_WILDCARD_URLS_GUIDE.md](ESPN_WILDCARD_URLS_GUIDE.md)
- **Data Reference**: [ESPN_CFB_DATA_ANALYSIS.md](ESPN_CFB_DATA_ANALYSIS.md)
- **Team IDs**: [ESPN_CFB_URL_REFERENCE.md](ESPN_CFB_URL_REFERENCE.md)
- **Full Index**: [ESPN_CFB_INDEX.md](ESPN_CFB_INDEX.md)

---

## 💬 Support

Questions? Issues?
1. Check the documentation files above
2. Review code comments in `espn_cfb_scraper.py`
3. Consult the troubleshooting section

---

## 🏆 Credits

Built for the Billy Walters Sports Analyzer project to enable comprehensive college football betting analysis.

**Analyze smarter. Bet better. Win more. 🏈📊**

---

*Last Updated: November 1, 2025*  
*Version: 1.0*  
*Status: ✅ Production Ready*

