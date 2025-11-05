# Billy Walters Sports Analyzer SDK

**For educational research only. Not for real wagering.**

This SDK models Billy Walters' analytical methodology — power ratings,
line value, and disciplined bankroll management — with data integrations
for weather and injuries.

## Quickstart

```bash
# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .

# Run CLI
uv run walters --help
```

### Environment
The SDK reads directly from your **system environment variables**.
Only one key is required for live integrations:

```plaintext
ACCUWEATHER_API_KEY
```

If you’ve already set it globally in Windows, no `.env` file is needed.

```powershell
# Example (PowerShell)
setx ACCUWEATHER_API_KEY "your_api_key_here"
```

Restart your terminal after setting it.

## Package Structure

```
src/walters/
├── core/           # Core analysis components
│   ├── models.py          # Data models
│   ├── cache.py           # Caching system
│   ├── http_client.py     # HTTP client
│   ├── analyzer.py        # Main analyzer
│   ├── power_ratings.py   # Power rating engine
│   ├── bet_sizing.py      # Bet sizing calculator
│   ├── key_numbers.py     # Key number analysis
│   └── ...
├── research/       # Research and data gathering
│   ├── engine.py          # Research engine
│   └── scrapy_bridge.py   # Scrapy integration
├── backtest/       # Backtesting framework
│   ├── engine.py          # Backtest engine
│   ├── metrics.py         # Performance metrics
│   └── validation.py      # Strategy validation
├── cli/            # Command-line interface
│   └── cli.py
└── integrations/   # External integrations
    └── overtime_loader.py

scrapers/           # Scrapy spiders (root level)
├── overtime_live/
└── vi_spider/

scripts/            # Utility scripts (root level)
examples/           # Example code (root level)
tests/              # Tests (root level)
```

## Usage

```python
# Import core components
from walters.core import models, analyzer
from walters.research import ResearchEngine, ScrapyBridge
from walters.backtest import BacktestEngine

# Run scrapy spiders
uv run python -m scrapy crawl overtime_live
```

## Scrapy Spiders

Run spiders to collect data:

```bash
# List available spiders
uv run python -m scrapy list

# Run overtime live betting spider
uv run python -m scrapy crawl overtime_live \
  -a clickmap=clickmaps/nfl_clickmap.yaml \
  -O exports/nfl_game.json

# Run injury spider
uv run python -m scrapy crawl espn_injuries

# Run Massey ratings spider
uv run python -m scrapy crawl massey_ratings
```
