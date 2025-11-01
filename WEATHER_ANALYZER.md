# Weather Analyzer - Billy Walters Methodology

## Overview

The Weather Analyzer fetches real-time weather data from AccuWeather API for game locations, providing critical environmental factors for betting decisions following Billy Walters' proven methodology.

**Why Weather Matters:**
- Wind >15mph drastically reduces passing efficiency and field goal accuracy
- Precipitation affects ball handling, reduces scoring by 3-7 points on average
- Temperature extremes (below 32°F or above 90°F) impact player performance
- Indoor games eliminate weather as a variable

---

## Quick Start

### Step 1: Get AccuWeather API Key

1. Sign up at [AccuWeather Developer Portal](https://developer.accuweather.com/)
2. Create a free app to get your API key
3. Add to your `.env` file:

```bash
ACCUWEATHER_API_KEY=your_api_key_here
```

### Step 2: Fetch Weather for a Card

```powershell
# Fetch weather for all games in a betting card
uv run walters-analyzer scrape-weather --card ./cards/wk-card-2025-10-31.json
```

### Step 3: Review Output

Weather data is saved to `data/weather/` in two formats:
- **JSONL**: `weather-{timestamp}.jsonl`
- **Parquet**: `weather-{timestamp}.parquet`

---

## Usage Examples

### Fetch Weather for Entire Card

```powershell
# College Football
uv run walters-analyzer scrape-weather --card ./cards/wk-card-2025-10-31.json

# NFL
uv run walters-analyzer scrape-weather --card ./cards/nfl-wk-9.json --sport nfl
```

### Fetch Weather for Single Stadium

```powershell
# Single game weather check
uv run walters-analyzer scrape-weather \
    --stadium "Lambeau Field" \
    --location "Green Bay, WI" \
    --sport nfl

# Outdoor stadium
uv run walters-analyzer scrape-weather \
    --stadium "Soldier Field" \
    --location "Chicago, IL"

# Indoor stadium (weather irrelevant)
uv run walters-analyzer scrape-weather \
    --stadium "Mercedes-Benz Dome" \
    --location "Atlanta, GA" \
    --dome
```

---

## Billy Walters Weather Factors

### Critical Thresholds

| Factor | Impact Level | Betting Adjustment |
|--------|--------------|-------------------|
| **Wind Speed** | | |
| > 25 mph | Extreme (40 pts) | Heavy favor Under, fade all passing |
| 20-25 mph | High (30 pts) | Favor Under, reduce passing props |
| 15-20 mph | Moderate (20 pts) | Monitor totals, reduce FG confidence |
| 10-15 mph | Low (10 pts) | Minor adjustment |
| **Precipitation** | | |
| Snow (>50% chance) | High (35 pts) | Heavy favor Under, favor rush teams |
| Rain (>50% chance) | Moderate (25 pts) | Favor Under, monitor turnovers |
| **Temperature** | | |
| Below 20°F | High (20 pts) | Ball handling issues, low scoring |
| 20-32°F (Freezing) | Moderate (15 pts) | Monitor fumbles, passing accuracy |
| Above 95°F | Moderate (15 pts) | Fatigue factor, tempo concerns |

### Impact Score System

The analyzer automatically calculates a **Weather Impact Score (0-100)**:

- **0-20**: Minimal impact - proceed with normal analysis
- **21-50**: Moderate impact - monitor game, adjust totals by 1-3 points
- **51-75**: High impact - significant adjustment needed, consider totals moves
- **76-100**: Extreme impact - strong consideration to skip bet or heavily favor Under

---

## Output Format

### Weather Data Structure

```json
{
  "source": "accuweather",
  "sport": "college_football",
  "collected_at": "2025-11-01T18:30:00+00:00",
  "game_date": "2025-11-02",
  "game_time": "7:30 PM",
  "stadium": "Soldier Field",
  "location": "Chicago, IL",
  "is_dome": false,
  
  "temperature_f": 38.0,
  "feels_like_f": 31.0,
  "wind_speed_mph": 18.5,
  "wind_gust_mph": 25.0,
  "wind_direction": "NW",
  "precipitation_prob": 65,
  "precipitation_type": "Rain",
  "humidity": 78,
  
  "weather_description": "Rainy and Windy",
  "cloud_cover": 90,
  "visibility_miles": 5.0,
  
  "weather_impact_score": 55,
  "betting_adjustment": "Favor Under | Fade Passing Yards | Favor Running Teams",
  
  "location_key": "348308",
  "forecast_url": "https://www.accuweather.com/en/us/chicago/60601/hourly-weather-forecast/348308"
}
```

---

## Integration with Gates

### Pre-Run Gate Check

The weather analyzer integrates with the `weather_confirmed` gate in your betting cards:

```python
# walters_analyzer/wkcard.py validates this automatically
{
  "entry_gates_checklist": {
    "injuries_confirmed": true,
    "weather_confirmed": true,  // ← Set after weather analysis
    "steam_ok": true
  }
}
```

### Example Workflow

```powershell
# 1. Scrape odds
uv run walters-analyzer scrape-overtime --sport cfb

# 2. Scrape injuries
uv run walters-analyzer scrape-injuries --sport cfb

# 3. Fetch weather (NEW!)
uv run walters-analyzer scrape-weather --card ./cards/wk-card-2025-11-02.json

# 4. Run card with gate validation
uv run walters-analyzer wk-card --file ./cards/wk-card-2025-11-02.json --dry-run
```

---

## Billy Walters Case Studies

### Case Study 1: The "Wind Game" (Chicago, 2018)

**Conditions:**
- Wind: 28 mph gusts
- Temperature: 34°F
- Game: Bears vs Rams

**Analysis:**
- Weather Impact Score: 85 (Extreme)
- Total opened at 48.5, dropped to 42

**Walters Approach:**
- Heavy Under play at 47.5 (early)
- Result: 15-6 final (21 points, Under hit by 26.5)

**Lesson**: Extreme wind games are **automatic Under** plays in Walters' system. The public is slow to adjust totals for wind.

### Case Study 2: Snow Bowl (Buffalo, 2014)

**Conditions:**
- Snow: Heavy, 80% probability
- Wind: 15 mph
- Visibility: 2 miles

**Analysis:**
- Weather Impact Score: 70 (High)
- Total opened at 44

**Walters Approach:**
- Under play, favor run-heavy team (Seahawks)
- Result: 31-25 final (56 points - unusual)

**Lesson**: Snow games are typically low-scoring, but modern offenses can still produce. Look for **run-first teams** as they have the advantage.

### Case Study 3: Dome Game (New Orleans)

**Conditions:**
- Dome: Yes (climate controlled)

**Analysis:**
- Weather Impact Score: 0
- Weather is irrelevant

**Lesson**: Indoor games remove weather as a variable. Focus entirely on matchup, injuries, and line value.

---

## Advanced Usage

### Batch Processing with Python

```python
import pandas as pd
from walters_analyzer.weather_fetcher import fetch_game_weather

# Read betting card
games = [
    {"stadium": "Lambeau Field", "location": "Green Bay, WI", "dome": False},
    {"stadium": "US Bank Stadium", "location": "Minneapolis, MN", "dome": True},
]

weather_data = []
for game in games:
    data = fetch_game_weather(
        stadium=game["stadium"],
        location=game["location"],
        is_dome=game["dome"],
        sport="nfl"
    )
    if data:
        weather_data.append(data)

# Analyze
df = pd.DataFrame(weather_data)
high_impact = df[df['weather_impact_score'] > 50]
print(f"High-impact weather games: {len(high_impact)}")
```

### Custom Thresholds

You can customize impact thresholds by modifying the `WeatherReportItem.calculate_impact_score()` method in `scrapers/overtime_live/items.py`.

---

## Caching & Performance

### Stadium Location Cache

The analyzer caches AccuWeather location keys for stadiums to minimize API calls:

**Cache Location**: `data/stadium_cache.json`

**Example Cache Entry**:
```json
{
  "Lambeau Field": {
    "location_key": "337016",
    "location_name": "Green Bay",
    "state": "WI",
    "cached_at": "2025-11-01T12:00:00+00:00"
  }
}
```

**Benefits**:
- Reduces API usage (important for free tier limits)
- Faster subsequent weather fetches
- Persistent across sessions

### API Rate Limits

AccuWeather free tier:
- 50 calls/day
- Use caching to stay within limits
- Consider upgrading for production use

---

## Troubleshooting

### "ACCUWEATHER_API_KEY not found"

**Solution**: Add your API key to `.env`:
```bash
ACCUWEATHER_API_KEY=your_key_here
```

### "Could not find location"

**Issue**: Stadium name or city not recognized

**Solution**: Try different search terms:
```powershell
# Instead of full stadium name
--location "Green Bay"  # City only

# Or with state
--location "Green Bay, Wisconsin"  # Full state name
```

### "No forecast data available"

**Issue**: API returned empty response

**Possible causes**:
1. Invalid API key
2. Rate limit exceeded (50/day for free tier)
3. Location key is incorrect

**Solution**: Check API status and usage at [AccuWeather Dashboard](https://developer.accuweather.com/user/me/apps)

---

## Python API Reference

### `fetch_game_weather()`

Fetch weather data for a specific game.

**Parameters:**
- `stadium` (str): Stadium name
- `location` (str): City/state for search
- `is_dome` (bool): Indoor stadium flag
- `game_date` (Optional[str]): Game date (ISO format)
- `game_time` (Optional[str]): Game time
- `sport` (str): "college_football" or "nfl"
- `use_cache` (bool): Use cached location keys

**Returns**: `Dict[str, Any]` or `None`

### `AccuWeatherClient`

Low-level API client for direct AccuWeather integration.

**Methods:**
- `search_location(query: str)`: Search for location
- `get_hourly_forecast(location_key: str, hours: int)`: Hourly forecast
- `get_daily_forecast(location_key: str, days: int)`: Daily forecast
- `get_current_conditions(location_key: str)`: Current weather

---

## Best Practices

### 1. Check Weather Early

Run weather analysis **24-48 hours before games**:
- Forecasts stabilize closer to game time
- Early detection of high-impact conditions
- Time to adjust betting strategy

### 2. Monitor Weather Updates

Weather can change rapidly:
- Re-run analysis on game day
- Check for forecast updates
- Be prepared to adjust or cancel bets

### 3. Dome Games First

Filter out dome games immediately:
- Weather is irrelevant indoors
- Focus analysis time on outdoor games
- Use the `is_dome` flag in your cards

### 4. Combine with Other Gates

Weather is ONE factor in Billy Walters' system:
- **Injuries**: Check for key player absences
- **Weather**: Analyze environmental impact
- **Steam**: Monitor line movement
- **Matchup**: Evaluate team styles

All gates must pass before placing a bet.

### 5. Historical Context

Review past weather games:
- How does this team perform in wind/rain/cold?
- Home team advantage in adverse conditions
- Road team from warm climate playing in cold weather

---

## Summary

The Weather Analyzer provides **critical environmental intelligence** for betting decisions using Billy Walters' proven methodology:

✅ Real-time weather data from AccuWeather API  
✅ Automatic impact scoring (0-100 scale)  
✅ Betting adjustment recommendations  
✅ Integration with gate validation system  
✅ Caching for efficiency  
✅ JSONL + Parquet output formats  

**Key Takeaway**: Weather is often the **most undervalued** factor by the public. Professional bettors like Billy Walters exploit this edge by systematically analyzing weather conditions and adjusting totals/spreads accordingly.

---

## Need Help?

- **AccuWeather API Docs**: https://developer.accuweather.com/
- **Billy Walters Book**: "Gambler: Secrets from a Life at Risk"
- **Issues**: Review `data/weather/` output and check API logs

**Happy analyzing! 🌦️**

