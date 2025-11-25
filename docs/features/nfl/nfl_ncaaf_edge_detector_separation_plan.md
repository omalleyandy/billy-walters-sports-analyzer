# NFL vs NCAAF Edge Detector Separation Plan

## Executive Summary

This document outlines the plan to create separate, optimized edge detectors for NFL and NCAAF, recognizing the fundamental differences between professional and college football betting markets.

---

## Why Separate Detectors?

### Market Efficiency Differences
- **NFL**: Highly efficient market, sharp bettors, small edges
- **NCAAF**: Less efficient market, more public money, larger edges possible

### Structural Differences
- **NFL**: 32 teams, balanced competition, parity
- **NCAAF**: 136 FBS teams, massive talent gaps, conference imbalances

### Data Availability
- **NFL**: Comprehensive injury reports, consistent data quality
- **NCAAF**: Limited injury data, inconsistent reporting

### Home Field Advantage
- **NFL**: 2.5 points (recent trend: <1.0 with COVID)
- **NCAAF**: 2.5 points (previously thought to be 3.5, corrected based on analysis)

---

## Current State Analysis

### Existing Files
1. **`src/walters_analyzer/valuation/billy_walters_edge_detector.py`**
   - Full-featured edge detector
   - Handles both NFL and NCAAF
   - 1,000+ lines of code
   - Supports weather, injuries, situational factors
   - **Status**: Updated with 3 fixes (HFA 2.5, market respect, bias correction)

2. **`scripts/analysis/analyze_ncaaf_edges.py`**
   - Simpler NCAAF-specific script
   - ~450 lines of code
   - Basic power rating + odds analysis
   - **Status**: Updated with 3 fixes

3. **`src/walters_analyzer/valuation/billy_walters_totals_detector.py`**
   - Totals (over/under) edge detector
   - League-agnostic
   - **Status**: Needs review/update

### Problems with Current Approach
1. **Single detector trying to handle two different sports**
   - NFL logic mixed with NCAAF logic
   - Hard to optimize for each sport
   - Different constants buried in code

2. **Inconsistent HFA handling**
   - Was using 2.5 for NFL, 3.5 for NCAAF (now both 2.5)
   - Should be more flexible/configurable

3. **Missing league-specific optimizations**
   - NCAAF: Conference strength adjustments
   - NFL: Key number awareness (3, 7)
   - NCAAF: Bowl eligibility motivation
   - NFL: Divisional game patterns

---

## Proposed Architecture

### Option 1: Inheritance-Based (Recommended)

```
BaseEdgeDetector (Abstract)
├── NFLEdgeDetector
└── NCAAFEdgeDetector
```

**Structure**:
```python
# src/walters_analyzer/valuation/base_edge_detector.py
class BaseEdgeDetector(ABC):
    """Base class for edge detection"""

    def __init__(self, league: str):
        self.league = league
        self.power_ratings = {}
        self.games = []

    @abstractmethod
    def get_hfa(self) -> float:
        """League-specific home field advantage"""
        pass

    @abstractmethod
    def apply_league_specific_adjustments(self, ...):
        """League-specific situational factors"""
        pass

    def detect_edge(self, ...):
        """Common edge detection logic"""
        # Shared logic for both leagues
        pass

# src/walters_analyzer/valuation/nfl_edge_detector.py
class NFLEdgeDetector(BaseEdgeDetector):
    """NFL-specific edge detection"""

    HFA = 2.0  # Billy Walters uses 2.0 for NFL
    KEY_NUMBERS = [3, 7, 6, 10, 14]
    MIN_EDGE = 3.5  # Higher threshold for efficient NFL market

    def get_hfa(self) -> float:
        return self.HFA

    def apply_league_specific_adjustments(self, game):
        """NFL S-factors"""
        adj = 0.0

        # Divisional game
        if game.is_divisional:
            adj += 1.0  # Road team +1

        # Thursday night
        if game.day_of_week == "Thursday":
            adj += game.rest_advantage * 0.5

        # Key number awareness
        adj += self._key_number_adjustment(game)

        return adj

# src/walters_analyzer/valuation/ncaaf_edge_detector.py
class NCAAFEdgeDetector(BaseEdgeDetector):
    """NCAAF-specific edge detection"""

    HFA = 2.5  # NCAAF home field advantage
    KEY_NUMBERS = [3, 7, 10, 14]  # Less important than NFL
    MIN_EDGE = 1.5  # Lower threshold for less efficient market

    def get_hfa(self) -> float:
        return self.HFA

    def apply_league_specific_adjustments(self, game):
        """NCAAF S-factors"""
        adj = 0.0

        # Conference game
        if game.is_conference:
            adj += 0.5  # Familiarity

        # Rivalry game
        if game.is_rivalry:
            adj += 1.5  # Underdogs play up

        # Bowl eligibility (6-5 team desperate for win)
        if game.bowl_eligibility_spot:
            adj += 2.0  # Massive motivational factor

        # FCS vs FBS (cupcake games)
        if game.is_fcs_matchup:
            adj -= 5.0  # Don't bet these

        return adj
```

**Pros**:
- Clean separation of concerns
- Shared logic in base class
- Easy to extend with new leagues
- Type-safe with proper inheritance

**Cons**:
- More files to maintain
- Slightly more complex architecture

---

### Option 2: Configuration-Based

```python
# src/walters_analyzer/valuation/edge_detector.py
class EdgeDetector:
    """Unified edge detector with league configs"""

    LEAGUE_CONFIGS = {
        "nfl": {
            "hfa": 2.0,
            "key_numbers": [3, 7, 6, 10, 14],
            "min_edge": 3.5,
            "s_factors": ["divisional", "thursday_night", "rest"],
        },
        "ncaaf": {
            "hfa": 2.5,
            "key_numbers": [3, 7, 10, 14],
            "min_edge": 1.5,
            "s_factors": ["conference", "rivalry", "bowl_eligibility"],
        },
    }

    def __init__(self, league: str):
        self.config = self.LEAGUE_CONFIGS[league]
        # ...
```

**Pros**:
- Single file, easier to navigate
- Configuration-driven

**Cons**:
- Risk of mixing league logic in conditionals
- Harder to extend with complex league-specific logic

---

## Recommended Implementation: Option 1 (Inheritance)

### File Structure
```
src/walters_analyzer/valuation/
├── base_edge_detector.py          # Abstract base class (NEW)
├── nfl_edge_detector.py            # NFL-specific detector (NEW)
├── ncaaf_edge_detector.py          # NCAAF-specific detector (NEW)
├── billy_walters_edge_detector.py  # Legacy (keep for backwards compatibility)
├── billy_walters_totals_detector.py  # Totals (needs update)
├── injury_impacts.py               # Shared
├── player_values.py                # Shared
└── weather_alert_mapper.py         # Shared
```

### Migration Path

**Phase 1: Create Base Class (1-2 hours)**
1. Extract common logic from `billy_walters_edge_detector.py`
2. Create `BaseEdgeDetector` abstract class
3. Define abstract methods for league-specific logic

**Phase 2: Implement NFL Detector (2-3 hours)**
1. Create `NFLEdgeDetector` extending base
2. Add NFL-specific constants (HFA 2.0, key numbers)
3. Implement NFL S-factors:
   - Divisional games (+1 road team)
   - Thursday night rest advantage
   - Key number awareness
4. Test with Week 11 NFL data

**Phase 3: Implement NCAAF Detector (2-3 hours)**
1. Create `NCAAFEdgeDetector` extending base
2. Add NCAAF-specific constants (HFA 2.5)
3. Implement NCAAF S-factors:
   - Conference games
   - Rivalry games
   - Bowl eligibility motivation
4. Test with Week 12 NCAAF data

**Phase 4: Update Scripts (1 hour)**
1. Update `/edge-detector` slash command
2. Update analysis scripts to use new detectors
3. Update documentation

**Phase 5: Deprecate Legacy (Future)**
1. Mark `billy_walters_edge_detector.py` as deprecated
2. Add warning when used
3. Eventually remove after migration complete

---

## League-Specific Differences (Summary)

### Home Field Advantage
| League | HFA | Rationale |
|--------|-----|-----------|
| NFL | 2.0 | Billy Walters' current value, <1.0 recent years |
| NCAAF | 2.5 | Our analysis showed 3.5 was too high |

### Minimum Edge Threshold
| League | Min Edge | Rationale |
|--------|----------|-----------|
| NFL | 3.5 | Highly efficient market, need larger edge |
| NCAAF | 1.5 | Less efficient, smaller edges viable |

### Key Numbers (Importance)
| League | Key Numbers | Importance |
|--------|-------------|------------|
| NFL | 3, 7, 6, 10, 14 | CRITICAL - adjust bet based on key number crossing |
| NCAAF | 3, 7, 10, 14 | MODERATE - less pronounced than NFL |

### Situational Factors (S-Factors)
| Factor | NFL | NCAAF |
|--------|-----|-------|
| Divisional Game | +1.0 road team | N/A |
| Conference Game | N/A | +0.5 |
| Rivalry Game | Varies | +1.5 underdog |
| Bowl Eligibility | N/A | +2.0 desperate team |
| Thursday Night | +0.5 per day rest | N/A |
| FCS Matchup | N/A | -5.0 (don't bet) |

### Weather Impact
| League | Impact | Rationale |
|--------|--------|-----------|
| NFL | MODERATE | Some outdoor stadiums, professional QBs |
| NCAAF | HIGH | More outdoor stadiums, college QBs less skilled |

### Injury Impact
| League | Impact | Rationale |
|--------|--------|-----------|
| NFL | HIGH | Comprehensive reports, star QB = 7 pts |
| NCAAF | MODERATE | Limited data, backup QBs more variable |

---

## Testing Strategy

### Unit Tests
```python
# tests/test_nfl_edge_detector.py
def test_nfl_hfa():
    detector = NFLEdgeDetector()
    assert detector.get_hfa() == 2.0

def test_nfl_divisional_adjustment():
    detector = NFLEdgeDetector()
    game = Game(is_divisional=True)
    adj = detector.apply_league_specific_adjustments(game)
    assert adj >= 1.0  # Road team gets boost

# tests/test_ncaaf_edge_detector.py
def test_ncaaf_hfa():
    detector = NCAAFEdgeDetector()
    assert detector.get_hfa() == 2.5

def test_ncaaf_rivalry_adjustment():
    detector = NCAAFEdgeDetector()
    game = Game(is_rivalry=True)
    adj = detector.apply_league_specific_adjustments(game)
    assert adj >= 1.5  # Big rivalry boost
```

### Integration Tests
```python
def test_nfl_edge_detection_week_11():
    """Test NFL detector on Week 11 actual data"""
    detector = NFLEdgeDetector()
    detector.load_power_ratings("data/nfl_week_11.json")
    detector.load_odds("data/odds_nfl_week_11.json")
    edges = detector.detect_all_edges()

    # Should find at least some edges
    assert len(edges) > 0

    # All edges should meet minimum threshold
    assert all(e.edge_points >= 3.5 for e in edges)

def test_ncaaf_edge_detection_week_12():
    """Test NCAAF detector on Week 12 actual data"""
    detector = NCAAFEdgeDetector()
    detector.load_power_ratings("data/ncaaf_week_12.json")
    detector.load_odds("data/odds_ncaaf_week_12.json")
    edges = detector.detect_all_edges()

    # NCAAF should find more edges (less efficient market)
    assert len(edges) >= len(nfl_edges)

    # All edges should meet minimum threshold
    assert all(e.edge_points >= 1.5 for e in edges)
```

---

## Success Metrics

### Development Metrics
- [ ] All existing tests pass with new architecture
- [ ] 100% test coverage for new detector classes
- [ ] Type hints on all public methods
- [ ] Documentation for each league-specific adjustment

### Performance Metrics
- [ ] Edge detection completes in <10 seconds for full week
- [ ] Memory usage <500 MB
- [ ] Backwards compatible with existing scripts

### Accuracy Metrics (Backtesting)
- [ ] NFL: 53%+ win rate on 100+ historical bets
- [ ] NCAAF: 52%+ win rate on 100+ historical bets
- [ ] Positive CLV on both leagues
- [ ] Edge size correlates with win rate

---

## Implementation Timeline

**Week 1: Foundation**
- Day 1-2: Create BaseEdgeDetector abstract class
- Day 3-4: Implement NFLEdgeDetector
- Day 5-6: Implement NCAAFEdgeDetector
- Day 7: Testing and bug fixes

**Week 2: Integration**
- Day 1-2: Update scripts to use new detectors
- Day 3-4: Backtest on historical data (2024 season)
- Day 5-6: Documentation and examples
- Day 7: Code review and refinement

**Week 3: Validation**
- Day 1-3: Run in production alongside old detector
- Day 4-5: Compare results, validate accuracy
- Day 6: Fix any discrepancies
- Day 7: Final deployment

---

## Risks & Mitigation

### Risk: Breaking Existing Scripts
**Mitigation**: Keep `billy_walters_edge_detector.py` as wrapper that delegates to new detectors

### Risk: Performance Regression
**Mitigation**: Benchmark before and after, optimize hot paths

### Risk: Accuracy Drops
**Mitigation**: Extensive backtesting before deployment, A/B testing

### Risk: Increased Complexity
**Mitigation**: Clear documentation, type hints, good test coverage

---

## Future Enhancements

### Short-term (Next Month)
1. Add conference strength ratings (NCAAF)
2. Implement key number buying logic (NFL)
3. Add bowl game special handling (NCAAF)
4. Playoff game adjustments (NFL)

### Medium-term (Next Quarter)
5. Machine learning for S-factor weights
6. Automatic HFA adjustment based on recent trends
7. Team-specific HFA (some teams have >3 pts at home)
8. Dynamic edge thresholds based on market efficiency

### Long-term (Next Year)
9. Support for other sports (NBA, MLB)
10. Real-time line movement tracking
11. Multi-sportsbook optimization
12. Automated bet placement

---

## Conclusion

Separating NFL and NCAAF edge detectors will:
1. **Improve accuracy** through league-specific optimizations
2. **Simplify maintenance** by isolating league logic
3. **Enable faster iteration** on league-specific features
4. **Provide clearer testing** with league-specific test suites
5. **Set foundation** for future league additions

**Recommendation**: Proceed with Option 1 (Inheritance-Based) architecture.

**Estimated Effort**: 15-20 hours over 2-3 weeks

**Expected Impact**: +2-3% win rate improvement through better calibration

---

**Created**: November 15, 2025
**Status**: DRAFT - Ready for Implementation
**Next Step**: Create BaseEdgeDetector abstract class
