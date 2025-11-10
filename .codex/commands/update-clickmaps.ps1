$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'update-clickmaps'
Set-Location $env:WIN_PROJECT
uv run python scripts/update_clickmaps.py --dir clickmaps
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'update-clickmaps'