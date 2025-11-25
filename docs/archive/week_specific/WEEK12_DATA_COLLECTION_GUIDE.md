# Week 12 Complete Data Collection & Analysis Guide

## Overview
This guide walks you through collecting fresh NFL data and updating power ratings for Week 12 analysis using Billy Walters methodology.

## Prerequisites
```powershell
# Install required package if needed
pip install aiohttp --break-system-packages
```

## Complete Workflow

### Step 1: Collect Comprehensive NFL Data
```powershell
python collect_nfl_data_comprehensive.py
```

**What This Does:**
- ✅ Fetches Week 12 schedule from ESPN API
- ✅ Calculates travel distances and timezone differences
- ✅ Identifies indoor/outdoor stadiums
- ✅ Sets up weather forecast structure
- ✅ Prepares injury report framework
- ✅ Calculates S-factors (travel, rest, weather)
- ✅ Identifies E-factors (division games, rivalries)

**Output:**
- `data/nfl_week_data/week_12_comprehensive.json`

**Review:**
- Check travel distances (especially coast-to-coast)
- Verify division games identified
- Note which games are outdoor (need weather)

### Step 2: Update Power Ratings with Week 11 Results
```powershell
python update_power_ratings_week12.py
```

**What This Does:**
- ✅ Fetches Week 11 final scores from ESPN
- ✅ **Includes Monday Night Football result**
- ✅ Applies Billy Walters 90/10 formula
- ✅ Updates ratings for all teams
- ✅ Shows before/after comparison

**Output:**
- `data/power_ratings_nfl_2025.json` (updated)
- `data/power_ratings/nfl_2025_week_12.json` (snapshot)

**Review:**
- Verify MNF result included
- Check top rating changes
- Note teams that improved/declined significantly

### Step 3: Manual Data Verification

#### A. Check Injury Reports
**Critical for accurate analysis!**

Visit:
- https://www.nfl.com/injuries/
- https://www.espn.com/nfl/injuries

Key players to track:
- **Aaron Rodgers (PIT)** - Wrist (critical for PIT@CLE)
- **C.J. Stroud (HOU)** - Concussion protocol
- **Josh Jacobs (GB)** - Knee
- **Mike Evans (TB)** - Hamstring

**Document in session notes:**
```powershell
# Add injury notes to session
python -c "from pathlib import Path; import sys; sys.path.insert(0, 'src'); from walters_analyzer.core.session_manager import SessionManager; m = SessionManager(Path('data')); s = m.load_latest_session(12); s.add_note('Aaron Rodgers OUT - major impact on PIT@CLE', 'injury'); m.save_session(s)"
```

#### B. Check Weather Forecasts (Saturday Morning)
For outdoor games, check:
- **CLE** (Huntington Bank Field) - Thursday night game
- **ARI** (State Farm Stadium) - Retractable roof (check if open)
- Other outdoor venues

Key weather factors:
- Wind >15 mph: Major impact on passing
- Temperature <32°F: Ball handling issues
- Precipitation: Reduced scoring

### Step 4: Run Edge Analysis with Fresh Data
```powershell
python analyze_edges_simple.py
```

**What This Does:**
- Uses updated power ratings
- Applies comprehensive S-factors
- Calculates final edges
- Shows high-priority opportunities

### Step 5: Update Session with Complete Analysis
```powershell
python scripts/quick_start_week12.py
```

## Data Quality Checklist

### Before Running Analysis:
- [ ] Power ratings updated with Week 11 results
- [ ] Monday Night Football score verified
- [ ] Injury reports checked (within 24 hours)
- [ ] Weather forecasts reviewed (for outdoor games)
- [ ] Travel/timezone data calculated
- [ ] Division games identified

### Critical S-Factor Variables:

**Travel (High Impact):**
- Distance (miles)
- Timezone difference
- Coast-to-coast travel (+10 S-points)

**Rest (Moderate Impact):**
- Days since last game
- Bye week advantage
- Thursday → Sunday vs Sunday → Thursday

**Weather (Outdoor Games Only):**
- Wind speed (>15 mph = major)
- Temperature (<32°F = significant)
- Precipitation (any = moderate)

**Injuries (Highest Impact):**
- Elite QB: 6-8 points
- Key skill positions: 2-4 points
- Multiple starters: Compounding effect

**Motivation (E-Factors):**
- Division games: +2 points (emotional, unpredictable)
- Revenge games: +1 point
- Playoff implications: +2 points

## Billy Walters Key Principles

### Data Collection:
1. **Accuracy > Speed** - Verify all data sources
2. **Recency Matters** - Use data <24 hours old
3. **Official Sources** - NFL.com, ESPN API priority
4. **Cross-Reference** - Verify key data points

### S-Factor Application:
- 5 S-factor points = 1 spread point
- Always conservative estimates
- Document assumptions
- Update as new info arrives

### E-Factor Caution:
- Division games are LESS predictable, not more
- Don't over-bet emotional games
- Reduce bet size on high E-factor games
- Focus on S-factors primarily

## Troubleshooting

### If ESPN API Fails:
The scripts have fallback data, but you should:
1. Check internet connection
2. Verify ESPN API is accessible
3. Use manual fallback data if needed
4. Update scripts with actual scores

### If Power Ratings Don't Update:
1. Check that Week 11 scores are complete
2. Verify MNF result is included
3. Run with `--verbose` flag for debugging
4. Check `data/power_ratings_nfl_2025.json` exists

### If Travel Data Seems Wrong:
1. Verify team locations in script
2. Check timezone mappings
3. Manually calculate distance if needed
4. Document corrections in session notes

## Expected Output Files

After running all steps:
```
data/
├── nfl_week_data/
│   └── week_12_comprehensive.json          # All collected data
├── power_ratings_nfl_2025.json              # Updated ratings
├── power_ratings/
│   └── nfl_2025_week_12.json                # Week 12 snapshot
└── sessions/
    └── 2025_week12_[timestamp].json         # Active session
```

## Next Steps After Data Collection

1. **Run Complete Analysis:**
   ```powershell
   python analyze_edges_simple.py
   ```

2. **Review Opportunities:**
   ```powershell
   python clv_track.py list-pending
   ```

3. **Place Bets (Following Timing Strategy):**
   - Favorites: Tuesday-Thursday
   - Underdogs: Saturday
   - Record all bets immediately in CLV system

4. **Update Closing Lines (Saturday):**
   ```powershell
   python clv_track.py update-closing-line --bet-id X --closing-line Y.Y
   ```

5. **Record Results (Sunday-Monday):**
   ```powershell
   python clv_track.py update-result --bet-id X --result won
   ```

## Billy Walters Quote

> "The single most important factor in sports betting success is accurate, 
> current information. Outdated data leads to outdated conclusions. 
> Update your ratings after every week. Check injuries daily. 
> Verify everything twice."

## Support

If you encounter issues:
1. Check error messages carefully
2. Verify all prerequisites installed
3. Review data files for completeness
4. Check session notes for context

---

**Last Updated:** November 19, 2025  
**Week:** 12  
**Status:** Production Ready
