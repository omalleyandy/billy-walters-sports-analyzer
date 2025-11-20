# 🚀 LIVE ODDS SCRAPER - Quick Start Guide (UV Version)

## 📋 What This Does

**scrape_week12_odds.py** automatically:
1. ✅ Fetches **LIVE odds** from Overtime.ag (no manual entry!)
2. ✅ Identifies Week 12 games
3. ✅ Calculates edges using Billy Walters methodology
4. ✅ Shows betting recommendations with actual spreads
5. ✅ Tells you exactly which team to bet and how much

---

## ⚡ Quick Start (30 seconds)

### **Step 1: Install Required Package (using UV)**
```powershell
# Install httpx with UV
uv pip install httpx
```

### **Step 2: Run the Scraper**
```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
python scrape_week12_odds.py
```

**That's it!** The script will:
- Fetch live odds from Overtime.ag
- Calculate all edges automatically
- Show you exactly what to bet

---

## 📊 Example Output

```
================================================================================
WEEK 12 LIVE ODDS SCRAPER - OVERTIME.AG
Scraped: Wednesday, November 20, 2025 at 06:15 AM
================================================================================

📥 Fetching live NFL odds from Overtime.ag...
✅ Received 14 NFL games

================================================================================
ANALYZING WEEK 12 GAMES
================================================================================

================================================================================
🏈 IND @ KC
================================================================================
📅 Game Time: Sunday, November 24, 2025 1:00 PM ET
📝 Notes: Colts off bye, playoff push
🎯 Priority: HIGH

📊 OVERTIME.AG LIVE ODDS:
   Indianapolis Colts: +3.5
   Kansas City Chiefs: -3.5

💡 EDGE ANALYSIS:
   Our Line: +0.5
   Overtime Line: +3.5
   Base Edge: 3.0 points
   S-Factors: +2.25 points
   Key Numbers: [1, 2, 3]
   Key Premium: +14.0%

🎯 TOTAL EDGE: 19.2%
   Confidence: HIGH
   ⭐ Stars: 3.0

💰 BET SIZING:
   Recommended: $600 (3.0%)

================================================================================
✅ RECOMMENDATION: BET $600

🎯 BET: Indianapolis Colts +3.5
================================================================================

[... more games ...]

================================================================================
📋 BETTING SUMMARY
================================================================================

✅ QUALIFIED BETS (2 games):

   🎯 IND @ KC
      Team: Indianapolis Colts +3.5
      Amount: $600
      Edge: 19.2%
      Stars: 3.0 ⭐
      Priority: HIGH

   🎯 LAR @ TB
      Team: LA Rams -6.5
      Amount: $500
      Edge: 13.0%
      Stars: 2.5 ⭐
      Priority: HIGH

================================================================================
💰 TOTAL RISK: $1,100 (5.5%)
✅ Within 15% weekly limit

📝 NEXT STEPS:
   1. Go to overtime.ag/sports#/nfl
   2. Verify lines haven't moved
   3. Place bets in priority order
   4. Screenshot confirmations

================================================================================
⚠️  REMEMBER: Only bet if edge >= 5.5%!
================================================================================

💾 Results saved to: output/week12_live_odds.json
```

---

## 🎯 What The Output Means

### **✅ RECOMMENDATION: BET $600**
- Script calculated edge ≥ 5.5%
- Billy Walters methodology approves this bet
- **Place this bet immediately**

### **❌ RECOMMENDATION: NO BET**
- Edge below 5.5% minimum
- **Skip this game**
- Wait for better lines or move on

### **🎯 BET: Indianapolis Colts +3.5**
- This tells you EXACTLY which team to bet
- This tells you the EXACT spread
- Go to Overtime.ag and bet Colts +3.5

---

## ⏰ When To Run This

### **Wednesday Morning (6:00 AM PT)**
```powershell
python scrape_week12_odds.py
```
- Lines just opened
- Best time for sharp value
- Place HIGH priority bets immediately

### **Thursday Morning (4:00 AM PT)**
```powershell
python scrape_week12_odds.py
```
- Check Thursday Night Football game (BUF @ HOU)
- Only bet if C.J. Stroud is OUT

### **Saturday Morning**
```powershell
python scrape_week12_odds.py
```
- Check conditional bets (CIN, GB)
- Final injury reports available

### **Anytime During Week**
- Run whenever you want updated edges
- Lines change constantly
- Re-run to see if new opportunities appear

---

## 🔄 Advantages Over Manual Method

### **OLD WAY** (check_overtime_edges.py):
1. Go to Overtime.ag ❌
2. Write down each spread ❌
3. Open script ❌
4. Fill in numbers manually ❌
5. Run script ❌
6. Review results ❌

**Time:** 15 minutes

### **NEW WAY** (scrape_week12_odds.py):
1. Run: `python scrape_week12_odds.py` ✅

**Time:** 30 seconds

---

## 💡 Pro Tips

### **1. Run Before Placing Bets**
```powershell
# Always get fresh odds right before betting
python scrape_week12_odds.py
```

### **2. Compare To Check If Lines Moved**
```powershell
# Morning scrape
python scrape_week12_odds.py > morning_odds.txt

# Evening scrape
python scrape_week12_odds.py > evening_odds.txt

# Compare
diff morning_odds.txt evening_odds.txt
```

### **3. Save Results**
The script automatically saves to `output/week12_live_odds.json`:
```json
{
  "scrape_time": "2025-11-20T06:15:00",
  "qualified_bets": [
    {
      "game": "IND @ KC",
      "bet_team": "Indianapolis Colts",
      "line": "+3.5",
      "amount": 600,
      "edge": 19.2
    }
  ]
}
```

---

## 🆘 Troubleshooting

### **Error: httpx not found**
```powershell
uv pip install httpx
```

### **Error: UV not found**
```powershell
# Install UV package manager
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

### **Error: Can't connect to Overtime.ag**
- Check internet connection
- Try again (API might be temporarily down)
- Check if Overtime.ag is accessible in browser

### **No games found**
- Lines might not be posted yet (too early Wednesday)
- Week 12 games might not be in system yet
- Check overtime.ag/sports#/nfl in browser

### **Script hangs**
- Press Ctrl+C to stop
- Check internet connection
- Try again

---

## 📁 Files You Need

| File | What It Does |
|------|--------------|
| `scrape_week12_odds.py` | Main scraper ✅ |
| `billy_walters_edge_calculator.py` | Edge calculator ✅ |
| **httpx** package | HTTP requests (install with `uv pip install httpx`) |

---

## 🎯 Wednesday Morning Workflow

### **UPDATED 10-Minute Workflow:**

```
⏰ 6:00 AM PT - Wake up

⚡ 6:01 AM - Run scraper:
python scrape_week12_odds.py

📊 6:02 AM - Review recommendations

✅ 6:05 AM - Place bets on Overtime.ag
           - Screenshot confirmations

☕ 6:10 AM - Done!
```

**Total time: 10 minutes** (down from 15!)

---

## 🚀 Key Benefits

1. **✅ No Manual Data Entry** - Script gets odds automatically
2. **✅ Always Current** - Fetches live odds every time you run it
3. **✅ Accurate** - No typos from manual entry
4. **✅ Fast** - 30 seconds instead of 15 minutes
5. **✅ Reliable** - Uses Overtime's actual API
6. **✅ Reusable** - Works for future weeks too

---

## 🎊 You're Ready!

**Old workflow:**
- Manual line entry
- 15 minutes
- Risk of typos

**New workflow:**
- Automatic scraping
- 30 seconds
- Billy Walters edges calculated instantly

**Run this Wednesday morning and let the script do all the work!**

---

## 📦 UV Package Manager Commands

```powershell
# Install httpx
uv pip install httpx

# Update httpx
uv pip install --upgrade httpx

# Check what's installed
uv pip list

# Remove httpx (if needed)
uv pip uninstall httpx
```

---

*Week 12 Live Odds Scraper*  
*Billy Walters NFL System for Overtime.ag*  
*UV Package Manager Version*  
*Created: November 19, 2025*
