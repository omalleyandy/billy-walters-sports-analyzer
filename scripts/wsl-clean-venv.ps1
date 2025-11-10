param(
  [string]$RepoPath = ".",
  [switch]$Recreate,
  [switch]$VerboseLog
)
$ErrorActionPreference = "Stop"

function Write-Info($msg){ if($VerboseLog){ Write-Host "• $msg" -ForegroundColor Cyan } }

# Resolve repo path & sanity check
$repo = Resolve-Path -LiteralPath $RepoPath
$pyproj = Join-Path $repo "pyproject.toml"
if(-not (Test-Path $pyproj)){
  Write-Error "pyproject.toml not found at $repo. Run from the repo root or pass -RepoPath."
  exit 2
}

# Stop common lock holders
Write-Info "Stopping python/uv processes (if any)…"
"python","python3","uv","pytest" | ForEach-Object {
  Get-Process $_ -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

$venv = Join-Path $repo ".venv"
if(Test-Path $venv){
  # Try WSL-safe removal first
  function To-WslPath([string]$winPath){
    $full = [System.IO.Path]::GetFullPath($winPath)
    $drive = $full.Substring(0,1).ToLower()
    $rest  = $full.Substring(2).Replace("\","/")
    "/mnt/$drive/$rest"
  }

  $wsl = Get-Command wsl -ErrorAction SilentlyContinue
  if($wsl){
    $wrepo = To-WslPath $repo.Path
    Write-Info "WSL removal: rm -rf .venv in $wrepo"
    wsl -d Ubuntu bash -lc "cd '$wrepo' && rm -rf .venv" 2>$null
  }

  # Windows fallback in case anything remains
  if(Test-Path $venv){
    Write-Info "Windows fallback removal of .venv…"
    attrib -r -h -s -Recurse $venv 2>$null
    Remove-Item -Recurse -Force $venv
  }
}

if($Recreate){
  Write-Info "Recreating Windows-native venv with uv sync…"
  Push-Location $repo
  uv sync
  Pop-Location
  Write-Host "✅ .venv removed and recreated (Windows-native)" -ForegroundColor Green
} else {
  Write-Host "✅ .venv removed" -ForegroundColor Green
}
