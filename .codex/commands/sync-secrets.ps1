# .codex/commands/sync-secrets.ps1
# Sync selected Windows environment variables -> GitHub Actions Secrets (repo-level)
# Requires: GitHub CLI (gh) authenticated with repo access (gh auth login)

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)] [string]$Owner,            # e.g., "omalleyandy"
  [Parameter(Mandatory=$true)] [string]$Repo,             # e.g., "billy-walters-sports-analyzer"
  [Parameter(Mandatory=$true)] [string[]]$Names,          # e.g., @('ACCUWEATHER_API_KEY','ANOTHER_KEY')
  [switch]$DryRun,                                        # Show what would happen
  [switch]$UseMachineScope                                # Pull from Machine scope in addition to User
)

$ErrorActionPreference = 'Stop'

function Write-Colored([string]$Level,[string]$Message) {
  switch ($Level) {
    'Header'  { Write-Host $Message -ForegroundColor Cyan }
    'Info'    { Write-Host $Message -ForegroundColor Gray }
    'Warn'    { Write-Host $Message -ForegroundColor Yellow }
    'Error'   { Write-Host $Message -ForegroundColor Red }
    'Success' { Write-Host $Message -ForegroundColor Green }
    default   { Write-Host $Message }
  }
}

# ---- Preconditions
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw "GitHub CLI 'gh' not found. Install with: winget install GitHub.cli"
}

# Ensure gh is authenticated
try {
  gh auth status | Out-Null
} catch {
  throw "Not authenticated with gh. Run: gh auth login"
}

$repoSlug = "$Owner/$Repo"
Write-Colored 'Header' "Sync Windows env → GitHub Secrets  repo=$repoSlug"
Write-Colored 'Info'   ("Mode: {0}" -f ($(if($DryRun){"DRY-RUN"}else{"LIVE"})))

# Pull env var helper
function Get-EnvVar([string]$Name) {
  $userVal    = [Environment]::GetEnvironmentVariable($Name, 'User')
  $machineVal = [Environment]::GetEnvironmentVariable($Name, 'Machine')
  if ($UseMachineScope -and $machineVal) { return $machineVal }
  return $userVal
}

$ok = @()
$skipped = @()
$missing = @()
$failed = @()

foreach ($n in $Names) {
  $val = Get-EnvVar $n
  if ([string]::IsNullOrWhiteSpace($val)) {
    Write-Colored 'Warn' "Skip: $n (not set in Windows env)"
    $missing += $n
    continue
  }

  if ($DryRun) {
    Write-Colored 'Info' "Would set secret '$n' on $repoSlug (value length: $($val.Length))"
    $skipped += $n
    continue
  }

  try {
    # Use --body to avoid shell quoting pitfalls. Avoid echoing secrets to console.
    gh secret set $n -R $repoSlug --body $val | Out-Null
    Write-Colored 'Success' "Set secret: $n"
    $ok += $n
  } catch {
    Write-Colored 'Error' "Failed to set $n  -> $($_.Exception.Message)"
    $failed += $n
  }
}

Write-Host ""
Write-Colored 'Header' "Summary"
Write-Colored 'Success' ("Set:     {0}" -f ($(if($ok){$ok -join ', '}else{'(none)'})))
if ($DryRun) { Write-Colored 'Info' ("Dry-run: {0}" -f ($(if($skipped){$skipped -join ', '}else{'(none)'}))) }
if ($missing) { Write-Colored 'Warn' ("Missing: {0}" -f ($missing -join ', ')) }
if ($failed)  { Write-Colored 'Error' ("Failed:  {0}" -f ($failed -join ', ')) }

if (-not $DryRun -and $ok.Count -gt 0) {
  Write-Colored 'Info' "Secrets available in GitHub Actions as env vars with the same names."
}

# Exit code: nonzero if failures occurred
if ($failed.Count -gt 0) { exit 2 }
