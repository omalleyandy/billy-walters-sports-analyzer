# .codex/workflows - Automated Betting Workflows

Collection of PowerShell automation scripts for common betting analysis workflows.

## Available Workflows

### 1. Daily Analysis (`daily-analysis.ps1`)

Complete daily betting workflow for game days (Sunday NFL, Saturday NCAA).

**Usage:**
```powershell
# Sunday NFL workflow
.codex/workflows/daily-analysis.ps1 -Sport nfl -Bankroll 10000

# Saturday NCAA workflow
.codex/workflows/daily-analysis.ps1 -Sport ncaaf -Bankroll 10000

# Auto-detect based on day of week
.codex/workflows/daily-analysis.ps1 -Bankroll 10000
```

**What it does:**
1. **9:00 AM**: Collect data (injuries, odds, teams)
2. **10:00 AM**: Launch interactive mode for analysis
3. **11:30 AM**: Optional sharp money monitoring
4. **Summary**: Display recommendations and next steps

**Perfect for:**
- Sunday mornings (NFL)
- Saturday mornings (NCAA)
- Full game-day preparation

### 2. Quick Analysis (`quick-analysis.ps1`)

Fast single-game analysis when you need immediate results.

**Usage:**
```powershell
# Basic analysis
.codex/workflows/quick-analysis.ps1 `
  -HomeTeam "Chiefs" `
  -AwayTeam "Bills" `
  -Spread -2.5

# With research data
.codex/workflows/quick-analysis.ps1 `
  -HomeTeam "Eagles" `
  -AwayTeam "Cowboys" `
  -Spread -3.0 `
  -Research `
  -Bankroll 10000
```

**Perfect for:**
- Last-minute line checks
- Quick edge validation
- Line shopping decisions

## Integration with .codex/super-run.ps1

These workflows call the master `super-run.ps1` script which provides:
- Logging with Chrome DevTools patterns
- Performance monitoring
- Error handling
- Task measurement
- Success tracking

## Integration with Tasks

Use with `.codex/tools/tasks.json` for VS Code/Cursor integration:

1. Open Command Palette (Ctrl+Shift+P)
2. Select "Tasks: Run Task"
3. Choose workflow:
   - "Run Full Workflow"
   - "Analyze Today's Slate"
   - "Monitor Sharp Money"

## Typical Game Day Schedule

### Sunday (NFL)
```powershell
# 9:00 AM - Collect data
.codex/super-run.ps1 -Task collect-data -Sport nfl

# 10:00 AM - Analyze slate
uv run walters-analyzer interactive --bankroll 10000

# Inside interactive mode:
walters> /analyze Chiefs vs Bills -2.5 --research
walters> /analyze Eagles vs Cowboys -3.0 --research
walters> /report session

# 11:30 AM - Monitor sharp money
uv run walters-analyzer monitor-sharp --sport nfl --duration 60

# 12:00 PM - Review and place bets
```

### Saturday (NCAA)
```powershell
# 11:00 AM - Collect data
.codex/super-run.ps1 -Task collect-data -Sport ncaaf

# 12:00 PM - Analyze top games
.codex/workflows/quick-analysis.ps1 -HomeTeam "Georgia" -AwayTeam "Alabama" -Spread -3.5 -Research

# Monitor key games
uv run walters-analyzer monitor-sharp --sport ncaaf --duration 60
```

## Advanced Usage

### Custom Workflows

Create your own workflow by copying and modifying templates:

```powershell
# Copy template
cp .codex/workflows/quick-analysis.ps1 .codex/workflows/my-workflow.ps1

# Edit and customize
# Add your logic, preferences, filters
```

### Scheduling

Use Windows Task Scheduler for automatic execution:

```powershell
# Create scheduled task for Sunday 9 AM
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 9am
$action = New-ScheduledTaskAction -Execute "pwsh" -Argument "-File C:\path\to\daily-analysis.ps1 -Sport nfl"
Register-ScheduledTask -TaskName "BillyWalters-Sunday" -Trigger $trigger -Action $action
```

## Logging

All workflows log to:
- Console (colored output)
- File: `logs/super-run-TIMESTAMP.log`
- Performance metrics tracked

## Error Handling

Workflows include:
- Try/catch blocks
- Graceful degradation
- Helpful error messages
- Recovery suggestions

## Integration with MCP

Workflows can be triggered from Claude Desktop via MCP server tools.

## Best Practices

1. **Run data collection first** (9:00 AM on game days)
2. **Allow time for analysis** (1-2 hours before first game)
3. **Monitor sharp money** (1 hour before kickoff)
4. **Review recommendations** before placing bets
5. **Track results** for CLV analysis

## Support

For issues:
1. Check logs in `logs/` directory
2. Run test-system: `.codex/super-run.ps1 -Task test-system`
3. Review documentation in `docs/guides/`

