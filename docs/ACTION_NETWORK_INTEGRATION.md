# Action Network Data Integration Summary

## Date: November 26, 2025

## Discovery

Successfully obtained Action Network odds JSON data containing:
- **16 NFL Week 13 games** with full odds from multiple sportsbooks
- **Betting percentages** (tickets AND money) - the key to sharp money detection
- **Line movement** (opening vs current)
- **Consensus lines** aggregated across books

## Data Structure

The Action Network JSON format provides:

```
pageProps:
  allBooks: {439 sportsbooks with metadata}
  league: "nfl"
  scoreboardResponse:
    games: [{game data with teams, markets/odds}]
    
Each game includes:
  - teams: [{full_name, abbr, standings, logo}]
  - markets: {
      "15": consensus odds,
      "30": opening lines,
      "{book_id}": individual book odds
    }
    
Each market includes:
  - spread: [{side, value, odds, bet_info: {tickets, money}}]
  - moneyline: [{side, odds, bet_info}]
  - total: [{side, value, odds, bet_info}]
```

## Sharp Money Analysis

Identified **7 sharp money plays** with 5+ point divergence between tickets and money:

### Top Signals

| Game | Pick | Tickets | Money | Divergence |
|------|------|---------|-------|------------|
| KC @ DAL | DAL +3.5 | 70% | 85% | **+15** |
| NO @ MIA | MIA -6.0 | 67% | 82% | **+15** |
| MIN @ SEA | SEA -10.5 | 30% | 41% | **+11** |
| GB @ DET | GB +2.5 | 48% | 56% | **+8** |
| LV @ LAC | LAC -10.0 | 51% | 58% | **+7** |
| TB @ ARI | ARI -3.0 | 58% | 63% | **+5** |
| NYJ @ ATL | ATL +2.5 | 32% | 37% | **+5** |

### Billy Walters Methodology Alignment

This data directly enables:
1. **Sharp vs Public money detection** - The core Walters principle
2. **Line movement validation** - Confirm sharps moving lines
3. **Contrarian plays** - Fade public when money disagrees
4. **Line shopping** - Best lines across books

## Parser Implementation

Created `action_network_parser.py` in:
```
src/walters_analyzer/data_collection/action_network_parser.py
```

Features:
- `ActionNetworkParser` class for parsing JSON
- `BettingPercentages` dataclass with divergence calculations
- `get_sharp_plays()` method to identify signals
- `get_best_lines()` method for line shopping
- `to_summary_dict()` for data export

## Usage

```python
from walters_analyzer.data_collection.action_network_parser import ActionNetworkParser

parser = ActionNetworkParser()
games = parser.parse_file('action_network_odds.json')

# Get sharp plays
sharp_plays = parser.get_sharp_plays(min_divergence=5.0)

# Analyze individual game
for game in games:
    if game.spread_sharp_side:
        print(f"Sharp on: {game.spread_sharp_side}")
```

## Next Steps

1. **Automate data collection** - Scrape Action Network periodically
2. **Integrate with edge calculator** - Combine with power ratings
3. **Track CLV** - Record sharp plays and measure closing line value
4. **Historical analysis** - Backtest sharp signals

## Data Source

- URL structure: `https://www.actionnetwork.com/nfl/odds`
- Data embedded in page as `__NEXT_DATA__` JSON
- Requires parsing from HTML or API access
- Consider using Firecrawl MCP for structured extraction

## Files

- Parser: `src/walters_analyzer/data_collection/action_network_parser.py`
- Sample data: `data/action_network/action_network_week13_nfl.json`
