# Week 14 Execution Plan
## NCAAF Week 14 + NFL Week 13 (Nov 27-Dec 1, 2025)
**Billy Walters Sports Analyzer**

---

## Executive Summary

All systems are ready for execution:

- **NCAAF Week 14:** 48 MAX BET plays ready (13.88 units recommended)
- **NFL Week 13:** Odds refreshed (12 unique games available)
- **CLV Tracking:** System ready to monitor performance
- **Target Metric:** Closing Line Value (CLV), not win percentage

---

## NCAAF WEEK 14 EXECUTION (Fri 11/28 - Sat 11/29)

### All 48 MAX BET Plays Ready

**Tier 1: Top 5 Plays (0.5u each = 2.5u total)**

1. **Indiana @ Purdue** (Fri 11/28, 7:30 PM)
   - Pick: Indiana (AWAY) -28.5
   - Edge: 66.1 points (Exceptional)
   - Power: Indiana +31.6 vs Purdue -9.5
   - Confidence: 95%
   - Units: 0.5

2. **Georgia State @ Old Dominion** (Sat 11/29, 2:00 PM)
   - Pick: Old Dominion (HOME) -27.0
   - Edge: 61.8 points (Exceptional)
   - Power: Georgia State -18.2 vs Old Dominion +13.1
   - Confidence: 95%
   - Units: 0.5

3. **Charlotte @ Tulane** (Sat 11/29, 7:30 PM)
   - Pick: Tulane (HOME) -30.0
   - Edge: 59.0 points (Exceptional)
   - Power: Charlotte -21.5 vs Tulane +4.0
   - Confidence: 95%
   - Units: 0.5

4. **Texas Tech @ West Virginia** (Sat 11/29, 12:00 PM)
   - Pick: Texas Tech (AWAY) -23.0
   - Edge: 55.3 points (Exceptional)
   - Power: Texas Tech +30.4 vs West Virginia -5.5
   - Confidence: 95%
   - Units: 0.5

5. **UCLA @ USC** (Sat 11/29, 7:30 PM)
   - Pick: USC (HOME) -21.5
   - Edge: 53.5 points (Exceptional)
   - Power: UCLA -14.9 vs USC +13.6
   - Confidence: 95%
   - Units: 0.5

**Tier 2: Plays 6-10 (0.375u each = 1.875u total)**

6. Notre Dame @ Stanford (-32.5) - Edge: 52.8pts - Notre Dame AWAY
7. Rice @ South Florida (+28.0) - Edge: 48.5pts - South Florida HOME
8. Temple @ North Texas (-20.0) - Edge: 45.7pts - North Texas HOME
9. James Madison @ Coastal Carolina (-21.5) - Edge: 45.0pts - James Madison AWAY
10. Central Florida @ BYU (-17.5) - Edge: 36.5pts - BYU HOME

**Tier 3: Plays 11-48 (0.25u each = 9.5u total)**
- 38 additional solid MAX BET opportunities across all tiers
- All show 5+ point edges with confidence levels
- Complete list available in: `output/clv_tracking/ncaaf_week_14_plays.json`

### Execution Checklist - NCAAF

**Before Betting (Now)**
- [ ] Review top 5 edges (provided above)
- [ ] Verify current market odds match spreads listed
- [ ] Check weather for outdoor games
- [ ] Monitor injury reports for key players

**Betting Process**
- [ ] Set opening odds for each play in CLV tracker
- [ ] Place bets on all 48 MAX BET plays
- [ ] Document opening line/odds for each game
- [ ] Record total units wagered (13.88u)

**During Games (Fri-Sat)**
- [ ] Monitor games real-time
- [ ] Watch for sharp money movement (should confirm our picks)
- [ ] Check if Action Network betting % align with our picks
- [ ] Note any unexpected weather/injury developments

**After Games (Sat-Sun)**
- [ ] Record final score for each game
- [ ] Note closing odds/line
- [ ] Calculate CLV for each bet: CLV = (Opening Odds - Closing Odds) / 100
- [ ] Calculate win/loss/push for each
- [ ] Track ROI on units wagered

### Expected Performance
- **Historical Success Rate:** 52-55% ATS (not primary metric)
- **Target CLV:** +2 to +5 points average
- **Expected ROI:** 3-5% on 13.88 units wagered
- **Success Definition:** Consistent +EV, not just wins

---

## NFL WEEK 13 STATUS

### Current Data
- **Games Available:** 12 unique games with complete odds
- **Data Source:** Overtime.ag API (refreshed 11/27)
- **Odds Type:** Spreads, totals, moneyline

### Games Available (12 total)
1. Chicago @ Philadelphia (Spread: -7.0)
2. Houston @ Indianapolis (Spread: -3.5)
3. Arizona @ Tampa Bay (Spread: -3.0)
4. Jacksonville @ Tennessee (Spread: +6.0)
5. LA Rams @ Carolina (Spread: +10.0)
6. New Orleans @ Miami (Spread: -5.5)
7. Atlanta @ NY Jets (Spread: +2.5)
8. San Francisco @ Cleveland (Spread: +4.5)
9. Minnesota @ Seattle (Spread: -6.5)
10. Buffalo @ Pittsburgh (Spread: +3.0)
11. Las Vegas @ LA Chargers (Spread: -9.5)
12. Denver @ Washington (Spread: +3.0)

### Note on NFL Data
- Missing 4 of 16 games (missing Green Bay, Detroit, NY Giants, New England)
- Current odds are from updated Overnight.ag API
- Recommend running full edge detection once all 16 games available
- Can execute plays on available 12 games using existing Week 12 edge data

### NFL Edge Data Available
From previous analysis (Week 12 finalization):
- **VERY STRONG:** Miami (-6.0), New England (-7.5), Philadelphia (-7.0)
- **STRONG:** Denver @ Washington, Buffalo @ Pittsburgh, Indianapolis vs Houston

---

## CLV TRACKING SYSTEM

### How to Track CLV

The system is ready in: `scripts/analysis/clv_tracker.py`

**Key Metrics:**
- **CLV (Closing Line Value):** Did we beat the closing line (expert consensus)?
  - Formula: (Opening Odds - Closing Odds) / 100
  - Target: +2 to +5 points average

- **Win %:** NOT primary metric (many factors outside our control)
  - Context: Even professionals hit 52-55% ATS

- **ROI (Return on Investment):** Units gained/lost relative to wagered
  - Formula: Wins - Losses (in units)
  - Target: 3-5% positive on total units

- **Confidence Score:** Our edge confidence (0-100%)
  - Shows prediction quality regardless of result

### CLV Example
- We bet at -110 (our opening odds)
- Game closes at -115 (market adjusted against us)
- CLV = (-110 - (-115)) / 100 = +0.05 (beat closing line by half a point)
- This is a WIN for our analysis even if we lose the game

### Tracking Files
- **Main tracker:** `output/clv_tracking/clv_tracker.json`
- **NCAAF Week 14 plays:** `output/clv_tracking/ncaaf_week_14_plays.json`

---

## Week-by-Week Workflow

### NCAAF (Every Saturday-Sunday during season)
1. Review all available games
2. Load edge data for current NCAAF week
3. Filter to MAX BET tier (7+ points)
4. Execute top 48 plays
5. Track CLV, ROI, confidence
6. Repeat next week

### NFL (Sundays-Mondays during season)
1. Refresh Overnight.ag odds
2. Load fresh power ratings (Massey)
3. Run edge detection for complete slate
4. Execute 7+ point edges only (conservative)
5. Track CLV and performance
6. Prepare next week

### Reporting
- Weekly CLV summary
- Season-to-date ROI tracking
- Edge accuracy analysis
- Confidence calibration checks

---

## Next Steps (Sequential)

### Phase 1: NCAAF Execution (Now)
1. Document all opening odds (save in CLV tracker)
2. Place all 48 bets
3. Monitor through games (Fri-Sat)
4. Record results (Sat-Sun)
5. Calculate CLV and ROI

### Phase 2: NFL Completion (After NCAAF)
1. Obtain remaining 4 NFL games' odds
2. Run complete edge detection
3. Execute 7+ point edges
4. Track parallel to NCAAF results
5. Compare league performance

### Phase 3: Performance Analysis (Week 15 prep)
1. Calculate season CLV
2. Analyze edge accuracy
3. Calibrate confidence scoring
4. Prepare improved Week 15 strategy
5. Document lessons learned

---

## Success Metrics & Goals

### This Week (Week 14)
- **Target:** +2 to +5 CLV average across 48 plays
- **Expected Units:** 13.88u wagered
- **Success Definition:** CLV > +2 average
- **Win %:** Don't obsess (not primary metric)

### Season Goal (Through Week 18)
- **Target ROI:** 3-5% positive
- **Target CLV:** +2 to +5 average
- **Win Rate:** 52-55% (satisfactory with positive CLV)
- **Bankroll Growth:** 10-15% by season end

### Key Principle
> "We're not trying to win games. We're trying to beat the closing line."
>
> Follow the money, not the tickets. Trust the model, track the CLV.

---

## Tools Ready to Use

1. **comprehensive_odds_analysis.py**
   - Auto-detects current week
   - Shows top opportunities
   - Displays edge distribution

2. **clv_tracker.py**
   - Tracks individual bets
   - Calculates CLV automatically
   - Provides statistics by league/week

3. **ncaaf_week_14_plays.json**
   - All 48 plays listed
   - Edge sizes, power ratings, game times
   - Unit recommendations
   - Status tracking

---

## Data Files Location

| File | Purpose | Location |
|------|---------|----------|
| Odds Tracker | NCAAF Week 14 plays | `output/clv_tracking/ncaaf_week_14_plays.json` |
| CLV Tracker | Individual bet records | `output/clv_tracking/clv_tracker.json` |
| NFL Odds (Fresh) | Week 13 refreshed odds | `output/overtime/nfl/pregame/overtime_nfl_walters_20251127_233513.json` |
| Edge Analysis | NCAAF Week 14 edges | `output/edge_detection/ncaaf_edges_week_14.json` |
| Analysis Script | Dynamic analysis | `scripts/analysis/comprehensive_odds_analysis.py` |

---

## Summary

**Ready to Execute:** YES

- NCAAF Week 14: 48 plays, 13.88u, all ready
- NFL Week 13: 12 games available, more coming
- CLV Tracking: System operational
- Next Gambles: Thanksgiving weekend (Fri-Sat)

**Focus:** Track CLV, not win percentage. We're measuring edge accuracy, not luck.

---

**Last Updated:** November 27, 2025, 11:35 PM PST
**Status:** READY FOR ACTION
