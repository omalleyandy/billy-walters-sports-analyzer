# Custom Billy Walters Power Rating Engine

## Overview

The Custom Power Rating Engine builds proprietary power ratings for NFL and NCAAF teams using raw ESPN component data instead of relying on Massey's composite ratings. This system embodies Billy Walters' principle of **information edge through transparent, defensible analysis**.

**Key Principle:** You don't need someone else's formula. Build your own from verifiable data.

## Architecture

### System Components

```
ESPN Component Data
├── Team Statistics (espn_team_stats)
│   ├── Offensive Metrics
│   └── Defensive Metrics
├── Injury Reports (espn_injuries)
│   └── Position-Specific Impact
├── Standings (espn_standings)
│   └── Recent Performance
└── (Optional) Massey Ratings
    └── Validation Comparison

        ↓

Custom Power Rating Engine
├── Offensive Rating (30%)
├── Defensive Rating (25%)
├── Injury Rating (15%)
├── Momentum Rating (15%)
└── Home Field Rating (15%)

        ↓

Output
├── Overall Power Rating
├── Component Breakdown
├── Massey Differential
└── Confidence Score
```

### League-Specific Scales

**NFL:**
- Range: 70-100
- Baseline: 85
- Home Field Advantage: 3.0 points

**NCAAF:**
- Range: 60-105
- Baseline: 80
- Home Field Advantage: 3.5 points (higher than NFL)

## Rating Components

### 1. Offensive Efficiency Rating (30% weight)

**Purpose:** What the team scores indicates offensive quality

**Calculation:**
```
PPG Differential = (Team PPG - League Average PPG) / League Average PPG
YPG Differential = (Team YPG - League Average YPG) / League Average YPG

Offensive Rating = (PPG Differential * 10 * 0.6) + (YPG Differential * 10 * 0.4)
```

**League Baselines:**
- NFL: 23.0 PPG, 350 YPG
- NCAAF: 28.5 PPG, 400 YPG

**Example:**
- Team A: 28 PPG (vs 23 baseline) = +5.5% diff = +1.83 rating adjustment
- Contributes to overall rating weighted at 30%

### 2. Defensive Efficiency Rating (25% weight)

**Purpose:** What the team prevents indicates defensive quality

**Calculation:**
```
PAPG Differential = (League Avg PAPG - Team PAPG) / League Avg PAPG
YAPG Differential = (League Avg YAPG - Team YAPG) / League Avg YAPG

Defensive Rating = (PAPG Differential * 10 * 0.6) + (YAPG Differential * 10 * 0.4)
```

**Example:**
- Team A: 20 PAPG (vs 23 baseline) = +13% advantage = +4.33 rating adjustment
- Better defense = positive contribution

### 3. Injury Impact Rating (15% weight)

**Purpose:** Injuries to key positions reduce team strength

**Methodology:**

Position-specific injury values (higher = more important):

**NFL:**
- QB Elite: 4.5 points
- RB Elite: 2.5 points
- WR1 Elite: 1.8 points
- LT/RT Elite: 1.5 points
- CB Elite: 1.2 points
- LB/DE Elite: 1.2-1.5 points

**NCAAF:**
- QB Elite: 5.0 points (higher due to depth)
- RB Elite: 3.5 points
- WR Elite: 2.5 points
- OL Elite: 1.5 points
- DL Elite: 2.0 points
- LB Elite: 1.8 points

**Severity Classification:**
- ELITE: Starting positions, high-impact players
- STARTER: Important players, some depth available
- BACKUP: Depth replacements, limited impact
- RESERVE: Minimal impact on team

**Calculation:**
```
Total Impact Points = Sum of (Position Value * Severity Multiplier)
Injury Rating Adjustment = -(Total Impact Points / 2.0)
Capped at: minimum -10.0 (catastrophic)
```

**Example:**
- Away QB Elite out: -5.0 pts
- Home RB Starter out: -1.5 pts
- Home WR out: -0.5 pts
- Total: -7.0 pts, divided by 2 = -3.5 rating adjustment

**Injury Level Categories:**
- HEALTHY: 0 elite, <2 total impact points
- MINOR: <1 elite, 2-4 total impact points
- MODERATE: 1 elite, 4-8 total impact points
- SEVERE: 2+ elite, 8+ total impact points

### 4. Momentum Rating (15% weight)

**Purpose:** Recent performance indicates current team condition

**Calculation:**
```
Streak Points = min(Streak Count, 5) * 0.5
Win % Contribution = (Win Pct - 0.5) * 10.0

Momentum Rating = Streak Points (if winning) or -Streak Points (if losing)
                + Win % Contribution
```

**Example:**
- Team on 3-game winning streak: +1.5
- Record 6-2 (75% win rate): +2.5
- Combined: +4.0 rating adjustment

### 5. Home Field Advantage Rating (15% weight)

**Purpose:** Venue advantage is consistent across seasons

**Values:**
- NFL: 3.0 points
- NCAAF: 3.5 points

**Applied:** Contextually in spread calculations, not stored in rating

## Overall Rating Calculation

```python
Overall Rating = Baseline Rating + Component Adjustments

Where:
  Baseline = 85 (NFL) or 80 (NCAAF)

  Component Adjustments =
    (Offensive Rating * 0.30) +
    (Defensive Rating * 0.25) +
    (Injury Rating * 0.15) +
    (Momentum Rating * 0.15) +
    (Home Field Rating * 0.15)

  Final Rating = max(Rating Min, min(Rating Max, Overall Rating))
```

### Complete Example (NFL)

**Kansas City Chiefs, Week 12:**

| Component | Value | Weight | Contribution |
|-----------|-------|--------|--------------|
| Offensive | +3.0 | 30% | +0.90 |
| Defensive | +2.5 | 25% | +0.63 |
| Injury | -1.0 | 15% | -0.15 |
| Momentum | +2.0 | 15% | +0.30 |
| Home Field | +3.0 | 15% | +0.45 |
| **Total Adjustment** | | | **+2.13** |
| Baseline | 85.0 | | |
| **Final Rating** | **87.13** | | |

**Buffalo Bills (visitor), Week 12:**

| Component | Value | Weight | Contribution |
|-----------|-------|--------|--------------|
| Offensive | +1.5 | 30% | +0.45 |
| Defensive | +1.0 | 25% | +0.25 |
| Injury | -2.0 | 15% | -0.30 |
| Momentum | -0.5 | 15% | -0.08 |
| Home Field | +0.0 | 15% | +0.00 |
| **Total Adjustment** | | | **+0.32** |
| Baseline | 85.0 | | |
| **Final Rating** | **85.32** | | |

**Predicted Spread:**
```
Spread = Home Rating - Away Rating + Home Field Advantage
Spread = 87.13 - 85.32 + 3.0 = 4.81 ≈ 4.8 (KC favored by 4.8)
```

## Spread Calculation

### Standard Spread

```python
spread = home_rating.overall_rating - away_rating.overall_rating
if include_home_field:
    spread += engine.home_field_advantage
```

### Matchup Analysis

1. **Rating Difference:** Primary predictor (intrinsic quality gap)
2. **Home Field Bonus:** Adjusts for venue advantage (always included)
3. **Total Spread:** Realistic line prediction

## Data Requirements

### Minimum Data

For basic rating generation, required fields:

**espn_team_stats:**
- points_per_game (offensive)
- points_allowed_per_game (defensive)
- total_yards_per_game
- yards_allowed_per_game

**espn_standings:**
- wins, losses
- streak_type, streak_count

**espn_injuries:**
- position, severity
- status (OUT, DOUBTFUL, QUESTIONABLE)

### Optimal Data

For enhanced accuracy, also include:

**espn_team_stats:**
- passing/rushing yards (offensive splits)
- completion_percentage, yards_per_attempt
- passing/rushing yards allowed
- sacks, interceptions, turnover_margin
- 3rd down %, 4th down %, red zone %

**espn_standings:**
- home_wins, home_losses
- away_wins, away_losses
- win_percentage

**espn_injuries:**
- impact_estimate (Billy Walters value)
- return_week (timeline)

## Usage

### Generate Ratings

```bash
# Generate custom ratings from ESPN data
python scripts/database/generate_custom_power_ratings.py
```

### Programmatic Usage

```python
from walters_analyzer.valuation.custom_power_rating_engine import (
    CustomPowerRatingEngine,
    League,
    OffensiveMetrics,
    DefensiveMetrics,
    InjuryImpact,
    TeamStatus,
)

# Initialize engine
engine = CustomPowerRatingEngine(league=League.NFL)

# Create metrics
offensive = OffensiveMetrics(
    points_per_game=28.5,
    total_yards_per_game=380,
    passing_yards_per_game=250,
    rushing_yards_per_game=130,
    completion_percentage=65.0,
)

defensive = DefensiveMetrics(
    points_allowed_per_game=20.0,
    yards_allowed_per_game=340,
)

injury = InjuryImpact(
    elite_players_out=0,
    starter_players_out=1,
    total_impact_points=1.5,
    injury_level="MINOR"
)

status = TeamStatus(
    wins=8,
    losses=2,
    streak_type="W",
    streak_count=3,
)

# Calculate rating
rating = engine.calculate_overall_rating(
    team_name="Kansas City Chiefs",
    offensive=offensive,
    defensive=defensive,
    injury=injury,
    status=status,
    week=12,
    season=2025,
    massey_rating=None,  # Optional comparison
)

print(f"KC Rating: {rating.overall_rating}")
for component in rating.components:
    print(f"  {component.component}: {component.rating_contribution:+.1f}")

# Calculate spread
spread = engine.calculate_spread("Kansas City", "Buffalo", include_home_field=True)
print(f"KC favored by {spread}")
```

## Validation & Comparison

### Massey Differential

Compare custom ratings against Massey for accuracy checks:

```python
rating = engine.get_rating("Kansas City")
print(f"Custom: {rating.overall_rating}")
print(f"Massey: {rating.massey_rating}")
print(f"Differential: {rating.massey_differential:+.1f}")
```

### Identifying Outliers

Ratings differing by >2 points from Massey:

```python
comparison = engine.compare_with_massey()
for outlier in comparison['outliers']:
    print(f"{outlier['team']}: "
          f"Custom {outlier['custom']:.1f}, "
          f"Massey {outlier['massey']:.1f}, "
          f"Diff {outlier['difference']:+.1f}")
```

## Billy Walters Principles Embedded

1. **Information Edge:** Build your own formula, don't follow consensus
2. **Transparency:** Every rating has a documented calculation
3. **Recent Performance:** Momentum and injury status weighted 30% combined
4. **Defensive Strength:** Defense valued equally with offense (25% vs 30%)
5. **Injury Impact:** Position-specific, not generic
6. **Comparison:** Always validate against independent sources
7. **Discipline:** Strict calculation methodology, no arbitrary adjustments

## Tuning & Customization

### Adjusting Component Weights

Modify weights in `calculate_overall_rating()` method based on your analysis:

```python
# Example: Emphasize recent form
weighted_rating = (
    (off_rating * 0.25) +      # Down from 0.30
    (def_rating * 0.20) +      # Down from 0.25
    (inj_rating * 0.15) +
    (mom_rating * 0.25) +      # Up from 0.15 (emphasize streak/record)
    (hf_rating * 0.15)
)
```

### Adjusting Injury Impact Values

Update NFL_INJURY_IMPACTS or NCAAF_INJURY_IMPACTS dictionaries:

```python
# Example: QB injuries more impactful
NFL_INJURY_IMPACTS = {
    "QB": {"ELITE": 5.0, "STARTER": 3.0},  # Up from 4.5, 2.5
    # ... rest of positions
}
```

### Adjusting Baselines

Modify league-specific constants for different seasons:

```python
# If 2026 season has higher scoring
NCAAF_INJURY_IMPACTS["PPG_BASELINE"] = 31.0  # Up from 28.5
```

## Performance Tracking

### Weekly Update Cycle

1. **Tuesday:** Collect ESPN data, generate ratings
2. **Wednesday:** Compare against Massey, identify edges
3. **Thursday:** Update for Thursday Night Football
4. **Sunday Evening:** After games complete, measure accuracy
5. **Monday:** Document lessons learned

### Metrics to Track

- **Spread Accuracy:** Predicted vs actual closing line
- **CLV (Closing Line Value):** Edge strength validation
- **Massey Differential:** Are your ratings better?
- **Component Accuracy:** Which factors predict best?

## Files & Locations

| File | Purpose |
|------|---------|
| `src/walters_analyzer/valuation/custom_power_rating_engine.py` | Core engine implementation |
| `scripts/database/generate_custom_power_ratings.py` | Rating generator script |
| `database/schema.sql` | ESPN category tables |

## Next Steps

1. **Populate ESPN Data:** Run ESPN loaders for Week 12
2. **Generate Ratings:** Run rating generator
3. **Validate Accuracy:** Compare spreads vs market lines
4. **Integrate with Edge Detection:** Use custom ratings instead of Massey
5. **Track Performance:** Measure CLV weekly

---

**Philosophy:** This is YOUR formula, built on YOUR understanding of football analytics. Trust the data, validate constantly, adjust based on results.
