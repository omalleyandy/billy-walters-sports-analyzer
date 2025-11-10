$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'scrape-overtime'
Set-Location $env:WIN_PROJECT
uv run scrapy crawl overtime_liveplus -O exports/nfl_game.json
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'scrape-overtime'