"""AccuWeather API client for weather impact analysis."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class AccuWeatherClient:
    """Client for fetching weather data from AccuWeather API."""

    BASE_URL = "http://dataservice.accuweather.com"

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize AccuWeather client.

        Args:
            api_key: AccuWeather API key (defaults to ACCUWEATHER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ACCUWEATHER_API_KEY")
        if not self.api_key:
            logger.warning(
                "AccuWeather API key not found. Weather data will be unavailable."
            )
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_location_key(self, city: str, state: str = "") -> Optional[str]:
        """
        Get AccuWeather location key for a city.

        Args:
            city: City name
            state: State code (optional)

        Returns:
            Location key string or None if not found
        """
        if not self.api_key:
            return None

        query = f"{city}, {state}" if state else city
        url = f"{self.BASE_URL}/locations/v1/cities/search"
        params = {"apikey": self.api_key, "q": query}

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return data[0]["Key"]
                else:
                    logger.error(f"AccuWeather location search failed: {response.status}")
        except Exception as e:
            logger.error(f"Error searching for location: {e}", exc_info=True)

        return None

    async def get_forecast(
        self, location_key: str, days: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for a location.

        Args:
            location_key: AccuWeather location key
            days: Number of days (1, 5, 10, or 15)

        Returns:
            Forecast data dict or None
        """
        if not self.api_key:
            return None

        url = f"{self.BASE_URL}/forecasts/v1/daily/{days}day/{location_key}"
        params = {"apikey": self.api_key, "details": "true", "metric": "false"}

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"AccuWeather forecast failed: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}", exc_info=True)

        return None

    async def get_game_weather(
        self, venue: str, game_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for a game venue.

        Args:
            venue: Stadium/venue name
            game_date: Game date (optional, for future implementation)

        Returns:
            Weather data dict with relevant game conditions
        """
        # Simple venue to city mapping (expand as needed)
        venue_city_map = {
            "Lambeau Field": ("Green Bay", "WI"),
            "Soldier Field": ("Chicago", "IL"),
            "Arrowhead Stadium": ("Kansas City", "MO"),
            "Mile High Stadium": ("Denver", "CO"),
            "Empower Field": ("Denver", "CO"),
            "Gillette Stadium": ("Foxborough", "MA"),
            "Highmark Stadium": ("Orchard Park", "NY"),
            "MetLife Stadium": ("East Rutherford", "NJ"),
        }

        # Try to find city from venue
        city_state = venue_city_map.get(venue)
        if not city_state:
            # Try to extract city from venue name
            logger.warning(f"Unknown venue: {venue}. Attempting extraction...")
            return None

        city, state = city_state
        location_key = await self.get_location_key(city, state)

        if not location_key:
            logger.warning(f"Could not find location key for {city}, {state}")
            return None

        forecast = await self.get_forecast(location_key, days=5)

        if not forecast:
            return None

        # Extract relevant weather data
        daily_forecasts = forecast.get("DailyForecasts", [])
        if not daily_forecasts:
            return None

        # Use first day for now (can be enhanced to match game_date)
        day_forecast = daily_forecasts[0]

        weather_data = {
            "temperature_high": day_forecast["Temperature"]["Maximum"]["Value"],
            "temperature_low": day_forecast["Temperature"]["Minimum"]["Value"],
            "precipitation_probability": day_forecast["Day"].get(
                "PrecipitationProbability", 0
            ),
            "wind_speed": day_forecast["Day"].get("Wind", {})
            .get("Speed", {})
            .get("Value", 0),
            "wind_direction": day_forecast["Day"].get("Wind", {}).get("Direction", {}),
            "conditions": day_forecast["Day"].get("IconPhrase", "Unknown"),
            "is_outdoor": True,  # Assume outdoor for now
            "weather_factor": self._calculate_weather_factor(day_forecast),
        }

        return weather_data

    def _calculate_weather_factor(self, forecast: Dict[str, Any]) -> float:
        """
        Calculate weather impact factor (-1 to 1, negative favors defense).

        Args:
            forecast: Daily forecast data

        Returns:
            Weather factor score
        """
        factor = 0.0

        # Temperature impact
        temp = forecast["Temperature"]["Maximum"]["Value"]
        if temp < 32:  # Freezing
            factor -= 0.3
        elif temp < 20:  # Extreme cold
            factor -= 0.5
        elif temp > 95:  # Extreme heat
            factor -= 0.2

        # Wind impact
        wind = forecast["Day"].get("Wind", {}).get("Speed", {}).get("Value", 0)
        if wind > 20:  # Significant wind
            factor -= 0.3
        elif wind > 30:  # Extreme wind
            factor -= 0.5

        # Precipitation impact
        precip_prob = forecast["Day"].get("PrecipitationProbability", 0)
        if precip_prob > 50:
            factor -= 0.2
        elif precip_prob > 80:
            factor -= 0.4

        return max(min(factor, 1.0), -1.0)  # Clamp to [-1, 1]

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

