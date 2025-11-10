# CLAUDE.md

## Commands
- `wk-card:dry-run` → run card with gates/price checks without placing bets.
- `wk-card:run` → live mode.

### JSON command examples
`/commands/wk-card.dry-run.json`
```json
{ "cmd": "uv run walters-analyzer wk-card --file ./cards/wk-card-2025-10-31.json --dry-run" }
```
`/commands/wk-card.run.json`
```json
{ "cmd": "uv run walters-analyzer wk-card --file ./cards/wk-card-2025-10-31.json" }
```

## Hooks
- `pre-run`: ensure `.env` loaded, confirm injuries/weather/steam gates are true.
- `post-run`: log CLV vs. close and append bias_log.

## Data Collection Commands

### Highlightly API (FREE tier)
- `highlightly:static` → collect teams and bookmakers (once daily)
- `highlightly:gameday` → collect matches, highlights, standings (game day)
- `highlightly:all` → complete Highlightly data collection

### PowerShell Scripts
`./scripts/highlightly_daily_static.ps1`
```powershell
# Fetch teams and bookmakers (FREE tier)
.\scripts\highlightly_daily_static.ps1
```

`./scripts/highlightly_gameday.ps1`
```powershell
# Fetch matches, highlights, standings for today
.\scripts\highlightly_gameday.ps1

# Or specify a date
.\scripts\highlightly_gameday.ps1 -Date "2024-11-10"
```

`./scripts/collect_all_data.ps1`
```powershell
# Complete data collection: Highlightly + overtime.ag + ESPN injuries
.\scripts\collect_all_data.ps1

# Skip static data if already collected
.\scripts\collect_all_data.ps1 -SkipStatic

# Specify date
.\scripts\collect_all_data.ps1 -Date "2024-11-10"
```

### Individual Commands
```powershell
# Highlightly (FREE tier endpoints only)
uv run walters-analyzer scrape-highlightly --endpoint teams --sport both
uv run walters-analyzer scrape-highlightly --endpoint bookmakers --sport both
uv run walters-analyzer scrape-highlightly --endpoint matches --sport both --date 2024-11-08
uv run walters-analyzer scrape-highlightly --endpoint highlights --sport both --date 2024-11-08
uv run walters-analyzer scrape-highlightly --endpoint standings --sport both

# overtime.ag odds
uv run walters-analyzer scrape-overtime --sport both

# ESPN injuries
uv run walters-analyzer scrape-injuries --sport nfl
uv run walters-analyzer scrape-injuries --sport cfb
```

## Note: Highlightly Odds Locked
The `odds` endpoint requires a paid Highlightly plan. Use overtime.ag for betting odds instead.
