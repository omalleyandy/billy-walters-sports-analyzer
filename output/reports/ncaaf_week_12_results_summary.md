# NCAAF Week 12 Results Summary
**Billy Walters Edge Detection Analysis**

Generated: 2025-11-12
Results Final: 2025-11-15 Evening

---

## Overall Performance

**Final Record: 3-12 (20.0%)**

| Classification | Record | Win % | Expected Win % | Edge Range |
|----------------|--------|-------|----------------|------------|
| MAX BET        | 1-2    | 33.3% | 77%           | 7-12 pts   |
| STRONG         | 1-5    | 16.7% | 64%           | 4-7 pts    |
| MODERATE       | 1-4    | 20.0% | 58%           | 2-4 pts    |
| LEAN           | 0-1    | 0.0%  | 54%           | 1.5-2 pts  |

---

## Detailed Results

### MAX BET (7+ point edges)

❌ **Sam Houston St -9.5** vs Delaware (Edge: 12.1 pts)
- Final: Delaware 23, Sam Houston 26
- Sam Houston won by 3, needed to win by >9.5
- **LOSS**

❌ **Boston College -16.5** vs Georgia Tech (Edge: 8.4 pts)
- Final: Georgia Tech 36, Boston College 34
- Boston College lost outright, needed to win by >16.5
- **LOSS**

✅ **South Carolina +19.0** @ Texas A&M (Edge: 7.0 pts)
- Final: South Carolina 30, Texas A&M 31
- South Carolina lost by 1, easily covered +19.0
- **WIN**

### STRONG (4-7 point edges)

✅ **Wisconsin +29.5** @ Indiana (Edge: 6.8 pts)
- Final: Wisconsin 7, Indiana 31
- Wisconsin lost by 24, covered +29.5
- **WIN**

❌ **Navy -10.0** vs South Florida (Edge: 6.5 pts)
- Final: South Florida 38, Navy 41
- Navy won by 3, didn't cover -10.0
- **LOSS**

❌ **UAB -18.5** vs North Texas (Edge: 6.3 pts)
- Final: North Texas 53, UAB 24
- UAB lost outright by 29 (MASSIVE upset)
- **LOSS**

❌ **Alabama -6.0** vs Oklahoma (Edge: 5.5 pts)
- Final: Oklahoma 23, Alabama 21
- Alabama lost outright (huge upset)
- **LOSS**

❌ **Troy +11.0** @ Old Dominion (Edge: 4.7 pts)
- Final: Troy 0, Old Dominion 33
- Troy lost by 33, didn't cover +11.0 (shutout)
- **LOSS**

❌ **Maryland +14.5** @ Illinois (Edge: 4.1 pts)
- Final: Maryland 6, Illinois 24
- Maryland lost by 18, didn't cover +14.5
- **LOSS**

### MODERATE (2-4 point edges)

❌ **LSU -5.5** vs Arkansas (Edge: 3.6 pts)
- Final: Arkansas 22, LSU 23
- LSU won by 1, didn't cover -5.5
- **LOSS**

❌ **Air Force +7.0** @ Connecticut (Edge: 3.1 pts)
- Final: Air Force 16, Connecticut 26
- Air Force lost by 10, didn't cover +7.0
- **LOSS**

❌ **Memphis +3.0** @ East Carolina (Edge: 2.8 pts)
- Final: Memphis 27, East Carolina 31
- Memphis lost by 4, didn't cover +3.0
- **LOSS**

✅ **Missouri St -4.5** vs UTEP (Edge: 2.7 pts)
- Final: UTEP 24, Missouri St 38
- Missouri St won by 14, easily covered -4.5
- **WIN**

❌ **Minnesota +25.0** @ Oregon (Edge: 2.4 pts)
- Final: Minnesota 13, Oregon 42
- Minnesota lost by 29, didn't cover +25.0
- **LOSS**

### LEAN (1.5-2 point edges)

❌ **North Carolina +6.0** @ Wake Forest (Edge: 1.5 pts)
- Final: North Carolina 12, Wake Forest 28
- North Carolina lost by 16, didn't cover +6.0
- **LOSS**

---

## Key Findings & Analysis

### 1. Model Performance Issues

**Major Concerns:**
- Actual win rate (20%) is FAR below expected (54-77%)
- Even the highest-edge plays (MAX BET) underperformed significantly
- No correlation between edge size and success rate

**Notable Failures:**
- UAB -18.5: Lost outright by 29 (48-point swing from prediction)
- Alabama -6.0: Lost outright at home to Oklahoma (huge upset)
- Troy +11.0: Shutout 0-33 (worse than worst-case scenario)
- Sam Houston -9.5: Won by only 3 (12-point miss on 12.1 edge)

### 2. Statistical Significance

**Critical Note:** 15 games is NOT a statistically significant sample size
- Need 200+ bets to properly evaluate a betting model
- One bad week doesn't invalidate the methodology
- However, the magnitude of the miss is concerning

### 3. Potential Issues to Investigate

**Power Ratings:**
- May be based on outdated or incomplete data
- Could be overvaluing certain teams (UAB, Alabama, Sam Houston)
- Need to verify Massey Ratings source data

**Missing Factors:**
- Weather: Not fully integrated yet
- Injuries: May not have captured key player absences
- Motivation: Late season dynamics (bowl eligibility, rivalry games)
- Rest: Thursday night games (Troy)

**Market Efficiency:**
- The market may have information we don't
- Large edges (>7 pts) should be rare in efficient markets
- 12.1 pt edge on FCS game suggests data quality issues

### 4. Games That Worked

**Winners Analysis:**
- South Carolina +19.0: Large dog in competitive game (narrow loss)
- Wisconsin +29.5: Large dog in blowout (still covered)
- Missouri St -4.5: Moderate favorite covered comfortably

**Pattern:** Underdogs with large spreads performed better than expected (2-4 on dogs vs 1-8 on favorites)

### 5. Games That Failed Catastrophically

- UAB vs North Texas: 48-point swing from prediction
- Troy @ Old Dominion: Shutout when we expected competitive game
- Alabama vs Oklahoma: Elite team lost at home as favorite

**Common Thread:** Our model significantly overestimated favorites

---

## Recommendations for Model Improvement

### Immediate Actions

1. **Verify Power Ratings Data**
   - Check Massey Ratings scraper is working correctly
   - Validate that ratings are current (not from earlier in season)
   - Compare to other power rating systems (ESPN FPI, Sagarin)

2. **Add Missing Data Layers**
   - Integrate injury data (especially QB injuries)
   - Add weather adjustments for outdoor games
   - Include rest/lookahead factors

3. **Recalibrate Edge Thresholds**
   - Current thresholds may be too aggressive
   - Consider raising minimum edge from 1.5 to 3.0 points
   - Reduce Kelly percentages until model proves itself

4. **Analyze Market Efficiency**
   - If we consistently find 7+ point edges, either:
     - Our model is wrong (more likely)
     - Market is wrong (less likely)
   - Should be suspicious of any edge >5 points

### Long-term Improvements

1. **Backtesting Framework**
   - Test model on historical data (2024, 2023 seasons)
   - Calculate actual CLV over full seasons
   - Identify systematic biases

2. **Machine Learning Integration**
   - Use more sophisticated statistical models
   - Incorporate situational factors
   - Learn from prediction errors

3. **Tracking & Analytics**
   - Build CLV tracking system
   - Monitor by conference, team type, game situation
   - Identify where model performs well/poorly

4. **Sample Size**
   - Continue betting discipline
   - Track 200+ picks before making major changes
   - Separate NFL and NCAAF analysis

---

## Billy Walters Methodology Notes

**Key Principles:**
- Success is measured by CLV (Closing Line Value), not win percentage
- One week is meaningless - need full season
- Bankroll management prevents catastrophic loss
- Model improvements are iterative

**This Week's Lessons:**
- 3-12 with proper Kelly sizing = Manageable loss
- Without bankroll management = Potential disaster
- The methodology (CLV, Kelly) is sound even when picks aren't

**Next Steps:**
1. Don't panic - small sample size
2. Investigate the systematic favorite bias
3. Verify data quality and recency
4. Continue tracking for meaningful sample
5. Compare to closing lines (CLV calculation needed)

---

## Action Items

- [ ] Verify Massey Ratings are current (check scraper timestamps)
- [ ] Add injury scraping for QB injuries (ESPN + official team sites)
- [ ] Backtest model on 2024 NCAAF season (at least 100 games)
- [ ] Calculate actual CLV for this week (need closing lines)
- [ ] Review edge threshold calibration
- [ ] Add weather integration to edge detector
- [ ] Build systematic favorite bias test

---

**Generated:** 2025-11-15
**Analyst:** Billy Walters Sports Analyzer v1.0
