#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete data collection workflow
    
.DESCRIPTION
    Runs full data collection pipeline:
    - Highlightly: teams, bookmakers, matches, highlights, standings
    - overtime.ag: betting odds
    - ESPN: injury reports
    
.PARAMETER Date
    Date to fetch data for (YYYY-MM-DD format). Defaults to today.
    
.PARAMETER SkipStatic
    Skip static data (teams, bookmakers) if already collected today.
    
.EXAMPLE
    .\scripts\collect_all_data.ps1
    
.EXAMPLE
    .\scripts\collect_all_data.ps1 -Date "2024-11-10"
    
.EXAMPLE
    .\scripts\collect_all_data.ps1 -SkipStatic
#>

param(
    [string]$Date,
    [switch]$SkipStatic
)

# Use provided date or default to today
if (-not $Date) {
    $Date = Get-Date -Format "yyyy-MM-dd"
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "  BILLY WALTERS SPORTS ANALYZER - DATA COLLECTION" -ForegroundColor Magenta
Write-Host "  Date: $Date" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""

# ============================================================================
# STATIC DATA (once daily)
# ============================================================================

if (-not $SkipStatic) {
    Write-Host "📊 STEP 1: STATIC DATA COLLECTION" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "  → Teams (NFL & NCAA)..." -ForegroundColor Cyan
    uv run walters-analyzer scrape-highlightly --endpoint teams --sport both
    
    Write-Host "`n  → Bookmakers..." -ForegroundColor Cyan
    uv run walters-analyzer scrape-highlightly --endpoint bookmakers --sport both
    
    Write-Host "`n✅ Static data complete`n" -ForegroundColor Green
} else {
    Write-Host "⏭️  Skipping static data (use -SkipStatic:`$false to include)`n" -ForegroundColor DarkGray
}

# ============================================================================
# GAME DAY DATA
# ============================================================================

Write-Host "🏈 STEP 2: GAME DAY DATA COLLECTION" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

Write-Host "  → Matches for $Date..." -ForegroundColor Cyan
uv run walters-analyzer scrape-highlightly --endpoint matches --sport both --date $Date

Write-Host "`n  → Highlights for $Date..." -ForegroundColor Cyan
uv run walters-analyzer scrape-highlightly --endpoint highlights --sport both --date $Date

Write-Host "`n  → Standings..." -ForegroundColor Cyan
uv run walters-analyzer scrape-highlightly --endpoint standings --sport both

Write-Host "`n✅ Game day data complete`n" -ForegroundColor Green

# ============================================================================
# BETTING ODDS
# ============================================================================

Write-Host "💰 STEP 3: BETTING ODDS COLLECTION" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

Write-Host "  → overtime.ag odds (NFL & CFB)..." -ForegroundColor Cyan
uv run walters-analyzer scrape-overtime --sport both

Write-Host "`n✅ Odds collection complete`n" -ForegroundColor Green

# ============================================================================
# INJURY REPORTS
# ============================================================================

Write-Host "🏥 STEP 4: INJURY REPORTS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

Write-Host "  → ESPN NFL injuries..." -ForegroundColor Cyan
uv run walters-analyzer scrape-injuries --sport nfl

Write-Host "`n  → ESPN College Football injuries..." -ForegroundColor Cyan
uv run walters-analyzer scrape-injuries --sport cfb

Write-Host "`n✅ Injury reports complete`n" -ForegroundColor Green

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "  ✅ DATA COLLECTION COMPLETE!" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""
Write-Host "📁 Data locations:" -ForegroundColor White
Write-Host "  • Highlightly: data/highlightly/nfl/ and data/highlightly/ncaaf/" -ForegroundColor Gray
Write-Host "  • Odds:        data/odds/nfl/ and data/odds/ncaaf/" -ForegroundColor Gray
Write-Host "  • Injuries:    data/injuries/nfl/ and data/injuries/ncaaf/" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor White
Write-Host "  1. Review data quality" -ForegroundColor Gray
Write-Host "  2. Run Billy Walters analysis" -ForegroundColor Gray
Write-Host "  3. Check for betting opportunities" -ForegroundColor Gray
Write-Host ""

