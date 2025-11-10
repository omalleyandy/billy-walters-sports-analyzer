# Slash Commands - Complete Guide

**Version**: 1.0  
**Feature**: Interactive REPL with AI Assistance  
**Inspiration**: Chrome DevTools Console + AI Patterns

## Quick Start

### Launch Interactive Mode
```bash
uv run walters-analyzer interactive
```

### Execute Single Command
```bash
uv run walters-analyzer slash "/help"
uv run walters-analyzer slash "/analyze Chiefs vs Bills -2.5"
```

---

## All Commands (12 Total)

| Command | Category | Description |
|---------|----------|-------------|
| `/analyze` | Analysis | Game analysis with AI insights |
| `/research` | Analysis | Multi-topic research |
| `/market` | Monitoring | Market movement monitoring |
| `/agent` | AI | Autonomous agent control |
| `/backtest` | Validation | Strategy backtesting |
| `/report` | Reporting | Generate reports |
| `/help` | Utility | Interactive help system |
| `/history` | Utility | Command history |
| `/clear` | Utility | Clear history |
| `/bankroll` | Management | Bankroll operations |
| `/debug` | DevTools | Debug tools (Chrome DevTools pattern) |
| `/optimize` | DevTools | Optimization suggestions |

---

## Analysis Commands

### /analyze

Analyze a game matchup with full Billy Walters methodology.

**Syntax:**
```
/analyze <home_team> vs <away_team> <spread> [--research]
```

**Examples:**
```
/analyze Chiefs vs Bills -2.5
/analyze Eagles @ Cowboys -3.0 --research
/analyze "Kansas City Chiefs" vs "Buffalo Bills" -2.5
```

**Returns:**
```json
{
  "status": "success",
  "data": {
    "matchup": "Buffalo Bills @ Kansas City Chiefs",
    "spread": "Kansas City Chiefs -2.5",
    "predicted_spread": 0.0,
    "edge": 2.5,
    "confidence": "Elevated Confidence",
    "recommendation": {
      "team": "Kansas City Chiefs",
      "stake_pct": 3.0,
      "stake_amount": 300.0,
      "win_probability": 0.58
    },
    "injury_summary": {
      "home_impact": 0.0,
      "away_impact": 0.0,
      "advantage": 0.0
    },
    "key_numbers": [
      "Projection crosses 3 (moving toward underdog)"
    ]
  },
  "ai_insights": {
    "confidence_explanation": "Elevated confidence: 2.5 pt edge is significant. Historical win rate: 58%",
    "risk_assessment": {
      "edge_risk": "low",
      "injury_risk": "low",
      "recommendation": "Strong bet"
    },
    "optimization_tips": [
      "No optimization opportunities identified"
    ]
  }
}
```

**AI Insights Included:**
- Confidence explanation with historical context
- Risk assessment (edge, injuries, key numbers)
- Optimization suggestions
- Historical win rate data

**Flags:**
- `--research`: Fetch live injury/weather data from research engine

**Use Cases:**
- Quick game evaluation
- Line shopping validation
- Pre-bet confirmation
- Learning Billy Walters methodology

---

### /research

Research teams, injuries, weather, or other topics.

**Syntax:**
```
/research <topic> <subject>
```

**Topics:**
- `injuries` - Team injury reports with point values
- `weather` - Stadium weather conditions
- `team` - Team statistics and info (future)

**Examples:**
```
/research injuries Chiefs
/research injuries "Philadelphia Eagles"
/research weather "Lambeau Field"
/research weather "Soldier Field"
```

**Returns (injuries):**
```json
{
  "status": "success",
  "topic": "injuries",
  "data": {
    "team": "Kansas City Chiefs",
    "injury_count": 5,
    "injuries": [
      {
        "name": "Patrick Mahomes",
        "position": "QB",
        "status": "Questionable",
        "injury": "Ankle",
        "points": -3.5
      }
    ],
    "total_impact": -3.2
  },
  "ai_insights": {
    "severity": "high",
    "recommendations": [
      "QB injury significant - monitor game-time status",
      "Line should move 3-4 points if Mahomes out"
    ]
  }
}
```

**Returns (weather):**
```json
{
  "status": "success",
  "topic": "weather",
  "data": {
    "venue": "Lambeau Field",
    "weather": {
      "temperature_high": 28,
      "temperature_low": 18,
      "wind_speed": 15,
      "conditions": "Snow showers",
      "weather_factor": -0.4
    }
  },
  "ai_insights": {
    "impact": {
      "severity": "significant",
      "note": "Adverse weather favors defense",
      "recommendation": "Consider under on totals"
    }
  }
}
```

**Use Cases:**
- Injury impact assessment
- Weather factor evaluation
- Line movement prediction
- Pre-game research

---

## Monitoring Commands

### /market

Monitor market movements and sharp money.

**Syntax:**
```
/market <action> [game_id] [duration]
```

**Actions:**
- `monitor` - Start monitoring a game
- `alerts` - View active alerts

**Examples:**
```
/market monitor Chiefs-Bills 3600
/market alerts
```

**Returns:**
```json
{
  "status": "info",
  "message": "Market monitoring for Chiefs-Bills",
  "duration": 3600,
  "note": "Use CLI: walters-analyzer monitor-sharp --sport nfl"
}
```

**Use Cases:**
- Sharp money detection
- Line movement tracking
- Steam identification
- Market inefficiency spotting

---

## AI Commands

### /agent

Activate autonomous agent for AI-powered decisions.

**Syntax:**
```
/agent <action> [args]
```

**Actions:**
- `analyze` - Agent analyzes game with reasoning chains
- `portfolio` - Portfolio optimization
- `learn` - Review past decisions for learning

**Examples:**
```
/agent analyze game123
/agent portfolio
/agent learn
```

**Returns:**
```json
{
  "status": "info",
  "message": "Agent action: analyze",
  "note": "Autonomous agent provides 5-step reasoning chains with ML predictions"
}
```

**Use Cases:**
- Autonomous decision making
- Portfolio optimization
- Pattern learning
- Meta-analysis

---

## Validation Commands

### /backtest

Backtest betting strategies on historical data.

**Syntax:**
```
/backtest <strategy> [parameters]
```

**Strategies:**
- `power_ratings` - Power rating-based betting
- `key_numbers` - Key number exploitation
- `injury_based` - Injury-driven analysis

**Examples:**
```
/backtest power_ratings from=2024-09-01 to=2024-11-01
/backtest key_numbers
```

**Returns:**
```json
{
  "status": "info",
  "message": "Backtesting strategy: power_ratings",
  "available_strategies": ["power_ratings", "key_numbers", "injury_based"],
  "note": "See: walters_analyzer.backtest module for implementation"
}
```

**Use Cases:**
- Strategy validation
- Historical performance
- Risk assessment
- Edge verification

---

## Reporting Commands

### /report

Generate analysis reports for sessions or performance.

**Syntax:**
```
/report <type>
```

**Report Types:**
- `session` - Current session statistics
- `performance` - Historical performance (future)
- `bankroll` - Bankroll status and history

**Examples:**
```
/report session
/report bankroll
```

**Returns (session):**
```json
{
  "status": "success",
  "data": {
    "session_stats": {
      "commands_executed": 12,
      "current_bankroll": 10000.0,
      "initial_bankroll": 10000.0
    }
  }
}
```

**Returns (bankroll):**
```json
{
  "status": "success",
  "data": {
    "bankroll": {
      "current": 10000.0,
      "initial": 10000.0,
      "change": 0.0,
      "bets_placed": 5
    }
  }
}
```

**Use Cases:**
- Session tracking
- Performance review
- Bankroll management
- Decision audit trail

---

## Utility Commands

### /help

Get help for slash commands.

**Syntax:**
```
/help [command]
```

**Examples:**
```
/help                # List all commands
/help analyze        # Help for /analyze
/help research       # Help for /research
```

**Returns (all commands):**
```json
{
  "status": "success",
  "data": {
    "available_commands": {
      "/analyze": "/analyze - Analyze a game matchup",
      "/research": "/research - Research teams, injuries, conditions",
      ... (all 12 commands)
    }
  }
}
```

**Returns (specific command):**
```json
{
  "status": "success",
  "data": {
    "command": "/analyze",
    "docstring": "Full documentation for /analyze command..."
  }
}
```

---

### /history

View command history.

**Syntax:**
```
/history [limit]
```

**Examples:**
```
/history        # Last 10 commands
/history 20     # Last 20 commands
```

**Returns:**
```json
{
  "status": "success",
  "data": {
    "history": [
      {
        "command": "/analyze Chiefs vs Bills -2.5",
        "timestamp": "2025-11-10T10:15:00",
        "result": "success"
      }
    ],
    "total_commands": 12
  }
}
```

---

### /clear

Clear command history.

**Syntax:**
```
/clear
```

**Returns:**
```json
{
  "status": "success",
  "message": "Command history cleared"
}
```

---

## Management Commands

### /bankroll

Manage bankroll settings and view history.

**Syntax:**
```
/bankroll [action] [amount]
```

**Actions:**
- (none) - Show current bankroll
- `show` - Show current bankroll
- `set <amount>` - Set new bankroll amount
- `history` - View bet history

**Examples:**
```
/bankroll               # Show current
/bankroll set 15000     # Set to $15,000
/bankroll history       # View bet history
```

**Returns (show):**
```json
{
  "status": "success",
  "data": {
    "current": 10000.0,
    "initial": 10000.0
  }
}
```

**Returns (set):**
```json
{
  "status": "success",
  "message": "Bankroll set to $15,000.00"
}
```

**Returns (history):**
```json
{
  "status": "success",
  "data": {
    "bet_history": [
      {
        "stake_pct": 3.0,
        "odds": -110,
        "result": null
      }
    ]
  }
}
```

---

## DevTools Commands (Chrome DevTools Patterns)

### /debug

Debug analysis issues with AI assistance.

**Syntax:**
```
/debug <target>
```

**Targets:**
- `last` - Debug last command execution
- `performance` - System performance metrics
- `network` - Network/API diagnostics (future)

**Examples:**
```
/debug last
/debug performance
```

**Returns (last):**
```json
{
  "status": "success",
  "data": {
    "last_command": "/analyze Chiefs vs Bills -2.5",
    "timestamp": "2025-11-10T10:15:00",
    "result": "success"
  },
  "ai_insights": {
    "diagnosis": "Command executed successfully",
    "suggestions": [
      "Command executed successfully",
      "No issues detected"
    ]
  }
}
```

**Returns (performance):**
```json
{
  "status": "success",
  "data": {
    "avg_command_time": "N/A",
    "total_commands": 12,
    "note": "Performance monitoring active"
  }
}
```

**AI Insights Pattern:**
Like Chrome DevTools Sources tab debugging:
- Diagnoses failures
- Suggests fixes
- Provides actionable recommendations

---

### /optimize

Get AI-powered optimization suggestions.

**Syntax:**
```
/optimize <target>
```

**Targets:**
- `bankroll` - Bankroll management optimization
- `portfolio` - Portfolio optimization (future)
- `strategy` - Strategy optimization (future)

**Examples:**
```
/optimize bankroll
/optimize portfolio
```

**Returns (bankroll):**
```json
{
  "status": "success",
  "data": {
    "current_settings": {
      "max_bet_pct": 3.0,
      "fractional_kelly": 0.5
    },
    "suggestions": [
      "Consider reducing max bet to 2.5% for more conservative approach",
      "Current Kelly fraction (0.5) is optimal for most scenarios",
      "Track CLV to validate edge estimates"
    ]
  }
}
```

**AI Insights Pattern:**
Like Chrome DevTools Performance Insights:
- Identifies inefficiencies
- Suggests optimizations
- Estimates improvements

---

## Interactive Mode Features

### Session Management

```
walters> /analyze Chiefs vs Bills -2.5
[Analysis results...]

walters> /history
[Shows all commands in session]

walters> /report session
[Session statistics]

walters> /clear
[History cleared]

walters> exit
[Exits interactive mode]
```

### Command History Navigation

- **Arrow Up/Down**: Navigate history (standard terminal behavior)
- **Tab**: Command completion (future enhancement)
- **Ctrl+C**: Interrupt current command
- **Ctrl+D or 'exit'**: Exit interactive mode

### AI Assistance Throughout

Every command provides:
- **Status** - Success, error, info, warning
- **Data** - Command-specific results
- **AI Insights** - Explanations, suggestions, recommendations
- **Suggestions** - Next steps or fixes

---

## Advanced Usage

### Chaining Commands

```
walters> /research injuries Chiefs
[15 injuries found, -3.2 pt impact]

walters> /analyze Chiefs vs Bills -2.5 --research
[Uses fresh injury data from research]

walters> /optimize bankroll
[Get staking suggestions]

walters> /report session
[Review session activity]
```

### Workflow Examples

#### Pre-Game Analysis
```
walters> /research injuries Eagles
walters> /research injuries Cowboys
walters> /analyze Eagles vs Cowboys -3.0 --research
walters> /bankroll
walters> /report session
```

#### Line Shopping
```
walters> /analyze Chiefs vs Bills -2.5
walters> /analyze Chiefs vs Bills -3.0
[Compare results to find best line]
```

#### Portfolio Building
```
walters> /analyze Game1 Team1 vs Team2 -X
walters> /analyze Game2 Team3 vs Team4 -Y
walters> /analyze Game3 Team5 vs Team6 -Z
walters> /report session
[Review all recommendations]
```

---

## Output Formats

### Success Response
```json
{
  "status": "success",
  "command": "analyze",
  "data": {
    /* Command-specific data */
  },
  "ai_insights": {
    /* AI-powered insights */
  }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "suggestion": "How to fix it",
  "debug_info": {
    /* Debugging context */
  }
}
```

### Info Response
```json
{
  "status": "info",
  "message": "Information message",
  "usage": "Command usage pattern",
  "examples": [
    /* Usage examples */
  ]
}
```

---

## Chrome DevTools AI Patterns

### 1. Confidence Explanations
```
"High confidence: 3.2 pt edge exceeds 3-point threshold. Historical win rate: 64%"
```
- Like Chrome DevTools Performance Insights
- Explains WHY (not just WHAT)
- Historical context provided

### 2. Risk Assessment
```json
{
  "edge_risk": "low",
  "injury_risk": "moderate",
  "key_number_risk": "alert",
  "recommendation": "Proceed with caution"
}
```
- Like Chrome DevTools Network timing
- Multiple risk factors evaluated
- Overall recommendation synthesized

### 3. Optimization Suggestions
```json
[
  "Edge too small - wait for better line",
  "Key number detected - time bet carefully",
  "Verify injury statuses before betting"
]
```
- Like Chrome DevTools Performance recommendations
- Actionable suggestions
- Prioritized by impact

### 4. Debug Assistance
```json
{
  "diagnosis": "Command failed due to missing argument",
  "suggestions": [
    "Check command syntax with /help",
    "Verify all required arguments",
    "Use /debug performance to check system"
  ]
}
```
- Like Chrome DevTools Sources debugging
- Identifies root cause
- Provides fix steps
- Links to relevant tools

---

## Best Practices

### 1. Start with /help
```
walters> /help
[Review all available commands]

walters> /help analyze
[Get detailed help for specific command]
```

### 2. Use /research Before /analyze
```
walters> /research injuries Chiefs
[Verify injury data is fresh]

walters> /analyze Chiefs vs Bills -2.5 --research
[Analysis uses verified data]
```

### 3. Track Your Session
```
walters> /history
[Review what you've analyzed]

walters> /report session
[Get session statistics]
```

### 4. Check Bankroll Frequently
```
walters> /bankroll
[Verify current bankroll]

walters> /bankroll history
[Review bet history]
```

### 5. Use AI Insights
```
# Every command returns ai_insights
# Read confidence explanations
# Follow optimization suggestions
# Heed risk assessments
```

---

## Troubleshooting

### Command Not Found
```
walters> /analyse Chiefs vs Bills -2.5

{
  "status": "error",
  "message": "Unknown command: /analyse",
  "suggestion": "Did you mean one of: /analyze, /agent, /backtest?",
  "available_commands": [...]
}
```

**Fix**: Check spelling, use `/help` to see all commands

### Invalid Syntax
```
walters> /analyze Chiefs

{
  "status": "error",
  "message": "Invalid syntax",
  "usage": "/analyze <home_team> vs <away_team> <spread> [--research]",
  "examples": [...]
}
```

**Fix**: Follow usage pattern shown in error

### Research Failed
```
walters> /research injuries UnknownTeam

{
  "status": "error",
  "message": "Research failed: Team not found",
  "suggestion": "Check team name spelling",
  "valid_teams": ["Chiefs", "Bills", ...]
}
```

**Fix**: Use correct team name from valid list

---

## Keyboard Shortcuts

### Standard Terminal
- **Ctrl+C**: Interrupt current command
- **Ctrl+D**: Exit interactive mode
- **Arrow Up/Down**: Navigate command history

### Future Enhancements
- **Tab**: Command completion
- **Ctrl+R**: Reverse search history
- **Ctrl+L**: Clear screen

---

## Integration with Other Features

### With CLI Commands
```bash
# Start interactive, use commands, then switch to CLI
uv run walters-analyzer interactive

walters> /analyze Chiefs vs Bills -2.5
walters> exit

# Continue with CLI
uv run walters-analyzer monitor-sharp --sport nfl
```

### With VS Code Tasks
```
# Run task to start interactive mode
Ctrl+Shift+P → Tasks: Run Task → Start Interactive Mode

# Use slash commands
# Exit when done
```

### With Automation
```powershell
# Workflow can drop into interactive mode
.codex/workflows/daily-analysis.ps1 -Sport nfl

# At stage 2, interactive mode opens
walters> /analyze ...
walters> /research ...
```

---

## Tips & Tricks

### 1. Use Partial Team Names
```
/analyze Chiefs vs Bills -2.5
# Works! No need for full "Kansas City Chiefs"
```

### 2. Check Last Command
```
/debug last
# Quick way to see what just ran
```

### 3. Build Command History
```
# Analyze multiple games
/analyze Game1 ...
/analyze Game2 ...
/analyze Game3 ...

# Review all at once
/history
/report session
```

### 4. Learn from AI Insights
```
# Every analysis includes:
• confidence_explanation - Learn why
• risk_assessment - Understand risks
• optimization_tips - Improve strategy
```

### 5. Fast Bankroll Checks
```
/bankroll
# Instant display, no arguments needed
```

---

## Command Reference Table

| Command | Args | Flags | Output | AI Insights |
|---------|------|-------|--------|-------------|
| `/analyze` | teams, spread | --research | Full analysis | Yes |
| `/research` | topic, subject | - | Research data | Yes |
| `/market` | action, game | - | Market info | No |
| `/agent` | action | - | Agent status | Future |
| `/backtest` | strategy | - | Backtest info | Future |
| `/report` | type | - | Report data | No |
| `/help` | [command] | - | Help text | No |
| `/history` | [limit] | - | Command list | No |
| `/clear` | - | - | Confirmation | No |
| `/bankroll` | [action] [amt] | - | Bankroll data | No |
| `/debug` | target | - | Debug info | Yes |
| `/optimize` | target | - | Optimization | Yes |

---

## Conclusion

The slash commands system provides:

✅ **12 interactive commands** for complete betting workflow  
✅ **AI insights** with every analysis  
✅ **Chrome DevTools patterns** for debugging and optimization  
✅ **REPL interface** for exploratory analysis  
✅ **Session tracking** with history and reports  
✅ **Error handling** with helpful suggestions  
✅ **Performance monitoring** built-in  

**The interactive mode makes Billy Walters methodology accessible and intuitive!**

---

**See Also:**
- **CLI Reference**: `docs/guides/CLI_REFERENCE.md`
- **MCP API**: `docs/MCP_API_REFERENCE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Quick Start**: `docs/guides/QUICKSTART_ANALYZE_GAME.md`
- **Code**: `walters_analyzer/slash_commands.py`

