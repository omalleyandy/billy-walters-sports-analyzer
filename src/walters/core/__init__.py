"""
Core Billy Walters analysis components.

This module contains the foundational components:
- HTTP client with connection pooling
- Caching system
- Data models
- Core calculation engines

Usage:
    # Import modules
    from walters.core import http_client, cache, models

    # Import specific functions
    from walters.core.http_client import async_get, async_post
    from walters.core.cache import cache_weather_data, cache_injury_data
    from walters.core.models import TeamRating, BetRecommendation
"""

# Export modules
__all__ = ['http_client', 'cache', 'models']

# Also export commonly used items for convenience
from .models import (
    BetType,
    TeamRating,
    GameResult,
    GameContext,
    InjuryReport,
    KeyNumberAnalysis,
    BetRecommendation,
    ComprehensiveAnalysis,
)

from .http_client import (
    async_get,
    async_post,
    cleanup_http_client,
)

from .cache import (
    cache_result,
    cache_weather_data,
    cache_injury_data,
    cache_analysis_result,
    cache_odds_data,
    clear_cache,
    get_cache_stats,
)
