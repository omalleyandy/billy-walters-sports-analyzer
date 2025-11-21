# Week 12 CLV Tracking & Line Monitoring Guide

## 🎯 Complete System Overview

You now have two integrated systems:
1. **CLV Tracking** - Track performance vs closing lines
2. **Line Movement Monitor** - Watch real-time line changes

---

## 📋 Quick Start (5 Minutes)

### Step 1: Record Your Bets
```powershell
python week12_clv_recorder.py
```

**What this does:**
- Records all 4 Week 12 recommended bets
- Captures opening lines
- Sets up CLV tracking

**Expected output:**
```
WEEK 12 CLV BET RECORDING
Recording 4 bets...

[1] RECORDED: IND_KC
    Pick: Indianapolis Colts +3.5
    Edge: 8.2%
    Stake: $500
    ID: WEEK12_IND_KC
...
```

---

### Step 2: Start Line Monitoring
```powershell
# Option A: Single check (quick test)
python week12_line_monitor.py --once

# Option B: Continuous monitoring (recommended)
python week12_line_monitor.py --interval 300
```

**What this does:**
- Fetches current odds every 5 minutes (300 seconds)
- Tracks line movements
- Shows your CLV in real-time
- Alerts on significant moves (±0.5+ points)

**Expected output:**
```
WEEK 12 LINE MOVEMENT STATUS
======================================================================

IND_KC: Indianapolis Colts @ Kansas City Chiefs
  Original Line: +3.5
  Current Line:  +3.0
  Movement:      -0.5 points
  Your Bet Line: +3.5
  Current CLV:   -0.5 points [BAD - losing to current line]
...
```

---

## 🔄 Complete Workflow

### Tuesday/Wednesday (Bet Placement)
```powershell
# 1. Record bets
python week12_clv_recorder.py

# 2. Start monitoring in background
# Open new PowerShell window:
python week12_line_monitor.py --interval 300
```

**Keep monitor running** throughout the week to track movements.

---

### Saturday Evening (Before Games)
```powershell
# Check current line status
python week12_line_monitor.py --once
```

---

### Sunday (Game Time - Update Closing Lines)

**IMPORTANT:** Record closing lines right before each game starts!

```powershell
# Edit week12_clv_updater.py - Update this section:

closing_lines = {
    'WEEK12_IND_KC': 3.5,    # ← PUT ACTUAL CLOSING LINE HERE
    'WEEK12_LAR_TB': -6.5,   # ← PUT ACTUAL CLOSING LINE HERE
    'WEEK12_CIN_NE': 7.0,    # ← PUT ACTUAL CLOSING LINE HERE
    'WEEK12_SEA_TEN': -13.5, # ← PUT ACTUAL CLOSING LINE HERE
}

# Then run:
python week12_clv_updater.py update-closing
```

**Expected output:**
```
UPDATE CLOSING LINES - WEEK 12
======================================================================

[1] UPDATED: IND_KC
    Bet Line:     +3.5
    Closing Line: +3.0
    CLV:          +0.5 points [BEAT CLOSING LINE ✓]
...
```

---

### Monday (After Games - Update Results)

**After all games complete**, update results:

```powershell
# Edit week12_clv_updater.py - Update this section:

results = {
    'WEEK12_IND_KC': 'won',     # ← won/lost/push
    'WEEK12_LAR_TB': 'won',     # ← won/lost/push
    'WEEK12_CIN_NE': 'lost',    # ← won/lost/push
    'WEEK12_SEA_TEN': 'won',    # ← won/lost/push
}

# Then run:
python week12_clv_updater.py update-results
```

**Expected output:**
```
UPDATE RESULTS - WEEK 12
======================================================================

[1] UPDATED: IND_KC
    Result: WON
    Profit: $+455.00
    CLV:    +0.5 points
...
```

---

### View Complete Summary
```powershell
python week12_clv_updater.py summary
```

**Shows:**
- Total bets placed
- CLV performance (% beating closing line)
- Average CLV in points
- Win/Loss record
- Total profit/loss
- ROI%

---

## 📊 Understanding CLV

### What is CLV (Closing Line Value)?

**CLV measures if you got better odds than the final line before the game.**

**Example:**
- You bet: IND +3.5 (opening line)
- Closing line: IND +3.0
- **Your CLV: +0.5 points ✅ GOOD!**

**Why CLV matters:**
- More important than short-term win rate
- Best predictor of long-term profitability
- Billy Walters: "Beat the closing line, you'll win over time"

**Target CLV Metrics:**
- **Good:** >55% of bets beat closing line
- **Great:** Average CLV >+0.3 points
- **Elite:** >60% beat closing + avg >+0.5 points

---

## ⏱️ Monitoring Schedule

### Aggressive (Recommended for Week 12)
```powershell
# Check every 5 minutes during betting hours
python week12_line_monitor.py --interval 300
```

### Moderate
```powershell
# Check every 15 minutes
python week12_line_monitor.py --interval 900
```

### Passive
```powershell
# Check every hour
python week12_line_monitor.py --interval 3600
```

---

## 🎯 Billy Walters Strategy Integration

### Bet Timing Based on Monitoring

**If CLV is POSITIVE (you're beating current line):**
- ✅ Hold your position
- ✅ You got good value
- ✅ Don't second-guess yourself

**If CLV is NEGATIVE (line moved against you):**
- ⚠️ Evaluate why (injury? sharp money?)
- ⚠️ Consider if new information changes your edge
- ❌ Don't panic - variance is normal

**Significant Movement Alerts:**
- **±1.0+ points:** Major move - investigate cause
- **±0.5 points:** Notable - check injury reports
- **<0.5 points:** Normal noise

---

## 📁 File Locations

All data is saved automatically:

```
data/
├── clv/
│   ├── bets/               # Individual bet records (JSON)
│   └── clv_tracking.csv    # Summary CSV for Excel
└── line_history.json       # Line movement history
```

---

## 🔧 Troubleshooting

### Issue: "No module named 'overtime_api_client'"
**Fix:**
```powershell
# Ensure you're in project directory
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
python week12_line_monitor.py --once
```

### Issue: "No bets recorded"
**Fix:**
```powershell
# Run recorder first
python week12_clv_recorder.py
# Then try monitor again
python week12_line_monitor.py --once
```

### Issue: Monitor stops running
**Fix:**
- Press Ctrl+C to stop cleanly
- Restart: `python week12_line_monitor.py --interval 300`
- Data is saved automatically

---

## 📈 Success Metrics (100-Bet Target)

After 100 bets, evaluate:

1. **CLV Performance**
   - Target: >55% beat closing line
   - Your avg CLV: >+0.3 points

2. **Win Rate**
   - Target: 54-57%
   - Break-even: 52.38%

3. **ROI**
   - Target: 5-8%
   - Good: >3%

4. **Process Adherence**
   - All bets ≥5.5% edge ✓
   - Risk limits maintained ✓
   - No emotional overrides ✓

---

## 🚀 Advanced Usage

### Export to CSV
```powershell
# View CSV in Excel
data\clv\clv_tracking.csv
```

### Multiple Weeks
```powershell
# System automatically handles multiple weeks
# Each bet gets unique recommendation_id
# Weekly summaries available via reporter
```

### Custom Monitoring
```python
# Edit week12_line_monitor.py
# Add your own games to tracked_games dict
self.tracked_games = {
    'YOUR_GAME': {'away': 'Team A', 'home': 'Team B'},
    ...
}
```

---

## ⚡ One-Command Quick Reference

```powershell
# 1. Setup (once)
python week12_clv_recorder.py

# 2. Monitor (ongoing)
python week12_line_monitor.py --interval 300

# 3. Before games (closing lines)
python week12_clv_updater.py update-closing

# 4. After games (results)
python week12_clv_updater.py update-results

# 5. View summary (anytime)
python week12_clv_updater.py summary
```

---

## 🎊 You're All Set!

Your Week 12 betting system now includes:
- ✅ Automated CLV tracking
- ✅ Real-time line movement monitoring
- ✅ Historical data storage
- ✅ Performance analytics
- ✅ Billy Walters methodology compliance

**Start monitoring now and beat those closing lines!** 🏈

---

**Need Help?**
- Check troubleshooting section above
- Review individual script comments
- All systems save data automatically
- You can't break anything - data is backed up

**Good luck with Week 12!** 📊
