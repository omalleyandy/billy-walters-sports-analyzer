# Usage (merge):  pwsh -File .codex/commands/gh-merge.ps1 123 merge
# Usage (squash): pwsh -File .codex/commands/gh-merge.ps1 123 squash
param([Parameter(Mandatory)] [int]$Pr,[ValidateSet('merge','squash')] [string]$Method='merge')
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'gh-merge'
Import-Module "$PSScriptRoot/../agents-utils.psm1" -Force
Invoke-GH-Merge -PR $Pr -Method $Method
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'gh-merge'