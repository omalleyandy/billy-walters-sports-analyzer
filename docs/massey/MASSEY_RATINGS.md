# Massey Ratings Scraper

## Overview

The Massey Ratings scraper collects comprehensive college football power ratings, game predictions, and matchup analysis from [masseyratings.com](https://masseyratings.com). This data provides a **solid foundation for identifying betting edges** and serves as a **baseline benchmark** for our Billy Walters-based rating system.

## Why Massey Ratings?

Kenneth Massey's ratings system is one of the most respected in college football analytics:

1. **Objective Power Ratings**: Mathematical model-based ratings free from human bias
2. **Game Predictions**: Predicted scores, spreads, and totals for all FBS games
3. **Historical Accuracy**: Proven track record in predicting game outcomes
4. **Comprehensive Data**: Includes offensive/defensive ratings, strength of schedule, and more

### Billy Walters Connection

According to Billy Walters' methodology:
- **Compare multiple rating systems** to find market inefficiencies
- **Look for 2+ point spread discrepancies** between your model and the market
- **Use objective data** to remove emotional bias from betting decisions
- **Track performance** against closing lines to measure edge

Massey Ratings provides an excellent **third-party benchmark** to validate our own models and identify potential edges.

## Features

### 1. Team Power Ratings
Scrapes comprehensive team ratings including:
- Overall power rating (scale: typically 60-100+)
- Rank (1-133 for FBS teams)
- Win-loss record
- Conference affiliation
- Strength of schedule (SOS)
- Offensive and defensive ratings (when available)

### 2. Game Predictions
Collects predictions for upcoming games:
- Predicted final scores for each team
- Predicted spread (home team perspective)
- Predicted total points
- Game date and time
- Team rankings
- Confidence level (High/Medium/Low)

### 3. Betting Edge Analysis
Automatically calculates betting edges when combined with market data:
- **Spread edge**: Difference between Massey spread and market spread
- **Total edge**: Difference between Massey total and market total
- **Recommendations**: Actionable betting insights based on edge size
- **Confidence levels**: High (3+ pt edge), Medium (2+ pt edge), Low (<2 pt edge)

## Installation

Already included in the base setup! Just ensure you have the dependencies:

```powershell
# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

## Usage

### Basic Commands

```powershell
# Scrape everything (ratings + games)
uv run walters-analyzer scrape-massey

# Scrape only team ratings
uv run walters-analyzer scrape-massey --data-type ratings

# Scrape only game predictions
uv run walters-analyzer scrape-massey --data-type games

# Specify season
uv run walters-analyzer scrape-massey --season 2025

# Custom output directory
uv run walters-analyzer scrape-massey --output-dir ./my_data/massey
```

### Advanced Scrapy Commands

```powershell
# Direct Scrapy control
scrapy crawl massey_ratings -a data_type=all
scrapy crawl massey_ratings -a data_type=ratings -a season=2025
scrapy crawl massey_ratings -s MASSEY_OUT_DIR=./custom_output
```

## Output Files

Scraped data is saved to `data/massey_ratings/` in multiple formats:

### 1. JSONL (Combined)
- **File**: `massey-{timestamp}.jsonl`
- **Contains**: All scraped data (ratings, games, matchups) in line-delimited JSON
- **Use case**: Import into databases, data pipelines

### 2. Parquet (By Type)
Efficient columnar format for analytics:
- **`massey-ratings-{timestamp}.parquet`**: Team power ratings
- **`massey-games-{timestamp}.parquet`**: Game predictions
- **`massey-matchups-{timestamp}.parquet`**: Matchup analysis (when available)

### 3. CSV (Games)
- **File**: `massey-games-{timestamp}.csv`
- **Contains**: Game predictions in spreadsheet format
- **Use case**: Quick analysis in Excel, manual review

## Data Schema

### Team Ratings (`data_type="rating"`)

```json
{
  "source": "masseyratings",
  "sport": "college_football",
  "collected_at": "2025-11-01T12:00:00Z",
  "data_type": "rating",
  "season": "2025",
  "rank": 1,
  "team_name": "Georgia",
  "team_abbr": "UGA",
  "rating": 95.3,
  "offensive_rating": 32.1,
  "defensive_rating": 28.7,
  "sos": 72.4,
  "record": "9-1",
  "conference": "SEC"
}
```

### Game Predictions (`data_type="game"`)

```json
{
  "source": "masseyratings",
  "sport": "college_football",
  "collected_at": "2025-11-01T12:00:00Z",
  "data_type": "game",
  "season": "2025",
  "game_date": "2025-11-02",
  "game_time": "3:30 PM",
  "away_team": "Alabama",
  "home_team": "LSU",
  "away_rank": 5,
  "home_rank": 8,
  "predicted_away_score": 31.0,
  "predicted_home_score": 27.0,
  "predicted_spread": 4.0,
  "predicted_total": 58.0,
  "confidence": "High",
  "matchup_id": "Alabama@LSU_2025-11-02",
  "market_spread": 6.5,
  "market_total": 55.5,
  "spread_edge": 2.5,
  "total_edge": 2.5,
  "edge_confidence": "Medium"
}
```

## Integration with Billy Walters Methodology

### 1. Finding Betting Edges

```python
import pandas as pd

# Load Massey predictions
massey_games = pd.read_parquet("data/massey_ratings/massey-games-latest.parquet")

# Load market odds (from overtime.ag scraper)
market_odds = pd.read_parquet("data/overtime_live/overtime-live-latest.parquet")

# Merge on team matchups
merged = massey_games.merge(market_odds, left_on=['away_team', 'home_team'], right_on=['away_team', 'home_team'])

# Find games with 2+ point spread edge
edges = merged[abs(merged['predicted_spread'] - merged['market_spread']) >= 2.0]

print(f"Found {len(edges)} games with betting edges")
```

### 2. Validating Your Own Models

```python
# Compare your model's predictions to Massey
your_predictions = load_your_predictions()
massey_predictions = pd.read_parquet("data/massey_ratings/massey-games-latest.parquet")

# Calculate correlation
correlation = your_predictions['spread'].corr(massey_predictions['predicted_spread'])
print(f"Model correlation with Massey: {correlation:.3f}")

# Find disagreements (potential edges)
disagreements = your_predictions[
    abs(your_predictions['spread'] - massey_predictions['predicted_spread']) > 3.0
]
```

### 3. Power Rating Benchmarking

```python
# Load Massey ratings
massey_ratings = pd.read_parquet("data/massey_ratings/massey-ratings-latest.parquet")

# Compare to your ratings
your_ratings = load_your_ratings()

# Analyze differences
rating_diff = your_ratings.merge(massey_ratings, on='team_name')
rating_diff['diff'] = rating_diff['your_rating'] - rating_diff['rating']

# Teams you rate significantly higher than Massey (potential value bets)
overrated_by_you = rating_diff[rating_diff['diff'] > 5.0]
underrated_by_you = rating_diff[rating_diff['diff'] < -5.0]
```

## Billy Walters Betting Principles Applied

### Principle 1: Use Multiple Data Sources
- **Massey Ratings**: Objective computer model
- **Market Odds**: Wisdom of the crowd
- **Your Model**: Proprietary Billy Walters methodology
- **Action**: Bet when all three align OR when you have high confidence against consensus

### Principle 2: Look for 2+ Point Edges
```python
# Filter for actionable edges
high_confidence_bets = games[
    (games['spread_edge'] >= 2.0) &  # 2+ point edge
    (games['confidence'] == 'High')    # High prediction confidence
]
```

### Principle 3: Track Closing Line Value (CLV)
```python
# After games complete, measure your edge
results = compare_predictions_to_results(massey_predictions, actual_results)
clv = calculate_closing_line_value(results)

print(f"Average CLV: {clv['mean']:.2f} points")
print(f"Win rate on 2+ pt edges: {clv['win_rate']:.1%}")
```

## Use Cases

### 1. Pre-Game Analysis
```powershell
# Saturday morning: scrape latest Massey predictions
uv run walters-analyzer scrape-massey --data-type games

# Compare to overnight line moves from overtime.ag
uv run walters-analyzer scrape-overtime --sport cfb

# Analyze for edges (in Python/Jupyter)
python analyze_edges.py
```

### 2. Weekly Power Rating Updates
```powershell
# Tuesday after games complete: update team ratings
uv run walters-analyzer scrape-massey --data-type ratings

# Track rating changes week-over-week
python track_rating_movements.py
```

### 3. Live Monitoring During Season
```bash
# Automate weekly scraping (cron job / Task Scheduler)
# Every Tuesday at 6 AM
0 6 * * 2 cd /path/to/project && uv run walters-analyzer scrape-massey
```

## Interpreting the Data

### Power Ratings Scale
- **95+**: Elite teams (Top 5)
- **85-95**: Top 25 teams
- **75-85**: Solid mid-major / good P5 teams
- **65-75**: Average FBS teams
- **<65**: Below-average teams

### Predicted Spreads
- **Positive**: Away team favored
- **Negative**: Home team favored
- **Example**: `predicted_spread: -7.0` means home team favored by 7 points

### Confidence Levels
- **High (70+ score)**: Large spread, complete data, clear favorite
- **Medium (40-69 score)**: Moderate data confidence
- **Low (<40 score)**: Incomplete data or uncertain outcome

## Troubleshooting

### No Data Extracted
1. Check screenshots in `snapshots/` directory
2. Massey Ratings website structure may have changed
3. Try running with `--season` flag: `--season 2024` or `--season 2025`

### Incomplete Game Data
- Massey may not have predictions for all games yet
- Early-season games may have less data
- Check `snapshots/massey_games.png` to see what was visible

### Playwright Errors
```powershell
# Reinstall Playwright browsers
uv run playwright install chromium

# On WSL, you may need system dependencies
sudo apt install libgbm1 libgtk-3-0 libasound2
```

## Billy Walters Edge Detection Strategy

### Step-by-Step Workflow

**Step 1: Collect Data**
```powershell
uv run walters-analyzer scrape-massey --data-type all
uv run walters-analyzer scrape-overtime --sport cfb
```

**Step 2: Identify Edges**
```python
import pandas as pd

massey = pd.read_csv("data/massey_ratings/massey-games-latest.csv")
market = pd.read_csv("data/overtime_live/overtime-live-latest.csv")

# Find 2+ point spread edges
edges = massey[
    (massey['spread_edge'].abs() >= 2.0) &
    (massey['confidence'].isin(['High', 'Medium']))
]

print(edges[['away_team', 'home_team', 'predicted_spread', 'market_spread', 'spread_edge']])
```

**Step 3: Apply Gates**
- Check injury reports: `uv run walters-analyzer scrape-injuries --sport cfb`
- Check weather: `uv run walters-analyzer scrape-weather --card ./cards/saturday-card.json`
- Verify line hasn't moved significantly (steam/reverse line movement)

**Step 4: Place Bets**
- Bet only when edge + gates align
- Proper bankroll management (Kelly Criterion)
- Track all bets in `bias_log` for CLV analysis

## Recommended Reading

- [Billy Walters Masterclass](https://www.masterclass.com/classes/billy-walters-teaches-sports-betting)
- [Massey Ratings Methodology](https://masseyratings.com/theory/massey.htm)
- [The Logic of Sports Betting](https://www.amazon.com/Logic-Sports-Betting-Ed-Miller/dp/0615116434)

## Advanced Features (Future)

### Planned Enhancements
- [ ] Scrape score distribution data (probability distributions)
- [ ] Historical data scraping (archive past predictions)
- [ ] Automated CLV tracking vs. actual results
- [ ] Integration with other rating systems (Sagarin, FPI, SP+)
- [ ] Real-time line movement alerts when edges appear

## Support

For issues, questions, or feature requests:
1. Check `snapshots/` directory for debug screenshots
2. Review Scrapy logs for detailed error messages
3. Ensure you're running latest version: `uv sync`

## Files Created by This Scraper

```
data/massey_ratings/
├── massey-20251101-120000.jsonl          # All data (ratings + games)
├── massey-ratings-20251101-120000.parquet # Team power ratings
├── massey-games-20251101-120000.parquet   # Game predictions
├── massey-games-20251101-120000.csv       # Games (spreadsheet format)
└── massey-matchups-20251101-120000.parquet # Matchup analysis (when available)

snapshots/
├── massey_ratings.png    # Debug screenshot of ratings page
├── massey_games.png      # Debug screenshot of games page
└── massey_error.png      # Error screenshot (if scraping fails)
```

## Example: Finding Tonight's Best Bet

```python
import pandas as pd
from datetime import datetime

# Load today's predictions
massey = pd.read_csv("data/massey_ratings/massey-games-latest.csv")
today = datetime.now().strftime("%Y-%m-%d")

# Filter for today's games with edges
todays_games = massey[massey['date'] == today]
edges = todays_games[
    (todays_games['spread_edge'].abs() >= 2.5) &  # 2.5+ point edge
    (todays_games['confidence'] == 'High')         # High confidence
].sort_values('spread_edge', ascending=False)

print("🎯 Tonight's Best Bets (per Massey vs. Market):")
print(edges[['away_team', 'home_team', 'predicted_spread', 'market_spread', 'spread_edge', 'confidence']])

# Cross-reference with injuries and weather before betting!
```

---

**Remember**: Massey Ratings is ONE tool in your toolkit. Always cross-reference with:
- Your own Billy Walters-based model
- Injury reports (critical!)
- Weather conditions (outdoor games)
- Line movement (steam, reverse line movement)
- Public betting percentages (fade the public)

**Bet responsibly. Use proper bankroll management. Track your CLV.**

