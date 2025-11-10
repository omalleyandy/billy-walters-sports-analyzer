#requires -Version 7.0
<#
.SYNOPSIS
  Generate commands.json from .codex/commands/*.ps1 Agents (SSOT).

.DESCRIPTION
  - Walks .codex/commands
  - Skips files starting with "_" (templates/private)
  - Extracts:
      * id            = file stem (e.g., 'devtools-espn-discover')
      * name          = same as id
      * description   = first contiguous top-of-file comment block (optional)
      * cwd           = repo root (.)
      * cmd           = ["pwsh","-NoProfile","-File",".codex/commands/<file>.ps1"]
      * argspec       = script param names + required flag (via Get-Command)
  - Writes commands.json atomically.

.PARAMETER Output
  Path to write commands.json (default: ./commands.json)

.PARAMETER CommandsDir
  Directory of agents (default: ./.codex/commands)

.PARAMETER DryRun
  Print JSON to stdout instead of writing file.

.EXAMPLE
  pwsh -File .codex/scripts/generate-commands-json.ps1

.EXAMPLE
  pwsh -File .codex/scripts/generate-commands-json.ps1 -Output .codex/cache/commands.json -DryRun
#>
[CmdletBinding()]
param(
  [string] $Output = "./commands.json",
  [string] $CommandsDir = "./.codex/commands",
  [switch] $DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path "."
$absCmdDir = Resolve-Path $CommandsDir

if (-not (Test-Path $absCmdDir)) {
  throw "Commands directory not found: $absCmdDir"
}

function Get-TopCommentBlock {
  param([string] $Path)
  $lines = Get-Content -Raw -Path $Path -ErrorAction Stop -Encoding UTF8 -Delimiter "`n" | Split-String "`n"
  $desc = @()
  foreach ($ln in $lines) {
    if ($ln.Trim().StartsWith('#')) {
      $desc += ($ln -replace '^\s*#\s?', '')
    } elseif ($ln.Trim() -eq '') {
      if ($desc.Count -gt 0) { break } else { continue }
    } else {
      break
    }
  }
  ($desc -join " ").Trim()
}

$items = Get-ChildItem -Path $absCmdDir -Filter *.ps1 -File -Recurse |
  Where-Object {
    # exclude templates/private (leading underscore) and anything in experimental/
    $_.BaseName -notmatch '(^_|\.test$)' -and $_.FullName -notmatch '\\experimental\\'
  } |
  Sort-Object FullName

$commands = @()

foreach ($f in $items) {
  $rel = Resolve-Path -Relative $f.FullName
  $id  = $f.BaseName
  $desc = Get-TopCommentBlock -Path $f.FullName

  # Try to reflect parameters from the script
  $argspec = @()
  try {
    $cmdInfo = Get-Command -ErrorAction Stop -Name $f.FullName
    foreach ($p in $cmdInfo.Parameters.GetEnumerator() | Sort-Object Key) {
      $name = $p.Key
      $meta = $p.Value
      $req  = -not $meta.IsOptional
      $argspec += [ordered]@{
        name     = $name
        required = $req
        # You can extend here with type/default: ($meta.ParameterType.FullName), ($meta.Attributes | ?{ $_ -is [System.Management.Automation.ParameterAttribute] }).DefaultValue
      }
    }
  } catch {
    # Non-reflectable script (no param() block). That's fine.
  }

  $commands += [ordered]@{
    id          = $id
    name        = $id
    cwd         = "."
    description = $desc
    cmd         = @("pwsh","-NoProfile","-File",$rel)
    argspec     = $argspec
  }
}

$payload = [ordered]@{
  version      = 1
  generated_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
  root         = (Resolve-Path ".").Path
  commands     = $commands
}

$json = $payload | ConvertTo-Json -Depth 8

if ($DryRun) {
  $json
  exit 0
}

# atomic write
$tmp = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tmp -Value $json -Encoding UTF8
Move-Item -Force -Path $tmp -Destination (Resolve-Path $Output).Path -ErrorAction SilentlyContinue
if (-not (Test-Path $Output)) {
  # If Output didn't previously exist, Move-Item above may fail; just save directly.
  Set-Content -Path $Output -Value $json -Encoding UTF8
}
Write-Host "[ok] wrote $Output"
