"""Test which AccuWeather endpoints are available on starter plan"""

import asyncio
import os
from data.accuweather_client import AccuWeatherClient


async def check_endpoints():
    print("=" * 70)
    print("TESTING ACCUWEATHER ENDPOINT AVAILABILITY")
    print("=" * 70)

    api_key = os.getenv("ACCUWEATHER_API_KEY")
    client = AccuWeatherClient(api_key=api_key)
    await client.connect()

    location_key = "1868"  # Green Bay

    # Test 1: Current conditions
    print("\nTEST 1: Current Conditions (usually free)")
    print("-" * 70)
    try:
        conditions = await client.get_current_conditions(location_key)
        print(f"[OK] Current conditions: {conditions.get('temperature', 'N/A')}°F")
        print(f"     Description: {conditions.get('description', 'N/A')}")
    except Exception as e:
        print(f"[FAIL] {e}")

    # Test 2: 12-hour forecast
    print("\nTEST 2: 12-Hour Forecast")
    print("-" * 70)
    try:
        forecast = await client.get_hourly_forecast(location_key, hours=12)
        print(f"[OK] Got {len(forecast)} hours of forecast")
    except Exception as e:
        print(f"[FAIL] {e}")

    # Test 3: Try to manually hit 5-day forecast endpoint
    print("\nTEST 3: 5-Day Daily Forecast (usually available on free tier)")
    print("-" * 70)
    try:
        data = await client._make_request(
            f"/forecasts/v1/daily/5day/{location_key}", params={"details": "true"}
        )
        if data and "DailyForecasts" in data:
            forecasts = data["DailyForecasts"]
            print(f"[OK] Got {len(forecasts)} days of forecast")
            if forecasts:
                first = forecasts[0]
                print(f"     Date: {first.get('Date', 'N/A')}")
                temp_max = (
                    first.get("Temperature", {}).get("Maximum", {}).get("Value", "N/A")
                )
                temp_min = (
                    first.get("Temperature", {}).get("Minimum", {}).get("Value", "N/A")
                )
                print(f"     High: {temp_max}°F, Low: {temp_min}°F")
        else:
            print("[FAIL] Unexpected response format")
    except Exception as e:
        print(f"[FAIL] {e}")

    # Test 4: Try 1-hour forecast
    print("\nTEST 4: 1-Hour Forecast (most basic)")
    print("-" * 70)
    try:
        forecast = await client.get_hourly_forecast(location_key, hours=1)
        print(f"[OK] Got {len(forecast)} hours of forecast")
    except Exception as e:
        print(f"[FAIL] {e}")

    print()
    print("=" * 70)
    print("ENDPOINT AVAILABILITY SUMMARY")
    print("=" * 70)
    print("Your AccuWeather plan: core-weather/starter")
    print()
    print("Recommendations:")
    print("1. If 5-day forecast works: Modify client to use daily forecast")
    print("2. If 12-hour works: Use shorter forecast window")
    print("3. If current conditions only: Use as spot check, rely on OpenWeather")
    print("4. Consider upgrading to prime/elite plan for full hourly access")
    print("=" * 70)

    await client.close()


if __name__ == "__main__":
    asyncio.run(check_endpoints())
