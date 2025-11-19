# PROJECT MEMORY - Windows PowerShell Edition

**Billy Walters Sports Betting System**

**Last Updated**: November 18, 2025  
**Environment**: Windows 11 + Python 3.13.7 + PowerShell

---

## System Configuration

### Environment

- **OS**: Windows 11
- **Shell**: Windows PowerShell
- **Python**: 3.13.7 (C:\Python313\python.exe)
- **Working Directory**: `C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\`
- **Virtual Environment**: `.venv` (uv-managed)
- **Package Manager**: uv (preferred) or pip
- **Encoding**: UTF-8 (set via `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`)

### Key Settings

- **Bankroll**: $10,000 (configurable)
- **Max Single Bet**: 3% of bankroll
- **Max Weekly Exposure**: 15% of bankroll
- **Minimum Edge**: 5.5%
- **Kelly Fraction**: 0.6 (60% fractional Kelly)

---

## Command Structure (PowerShell Only)

### Your Actual Working Commands

```powershell
# System Health
python check_status.py

# Core Analysis
python analyze_edges.py          # Main edge detection
python analyze_week12.py          # Week-specific analysis
python analyze_simple.py          # Simplified analyzer

# Data Collection
python scrape_data.py             # Multi-source scraper
python check_overtime_edges.py    # Overtime API
python week12_collector.py        # Week collector

# Testing
python test_analyzer_simple.py    # Quick tests
python test_imports.py            # Import validation
.\.venv\Scripts\python.exe -m pytest  # Full test suite

# Monitoring
python start_monitor.py           # Live line monitoring

# Simulation
python simulate_betting.py        # Backtest system
```

### Why Module Execution Doesn't Work

`python -m walters_analyzer` doesn't work because the package lacks `__main__.py`.  
Use direct script execution instead (shown above).

---

## Billy Walters Methodology

### Core Principles

1. **Accuracy Over Speed** - Validate all data before analysis
2. **Mathematical Rigor** - Every bet needs quantified edge ≥5.5%
3. **Risk Management** - Never exceed 3% single / 15% weekly limits
4. **Process Over Results** - Judge methodology, not short-term outcomes
5. **Transparency** - Document everything, admit mistakes

### Power Rating System

- **90/10 Formula**: 90% previous rating + 10% new performance
- **S-factors**: Travel, rest, weather, motivation (5 points = 1 spread point)
- **Injury Impact**: Position-tier multipliers (QB=6-8pts, WR cluster×1.5)
- **Key Numbers**: 3 (+1.5%), 7 (+1.2%), 6 (+1.0%) edge premiums

### Bet Sizing

- **Kelly Criterion**: Fractional Kelly at 60%
- **Star System**: 0.5-3.0 stars based on edge percentage
- **Absolute Limits**: 3% max single bet, 15% max weekly
- **Stop Loss**: 10% weekly drawdown triggers halt

---

## Recent Updates (November 18, 2025)

### Windows PowerShell Migration

- ✅ All bash commands removed from documentation
- ✅ PowerShell syntax standardized across all guides
- ✅ Command structure clarified (direct script execution)
- ✅ Environment variables and paths updated for Windows

### Emoji Compatibility Fix

- ✅ 52 Python files updated (emojis → text symbols)
- ✅ 6 BOM syntax errors fixed (removed `[*]` prefixes)
- ✅ `scripts/remove_emojis.py` improved for future use
- ✅ All scripts tested and validated

### Text Symbol Replacements

```
✓  → [OK]       ❌ → [ERROR]     ⚠️ → [WARNING]
📊 → [CHART]    💰 → [MONEY]     🎯 → [TARGET]
⭐ → [STAR]     🏈 → [NFL]       📝 → [NOTE]
```

---

## Current Project State

### System Health (Last Check: 2025-11-18 19:31:50)

```
[OK] Python 3.13.7
[OK] pydantic 2.12.3
[OK] aiohttp 3.12.15
[OK] walters_analyzer package functional
[OK] Configuration valid ($10K bankroll, 3% max)
[WARNING] fastmcp not installed (optional - MCP server only)
```

### Performance Tracking

- **Sample Size**: Building toward 100+ bets for statistical validity
- **Focus Metric**: Closing Line Value (CLV) over win rate
- **Current Week**: NFL Week 12, NCAAF Week 12
- **Backtest Results**: 14-2-0 record (87.5% win rate, +$9,284 profit in validation)

### Data Sources

- **Overtime API**: Live odds, spreads, totals
- **Massey Ratings**: Power ratings for edge calculation
- **Vegas Insider**: Line movements, closing lines
- **ESPN**: Schedules, scores, statistics
- **AccuWeather**: Game-day weather conditions
- **@ProFootballDoc**: Injury reports and analysis

---

## File Structure

### Core Package (`src\walters_analyzer\`)

```
walters_analyzer\
├── analysis\      # Analysis engines
├── config\        # Configuration management
├── core\          # Core functionality (analyzer, models)
├── scrapers\      # Web scrapers
├── valuation\     # Valuation models
├── monitoring\    # Live monitoring
└── feeds\         # Data feeds
```

### Root Scripts (Direct Execution)

- `check_status.py` - System health diagnostics
- `analyze_edges.py` - Core edge detection
- `analyze_week12.py` - Week-specific analyzer
- `scrape_data.py` - Multi-source data collection
- `simulate_betting.py` - Backtest engine
- `start_monitor.py` - Live line monitoring

### Utility Scripts (`scripts\`)

- `remove_emojis.py` - Windows emoji compatibility tool

---

## Development Patterns

### Code Standards

- **Type Hints**: All functions have type annotations
- **Docstrings**: Google-style with Args, Returns, Examples
- **Testing**: pytest with >80% coverage target
- **Error Handling**: Retry logic, comprehensive logging
- **Data Format**: Parquet for efficiency, JSON for shareability

### PowerShell Workflow

```powershell
# Navigate to project
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Activate venv (optional)
.\.venv\Scripts\Activate.ps1

# Run analysis
python analyze_edges.py

# View results
Get-Content (Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
```

---

## Key Learnings

### Methodology Audit Findings

**Current Alignment**: 6/10 → Working toward 9/10  
**Gaps Identified**:

- Dynamic power rating updates (90/10 formula)
- Complete S-factors implementation
- Automated injury impact calculations
- Comprehensive key numbers analysis

**Completed Improvements (November 18, 2025)**:

- ✅ Bet sizing: 5% → 3% maximum
- ✅ Edge calculator with S-factors
- ✅ Risk management framework
- ✅ Injury impact system
- ✅ Key numbers methodology

### Critical Lessons

1. **Schedule Validation**: Always verify games exist (caught bye week errors)
2. **Data Accuracy**: Inaccurate data makes all analysis worthless
3. **Sample Size**: Need 100+ bets before drawing conclusions
4. **CLV Tracking**: Primary indicator of long-term edge
5. **Process Adherence**: Stick to methodology during losing streaks

---

## Risk Management Rules

### Absolute Limits (Non-Negotiable)

- ✅ Single bet ≤3% of bankroll
- ✅ Weekly exposure ≤15% of bankroll
- ✅ Minimum edge ≥5.5%
- ✅ Stop-loss at 10% weekly drawdown

### Edge Calculation

```
Base Edge = |Our Line - Market Line|
S-Factors = (Travel + Rest + Weather + Motivation) / 5
Key Numbers = Premium if crossing 3, 7, or 6
Total Edge = Base Edge + S-Factors + Key Numbers
```

### Bet Timing

- **Favorites**: Bet early (Wednesday-Thursday)
- **Underdogs**: Bet late (Saturday)
- **Key Numbers**: Never buy through 3 or 7

---

## Common Workflows (PowerShell)

### Daily Morning Routine

```powershell
# Navigate to project
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Check system health
python check_status.py

# Scrape latest data
python scrape_data.py

# Analyze for edges
python analyze_edges.py

# View results
Get-Content (Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
```

### Wednesday Early Week

```powershell
# Best for favorites - early lines
python analyze_week12.py
```

### Saturday Late Week

```powershell
# Best for underdogs - closing lines
python analyze_edges.py
```

### Before Placing Bets

```powershell
# Verify system
python check_status.py

# Final calculation
python analyze_edges.py

# Review risk: ≤3% single, ≤15% weekly
```

### View Recent Output

```powershell
# List recent files
Get-ChildItem output\ -File | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# View latest JSON
Get-Content (Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1)

# View with formatting
Get-Content (Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1) | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Check Logs

```powershell
# View scraper logs
Get-Content scraper_output.log -Tail 50

# View all logs
Get-ChildItem logs\ -Recurse -File *.log | ForEach-Object { Get-Content $_.FullName -Tail 10 }
```

---

## Documentation Reference

### Primary Guides

1. **PROJECT_INSTRUCTIONS_V2.md** - Complete methodology (PowerShell)
2. **POWERSHELL_COMMANDS.md** - All working commands
3. **START_HERE_NOW.md** - Immediate actions
4. **COMPLETE_SYSTEM_GUIDE.md** - Comprehensive reference

### Status Reports

5. **SYSTEM_STATUS_2025-11-18.md** - System health
6. **EMOJI_FIX_SUMMARY.md** - Emoji removal details
7. **WINDOWS_MIGRATION_COMPLETE.md** - Migration summary

### Week-Specific

8. **WEEK12_BETTING_CARD.md** - Current week analysis
9. **NFL_WEEK12_SFACTOR_SUMMARY.md** - S-factors
10. **WEEK12_TIMING_CHEATSHEET.md** - Bet timing

---

## User Patterns & Preferences

### Working Style

- Rigorous error correction (catches mistakes, expects fixes)
- Strategic direction with technical oversight
- Values accuracy over speed
- Emphasizes validation and verification
- Mathematical mindset (wants calculations, not opinions)
- Long-term thinking (building 100-bet sample)

### Development Preferences

- **Package Manager**: uv (not pip)
- **Testing**: pytest with comprehensive fixtures
- **Documentation**: Real examples, not just theory
- **Type Hints**: Required on all functions
- **Error Handling**: Retry logic, graceful degradation
- **Shell**: Windows PowerShell (no bash commands)

### Success Metrics

1. **CLV** (Closing Line Value) - Primary indicator
2. **Sample Size** - Need 100+ bets
3. **Process Adherence** - Did we follow methodology?
4. **Methodology Alignment** - 6/10 → 9/10 goal
5. **Risk Compliance** - Zero violations

---

## Integration Points

### Claude Desktop MCP

- **Server File**: `.claude\walters_mcp_server.py`
- **Status**: Ready (20KB)
- **Dependency**: fastmcp (optional, not critical)

### Claude Code Integration

- **Slash Commands**: Defined in `commands.json`
- **Session Tracking**: `CLAUDE.md` for context
- **Automated Analysis**: Via CLI commands

---

## Critical Reminders

### Before Any Analysis

1. ✅ Run `python check_status.py`
2. ✅ Verify schedule (no bye weeks)
3. ✅ Check data freshness (<24 hours)
4. ✅ Validate power ratings currency

### During Analysis

1. ✅ Show all calculations step-by-step
2. ✅ Cite Billy Walters methodology
3. ✅ Provide risk percentages
4. ✅ Flag uncertainties explicitly

### After Analysis

1. ✅ Risk check: 3% single, 15% weekly
2. ✅ Edge check: All bets ≥5.5%
3. ✅ Key numbers: Justified premiums
4. ✅ Documentation: Timestamped records

---

## Response Patterns

### When Analyzing Games

- Start with schedule validation
- Show edge calculations transparently
- Provide specific percentages
- Recommend bet sizes (stars + dollars)
- Flag uncertainties
- Use direct, honest tone

### When User Reports Errors

1. Acknowledge immediately
2. Explain cause and impact
3. Fix and verify
4. Prevent recurrence
5. Document for future

### When Performance Questions

1. Emphasize sample size first
2. Focus on CLV over win rate
3. Review process adherence
4. Explain variance vs edge
5. Maintain discipline messaging

---

## PowerShell-Specific Tips

### Virtual Environment

```powershell
# Activate
.\.venv\Scripts\Activate.ps1

# If execution policy error
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Deactivate
deactivate
```

### Package Management

```powershell
# Using uv (recommended)
uv sync
uv pip install <package>
uv sync --upgrade

# Using pip
pip install -r requirements.txt
pip install <package>
```

### File Operations

```powershell
# List files by date
Get-ChildItem | Sort-Object LastWriteTime -Descending

# Find files
Get-ChildItem -Recurse -Filter "*.py"

# View file content
Get-Content filename.txt

# Tail logs
Get-Content logfile.log -Tail 50 -Wait
```

### Testing

```powershell
# Run all tests
.\.venv\Scripts\python.exe -m pytest

# Run with verbose
.\.venv\Scripts\python.exe -m pytest -v

# Run specific test
.\.venv\Scripts\python.exe -m pytest tests\test_analyzer.py

# With coverage
.\.venv\Scripts\python.exe -m pytest --cov=walters_analyzer
```

---

## Troubleshooting (PowerShell)

### Python Not Found

```powershell
# Use full path
C:\Python313\python.exe check_status.py

# Or add to PATH
```

### Module Not Found

```powershell
# Verify in project directory
Get-Location

# Activate venv
.\.venv\Scripts\Activate.ps1

# Reinstall
uv sync
```

### Encoding Issues

```powershell
# Set UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### Permission Errors

```powershell
# Run as Administrator
Start-Process powershell -Verb RunAs
```

---

## Data Verification (PowerShell)

### Check Data Freshness

```powershell
# Check last modified time
Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Format-List Name, LastWriteTime

# If older than 24 hours, re-scrape
if ((Get-Date) - (Get-ChildItem output\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime -gt [TimeSpan]::FromHours(24)) {
    Write-Host "Data is stale - running scraper" -ForegroundColor Yellow
    python scrape_data.py
}
```

### Validate Schedule

```powershell
# Before analysis, verify games
python -c "from espn_client import ESPNClient; import asyncio; asyncio.run(ESPNClient().get_nfl_schedule(week=12))"
```

---

## Environment Variables

### Required Variables (.env file)

```
# API Keys
ACCUWEATHER_API_KEY=your_key_here
HIGHLIGHTLY_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Optional
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1234567890
SMS_ALERT_NUMBERS=+1234567890,+0987654321
SMS_ALERTS_ENABLED=true
```

### View Current Config

```powershell
# Check environment variables
Get-Content .env

# View configuration
python -c "from config_manager import ConfigManager; cfg = ConfigManager(); print(f'Bankroll: ${cfg.bankroll}\nMax Bet: {cfg.max_bet_pct}%\nKelly: {cfg.fractional_kelly}')"
```

### Edit Configuration

```powershell
# Edit .env
notepad .env

# Or use VS Code
code .env
```

---

## Output Structure

### Directory Layout

```
output\
├── overtime\
│   └── nfl\
│       └── pregame\
│           └── [timestamped].json
├── unified\
│   └── [timestamped].json
└── espn\
    └── [timestamped].json
```

### JSON Format

```json
{
  "timestamp": "2025-11-18T19:30:00",
  "sport": "nfl",
  "week": 12,
  "opportunities": [
    {
      "game": "Team A @ Team B",
      "edge": 8.5,
      "confidence": "HIGH",
      "recommended_bet": 600,
      "risk_percentage": 3.0
    }
  ]
}
```

---

## Testing Reference (PowerShell)

### Quick Tests

```powershell
# Test imports
python test_imports.py

# Test analyzer
python test_analyzer_simple.py

# Test web fetch
python test_web_fetch.py
```

### Full Test Suite

```powershell
# All tests
.\.venv\Scripts\python.exe -m pytest

# Verbose
.\.venv\Scripts\python.exe -m pytest -v

# Specific file
.\.venv\Scripts\python.exe -m pytest tests\test_analyzer.py

# With coverage
.\.venv\Scripts\python.exe -m pytest --cov=walters_analyzer --cov-report=html
```

### Syntax Validation

```powershell
# Check any Python file
python -c "import ast; ast.parse(open('filename.py').read()); print('[OK] Valid syntax')"

# Check multiple files
Get-ChildItem -Filter *.py | ForEach-Object {
    python -c "import ast; ast.parse(open('$($_.Name)').read()); print('[OK] $($_.Name)')"
}
```

---

## Maintenance Tasks (PowerShell)

### Clear Cache

```powershell
# Clear Python cache
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse

# Clear pytest cache
Remove-Item -Path .pytest_cache -Recurse -Force

# Clear uv cache
Remove-Item -Path .uv-cache -Recurse -Force
```

### Backup Data

```powershell
# Create backup directory
$backupDir = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir

# Copy important files
Copy-Item -Path output\* -Destination $backupDir\output\ -Recurse
Copy-Item -Path .env -Destination $backupDir\
Copy-Item -Path *.md -Destination $backupDir\
```

### Update Dependencies

```powershell
# Using uv
uv sync --upgrade

# Using pip
pip install --upgrade -r requirements.txt

# Check for outdated packages
pip list --outdated
```

---

## Quick Reference Card

| Task          | Command                                                                                          |
| ------------- | ------------------------------------------------------------------------------------------------ |
| Check health  | `python check_status.py`                                                                         |
| Analyze edges | `python analyze_edges.py`                                                                        |
| Scrape data   | `python scrape_data.py`                                                                          |
| Run tests     | `.\.venv\Scripts\python.exe -m pytest`                                                           |
| View status   | `Get-Content status_report.txt`                                                                  |
| Recent output | `Get-ChildItem output\ -File \| Sort-Object LastWriteTime -Descending \| Select-Object -First 5` |
| Activate venv | `.\.venv\Scripts\Activate.ps1`                                                                   |
| View logs     | `Get-Content scraper_output.log -Tail 50`                                                        |

---

## Migration Notes

### What Changed (November 18, 2025)

- ✅ All bash/Linux commands removed
- ✅ PowerShell syntax throughout documentation
- ✅ Windows path separators (\\ instead of /)
- ✅ PowerShell-specific examples and workflows
- ✅ Emoji compatibility fixed for Windows terminals
- ✅ Virtual environment activation updated for PowerShell

### No Longer Valid

- ❌ `python -m walters_analyzer` (use direct scripts)
- ❌ Bash command chaining with `&&` (use `;` in PowerShell)
- ❌ Linux path separators `/` (use `\`)
- ❌ Emoji symbols in Python code (now text-based)

### Recommended Going Forward

- ✅ Use PowerShell for all command-line operations
- ✅ Use uv for package management
- ✅ Use direct script execution pattern
- ✅ Follow Windows path conventions
- ✅ Use text symbols instead of emojis in code

---

**Last Updated**: November 18, 2025  
**Environment**: Windows 11 + Python 3.13.7 + PowerShell  
**Status**: ✅ Fully Operational and Windows-Native
