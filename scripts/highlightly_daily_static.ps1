#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fetch static Highlightly data (teams, bookmakers)
    
.DESCRIPTION
    Run this once daily or when you need updated team/bookmaker lists.
    Uses FREE tier endpoints only.
    
.EXAMPLE
    .\scripts\highlightly_daily_static.ps1
#>

Write-Host "🏈 Fetching Highlightly Static Data" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Teams
Write-Host "1️⃣ Fetching NFL & NCAA teams..." -ForegroundColor Cyan
uv run walters-analyzer scrape-highlightly --endpoint teams --sport both

# Bookmakers
Write-Host "`n2️⃣ Fetching bookmakers list..." -ForegroundColor Cyan
uv run walters-analyzer scrape-highlightly --endpoint bookmakers --sport both

Write-Host "`n✅ Static data collection complete!" -ForegroundColor Green

