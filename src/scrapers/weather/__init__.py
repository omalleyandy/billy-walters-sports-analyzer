"""
Weather Scraper Module

Game-day weather conditions for outdoor stadiums.
Supports multiple weather providers with fallback.

Providers:
    AccuWeatherClient: AccuWeather API (primary)
    OpenWeatherClient: OpenWeather API (fallback)
    WeatherClient: Unified client with provider selection
"""

from scrapers.weather.accuweather import AccuWeatherClient
from scrapers.weather.client import WeatherClient
from scrapers.weather.openweather import OpenWeatherClient

__all__ = [
    "AccuWeatherClient",
    "OpenWeatherClient",
    "WeatherClient",
]
