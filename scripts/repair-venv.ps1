param(
  [string]$RepoPath = ".",
  [string]$CardFile,           # optional; auto-picks newest in ./cards if omitted
  [switch]$VerboseLog
)
$ErrorActionPreference = "Stop"

function Write-Info($m){ if($VerboseLog){ Write-Host "• $m" -ForegroundColor Cyan } }

# Resolve repo + sanity checks
$repo = Resolve-Path -LiteralPath $RepoPath
$pyproj = Join-Path $repo "pyproject.toml"
if(-not (Test-Path $pyproj)){
  Write-Error "pyproject.toml not found at $repo. Use -RepoPath to point at your repo root."
}

# 1) Run the cleaner (removes .venv via WSL-safe path, then uv sync if -Recreate)
$cleaner = Join-Path $repo "scripts\wsl-clean-venv.ps1"
if(-not (Test-Path $cleaner)){ Write-Error "Cleaner not found: $cleaner"; }
Write-Info "Running wsl-clean-venv.ps1 with -Recreate…"
& $cleaner -RepoPath $repo -Recreate -VerboseLog:$VerboseLog

# 2) Pick a card file if not provided -> newest .json in ./cards
if(-not $CardFile){
  $cardsDir = Join-Path $repo "cards"
  if(-not (Test-Path $cardsDir)){ Write-Error "cards/ directory not found at $cardsDir"; }
  $latest = Get-ChildItem -Path $cardsDir -Filter *.json -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if(-not $latest){ Write-Error "No JSON cards found in $cardsDir"; }
  $CardFile = $latest.FullName
  Write-Info "Auto-selected card: $CardFile"
} else {
  $CardFile = (Resolve-Path -LiteralPath $CardFile).Path
}

# 3) Dry-run to confirm health
Push-Location $repo
try {
  Write-Info "Running dry-run: uv run walters-analyzer wk-card --file `"$CardFile`" --dry-run"
  $p = Start-Process -FilePath uv -ArgumentList @("run","walters-analyzer","wk-card","--file",$CardFile,"--dry-run") -NoNewWindow -PassThru -Wait
  if($p.ExitCode -ne 0){ throw "wk-card dry-run failed (exit $($p.ExitCode))." }
  Write-Host "✅ venv repaired and wk-card dry-run succeeded" -ForegroundColor Green
} finally {
  Pop-Location
}
