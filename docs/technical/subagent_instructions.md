# NFL Subagent Instructions (Dynamic Week Detection)

**Purpose**: Parallel data collection for Billy Walters edge detection  
**Target**: Current NFL Week (auto-detected from system date)  
**Status**: Ready for execution when live access is available

---

## Overview

This document provides detailed instructions for six subagents to work in parallel collecting NFL data for the current week. Each subagent handles a specific data domain, with standardized output formats that integrate directly into the Billy Walters edge detector.

**Week Detection**: The system automatically detects the current NFL week based on the current date. Use `get_nfl_week()` from `src/walters_analyzer/season_calendar.py` to determine the target week.

### Integration Flow

```
Subagent 1: Schedule & Game Info
    ↓
Subagent 2: Betting Lines → CSV (game_id keyed)
    ↓
Subagent 3: Weather Data → JSON (stadium-based)
    ↓
Subagent 4: Team Situational Analysis → JSON (power ratings + S-factors)
    ↓
Subagent 5: Player Situational Analysis → JSON (player efficiency splits)
    ↓
Subagent 6: Injury Reports → JSON (official + beat reports)
    ↓
Main Analyzer: Reconcile all data → Edge Detection → Kelly Criterion Bet Sizing
```

---

## Subagent 1: Schedule & Game Info

**Objective**: Pull official NFL fixtures for current week with complete metadata

**Note**: Use `get_nfl_week()` from `src/walters_analyzer/season_calendar.py` to detect current week.

### Data Sources
- **Primary**: NFL.com official schedule API
- **Backup**: ESPN API (`src/data/espn_api_client.py`)
- **Verification**: Pro Football Reference

### Required Fields

**Output Format**: JSON file (`data/current/nfl_week_{week}_schedule.json`)

**Note**: Replace `{week}` with current week number (e.g., `nfl_week_11_schedule.json` for Week 11).

```json
{
  "week": 11,
  "season": 2025,
  "scraped_at": "2025-11-13T10:00:00Z",
  "games": [
    {
      "game_id": "NFL_2025_11_BUF_KC",
      "week": 11,
      "date": "2025-11-17",
      "time": "20:20:00",
      "timezone": "America/New_York",
      "home_team": "Kansas City",
      "away_team": "Buffalo",
      "home_abbreviation": "KC",
      "away_abbreviation": "BUF",
      "stadium": {
        "name": "Arrowhead Stadium",
        "city": "Kansas City",
        "state": "MO",
        "is_dome": false,
        "surface_type": "grass",
        "capacity": 76416
      },
      "status": "scheduled",
      "is_postponed": false,
      "is_neutral_site": false,
      "is_international": false,
      "travel_distance_miles": 1131,
      "away_team_previous_opponent": "Dolphins",
      "away_team_previous_result": "L 24-31",
      "away_team_rest_days": 7,
      "home_team_previous_opponent": "Broncos",
      "home_team_previous_result": "W 27-24",
      "home_team_rest_days": 7,
      "is_divisional_game": false,
      "is_rivalry_game": false,
      "unique_circumstances": []
    }
  ]
}
```

### Collection Tasks

1. **Pull Official Schedule**
   ```python
   from walters_analyzer.season_calendar import get_nfl_week
   
   current_week = get_nfl_week()
   if current_week is None:
       raise ValueError("NFL season not active")
   
   # Query NFL.com API or ESPN API for current_week
   # Filter for games where week == current_week and season == 2025
   ```
   - Confirm no postponements (`status != "postponed"`)

2. **Stadium Information**
   - Lookup stadium details for each home team
   - Critical: Flag `is_dome` status (needed for weather adjustments)
   - Record surface type (grass vs turf affects weather impact)

3. **Travel & Rest Analysis**
   - Calculate travel distance (away team city → home team city)
   - Count rest days since previous game (must be 6-8 for normal schedule)
   - Flag short-week scenarios (Thursday night → Sunday, <6 rest days)

4. **Contextual Flags**
   - Check if divisional game (same division)
   - Check if rivalry game (historical rivalries)
   - Flag international games (London, Mexico City, etc.)
   - Flag neutral site games (rare but possible)

5. **Previous Week Results**
   - Record previous opponent for both teams
   - Record previous result (W/L and score)
   - Use for momentum/revenge spot analysis

### Validation Rules

- ✅ All 16 games present (unless bye weeks)
- ✅ All game_id fields unique
- ✅ All dates fall within current week date range (use `get_week_date_range(week, League.NFL)`)
- ✅ All stadiums have `is_dome` flag set
- ✅ No null values for critical fields (home_team, away_team, date, time)

### File Output

**Location**: `data/current/nfl_week_{week}_schedule.json`  
**Format**: JSON (pretty-printed, 2-space indent)  
**Timestamp**: Include `scraped_at` in ISO 8601 format

---

## Subagent 2: Betting Lines

**Objective**: Query Overtime.ag for full market (spread, ML, totals, 1H lines)

### Data Sources
- **Primary**: Overtime.ag API (`src/data/overtime_api_client.py`)
- **Endpoint**: `https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering`
- **Method**: HTTP POST (no browser required)

### Required Fields

**Output Format**: CSV file (`output/overtime/nfl/pregame/api_walters_week_{week}_{timestamp}.csv`)

**Note**: Replace `{week}` with current week number and `{timestamp}` with ISO 8601 timestamp.

**CSV Columns**:
```
game_id,away_team,home_team,spread,spread_odds_away,spread_odds_home,total,over_odds,under_odds,moneyline_away,moneyline_home,first_half_spread,first_half_total,scraped_at,book_margin,opening_spread,opening_total
```

**Example Row**:
```csv
NFL_2025_11_BUF_KC,Buffalo,Kansas City,-2.5,-110,-110,52.5,-110,-110,+140,-160,-1.5,26.5,2025-11-13T10:15:00Z,4.5%,-3.0,51.0
```

**Note**: Spread is from home team perspective (negative = home favorite, positive = home underdog)

### Collection Tasks

1. **Query Overtime.ag API**
   ```python
   # Use existing client
   from src.data.overtime_api_client import OvertimeApiClient
   
   client = OvertimeApiClient()
   nfl_data = await client.scrape_nfl()
   ```

2. **Extract Full Market**
   - Main spread (full game)
   - First-half spread (1H)
   - Total (over/under)
   - First-half total (1H total)
   - Moneyline (both sides)

3. **Capture Line History**
   - Record opening line (if available)
   - Record current line
   - Calculate movement (current - opening)

4. **Calculate Book Margin**
   - Convert odds to implied probabilities
   - Book margin = (1 / prob1 + 1 / prob2) - 1
   - Example: -110 both sides = (1/0.524 + 1/0.524) - 1 = 4.5%

5. **Timestamp All Data**
   - Record exact scrape time (UTC)
   - Lines move frequently - timestamp critical for CLV tracking

### Validation Rules

- ✅ All 16 games have spread, total, moneyline
- ✅ Spread odds sum to ~104.5% (typical book margin)
- ✅ All timestamps in ISO 8601 format
- ✅ No duplicate game_id entries

### File Output

**Location**: `output/overtime/nfl/pregame/api_walters_week_{week}_{timestamp}.csv`  
**Format**: CSV (UTF-8, comma-delimited)  
**Header Row**: Required (column names as shown above)  
**Backup JSON**: Also save as JSON for downstream processing (`api_walters_week_{week}_{timestamp}.json`)

---

## Subagent 3: Weather Data

**Objective**: Fetch forecasted kickoff conditions for all outdoor stadiums

### Data Sources
- **Primary**: AccuWeather API (`src/data/accuweather_client.py`)
- **Backup**: OpenWeather API (`src/data/openweather_client.py`)
- **Plan**: AccuWeather Starter (free tier - 12-hour hourly forecast limit)

### Required Fields

**Output Format**: JSON file (`data/current/nfl_week_{week}_weather.json`)

```json
{
  "week": 11,
  "scraped_at": "2025-11-13T10:30:00Z",
  "games": [
    {
      "game_id": "NFL_2025_11_BUF_KC",
      "stadium": "Arrowhead Stadium",
      "city": "Kansas City",
      "state": "MO",
      "kickoff_time": "2025-11-17T20:20:00-06:00",
      "is_dome": false,
      "weather": {
        "temperature_f": 38.0,
        "feels_like_f": 32.0,
        "wind_speed_mph": 18.5,
        "wind_gust_mph": 28.0,
        "wind_direction": "NW",
        "precipitation_chance": 0.15,
        "precipitation_type": "none",
        "humidity": 65.0,
        "conditions": "partly_cloudy",
        "forecast_source": "AccuWeather",
        "forecast_hours_ahead": 168
      },
      "historical_norms": {
        "avg_temp_nov": 48.0,
        "avg_wind_nov": 12.0,
        "avg_precip_nov": 0.35
      },
      "weather_impact_flags": {
        "wind_sensitive": true,
        "temp_sensitive": true,
        "precip_sensitive": false,
        "wind_threshold_met": true,
        "precip_threshold_met": false
      },
      "billy_walters_adjustments": {
        "temperature_adjustment": -1.0,
        "wind_adjustment": -3.0,
        "precipitation_adjustment": 0.0,
        "total_adjustment": -3.0,
        "spread_adjustment": -0.5
      }
    },
    {
      "game_id": "NFL_2025_11_ATL_NO",
      "stadium": "Mercedes-Benz Stadium",
      "is_dome": true,
      "weather": null,
      "weather_impact_flags": {
        "wind_sensitive": false,
        "temp_sensitive": false,
        "precip_sensitive": false
      }
    }
  ]
}
```

### Collection Tasks

1. **Load Schedule Data**
   ```python
   from walters_analyzer.season_calendar import get_nfl_week
   
   current_week = get_nfl_week()
   schedule_path = f"data/current/nfl_week_{current_week}_schedule.json"
   # Read schedule file
   ```
   - Extract game_id, stadium, kickoff_time for each game

2. **Filter Dome Stadiums**
   - Skip weather fetch for `is_dome: true` games
   - Set weather to `null` with appropriate flags

3. **Fetch Weather for Outdoor Stadiums**
   ```python
   from src.data.accuweather_client import AccuWeatherClient
   
   client = AccuWeatherClient(api_key=os.getenv('ACCUWEATHER_API_KEY'))
   await client.connect()
   
   # For games <12 hours away: Use hourly forecast (accurate)
   # For games >12 hours away: Use current conditions (estimate)
   hours_ahead = (kickoff_time - now).total_seconds() / 3600
   
   if hours_ahead <= 12:
       weather = await client.get_hourly_forecast(location_key, hours=min(hours_ahead, 12))
   else:
       weather = await client.get_current_conditions(location_key)
   ```

4. **Calculate Billy Walters Adjustments**
   - **Temperature**: <20°F = -4pts, 20-25°F = -3pts, 25-32°F = -2pts, 32-40°F = -1pt
   - **Wind**: >20mph = -5pts total, 15-20mph = -3pts, 10-15mph = -1pt
   - **Precipitation**: Snow >60% = -5pts, Rain >60% = -3pts
   - **Spread Adjustment**: Wind >15mph = -0.5pts (favors rushing team)

5. **Flag Weather-Sensitive Thresholds**
   - `wind_threshold_met`: Wind ≥15 mph
   - `precip_threshold_met`: Precipitation chance >60% and type != "none"

6. **Historical Climate Norms** (Optional)
   - Lookup November averages for stadium city
   - Compare current forecast to historical norms
   - Flag if significantly different (>10°F, >5mph wind difference)

### Validation Rules

- ✅ All outdoor stadiums have weather data
- ✅ All dome stadiums have `weather: null`
- ✅ All kickoff_times in timezone-aware format
- ✅ All adjustments calculated correctly (Billy Walters thresholds)

### File Output

**Location**: `data/current/nfl_week_{week}_weather.json`  
**Format**: JSON (pretty-printed, 2-space indent)  
**Timestamp**: Include `scraped_at` in ISO 8601 format

---

## Subagent 4: Team Situational Analysis

**Objective**: Compile team-level metrics and update Billy Walters power ratings

### Data Sources
- **Power Ratings**: Existing `data/power_ratings_nfl_2025.json` (90/10 update formula)
- **Team Stats**: ESPN API (`src/data/espn_api_client.py`)
- **Advanced Metrics**: nflfastR (EPA/play, success rate) - if available
- **Pace Data**: Pro Football Reference (plays per game)

### Required Fields

**Output Format**: JSON file (`data/current/nfl_week_{week}_team_situational.json`)

```json
{
  "week": 11,
  "scraped_at": "2025-11-13T11:00:00Z",
  "power_ratings_updated": true,
  "teams": [
    {
      "team": "Kansas City",
      "team_abbreviation": "KC",
      "power_rating": {
        "overall": 92.5,
        "offensive": 23.5,
        "defensive": 8.2,
        "home_field_advantage": 2.5,
        "last_updated": "2025-11-10",
        "update_method": "billy_walters_90_10"
      },
      "current_season_metrics": {
        "epa_per_play": 0.12,
        "success_rate": 0.48,
        "explosive_play_rate": 0.18,
        "plays_per_game": 68.5,
        "pace_adjustment": 0.0,
        "points_per_game": 28.5,
        "points_allowed_per_game": 21.2,
        "turnover_margin": 0.3,
        "penalties_per_game": 6.2,
        "penalty_yards_per_game": 52.0,
        "special_teams_dvoa": 2.5
      },
      "situational_factors": {
        "rest_days": 7,
        "rest_advantage": 0.0,
        "travel_distance_miles": 0,
        "travel_penalty": 0.0,
        "consecutive_road_games": 0,
        "consecutive_home_games": 2,
        "short_week": false,
        "coming_off_bye": false,
        "divisional_game": false,
        "rivalry_game": false,
        "revenge_spot": false,
        "lookahead_spot": false,
        "letdown_spot": false,
        "total_s_factor_adjustment": 0.0,
        "s_factor_cap_applied": false
      }
    }
  ],
  "games": [
    {
      "game_id": "NFL_2025_11_BUF_KC",
      "away_team": "Buffalo",
      "home_team": "Kansas City",
      "matchup_situational": {
        "rest_differential": 0,
        "travel_advantage": "home",
        "home_team_s_factor": 0.0,
        "away_team_s_factor": 0.0,
        "net_s_factor": 0.0,
        "max_s_factor_cap": 2.0,
        "s_factor_cap_applied": false
      }
    }
  ]
}
```

### Collection Tasks

1. **Update Power Ratings (Billy Walters 90/10 Formula)**
   ```python
   # Formula: New Rating = (Old Rating × 0.90) + (Game Result × 0.10)
   # Load existing ratings
   from src.walters_analyzer.valuation.power_ratings import PowerRatingSystem
   
   prs = PowerRatingSystem()
   prs.load_ratings(Path("data/power_ratings_nfl_2025.json"))
   
   # Update from Week 10 results
   for game_result in week_10_results:
       prs.update_ratings_from_game(game_result)
   
   # Save updated ratings
   prs.save_ratings(Path("data/power_ratings_nfl_2025.json"))
   ```

2. **Collect Current Season Metrics**
   - **EPA/Play**: Expected Points Added per play (offense + defense)
   - **Success Rate**: % of plays with positive EPA
   - **Explosive Play Rate**: % of plays gaining 20+ yards (offense) or allowing 20+ yards (defense)
   - **Pace**: Plays per game (affects totals, not spreads)
   - **Turnover Margin**: Takeaways - Giveaways per game
   - **Penalties**: Penalties and penalty yards per game
   - **Special Teams DVOA**: If available from Football Outsiders

3. **Calculate Situational Factors (S-Factor)**
   - **Rest Advantage**: Bye week (+3pts), 8+ rest days (+1pt), 6 rest days (0), <6 rest days (-1pt)
   - **Travel Penalty**: >1500 miles = -1.5pts, 1000-1500 miles = -1pt, 500-1000 miles = -0.5pts
   - **Consecutive Road Games**: 3+ consecutive road games = -1pt
   - **Short Week**: Thursday night after Sunday = -0.5pts
   - **Divisional Game**: +0.5pts intensity
   - **Rivalry Game**: +0.5pts motivation
   - **Revenge Spot**: Lost previous meeting = +0.5pts
   - **Lookahead Spot**: Next week is marquee opponent = -0.5pts
   - **Letdown Spot**: Coming off emotional win = -0.5pts

4. **Apply S-Factor Caps**
   - **Maximum Total S-Factor**: ±2.0 points per team
   - **Maximum Net S-Factor**: ±3.0 points per game (combined adjustments)
   - Flag when cap is applied (`s_factor_cap_applied: true`)

### Validation Rules

- ✅ All 32 teams have power ratings
- ✅ All power ratings updated with latest game results
- ✅ All S-factors within ±2.0 cap per team
- ✅ All net S-factors within ±3.0 cap per game

### File Output

**Location**: `data/current/nfl_week_{week}_team_situational.json`  
**Format**: JSON (pretty-printed, 2-space indent)  
**Backup**: Also update `data/power_ratings_nfl_2025.json` with latest ratings

---

## Subagent 5: Player Situational Analysis

**Objective**: Gather player efficiency splits for key units (QB, OL, CB rooms)

### Data Sources
- **Player Stats**: ESPN API, Pro Football Reference
- **Snap Counts**: Pro Football Reference (usage tracking)
- **Injury Valuation Tables**: `src/walters_analyzer/valuation/player_values.py`

### Required Fields

**Output Format**: JSON file (`data/current/nfl_week_{week}_player_situational.json`)

```json
{
  "week": 11,
  "scraped_at": "2025-11-13T11:30:00Z",
  "teams": [
    {
      "team": "Kansas City",
      "team_abbreviation": "KC",
      "key_units": {
        "quarterback": {
          "starter": "Patrick Mahomes",
          "backup": "Blaine Gabbert",
          "starter_epa_per_play": 0.18,
          "backup_epa_per_play": 0.05,
          "starter_snap_pct": 0.98,
          "backup_snap_pct": 0.02,
          "injury_status": "healthy",
          "point_value_if_out": 4.5,
          "usage_change": "none"
        },
        "offensive_line": {
          "left_tackle": {"player": "Donovan Smith", "pff_grade": 72.5, "injury_status": "healthy", "point_value_if_out": 1.5},
          "right_tackle": {"player": "Jawaan Taylor", "pff_grade": 68.0, "injury_status": "healthy", "point_value_if_out": 1.5},
          "center": {"player": "Creed Humphrey", "pff_grade": 85.0, "injury_status": "healthy", "point_value_if_out": 1.0},
          "left_guard": {"player": "Joe Thuney", "pff_grade": 78.5, "injury_status": "questionable", "point_value_if_out": 0.8},
          "right_guard": {"player": "Trey Smith", "pff_grade": 75.0, "injury_status": "healthy", "point_value_if_out": 0.8},
          "cluster_impact": 0.0,
          "usage_change": "none"
        },
        "cornerback_room": {
          "cb1": {"player": "L'Jarius Sneed", "snap_pct": 0.95, "pff_grade": 82.0, "injury_status": "healthy", "point_value_if_out": 1.2},
          "cb2": {"player": "Trent McDuffie", "snap_pct": 0.92, "pff_grade": 79.5, "injury_status": "healthy", "point_value_if_out": 1.2},
          "cb3": {"player": "Jaylen Watson", "snap_pct": 0.35, "pff_grade": 68.0, "injury_status": "healthy", "point_value_if_out": 0.6},
          "room_impact": 0.0,
          "usage_change": "none"
        },
        "running_back": {
          "rb1": {"player": "Isiah Pacheco", "snap_pct": 0.65, "ypc": 4.8, "injury_status": "healthy", "point_value_if_out": 2.5},
          "rb2": {"player": "Clyde Edwards-Helaire", "snap_pct": 0.25, "ypc": 4.2, "injury_status": "healthy", "point_value_if_out": 1.5},
          "usage_change": "none"
        },
        "wide_receiver": {
          "wr1": {"player": "Tyreek Hill", "snap_pct": 0.88, "target_share": 0.28, "injury_status": "healthy", "point_value_if_out": 1.8},
          "wr2": {"player": "Marquise Brown", "snap_pct": 0.82, "target_share": 0.22, "injury_status": "healthy", "point_value_if_out": 1.2},
          "usage_change": "none"
        }
      },
      "cumulative_player_impact": 0.0
    }
  ],
  "games": [
    {
      "game_id": "NFL_2025_11_BUF_KC",
      "away_team": "Buffalo",
      "home_team": "Kansas City",
      "player_matchup_analysis": {
        "away_team_qb_vs_home_cb": {
          "qb_epa": 0.16,
          "cb_room_pff_grade": 80.75,
          "advantage": "qb"
        },
        "home_team_qb_vs_away_cb": {
          "qb_epa": 0.18,
          "cb_room_pff_grade": 78.5,
          "advantage": "qb"
        },
        "estimated_player_adjustment": 0.0
      }
    }
  ]
}
```

### Collection Tasks

1. **Identify Key Units Per Team**
   - **Quarterback**: Starter + backup (EPA/play comparison)
   - **Offensive Line**: LT, RT, C, LG, RG (PFF grades if available)
   - **Cornerback Room**: CB1, CB2, CB3 (snap % and PFF grades)
   - **Running Back**: RB1, RB2 (snap % and YPC)
   - **Wide Receiver**: WR1, WR2 (snap % and target share)

2. **Collect Player Efficiency Metrics**
   - **QB**: EPA/play, success rate, completion %
   - **OL**: PFF pass-block grade, run-block grade
   - **CB**: PFF coverage grade, passer rating allowed
   - **RB**: YPC, success rate, explosive play rate
   - **WR**: Target share, yards per route run, catch rate

3. **Map to Billy Walters Injury Values**
   ```python
   from src.walters_analyzer.valuation.player_values import PlayerValuation
   
   calculator = PlayerValuation()
   
   # Example: Elite QB out
   qb_value = calculator.get_player_value("QB", "elite", is_out=True)
   # Returns: 4.5 points
   ```

4. **Track Usage Changes**
   - Compare snap counts this week vs last 3 weeks average
   - Flag significant changes (>10% snap % change)
   - Note if starter demoted or backup promoted

5. **Calculate Cumulative Impact**
   - Sum all player impacts per team
   - Ensure total stays within 2-3 point cap
   - Separate from S-factor (S-factor is team situational, player impact is unit-specific)

### Validation Rules

- ✅ All 32 teams have key unit data
- ✅ All point values align with Billy Walters injury tables
- ✅ Cumulative player impact per team ≤ 3.0 points
- ✅ All snap percentages sum to ≤100% per position group

### File Output

**Location**: `data/current/nfl_week_{week}_player_situational.json`  
**Format**: JSON (pretty-printed, 2-space indent)

---

## Subagent 6: Injury Reports

**Objective**: Pull official injury reports and trusted beat updates

### Data Sources
- **Official**: NFL.com injury reports (Wednesday/Thursday/Friday)
- **Beat Writers**: Twitter/X feeds, team websites
- **Player News**: ESPN injury updates, Pro Football Doc analysis

### Required Fields

**Output Format**: JSON file (`data/current/nfl_week_{week}_injuries.json`)

```json
{
  "week": 11,
  "scraped_at": "2025-11-13T12:00:00Z",
  "report_date": "2025-11-13",
  "report_type": "thursday",
  "teams": [
    {
      "team": "Kansas City",
      "team_abbreviation": "KC",
      "injuries": [
        {
          "player": "Joe Thuney",
          "position": "LG",
          "injury_type": "pectoral",
          "status": "questionable",
          "practice_status": "limited",
          "estimated_point_value": 0.8,
          "point_value_if_out": 0.8,
          "point_value_if_doubtful": 0.6,
          "point_value_if_questionable": 0.0,
          "source": "nfl_official",
          "last_updated": "2025-11-13T16:00:00Z"
        },
        {
          "player": "Isiah Pacheco",
          "position": "RB",
          "injury_type": "shoulder",
          "status": "probable",
          "practice_status": "full",
          "estimated_point_value": 0.0,
          "point_value_if_out": 2.5,
          "point_value_if_doubtful": 1.5,
          "point_value_if_questionable": 0.0,
          "source": "nfl_official",
          "last_updated": "2025-11-13T16:00:00Z"
        }
      ],
      "injury_summary": {
        "total_players_listed": 2,
        "out_count": 0,
        "doubtful_count": 0,
        "questionable_count": 1,
        "probable_count": 1,
        "cumulative_point_impact": 0.0,
        "cumulative_point_impact_if_all_out": 3.3,
        "injury_cap_applied": false,
        "severity": "minor"
      }
    }
  ],
  "games": [
    {
      "game_id": "NFL_2025_11_BUF_KC",
      "away_team": "Buffalo",
      "home_team": "Kansas City",
      "injury_matchup": {
        "away_team_injury_impact": 0.0,
        "home_team_injury_impact": 0.0,
        "net_injury_adjustment": 0.0,
        "injury_cap_applied": false
      }
    }
  ]
}
```

### Collection Tasks

1. **Pull Official NFL Injury Reports**
   - Wednesday: Initial practice report
   - Thursday: Updated practice report
   - Friday: Final injury report (most accurate)
   - Saturday: Any late-breaking updates

2. **Categorize Injury Status**
   - **Out**: Player will not play (full point value applied)
   - **Doubtful**: 75% chance player will not play (75% of point value)
   - **Questionable**: 50/50 chance (0% point value - too uncertain)
   - **Probable**: Player will likely play (0% point value)

3. **Map to Billy Walters Point Values**
   ```python
   from src.walters_analyzer.valuation.injury_impacts import InjuryImpactCalculator
   
   calculator = InjuryImpactCalculator()
   
   # Example: Elite QB out
   impact = calculator.calculate_player_impact(
       player_name="Patrick Mahomes",
       position="QB",
       status="out",
       is_elite=True
   )
   # Returns: InjuryImpact(total_impact=4.5, severity="critical")
   ```

4. **Apply Injury Caps**
   - **Maximum per-team**: 3.0 points total injury impact
   - **Maximum per-game**: 5.0 points net injury adjustment (combined teams)
   - Flag when cap is applied (`injury_cap_applied: true`)

5. **Cross-Reference Beat Reports**
   - Check team beat writers for practice updates
   - Verify "questionable" players likely to play
   - Flag late-breaking injuries not yet on official report

6. **Calculate Cumulative Impact**
   - Sum all player impacts per team
   - Apply status multipliers:
     - Out: 100% of point value
     - Doubtful: 75% of point value
     - Questionable: 0% of point value (uncertain)
     - Probable: 0% of point value

### Validation Rules

- ✅ All 32 teams have injury data (even if empty list)
- ✅ All point values align with Billy Walters injury tables
- ✅ Cumulative injury impact per team ≤ 3.0 points
- ✅ All status fields are valid (out, doubtful, questionable, probable)

### File Output

**Location**: `data/current/nfl_week_{week}_injuries.json`  
**Format**: JSON (pretty-printed, 2-space indent)  
**Backup**: Also save raw NFL.com report HTML for audit trail

---

## Integration Instructions

### Step 1: Subagents Deliver Data Packets

Once all six subagents complete their collection, verify all output files exist:

```bash
# Get current week first
from walters_analyzer.season_calendar import get_nfl_week
week = get_nfl_week()

# Verify all files present
ls -la data/current/nfl_week_{week}_*.json
ls -la output/overtime/nfl/pregame/api_walters_week_{week}_*.csv
```

**Expected Files:**
- ✅ `data/current/nfl_week_{week}_schedule.json`
- ✅ `output/overtime/nfl/pregame/api_walters_week_{week}_{timestamp}.csv`
- ✅ `data/current/nfl_week_{week}_weather.json`
- ✅ `data/current/nfl_week_{week}_team_situational.json`
- ✅ `data/current/nfl_week_{week}_player_situational.json`
- ✅ `data/current/nfl_week_{week}_injuries.json`

### Step 2: Load Data into Edge Detector

```python
from src.walters_analyzer.valuation.billy_walters_edge_detector import BillyWaltersEdgeDetector
import json
import pandas as pd

# Initialize edge detector
detector = BillyWaltersEdgeDetector()

# Get current week
from walters_analyzer.season_calendar import get_nfl_week
week = get_nfl_week()

# Load power ratings (from team situational data)
with open(f"data/current/nfl_week_{week}_team_situational.json") as f:
    team_data = json.load(f)

for team_info in team_data["teams"]:
    rating = team_info["power_rating"]["overall"]
    detector.power_ratings[team_info["team"]] = PowerRating(
        team=team_info["team"],
        rating=rating,
        offensive_rating=team_info["power_rating"]["offensive"],
        defensive_rating=team_info["power_rating"]["defensive"],
        home_field_advantage=team_info["power_rating"]["home_field_advantage"],
        source="billy_walters"
    )

# Load schedule data (CRITICAL: Must be loaded first)
with open(f"data/current/nfl_week_{week}_schedule.json") as f:
    schedule_data = json.load(f)

# Load betting lines (find latest file)
import glob
import os
odds_files = glob.glob(f"output/overtime/nfl/pregame/api_walters_week_{week}_*.csv")
latest_odds = max(odds_files, key=os.path.getctime)
odds_df = pd.read_csv(latest_odds)

# Load weather data
with open(f"data/current/nfl_week_{week}_weather.json") as f:
    weather_data = json.load(f)

# Load situational factors
# (Already in team_situational.json)

# Load injury data
with open(f"data/current/nfl_week_{week}_injuries.json") as f:
    injury_data = json.load(f)
```

### Step 3: Run Edge Detection

```python
# For each game
for _, row in odds_df.iterrows():
    game_id = row["game_id"]
    away_team = row["away_team"]
    home_team = row["home_team"]
    market_spread = row["spread"]
    market_total = row["total"]
    
    # Load game-specific data
    game_schedule = next(g for g in schedule_data["games"] if g["game_id"] == game_id)
    game_weather = next(w for w in weather_data["games"] if w["game_id"] == game_id)
    game_situational = next(s for s in team_data["games"] if s["game_id"] == game_id)
    game_injuries = next(i for i in injury_data["games"] if i["game_id"] == game_id)
    
    # Build SituationalFactor
    situational = SituationalFactor(
        rest_days=game_situational["matchup_situational"]["away_team_rest_days"],
        rest_advantage=game_situational["matchup_situational"]["net_s_factor"],
        travel_distance=game_schedule["travel_distance_miles"],
        travel_penalty=game_situational["matchup_situational"]["away_team_s_factor"],
        divisional_game=game_schedule["is_divisional_game"],
        rivalry_game=game_schedule["is_rivalry_game"],
        total_adjustment=game_situational["matchup_situational"]["net_s_factor"]
    )
    
    # Build WeatherImpact
    if game_weather["weather"]:
        weather = WeatherImpact(
            temperature=game_weather["weather"]["temperature_f"],
            wind_speed=game_weather["weather"]["wind_speed_mph"],
            precipitation=game_weather["weather"]["precipitation_type"],
            indoor=False,
            total_adjustment=game_weather["billy_walters_adjustments"]["total_adjustment"],
            spread_adjustment=game_weather["billy_walters_adjustments"]["spread_adjustment"]
        )
    else:
        weather = None  # Dome stadium
    
    # Detect edge
    edge = detector.detect_edge(
        game_id=game_id,
        away_team=away_team,
        home_team=home_team,
        market_spread=market_spread,
        market_total=market_total,
        week=week,  # Current week from get_nfl_week()
        game_time=game_schedule["time"],
        situational=situational,
        weather=weather,
        sharp_action=None,  # Subagent 7 (future)
        best_odds=int(row["spread_odds_home"])
    )
    
    if edge:
        print(f"✅ Edge detected: {edge.matchup}")
        print(f"   Edge: {edge.edge_points:.1f} points")
        print(f"   Recommended: {edge.recommended_bet}")
        print(f"   Kelly: {edge.kelly_fraction:.2%}")
```

### Step 4: Generate Betting Card

The edge detector automatically generates:
- `output/edge_detection/nfl_edges_detected_week_{week}.jsonl` (spread edges)
- `output/edge_detection/nfl_totals_detected_week_{week}.jsonl` (total edges)
- `output/edge_detection/edge_report_week_{week}.txt` (formatted report)

### Step 5: Apply Kelly Criterion Bankroll Management

```python
# Fractional Kelly with safety factor
bankroll = 10000  # $10,000 bankroll
kelly_fraction = 0.25  # Conservative 25% Kelly

for edge in detected_edges:
    # Calculate Kelly stake
    win_prob = edge.confidence / 100.0
    odds_decimal = edge.spread_decimal
    kelly_pct = (win_prob * odds_decimal - 1) / (odds_decimal - 1)
    
    # Apply fractional Kelly and cap
    stake_pct = kelly_pct * kelly_fraction
    stake_pct = min(stake_pct, 0.03)  # Max 3% per bet
    
    stake_amount = bankroll * stake_pct
    print(f"{edge.matchup}: ${stake_amount:.2f} ({stake_pct:.2%})")
```

---

## Quality Checklist

Before declaring data collection complete, verify:

### Schedule & Game Info
- [ ] All 16 games present (unless bye weeks)
- [ ] All stadiums have `is_dome` flag
- [ ] All travel distances calculated
- [ ] All rest days calculated

### Betting Lines
- [ ] All games have spread, total, moneyline
- [ ] Book margins reasonable (4-5%)
- [ ] Timestamps accurate
- [ ] CSV format valid

### Weather Data
- [ ] All outdoor stadiums have weather
- [ ] All dome stadiums have `weather: null`
- [ ] All Billy Walters adjustments calculated
- [ ] Weather flags set correctly

### Team Situational
- [ ] All power ratings updated (90/10 formula)
- [ ] All S-factors within ±2.0 cap
- [ ] All metrics current (through Week 10)

### Player Situational
- [ ] All key units identified
- [ ] All point values from Billy Walters tables
- [ ] Cumulative impact ≤ 3.0 points per team

### Injury Reports
- [ ] All teams have injury data (even if empty)
- [ ] All point values from Billy Walters tables
- [ ] Cumulative impact ≤ 3.0 points per team
- [ ] Status categories correct (out/doubtful/questionable/probable)

---

## Troubleshooting

### Missing Data
- **Problem**: Game missing from schedule
- **Solution**: Check NFL.com directly, verify week number correct

### Weather API Limits
- **Problem**: AccuWeather 12-hour limit exceeded
- **Solution**: Use OpenWeather API for games >12 hours away

### Power Rating Calculation Errors
- **Problem**: Ratings don't match 90/10 formula
- **Solution**: Verify previous week's ratings loaded correctly, check game results input

### Injury Point Value Discrepancies
- **Problem**: Point values don't match Billy Walters tables
- **Solution**: Check `src/walters_analyzer/valuation/injury_impacts.py` for correct values

### Integration Failures
- **Problem**: Edge detector can't load data
- **Solution**: Verify JSON format valid, check file paths, ensure game_id matches across all files

---

## Next Steps After Data Collection

1. **Run Edge Detection**: Execute Billy Walters edge detector with all collected data
2. **Generate Betting Card**: Rank edges by strength, apply Kelly Criterion
3. **Track CLV**: Monitor closing line value for each bet
4. **Update Power Ratings**: After games complete, update ratings for Week 12

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-13  
**Status**: Ready for execution
