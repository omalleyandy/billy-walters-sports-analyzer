#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fetch game day Highlightly data
    
.DESCRIPTION
    Run this on game days to get matches, highlights, and standings.
    Uses FREE tier endpoints only.
    
.PARAMETER Date
    Date to fetch data for (YYYY-MM-DD format). Defaults to today.
    
.EXAMPLE
    .\scripts\highlightly_gameday.ps1
    
.EXAMPLE
    .\scripts\highlightly_gameday.ps1 -Date "2024-11-10"
#>

param(
    [string]$Date
)

# Use provided date or default to today
if (-not $Date) {
    $Date = Get-Date -Format "yyyy-MM-dd"
}

Write-Host "🏈 Fetching Highlightly Game Day Data for $Date" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Matches
Write-Host "1️⃣ Fetching matches..." -ForegroundColor Cyan
uv run walters-analyzer scrape-highlightly --endpoint matches --sport both --date $Date

# Highlights
Write-Host "`n2️⃣ Fetching highlights..." -ForegroundColor Cyan
uv run walters-analyzer scrape-highlightly --endpoint highlights --sport both --date $Date

# Standings
Write-Host "`n3️⃣ Fetching standings..." -ForegroundColor Cyan
uv run walters-analyzer scrape-highlightly --endpoint standings --sport both

Write-Host "`n✅ Game day data collection complete!" -ForegroundColor Green

