#requires -Version 7.0
<#
.SYNOPSIS
  Run a command by id from commands.json with optional args interpolation.

.DESCRIPTION
  - Loads commands.json (default ./commands.json)
  - Finds entry by .commands[].id
  - Interpolates ${key} placeholders in cmd array from -Args hashtable
  - Executes with working directory = cwd (relative to repo root)
  - Streams stdout/stderr and returns the child exit code

.PARAMETER Id
  Id of the command in commands.json

.PARAMETER Args
  Hashtable of key/value to substitute into ${key} placeholders

.PARAMETER JsonPath
  Path to commands.json (default: ./commands.json)

.PARAMETER TimeoutSec
  Process timeout (default 1800 sec)

.EXAMPLE
  pwsh -File .codex/scripts/run-json-command.ps1 -Id devtools-espn-discover

.EXAMPLE
  pwsh -File .codex/scripts/run-json-command.ps1 -Id espn.pull -Args @{ dates='20251106-20251109'; limit='200' }
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $Id,
  [hashtable] $Args,
  [string] $JsonPath = "./commands.json",
  [int] $TimeoutSec = 1800
)

$ErrorActionPreference = 'Stop'
$projRoot = Resolve-Path "."
if (-not (Test-Path $JsonPath)) {
  throw "commands.json not found at: $JsonPath"
}

$json = Get-Content -Raw -Path $JsonPath | ConvertFrom-Json
$cmdDef = $json.commands | Where-Object { $_.id -eq $Id }
if (-not $cmdDef) { throw "Command id '$Id' not found in $JsonPath" }

# Resolve CWD relative to repo root
$cwd = Resolve-Path (Join-Path $projRoot $cmdDef.cwd)
Push-Location $cwd
try {
  # Interpolate ${name}
  $cmd = @()
  foreach ($part in $cmdDef.cmd) {
    $cmd += ([regex]::Replace($part, '\$\{(\w+)\}', {
      param($m)
      $key = $m.Groups[1].Value
      if ($Args -and $Args.ContainsKey($key)) { return [string]$Args[$key] }
      return ""
    }))
  }

  Write-Host "[info] id=$($cmdDef.id) cwd=$cwd"
  Write-Host "[info] cmd=$($cmd -join ' ')"

  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName  = $cmd[0]
  $psi.Arguments = ($cmd | Select-Object -Skip 1) -join ' '
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $psi.UseShellExecute        = $false

  $p = [System.Diagnostics.Process]::new()
  $p.StartInfo = $psi
  [void]$p.Start()

  if (-not $p.WaitForExit($TimeoutSec * 1000)) {
    try { $p.Kill() } catch {}
    throw "Timeout after $TimeoutSec seconds"
  }

  $out = $p.StandardOutput.ReadToEnd()
  $err = $p.StandardError.ReadToEnd()

  if ($p.ExitCode -ne 0) {
    if ($out) { Write-Host $out }
    if ($err) { Write-Error $err }
    exit $p.ExitCode
  }

  if ($out) { Write-Output $out }
}
finally {
  Pop-Location
}