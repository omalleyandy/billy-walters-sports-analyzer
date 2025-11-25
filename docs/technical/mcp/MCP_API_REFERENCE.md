# MCP Server API Reference - Billy Walters Sports Analyzer

**Server Name**: `billy-walters-expert`  
**Version**: 2.0.0  
**Protocol**: Model Context Protocol (MCP)  
**Framework**: FastMCP

## Overview

The Billy Walters MCP Server provides Claude Desktop with 6 powerful analysis tools, 3 real-time resources, and custom prompts for comprehensive betting analysis.

**Location**: `.claude/walters_mcp_server.py`

## Configuration

### Claude Desktop Setup

1. **Install Dependencies**:
```bash
uv sync --extra mcp
```

2. **Update Claude Desktop Config**:
Location: `~/.config/Claude/claude-desktop-config.json` (Linux/Mac)  
Or: `%APPDATA%\Claude\claude-desktop-config.json` (Windows)

Copy from: `.claude/claude-desktop-config.json`

3. **Set Environment Variables**:
```bash
export ACCUWEATHER_API_KEY=your_key
export HIGHLIGHTLY_API_KEY=your_key
export ODDS_API_KEY=your_key
```

4. **Start MCP Server**:
```bash
uv run python .claude/walters_mcp_server.py
```

5. **Restart Claude Desktop**

---

## Tools

### 1. analyze_game

Comprehensive game analysis using Billy Walters methodology.

**Function Signature:**
```python
async def analyze_game(
    home_team: str,
    away_team: str,
    spread: float,
    total: Optional[float] = None,
    game_date: Optional[str] = None,
    include_research: bool = True
) -> Dict[str, Any]
```

**Parameters:**
- `home_team` (string, required): Home team name (e.g., "Kansas City Chiefs")
- `away_team` (string, required): Away team name (e.g., "Buffalo Bills")
- `spread` (number, required): Current market spread (home perspective)
- `total` (number, optional): Game total O/U
- `game_date` (string, optional): Game date in YYYY-MM-DD format
- `include_research` (boolean, optional, default=true): Fetch injury/weather data

**Returns:**
```json
{
  "matchup": "Buffalo Bills @ Kansas City Chiefs",
  "spread": "Kansas City Chiefs -2.5",
  "analysis": {
    "predicted_spread": 0.0,
    "market_spread": -2.5,
    "edge": 2.5,
    "confidence": "Elevated Confidence"
  },
  "injuries": {
    "home_impact": 0.0,
    "away_impact": 0.0,
    "advantage": 0.0
  },
  "key_numbers": [
    "Projection crosses 3 (moving toward underdog)"
  ],
  "recommendation": {
    "bet_type": "spread",
    "team": "Kansas City Chiefs",
    "edge": 2.5,
    "win_probability": 0.58,
    "stake_pct": 3.0,
    "stake_amount": 300.0,
    "conviction": "Elevated Confidence"
  },
  "ai_insights": {
    "confidence_explanation": "2.5 pt edge significant. Historical win rate: 58%",
    "risk_level": "low",
    "optimization_tips": [...]
  }
}
```

**Example Usage in Claude:**
```
analyze_game(
  home_team="Kansas City Chiefs",
  away_team="Buffalo Bills",
  spread=-2.5,
  include_research=true
)
```

**Use Cases:**
- Pre-game analysis
- Line shopping validation
- Edge verification
- Research coordination

---

### 2. find_sharp_money

Monitor games for sharp betting patterns and reverse line movement.

**Function Signature:**
```python
async def find_sharp_money(
    game_id: str,
    monitor_duration: int = 3600
) -> Dict[str, Any]
```

**Parameters:**
- `game_id` (string, required): Game identifier
- `monitor_duration` (number, optional, default=3600): Duration in seconds

**Returns:**
```json
{
  "game_id": "chiefs_bills_2025-11-10",
  "monitoring_duration": 3600,
  "alerts": [
    {
      "timestamp": "2025-11-10T10:30:00Z",
      "type": "reverse_line_movement",
      "old_line": -2.5,
      "new_line": -2.0,
      "public_percentage": 65,
      "sharp_indicator": 0.85,
      "confidence": "high",
      "recommendation": "Sharp money on underdog"
    }
  ],
  "summary": {
    "total_alerts": 3,
    "avg_confidence": 0.78,
    "recommendation": "Strong sharp action detected - consider contrarian play"
  }
}
```

**Example Usage:**
```
find_sharp_money(game_id="chiefs_bills", monitor_duration=1800)
```

**Use Cases:**
- Pre-game sharp money detection
- Line movement analysis
- Steam detection
- Contrarian betting opportunities

---

### 3. calculate_kelly_stake

Calculate optimal bet sizing using Kelly Criterion.

**Function Signature:**
```python
async def calculate_kelly_stake(
    edge_percentage: float,
    odds: int,
    bankroll: float,
    kelly_fraction: float = 0.5
) -> Dict[str, Any]
```

**Parameters:**
- `edge_percentage` (number, required): Your calculated edge (e.g., 2.5 for 2.5%)
- `odds` (number, required): American odds (e.g., -110, +150)
- `bankroll` (number, required): Current bankroll amount
- `kelly_fraction` (number, optional, default=0.5): Fraction of full Kelly (0.5 = half Kelly)

**Returns:**
```json
{
  "full_kelly": 4.8,
  "fractional_kelly": 2.4,
  "recommended_stake_pct": 2.4,
  "recommended_stake_amount": 240.0,
  "max_allowed_pct": 3.0,
  "capped_stake_pct": 2.4,
  "capped_stake_amount": 240.0,
  "explanation": "Using 0.5 fractional Kelly for safety. Capped at 3% max bet.",
  "risk_assessment": {
    "probability_of_ruin": 0.02,
    "expected_growth_rate": 0.045,
    "kelly_volatility": "moderate"
  }
}
```

**Example Usage:**
```
calculate_kelly_stake(
  edge_percentage=2.5,
  odds=-110,
  bankroll=10000,
  kelly_fraction=0.5
)
```

**Use Cases:**
- Bet sizing validation
- Risk assessment
- Bankroll management
- Portfolio optimization

---

### 4. backtest_strategy

Test betting strategies on historical data.

**Function Signature:**
```python
async def backtest_strategy(
    strategy: str,
    start_date: str,
    end_date: str,
    initial_bankroll: float = 10000.0
) -> Dict[str, Any]
```

**Parameters:**
- `strategy` (string, required): Strategy name ("power_ratings", "key_numbers", "injury_based")
- `start_date` (string, required): Start date (YYYY-MM-DD)
- `end_date` (string, required): End date (YYYY-MM-DD)
- `initial_bankroll` (number, optional, default=10000): Starting bankroll

**Returns:**
```json
{
  "strategy": "power_ratings",
  "period": "2024-09-01 to 2024-11-01",
  "results": {
    "total_bets": 127,
    "wins": 72,
    "losses": 51,
    "pushes": 4,
    "win_rate": 0.585,
    "roi": 8.7,
    "final_bankroll": 10870.0,
    "max_drawdown": -420.0,
    "sharpe_ratio": 1.23,
    "avg_clv": 0.45
  },
  "confidence_breakdown": {
    "high_confidence": {"bets": 23, "win_rate": 0.652},
    "elevated_confidence": {"bets": 48, "win_rate": 0.604},
    "slight_edge": {"bets": 56, "win_rate": 0.536}
  },
  "insights": [
    "High confidence bets showed 65.2% win rate",
    "Positive CLV of +0.45 points indicates sharp line detection",
    "Max drawdown of $420 within acceptable limits"
  ]
}
```

**Example Usage:**
```
backtest_strategy(
  strategy="power_ratings",
  start_date="2024-09-01",
  end_date="2024-11-01",
  initial_bankroll=10000
)
```

**Use Cases:**
- Strategy validation
- Historical performance analysis
- Risk assessment
- Edge verification

---

### 5. get_injury_report

Get comprehensive injury analysis for a team.

**Function Signature:**
```python
async def get_injury_report(
    team: str
) -> Dict[str, Any]
```

**Parameters:**
- `team` (string, required): Team name (e.g., "Philadelphia Eagles")

**Returns:**
```json
{
  "team": "Philadelphia Eagles",
  "injury_count": 15,
  "total_impact": -3.2,
  "critical_injuries": [
    {
      "player": "Jalen Hurts",
      "position": "QB",
      "status": "Questionable",
      "injury": "Ankle",
      "points": -3.5,
      "game_time_decision": true
    }
  ],
  "by_position": {
    "QB": {"count": 1, "impact": -3.5},
    "WR": {"count": 3, "impact": -2.7},
    "OL": {"count": 2, "impact": -1.8}
  },
  "position_crises": [
    "Multiple OL injuries - pass protection concern"
  ],
  "recommendations": [
    "QB injury significant - monitor game-time status",
    "Consider under if Hurts sits",
    "Line should move 3-4 points if Hurts out"
  ]
}
```

**Example Usage:**
```
get_injury_report(team="Philadelphia Eagles")
```

**Use Cases:**
- Pre-game injury assessment
- Line movement prediction
- Situational analysis
- Research verification

---

### 6. get_market_alerts

Retrieve active betting alerts and opportunities.

**Function Signature:**
```python
async def get_market_alerts() -> Dict[str, Any]
```

**Parameters:** None

**Returns:**
```json
{
  "active_alerts": [
    {
      "alert_id": "alert_001",
      "type": "steam",
      "game": "Chiefs vs Bills",
      "direction": "Chiefs -2.5 → -3.0",
      "confidence": 0.87,
      "created_at": "2025-11-10T10:15:00Z",
      "expires_at": "2025-11-10T11:00:00Z",
      "action": "Consider following steam on Chiefs",
      "edge_estimate": 1.2
    },
    {
      "alert_id": "alert_002",
      "type": "reverse_line_movement",
      "game": "Eagles vs Cowboys",
      "details": "Line moved toward underdog despite 70% public on favorite",
      "sharp_indicator": 0.92,
      "recommendation": "Strong sharp play on Cowboys"
    }
  ],
  "summary": {
    "total_active": 2,
    "high_confidence": 1,
    "moderate_confidence": 1,
    "expires_soon": []
  }
}
```

**Example Usage:**
```
get_market_alerts()
```

**Use Cases:**
- Real-time opportunity detection
- Steam identification
- Reverse line movement alerts
- Market inefficiency detection

---

## Resources

### 1. betting-history

Historical betting performance data.

**URI**: `betting-history://latest`  
**Refresh**: On-demand

**Data Structure:**
```json
{
  "total_bets": 127,
  "period": "Last 90 days",
  "performance": {
    "win_rate": 0.585,
    "roi": 8.7,
    "units_won": 11.2,
    "avg_stake": 2.1
  },
  "by_confidence": {
    "high": {"bets": 23, "win_rate": 0.652, "roi": 12.4},
    "elevated": {"bets": 48, "win_rate": 0.604, "roi": 9.1},
    "slight": {"bets": 56, "win_rate": 0.536, "roi": 4.3}
  },
  "recent_bets": [
    {
      "date": "2025-11-07",
      "game": "Chiefs -2.5",
      "stake": 3.0,
      "result": "win",
      "pnl": 270.0,
      "clv": 0.5
    }
  ]
}
```

### 2. active-monitors

Currently active market monitoring sessions.

**URI**: `active-monitors://status`  
**Refresh**: Real-time

**Data Structure:**
```json
{
  "active_monitors": [
    {
      "monitor_id": "mon_001",
      "game": "Chiefs vs Bills",
      "started_at": "2025-11-10T10:00:00Z",
      "duration": 3600,
      "alerts_generated": 3,
      "status": "active"
    }
  ],
  "total_active": 1,
  "system_status": "operational"
}
```

### 3. system-config

Current system configuration and settings.

**URI**: `system-config://current`  
**Refresh**: On-demand

**Data Structure:**
```json
{
  "bankroll": {
    "current": 10000.0,
    "initial": 10000.0,
    "max_bet_pct": 3.0,
    "fractional_kelly": 0.5
  },
  "key_numbers": [3, 7, 6, 10, 14],
  "confidence_thresholds": {
    "high": 3.0,
    "elevated": 2.0,
    "slight": 1.0
  },
  "research": {
    "accuweather_enabled": true,
    "profootballdoc_enabled": true,
    "highlightly_enabled": true,
    "cache_ttl": 300
  },
  "features": {
    "autonomous_agent": false,
    "ml_predictions": true,
    "ai_scraping": true
  }
}
```

---

## Custom Prompts

### 1. analyze_slate

Analyze full slate of games for a given date.

**Usage in Claude:**
```
Use the analyze_slate prompt for 2025-11-10
```

**Template:**
```
Analyze all NFL games for {date} using Billy Walters methodology. 
For each game, provide:
1. Power rating analysis
2. Injury impact assessment
3. Key number evaluation
4. Sharp money indicators
5. Recommended bet sizing

Focus on games with edges > 2 points.
Rank by expected value.
```

**Parameters:**
- `{date}` - Game date (YYYY-MM-DD)

**Output:**
- Full slate analysis
- Ranked by EV
- Top 3-5 recommendations

### 2. find_value

Find best value bets across all available games.

**Usage in Claude:**
```
Use the find_value prompt
```

**Template:**
```
Search for the best value betting opportunities in today's games.

Look for:
1. Reverse line movement (public vs sharp money)
2. Key number advantages (3, 7 specifically)
3. Power rating edges > 2.5 points
4. Weather/injury impacts underpriced by market

Rank by expected value and provide:
- Top 5 opportunities
- Risk assessment for each
- Optimal bet sizing
- Entry timing recommendations
```

**Output:**
- Top value bets
- EV rankings
- Risk-adjusted recommendations

### 3. portfolio_optimization

Optimize betting portfolio for risk/reward.

**Usage in Claude:**
```
Use the portfolio_optimization prompt with bankroll=10000 and games=[...]
```

**Template:**
```
Given a bankroll of {bankroll} and the following games {games}, 
create an optimal betting portfolio.

Apply:
1. Kelly Criterion sizing
2. Correlation risk limits (<20%)
3. Maximum single bet (3% of bankroll)
4. Diversification across time slots
5. Risk of ruin minimization

Provide:
- Recommended bets with sizing
- Portfolio correlation matrix
- Expected return and volatility
- Risk metrics (VaR, max drawdown)
```

**Parameters:**
- `{bankroll}` - Current bankroll
- `{games}` - List of games with edges

**Output:**
- Optimized portfolio
- Risk metrics
- Expected outcomes

---

## Tool Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {
    /* Tool-specific data */
  },
  "metadata": {
    "timestamp": "2025-11-10T10:00:00Z",
    "execution_time_ms": 245,
    "cache_hit": false
  }
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "type": "ValueError",
    "message": "Invalid team name",
    "suggestion": "Check team name spelling or use /research to find correct name"
  },
  "metadata": {
    "timestamp": "2025-11-10T10:00:00Z"
  }
}
```

---

## Advanced Usage

### Chaining Tools

```
# Step 1: Get injury report
injuries = get_injury_report(team="Chiefs")

# Step 2: Analyze game with injury context
analysis = analyze_game(
  home_team="Chiefs",
  away_team="Bills",
  spread=-2.5,
  include_research=true
)

# Step 3: Calculate optimal stake
stake = calculate_kelly_stake(
  edge_percentage=analysis.edge,
  odds=-110,
  bankroll=10000
)

# Step 4: Monitor for sharp money
alerts = find_sharp_money(
  game_id="chiefs_bills",
  monitor_duration=3600
)
```

### Using Prompts with Tools

```
# 1. Use analyze_slate prompt to get top games
Top games for today: Chiefs -2.5, Eagles -3.0, 49ers -4.0

# 2. Deep dive with tools
analyze_game(home_team="Chiefs", away_team="Bills", spread=-2.5)
get_injury_report(team="Bills")

# 3. Portfolio optimization
Use portfolio_optimization with these 3 games and $10,000 bankroll
```

---

## Performance Characteristics

| Tool | Avg Response Time | Cache Hit | Notes |
|------|------------------|-----------|-------|
| analyze_game | 200-500ms | 80% | Fast with cached research |
| find_sharp_money | 1-2s | N/A | Real-time API calls |
| calculate_kelly_stake | <50ms | N/A | Pure calculation |
| backtest_strategy | 5-30s | 50% | Depends on data volume |
| get_injury_report | 100-300ms | 90% | Heavily cached |
| get_market_alerts | <100ms | N/A | In-memory checks |

---

## Error Handling

### Common Errors

**Invalid Team Name:**
```json
{
  "error": "Team not found: 'Cheifs'",
  "suggestion": "Did you mean 'Chiefs'?",
  "valid_teams": ["Kansas City Chiefs", "Buffalo Bills", ...]
}
```

**Missing API Key:**
```json
{
  "error": "AccuWeather API key not configured",
  "suggestion": "Set ACCUWEATHER_API_KEY in environment",
  "impact": "Weather data unavailable (analysis continues)"
}
```

**Rate Limit:**
```json
{
  "error": "API rate limit exceeded",
  "retry_after": 60,
  "suggestion": "Wait 60 seconds or use cached data"
}
```

### Graceful Degradation

If a component fails:
1. **Log warning** (not error)
2. **Continue with available data**
3. **Note limitation in response**
4. **Provide alternative suggestions**

Example:
```json
{
  "status": "partial_success",
  "data": { /* Analysis with available data */ },
  "warnings": [
    "Weather data unavailable - using historical averages",
    "Injury data from cache (2 hours old)"
  ]
}
```

---

## Rate Limiting

### Default Limits
- **MCP Server**: 60 requests/minute
- **AccuWeather**: 50 calls/day (free tier)
- **Highlightly**: 1000 calls/day
- **The Odds API**: 500 calls/month (free tier)

### Optimization Strategies
1. **Caching**: 5-minute TTL for research data
2. **Batching**: Combine multiple requests
3. **Lazy Loading**: Fetch only when needed
4. **Fallbacks**: Use cached data when rate-limited

---

## Integration Examples

### Example 1: Pre-Game Analysis Workflow

```
# In Claude Desktop
User: "Analyze today's NFL slate"

Claude: [Uses analyze_slate prompt]

For each game:
1. analyze_game(home="Team A", away="Team B", spread=-3.5, include_research=true)
2. get_injury_report(team="Team A")
3. calculate_kelly_stake(edge=2.5, odds=-110, bankroll=10000)

Returns: Top 3 recommendations with full reasoning
```

### Example 2: Sharp Money Detection

```
User: "Monitor Chiefs-Bills for sharp money"

Claude: find_sharp_money(game_id="chiefs_bills", monitor_duration=3600)

# After monitoring
User: "Should I bet this?"

Claude: 
1. Checks alerts from find_sharp_money
2. Runs analyze_game for current analysis
3. Calculates stake with calculate_kelly_stake
4. Provides recommendation with reasoning
```

### Example 3: Portfolio Optimization

```
User: "Optimize my Sunday portfolio with $10,000"

Claude:
1. Gets all games: analyze_slate for today
2. For each game: analyze_game with research
3. Uses portfolio_optimization prompt
4. Returns optimal bet distribution with:
   - Stake sizing per game
   - Correlation analysis
   - Risk metrics
   - Expected portfolio return
```

---

## Monitoring & Debugging

### MCP Server Logs

**Location**: `logs/mcp-server.log`

**Format:**
```
2025-11-10 10:00:00 - INFO - MCP Server initialized
2025-11-10 10:00:15 - INFO - Tool called: analyze_game
2025-11-10 10:00:15 - DEBUG - Research engine: cache hit
2025-11-10 10:00:15 - INFO - Analysis complete (250ms)
```

### Performance Monitoring

```python
# In MCP server
@mcp.tool()
async def analyze_game(...):
    start_time = time.time()
    
    try:
        result = await do_analysis()
        duration = (time.time() - start_time) * 1000
        
        logger.info(f"analyze_game completed ({duration:.0f}ms)")
        return result
    except Exception as e:
        logger.error(f"analyze_game failed: {e}")
        raise
```

---

## Security Considerations

### API Key Safety
- **Never** log API keys
- **Never** return API keys in responses
- **Always** use environment variables
- **Validate** all inputs before API calls

### Data Privacy
- No personal betting data shared externally
- All data stored locally
- Optional anonymous usage stats
- Full GDPR compliance

---

## Troubleshooting

### MCP Server Won't Start

**Check:**
1. Python environment: `uv sync --extra mcp`
2. Environment variables: `echo $ACCUWEATHER_API_KEY`
3. Port conflicts: MCP uses default port
4. Claude Desktop config: Verify paths

**Fix:**
```bash
# Reinstall dependencies
uv sync --extra mcp --force

# Verify server starts
uv run python .claude/walters_mcp_server.py

# Check Claude Desktop config
cat ~/.config/Claude/claude-desktop-config.json
```

### Tools Not Appearing in Claude

**Possible causes:**
1. MCP server not running
2. Claude Desktop not restarted
3. Configuration file errors
4. Environment variables missing

**Fix:**
1. Restart MCP server
2. Restart Claude Desktop completely
3. Check logs for errors
4. Verify config file syntax

### Slow Tool Responses

**Causes:**
- API rate limiting
- No caching (cold start)
- Network latency
- Large dataset processing

**Optimizations:**
1. Use caching (default 5-min TTL)
2. Reduce monitor_duration
3. Limit backtest date range
4. Pre-warm cache with common queries

---

## Best Practices

### 1. Cache Management
```
# Let cache warm up with common teams
get_injury_report("Chiefs")
get_injury_report("Bills")
get_injury_report("Eagles")

# Future queries will hit cache
```

### 2. Research Data Freshness
```
# Morning: Scrape fresh data
walters-analyzer scrape-injuries --sport nfl

# Then: Analysis uses fresh cache
analyze_game(..., include_research=true)
```

### 3. Rate Limit Management
```
# Batch similar queries
analyze_slate (analyzes all games efficiently)

# Instead of:
analyze_game for each game individually
```

### 4. Error Recovery
```
# If tool fails, retry with degraded mode
analyze_game(..., include_research=false)  # Skip research if API down
```

---

## Conclusion

The Billy Walters MCP Server provides Claude Desktop with comprehensive betting analysis capabilities through:

✅ **6 powerful tools** for all analysis needs  
✅ **3 real-time resources** for performance tracking  
✅ **Custom prompts** for complex workflows  
✅ **Professional error handling** with graceful degradation  
✅ **Performance optimization** with intelligent caching  
✅ **Full transparency** with reasoning chains  

**The MCP server makes Billy Walters methodology accessible directly from Claude Desktop with AI-powered assistance!**

---

**See Also:**
- **Architecture**: `docs/ARCHITECTURE.md`
- **CLI Reference**: `docs/guides/CLI_REFERENCE.md`
- **Quick Start**: `docs/guides/QUICKSTART_ANALYZE_GAME.md`
- **MCP Server Code**: `.claude/walters_mcp_server.py`

