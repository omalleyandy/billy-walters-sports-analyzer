Check weather conditions for NFL/NCAAF games and calculate Billy Walters weather impact.

Usage: /weather [team_name] [game_time]

Examples:
- /weather "Green Bay" "2025-11-17 13:00"
- /weather "Kansas City"
- /weather

This command will:
1. Fetch weather forecast using unified weather client (AccuWeather + OpenWeather fallback)
2. Determine if stadium is indoor or outdoor
3. Calculate Billy Walters weather impact on total and spread
4. Provide detailed betting recommendations

Billy Walters Weather Impact Principles:
- Wind >15 MPH: Reduce total by 3-5 points, favor defense
- Temperature <32°F: Reduce total by 2-3 points, favor rushing teams
- Rain/Snow: Reduce total by 2-4 points, favor ground game
- Indoor stadiums: No weather adjustments

Weather factors analyzed:
- Temperature (actual and feels-like)
- Wind speed and direction
- Precipitation type and probability
- Humidity levels
- Indoor vs outdoor venue

Output includes:
- Current/forecast weather conditions
- Total adjustment (points)
- Spread adjustment (points)
- Betting recommendation with confidence level
- Source (AccuWeather or OpenWeather)

Technical Implementation (FIXED 2025-11-12):
- Uses AccuWeather API with your ACCUWEATHER_API_KEY from .env
- Properly handles async API calls with asyncio
- Maps home team → stadium city → location key → forecast
- Only calls API for outdoor stadiums (saves API quota)
- Indoor stadiums (Atlanta, Detroit, Minnesota, etc.) return None
- API Usage: ~2 calls per weather check (location + forecast)
- Respects starter plan limits (50 calls/day)

Example Output:
```
Weather for Buffalo: 38°F, 10.5 MPH wind
Total adjustment: 0.0 points
Spread adjustment: 0.0 points
Recommendation: No significant weather impact

Weather for Cleveland: 40°F, 19.6 MPH wind
Total adjustment: -0.2 points (wind factor)
Spread adjustment: -0.1 points
Recommendation: Slight favor to defense, reduce total by 0.2
```