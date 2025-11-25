# Custom Power Rating System - Quick Reference

## Component Weights at a Glance

| Component | Weight | Scale | Key Input |
|-----------|--------|-------|-----------|
| **Offensive Efficiency** | 30% | ±10 | PPG, YPG |
| **Defensive Efficiency** | 25% | ±10 | PAPG, YAPG |
| **Injury Impact** | 15% | -10 to 0 | Position + Severity |
| **Momentum** | 15% | ±5 | W/L Streak + Record |
| **Home Field** | 15% | +3.0/3.5 | Venue Only |

## League Scales

**NFL:**
- Scale: 70-100
- Baseline: 85
- Home Advantage: 3.0 pts

**NCAAF:**
- Scale: 60-105
- Baseline: 80
- Home Advantage: 3.5 pts

## Key Formulas

### Offensive Rating
```
PPG Diff = (Team PPG - League Avg PPG) / League Avg PPG
Rating = (PPG Diff * 10 * 0.6) + (YPG Diff * 10 * 0.4)
```

### Defensive Rating
```
PAPG Diff = (League Avg PAPG - Team PAPG) / League Avg PAPG  [reversed]
Rating = (PAPG Diff * 10 * 0.6) + (YAPG Diff * 10 * 0.4)
```

### Injury Rating
```
Total Impact = Sum(Position Value * Severity)
Injury Rating = -(Total Impact / 2.0)
Max penalty: -10.0
```

### Momentum Rating
```
Streak Pts = min(Streak, 5) * 0.5
Win % Pts = (Win% - 0.5) * 10.0
Momentum = Streak Pts (or -Streak Pts) + Win % Pts
```

### Overall Rating
```
Adjustment = (Off*0.30) + (Def*0.25) + (Inj*0.15) + (Mom*0.15) + (HF*0.15)
Overall = Baseline + Adjustment
```

### Spread
```
Spread = Home Rating - Away Rating + Home Field Advantage
```

## Injury Impact Values

### NFL
| Position | Elite | Starter | Backup |
|----------|-------|---------|--------|
| QB | 4.5 | 2.5 | 0.5 |
| RB | 2.5 | 1.5 | 0.3 |
| WR | 1.8 | 1.0 | 0.2 |
| TE | 1.5 | 0.8 | 0.1 |
| OL | 1.5 | 0.8 | 0.1 |
| DE | 1.5 | 0.8 | 0.1 |
| LB | 1.2 | 0.6 | 0.1 |
| CB | 1.2 | 0.6 | 0.1 |
| S | 1.0 | 0.5 | 0.1 |

### NCAAF (Higher due to depth)
| Position | Elite | Starter | Backup |
|----------|-------|---------|--------|
| QB | 5.0 | 3.0 | 0.8 |
| RB | 3.5 | 2.0 | 0.5 |
| WR | 2.5 | 1.5 | 0.3 |
| TE | 2.0 | 1.2 | 0.2 |
| OL | 1.5 | 1.0 | 0.2 |
| DL | 2.0 | 1.2 | 0.2 |
| LB | 1.8 | 1.0 | 0.2 |
| DB | 1.5 | 0.8 | 0.1 |

## Injury Severity Levels

| Level | Elite Out | Starter Out | Total Impact | Effect |
|-------|-----------|-------------|--------------|--------|
| HEALTHY | 0 | <2 | <2 | No adjustment |
| MINOR | <1 | 2+ | 2-4 | -1 to -2 pts |
| MODERATE | 1 | Any | 4-8 | -2 to -4 pts |
| SEVERE | 2+ | Any | 8+ | -4+ pts |

## League Averages (2025 expected)

**NFL:**
- PPG: 23.0
- YPG: 350.0
- PAPG: 23.0
- YAPG: 350.0

**NCAAF:**
- PPG: 28.5
- YPG: 400.0
- PAPG: 28.5
- YAPG: 400.0

## Common Spreads

### Example Matchups

**Kansas City (Home) vs Buffalo (Away):**
- KC Rating: 87.1
- Buffalo Rating: 85.3
- Spread = 87.1 - 85.3 + 3.0 = 4.8 (KC -4.8)

**Ohio State (Home) vs Michigan (Away):**
- Ohio St: 92.5
- Michigan: 91.8
- Spread = 92.5 - 91.8 + 3.5 = 4.2 (OSU -4.2)

## Usage Commands

### Generate Ratings
```bash
python scripts/database/generate_custom_power_ratings.py
```

### Use Programmatically
```python
from walters_analyzer.valuation.custom_power_rating_engine import (
    CustomPowerRatingEngine, League
)

engine = CustomPowerRatingEngine(league=League.NFL)
spread = engine.calculate_spread("Kansas City", "Buffalo")
```

## Key Takeaways

1. **Offensive > Defensive** in weighting (30% vs 25%)
2. **Recent Form Matters** (Momentum 15% + injury status)
3. **Injuries Position-Specific** (QB much worse than WR)
4. **Home Field Consistent** (+3 to +3.5 pts across all matchups)
5. **Everything Transparent** (see component breakdown)

## Validation Checklist

- [ ] Are custom ratings in 70-100 (NFL) or 60-105 (NCAAF)?
- [ ] Does spread calculation include home field advantage?
- [ ] Are position-specific injury values applied?
- [ ] Is Massey differential tracked for comparison?
- [ ] Are top/bottom teams reasonable?

## Next Steps

1. Load ESPN data (team stats, injuries, standings)
2. Run rating generator
3. Compare spreads vs market lines
4. Track CLV weekly
5. Refine weights based on results

---

**Version:** 1.0 | **Last Updated:** 2025-11-23 | **Status:** Production Ready
