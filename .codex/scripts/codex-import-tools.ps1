#requires -Version 7.0
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $ZipPath,
  [string] $TargetDir = ".\.codex\tools",
  [switch] $DryRun,
  [switch] $Overwrite,
  [switch] $NoBackup
)
$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSEdition -ne 'Core') {
  Write-Host "[info] Relaunching in PowerShell 7..."
  & pwsh -NoProfile -File $PSCommandPath @PSBoundParameters
  exit $LASTEXITCODE
}

$projRoot = Resolve-Path "."
if (-not (Test-Path -LiteralPath $ZipPath)) { throw "ZIP not found: $ZipPath" }
$zipAbs = Resolve-Path -LiteralPath $ZipPath
try { Unblock-File -LiteralPath $zipAbs -ErrorAction SilentlyContinue } catch {}

$targetAbs = Resolve-Path $TargetDir -ErrorAction SilentlyContinue
if (-not $targetAbs) { New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null; $targetAbs = Resolve-Path $TargetDir }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stage = Join-Path ([System.IO.Path]::GetTempPath()) "codex-tools-import-$stamp"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Write-Host "[info] Staging ZIP to: $stage"
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipAbs.Path, $stage)

function Get-Rel {
  param($base, $path)
  $has = [System.IO.Path].GetMethods().Name -contains 'GetRelativePath'
  if ($has) { return ([System.IO.Path]::GetRelativePath($base, $path) -replace '\\','/') }
  $uBase = [Uri](Resolve-Path $base); $uPath = [Uri](Resolve-Path $path)
  return ($uBase.MakeRelativeUri($uPath).ToString()) -replace '%20',' '
}

$doBackup = -not [bool]$NoBackup -and -not [bool]$DryRun
if ($doBackup) {
  $backup = Join-Path $projRoot ".codex\backups\tools-$stamp"
  New-Item -ItemType Directory -Force -Path $backup | Out-Null
  Write-Host "[info] Backing up '$($targetAbs.Path)' → '$backup'"
  Copy-Item -Path "$($targetAbs.Path)\*" -Destination $backup -Recurse -Force -ErrorAction SilentlyContinue
}

$stageFiles  = Get-ChildItem -Path $stage     -Recurse -File
$targetFiles = Get-ChildItem -Path $targetAbs -Recurse -File -ErrorAction SilentlyContinue
$stageMap  = @{}; foreach ($f in $stageFiles)  { $stageMap[(Get-Rel $stage $f.FullName)]      = $f }
$targetMap = @{}; foreach ($f in $targetFiles) { $targetMap[(Get-Rel $targetAbs $f.FullName)] = $f }

$adds=@(); $conflicts=@(); $identical=@()
foreach ($rel in $stageMap.Keys) {
  if ($targetMap.ContainsKey($rel)) {
    $s = Get-FileHash -Algorithm SHA256 -Path $stageMap[$rel].FullName
    $t = Get-FileHash -Algorithm SHA256 -Path $targetMap[$rel].FullName
    if ($s.Hash -ne $t.Hash) { $conflicts += $rel } else { $identical += $rel }
  } else { $adds += $rel }
}

Write-Host "`n=== PLAN ==="
Write-Host "Target:    $($targetAbs.Path)"
Write-Host "Adds:      $($adds.Count)"
Write-Host "Conflicts: $($conflicts.Count)"
Write-Host "Identical: $($identical.Count)"
if ([bool]$DryRun) { Write-Host "`n[dry-run] No files will be changed." }

if (-not [bool]$DryRun) {
  foreach ($rel in $adds) {
    $src = Join-Path $stage $rel; $dst = Join-Path $targetAbs $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
    Copy-Item -Force -LiteralPath $src -Destination $dst
  }
  foreach ($rel in $conflicts) {
    $src = Join-Path $stage $rel; $dst = Join-Path $targetAbs $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
    if ([bool]$Overwrite) { Copy-Item -Force -LiteralPath $src -Destination $dst }
    else {
      $dstAlt = "$dst.import-$stamp"
      Copy-Item -Force -LiteralPath $src -Destination $dstAlt
      Write-Warning "Conflict kept both → existing: $rel, imported: $($rel).import-$stamp"
    }
  }
  Write-Host "[ok] Import finished."
}

$summaryPath = Join-Path $projRoot ".codex\logs\tools-import-$stamp.json"
New-Item -ItemType Directory -Force -Path (Split-Path $summaryPath) | Out-Null
$summary = [ordered]@{
  when       = (Get-Date)
  zip        = $zipAbs.Path
  target     = $targetAbs.Path
  adds       = $adds
  conflicts  = $conflicts
  identical  = $identical
  overwrite  = [bool]$Overwrite
  dry_run    = [bool]$DryRun
  no_backup  = [bool]$NoBackup
  backup_dir = $(if ($doBackup) { $backup } else { $null })
}
$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryPath -Encoding UTF8
Write-Host "[info] Wrote summary: $summaryPath"
