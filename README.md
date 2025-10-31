# Walters Analyzer (WSA)

Canonical, uv-based repo scaffold so we stay in sync. One env per project.
This repo includes:
- **CLI**: `walters-analyzer` with `wk-card` command
- **Cards**: JSON snapshots in `./cards/`
- **Scrapers (skeleton)**: VegasInsider spider layout (Scrapy + Playwright)
- **Claude**: `/commands` and `/hooks` placeholders
- **Env**: `.env.example` for required keys

## Quickstart (Windows PowerShell)
```powershell
Set-Location "C:\Users\omall\Documents\python_projects\billy_walters_sports_betting"
# unzip contents here
uv sync
uv run walters-analyzer wk-card --file .\cards\wk-card-2025-10-31.json --dry-run
uv run walters-analyzer wk-card --file .\cards\wk-card-2025-10-31.json
```

## WSL
```bash
cd ~/Documents/python_projects/billy_walters_sports_betting
uv sync
uv run walters-analyzer wk-card --file ./cards/wk-card-2025-10-31.json --dry-run
```

## Extras (scraping)
```powershell
uv sync --extra scraping   # correct flag is --extra
```
