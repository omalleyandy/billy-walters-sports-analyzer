# Windows PowerShell Guide for Odds Analysis

Since `jq` isn't available on Windows by default, here are PowerShell alternatives for analyzing your scraped odds data.

## 🎯 Quick Analysis Script

We've created a comprehensive analysis script for you:

```powershell
# Analyze NFL odds
.\analyze_odds.ps1 -File nfl_odds.json

# Analyze College Football odds
.\analyze_odds.ps1 -File cfb_odds.json
```

**What it shows:**
- Summary statistics
- Games by date
- All unique matchups
- Full game lines (filtered from half/quarter lines)
- Big favorites (spread > 7 for NFL, > 14 for CFB)
- High scoring games (total > 50 for NFL, > 60 for CFB)
- Low scoring games (total < 40 for NFL, < 45 for CFB)
- Exports full game lines to separate file

## 📊 Manual PowerShell Commands

### View Your Data

```powershell
# Load the data
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json

# Count total games
$nfl.Count

# Show first 3 games
$nfl | Select-Object -First 3 | ForEach-Object {
    Write-Host "$($_.teams.away) @ $($_.teams.home)"
    Write-Host "Spread: $($_.markets.spread.away.line) / $($_.markets.spread.home.line)"
    Write-Host "Total: $($_.markets.total.over.line)"
    Write-Host ""
}
```

### Show Just Matchups

```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json
$nfl | ForEach-Object { "$($_.teams.away) @ $($_.teams.home)" } | Sort-Object -Unique
```

### Filter Full Game Lines Only

Full game lines typically have larger spreads (±1.5 or more):

```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json
$fullGame = $nfl | Where-Object { [Math]::Abs($_.markets.spread.away.line) -gt 1 }
Write-Host "Found $($fullGame.Count) full game lines"
```

### Find Big Favorites

```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json

# NFL: Spreads > 7 points
$bigFavorites = $nfl | Where-Object { $_.markets.spread.home.line -lt -7 }
$bigFavorites | ForEach-Object {
    "$($_.teams.away) (+$($_.markets.spread.away.line)) @ $($_.teams.home) ($($_.markets.spread.home.line))"
}
```

### Find High Scoring Games

```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json

# Totals over 50
$highScoring = $nfl | Where-Object { $_.markets.total.over.line -gt 50 }
$highScoring | ForEach-Object {
    "$($_.teams.away) @ $($_.teams.home): O/U $($_.markets.total.over.line)"
}
```

### Show Games by Date

```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json
$nfl | Group-Object event_date |
    Sort-Object Name |
    ForEach-Object {
        "$($_.Name): $($_.Count) line options"
    }
```

### Export to CSV

```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json

# Create flattened CSV
$nfl | Select-Object -Property `
    @{Name='Away Team';Expression={$_.teams.away}},
    @{Name='Home Team';Expression={$_.teams.home}},
    @{Name='Date';Expression={$_.event_date}},
    @{Name='Time';Expression={$_.event_time}},
    @{Name='Away Spread';Expression={$_.markets.spread.away.line}},
    @{Name='Away Spread Price';Expression={$_.markets.spread.away.price}},
    @{Name='Home Spread';Expression={$_.markets.spread.home.line}},
    @{Name='Home Spread Price';Expression={$_.markets.spread.home.price}},
    @{Name='Total';Expression={$_.markets.total.over.line}},
    @{Name='Over Price';Expression={$_.markets.total.over.price}},
    @{Name='Under Price';Expression={$_.markets.total.under.price}},
    @{Name='Away ML';Expression={$_.markets.moneyline.away.price}},
    @{Name='Home ML';Expression={$_.markets.moneyline.home.price}} |
Export-Csv -Path nfl_odds.csv -NoTypeInformation

Write-Host "Exported to nfl_odds.csv"
```

### Find Specific Teams

```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json

# Find all Chiefs games
$nfl | Where-Object {
    $_.teams.away -like "*Chiefs*" -or $_.teams.home -like "*Chiefs*"
} | ForEach-Object {
    Write-Host "$($_.teams.away) @ $($_.teams.home)"
    Write-Host "Spread: $($_.markets.spread.home.line)"
    Write-Host "Total: $($_.markets.total.over.line)"
    Write-Host ""
}
```

### Compare Odds Between Books

If you scrape multiple times:

```powershell
# Load two snapshots
$odds1 = Get-Content odds_snapshot1.json | ConvertFrom-Json
$odds2 = Get-Content odds_snapshot2.json | ConvertFrom-Json

# Compare spreads for same game
$game1 = $odds1[0]
$game2 = $odds2[0]

Write-Host "Snapshot 1: $($game1.markets.spread.home.line)"
Write-Host "Snapshot 2: $($game2.markets.spread.home.line)"
Write-Host "Line Movement: $($game2.markets.spread.home.line - $game1.markets.spread.home.line) points"
```

## 🔄 Scraping Both Sports

```powershell
# Scrape both CFB and NFL
uv run scrapy crawl overtime_api -a sport=cfb -o cfb_odds.json
uv run scrapy crawl overtime_api -a sport=nfl -o nfl_odds.json

# Analyze both
.\analyze_odds.ps1 -File cfb_odds.json
.\analyze_odds.ps1 -File nfl_odds.json
```

## 📅 Automated Scraping with Task Scheduler

Create a batch file `scrape_odds.bat`:

```batch
@echo off
cd /d C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

REM Generate timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

REM Scrape odds
uv run scrapy crawl overtime_api -a sport=cfb -o odds\cfb_%timestamp%.json
uv run scrapy crawl overtime_api -a sport=nfl -o odds\nfl_%timestamp%.json

REM Run analysis
powershell -File analyze_odds.ps1 -File odds\cfb_%timestamp%.json > reports\cfb_%timestamp%.txt
powershell -File analyze_odds.ps1 -File odds\nfl_%timestamp%.json > reports\nfl_%timestamp%.txt

echo Scrape completed at %timestamp%
```

Then schedule it with Task Scheduler to run every hour.

## 🎨 Pretty Display Function

Add this to your PowerShell profile for nicer output:

```powershell
function Show-OddsGame {
    param($Game)

    Write-Host "`n$($Game.rotation_number) - $($Game.event_date) $($Game.event_time)" -ForegroundColor Cyan
    Write-Host "  $($Game.teams.away) @ $($Game.teams.home)" -ForegroundColor White

    if ($Game.markets.spread.away.line) {
        Write-Host "  Spread: " -NoNewline
        Write-Host "$($Game.teams.away) $($Game.markets.spread.away.line) " -NoNewline -ForegroundColor Green
        Write-Host "($($Game.markets.spread.away.price)) " -NoNewline
        Write-Host "| " -NoNewline
        Write-Host "$($Game.teams.home) $($Game.markets.spread.home.line) " -NoNewline -ForegroundColor Red
        Write-Host "($($Game.markets.spread.home.price))"
    }

    if ($Game.markets.total.over.line) {
        Write-Host "  Total: O/U $($Game.markets.total.over.line) " -NoNewline
        Write-Host "($($Game.markets.total.over.price)/$($Game.markets.total.under.price))" -ForegroundColor Yellow
    }

    if ($Game.markets.moneyline.away.price) {
        Write-Host "  ML: $($Game.markets.moneyline.away.price) / $($Game.markets.moneyline.home.price)" -ForegroundColor Magenta
    }
}

# Usage:
# $nfl = Get-Content nfl_odds.json | ConvertFrom-Json
# $nfl | ForEach-Object { Show-OddsGame $_ }
```

## 🚀 Integration with Billy Walters System

Combine odds scraping with injury analysis:

```powershell
# 1. Scrape latest odds
uv run scrapy crawl overtime_api -a sport=cfb -o cfb_odds.json
uv run scrapy crawl overtime_api -a sport=nfl -o nfl_odds.json

# 2. Scrape injury reports
uv run walters-analyzer scrape-injuries --sport cfb
uv run walters-analyzer scrape-injuries --sport nfl

# 3. Run Billy Walters analysis
uv run python analyze_games_with_injuries.py

# 4. Analyze the odds
.\analyze_odds.ps1 -File cfb_odds.json
.\analyze_odds.ps1 -File nfl_odds.json
```

## 💡 Pro Tips

### Tip 1: Save Output to File
```powershell
.\analyze_odds.ps1 -File nfl_odds.json > nfl_analysis.txt
notepad nfl_analysis.txt
```

### Tip 2: Create Timestamped Snapshots
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
uv run scrapy crawl overtime_api -a sport=nfl -o "odds_archive\nfl_$timestamp.json"
```

### Tip 3: Quick Game Lookup
```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json
$nfl | Where-Object { $_.teams.away -eq "Kansas City Chiefs" }
```

### Tip 4: Export Full Game Lines Only
```powershell
$nfl = Get-Content nfl_odds.json | ConvertFrom-Json
$fullGame = $nfl | Where-Object { [Math]::Abs($_.markets.spread.away.line) -gt 1 }
$fullGame | ConvertTo-Json -Depth 10 | Out-File nfl_full_game.json
```

## 📚 More Resources

- **API Documentation**: See `OVERTIME_API.md`
- **Quick Start**: See `API_SPIDER_QUICK_START.md`
- **Project README**: See `README.md`

---

**Need `jq` on Windows?**

You can install `jq` on Windows using:
- **Chocolatey**: `choco install jq`
- **Scoop**: `scoop install jq`
- **Manual**: Download from https://jqlang.github.io/jq/download/

But PowerShell works great without it! 🚀
