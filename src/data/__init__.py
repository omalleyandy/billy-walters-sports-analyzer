"""
Billy Walters Sports Analyzer - Data Integration Package

API clients for fetching odds, game data, and weather information.
"""

from .action_network_client import ActionNetworkClient
from .validated_action_network import ValidatedActionNetworkClient

# Overtime clients archived - use overtime_api_client.py or overtime_hybrid_scraper.py
from .accuweather_client import AccuWeatherClient
from .openweather_client import OpenWeatherClient
from .weather_client import WeatherClient
from .validated_weather import ValidatedWeatherClient
from .models import (
    League,
    Conference,
    Team,
    Stadium,
    WeatherConditions,
    OddsMovement,
    Game,
    ActionNetworkResponse,
)

__all__ = [
    # Action Network
    "ActionNetworkClient",
    "ValidatedActionNetworkClient",
    # Overtime - archived (use overtime_api_client or overtime_hybrid_scraper)
    # Weather
    "AccuWeatherClient",
    "OpenWeatherClient",
    "WeatherClient",
    "ValidatedWeatherClient",
    # Models
    "League",
    "Conference",
    "Team",
    "Stadium",
    "WeatherConditions",
    "OddsMovement",
    "Game",
    "ActionNetworkResponse",
]

__version__ = "1.0.0"
