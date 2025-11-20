# Week 12 Data Collection - Quick Commands

## Complete Workflow (Run in Order)

```powershell
# 1. Collect comprehensive NFL data
python collect_nfl_data_comprehensive.py

# 2. Update power ratings with Week 11 results (includes MNF)
python update_power_ratings_week12.py

# 3. Mark injury/weather checks complete
python -c "from pathlib import Path; import sys; sys.path.insert(0, 'src'); from walters_analyzer.core.session_manager import SessionManager; m = SessionManager(Path('data')); s = m.load_latest_session(12); s.mark_injuries_checked(); s.mark_weather_checked(); m.save_session(s)"

# 4. Run edge analysis
python analyze_edges_simple.py

# 5. Check session status
python scripts/quick_start_week12.py
```

## Data Verification Commands

```powershell
# View collected data
cat data\nfl_week_data\week_12_comprehensive.json

# View updated power ratings
cat data\power_ratings_nfl_2025.json

# Check top rating changes
python -c "import json; data = json.load(open('data/power_ratings_nfl_2025.json')); print('Last Updated:', data['last_updated']); print('Week:', data['week'])"
```

## CLV Tracking Commands

```powershell
# Record new bet
python clv_track.py record-bet --game "AWAY_HOME" --line X.X --amount XXX --edge X.X

# List pending bets
python clv_track.py list-pending

# Update closing line
python clv_track.py update-closing-line --bet-id X --closing-line Y.Y

# Record result
python clv_track.py update-result --bet-id X --result won

# View summary
python clv_track.py summary
```

## Manual Data Sources

**Injury Reports:**
- https://www.nfl.com/injuries/
- https://www.espn.com/nfl/injuries

**Weather Forecasts:**
- https://weather.com
- https://www.accuweather.com

**Line Shopping:**
- https://www.vegasinsider.com
- https://www.covers.com
- Your preferred sportsbooks

## Key S-Factor Formulas

**Travel Impact:**
- 5 S-factor points = 1 spread point
- Short travel (<500mi, no TZ): 0 points
- Moderate (500-1500mi): 2-3 points  
- Long (>1500mi or 2+ TZ): 5-7 points
- Coast-to-coast (3 TZ): 10 points

**Injury Impact:**
- Elite QB: 6-8 points
- Star skill player: 3-4 points
- Key starter: 2-3 points
- Depth player: 0-1 points

**Weather Impact:**
- Indoor: 0 points
- Wind >15mph: 5 points
- Temp <32°F: 3 points
- Precipitation: 3 points

**Division Games (E-Factor):**
- Division rivalry: +2 points (MORE unpredictable)
- Reduce bet confidence by 20%

## Risk Management Reminders

- Single bet max: 3% ($600 on $20K)
- Weekly total max: 15% ($3,000 on $20K)
- Minimum edge: 5.5%
- Stop-loss: 10% weekly drawdown

## Timing Strategy

**Favorites:** Bet Tuesday-Thursday (early)
**Underdogs:** Bet Saturday (late)
**Always:** Record bet immediately in CLV system

---

**Save this file for quick reference during Week 12!**
