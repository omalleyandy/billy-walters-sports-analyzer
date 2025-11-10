$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'lint'
Set-Location $env:WIN_PROJECT
uv run ruff check
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'lint'