"""
News & Injury E-Factor Aggregator

Combines news feed items and injury data into unified E-Factor parameters
for seamless integration into the IntegratedEdgeCalculator.

This aggregator:
1. Fetches news items from NewsFeedAggregator (coaching, transactions, injuries, playoff)
2. Fetches injury data
3. Maps both to EFactorInputs using NewsInjuryMapper
4. Aggregates impacts for easy consumption by edge calculator

Usage:
    aggregator = NewsInjuryEFactorAggregator()
    await aggregator.initialize()

    # Fetch and map for both teams in a game
    home_efactor = await aggregator.get_game_efactor_inputs(
        "DET", "nfl", week=13
    )
    away_efactor = await aggregator.get_game_efactor_inputs(
        "GB", "nfl", week=13
    )

    print(f"Home team impact: {home_efactor.key_player_impact:.1f}pts")
    print(f"Away team impact: {away_efactor.key_player_impact:.1f}pts")

    await aggregator.close()
"""

import asyncio
import logging
from typing import Dict, List, Optional

from walters_analyzer.data_integration.news_feed_aggregator import (
    League,
    NewsFeedAggregator,
)
from walters_analyzer.data_integration.news_injury_mapper import (
    EFactorInputs,
    InjuryData,
    NewsInjuryMapper,
)

logger = logging.getLogger(__name__)


class NewsInjuryEFactorAggregator:
    """
    Aggregates news and injury data into E-Factor parameters.

    Provides unified interface for edge calculator to get E-Factor inputs
    for both teams in a game.
    """

    def __init__(self):
        """Initialize aggregator."""
        self.news_aggregator = NewsFeedAggregator()
        self.mapper = NewsInjuryMapper()
        self.injury_cache: Dict[str, List[InjuryData]] = {}
        self.news_cache: Dict[str, Dict] = {}

    async def initialize(self) -> None:
        """Initialize news aggregator and load feeds."""
        await self.news_aggregator.initialize()
        logger.info("NewsInjuryEFactorAggregator initialized")

    async def close(self) -> None:
        """Close news aggregator."""
        await self.news_aggregator.close()
        logger.info("NewsInjuryEFactorAggregator closed")

    async def get_game_efactor_inputs(
        self, team: str, league: str, week: Optional[int] = None
    ) -> EFactorInputs:
        """
        Get E-Factor inputs for a team in a given week.

        Args:
            team: Team abbreviation (e.g., "DAL")
            league: League ("nfl" or "ncaaf")
            week: Week number (optional, for context)

        Returns:
            EFactorInputs with all applicable parameters set
        """
        # Determine league enum
        league_enum = League.NFL if league.lower() == "nfl" else League.NCAAF

        # Fetch and categorize news items
        all_items = await self.news_aggregator.fetch_league_news(
            league_enum, validate=True
        )

        # Filter for team-specific news
        team_news = self._filter_team_news(all_items, team)

        # Fetch injury data (would be populated from actual data source)
        injuries = self.injury_cache.get(f"{team}_{league}", [])

        # Map news to E-Factor parameters
        news_efactor = self.mapper.map_news_to_efactor(team_news, team)

        # Map injuries to E-Factor parameters
        injury_efactor = self.mapper.map_injuries_to_efactor(injuries, team)

        # Merge mappings into EFactorInputs
        efactor_inputs = self._merge_efactor_data(news_efactor, injury_efactor)

        logger.info(
            f"E-Factor inputs for {team} ({league}, week {week}): "
            f"key_player_impact={efactor_inputs.key_player_impact:.1f}, "
            f"coaching_change={efactor_inputs.coaching_change_this_week}"
        )

        return efactor_inputs

    def _filter_team_news(self, items, team: str) -> List:
        """
        Filter news items for specific team.

        Args:
            items: All news items
            team: Team abbreviation

        Returns:
            Filtered items relevant to team
        """
        team_lower = team.lower()
        filtered = []

        for item in items:
            # Check title and summary for team mentions
            combined = f"{item.title} {item.summary}".lower()

            # Simple team name matching (can be expanded with full names)
            if team_lower in combined:
                filtered.append(item)

        return filtered

    def _merge_efactor_data(self, news_data: Dict, injury_data: Dict) -> EFactorInputs:
        """
        Merge news and injury mappings into EFactorInputs.

        Args:
            news_data: Dict from news mapping
            injury_data: Dict from injury mapping

        Returns:
            Unified EFactorInputs object
        """
        # Start with defaults
        efactor = EFactorInputs()

        # Apply news data
        for key, value in news_data.items():
            if hasattr(efactor, key):
                setattr(efactor, key, value)

        # Apply injury data (injury data takes precedence)
        for key, value in injury_data.items():
            if hasattr(efactor, key):
                setattr(efactor, key, value)

        return efactor

    def set_injury_data(
        self, team: str, league: str, injuries: List[InjuryData]
    ) -> None:
        """
        Set injury data for a team.

        Args:
            team: Team abbreviation
            league: League ("nfl" or "ncaaf")
            injuries: List of injury data
        """
        cache_key = f"{team}_{league}"
        self.injury_cache[cache_key] = injuries
        logger.info(f"Set {len(injuries)} injury records for {team} ({league})")

    async def get_games_efactor_inputs(
        self, teams: List[str], league: str, week: Optional[int] = None
    ) -> Dict[str, EFactorInputs]:
        """
        Get E-Factor inputs for multiple teams.

        Args:
            teams: List of team abbreviations
            league: League ("nfl" or "ncaaf")
            week: Week number (optional)

        Returns:
            Dict mapping team -> EFactorInputs
        """
        results = {}

        for team in teams:
            efactor = await self.get_game_efactor_inputs(team, league, week)
            results[team] = efactor

        return results


async def main() -> None:
    """Demo usage."""
    aggregator = NewsInjuryEFactorAggregator()
    await aggregator.initialize()

    # Demo: Set some injury data
    injuries = [
        InjuryData(
            team="DAL",
            position="QB",
            player_name="Dak Prescott",
            injury_type="ankle",
            status="questionable",
            practice_status="limited",
            is_key_player=True,
            tier="star",
        ),
    ]
    aggregator.set_injury_data("DAL", "nfl", injuries)

    # Get E-Factor inputs
    efactor_inputs = await aggregator.get_game_efactor_inputs("DAL", "nfl")

    print("E-Factor Inputs for DAL:")
    print(f"  Key player impact: {efactor_inputs.key_player_impact:.1f}pts")
    print(f"  Position group health: {efactor_inputs.position_group_health:.2f}")
    print(f"  Coaching change: {efactor_inputs.coaching_change_this_week}")
    print(f"  Morale shift: {efactor_inputs.morale_shift:+.2f}")

    await aggregator.close()


if __name__ == "__main__":
    asyncio.run(main())
