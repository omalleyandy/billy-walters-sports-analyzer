$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'render-week-card'
Set-Location $env:WIN_PROJECT
uv run walters wk-card --slate data/slate_week9.csv --out exports/week9
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'render-week-card'