# PowerShell Odds Analysis Script
# Usage: .\analyze_odds.ps1 -File nfl_odds.json
# Or: .\analyze_odds.ps1 -File cfb_odds.json

param(
    [string]$File = "nfl_odds.json"
)

if (-not (Test-Path $File)) {
    Write-Host "Error: File '$File' not found!" -ForegroundColor Red
    exit 1
}

# Load the JSON data
Write-Host "`nLoading $File..." -ForegroundColor Cyan
$odds = Get-Content $File | ConvertFrom-Json

# Determine sport
$sport = if ($odds[0].sport -eq "nfl") { "NFL" } else { "College Football" }

Write-Host "`n" + ("=" * 70) -ForegroundColor Green
Write-Host "  $sport ODDS ANALYSIS" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green

# Summary Statistics
Write-Host "`n📊 SUMMARY:" -ForegroundColor Cyan
Write-Host "  Total line options: $($odds.Count)"

$uniqueGames = $odds | ForEach-Object { "$($_.teams.away) @ $($_.teams.home)" } | Sort-Object -Unique
Write-Host "  Unique matchups: $($uniqueGames.Count)"

# Games by Date
Write-Host "`n📅 GAMES BY DATE:" -ForegroundColor Cyan
$odds | Group-Object event_date |
    Sort-Object Name |
    ForEach-Object {
        $date = ([DateTime]$_.Name).ToString("ddd, MMM dd")
        Write-Host "  $date`: $($_.Count) line options"
    }

# Unique Matchups
Write-Host "`n🏈 UNIQUE MATCHUPS:" -ForegroundColor Cyan
$uniqueGames | ForEach-Object { Write-Host "  $_" }

# Full Game Lines (spread > 1 or < -1)
Write-Host "`n🎯 FULL GAME LINES (Spread > 1):" -ForegroundColor Yellow
$fullGameLines = $odds | Where-Object {
    $_.markets.spread.away.line -ne $null -and
    [Math]::Abs($_.markets.spread.away.line) -gt 1
}
Write-Host "  Found: $($fullGameLines.Count) full game lines`n"

foreach ($game in $fullGameLines | Sort-Object event_date, event_time) {
    $awaySpread = $game.markets.spread.away
    $homeSpread = $game.markets.spread.home
    $total = $game.markets.total.over
    $awayML = $game.markets.moneyline.away.price
    $homeML = $game.markets.moneyline.home.price

    Write-Host "  $($game.rotation_number) - $($game.event_date) $($game.event_time)" -ForegroundColor White
    Write-Host "    $($game.teams.away) @ $($game.teams.home)" -ForegroundColor White
    Write-Host "    Spread: $($game.teams.away) $($awaySpread.line) ($($awaySpread.price)) | $($game.teams.home) $($homeSpread.line) ($($homeSpread.price))"

    if ($total.line -ne $null) {
        Write-Host "    Total: O/U $($total.line) ($($game.markets.total.over.price)/$($game.markets.total.under.price))"
    }

    if ($awayML -ne $null -and $homeML -ne $null) {
        Write-Host "    Moneyline: $($awayML) / $($homeML)"
    }
    Write-Host ""
}

# Big Favorites (spread > 7 for NFL, > 14 for CFB)
$bigSpreadThreshold = if ($sport -eq "NFL") { 7 } else { 14 }
Write-Host "`n🔥 BIG FAVORITES (Spread > $bigSpreadThreshold):" -ForegroundColor Red

$bigFavorites = $odds | Where-Object {
    $_.markets.spread.home.line -ne $null -and
    $_.markets.spread.home.line -lt -$bigSpreadThreshold
}

if ($bigFavorites.Count -gt 0) {
    foreach ($game in $bigFavorites | Sort-Object { $_.markets.spread.home.line }) {
        Write-Host "  $($game.teams.away) (+$($game.markets.spread.away.line)) @ $($game.teams.home) ($($game.markets.spread.home.line))" -ForegroundColor White
        Write-Host "    Date: $($game.event_date) $($game.event_time)"
        Write-Host "    Total: O/U $($game.markets.total.over.line)"
        if ($game.markets.moneyline.away.price -ne $null) {
            Write-Host "    ML: $($game.markets.moneyline.away.price) / $($game.markets.moneyline.home.price)"
        }
        Write-Host ""
    }
} else {
    Write-Host "  No games with spreads > $bigSpreadThreshold`n"
}

# High Totals (> 50 for NFL, > 60 for CFB)
$highTotalThreshold = if ($sport -eq "NFL") { 50 } else { 60 }
Write-Host "`n🎯 HIGH SCORING GAMES (Total > $highTotalThreshold):" -ForegroundColor Magenta

$highTotals = $odds | Where-Object {
    $_.markets.total.over.line -ne $null -and
    $_.markets.total.over.line -gt $highTotalThreshold
}

if ($highTotals.Count -gt 0) {
    foreach ($game in $highTotals | Sort-Object { -$_.markets.total.over.line }) {
        Write-Host "  $($game.teams.away) @ $($game.teams.home): O/U $($game.markets.total.over.line)" -ForegroundColor White
        Write-Host "    Date: $($game.event_date) $($game.event_time)"
        Write-Host "    Spread: $($game.markets.spread.home.line)"
        Write-Host ""
    }
} else {
    Write-Host "  No games with totals > $highTotalThreshold`n"
}

# Low Totals (< 40 for NFL, < 45 for CFB)
$lowTotalThreshold = if ($sport -eq "NFL") { 40 } else { 45 }
Write-Host "`n🥶 LOW SCORING GAMES (Total < $lowTotalThreshold):" -ForegroundColor Blue

$lowTotals = $odds | Where-Object {
    $_.markets.total.over.line -ne $null -and
    $_.markets.total.over.line -lt $lowTotalThreshold
}

if ($lowTotals.Count -gt 0) {
    foreach ($game in $lowTotals | Sort-Object { $_.markets.total.over.line }) {
        Write-Host "  $($game.teams.away) @ $($game.teams.home): O/U $($game.markets.total.over.line)" -ForegroundColor White
        Write-Host "    Date: $($game.event_date) $($game.event_time)"
        Write-Host ""
    }
} else {
    Write-Host "  No games with totals < $lowTotalThreshold`n"
}

# Export full game lines to separate file
$outputFile = $File -replace "\.json$", "_full_game.json"
Write-Host "`n💾 EXPORT:" -ForegroundColor Green
Write-Host "  Saving $($fullGameLines.Count) full game lines to: $outputFile"
$fullGameLines | ConvertTo-Json -Depth 10 | Out-File $outputFile

Write-Host "`n" + ("=" * 70) -ForegroundColor Green
Write-Host "Analysis complete!" -ForegroundColor Green
Write-Host ("=" * 70) + "`n" -ForegroundColor Green
