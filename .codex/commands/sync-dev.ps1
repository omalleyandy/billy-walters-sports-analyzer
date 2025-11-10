$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'sync-dev'
Set-Location $env:WIN_PROJECT
uv sync --extra dev
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'sync-dev'