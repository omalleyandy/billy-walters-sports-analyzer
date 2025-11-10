# Video Tutorial Scripts - Billy Walters Sports Analyzer

**Production-ready scripts for video tutorials and demos**

## Tutorial 1: "Quick Start - Analyze Your First Game" (3 minutes)

### Script

**[0:00-0:15] Intro**
```
Hi! Today I'll show you how to analyze an NFL game using the Billy Walters Sports Analyzer - 
the most advanced AI-powered betting analysis system.

In just 30 seconds, you'll get:
• Professional injury impact analysis
• Kelly Criterion bet sizing
• AI-powered insights
```

**[0:15-0:45] Setup**
```
[SCREEN: Terminal]

First, make sure you have the analyzer installed:
$ uv sync

That's it! Now let's analyze a game.
```

**[0:45-1:45] Basic Analysis**
```
[TYPE COMMAND SLOWLY]
$ uv run walters-analyzer analyze-game \
  --home "Kansas City Chiefs" \
  --away "Buffalo Bills" \
  --spread -2.5

[WAIT FOR OUTPUT]

Look at this output! We get:
• Predicted spread: 0.0 points
• Market spread: -2.5 points  
• Our edge: +2.5 points
• Confidence: "Elevated Confidence"
• Stake recommendation: 3.0% of bankroll ($300 on $10k)
• Win probability: 58%

[HIGHLIGHT KEY PARTS ON SCREEN]

This means we have a 2.5-point edge, and the system recommends 
betting 3% of our bankroll - that's $300 on a $10,000 bankroll.
```

**[1:45-2:30] With Research**
```
Now let's add research data - injuries and weather:

[TYPE]
$ uv run walters-analyzer analyze-game \
  --home "Kansas City Chiefs" \
  --away "Buffalo Bills" \
  --spread -2.5 \
  --research \
  --bankroll 10000

[WAIT FOR OUTPUT]

Now we see:
• 5 home team injuries (-1.2 point impact)
• 8 away team injuries (-2.5 point impact)
• Injury advantage calculation
• Key number alerts

[POINT TO KEY NUMBER ALERT]
The system detected we're near the key number 3 - 
that's extra valuable in NFL betting!
```

**[2:30-3:00] Wrap-up**
```
That's it! In 30 seconds you got:
✓ Complete Billy Walters analysis
✓ Injury impact with point values
✓ Kelly Criterion bet sizing
✓ AI-powered insights

To learn more, check out the full documentation.
Links in the description. Happy betting!
```

---

## Tutorial 2: "Interactive Mode - Power User Workflow" (5 minutes)

### Script

**[0:00-0:20] Intro**
```
Welcome back! Today I'll show you the Interactive Mode - 
the most powerful way to use the Billy Walters Sports Analyzer.

With 12 slash commands and AI assistance, you can:
• Analyze multiple games
• Research injuries and weather
• Track your bankroll
• Debug issues
All in one session!
```

**[0:20-1:00] Launch Interactive Mode**
```
[SCREEN: Terminal]
$ uv run walters-analyzer interactive

[WAIT FOR PROMPT]

================================================================================
BILLY WALTERS INTERACTIVE MODE
================================================================================

Type slash commands to interact with the analyzer.
Try: /help for available commands

walters> 

[TYPE]
walters> /help

[SHOW OUTPUT]
Look at all these commands! 12 total.
Let's use the most popular ones.
```

**[1:00-2:00] Research Commands**
```
[TYPE]
walters> /research injuries Chiefs

[SHOW OUTPUT]
{
  "team": "Kansas City Chiefs",
  "injury_count": 5,
  "total_impact": -1.2,
  "critical_injuries": [...]
}

Great! Now let's check the opponent:

walters> /research injuries Bills

We found 8 injuries with -2.5 point impact.
Bills are more banged up - advantage Chiefs!
```

**[2:00-3:30] Analysis with AI Insights**
```
walters> /analyze Chiefs vs Bills -2.5 --research

[SHOW FULL OUTPUT]

Check out the AI insights section:
• Confidence explanation: "2.5 pt edge significant, 58% historical win rate"
• Risk assessment: All metrics look good
• Optimization tips: No red flags

This transparency is what makes the system special.
You understand WHY you're betting, not just WHAT to bet.
```

**[3:30-4:15] Bankroll Management**
```
walters> /bankroll

Current: $10,000
Initial: $10,000

[SIMULATE BET]
walters> /analyze Eagles vs Cowboys -3.0

Recommended stake: 3.0% ($300)

walters> /bankroll set 10300
[Simulate winning the previous bet]

walters> /bankroll history
[Shows bet history]

The system tracks everything for performance analysis.
```

**[4:15-5:00] Advanced Features**
```
walters> /debug last
[Shows debugging info for last command]

walters> /optimize bankroll
[AI suggestions for bankroll management]

walters> /history
[Shows all commands this session]

walters> /report session
[Session statistics]

walters> exit

[RETURN TO SHELL]

That's interactive mode! Perfect for analyzing multiple games
with full research and AI assistance. See you next time!
```

---

## Tutorial 3: "Automated Sunday Workflow" (7 minutes)

### Script

**[0:00-0:30] Intro**
```
It's Sunday morning. Game day! Let me show you how to automate
your entire betting workflow with one command.

We'll go from zero to fully analyzed slate in 10 minutes.
All automated. AI-powered. Billy Walters methodology.
```

**[0:30-1:30] The Workflow**
```
[SCREEN: Show workflow diagram]

Our Sunday workflow has 3 stages:
1. 9:00 AM - Data Collection (injuries, odds, weather)
2. 10:00 AM - Interactive Analysis (game by game)
3. 11:30 AM - Sharp Money Monitoring (line movements)

Let's run it!

[TERMINAL]
$ .codex/workflows/daily-analysis.ps1 -Sport nfl -Bankroll 10000
```

**[1:30-3:00] Stage 1: Data Collection**
```
[SHOW COLLECTION OUTPUT]

[9:00 AM] STAGE 1: DATA COLLECTION
Collecting fresh data...

[INFO] Starting: Scrape Injuries
[SUCCESS] Completed: Scrape Injuries (12.5s)
[INFO] Starting: Highlightly - Matches  
[SUCCESS] Completed: Highlightly - Matches (3.2s)
[INFO] Starting: Highlightly - Odds
[SUCCESS] Completed: Highlightly - Odds (2.8s)

[+] Stage 1 complete. Data collected.

Perfect! We now have fresh injuries and odds for all games.
```

**[3:00-5:00] Stage 2: Interactive Analysis**
```
[SHOW INTERACTIVE MODE LAUNCH]

[10:00 AM] STAGE 2: SLATE ANALYSIS
Opening interactive mode...

walters> /help
[Show available commands]

Let's analyze today's games:

walters> /analyze Chiefs vs Bills -2.5 --research
[SHOW FULL OUTPUT - Edge: 2.5, Stake: 3.0%]

walters> /analyze Eagles vs Cowboys -3.0 --research
[SHOW FULL OUTPUT - Edge: 3.0, Stake: 3.0%]

walters> /analyze 49ers vs Seahawks -4.0 --research
[SHOW FULL OUTPUT - Edge: 1.0, No play]

walters> /report session
{
  "commands_executed": 4,
  "plays_recommended": 2,
  "total_stake": 6.0%
}

Perfect! We have 2 plays totaling 6% of bankroll.
```

**[5:00-6:30] Stage 3: Sharp Money Monitoring**
```
walters> exit

[WORKFLOW CONTINUES]

[11:30 AM] STAGE 3: SHARP MONEY MONITORING
Monitor sharp money for 60 minutes? (Y/N): Y

[SHOW MONITORING]

================================================================================
BILLY WALTERS SHARP MONEY MONITOR
================================================================================

Sport:    NFL
Duration: 60 minutes

Monitoring...

[SHOW ALERTS]
⚠️ ALERT: Chiefs line moved -2.5 → -3.0 (sharp action)
⚠️ ALERT: Eagles line stable (public vs sharp balance)

[AFTER 60 MIN]

📊 MONITORING SUMMARY
Total Alerts: 2
• Chiefs: Sharp action confirmed
• Eagles: Line stable, good entry

```

**[6:30-7:00] Wrap-up**
```
[SHOW FINAL SUMMARY]

================================================================================
DAILY WORKFLOW COMPLETE
================================================================================

Next steps:
  1. Review analysis recommendations
  2. Place bets within Kelly limits (Chiefs 3%, Eagles 3%)
  3. Track results for CLV

[FADE OUT]

That's it! One command automated your entire Sunday morning routine.
Scraping, research, analysis, monitoring - all done.

Now you just place the bets and track results.

See you next week!
```

---

## Tutorial 4: "MCP Server + Claude Desktop" (10 minutes)

### Script

**[0:00-0:45] Intro + Setup**
```
Today I'll show you the ultimate power-user feature:
Using Billy Walters Sports Analyzer directly from Claude Desktop.

With the MCP server, you can ask Claude to:
• Analyze games
• Find sharp money
• Calculate Kelly stakes
• Run backtests
All with natural language!

[SHOW SETUP]
1. Install dependencies: uv sync --extra mcp
2. Copy .claude/claude-desktop-config.json to Claude config folder
3. Start MCP server: uv run python .claude/walters_mcp_server.py
4. Restart Claude Desktop
```

**[0:45-2:00] Tool 1: analyze_game**
```
[SCREEN: Claude Desktop]

Me: "Analyze Chiefs vs Bills with -2.5 spread"

[SHOW CLAUDE THINKING]

Claude: "I'll analyze this game using the Billy Walters methodology..."

[CALLS MCP TOOL]
analyze_game(
  home_team="Kansas City Chiefs",
  away_team="Buffalo Bills",
  spread=-2.5,
  include_research=true
)

[SHOW RESULT]

Claude: "Based on the analysis:

• Edge: +2.5 points (Elevated Confidence)
• Injury impact: Chiefs -1.2, Bills -2.5 (advantage Chiefs)
• Key number alert: Crosses 3
• Win probability: 58%
• Recommended stake: 3.0% ($300)

The 2.5-point edge combined with injury advantage makes this
a strong play. Historical win rate at this confidence: 58%.
I recommend betting Chiefs -2.5 at 3% of bankroll."

[HIGHLIGHT THE REASONING]
See how Claude explains everything in plain English?
That's the power of MCP integration!
```

**[2:00-4:00] Tool 2: find_sharp_money**
```
Me: "Monitor this game for sharp money for the next hour"

Claude: [Calls find_sharp_money]

find_sharp_money(
  game_id="chiefs_bills",
  monitor_duration=3600
)

[AFTER MONITORING]

Claude: "Sharp money detected!

• Line moved from -2.5 to -3.0
• Public: 65% on Chiefs
• Sharp books moved first
• Confidence: 85%

This confirms our analysis. Sharp money is following
the Chiefs, which validates our +2.5 edge.

Updated recommendation: Chiefs -3.0 if available,
or wait for line to come back to -2.5."
```

**[4:00-6:00] Tool 3: Portfolio Optimization**
```
Me: "I want to bet on Chiefs, Eagles, and 49ers today with $10,000. Optimize my portfolio."

Claude: [Analyzes all games then uses portfolio_optimization]

"I'll analyze each game and optimize your portfolio...

[CALLS TOOLS]
analyze_game(home="Chiefs", away="Bills", spread=-2.5)
analyze_game(home="Eagles", away="Cowboys", spread=-3.0)
analyze_game(home="49ers", away="Seahawks", spread=-4.0)

Results:
• Chiefs: +2.5 edge, 58% win prob
• Eagles: +3.0 edge, 64% win prob
• 49ers: +1.0 edge, 52% win prob

Optimized Portfolio:
• Chiefs: 2.5% ($250) - Good edge, reduced for correlation
• Eagles: 3.0% ($300) - Best edge, full Kelly
• 49ers: 0.5% ($50) - Minimal edge, small stake

Total risk: 6.0% of bankroll
Expected return: +3.8%
Correlation: 15% (safe)
Risk-adjusted return: Excellent"

[HIGHLIGHT CORRELATION ANALYSIS]
Notice how Claude reduced the Chiefs stake due to correlation?
That's portfolio optimization in action!
```

**[6:00-8:00] Custom Prompts**
```
Me: "Use analyze_slate for today"

Claude: [Uses custom prompt]

"Analyzing all NFL games for 2025-11-10...

[SHOWS ANALYSIS FOR EACH GAME]

Top 3 Recommendations by EV:
1. Eagles -3.0: +3.0 edge, 64% win prob, 3.0% stake, EV: +4.2%
2. Chiefs -2.5: +2.5 edge, 58% win prob, 2.5% stake, EV: +3.1%
3. 49ers -4.0: +1.5 edge, 54% win prob, 1.5% stake, EV: +1.8%

[Shows full reasoning for each]

Recommended total stake: 7.0% of bankroll
Expected portfolio return: +3.2%"

This is the analyze_slate prompt in action.
One request, complete slate analysis!
```

**[8:00-10:00] Advanced Features + Wrap-up**
```
Me: "Get active market alerts"

Claude: get_market_alerts()

[SHOWS ALERTS]

Me: "Calculate Kelly stake for a 2.5% edge at -110 with $10k bankroll"

Claude: calculate_kelly_stake(
  edge_percentage=2.5,
  odds=-110,
  bankroll=10000,
  kelly_fraction=0.5
)

"Recommended stake: 3.0% ($300)
Full Kelly would be 6%, but we use 50% for safety."

[FADE TO LOGO]

That's the MCP server! Use Billy Walters methodology
directly from Claude Desktop with natural language.

• 6 powerful tools
• 3 real-time resources
• Custom prompts for complex workflows

Check the docs for setup instructions. See you next time!
```

---

## Tutorial 5: "Automated Game Day" (5 minutes)

### Script

**[0:00-0:30] Intro**
```
It's Sunday morning, 9 AM. Instead of manually scraping data,
researching injuries, and analyzing games...

What if one command did it all?

[DRAMATIC PAUSE]

Let me show you the automated workflow.
```

**[0:30-1:30] One Command**
```
[TERMINAL - BIG TEXT]
$ .codex/workflows/daily-analysis.ps1 -Sport nfl -Bankroll 10000

[PRESS ENTER]

Watch this...

[SHOW AUTOMATED COLLECTION]
[9:00 AM] STAGE 1: DATA COLLECTION
[INFO] Scrape Injuries...
[SUCCESS] 127 injuries collected (8.2s)
[INFO] Highlightly Matches...
[SUCCESS] 16 games collected (2.1s)
[INFO] Highlightly Odds...
[SUCCESS] Odds collected (1.9s)

[+] Stage 1 complete. All data fresh!
```

**[1:30-3:30] Interactive Analysis**
```
[10:00 AM] STAGE 2: SLATE ANALYSIS
Opening interactive mode...

[INTERACTIVE PROMPT APPEARS]

walters> /analyze Chiefs vs Bills -2.5 --research
[SHOW ANALYSIS - Edge: 2.5, Stake: 3%]

walters> /analyze Eagles vs Cowboys -3.0 --research
[SHOW ANALYSIS - Edge: 3.0, Stake: 3%]

walters> /analyze Packers vs Bears -6.5 --research
[SHOW ANALYSIS - Edge: 0.8, No play]

walters> /report session
{
  "games_analyzed": 3,
  "plays_recommended": 2,
  "total_stake": 6.0%,
  "expected_return": "+3.5%"
}

[TYPE]
walters> exit
```

**[3:30-4:30] Sharp Money Monitoring**
```
[11:30 AM] STAGE 3: SHARP MONEY MONITORING
Monitor for 60 minutes? Y

[SHOW MONITORING]

⚠️ ALERT: Chiefs -2.5 → -3.0 (sharp action detected)
✓ Eagles line stable at -3.0
⚠️ ALERT: Packers significant public action

📊 SUMMARY
Alerts: 2
Confirmed: Chiefs sharp action validates our analysis
```

**[4:30-5:00] Wrap-up**
```
[SHOW SUMMARY SCREEN]

DAILY WORKFLOW COMPLETE

Recommendations:
• Chiefs -2.5 or -3.0: 3.0% ($300)
• Eagles -3.0: 3.0% ($300)

Total risk: 6% of bankroll
Expected return: +3.5%

[FADE OUT]

That's it! One command. Complete Sunday workflow.
From zero to analyzed slate in 10 minutes.

Automation + AI + Billy Walters = Winning combination.

See you next Sunday!
```

---

## Tutorial 6: "Chrome DevTools AI Features" (8 minutes)

### Script

**[0:00-0:40] Intro**
```
The Billy Walters Sports Analyzer includes advanced AI features
inspired by Chrome DevTools.

Performance monitoring. Network analysis. Automatic debugging.
All designed to make your scraping faster and more reliable.

Let me show you.
```

**[0:40-2:00] AI-Assisted Scraping**
```
[TERMINAL]
$ uv run walters-analyzer scrape-ai --sport nfl

[SHOW OUTPUT]

================================================================================
AI-ASSISTED ODDS SCRAPING
================================================================================

Features:
  • Performance monitoring with AI insights
  • Network request analysis
  • Automatic debugging recommendations
  • Bottleneck detection

[PROGRESS INDICATORS]

[RESULTS]
Games extracted: 15
Performance Score: 87/100
  [OK] Excellent performance

Extraction: SUCCESS

AI Recommendations (3):
  • request_blocking: Block 15 analytics requests for 20% speed boost
  • wait_strategy: Current 3s wait is optimal
  • cache_usage: 80% cache hit rate - excellent
```

**[2:00-4:00] Performance Insights**
```
[OPEN ai-insights-nfl-TIMESTAMP.json]

{
  "performance_analysis": {
    "performance_score": 87,
    "metrics": {
      "page_load_time": 1200,
      "network_requests": 45,
      "javascript_errors": 0
    },
    "insights": [
      {
        "type": "performance",
        "message": "Page load efficient at 1.2s",
        "recommendation": "No optimization needed"
      }
    ]
  },
  "network_analysis": {
    "odds_endpoints": 3,
    "slow_requests": 0,
    "unnecessary_requests": 15
  }
}

[HIGHLIGHT KEY METRICS]

Like Chrome DevTools Performance tab, we get:
• Performance score (0-100)
• Bottleneck identification
• Optimization suggestions
• Network timing analysis
```

**[4:00-6:00] Debugging Features**
```
[SIMULATE SCRAPING FAILURE]

Extraction: FAILED

Potential Issues:
  • Cloudflare challenge detected (likelihood: very high)
  • Dynamic content not loaded (likelihood: medium)

Suggested Fixes:
  • Wait 5-10 seconds for Cloudflare bypass
  • Verify element selectors
  • Check for page updates

[SHOW FIX]

Just like Chrome DevTools Sources debugging!
The AI tells you:
• What went wrong
• Why it happened
• How to fix it

No guessing. Clear diagnosis. Actionable fixes.
```

**[6:00-8:00] Network Analysis + Wrap-up**
```
[SHOW NETWORK ANALYSIS]

Network Analysis:
• Total requests: 45
• Odds API endpoints: 3 found
• Slow requests: 2 (>1s)
• Unnecessary: 15 analytics requests

Recommendations:
• Block: google-analytics.com, facebook.com, ...
• Expected speedup: 20-25%
• Bandwidth saved: ~500KB per scrape

[TERMINAL]
# Apply recommendations
[Show configuration change]

# Re-run with optimizations
$ uv run walters-analyzer scrape-ai --sport nfl

Performance Score: 95/100 (was 87)
Extraction time: 3.2s (was 4.1s)
[SHOW 20% IMPROVEMENT]

That's AI-assisted scraping! 
Chrome DevTools patterns make it fast, reliable, and self-improving.

Check docs/guides for complete reference. Happy scraping!
```

---

## Demo Scenarios

### Scenario 1: "First Time User"

**Goal**: Get from zero to first analysis in 2 minutes

```bash
# Install
git clone [repo]
cd billy-walters-sports-analyzer
uv sync

# First analysis
uv run walters-analyzer analyze-game \
  --home "Chiefs" \
  --away "Bills" \
  --spread -2.5

# Success! Show output, explain edge, stake, confidence
```

### Scenario 2: "Power User"

**Goal**: Analyze full Sunday slate with automation

```powershell
# Morning (one command does everything)
.codex/workflows/daily-analysis.ps1 -Sport nfl -Bankroll 10000

# Interactive analysis
# Sharp money monitoring
# Done in 15 minutes total
```

### Scenario 3: "Developer Integration"

**Goal**: Integrate into existing betting system

```python
# Python API usage
from walters_analyzer.core import BillyWaltersAnalyzer
from walters_analyzer.core.models import GameInput, TeamSnapshot, GameOdds, SpreadLine

# Build game
game = GameInput(
    home_team=TeamSnapshot(name="Chiefs"),
    away_team=TeamSnapshot(name="Bills"),
    odds=GameOdds(spread=SpreadLine(home_spread=-2.5))
)

# Analyze
analyzer = BillyWaltersAnalyzer()
result = analyzer.analyze(game)

# Use result
print(f"Edge: {result.edge}")
print(f"Stake: {result.recommendation.stake_pct}%")
```

---

## Screen Recording Tips

### Terminal Settings
- Font: Fira Code, size 14-16
- Theme: Dark with good contrast
- Colors: Bright for visibility
- Window: Full screen or large size

### Pacing
- Type commands slowly (1-2 chars/sec)
- Pause to show output (3-5 seconds)
- Highlight key parts (circle/arrow annotations)
- Explain as you go

### Annotations
- **Arrow**: Point to important values
- **Circle**: Highlight key metrics
- **Box**: Frame sections
- **Zoom**: Enlarge small text

### Voice-Over
- Clear, enthusiastic tone
- Explain technical terms
- Relate to real-world betting
- Summarize at transitions

---

## Conclusion

These video scripts demonstrate:

✅ **Quick start** (30 seconds to first analysis)  
✅ **Interactive mode** (power user workflow)  
✅ **Automation** (one-command game day)  
✅ **MCP integration** (Claude Desktop usage)  
✅ **AI features** (Chrome DevTools patterns)  

**Each tutorial showcases different aspects of the system while maintaining focus on ease of use and AI assistance.**

---

**Production Notes:**
- Record at 1080p minimum (4K preferred)
- Use screen recording software with audio
- Add chapter markers at sections
- Include captions for accessibility
- Provide command reference in description

**See Also:**
- **Quick Start**: `docs/guides/QUICKSTART_ANALYZE_GAME.md`
- **CLI Reference**: `docs/guides/CLI_REFERENCE.md`
- **MCP API**: `docs/MCP_API_REFERENCE.md`

