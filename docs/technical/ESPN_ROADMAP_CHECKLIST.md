# ESPN Roadmap Implementation - Actionable Checklist

**Status**: Ready for Activation
**Last Updated**: 2025-11-23
**Owner**: Billy Walters Sports Analyzer Team

---

## PHASE 1: Automated ESPN Data Collection (Week 1)
**Objective**: Friday 9 AM UTC automated collection runs successfully
**Time**: ~15 minutes to activate
**Estimated Completion**: This Week (Nov 29)

### TIER 1A: Activate GitHub Actions (5 min)
- [ ] Read `.github/workflows/espn-collection.yml`
- [ ] Commit workflow file to repository
  ```bash
  git add .github/workflows/espn-collection.yml
  git commit -m "ci: add ESPN automated data collection (Friday 9 AM UTC)"
  git push origin main
  ```
- [ ] Go to GitHub repo Settings → Actions → General
- [ ] Select "Allow all actions and reusable workflows"
- [ ] Click Save
- [ ] Verify workflow appears in Actions tab

**Success Criteria**:
- [ ] Workflow visible in GitHub Actions tab
- [ ] Scheduled trigger shows "Friday 9 AM UTC"
- [ ] Can manually trigger via "Run workflow"

### TIER 1B: Test Collection (10 min)
- [ ] Create required directories
  ```bash
  mkdir -p data/archive/raw/{nfl,ncaaf}/{team_stats,injuries,schedules}/current
  mkdir -p data/metrics/logs
  ```
- [ ] Run NFL collection
  ```bash
  uv run python scripts/dev/espn_production_orchestrator.py --league nfl
  ```
- [ ] Run NCAAF collection
  ```bash
  uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf
  ```
- [ ] Verify output in `data/archive/raw/`
- [ ] Check `data/metrics/logs/` for success message

**Success Criteria**:
- [ ] NFL: 32/32 teams collected
- [ ] NCAAF: 130+/136+ teams collected
- [ ] Injury reports collected for both leagues
- [ ] Game schedules collected for both leagues
- [ ] No errors in log file

---

## PHASE 2: Spread Comparisons (Week 2)
**Objective**: Generate ESPN vs Massey-only spread comparisons
**Time**: ~5 hours implementation + testing
**Estimated Completion**: Dec 6

### TIER 2A: Wire Odds Data into Comparisons (2 hrs)
- [ ] Review `scripts/analysis/compare_espn_impact.py`
- [ ] Load Overtime.ag API output (spreads)
- [ ] Load ESPN/Massey power ratings
- [ ] Calculate baseline vs enhanced predictions
- [ ] Compute edge analysis
- [ ] Test with current NFL week games
- [ ] Test with current NCAAF week games

**Success Criteria**:
- [ ] Script runs without errors
- [ ] Generates 15+ NFL game comparisons
- [ ] Generates 50+ NCAAF game comparisons
- [ ] Shows spread delta for each game
- [ ] Calculates edge improvement

### TIER 2B: Create Spread Comparison Tracker (2 hrs)
- [ ] Create `src/walters_analyzer/spreads/comparison_tracker.py`
- [ ] Implement `SpreadComparison` dataclass
- [ ] Implement `ComparisonDatabase` class
- [ ] Add methods:
  - [ ] `load_comparisons_from_file()`
  - [ ] `calculate_edge_improvement()`
  - [ ] `find_divergent_games()`
  - [ ] `export_to_json()`
- [ ] Write unit tests (3-4 tests)
- [ ] Test with real ESPN data

**Success Criteria**:
- [ ] Module imports without errors
- [ ] Can load and save comparisons
- [ ] Calculates edge improvement correctly
- [ ] Tests pass (3/3 minimum)

### TIER 2C: Generate First Comparisons (1 hr)
- [ ] Run comparison analysis for current week
  ```bash
  uv run python scripts/analysis/compare_espn_impact.py --league nfl --show-comparisons
  ```
- [ ] Review output (look for):
  - [ ] Average spread delta
  - [ ] Games with edge improvement
  - [ ] Largest divergences
- [ ] Save results to `output/espn_analysis/`
- [ ] Document findings in notes

**Success Criteria**:
- [ ] ✓ Report generated with 15+ games
- [ ] ✓ Shows ESPN impact on predictions
- [ ] ✓ Identifies improved edges
- [ ] ✓ Results saved for tracking

---

## PHASE 3: CLV Tracking Database (Weeks 2-4)
**Objective**: Track 20+ bets with CLV calculations
**Time**: ~3-4 hours setup + ongoing manual tracking
**Estimated Completion**: Dec 27

### TIER 3A: Create CLV Database Schema (1.5 hrs)
- [ ] Create `src/walters_analyzer/bet_tracker/clv_tracker.py`
- [ ] Implement `TrackedBet` dataclass with fields:
  - [ ] bet_id, week, game_id, matchup
  - [ ] bet_type, selection
  - [ ] opening_line, opening_price, bet_size, wager_timestamp
  - [ ] closing_line, closing_price, closing_timestamp
  - [ ] final_score_away, final_score_home, result
  - [ ] clv, cover, profit_loss
  - [ ] edge_reason, espn_adjustment, weather_adjustment
- [ ] Implement `CLVTracker` class with methods:
  - [ ] `add_bet()`
  - [ ] `update_closing_line()`
  - [ ] `update_score()`
  - [ ] `calculate_clv()`
  - [ ] `get_summary()`
  - [ ] `export_to_json()`
- [ ] Test with sample data

**Success Criteria**:
- [ ] Module imports without errors
- [ ] Can add, update, and retrieve bets
- [ ] CLV calculation matches expected values
- [ ] Can generate summary statistics

### TIER 3B: Set Up Tracking Infrastructure (1 hr)
- [ ] Create `data/bets/` directory
- [ ] Create `data/bets/clv_database.jsonl` file
- [ ] Create `data/bets/tracking_log.md` for notes
- [ ] Test adding sample bets:
  ```bash
  cat >> data/bets/clv_database.jsonl << 'EOF'
  {"bet_id": "BET_001", "week": 12, "matchup": "Test", "selection": "Test", "opening_line": 3.0, "opening_price": -110.0, "bet_size": 1.0}
  EOF
  ```

**Success Criteria**:
- [ ] Directories created
- [ ] Files created and readable
- [ ] Can add entries without errors
- [ ] Can read entries back

### TIER 3C: Track Real Bets (Weeks 2-4)
**Goal**: Accumulate 20+ tracked bets

**Week 2 (Nov 30 - Dec 6)**:
- [ ] Track 5-7 bets from NFL Week 12
- [ ] Track 5-7 bets from NCAAF Week 13
- [ ] Record opening lines
- [ ] Document edge reasoning

**Week 3 (Dec 7 - Dec 13)**:
- [ ] Track 5-7 bets from NFL Week 13
- [ ] Track 5-7 bets from NCAAF Week 14
- [ ] Update closing lines
- [ ] Record game outcomes

**Week 4 (Dec 14 - Dec 20)**:
- [ ] Track remaining bets to reach 20+ total
- [ ] Update all closing lines
- [ ] Calculate CLV for completed games
- [ ] Generate interim summary report

**Success Criteria**:
- [ ] 20+ total bets tracked with complete data
- [ ] Closing lines recorded for all games
- [ ] CLV calculated for all completed games
- [ ] Summary shows:
  - [ ] Total bets: 20+
  - [ ] Win rate: 50%+
  - [ ] Average CLV: +0.0 or better
  - [ ] ROI: 0% or better

---

## PHASE 4: Historical Backtesting (Weeks 5-8)
**Objective**: Validate ESPN enhancement with historical data
**Time**: ~4 hours implementation
**Estimated Completion**: Jan 24

### TIER 4A: Build Backtesting Harness (2 hrs)
- [ ] Create `scripts/backtest/espn_backtest.py`
- [ ] Implement backtesting class:
  - [ ] Load historical games (Weeks 1-4)
  - [ ] Generate predictions with Massey-only (control)
  - [ ] Generate predictions with Massey + ESPN (treatment)
  - [ ] Record spreads and outcomes
  - [ ] Calculate metrics for both versions
- [ ] Add result logging
- [ ] Test with sample weeks

**Success Criteria**:
- [ ] Script runs without errors
- [ ] Generates results for all test weeks
- [ ] Control and treatment groups both complete
- [ ] Results saved to file

### TIER 4B: Performance Analysis (1.5 hrs)
- [ ] Calculate statistics:
  - [ ] Hit rate (% of correct predictions)
  - [ ] CLV average
  - [ ] ROI
  - [ ] Spread prediction accuracy (abs error)
- [ ] Compare control vs treatment:
  - [ ] Hit rate difference
  - [ ] CLV improvement
  - [ ] ROI improvement
- [ ] Calculate statistical significance
- [ ] Generate visualization/report

**Success Criteria**:
- [ ] Both control and treatment analyzed
- [ ] Hit rate difference calculated
- [ ] CLV improvement quantified
- [ ] Statistical significance > 80%
- [ ] Report shows ESPN value clearly

### TIER 4C: Validation Report (0.5 hrs)
- [ ] Generate backtesting report:
  ```
  Backtesting Results - Weeks 1-4, 2025
  =====================================

  Control (Massey-only):
  - Bets Analyzed: 45
  - Hit Rate: 58%
  - Avg CLV: +0.72
  - ROI: 8.3%

  Treatment (Massey + ESPN):
  - Bets Analyzed: 45
  - Hit Rate: 64% (+6%)
  - Avg CLV: +1.28 (+0.56 improvement)
  - ROI: 14.7% (+6.4%)

  Statistical Significance: 94%
  Conclusion: ESPN enhancement is VALIDATED
  ```
- [ ] Save report to `output/backtest_results_*.json`
- [ ] Update documentation with findings

**Success Criteria**:
- [ ] Treatment CLV > Control CLV
- [ ] Improvement statistically significant (>80%)
- [ ] Report clearly shows ESPN value
- [ ] Results documented for reference

---

## PHASE 5: Weight Optimization (Month 2+)
**Objective**: Find optimal ESPN/Massey weight split
**Time**: ~5 hours implementation
**Estimated Completion**: Feb 28

### TIER 5A: Set Up A/B Testing (2 hrs)
- [ ] Create weight variants to test:
  - [ ] Variant A (Control): 90/10
  - [ ] Variant B: 85/15
  - [ ] Variant C: 95/5
  - [ ] Variant D: 80/20
- [ ] Implement weight optimization framework:
  - [ ] Load historical game data
  - [ ] Run edge detection with each weight
  - [ ] Calculate CLV for each variant
  - [ ] Track results in database
- [ ] Test with Weeks 5-8 data

**Success Criteria**:
- [ ] All 4 variants generate predictions
- [ ] CLV calculated for each variant
- [ ] Results comparable across variants
- [ ] One clear winner identified

### TIER 5B: Performance Analysis (2 hrs)
- [ ] For each variant, calculate:
  - [ ] Average CLV
  - [ ] Hit rate
  - [ ] ROI
  - [ ] Confidence interval
- [ ] Statistical significance testing
- [ ] Identify best variant
- [ ] Quantify improvement over baseline

**Success Criteria**:
- [ ] Best variant identified
- [ ] Improvement quantified with confidence
- [ ] Statistical test shows significance
- [ ] Recommendation documented

### TIER 5C: Deploy Optimized Model (1 hr)
- [ ] Update ESPN integration with optimal weights
- [ ] Document final formula
- [ ] Update `src/walters_analyzer/valuation/espn_integration.py`
- [ ] Test with current week games
- [ ] Update production documentation

**Success Criteria**:
- [ ] Optimal weights in production code
- [ ] Edge detector uses new weights
- [ ] Documentation updated
- [ ] All tests pass

---

## ONGOING: Weekly Monitoring
**After All Phases Complete**

### Every Friday (Post-Automation)
- [ ] Review ESPN collection metrics
  - [ ] Check `data/metrics/logs/` for errors
  - [ ] Verify team stats collected
  - [ ] Confirm injuries/schedules current
- [ ] Monitor new games' spread predictions
- [ ] Review edge changes from ESPN enhancement

### Every Sunday
- [ ] Track new game outcomes
- [ ] Update CLV database with closing lines and scores
- [ ] Calculate weekly CLV performance
- [ ] Monitor ROI vs target

### Monthly
- [ ] Generate performance report
- [ ] Compare actual CLV vs predicted
- [ ] Adjust methodology if needed
- [ ] Document lessons learned

---

## Decision Checklist

Before Starting Phase 1, Confirm:

- [ ] **Automation Strategy**: Run Friday 9 AM UTC every week?
  - [ ] YES - Proceed with GitHub Actions setup
  - [ ] NO - Document manual collection schedule

- [ ] **Betting Type**: Virtual or real money bets?
  - [ ] Virtual - No capital required, pure tracking
  - [ ] Real - Requires bankroll and bet placement

- [ ] **Success Criteria**: What validates ESPN enhancement?
  - [ ] +0.5 CLV minimum (professional)
  - [ ] +1.0 CLV minimum (elite)
  - [ ] Other: ___________

- [ ] **Timeline**: When should all phases be complete?
  - [ ] End of Q1 2026 (natural pace)
  - [ ] End of 2025 (accelerated)
  - [ ] Other: ___________

- [ ] **Resource Allocation**: Who owns each phase?
  - [ ] Claude Code (automation + analysis)
  - [ ] Andy (bet placement + validation)
  - [ ] Other: ___________

---

## Quick Status Overview

```
PHASE 1: Automated Collection
├─ GitHub Actions: ⏳ Pending
├─ Manual Testing: ⏳ Pending
├─ Verification: ⏳ Pending
└─ Target: Nov 29, 2025

PHASE 2: Spread Comparisons
├─ Implementation: ⏳ Pending
├─ Testing: ⏳ Pending
├─ First Comparisons: ⏳ Pending
└─ Target: Dec 6, 2025

PHASE 3: CLV Tracking
├─ Database Setup: ⏳ Pending
├─ Bet Tracking (5): ⏳ Pending
├─ Bet Tracking (10): ⏳ Pending
├─ Bet Tracking (20): ⏳ Pending
└─ Target: Dec 27, 2025

PHASE 4: Backtesting
├─ Harness: ⏳ Pending
├─ Analysis: ⏳ Pending
├─ Validation: ⏳ Pending
└─ Target: Jan 24, 2026

PHASE 5: Optimization
├─ Weight Testing: ⏳ Pending
├─ Performance Analysis: ⏳ Pending
├─ Deployment: ⏳ Pending
└─ Target: Feb 28, 2026
```

---

## How to Use This Checklist

1. **Print it out** or keep it open in editor
2. **Check off items** as you complete them
3. **Update Progress** at end of each session
4. **Track Timeline** - note actual vs estimated completion dates
5. **Document Issues** - add notes when hitting blockers

---

## Support Resources

| Need | Resource |
|------|----------|
| Quick Start | `docs/ESPN_QUICK_START_GUIDE.md` |
| Full Plan | `docs/ESPN_ROADMAP_IMPLEMENTATION_2025.md` |
| API Details | `docs/ESPN_Integration_Quick_Reference.md` |
| Session Notes | `docs/ESPN_ROADMAP_SESSION_SUMMARY_2025-11-23.md` |
| Commands | Appendix in ESPN_QUICK_START_GUIDE.md |

---

**Status**: Ready for Activation
**Start Date**: Ready Now (This Week)
**Estimated Total Time**: 25-30 hours over 12-16 weeks
**Next Action**: Review this checklist and approve to proceed

Updated: 2025-11-23 by Claude Code
