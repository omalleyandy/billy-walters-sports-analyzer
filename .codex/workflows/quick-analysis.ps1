#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick Game Analysis - Analyze a single game fast

.DESCRIPTION
    Quick workflow for analyzing a single game with optional research

.PARAMETER HomeTeam
    Home team name

.PARAMETER AwayTeam
    Away team name

.PARAMETER Spread
    Current spread (home team perspective)

.PARAMETER Research
    Include research data (injuries, weather)

.PARAMETER Bankroll
    Current bankroll

.EXAMPLE
    .codex/workflows/quick-analysis.ps1 -HomeTeam "Chiefs" -AwayTeam "Bills" -Spread -2.5 -Research
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$HomeTeam,
    
    [Parameter(Mandatory=$true)]
    [string]$AwayTeam,
    
    [Parameter(Mandatory=$true)]
    [decimal]$Spread,
    
    [Parameter(Mandatory=$false)]
    [switch]$Research,
    
    [Parameter(Mandatory=$false)]
    [decimal]$Bankroll = 10000
)

$cmd = @(
    "uv", "run", "walters-analyzer", "analyze-game",
    "--home", $HomeTeam,
    "--away", $AwayTeam,
    "--spread", $Spread.ToString(),
    "--bankroll", $Bankroll.ToString()
)

if ($Research) {
    $cmd += "--research"
}

Write-Host "Analyzing: $AwayTeam @ $HomeTeam" -ForegroundColor Cyan
Write-Host "Spread: $HomeTeam $Spread" -ForegroundColor Cyan
if ($Research) {
    Write-Host "Research: ENABLED" -ForegroundColor Green
}
Write-Host ""

& $cmd[0] $cmd[1..($cmd.Length-1)]

