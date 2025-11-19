# 🚀 WEDNESDAY MORNING QUICK START

## ⏰ 6:00 AM PT - Your 15-Minute Workflow

### **1️⃣ Get Overtime.ag Lines** (5 min)
```
Open: overtime.ag/sports#/nfl

Find these games and write down spreads:
[ ] IND @ KC: _______
[ ] LAR @ TB: _______
```

---

### **2️⃣ Fill In Script** (2 min)
```powershell
# Open editor
code check_overtime_edges.py

# Find and update these lines:
"IND @ KC": {
    "overtime_line": 3.5,  # 👈 PUT NUMBER HERE

"LAR @ TB": {
    "overtime_line": -6.5,  # 👈 PUT NUMBER HERE
```

---

### **3️⃣ Run Calculator** (1 min)
```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
python check_overtime_edges.py
```

---

### **4️⃣ Review & Bet** (7 min)
```
Look for:
✅ RECOMMENDATION: BET $XXX

Only bet if you see ✅ (not ❌)

Go to overtime.ag and place those bets
```

---

## 📝 Copy/Paste Commands

```powershell
# Navigate to project
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Run edge checker
python check_overtime_edges.py

# If you want to test the edge calculator first:
python billy_walters_edge_calculator.py
```

---

## 🎯 Decision Rules (Billy Walters)

| Rule | Action |
|------|--------|
| Edge ≥ 5.5% | ✅ BET |
| Edge < 5.5% | ❌ SKIP |
| Bet > 3% of bankroll | ❌ REDUCE to 3% max |
| Weekly total > 15% | ❌ REDUCE all bets |
| Line moved significantly | 🔄 RE-RUN script |
| Unsure which team | 🛑 STOP - don't bet |

---

## 🚨 Most Important Rules

1. **ONLY bet if edge ≥ 5.5%**
2. **NEVER exceed 3% per bet**
3. **NEVER exceed 15% per week**
4. **Screenshot everything**
5. **When in doubt, don't bet**

---

## 📞 Files You Need

| File | Purpose |
|------|---------|
| `check_overtime_edges.py` | Main tool - run Wednesday |
| `CHECK_OVERTIME_EDGES_GUIDE.md` | Detailed instructions |
| `EXAMPLE_OUTPUT.md` | What the output looks like |
| `WEEK12_BETTING_CARD.md` | Your betting strategy |
| `billy_walters_edge_calculator.py` | Core calculator (used by checker) |

---

## ⏰ This Week's Timeline

**Wednesday 6:00 AM PT:**
- [ ] Run edge checker for IND, LAR
- [ ] Place qualified bets immediately

**Thursday 4:00 AM PT:**
- [ ] Check C.J. Stroud injury status
- [ ] If OUT: Fill in BUF line, run checker, bet if qualified
- [ ] If playing: Skip BUF bet

**Saturday Morning:**
- [ ] Check Josh Jacobs & Ja'Marr Chase status
- [ ] Fill in remaining lines
- [ ] Run checker for conditional bets

---

## 💰 Expected Bets (if lines match projections)

| Game | Amount | When |
|------|--------|------|
| IND @ KC | ~$600 | Wed 6:00 AM |
| LAR @ TB | ~$500 | Wed 6:00 AM |
| CIN vs NE | ~$300 | Thu (if Chase OUT) |
| BUF @ HOU | ~$500 | Thu (if Stroud OUT) |
| GB vs MIN | ~$200 | Sat (if Jacobs plays) |

**Maximum Risk:** $2,100 (10.5% of $20K) ✅

---

## 🆘 Troubleshooting

**Script won't run?**
```powershell
# Check you're in right place
pwd
# Should show: ...\billy-walters-sports-analyzer

# Check Python works
python --version
# Should show: Python 3.x.x

# Try again
python check_overtime_edges.py
```

**Getting errors?**
- Make sure you changed `None` to a number
- Use decimals: `3.5` not `3,5`
- Don't put quotes around numbers
- Correct: `"overtime_line": 3.5,`
- Wrong: `"overtime_line": "3.5",`

**Lines moved?**
- Change the number in the script
- Re-run: `python check_overtime_edges.py`
- New edge will calculate automatically

---

## ✅ Success Checklist

Before Wednesday morning, verify:
- [ ] Script runs: `python check_overtime_edges.py`
- [ ] You see "WAITING FOR LINES" (this is correct!)
- [ ] You know how to edit the script
- [ ] Overtime.ag account is funded
- [ ] Alarm set for 6:00 AM PT
- [ ] This quick start guide printed/visible

---

## 🎊 You're Ready!

**You have:**
- ✅ Production-grade edge calculator
- ✅ Overtime.ag specific verification tool
- ✅ Week 12 betting strategy
- ✅ Billy Walters methodology (6/10 → 8/10)
- ✅ Risk management controls (3% max, 15% weekly)

**Wednesday morning = just follow the 15-minute workflow above!**

---

*Billy Walters System for Overtime.ag*  
*Week 12 - November 20, 2025*  
*Good luck! 🏈💰*
