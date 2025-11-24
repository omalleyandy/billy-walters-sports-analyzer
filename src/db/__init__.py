"""
Billy Walters Sports Analytics Database Package

Provides database connection, models, and CRUD operations
for PostgreSQL-based sports betting analytics.
"""

from .connection import DatabaseConnection, get_db_connection
from .models import (
    Game,
    PowerRating,
    Odds,
    Bet,
    Weather,
    Injury,
    SituationalFactors,
    PerformanceMetrics,
)
from .operations import DatabaseOperations

__all__ = [
    "DatabaseConnection",
    "get_db_connection",
    "DatabaseOperations",
    "Game",
    "PowerRating",
    "Odds",
    "Bet",
    "Weather",
    "Injury",
    "SituationalFactors",
    "PerformanceMetrics",
]
