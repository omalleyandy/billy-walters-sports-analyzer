# Claude Start - Unified Start Script
# Run this at the START of every Claude Code session
#
# Usage:
#   .\scripts\claude-start.ps1
#
# What it does:
#   1. Syncs with GitHub (fetches latest, updates main)
#   2. Cleans up merged branches (with confirmation)
#   3. Shows comprehensive status report
#   4. Gets you ready to work!

param(
    [switch]$SkipCleanup  # Skip the cleanup step if you want to go faster
)

$ErrorActionPreference = "Continue"

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         🚀 CLAUDE CODE SESSION - STARTING UP 🚀          ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Step 1: Sync with GitHub
Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
Write-Host "STEP 1: Syncing with GitHub" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

$syncScript = Join-Path $scriptDir "sync-before-chat.ps1"
if (Test-Path $syncScript) {
    & $syncScript
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Sync failed. Please fix the issues and try again."
        exit 1
    }
} else {
    Write-Error "sync-before-chat.ps1 not found at $syncScript"
    exit 1
}

# Step 2: Cleanup merged branches (optional)
if (-not $SkipCleanup) {
    Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
    Write-Host "STEP 2: Cleaning up merged branches" -ForegroundColor Cyan
    Write-Host ("═" * 60) -ForegroundColor Cyan

    $cleanupScript = Join-Path $scriptDir "cleanup-merged-branches.ps1"
    if (Test-Path $cleanupScript) {
        & $cleanupScript
        # Don't fail if cleanup is cancelled or fails - it's optional
    } else {
        Write-Warning "cleanup-merged-branches.ps1 not found. Skipping cleanup."
    }
} else {
    Write-Host "`n⏭️  Skipping cleanup (use without -SkipCleanup to include)" -ForegroundColor Yellow
}

# Step 3: Show status report
Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
Write-Host "STEP 3: Status Report" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

$statusScript = Join-Path $scriptDir "show-branch-status.ps1"
if (Test-Path $statusScript) {
    & $statusScript
} else {
    Write-Warning "show-branch-status.ps1 not found. Skipping status report."
}

# Final message
Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              ✅ READY TO CODE WITH CLAUDE! ✅            ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`nℹ️  When you're done coding, run:" -ForegroundColor Cyan
Write-Host "   .\scripts\claude-end.ps1" -ForegroundColor White
Write-Host "`n   This will commit, push, and create a PR automatically!" -ForegroundColor Gray
