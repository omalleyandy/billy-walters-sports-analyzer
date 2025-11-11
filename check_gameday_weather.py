"""
Gameday Weather Checker - Run on game day morning for accurate forecast

Usage:
    python check_gameday_weather.py "Green Bay Packers" "2025-11-11 20:15"

Or just run without arguments to check for today's games.
"""
import asyncio
import sys
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv('.env', override=True)

async def check_gameday_weather(team_name: str, game_time_str: str):
    from data.accuweather_client import AccuWeatherClient

    # Parse game time
    game_time = datetime.strptime(game_time_str, "%Y-%m-%d %H:%M")
    now = datetime.now()
    hours_ahead = int((game_time - now).total_seconds() / 3600)

    print("=" * 70)
    print(f"GAMEDAY WEATHER CHECK: {team_name}")
    print("=" * 70)
    print(f"Current Time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"Game Time: {game_time.strftime('%A, %B %d, %Y at %I:%M %p ET')}")
    print(f"Hours Until Game: {hours_ahead}")
    print()

    if hours_ahead < 0:
        print("[INFO] Game has already started!")
        return
    elif hours_ahead > 12:
        print("[WARNING] Game is still >12 hours away")
        print("For best accuracy, run this script again within 12 hours of game time")
        print()
    else:
        print("[OK] Within 12-hour forecast window - accurate hourly data available!")
        print()

    # Map team names to cities
    team_cities = {
        "Green Bay Packers": ("Green Bay", "WI"),
        "Green Bay": ("Green Bay", "WI"),
        "Philadelphia Eagles": ("Philadelphia", "PA"),
        "Philadelphia": ("Philadelphia", "PA"),
        # Add more as needed
    }

    city, state = team_cities.get(team_name, (team_name, ""))
    if not state:
        print(f"[ERROR] Unknown team: {team_name}")
        print(f"Please add to team_cities mapping")
        return

    api_key = os.getenv('ACCUWEATHER_API_KEY')
    client = AccuWeatherClient(api_key=api_key)
    await client.connect()

    try:
        forecast = await client.get_game_forecast(city, state, game_time)

        temp = forecast.get('temperature')
        feels_like = forecast.get('feels_like')
        wind = forecast.get('wind_speed')
        wind_gust = forecast.get('wind_gust')
        precip_type = forecast.get('precipitation_type')
        precip_prob = forecast.get('precipitation_probability', 0)
        humidity = forecast.get('humidity')
        description = forecast.get('description')

        print("GAME-TIME FORECAST:")
        print("-" * 70)
        print(f"Temperature: {temp}°F")
        print(f"Feels Like: {feels_like}°F")
        print(f"Wind Speed: {wind} mph")
        print(f"Wind Gust: {wind_gust} mph")
        print(f"Precipitation: {precip_type or 'None'}")
        print(f"Precipitation Probability: {precip_prob}%")
        print(f"Humidity: {humidity}%")
        print(f"Conditions: {description}")
        print()

        # Billy Walters Impact
        total_adj = 0
        factors = []

        if wind and wind > 20:
            total_adj -= 5
            factors.append(f"STRONG WIND ({wind} mph): -5 pts")
        elif wind and wind > 15:
            total_adj -= 3
            factors.append(f"Moderate wind ({wind} mph): -3 pts")
        elif wind and wind > 10:
            total_adj -= 1
            factors.append(f"Breezy ({wind} mph): -1 pt")

        if temp and temp < 20:
            total_adj -= 4
            factors.append(f"EXTREME COLD ({temp}°F): -4 pts")
        elif temp and temp < 25:
            total_adj -= 3
            factors.append(f"Very cold ({temp}°F): -3 pts")
        elif temp and temp < 32:
            total_adj -= 2
            factors.append(f"Freezing ({temp}°F): -2 pts")
        elif temp and temp < 40:
            total_adj -= 1
            factors.append(f"Cold ({temp}°F): -1 pt")

        if precip_prob > 60 and precip_type and 'snow' in str(precip_type).lower():
            total_adj -= 5
            factors.append(f"Snow very likely ({precip_prob}%): -5 pts")
        elif precip_prob > 30 and precip_type and 'snow' in str(precip_type).lower():
            total_adj -= 3
            factors.append(f"Snow possible ({precip_prob}%): -3 pts")
        elif precip_prob > 60 and precip_type and 'rain' in str(precip_type).lower():
            total_adj -= 3
            factors.append(f"Rain very likely ({precip_prob}%): -3 pts")

        print("BILLY WALTERS WEATHER IMPACT:")
        print("=" * 70)

        if total_adj == 0:
            print("WEATHER IMPACT: NEUTRAL")
            print("No significant weather impact on scoring")
            print()
            print("RECOMMENDATION: Weather is not a factor in betting decision")
        else:
            print(f"TOTAL ADJUSTMENT: {total_adj} points")
            for factor in factors:
                print(f"  - {factor}")
            print()

            if total_adj <= -5:
                print("STRONG UNDER LEAN - Weather significantly reduces scoring")
            elif total_adj <= -3:
                print("MODERATE UNDER LEAN - Weather moderately reduces scoring")
            elif total_adj <= -1:
                print("SLIGHT UNDER LEAN - Weather slightly reduces scoring")

        print("=" * 70)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

    await client.close()

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        team = sys.argv[1]
        game_time = sys.argv[2]
    else:
        # Default to Green Bay Packers Tuesday night game
        team = "Green Bay Packers"
        game_time = "2025-11-11 20:15"
        print(f"Using default: {team} at {game_time}")
        print()

    asyncio.run(check_gameday_weather(team, game_time))
