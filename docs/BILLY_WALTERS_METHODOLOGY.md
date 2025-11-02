# Billy Walters Methodology - Implementation Guide

This document explains the Billy Walters sports betting methodology as implemented in this codebase, based on his Advanced Masterclass principles.

## Table of Contents

1. [Core Philosophy](#core-philosophy)
2. [Power Ratings](#power-ratings)
3. [S/W/E Factor System](#swe-factor-system)
4. [Key Numbers](#key-numbers)
5. [Star System & Bet Sizing](#star-system--bet-sizing)
6. [Closing Line Value (CLV)](#closing-line-value-clv)
7. [Complete Workflow](#complete-workflow)

---

## Core Philosophy

Billy Walters' approach is **data-driven, systematic, and disciplined**:

1. **Power Ratings**: Objective team strength measurements
2. **Situational Analysis**: Context matters (rest, travel, motivation)
3. **Key Numbers**: Understanding half-point value
4. **Bet Sizing**: Risk management through star system
5. **CLV Tracking**: Validation that you're beating the market

> **"If you consistently beat the closing line, you will be profitable long-term."** - Billy Walters

---

## Power Ratings

### Formula

```
new_rating = (old_rating × 0.9) + (true_game_performance × 0.1)
```

### True Game Performance

```
true_performance = score_differential +
                   opponent_rating +
                   injury_differential -
                   home_field_adjustment
```

### Home Field Advantage

- **NFL**: 2.5 points
- **CFB**: 3.5 points (larger due to crowd/environment)

### Example

Alabama beats Georgia 42-35 at home:

```python
score_diff = 42 - 35 = 7
opponent_rating = 85.0  # Georgia is elite
injury_diff = 0
home_field = -3.5  # Subtract because Alabama had advantage

true_performance = 7 + 85.0 + 0 - (-3.5) = 95.5

If Alabama's old rating was 80:
new_rating = (80 × 0.9) + (95.5 × 0.1)
new_rating = 72 + 9.55 = 81.55
```

### Implementation

```python
from walters_analyzer.power_ratings import PowerRatingEngine, GameResult

engine = PowerRatingEngine()

game = GameResult(
    team="Alabama",
    opponent="Georgia",
    team_score=42,
    opponent_score=35,
    is_home=True,
    sport="cfb",
    date="2024-11-09"
)

rating = engine.update_rating(game)
print(f"New rating: {rating.rating}")
```

---

## S/W/E Factor System

### Situational Factors (S)

**Rule: 5 S-factor points = 1 point spread adjustment**

| Factor | Points | Description |
|--------|--------|-------------|
| Rest advantage (3+ days) | 3 | Significant rest edge |
| Rest advantage (2 days) | 2 | Moderate rest edge |
| Rest advantage (1 day) | 1 | Small rest edge |
| Cross-country travel | -3 | 3+ time zones |
| Very long travel (2000+ mi) | -2 | Major travel fatigue |
| Long travel (1000+ mi) | -1 | Travel fatigue |
| Rivalry game | 2 | Intense motivation |
| Revenge game | 2 | Motivation from recent loss |
| Divisional game | 1 | Familiarity, intensity |
| ATS hot streak (4-1, 5-0) | 2 | Momentum |
| ATS cold streak (0-5, 1-4) | -2 | Negative momentum |

### Weather Factors (W)

Weather primarily affects **totals**, not spreads (both teams affected equally).

| Condition | Impact | Total Adjustment |
|-----------|--------|------------------|
| Extreme wind (25+ mph) | 40 pts | -7.0 points |
| High wind (20-25 mph) | 30 pts | -5.0 points |
| Moderate wind (15-20 mph) | 20 pts | -3.0 points |
| Heavy snow (50%+ prob) | 35 pts | Included above |
| Heavy rain (50%+ prob) | 25 pts | Included above |
| Extreme cold (<20°F) | 20 pts | -3.0 points |
| Dome game | 0 pts | No adjustment |

### Emotional Factors (E)

**Rule: 5 E-factor points = 1 point spread adjustment** (same as S)

| Factor | Points | Description |
|--------|--------|-------------|
| Playoff elimination game | 5 | Must-win situation |
| Playoff clinch game | 3 | Can clinch playoff spot |
| Playoff seeding | 2 | Seeding implications |
| New coach (first season) | 2 | Fresh motivation |
| Star player return | 1 | Emotional lift |

### Example

```python
from walters_analyzer.situational_factors import SWEFactorCalculator, GameContext

context = GameContext(
    team="Alabama",
    opponent="LSU",
    sport="cfb",
    is_home=False,
    game_date="2024-11-09",

    # S-factors
    team_rest_days=7,
    opponent_rest_days=7,
    is_rivalry=True,  # +2 points
    team_ats_last_5=3,  # 3-2 ATS, +1 point

    # E-factors
    playoff_implications="seeding",  # +2 points

    # W-factors
    wind_speed_mph=8,  # Low wind, no impact
)

calculator = SWEFactorCalculator()
result = calculator.calculate_all_factors(context)

print(f"S-factors: {result['s_factors']['total_points']} pts")  # 3 points
print(f"E-factors: {result['e_factors']['total_points']} pts")  # 2 points
print(f"Total spread adjustment: {result['total_spread_adjustment']}")  # 1.0 (5 points / 5)
```

---

## Key Numbers

Key numbers are margins that occur more frequently than others. Understanding their value is **critical** for evaluating half-points.

### NFL Key Numbers

| Number | Frequency | Value | Why? |
|--------|-----------|-------|------|
| 3 | 8.0% | **Highest** | Field goal |
| 7 | 6.0% | **2nd** | Touchdown + XP |
| 6 | 5.0% | Important | Two field goals |
| 10 | 4.5% | Important | TD + FG |
| 14 | 5.0% | Important | Two TDs |

### CFB Key Numbers

CFB has **lower** key number values due to more variance:

| Number | Frequency | Value |
|--------|-----------|-------|
| 3 | 7.0% | Lower than NFL |
| 7 | 5.0% | Lower than NFL |
| 6 | 4.5% | Lower than NFL |

### Buying Half-Points

**Billy Walters Rule**: Only buy half-points if the **value > cost**

Example: Should you buy from -3.0 to -2.5?

```
Value of crossing 3: 8% (in NFL)
Cost of 20 cents (−110 to −130): ~4%

8% > 4% → YES, BUY
```

### Bet Timing

**"Bet favorites early, dogs late"** - Billy Walters

- **Favorites**: Public bets them → line moves up → lock in early
- **Dogs**: Public avoids them → line may improve → wait if possible

### Implementation

```python
from walters_analyzer.key_numbers import KeyNumberCalculator

calc = KeyNumberCalculator()

# Calculate edge
analysis = calc.calculate_edge_value(
    your_line=-2.5,  # Your prediction
    market_line=-3.5,  # Market line
    sport='nfl'
)

print(f"Key numbers crossed: {analysis.key_numbers_crossed}")  # [3]
print(f"Edge percentage: {analysis.edge_percentage}%")  # ~8%

# Should you buy half-point?
buy_analysis = calc.should_buy_half_point(-3.0, price_diff=20, sport='nfl')
print(f"Should buy: {buy_analysis['recommendation']}")  # BUY
```

---

## Star System & Bet Sizing

Billy Walters uses a **star system** to size bets based on edge:

### Star Thresholds

| Edge | Stars | Bet Size | Confidence |
|------|-------|----------|------------|
| 15%+ | 3.0 | 3% bankroll | Very High |
| 13-15% | 2.5 | 2.5% bankroll | High |
| 11-13% | 2.0 | 2% bankroll | High |
| 9-11% | 1.5 | 1.5% bankroll | Medium |
| 7-9% | 1.0 | 1% bankroll | Medium |
| 5.5-7% | 0.5 | 0.5% bankroll | Low |
| <5.5% | 0.0 | **NO BET** | None |

### Kelly Criterion

The system also supports **Kelly Criterion** for mathematical optimization:

```
Kelly % = (bp - q) / b

Where:
  b = decimal odds
  p = win probability
  q = loss probability (1 - p)
```

**Fractional Kelly** (25%) is used for risk management - full Kelly is too aggressive.

### Implementation

```python
from walters_analyzer.bet_sizing import BetSizingCalculator

calc = BetSizingCalculator(bankroll=10000)

# Calculate bet size
sizing = calc.calculate_bet_size(
    edge_percentage=0.08,  # 8% edge
    price=-110
)

print(f"Stars: {sizing['stars']}")  # 1.0
print(f"Bet amount: ${sizing['bet_amount']}")  # $100 (1% of $10k)
print(f"Expected value: ${sizing['expected_value']}")  # ~$7.27
```

---

## Closing Line Value (CLV)

**CLV is the gold standard for measuring betting skill.**

### What is CLV?

```
CLV = Closing Line - Your Line
```

- **Positive CLV**: You got a better line than the closing line (sharp)
- **Negative CLV**: You got a worse line (recreational)

### Why CLV Matters

> "You can lose in the short-term with positive CLV and still be a winning bettor long-term. Conversely, you can win in the short-term with negative CLV and be a losing bettor." - Billy Walters

**Example:**

```
You bet: Cowboys -3.0 at -110
Closing line: Cowboys -3.5

CLV = -3.5 - (-3.0) = -0.5 (you got Cowboys at a better price!)
```

Even if Cowboys win by exactly 3 (you push), you still have **positive CLV** because the market moved against you.

### Tracking CLV

```python
from walters_analyzer.clv_tracker import CLVTracker

tracker = CLVTracker()

# Log bet when placed
bet_id = tracker.log_bet(
    game="Cowboys @ Giants",
    game_date="2024-11-10",
    sport="nfl",
    bet_type="spread",
    side="away",
    your_line=-3.0,
    opening_line=-2.5,
    price=-110,
    edge_percentage=0.08,
    stars=1.0,
    bet_amount=100,
    bankroll=10000
)

# Update closing line (after game starts)
tracker.update_closing_line(bet_id, closing_line=-3.5)

# Update result (after game ends)
tracker.update_result(bet_id, result="win", profit=90.91)

# Get CLV stats
stats = tracker.get_clv_stats()
print(f"Average CLV: {stats['avg_clv']} points")
print(f"Beating close: {stats['pct_beating_close']}%")
```

### Target Metrics

- **Average CLV**: > 0 (positive)
- **% Beating Close**: > 50%
- **Win Rate**: > 52.38% (to overcome -110 juice)

---

## Complete Workflow

### 1. Build Power Ratings

```python
from walters_analyzer.power_ratings import PowerRatingEngine, GameResult

engine = PowerRatingEngine()

# Update ratings after each game
game = GameResult("Alabama", "LSU", 42, 35, True, "cfb", "2024-11-09")
engine.update_rating(game)
```

### 2. Calculate S/W/E Factors

```python
from walters_analyzer.situational_factors import SWEFactorCalculator, GameContext

context = GameContext(
    team="Alabama",
    opponent="LSU",
    sport="cfb",
    is_home=False,
    game_date="2024-11-16",
    is_rivalry=True,
    playoff_implications="seeding",
    wind_speed_mph=12
)

calculator = SWEFactorCalculator()
factors = calculator.calculate_all_factors(context)
```

### 3. Analyze Game

```python
from walters_analyzer.analyzer import BillyWaltersAnalyzer

analyzer = BillyWaltersAnalyzer(bankroll=10000)

analysis = analyzer.analyze_game(
    away_team="Alabama",
    home_team="LSU",
    sport="cfb",
    market_spread=-3.0,
    game_context=context,
    game_date="2024-11-16"
)

if analysis.should_bet:
    print(f"{analysis.recommendation.stars}⭐ BET ${analysis.recommendation.bet_amount}")
```

### 4. Place Bet & Track CLV

```python
if analysis.should_bet:
    bet_id = analyzer.place_bet(analysis, game_date="2024-11-16")

    # After game starts
    analyzer.update_game_result(
        bet_id=bet_id,
        closing_line=-3.5,
        actual_result="win",
        profit=90.91
    )
```

### 5. Monitor Performance

```python
report = analyzer.get_performance_report()
print(report)
```

---

## Best Practices

### 1. **Discipline**
- Only bet when edge ≥ 5.5% (0.5 stars minimum)
- Never bet more than star system recommends
- Never chase losses

### 2. **Data Quality**
- Update power ratings after every game
- Verify injury reports before betting
- Check weather forecasts for outdoor games
- Monitor line movements

### 3. **Record Keeping**
- Log every bet in CLV tracker
- Track opening and closing lines
- Review weekly performance
- Adjust thresholds based on results

### 4. **Bankroll Management**
- Use fractional Kelly (25%) or star system
- Never risk more than 5% on single bet
- Adjust unit size as bankroll changes
- Keep 3-6 months of expenses as buffer

### 5. **Continuous Improvement**
- Backtest strategy on historical data
- Validate S/W/E factor weights empirically
- Compare your ratings to market (Massey, etc.)
- Track CLV religiously

---

## Example: Complete Game Analysis

**Game**: Alabama @ LSU (Nov 16, 2024)

**Market**: Alabama -3.0 (-110)

### Step 1: Power Ratings

```
Alabama rating: 82.5
LSU rating: 78.0
Rating differential: +4.5 (Alabama advantage)
Home field (LSU): +3.5
Predicted spread: -1.0 (Alabama favored by 1)
Market spread: -3.0
Raw edge: 2.0 points
```

### Step 2: S/W/E Factors

```
S-factors:
  - Rivalry game: +2 points
  - Alabama ATS 3-2 last 5: +1 point
  Total: 3 points → +0.6 spread adjustment

E-factors:
  - Playoff seeding implications: +2 points
  Total: 2 points → +0.4 spread adjustment

W-factors:
  - Wind 12 mph, temp 68°F → No significant impact

Total adjustment: +1.0 points (favors Alabama)
```

### Step 3: Adjusted Prediction

```
Predicted spread: -1.0 (from ratings)
S/W/E adjustment: +1.0 (favors Alabama)
Final prediction: -2.0 (Alabama by 2)

Market: -3.0
Edge: 1.0 point
```

### Step 4: Key Numbers

```
Your line: -2.0
Market: -3.0
Key numbers crossed: [3]
Key 3 value: 8% (NFL), 7% (CFB)

Edge percentage: ~7%
```

### Step 5: Bet Recommendation

```
Edge: 7% → 1.0 STAR
Bankroll: $10,000
Bet size: 1% = $100
Confidence: Medium

Recommendation: BET LSU +3.0 for $100
```

### Step 6: Track Result

```
Opening: Alabama -3.0
Closing: Alabama -3.5
CLV: +0.5 points (you beat the close!)

Final score: Alabama 42, LSU 38
Result: LSU +3 WINS (42-38 = 4 > 3)
Profit: $90.91
```

---

## Resources

- **Billy Walters Advanced Masterclass**: Original source material
- **Power Ratings Module**: [`walters_analyzer/power_ratings.py`](../walters_analyzer/power_ratings.py)
- **S/W/E Factors Module**: [`walters_analyzer/situational_factors.py`](../walters_analyzer/situational_factors.py)
- **Key Numbers Module**: [`walters_analyzer/key_numbers.py`](../walters_analyzer/key_numbers.py)
- **Bet Sizing Module**: [`walters_analyzer/bet_sizing.py`](../walters_analyzer/bet_sizing.py)
- **CLV Tracker Module**: [`walters_analyzer/clv_tracker.py`](../walters_analyzer/clv_tracker.py)
- **Complete Example**: [`examples/complete_workflow_example.py`](../examples/complete_workflow_example.py)

---

## Questions?

This methodology is **proven over 40+ years** of Billy Walters' career. Trust the process:

1. Build accurate power ratings
2. Factor in situational context (S/W/E)
3. Understand key number value
4. Size bets appropriately (star system)
5. Validate with CLV tracking

**Discipline + Data + Long-term thinking = Success**
