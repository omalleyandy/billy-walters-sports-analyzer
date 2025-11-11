# Weather Alert Calibration Analysis

**Date**: 2025-11-11
**Issue**: Verify alert adjustments align with Billy Walters Advanced Masterclass W-Factors

## Billy Walters W-Factors (Official Methodology)

From Advanced Masterclass PRD (lines 409-419):

```python
W_FACTORS = {
    'wind_15mph': -0.20,          # Wind affects passing
    'wind_20mph': -0.40,          # Severe wind
    'rain_moderate': -0.20,       # Moderate rain
    'rain_heavy': -0.40,          # Heavy rain
    'snow_light': -0.20,          # Light snow
    'snow_heavy': -0.60,          # Heavy snow
    'extreme_cold': -0.20,        # Below 20°F
    'extreme_heat': -0.20,        # Above 90°F for cold-weather team
}
```

**Key Principle**: Each W-Factor worth 0.20 points (S-W-E system)

## Current Weather Condition Implementation

From `billy_walters_edge_detector.py` (lines 535-548):

```python
# Wind impact (most important for passing)
if wind_speed and wind_speed > 15:
    condition_total_adj -= min((wind_speed - 15) * 0.3, 5.0)  # 15-20mph: -1.5pts, 20+mph: -3.0pts
    condition_spread_adj -= 1.0

# Temperature impact
if temperature and temperature < 32:
    condition_total_adj -= 2.5  # Cold weather
    condition_spread_adj -= 0.5

# Precipitation
if precipitation and precipitation.lower() in ["rain", "snow"]:
    condition_total_adj -= 3.0  # Rain/snow
    condition_spread_adj -= 1.0
```

## Current Weather Alert Implementation

From `weather_alert_mapper.py`:

```python
ALERT_ADJUSTMENTS = {
    "Blizzard Warning": (-7.0, -2.5, "HIGH"),           # CRITICAL
    "Winter Storm Warning": (-5.0, -2.0, "HIGH"),       # MAJOR
    "Winter Weather Advisory": (-2.5, -1.0, "MEDIUM"),  # MODERATE
    "High Wind Warning": (-5.5, -2.0, "HIGH"),          # MAJOR
    "Wind Advisory": (-3.5, -1.5, "HIGH"),              # MODERATE
    # ... 20+ more alert types
}
```

## Analysis: Significant Discrepancy

### Issue 1: Total Adjustments Too Large

**Billy Walters W-Factors**: 0.20-0.60 points max
**Current Implementation**: 2.5-7.0 points (10-35× larger!)

### Issue 2: Condition Calculations Misaligned

| Condition | Billy Walters | Current | Ratio |
|-----------|---------------|---------|-------|
| Wind 15-20 MPH | -0.20 pts | -1.5 pts | 7.5× |
| Wind 20+ MPH | -0.40 pts | -3.0 pts | 7.5× |
| Cold (<32°F) | -0.20 pts | -2.5 pts | 12.5× |
| Rain/Snow | -0.20 to -0.60 pts | -3.0 pts | 5-15× |

### Issue 3: Alert Adjustments Extremely Oversized

| Alert | Current | Billy Walters Equivalent | Ratio |
|-------|---------|-------------------------|-------|
| Winter Storm Warning | -5.0 pts | ~-0.60 pts (heavy snow) | 8.3× |
| Blizzard Warning | -7.0 pts | ~-0.80 pts (extreme snow + wind) | 8.75× |
| High Wind Warning | -5.5 pts | ~-0.40 pts (severe wind) | 13.75× |
| Winter Weather Advisory | -2.5 pts | ~-0.20 to -0.40 pts | 6.25-12.5× |

## Recommended Corrections

### 1. Condition-Based Adjustments (billy_walters_edge_detector.py)

**Current (INCORRECT)**:
```python
# Wind impact
if wind_speed and wind_speed > 15:
    condition_total_adj -= min((wind_speed - 15) * 0.3, 5.0)
    condition_spread_adj -= 1.0

# Temperature impact
if temperature and temperature < 32:
    condition_total_adj -= 2.5
    condition_spread_adj -= 0.5

# Precipitation
if precipitation and precipitation.lower() in ["rain", "snow"]:
    condition_total_adj -= 3.0
    condition_spread_adj -= 1.0
```

**Corrected (BILLY WALTERS ALIGNED)**:
```python
# Wind impact (Billy Walters W-Factors)
if wind_speed:
    if wind_speed >= 20:
        condition_total_adj -= 0.40  # wind_20mph
        condition_spread_adj -= 0.15
    elif wind_speed >= 15:
        condition_total_adj -= 0.20  # wind_15mph
        condition_spread_adj -= 0.10

# Temperature impact (Billy Walters W-Factors)
if temperature:
    if temperature < 20:
        condition_total_adj -= 0.20  # extreme_cold
        condition_spread_adj -= 0.10
    elif temperature > 90:
        condition_total_adj -= 0.20  # extreme_heat (cold-weather teams)
        condition_spread_adj -= 0.10

# Precipitation (Billy Walters W-Factors)
if precipitation:
    precip_lower = precipitation.lower()
    if precip_lower == "snow":
        # Determine severity based on weather data or default to moderate
        condition_total_adj -= 0.40  # Assume moderate-heavy snow
        condition_spread_adj -= 0.15
    elif precip_lower == "rain":
        condition_total_adj -= 0.30  # Assume moderate rain
        condition_spread_adj -= 0.12
```

### 2. Alert-Based Adjustments (weather_alert_mapper.py)

**Current (INCORRECT)**:
```python
ALERT_ADJUSTMENTS = {
    "Blizzard Warning": (-7.0, -2.5, "HIGH"),
    "Winter Storm Warning": (-5.0, -2.0, "HIGH"),
    "Winter Weather Advisory": (-2.5, -1.0, "MEDIUM"),
    "High Wind Warning": (-5.5, -2.0, "HIGH"),
    "Wind Advisory": (-3.5, -1.5, "HIGH"),
    # ...
}
```

**Corrected (BILLY WALTERS ALIGNED)**:
```python
ALERT_ADJUSTMENTS = {
    # Winter Weather (Billy Walters: -0.20 to -0.60)
    "Blizzard Warning": (-0.80, -0.30, "HIGH"),         # Extreme: heavy snow + wind
    "Ice Storm Warning": (-0.70, -0.25, "HIGH"),        # Extreme: ice accumulation
    "Winter Storm Warning": (-0.60, -0.25, "HIGH"),     # Heavy snow equivalent
    "Heavy Snow Warning": (-0.50, -0.20, "HIGH"),       # Heavy snow
    "Winter Weather Advisory": (-0.30, -0.12, "MEDIUM"), # Light-moderate snow
    "Snow Advisory": (-0.20, -0.10, "MEDIUM"),          # Light snow

    # Wind (Billy Walters: -0.20 to -0.40)
    "Extreme Wind Warning": (-0.50, -0.20, "HIGH"),     # Beyond 20mph threshold
    "High Wind Warning": (-0.40, -0.15, "HIGH"),        # Severe wind (20+ mph)
    "Wind Advisory": (-0.20, -0.10, "MEDIUM"),          # Moderate wind (15+ mph)

    # Precipitation (Billy Walters: -0.20 to -0.40)
    "Flash Flood Warning": (-0.50, -0.20, "HIGH"),      # Severe rain + field issues
    "Flood Warning": (-0.40, -0.15, "MEDIUM"),          # Heavy rain
    "Heavy Rain Warning": (-0.35, -0.12, "MEDIUM"),     # Heavy rain
    "Excessive Rainfall": (-0.30, -0.12, "MEDIUM"),     # Moderate-heavy rain

    # Thunderstorms (Billy Walters: -0.20 to -0.40 + delays)
    "Severe Thunderstorm Warning": (-0.40, -0.15, "MEDIUM"), # Heavy rain + wind + delays
    "Thunderstorm Watch": (-0.20, -0.08, "LOW"),        # Moderate rain possibility
    "Tornado Warning": (-0.60, -0.25, "HIGH"),          # Game delays likely

    # Temperature (Billy Walters: -0.20)
    "Extreme Cold Warning": (-0.30, -0.12, "HIGH"),     # Below 20°F + wind chill
    "Wind Chill Warning": (-0.25, -0.10, "MEDIUM"),     # Extreme wind chill
    "Wind Chill Advisory": (-0.15, -0.06, "LOW"),       # Cold + wind
    "Cold Weather Advisory": (-0.20, -0.08, "MEDIUM"),  # Below 20°F
    "Excessive Heat Warning": (-0.25, -0.10, "MEDIUM"), # Above 90°F
    "Heat Advisory": (-0.15, -0.06, "LOW"),             # Above 90°F

    # Fog (Billy Walters: not specified, conservative)
    "Dense Fog Advisory": (-0.15, -0.06, "LOW"),        # Visibility issues

    # Coastal (less relevant, conservative)
    "Gale Warning": (-0.25, -0.10, "MEDIUM"),           # Coastal wind
    "Storm Warning": (-0.40, -0.15, "HIGH"),            # Coastal storm
}
```

### 3. Severity Classification Thresholds

**Current (INCORRECT)**:
```python
if abs_impact >= 6.0:
    return "CRITICAL"
elif abs_impact >= 4.0:
    return "MAJOR"
elif abs_impact >= 2.0:
    return "MODERATE"
elif abs_impact >= 1.0:
    return "MINOR"
else:
    return "NEGLIGIBLE"
```

**Corrected (BILLY WALTERS ALIGNED)**:
```python
if abs_impact >= 0.60:
    return "CRITICAL"  # Blizzard, Tornado, extreme conditions
elif abs_impact >= 0.40:
    return "MAJOR"     # Winter Storm, High Wind, Heavy Rain
elif abs_impact >= 0.20:
    return "MODERATE"  # Advisories, Moderate conditions
elif abs_impact >= 0.10:
    return "MINOR"     # Watches, Light conditions
else:
    return "NEGLIGIBLE"
```

## Context: Billy Walters S-W-E System

**Important**: Billy Walters uses a **modular factor system**:
- **S-Factors** (Special): 0.20-0.40 pts each (division, rest, coaching)
- **W-Factors** (Weather): 0.20-0.60 pts each (wind, temp, precip)
- **E-Factors** (Emotional): 0.20-0.40 pts each (revenge, lookahead, letdown)

**Total SWE adjustment**: Typically 0.5-2.0 points combined

**Power ratings dominate**: 70-100 scale (30 point range)
**Weather is secondary**: Modifies spread by 0.2-0.6 points, not 5-7 points

## Impact of Correction

### Before (Overcorrecting)
```
Blizzard Warning: -7.0 pts total
Power Rating Spread: +4.5 pts
Weather-adjusted: +4.5 - 7.0 = -2.5 (flips bet!)
```

### After (Proper Billy Walters)
```
Blizzard Warning: -0.8 pts total
Power Rating Spread: +4.5 pts
Weather-adjusted: +4.5 - 0.8 = +3.7 (modifies, doesn't flip)
```

## Historical Context Multiplier

From `billy_walters_config.json`:
```json
"WEATHER_INJURY_COMPOUND": 1.2
```

Billy Walters principle: Weather compounds with injuries by 20%
- Injury impact: 3.0 pts
- Weather: 0.40 pts
- Combined: (3.0 + 0.40) × 1.2 = 4.08 pts (not 3.0 + 5.0 = 8.0!)

## Recommended Implementation Priority

### Phase 1: Immediate (Critical)
1. Update `ALERT_ADJUSTMENTS` table in `weather_alert_mapper.py` (divide by ~10)
2. Update `_classify_severity()` thresholds (divide by ~10)
3. Update condition calculations in `billy_walters_edge_detector.py` (divide by ~10)

### Phase 2: Testing (Next Session)
1. Re-run test suite with corrected values
2. Verify severity classifications align
3. Validate maximum principle still works correctly
4. Test with historical games where weather affected outcome

### Phase 3: Documentation (Next Session)
1. Update `WEATHER_ALERTS_IMPLEMENTATION.md` with corrected values
2. Add section explaining Billy Walters S-W-E system
3. Document why previous values were 10× too large
4. Add examples with correct calculations

## References

- **Billy Walters Methodology**: `docs/guides/billy_walters_analytics_prd_v1.5.md` (lines 409-419)
- **Current Conditions**: `src/walters_analyzer/valuation/billy_walters_edge_detector.py` (lines 535-548)
- **Current Alerts**: `src/walters_analyzer/valuation/weather_alert_mapper.py` (lines 19-55)
- **Config**: `src/walters_analyzer/valuation/billy_walters_config.json` (line 240)

## Conclusion

The current weather alert adjustments are **8-13× too large** compared to Billy Walters' documented W-Factor methodology. Weather should **modify** spreads by 0.2-0.8 points, not **dominate** them with 5-7 point adjustments.

**Immediate Action Required**: Recalibrate all weather adjustments to align with Billy Walters' 0.20-0.60 point W-Factor system.
