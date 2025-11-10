$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'validate-config'
Set-Location $env:WIN_PROJECT
uv run python scripts/validate_config.py
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'validate-config'