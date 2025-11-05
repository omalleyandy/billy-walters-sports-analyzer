# Windows Environment Variables Setup Guide

## Why Use Windows Environment Variables?

Using Windows environment variables instead of `.env` files provides several benefits:

1. **Better Security**: Credentials stored in Windows user profile, not in files
2. **No File Management**: No need to copy/maintain `.env` files
3. **System-Wide Access**: Available to all applications in your user session
4. **Version Control Safe**: Nothing to accidentally commit to Git
5. **Professional Setup**: Industry standard for production environments

## Quick Setup

### Method 1: PowerShell Script (Recommended)

1. **Edit the script** with your actual values:
   ```powershell
   notepad .\scripts\set_windows_env_vars.ps1
   ```

2. **Run as Administrator**:
   ```powershell
   # Right-click PowerShell -> Run as Administrator
   cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
   .\scripts\set_windows_env_vars.ps1
   ```

3. **Restart your terminal/IDE** for changes to take effect

4. **Verify**:
   ```powershell
   .\scripts\verify_env_vars.ps1
   ```

### Method 2: Windows Settings GUI

1. Press `Win + X` → Select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Add each variable:

**Required Variables:**
- `OV_CUSTOMER_ID` = Your overtime.ag customer ID
- `OV_CUSTOMER_PASSWORD` = Your overtime.ag password
- `ACCUWEATHER_API_KEY` = Your AccuWeather API key

**Optional Variables:**
- `BANKROLL` = 10000.0
- `KELLY_FRACTION` = 0.25
- `MAX_BET_PERCENTAGE` = 0.03
- `OPENWEATHER_API_KEY` = Your OpenWeather API key (backup)
- `REDIS_HOST` = localhost (if using Redis)
- `REDIS_PORT` = 6379 (if using Redis)
- `OVERTIME_MONITOR_INTERVAL` = 10 (for monitoring mode)

### Method 3: PowerShell One-Liners

```powershell
# Set individual variables
[System.Environment]::SetEnvironmentVariable('OV_CUSTOMER_ID', 'YOUR_ID', 'User')
[System.Environment]::SetEnvironmentVariable('OV_CUSTOMER_PASSWORD', 'YOUR_PASS', 'User')
[System.Environment]::SetEnvironmentVariable('ACCUWEATHER_API_KEY', 'YOUR_KEY', 'User')
```

## Verification

### Check All Variables
```powershell
.\scripts\verify_env_vars.ps1
```

### Check Specific Variable
```powershell
$env:OV_CUSTOMER_ID
```

### List All Related Variables
```powershell
Get-ChildItem Env: | Where-Object { 
    $_.Name -like 'OV_*' -or 
    $_.Name -like '*API_KEY' -or 
    $_.Name -like 'BANKROLL' 
}
```

## Using with the Project

Once environment variables are set, the scrapers will automatically use them:

```powershell
# No .env file needed!
uv run scrapy crawl overtime_live
uv run scrapy crawl overtime_live -a monitor=10
```

## Migration from .env Files

If you're currently using a `.env` file:

1. **Copy values from `.env`** to Windows environment variables using the script
2. **Verify** variables are set correctly
3. **Test** that scrapers work: `uv run scrapy list`
4. **Optional**: Delete or rename `.env` to `.env.backup`

The code will prefer system environment variables over `.env` files.

## Updating Variables

### Change a Variable
```powershell
[System.Environment]::SetEnvironmentVariable('OV_CUSTOMER_PASSWORD', 'NEW_PASSWORD', 'User')
```

### Remove a Variable
```powershell
[System.Environment]::SetEnvironmentVariable('OV_CUSTOMER_ID', $null, 'User')
```

### Export Variables (for backup)
```powershell
# Create a backup of your variables
$vars = @(
    'OV_CUSTOMER_ID',
    'OV_CUSTOMER_PASSWORD',
    'ACCUWEATHER_API_KEY',
    'BANKROLL'
)

foreach ($var in $vars) {
    $value = [System.Environment]::GetEnvironmentVariable($var, 'User')
    if ($value) {
        "$var=$value" | Add-Content -Path "env_backup_$(Get-Date -Format 'yyyyMMdd').txt"
    }
}
```

## Security Best Practices

1. **Never commit** environment variable values to Git
2. **Use different credentials** for development vs production
3. **Rotate API keys** periodically
4. **Backup** your environment variables securely
5. **Document** which variables your team needs (but not their values)

## Troubleshooting

### Variables Not Found

**Problem**: Scrapers can't find environment variables

**Solution**:
1. Verify variables are set: `.\scripts\verify_env_vars.ps1`
2. Restart your terminal/IDE completely
3. Check you set them as 'User' not 'Process': 
   ```powershell
   [System.Environment]::GetEnvironmentVariable('OV_CUSTOMER_ID', 'User')
   ```

### Still Want to Use .env Files?

If you prefer `.env` files (e.g., for quick testing):

```powershell
# Install optional dotenv support
uv sync --extra dotenv
```

The code will still work with `.env` files if `python-dotenv` is installed.

## System vs User vs Process Variables

- **User** (Recommended): Permanent, available to all your sessions
- **Machine**: Permanent, available to all users (requires admin)
- **Process**: Temporary, only for current session

Always use **User** for credentials in this project.

## Complete Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OV_CUSTOMER_ID` | ✅ | - | Overtime.ag customer ID |
| `OV_CUSTOMER_PASSWORD` | ✅ | - | Overtime.ag password |
| `ACCUWEATHER_API_KEY` | ✅ | - | Primary weather API |
| `OPENWEATHER_API_KEY` | ❌ | - | Backup weather API |
| `BANKROLL` | ❌ | 10000.0 | Starting bankroll |
| `KELLY_FRACTION` | ❌ | 0.25 | Kelly criterion fraction |
| `MAX_BET_PERCENTAGE` | ❌ | 0.03 | Max bet as % of bankroll |
| `REDIS_HOST` | ❌ | - | Redis hostname for distributed tracking |
| `REDIS_PORT` | ❌ | - | Redis port |
| `REDIS_DB` | ❌ | - | Redis database number |
| `OVERTIME_MONITOR_INTERVAL` | ❌ | - | Monitoring interval in seconds |
| `NEWS_API_KEY` | ❌ | - | NewsAPI.org key |
| `PROFOOTBALLDOC_API_KEY` | ❌ | - | ProFootballDoc API key |

## Next Steps

After setting up environment variables:

1. **Sync dependencies**: `uv sync`
2. **Verify setup**: `.\scripts\verify_env_vars.ps1`
3. **Test scraper**: `uv run scrapy crawl overtime_live`
4. **Start monitoring**: `uv run scrapy crawl overtime_live -a monitor=10`

---

**Questions?** Check the main [README.md](../README.md) or [START_HERE.md](../START_HERE.md)

