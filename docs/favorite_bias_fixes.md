# Fixing the Systematic Favorite Bias

## Problem Summary
- Favorites overestimated by avg 2.4 pts (1-6 record, 14.3%)
- Underdogs underestimated by avg 2.5 pts (2-6 record, 25.0%)
- Total systematic bias: ~5 points in favor direction

## Root Causes

### 1. Home Field Advantage Too High (MOST LIKELY)
**Current:** Using 3.5 points for all NCAAF games
**Problem:** This might be inflated, especially for:
- Non-power conference teams
- Late season games
- Neutral site games

### 2. Power Ratings Don't Account for Regression
**Problem:** Extreme ratings (very high/low) don't regress to mean
- Alabama rated too high based on pre-season hype
- G5 teams (UAB, Sam Houston) overvalued

### 3. Margin of Victory Bias
**Problem:** Massey composite includes MOV-based systems
- Teams that run up scores look better than they are
- Doesn't predict close games well

### 4. Stale Ratings
**Problem:** Using season-long ratings in Week 12
- Teams change throughout season
- Need recency weighting

### 5. No Respect for the Market
**Problem:** When our edge is >7 pts, we're probably wrong
- Market processes more information than we have
- Large disagreements = red flag, not opportunity

---

## Solutions (By Impact)

### Solution 1: Reduce Home Field Advantage ⭐⭐⭐⭐⭐
**Impact: HIGH | Effort: LOW**

```python
# Current (in billy_walters_edge_detector.py)
HFA_NCAAF = 3.5

# Fix 1A: Reduce to 2.5 (closer to NFL)
HFA_NCAAF = 2.5

# Fix 1B: Make HFA conference-specific
HFA_BY_CONFERENCE = {
    'SEC': 3.0,      # Strong home field
    'Big Ten': 3.0,
    'Big 12': 2.5,
    'ACC': 2.5,
    'Pac-12': 2.0,   # West coast, less travel impact
    'AAC': 2.0,      # G5 conferences
    'Sun Belt': 2.0,
    'MAC': 2.0,
    'C-USA': 2.0,
    'MWC': 2.0,
}

# Fix 1C: Make HFA team-specific (use historical data)
# Top 25 teams might have 4.0 HFA
# Mid-tier teams: 2.5 HFA
# Bottom teams: 1.5 HFA
```

**Action:** Change line 47 in `src/walters_analyzer/valuation/billy_walters_edge_detector.py`

---

### Solution 2: Add Regression to the Mean ⭐⭐⭐⭐
**Impact: HIGH | Effort: MEDIUM**

```python
def regress_power_rating(rating, games_played, league_avg=50.0):
    """
    Regress extreme ratings toward the mean

    More regression early in season, less late
    More regression for extreme ratings
    """
    # Regression factor (0 = full regression, 1 = no regression)
    # Based on sample size
    confidence = min(games_played / 12, 1.0)  # Full confidence at 12 games

    # Additional regression for extreme ratings
    distance_from_mean = abs(rating - league_avg)
    if distance_from_mean > 20:
        confidence *= 0.9  # 10% more regression for extremes
    if distance_from_mean > 30:
        confidence *= 0.8  # 20% more for very extreme

    # Regressed rating
    regressed = (rating * confidence) + (league_avg * (1 - confidence))

    return regressed

# Usage in edge detector
away_rating_regressed = regress_power_rating(away_rating, games_played=11)
home_rating_regressed = regress_power_rating(home_rating, games_played=11)
```

**Result:** Alabama (rated 85) → regressed to 78, reducing overconfidence

---

### Solution 3: Add Market Respect Threshold ⭐⭐⭐⭐⭐
**Impact: HIGH | Effort: LOW**

```python
# In edge detection logic
def classify_edge(edge_abs, predicted_line, market_line):
    """
    Classify edge with market respect

    If edge is very large, downgrade classification
    Market is probably right
    """
    # Original classification
    if edge_abs >= 7:
        classification = "MAX BET"
    elif edge_abs >= 4:
        classification = "STRONG"
    # ... etc

    # MARKET RESPECT ADJUSTMENT
    # If edge > 7 points, we're probably wrong - downgrade or skip
    if edge_abs > 10:
        return None  # DON'T BET - too suspicious
    elif edge_abs > 7:
        # Downgrade MAX BET → STRONG
        if classification == "MAX BET":
            classification = "STRONG"

    return classification
```

**Result:** Would have skipped Sam Houston -9.5 (12.1 edge) entirely

---

### Solution 4: Add Recency Weighting ⭐⭐⭐
**Impact: MEDIUM | Effort: MEDIUM**

```python
def get_recent_weighted_rating(team_id, current_week):
    """
    Weight recent games more heavily

    Last 3 games: 50% weight
    Games 4-6: 30% weight
    Games 7-12: 20% weight
    """
    # Get game-by-game results
    recent_ratings = get_team_weekly_ratings(team_id, weeks=[9, 10, 11])
    mid_ratings = get_team_weekly_ratings(team_id, weeks=[6, 7, 8])
    early_ratings = get_team_weekly_ratings(team_id, weeks=[1, 2, 3, 4, 5])

    weighted_rating = (
        recent_ratings * 0.50 +
        mid_ratings * 0.30 +
        early_ratings * 0.20
    )

    return weighted_rating
```

**Requires:** Historical power ratings by week (not just current)

---

### Solution 5: Situational Adjustments ⭐⭐⭐
**Impact: MEDIUM | Effort: MEDIUM**

```python
def apply_situational_adjustments(predicted_spread, game_info):
    """
    Adjust for game-specific situations
    """
    adjustment = 0

    # Thursday night road favorite (Troy @ ODU)
    if game_info['day_of_week'] == 'Thursday' and predicted_spread < -3:
        adjustment -= 2.0  # Reduce favorite strength

    # Rivalry game (reduce favorite edge)
    if game_info['is_rivalry']:
        adjustment -= 1.5

    # Lookahead spot (big game next week)
    if game_info['has_lookahead']:
        adjustment -= 1.0

    # Letdown spot (big win last week)
    if game_info['is_letdown']:
        adjustment -= 1.0

    # Bowl eligibility desperation (6-5 team needs win)
    if game_info['underdog_needs_bowl']:
        adjustment += 2.0  # Boost underdog

    return predicted_spread + adjustment
```

---

### Solution 6: Separate Favorite/Underdog Calibration ⭐⭐⭐⭐
**Impact: HIGH | Effort: LOW**

```python
# Simple fix: Apply systematic bias correction

def apply_bias_correction(predicted_spread, our_team_is_favorite):
    """
    Correct for known systematic biases

    Based on historical analysis showing:
    - Favorites overestimated by ~2.4 pts
    - Underdogs underestimated by ~2.5 pts
    """
    if our_team_is_favorite:
        # We're betting the favorite - reduce their strength
        corrected_spread = predicted_spread * 0.85  # 15% haircut
    else:
        # We're betting the underdog - boost their strength
        corrected_spread = predicted_spread * 1.15  # 15% bonus

    return corrected_spread

# Example:
# Predicted: Alabama -12, Market: -6, Edge: 6 pts (bet Alabama)
# Corrected: Alabama -10.2, Market: -6, Edge: 4.2 pts (STRONG instead of STRONG)
```

---

### Solution 7: Blend with Market Consensus ⭐⭐⭐⭐
**Impact: HIGH | Effort: LOW**

```python
def blend_with_market(our_prediction, market_line, confidence=0.7):
    """
    Blend our prediction with market consensus

    Market processes more info than we have
    Use as sanity check
    """
    # If we're very confident (small edge), use our number
    # If we're uncertain (large edge), trust market more

    edge = abs(our_prediction - market_line)

    if edge < 3:
        # Small disagreement - use our prediction
        blend_factor = confidence  # 70% us, 30% market
    elif edge < 5:
        # Medium disagreement - blend equally
        blend_factor = 0.5
    elif edge < 7:
        # Large disagreement - trust market more
        blend_factor = 0.3  # 30% us, 70% market
    else:
        # Huge disagreement - mostly trust market
        blend_factor = 0.1  # 10% us, 90% market

    blended = (our_prediction * blend_factor) + (market_line * (1 - blend_factor))

    return blended

# Example:
# Our prediction: Sam Houston -12.6, Market: -9.5, Edge: 3.1
# Huge edge = suspicious
# Blended: (-12.6 * 0.1) + (-9.5 * 0.9) = -9.81
# New edge: 0.31 pts → NO BET
```

---

## Implementation Priority

### Phase 1: Quick Fixes (This Week) ✅
1. **Reduce HFA to 2.5** (5 min)
2. **Add market respect threshold** (10 min)
3. **Apply bias correction factor** (10 min)

### Phase 2: Data Enhancements (Next Week)
4. **Add regression to mean** (1 hour)
5. **Implement market blending** (1 hour)

### Phase 3: Advanced Features (Next Month)
6. **Recency weighting** (requires weekly ratings data)
7. **Situational adjustments** (requires game context data)

---

## Expected Impact

**Current Performance:** 3-12 (20%)

**With Phase 1 Fixes:**
- Estimated: 6-9 (40%) - Still below expected but manageable
- Would have filtered out: Sam Houston (12.1 edge too high)
- Would have reduced: Alabama, UAB, Navy edges significantly

**With Phase 2 Fixes:**
- Estimated: 7-8 (47%) - Approaching break-even
- Better calibrated edge sizing

**With Phase 3 Fixes:**
- Estimated: 8-7 (53%) - Slight profit
- Long-term sustainable model

---

## Testing Methodology

1. **Backtest on 2024 Season**
   - Apply each fix to historical data
   - Measure impact on win rate and CLV
   - Validate improvements are real

2. **Track Separately**
   - Old model vs new model
   - Measure CLV difference
   - Iterate based on results

3. **Sample Size**
   - Need 100+ bets to validate
   - Track full 2025 season
   - Adjust quarterly based on results

---

## Code Changes Required

**File:** `src/walters_analyzer/valuation/billy_walters_edge_detector.py`

**Changes:**
- Line 47: HFA_NCAAF = 2.5 (down from 3.5)
- Line ~200: Add `regress_power_rating()` function
- Line ~400: Add `apply_bias_correction()` function
- Line ~600: Add market respect threshold in classification
- Line ~800: Add `blend_with_market()` optional feature

**Estimated total:** 50 lines of code, 2 hours work
