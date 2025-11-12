"""Test new AccuWeather API key capabilities"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Force reload .env
load_dotenv(".env", override=True)


async def check_new_key():
    from data.accuweather_client import AccuWeatherClient

    print("=" * 70)
    print("TESTING NEW ACCUWEATHER API KEY")
    print("=" * 70)

    api_key = os.getenv("ACCUWEATHER_API_KEY")
    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")
    print()

    client = AccuWeatherClient(api_key=api_key)
    await client.connect()

    location_key = "1868"  # Green Bay

    # Test 1: Current Conditions
    print("TEST 1: Current Conditions")
    print("-" * 70)
    try:
        conditions = await client.get_current_conditions(location_key)
        print(f"[OK] Current temp: {conditions.get('temperature', 'N/A')}°F")
        print(f"     Conditions: {conditions.get('description', 'N/A')}")
    except Exception as e:
        print(f"[FAIL] {e}")

    print()

    # Test 2: 12-hour forecast
    print("TEST 2: 12-Hour Forecast")
    print("-" * 70)
    try:
        forecast = await client.get_hourly_forecast(location_key, hours=12)
        print(f"[OK] Got {len(forecast)} hours of forecast")
        if forecast:
            first = forecast[0]
            print(
                f"     Next hour: {first.get('temperature', 'N/A')}°F, {first.get('description', 'N/A')}"
            )
    except Exception as e:
        print(f"[FAIL] {e}")

    print()

    # Test 3: 24-hour forecast (requires better plan)
    print("TEST 3: 24-Hour Forecast (requires upgraded plan)")
    print("-" * 70)
    try:
        forecast = await client.get_hourly_forecast(location_key, hours=24)
        print(f"[OK] Got {len(forecast)} hours of forecast")
        print("[SUCCESS] You have access to 24-hour forecasts!")
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "Forbidden" in error_str:
            print("[INFO] 24-hour forecast not available (starter plan)")
        else:
            print(f"[FAIL] {e}")

    print()

    # Test 4: 72-hour forecast (prime/elite plan)
    print("TEST 4: 72-Hour Forecast (requires prime/elite plan)")
    print("-" * 70)
    try:
        forecast = await client.get_hourly_forecast(location_key, hours=72)
        print(f"[OK] Got {len(forecast)} hours of forecast")
        print("[SUCCESS] You have access to 72-hour forecasts! (Prime/Elite plan)")
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "Forbidden" in error_str:
            print("[INFO] 72-hour forecast not available")
        else:
            print(f"[FAIL] {e}")

    print()

    # Test 5: MNF Game Forecast
    print("TEST 5: Monday Night Football Game Forecast")
    print("-" * 70)
    game_time = datetime(2025, 11, 11, 20, 15)
    try:
        forecast = await client.get_game_forecast("Green Bay", "WI", game_time)
        print("[OK] Got game forecast")
        print()
        print("MNF Weather Conditions:")
        print(f"  Temperature: {forecast.get('temperature', 'N/A')}°F")
        print(f"  Feels Like: {forecast.get('feels_like', 'N/A')}°F")
        print(f"  Wind Speed: {forecast.get('wind_speed', 'N/A')} mph")
        print(f"  Wind Gust: {forecast.get('wind_gust', 'N/A')} mph")
        print(f"  Precipitation: {forecast.get('precipitation_type', 'None')}")
        print(f"  Precip Probability: {forecast.get('precipitation_probability', 0)}%")
        print(f"  Humidity: {forecast.get('humidity', 'N/A')}%")
        print(f"  Conditions: {forecast.get('description', 'N/A')}")
    except Exception as e:
        print(f"[FAIL] {e}")

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    await client.close()


if __name__ == "__main__":
    asyncio.run(check_new_key())
