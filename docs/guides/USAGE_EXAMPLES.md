# Billy Walters Sports Analyzer - Complete Usage Examples

**The definitive guide with real-world workflows and examples**

## Table of Contents
1. [Daily Workflows](#daily-workflows)
2. [Single Game Analysis](#single-game-analysis)
3. [Interactive Mode Examples](#interactive-mode-examples)
4. [Automation Examples](#automation-examples)
5. [Advanced Workflows](#advanced-workflows)
6. [Troubleshooting Examples](#troubleshooting-examples)

---

## Daily Workflows

### Sunday NFL Workflow (Automated)

**9:00 AM - Data Collection:**
```powershell
# Option 1: Automated workflow
.codex/workflows/daily-analysis.ps1 -Sport nfl -Bankroll 10000

# Option 2: Manual collection
.codex/super-run.ps1 -Task collect-data -Sport nfl

# Option 3: Individual commands
uv run walters-analyzer scrape-injuries --sport nfl
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --date $(date +%Y-%m-%d)
uv run walters-analyzer scrape-ai --sport nfl
```

**10:00 AM - Analyze Games:**
```bash
# Interactive mode (recommended)
uv run walters-analyzer interactive --bankroll 10000

# Inside interactive:
walters> /help
walters> /research injuries Chiefs
walters> /research injuries Bills
walters> /analyze Chiefs vs Bills -2.5 --research

walters> /research injuries Eagles
walters> /research injuries Cowboys
walters> /analyze Eagles vs Cowboys -3.0 --research

walters> /report session
walters> /bankroll history
walters> exit
```

**Alternative - Direct CLI:**
```bash
uv run walters-analyzer analyze-game \
  --home "Kansas City Chiefs" \
  --away "Buffalo Bills" \
  --spread -2.5 \
  --research \
  --bankroll 10000 \
  --venue "Arrowhead Stadium"

uv run walters-analyzer analyze-game \
  --home "Philadelphia Eagles" \
  --away "Dallas Cowboys" \
  --spread -3.0 \
  --research \
  --bankroll 10000
```

**11:30 AM - Monitor Sharp Money:**
```bash
uv run walters-analyzer monitor-sharp \
  --sport nfl \
  --duration 60 \
  --test  # First time, test API connection
```

**12:00 PM - Review and Bet:**
```bash
# View all collected odds
uv run walters-analyzer view-odds --today

# Compare lines for specific team
uv run walters-analyzer view-odds --compare "Chiefs"

# Export for offline review
uv run walters-analyzer view-odds --today --export sunday-odds.csv
```

---

### Saturday NCAA Workflow

**11:00 AM - Data Collection:**
```powershell
.codex/workflows/daily-analysis.ps1 -Sport ncaaf -Bankroll 10000
```

**12:00 PM - Top Games Analysis:**
```bash
uv run walters-analyzer interactive

walters> /analyze Georgia vs Alabama -3.5 --research
walters> /analyze Michigan vs Ohio State -6.5 --research
walters> /analyze Texas vs Oklahoma -4.0 --research
walters> /report session
```

**1:00 PM - Monitor & Bet:**
```bash
uv run walters-analyzer monitor-sharp --sport ncaaf --duration 90
```

---

## Single Game Analysis

### Quick Analysis (30 seconds)

```bash
# Minimum required: teams and spread
uv run walters-analyzer analyze-game \
  --home "Chiefs" \
  --away "Bills" \
  --spread -2.5
```

**Output:**
```
Matchup:  Buffalo Bills @ Kansas City Chiefs
Spread:   Kansas City Chiefs -2.5

Edge:             +2.5 pts
Confidence:       Elevated Confidence

RECOMMENDATION: Elevated Confidence
Stake:            3.00% ($300.00)
```

### Full Analysis (2 minutes)

```bash
# With research, weather, custom prices
uv run walters-analyzer analyze-game \
  --home "Kansas City Chiefs" \
  --away "Buffalo Bills" \
  --spread -2.5 \
  --home-price -105 \
  --away-price -115 \
  --venue "Arrowhead Stadium" \
  --date 2025-11-10 \
  --bankroll 10000 \
  --research
```

**Output:**
```
[*] Gathering research data...
[+] Loaded 5 home injuries
[+] Loaded 8 away injuries
[+] Weather: Clear, 45°F, Wind 10mph

HOME TEAM INJURIES:
  Total Impact: -1.2 pts
  • Patrick Mahomes (QB): -0.5 pts (Questionable)
  • Travis Kelce (TE): -0.7 pts (Questionable)

AWAY TEAM INJURIES:
  Total Impact: -2.5 pts
  • Josh Allen (QB): -1.5 pts (Doubtful)
  • Stefon Diggs (WR): -1.0 pts (Out)

ANALYSIS:
  Predicted Spread: -1.3
  Market Spread:    -2.5
  Edge:             +1.2 pts

KEY NUMBER ALERTS:
  [*] Near key number 3

RECOMMENDATION: Slight Edge
Stake: 1.50% ($150.00)
Win Prob: 54.0%
```

### Line Shopping Example

```bash
# Check multiple lines to find best value
uv run walters-analyzer analyze-game --home "Chiefs" --away "Bills" --spread -2.5
# Edge: +2.5

uv run walters-analyzer analyze-game --home "Chiefs" --away "Bills" --spread -3.0
# Edge: +3.0 (better!)

uv run walters-analyzer analyze-game --home "Chiefs" --away "Bills" --spread -2.0
# Edge: +2.0 (worse)

# Conclusion: Best line is -3.0
```

---

## Interactive Mode Examples

### Example Session 1: Single Game Deep Dive

```
$ uv run walters-analyzer interactive --bankroll 10000

walters> /help analyze
[Shows detailed /analyze help]

walters> /research injuries Chiefs
{
  "status": "success",
  "data": {
    "team": "Kansas City Chiefs",
    "injury_count": 5,
    "total_impact": -1.2
  }
}

walters> /research injuries Bills
{
  "status": "success",
  "data": {
    "team": "Buffalo Bills",
    "injury_count": 8,
    "total_impact": -2.5
  }
}

walters> /analyze Chiefs vs Bills -2.5 --research
{
  "status": "success",
  "data": {
    "edge": 1.2,
    "confidence": "Slight Edge",
    "recommendation": {
      "stake_pct": 1.5,
      "stake_amount": 150.0
    }
  },
  "ai_insights": {
    "confidence_explanation": "1.2 pt edge with Bills injury advantage",
    "risk_assessment": {"edge_risk": "moderate"},
    "optimization_tips": ["Monitor Allen's status"]
  }
}

walters> /bankroll
{
  "data": {
    "current": 10000.0,
    "initial": 10000.0
  }
}

walters> /report session
{
  "data": {
    "commands_executed": 6,
    "analyses_run": 1
  }
}

walters> exit
```

### Example Session 2: Full Slate Analysis

```
walters> /analyze Game1 Team1 vs Team2 -3.5 --research
[Result: 2.5 pt edge, stake 3.0%]

walters> /analyze Game2 Team3 vs Team4 -7.0 --research
[Result: 1.0 pt edge, stake 1.0%]

walters> /analyze Game3 Team5 vs Team6 -2.0 --research
[Result: 0.5 pt edge, no play]

walters> /report session
{
  "session_stats": {
    "commands_executed": 4,
    "games_analyzed": 3,
    "plays_recommended": 2,
    "total_stake": 4.0
  }
}

walters> /bankroll
{
  "current": 10000.0,
  "recommended_risk": 4.0,
  "amount_at_risk": 400.0
}
```

### Example Session 3: Research Focus

```
walters> /research injuries Eagles
walters> /research injuries Cowboys  
walters> /research injuries 49ers
walters> /research injuries Seahawks

walters> /research weather "Lambeau Field"
walters> /research weather "Soldier Field"

walters> /history
[Shows all 6 research commands]
```

---

## Automation Examples

### VS Code Task Runner

**Scenario**: Analyze today's slate from VS Code

**Steps:**
1. Open project in VS Code/Cursor
2. Press `Ctrl+Shift+P`
3. Type "Tasks: Run Task"
4. Select "Run Full Workflow"
5. Enter sport: `nfl`
6. Enter bankroll: `10000`
7. Wait for completion

**What Happens:**
- Collects fresh data
- Launches interactive mode
- Prompts for sharp money monitoring
- Generates summary

### Super-Run Orchestrator

**Scenario**: Automated data collection

```powershell
# Collect all data sources
.codex/super-run.ps1 -Task collect-data -Sport nfl -VerboseOutput

# Output:
[INFO] Starting: Scrape Injuries
[SUCCESS] Completed: Scrape Injuries (12.5s)
[INFO] Starting: Highlightly - Matches
[SUCCESS] Completed: Highlightly - Matches (3.2s)
[INFO] Starting: Highlightly - Odds
[SUCCESS] Completed: Highlightly - Odds (2.8s)
[INFO] Data collection complete: 3/3 successful
```

**Scenario**: System health check

```powershell
.codex/super-run.ps1 -Task test-system

# Output:
[SUCCESS] Completed: CLI Help
[SUCCESS] Completed: Slash Command - Help
[SUCCESS] Completed: Slash Command - Bankroll
[SUCCESS] Completed: Analyze Game
[SUCCESS] System test PASSED: All 4/4 tests successful
```

### Daily Workflow Script

**Scenario**: Complete Sunday morning routine

```powershell
.codex/workflows/daily-analysis.ps1 -Sport nfl -Bankroll 10000

# What it does:
# 1. Collects data from all sources
# 2. Opens interactive mode for analysis
# 3. Prompts for sharp money monitoring
# 4. Displays final summary
```

**Scenario**: Quick pre-game check

```powershell
.codex/workflows/quick-analysis.ps1 `
  -HomeTeam "Chiefs" `
  -AwayTeam "Bills" `
  -Spread -2.5 `
  -Research `
  -Bankroll 10000

# Output: Full analysis in <5 seconds
```

---

## Advanced Workflows

### Portfolio Construction

```bash
# Analyze all interesting games
uv run walters-analyzer interactive

walters> /analyze Chiefs vs Bills -2.5 --research
# Edge: 2.5, Stake: 3.0% ($300)

walters> /analyze Eagles vs Cowboys -3.0 --research
# Edge: 3.0, Stake: 3.0% ($300)

walters> /analyze 49ers vs Seahawks -4.0 --research
# Edge: 1.5, Stake: 2.0% ($200)

walters> /optimize portfolio
# AI checks correlation, suggests adjustments
# Recommends 2.5% + 2.5% + 1.5% = 6.5% total risk

walters> /report session
# Review full portfolio
```

### Line Movement Tracking

```bash
# Morning line
uv run walters-analyzer analyze-game --home "Chiefs" --away "Bills" --spread -2.5
# Edge: 2.5

# Midday check
uv run walters-analyzer analyze-game --home "Chiefs" --away "Bills" --spread -3.0
# Edge: 3.0 (line moved, edge improved!)

# Pre-game final check
uv run walters-analyzer analyze-game --home "Chiefs" --away "Bills" --spread -2.0
# Edge: 2.0 (line came back, edge decreased)

# Decision: Bet the -3.0 if still available
```

### Sharp Money Following

```bash
# Monitor for sharp moves
uv run walters-analyzer monitor-sharp --sport nfl --duration 120

# When alert fires:
# "Sharp money detected: Eagles line moved from -3.0 to -3.5"

# Analyze the game
uv run walters-analyzer analyze-game \
  --home "Eagles" \
  --away "Cowboys" \
  --spread -3.5 \
  --research

# If edge confirms sharp move, follow the money
```

### Weather-Dependent Analysis

```bash
# Check weather first
uv run walters-analyzer interactive

walters> /research weather "Lambeau Field"
{
  "weather": {
    "temperature": 15,
    "wind_speed": 25,
    "conditions": "Snow",
    "weather_factor": -0.5
  }
}

walters> /analyze Packers vs Bears -3.0 --research
# Analysis factors in weather
# Suggests: Consider under if weather severe

walters> /research weather "Mile High Stadium"
# Check another outdoor game
```

---

## Bankroll Management Examples

### Conservative Approach

```bash
walters> /bankroll set 10000
walters> /analyze Game1 ... # 3.0 pt edge
# Recommendation: 3.0% ($300)

walters> /optimize bankroll
# Suggestion: "Consider 2.5% max for more conservative"

walters> /bankroll set 10000  # Keep at 3% max
# Stick with standard Kelly

# Analysis automatically uses new settings
```

### Tracking Performance

```bash
walters> /analyze Chiefs vs Bills -2.5
# Stake recommended: 3.0% ($300)
# [Bet placed, Chiefs won]

walters> /bankroll history
{
  "bet_history": [
    {
      "stake_pct": 3.0,
      "odds": -110,
      "result": 1.0  # Win
    }
  ]
}

# New bankroll calculated automatically
walters> /bankroll
{
  "current": 10270.0,  # Up $270
  "initial": 10000.0
}
```

---

## Research-Driven Analysis

### Injury Impact Study

```bash
walters> /research injuries "Philadelphia Eagles"
{
  "injury_count": 15,
  "total_impact": -3.2,
  "critical_injuries": [
    {
      "player": "Jalen Hurts",
      "position": "QB",
      "status": "Questionable",
      "points": -3.5
    }
  ]
}

# AI Insight: "QB injury significant"

walters> /analyze Eagles vs Cowboys -3.0
# Without research flag - uses cached data

walters> /analyze Eagles vs Cowboys -3.0 --research
# With research flag - fetches fresh data

# Compare results to see injury impact
```

### Weather Analysis

```bash
walters> /research weather "Soldier Field"
{
  "weather": {
    "temperature": 25,
    "wind": 20,
    "precipitation": 40,
    "weather_factor": -0.3
  },
  "ai_insights": {
    "impact": "moderate",
    "recommendation": "Consider under on totals"
  }
}

walters> /analyze Bears vs Packers -4.0 --research
# Analysis factors in weather
# Adjusts total prediction downward
```

---

## Troubleshooting Examples

### Unknown Team Name

```bash
walters> /analyze Cheifs vs Bills -2.5  # Typo!

{
  "status": "error",
  "message": "Team not found: 'Cheifs'",
  "suggestion": "Did you mean 'Chiefs'?",
  "valid_teams": ["Kansas City Chiefs", "Chiefs", ...]
}

# Fix:
walters> /analyze Chiefs vs Bills -2.5
```

### Missing Arguments

```bash
walters> /analyze Chiefs vs Bills

{
  "status": "error",
  "message": "Invalid syntax",
  "usage": "/analyze <home_team> vs <away_team> <spread>",
  "examples": [
    "/analyze Chiefs vs Bills -2.5"
  ]
}

# Fix:
walters> /analyze Chiefs vs Bills -2.5
```

### Research Unavailable

```bash
walters> /research injuries UnknownTeam

{
  "status": "error",
  "message": "Research failed: No data found",
  "suggestion": "Check team name or run scraper first",
  "debug": {"topic": "injuries", "team": "UnknownTeam"}
}

# Fix: Scrape fresh data
exit

$ uv run walters-analyzer scrape-injuries --sport nfl
# Then retry research
```

---

## Week Card Examples

### Preview Card

```bash
# Basic preview
uv run walters-analyzer wk-card \
  --file cards/week10.json \
  --dry-run

# Output:
Wk-Card 2025-11-10 | source=manual | dry_run=True
- 101 Eagles vs Cowboys
  spread: Eagles -3.0 (size=2u, max_juice=-110)
```

### Preview with Bankroll

```bash
uv run walters-analyzer wk-card \
  --file cards/week10.json \
  --dry-run \
  --show-bankroll \
  --bankroll 10000

# Output:
Wk-Card 2025-11-10 | Bankroll=$10,000.00
- 101 Eagles vs Cowboys
  spread: Eagles -3.0 (size=2u) → 2.50% ($250.00)
  moneyline: Eagles (price=-150) → 1.20% ($120.00)
```

### Execute Card (Production)

```bash
# Remove --dry-run to actually place bets
uv run walters-analyzer wk-card \
  --file cards/week10.json \
  --show-bankroll \
  --bankroll 10000

# Validates gates:
# ✓ injuries_confirmed
# ✓ weather_confirmed
# ✓ steam_ok

# Places bets if gates pass
```

---

## Scraping Examples

### AI-Assisted Scraping

```bash
# Scrape with full AI monitoring
uv run walters-analyzer scrape-ai --sport nfl

# Output:
================================================================================
AI-ASSISTED ODDS SCRAPING
================================================================================

Features:
  • Performance monitoring with AI insights
  • Network request analysis
  • Automatic debugging recommendations

[Scraping...]

SCRAPING RESULTS:
Games extracted: 15
Performance Score: 87/100
  [OK] Excellent performance

AI Recommendations (2):
  • request_blocking: Faster scraping, lower bandwidth
  • wait_strategy: More reliable element detection

Session Stats:
  Success Rate: 95.0%
  Avg Performance: 87.0/100
```

### Traditional Scraping

```bash
# Scrapy-based scraping
uv run walters-analyzer scrape-overtime --sport nfl

# Highlightly API
uv run walters-analyzer scrape-highlightly \
  --endpoint all \
  --sport nfl \
  --date 2025-11-10

# ESPN injuries
uv run walters-analyzer scrape-injuries --sport nfl
```

---

## Data Viewing Examples

### View Today's Odds

```bash
uv run walters-analyzer view-odds --today

# Output:
📅 Today's games:

[1] Las Vegas Raiders @ Denver Broncos
    Event: 2025-11-10 13:00 ET
    Spread: Raiders +9.0 (-110) | Broncos -9.0 (-110)
    Total: O 43.0 (-110) | U 43.0 (-110)
    ML: Raiders +380 | Broncos -515

[2] ...
```

### Filter by Team

```bash
uv run walters-analyzer view-odds --team "Chiefs" --upcoming 7

# Shows all Chiefs games in next 7 days
```

### Compare Lines

```bash
uv run walters-analyzer view-odds --compare "Eagles"

# Shows all available lines for Eagles games
# Useful for line shopping
```

### Export for Analysis

```bash
uv run walters-analyzer view-odds \
  --today \
  --export sunday-games.csv

# Creates CSV for offline analysis/archiving
```

---

## MCP Server Examples (Claude Desktop)

### In Claude Desktop

**Example 1: Quick Game Analysis**
```
User: "Analyze Chiefs vs Bills with -2.5 spread"

Claude: [Calls MCP tool]
analyze_game(
  home_team="Kansas City Chiefs",
  away_team="Buffalo Bills",
  spread=-2.5,
  include_research=true
)

[Returns full analysis with AI insights]

Claude: "Based on Billy Walters methodology:
• Edge: +2.5 points
• Confidence: Elevated (58% historical win rate)
• Recommended stake: 3.0% ($300 on $10k bankroll)

Key factors:
- Slight injury advantage to Chiefs
- Line crosses key number 3
- Consider timing bet near game time"
```

**Example 2: Portfolio Optimization**
```
User: "I want to bet on 3 games today with $10,000. Optimize my portfolio."

Claude: [Uses portfolio_optimization prompt]

[Analyzes all 3 games]
analyze_game(home="Team1", away="Team2", spread=-3.5)
analyze_game(home="Team3", away="Team4", spread=-7.0)
analyze_game(home="Team5", away="Team6", spread=-2.0)

[Returns optimized portfolio]
"Recommended portfolio:
Game 1: 2.5% ($250) - Reduced from 3% due to correlation
Game 2: 1.5% ($150) - High risk game, reduced stake
Game 3: 2.0% ($200) - Good value, moderate stake

Total risk: 6.0% of bankroll
Expected return: +4.2%
Correlation risk: 12% (within 20% limit)"
```

**Example 3: Sharp Money Detection**
```
User: "Monitor Chiefs-Bills for sharp money for next hour"

Claude:
find_sharp_money(
  game_id="chiefs_bills",
  monitor_duration=3600
)

[After 1 hour]
"Sharp money detected:
• Line moved from -2.5 to -3.0 (0.5 points)
• Public: 65% on Chiefs
• Sharp books: Moved first
• Confidence: 85%

Recommendation: Strong sharp action on Chiefs. Edge increased from +2.5 to +3.0. Suggest betting Chiefs -3.0."
```

---

## Combination Workflows

### Research → Analyze → Monitor

```bash
# Step 1: Research
uv run walters-analyzer interactive

walters> /research injuries Chiefs
walters> /research weather "Arrowhead Stadium"

# Step 2: Analyze
walters> /analyze Chiefs vs Bills -2.5 --research
# Edge: 2.5, Stake: 3.0%

walters> exit

# Step 3: Monitor
uv run walters-analyzer monitor-sharp \
  --sport nfl \
  --game-id "chiefs_bills" \
  --duration 60

# Step 4: Place bet if confirmed
```

### Scrape → View → Analyze

```bash
# Step 1: Scrape fresh data
uv run walters-analyzer scrape-ai --sport nfl

# Step 2: View available games
uv run walters-analyzer view-odds --today

# Step 3: Analyze selected games
uv run walters-analyzer analyze-game \
  --home "Team A" --away "Team B" --spread -X --research
```

### Backtest → Validate → Apply

```bash
# Step 1: Backtest strategy (future)
walters> /backtest power_ratings from=2024-09-01 to=2024-11-01
# Result: 58.5% win rate, 8.7% ROI

# Step 2: Validate with current game
walters> /analyze CurrentGame ... --research
# Check if edge matches backtest patterns

# Step 3: Apply with confidence
# Bet if analysis confirms backtest edge
```

---

## Best Practices Summary

### 1. Data Freshness
```bash
# Always scrape before analyzing
uv run walters-analyzer scrape-injuries --sport nfl  # Morning
uv run walters-analyzer scrape-highlightly ...        # Morning
uv run walters-analyzer analyze-game ... --research   # Uses fresh data
```

### 2. Research First
```bash
walters> /research injuries Team1
walters> /research injuries Team2
walters> /analyze Team1 vs Team2 -X --research
# Research validates cached data before analysis
```

### 3. Verify with Multiple Checks
```bash
# Check 1: Direct analysis
uv run walters-analyzer analyze-game ...

# Check 2: Interactive with research
walters> /research injuries ...
walters> /analyze ...

# Check 3: Compare lines
walters> /analyze ... -2.5
walters> /analyze ... -3.0
# Pick best line
```

### 4. Track Everything
```bash
walters> /history           # Command history
walters> /bankroll history  # Bet history  
walters> /report session    # Session stats
# Keep audit trail for learning
```

### 5. Use AI Insights
```
# Every analysis includes:
• confidence_explanation → Understand WHY
• risk_assessment → Know the risks
• optimization_tips → Improve strategy
# Read and apply these insights!
```

---

## Conclusion

The Billy Walters Sports Analyzer provides multiple interaction modes for every use case:

✅ **Quick Analysis**: Direct CLI for speed  
✅ **Deep Analysis**: Interactive mode for research  
✅ **Automation**: PowerShell workflows for game days  
✅ **VS Code**: One-click tasks for convenience  
✅ **Claude Desktop**: AI-powered assistance via MCP  

**All modes provide:**
- Complete Billy Walters methodology
- AI insights and suggestions
- Bankroll-aware recommendations
- Full transparency

**Choose the mode that fits your workflow!**

---

**See Also:**
- **CLI Reference**: `docs/guides/CLI_REFERENCE.md`
- **Slash Commands**: `docs/guides/SLASH_COMMANDS_GUIDE.md`
- **MCP API**: `docs/MCP_API_REFERENCE.md`
- **Quick Start**: `docs/guides/QUICKSTART_ANALYZE_GAME.md`
- **Architecture**: `docs/ARCHITECTURE.md`

