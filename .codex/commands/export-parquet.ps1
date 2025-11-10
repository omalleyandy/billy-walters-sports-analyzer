$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'export-parquet'
Set-Location $env:WIN_PROJECT
uv run python scripts/export_parquet.py --out exports/latest.parquet
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'export-parquet'