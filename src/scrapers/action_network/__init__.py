"""
Action Network Scraper Module

Extracts betting odds, betting percentages, and sharp money signals
from Action Network for NFL and NCAAF.

Key Features:
    - Extracts __NEXT_DATA__ for structured JSON data
    - League-specific divergence thresholds (NFL vs NCAAF)
    - Sharp money detection with signal strength classification
    - Line movement tracking from opening spreads
    - CloudFlare bypass with stealth browser settings
"""

from scrapers.action_network.scraper import (
    ActionNetworkScraper,
    BettingPercentages,
    GameOdds,
    MoneylineLine,
    SpreadLine,
    TotalLine,
)

__all__ = [
    "ActionNetworkScraper",
    "GameOdds",
    "SpreadLine",
    "MoneylineLine",
    "TotalLine",
    "BettingPercentages",
]
