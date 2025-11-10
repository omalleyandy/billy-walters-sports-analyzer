#requires -Version 7.2
param([string]$ToolName = 'unknown')
Import-Module "$PSScriptRoot/../agents-utils.psm1" -Force
$ErrorActionPreference = 'Stop'
Write-RunMeta -ToolName $ToolName -Project $env:WIN_PROJECT