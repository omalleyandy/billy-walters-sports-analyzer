param(
  [switch]$NoHeadless,
  [int]$WaitMs = 5000,
  [string[]]$Args
)
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = 1
$cli = @()
if ($NoHeadless) { $cli += '--no-headless' }
$cli += @('--wait-ms', "$WaitMs")
if ($Args) { $cli += $Args }
uv run codex-devtools @cli
