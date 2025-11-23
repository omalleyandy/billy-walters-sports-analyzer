"""
AccuWeather API Client

Fetches weather forecasts for game locations.
Implements rate limiting, retry logic, and error handling.

Billy Walters Weather Impact Principles:
- Wind >15 MPH: Reduce total by 3-5 points, favor defense
- Temp <32°F: Reduce total by 2-3 points, favor rushing
- Rain/Snow: Reduce total by 2-4 points
- Indoor: No adjustments
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AccuWeatherClient:
    """Client for fetching weather data from AccuWeather API."""

    BASE_URL = "https://dataservice.accuweather.com"

    # NFL Stadium locations (city for location key lookup)
    NFL_STADIUM_LOCATIONS = {
        "Arizona": {"city": "Glendale", "state": "AZ", "indoor": True},
        "Atlanta": {"city": "Atlanta", "state": "GA", "indoor": True},
        "Baltimore": {"city": "Baltimore", "state": "MD", "indoor": False},
        "Buffalo": {"city": "Buffalo", "state": "NY", "indoor": True},
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

    def __init__(
        self,
        api_key: str | None = None,
        rate_limit_delay: float = 1.0,
        timeout: float = 30.0,
    ):
        """
        Initialize AccuWeather API client.

        Args:
            api_key: AccuWeather API key (defaults to ACCUWEATHER_API_KEY env var)
            rate_limit_delay: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("ACCUWEATHER_API_KEY")
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.last_request_time: float = 0.0
        self._client: httpx.AsyncClient | None = None

        if not self.api_key:
            raise ValueError(
                "ACCUWEATHER_API_KEY must be set "
                "either as argument or environment variable"
            )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP client."""
        logger.info("Initializing AccuWeather API client")
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.timeout,
            headers={
                "User-Agent": "BillyWaltersSportsAnalyzer/1.0",
                "Accept": "application/json",
            },
        )
        logger.info("AccuWeather client initialized")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
        logger.info("Closed AccuWeather client")

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = asyncio.get_event_loop().time()

    async def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any] | list[Any]:
        """
        Make HTTP request with retry logic.

        Args:
            endpoint: API endpoint
            params: Query parameters
            max_retries: Maximum retry attempts

        Returns:
            Response JSON data

        Raises:
            RuntimeError: If request fails after all retries
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Call connect() first.")

        await self._rate_limit()

        # Add API key to params
        if params is None:
            params = {}
        params["apikey"] = self.api_key

        for attempt in range(max_retries):
            try:
                logger.debug(f"GET {endpoint} (attempt {attempt + 1}/{max_retries})")

                response = await self._client.get(endpoint, params=params)
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP error {e.response.status_code}: {e.response.text}"
                )

                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise RuntimeError(
                        f"Client error {e.response.status_code}: {e.response.text}"
                    ) from e

                # Retry server errors (5xx)
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"Request failed after {max_retries} attempts"
                    ) from e

            except httpx.RequestError as e:
                logger.warning(f"Request error: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"Request failed after {max_retries} attempts: {e}"
                    ) from e

        raise RuntimeError("Unexpected error in _make_request")

    async def get_location_key(
        self, city: str, state: str, max_retries: int = 3
    ) -> str:
        """
        Get AccuWeather location key for a city.

        Args:
            city: City name
            state: State abbreviation
            max_retries: Maximum retry attempts

        Returns:
            Location key string

        Raises:
            RuntimeError: If location not found or request fails
        """
        logger.info(f"Getting location key for {city}, {state}")

        # Search for location
        query = f"{city}, {state}"
        data = await self._make_request(
            "/locations/v1/cities/US/search",
            params={"q": query},
            max_retries=max_retries,
        )

        if not data or not isinstance(data, list):
            raise RuntimeError(f"No location found for {query}")

        # Get first result
        location = data[0]
        location_key = location.get("Key")

        if not location_key:
            raise RuntimeError(f"No location key in response for {query}")

        logger.info(f"Location key for {city}, {state}: {location_key}")
        return location_key

    async def get_current_conditions(
        self, location_key: str, max_retries: int = 3
    ) -> dict[str, Any]:
        """
        Get current weather conditions for a location.

        Args:
            location_key: AccuWeather location key
            max_retries: Maximum retry attempts

        Returns:
            Current conditions dictionary

        Raises:
            RuntimeError: If request fails
        """
        logger.info(f"Getting current conditions for location {location_key}")

        data = await self._make_request(
            f"/currentconditions/v1/{location_key}",
            params={"details": "true"},
            max_retries=max_retries,
        )

        if not data or not isinstance(data, list):
            raise RuntimeError("Invalid response from current conditions API")

        conditions = data[0]
        logger.info(f"Fetched current conditions for {location_key}")

        return self._format_conditions(conditions)

    async def get_hourly_forecast(
        self,
        location_key: str,
        hours: int = 12,
        max_retries: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Get hourly weather forecast for a location.

        Args:
            location_key: AccuWeather location key
            hours: Number of hours to forecast (1, 12, 24, 72, 120)
            max_retries: Maximum retry attempts

        Returns:
            List of hourly forecast dictionaries

        Raises:
            RuntimeError: If request fails
        """
        # Map hours to API endpoint
        if hours <= 12:
            endpoint = f"/forecasts/v1/hourly/12hour/{location_key}"
        elif hours <= 24:
            endpoint = f"/forecasts/v1/hourly/24hour/{location_key}"
        elif hours <= 72:
            endpoint = f"/forecasts/v1/hourly/72hour/{location_key}"
        else:
            endpoint = f"/forecasts/v1/hourly/120hour/{location_key}"

        logger.info(f"Getting {hours}h forecast for location {location_key}")

        data = await self._make_request(
            endpoint, params={"details": "true"}, max_retries=max_retries
        )

        if not isinstance(data, list):
            raise RuntimeError("Invalid response from hourly forecast API")

        logger.info(f"Fetched {len(data)} hourly forecasts")

        # Format and return
        forecasts = [self._format_hourly(hour) for hour in data]
        return forecasts[:hours]  # Return only requested hours

    def _format_conditions(self, conditions: dict[str, Any]) -> dict[str, Any]:
        """Format current conditions data to standard weather format."""
        temp = conditions.get("Temperature", {}).get("Imperial", {})
        feels_like = conditions.get("RealFeelTemperature", {}).get("Imperial", {})
        wind = conditions.get("Wind", {})
        wind_speed = wind.get("Speed", {}).get("Imperial", {})
        wind_gust = conditions.get("WindGust", {}).get("Speed", {}).get("Imperial", {})

        return {
            # Standard keys expected by weather analysis
            "temperature": temp.get("Value"),
            "feels_like": feels_like.get("Value"),
            "wind_speed": wind_speed.get("Value"),
            "wind_gust": wind_gust.get("Value"),
            "wind_direction": wind.get("Direction", {}).get("English"),
            "humidity": conditions.get("RelativeHumidity"),
            "description": conditions.get("WeatherText"),
            "precipitation_type": conditions.get("PrecipitationType"),
            "precipitation_probability": 100
            if conditions.get("HasPrecipitation", False)
            else 0,
            # Additional data
            "has_precipitation": conditions.get("HasPrecipitation", False),
            "uv_index": conditions.get("UVIndex"),
            "visibility": conditions.get("Visibility", {})
            .get("Imperial", {})
            .get("Value"),
            "timestamp": conditions.get("LocalObservationDateTime"),
            "source": "accuweather",
        }

    def _format_hourly(self, hourly: dict[str, Any]) -> dict[str, Any]:
        """Format hourly forecast data to standard weather format."""
        temp = hourly.get("Temperature", {})
        feels_like = hourly.get("RealFeelTemperature", {})
        wind = hourly.get("Wind", {})
        wind_speed = wind.get("Speed", {})
        wind_gust = (
            hourly.get("WindGust", {}).get("Speed", {}) if "WindGust" in hourly else {}
        )

        return {
            "forecast_time": hourly.get("DateTime"),
            # Standard keys expected by weather analysis
            "temperature": temp.get("Value"),
            "feels_like": feels_like.get("Value") if feels_like else temp.get("Value"),
            "wind_speed": wind_speed.get("Value"),
            "wind_gust": wind_gust.get("Value")
            if wind_gust
            else wind_speed.get("Value"),
            "wind_direction": wind.get("Direction", {}).get("English"),
            "humidity": hourly.get("RelativeHumidity"),
            "description": hourly.get("IconPhrase"),
            "precipitation_type": hourly.get("PrecipitationType"),
            "precipitation_probability": hourly.get("PrecipitationProbability", 0),
            # Additional data
            "has_precipitation": hourly.get("HasPrecipitation", False),
            "uv_index": hourly.get("UVIndex"),
            "source": "accuweather",
        }

    async def get_game_forecast(
        self,
        city: str,
        state: str,
        game_time: datetime,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """
        Get weather forecast for a specific game time.

        Args:
            city: Stadium city
            state: Stadium state
            game_time: Game start time
            max_retries: Maximum retry attempts

        Returns:
            Weather forecast dictionary

        Raises:
            RuntimeError: If request fails
        """
        logger.info(f"Getting game forecast for {city}, {state} at {game_time}")

        # Get location key
        location_key = await self.get_location_key(city, state, max_retries=max_retries)

        # Get hourly forecast
        from datetime import timezone

        now = datetime.now(timezone.utc)
        hours_ahead = int((game_time - now).total_seconds() / 3600)

        if hours_ahead < 0:
            # Game in the past - get current conditions
            logger.warning("Game time is in the past, getting current conditions")
            return await self.get_current_conditions(
                location_key, max_retries=max_retries
            )

        # Starter plan only has 12-hour hourly forecast access
        # For games >12 hours away, fall back to less granular but available data
        if hours_ahead > 12:
            logger.info(
                f"Game is {hours_ahead} hours away, using current conditions "
                "(starter plan limited to 12-hour forecast)"
            )
            # Return current conditions as best available forecast
            # Note: This is a limitation of the starter plan
            conditions = await self.get_current_conditions(
                location_key, max_retries=max_retries
            )
            logger.warning(
                f"Using current conditions for game {hours_ahead} hours away. "
                "For better forecasts, upgrade AccuWeather plan or use OpenWeather fallback."
            )
            return conditions

        # Get hourly forecast (within 12-hour window)
        forecast_hours = min(hours_ahead + 1, 12)
        forecasts = await self.get_hourly_forecast(
            location_key, hours=forecast_hours, max_retries=max_retries
        )

        # Find closest forecast to game time
        closest_forecast = min(
            forecasts,
            key=lambda f: abs(
                datetime.fromisoformat(f["forecast_time"].replace("Z", "+00:00"))
                - game_time
            ),
        )

        logger.info(
            f"Found forecast for game time: {closest_forecast['forecast_time']}"
        )
        return closest_forecast

    def _normalize_team_name(self, team: str) -> str:
        """
        Normalize ESPN full team names to stadium lookup format.

        Args:
            team: Full team name (e.g., "New England Patriots")

        Returns:
            Short team name for stadium lookup (e.g., "New England")
        """
        # Map full team names to stadium lookup keys
        team_mappings = {
            "Arizona Cardinals": "Arizona",
            "Atlanta Falcons": "Atlanta",
            "Baltimore Ravens": "Baltimore",
            "Buffalo Bills": "Buffalo",
            "Carolina Panthers": "Carolina",
            "Chicago Bears": "Chicago",
            "Cincinnati Bengals": "Cincinnati",
            "Cleveland Browns": "Cleveland",
            "Dallas Cowboys": "Dallas",
            "Denver Broncos": "Denver",
            "Detroit Lions": "Detroit",
            "Green Bay Packers": "Green Bay",
            "Houston Texans": "Houston",
            "Indianapolis Colts": "Indianapolis",
            "Jacksonville Jaguars": "Jacksonville",
            "Kansas City Chiefs": "Kansas City",
            "Las Vegas Raiders": "Las Vegas",
            "Los Angeles Chargers": "LA Chargers",
            "Los Angeles Rams": "LA Rams",
            "Miami Dolphins": "Miami",
            "Minnesota Vikings": "Minnesota",
            "New England Patriots": "New England",
            "New Orleans Saints": "New Orleans",
            "New York Giants": "NY Giants",
            "New York Jets": "NY Jets",
            "Philadelphia Eagles": "Philadelphia",
            "Pittsburgh Steelers": "Pittsburgh",
            "San Francisco 49ers": "San Francisco",
            "Seattle Seahawks": "Seattle",
            "Tampa Bay Buccaneers": "Tampa Bay",
            "Tennessee Titans": "Tennessee",
            "Washington Commanders": "Washington",
        }

        # Try exact match first
        if team in team_mappings:
            return team_mappings[team]

        # If already short form, return as-is
        if team in self.NFL_STADIUM_LOCATIONS:
            return team

        # Fallback: return original (will log warning in get_game_weather)
        return team

    async def get_game_weather(
        self, team: str, game_time: datetime, max_retries: int = 3
    ) -> dict[str, Any] | None:
        """
        Get weather forecast for a specific NFL game using team name.

        Args:
            team: Home team name (e.g., "Green Bay Packers" or "Green Bay")
            game_time: Game start time
            max_retries: Maximum retry attempts

        Returns:
            Weather data dict with temperature, wind, precipitation, or None

        Raises:
            RuntimeError: If request fails
        """
        # Normalize team name to stadium lookup format
        normalized_team = self._normalize_team_name(team)

        # Get stadium info
        stadium_info = self.NFL_STADIUM_LOCATIONS.get(normalized_team)
        if not stadium_info:
            logger.warning(
                f"No stadium info for team: {team} (normalized: {normalized_team})"
            )
            return None

        # Indoor stadium = no weather impact
        if stadium_info.get("indoor"):
            return {
                "indoor": True,
                "temperature_f": None,
                "wind_speed_mph": None,
                "precipitation_type": None,
                "weather_text": "Indoor",
                "city": stadium_info["city"],
                "state": stadium_info["state"],
            }

        # Get forecast for outdoor stadium
        forecast = await self.get_game_forecast(
            stadium_info["city"], stadium_info["state"], game_time, max_retries
        )

        # Add stadium info to forecast
        forecast["indoor"] = False
        forecast["city"] = stadium_info["city"]
        forecast["state"] = stadium_info["state"]

        return forecast

    def calculate_weather_impact(
        self, weather_data: dict[str, Any]
    ) -> tuple[float, float]:
        """
        Calculate weather impact on total and spread using Billy Walters principles.

        Principles:
        - Wind >15 MPH: Reduce total by 3-5 points, favor defense
        - Temp <32°F: Reduce total by 2-3 points, favor rushing
        - Rain/Snow: Reduce total by 2-4 points

        Args:
            weather_data: Weather data from get_game_weather or get_game_forecast

        Returns:
            (total_adjustment, spread_adjustment) in points
        """
        if weather_data.get("indoor"):
            return 0.0, 0.0

        total_adj = 0.0
        spread_adj = 0.0

        # Support both key formats (standardized and legacy)
        temperature = weather_data.get("temperature") or weather_data.get(
            "temperature_f"
        )
        wind_speed = weather_data.get("wind_speed") or weather_data.get(
            "wind_speed_mph"
        )
        precipitation = weather_data.get("precipitation_type")

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


# Example usage
async def main():
    """Example usage of AccuWeatherClient with Billy Walters analysis."""
    from datetime import timezone

    async with AccuWeatherClient() as client:
        # Test: Get weather for Green Bay (outdoor, cold weather stadium)
        test_time = datetime.now(timezone.utc).replace(hour=13, minute=0, second=0)
        weather = await client.get_game_weather("Green Bay", test_time)

        if weather:
            print("\n" + "=" * 60)
            print("Weather for Green Bay Packers")
            print("=" * 60)
            print(f"Indoor: {weather['indoor']}")
            temp = weather.get("temperature") or weather.get("temperature_f")
            wind = weather.get("wind_speed") or weather.get("wind_speed_mph")
            desc = weather.get("description") or weather.get("weather_text")
            print(f"Temperature: {temp}°F")
            print(f"Wind Speed: {wind} MPH")
            print(f"Precipitation: {weather.get('precipitation_type')}")
            print(f"Conditions: {desc}")

            # Calculate Billy Walters impact
            total_adj, spread_adj = client.calculate_weather_impact(weather)
            print("\nBilly Walters Impact:")
            print(f"Total Adjustment: {total_adj:+.1f} points")
            print(f"Spread Adjustment: {spread_adj:+.1f} points")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
