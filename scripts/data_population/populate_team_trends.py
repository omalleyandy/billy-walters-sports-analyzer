#!/usr/bin/env python3
"""
Team Trends Population Script

Populates team_trends table with:
- Streak information (last 4-6 games)
- Playoff context (position, ranking, probability)
- Emotional state (confidence, desperation)
- Rest advantage calculation

Data sources: game_results + team_standings (ESPN)

Usage:
    python populate_team_trends.py --league nfl --week 13 --season 2025
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.connection import DatabaseConnection
from src.db.raw_data_operations import RawDataOperations
from src.db.raw_data_models import TeamTrends

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class TeamTrendsPopulator:
    """Populate team_trends table from game results and standings."""

    def __init__(self):
        """Initialize populator with database connection."""
        self.db_conn = DatabaseConnection()
        self.db_ops = RawDataOperations(self.db_conn)

    def get_league_id(self, league: str) -> int:
        """Get league ID from name."""
        query = "SELECT id FROM leagues WHERE name = ?"
        result = self.db_conn.execute_query(query, (league.upper(),))
        if result:
            return result[0]["id"]
        raise ValueError(f"League not found: {league}")

    def get_team_list(self, league_id: int) -> Dict[int, str]:
        """Get all teams for a league."""
        query = "SELECT id, name FROM teams WHERE league_id = ?"
        results = self.db_conn.execute_query(query, (league_id,))
        return {row["id"]: row["name"] for row in results}

    def calculate_streak(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> Tuple[Optional[str], Optional[int], Optional[float]]:
        """
        Calculate team streak from recent game results.

        Returns: (streak_direction, streak_length, recent_form_pct)
        """
        # Query last 6 games for the team
        query = """
            SELECT
                CASE
                    WHEN away_team_id = ? AND away_ats = 1 THEN 'W'
                    WHEN home_team_id = ? AND home_ats = 1 THEN 'W'
                    ELSE 'L'
                END as result
            FROM game_results
            WHERE league_id = ? AND (away_team_id = ? OR home_team_id = ?)
            ORDER BY collected_at DESC
            LIMIT 6
        """
        results = self.db_conn.execute_query(
            query, (team_id, team_id, league_id, team_id, team_id)
        )

        if not results:
            return None, None, None

        results_list = [row["result"] for row in results]

        # Calculate streak
        streak_direction = results_list[0]  # W or L
        streak_length = 1
        for result in results_list[1:]:
            if result == streak_direction:
                streak_length += 1
            else:
                break

        # Calculate recent form percentage
        wins = sum(1 for r in results_list if r == "W")
        recent_form_pct = wins / len(results_list) if results_list else 0.0

        return streak_direction, streak_length, recent_form_pct

    def get_standings_data(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Get playoff position and divisional/conference ranking.

        Returns: (playoff_position, divisional_rank, conference_rank)
        """
        # Query latest standings for this team
        query = """
            SELECT playoff_position, division_rank, conference_rank
            FROM team_standings
            WHERE league_id = ? AND team_id = ? AND season = ?
            ORDER BY week DESC
            LIMIT 1
        """
        results = self.db_conn.execute_query(
            query, (league_id, team_id, season)
        )

        if not results:
            return None, None, None

        row = results[0]
        return (
            row.get("playoff_position"),
            row.get("division_rank"),
            row.get("conference_rank"),
        )

    def calculate_desperation_level(
        self, playoff_position: Optional[int], wins: int, losses: int
    ) -> int:
        """
        Calculate desperation level (0-10 scale).

        0 = clinched playoff spot or eliminated
        10 = must-win scenario (last week, playoff edge)

        Args:
            playoff_position: Current playoff position (1=first, 16=last)
            wins: Team wins
            losses: Team losses

        Returns:
            Desperation level 0-10
        """
        if playoff_position is None:
            return 5  # Unknown, use middle

        # Playoff locked in (positions 1-6 in NFL)
        if playoff_position <= 6:
            return 0  # Clinched, low desperation

        # Playoff edge (positions 7-12)
        if 7 <= playoff_position <= 12:
            return 5  # Moderate desperation

        # Out of playoff picture (13+)
        return 2  # Likely eliminated, playing for pride

    def calculate_emotional_state(
        self, streak_direction: Optional[str], streak_length: Optional[int]
    ) -> str:
        """
        Determine emotional state from streak.

        Args:
            streak_direction: 'W' or 'L'
            streak_length: Number of consecutive wins/losses

        Returns:
            Emotional state: 'confident', 'neutral', 'desperate'
        """
        if streak_direction is None:
            return "neutral"

        if streak_direction == "W":
            if streak_length and streak_length >= 3:
                return "confident"
            else:
                return "neutral"
        else:  # Loss streak
            if streak_length and streak_length >= 3:
                return "desperate"
            else:
                return "neutral"

    def calculate_rest_advantage(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> Optional[float]:
        """
        Calculate rest advantage from days between games.

        Returns: rest_advantage (0.0 = equal, 0.5 = significant advantage)
        """
        # Typical rest is 6-7 days between games
        # Thursday games = 3 days rest (disadvantage)
        # Monday games = 10+ days (advantage)
        # Standard = 7 days (neutral = 0.0)

        # For now, return neutral (would require game schedule)
        return 0.0

    def populate_week(self, league: str, season: int, week: int) -> None:
        """Populate team_trends for a specific week."""
        logger.info(
            f"Populating team trends for {league.upper()} Season {season}, "
            f"Week {week}"
        )

        league_id = self.get_league_id(league)
        teams = self.get_team_list(league_id)

        inserted = 0
        errors = 0

        for team_id, team_name in teams.items():
            try:
                # Calculate all metrics
                (
                    streak_direction,
                    streak_length,
                    recent_form_pct,
                ) = self.calculate_streak(league_id, team_id, season, week)

                (
                    playoff_position,
                    divisional_rank,
                    conference_rank,
                ) = self.get_standings_data(league_id, team_id, season, week)

                desperation_level = self.calculate_desperation_level(
                    playoff_position, 0, 0  # Would need actual win/loss counts
                )

                emotional_state = self.calculate_emotional_state(
                    streak_direction, streak_length
                )

                rest_advantage = self.calculate_rest_advantage(
                    league_id, team_id, season, week
                )

                # Create TeamTrends model
                streak_str = (
                    f"{streak_direction}{streak_length}"
                    if streak_length
                    else "?unknown"
                )
                trends = TeamTrends(
                    league_id=league_id,
                    team_id=team_id,
                    season=season,
                    week=week,
                    streak_direction=streak_direction,
                    streak_length=streak_length,
                    recent_form_pct=recent_form_pct,
                    playoff_position=playoff_position,
                    divisional_rank=divisional_rank,
                    conference_rank=conference_rank,
                    emotional_state=emotional_state,
                    desperation_level=desperation_level,
                    rest_advantage=rest_advantage,
                    source="game_results_standings",
                    notes=f"{streak_str} streak, {emotional_state.title()} "
                    f"mode",
                )

                # Insert to database
                self.db_ops.insert_team_trends(trends)
                inserted += 1

                logger.info(
                    f"  {team_name}: {streak_direction}{streak_length} streak, "
                    f"{emotional_state}, desp={desperation_level}"
                )

            except Exception as e:
                logger.error(
                    f"  Error processing {team_name} (ID {team_id}): {e}"
                )
                errors += 1

        logger.info(
            f"Completed: {inserted} teams updated, {errors} errors"
        )

    def populate_all_weeks(self, league: str, season: int) -> None:
        """Populate team_trends for all weeks in a season."""
        max_weeks = 17 if league.lower() == "nfl" else 15

        for week in range(1, max_weeks + 1):
            try:
                self.populate_week(league, season, week)
            except Exception as e:
                logger.error(f"Error processing week {week}: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Populate team_trends table from game results and standings"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="nfl",
        help="League (nfl or ncaaf)",
    )
    parser.add_argument(
        "--season", type=int, default=2025, help="Season (default 2025)"
    )
    parser.add_argument(
        "--week", type=int, help="Week to populate (if not specified, do all weeks)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    populator = TeamTrendsPopulator()

    if args.week:
        populator.populate_week(args.league, args.season, args.week)
    else:
        populator.populate_all_weeks(args.league, args.season)

    logger.info("Team trends population complete!")


if __name__ == "__main__":
    main()
