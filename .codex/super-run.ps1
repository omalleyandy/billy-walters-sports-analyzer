#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Billy Walters Sports Analyzer - Super Run Script
    Automated workflow orchestration for daily betting analysis

.DESCRIPTION
    This script automates the complete daily workflow:
    1. Data collection (injuries, odds, weather)
    2. Game analysis with AI assistance
    3. Sharp money monitoring
    4. Report generation
    
    Inspired by Chrome DevTools AI assistance patterns for performance and debugging

.PARAMETER Task
    The task to execute (collect-data, analyze-slate, monitor-sharp, full-workflow)

.PARAMETER Sport
    Sport to analyze (nfl, ncaaf, both)

.PARAMETER Bankroll
    Starting bankroll amount

.PARAMETER DryRun
    Run in dry-run mode (no actual bets)

.EXAMPLE
    .codex/super-run.ps1 -Task full-workflow -Sport nfl -Bankroll 10000

.EXAMPLE
    .codex/super-run.ps1 -Task analyze-slate -Sport nfl -DryRun

.NOTES
    Author: Billy Walters SDK Team
    Version: 1.0.0
    Requires: uv, PowerShell 7+
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('collect-data', 'analyze-slate', 'monitor-sharp', 'full-workflow', 'test-system')]
    [string]$Task = 'full-workflow',
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('nfl', 'ncaaf', 'both')]
    [string]$Sport = 'nfl',
    
    [Parameter(Mandatory=$false)]
    [decimal]$Bankroll = 10000,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerboseOutput
)

# ============================================================================
# Configuration
# ============================================================================

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$LogDir = Join-Path $ProjectRoot "logs"
$DataDir = Join-Path $ProjectRoot "data"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "super-run-$Timestamp.log"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# ============================================================================
# Logging Functions (Chrome DevTools style)
# ============================================================================

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('INFO', 'SUCCESS', 'WARNING', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO'
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Console output with colors
    switch ($Level) {
        'SUCCESS' { Write-Host $logMessage -ForegroundColor Green }
        'WARNING' { Write-Host $logMessage -ForegroundColor Yellow }
        'ERROR'   { Write-Host $logMessage -ForegroundColor Red }
        'DEBUG'   { if ($VerboseOutput) { Write-Host $logMessage -ForegroundColor Gray } }
        default   { Write-Host $logMessage }
    }
    
    # File output
    Add-Content -Path $LogFile -Value $logMessage
}

function Write-Section {
    param([string]$Title)
    
    $separator = "=" * 80
    Write-Log $separator
    Write-Log $Title
    Write-Log $separator
}

function Measure-Task {
    param(
        [string]$TaskName,
        [scriptblock]$ScriptBlock
    )
    
    Write-Log "Starting: $TaskName" -Level DEBUG
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        & $ScriptBlock
        $stopwatch.Stop()
        Write-Log "Completed: $TaskName (${($stopwatch.Elapsed.TotalSeconds)}s)" -Level SUCCESS
        return @{ Success = $true; Duration = $stopwatch.Elapsed.TotalSeconds }
    }
    catch {
        $stopwatch.Stop()
        Write-Log "Failed: $TaskName - $($_.Exception.Message)" -Level ERROR
        return @{ Success = $false; Duration = $stopwatch.Elapsed.TotalSeconds; Error = $_.Exception.Message }
    }
}

# ============================================================================
# Task Functions
# ============================================================================

function Invoke-CollectData {
    <#
    .SYNOPSIS
        Collect fresh data from all sources
    #>
    Write-Section "DATA COLLECTION"
    
    $results = @()
    
    # 1. Scrape injuries
    Write-Log "Scraping injury reports..."
    $results += Measure-Task "Scrape Injuries" {
        uv run walters-analyzer scrape-injuries --sport $(if ($Sport -eq 'both') { 'nfl' } else { $Sport })
    }
    
    # 2. Scrape highlightly data
    Write-Log "Fetching Highlightly data..."
    $results += Measure-Task "Highlightly - Matches" {
        uv run walters-analyzer scrape-highlightly --endpoint matches --sport $Sport --date (Get-Date -Format "yyyy-MM-dd")
    }
    
    $results += Measure-Task "Highlightly - Odds" {
        uv run walters-analyzer scrape-highlightly --endpoint odds --sport $Sport --date (Get-Date -Format "yyyy-MM-dd")
    }
    
    # 3. Optional: AI-assisted scraping for odds
    if ($VerboseOutput) {
        Write-Log "Running AI-assisted scraping..."
        $results += Measure-Task "AI Scraping" {
            uv run walters-analyzer scrape-ai --sport $(if ($Sport -eq 'both') { 'nfl' } else { $Sport })
        }
    }
    
    # Summary
    $successCount = ($results | Where-Object { $_.Success }).Count
    $totalCount = $results.Count
    Write-Log "Data collection complete: $successCount/$totalCount successful" -Level SUCCESS
    
    return $results
}

function Invoke-AnalyzeSlate {
    <#
    .SYNOPSIS
        Analyze all games for today with AI assistance
    #>
    Write-Section "SLATE ANALYSIS"
    
    Write-Log "Loading today's games..."
    
    # Get games from latest data
    $gamesFile = Get-ChildItem -Path (Join-Path $DataDir "highlightly/$Sport") -Filter "matches-*.jsonl" | 
                 Sort-Object LastWriteTime -Descending | 
                 Select-Object -First 1
    
    if (-not $gamesFile) {
        Write-Log "No games data found. Run collect-data first." -Level WARNING
        return @()
    }
    
    Write-Log "Analyzing games from: $($gamesFile.Name)"
    
    # For now, use interactive mode to analyze
    # Future: Parse JSONL and analyze each game programmatically
    Write-Log "Use interactive mode for detailed analysis:" -Level INFO
    Write-Log "  uv run walters-analyzer interactive" -Level INFO
    Write-Log "  Then: /analyze Team1 vs Team2 -X.X --research" -Level INFO
    
    return @{ Success = $true; Message = "See interactive mode for detailed analysis" }
}

function Invoke-MonitorSharp {
    <#
    .SYNOPSIS
        Monitor for sharp money movements
    #>
    Write-Section "SHARP MONEY MONITORING"
    
    Write-Log "Starting sharp money monitor..."
    Write-Log "Duration: 60 minutes"
    
    $result = Measure-Task "Sharp Money Monitor" {
        uv run walters-analyzer monitor-sharp --sport $(if ($Sport -eq 'both') { 'americanfootball_nfl' } else { "americanfootball_$Sport" }) --duration 60
    }
    
    return $result
}

function Invoke-TestSystem {
    <#
    .SYNOPSIS
        Test system functionality (Chrome DevTools debugging pattern)
    #>
    Write-Section "SYSTEM TEST"
    
    Write-Log "Running system diagnostics..."
    
    # Test 1: CLI availability
    $results = @()
    $results += Measure-Task "CLI Help" {
        uv run walters-analyzer --help | Out-Null
    }
    
    # Test 2: Slash commands
    $results += Measure-Task "Slash Command - Help" {
        uv run walters-analyzer slash "/help" | Out-Null
    }
    
    $results += Measure-Task "Slash Command - Bankroll" {
        uv run walters-analyzer slash "/bankroll" | Out-Null
    }
    
    # Test 3: Core analyzer
    $results += Measure-Task "Analyze Game" {
        uv run walters-analyzer analyze-game --home "Chiefs" --away "Bills" --spread -2.5 | Out-Null
    }
    
    # Summary
    $successCount = ($results | Where-Object { $_.Success }).Count
    $totalCount = $results.Count
    
    if ($successCount -eq $totalCount) {
        Write-Log "System test PASSED: All $totalCount tests successful" -Level SUCCESS
    }
    else {
        Write-Log "System test PARTIAL: $successCount/$totalCount tests successful" -Level WARNING
    }
    
    return $results
}

function Invoke-FullWorkflow {
    <#
    .SYNOPSIS
        Execute complete daily workflow
    #>
    Write-Section "FULL WORKFLOW EXECUTION"
    
    Write-Log "Sport: $Sport"
    Write-Log "Bankroll: $$Bankroll"
    Write-Log "Dry Run: $DryRun"
    Write-Log ""
    
    $workflowResults = @{
        StartTime = Get-Date
        Sport = $Sport
        Bankroll = $Bankroll
        DryRun = $DryRun
        Steps = @()
    }
    
    # Step 1: Collect Data
    Write-Log "Step 1/3: Collecting data..." -Level INFO
    $collectResult = Invoke-CollectData
    $workflowResults.Steps += @{ Step = "Collect Data"; Result = $collectResult }
    
    # Step 2: Analyze Slate
    Write-Log "Step 2/3: Analyzing slate..." -Level INFO
    $analyzeResult = Invoke-AnalyzeSlate
    $workflowResults.Steps += @{ Step = "Analyze Slate"; Result = $analyzeResult }
    
    # Step 3: Monitor Sharp Money (optional, skip in dry-run)
    if (-not $DryRun) {
        Write-Log "Step 3/3: Monitoring sharp money..." -Level INFO
        $monitorResult = Invoke-MonitorSharp
        $workflowResults.Steps += @{ Step = "Monitor Sharp"; Result = $monitorResult }
    }
    else {
        Write-Log "Step 3/3: Skipped (dry-run mode)" -Level INFO
    }
    
    $workflowResults.EndTime = Get-Date
    $workflowResults.Duration = ($workflowResults.EndTime - $workflowResults.StartTime).TotalMinutes
    
    # Final Summary
    Write-Section "WORKFLOW SUMMARY"
    Write-Log "Completed in $([math]::Round($workflowResults.Duration, 2)) minutes" -Level SUCCESS
    Write-Log "Log file: $LogFile" -Level INFO
    
    return $workflowResults
}

# ============================================================================
# Main Execution
# ============================================================================

try {
    Write-Section "BILLY WALTERS SUPER-RUN"
    Write-Log "Task: $Task"
    Write-Log "Timestamp: $Timestamp"
    Write-Log "Project: $ProjectRoot"
    Write-Log ""
    
    # Change to project directory
    Push-Location $ProjectRoot
    
    # Execute requested task
    $result = switch ($Task) {
        'collect-data'   { Invoke-CollectData }
        'analyze-slate'  { Invoke-AnalyzeSlate }
        'monitor-sharp'  { Invoke-MonitorSharp }
        'test-system'    { Invoke-TestSystem }
        'full-workflow'  { Invoke-FullWorkflow }
        default          { throw "Unknown task: $Task" }
    }
    
    Write-Log ""
    Write-Log "Super-run completed successfully!" -Level SUCCESS
    Write-Log "Log saved to: $LogFile" -Level INFO
    
    exit 0
}
catch {
    Write-Log "Super-run failed: $($_.Exception.Message)" -Level ERROR
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level ERROR
    exit 1
}
finally {
    Pop-Location
}

