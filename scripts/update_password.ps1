# =============================================================================
# Quick Password Updater for Overtime.ag
# =============================================================================
# Run this script to update your OV_PASSWORD securely
# =============================================================================

Write-Host "`n=== Update Overtime.ag Password ===" -ForegroundColor Cyan
Write-Host ""

# Get current password
$currentPass = [System.Environment]::GetEnvironmentVariable('OV_PASSWORD', 'User')

if ($currentPass) {
    Write-Host "Current password is set to: " -NoNewline
    Write-Host $currentPass -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "No password currently set" -ForegroundColor Yellow
    Write-Host ""
}

# Prompt for new password
Write-Host "Enter your overtime.ag password:" -ForegroundColor Cyan
Write-Host "(This will be stored securely in your Windows user profile)" -ForegroundColor Gray
Write-Host ""

$newPassword = Read-Host -AsSecureString "Password"

# Convert SecureString to plain text for storage
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($newPassword)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

if (-not $plainPassword) {
    Write-Host "`n[CANCELLED] No password entered" -ForegroundColor Yellow
    exit 1
}

# Confirm
Write-Host "`n[INFO] Setting OV_PASSWORD in Windows environment..." -ForegroundColor Green

try {
    [System.Environment]::SetEnvironmentVariable('OV_PASSWORD', $plainPassword, 'User')
    Write-Host "[SUCCESS] Password updated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: You must restart your terminal/IDE for the change to take effect!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After restarting, verify with:" -ForegroundColor Cyan
    Write-Host "  .\scripts\verify_env_vars.ps1" -ForegroundColor White
    Write-Host ""
}
catch {
    Write-Host "[ERROR] Failed to set password: $_" -ForegroundColor Red
    exit 1
}

