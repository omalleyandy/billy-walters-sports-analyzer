# Getting Your Monitor Running - Step by Step

## Current Situation

Your `start_monitor.py` files won't work because:
1. ❌ Your package `walters_analyzer` is not installed
2. ❌ The files reference modules that don't exist (`config_manager`, `unified_betting_system_production`)
3. ✅ You have a proper Python package structure in `src/walters_analyzer/`
4. ✅ You have existing monitoring tools: `live_odds_monitor.py`

## Quick Fix: Install Your Package First

### Step 1: Install the Package

```powershell
# Using uv (recommended for your project)
uv pip install -e .

# Or using regular pip
pip install -e .
```

This installs your `walters_analyzer` package in "editable" mode so changes are reflected immediately.

### Step 2: Verify Installation

```powershell
# Should now work
python -c "import walters_analyzer; print('✅ Package installed!')"

# Check available CLI commands
python -m walters_analyzer.cli --help
```

---

## Option A: Use Your Existing Live Odds Monitor

You already have `src/data/live_odds_monitor.py`. To run it at 1-minute intervals:

```powershell
# Check how to run it
Get-Content src\data\live_odds_monitor.py | Select-Object -Last 100

# Likely runs like this (after installing package)
python src/data/live_odds_monitor.py --interval 60
```

---

## Option B: Use the Quick Monitor I Created

I created `quick_monitor.py` which uses your installed package:

```powershell
# After installing the package
python quick_monitor.py --interval 60
```

---

## Option C: Use Your CLI Commands Directly

Your package has a CLI with commands like:

```powershell
# Analyze a specific game
python -m walters_analyzer.cli analyze-game --home "Eagles" --away "Cowboys" --spread -3.5 --research

# Scrape odds with AI monitoring
python -m walters_analyzer.cli scrape-ai --sport nfl
```

You could create a simple loop script:

```powershell
# create continuous_analysis.py
while ($true) {
    python -m walters_analyzer.cli scrape-ai --sport nfl
    Start-Sleep -Seconds 60
}
```

---

## Recommended Setup Process

### 1. Install Package (Required First Step)

```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
uv pip install -e .
```

### 2. Test Installation

```powershell
python -c "import walters_analyzer; print('✅ Package works!')"
```

### 3. Check What Monitoring Tools You Have

```powershell
# Check your existing monitor
python src/data/live_odds_monitor.py --help

# Or run it with 1-minute intervals
python src/data/live_odds_monitor.py --interval 60
```

### 4. Or Use Quick Monitor

```powershell
python quick_monitor.py --interval 60
```

---

## SMS Alerts

The SMS alert files I created (`sms_alerts.py`, `start_monitor_with_sms.py`) won't work until:

1. ✅ Package is installed
2. ✅ Monitor is integrated with your actual analysis code
3. ✅ Twilio is set up

**For now, focus on getting basic monitoring working first.**

---

## Troubleshooting

### "No module named 'walters_analyzer'"
**Solution**: Install the package with `uv pip install -e .`

### "Cannot import X from walters_analyzer"
**Solution**: Check what modules actually exist:
```powershell
Get-ChildItem src\walters_analyzer\*.py
python -c "import walters_analyzer; import pkgutil; print([m.name for m in pkgutil.iter_modules(walters_analyzer.__path__)])"
```

### Rate Limiting
**Solution**: Increase interval or check your API quotas:
- The Odds API: 500 requests/month free
- AccuWeather: Check your plan
- Adjust interval accordingly

---

## Next Steps

1. **Now**: Install package with `uv pip install -e .`
2. **Then**: Run `python src/data/live_odds_monitor.py --interval 60`
3. **Later**: Integrate SMS alerts once monitoring works
4. **Future**: Set up Windows Task Scheduler for 24/7 operation

---

## Files You Need vs Files I Created

### Won't Work (Need Package Installed):
- ❌ `start_monitor.py` (references non-existent modules)
- ❌ `start_monitor_with_sms.py` (same issue)

### Will Work:
- ✅ `quick_monitor.py` (checks for package first)
- ✅ `sms_alerts.py` (standalone module, works after Twilio setup)
- ✅ Your existing: `src/data/live_odds_monitor.py`

### Need to Fix:
- The monitor files need to import from YOUR actual modules
- After you show me what your analysis code looks like, I can fix them

---

## What to Run Right Now

```powershell
# Step 1: Install
uv pip install -e .

# Step 2: Test
python -c "import walters_analyzer; print('Works!')"

# Step 3: Show me your analysis tools
Get-Content src\walters_analyzer\cli.py | Select-Object -Last 100

# Then I can help integrate properly!
```
