# NCAAF Edge Detection System Design

**Date**: 2025-11-23
**Status**: Design Phase (Ready for Implementation)
**Scope**: Production-ready NCAAF edge detection system (separate from NFL)

---

## Executive Summary

This document outlines the architecture for implementing NCAAF (NCAA college football) edge detection as a parallel system to the existing NFL implementation. The system will follow the same Billy Walters methodology but account for key differences in college football:

- **Different schedule**: Multiple game times on Thursday/Saturday (not weekly)
- **Different spreads**: College lines vary more widely due to skill disparity
- **Different data sources**: ESPN Massey ratings for NCAAF, action network for sharp indicators
- **Roster turnover**: Graduation impacts carry more weight than NFL trades
- **Conference dynamics**: Conference affiliation affects scheduling and strength of schedule

---

## System Architecture

### 1. League Separation Strategy

**Keep NFL and NCAAF completely separate:**

```
Edge Detection Pipeline:
├── NFL Path
│   ├── Input: NFL power ratings (Massey)
│   ├── Input: NFL odds (Overtime.ag)
│   ├── Input: NFL schedule (ESPN)
│   ├── Input: NFL injuries (NFL.com, ESPN)
│   ├── Processing: NFL edge detector logic
│   └── Output: output/edge_detection/nfl_edges_detected_week_12.jsonl
│
└── NCAAF Path
    ├── Input: NCAAF power ratings (Massey)
    ├── Input: NCAAF odds (Overtime.ag)
    ├── Input: NCAAF schedule (ESPN)
    ├── Input: NCAAF injuries (ESPN)
    ├── Processing: NCAAF edge detector logic
    └── Output: output/edge_detection/ncaaf_edges_detected_week_13.jsonl
```

**Rationale for Separation:**
1. **Week numbering is different**: NFL has weeks 1-18; NCAAF has variable scheduling
2. **Game times are different**: NFL is mostly Thursday/Sunday/Monday; NCAAF has Thursday/Friday/Saturday
3. **Power ratings scale differently**: College football has larger spreads (10+ points common)
4. **Data sources differ**: Different injury databases, different schedule formats
5. **Cleanest implementation**: Minimal coupling, easier to maintain and debug

### 2. Data Model Alignment

Use the same `BettingEdge` dataclass from NFL implementation but with NCAAF-specific values:

```python
@dataclass
class BettingEdge:
    # Common Fields
    game_id: str                          # e.g., "114561232"
    matchup: str                          # e.g., "Ohio State @ Michigan"
    week: int                             # For NCAAF: season week (e.g., 13)
    game_time: str                        # ISO format: "2025-11-29T15:30:00Z"
    away_team: str
    home_team: str

    # Ratings (scaled for college football)
    away_rating: float                    # NCAAF ratings: 60-105 range
    home_rating: float                    # (vs NFL: 70-100)

    # Spread Analysis
    predicted_spread: float               # Our prediction (home favored)
    market_spread: float                  # Vegas line
    market_total: float

    # Edge Identification
    edge_points: float                    # Difference: |predicted - market|
    edge_type: EdgeType
    edge_strength: str                    # "very_strong", "strong", "medium", "weak"

    # Adjustments (NCAAF-specific factors)
    situational_adjustment: float         # Conference games, rest, travel
    weather_adjustment: float             # Much larger impact in college
    emotional_adjustment: float           # Playoff implications, bowl eligibility
    injury_adjustment: float              # Star QB/RB injuries critical

    # Betting Recommendation
    recommended_bet: Optional[str]        # "away", "home", None
    kelly_fraction: float                 # 0-0.25
    confidence_score: float               # 0-100

    # Metadata
    data_sources: List[str]
    timestamp: str
```

---

## Data Collection Requirements

### 1. Power Ratings

**Source**: ESPN Massey Ratings (via existing API integration)

**NCAAF-Specific Adjustments**:
- Scale ratings to 60-105 range (vs NFL's 70-100)
- Account for strength of schedule (SOS) adjustments
- Home field advantage: +2.5 to +4.5 points (higher than NFL's +3)
- Recency bias: Recent games weighted more heavily

**Data File**:
```
data/current/massey_ratings_ncaaf.json
```

### 2. Game Schedules

**Source**: ESPN NCAAF schedule API

**Required Fields**:
- Game ID (ESPN format)
- Away team, Home team
- Game time (ISO format with timezone)
- Conference information
- Current week number

**Data File**:
```
data/current/ncaaf_week_13_games.json
```

### 3. Betting Odds

**Source**: Overtime.ag API (existing integration)

**Output Format** (Already standardized):
```json
{
  "game_id": "114561232",
  "league": "NCAAF",
  "away_team": "Ohio State",
  "home_team": "Michigan",
  "spread": {
    "away": 2.5,
    "home": -2.5,
    "away_odds": -110,
    "home_odds": -110
  },
  "total": {
    "points": 52.0,
    "over_odds": -110,
    "under_odds": -110
  }
}
```

**File**:
```
output/overtime/ncaaf/pregame/api_walters_20251122_131520.json
```

### 4. Injury Data

**Source**: ESPN NCAAF injury reports

**NCAAF-Specific Injury Values**:
```python
NCAAF_INJURY_VALUES = {
    # Quarterbacks (much more critical in college)
    "QB_ELITE": 5.0,              # Top-tier starter
    "QB_STARTER": 3.5,            # Primary backup
    "QB_BACKUP": 1.0,

    # Running Backs
    "RB_ELITE": 3.5,              # Elite every-down back
    "RB_STARTER": 2.0,
    "RB_BACKUP": 0.5,

    # Wide Receivers
    "WR_ELITE": 2.5,              # Top target
    "WR_STARTER": 1.5,
    "WR_BACKUP": 0.3,

    # Offensive Line (group adjustments more important)
    "OL_ELITE": 1.5,              # Key anchor
    "OL_STARTER": 1.0,
    "OL_BACKUP": 0.3,

    # Defensive Line
    "DL_ELITE": 2.0,              # Pass rush leader
    "DL_STARTER": 1.2,
    "DL_BACKUP": 0.3,

    # Linebackers
    "LB_ELITE": 1.8,              # Coverage leader
    "LB_STARTER": 1.0,
    "LB_BACKUP": 0.3,

    # Defensive Backs
    "DB_ELITE": 1.5,              # Top cornerback
    "DB_STARTER": 0.8,
    "DB_BACKUP": 0.2,
}
```

**Key Differences from NFL**:
- College QBs are more impactful (5.0 pts vs NFL's 4.5)
- Less roster depth: backups are significantly worse
- Younger players: more inconsistent performance with injuries

### 5. Weather Data

**Source**: AccuWeather (existing integration)

**NCAAF-Specific Factors**:
- Larger impact due to varying stadium quality
- More outdoor stadiums than NFL
- Regional weather patterns more severe (cold northern schools vs warm southern)

**Billy Walters NCAAF Weather Adjustments**:
```
Wind Speed Impact (GREATER than NFL):
- >20 mph: -6 points to total (vs NFL -5)
- 15-20 mph: -4 points (vs NFL -3)
- 10-15 mph: -2 points (vs NFL -1)

Temperature Impact (Similar to NFL):
- <20°F: -4 pts
- 20-25°F: -3 pts
- 25-32°F: -2 pts
- 32-40°F: -1 pt

Precipitation Impact (SIMILAR):
- Snow >60%: -5 pts
- Rain >60%: -3 pts
```

---

## Edge Detection Logic

### 1. Power Rating Edge (Primary)

```python
# NCAAF Power Rating Calculation
predicted_home_spread = away_rating - home_rating

# Home field advantage (larger in college)
home_field_bonus = 3.5  # vs NFL's 3.0
predicted_home_spread -= home_field_bonus

# Edge Detection
market_spread = -2.5
edge_points = abs(predicted_home_spread - market_spread)  # In favor of away team
edge_type = "power_rating"

# Confidence Mapping (NCAAF calibration)
confidence = min(edge_points * 10.5, 100)  # Calibrated differently than NFL

# Kelly Sizing (Same as NFL)
kelly_fraction = min(edge_points / 20, 0.25)
```

### 2. Situational Factor Adjustments

```python
S_FACTOR_ADJUSTMENTS = {
    # Rest Advantages (similar to NFL)
    "extra_rest": +1.5,        # 8+ days vs opponent's 6
    "short_rest": -2.0,        # <6 days rest
    "equivalent_rest": 0.0,

    # Travel Distance (larger impact in college)
    "long_travel": -1.5,       # >1500 miles
    "medium_travel": -0.8,     # 500-1500 miles
    "short_travel": -0.3,      # <500 miles
    "home_state": 0.0,

    # Conference Dynamics
    "conference_game": +1.0,   # Higher intensity
    "rivalry_game": +1.5,      # Even higher intensity
    "playoff_implications": +1.5,  # Bowl eligibility scenarios

    # Schedule Spot Analysis
    "revenge_spot": +1.2,      # Playing team that beat them
    "lookahead_spot": -2.0,    # Looking ahead to big game
    "letdown_spot": -1.5,      # After emotional win
}
```

### 3. Weather Impact (NCAAF-specific)

```python
async def calculate_weather_adjustment(away_team, home_team, game_time):
    """Calculate NCAAF-specific weather impact"""

    # Different thresholds for college football
    if wind_speed > 20:
        total_adjustment = -6.0  # vs NFL -5.0
    elif wind_speed > 15:
        total_adjustment = -4.0  # vs NFL -3.0
    elif wind_speed > 10:
        total_adjustment = -2.0  # vs NFL -1.0

    # Temperature impact (same as NFL)
    # Spread adjustment (favors run game in bad weather)

    return total_adjustment, spread_adjustment
```

### 4. Injury Impact (NCAAF-specific)

```python
# Key differences:
# 1. Backup quality is much lower in college
# 2. QB injuries are devastating (college game flow dependent)
# 3. Star RB injuries impact team identity
# 4. Offensive line injuries cascade more (less depth)

NCAAF_INJURY_MULTIPLIERS = {
    "elite_starter_loss": 4.5,      # QB, elite RB
    "major_starter_loss": 2.5,      # Good RB, top WR
    "starter_loss": 1.5,            # Role player
    "backup_loss": 0.3,
}
```

### 5. Sharp Action Analysis

**NCAAF-Specific Indicators**:
- Line movement is more volatile (less sharp money)
- Sharp groups have identified NCAAF expertise less
- Reverse line movement more common (public heavy on favorites)
- Mid-week movement often predicts Saturday action

---

## Implementation Architecture

### File Structure

```
src/walters_analyzer/valuation/
├── billy_walters_edge_detector.py          # NFL (existing)
├── ncaaf_edge_detector.py                  # NEW: NCAAF version
├── ncaaf_situational_factors.py            # NEW: NCAAF S-factors
├── ncaaf_injury_impacts.py                 # NEW: NCAAF injury values
└── ... (shared modules)

scripts/analysis/
├── check_betting_results.py                # Works for both leagues
└── analyze_ncaaf_edges.py                  # NEW: NCAAF-specific script

output/edge_detection/
├── nfl_edges_detected_week_12.jsonl        # NFL (existing)
├── ncaaf_edges_detected_week_13.jsonl      # NEW: NCAAF edges
├── nfl_totals_detected_week_12.jsonl       # NFL totals
└── ncaaf_totals_detected_week_13.jsonl     # NEW: NCAAF totals

data/current/
├── nfl_week_12_games.json
├── ncaaf_week_13_games.json                # NEW
├── massey_ratings_nfl.json
├── massey_ratings_ncaaf.json               # Already exists!
├── nfl_week_12_injuries.json
└── ncaaf_week_13_injuries.json             # NEW
```

### Main Detector: `ncaaf_edge_detector.py`

```python
class NCAAFEdgeDetector:
    """College football edge detection system"""

    async def detect_edges(self, week: int) -> List[BettingEdge]:
        """Main method: detect all NCAAF edges for a week"""

        # 1. Load data
        games = await self.load_schedule(week)
        ratings = await self.load_power_ratings()
        odds = await self.load_odds(week)
        injuries = await self.load_injuries(week)
        weather = await self.load_weather(games)

        # 2. Process each game
        edges = []
        for game in games:
            edge = await self.analyze_game(
                game, ratings, odds, injuries, weather
            )
            if edge:
                edges.append(edge)

        # 3. Save results
        await self.save_edges(edges, "ncaaf", week)
        return edges

    async def analyze_game(self, game, ratings, odds, injuries, weather):
        """Analyze single NCAAF game"""

        # Power rating edge
        edge_points = calculate_power_rating_edge(
            game, ratings, home_field_bonus=3.5  # NCAAF-specific
        )

        # Adjustments
        situational = calculate_ncaaf_situational_adjustment(game, week)
        weather_adj = weather.get(game.id, {}).total_adjustment
        injury_adj = injuries_calculator.calculate_impact(
            game.away_team, game.home_team, ncaaf=True
        )

        # Combined edge
        total_edge = edge_points + situational + weather_adj + injury_adj

        # Recommendation
        if total_edge >= NCAAF_EDGE_THRESHOLD:
            return BettingEdge(
                edge_points=total_edge,
                recommended_bet="away" if total_edge > 0 else "home",
                kelly_fraction=calculate_kelly(total_edge),
                confidence_score=calculate_confidence(total_edge),
                # ... other fields
            )
```

---

## Output Format

### NCAAF Edges File: `ncaaf_edges_detected_week_13.jsonl`

Same structure as NFL, one JSON object per line:

```json
{
  "game_id": "114561232",
  "matchup": "Ohio State @ Michigan",
  "week": 13,
  "game_time": "2025-11-29T15:30:00Z",
  "away_team": "Ohio State",
  "home_team": "Michigan",
  "away_rating": 92.5,
  "home_rating": 94.2,
  "predicted_spread": 4.2,
  "market_spread": -2.5,
  "market_total": 52.0,
  "edge_points": 6.7,
  "edge_type": "power_rating",
  "edge_strength": "strong",
  "situational_adjustment": 1.0,
  "weather_adjustment": 0.0,
  "emotional_adjustment": 1.5,
  "injury_adjustment": 0.0,
  "recommended_bet": "away",
  "kelly_fraction": 0.22,
  "confidence_score": 67.0,
  "timestamp": "2025-11-23T05:07:25.113446",
  "data_sources": ["massey", "action_network", "espn_injuries"]
}
```

---

## Integration with Results Checker

The existing `BettingResultsChecker` already supports NCAAF:

```bash
# Check NCAAF results
uv run python scripts/analysis/check_betting_results.py --league ncaaf --week 13

# Output:
# - Fetches actual scores from ESPN
# - Loads predictions from ncaaf_edges_detected_week_13.jsonl
# - Calculates ATS/ROI
# - Generates: docs/performance_reports/REPORT_NCAAF_WEEK13_20251129_150452.md
```

**No modifications needed** - Results Checker already works for both leagues!

---

## Testing Strategy

### Unit Tests

```python
test_ncaaf_edge_detector.py:
    test_power_rating_edge_calculation()
    test_home_field_advantage_ncaaf()
    test_situational_factors_ncaaf()
    test_weather_adjustment_ncaaf()
    test_injury_impact_ncaaf()
    test_confidence_calibration()
    test_kelly_sizing()
```

### Integration Tests

```python
test_ncaaf_edge_detector_integration.py:
    test_load_all_data_ncaaf()
    test_analyze_full_week()
    test_output_file_format()
    test_with_real_week_13_data()
```

### Validation Tests

- Compare predicted spreads with market accuracy
- Validate JSON output format matches expectations
- Ensure all required fields present
- Verify no duplicate games
- Check data types and ranges

---

## Implementation Timeline

### Phase 1: Core System (1-2 hours)
1. Create `ncaaf_edge_detector.py` with basic structure
2. Implement power rating calculation (NCAAF-tuned)
3. Implement situational factors
4. Implement weather adjustments
5. Basic testing

### Phase 2: Integration (1 hour)
1. Wire up to existing data loaders
2. Test with actual Week 13 data
3. Validate output format
4. Test with results checker

### Phase 3: Optimization & Docs (1 hour)
1. Tune confidence/Kelly calculations
2. Performance optimization
3. Documentation
4. Add to `/collect-all-data` workflow

**Total: 3-4 hours for complete production-ready system**

---

## Key Differences from NFL Implementation

| Aspect | NFL | NCAAF |
|--------|-----|-------|
| **Power Rating Scale** | 70-100 | 60-105 |
| **Home Field Bonus** | +3.0 pts | +3.5 pts |
| **Spread Range** | Typically 3-10 pts | Typically 2-20 pts |
| **QB Injury Impact** | 4.5 pts | 5.0 pts |
| **Backup Quality** | Decent | Poor |
| **Roster Depth** | Good | Limited |
| **Weather Impact** | Moderate | Larger |
| **Week Numbering** | 1-18 | Variable (1-15) |
| **Situational Factors** | Rest, travel | Rest, travel, conference, playoff implications |

---

## Success Criteria

1. ✅ NCAAF edges file generated in correct JSONL format
2. ✅ Loads with existing results checker (no modifications)
3. ✅ Matches power rating predictions with reasonable accuracy
4. ✅ 18/18 results checker tests still passing
5. ✅ Documentation complete
6. ✅ Integration with `/collect-all-data` workflow

---

## Future Enhancements

1. **Conference Strength Ratings**: Adjust power ratings based on conference SOS
2. **Portal Transfer Impact**: Account for transfer portal losses
3. **Motivation Analysis**: Bowl eligibility, draft positioning, coaching changes
4. **Consensus Lines**: Monitor multiple sportsbooks for line discrepancies
5. **Sharp Money Tracking**: Identify NCAAF sharp indicators
6. **Historical Backtesting**: Validate NCAAF edge thresholds with past data

---

## References

- Existing NFL Implementation: `src/walters_analyzer/valuation/billy_walters_edge_detector.py`
- Results Checker: `src/walters_analyzer/performance/results_checker.py`
- Data: ESPN Massey Ratings, Overtime.ag API, ESPN schedules/injuries
- Billy Walters Methodology: `docs/guides/BILLY_WALTERS_METHODOLOGY.md`

---

**Document Status**: Ready for Implementation Phase 1
**Last Updated**: 2025-11-23
**Next Step**: Begin coding `ncaaf_edge_detector.py`
