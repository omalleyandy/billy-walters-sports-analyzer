# CLI Reference - Billy Walters Sports Analyzer

This document provides comprehensive reference for all CLI commands in the Billy Walters Sports Analyzer.

## Table of Contents
- [analyze-game](#analyze-game) - NEW! Full Billy Walters game analysis
- [wk-card](#wk-card) - Week card betting workflow
- [scrape-overtime](#scrape-overtime) - Scrape odds from overtime.ag
- [scrape-injuries](#scrape-injuries) - Scrape injury reports
- [scrape-highlightly](#scrape-highlightly) - Scrape data from Highlightly API
- [view-odds](#view-odds) - View scraped odds data
- [monitor-sharp](#monitor-sharp) - Monitor sharp money movements

---

## analyze-game

**NEW!** Analyze a single game using the complete Billy Walters methodology with bankroll-aware recommendations.

### Features
- Power rating-based predictions
- Injury impact analysis (point values)
- Key number detection (3, 7, 6, 10, 14)
- Kelly Criterion bankroll management
- Research integration (injuries, weather)
- Detailed recommendation output

### Usage

```bash
# Basic analysis with spread
uv run walters-analyzer analyze-game \
  --home "Philadelphia Eagles" \
  --away "Dallas Cowboys" \
  --spread -3.0

# Full analysis with research integration
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

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--home` | string | Yes | - | Home team name |
| `--away` | string | Yes | - | Away team name |
| `--spread` | float | No | - | Current spread (home perspective) |
| `--total` | float | No | - | Current total |
| `--home-price` | int | No | -110 | Home spread price (American odds) |
| `--away-price` | int | No | -110 | Away spread price (American odds) |
| `--venue` | string | No | - | Stadium/venue for weather lookup |
| `--date` | string | No | - | Game date (YYYY-MM-DD format) |
| `--bankroll` | float | No | 10000.0 | Starting bankroll amount |
| `--research` | flag | No | false | Fetch live injury/weather data |

### Example Output

```
================================================================================
BILLY WALTERS GAME ANALYSIS
================================================================================

Matchup:  Dallas Cowboys @ Philadelphia Eagles
Spread:   Philadelphia Eagles -3.0 (-110/-110)

HOME TEAM INJURIES:
  Total Impact: +0.4 pts
  • Player Name (QB): -2.5 pts
  • Player Name (WR): -1.2 pts

AWAY TEAM INJURIES:
  Total Impact: +0.5 pts
  • Player Name (CB): -1.8 pts
  • Player Name (LB): -0.7 pts

ANALYSIS:
  Predicted Spread: +0.1
  Market Spread:    -3.0
  Edge:             +3.1 pts
  Confidence:       High Confidence

KEY NUMBER ALERTS:
  [!] Projection crosses 3 (moving toward the underdog)

================================================================================
RECOMMENDATION: High Confidence
================================================================================
Bet Type:      SPREAD
Team:          Philadelphia Eagles
Edge:          +3.1 pts
Win Prob:      64.0%
Stake:         3.00% ($300.00)

Notes:
  • Net injury advantage: +0.1 pts
  • Predicted spread +0.1 vs market -3.0
  • Projection crosses 3 (moving toward the underdog)
```

### Confidence Levels

| Edge (pts) | Confidence Level | Kelly Stake |
|-----------|------------------|-------------|
| < 1.0 | No Play | 0% |
| 1.0-1.9 | Slight Edge | 0.5-1.5% |
| 2.0-2.9 | Elevated Confidence | 1.5-3.0% |
| ≥ 3.0 | High Confidence | 3.0% (max) |

### Research Integration

When `--research` flag is used:
1. **Injury Data**: Fetches from ProFootballDoc cache or live scraping
2. **Weather Data**: Queries AccuWeather API for venue conditions
3. **Point Values**: Each injury assigned point impact based on position/status

---

## wk-card

Run or preview a week card JSON with betting entries.

### NEW Features
- `--show-bankroll` - Display Kelly Criterion stake recommendations
- `--bankroll` - Specify starting bankroll amount

### Usage

```bash
# Basic preview
uv run walters-analyzer wk-card --file cards/week10.json --dry-run

# With bankroll display
uv run walters-analyzer wk-card \
  --file cards/week10.json \
  --dry-run \
  --show-bankroll \
  --bankroll 10000
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--file` | path | Yes | - | Path to week card JSON |
| `--dry-run` | flag | No | false | Preview without placing bets |
| `--show-bankroll` | flag | No | false | Show Kelly stake percentages |
| `--bankroll` | float | No | 10000.0 | Starting bankroll amount |

### Example Output

```
Wk-Card 2025-11-10 | source=manual | dry_run=True | Bankroll=$10,000.00
- 101 Philadelphia Eagles vs Dallas Cowboys
  spread: Eagles -3.0 (size=2u, max_juice=-110) → 2.50% ($250.00)
  moneyline: Eagles (max_price=-150, size=1u) → 1.20% ($120.00)
```

---

## scrape-overtime

Scrape odds from overtime.ag sportsbook.

### Usage

```bash
# Scrape NFL pre-game odds
uv run walters-analyzer scrape-overtime --sport nfl

# Scrape live betting odds
uv run walters-analyzer scrape-overtime --sport nfl --live

# Custom output directory
uv run walters-analyzer scrape-overtime \
  --sport both \
  --output-dir data/custom_odds
```

### Arguments

| Argument | Type | Choices | Default | Description |
|----------|------|---------|---------|-------------|
| `--sport` | string | nfl, cfb, both | both | Sport to scrape |
| `--live` | flag | - | false | Scrape live odds |
| `--output-dir` | path | - | auto | Output directory |

---

## scrape-injuries

Scrape injury reports from ESPN.

### Usage

```bash
# Scrape NFL injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Scrape college football injuries
uv run walters-analyzer scrape-injuries --sport cfb

# Custom output directory
uv run walters-analyzer scrape-injuries \
  --sport nfl \
  --output-dir data/custom_injuries
```

### Arguments

| Argument | Type | Choices | Default | Description |
|----------|------|---------|---------|-------------|
| `--sport` | string | nfl, cfb | cfb | Sport to scrape |
| `--output-dir` | path | - | auto | Output directory |

---

## scrape-highlightly

Scrape data from Highlightly API (requires API key).

### Usage

```bash
# Scrape teams
uv run walters-analyzer scrape-highlightly \
  --endpoint teams \
  --sport nfl

# Scrape today's matches
uv run walters-analyzer scrape-highlightly \
  --endpoint matches \
  --sport nfl \
  --date 2025-11-08

# Scrape odds for a specific match
uv run walters-analyzer scrape-highlightly \
  --endpoint odds \
  --sport nfl \
  --match-id 12345 \
  --odds-type prematch
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--endpoint` | string | Yes | API endpoint (teams, matches, odds, etc.) |
| `--sport` | string | No | Sport (nfl, ncaaf, both) |
| `--date` | string | No | Date filter (YYYY-MM-DD) |
| `--match-id` | int | No | Match ID for specific game |
| `--team-id` | int | No | Team ID for statistics |
| `--odds-type` | string | No | Odds type (prematch, live) |

---

## view-odds

View scraped odds data with filtering and export options.

### Usage

```bash
# View latest odds
uv run walters-analyzer view-odds

# View today's games
uv run walters-analyzer view-odds --today

# Filter by team
uv run walters-analyzer view-odds \
  --team "Eagles" \
  --upcoming 7

# Export to CSV
uv run walters-analyzer view-odds \
  --sport nfl \
  --upcoming 7 \
  --export odds_export.csv
```

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--data-dir` | path | Data directory (default: data/overtime_live) |
| `--file` | path | Specific JSONL file to load |
| `--sport` | string | Filter by sport (nfl, college_football) |
| `--date` | string | Filter by date (YYYY-MM-DD) |
| `--today` | flag | Show today's games |
| `--upcoming` | int | Show games in next N days |
| `--team` | string | Filter by team name (partial match) |
| `--compare` | string | Compare lines for a team |
| `--summary` | flag | Show summary only |
| `--brief` | flag | Brief output (no odds details) |
| `--export` | path | Export to CSV file |

---

## monitor-sharp

Monitor market for sharp money movements.

### Usage

```bash
# Test connection
uv run walters-analyzer monitor-sharp --test

# Monitor NFL for 2 hours
uv run walters-analyzer monitor-sharp \
  --sport nfl \
  --duration 120

# Monitor specific game
uv run walters-analyzer monitor-sharp \
  --sport nfl \
  --game-id "chiefs_bills_2025-11-10" \
  --duration 60 \
  --interval 30
```

### Arguments

| Argument | Type | Choices | Default | Description |
|----------|------|---------|---------|-------------|
| `--sport` | string | nfl, ncaaf, nba, mlb, nhl | nfl | Sport to monitor |
| `--game-id` | string | - | - | Specific game to monitor |
| `--duration` | int | - | 120 | Duration in minutes |
| `--interval` | int | - | settings | Check interval in seconds |
| `--test` | flag | - | false | Test API connection |

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# AccuWeather (for weather data)
ACCUWEATHER_API_KEY=your_key_here

# The Odds API (for sharp money monitoring)
ODDS_API_KEY=your_key_here

# Highlightly API (for odds tracking)
HIGHLIGHTLY_API_KEY=your_key_here
```

### Settings File

Customize behavior in `walters_analyzer/config/settings.py`:

```python
# Bankroll management
max_bet_pct = 3.0          # Maximum bet as % of bankroll
min_bet_pct = 0.5          # Minimum bet as % of bankroll
fractional_kelly = 0.5     # Use half-Kelly for safety

# Key numbers (NFL)
key_numbers = [3, 7, 6, 10, 14]

# Confidence thresholds
confidence_buckets = [
    (3.0, "High Confidence"),
    (2.0, "Elevated Confidence"),
    (1.0, "Slight Edge"),
]
```

---

## Best Practices

### 1. Daily Workflow

```bash
# Morning: Scrape fresh data
uv run walters-analyzer scrape-injuries --sport nfl
uv run walters-analyzer scrape-highlightly --endpoint matches --sport nfl --date $(date +%Y-%m-%d)

# Afternoon: Analyze games
uv run walters-analyzer analyze-game \
  --home "Team A" \
  --away "Team B" \
  --spread -3.5 \
  --research \
  --bankroll 10000

# Pre-game: Monitor for sharp moves
uv run walters-analyzer monitor-sharp --sport nfl --duration 60
```

### 2. Bankroll Management

- Start with fractional Kelly (50% of full Kelly)
- Max 3% of bankroll on any single bet
- Track performance and adjust over time
- Never chase losses

### 3. Research Integration

- Use `--research` flag for fresh injury/weather data
- Run scrapers daily to keep cache updated
- Verify critical injuries manually
- Check weather for outdoor games

### 4. Key Number Awareness

Pay special attention when analysis crosses key numbers:
- **3 & 7**: Most common NFL margins
- **6**: Two field goals
- **10**: Touchdown + field goal
- **14**: Two touchdowns

---

## Troubleshooting

### Missing Dependencies

```bash
# Install all optional dependencies
uv sync --all-extras

# Or install specific groups
uv pip install -e ".[scraping,mcp,ml]"
```

### API Key Issues

```bash
# Test AccuWeather
echo $ACCUWEATHER_API_KEY

# Test Odds API
uv run walters-analyzer monitor-sharp --test
```

### Encoding Issues (Windows)

If you see `UnicodeEncodeError`, ensure PowerShell uses UTF-8:

```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

## Support

For issues or questions:
1. Check this documentation
2. Review `docs/reports/INTEGRATION_ANALYSIS.md`
3. Check `AGENTS.md` for automation tips
4. Review logs in `logs/walters-analyzer.log`

