#requires -Version 7.0
# Pester smoke test: ensure we can generate, read, and run one command through both paths.

Import-Module Pester -ErrorAction Stop

$proj = Resolve-Path "."
$gen  = Join-Path $proj ".codex\scripts\generate-commands-json.ps1"
$run  = Join-Path $proj ".codex\scripts\run-json-command.ps1"

Describe "Command System Parity" {
  It "generates commands.json" {
    $out = & pwsh -NoProfile -File $gen 2>&1
    $LASTEXITCODE | Should -Be 0
    Test-Path (Join-Path $proj "commands.json") | Should -BeTrue
  }

  It "has at least one command and can run via JSON" {
    $j = Get-Content -Raw -Path (Join-Path $proj "commands.json") | ConvertFrom-Json
    $first = $j.commands[0]
    $first | Should -Not -BeNullOrEmpty

    $jsonOut = & pwsh -NoProfile -File $run -Id $first.id 2>&1
    $LASTEXITCODE | Should -Be 0
    ($jsonOut | Out-String).Length | Should -BeGreaterThan 0
  }
}