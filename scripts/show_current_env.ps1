# =============================================================================
# Show Current .env File Values (Safely)
# =============================================================================
# Display what's in your .env file with sensitive data masked
# =============================================================================

Write-Host "`n=== Current .env File Contents ===" -ForegroundColor Cyan
Write-Host ""

$envFile = ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    Write-Host "No .env file exists yet. You can:" -ForegroundColor Yellow
    Write-Host "  1. Copy from template: Copy-Item env.template .env" -ForegroundColor White
    Write-Host "  2. Or just use Windows environment variables (recommended)" -ForegroundColor White
    exit 1
}

$lineCount = 0
$varCount = 0
$emptyCount = 0
$commentCount = 0

Get-Content $envFile | ForEach-Object {
    $lineCount++
    $line = $_.Trim()
    
    if (-not $line) {
        # Empty line
        $emptyCount++
        return
    }
    
    if ($line.StartsWith("#")) {
        # Comment line
        $commentCount++
        Write-Host $line -ForegroundColor DarkGray
        return
    }
    
    if ($line -match "^([^=]+)=(.*)$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        $varCount++
        
        # Check if it's a placeholder value
        $isPlaceholder = $false
        if ($value -eq "your_accuweather_api_key_here" -or
            $value -eq "your_openweather_api_key_here" -or
            $value -eq "your_customer_id_here" -or
            $value -eq "your_password_here" -or
            $value -like "*username:password@proxy*") {
            $isPlaceholder = $true
        }
        
        # Determine display value
        if (-not $value) {
            $displayValue = "(empty)"
            $color = "Yellow"
        }
        elseif ($isPlaceholder) {
            $displayValue = $value
            $color = "Yellow"
        }
        elseif ($key -like "*PASSWORD*" -or $key -like "*KEY*") {
            # Hide sensitive values
            $displayValue = "***CONFIGURED***"
            $color = "Green"
        }
        else {
            $displayValue = $value
            $color = "Green"
        }
        
        Write-Host "$key = $displayValue" -ForegroundColor $color
    }
    else {
        Write-Host $line -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "  Total lines: $lineCount" -ForegroundColor White
Write-Host "  Variables: $varCount" -ForegroundColor White
Write-Host "  Comments: $commentCount" -ForegroundColor White
Write-Host "  Empty lines: $emptyCount" -ForegroundColor White
Write-Host ""

# Check for placeholder values
$hasPlaceholders = $false
Get-Content $envFile | ForEach-Object {
    if ($_ -match "your_.*_here" -or $_ -match "username:password@proxy") {
        $hasPlaceholders = $true
    }
}

if ($hasPlaceholders) {
    Write-Host "[WARNING] Some variables still have placeholder values!" -ForegroundColor Yellow
    Write-Host "Edit .env with your actual values before migrating to Windows" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env with your actual API keys (if needed)" -ForegroundColor White
Write-Host "  2. Run: .\scripts\migrate_env_to_windows.ps1" -ForegroundColor White
Write-Host "  3. Then backup/delete .env: Move-Item .env .env.backup" -ForegroundColor White
Write-Host ""

