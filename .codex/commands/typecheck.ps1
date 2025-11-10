$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'typecheck'
Set-Location $env:WIN_PROJECT
uv run mypy src || $true  # soft gate
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'typecheck'