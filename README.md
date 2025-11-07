# Billy Walters Sports Analyzer (Ultimate Edition)

**The most comprehensive Billy Walters-inspired sports betting analysis system combining real-time data ingestion, professional analysis, and AI-powered decision making.**

## 🚀 What's New - Ultimate Edition Features

### 🤖 Claude Desktop Integration (NEW!)
- **MCP Server**: Full Claude Desktop integration with 6 analysis tools
- **Autonomous Agent**: Self-learning AI with 5-step reasoning chains
- **Real-time Analysis**: Sharp money detection and market monitoring
- **Portfolio Optimization**: Risk management and Kelly Criterion sizing

### 🧠 Core Capabilities
- **Billy Walters Methodology**: Complete implementation of proven betting strategies
- **Data Ingestion**: Chrome DevTools scraping + multi-source research engine
- **Advanced Analysis**: Power ratings, key numbers, injury impacts, weather
- **Machine Learning**: XGBoost, Random Forest, optional PyTorch neural networks
- **Backtesting**: Historical validation with performance metrics

### 📊 System Components
- **CLI**: `walters-analyzer` with `wk-card`, `scrape-overtime`, and `scrape-injuries` commands
- **MCP Server**: Claude Desktop tools for AI-powered analysis
- **Autonomous Agent**: Self-learning betting agent with reasoning chains
- **Billy Walters Valuation**: Position-specific injury impacts and market inefficiencies
- **Cards**: JSON betting card snapshots in `./cards/`
- **Scrapers**: Real-time odds and injury data collection
- **Research Engine**: AccuWeather, Highlightly, ProFootballDoc integration

## Billy Walters Methodology

This system implements Billy Walters' sophisticated approach to injury impact analysis:

- **Position-Specific Valuations**: Elite QB = 3.5-4.5 pts, Elite RB = 2.5 pts, WR1 = 1.8 pts, etc.
- **Injury Capacity Multipliers**: OUT = 0%, Questionable = 92%, Hamstring = 70%, Ankle = 80%
- **Market Inefficiency Detection**: Markets typically underreact by 15% to injuries
- **Position Group Crisis Analysis**: Multiple injuries to same unit compound (O-line, secondary, etc.)
- **Recovery Timeline Tracking**: Hamstring = 14 days, Ankle = 10 days, ACL = 270 days
- **Historical Win Rates**: 3+ point edge = 64% win rate, 2-3 pts = 58%, 1-2 pts = 54%

### Key Advantages Over Generic Systems

| Generic Approach | Billy Walters Approach |
|-----------------|------------------------|
| "QB OUT! (+10 pts)" | "Mahomes ankle: 65% capacity (-1.2 of 3.5 pts)" |
| "High injuries - be cautious" | "Edge: 3.2 pts. Historical: 64% win rate. Bet 2% bankroll" |
| Position counts only | Specific point spread impacts |
| No market analysis | Market inefficiency detection |
| No bet sizing | Kelly Criterion bet sizing |

## Setup

### 1. Install Dependencies
```powershell
# Windows PowerShell
uv sync
uv sync --extra scraping  # Optional: additional scraping utilities
uv sync --extra dev       # Optional: development tools (pytest, ruff, coverage)
uv sync --extra ai        # NEW! All AI/ML features (MCP + Autonomous Agent)
uv sync --extra mcp       # NEW! MCP Server only (Claude Desktop integration)
uv sync --extra ml        # NEW! Machine Learning only (scikit-learn, xgboost)
uv sync --extra dl        # NEW! Deep Learning (PyTorch)
uv sync --extra research  # NEW! Research API integrations
```

```bash
# WSL/Linux
uv sync
uv sync --extra scraping  # Optional: additional scraping utilities
uv sync --extra dev       # Optional: development tools (pytest, ruff, coverage)
uv sync --extra ai        # NEW! All AI/ML features (MCP + Autonomous Agent)
uv sync --extra mcp       # NEW! MCP Server only (Claude Desktop integration)
uv sync --extra ml        # NEW! Machine Learning only (scikit-learn, xgboost)
uv sync --extra dl        # NEW! Deep Learning (PyTorch)
uv sync --extra research  # NEW! Research API integrations
```

### 2. Install Playwright Browsers
```powershell
# Required for web scraping
uv run playwright install chromium
```

### 3. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
# Edit .env with your overtime.ag credentials and optional proxy
```

Required environment variables:
- `OV_CUSTOMER_ID`: Your overtime.ag customer ID
- `OV_CUSTOMER_PASSWORD`: Your overtime.ag password

Optional (recommended for stealth):
- `PROXY_URL`: Your residential proxy for Cloudflare bypass and IP rotation

**Proxy Setup:** See [PROXY_SETUP.md](PROXY_SETUP.md) for complete proxy configuration guide including:
- Residential proxy setup (10 rotating IPs)
- Cloudflare bypass configuration
- IP verification and monitoring
- Troubleshooting proxy issues

### 4. Running Tests (Optional)
```bash
# Install dev dependencies first
uv sync --extra dev

# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=walters_analyzer --cov=scrapers
```

## Usage

### WK-Card (Betting Card Analysis)
```powershell
# Preview card (dry-run)
uv run walters-analyzer wk-card --file .\cards\wk-card-2025-10-31.json --dry-run

# Execute card
uv run walters-analyzer wk-card --file .\cards\wk-card-2025-10-31.json
```

### Scrape Overtime.ag Odds

#### Pre-Game Odds
```powershell
# Scrape both NFL and College Football (default)
uv run walters-analyzer scrape-overtime

# Scrape NFL only
uv run walters-analyzer scrape-overtime --sport nfl

# Scrape College Football only
uv run walters-analyzer scrape-overtime --sport cfb

# Custom output directory
uv run walters-analyzer scrape-overtime --output-dir ./my_data
```

#### Live Betting Odds
```powershell
# Scrape live betting odds
uv run walters-analyzer scrape-overtime --live
```

### Scrape ESPN Injury Reports

Critical for gate checks - track player injury status (Out, Doubtful, Questionable, Probable):

```powershell
# Scrape College Football injuries (default)
uv run walters-analyzer scrape-injuries --sport cfb

# Scrape NFL injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Custom output directory
uv run walters-analyzer scrape-injuries --sport cfb --output-dir ./injury_data
```

**Why Injuries Matter:**
- Key player absences significantly impact point spreads
- Starting QB injuries can move lines 3-7 points
- Essential gate check before placing any wager

See [INJURY_SCRAPER.md](INJURY_SCRAPER.md) for complete documentation, gate integration examples, and position impact guidelines.

### Billy Walters Analysis Scripts

Two powerful analysis scripts using the Billy Walters methodology:

```bash
# Combined game + injury analysis (MAIN TOOL)
uv run python analyze_games_with_injuries.py

# Position-based injury analysis
uv run python analyze_injuries_by_position.py
```

**What You Get:**
- Specific point spread impacts (not generic scores)
- Injury capacity percentages (Questionable = 92%, Hamstring = 70%)
- Market inefficiency detection (15% underreaction factor)
- Position group crisis alerts (O-line depleted, secondary crisis)
- Recovery timeline estimates
- Betting recommendations with historical win rates
- Kelly Criterion bet sizing (0.5-3% of bankroll)

### Output Files

**Organized by source and sport:**

**Injury Data (ESPN):**
- **NFL:** `data/injuries/nfl/nfl-injuries-{timestamp}.jsonl` and `.parquet`
- **NCAAF:** `data/injuries/ncaaf/ncaaf-injuries-{timestamp}.jsonl` and `.parquet`

**Odds Data (overtime.ag via Chrome DevTools):**
- **NFL:** `data/odds/nfl/nfl-odds-{timestamp}.jsonl`, `.json`, and `.csv`
- **NCAAF:** `data/odds/ncaaf/ncaaf-odds-{timestamp}.jsonl`, `.json`, and `.csv`

### Data Schema
Each game record includes:
- `source`: "overtime.ag"
- `sport`: "nfl" or "college_football"
- `league`: "NFL" or "NCAAF"
- `rotation_number`: e.g., "451-452"
- `event_date`: ISO date (e.g., "2025-11-02")
- `event_time`: Game time with timezone (e.g., "1:00 PM ET")
- `away_team`, `home_team`: Team names
- `spread_away_line`, `spread_away_price`: Spread for away team
- `spread_home_line`, `spread_home_price`: Spread for home team
- `total_over_line`, `total_over_price`: Over total
- `total_under_line`, `total_under_price`: Under total
- `moneyline_away_price`, `moneyline_home_price`: Moneyline odds
- `is_live`: Boolean (true for live betting, false for pre-game)
- `quarter`, `clock`: Game state for live betting

## Direct Scrapy Commands (Advanced)

```powershell
# Pre-game odds spider
scrapy crawl pregame_odds -a sport=both

# Live betting spider
scrapy crawl overtime_live

# With custom settings
scrapy crawl pregame_odds -a sport=nfl -s OVERTIME_OUT_DIR=./custom_output
```

## Troubleshooting

### Login Issues
- Ensure `OV_CUSTOMER_ID` and `OV_CUSTOMER_PASSWORD` are set in `.env`
- Check that credentials are correct by logging in manually at https://overtime.ag
- Check logs for "Login successful" message

### Playwright Issues
- Run `uv run playwright install chromium` if you see browser errors
- On WSL, you may need: `sudo apt install libgbm1 libgtk-3-0 libasound2`

### Scraping Issues
- Check `snapshots/` directory for debug screenshots
- Review logs for timeout or selector errors
- Ensure stable internet connection
- **Blocked by Cloudflare?** Configure a residential proxy (see [PROXY_SETUP.md](PROXY_SETUP.md))

### Proxy Issues
- See [PROXY_SETUP.md](PROXY_SETUP.md) for complete troubleshooting guide
- Verify proxy with: `curl -x "http://user:pass@proxy:port" "https://ipinfo.io/json"`
- Check logs for "Proxy IP verified" message
- Ensure `PROXY_URL` is set correctly in `.env`

## 🤖 Claude Desktop Integration (NEW!)

### MCP Server Setup

The MCP server provides AI-powered analysis tools directly in Claude Desktop.

**Quick Start:**
```bash
# Install MCP dependencies
uv sync --extra mcp

# Set environment variables
export WALTERS_API_KEY="your_key"
export ACCUWEATHER_API_KEY="your_key"
export HIGHLIGHTLY_API_KEY="your_key"

# Start MCP server
uv run python .claude/walters_mcp_server.py
```

**Configure Claude Desktop:**
1. Copy `.claude/claude-desktop-config.json` settings to your Claude Desktop config
2. Location: `~/.config/Claude/claude_desktop_config.json` (Linux/Mac)
3. Restart Claude Desktop
4. MCP tools will be available automatically

**Available Tools:**
- `analyze_game` - Comprehensive game analysis with Billy Walters methodology
- `find_sharp_money` - Monitor games for sharp betting patterns
- `calculate_kelly_stake` - Calculate optimal bet sizing using Kelly Criterion
- `backtest_strategy` - Test betting strategies on historical data
- `get_injury_report` - Get comprehensive injury analysis for a team
- `get_market_alerts` - Retrieve active betting alerts and opportunities

**Example Usage in Claude Desktop:**
```
Analyze the Chiefs vs Bills game with -2.5 spread
```

Claude will automatically use the `analyze_game` tool to provide:
- Power rating analysis
- Key number edge detection
- Sharp money indicators
- Injury and weather impacts
- Kelly Criterion bet sizing
- Expected value calculation

See [.claude/README.md](.claude/README.md) for complete MCP server documentation.

## 🧠 Autonomous Agent (NEW!)

### Self-Learning Betting Agent with Reasoning Chains

The autonomous agent makes decisions with full transparency, showing you exactly how it arrives at each recommendation.

**Setup:**
```bash
# Install ML dependencies
uv sync --extra ml

# Optional: Install PyTorch for deep learning
uv sync --extra dl
```

**Quick Example:**
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
    'opening_spread': -3.5,
    'public_percentage': 68,
    'money_percentage': 45
}

decision = await agent.make_autonomous_decision(game_data)

# View reasoning chain
print(f"Recommendation: {decision.recommendation}")
print(f"Confidence: {decision.confidence.name}")
print(f"Stake: {decision.stake_percentage:.1f}% of bankroll")
print(f"Expected Value: {decision.expected_value:.2f}%")

for step in decision.reasoning_chain:
    print(f"\nStep {step.step_number}: {step.description}")
    print(f"  Confidence: {step.confidence:.1%}")
    print(f"  Evidence: {', '.join(step.evidence)}")
    print(f"  Impact: {step.impact_on_decision}")
```

**5-Step Reasoning Process:**
1. **Power Rating Analysis** - Team strength and predicted spread
2. **Market Efficiency Check** - Line movement and sharp money indicators
3. **Situational Analysis** - Rest, travel, motivation factors
4. **Historical Pattern Matching** - Similar games and outcomes
5. **Portfolio Risk Analysis** - Correlation and position sizing

**Machine Learning Features:**
- **XGBoost** for game outcome prediction
- **Random Forest** for value estimation
- **Pattern Recognition** engine with similarity matching
- **Meta Learning** system that learns from past decisions
- **Optional PyTorch** neural networks for advanced pattern matching

**Portfolio Management:**
- Correlation analysis to avoid overexposure
- Value at Risk (VaR) calculation at 95% confidence
- Position sizing optimization
- Maximum drawdown tracking

**Memory System:**
- Short-term memory (last 100 decisions)
- Long-term categorized storage
- Similar decision recall
- Performance learning and strategy refinement

See [.claude/README.md](.claude/README.md) for complete autonomous agent documentation.

## 📚 Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Claude Desktop                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Chat UI    │  │    Tools     │  │   Prompts    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
└─────────────────────────────┬──────────────────────────┘
                              │ MCP Protocol
┌─────────────────────────────┴──────────────────────────┐
│                      MCP Server                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │          WaltersMCPEngine                        │  │
│  │  • analyze_game    • find_sharp_money            │  │
│  │  • kelly_stake     • backtest_strategy           │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                       │
│  ┌──────────────┴───────────────────────────────────┐  │
│  │    WaltersSportsAnalyzer (Core)                  │  │
│  │  • Power Ratings  • Bankroll Management          │  │
│  │  • Key Numbers    • Risk Analysis                │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                       │
│  ┌──────────────┴───────────────────────────────────┐  │
│  │         Data Ingestion & Research                │  │
│  │  • Chrome DevTools    • AccuWeather              │  │
│  │  • Highlightly        • ProFootballDoc           │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────┴──────────────────────────┐
│         Autonomous Agent (Optional)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │       WaltersCognitiveAgent                      │  │
│  │  • 5-Step Reasoning    • XGBoost/RandomForest    │  │
│  │  • Pattern Recognition • Portfolio Optimization  │  │
│  │  • Meta Learning       • Memory System           │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 📖 Documentation

### Core Documentation
- [README.md](README.md) - This file (main documentation)
- [INTEGRATION_ANALYSIS.md](INTEGRATION_ANALYSIS.md) - Integration architecture and strategy
- [.claude/README.md](.claude/README.md) - MCP server and autonomous agent guide

### Methodology & Guides
- [BILLY_WALTERS_METHODOLOGY.md](BILLY_WALTERS_METHODOLOGY.md) - Complete Billy Walters approach
- [QUICKSTART.md](QUICKSTART.md) - Fast start guide
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Detailed usage instructions

### Specialized Guides
- [INJURY_SCRAPER.md](INJURY_SCRAPER.md) - Injury data collection and analysis
- [PROXY_SETUP.md](PROXY_SETUP.md) - Proxy configuration for scraping
- [CHROME_DEVTOOLS_BREAKTHROUGH.md](CHROME_DEVTOOLS_BREAKTHROUGH.md) - Advanced scraping techniques

### Testing & Validation
- [TESTING_QUICK_START.md](TESTING_QUICK_START.md) - Testing guide
- [BACKTEST_RESULTS_SUMMARY.md](BACKTEST_RESULTS_SUMMARY.md) - Historical performance
- [DATA_QUALITY_REVIEW.md](DATA_QUALITY_REVIEW.md) - Data validation

## ⚠️ Educational Purpose & Risk Warning

This system is designed for **educational and research purposes only**.

**Important Notes:**
- Sports betting involves substantial risk of financial loss
- Past performance does not guarantee future results
- The system includes safety features (paper trading mode, loss limits, bet size caps)
- Always bet responsibly and within your means
- This is not financial advice

**Safety Features Built-In:**
- Paper trading mode enabled by default
- Daily loss limits (5% of bankroll)
- Maximum bet size limits (3% per bet)
- Confirmation required for all bets
- Real-time risk monitoring

## Collaboration Permissions Quick Checklist

- Keep the repository private and restrict collaborators to the two active maintainers.
- Issue fine-grained personal access tokens (PATs) scoped only to `billy-walters-sports-analyzer` when command-line or API access is required.
- Grant PAT permissions strictly aligned with needed features (e.g., contents, issues, pull requests, workflows, administration).
- Audit PATs and GitHub App installations periodically, revoking any tokens or integrations that are no longer in use.
