# Massey Ratings - Example Output

## Sample Data from November 1, 2025

### Team Power Ratings (Top 10)

| Rank | Team | Rating | Pwr | Off | Def | SoS | Record | Conference |
|------|------|--------|-----|-----|-----|-----|--------|------------|
| 1 | Ohio St | 9.36 | 84.17 | 66.47 | 45.50 | 55.28 | 7-0 | Big 10 |
| 2 | Indiana | 9.08 | 77.46 | 66.43 | 38.83 | 58.03 | 8-0 | Big 10 |
| 3 | Alabama | 8.99 | 78.95 | 66.50 | 40.25 | 64.32 | 7-1 | Southeastern |
| 4 | Texas A&M | 8.95 | 72.19 | 65.51 | 34.48 | 63.51 | 8-0 | Southeastern |
| 5 | Georgia | 8.92 | 77.24 | 65.43 | 39.61 | 64.65 | 6-1 | Southeastern |
| 6 | Oregon | 8.88 | 78.77 | 67.55 | 39.02 | 59.41 | 7-1 | Big 10 |
| 7 | Mississippi | 8.76 | 74.27 | 66.58 | 35.49 | 62.65 | 7-1 | Southeastern |
| 8 | BYU | 8.71 | 68.98 | 61.98 | 34.80 | 57.16 | 8-0 | Big 12 |
| 9 | Notre Dame | 8.69 | 78.78 | 67.36 | 39.22 | 63.13 | 5-2 | FBS Indep |
| 10 | Texas | 8.60 | 74.36 | 62.53 | 39.63 | 61.05 | 6-2 | Southeastern |

**File:** `massey-ratings-20251101-104919.parquet`  
**Total Teams:** 136 FBS teams

---

### Game Predictions (Saturday November 1, 2025)

#### Featured Games with Betting Edges

**#1 Penn St @ Ohio St (12:00 PM ET)**
- **Teams:** Penn St (#32, 3-4) @ Ohio St (#1, 7-0)
- **Predicted Score:** 20-35 (Ohio St)
- **Massey Spread:** -15.5 (Ohio St favored)
- **Massey Total:** 51.5
- **Win Probability:** Ohio St 89%, Penn St 11%
- **Confidence:** High
- **Betting Note:** Huge spread - check if market is higher (potential edge)

**#2 Duke @ Clemson (12:00 PM ET)**
- **Teams:** Duke (#56, 4-3) @ Clemson (#51, 3-4)
- **Predicted Score:** 24-31 (Clemson)
- **Massey Spread:** -7.5 (Clemson favored)
- **Massey Total:** 56.5
- **Win Probability:** Clemson 73%, Duke 27%
- **Confidence:** High
- **Betting Note:** Close ranks - monitor market spread

**#3 Miami FL @ SMU (12:00 PM ET)**
- **Teams:** Miami FL (#13, 6-1) @ SMU (#41, 5-3)
- **Predicted Score:** 30-26 (Miami FL)
- **Massey Spread:** -3.5 (Miami FL favored)
- **Massey Total:** 56.5
- **Win Probability:** Miami FL 62%, SMU 38%
- **Confidence:** High
- **Betting Note:** Away favorite - look for edge on Miami

**#4 Notre Dame @ Boston College (3:30 PM ET)**
- **Teams:** Notre Dame (#9, 5-2) @ Boston College (#102, 1-7)
- **Predicted Score:** 44-14 (Notre Dame)
- **Massey Spread:** -29.5 (Notre Dame favored)
- **Massey Total:** 57.5
- **Win Probability:** Notre Dame 98%, BC 2%
- **Confidence:** High
- **Betting Note:** Massive blowout expected - fade or stay away?

**#5 Oklahoma @ Tennessee (7:30 PM ET)**
- **Teams:** Oklahoma (#14, 6-2) @ Tennessee (#11, 6-2)
- **Predicted Score:** 27-33 (Tennessee)
- **Massey Spread:** -5.5 (Tennessee favored)
- **Massey Total:** 60.5
- **Win Probability:** Tennessee 64%, Oklahoma 36%
- **Confidence:** High
- **Betting Note:** SEC showdown - great game for edge hunting

---

### CSV Output Sample

```csv
date,time,away_team,home_team,predicted_away_score,predicted_home_score,predicted_spread,predicted_total,confidence,market_spread,market_total,spread_edge,total_edge,edge_confidence
2025-11-01,12:00 PM.ET,Army,Air Force,28,24,-3.5,55.5,High,,,,,
2025-11-01,12:00 PM.ET,UCF,Baylor,30,31,-1.5,61.5,High,,,,,
2025-11-01,12:00 PM.ET,Duke,Clemson,24,31,-7.5,56.5,High,,,,,
2025-11-01,12:00 PM.ET,UAB,Connecticut,28,35,-6.5,65.5,High,,,,,
2025-11-01,12:00 PM.ET,West Virginia,Houston,21,28,-7.5,51.5,High,,,,,
```

**File:** `massey-games-20251101-104817.csv`  
**Total Games:** 52 games

---

### JSONL Output Sample

```json
{
  "source": "masseyratings",
  "sport": "college_football",
  "collected_at": "2025-11-01T10:48:17Z",
  "data_type": "game",
  "season": "2025",
  "game_date": "2025-11-01",
  "game_time": "12:00 PM.ET",
  "away_team": "Penn St",
  "home_team": "Ohio St",
  "away_rank": 32,
  "home_rank": 1,
  "predicted_away_score": 20,
  "predicted_home_score": 35,
  "predicted_spread": -15.5,
  "predicted_total": 51.5,
  "confidence": "High",
  "matchup_id": "Penn St@Ohio St_2025-11-01"
}
```

---

## Edge Analysis Example

### After running `analyze_massey_edges.py`:

```
🎯 Betting Edges (5 games)
┌─────────────────────────────┬────────┬────────┬──────┬────────┬────────┬────────┬───────────────────────┐
│ Matchup                     │ Massey │ Market │ Edge │ Massey │ Market │ Total  │ Recommendation        │
│                             │ Spread │ Spread │      │ Total  │ Total  │ Edge   │                       │
├─────────────────────────────┼────────┼────────┼──────┼────────┼────────┼────────┼───────────────────────┤
│ Duke @ Clemson              │  -7.5  │  -10.0 │ 2.5  │  56.5  │  54.0  │  2.5   │ BET HOME (Clemson)    │
│ Penn St @ Ohio St           │ -15.5  │  -13.0 │ 2.5  │  51.5  │  53.0  │  1.5   │ Consider HOME (OSU)   │
│ South Carolina @ Mississippi│ -13.5  │  -16.0 │ 2.5  │  53.5  │  50.5  │  3.0   │ BET HOME (Ole Miss)   │
│ USC @ Nebraska              │  -6.5  │  -4.0  │ 2.5  │  60.5  │  57.0  │  3.5   │ BET OVER              │
│ Oklahoma @ Tennessee        │  -5.5  │  -8.0  │ 2.5  │  60.5  │  58.0  │  2.5   │ BET HOME (Tennessee)  │
└─────────────────────────────┴────────┴────────┴──────┴────────┴────────┴────────┴───────────────────────┘

Summary:
  Total games analyzed: 52
  Games with 2.0+ point edge: 5
  High confidence edges: 3
  Medium confidence edges: 2

⚠️  Remember to check before betting:
  1. Injury reports (key players out?)
  2. Weather conditions (wind, rain, cold?)
  3. Line movement (steam? reverse line movement?)
  4. Public betting % (fade the public)
  5. Your own model's prediction

Saved analysis to: data/massey_ratings/edge_analysis_20251101_105500.csv
```

---

## Billy Walters Analysis

### Interpreting the Data

**Duke @ Clemson Example:**
- **Massey Spread:** -7.5 (Clemson favored by 7.5)
- **Market Spread:** -10.0 (Clemson favored by 10)
- **Edge:** 2.5 points

**Betting Opportunity:**
- Market has Clemson favored by MORE than Massey
- This suggests **Clemson is overvalued** by the market
- Or Duke is **undervalued**
- **Billy Walters Action:** Bet Duke +10 (getting extra points vs. Massey)

**Risk Factors to Check:**
1. Is Duke's QB healthy? (injury gate)
2. Weather in Clemson? (if outdoor, check wind/rain)
3. Has the line moved from -10? (if steaming to -11, fade)
4. What's the public % on Clemson? (if 75%+, fade public)

### Edge Sizing

| Massey vs. Market Edge | Action |
|------------------------|--------|
| 3.0+ points | **Strong bet** (2-3 units) - High confidence |
| 2.0-2.9 points | **Bet** (1-2 units) - Good edge |
| 1.5-1.9 points | **Small bet** (0.5-1 unit) - Marginal edge |
| < 1.5 points | **No bet** - Not enough edge |

---

## Integration with Betting Workflow

### 1. Morning Analysis (8:00 AM)
```powershell
uv run walters-analyzer scrape-massey --data-type games
```
**Output:** Fresh Massey predictions for today's games

### 2. Market Comparison (9:00 AM)
```powershell
uv run walters-analyzer scrape-overtime --sport cfb
uv run python scripts/analyze_massey_edges.py
```
**Output:** Games with 2+ point edges identified

### 3. Gate Checks (10:00 AM)
```powershell
uv run walters-analyzer scrape-injuries --sport cfb
uv run walters-analyzer scrape-weather --card ./cards/saturday.json
```
**Output:** Injury status and weather impact scores

### 4. Final Bet Placement (11:00 AM)
- Review edge analysis
- Confirm gates pass
- Check line movement
- Place bets on 2+ unit opportunities

### 5. Post-Game Review (Monday)
- Compare Massey predictions to actual results
- Calculate CLV (closing line value)
- Track performance by edge size
- Refine thresholds as needed

---

## Data Quality Metrics

### Games Data (52 games scraped)
- ✅ **100%** have predicted scores
- ✅ **100%** have predicted spreads
- ✅ **100%** have predicted totals
- ✅ **100%** have confidence ratings
- ✅ **100%** have team rankings
- ✅ **100%** have date/time

### Ratings Data (136 teams scraped)
- ✅ **100%** have power ratings
- ✅ **100%** have offensive ratings
- ✅ **100%** have defensive ratings
- ✅ **100%** have SoS (strength of schedule)
- ✅ **100%** have win-loss records
- ✅ **100%** have conference affiliations

**Data Quality Score: 100% ✅**

---

## Files Generated Per Scrape

### Complete Scrape (`--data-type all`)
```
data/massey_ratings/
├── massey-20251101-105352.jsonl              # All data (ratings + games)
├── massey-ratings-20251101-105352.parquet    # Team ratings only
├── massey-games-20251101-105352.parquet      # Game predictions only
└── massey-games-20251101-105352.csv          # Games (spreadsheet)
```

### Games Only (`--data-type games`)
```
data/massey_ratings/
├── massey-20251101-105352.jsonl       # Game predictions
├── massey-games-20251101-105352.parquet
└── massey-games-20251101-105352.csv
```

### Ratings Only (`--data-type ratings`)
```
data/massey_ratings/
├── massey-20251101-104919.jsonl              # Team ratings
└── massey-ratings-20251101-104919.parquet
```

---

## Real-World Example: Finding an Edge

### Scenario: Saturday Morning Analysis

**Step 1: Duke @ Clemson**
- Massey predicts: Duke 24, Clemson 31 (Clemson -7.5)
- Market odds: Clemson -10.0
- **Edge identified:** 2.5 points

**Step 2: Validate the Edge**
- ✅ Massey confidence: High
- ✅ Duke has no key injuries (checked ESPN)
- ✅ Weather: Clear, 65°F (no impact)
- ✅ Line stable at -10 (no steam)
- ✅ Your model says: Duke +9 (agrees with Massey)

**Step 3: Betting Decision**
- **Bet:** Duke +10 (2 units)
- **Rationale:** 
  - Massey edge: 2.5 points
  - No gate issues
  - Model agreement
  - High confidence
- **Expected Value:** Positive (getting 2.5 extra points)

**Step 4: Result Tracking**
- Game ends: Duke 27, Clemson 30 (Duke covers +10!)
- CLV: Closing line was -9.5, we got -10 ✅
- **Win:** 2 units profit
- **Learning:** Massey + model agreement = reliable edge

---

## Integration with Existing Data

### Combining with Overtime.ag Odds

```python
import pandas as pd

# Load Massey predictions
massey = pd.read_csv("data/massey_ratings/massey-games-latest.csv")

# Load market odds
market = pd.read_csv("data/overtime_live/overtime-live-latest.csv")

# Merge on team matchups
merged = massey.merge(
    market,
    left_on=['away_team', 'home_team'],
    right_on=['away_team', 'home_team'],
    how='inner'
)

# Calculate edges
merged['spread_edge'] = abs(
    merged['predicted_spread'] - merged['spread_home_line']
)
merged['total_edge'] = abs(
    merged['predicted_total'] - merged['total_over_line']
)

# Filter for opportunities
edges = merged[
    (merged['spread_edge'] >= 2.0) | (merged['total_edge'] >= 3.0)
]

print(f"Found {len(edges)} betting opportunities")
print(edges[['away_team', 'home_team', 'spread_edge', 'total_edge']])
```

---

## Billy Walters Betting Strategy

### The Massey Edge Formula

1. **Find the Edge**
   - Massey Spread - Market Spread = Edge
   - If |Edge| ≥ 2.0 points → **Opportunity**

2. **Validate the Edge**
   - Injury gate: No key players out ✅
   - Weather gate: Impact score < 50 ✅
   - Steam gate: Line hasn't moved against you ✅
   - Model gate: Your model agrees ✅

3. **Size the Bet**
   - 3.0+ point edge → 2-3 units (high confidence)
   - 2.0-2.9 point edge → 1-2 units (medium confidence)
   - < 2.0 points → No bet (insufficient edge)

4. **Track Performance**
   - Log all bets with edge size
   - Measure CLV (closing line value)
   - Calculate ROI by edge bucket
   - Refine thresholds based on results

### Expected Results (Over Season)

Based on Billy Walters methodology:

| Edge Size | Expected Hit Rate | Expected ROI |
|-----------|-------------------|--------------|
| 3.0+ points | 58-62% | 8-12% |
| 2.0-2.9 points | 54-58% | 4-8% |
| 1.5-1.9 points | 52-54% | 2-4% |

**Note:** These are theoretical - track YOUR actual results!

---

## Next Steps

1. **Daily Scraping:** Set up automated morning scrapes
2. **Edge Tracking:** Use the analysis script before each betting session
3. **CLV Measurement:** Track Massey edge vs. actual results
4. **Model Refinement:** Compare Massey to your Billy Walters model
5. **Multi-Source Validation:** Add FPI, Sagarin, SP+ for additional confirmation

**See [MASSEY_QUICKSTART.md](MASSEY_QUICKSTART.md) for immediate usage guide.**

