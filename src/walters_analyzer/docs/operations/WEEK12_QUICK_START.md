# QUICK START - Week 12 NFL Analysis
**Purpose:** Get running in under 5 minutes  
**Updated:** November 19, 2024, 5:30 PM ET  
**Production Location:** src/walters_analyzer/docs/operations/

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

```powershell
# Quick status check
python check_status.py --verbose

# Run analysis
python analyze_edges.py --week 12 --bankroll 20000 --min-edge 5.5

# View current opportunities
python view_opportunities.py --week 12 --min-priority 60

# Start monitoring
python start_monitor.py --interval 60

# Record bet (CLV)
python -m walters_analyzer.cli.clv_cli record-bet --game "AWAY_HOME" --bet-type spread --line X.X --amount XXX

# Fix imports if needed
python fix_imports.py
```

---

## ⚠️ CRITICAL REMINDERS

### Before Placing ANY Bet
1. ✅ Edge ≥5.5% (minimum threshold)
2. ✅ Bet ≤3% of bankroll (absolute max)
3. ✅ Weekly total ≤15% of bankroll
4. ✅ Schedule validated (no bye weeks!)
5. ✅ Latest injury reports checked
6. ✅ Weather forecast reviewed
7. ✅ Line shopped across 5+ books

### Risk Management (NON-NEGOTIABLE)
- Single bet max: $600 (3% of $20K)
- Weekly exposure max: $3,000 (15% of $20K)
- Stop-loss: $2,000 weekly drawdown (10%)
- Minimum edge: 5.5% (no exceptions)

---

## 🚀 IF YOU ONLY HAVE 5 MINUTES

```powershell
# Run this sequence
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
python check_status.py
python analyze_edges.py --week 12 --bankroll 20000
python view_opportunities.py --week 12
```

Then review the output and decide:
1. Are there 5.5%+ edges?
2. Is this the right time to bet (favorites early, dogs late)?
3. Do injury reports change the analysis?

---

## 📚 FULL DOCUMENTATION

For complete details, see:
- **Session Continuity**: `src/walters_analyzer/docs/session_continuity/WEEK12_CONTINUITY.md`
- **Methodology**: `src/walters_analyzer/docs/methodology/BILLY_WALTERS_PRINCIPLES.md`
- **Troubleshooting**: `src/walters_analyzer/docs/operations/TROUBLESHOOTING.md`

---

**Production Status:** Ready for Week 12  
**Next Review:** Wednesday morning (injury reports)  
**Priority:** Update power ratings FIRST!
