$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'wk-card-adv'
Set-Location $env:WIN_PROJECT
uv run walters wk-card-adv --season 2025 --slate-csv data/slate_week9.csv --ratings-csv data/ratings.csv --injuries-csv data/injuries.csv --weather-csv data/weather.csv --derivatives-csv data/derivatives.csv
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'wk-card-adv'