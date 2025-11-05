# Windows Environment Variables - Setup Complete

## ✅ What Was Done

Your project now uses **Windows environment variables** instead of `.env` files for better security and ease of maintenance.

## Current Status

### Already Configured ✅
- `OV_CUSTOMER_ID` = DAL519
- `ACCUWEATHER_API_KEY` = ***configured***
- `OPENWEATHER_API_KEY` = ***configured***

### Needs Configuration ❌
- `OV_CUSTOMER_PASSWORD` - Add your overtime.ag password

## Quick Setup

### Add the Missing Password

**Option 1: PowerShell Command** (Run as Administrator)
```powershell
[System.Environment]::SetEnvironmentVariable('OV_CUSTOMER_PASSWORD', 'your_password', 'User')
```

**Option 2: Windows Settings GUI**
1. Press `Win + X` → "System"
2. "Advanced system settings" → "Environment Variables"
3. Under "User variables" → "New"
4. Variable name: `OV_CUSTOMER_PASSWORD`
5. Variable value: Your actual password
6. Click OK

**Then restart your terminal/IDE!**

### Verify Setup
```powershell
.\scripts\verify_env_vars.ps1
```

## Using the System

### No .env File Needed!

Just run your scrapers normally:

```powershell
# Single scrape
uv run scrapy crawl overtime_live

# Continuous monitoring
uv run scrapy crawl overtime_live -a monitor=10

# Test integration
uv run python tests/test_cdp_integration.py
```

### Optional: Add More Variables

**Bankroll Settings:**
```powershell
[System.Environment]::SetEnvironmentVariable('BANKROLL', '10000.0', 'User')
[System.Environment]::SetEnvironmentVariable('KELLY_FRACTION', '0.25', 'User')
[System.Environment]::SetEnvironmentVariable('MAX_BET_PERCENTAGE', '0.03', 'User')
```

**Redis (for distributed odds tracking):**
```powershell
[System.Environment]::SetEnvironmentVariable('REDIS_HOST', 'localhost', 'User')
[System.Environment]::SetEnvironmentVariable('REDIS_PORT', '6379', 'User')
[System.Environment]::SetEnvironmentVariable('REDIS_DB', '0', 'User')
```

**Monitoring:**
```powershell
[System.Environment]::SetEnvironmentVariable('OVERTIME_MONITOR_INTERVAL', '10', 'User')
```

## Benefits of This Approach

✅ **More Secure** - Credentials in Windows profile, not files  
✅ **No File Maintenance** - No `.env` files to manage  
✅ **System-Wide** - Available to all applications  
✅ **Git-Safe** - Nothing to accidentally commit  
✅ **Professional** - Industry standard approach  

## Files Created

1. **`scripts/set_windows_env_vars.ps1`** - Batch setup script
2. **`scripts/verify_env_vars.ps1`** - Check what's configured
3. **`docs/WINDOWS_ENV_SETUP.md`** - Complete guide

## Changes Made

- ✅ Removed `python-dotenv` from required dependencies
- ✅ Made `.env` files completely optional
- ✅ Spiders now use Windows environment variables directly
- ✅ Backward compatible - still works with `.env` if you install `python-dotenv`

## Troubleshooting

### "Variables not found"
- Make sure to **restart terminal/IDE** after setting variables
- Verify with: `.\scripts\verify_env_vars.ps1`

### Still want .env files?
```powershell
uv sync --extra dotenv
```

## Next Steps

1. ✅ Add `OV_CUSTOMER_PASSWORD` environment variable
2. ✅ Restart terminal/IDE
3. ✅ Run: `.\scripts\verify_env_vars.ps1`
4. ✅ Test: `uv run scrapy crawl overtime_live`

---

**See full documentation:** `docs/WINDOWS_ENV_SETUP.md`

