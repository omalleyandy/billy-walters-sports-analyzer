"""
NFL.com Scraper Module

Official NFL data collection from NFL.com including
game stats, injuries, scoreboards, and team statistics.

Clients:
    NFLComClient: Main NFL.com API client
    NFLGameStatsClient: Detailed game statistics
    NFLOfficialInjuryScraper: Official injury reports
    NFLScoreboardScraper: Scores and schedules
    NFLStatsScraper: Team and player statistics
"""

from scrapers.nfl_com.client import NFLComClient
from scrapers.nfl_com.game_stats import NFLGameStatsClient
from scrapers.nfl_com.injuries import NFLOfficialInjuryScraper
from scrapers.nfl_com.scoreboard import NFLScoreboardScraper
from scrapers.nfl_com.stats import NFLStatsScraperClient

__all__ = [
    "NFLComClient",
    "NFLGameStatsClient",
    "NFLOfficialInjuryScraper",
    "NFLScoreboardScraper",
    "NFLStatsScraperClient",
]
