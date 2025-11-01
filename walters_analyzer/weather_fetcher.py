"""
AccuWeather API integration for game weather analysis.

Billy Walters methodology emphasizes weather as a critical factor:
- Wind >15mph significantly impacts passing games and field goals
- Precipitation affects ball handling, reduces scoring
- Temperature extremes impact player performance
- Dome games eliminate weather as a variable
"""

import httpx
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AccuWeatherClient:
    """
    Client for AccuWeather API with Billy Walters-focused weather analysis.
    
    API Documentation: https://developer.accuweather.com/
    
    Key endpoints:
    - Location Search: Find location key for stadium
    - Hourly Forecast: Get detailed hourly conditions
    - Daily Forecast: Get daily overview
    """
    
    BASE_URL = "https://dataservice.accuweather.com"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ACCUWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ACCUWEATHER_API_KEY not found. Set it in .env or pass to constructor."
            )
        self.client = httpx.Client(timeout=30.0)
    
    def search_location(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for a location (stadium/city) and return location key.
        
        Args:
            query: Search term (e.g., "Lambeau Field" or "Green Bay, WI")
            
        Returns:
            Location data including key, or None if not found
        """
        url = f"{self.BASE_URL}/locations/v1/cities/search"
        params = {
            "apikey": self.api_key,
            "q": query,
            "details": "true"
        }
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            results = response.json()
            
            if results and len(results) > 0:
                # Return the first (best) match
                return results[0]
            return None
        except httpx.HTTPError as e:
            print(f"Error searching location '{query}': {e}")
            return None
    
    def get_hourly_forecast(
        self, 
        location_key: str, 
        hours: int = 12
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get hourly forecast for a location.
        
        Args:
            location_key: AccuWeather location key
            hours: Number of hours (1, 12, 24, 72, 120)
            
        Returns:
            List of hourly forecasts or None
        """
        # AccuWeather API supports specific hour intervals
        valid_hours = [1, 12, 24, 72, 120]
        hours = min(valid_hours, key=lambda x: abs(x - hours))
        
        url = f"{self.BASE_URL}/forecasts/v1/hourly/{hours}hour/{location_key}"
        params = {
            "apikey": self.api_key,
            "details": "true",
            "metric": "false"  # Use imperial units (Fahrenheit, MPH)
        }
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching hourly forecast for {location_key}: {e}")
            return None
    
    def get_daily_forecast(
        self,
        location_key: str,
        days: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get daily forecast for a location.
        
        Args:
            location_key: AccuWeather location key
            days: Number of days (1 or 5)
            
        Returns:
            Daily forecast data or None
        """
        days = 5 if days > 1 else 1
        url = f"{self.BASE_URL}/forecasts/v1/daily/{days}day/{location_key}"
        params = {
            "apikey": self.api_key,
            "details": "true",
            "metric": "false"
        }
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching daily forecast for {location_key}: {e}")
            return None
    
    def get_current_conditions(
        self,
        location_key: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get current weather conditions.
        
        Args:
            location_key: AccuWeather location key
            
        Returns:
            Current conditions or None
        """
        url = f"{self.BASE_URL}/currentconditions/v1/{location_key}"
        params = {
            "apikey": self.api_key,
            "details": "true"
        }
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching current conditions for {location_key}: {e}")
            return None
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class StadiumWeatherCache:
    """
    Cache for stadium location keys to minimize API calls.
    """
    
    def __init__(self, cache_file: str = "data/stadium_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_location_key(self, stadium: str) -> Optional[str]:
        """Get cached location key for stadium."""
        return self.cache.get(stadium, {}).get("location_key")
    
    def set_location_key(self, stadium: str, location_key: str, location_data: Dict):
        """Cache location key for stadium."""
        self.cache[stadium] = {
            "location_key": location_key,
            "location_name": location_data.get("EnglishName"),
            "state": location_data.get("AdministrativeArea", {}).get("ID"),
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
        self._save_cache()


def extract_weather_data(
    forecast_hour: Dict[str, Any],
    location_data: Dict[str, Any],
    stadium: str,
    is_dome: bool,
    game_date: Optional[str] = None,
    game_time: Optional[str] = None,
    sport: str = "college_football"
) -> Dict[str, Any]:
    """
    Extract and normalize weather data for betting analysis.
    
    Args:
        forecast_hour: Hourly forecast data from AccuWeather
        location_data: Location information
        stadium: Stadium name
        is_dome: Whether stadium is indoor
        game_date: Game date (ISO format)
        game_time: Game time
        sport: Sport type
        
    Returns:
        Normalized weather data dictionary
    """
    from scrapers.overtime_live.items import iso_now
    
    # Extract location info
    city = location_data.get("EnglishName", "Unknown")
    state = location_data.get("AdministrativeArea", {}).get("ID", "")
    location = f"{city}, {state}" if state else city
    
    # Extract temperature
    temp_data = forecast_hour.get("Temperature", {})
    temperature_f = temp_data.get("Value")
    
    feels_like_data = forecast_hour.get("RealFeelTemperature", {})
    feels_like_f = feels_like_data.get("Value")
    
    # Extract wind
    wind_data = forecast_hour.get("Wind", {})
    wind_speed = wind_data.get("Speed", {})
    wind_speed_mph = wind_speed.get("Value")
    
    wind_gust_data = forecast_hour.get("WindGust", {})
    wind_gust_speed = wind_gust_data.get("Speed", {})
    wind_gust_mph = wind_gust_speed.get("Value")
    
    wind_direction_data = wind_data.get("Direction", {})
    wind_direction = wind_direction_data.get("English")
    
    # Extract precipitation
    precip_prob = forecast_hour.get("PrecipitationProbability")
    has_precipitation = forecast_hour.get("HasPrecipitation", False)
    precip_type = forecast_hour.get("PrecipitationType", "None") if has_precipitation else "None"
    
    # Extract other conditions
    humidity = forecast_hour.get("RelativeHumidity")
    cloud_cover = forecast_hour.get("CloudCover")
    visibility = forecast_hour.get("Visibility", {})
    visibility_miles = visibility.get("Value")
    
    weather_desc = forecast_hour.get("IconPhrase", "Unknown")
    
    # Build weather item
    weather_item = {
        "source": "accuweather",
        "sport": sport,
        "collected_at": iso_now(),
        "game_date": game_date,
        "game_time": game_time,
        "stadium": stadium,
        "location": location,
        "is_dome": is_dome,
        "temperature_f": temperature_f,
        "feels_like_f": feels_like_f,
        "wind_speed_mph": wind_speed_mph,
        "wind_gust_mph": wind_gust_mph,
        "wind_direction": wind_direction,
        "precipitation_prob": precip_prob,
        "precipitation_type": precip_type,
        "humidity": humidity,
        "weather_description": weather_desc,
        "cloud_cover": cloud_cover,
        "visibility_miles": visibility_miles,
        "location_key": location_data.get("Key"),
        "forecast_url": f"https://www.accuweather.com/en/us/{city.lower().replace(' ', '-')}/{location_data.get('Key')}/hourly-weather-forecast/{location_data.get('Key')}"
    }
    
    # Add placeholder values for required fields before creating WeatherReportItem
    weather_item["weather_impact_score"] = 0
    weather_item["betting_adjustment"] = ""
    
    # Calculate Billy Walters impact scores
    from scrapers.overtime_live.items import WeatherReportItem
    temp_item = WeatherReportItem(**weather_item)
    weather_item["weather_impact_score"] = temp_item.calculate_impact_score()
    weather_item["betting_adjustment"] = temp_item.get_betting_adjustment()
    
    return weather_item


def fetch_game_weather(
    stadium: str,
    location: str,
    is_dome: bool = False,
    game_date: Optional[str] = None,
    game_time: Optional[str] = None,
    sport: str = "college_football",
    use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Fetch weather for a specific game.
    
    Args:
        stadium: Stadium name
        location: City/location for search
        is_dome: Whether stadium is indoor
        game_date: Game date (ISO format or relative)
        game_time: Game time
        sport: Sport type
        use_cache: Use cached location keys
        
    Returns:
        Weather data dictionary or None
    """
    cache = StadiumWeatherCache() if use_cache else None
    
    with AccuWeatherClient() as client:
        # Try to get location key from cache
        location_key = cache.get_location_key(stadium) if cache else None
        location_data = None
        
        if not location_key:
            # Search for location
            location_data = client.search_location(location)
            if not location_data:
                print(f"Could not find location for: {location}")
                return None
            
            location_key = location_data["Key"]
            if cache:
                cache.set_location_key(stadium, location_key, location_data)
        
        # If we don't have location_data, fetch it
        if not location_data:
            # For cached keys, we need to search again to get full data
            location_data = client.search_location(location)
            if not location_data:
                print(f"Could not fetch location data for: {location}")
                return None
        
        # Get hourly forecast (use 12-hour to capture game time)
        hourly_forecast = client.get_hourly_forecast(location_key, hours=12)
        
        if not hourly_forecast or len(hourly_forecast) == 0:
            print(f"No forecast data available for {stadium}")
            return None
        
        # Use the first hour as representative (or match game time if parsing is added)
        forecast_hour = hourly_forecast[0]
        
        # Extract and return weather data
        return extract_weather_data(
            forecast_hour=forecast_hour,
            location_data=location_data,
            stadium=stadium,
            is_dome=is_dome,
            game_date=game_date,
            game_time=game_time,
            sport=sport
        )

