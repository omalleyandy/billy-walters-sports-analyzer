# Template Agent
# Purpose: One place to copy for new Agents. Produces transcripts under ./.runs.
# Usage:
#   pwsh -File .codex/commands/_template.ps1 -Example "demo"
# Notes:
#   - Keep params simple types so they reflect cleanly into commands.json via generator.

param(
  [string] $Example = "demo"
)

$ErrorActionPreference = "Stop"

# 1) Prepare transcripts
$runDir = ".\.runs"
if (-not (Test-Path $runDir)) { New-Item -ItemType Directory -Force -Path $runDir | Out-Null }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$transcript = Join-Path $runDir "$($MyInvocation.MyCommand.Name)-$stamp.log"
Start-Transcript -Path $transcript -ErrorAction SilentlyContinue | Out-Null

try {
  Write-Host "[info] Starting $($MyInvocation.MyCommand.Name) Example=$Example"

  # 2) Env validation (customize as needed)
  $uv = Get-Command uv -ErrorAction SilentlyContinue
  if (-not $uv) { throw "uv not found on PATH. Install uv or open the repo dev shell." }

  # 3) Business logic (replace with real work)
  Write-Host "[ok] Hello, Agent. Example=$Example"

  # Example uv run pattern:
  # uv run python -c "print('hello from uv')"

  Write-Host "[ok] Completed successfully."
  exit 0
}
catch {
  Write-Error "[error] $($_.Exception.Message)"
  exit 1
}
finally {
  Stop-Transcript | Out-Null
}