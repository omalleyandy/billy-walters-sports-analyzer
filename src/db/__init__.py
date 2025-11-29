"""
Billy Walters Sports Analytics Database Package

Provides database connection, models, and CRUD operations
for SQLite-based sports betting analytics.
"""

from .connection import DatabaseConnection, get_db_connection, close_db_connection
from .models import (
    League,
    Team,
    Game,
    Edge,
    CLVPlay,
    EdgeSession,
    CLVSession,
    PowerRating,
    Odds,
    Bet,
    Weather,
    Injury,
    SituationalFactors,
    PerformanceMetrics,
)
from .operations import DatabaseOperations
from .raw_data_models import (
    GameSchedule,
    GameResult,
    TeamStats,
    PlayerStats,
    TeamStandings,
    BettingOdds,
    SharpMoneySignal,
    WeatherData,
    InjuryReport,
    NewsArticle,
    CollectionSession,
    PlayerValuation,
    PracticeReport,
    GameSWEFactors,
    TeamTrends,
)
from .raw_data_operations import RawDataOperations

__all__ = [
    "DatabaseConnection",
    "get_db_connection",
    "close_db_connection",
    "DatabaseOperations",
    "RawDataOperations",
    # SQLite-based models
    "League",
    "Team",
    "Game",
    "Edge",
    "CLVPlay",
    "EdgeSession",
    "CLVSession",
    # Raw data models
    "GameSchedule",
    "GameResult",
    "TeamStats",
    "PlayerStats",
    "TeamStandings",
    "PowerRating",
    "BettingOdds",
    "SharpMoneySignal",
    "WeatherData",
    "InjuryReport",
    "NewsArticle",
    "CollectionSession",
    # TIER 1 Critical tables
    "PlayerValuation",
    "PracticeReport",
    "GameSWEFactors",
    "TeamTrends",
    # Legacy models
    "Odds",
    "Bet",
    "Weather",
    "Injury",
    "SituationalFactors",
    "PerformanceMetrics",
]
