"""Unified research coordinator that integrates multiple data sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .accuweather_client import AccuWeatherClient
from .profootballdoc_fetcher import ProFootballDocFetcher

logger = logging.getLogger(__name__)


@dataclass
class ResearchSnapshot:
    """Consolidated research data for a game."""

    home_team: str
    away_team: str
    home_injuries: List[Dict[str, Any]] = field(default_factory=list)
    away_injuries: List[Dict[str, Any]] = field(default_factory=list)
    weather: Optional[Dict[str, Any]] = None
    odds_history: List[Dict[str, Any]] = field(default_factory=list)
    sharp_money_indicator: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ResearchEngine:
    """Coordinates data collection from multiple sources with caching."""

    def __init__(
        self,
        accuweather: Optional[AccuWeatherClient] = None,
        profootballdoc: Optional[ProFootballDocFetcher] = None,
        cache_ttl_seconds: int = 300,
    ) -> None:
        """
        Initialize research engine with optional client overrides.

        Args:
            accuweather: Weather data client
            profootballdoc: Injury report client
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.accuweather = accuweather or AccuWeatherClient()
        self.profootballdoc = profootballdoc or ProFootballDocFetcher()
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, tuple[ResearchSnapshot, datetime]] = {}

    async def gather_for_game(
        self,
        home_team: str,
        away_team: str,
        venue: Optional[str] = None,
        date: Optional[datetime] = None,
        use_cache: bool = True,
    ) -> ResearchSnapshot:
        """
        Gather all research data for a specific game.

        Args:
            home_team: Home team name
            away_team: Away team name
            venue: Stadium/venue name for weather lookup
            date: Game date
            use_cache: Whether to use cached data

        Returns:
            ResearchSnapshot with all available data
        """
        cache_key = f"{home_team}:{away_team}:{date}"

        # Check cache
        if use_cache and cache_key in self._cache:
            cached_snapshot, cached_time = self._cache[cache_key]
            age = (datetime.now() - cached_time).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Using cached research data (age: {age:.1f}s)")
                return cached_snapshot

        # Gather fresh data
        snapshot = ResearchSnapshot(home_team=home_team, away_team=away_team)

        # Fetch injury reports
        try:
            home_injuries = await self.profootballdoc.get_team_injuries(home_team)
            away_injuries = await self.profootballdoc.get_team_injuries(away_team)
            snapshot.home_injuries = home_injuries
            snapshot.away_injuries = away_injuries
            logger.info(
                f"Fetched injuries: {len(home_injuries)} home, {len(away_injuries)} away"
            )
        except Exception as e:
            logger.error(f"Failed to fetch injury data: {e}", exc_info=True)

        # Fetch weather if venue provided
        if venue:
            try:
                weather_data = await self.accuweather.get_game_weather(venue, date)
                snapshot.weather = weather_data
                logger.info(f"Fetched weather for {venue}")
            except Exception as e:
                logger.error(f"Failed to fetch weather: {e}", exc_info=True)

        # Cache and return
        self._cache[cache_key] = (snapshot, datetime.now())
        return snapshot

    def clear_cache(self) -> None:
        """Clear the research data cache."""
        self._cache.clear()
        logger.info("Research cache cleared")

    async def close(self) -> None:
        """Close all client connections."""
        try:
            await self.accuweather.close()
            await self.profootballdoc.close()
        except Exception as e:
            logger.error(f"Error closing research clients: {e}", exc_info=True)
