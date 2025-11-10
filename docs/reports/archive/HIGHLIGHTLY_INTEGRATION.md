# Highlightly NFL/NCAA API Integration

Complete integration guide for the Highlightly API in the Billy Walters Sports Analyzer.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [CLI Usage](#cli-usage)
- [API Endpoints](#api-endpoints)
- [MCP Server Tools](#mcp-server-tools)
- [Data Storage](#data-storage)
- [Billy Walters Methodology Integration](#billy-walters-methodology-integration)
- [Examples](#examples)

## Overview

The Highlightly API provides comprehensive NFL and NCAA football data including:

- **Teams** - Team information and statistics
- **Matches** - Live scores, schedules, and detailed match data
- **Odds** - Prematch and live odds from multiple bookmakers
- **Players** - Player profiles and season statistics
- **Highlights** - Video highlights and game recaps
- **Standings** - League and conference standings
- **Historical Data** - Head-to-head matchups and recent form
- **Injuries** - Match-level injury reports
- **Weather** - Venue and weather information
- **Lineups** - Starting lineups by match

**API Documentation**: https://highlightly.net/documentation/american-football/

## Setup

### 1. API Key Configuration

The API key is already configured in your `.env` file:

```bash
HIGHLIGHTLY_API_KEY=e674f79b-ad6f-47cb-88da-7895183dcbe8
```

### 2. Install Dependencies

The integration uses existing dependencies:

```powershell
uv sync --extra research  # Includes httpx for async requests
```

### 3. Verify Installation

Test the API connection:

```powershell
uv run walters-analyzer scrape-highlightly --endpoint teams --sport nfl
```

## CLI Usage

### Basic Command Structure

```bash
uv run walters-analyzer scrape-highlightly --endpoint <ENDPOINT> --sport <SPORT> [OPTIONS]
```

### Available Endpoints

| Endpoint | Description | Required Arguments |
|----------|-------------|-------------------|
| `teams` | Get team information | None |
| `matches` | Get match schedules | None |
| `odds` | Get betting odds | None (match-id recommended) |
| `bookmakers` | Get bookmaker list | None |
| `highlights` | Get video highlights | None |
| `standings` | Get standings | None |
| `lineups` | Get team lineups | `--match-id` |
| `players` | Get player profiles | None |
| `last-five` | Get recent games | `--team-id` |
| `head-to-head` | Get H2H history | `--team-id` and `--team-id-two` |
| `all` | Get all available data | None |

### Command Options

```
--endpoint          Endpoint to scrape (required)
--sport            nfl, ncaaf, or both (default: both)
--date             Date filter YYYY-MM-DD (matches, highlights)
--match-id         Match ID (odds, lineups, match details)
--team-id          Team ID (statistics, last-five)
--team-id-two      Second team ID (head-to-head)
--name             Search by name (teams, players)
--season           Season year filter
--odds-type        prematch or live (default: prematch)
--output-dir       Custom output directory
```

## API Endpoints

### Teams

Get team information and statistics.

```powershell
# Get all NFL teams
uv run walters-analyzer scrape-highlightly --endpoint teams --sport nfl

# Search for specific team
uv run walters-analyzer scrape-highlightly --endpoint teams --sport nfl --name "Chiefs"

# Get all teams (NFL and NCAA)
uv run walters-analyzer scrape-highlightly --endpoint teams --sport both
```

**Output**: `data/highlightly/nfl/teams-{timestamp}.jsonl`

### Matches

Get match schedules and live scores.

```powershell
# Get today's NFL matches
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --date 2024-11-08

# Get current week NCAA matches
uv run walters-analyzer scrape-highlightly --endpoint matches --sport ncaaf

# Get match details (includes venue, weather, injuries, events)
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --match-id 12345
```

**Output**: `data/highlightly/nfl/matches-{date}-{timestamp}.jsonl`

### Odds

Get betting odds from multiple bookmakers.

```powershell
# Get prematch odds for a specific match
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --match-id 12345

# Get live odds
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --match-id 12345 --odds-type live

# Get all odds for a date
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --date 2024-11-08
```

**Output**: `data/highlightly/nfl/odds-prematch-{match_id}-{timestamp}.jsonl`

**Markets Available**:
- Full Time Result (Home/Away/Draw)
- Moneyline (Home/Away)
- Totals (Over/Under)
- Odd or Even

### Bookmakers

Get list of available bookmakers.

```powershell
# Get all bookmakers
uv run walters-analyzer scrape-highlightly --endpoint bookmakers --sport nfl

# Search for specific bookmaker
uv run walters-analyzer scrape-highlightly --endpoint bookmakers --sport nfl --name "Stake.com"
```

**Output**: `data/highlightly/nfl/bookmakers-{timestamp}.jsonl`

### Highlights

Get video highlights and game recaps.

```powershell
# Get highlights for a date
uv run walters-analyzer scrape-highlightly --endpoint highlights --sport nfl --date 2024-11-08

# Get highlights for specific match
uv run walters-analyzer scrape-highlightly --endpoint highlights --sport nfl --match-id 12345
```

**Output**: `data/highlightly/nfl/highlights-{date}-{timestamp}.jsonl`

**Types**:
- `VERIFIED` - Official sources (1-48 hours after game)
- `UNVERIFIED` - Real-time user uploads

### Standings

Get league and conference standings.

```powershell
# Get current NFL standings
uv run walters-analyzer scrape-highlightly --endpoint standings --sport nfl

# Get specific conference (NFC, AFC)
uv run walters-analyzer scrape-highlightly --endpoint standings --sport nfl --season 2024
```

**Output**: `data/highlightly/nfl/standings-{season}-{timestamp}.jsonl`

### Lineups

Get starting lineups for a match.

```powershell
# Get lineups (requires match ID)
uv run walters-analyzer scrape-highlightly --endpoint lineups --sport nfl --match-id 12345
```

**Output**: `data/highlightly/nfl/lineups-{match_id}-{timestamp}.jsonl`

### Players

Get player profiles and statistics.

```powershell
# Get all players
uv run walters-analyzer scrape-highlightly --endpoint players --sport nfl

# Search for specific player
uv run walters-analyzer scrape-highlightly --endpoint players --sport nfl --name "Patrick Mahomes"
```

**Output**: `data/highlightly/nfl/players-{name}-{timestamp}.jsonl`

**Statistics Categories**:
- General (games played, total yards, touchdowns)
- Defense (tackles, sacks, interceptions)
- Passing (attempts, completions, yards, TDs)
- Rushing (attempts, yards, TDs)
- Receiving (receptions, yards, TDs)
- Scoring (points, field goals, extra points)
- Punting/Kicking

### Last Five Games

Get recent form for a team.

```powershell
# Get last 5 finished games (requires team ID)
uv run walters-analyzer scrape-highlightly --endpoint last-five --sport nfl --team-id 92730
```

**Output**: `data/highlightly/nfl/last-five-{team_id}-{timestamp}.jsonl`

### Head-to-Head

Get historical matchups between two teams.

```powershell
# Get H2H history (requires both team IDs)
uv run walters-analyzer scrape-highlightly --endpoint head-to-head --sport nfl --team-id 92730 --team-id-two 92731
```

**Output**: `data/highlightly/nfl/head-to-head-{team1}-vs-{team2}-{timestamp}.jsonl`

### All Endpoints

Scrape all available data at once.

```powershell
# Get comprehensive data for both leagues
uv run walters-analyzer scrape-highlightly --endpoint all --sport both
```

## MCP Server Tools

The Highlightly integration provides 6 new tools for Claude Desktop analysis.

### get_highlightly_teams

Get team information.

```
Get NFL teams list

Args:
  league: NFL or NCAA
  name: Optional team name filter
```

**Example Usage in Claude Desktop**:
```
Show me all NFL teams
```

### get_highlightly_match_data

Get comprehensive match data including venue, weather, injuries, and odds.

```
Get comprehensive match data for match ID 12345

Args:
  match_id: Match ID from Highlightly
  include_odds: Include odds from multiple bookmakers (default: true)
```

**Example Usage in Claude Desktop**:
```
Analyze match 12345 with all available data
```

### get_highlightly_player_stats

Get player statistics and profile.

```
Get Patrick Mahomes statistics

Args:
  player_name: Player name to search
```

**Example Usage in Claude Desktop**:
```
Show me Patrick Mahomes stats for the last 3 seasons
```

### get_highlightly_historical_matchups

Get head-to-head and recent form for pattern recognition.

```
Get H2H and recent form

Args:
  team_id_one: First team ID
  team_id_two: Second team ID
```

**Example Usage in Claude Desktop**:
```
Compare Chiefs vs Bills recent performance and head-to-head
```

### get_highlightly_odds_history

Get line movement analysis from multiple bookmakers.

```
Get odds comparison for match 12345

Args:
  match_id: Match ID
  bookmaker_name: Optional bookmaker filter
```

**Example Usage in Claude Desktop**:
```
Compare odds across bookmakers for this game
```

### backtest_with_highlightly

Enhanced backtesting with historical Highlightly data.

```
Backtest odds comparison strategy

Args:
  league: NFL or NCAA
  date: Date to backtest (YYYY-MM-DD)
  strategy: odds_comparison, sharp_detection, or weather_impact
```

**Example Usage in Claude Desktop**:
```
Backtest my strategy on NFL games from November 8th
```

## Data Storage

### Directory Structure

```
data/highlightly/
├── nfl/
│   ├── teams-20241108-120000.jsonl
│   ├── matches-2024-11-08-120000.jsonl
│   ├── odds-prematch-12345-120000.jsonl
│   ├── players-Mahomes-120000.jsonl
│   ├── standings-2024-120000.jsonl
│   └── highlights-2024-11-08-120000.jsonl
└── ncaaf/
    ├── teams-20241108-120000.jsonl
    ├── matches-2024-11-08-120000.jsonl
    └── ...
```

### File Format

All data is stored in JSONL format (one JSON object per line):

```jsonl
{"id": 1, "name": "Saints", "displayName": "New Orleans Saints", "abbreviation": "NO", "league": "NFL"}
{"id": 2, "name": "Chiefs", "displayName": "Kansas City Chiefs", "abbreviation": "KC", "league": "NFL"}
```

### Loading Data

```python
import orjson
from pathlib import Path

# Load JSONL file
filepath = Path("data/highlightly/nfl/teams-20241108-120000.jsonl")

teams = []
with open(filepath, 'rb') as f:
    for line in f:
        if line.strip():
            teams.append(orjson.loads(line))

print(f"Loaded {len(teams)} teams")
```

## Billy Walters Methodology Integration

### Multi-Book Odds Comparison

Highlightly provides odds from multiple bookmakers, enabling:

1. **Best Line Shopping** - Find the best available odds
2. **Sharp Money Detection** - Compare sharp vs public books
3. **Market Inefficiency** - Identify discrepancies between books
4. **CLV Tracking** - Compare entry odds to closing lines

**Example Workflow**:

```powershell
# 1. Get odds from multiple bookmakers
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --match-id 12345

# 2. Compare to overtime.ag odds
uv run walters-analyzer scrape-overtime --sport nfl

# 3. Analyze in Claude Desktop
"Compare Highlightly odds to overtime.ag for arbitrage opportunities"
```

### Historical Backtesting

Use Highlightly's comprehensive historical data for:

1. **Pattern Recognition** - Head-to-head and last-five games
2. **Weather Impact** - Venue and weather data
3. **Injury Analysis** - Match-level injury reports
4. **Performance Validation** - Backtest Billy Walters methodology

**Example Workflow**:

```powershell
# Get historical matches with complete data
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --date 2024-10-01

# Get odds history
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --date 2024-10-01

# Backtest in Claude Desktop
"Backtest power ratings on October 1st NFL games using Highlightly data"
```

### Enhanced Player Analysis

Player statistics for power rating adjustments:

1. **Season Trends** - Performance by season and coverage
2. **Position-Specific Stats** - Defense, passing, rushing, receiving
3. **Team Context** - Stats broken down by team

**Example Workflow**:

```powershell
# Get player stats
uv run walters-analyzer scrape-highlightly --endpoint players --sport nfl --name "Josh Allen"

# Analyze in Claude Desktop
"How has Josh Allen's performance changed over the last 3 seasons?"
```

### Injury Cross-Validation

Compare multiple injury sources:

1. **ESPN Scraper** - Real-time injury reports
2. **Highlightly API** - Match-level injury data
3. **Cross-Validation** - Verify accuracy across sources

**Example Workflow**:

```powershell
# Get ESPN injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Get Highlightly match data with injuries
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --match-id 12345

# Compare in Claude Desktop
"Cross-validate injury reports from ESPN and Highlightly"
```

## Examples

### Example 1: Pre-Game Analysis

Comprehensive pre-game analysis using Highlightly data:

```powershell
# Step 1: Get match data
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --date 2024-11-08

# Step 2: Get specific match details (use match ID from step 1)
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --match-id 12345

# Step 3: Get odds from multiple bookmakers
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --match-id 12345

# Step 4: Get team history
uv run walters-analyzer scrape-highlightly --endpoint head-to-head --sport nfl --team-id 92730 --team-id-two 92731
```

**Claude Desktop Analysis**:
```
Analyze the Chiefs vs Bills game:
1. Compare odds across bookmakers
2. Review head-to-head history
3. Check injury reports
4. Assess weather impact
5. Provide betting recommendation
```

### Example 2: Player Research

Deep dive into player performance:

```powershell
# Get player stats
uv run walters-analyzer scrape-highlightly --endpoint players --sport nfl --name "Patrick Mahomes"
```

**Claude Desktop Analysis**:
```
Analyze Patrick Mahomes:
1. Performance trends over last 3 seasons
2. Home vs away splits
3. Impact of key injuries
4. Playoff performance
```

### Example 3: Multi-Book Arbitrage

Find arbitrage opportunities:

```powershell
# Get all bookmakers
uv run walters-analyzer scrape-highlightly --endpoint bookmakers --sport nfl

# Get odds for specific match from all bookmakers
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --match-id 12345
```

**Claude Desktop Analysis**:
```
Find arbitrage opportunities:
1. Compare all bookmaker odds
2. Calculate arbitrage percentage
3. Identify profitable combinations
4. Recommend bet sizing
```

### Example 4: Historical Backtesting

Validate betting strategies:

```powershell
# Get historical data for date range
for date in 2024-10-01 2024-10-08 2024-10-15; do
    uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --date $date
    uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --date $date
done
```

**Claude Desktop Analysis**:
```
Backtest my strategy:
1. Load historical matches and odds
2. Apply Billy Walters power ratings
3. Calculate expected vs actual results
4. Generate performance report
```

### Example 5: Live Game Monitoring

Monitor line movements during games:

```powershell
# Get live odds
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --match-id 12345 --odds-type live

# Compare to prematch
uv run walters-analyzer scrape-highlightly --endpoint odds --sport nfl --match-id 12345 --odds-type prematch
```

**Claude Desktop Analysis**:
```
Analyze live line movements:
1. Compare current odds to opening lines
2. Identify sharp money indicators
3. Calculate CLV opportunities
4. Recommend live betting actions
```

## Rate Limits

Monitor your API usage through response headers:

```
x-ratelimit-requests-limit: Total requests allowed per day
x-ratelimit-requests-remaining: Remaining requests
```

The client automatically displays remaining requests after each call.

## Troubleshooting

### API Key Issues

```powershell
# Verify API key is set
echo $env:HIGHLIGHTLY_API_KEY

# If missing, add to .env file
HIGHLIGHTLY_API_KEY=your_key_here
```

### Connection Errors

```powershell
# Test basic connectivity
uv run walters-analyzer scrape-highlightly --endpoint bookmakers --sport nfl
```

### Data Not Found

Some endpoints require specific parameters:

```
- lineups: Requires --match-id
- last-five: Requires --team-id
- head-to-head: Requires --team-id and --team-id-two
```

### MCP Server Not Loading

Restart Claude Desktop after updating MCP server:

1. Close Claude Desktop completely
2. Restart Claude Desktop
3. Verify tools are available: "Show me available Highlightly tools"

## Additional Resources

- **Highlightly Documentation**: https://highlightly.net/documentation/american-football/
- **OpenAPI Spec**: `.claude/openapi.json`
- **Billy Walters Methodology**: `BILLY_WALTERS_METHODOLOGY.md`
- **MCP Server Guide**: `.claude/README.md`

## Support

For issues or questions:

1. Check existing documentation
2. Review error messages and logs
3. Test individual endpoints
4. Verify API key and connectivity
5. Check rate limits

---

**Integration Complete** ✅

The Highlightly NFL/NCAA API is fully integrated into the Billy Walters Sports Analyzer with CLI commands, MCP server tools, and comprehensive data storage for historical backtesting and real-time analysis.

