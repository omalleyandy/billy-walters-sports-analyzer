# QUICK START - What to Run Right Now

## TL;DR

You need to **install your package first**, then everything will work.

```powershell
# Run this NOW
uv pip install -e .

# Then test
python simple_monitor.py --interval 60
```

---

## Three Options (Ranked by Ease)

### 🟢 Option 1: Simple Monitor (Works Immediately)

**No setup required - works right now:**

```powershell
python simple_monitor.py --interval 60
```

This is just a template loop. You'll need to add your actual analysis code where it says "YOUR ANALYSIS CODE GOES HERE".

**Pros**: Works immediately, no dependencies
**Cons**: You need to add your own analysis logic

---

### 🟡 Option 2: Install Package + Use Your Existing Tools

**Requires 1 minute of setup:**

```powershell
# Step 1: Install (required)
uv pip install -e .

# Step 2: Verify
python -c "import walters_analyzer; print('✅ Works!')"

# Step 3: Use your existing monitor
python src/data/live_odds_monitor.py --interval 60

# Or use quick_monitor
python quick_monitor.py --interval 60
```

**Pros**: Uses your real analysis code
**Cons**: Requires package installation first

---

### 🔴 Option 3: Full Integration with SMS

**Requires Twilio setup + package installation:**

```powershell
# Step 1: Install package
uv pip install -e .

# Step 2: Install Twilio
uv pip install twilio

# Step 3: Configure .env (see SMS_SETUP_GUIDE.md)
# TWILIO_ACCOUNT_SID=...
# TWILIO_AUTH_TOKEN=...
# etc.

# Step 4: Test SMS
python sms_alerts.py

# Step 5: Run enhanced monitor
python start_monitor_with_sms.py --interval 60
```

**Pros**: Full featured with text alerts
**Cons**: Most setup required

---

## What's Broken and Why

### ❌ `start_monitor.py` - Won't Work Yet
**Problem**: Tries to import `config_manager`, `unified_betting_system_production` which don't exist in your project

**Fix**: Need to rewrite imports to use YOUR actual modules after package is installed

### ❌ `start_monitor_with_sms.py` - Won't Work Yet  
**Problem**: Same import issues + needs Twilio setup

**Fix**: Install package + Twilio first

### ✅ `simple_monitor.py` - Works Now
**No problems**: Just a basic loop, add your code

### ✅ `sms_alerts.py` - Works Now
**No problems**: Standalone module, just needs Twilio credentials

### ✅ `quick_monitor.py` - Works After Install
**Minor issue**: Needs package installed first

---

## My Recommendation

**Do this right now:**

```powershell
# Option 1: Quick test with simple_monitor
python simple_monitor.py --interval 60
# (Press Ctrl+C after 2-3 iterations to stop)

# Option 2: Proper setup
uv pip install -e .
python quick_monitor.py --interval 60
```

**Then tell me:**
1. Did the package install work?
2. What error (if any) did you get?
3. Do you want SMS alerts or just basic monitoring?

**Then I can:**
- Fix the broken monitor files to use YOUR actual code
- Integrate with your real analysis functions  
- Set up SMS properly if desired

---

## Files Summary

| File | Status | Purpose |
|------|--------|---------|
| `simple_monitor.py` | ✅ Works now | Basic loop template |
| `quick_monitor.py` | ⚠️ Needs install | Uses your package |
| `start_monitor.py` | ❌ Broken | Wrong imports |
| `start_monitor_with_sms.py` | ❌ Broken | Wrong imports |
| `sms_alerts.py` | ✅ Works | SMS module |
| Your existing: `src/data/live_odds_monitor.py` | ⚠️ Needs install | Your real monitor |

---

## Next Command to Run

```powershell
# Pick ONE of these:

# A) Test basic loop now (no setup)
python simple_monitor.py --interval 60

# B) Install package then use real tools
uv pip install -e .
python quick_monitor.py --interval 60

# C) Use your existing monitor (after install)
uv pip install -e .
python src/data/live_odds_monitor.py --interval 60
```

---

## Background Execution (After Working)

Once you have a working monitor, run in background:

```powershell
# PowerShell background execution
Start-Process python `
    -ArgumentList "simple_monitor.py --interval 60" `
    -WorkingDirectory $PWD `
    -RedirectStandardOutput "monitor.log" `
    -RedirectStandardError "monitor_errors.log" `
    -WindowStyle Hidden

# Watch logs
Get-Content monitor.log -Wait
```

---

**Bottom line**: Run `uv pip install -e .` first, then everything else becomes easy!
