$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'tests'
Set-Location $env:WIN_PROJECT
uv run pytest -q
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'tests'