"""
API Clients Package for Billy Walters Sports Analyzer
Superior API implementations for reliable data collection
"""

# Direct API clients (no scraping needed)
from .overtime_api_client import OvertimeApiClient
# from .overtime_data_converter import OvertimeToWaltersConverter  # SKIP FOR NOW
from .overtime_signalr_client import OvertimeSignalRClient

# ESPN API clients
from .espn_client import ESPNClient
from .espn_ncaaf_scoreboard_client import ESPNNCAAFScoreboardClient

# Weather API clients
from .accuweather_client import AccuWeatherClient
from .openweather_client import OpenWeatherClient

# Action Network scraper
from .action_network_client import ActionNetworkClient

__all__ = [
    'OvertimeApiClient',
    'OvertimeSignalRClient',
    'ESPNClient',
    'ESPNNCAAFScoreboardClient',
    'AccuWeatherClient',
    'OpenWeatherClient',
    'ActionNetworkClient'
]

print("[OK] Superior API clients loaded successfully")
