#!/usr/bin/env python3
"""
Player Valuations Baseline Population Script

Populates player_valuations table with baseline point spread impact values
based on position and depth chart position.

Uses existing PlayerValuation.calculate_player_value() logic to assign
baseline tier values.

Phase 1: Baseline from depth chart position
- Starters (position 1) → elite/above_average tier
- Backups (position 2) → average/backup tier
- Calculate point_value from position tier
- Set snap_count_pct = 100 (will be updated weekly in Phase 2)

Phase 2 (Future): Update snap counts weekly from ESPN/PFF

Usage:
    python populate_player_valuations_baseline.py --league nfl --season 2025
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.connection import DatabaseConnection  # noqa: E402
from src.db.raw_data_operations import RawDataOperations  # noqa: E402
from src.db.raw_data_models import PlayerValuation  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class PlayerValuationsBaselinePopulator:
    """Populate player_valuations with baseline point values."""

    # Default point values by position (elite tier)
    POSITION_DEFAULTS = {
        "QB": {"elite": 4.5, "above_average": 3.5, "average": 2.5},
        "RB": {"elite": 2.0, "above_average": 1.8, "average": 1.2},
        "WR": {"elite": 1.5, "above_average": 1.2, "average": 0.8},
        "TE": {"elite": 1.5, "above_average": 1.2, "average": 0.8},
        "OL": {"elite": 1.0, "above_average": 0.8, "average": 0.5},
        "DL": {"elite": 1.2, "above_average": 1.0, "average": 0.6},
        "LB": {"elite": 1.0, "above_average": 0.8, "average": 0.5},
        "DB": {"elite": 0.8, "above_average": 0.6, "average": 0.4},
        "K": {"elite": 1.0, "above_average": 0.8, "average": 0.5},
        "P": {"elite": 0.8, "above_average": 0.6, "average": 0.4},
    }

    # Depth chart position mapping
    DEPTH_CHART_TIERS = {
        1: "elite",  # Starter
        2: "above_average",  # Backup
        3: "average",  # Third string
    }

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

    def get_teams(self, league_id: int) -> list:
        """Get all teams for a league."""
        query = "SELECT id, name FROM teams WHERE league_id = ?"
        results = self.db_conn.execute_query(query, (league_id,))
        return [dict(row) for row in results] if results else []

    def get_point_value(
        self, position: Optional[str], depth_position: Optional[int]
    ) -> float:
        """
        Get baseline point value for a player.

        Args:
            position: Player position (QB, RB, WR, etc.)
            depth_position: Depth chart position (1, 2, 3, etc.)

        Returns:
            Point value (0.4 to 4.5)
        """
        if not position:
            return 1.0  # Unknown position

        position_upper = position.upper()

        if position_upper not in self.POSITION_DEFAULTS:
            return 1.0  # Unknown position

        # Determine tier from depth position
        tier = self.DEPTH_CHART_TIERS.get(depth_position, "average")

        # Get value from tier
        values = self.POSITION_DEFAULTS[position_upper]
        return values.get(tier, 1.0)

    def load_mock_roster(self, season: int) -> Dict:
        """
        Load mock player roster for testing.

        In production, this would load from ESPN depth charts.

        Returns:
            Dictionary with teams and player lists
        """
        return {
            "teams": [
                {
                    "name": "Kansas City Chiefs",
                    "players": [
                        {
                            "name": "Patrick Mahomes",
                            "position": "QB",
                            "depth_position": 1,
                        },
                        {
                            "name": "Isiah Pacheco",
                            "position": "RB",
                            "depth_position": 1,
                        },
                        {
                            "name": "JuJu Smith-Schuster",
                            "position": "WR",
                            "depth_position": 1,
                        },
                    ],
                }
            ]
        }

    def populate_season(self, league: str, season: int) -> None:
        """
        Populate baseline player valuations for a season.

        Args:
            league: League name (nfl/ncaaf)
            season: Season year
        """
        logger.info(
            f"Populating baseline player valuations for {league.upper()} {season}"
        )

        league_id = self.get_league_id(league)
        teams = self.get_teams(league_id)

        if not teams:
            logger.warning("No teams found in database")
            return

        # Load roster (mock for now)
        roster_data = self.load_mock_roster(season)

        total_inserted = 0
        teams_processed = 0

        for team_info in teams:
            team_id = team_info["id"]
            team_name = team_info["name"]

            try:
                # Find team roster data
                team_roster = None
                for team_data in roster_data.get("teams", []):
                    if team_data["name"] == team_name:
                        team_roster = team_data
                        break

                if not team_roster:
                    logger.debug(f"No roster data found for {team_name}")
                    continue

                # Process each player
                for player_data in team_roster.get("players", []):
                    player_name = player_data.get("name")
                    position = player_data.get("position")
                    depth_position = player_data.get("depth_position", 1)

                    # Calculate point value
                    point_value = self.get_point_value(position, depth_position)

                    # Create player valuation
                    valuation = PlayerValuation(
                        league_id=league_id,
                        team_id=team_id,
                        player_id=None,  # Would be scraped from ESPN
                        player_name=player_name,
                        position=position,
                        season=season,
                        week=None,  # Baseline applies all weeks
                        point_value=point_value,
                        snap_count_pct=100.0,  # Baseline assumption
                        impact_rating=point_value,
                        is_starter=(depth_position == 1),
                        depth_chart_position=depth_position,
                        source="depth_chart_baseline",
                        notes=f"Baseline from {depth_position} depth chart position",
                    )

                    # Insert to database
                    self.db_ops.insert_player_valuation(valuation)
                    total_inserted += 1

                teams_processed += 1
                logger.info(
                    f"  {team_name}: {len(team_roster.get('players', []))} players"
                )

            except Exception as e:
                logger.error(f"Error processing {team_name} (ID {team_id}): {e}")

        logger.info(
            f"Completed: {teams_processed} teams, {total_inserted} players inserted"
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Populate baseline player valuations")
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
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    populator = PlayerValuationsBaselinePopulator()
    populator.populate_season(args.league, args.season)

    logger.info("Player valuations baseline population complete!")


if __name__ == "__main__":
    main()
