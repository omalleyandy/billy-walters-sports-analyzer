# Massey Ratings Quick Start Guide

## 5-Minute Setup to Finding Betting Edges

### Step 1: Scrape Massey Ratings (30 seconds)

```powershell
# Get today's game predictions and team ratings
uv run walters-analyzer scrape-massey
```

**Output:**
- `data/massey_ratings/massey-games-*.csv` - Game predictions (spreads, totals, scores)
- `data/massey_ratings/massey-ratings-*.parquet` - Team power ratings
- `data/massey_ratings/massey-*.jsonl` - All data in JSON format

### Step 2: Scrape Market Odds (1 minute)

```powershell
# Get current market odds from overtime.ag
uv run walters-analyzer scrape-overtime --sport cfb
```

**Output:**
- `data/overtime_live/overtime-live-*.csv` - Current spreads, totals, moneylines

### Step 3: Find Edges (instant)

```powershell
# Analyze for betting opportunities
uv run python scripts/analyze_massey_edges.py
```

**Output:**
```
🎯 Betting Edges (8 games)
┌─────────────────────┬────────┬────────┬──────┬────────┬────────┬────────┬──────────────────────┐
│ Matchup             │ Massey │ Market │ Edge │ Massey │ Market │ Total  │ Recommendation       │
│                     │ Spread │ Spread │      │ Total  │ Total  │ Edge   │                      │
├─────────────────────┼────────┼────────┼──────┼────────┼────────┼────────┼──────────────────────┤
│ Duke @ Clemson      │  -7.5  │  -10.0 │ 2.5  │  56.5  │  54.0  │  2.5   │ BET CLEMSON          │
│ Penn St @ Ohio St   │ -15.5  │  -13.0 │ 2.5  │  51.5  │  53.0  │  1.5   │ Consider OHIO ST     │
│ ...                 │  ...   │  ...   │ ...  │  ...   │  ...   │  ...   │ ...                  │
└─────────────────────┴────────┴────────┴──────┴────────┴────────┴────────┴──────────────────────┘

⚠️  Remember to check before betting:
  1. Injury reports (key players out?)
  2. Weather conditions (wind, rain, cold?)
  3. Line movement (steam? reverse line movement?)
  4. Public betting % (fade the public)
  5. Your own model's prediction
```

### Step 4: Apply Billy Walters Gates

Before placing any bet, check critical factors:

```powershell
# Check injuries
uv run walters-analyzer scrape-injuries --sport cfb

# Check weather (for outdoor games)
uv run walters-analyzer scrape-weather --card ./cards/saturday-card.json
```

**Gate Checks:**
- ✅ No key player injuries (especially QB)
- ✅ Weather impact score < 50 (check for wind > 15mph, rain)
- ✅ Line hasn't moved significantly against you (no steam)
- ✅ Edge remains at betting time (2+ points)

### Step 5: Place Your Bet

Only bet when:
1. **Edge exists** (2+ points spread, 3+ points total)
2. **Gates pass** (no injuries, good weather, line stable)
3. **Confidence is high** (your model + Massey agree)
4. **Proper unit sizing** (Kelly Criterion: 1-3 units)

---

## Example Workflow: Saturday Morning

```powershell
# 8:00 AM - Scrape Massey predictions
uv run walters-analyzer scrape-massey --data-type games

# 8:30 AM - Check market odds
uv run walters-analyzer scrape-overtime --sport cfb

# 9:00 AM - Analyze edges
uv run python scripts/analyze_massey_edges.py --min-edge 2.5

# 9:30 AM - Check gates
uv run walters-analyzer scrape-injuries --sport cfb
uv run walters-analyzer scrape-weather --card ./cards/saturday-card.json

# 10:00 AM - Review and place bets
# Use the edge analysis + gate checks to make final decisions
```

---

## Understanding Massey Predictions

### Power Ratings (Pwr column)
- **84.17** (Ohio St) = Elite team
- **77.46** (Indiana) = Top 10 team
- **60.00** = Average FBS team
- **40.00** = Below-average team

### Predicted Spreads
- **-7.5** = Home team favored by 7.5 points
- **+3.5** = Away team favored by 3.5 points
- **Compare to market** to find edges

### Confidence Levels
- **High**: Large spread, complete data, clear favorite (bet with confidence)
- **Medium**: Moderate data (proceed with caution)
- **Low**: Uncertain outcome (avoid or reduce stake)

---

## Billy Walters Edge Thresholds

| Edge Size | Confidence | Action |
|-----------|------------|--------|
| 3+ points | High | **Strong Bet** (2-3 units) |
| 2-3 points | High | Bet (1-2 units) |
| 2-3 points | Medium | Small bet (0.5-1 unit) |
| < 2 points | Any | **No bet** |

---

## Troubleshooting

### "No edges found"
- Lower the `--min-edge` threshold: `--min-edge 1.5`
- Markets may be efficient (this is common)
- Try different game dates or times

### "No market data"
- Run: `uv run walters-analyzer scrape-overtime --sport cfb`
- Ensure overtime.ag credentials in `.env` file
- Check that games haven't started yet

### "Scraper failed"
- Check `snapshots/` directory for debug screenshots
- Ensure: `uv run playwright install chromium`
- Massey website structure may have changed

---

## Next Steps

1. **Automate daily scraping** (Windows Task Scheduler / cron)
2. **Track your CLV** (closing line value) against actual results
3. **Build your own model** using Billy Walters principles
4. **Compare models** (Massey vs. yours vs. FPI vs. Sagarin)
5. **Refine your edge detection** based on results

**See [MASSEY_RATINGS.md](MASSEY_RATINGS.md) for complete documentation.**

