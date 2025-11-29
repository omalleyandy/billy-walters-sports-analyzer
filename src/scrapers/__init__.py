"""
Billy Walters Sports Analyzer - Web Scrapers Package

Centralized web scraping infrastructure for collecting sports betting data.
Each submodule handles a specific data source.

Modules:
    action_network: Sharp money signals and betting percentages
    espn: Team stats, schedules, injuries, news
    overtime: Pregame odds via direct API
    nfl_com: Official NFL data
    massey: Power ratings
    weather: Game-day weather conditions
"""

import sys
from pathlib import Path

# Ensure project root is in path for absolute imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scrapers.action_network import ActionNetworkScraper
from scrapers.espn import ESPNClient
from scrapers.massey import MasseyRatingsScraper
from scrapers.nfl_com import NFLComClient
from scrapers.overtime import OvertimeApiClient
from scrapers.weather import AccuWeatherClient, OpenWeatherClient, WeatherClient

__all__ = [
    # Action Network
    "ActionNetworkScraper",
    # ESPN
    "ESPNClient",
    # Massey Ratings
    "MasseyRatingsScraper",
    # NFL.com
    "NFLComClient",
    # Overtime.ag
    "OvertimeApiClient",
    # Weather
    "AccuWeatherClient",
    "OpenWeatherClient",
    "WeatherClient",
]

__version__ = "1.0.0"
