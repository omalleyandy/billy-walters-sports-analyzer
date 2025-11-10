# Claude Integration for Billy Walters Sports Analyzer

This directory contains Claude Desktop integration components including an MCP server and autonomous betting agent.

## Components

### 1. MCP Server (`walters_mcp_server.py`)

FastMCP-based server that exposes Billy Walters analysis capabilities to Claude Desktop.

#### Features
- **6 Core Tools**: Game analysis, sharp money detection, Kelly sizing, backtesting, injury reports, market alerts
- **3 Resources**: Betting history, active monitors, system config
- **Custom Prompts**: Slate analysis, value finding, portfolio optimization

#### Setup

1. **Install dependencies**:
```bash
uv sync
# or manually:
pip install fastmcp pydantic aiohttp
```

2. **Set environment variables**:
```bash
export WALTERS_API_KEY="your_key"
export NEWS_API_KEY="your_key"
export HIGHLIGHTLY_API_KEY="your_key"
export ACCUWEATHER_API_KEY="your_key"
export PYTHONPATH="${PYTHONPATH}:./src"
```

3. **Configure Claude Desktop**:
   - Copy `claude-desktop-config.json` settings to your Claude Desktop config
   - Location: `~/.config/Claude/claude_desktop_config.json` (Linux/Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

4. **Start the server**:
```bash
uv run python .claude/walters_mcp_server.py
```

#### Available Tools

**analyze_game**
```python
# Comprehensive game analysis with Billy Walters methodology
{
  "home_team": "Kansas City Chiefs",
  "away_team": "Buffalo Bills",
  "spread": -2.5,
  "total": 47.5,
  "include_research": true
}
```

**find_sharp_money**
```python
# Monitor game for sharp betting patterns
{
  "game_id": "KC_vs_BUF",
  "monitor_duration": 3600  # seconds
}
```

**calculate_kelly_stake**
```python
# Calculate optimal bet sizing using Kelly Criterion
{
  "edge_percentage": 2.5,
  "odds": -110,
  "bankroll": 10000,
  "kelly_fraction": 0.25
}
```

**backtest_strategy**
```python
# Test betting strategies on historical data
{
  "strategy": "power_rating",
  "start_date": "2024-09-01",
  "end_date": "2024-12-31",
  "initial_bankroll": 10000
}
```

**get_injury_report**
```python
# Get comprehensive injury analysis for a team
{
  "team": "Kansas City Chiefs"
}
```

**get_market_alerts**
```python
# Retrieve active betting alerts and opportunities
{}
```

### 2. Autonomous Agent (`walters_autonomous_agent.py`)

Self-learning betting agent with reasoning chains and ML capabilities.

#### Features
- **5-Step Reasoning Chain**: Power ratings → Market analysis → Situational factors → Historical patterns → Risk assessment
- **Machine Learning**: XGBoost, Random Forest, optional PyTorch
- **Portfolio Management**: Correlation analysis, VaR calculation, position sizing
- **Memory System**: Learns from past decisions

#### Setup

1. **Install ML dependencies**:
```bash
uv add scikit-learn xgboost numpy pandas
# Optional for deep learning:
uv add torch
```

2. **Usage Example**:
```python
from .claude.walters_autonomous_agent import WaltersCognitiveAgent

# Initialize agent
agent = WaltersCognitiveAgent(initial_bankroll=10000)

# Make decision
game_data = {
    'game_id': 'KC_vs_BUF_2024',
    'home_team': 'Kansas City Chiefs',
    'away_team': 'Buffalo Bills',
    'spread': -2.5,
    'total': 47.5,
    'home_rating': 8.5,
    'away_rating': 9.0,
    'home_field_advantage': 2.5,
    'opening_spread': -3.5,
    'public_percentage': 68,
    'money_percentage': 45
}

decision = await agent.make_autonomous_decision(game_data)

# View reasoning
for step in decision.reasoning_chain:
    print(f"Step {step.step_number}: {step.description}")
    print(f"Confidence: {step.confidence:.1%}")
    print(f"Evidence: {step.evidence}")
    print(f"Impact: {step.impact_on_decision}\n")

# View recommendation
print(f"Recommendation: {decision.recommendation}")
print(f"Confidence: {decision.confidence.name}")
print(f"Stake: {decision.stake_percentage:.1f}% of bankroll")
print(f"Expected Value: {decision.expected_value:.2f}%")
```

#### Agent Capabilities

**Power Rating Analysis**
- Team strength evaluation
- Home field advantage
- Predicted spread calculation
- Edge identification

**Market Analysis**
- Line movement tracking
- Public vs sharp money splits
- Reverse line movement detection
- Key number analysis (3, 7, 6, 10, 14)

**Situational Factors**
- Rest advantage calculation
- Travel impact assessment
- Motivational spots (revenge games, lookahead, sandwich)
- Timezone crosses

**Pattern Recognition**
- Historical game similarity matching
- Success rate analysis
- ROI tracking
- Neural pattern matching (if PyTorch available)

**Risk Management**
- Portfolio correlation analysis
- Value at Risk (VaR) calculation
- Maximum drawdown assessment
- Position size optimization

#### Meta Learning

The agent learns from every decision:
```python
# Agent automatically learns
agent.memory_bank.remember_decision(decision, outcome)

# Get learned strategies
strategies = await agent.meta_learner.get_strategy_recommendations()
for strategy, perf in strategies.items():
    print(f"{strategy}: {perf['recommendation']} ({perf['performance']:.1%} win rate)")
```

### 3. Claude Desktop Config (`claude-desktop-config.json`)

Complete configuration for Claude Desktop integration.

#### Structure
- **mcpServers**: MCP server definitions
- **globalSettings**: Server behavior
- **slashCommands**: Custom slash commands
- **skills**: Skill configurations
- **dataConnections**: API integrations
- **autonomousAgent**: Agent settings
- **monitoring**: Performance tracking

#### Slash Commands

- `/analyze <home_team> vs <away_team> [options]` - Analyze a game matchup
- `/research <topic> [team] [options]` - Research teams, injuries, or conditions
- `/market <game_id> [duration=3600]` - Monitor market movements
- `/agent analyze <game_id>` - Activate autonomous agent
- `/backtest <strategy> from=<date> to=<date>` - Backtest strategies
- `/report <type> [format=markdown]` - Generate reports

## Quick Start

### 1. Basic Setup
```bash
# Install dependencies
uv sync

# Set API keys in .env
cp env.template .env
# Edit .env with your API keys

# Test MCP server
uv run python .claude/walters_mcp_server.py
```

### 2. Claude Desktop Integration
```bash
# Copy config to Claude Desktop
cp .claude/claude-desktop-config.json ~/.config/Claude/claude_desktop_config.json

# Restart Claude Desktop
# The MCP server will auto-start when Claude Desktop launches
```

### 3. Test Autonomous Agent
```bash
# Run the agent demo
uv run python -c "
from walters_autonomous_agent import main
import asyncio
asyncio.run(main())
"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Desktop                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Chat UI    │  │    Tools     │  │   Prompts    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
└─────────────────────────────┬───────────────────────────────┘
                              │ MCP Protocol
┌─────────────────────────────┴───────────────────────────────┐
│                      MCP Server                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              WaltersMCPEngine                        │  │
│  │  • Game Analysis    • Sharp Money Detection          │  │
│  │  • Kelly Sizing     • Backtesting                    │  │
│  │  • Injury Reports   • Market Alerts                  │  │
│  └──────────────┬────────────────────────────────────────┘  │
│                 │                                            │
│  ┌──────────────┴────────────────────────────────────────┐  │
│  │         WaltersSportsAnalyzer (Core)                  │  │
│  │  • Power Ratings    • Bankroll Management            │  │
│  │  • Key Numbers      • Risk Analysis                   │  │
│  └──────────────┬────────────────────────────────────────┘  │
│                 │                                            │
│  ┌──────────────┴────────────────────────────────────────┐  │
│  │         ResearchEngine                                │  │
│  │  • AccuWeather     • ProFootballDoc                   │  │
│  │  • Highlightly     • Web Integration                  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────┴───────────────────────────────┐
│              Autonomous Agent (Optional)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         WaltersCognitiveAgent                        │  │
│  │  • Reasoning Chain    • Pattern Recognition          │  │
│  │  • ML Models          • Portfolio Optimization       │  │
│  │  • Meta Learning      • Memory System                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Dependencies

### Required
- `fastmcp` - MCP server framework
- `pydantic` - Data validation
- `aiohttp` - Async HTTP client

### Optional (for Autonomous Agent)
- `scikit-learn` - ML models
- `xgboost` - Gradient boosting
- `numpy` - Numerical computing
- `pandas` - Data analysis
- `torch` - Deep learning (optional)

## Safety & Compliance

This system is designed for **educational purposes only**.

**Important Safety Features:**
- Paper trading mode enabled by default
- Daily loss limits (5% of bankroll)
- Confirmation required for all bets
- Maximum bet size (3% of bankroll)
- Risk monitoring and alerts

**Educational Use Only:**
Sports betting involves substantial risk of financial loss. This system is provided for learning and research purposes. Always bet responsibly and within your means.

## Troubleshooting

### MCP Server won't start
```bash
# Check dependencies
uv sync

# Check API keys
echo $WALTERS_API_KEY

# Check PYTHONPATH
echo $PYTHONPATH

# Run with debug logging
LOG_LEVEL=DEBUG uv run python .claude/walters_mcp_server.py
```

### Claude Desktop not connecting
1. Verify config location: `~/.config/Claude/claude_desktop_config.json`
2. Check server is running: `ps aux | grep walters_mcp_server`
3. Restart Claude Desktop
4. Check Claude Desktop logs

### Autonomous Agent errors
```bash
# Install ML dependencies
uv add scikit-learn xgboost numpy pandas

# For PyTorch support
uv add torch

# Test agent
uv run python .claude/walters_autonomous_agent.py
```

## Contributing

When adding new MCP tools or agent capabilities:
1. Update `walters_mcp_server.py` with new @mcp.tool() decorators
2. Update `claude-desktop-config.json` capabilities section
3. Update this README with usage examples
4. Add tests for new functionality

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Billy Walters Methodology](../docs/billy_walters_cheat_card.md)
- [Integration Analysis](../INTEGRATION_ANALYSIS.md)
