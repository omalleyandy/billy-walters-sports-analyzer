# PowerShell Command Reference
## Billy Walters Sports Betting System

**Last Updated**: November 18, 2025  
**System Status**: ✓ ALL TESTS PASSED

---

## System Health Check

### Check System Status
```powershell
# Full system health check (recommended to run first)
python check_status.py

# View the status report
Get-Content status_report.txt
```

**What it checks**:
- Python version and environment
- Required dependencies (pydantic, fastmcp, aiohttp)
- Walters Analyzer package imports
- Configuration settings (bankroll, max bet %, Kelly fraction)
- MCP server availability

**Last Run Results**:
```
✓ ALL TESTS PASSED!
- Python 3.13.7
- Virtual Environment: Active (.venv)
- Bankroll: $10,000
- Max Bet: 3.0%
- Fractional Kelly: 0.6 (60%)
```

---

## Core Analysis Commands

### 1. Analyze Current Week Edges
```powershell
# Run full Billy Walters edge analysis for current week
python analyze_edges.py

# Or use the Week 12 specific analyzer
python analyze_week12.py
```

**What it does**:
- Fetches latest odds from Overtime API
- Gets Massey power ratings
- Calculates edge percentages
- Applies S-factors (travel, rest, weather)
- Identifies key numbers (3, 6, 7, 14)
- Recommends bet sizes using Kelly Criterion

**Output location**: `output/` directory with timestamped JSON files

### 2. Scrape Latest Betting Lines
```powershell
# Scrape from multiple sources
python scrape_data.py

# Or scrape specific sources
python vegas_insider_live_scraper.py  # Vegas Insider
python massey_ratings_live_scraper.py # Massey Ratings
```

**What it fetches**:
- Current spreads and totals
- Moneyline odds
- Line movements
- Closing line values

### 3. Run Betting Simulation
```powershell
# Backtest the system with historical data
python simulate_betting.py
```

**What it simulates**:
- Historical bet performance
- Bankroll growth/drawdown
- Kelly Criterion effectiveness
- Risk management compliance

### 4. Monitor Live Lines
```powershell
# Start continuous line monitoring
python start_monitor.py
```

**What it monitors**:
- Real-time line movements
- Edge detection alerts
- Key number crosses
- Steam moves and sharp action

---

## Data Collection Scripts

### NFL Week 12 Specific
```powershell
# Collect all Week 12 odds
python week12_collector.py

# Simple Week 12 analysis
python analyze_simple.py
```

### Check Overtime API
```powershell
# Check for betting edges from Overtime
python check_overtime_edges.py
```

---

## Testing Commands

### Run Test Suite
```powershell
# Run all tests
.\.venv\Scripts\python.exe -m pytest

# Run specific test file
.\.venv\Scripts\python.exe -m pytest tests\test_analyzer.py

# Verbose output
.\.venv\Scripts\python.exe -m pytest -v

# With coverage
.\.venv\Scripts\python.exe -m pytest --cov=walters_analyzer
```

### Quick Tests
```powershell
# Test analyzer directly
python test_analyzer_simple.py

# Test imports
python test_imports.py

# Test web fetch client
python test_web_fetch.py
```

### Batch Test Scripts
```powershell
# Windows batch files for quick testing
.\test_analyzer.bat
.\test_system.bat
.\test_mcp.bat
```

---

## MCP Server Commands

### Test MCP Server
```powershell
# Run MCP diagnostics
python diagnose_mcp.py

# Test MCP server directly
.\test_mcp_server.ps1
```

### Setup MCP Server
```powershell
# Setup MCP integration
.\setup_mcp.ps1
```

---

## Common Workflows

### Daily Morning Routine
```powershell
# 1. Check system health
python check_status.py

# 2. Scrape latest odds
python scrape_data.py

# 3. Analyze for edges
python analyze_edges.py

# 4. Review opportunities
# Output files are in ./output/ directory
```

### Wednesday Early Week Analysis
```powershell
# Check opening lines (best for favorites)
python analyze_week12.py
```

### Saturday Late Week Analysis
```powershell
# Check closing lines (best for underdogs)
python analyze_edges.py
```

### Before Placing Bets
```powershell
# 1. Verify data freshness
python check_status.py

# 2. Check for line movements
python start_monitor.py  # Let run for 10-15 minutes

# 3. Final edge calculation
python analyze_edges.py

# 4. Review risk management
# Check that total exposure ≤15% and single bet ≤3%
```

---

## Output Files and Logs

### View Recent Analysis
```powershell
# List recent output files
Get-ChildItem output\ -File | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# View latest analysis
Get-Content (Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1)

# View with formatting (requires ConvertFrom-Json)
Get-Content (Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1) | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Check Logs
```powershell
# View scraper logs
Get-Content scraper_output.log -Tail 50

# View SignalR test logs
Get-Content signalr_test.log -Tail 50

# View all logs in logs directory
Get-ChildItem logs\ -Recurse -File *.log | ForEach-Object { Get-Content $_.FullName -Tail 10 }
```

---

## Environment Management

### Activate Virtual Environment
```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# If you get execution policy error, run as Administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then retry activation
.\.venv\Scripts\Activate.ps1
```

### Deactivate Virtual Environment
```powershell
deactivate
```

### Install Dependencies
```powershell
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt

# Install dev dependencies
pip install -e .[dev]
```

### Update Dependencies
```powershell
# Update all packages
uv sync --upgrade

# Or with pip
pip install --upgrade -r requirements.txt
```

---

## Configuration Files

### View Current Configuration
```powershell
# Check environment variables
Get-Content .env

# View configuration manager
python -c "from config_manager import ConfigManager; cfg = ConfigManager(); print(f'Bankroll: ${cfg.bankroll}\nMax Bet: {cfg.max_bet_pct}%\nKelly: {cfg.fractional_kelly}')"
```

### Edit Configuration
```powershell
# Edit .env file
notepad .env

# Or use VS Code
code .env
```

---

## Troubleshooting

### Common Issues

#### Issue: "python: command not found"
```powershell
# Check Python installation
python --version

# If not found, add Python to PATH or use full path
C:\Python313\python.exe check_status.py
```

#### Issue: "No module named 'walters_analyzer'"
```powershell
# Make sure you're in the project directory
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Verify package is installed
python -c "import walters_analyzer; print(walters_analyzer.__file__)"
```

#### Issue: "ModuleNotFoundError"
```powershell
# Reinstall dependencies
uv sync

# Or manually install missing package
pip install <package-name>
```

#### Issue: "Permission denied" errors
```powershell
# Run PowerShell as Administrator
Start-Process powershell -Verb RunAs

# Then navigate to project and retry
```

### Clear Cache and Rebuild
```powershell
# Clear Python cache
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse

# Clear pytest cache
Remove-Item -Path .pytest_cache -Recurse -Force

# Clear uv cache
Remove-Item -Path .uv-cache -Recurse -Force

# Reinstall everything fresh
uv sync --reinstall
```

---

## PowerShell Aliases (Optional Setup)

Add these to your PowerShell profile for shortcuts:

### Create Profile (if doesn't exist)
```powershell
# Check if profile exists
Test-Path $PROFILE

# Create profile if needed
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -Type File -Force
}

# Edit profile
notepad $PROFILE
```

### Add Aliases to Profile
```powershell
# Add these lines to your $PROFILE file:

# Billy Walters System Aliases
function bw-status { python C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\check_status.py }
function bw-analyze { python C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\analyze_edges.py }
function bw-scrape { python C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\scrape_data.py }
function bw-simulate { python C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\simulate_betting.py }
function bw-monitor { python C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\start_monitor.py }

# Quick directory jump
function bw { Set-Location C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer }
```

### Reload Profile
```powershell
# After editing profile, reload it
. $PROFILE

# Now you can use shortcuts:
bw           # Jump to project
bw-status    # Run status check
bw-analyze   # Run edge analysis
```

---

## Data Verification

### Validate Schedule
```powershell
# Before any analysis, verify games are correct
python -c "from espn_client import ESPNClient; import asyncio; asyncio.run(ESPNClient().get_nfl_schedule(week=12))"
```

### Check Data Freshness
```powershell
# Check when odds were last updated
Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Format-List Name, LastWriteTime

# If older than 24 hours, re-scrape
if ((Get-Date) - (Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime -gt [TimeSpan]::FromHours(24)) {
    Write-Host "Data is stale - running scraper" -ForegroundColor Yellow
    python scrape_data.py
}
```

---

## Risk Management Checks

### Before Betting
```powershell
# Calculate total exposure
python -c @"
import json
from pathlib import Path

# Load latest analysis
latest = sorted(Path('output').glob('*.json'))[-1]
data = json.loads(latest.read_text())

total_risk = sum(bet['recommended_bet'] for bet in data.get('opportunities', []))
bankroll = 10000  # Update with your actual bankroll

print(f'Total Exposure: ${total_risk:,.2f}')
print(f'Percentage: {(total_risk/bankroll)*100:.1f}%')
print(f'Limit Check: {"[OK]" if total_risk/bankroll <= 0.15 else "[EXCEED]"}')
"@
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Check system health | `python check_status.py` |
| Analyze current week | `python analyze_edges.py` |
| Scrape latest odds | `python scrape_data.py` |
| Run simulation | `python simulate_betting.py` |
| Monitor live lines | `python start_monitor.py` |
| Run all tests | `.\.venv\Scripts\python.exe -m pytest` |
| View status report | `Get-Content status_report.txt` |
| Check recent output | `Get-ChildItem output\ -File \| Sort-Object LastWriteTime -Descending \| Select-Object -First 5` |

---

## Important Notes

### Emoji-Free Output
All Python scripts now use text-based indicators for Windows compatibility:
- `[OK]` = Success
- `[ERROR]` = Error
- `[WARN]` = Warning
- `[INFO]` = Information

### UTF-8 Encoding
If you see encoding errors, set UTF-8:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### PowerShell Version
For best experience, use PowerShell 7+:
```powershell
# Check version
$PSVersionTable.PSVersion

# Download PowerShell 7+
# Visit: https://github.com/PowerShell/PowerShell/releases
```

---

## Getting Help

### In-Script Help
Most scripts support `--help`:
```powershell
python analyze_edges.py --help
python scrape_data.py --help
```

### Documentation
- Quick Start: `Get-Content START_HERE.md`
- Project Instructions: `Get-Content PROJECT_INSTRUCTIONS_V2.md`
- Week 12 Guide: `Get-Content WEEK12_BETTING_CARD.md`

### Check System Components
```powershell
# List all Python files
Get-ChildItem -Filter *.py -Recurse | Where-Object { $_.Directory.Name -notmatch "venv|__pycache__|\.git" } | Select-Object FullName

# Check installed packages
pip list

# Verify uv installation
uv --version
```

---

**System Status**: ✓ Operational  
**Last Status Check**: 2025-11-18 14:53:24  
**Environment**: Windows 11 + Python 3.13.7 + PowerShell
