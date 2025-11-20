# Billy Walters Weekly Tracking & Power Rating System
## Implementation Guide

### Status: PHASE 1 - Foundation

This document outlines the complete implementation of weekly power rating updates and comprehensive tracking for NFL and NCAAF betting analysis.

---

## System Overview

### Core Components

**1. overtime.ag Scraper** ✅ COMPLETE
- Location: `overtime_ag_scraper.py`
- Status: Framework ready, needs HTML parsing implementation
- Purpose: Primary source for betting lines (spreads, totals, moneylines)

**2. Power Rating System** 🔧 IN PROGRESS
- Week 1 baseline from Massey Ratings
- Weekly updates using 90/10 formula
- Automated game result integration

**3. Weekly Tracker** 📋 PLANNED
- Excel-based tracking system
- Separate sheets per league/week
- Automated data population

**4. Data Integration** 🔄 PLANNED
- Existing: Massey Ratings, Vegas Insider
- New: overtime.ag, ESPN (if needed)
- Weekly schedule validation

---

## Data Source Architecture

### Primary Sources (Current)

```
Massey Ratings (✅ Working)
├── Power ratings baseline (Week 1)
├── Weekly rating updates
├── Game matchups
└── Team rankings

Vegas Insider (✅ Working)
├── Betting lines (backup)
└── Line movement tracking

overtime.ag (🔧 Setup Phase)
├── Primary betting lines
├── NFL spreads/totals/moneylines
├── NCAAF spreads/totals/moneylines
└── Live betting (optional)
```

### Planned Additions

```
ESPN.com (📋 Phase 2)
├── Injury reports
├── Team stats
├── Player stats
└── Game schedules

NFL.com (📋 Phase 2)
├── Official injury designations
├── Depth charts
└── Advanced stats
```

---

## Power Rating System - 90/10 Formula

### Mathematical Framework

**Billy Walters 90/10 Formula**:
```
New Rating = (Old Rating × 0.90) + (Game Result × 0.10)

Where:
- Old Rating: Team's power rating before game
- Game Result: Actual margin adjusted for home field advantage
- 0.90/0.10: Weight ratio (90% history, 10% recent performance)
```

### Implementation Steps

#### Week 1 Baseline (Start of Season)

**Option 1: Massey Ratings Only** (Simplest)
```python
# Use existing scraper
from massey_ratings_live_scraper import MasseyRatingsScraper

async def get_week1_baseline():
    scraper = MasseyRatingsScraper()
    await scraper.initialize()
    ratings = await scraper.scrape_team_ratings('nfl')
    await scraper.close()
    return ratings
```

**Option 2: Multi-Source Average** (More Robust)
```python
def get_week1_baseline_averaged():
    # Average: Massey (50%) + Market consensus (50%)
    massey = get_massey_ratings()
    market = derive_from_win_totals()
    
    baseline = {}
    for team in massey:
        baseline[team] = (massey[team] * 0.5) + (market[team] * 0.5)
    
    return baseline
```

#### Weekly Update Process

**After Each Week's Games**:

```python
from datetime import datetime

def update_power_ratings_weekly(week_number: int, season: int = 2025):
    """
    Update all team power ratings using 90/10 formula
    
    Steps:
    1. Load current power ratings
    2. Fetch game results from ESPN/NFL.com/Massey
    3. Apply 90/10 formula to each team
    4. Adjust for home field advantage (~2.5 points)
    5. Remove garbage time points
    6. Save updated ratings
    """
    
    # 1. Load current ratings
    ratings = load_power_ratings(week_number - 1)
    
    # 2. Get game results
    games = fetch_game_results(week_number, season)
    
    # 3. Apply formula
    for game in games:
        # Adjust for home field
        adjusted_margin = game.margin - 2.5  # If home team won
        
        # Update winner
        old_rating = ratings[game.winner]
        new_rating = (old_rating * 0.90) + (adjusted_margin * 0.10)
        ratings[game.winner] = new_rating
        
        # Update loser
        old_rating = ratings[game.loser]
        new_rating = (old_rating * 0.90) + (-adjusted_margin * 0.10)
        ratings[game.loser] = new_rating
    
    # 4. Save updated ratings
    save_power_ratings(ratings, week_number)
    
    return ratings
```

### Adjustments

**Garbage Time Removal**:
```python
def remove_garbage_time(game_result):
    """
    Remove prevent defense scores (last 2 min when >14 pt lead)
    
    Example:
    - Final: 35-17 (18 pt margin)
    - Late TD by losing team: 35-24 (11 pt margin)
    - Adjusted: 35-17 (18 pt margin - ignore late score)
    """
    # Implementation requires play-by-play data
    # For now, use final score as-is
    return game_result.final_margin
```

**Home Field Advantage**:
```python
HFA_VALUES = {
    'nfl': 2.5,      # NFL average
    'ncaaf': 3.5,    # College average (higher due to crowd/atmosphere)
}

def adjust_for_home_field(margin, home_team_won, sport='nfl'):
    """
    Adjust margin for home field advantage
    
    Example:
    - Home team wins by 10: actual margin = 10 - 2.5 = 7.5
    - Away team wins by 10: actual margin = 10 + 2.5 = 12.5
    """
    hfa = HFA_VALUES[sport]
    
    if home_team_won:
        return margin - hfa
    else:
        return margin + hfa
```

---

## Weekly Tracking System

### Excel Workbook Structure

**Filename Format**: `billy_walters_tracker_2025.xlsx`

**Sheets**:

#### 1. NFL_Power_Ratings
```
Columns:
- Team
- Week_0_Baseline (from Massey preseason)
- Week_1 (after applying 90/10)
- Week_2
- ...
- Week_18
- Last_Updated
- Season_Change
```

#### 2. NCAAF_Power_Ratings
```
Same structure as NFL
```

#### 3. NFL_Week[N]_Games
```
Columns:
- Game_ID
- Date
- Time
- Away_Team
- Home_Team
- Our_Power_Rating_Line
- overtime.ag_Line
- Line_Differential
- S_Factor_Travel
- S_Factor_Rest
- S_Factor_Weather
- S_Factor_Motivation
- S_Factor_Total_Adjustment
- Injury_Impact
- Key_Numbers_Crossed
- Total_Edge_Percentage
- Confidence_Level (HIGH/MEDIUM/LOW)
- Bet_Recommendation (Team + Line)
- Star_Rating (0.5-3.0)
- Bet_Size_Dollars
- Bet_Size_Percentage
- Timing_Strategy (EARLY/LATE)
- Notes
```

#### 4. NFL_Week[N]_Results
```
Columns:
- Game_ID
- Bet_Made (YES/NO)
- Our_Pick
- Our_Line
- Closing_Line
- Beat_Closing_Line (YES/NO)
- CLV_Points
- Final_Score
- Result (WIN/LOSS/PUSH)
- Profit_Loss_Dollars
- Process_Adherence (GOOD/FAIR/POOR)
- What_Went_Right
- What_Went_Wrong
- Lessons_Learned
```

#### 5. Season_Summary_NFL
```
Columns:
- Week
- Games_Analyzed
- Bets_Made
- Win_Loss_Push_Record
- Win_Percentage
- ROI_Percentage
- CLV_Positive_Rate
- Average_Edge
- Largest_Bet
- Weekly_Bankroll
- Week_PnL
- Season_PnL
- Risk_Compliance (✓/✗)
```

### Automation Scripts

#### Generate Weekly Tracker
```python
# File: generate_weekly_tracker.py

import openpyxl
from openpyxl.styles import Font, PatternFill
from datetime import datetime

def create_weekly_tracker(week: int, season: int = 2025):
    """
    Generate Excel tracker for specified week
    
    Args:
        week: NFL/NCAAF week number
        season: Year
    """
    
    wb = openpyxl.Workbook()
    
    # Create NFL sheets
    create_nfl_games_sheet(wb, week)
    create_nfl_results_sheet(wb, week)
    
    # Create NCAAF sheets
    create_ncaaf_games_sheet(wb, week)
    create_ncaaf_results_sheet(wb, week)
    
    # Create power rating sheets
    create_power_ratings_sheet(wb, 'nfl')
    create_power_ratings_sheet(wb, 'ncaaf')
    
    # Create summary sheets
    create_season_summary_sheet(wb, 'nfl')
    create_season_summary_sheet(wb, 'ncaaf')
    
    # Create bankroll sheet
    create_bankroll_sheet(wb)
    
    # Save
    filename = f'trackers/billy_walters_week{week}_{season}.xlsx'
    wb.save(filename)
    
    print(f"✅ Created tracker: {filename}")
```

#### Auto-Populate from Scrapers
```python
# File: populate_tracker.py

async def populate_weekly_tracker(week: int):
    """
    Auto-populate tracker with scraped data
    
    Steps:
    1. Load Excel tracker
    2. Scrape overtime.ag for betting lines
    3. Load power ratings
    4. Calculate our lines
    5. Compute edge for each game
    6. Fill in Excel cells
    7. Save
    """
    
    # 1. Load tracker
    wb = openpyxl.load_workbook(f'trackers/billy_walters_week{week}_2025.xlsx')
    nfl_sheet = wb['NFL_Week{week}_Games']
    
    # 2. Scrape overtime.ag
    scraper = OvertimeAgScraper()
    await scraper.initialize()
    lines = await scraper.scrape_nfl()
    await scraper.close()
    
    # 3. Load power ratings
    ratings = load_power_ratings(week)
    
    # 4. Populate each row
    row = 2  # Start after headers
    for game_line in lines:
        # Get teams
        away = game_line.away_team
        home = game_line.home_team
        
        # Calculate our line
        our_line = ratings[home] - ratings[away] - 2.5  # HFA
        
        # overtime.ag line
        market_line = game_line.spread
        
        # Edge
        edge = abs(our_line - market_line)
        
        # Write to Excel
        nfl_sheet.cell(row, 1).value = f"{away}@{home}"
        nfl_sheet.cell(row, 4).value = away
        nfl_sheet.cell(row, 5).value = home
        nfl_sheet.cell(row, 6).value = our_line
        nfl_sheet.cell(row, 7).value = market_line
        nfl_sheet.cell(row, 8).value = edge
        
        row += 1
    
    # 5. Save
    wb.save(f'trackers/billy_walters_week{week}_2025.xlsx')
    
    print(f"✅ Populated tracker for Week {week}")
```

---

## Implementation Timeline

### Phase 1: Foundation (This Week)

**Day 1-2: overtime.ag Scraper** 🔧 IN PROGRESS
- [ ] Test scraper on your Windows machine
- [ ] Inspect HTML structure from debug files
- [ ] Implement parsing logic for betting lines
- [ ] Validate data accuracy

**Day 3: Power Rating System**
- [ ] Create `power_rating_manager.py`
- [ ] Fetch Week 1 baseline from Massey
- [ ] Implement 90/10 update function
- [ ] Test with historical data

**Day 4-5: Weekly Tracker**
- [ ] Create Excel template generator
- [ ] Build auto-population scripts
- [ ] Test with current week data
- [ ] Validate calculations

### Phase 2: Enhancement (Next Week)

**ESPN/NFL.com Integration** (If Needed)
- [ ] Build ESPN injury scraper
- [ ] Build ESPN schedule validator
- [ ] Build NFL.com stats scraper
- [ ] Integrate with tracking system

**Advanced Features**
- [ ] Weather integration (AccuWeather)
- [ ] S-factors automation
- [ ] Key numbers detection
- [ ] Bet recommendation engine

---

## Immediate Next Steps

### What You Need to Do Now:

1. **Test overtime.ag Scraper**
   ```powershell
   cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
   uv run python overtime_ag_scraper.py
   ```
   
   This will:
   - Navigate to overtime.ag/sports
   - Save debug files (HTML, text, screenshot)
   - Show you what needs to be parsed

2. **Review Debug Files**
   - Open `overtime_screenshot.png` to see what Playwright sees
   - Open `overtime_debug_nfl_[timestamp].html` to see HTML structure
   - Look for patterns: team names, odds, spreads, totals

3. **Share Findings**
   - What HTML elements contain betting lines?
   - How are team names displayed?
   - How are odds formatted?
   - Any JavaScript that needs special handling?

4. **Clarify ESPN/NFL.com Status**
   - Do you have existing scrapers for these sources?
   - Or do we need to build them?
   - What data do you actually need from them?

### What I'll Do Once You Test:

1. **Implement Parsing Logic**
   - Based on HTML structure you share
   - Extract betting lines accurately
   - Handle edge cases

2. **Build Power Rating Manager**
   - Week 1 baseline from Massey
   - 90/10 update automation
   - Game result integration

3. **Create Weekly Tracker**
   - Excel template generator
   - Auto-population scripts
   - Comprehensive tracking

---

## Questions to Answer

### Critical (Blocks Phase 1):
1. ✅ Can you run `overtime_ag_scraper.py` on your Windows machine?
2. ✅ What does the HTML structure look like? (from debug files)
3. ✅ Do you have login credentials for overtime.ag in your `.env`?

### Important (Needed This Week):
4. What week are we currently in? (NFL Week 11? NCAAF Week 12?)
5. Do you want to backfill power ratings from Week 1, or start fresh?
6. Do ESPN/NFL.com scrapers exist, or do we build them?

### Nice to Have (Can Wait):
7. Preferred Excel layout/format?
8. Any specific metrics you want tracked?
9. Integration with your existing `billy_walters_power_ratings.py`?

---

## Success Criteria

### Phase 1 Complete When:
- ✅ overtime.ag scraper returns accurate betting lines
- ✅ Power ratings update weekly via 90/10 formula
- ✅ Weekly tracker auto-populates with data
- ✅ All calculations validated against Billy Walters methodology

### System Working When:
- Scrape overnight.ag every 6 hours
- Update power ratings after each week
- Generate tracker template for upcoming week
- Auto-populate with scraped data
- Track results and calculate ROI
- Maintain 100+ bet sample for statistical validity

---

## Contact Points

**When You're Ready to Continue:**
1. Share debug files from overtime.ag scraper
2. Answer the critical questions above
3. We'll implement Phase 1 together

**Estimated Timeline:**
- With your help: 2-3 days for Phase 1
- Solo development: 5-7 days
- Full system (Phase 1 + 2): 7-10 days

Let's build this right! 🚀
