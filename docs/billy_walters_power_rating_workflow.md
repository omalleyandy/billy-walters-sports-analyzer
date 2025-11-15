# Billy Walters Power Rating Workflow

Complete workflow for collecting data sources and calculating Billy Walters power ratings with mathematical edge detection.

## Overview

This workflow integrates multiple data sources to calculate week-to-week power ratings using Billy Walters methodology:

1. **ESPN Team Statistics** - Primary source for offensive/defensive metrics
2. **Massey Ratings** - Fallback/composite baseline (70-100 scale)
3. **Overtime.ag Odds** - Market lines for edge detection
4. **Weather Data** - Game conditions impact
5. **Injury Reports** - Player availability impact

## Data Sources

### ESPN Team Statistics

**Collection:**
```bash
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl --week 11
```

**Metrics Used:**
- Points per game (PPG)
- Points allowed per game (PAPG)
- Total yards per game
- Turnover margin
- 3rd down conversion %
- Takeaways/Giveaways

**Output:** `data/current/nfl_team_stats_week_{week}.json`

### Massey Ratings (Fallback)

**Collection:**
```bash
uv run python -m src.data.massey_ratings_scraper
```

**Usage:**
- Primary fallback when ESPN stats unavailable
- Composite of 100+ ranking systems
- Provides baseline 70-100 scale ratings

**Output:** `output/massey/nfl/ratings/nfl_ratings_{timestamp}.json`

### Overtime.ag Odds

**Collection:**
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```

**Data:**
- Game spreads
- Totals (over/under)
- Moneylines
- Best available odds

**Output:** `output/overtime/nfl/pregame/api_walters_{timestamp}.json`

## Power Rating Calculation

### Billy Walters Formula

**Base Rating:**
```
Base = 75.0 + (PPG - 23.3) * 0.5 - (PAPG - 23.3) * 0.5
```

**Enhancement (with ESPN stats):**
```
Enhanced = Base + (PPG - 23.3) * 0.15 + (23.3 - PAPG) * 0.15 + (TO_Margin * 0.3)
```

**Fallback (Massey only):**
```
Rating = Massey Rating (70-100 scale)
```

### Rating Scale

- **70-75**: Bottom tier teams
- **75-80**: Average teams
- **80-85**: Above average
- **85-90**: Good teams
- **90-95**: Very good teams
- **95-100**: Elite teams

### Home Field Advantage

- **NFL**: 3.0 points
- **NCAAF**: 3.5 points

## Complete Workflow

### Step 1: Collect All Data Sources

```bash
# ESPN Team Statistics
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl --week 11

# Massey Ratings (fallback)
uv run python -m src.data.massey_ratings_scraper

# Overtime Odds
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

### Step 2: Run Power Rating Integration

```bash
uv run python scripts/analysis/billy_walters_power_rating_integration.py --week 11 --league nfl
```

**What it does:**
1. Collects ESPN team stats
2. Loads Massey ratings (fallback)
3. Loads Overtime odds
4. Calculates power ratings for all teams
5. Detects betting edges (≥3.5 point threshold)
6. Saves results

**Output:** `output/billy_walters/week_{week}/power_ratings_week_{week}.json`

### Step 3: Review Detected Edges

The integration script automatically detects edges using:
- Power rating differential
- Weather adjustments
- Injury impacts
- Situational factors
- Key number value

**Edge Thresholds:**
- **3.5-4.5 points**: Weak edge (1% Kelly)
- **4.5-5.5 points**: Medium edge (2% Kelly)
- **5.5-7.0 points**: Strong edge (3% Kelly)
- **7.0+ points**: Very strong edge (4-5% Kelly)

## Example Output

```
Top 10 Power Ratings:
   1. Indianapolis Colts        80.75 (espn_enhanced)
   2. Seattle Seahawks          80.72 (espn_enhanced)
   3. Los Angeles Rams          80.44 (espn_enhanced)
   4. Detroit Lions             79.61 (espn_enhanced)
   5. Kansas City Chiefs        79.22 (espn_enhanced)

Detected 10 betting edges

Top Edges:
  1. Cincinnati Bengals @ Pittsburgh Steelers Edge: 13.52 pts | home
  2. Houston Texans @ Tennessee Titans   Edge: 11.80 pts | away
  3. Tampa Bay Buccaneers @ Buffalo Bills Edge: 11.36 pts | home
```

## Weekly Workflow

### Tuesday-Wednesday (Data Collection)

```bash
# Complete data collection
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl --week 11
uv run python -m src.data.massey_ratings_scraper
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

### Wednesday-Thursday (Analysis)

```bash
# Calculate power ratings and detect edges
uv run python scripts/analysis/billy_walters_power_rating_integration.py --week 11 --league nfl

# Or use edge detector directly
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector
```

### Sunday (Game Day)

```bash
# Refresh odds before games
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# Re-run edge detection with latest odds
uv run python scripts/analysis/billy_walters_power_rating_integration.py --week 11 --analysis-only
```

## Data Source Priority

1. **Primary**: ESPN Team Statistics (most current, comprehensive)
2. **Fallback**: Massey Ratings (composite, reliable baseline)
3. **Enhancement**: Combine both when available

**Integration Logic:**
- Use ESPN stats if available → Calculate base rating
- Enhance with turnover margin and efficiency metrics
- Fallback to Massey if ESPN stats missing
- Combine both sources when possible for best accuracy

## Output Files

```
output/
├── billy_walters/
│   └── week_11/
│       └── power_ratings_week_11.json
├── edge_detection/
│   ├── nfl_edges_detected.jsonl
│   └── edge_report.txt
├── espn/
│   ├── stats/nfl/team_stats_nfl_*.json
│   ├── standings/nfl/standings_nfl_*.json
│   └── schedule/nfl/schedule_nfl_*.json
├── massey/
│   └── nfl/
│       └── ratings/nfl_ratings_*.json
└── overtime/
    └── nfl/
        └── pregame/api_walters_*.json
```

## Troubleshooting

### Missing Data Sources

**Issue**: Massey ratings not found

**Solution:**
```bash
uv run python -m src.data.massey_ratings_scraper
```

**Issue**: ESPN stats not found

**Solution:**
```bash
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl --week 11
```

**Issue**: No Overtime odds

**Solution:**
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

### No Edges Detected

**Possible reasons:**
1. Power ratings too close to market lines
2. Missing team data (skips games without ratings)
3. Edge threshold too high (default: 3.5 points)

**Check:**
- Verify all teams have power ratings
- Review power ratings vs market lines manually
- Lower edge threshold if needed (modify in edge detector)

## Next Steps

1. **Review detected edges** - Validate against your own analysis
2. **Check weather/injuries** - Add contextual factors
3. **Monitor line movement** - Track sharp action
4. **Execute bets** - Use Kelly Criterion for sizing
5. **Track CLV** - Monitor Closing Line Value

## Resources

- [Billy Walters Edge Detector](src/walters_analyzer/valuation/billy_walters_edge_detector.py)
- [Power Rating System](src/walters_analyzer/valuation/power_ratings.py)
- [ESPN API Client](src/data/espn_api_client.py)
- [Massey Ratings Scraper](src/data/massey_ratings_scraper.py)
- [Overtime API Client](src/data/overtime_api_client.py)
