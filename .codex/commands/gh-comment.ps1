# Usage: pwsh -File .codex/commands/gh-comment.ps1 123 "Build finished ✅"
param([Parameter(Mandatory)] [int]$Pr,[Parameter(Mandatory)] [string]$Body)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'gh-comment'
Import-Module "$PSScriptRoot/../agents-utils.psm1" -Force
Invoke-GH-Comment -PR $Pr -Body $Body
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'gh-comment'