# S and W Factor Integration - Quick Start

## Files Copied to Windows

✅ **Main Module:** `billy_walters_sfactor_reference.py` (root directory)  
✅ **Valuation Module:** `src/walters_analyzer/valuation/sfactor_wfactor.py`  
✅ **Documentation:** `docs/SFACTOR_QUICK_REFERENCE.md`

## Quick Test

Test the module works on Windows:

```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
python billy_walters_sfactor_reference.py
```

Expected output:
```
Example: Buffalo Bills @ Detroit Lions (Week 12)
============================================================

Lions S-Factors: S-Factors: 0.0 pts → 0.00 spread
Breakdown: {'turf': 0, 'division': 0, 'schedule': 0, 'time_zone': 0}

W-Factors: W-Factors: 0.0 pts → 0.00 spread
Breakdown: {'temperature': 0.0, 'precipitation': 0.0, 'wind': 0.0}

============================================================
Total adjustment for Lions: 0.00 points
```

## Integration with Analyzer

### Method 1: Simple Direct Usage (Recommended for Start)

Add to your analysis script:

```python
from billy_walters_sfactor_reference import (
    SFactorCalculator,
    WFactorCalculator,
    TeamQuality,
    TurfType,
    get_team_time_zone,
    is_warm_weather_team,
    is_dome_team
)

# Example: Calculate S-Factors for a game
def analyze_game_with_factors(home_team, away_team, game_info):
    # Calculate S-Factors for home team
    home_sfactors = SFactorCalculator.calculate_complete_sfactors(
        is_home=True,
        same_division=game_info.get('same_division', False),
        same_conference=game_info.get('same_conference', True),
        coming_off_bye=game_info.get('home_off_bye', False),
        team_quality=TeamQuality.AVERAGE,  # Determine from power ratings
        is_thursday_night=game_info.get('thursday_night', False),
        team_time_zone=get_team_time_zone(home_team),
        game_time_zone=game_info.get('game_time_zone', 'ET')
    )
    
    # Calculate S-Factors for away team
    away_sfactors = SFactorCalculator.calculate_complete_sfactors(
        is_home=False,
        same_division=game_info.get('same_division', False),
        same_conference=game_info.get('same_conference', True),
        coming_off_bye=game_info.get('away_off_bye', False),
        team_quality=TeamQuality.AVERAGE,
        team_time_zone=get_team_time_zone(away_team),
        game_time_zone=game_info.get('game_time_zone', 'ET')
    )
    
    # Calculate W-Factors (if weather data available)
    wfactors = WFactorCalculator.calculate_complete_wfactors(
        temperature_f=game_info.get('temperature'),
        home_team_warm_weather=is_warm_weather_team(home_team),
        visiting_team_warm_weather=is_warm_weather_team(away_team),
        home_team_dome=is_dome_team(home_team),
        visiting_team_dome=is_dome_team(away_team),
        is_raining=game_info.get('rain', False),
        wind_speed_mph=game_info.get('wind', 0)
    )
    
    # Net advantage
    net_sfactor = home_sfactors.spread_adjustment - away_sfactors.spread_adjustment
    net_adjustment = net_sfactor + wfactors.spread_adjustment
    
    print(f"\n=== S and W Factor Analysis ===")
    print(f"Home S-Factors: {home_sfactors.total_points:.1f} pts → {home_sfactors.spread_adjustment:.2f}")
    print(f"Away S-Factors: {away_sfactors.total_points:.1f} pts → {away_sfactors.spread_adjustment:.2f}")
    print(f"W-Factors: {wfactors.spread_adjustment:.2f}")
    print(f"Net Adjustment: {net_adjustment:+.2f} points to home team")
    
    return net_adjustment
```

### Method 2: Modify Existing Analyzer (Full Integration)

Update `src/walters_analyzer/core/analyzer.py`:

```python
# Add import at top
from walters_analyzer.valuation.sfactor_wfactor import (
    SFactorCalculator,
    WFactorCalculator,
    TeamQuality,
    get_team_time_zone,
    is_warm_weather_team,
    is_dome_team
)

# In the analyze() method, after predicted_spread calculation:
def analyze(self, matchup: GameInput) -> GameAnalysis:
    # ... existing injury and predicted spread code ...
    
    predicted_spread = self.valuation.calculate_predicted_spread(
        matchup.home_team.name,
        matchup.away_team.name,
        list(matchup.home_team.injuries),
        list(matchup.away_team.injuries),
    )
    
    # NEW: Calculate S and W Factors
    home_sfactors = SFactorCalculator.calculate_complete_sfactors(
        is_home=True,
        # Add game context from matchup data
        team_time_zone=get_team_time_zone(matchup.home_team.abbrev),
        game_time_zone="ET",  # Get from game data
    )
    
    away_sfactors = SFactorCalculator.calculate_complete_sfactors(
        is_home=False,
        team_time_zone=get_team_time_zone(matchup.away_team.abbrev),
        game_time_zone="ET",
    )
    
    wfactors = WFactorCalculator.calculate_complete_wfactors(
        home_team_warm_weather=is_warm_weather_team(matchup.home_team.abbrev),
        visiting_team_warm_weather=is_warm_weather_team(matchup.away_team.abbrev),
        home_team_dome=is_dome_team(matchup.home_team.abbrev),
        visiting_team_dome=is_dome_team(matchup.away_team.abbrev)
    )
    
    # Apply adjustments to predicted spread
    net_factor_adjustment = (
        home_sfactors.spread_adjustment - 
        away_sfactors.spread_adjustment + 
        wfactors.spread_adjustment
    )
    
    adjusted_predicted_spread = predicted_spread + net_factor_adjustment
    
    # Continue with existing edge calculation using adjusted spread
    market_spread = matchup.odds.spread.home_spread if matchup.odds else 0.0
    edge = round(adjusted_predicted_spread - market_spread, 1)
    
    # Add S/W factor info to notes
    notes = [
        f"Net injury advantage: {injury_advantage:+.1f} pts",
        f"S/W Factor adjustment: {net_factor_adjustment:+.2f} pts",
        f"Adjusted spread {adjusted_predicted_spread:+.1f} vs market {market_spread:+.1f}",
    ] + [alert.description for alert in key_alerts]
    
    # ... rest of existing code ...
```

## Data Requirements

To use S and W factors, you need:

**From Game Schedule:**
- Is Thursday/Sunday/Monday night game?
- Is team coming off bye week?
- Time zone of game location

**From Weather API:**
- Temperature (if outdoor game)
- Precipitation status
- Wind speed

**From Team Data:**
- Team abbreviation (for time zone lookup)
- Division/Conference matchup info
- Previous game result (for bounce-back)

## Example: Week 12 Bills @ Lions

```python
from billy_walters_sfactor_reference import *

# Bills @ Lions, Week 12
game_data = {
    'home_team': 'DET',
    'away_team': 'BUF',
    'same_division': False,
    'same_conference': True,
    'home_off_bye': False,  # Lions NOT off bye (they were Week 5)
    'away_off_bye': False,
    'thursday_night': False,
    'sunday_night': False,
    'game_time_zone': 'ET',
    'temperature': None,  # Indoor game at Ford Field
}

# Home team S-Factors
lions_sf = SFactorCalculator.calculate_complete_sfactors(
    is_home=True,
    same_division=False,
    same_conference=True,
    coming_off_bye=False,
    team_time_zone='ET',
    game_time_zone='ET'
)

# Away team S-Factors  
bills_sf = SFactorCalculator.calculate_complete_sfactors(
    is_home=False,
    same_division=False,
    same_conference=True,
    team_time_zone='ET',
    game_time_zone='ET'
)

# W-Factors (indoor game)
w_factors = WFactorCalculator.calculate_complete_wfactors(
    temperature_f=None,  # Indoor
    home_team_dome=True,
    visiting_team_dome=False
)

print(f"Lions advantage: {lions_sf.spread_adjustment:.2f}")
print(f"Bills advantage: {bills_sf.spread_adjustment:.2f}")
print(f"Weather adjustment: {w_factors.spread_adjustment:.2f}")
print(f"Net: {lions_sf.spread_adjustment - bills_sf.spread_adjustment + w_factors.spread_adjustment:.2f}")
```

## Next Steps

1. **Test the module** - Run the test script above
2. **Choose integration method** - Start with Method 1 (simple) or go full with Method 2
3. **Gather game context data** - Build collectors for schedule/weather info
4. **Add to reports** - Include S/W factor breakdown in analysis output
5. **Validate** - Compare with/without factors to measure impact

## Reference Materials

- **Quick Reference:** `docs/SFACTOR_QUICK_REFERENCE.md` - Print this!
- **Full Documentation:** Check `/mnt/project/SFACTOR_WFACTOR_IMPLEMENTATION_GUIDE.md` for complete details
- **Module Code:** `billy_walters_sfactor_reference.py` - All calculations

## Support

If you get import errors:
```powershell
# Make sure you're in project root
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Test import
python -c "from billy_walters_sfactor_reference import SFactorCalculator; print('SUCCESS')"
```

If helper functions not found:
```python
# Use full module reference
import billy_walters_sfactor_reference as sfactor
sfactor.get_team_time_zone("BUF")
```

---

**Status:** ✅ S and W Factor system copied to Windows and ready for integration!
