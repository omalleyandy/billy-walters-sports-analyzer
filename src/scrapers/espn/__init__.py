"""
ESPN Scraper Module

Comprehensive ESPN data collection for NFL and NCAAF including
team stats, schedules, injuries, news, and transactions.

Clients:
    ESPNClient: Main client with retry logic and rate limiting
    ESPNNFLScoreboardClient: NFL scores and schedules
    ESPNNCAAFScoreboardClient: NCAAF scores and schedules
    ESPNInjuryScraper: Player injury reports
    ESPNNewsClient: News articles
    ESPNPlayerStatsClient: Player statistics
    ESPNTransactionsClient: NFL trades and signings
    ESPNNCAAFTransactionsClient: Transfer portal activity
    ESPNNCAAFTeamScraper: NCAAF team rosters
    ESPNNCAAFNewsClient: NCAAF-specific news
    ESPNNCAAFNormalizer: Team name normalization
"""

from scrapers.espn.client import ESPNClient
from scrapers.espn.injuries import ESPNInjuryScraper
from scrapers.espn.ncaaf_news import ESPNNCAAFNewsClient
from scrapers.espn.ncaaf_normalizer import ESPNNCAAFNormalizer
from scrapers.espn.ncaaf_scoreboard import ESPNNCAAFScoreboardClient
from scrapers.espn.ncaaf_team import ESPNNcaafTeamScraper
from scrapers.espn.ncaaf_transactions import ESPNNCAAFTransactionsClient
from scrapers.espn.news import ESPNNewsClient
from scrapers.espn.nfl_scoreboard import ESPNNFLScoreboardClient
from scrapers.espn.player_stats import ESPNPlayerStatsClient
from scrapers.espn.transactions import ESPNTransactionsClient

__all__ = [
    "ESPNClient",
    "ESPNNFLScoreboardClient",
    "ESPNNCAAFScoreboardClient",
    "ESPNInjuryScraper",
    "ESPNNewsClient",
    "ESPNPlayerStatsClient",
    "ESPNTransactionsClient",
    "ESPNNCAAFTransactionsClient",
    "ESPNNcaafTeamScraper",
    "ESPNNCAAFNewsClient",
    "ESPNNCAAFNormalizer",
]
