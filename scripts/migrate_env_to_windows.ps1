# =============================================================================
# Migrate .env File to Windows Environment Variables
# =============================================================================
# This script reads your existing .env file and sets Windows environment variables
# Run as Administrator: Right-click PowerShell -> Run as Administrator
# =============================================================================

param(
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

Write-Host "`n=== Billy Walters Sports Analyzer - Environment Migration ===" -ForegroundColor Cyan
Write-Host "This script will migrate your .env file to Windows environment variables" -ForegroundColor Yellow
Write-Host ""

$envFile = ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with your actual values first" -ForegroundColor Yellow
    Write-Host "You can copy from: env.template" -ForegroundColor Cyan
    exit 1
}

Write-Host "[INFO] Reading .env file..." -ForegroundColor Green

# Read and parse .env file
$envVars = @{}
Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    
    # Skip comments and empty lines
    if ($line -and -not $line.StartsWith("#")) {
        if ($line -match "^([^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            # Skip placeholder values
            if ($value -and 
                $value -ne "your_accuweather_api_key_here" -and
                $value -ne "your_openweather_api_key_here" -and
                $value -ne "your_customer_id_here" -and
                $value -ne "your_password_here" -and
                $value -ne "http://username:password@proxy.example.com:6060") {
                
                $envVars[$key] = $value
            }
        }
    }
}

Write-Host "`nFound $($envVars.Count) variables to migrate:`n" -ForegroundColor Cyan

# Display what will be set
$envVars.GetEnumerator() | Sort-Object Name | ForEach-Object {
    $displayValue = if ($_.Key -like "*PASSWORD*" -or $_.Key -like "*KEY*") {
        "***HIDDEN***"
    } else {
        $_.Value
    }
    Write-Host "  $($_.Key) = $displayValue" -ForegroundColor White
}

Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] No changes will be made. Remove -DryRun flag to apply changes." -ForegroundColor Yellow
    exit 0
}

Write-Host "[WARNING] This will permanently set these environment variables in your Windows user profile" -ForegroundColor Yellow

if (-not $Force) {
    $confirm = Read-Host "Continue? (yes/no)"
    
    if ($confirm -ne "yes") {
        Write-Host "[CANCELLED] No changes made" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "[FORCE MODE] Proceeding without confirmation..." -ForegroundColor Yellow
}

Write-Host "`n[INFO] Setting Windows environment variables..." -ForegroundColor Green

$successCount = 0
$errorCount = 0

$envVars.GetEnumerator() | Sort-Object Name | ForEach-Object {
    try {
        [System.Environment]::SetEnvironmentVariable($_.Key, $_.Value, 'User')
        Write-Host "[OK] Set $($_.Key)" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host "[ERROR] Failed to set $($_.Key): $_" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
Write-Host "=== Migration Complete ===" -ForegroundColor Cyan
Write-Host "  Successfully set: $successCount variables" -ForegroundColor Green
if ($errorCount -gt 0) {
    Write-Host "  Errors: $errorCount variables" -ForegroundColor Red
}

Write-Host "`n[IMPORTANT] Next steps:" -ForegroundColor Yellow
Write-Host "  1. Close and restart your terminal/IDE" -ForegroundColor White
Write-Host "  2. Verify: .\scripts\verify_env_vars.ps1" -ForegroundColor White
Write-Host "  3. Optional: Backup .env file: Move-Item .env .env.backup" -ForegroundColor White
Write-Host "  4. Test: uv run scrapy list" -ForegroundColor White
Write-Host ""

