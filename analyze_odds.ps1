param(
    [Parameter(Mandatory=$true)]
    [string]$File,

    [double]$HighTotalThreshold = 55.0,
    [double]$LowTotalThreshold = 42.0
)

# Validate file exists
if (-not (Test-Path $File)) {
    Write-Host "Error: File '$File' not found" -ForegroundColor Red
    exit 1
}

# Read and parse JSON
try {
    $oddsData = Get-Content $File -Raw | ConvertFrom-Json
} catch {
    Write-Host "Error: Failed to parse JSON from '$File'" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Validate data
if (-not $oddsData) {
    Write-Host "Error: No data found in file" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   ODDS ANALYSIS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Source: $File" -ForegroundColor Gray
Write-Host "Games found: $($oddsData.Count)" -ForegroundColor Gray
Write-Host ""

# Create unique game identifier for deduplication
$uniqueGames = $oddsData | ForEach-Object { "$($_.teams.away) `@ $($_.teams.home)" } | Select-Object -Unique

Write-Host "Unique matchups: $($uniqueGames.Count)`n" -ForegroundColor Yellow

# ========================================
# SPREADS ANALYSIS
# ========================================
Write-Host "`n[SPREADS]" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Gray

$gamesWithSpreads = $oddsData | Where-Object {
    $_.markets.spread.away.line -ne $null -or $_.markets.spread.home.line -ne $null
}

if ($gamesWithSpreads.Count -gt 0) {
    foreach ($game in $gamesWithSpreads) {
        $awayLine = if ($game.markets.spread.away.line) { $game.markets.spread.away.line } else { "N/A" }
        $awayPrice = if ($game.markets.spread.away.price) { $game.markets.spread.away.price } else { "" }
        $homeLine = if ($game.markets.spread.home.line) { $game.markets.spread.home.line } else { "N/A" }
        $homePrice = if ($game.markets.spread.home.price) { $game.markets.spread.home.price } else { "" }

        # Format spread display with proper signs
        $awayDisplay = if ($awayLine -ne "N/A") {
            if ($awayLine -gt 0) { "+$awayLine" } else { "$awayLine" }
        } else { "N/A" }

        $homDisplay = if ($homeLine -ne "N/A") {
            if ($homeLine -gt 0) { "+$homeLine" } else { "$homeLine" }
        } else { "N/A" }

        Write-Host "  $($game.teams.away) ($awayDisplay $awayPrice) `@ $($game.teams.home) ($homDisplay $homePrice)" -ForegroundColor White
    }
} else {
    Write-Host "  No spreads available" -ForegroundColor Yellow
}

# ========================================
# TOTALS ANALYSIS
# ========================================
Write-Host "`n[TOTALS]" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Gray

$gamesWithTotals = $oddsData | Where-Object {
    $_.markets.total.over.line -ne $null -or $_.markets.total.under.line -ne $null
}

if ($gamesWithTotals.Count -gt 0) {
    foreach ($game in $gamesWithTotals) {
        $total = if ($game.markets.total.over.line) {
            $game.markets.total.over.line
        } elseif ($game.markets.total.under.line) {
            $game.markets.total.under.line
        } else {
            $null
        }

        if ($total) {
            $overPrice = if ($game.markets.total.over.price) { " ($($game.markets.total.over.price))" } else { "" }
            $underPrice = if ($game.markets.total.under.price) { " ($($game.markets.total.under.price))" } else { "" }

            Write-Host "  $($game.teams.away) `@ $($game.teams.home): O/U $total" -ForegroundColor White
            Write-Host "    Over $total$overPrice | Under $total$underPrice" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  No totals available" -ForegroundColor Yellow
}

# ========================================
# HIGH SCORING GAMES
# ========================================
Write-Host "`n[HIGH SCORING GAMES (Total `> $HighTotalThreshold)]" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Gray

$highScoringGames = $gamesWithTotals | Where-Object {
    $total = if ($_.markets.total.over.line) { $_.markets.total.over.line } else { $_.markets.total.under.line }
    $total -and $total -gt $HighTotalThreshold
} | Sort-Object {
    if ($_.markets.total.over.line) { $_.markets.total.over.line } else { $_.markets.total.under.line }
} -Descending

if ($highScoringGames.Count -gt 0) {
    foreach ($game in $highScoringGames) {
        $total = if ($game.markets.total.over.line) { $game.markets.total.over.line } else { $game.markets.total.under.line }
        Write-Host "  $($game.teams.away) `@ $($game.teams.home): O/U $total" -ForegroundColor Cyan
    }
    Write-Host "`n  Found $($highScoringGames.Count) high-scoring games" -ForegroundColor Yellow
} else {
    Write-Host "  No games with totals `> $HighTotalThreshold" -ForegroundColor Yellow
}

# ========================================
# LOW SCORING GAMES
# ========================================
Write-Host "`n[LOW SCORING GAMES (Total `< $LowTotalThreshold)]" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Gray

$lowScoringGames = $gamesWithTotals | Where-Object {
    $total = if ($_.markets.total.over.line) { $_.markets.total.over.line } else { $_.markets.total.under.line }
    $total -and $total -lt $LowTotalThreshold
} | Sort-Object {
    if ($_.markets.total.over.line) { $_.markets.total.over.line } else { $_.markets.total.under.line }
}

if ($lowScoringGames.Count -gt 0) {
    foreach ($game in $lowScoringGames) {
        $total = if ($game.markets.total.over.line) { $game.markets.total.over.line } else { $game.markets.total.under.line }
        Write-Host "  $($game.teams.away) `@ $($game.teams.home): O/U $total" -ForegroundColor Cyan
    }
    Write-Host "`n  Found $($lowScoringGames.Count) low-scoring games" -ForegroundColor Yellow
} else {
    Write-Host "  No games with totals `< $LowTotalThreshold" -ForegroundColor Yellow
}

# ========================================
# SUMMARY
# ========================================
Write-Host "`n[SUMMARY]" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "  Total games: $($oddsData.Count)" -ForegroundColor White
Write-Host "  Games with spreads: $($gamesWithSpreads.Count)" -ForegroundColor White
Write-Host "  Games with totals: $($gamesWithTotals.Count)" -ForegroundColor White
Write-Host "  High-scoring games (`> $HighTotalThreshold): $($highScoringGames.Count)" -ForegroundColor White
Write-Host "  Low-scoring games (`< $LowTotalThreshold): $($lowScoringGames.Count)" -ForegroundColor White

Write-Host "`n========================================`n" -ForegroundColor Cyan
