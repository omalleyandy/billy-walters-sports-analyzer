# =============================================================================
# Set Windows Environment Variables for Billy Walters Sports Analyzer
# =============================================================================
# Run this script AS ADMINISTRATOR in PowerShell
# These will be set as USER variables (permanent for your account)
#
# Usage: Right-click PowerShell -> Run as Administrator
#        Then run: .\scripts\set_windows_env_vars.ps1
# =============================================================================

Write-Host "Setting Windows Environment Variables..." -ForegroundColor Cyan
Write-Host "These will be permanently stored in your Windows user profile" -ForegroundColor Yellow
Write-Host ""

# Core Credentials
Write-Host "Setting Overtime.ag credentials..." -ForegroundColor Green
[System.Environment]::SetEnvironmentVariable('OV_CUSTOMER_ID', 'DAL519', 'User')
[System.Environment]::SetEnvironmentVariable('OV_CUSTOMER_PASSWORD', 'YOUR_PASSWORD_HERE', 'User')

# Weather APIs
Write-Host "Setting Weather API keys..." -ForegroundColor Green
[System.Environment]::SetEnvironmentVariable('ACCUWEATHER_API_KEY', 'YOUR_API_KEY_HERE', 'User')
[System.Environment]::SetEnvironmentVariable('OPENWEATHER_API_KEY', 'YOUR_API_KEY_HERE', 'User')

# Optional: News and Analysis APIs
# [System.Environment]::SetEnvironmentVariable('NEWS_API_KEY', 'YOUR_API_KEY_HERE', 'User')
# [System.Environment]::SetEnvironmentVariable('PROFOOTBALLDOC_API_KEY', 'YOUR_API_KEY_HERE', 'User')
# [System.Environment]::SetEnvironmentVariable('HIGHLIGHTLY_API_KEY', 'YOUR_API_KEY_HERE', 'User')

# Optional: Bankroll Settings
Write-Host "Setting Bankroll configuration..." -ForegroundColor Green
[System.Environment]::SetEnvironmentVariable('BANKROLL', '10000.0', 'User')
[System.Environment]::SetEnvironmentVariable('KELLY_FRACTION', '0.25', 'User')
[System.Environment]::SetEnvironmentVariable('MAX_BET_PERCENTAGE', '0.03', 'User')

# Optional: Redis for distributed odds tracking
# [System.Environment]::SetEnvironmentVariable('REDIS_HOST', 'localhost', 'User')
# [System.Environment]::SetEnvironmentVariable('REDIS_PORT', '6379', 'User')
# [System.Environment]::SetEnvironmentVariable('REDIS_DB', '0', 'User')

# Optional: Monitoring interval
# [System.Environment]::SetEnvironmentVariable('OVERTIME_MONITOR_INTERVAL', '10', 'User')

Write-Host ""
Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: You must restart your terminal/IDE for changes to take effect!" -ForegroundColor Yellow
Write-Host ""
Write-Host "To verify, open a NEW PowerShell window and run:" -ForegroundColor Cyan
Write-Host "  Get-ChildItem Env: | Where-Object { `$_.Name -like 'OV_*' -or `$_.Name -like '*API_KEY' }" -ForegroundColor White
Write-Host ""

