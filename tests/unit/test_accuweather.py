"""Test AccuWeather API connectivity and key validity"""

import asyncio
import os
from data.accuweather_client import AccuWeatherClient


async def test_accuweather():
    print("=" * 70)
    print("TESTING ACCUWEATHER API")
    print("=" * 70)

    # Check API key
    api_key = os.getenv("ACCUWEATHER_API_KEY")
    if not api_key:
        print("ERROR: ACCUWEATHER_API_KEY not set in environment")
        return

    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")
    print()

    try:
        # Initialize client
        client = AccuWeatherClient(api_key=api_key)
        await client.connect()
        print("[OK] AccuWeather client initialized")
        print()

        # Test 1: Get location key for Green Bay
        print("TEST 1: Getting location key for Green Bay, WI")
        print("-" * 70)
        try:
            location_key = await client.get_location_key("Green Bay", "WI")
            print(f"[OK] Location Key: {location_key}")
        except Exception as e:
            print(f"[ERROR] Failed to get location key: {e}")
            await client.close()
            return

        print()

        # Test 2: Get game forecast for Monday Night Football
        print("TEST 2: Getting game forecast for MNF (Nov 11, 8:15 PM ET)")
        print("-" * 70)
        from datetime import datetime

        game_time = datetime(2025, 11, 11, 20, 15)  # 8:15 PM ET

        try:
            forecast = await client.get_game_forecast("Green Bay", "WI", game_time)

            if forecast:
                print("[OK] Got game forecast")
                print()
                print("Game Weather Conditions:")
                print(f"  Temperature: {forecast.get('temperature', 'N/A')}°F")
                print(f"  Feels Like: {forecast.get('feels_like', 'N/A')}°F")
                print(f"  Wind Speed: {forecast.get('wind_speed', 'N/A')} mph")
                print(f"  Wind Gust: {forecast.get('wind_gust', 'N/A')} mph")
                print(
                    f"  Precipitation Type: {forecast.get('precipitation_type', 'None')}"
                )
                print(
                    f"  Precipitation Prob: {forecast.get('precipitation_probability', 'N/A')}%"
                )
                print(f"  Humidity: {forecast.get('humidity', 'N/A')}%")
                print(f"  Description: {forecast.get('description', 'N/A')}")
                print(f"  Source: {forecast.get('source', 'N/A')}")
            else:
                print("[WARNING] No forecast data returned")
        except Exception as e:
            print(f"[ERROR] Failed to get forecast: {e}")
            import traceback

            traceback.print_exc()

        print()
        print("=" * 70)
        print("ACCUWEATHER API TEST COMPLETE")
        print("=" * 70)

        await client.close()
        print("[OK] Client closed successfully")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_accuweather())
