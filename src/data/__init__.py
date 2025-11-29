"""
Billy Walters Sports Analyzer - Data Integration Package

This package provides backwards compatibility re-exports from the new
src.scrapers package. New code should import directly from scrapers.

Example:
    # Old (still works for backwards compatibility):
    from src.data import ESPNClient

    # New (preferred):
    from scrapers.espn import ESPNClient
"""

import sys
from pathlib import Path

# Ensure project root is in path for absolute imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Re-export scrapers from new locations for backwards compatibility
from scrapers.action_network import ActionNetworkScraper
from scrapers.espn import ESPNClient
from scrapers.massey import MasseyRatingsScraper
from scrapers.nfl_com import NFLComClient
from scrapers.overtime import OvertimeApiClient
from scrapers.weather import AccuWeatherClient, OpenWeatherClient, WeatherClient

# Local validators and utilities
from .validated_action_network import ValidatedActionNetworkClient
from .validated_weather import ValidatedWeatherClient

# Data models
from .models import (
    ActionNetworkResponse,
    Conference,
    Game,
    League,
    OddsMovement,
    Stadium,
    Team,
    WeatherConditions,
)

# Backwards compatibility alias
ActionNetworkClient = ActionNetworkScraper

__all__ = [
    # Scrapers (re-exported from src.scrapers)
    "ESPNClient",
    "ActionNetworkScraper",
    "ActionNetworkClient",  # Backwards compat alias
    "MasseyRatingsScraper",
    "NFLComClient",
    "OvertimeApiClient",
    "AccuWeatherClient",
    "OpenWeatherClient",
    "WeatherClient",
    # Validators
    "ValidatedActionNetworkClient",
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
