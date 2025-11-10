# Quick Start: Game Analysis with Billy Walters Methodology

This guide shows you how to quickly analyze NFL/NCAA games using the complete Billy Walters methodology.

## Installation

```bash
# Clone and setup
cd billy-walters-sports-analyzer
uv sync
```

## Basic Game Analysis (30 seconds)

Analyze any game with just the matchup and spread:

```bash
uv run walters-analyzer analyze-game \
  --home "Kansas City Chiefs" \
  --away "Buffalo Bills" \
  --spread -2.5
```

**Output:**
```
================================================================================
BILLY WALTERS GAME ANALYSIS
================================================================================

Matchup:  Buffalo Bills @ Kansas City Chiefs
Spread:   Kansas City Chiefs -2.5 (-110/-110)

ANALYSIS:
  Predicted Spread: +0.0
  Market Spread:    -2.5
  Edge:             +2.5 pts
  Confidence:       Elevated Confidence

RECOMMENDATION: Elevated Confidence
Bet Type:      SPREAD
Team:          Kansas City Chiefs
Edge:          +2.5 pts
Win Prob:      58.0%
Stake:         3.00% ($300.00)
```

## Full Analysis with Research (2 minutes)

Get complete analysis including injuries and weather:

### Step 1: Scrape Fresh Data

```bash
# Get latest injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Get today's matches
uv run walters-analyzer scrape-highlightly \
  --endpoint matches \
  --sport nfl \
  --date $(date +%Y-%m-%d)
```

### Step 2: Analyze with Research

```bash
uv run walters-analyzer analyze-game \
  --home "Philadelphia Eagles" \
  --away "Dallas Cowboys" \
  --spread -3.0 \
  --venue "Lincoln Financial Field" \
  --date 2025-11-10 \
  --research
```

**Output with Research:**
```
[*] Gathering research data...
[+] Loaded 15 home injuries
[+] Loaded 20 away injuries

================================================================================
BILLY WALTERS GAME ANALYSIS
================================================================================

Matchup:  Dallas Cowboys @ Philadelphia Eagles
Spread:   Philadelphia Eagles -3.0 (-110/-110)

HOME TEAM INJURIES:
  Total Impact: +0.4 pts
  • Jalen Hurts (QB): -2.5 pts
  • A.J. Brown (WR): -1.8 pts
  • Lane Johnson (OT): -1.2 pts

AWAY TEAM INJURIES:
  Total Impact: +0.5 pts
  • Trevon Diggs (CB): -2.2 pts
  • Micah Parsons (LB): -1.5 pts

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

## What You Get

### 1. **Injury Analysis**
- Point value for each injury by position
- Critical player identification
- Position group crisis detection
- Net injury advantage calculation

### 2. **Key Number Detection**
When your predicted spread crosses NFL key numbers (3, 7, 6, 10, 14), you get alerts:
```
KEY NUMBER ALERTS:
  [!] Projection crosses 3 (moving toward the underdog)
```

This means extra value because the market inefficiently prices margins near key numbers.

### 3. **Kelly Criterion Bankroll Management**
- Automatic stake sizing based on edge
- Win probability estimation
- Risk limits (max 3% per bet)
- Fractional Kelly for safety

### 4. **Confidence Levels**

| Edge | Confidence | Typical Stake |
|------|------------|---------------|
| < 1.0 pt | No Play | 0% |
| 1.0-1.9 pts | Slight Edge | 0.5-1.5% |
| 2.0-2.9 pts | Elevated Confidence | 1.5-3.0% |
| ≥ 3.0 pts | High Confidence | 3.0% |

## Real-World Example: Sunday Morning Workflow

### 9:00 AM - Gather Data
```bash
# Fresh injury reports
uv run walters-analyzer scrape-injuries --sport nfl

# Today's games with odds
uv run walters-analyzer scrape-highlightly \
  --endpoint matches \
  --sport nfl \
  --date 2025-11-10
```

### 10:00 AM - Analyze Each Game
```bash
# Game 1: Early window
uv run walters-analyzer analyze-game \
  --home "Green Bay Packers" \
  --away "Chicago Bears" \
  --spread -6.5 \
  --research \
  --bankroll 10000

# Game 2: Late window  
uv run walters-analyzer analyze-game \
  --home "Seattle Seahawks" \
  --away "San Francisco 49ers" \
  --spread -3.0 \
  --venue "Lumen Field" \
  --research \
  --bankroll 10000
```

### 11:30 AM - Monitor for Sharp Money
```bash
# Watch for line movements
uv run walters-analyzer monitor-sharp \
  --sport nfl \
  --duration 60
```

## Advanced Usage

### Custom Bankroll
```bash
uv run walters-analyzer analyze-game \
  --home "Team A" \
  --away "Team B" \
  --spread -3.5 \
  --bankroll 25000  # $25,000 bankroll
```

### Different Juice
```bash
uv run walters-analyzer analyze-game \
  --home "Team A" \
  --away "Team B" \
  --spread -3.5 \
  --home-price -105 \
  --away-price -115
```

### Weather-Sensitive Games
```bash
uv run walters-analyzer analyze-game \
  --home "Buffalo Bills" \
  --away "Miami Dolphins" \
  --spread -4.0 \
  --venue "Highmark Stadium" \
  --date 2025-12-15 \
  --research  # Will fetch December Buffalo weather
```

## Understanding the Output

### Injury Impact Points
- **QB**: 10.0 pts (Out), 7.5 pts (Doubtful), 3.5 pts (Questionable)
- **WR/CB**: 2.5 pts (Out), 1.9 pts (Doubtful), 0.9 pts (Questionable)
- **RB**: 3.0 pts (Out), 2.3 pts (Doubtful), 1.1 pts (Questionable)
- **OL**: 1.5 pts (Out), 1.1 pts (Doubtful), 0.5 pts (Questionable)

### Win Probability to Edge Mapping
The analyzer uses conservative estimates:
- **Edge ≥ 3.0 pts**: 64% win probability
- **Edge ≥ 2.0 pts**: 58% win probability
- **Edge ≥ 1.0 pts**: 54% win probability
- **Edge < 1.0 pts**: 52% win probability (typically no bet)

### Kelly Sizing
The system uses **fractional Kelly (50%)** for safety:
- Full Kelly = (win_prob × price_offered - 1) / (price_offered - 1)
- Stake = 0.5 × Full Kelly
- Capped at 3% of bankroll

## Tips for Success

### 1. **Update Data Daily**
Run scrapers every morning to ensure fresh injury reports.

### 2. **Trust the System**
Don't override Kelly sizing based on "feel" - the math protects you.

### 3. **Focus on Key Numbers**
Games with alerts crossing 3 or 7 deserve extra scrutiny.

### 4. **Track Results**
The system learns from performance over time.

### 5. **Weather Matters**
Always use `--research` for outdoor games in cold/wind/rain.

## Troubleshooting

### No Injuries Found
```bash
# Make sure you've scraped recently
uv run walters-analyzer scrape-injuries --sport nfl

# Check data directory
ls data/injuries/nfl/
```

### Missing Power Ratings
Power ratings load from `data/power_ratings_nfl_2025.json`. The system still works without them but uses injury-based predictions only.

### Research Errors
```bash
# Check .env file has API keys
cat .env | grep API_KEY

# Test manually
uv run walters-analyzer monitor-sharp --test
```

## Next Steps

- **Week Card Workflow**: See `wk-card` command for managing multiple bets
- **Sharp Money Monitoring**: Use `monitor-sharp` for real-time line movement tracking
- **Historical Analysis**: Check `docs/reports/` for backtesting results
- **Full CLI Reference**: See `docs/guides/CLI_REFERENCE.md`

## Questions?

Check the full documentation:
- **CLI Reference**: `docs/guides/CLI_REFERENCE.md`
- **Integration Analysis**: `docs/reports/INTEGRATION_ANALYSIS.md`
- **Billy Walters Methodology**: `docs/billy_walters_cheat_card.md`

