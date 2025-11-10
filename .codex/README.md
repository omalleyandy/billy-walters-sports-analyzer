# Codex Command System (SSOT: Agents → JSON)

**Design:** PowerShell Agents are the single source of truth. `commands.json` is generated **from** Agents for TUIs, menus, and API launchers—no drift.

## Quickstart (Windows PowerShell 7+)
```powershell
# 0) Ensure uv is available
uv --version

# 1) Generate commands.json from .codex/commands
pwsh -File .codex/scripts/generate-commands-json.ps1

# 2) Run a command by id from JSON
pwsh -File .codex/scripts/run-json-command.ps1 -Id devtools-espn-discover
pwsh -File .codex/scripts/run-json-command.ps1 -Id espn.pull -Args @{ dates='20251106-20251109'; limit='200' }

# 3) Pester smoke tests
Invoke-Pester .codex/tests/test-command-parity.ps1