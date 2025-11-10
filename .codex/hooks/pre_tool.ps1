#requires -Version 7.2
param([string]$ToolName = 'unknown')
Import-Module "$PSScriptRoot/../agents-utils.psm1" -Force
$ErrorActionPreference = 'Stop'

Write-RunHeader -ToolName $ToolName -Project $env:WIN_PROJECT
Assert-ProjectPresent
Assert-Uv

# Auto-warnings
$missing = Test-EnvVars -Names @('ACCUWEATHER_API_KEY')
if ($missing.Count -gt 0) {
  Write-Colored -Level Warn -Message ("[warn] missing env vars: {0}" -f ($missing -join ', '))
}

# Gentle dirty notice
$state = Get-RepoState -Path $env:WIN_PROJECT
if ($state.Dirty -eq 'dirty') {
  Write-Colored -Level Warn -Message "[warn] git working tree is DIRTY"
}