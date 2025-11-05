# Complete Environment Variables Reference

## 📋 All Variables from Your .env File

Based on your current `.env` file, here are **all** the variables you should migrate to Windows environment variables:

### ✅ Required Variables (Must Set)

```powershell
# Weather API
ACCUWEATHER_API_KEY = ***CONFIGURED*** (you already have this)

# Overtime.ag Credentials
OV_CUSTOMER_ID = DAL519 (you already have this)
OV_PASSWORD = ***CONFIGURED*** (your actual password)
```

### 🌐 Proxy Configuration (Important for Scraping)

```powershell
# Proxy for scraping (you're using scrapegw.com)
PROXY_URL = http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060
PROXY_USER = 5iwdzupyp3mzyv6
PROXY_PASS = 9cz69tojhtqot8f
OVERTIME_PROXY = http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060
```

### 🎯 Overtime.ag Configuration

```powershell
# Target URLs
OVERTIME_LIVE_URL = https://overtime.ag/sports#/integrations/liveBetting
OVERTIME_START_URL = https://overtime.ag/sports
OV_LOGIN_URL = https://overtime.ag/login

# Sport filters
OVERTIME_SPORT = FOOTBALL
OVERTIME_COMP = College Football

# Output directory
OVERTIME_OUT_DIR = data/overtime

# Storage state (optional)
OV_STORAGE_STATE = .overtime_state.json
```

### 🤖 AI/API Keys

```powershell
# Anthropic (Claude API)
ANTHROPIC_API_KEY = ***CONFIGURED*** (your actual key)
```

## 🚀 Quick Migration Commands

### Option 1: Use the Migration Script (Recommended)

```powershell
# The script will read your .env and set everything automatically
.\scripts\migrate_env_to_windows.ps1

# Dry run first to see what will be set (no changes made)
.\scripts\migrate_env_to_windows.ps1 -DryRun
```

### Option 2: Set Manually (One-by-One)

```powershell
# Run as Administrator
# Weather
[System.Environment]::SetEnvironmentVariable('ACCUWEATHER_API_KEY', 'YOUR_ACTUAL_KEY', 'User')

# Overtime.ag
[System.Environment]::SetEnvironmentVariable('OV_CUSTOMER_ID', 'DAL519', 'User')
[System.Environment]::SetEnvironmentVariable('OV_PASSWORD', 'YOUR_ACTUAL_PASSWORD', 'User')
[System.Environment]::SetEnvironmentVariable('OV_LOGIN_URL', 'https://overtime.ag/login', 'User')

# Proxy (use your actual credentials)
[System.Environment]::SetEnvironmentVariable('PROXY_URL', 'http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060', 'User')
[System.Environment]::SetEnvironmentVariable('PROXY_USER', '5iwdzupyp3mzyv6', 'User')
[System.Environment]::SetEnvironmentVariable('PROXY_PASS', '9cz69tojhtqot8f', 'User')
[System.Environment]::SetEnvironmentVariable('OVERTIME_PROXY', 'http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060', 'User')

# Overtime URLs
[System.Environment]::SetEnvironmentVariable('OVERTIME_LIVE_URL', 'https://overtime.ag/sports#/integrations/liveBetting', 'User')
[System.Environment]::SetEnvironmentVariable('OVERTIME_START_URL', 'https://overtime.ag/sports', 'User')

# Overtime Config
[System.Environment]::SetEnvironmentVariable('OVERTIME_SPORT', 'FOOTBALL', 'User')
[System.Environment]::SetEnvironmentVariable('OVERTIME_COMP', 'College Football', 'User')
[System.Environment]::SetEnvironmentVariable('OVERTIME_OUT_DIR', 'data/overtime', 'User')
[System.Environment]::SetEnvironmentVariable('OV_STORAGE_STATE', '.overtime_state.json', 'User')

# AI APIs
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'YOUR_ACTUAL_KEY', 'User')
```

## 📝 Variable Mapping

| .env Variable | Windows Env Var | Purpose | Required |
|---------------|-----------------|---------|----------|
| `ACCUWEATHER_API_KEY` | `ACCUWEATHER_API_KEY` | Weather data | ✅ Yes |
| `OV_CUSTOMER_ID` | `OV_CUSTOMER_ID` | Overtime login | ✅ Yes |
| `OV_PASSWORD` | `OV_PASSWORD` | Overtime password | ✅ Yes |
| `PROXY_URL` | `PROXY_URL` | Scraping proxy | 🔶 Recommended |
| `PROXY_USER` | `PROXY_USER` | Proxy username | 🔶 Recommended |
| `PROXY_PASS` | `PROXY_PASS` | Proxy password | 🔶 Recommended |
| `OVERTIME_PROXY` | `OVERTIME_PROXY` | Overtime-specific proxy | 🔶 Recommended |
| `OVERTIME_LIVE_URL` | `OVERTIME_LIVE_URL` | Target URL | ⚪ Optional |
| `OVERTIME_START_URL` | `OVERTIME_START_URL` | Fallback URL | ⚪ Optional |
| `OV_LOGIN_URL` | `OV_LOGIN_URL` | Login page | ⚪ Optional |
| `OVERTIME_SPORT` | `OVERTIME_SPORT` | Sport filter | ⚪ Optional |
| `OVERTIME_COMP` | `OVERTIME_COMP` | Competition filter | ⚪ Optional |
| `OVERTIME_OUT_DIR` | `OVERTIME_OUT_DIR` | Output directory | ⚪ Optional |
| `OV_STORAGE_STATE` | `OV_STORAGE_STATE` | Session storage | ⚪ Optional |
| `ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY` | Claude API | ⚪ Optional |

## ⚠️ Important Notes

1. **Proxy Credentials**: Your proxy credentials are in the `.env` file. Make sure to migrate them!
2. **OV_PASSWORD**: The variable name is `OV_PASSWORD`, not `OV_CUSTOMER_PASSWORD`
3. **Restart Required**: After setting variables, restart your terminal/IDE
4. **Backup**: Keep your `.env` file as `.env.backup` until you verify everything works

## 🧪 Step-by-Step Migration Process

### Step 1: Dry Run (See What Will Happen)
```powershell
.\scripts\migrate_env_to_windows.ps1 -DryRun
```

### Step 2: Migrate Variables
```powershell
# Run as Administrator
.\scripts\migrate_env_to_windows.ps1
# Type 'yes' to confirm
```

### Step 3: Restart Terminal
Close and reopen your terminal/IDE completely.

### Step 4: Verify
```powershell
.\scripts\verify_env_vars.ps1
```

### Step 5: Test
```powershell
uv run scrapy list
uv run scrapy crawl overtime_live
```

### Step 6: Backup .env
```powershell
# Once everything works
Move-Item .env .env.backup
```

## 🔍 Verification Checklist

After migration, verify these work:

```powershell
# Check individual variables
$env:OV_CUSTOMER_ID
$env:ACCUWEATHER_API_KEY
$env:PROXY_URL

# Run verification script
.\scripts\verify_env_vars.ps1

# Test scrapy
uv run scrapy list

# Test CDP integration
uv run python tests/test_cdp_integration.py
```

## 🆘 Troubleshooting

### "Variable not found"
```powershell
# Check if it's actually set
[System.Environment]::GetEnvironmentVariable('OV_PASSWORD', 'User')

# If empty, set it manually
[System.Environment]::SetEnvironmentVariable('OV_PASSWORD', 'YOUR_PASSWORD', 'User')
```

### "Still reading from .env"
- Restart your terminal/IDE completely
- Check that variables are set as 'User' not 'Process'

### "Proxy not working"
Verify all proxy variables are set:
```powershell
$env:PROXY_URL
$env:OVERTIME_PROXY
```

## 📚 Additional Resources

- **Setup Guide**: `docs/WINDOWS_ENV_SETUP.md`
- **Verification Script**: `scripts/verify_env_vars.ps1`
- **Migration Script**: `scripts/migrate_env_to_windows.ps1`
- **Summary**: `ENVIRONMENT_VARIABLES_SUMMARY.md`

---

**Ready to migrate?** Run: `.\scripts\migrate_env_to_windows.ps1 -DryRun` to see what will happen!

