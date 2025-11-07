# Billy Walters Sports Expert (Educational)

One-stop, backtestable SDK that wraps power ratings, key-number edges, injuries,
and weather into a reproducible package. **For learning only.**

## Quick start

```bash
uv sync  # or: python -m pip install -e .
uv run walters analyze "Philadelphia Eagles" "Dallas Cowboys" --spread -3.5
```

## Layout

- `walters_analyzer/core`: ratings, key numbers, bankroll, analyzer
- `walters_analyzer/research`: injuries (ProFootballDoc), weather (AccuWeather), odds (Highlightly)
- `docs`: Billy Walters masterclass notes & cheat card

## Features

### Core Analysis
- **Power Ratings**: Team strength evaluation
- **Key Numbers**: NFL spread significance analysis (3, 7, 6, 10, 14)
- **Bankroll Management**: Kelly Criterion and fractional Kelly
- **Market Analysis**: Sharp money detection and reverse line movement

### Research Integration
- **Injury Reports**: ProFootballDoc integration with point value impact
- **Weather Data**: AccuWeather API for outdoor games
- **Odds Tracking**: Highlightly API for line movement monitoring

### Advanced Features
- **MCP Server**: Claude Desktop integration for AI-powered analysis
- **Autonomous Agent**: Self-learning betting agent with reasoning chains
- **Portfolio Optimization**: Risk management and correlation analysis
- **Backtesting**: Historical strategy validation

## Claude Desktop Integration

This project includes a fully configured MCP server for Claude Desktop:

1. Copy `.claude/claude-desktop-config.json` to your Claude Desktop config
2. Update API keys in your environment
3. Start the MCP server: `uv run python .claude/walters_mcp_server.py`

### Available Tools
- `analyze_game` - Comprehensive game analysis
- `find_sharp_money` - Monitor for sharp betting patterns
- `calculate_kelly_stake` - Optimal bet sizing
- `backtest_strategy` - Test strategies on historical data
- `get_injury_report` - Team injury analysis
- `get_market_alerts` - Real-time market alerts

## Autonomous Agent

The autonomous agent provides AI-powered betting decisions with full reasoning chains:

```python
from walters_autonomous_agent import WaltersCognitiveAgent

agent = WaltersCognitiveAgent(initial_bankroll=10000)
decision = await agent.make_autonomous_decision(game_data)

# View reasoning chain
for step in decision.reasoning_chain:
    print(f"{step.description}: {step.confidence}")
```

### Agent Capabilities
- Multi-step reasoning with evidence tracking
- Pattern recognition from historical data
- Portfolio risk analysis
- Meta-learning from past decisions
- XGBoost and Random Forest models
- Optional PyTorch deep learning

## Documentation

- `docs/billy_walters_cheat_card.md` - Quick reference guide
- `docs/advanced-master-class-section-*.md` - Detailed methodology
- `docs/Billy Walters Sports Betting SDK – Comprehensive Data Integration.docx` - Full integration guide

## Educational Purpose

This software is for educational and research purposes only. Sports betting involves substantial risk of financial loss. Always bet responsibly and within your means.

## License

Educational use only. Not for commercial wagering operations.
