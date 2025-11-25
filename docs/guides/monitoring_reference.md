# 1-Minute Monitoring & SMS Alerts - Quick Reference

## 🎯 Core Commands (Use These)

### Start 1-Minute Monitoring
```powershell
# All odds scrapers at 1-minute intervals
python continuous_scraper.py --interval 60

# Specific scrapers only
python continuous_scraper.py --interval 60 --scrapers overtime highlightly

# Monitor sharp money movements
python -m walters_analyzer.cli monitor-sharp

# Monitor specific game
python src\data\live_odds_monitor.py Eagles Cowboys --interval 60
```

### Run in Background
```powershell
Start-Process python `
    -ArgumentList "continuous_scraper.py --interval 60" `
    -WorkingDirectory $PWD `
    -RedirectStandardOutput "scraper.log" `
    -RedirectStandardError "scraper_errors.log" `
    -WindowStyle Hidden

# Watch logs
Get-Content scraper.log -Wait

# Stop background process
Get-Process python | Where-Object {$_.Path -like "*continuous_scraper*"} | Stop-Process
```

---

## 📱 SMS Alerts Setup

### 1. Install Twilio
```powershell
pip install twilio
```

### 2. Configure .env
Create/edit `.env` file in project root:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890
SMS_ALERT_NUMBERS=+19876543210,+18885551234
SMS_ALERTS_ENABLED=true
```

### 3. Get Twilio Credentials
1. Sign up: https://www.twilio.com/try-twilio (free $15 credit)
2. Dashboard → Account SID (copy)
3. Dashboard → Auth Token (click "View" to reveal)
4. Phone Numbers → Buy a number ($1/month)

### 4. Test SMS
```powershell
python sms_alerts.py
```

### 5. Expected Costs
- **Conservative** (75+ priority): ~$1.20-$2.40/month
- **Aggressive** (60+ priority): ~$4.80-$7.20/month
- Per SMS: $0.0079 (US)
- Free trial: $15 = ~1,900 messages

---

## 📁 Files Reference

### ✅ Working Files (Use These)
- **continuous_scraper.py** - Main 1-minute scraper
- **sms_alerts.py** - SMS module (standalone)
- **simple_monitor.py** - Basic template loop
- **quick_monitor.py** - Uses package after install

### ❌ Broken Files (Ignore These)
- **start_monitor.py** - Wrong imports, doesn't work
- **start_monitor_with_sms.py** - Wrong imports, doesn't work

### 📖 Documentation Files
- **START_HERE.md** - Quick start guide
- **MONITOR_SETUP_GUIDE.md** - Detailed setup
- **SMS_SETUP_GUIDE.md** - Complete SMS guide
- **SMS_QUICKSTART.md** - SMS quick reference

---

## 🏗️ Project Structure

```
billy-walters-sports-analyzer/
├── src/walters_analyzer/          # Main package (installed)
│   ├── cli.py                     # CLI commands
│   ├── live_odds_monitor.py       # Per-game monitor
│   └── ...
├── continuous_scraper.py          # ✅ NEW: 1-min scraper
├── sms_alerts.py                  # ✅ NEW: SMS module
├── simple_monitor.py              # ✅ NEW: Basic loop
└── .env                           # Config (create this)
```

---

## 🎛️ CLI Commands Available

```powershell
# Full help
python -m walters_analyzer.cli --help

# Analyze specific game
python -m walters_analyzer.cli analyze-game --home Eagles --away Cowboys --spread -3.5 --research

# Scrape odds sources
python -m walters_analyzer.cli scrape-overtime
python -m walters_analyzer.cli scrape-highlightly
python -m walters_analyzer.cli scrape-nfl-site

# Monitor sharp money
python -m walters_analyzer.cli monitor-sharp

# View scraped odds
python -m walters_analyzer.cli view-odds
```

---

## 📊 Monitoring Options Comparison

| Method | Interval | Coverage | Best For |
|--------|----------|----------|----------|
| `continuous_scraper.py` | 1-60 min | All games | Finding opportunities across slate |
| `monitor-sharp` | Continuous | Market movements | Detecting sharp action |
| `live_odds_monitor.py` | 1-60 min | Single game | Deep dive on one matchup |

---

## 🔧 Common Tasks

### Check What's Running
```powershell
Get-Process python
tasklist | findstr python
```

### Stop Background Monitors
```powershell
Stop-Process -Name python -Force
```

### View Recent Output
```powershell
Get-ChildItem output\pregame -Recurse | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 10
```

### Check Logs
```powershell
Get-Content scraper.log -Tail 50
Get-Content scraper_errors.log
Get-Content logs\walters-analyzer.log -Tail 50
```

---

## ⚡ Quick Start Workflow

```powershell
# 1. Test basic monitoring (2-3 iterations)
python continuous_scraper.py --interval 60

# 2. If working, run in background
Start-Process python `
    -ArgumentList "continuous_scraper.py --interval 60" `
    -WorkingDirectory $PWD `
    -RedirectStandardOutput "scraper.log" `
    -WindowStyle Hidden

# 3. Watch logs
Get-Content scraper.log -Wait

# 4. Add SMS later (optional)
pip install twilio
# Configure .env
python sms_alerts.py  # Test
```

---

## 🚨 Troubleshooting

### "No module named 'walters_analyzer'"
```powershell
uv pip install -e .
```

### "TWILIO_ACCOUNT_SID not found"
```powershell
# Create .env file in project root with credentials
```

### High API costs
```powershell
# Increase interval
python continuous_scraper.py --interval 300  # 5 minutes

# Reduce scrapers
python continuous_scraper.py --interval 60 --scrapers overtime
```

### Rate limiting errors
```powershell
# Increase interval to 2+ minutes
python continuous_scraper.py --interval 120
```

---

## 📝 Important Notes

1. **SMS Throttling**: Built-in rate limiting
   - Max 1 SMS per game per 5 minutes
   - Quiet hours: midnight-7am (no SMS)
   - Daily limit: 100 messages

2. **API Quotas**:
   - The Odds API: 500 requests/month free
   - AccuWeather: Check your plan
   - Adjust intervals accordingly

3. **Billy Walters Principles** (always apply):
   - Minimum 5.5% edge before betting
   - Single bet ≤3% bankroll
   - Weekly exposure ≤15%
   - Track CLV (Closing Line Value)

4. **Data Accuracy**:
   - Always validate schedule before analysis
   - Verify team names and bye weeks
   - Cross-reference multiple sources

---

## 🔗 External Resources

- **Twilio Console**: https://console.twilio.com
- **Twilio Docs**: https://www.twilio.com/docs/sms
- **The Odds API**: https://the-odds-api.com
- **System Logs**: `logs/walters-analyzer.log`

---

**Last Updated**: November 16, 2025  
**Version**: 1.0  
**Project**: Billy Walters Sports Analyzer
