# Week 10 Data Update Summary - Billy Walters Sports Analyzer

**Generated:** 2025-11-10 11:46:30
**NFL Week:** 10 (Nov 06-12, 2025)
**Season Phase:** Regular Season

---

## Update Status

### Game Schedules and Scores

**Source:** ESPN API
**Status:** Updated Successfully
**Last Update:** 2025-11-10 11:45:47

**Week 10 Results:**
- Total Games: 14
- Completed: 13
- Scheduled: 1 (Eagles @ Packers - Sunday Night)

**Completed Games:**
1. Denver 10, Las Vegas 7 (Thu Nov 7)
2. Indianapolis 31, Atlanta 25
3. Chicago 24, NY Giants 20
4. Miami 30, Buffalo 13
5. Baltimore 27, Minnesota 19
6. NY Jets 27, Cleveland 20
7. New England 28, Tampa Bay 23
8. New Orleans 17, Carolina 7
9. Houston 36, Jacksonville 29
10. Seattle 44, Arizona 22
11. LA Rams 42, San Francisco 26
12. Detroit 44, Washington 22
13. LA Chargers 25, Pittsburgh 10

**Upcoming:**
- Philadelphia Eagles @ Green Bay Packers (Sun Nov 10, 8:15 PM ET)

---

## Power Ratings (Week 10)

**Source:** Billy Walters 90/10 Formula
**Last Update:** 2025-11-09 08:10:31

**Top 10 Teams:**
1. Buffalo Bills - 19.10
2. Detroit Lions - 18.92
3. Kansas City Chiefs - 17.69
4. Seattle Seahawks - 15.02
5. Philadelphia Eagles - 13.26
6. Houston Texans - 13.67
7. LA Rams - 12.37
8. Indianapolis Colts - 11.90
9. LA Chargers - 11.88
10. Green Bay Packers - 11.55

**Bottom 5 Teams:**
1. Tennessee Titans - -4.35
2. Las Vegas Raiders - -0.52/-0.10
3. Washington Commanders - 0.99
4. Denver Broncos - 0.10/10.02 (duplicate entries)
5. Carolina Panthers - 1.29

**Notable Moves:**
- Buffalo continues to lead with strong rating (19.10)
- Detroit Lions showing dominance (18.92) after 44-22 win over Washington
- LA Rams surging (12.37) after 42-26 victory over San Francisco
- Seattle Seahawks moving up (15.02) following 44-22 win over Arizona

---

## Odds Data

**Sources:** Overtime.ag, Action Network

### Overtime.ag Status
**Status:** No active lines (games completed)
**Last Attempt:** 2025-11-10 11:46:30
**Account Balance:** -$1,988.43 (Available: $8,011.57)

**Note:** Lines for Week 10 have been taken down as games are complete. Week 11 lines typically post on Tuesday/Wednesday after Monday Night Football.

### Recommended Next Steps:
1. Check Tuesday/Wednesday for Week 11 opening lines
2. Monitor for early line movements
3. Look for Week 11 value opportunities

---

## Team Statistics

**Source:** ESPN API
**Status:** Partial Update
**Issue:** Standing data structure returned 0 teams (API format change)

**Action Required:** Review ESPN standings endpoint format and update parser.

---

## Weather Data

**Status:** Not Available
**Issues Encountered:**
- AccuWeather client method mismatch
- OpenWeather client requires city/state parameters

**Action Required for Next Week:**
1. Update weather client interfaces to match current APIs
2. Map NFL teams to stadium locations with city/state
3. Implement fallback weather data sources

---

## Injury Reports

**Status:** Failed
**Issue:** Method name mismatch in ESPNInjuryScraper

**Action Required:**
1. Review ESPNInjuryScraper class interface
2. Update method calls to match current implementation
3. Add injury data integration for Week 11 analysis

---

## Data Quality Assessment

### Successful Updates
- Game schedules and scores: 14 games tracked
- Power ratings: Current through Week 10
- Historical data: Weeks 1-10 available

### Needs Attention
- Weather integration: API interface updates required
- Team statistics: ESPN endpoint parser needs fixing
- Injury reports: Method interface alignment needed
- Odds data: Wait for Week 11 lines (normal timing)

---

## Key Insights for Week 10

### Dominant Performances
1. **Seattle 44, Arizona 22** - Seahawks moved to #4 in power ratings
2. **Detroit 44, Washington 22** - Lions showing championship form
3. **LA Rams 42, San Francisco 26** - Rams surging in NFC West

### Surprising Results
1. **Miami 30, Buffalo 13** - Dolphins upset Bills at home
2. **New England 28, Tampa Bay 23** - Patriots road win in Florida
3. **Denver 10, Las Vegas 7** - Low-scoring Thursday night affair

### Power Rating Implications
- **Buffalo** maintains top rating despite loss (19.10) - Walters 90/10 formula keeps historical strength
- **Detroit** proving to be elite team (18.92)
- **Seattle** emerging as contender (15.02)
- **San Francisco** declining after loss (10.72)

---

## Upcoming Week 11 Preparation

### Data Collection Checklist
- [ ] Monitor for Week 11 opening lines (Tuesday/Wednesday)
- [ ] Update weather forecasts for game locations
- [ ] Collect injury reports (Wednesday official reports)
- [ ] Update team statistics after Week 10 complete
- [ ] Run edge detection when lines available

### Analysis Priorities
1. **Eagles @ Packers** - Complete Week 10 with SNF result
2. **Week 11 Line Shopping** - Compare opening lines across books
3. **Weather Impact** - Identify outdoor games with weather factors
4. **Injury Analysis** - Track key player statuses for Week 11

---

## System Health

**Database:** Operational
**API Clients:**
- ESPN: Operational
- Overtime: Operational (no current lines)
- Weather: Needs update
- Injury: Needs update

**Power Ratings Engine:** Fully operational
**Edge Detection System:** Ready (awaiting odds data)

---

## Files Generated

1. `data/current/nfl_week_10_games.json` - Game schedules/scores
2. `data/power_ratings/nfl_2025_week_10.json` - Current power ratings
3. `output/overtime_nfl_odds_20251110_114630.json` - Overtime attempt (0 games)
4. `data/current/week_10_update_summary.md` - This report

---

## Next Session Action Items

**Immediate (Today):**
1. Watch Eagles @ Packers game and update results
2. Check for Week 11 schedule release

**Tuesday/Wednesday:**
1. Fetch Week 11 opening lines from Overtime and Action Network
2. Run edge detection with fresh lines
3. Update power ratings after Week 10 complete

**Ongoing:**
1. Fix weather client integration
2. Update team statistics parser
3. Resolve injury report scraper interface

---

## Contacts & Resources

- **Current Week Check:** `/current-week` slash command
- **Data Update Script:** `scripts/utilities/update_all_data.py`
- **Power Ratings:** `data/power_ratings/nfl_2025_week_*.json`
- **Edge Detection:** `src/walters_analyzer/valuation/billy_walters_edge_detector.py`

---

*Report generated by Billy Walters Sports Analyzer*
*Data update system v1.0*
