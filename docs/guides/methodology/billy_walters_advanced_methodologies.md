# Billy Walters Advanced Betting Methodologies
**Research Summary - November 2025**

Based on Billy Walters' book "Gambler: Secrets from a Life at Risk" and interviews.

---

## Core Principles

### 1. Three Pillars of Success
1. **Handicapping** - Creating accurate power ratings and predictions
2. **Betting Strategy** - Line shopping, timing, bet selection
3. **Money Management** - Kelly Criterion, bet sizing, bankroll protection

### 2. The Break-Even Reality
- **Win Rate Required**: 52.38% (due to 10% vig/juice)
- **Realistic Goal**: 53-55% long-term win rate
- **Success Metric**: Closing Line Value (CLV), not win percentage

---

## Power Ratings System

### Structure
- **Scale**: Numerical ratings representing team strength on neutral field
- **Example**: Cowboys 45 vs Cardinals 38 = 7-point predicted spread
- **Updates**: Weekly recalculation for every team
- **Formula**: Billy uses "90/10 update" (90% prior rating + 10% new performance)

### Power Rating Components
1. **Base Rating**: Team strength on neutral field
2. **Home Field Advantage**: Add for home team
3. **Situational Adjustments**: S-factors, W-factors, E-factors
4. **Injury Adjustments**: Player-specific point values

---

## Home Field Advantage (CRITICAL!)

### NFL
- **Historical (1974-2022)**: ~2.5 points
- **Recent (2018-2022)**: <1.0 point (COVID impact, no fans)
- **Current Recommendation**: 2.0-2.5 points

**⚠️ WARNING**: Using outdated 3.0 HFA will cause losses!

### NCAAF
- **Traditional**: 3.5 points
- **Our Analysis (Week 12)**: Overestimated favorites by 2.4 pts
- **Recommended**: 2.5 points (based on systematic bias findings)

---

## Situational Factors (S-Factors)

### Confirmed S-Factors
1. **Divisional Games**: Visitors play tougher (road teams cover more)
2. **Thursday Night Football**: Rest advantage for team with longer rest
3. **Consecutive Road Games**: Each road game progressively harder
4. **Time Zone Changes**: East→West easier than West→East
5. **Temperature Differentials**: Warm→Cold climate disadvantage
6. **Turf Differences**: Grass vs turf transition

### Point Values
- Billy keeps exact values proprietary
- "Dozens of factors quantified based on long-term statistical analysis"
- Each factor likely worth 0.5-2.0 points

---

## Weather Factors (W-Factors)

### Confirmed Impacts
- **Wind >15 MPH**: Significantly affects passing game
- **Temperature <32°F**: Affects ball handling
- **Precipitation**: Reduces scoring
- **Indoor Stadiums**: No weather adjustment

### Totals (Over/Under) Impact
- Weather primarily affects totals betting
- Only bet totals with "logical reasoning about weather/injuries"

---

## Emotional Factors (E-Factors)

### Likely Factors (Not Explicitly Confirmed)
1. **Revenge Games**: Team playing opponent that beat them earlier
2. **Lookahead Spots**: Big game next week reduces focus
3. **Letdown Spots**: Coming off emotional win
4. **Playoff Implications**: Win-or-go-home scenarios
5. **Coach Firings**: Dead cat bounce or complete collapse

---

## Injury Point Values

### Confirmed Values
- **Elite QB Injury**: ~7 points (~1 touchdown)
- **Top Non-QB Player**: 2.5-3 points
- **Generic Player**: ~1 point each

### Our Enhanced Values (From Code)
- **QB Elite**: 4.5 points
- **RB Elite**: 2.5 points
- **WR1 Elite**: 1.8 points
- **LT/RT Elite**: 1.5 points
- **CB Elite**: 1.2 points

**Note**: Billy says injuries are "second-most important factor" after power ratings

---

## Betting Strategy

### Bet Sizing (Kelly Criterion)
- **Maximum**: 3% of bankroll on any single bet
- **Typical Range**: 1-3% based on edge size
- **Edge-Based Scaling**: Larger edge = larger bet (up to max)

**Our Implementation**:
- 7+ pt edge: 5% Kelly (MAX BET, 77% win rate)
- 4-7 pt edge: 3% Kelly (STRONG, 64% win rate)
- 2-4 pt edge: 2% Kelly (MODERATE, 58% win rate)
- 1.5-2 pt edge: 1% Kelly (LEAN, 54% win rate)

### Timing Strategy
- **Favorites**: Bet early (before public money moves line)
- **Underdogs**: Bet late (after public inflates favorite)

### Line Shopping
- **Critical**: "The best price requires work"
- **Multiple Books**: Set up accounts at 5-10 sportsbooks
- **Half-Point Differences**: Can be worth millions over time

---

## Key Numbers (NFL)

### Most Important (in order)
1. **3** - Most common margin of victory (field goal)
2. **7** - Second most common (touchdown + PAT)
3. **6** - Third (touchdown, missed PAT)
4. **10** - Fourth (two field goals + touchdown)
5. **14** - Fifth (two touchdowns)

### Strategy
- **Buying/Selling Points**: Only worthwhile crossing key numbers
- **Example**: Moving from -2.5 to -3 is NOT worth it (wrong side of 3)
- **Example**: Moving from -3.5 to -3 IS worth it (landing on 3)

**Note**: NCAAF key numbers are similar but less pronounced

---

## Bet Type Hierarchy (by Value)

### 1. Spread Bets (Primary)
- Most efficient market
- Where Billy makes most money
- Focus here for consistent profits

### 2. Moneyline Bets
- Better for low-scoring sports (baseball, hockey, soccer)
- NFL: Only use when spread crosses key number

### 3. Totals (Over/Under)
- Only with "logical reasoning" (weather, injuries, pace)
- Less efficient than spreads

### 4. Parlays (AVOID)
- "Much harder to win"
- Poor value compared to straight bets
- Billy explicitly discourages

### 5. Prop Bets (AVOID)
- Coin-flip gambling unless justified
- Soft markets but require deep research

---

## Edge Detection Thresholds

### Minimum Edge
- **Billy's Approach**: Only bet when edge exists
- **Our Implementation**: 1.5 point minimum (NCAAF), 3.5 point minimum (NFL in comments)

### Market Respect (Our Addition)
- **New Rule**: Skip edges >10 points
- **Rationale**: Market processes more info than we have
- **Large disagreements = red flag**, not opportunity

---

## Bankroll Management

### Core Principles
1. **Expect to Lose It All**: Treat losses as inevitable
2. **1-3% Maximum**: Never risk more on single bet
3. **Fractional Kelly**: Use 25% of full Kelly (conservative)
4. **Diversification**: Spread bets across multiple games

### Example
- **Bankroll**: $10,000
- **Max Bet**: $300 (3%)
- **Typical Bet**: $100-200 (1-2%)
- **Small Edge**: $100 (1%)

---

## System Evolution

### Continuous Improvement
- Billy updated his models "at least fifty different times" over 60+ years
- "Information is king" - requires voracious reading
- No system is foolproof - discipline required

### Our Approach
- Start with Walters' framework
- Add modern data sources (ESPN API, AccuWeather, etc.)
- Backtest extensively
- Iterate based on results

---

## Week 12 NCAAF Analysis Integration

### What We Learned
1. **HFA Too High**: 3.5 → 2.5 (based on systematic bias)
2. **Favorites Overestimated**: Applied 15% haircut
3. **Market Respect**: Filter out >10 pt edges
4. **Sample Size**: 15 games NOT statistically significant

### What Aligns with Billy's Methods
- ✅ Power ratings foundation
- ✅ Edge-based bet sizing
- ✅ Kelly Criterion (fractional)
- ✅ Home field advantage (now corrected)
- ✅ Money management (1-3% max)

### What's Missing
- ⏳ Injury intelligence layer
- ⏳ S-factor integration
- ⏳ Weather alerts system (partially done)
- ⏳ Sharp action tracking
- ⏳ CLV measurement
- ⏳ Backtesting framework

---

## Implementation Checklist

### Phase 1: Foundation (COMPLETED ✅)
- [x] Power ratings (Massey composite)
- [x] Odds integration (Overtime.ag API)
- [x] Home field advantage (corrected to 2.5)
- [x] Edge detection thresholds
- [x] Kelly-based bet sizing
- [x] Market respect threshold

### Phase 2: Enhancements (IN PROGRESS)
- [x] Weather impact (AccuWeather API)
- [ ] Injury intelligence (ESPN + NFL official)
- [ ] S-factors (situational adjustments)
- [ ] Key number awareness (3, 7, 6, 10, 14)
- [ ] Bias correction (favorites/underdogs)

### Phase 3: Advanced (TODO)
- [ ] CLV tracking system
- [ ] Sharp money detection
- [ ] E-factors (emotional/motivational)
- [ ] Backtesting framework
- [ ] Line movement alerts
- [ ] Multiple sportsbook integration

---

## Key Quotes from Billy Walters

> "You'll need to win 52.38 percent of the time to break even."

> "You should not risk any more than 1 to 3 percent of your bankroll on any single bet."

> "Properly assessing injuries is the second-most important factor in gaining a handicapping advantage in sports."

> "Bet favorites early and underdogs late."

> "The best price requires work - set up accounts at multiple places."

> "Information is king."

> "Develop your own system and stick to it."

> "No system is foolproof."

---

## References

1. Billy Walters with Armen Keteyian, "Gambler: Secrets from a Life at Risk" (2023)
2. ESPN Interview (October 2023)
3. Action Network Interviews
4. Covers.com Analysis
5. Our Week 12 NCAAF Analysis (November 2025)

---

**Last Updated**: November 15, 2025
**Next Review**: After 200+ bets tracked (statistically significant sample)
