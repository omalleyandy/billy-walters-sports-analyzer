#!/usr/bin/env python3
"""
AccuWeather API Client
Fetches weather forecasts for NFL/NCAAF game locations

Billy Walters Weather Impact Principles:
- Wind >15 MPH: Reduce total by 3-5 points, favor defense
- Temp <32°F: Reduce total by 2-3 points, favor rushing
- Rain/Snow: Reduce total by 2-4 points
- Indoor: No adjustments
"""

import os
import requests
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class AccuWeatherClient:
    """Client for AccuWeather API"""

    # NFL Stadium locations (city for location key lookup)
    NFL_STADIUM_LOCATIONS = {
        "Arizona": {"city": "Glendale", "state": "AZ", "indoor": True},
        "Atlanta": {"city": "Atlanta", "state": "GA", "indoor": True},
        "Baltimore": {"city": "Baltimore", "state": "MD", "indoor": False},
        "Buffalo": {"city": "Buffalo", "state": "NY", "indoor": False},
        "Carolina": {"city": "Charlotte", "state": "NC", "indoor": False},
        "Chicago": {"city": "Chicago", "state": "IL", "indoor": False},
        "Cincinnati": {"city": "Cincinnati", "state": "OH", "indoor": False},
        "Cleveland": {"city": "Cleveland", "state": "OH", "indoor": False},
        "Dallas": {"city": "Arlington", "state": "TX", "indoor": True},
        "Denver": {"city": "Denver", "state": "CO", "indoor": False},
        "Detroit": {"city": "Detroit", "state": "MI", "indoor": True},
        "Green Bay": {"city": "Green Bay", "state": "WI", "indoor": False},
        "Houston": {"city": "Houston", "state": "TX", "indoor": True},
        "Indianapolis": {"city": "Indianapolis", "state": "IN", "indoor": True},
        "Jacksonville": {"city": "Jacksonville", "state": "FL", "indoor": False},
        "Kansas City": {"city": "Kansas City", "state": "MO", "indoor": False},
        "Las Vegas": {"city": "Las Vegas", "state": "NV", "indoor": True},
        "LA Chargers": {"city": "Inglewood", "state": "CA", "indoor": False},
        "LA Rams": {"city": "Inglewood", "state": "CA", "indoor": False},
        "Miami": {"city": "Miami Gardens", "state": "FL", "indoor": False},
        "Minnesota": {"city": "Minneapolis", "state": "MN", "indoor": True},
        "New England": {"city": "Foxborough", "state": "MA", "indoor": False},
        "New Orleans": {"city": "New Orleans", "state": "LA", "indoor": True},
        "NY Giants": {"city": "East Rutherford", "state": "NJ", "indoor": False},
        "NY Jets": {"city": "East Rutherford", "state": "NJ", "indoor": False},
        "Philadelphia": {"city": "Philadelphia", "state": "PA", "indoor": False},
        "Pittsburgh": {"city": "Pittsburgh", "state": "PA", "indoor": False},
        "San Francisco": {"city": "Santa Clara", "state": "CA", "indoor": False},
        "Seattle": {"city": "Seattle", "state": "WA", "indoor": False},
        "Tampa Bay": {"city": "Tampa", "state": "FL", "indoor": False},
        "Tennessee": {"city": "Nashville", "state": "TN", "indoor": False},
        "Washington": {"city": "Landover", "state": "MD", "indoor": False},
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AccuWeather client

        Args:
            api_key: AccuWeather API key (or use ACCUWEATHER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ACCUWEATHER_API_KEY")
        if not self.api_key:
            logger.warning("No AccuWeather API key found. Weather features disabled.")

        self.base_url = "http://dataservice.accuweather.com"
        self.location_cache: Dict[str, str] = {}  # city -> location_key cache

    def get_location_key(self, city: str, state: str) -> Optional[str]:
        """
        Get AccuWeather location key for a city

        Args:
            city: City name
            state: State code (e.g., "AZ", "NY")

        Returns:
            Location key or None
        """
        if not self.api_key:
            return None

        # Check cache
        cache_key = f"{city},{state}"
        if cache_key in self.location_cache:
            return self.location_cache[cache_key]

        try:
            # City search endpoint
            url = f"{self.base_url}/locations/v1/cities/US/search"
            params = {
                "apikey": self.api_key,
                "q": city,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Find matching city/state
            for location in data:
                admin_area = location.get("AdministrativeArea", {})
                if admin_area.get("ID") == state:
                    location_key = location.get("Key")
                    self.location_cache[cache_key] = location_key
                    logger.info(
                        f"Found location key for {city}, {state}: {location_key}"
                    )
                    return location_key

            logger.warning(f"No location key found for {city}, {state}")
            return None

        except Exception as e:
            logger.error(f"Error getting location key for {city}, {state}: {e}")
            return None

    def get_hourly_forecast(
        self, location_key: str, hours_ahead: int = 12
    ) -> Optional[Dict]:
        """
        Get hourly forecast for a location

        Args:
            location_key: AccuWeather location key
            hours_ahead: Hours into future (12 or 120)

        Returns:
            Forecast data or None
        """
        if not self.api_key:
            return None

        try:
            # Hourly forecast endpoint
            url = (
                f"{self.base_url}/forecasts/v1/hourly/{hours_ahead}hour/{location_key}"
            )
            params = {
                "apikey": self.api_key,
                "details": "true",  # Include wind, precipitation
                "metric": "false",  # Use Fahrenheit
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return data

        except Exception as e:
            logger.error(f"Error getting forecast for location {location_key}: {e}")
            return None

    def get_game_weather(self, team: str, game_time: datetime) -> Optional[Dict]:
        """
        Get weather forecast for a specific game

        Args:
            team: Home team name
            game_time: Game datetime

        Returns:
            Weather data dict with temperature, wind, precipitation
        """
        # Get stadium info
        stadium_info = self.NFL_STADIUM_LOCATIONS.get(team)
        if not stadium_info:
            logger.warning(f"No stadium info for team: {team}")
            return None

        # Indoor stadium = no weather impact
        if stadium_info.get("indoor"):
            return {
                "indoor": True,
                "temperature": None,
                "wind_speed": None,
                "precipitation": None,
                "conditions": "Indoor",
            }

        # Get location key
        location_key = self.get_location_key(
            stadium_info["city"], stadium_info["state"]
        )

        if not location_key:
            return None

        # Get forecast
        forecast = self.get_hourly_forecast(location_key, hours_ahead=12)
        if not forecast:
            return None

        # Find closest forecast to game time
        closest_forecast = None
        min_time_diff = float("inf")

        for hour_forecast in forecast:
            forecast_time = datetime.fromisoformat(
                hour_forecast["DateTime"].replace("Z", "+00:00")
            )
            time_diff = abs((forecast_time - game_time).total_seconds())

            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = hour_forecast

        if not closest_forecast:
            return None

        # Extract weather data
        temperature = closest_forecast.get("Temperature", {}).get("Value")
        wind_speed = closest_forecast.get("Wind", {}).get("Speed", {}).get("Value")
        has_precipitation = closest_forecast.get("HasPrecipitation", False)
        precipitation_type = closest_forecast.get("PrecipitationType", "None")
        icon_phrase = closest_forecast.get("IconPhrase", "")

        weather_data = {
            "indoor": False,
            "temperature": temperature,
            "wind_speed": wind_speed,
            "precipitation": precipitation_type if has_precipitation else None,
            "conditions": icon_phrase,
            "forecast_time": closest_forecast["DateTime"],
            "city": stadium_info["city"],
            "state": stadium_info["state"],
        }

        logger.info(
            f"Weather for {team} ({stadium_info['city']}): "
            f"{temperature}°F, Wind {wind_speed} MPH, {icon_phrase}"
        )

        return weather_data

    def calculate_weather_impact(self, weather_data: Dict) -> Tuple[float, float]:
        """
        Calculate weather impact on total and spread

        Billy Walters principles:
        - Wind >15 MPH: Reduce total by 3-5 points
        - Temp <32°F: Reduce total by 2-3 points
        - Rain/Snow: Reduce total by 2-4 points

        Args:
            weather_data: Weather data from get_game_weather

        Returns:
            (total_adjustment, spread_adjustment)
        """
        if weather_data.get("indoor"):
            return 0.0, 0.0

        total_adj = 0.0
        spread_adj = 0.0

        temperature = weather_data.get("temperature")
        wind_speed = weather_data.get("wind_speed")
        precipitation = weather_data.get("precipitation")

        # Wind impact (most important for passing)
        if wind_speed and wind_speed > 15:
            # Reduce total by 0.3 points per MPH over 15, max 5 points
            wind_impact = min((wind_speed - 15) * 0.3, 5.0)
            total_adj -= wind_impact
            spread_adj -= 1.0  # Favors defense

            logger.info(
                f"High wind ({wind_speed} MPH): Total -{wind_impact:.1f}, Spread -1.0"
            )

        # Temperature impact
        if temperature and temperature < 32:
            temp_impact = 2.5
            total_adj -= temp_impact
            spread_adj -= 0.5  # Favors rushing teams

            logger.info(
                f"Cold weather ({temperature}°F): Total -{temp_impact}, Spread -0.5"
            )

        # Precipitation
        if precipitation and precipitation.lower() in ["rain", "snow"]:
            precip_impact = 3.0
            total_adj -= precip_impact
            spread_adj -= 1.0

            logger.info(
                f"Precipitation ({precipitation}): Total -{precip_impact}, Spread -1.0"
            )

        return total_adj, spread_adj


def main():
    """Test weather client"""
    client = AccuWeatherClient()

    if not client.api_key:
        print("No API key found. Set ACCUWEATHER_API_KEY environment variable.")
        return

    # Test: Get weather for Green Bay (outdoor, cold weather stadium)
    test_time = datetime.now(timezone.utc)
    weather = client.get_game_weather("Green Bay", test_time)

    if weather:
        print("\n" + "=" * 60)
        print("Weather for Green Bay Packers")
        print("=" * 60)
        print(f"Indoor: {weather['indoor']}")
        print(f"Temperature: {weather.get('temperature')}°F")
        print(f"Wind Speed: {weather.get('wind_speed')} MPH")
        print(f"Precipitation: {weather.get('precipitation')}")
        print(f"Conditions: {weather.get('conditions')}")

        # Calculate impact
        total_adj, spread_adj = client.calculate_weather_impact(weather)
        print("\nBilly Walters Impact:")
        print(f"Total Adjustment: {total_adj:+.1f} points")
        print(f"Spread Adjustment: {spread_adj:+.1f} points")
        print("=" * 60)


if __name__ == "__main__":
    main()
