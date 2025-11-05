# =============================================================================
# Verify Windows Environment Variables
# =============================================================================
# Quick script to check which environment variables are set
# =============================================================================

Write-Host "`nChecking Billy Walters Sports Analyzer Environment Variables..." -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

function Test-EnvVar {
    param($Name, $Required = $false)
    
    $value = [System.Environment]::GetEnvironmentVariable($Name, 'User')
    if ($value) {
        $display = if ($Name -like '*PASSWORD*' -or $Name -like '*KEY*') { 
            "***HIDDEN***" 
        } else { 
            $value 
        }
        Write-Host "[OK] $Name = $display" -ForegroundColor Green
        return $true
    } else {
        $status = if ($Required) { "MISSING (Required)" } else { "Not Set (Optional)" }
        $color = if ($Required) { "Red" } else { "Yellow" }
        Write-Host "[ ] $Name - $status" -ForegroundColor $color
        return $false
    }
}

Write-Host "`nCore Credentials:" -ForegroundColor White
$hasOvId = Test-EnvVar "OV_CUSTOMER_ID" -Required $true
$hasOvPass = Test-EnvVar "OV_PASSWORD" -Required $true
Test-EnvVar "OV_CUSTOMER_PASSWORD"  # Alternative name (optional)

Write-Host "`nWeather APIs:" -ForegroundColor White
$hasAccu = Test-EnvVar "ACCUWEATHER_API_KEY" -Required $true
Test-EnvVar "OPENWEATHER_API_KEY"

Write-Host "`nBankroll Settings:" -ForegroundColor White
Test-EnvVar "BANKROLL"
Test-EnvVar "KELLY_FRACTION"
Test-EnvVar "MAX_BET_PERCENTAGE"

Write-Host "`nOptional Services:" -ForegroundColor White
Test-EnvVar "NEWS_API_KEY"
Test-EnvVar "PROFOOTBALLDOC_API_KEY"
Test-EnvVar "HIGHLIGHTLY_API_KEY"

Write-Host "`nRedis Configuration:" -ForegroundColor White
Test-EnvVar "REDIS_HOST"
Test-EnvVar "REDIS_PORT"
Test-EnvVar "REDIS_DB"

Write-Host "`nMonitoring:" -ForegroundColor White
Test-EnvVar "OVERTIME_MONITOR_INTERVAL"

Write-Host "`n" + "=" * 70 -ForegroundColor Gray

if ($hasOvId -and $hasOvPass -and $hasAccu) {
    Write-Host "`n[SUCCESS] All required environment variables are set!" -ForegroundColor Green
    Write-Host "You can now run scrapers without a .env file" -ForegroundColor Green
} else {
    Write-Host "`n[WARNING] Some required variables are missing" -ForegroundColor Yellow
    Write-Host "Run: .\scripts\set_windows_env_vars.ps1 (as Administrator)" -ForegroundColor Cyan
}

Write-Host ""

