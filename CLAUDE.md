# Billy Walters Sports Analyzer - Development Guidelines

This document contains critical information about working with the Billy Walters Sports Analyzer codebase. Follow these guidelines precisely.

## Project Overview

This is a **football-focused sports analytics and betting analysis system** (NFL & NCAAF) inspired by Billy Walters' analytical approach. The project integrates weather data, AI-powered analysis, odds tracking, and statistical modeling to provide comprehensive insights for informed decision-making.

### Sports Focus
- **NFL** (National Football League)
- **NCAAF** (NCAA College Football)

### Existing Components
- **MCP Server** (walters_mcp_server.py) - Model Context Protocol server for tool integration
- **Autonomous Agent** (walters_autonomous_agent.py) - Automated analysis agent
- **PRD** (billy_walters_analytics_prd.md) - Product requirements document

## Core Development Rules

### 1. Package Management
- ONLY use uv, NEVER pip
- Installation: `uv add package`
- Running tools: `uv run tool`
- Upgrading: `uv add --dev package --upgrade-package package`
- FORBIDDEN: `uv pip install`, `@latest` syntax

### 2. Code Quality
- Type hints required for all code
- Use pyright for type checking
  - Run `uv run pyright` after every change and fix resulting errors
- Public APIs must have docstrings
- Functions must be focused and small
- Follow existing patterns exactly
- Line length: 88 chars maximum

### 3. Testing Requirements
- Framework: `uv run pytest`
- Async testing: use anyio, not asyncio
- Coverage: test edge cases and errors
- New features require tests
- Bug fixes require regression tests
- Test with realistic NFL/NCAAF data and edge cases

### 4. Code Style
- PEP 8 naming (snake_case for functions/variables)
- Class names in PascalCase
- Constants in UPPER_SNAKE_CASE
- Document with docstrings
- Use f-strings for formatting

## Environment Variables & API Keys

### Required Environment Variables

Store these in .env file (NEVER commit to git):

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Weather Services
ACCUWEATHER_API_KEY=...
OPENWEATHER_API_KEY=...

# Sports Data Sources
ACTION_USERNAME=...
ACTION_PASSWORD=...

# Overtime/OV Service
OV_CUSTOMER_ID=...
OV_PASSWORD=...
OV_LOGIN_URL=...
OV_STORAGE_STATE=...
OVERTIME_START_URL=...
OVERTIME_OUT_DIR=...
OVERTIME_PROXY=...
OVERTIME_LIVE_URL=...
OVERTIME_COMP=...

# Proxy Configuration
PROXY_URL=...
PROXY_USER=...
PROXY_PASS=...

# GitHub (for automation)
GITHUB_TOKEN=ghp_...

# Other Services
HIGHLIGHTLY_API_KEY=...

## MCP Server Integration

Your project includes a custom MCP server (walters_mcp_server.py) that provides:
- Sports data tools
- Weather integration
- Odds analysis capabilities
- AI-powered predictions

### Using the MCP Server

Start the MCP server:
`uv run python .claude/walters_mcp_server.py`

The server exposes tools that Claude Code can use via the Model Context Protocol.

## Autonomous Agent

The walters_autonomous_agent.py provides automated analysis capabilities:
- Scheduled game analysis
- Automated odds monitoring
- Weather impact calculations
- Value opportunity detection

## Football Analytics Best Practices

### 1. NFL-Specific Considerations
- **Week numbering**: Handle bye weeks correctly
- **Playoff formats**: Different playoff structure than regular season
- **Roster changes**: Track trades, injuries, suspensions
- **Home field advantage**: Quantify and factor in
- **Division games**: Historical rivalry and performance patterns
- **Weather impact**: Critical for outdoor stadiums (Buffalo, Green Bay, etc.)

### 2. NCAAF-Specific Considerations
- **Conference alignments**: Track conference changes
- **Bowl games**: Different dynamics than regular season
- **Talent disparity**: Larger skill gaps between teams
- **Home field advantage**: Often more significant than NFL
- **Roster turnover**: High due to graduations and transfers
- **Strength of schedule**: Varies widely across conferences

### 3. Weather Impact Analysis
- Wind speed >15 mph significantly affects passing
- Temperature <32°F affects ball handling
- Precipitation reduces scoring
- Track indoor vs outdoor stadium

### 4. Odds Analysis
- Store odds in decimal format for calculations
- Track line movements (opening line vs closing line)
- Monitor sharp action indicators
- Calculate implied probability vs true probability
- Identify value opportunities (positive expected value)

## API Integration Guidelines

### Weather APIs
- AccuWeather: 5-day forecasts, detailed conditions
- OpenWeather: Alternative forecast source, historical data
- Use both for redundancy and cross-validation

### AI Services
- Anthropic Claude: Matchup analysis, narrative generation
- OpenAI: Predictions, pattern recognition

### Sports Data
- Overtime API: Game data, scores, schedules
- Action Network: Betting lines, sharp action, odds movements

### Proxy Management
- Use PROXY_URL, PROXY_USER, PROXY_PASS for scraping
- Implement rotation for high-volume requests
- Respect rate limits

## Data Models

Use Pydantic for all data models:
- Game, Team, Stadium
- WeatherConditions
- OddsMovement
- PlayerStats
- League enum (NFL/NCAAF)

## Git Workflow

- Always use feature branches; do not commit directly to main
- Name branches descriptively: feat/weather-integration, fix/odds-calculation
- Create pull requests for all changes
- Use conventional commits: feat(nfl): add weather impact analysis

## Code Formatting

### Ruff
- Format: `uv run ruff format .`
- Check: `uv run ruff check .`
- Fix: `uv run ruff check . --fix`

### Type Checking
- Run `uv run pyright` after every change

## Security & Privacy

- NEVER commit API keys or credentials
- Add .env, .env.* to .gitignore
- Use environment variables for all sensitive data
- Rotate API keys if accidentally exposed

## Project Structure

billy-walters-sports-analyzer/
├── src/
│   ├── data/                    # Data collection (13 scrapers & clients)
│   │   ├── accuweather_client.py
│   │   ├── espn_api_client.py
│   │   ├── overtime_signalr_client.py
│   │   └── ...
│   ├── walters_analyzer/        # Core analysis system
│   │   ├── valuation/           # Edge detection & analysis
│   │   │   ├── billy_walters_edge_detector.py
│   │   │   ├── billy_walters_totals_detector.py
│   │   │   ├── analyze_games_with_injuries.py
│   │   │   └── analyze_injuries_by_position.py
│   │   ├── query/               # Display utilities
│   │   │   ├── check_game.py
│   │   │   ├── show_current_odds.py
│   │   │   └── watch_alerts.py
│   │   └── ...
│   └── db/                      # Database layer
├── scripts/                     # Operational scripts
│   ├── analysis/                # Weekly analysis (8 scripts)
│   ├── validation/              # Data validation (3 scripts)
│   ├── backtest/                # Backtesting (2 scripts)
│   ├── utilities/               # Helper scripts (5 scripts)
│   └── dev/                     # Development/deployment (14 scripts)
├── tests/                       # Test suite (146 tests)
│   └── test_validation_integration.py
├── examples/                    # Example scripts
├── .claude/
│   ├── walters_mcp_server.py
│   ├── walters_autonomous_agent.py
│   ├── billy_walters_analytics_prd.md
│   ├── hooks/
│   └── commands/
├── .env.example
├── .gitignore
├── CLAUDE.md
└── README.md

### Directory Guidelines

**When adding new files:**
- Data scrapers/clients → `src/data/`
- Edge detection/analysis → `src/walters_analyzer/valuation/`
- Query/display utilities → `src/walters_analyzer/query/`
- Weekly analysis scripts → `scripts/analysis/`
- Data validation → `scripts/validation/`
- Backtesting → `scripts/backtest/`
- Helper utilities → `scripts/utilities/`
- Dev/deployment → `scripts/dev/`
- Tests → `tests/`
- Examples → `examples/`

## Responsible Use

This is an analytical tool for educational/research purposes only.
Always gamble responsibly and within legal jurisdictions.

## Resources

- Billy Walters' Principles: Information edge, statistical modeling, disciplined bankroll management
- NFL Data: Pro Football Reference, NFL.com, ESPN
- NCAAF Data: Sports Reference CFB, ESPN, NCAA.com
- Weather: NOAA, Weather.gov
- Python Libraries: pandas, numpy, scikit-learn, httpx, pydantic, anthropic, openai
