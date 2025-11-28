"""Data integration module for Billy Walters analyzer.

Handles integration of external data sources (news feeds, injury reports, etc.)
into the edge detection and E-Factor calculation pipeline.
"""

from walters_analyzer.data_integration.news_feed_aggregator import (
    FeedConfig,
    FeedHealthReport,
    FeedItem,
    League,
    NewsFeedAggregator,
    NewsCategory,
)
from walters_analyzer.data_integration.news_injury_mapper import (
    EFactorInputs,
    InjuryData,
    NewsInjuryMapper,
    PlayerTier,
    Position,
)

__all__ = [
    "NewsFeedAggregator",
    "FeedConfig",
    "FeedItem",
    "FeedHealthReport",
    "NewsCategory",
    "League",
    "NewsInjuryMapper",
    "EFactorInputs",
    "InjuryData",
    "Position",
    "PlayerTier",
]
