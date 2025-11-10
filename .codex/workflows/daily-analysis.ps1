#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Daily Analysis Workflow - Automated Sunday/Saturday betting analysis

.DESCRIPTION
    Executes the complete daily betting workflow:
    1. Morning: Collect all data (injuries, odds, weather)
    2. Mid-morning: Analyze full slate with AI assistance
    3. Pre-game: Monitor for sharp money movements
    4. Post-analysis: Generate reports and recommendations

.PARAMETER Sport
    Sport to analyze (nfl for Sunday, ncaaf for Saturday)

.PARAMETER Bankroll
    Current bankroll amount

.PARAMETER DayOfWeek
    Day of week (Sunday, Saturday, or auto-detect)

.EXAMPLE
    .codex/workflows/daily-analysis.ps1 -Sport nfl -Bankroll 10000
    # Runs NFL Sunday workflow

.EXAMPLE
    .codex/workflows/daily-analysis.ps1 -Sport ncaaf -Bankroll 10000
    # Runs NCAA Saturday workflow
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('nfl', 'ncaaf', 'auto')]
    [string]$Sport = 'auto',
    
    [Parameter(Mandatory=$false)]
    [decimal]$Bankroll = 10000,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('Sunday', 'Saturday', 'auto')]
    [string]$DayOfWeek = 'auto'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))

# Auto-detect sport based on day
if ($Sport -eq 'auto') {
    $today = (Get-Date).DayOfWeek
    if ($today -eq 'Sunday') {
        $Sport = 'nfl'
    }
    elseif ($today -eq 'Saturday') {
        $Sport = 'ncaaf'
    }
    else {
        Write-Host "Not a typical game day. Using NFL by default." -ForegroundColor Yellow
        $Sport = 'nfl'
    }
}

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "BILLY WALTERS DAILY ANALYSIS WORKFLOW" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Sport:    $($Sport.ToUpper())" -ForegroundColor White
Write-Host "Bankroll: $$Bankroll" -ForegroundColor White
Write-Host "Date:     $(Get-Date -Format 'yyyy-MM-dd dddd')" -ForegroundColor White
Write-Host ""

# Stage 1: Morning Data Collection (9:00 AM)
Write-Host "[9:00 AM] STAGE 1: DATA COLLECTION" -ForegroundColor Green
Write-Host "Collecting fresh data from all sources..." -ForegroundColor Gray
Write-Host ""

& "$ProjectRoot/.codex/super-run.ps1" -Task collect-data -Sport $Sport

Write-Host ""
Write-Host "[+] Stage 1 complete. Data collected." -ForegroundColor Green
Write-Host ""

# Stage 2: Analysis (10:00 AM)
Write-Host "[10:00 AM] STAGE 2: SLATE ANALYSIS" -ForegroundColor Green
Write-Host "Opening interactive mode for game-by-game analysis..." -ForegroundColor Gray
Write-Host ""
Write-Host "In interactive mode, use:" -ForegroundColor Yellow
Write-Host "  /analyze Team1 vs Team2 -X.X --research" -ForegroundColor Yellow
Write-Host "  /research injuries TeamName" -ForegroundColor Yellow
Write-Host "  /bankroll" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to start interactive mode (or Ctrl+C to skip)..." -ForegroundColor Yellow
$null = Read-Host

uv run walters-analyzer interactive --bankroll $Bankroll

# Stage 3: Sharp Money Monitoring (11:30 AM - 12:30 PM)
Write-Host ""
Write-Host "[11:30 AM] STAGE 3: SHARP MONEY MONITORING" -ForegroundColor Green
Write-Host "Monitor sharp money for 60 minutes? (Y/N)" -ForegroundColor Yellow
$response = Read-Host

if ($response -eq 'Y' -or $response -eq 'y') {
    & "$ProjectRoot/.codex/super-run.ps1" -Task monitor-sharp -Sport $Sport
}
else {
    Write-Host "Skipping sharp money monitoring." -ForegroundColor Gray
}

# Final Summary
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "DAILY WORKFLOW COMPLETE" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Review analysis recommendations" -ForegroundColor Gray
Write-Host "  2. Place bets within Kelly stake limits" -ForegroundColor Gray
Write-Host "  3. Track results for CLV analysis" -ForegroundColor Gray
Write-Host ""

