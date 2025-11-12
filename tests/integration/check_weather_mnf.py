"""Check weather for Monday Night Football - PHI @ GB"""

import asyncio
from datetime import datetime
from data.weather_client import WeatherClient
import os


async def main():
    # Initialize client
    accuweather_key = os.getenv("ACCUWEATHER_API_KEY")
    openweather_key = os.getenv("OPENWEATHER_API_KEY")

    client = WeatherClient(
        accuweather_api_key=accuweather_key,
        openweather_api_key=openweather_key,
        prefer_accuweather=True,
    )

    city = "Green Bay"
    state = "WI"
    game_time = datetime(2025, 11, 11, 20, 15)

    try:
        await client.connect()
        weather = await client.get_game_forecast(city, state, game_time)

        print("=" * 70)
        print("MONDAY NIGHT FOOTBALL - WEATHER REPORT")
        print("=" * 70)
        print(f"Game: Philadelphia Eagles @ Green Bay Packers")
        print(f"Location: Lambeau Field, {city}, {state}")
        print(f"Game Time: Monday, November 11, 2025 at 8:15 PM ET")
        print(f"Stadium: OUTDOOR")
        print()
        print("FORECAST:")
        print("-" * 70)
        print(f"Temperature: {weather.get('temperature', 'N/A')}°F")
        print(f"Feels Like: {weather.get('feels_like', 'N/A')}°F")
        print(f"Wind Speed: {weather.get('wind_speed', 'N/A')} mph")
        print(f"Wind Gust: {weather.get('wind_gust', 'N/A')} mph")
        print(f"Precipitation: {weather.get('precipitation_type', 'None')}")
        print(
            f"Precipitation Probability: {weather.get('precipitation_probability', 0)}%"
        )
        print(f"Humidity: {weather.get('humidity', 'N/A')}%")
        print(f"Conditions: {weather.get('description', 'N/A')}")
        print(f"Data Source: {weather.get('source', 'N/A')}")
        print()

        # Calculate Billy Walters impact
        temp = weather.get("temperature") or 50  # Default to moderate temp if None
        wind = weather.get("wind_speed") or 0
        precip_prob = weather.get("precipitation_probability") or 0
        precip_type = (weather.get("precipitation_type") or "").lower()

        total_adjustment = 0
        factors = []

        if wind > 20:
            total_adjustment -= 5
            factors.append(f"STRONG WIND ({wind} mph): -5 pts")
        elif wind > 15:
            total_adjustment -= 3
            factors.append(f"Moderate wind ({wind} mph): -3 pts")
        elif wind > 10:
            total_adjustment -= 1
            factors.append(f"Breezy ({wind} mph): -1 pt")

        if temp < 20:
            total_adjustment -= 4
            factors.append(f"EXTREME COLD ({temp}°F): -4 pts")
        elif temp < 25:
            total_adjustment -= 3
            factors.append(f"Very cold ({temp}°F): -3 pts")
        elif temp < 32:
            total_adjustment -= 2
            factors.append(f"Cold/freezing ({temp}°F): -2 pts")
        elif temp < 40:
            total_adjustment -= 1
            factors.append(f"Cold ({temp}°F): -1 pt")

        if "snow" in precip_type and precip_prob > 60:
            total_adjustment -= 5
            factors.append(f"Snow very likely ({precip_prob}%): -5 pts")
        elif "snow" in precip_type and precip_prob > 30:
            total_adjustment -= 3
            factors.append(f"Snow possible ({precip_prob}%): -3 pts")
        elif "rain" in precip_type and precip_prob > 60:
            total_adjustment -= 3
            factors.append(f"Rain very likely ({precip_prob}%): -3 pts")
        elif "rain" in precip_type and precip_prob > 30:
            total_adjustment -= 1
            factors.append(f"Rain possible ({precip_prob}%): -1 pt")

        print("BILLY WALTERS WEATHER IMPACT:")
        print("=" * 70)

        if total_adjustment == 0:
            print("WEATHER IMPACT: NEUTRAL")
            print("No significant weather impact expected")
            print()
            print("BETTING RECOMMENDATION:")
            print("Weather is NOT a factor - proceed with OVER 45.5")
        else:
            print(f"TOTAL ADJUSTMENT: {total_adjustment} points")
            for factor in factors:
                print(f"  - {factor}")
            print()

            original_total = 45.5
            model_prediction = 50.7
            adjusted_prediction = model_prediction + total_adjustment
            market_edge = adjusted_prediction - original_total

            print(f"Market Total: {original_total}")
            print(f"Model Prediction (no weather): {model_prediction} pts")
            print(f"Weather-Adjusted Prediction: {adjusted_prediction} pts")
            print(f"Adjusted Edge: {market_edge:.1f} pts")
            print()

            if total_adjustment <= -5:
                print("STRONG UNDER LEAN - Pass on OVER or bet UNDER")
            elif total_adjustment <= -3:
                print("MODERATE UNDER LEAN - Reduce OVER bet or pass")
            else:
                print("SLIGHT UNDER LEAN - Proceed cautiously with OVER")

    except Exception as e:
        print(f"ERROR: {e}")
        print()
        print("Check weather manually at weather.com or nfl.com")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
