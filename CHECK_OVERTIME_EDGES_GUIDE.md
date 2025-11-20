# How to Use check_overtime_edges.py

## 📋 Wednesday Morning Workflow

### **Step 1: Go to Overtime.ag (6:00 AM PT)**
1. Open browser: `overtime.ag/sports#/nfl`
2. Look for Week 12 games
3. Write down the spreads for each game

### **Step 2: Fill in the Lines**

Open `check_overtime_edges.py` in your editor and find these sections:

```python
"IND @ KC": {
    "overtime_line": None,  # 👈 Change this!
```

**Example - If Overtime shows: IND +3.5**
```python
"IND @ KC": {
    "overtime_line": 3.5,  # ✅ Fill in the number
```

**Example - If Overtime shows: KC -3.5**
```python
"IND @ KC": {
    "overtime_line": -3.5,  # ✅ Negative for favorite
```

### **Step 3: Run the Script**

```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
python check_overtime_edges.py
```

### **Step 4: Review Output**

The script will show you:
- ✅ **QUALIFIED BETS** - Place these immediately
- ❌ **REJECTED BETS** - Edge below 5.5%, skip these
- ⏳ **WAITING FOR LINES** - Fill in more lines and re-run

### **Step 5: Place Bets on Overtime.ag**

Only place bets that show:
```
✅ RECOMMENDATION: BET $500
```

---

## 📝 Example: Filling in IND @ KC

**What you see on Overtime.ag:**
```
Indianapolis Colts @ Kansas City Chiefs
Spread: IND +3.5 (-110)
```

**What to put in the script:**
```python
"IND @ KC": {
    "overtime_line": 3.5,  # Positive because Colts are underdog
```

**What you see on Overtime.ag:**
```
LA Rams @ Tampa Bay Buccaneers
Spread: LAR -6.5 (-110)
```

**What to put in the script:**
```python
"LAR @ TB": {
    "overtime_line": -6.5,  # Negative because Rams are favorite
```

---

## 🔢 Quick Reference: Positive vs Negative

| Team Status | Example Line | What to Enter |
|-------------|--------------|---------------|
| **Underdog** (getting points) | IND +3.5 | `3.5` |
| **Favorite** (giving points) | KC -3.5 | `-3.5` |
| **Underdog** (getting points) | TB +6.5 | `6.5` |
| **Favorite** (giving points) | LAR -6.5 | `-6.5` |

**Easy rule:** Copy the sign (+/-) from Overtime.ag

---

## ⚠️ Important Notes

1. **Re-run after each update**
   - Fill in one game? Re-run script
   - Want to update a line? Change it and re-run

2. **Thursday morning for BUF @ HOU**
   - Check C.J. Stroud injury status first
   - Only fill in this line if Stroud is OUT

3. **Screenshot everything**
   - Script output
   - Overtime.ag confirmation screens
   - Keep for records

4. **If edge < 5.5%**
   - DO NOT BET
   - Even if the betting card said to
   - Actual lines matter more than projections

---

## 💡 Pro Tips

### **Line Shopping Within Overtime**
- Check both "Game Lines" and "Alternate Spreads"
- Sometimes better value on alternate lines
- Script works with any line you input

### **Timing Matters**
- Lines open ~6:00 AM PT Wednesday
- Sharp money moves lines by 9:00 AM PT
- Best edges often in first 1-2 hours

### **If Lines Move**
- Don't chase bad numbers
- If line moves away from you, edge decreases
- Better to skip than force a bet

---

## 🆘 Troubleshooting

**Script won't run?**
```powershell
# Make sure you're in the right directory
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Make sure billy_walters_edge_calculator.py exists
dir billy_walters_edge_calculator.py

# Run again
python check_overtime_edges.py
```

**Getting errors?**
- Check that you entered numbers only (no + or - symbols in quotes)
- Use decimal points: `3.5` not `3,5`
- Make sure to change `None` to a number

---

## 📅 Reusable for Future Weeks

Just update the games section for next week:
1. Change game matchups
2. Update our power ratings
3. Update S-factor points
4. Update expected lines
5. Run same process!

---

**Ready for Wednesday morning! 🏈💰**
