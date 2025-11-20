# QUICK START - Week 12 NFL Analysis
**Purpose:** Get running in under 5 minutes  
**Updated:** November 19, 2024, 5:30 PM ET

---

## ⚡ IMMEDIATE ACTIONS (5 Minutes)

### Step 1: Update Power Ratings (2 min)
```powershell
# Navigate to project directory
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Update power ratings with Week 11 results
python billy_walters_power_ratings.py --week 11 --update

# If that doesn't work, try:
python power_rating_system.py --update-week 11
```

### Step 2: Check System Status (1 min)
```powershell
# Verify everything is working
python check_status.py

# Check current opportunities
python view_opportunities.py --week 12
```

### Step 3: Run Initial Analysis (2 min)
```powershell
# Run edge detection for Week 12
python analyze_edges.py --week 12 --bankroll 20000

# If import errors, run the fix:
python fix_imports.py
```

---

## 📋 WEEK 12 CRITICAL INFO

### Games Requiring Immediate Attention

#### THURSDAY NIGHT (Nov 21, 8:15 PM ET)
**Pittsburgh @ Cleveland**
- Current: CLE +7.5
- Check: Aaron Rodgers status (PIT QB - wrist)
- Action: If Rodgers OUT, bet CLE immediately
- If Rodgers PLAYS, potential value on PIT +7.5

#### HIGH-EDGE OPPORTUNITIES
1. **IND +7.5 vs DET** (1:00 PM Sunday)
   - Colts off bye, Lions outdoor struggle
   - Potential 5-6% edge
   - Bet size: 1.5-2.0 stars

2. **ARI +1.0 vs SEA** (4:25 PM Sunday)  
   - Division home dog
   - Line moving toward ARI
   - Bet size: 1.0-1.5 stars

3. **CAR +10.5 vs KC** (1:00 PM Sunday)
   - Chiefs overvalued at 5-5
   - Double-digit dog value
   - Bet size: 1.0 star

### Key Injury Updates Needed
- **C.J. Stroud** (HOU) - Concussion protocol
- **Mike Evans** (TB) - Hamstring
- **Aaron Rodgers** (PIT) - Wrist

### Bye Week Teams (DON'T ANALYZE!)
ATL, BUF, CIN, JAX, NO, NYJ

---

## 🎯 WEDNESDAY CHECKLIST

### Morning (by 11 AM ET)
- [ ] Check official injury reports
- [ ] Update power ratings if needed
- [ ] Calculate S-factors for all games
- [ ] Review overnight line movements

### Afternoon (by 3 PM ET)
- [ ] Run final edge calculations
- [ ] Identify qualifying bets (5.5%+ edge)
- [ ] Check weather for outdoor games
- [ ] Compare lines across 5+ sportsbooks

### Evening (by 6 PM ET)
- [ ] Place FAVORITE bets (road favorites, popular teams)
- [ ] Document all bets with timestamps
- [ ] Set alerts for Thursday night game
- [ ] Save opening lines for CLV tracking

---

## 💻 ESSENTIAL COMMANDS

### Core Analysis
```powershell
# Main analysis command
python analyze_edges.py --week 12 --bankroll 20000

# View current opportunities
python view_opportunities.py --week 12

# Check system status
python check_status.py

# Update power ratings
python billy_walters_power_ratings.py --week 11 --update
```

### Data Collection
```powershell
# Scrape latest odds
python scrape_week12_odds.py

# Collect all data sources
python week12_collector.py

# Get Massey ratings
python massey_ratings_scraper.py
```

### CLV Tracking (New!)
```powershell
# Record a bet
python -m walters_analyzer.cli.clv_cli record-bet --game "IND_DET" --bet-type spread --line 7.5 --odds -110 --amount 400

# Update closing line
python -m walters_analyzer.cli.clv_cli update-closing-line --bet-id 1 --closing-line 6.5 --closing-odds -110

# View CLV summary
python -m walters_analyzer.cli.clv_cli summary --week 12
```

### If Import Errors
```powershell
# Quick fix for imports
python fix_imports.py

# Or manually fix:
$env:PYTHONPATH = "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\src"
```

---

## 📊 CURRENT LINES SNAPSHOT

### Must-Monitor Games
| Game | Current | Open | Movement | Action |
|------|---------|------|----------|---------|
| PIT@CLE | CLE +7.5 | CLE +8.5 | PIT ↓1.0 | Watch injuries |
| IND@DET | DET -7.5 | DET -7.0 | DET ↑0.5 | Bet IND if holds |
| ARI@SEA | SEA -1.0 | SEA -1.5 | SEA ↓0.5 | Bet ARI soon |
| CAR@KC | KC -10.5 | KC -9.5 | KC ↑1.0 | Monitor total |

### Key Numbers Alert
- **On 3**: CHI -3.0, PHI -3.0
- **On 7**: DET -7.5, MIA -7.5  
- **On 10**: KC -10.5, WAS -10.5

---

## 📁 FILE REFERENCES

### Today's Documentation
1. **Full NFL Data**: `WEEK12_NFL_DATA_UPDATE.md`
2. **NCAAF Data**: `WEEK13_NCAAF_DATA_UPDATE.md`
3. **Session Summary**: `SESSION_SUMMARY_NOV19-20_2024.md`
4. **This Guide**: `QUICK_START_WEEK12.md`

### Key Project Files
- Analysis engine: `analyze_edges.py`
- Power ratings: `billy_walters_power_ratings.py`
- CLV tracking: `src/walters_analyzer/cli/clv_cli.py`
- Risk config: `billy_walters_risk_config.py`

---

## ⚠️ DO NOT FORGET

### Critical Reminders
1. **Bankroll Limits**: Max 3% single bet, 15% weekly
2. **Minimum Edge**: 5.5% or no bet
3. **Bye Teams**: ATL, BUF, CIN, JAX, NO, NYJ
4. **CLV Tracking**: Record EVERY bet immediately
5. **Line Shopping**: Always check 5+ books

### Billy Walters Rules
- Bet favorites early (Wednesday)
- Bet underdogs late (Saturday)
- Document everything immediately
- Process over results always
- Trust the math, not feelings

---

## 🚨 EMERGENCY FIXES

### If Scripts Won't Run
```powershell
# Option 1: Set Python path
$env:PYTHONPATH = "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\src"

# Option 2: Run from src directory
cd src
python -m walters_analyzer.analyze_edges --week 12

# Option 3: Use absolute imports fix
python fix_imports.py
```

### If Power Ratings Fail
```powershell
# Manual calculation
python -c "
old_rating = 7.15  # Bills example
true_perf = 12.0   # Week 11 actual
new_rating = (0.90 * old_rating) + (0.10 * true_perf)
print(f'New Rating: {new_rating:.2f}')
"
```

### If Odds Won't Update
1. Check `scrape_week12_odds.py`
2. Try `overtime_api_client.py` directly
3. Manual entry as last resort

---

## 📞 QUICK CONTACT REFERENCE

### Data Sources
- **Vegas Insider**: vegasinsider.com
- **Covers**: covers.com/nfl/matchups
- **ESPN**: espn.com/nfl/lines
- **Overtime**: overtime.ag/sports#/
- **Massey**: masseyratings.com/nfl

### Project Locations
- **Main**: `C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\`
- **Source**: `.\src\walters_analyzer\`
- **Data**: `.\data\week12\`
- **Output**: `.\output\`

---

## ✅ SUCCESS CHECKLIST

Before placing any bets, confirm:
- [ ] Power ratings updated with Week 11
- [ ] S-factors calculated for all games
- [ ] Injuries checked and incorporated
- [ ] Minimum 5.5% edge verified
- [ ] Bet size ≤3% of bankroll
- [ ] Weekly total ≤15% of bankroll
- [ ] Lines compared across 5+ books
- [ ] CLV tracking system ready
- [ ] All bets documented immediately

---

## 🎯 WEDNESDAY TIMELINE

### 9:00 AM - Initial Setup
- Run power ratings update
- Check overnight line moves
- Review injury reports

### 11:00 AM - Analysis
- Calculate all S-factors
- Run edge detection
- Identify qualifying bets

### 2:00 PM - Preparation
- Final injury updates
- Weather checks
- Line shopping

### 4:00 PM - Execution
- Place favorite bets
- Document with timestamps
- Set up CLV tracking

### 6:00 PM - Thursday Prep
- Final PIT/CLE analysis
- Set game alerts
- Review checklist

---

**READY TO START?**

1. Open PowerShell
2. Navigate to project: `cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer`
3. Run: `python analyze_edges.py --week 12 --bankroll 20000`
4. Review output in `.\output\week12_analysis.csv`
5. Place qualifying bets
6. Document everything

---

**Remember**: "It's not about being right, it's about being disciplined." - Billy Walters

**Good luck with Week 12!** 🏈

*Last Updated: November 19, 2024, 5:30 PM ET*