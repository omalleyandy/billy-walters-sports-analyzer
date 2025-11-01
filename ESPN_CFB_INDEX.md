# ESPN College Football Data Scraping - Complete Project Index

## 📚 Documentation Overview

This project provides a comprehensive solution for scraping ESPN's college football data for all 136 FBS teams to support betting analysis.

---

## 📁 File Guide

### 1. **ESPN_CFB_SCRAPING_SUMMARY.md** ⭐ START HERE
**Quick start guide and project overview**
- What this project does
- Quick installation instructions
- How to run the scraper
- Expected output structure
- Key insights about wildcards
- Use cases for betting analysis

🔗 **Best for**: First-time users, quick setup

---

### 2. **ESPN_WILDCARD_URLS_GUIDE.md** 📖 COMPREHENSIVE GUIDE
**Complete explanation of ESPN's wildcard URL system**
- What wildcards are and why they matter
- All wildcard URL patterns with examples
- How to discover and expand wildcards
- Systematic crawling strategy
- Code examples in Python
- Best practices for scraping

🔗 **Best for**: Understanding the URL structure in depth

---

### 3. **ESPN_CFB_DATA_ANALYSIS.md** 🔍 DETAILED ANALYSIS
**Comprehensive data structure and availability analysis**
- All 136 FBS teams with IDs organized by conference
- Detailed breakdown of every page type
- Complete data fields available on each page
- Key data for betting edge analysis
- Statistical indicators and advanced metrics
- Implementation recommendations

🔗 **Best for**: Understanding what data is available and where

---

### 4. **ESPN_CFB_URL_REFERENCE.md** 📋 QUICK REFERENCE
**Fast lookup table for all URLs and team IDs**
- All 11 static URLs in table format
- Complete team ID lookup by conference
- URL pattern templates
- Popular teams quick access
- Python usage examples
- Summary statistics

🔗 **Best for**: Quick lookups while coding

---

### 5. **scripts/espn_cfb_scraper.py** 💻 WORKING CODE
**Production-ready Python scraper implementation**
- Automatic team ID discovery
- Comprehensive data collection
- Browser automation with Playwright
- Organized JSON output
- Error handling and logging
- Configurable scraping options

🔗 **Best for**: Running the actual scraper

---

### 6. **requirements_espn_scraper.txt** 📦 DEPENDENCIES
**Python package requirements**
- All necessary dependencies
- Specific version requirements
- Installation instructions

🔗 **Best for**: Setting up your environment

---

## 🚀 Quick Start Path

### For First-Time Users:
1. Read: `ESPN_CFB_SCRAPING_SUMMARY.md` (5 minutes)
2. Install: `pip install -r requirements_espn_scraper.txt` (2 minutes)
3. Run: `python scripts/espn_cfb_scraper.py` (5-30 minutes depending on scope)
4. Review: Check `data/espn_cfb/` directory for output

### For Understanding Wildcards:
1. Read: `ESPN_WILDCARD_URLS_GUIDE.md` (15 minutes)
2. Reference: `ESPN_CFB_URL_REFERENCE.md` (as needed)

### For Data Analysis:
1. Read: `ESPN_CFB_DATA_ANALYSIS.md` (20 minutes)
2. Reference: `ESPN_CFB_URL_REFERENCE.md` (as needed)

### For Development:
1. Study: `scripts/espn_cfb_scraper.py` (30 minutes)
2. Reference: All documentation files as needed

---

## 🎯 Key Concepts

### Wildcards (`*`)
ESPN uses wildcards in URLs that must be replaced with:
- **Team IDs**: Numeric identifiers (e.g., 228 = Clemson, 333 = Alabama)
- **Game IDs**: Numeric identifiers (e.g., 401754577 = specific game)

### URL Expansion
```
Template:  /college-football/team/stats/_/id/*
Replace:   * → 228 (Clemson's team ID)
Result:    /college-football/team/stats/_/id/228
```

### Coverage
- **136 FBS teams** across 11 conferences
- **544 team-specific pages** (136 teams × 4 page types)
- **300-400 games** per season
- **555+ total URLs** when fully expanded

---

## 📊 What You Can Scrape

### Static Pages (11 URLs)
✅ Homepage, Scoreboard, Schedule  
✅ SP+ Rankings, FPI Ratings  
✅ Standings, Stats, Odds  
✅ Rankings, Teams List  

### Team Pages (544 URLs)
✅ Team homepage (136)  
✅ Team statistics (136)  
✅ Advanced stats (136)  
✅ Team rosters (136)  

### Game Pages (300-400 URLs)
✅ Game details, scores, stats  
✅ Odds, weather, injuries  
✅ Play-by-play, box scores  

---

## 🏈 All 136 FBS Team IDs

### Quick Conference Reference
| Conference | Teams | Example IDs |
|------------|-------|-------------|
| **ACC** | 17 | 228 (Clemson), 59 (GT), 52 (FSU) |
| **American** | 14 | 235 (Memphis), 2655 (Tulane) |
| **Big 12** | 16 | 251 (Texas), 254 (Utah) |
| **Big Ten** | 18 | 194 (OSU), 130 (Michigan), 84 (Indiana) |
| **Conference USA** | 12 | 2348 (LA Tech), 98 (WKU) |
| **FBS Independents** | 2 | 87 (Notre Dame), 41 (UConn) |
| **MAC** | 13 | 2649 (Toledo), 195 (Ohio) |
| **Mountain West** | 12 | 68 (Boise State), 2439 (UNLV) |
| **Pac-12** | 2 | 204 (Oregon State), 265 (Wazzu) |
| **SEC** | 16 | 333 (Alabama), 61 (Georgia), 99 (LSU) |
| **Sun Belt** | 14 | 2026 (App State), 309 (Louisiana) |

*See `ESPN_CFB_URL_REFERENCE.md` for complete team list*

---

## 💡 Use Cases

### Pre-Game Analysis
- Compare offensive vs defensive matchups
- Check injury reports
- Analyze weather impact
- Compare model predictions vs market lines

### Line Shopping
- Track odds movements
- Identify steam moves
- Find reverse line movement
- Calculate expected value

### Model Building
- Train predictive models
- Validate with CLV
- Backtest strategies
- Find profitable patterns

---

## 🛠️ Customization

### Scrape Only SEC Teams
```python
sec_team_ids = [333, 8, 2, 57, 61, 96, 99, 344, 142, 201, 145, 2579, 2633, 245, 251, 238]
for team_id in sec_team_ids:
    scraper.scrape_team_stats(team_id, team_name)
```

### Change Output Directory
```python
scraper = ESPNCFBScraper(output_dir="my_custom_dir")
```

### Add Custom Data Sources
```python
async def scrape_custom_page(self):
    url = "https://www.espn.com/college-football/custom-page"
    content = await self.fetch_page(url)
    # Parse and save
```

---

## 📈 Data Output Structure

```
data/espn_cfb/
├── teams_list.json              # All 136 teams
├── schedule.json                # Season schedule
├── fpi_data.json               # FPI ratings
├── teams/
│   ├── team_228_roster.json    # Rosters (136 files)
│   └── ...
├── stats/
│   ├── team_228_stats.json     # Team stats (136 files)
│   └── ...
├── games/
│   ├── game_401754577.json     # Game data (100s of files)
│   └── ...
├── odds/
│   ├── odds_20251101_120000.json  # Odds snapshots
│   └── ...
└── rankings/
    ├── rankings_20251101.json  # Rankings (weekly)
    └── ...
```

---

## ⚠️ Important Notes

### Rate Limiting
- Use 1-2 second delays between requests
- Be respectful of ESPN's servers
- Consider proxies for large-scale scraping

### Data Freshness
- **Odds**: Hourly during game days
- **Stats**: After each game
- **Rankings**: Weekly (Mon/Tue)
- **Rosters**: Season start

### Legal
- Review ESPN's Terms of Service
- Personal analysis only
- Don't redistribute commercially
- Respect robots.txt

---

## 🔧 Troubleshooting

### Installation Issues
```bash
# If Playwright fails
playwright install chromium --force

# If dependencies conflict
pip install -r requirements_espn_scraper.txt --upgrade
```

### Scraping Issues
- Check internet connection
- Verify ESPN pages are accessible
- Review error logs in console
- Increase delays between requests

### Data Issues
- Validate team IDs are current
- Check for ESPN page structure changes
- Verify JSON output format
- Cross-reference with manual checks

---

## 📧 Documentation Map

```
START HERE → ESPN_CFB_SCRAPING_SUMMARY.md
    ↓
UNDERSTAND WILDCARDS → ESPN_WILDCARD_URLS_GUIDE.md
    ↓
DETAILED DATA → ESPN_CFB_DATA_ANALYSIS.md
    ↓
QUICK REFERENCE → ESPN_CFB_URL_REFERENCE.md
    ↓
IMPLEMENT → scripts/espn_cfb_scraper.py
```

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Total Documentation Files** | 6 |
| **Lines of Python Code** | 500+ |
| **FBS Teams Covered** | 136 |
| **Conferences** | 11 |
| **URL Patterns Documented** | 16 |
| **Expanded URLs Available** | 555+ |
| **Team IDs Mapped** | 136 |

---

## ✅ Project Deliverables

- ✅ Complete documentation (4 markdown files)
- ✅ Working Python scraper
- ✅ All 136 team IDs mapped
- ✅ Wildcard system explained
- ✅ Installation instructions
- ✅ Usage examples
- ✅ Quick reference tables
- ✅ Data structure analysis

---

## 🎓 Learning Path

### Beginner (1 hour)
1. Read `ESPN_CFB_SCRAPING_SUMMARY.md`
2. Install dependencies
3. Run scraper with 5 teams
4. Explore output data

### Intermediate (3 hours)
1. Read `ESPN_WILDCARD_URLS_GUIDE.md`
2. Study `espn_cfb_scraper.py`
3. Run full scrape (all 136 teams)
4. Customize scraper for specific needs

### Advanced (1 day)
1. Read all documentation
2. Understand complete data structure
3. Build custom analytics
4. Integrate with betting models

---

## 🚀 Quick Commands

```bash
# Setup
pip install -r requirements_espn_scraper.txt
playwright install chromium

# Run (test mode - 5 teams)
python scripts/espn_cfb_scraper.py

# View output
ls -R data/espn_cfb/

# Check specific data
cat data/espn_cfb/teams_list.json
cat data/espn_cfb/stats/team_228_stats.json
```

---

## 📝 Documentation Versions

| File | Last Updated | Version |
|------|--------------|---------|
| ESPN_CFB_INDEX.md | Nov 1, 2025 | 1.0 |
| ESPN_CFB_SCRAPING_SUMMARY.md | Nov 1, 2025 | 1.0 |
| ESPN_WILDCARD_URLS_GUIDE.md | Nov 1, 2025 | 1.0 |
| ESPN_CFB_DATA_ANALYSIS.md | Nov 1, 2025 | 1.0 |
| ESPN_CFB_URL_REFERENCE.md | Nov 1, 2025 | 1.0 |
| espn_cfb_scraper.py | Nov 1, 2025 | 1.0 |

---

**Status**: ✅ Complete Project Ready for Use  
**Total Pages of Documentation**: 20+  
**Code Lines**: 500+  
**Teams Documented**: 136  
**URLs Mapped**: 555+  

---

## 🎯 Next Steps

1. **Choose your starting point** from the documentation map above
2. **Install dependencies** using the quick commands
3. **Run the scraper** in test mode first
4. **Explore the data** in the output directory
5. **Customize** for your specific betting analysis needs

---

**Ready to analyze college football data like never before! 🏈📊**

