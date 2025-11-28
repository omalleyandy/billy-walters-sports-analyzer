#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete Billy Walters weekly data collection workflow with X News integration

.DESCRIPTION
    Runs full data collection pipeline including:
    - Massey Power Ratings
    - ESPN Team Statistics
    - X News & Injury Posts (NEW - STEP 5)
    - Weather Data
    - Overtime.ag Odds
    - Edge Detection Analysis

.PARAMETER League
    League to analyze: 'nfl', 'ncaaf', or 'both' (default: 'both')

.EXAMPLE
    .\scripts\dev\collect_all_data_weekly.ps1 -League nfl

.EXAMPLE
    .\scripts\dev\collect_all_data_weekly.ps1
#>

param(
    [ValidateSet('nfl', 'ncaaf', 'both')]
    [string]$League = 'both'
)

# Colors for output
$Colors = @{
    Header = 'Magenta'
    Step = 'Yellow'
    Success = 'Green'
    Info = 'Cyan'
    Warning = 'Red'
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Colors.Header
Write-Host "  BILLY WALTERS SPORTS ANALYZER" -ForegroundColor $Colors.Header
Write-Host "  Complete Weekly Data Collection" -ForegroundColor $Colors.Header
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor $Colors.Header
Write-Host "  League: $($League.ToUpper())" -ForegroundColor $Colors.Header
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Colors.Header
Write-Host ""

$Steps = @(
    @{
        Number = 1
        Name = "Massey Power Ratings"
        Command = "uv run python scripts/scrapers/scrape_massey_games.py"
    },
    @{
        Number = 2
        Name = "ESPN Team Stats (NFL)"
        Command = "uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl"
        Condition = $League -in @('nfl', 'both')
    },
    @{
        Number = 3
        Name = "ESPN Team Stats (NCAAF)"
        Command = "uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf"
        Condition = $League -in @('ncaaf', 'both')
    },
    @{
        Number = 4
        Name = "X News & Injury Posts (NEW - STEP 5)"
        Command = "uv run python scripts/scrapers/scrape_x_news_integrated.py --all"
        Description = "Breaking news from @NFL, @AdamSchefter, @FieldYates + NCAAF sources"
    },
    @{
        Number = 5
        Name = "Weather Data"
        Command = "uv run python -m src.data.weather_client --league nfl"
    },
    @{
        Number = 6
        Name = "Overtime.ag Odds"
        Command = "uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf"
    },
    @{
        Number = 7
        Name = "Edge Detection (NFL)"
        Command = "uv run python src/walters_analyzer/valuation/billy_walters_edge_detector.py --league nfl"
        Condition = $League -in @('nfl', 'both')
    },
    @{
        Number = 8
        Name = "Edge Detection (NCAAF)"
        Command = "uv run python src/walters_analyzer/valuation/ncaaf_edge_detector.py --league ncaaf"
        Condition = $League -in @('ncaaf', 'both')
    }
)

$CompletedSteps = @()
$FailedSteps = @()

foreach ($Step in $Steps) {
    # Check condition
    if ($null -ne $Step.Condition -and -not $Step.Condition) {
        continue
    }

    Write-Host "[$($Step.Number)] $($Step.Name)" -ForegroundColor $Colors.Step
    if ($Step.Description) {
        Write-Host "    $($Step.Description)" -ForegroundColor $Colors.Info
    }

    Write-Host "    Running: $($Step.Command)" -ForegroundColor $Colors.Info
    Write-Host ""

    try {
        Invoke-Expression $Step.Command
        Write-Host "[OK] $($Step.Name) complete" -ForegroundColor $Colors.Success
        $CompletedSteps += $Step.Name
    }
    catch {
        Write-Host "[ERROR] $($Step.Name) failed: $_" -ForegroundColor $Colors.Warning
        $FailedSteps += $Step.Name
    }

    Write-Host ""
}

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Colors.Header
Write-Host "  COLLECTION SUMMARY" -ForegroundColor $Colors.Header
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Colors.Header
Write-Host ""

Write-Host "Completed: $($CompletedSteps.Count)" -ForegroundColor $Colors.Success
foreach ($Step in $CompletedSteps) {
    Write-Host "  [OK] $Step" -ForegroundColor $Colors.Success
}

if ($FailedSteps.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed: $($FailedSteps.Count)" -ForegroundColor $Colors.Warning
    foreach ($Step in $FailedSteps) {
        Write-Host "  [ERROR] $Step" -ForegroundColor $Colors.Warning
    }
}

Write-Host ""
Write-Host "Data locations:" -ForegroundColor $Colors.Info
Write-Host "  • Power ratings: output/massey/" -ForegroundColor $Colors.Info
Write-Host "  • Team stats: output/espn/stats/" -ForegroundColor $Colors.Info
Write-Host "  • X News posts: output/x_news/integrated/" -ForegroundColor $Colors.Info
Write-Host "  • Weather data: output/weather/" -ForegroundColor $Colors.Info
Write-Host "  • Odds data: output/overtime/" -ForegroundColor $Colors.Info
Write-Host "  • Edge detection: output/edge_detection/" -ForegroundColor $Colors.Info
Write-Host ""

Write-Host "Next steps:" -ForegroundColor $Colors.Info
Write-Host "  1. Review edge detection results" -ForegroundColor $Colors.Info
Write-Host "  2. Check X News impact on edges" -ForegroundColor $Colors.Info
Write-Host "  3. Generate betting recommendations" -ForegroundColor $Colors.Info
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Colors.Header
if ($FailedSteps.Count -eq 0) {
    Write-Host "  [SUCCESS] All data collection steps completed!" -ForegroundColor $Colors.Success
} else {
    Write-Host "  [WARNING] Some steps failed - review errors above" -ForegroundColor $Colors.Warning
}
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Colors.Header
