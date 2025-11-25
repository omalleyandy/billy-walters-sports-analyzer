#!/usr/bin/env python3
"""
Game ID Mapper - Maps between different game ID systems

Handles mapping between:
- Overtime.ag game IDs (114570440, etc.)
- ESPN game IDs (401772891, etc.)
- Custom Billy Walters IDs (team_team_team_2025_W13, etc.)

Uses team names and game dates to perform fuzzy matching.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.connection import get_db_connection


class GameIDMapper:
    """Maps game IDs between different systems."""

    def __init__(self):
        """Initialize mapper with database connection."""
        self.db = get_db_connection()
        self._espn_schedule_cache: Dict[str, str] = {}
        self._load_espn_schedules()

    def _load_espn_schedules(self) -> None:
        """Load all ESPN schedules into cache for fast lookup."""
        result = self.db.execute_query(
            """
            SELECT game_id, home_team, away_team, game_date, season, week
            FROM espn_schedules
            WHERE season = 2025
            ORDER BY game_date DESC
            """
        )

        for row in result:
            game_id, home_team, away_team, game_date, season, week = row
            # Create cache keys for lookup
            key = self._make_cache_key(home_team, away_team, game_date)
            self._espn_schedule_cache[key] = game_id

    def _make_cache_key(
        self, home_team: str, away_team: str, game_date
    ) -> str:
        """Create normalized cache key from team names and date."""
        # Normalize team names (strip, lowercase for comparison)
        home = home_team.strip().lower()
        away = away_team.strip().lower()

        # Extract date if it's a timestamp
        if hasattr(game_date, "date"):
            date_str = game_date.date().isoformat()
        else:
            date_str = str(game_date)[:10]

        return f"{home}|{away}|{date_str}"

    def map_overtime_to_espn(
        self,
        overtime_game_id: str,
        home_team: str,
        away_team: str,
        game_date,
    ) -> Optional[str]:
        """
        Map Overtime.ag game ID to ESPN game ID.

        Args:
            overtime_game_id: Overtime.ag game ID (e.g., "114570440")
            home_team: Home team name
            away_team: Away team name
            game_date: Game date (datetime or string)

        Returns:
            ESPN game ID if found, None otherwise
        """
        # Try exact match first
        key = self._make_cache_key(home_team, away_team, game_date)
        if key in self._espn_schedule_cache:
            return self._espn_schedule_cache[key]

        # If not found in cache, try fuzzy match with date tolerance
        # (accounts for time zone differences)
        try:
            result = self.find_game_by_teams_and_date(
                home_team,
                away_team,
                game_date,
                tolerance_days=2
            )

            if result:
                # Cache for future lookups
                self._espn_schedule_cache[key] = result
                return result

        except Exception as e:
            print(
                f"[WARNING] Mapping error for {home_team} vs "
                f"{away_team}: {e}"
            )

        return None

    def get_stadium_from_city(self, city: str) -> Optional[str]:
        """
        Get stadium location from city name.

        Args:
            city: City name (e.g., "San Francisco, CA")

        Returns:
            Stadium name/location if found
        """
        try:
            result = self.db.execute_query(
                """
                SELECT stadium FROM espn_schedules
                WHERE (city ILIKE %s OR stadium ILIKE %s)
                AND season = 2025
                LIMIT 1
                """,
                (f"%{city}%", f"%{city}%"),
            )

            if result:
                return result[0][0]

        except Exception as e:
            print(f"[WARNING] Stadium lookup error for {city}: {e}")

        return city  # Return original if no match

    def find_game_by_teams_and_date(
        self,
        home_team: str,
        away_team: str,
        game_date,
        tolerance_days: int = 1,
    ) -> Optional[str]:
        """
        Find ESPN game ID by team names and approximate date.

        Args:
            home_team: Home team name
            away_team: Away team name
            game_date: Expected game date
            tolerance_days: Allow +/- N days for date matching

        Returns:
            ESPN game ID if found
        """
        try:
            # Parse date if needed
            if isinstance(game_date, str):
                game_date = datetime.fromisoformat(game_date)

            # Search within tolerance window
            result = self.db.execute_query(
                """
                SELECT game_id, game_date FROM espn_schedules
                WHERE season = 2025
                AND LOWER(home_team) = LOWER(%s)
                AND LOWER(away_team) = LOWER(%s)
                AND game_date >= %s - INTERVAL '%s days'
                AND game_date <= %s + INTERVAL '%s days'
                ORDER BY ABS(EXTRACT(EPOCH FROM (game_date - %s)))
                LIMIT 1
                """,
                (
                    home_team,
                    away_team,
                    game_date,
                    tolerance_days,
                    game_date,
                    tolerance_days,
                    game_date,
                ),
            )

            if result:
                return result[0][0]

        except Exception as e:
            print(
                f"[WARNING] Date-based mapping error: {home_team} vs "
                f"{away_team}: {e}"
            )

        return None

    def populate_games_table(
        self, season: int = 2025, week: int = 13, league: str = "NFL"
    ) -> int:
        """
        Populate games table from espn_schedules for a specific week.

        Args:
            season: Season year
            week: Week number
            league: League ('NFL' or 'NCAAF')

        Returns:
            Number of games inserted
        """
        count = 0
        try:
            # Get schedules for this week
            schedules = self.db.execute_query(
                """
                SELECT game_id, season, week, league, home_team, away_team,
                       game_date
                FROM espn_schedules
                WHERE season = %s AND week = %s AND league = %s
                """,
                (season, week, league),
            )

            print(
                f"[INFO] Found {len(schedules)} {league} schedules to copy "
                f"to games table"
            )

            for row in schedules:
                try:
                    (game_id, season, week, league, home_team,
                     away_team, game_date) = row

                    # Insert into games table
                    self.db.execute_query(
                        """
                        INSERT INTO games
                        (game_id, season, week, league, home_team,
                         away_team, game_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (game_id, season, week, league, home_team,
                         away_team, game_date),
                        fetch=False,
                    )
                    count += 1

                except Exception as e:
                    # Likely duplicate, continue
                    continue

            print(f"[OK] Inserted {count} games into games table")
            return count

        except Exception as e:
            print(f"[ERROR] Failed to populate games table: {e}")
            return 0

    def close(self) -> None:
        """Close database connection."""
        self.db.close_all_connections()


if __name__ == "__main__":
    # Test the mapper
    mapper = GameIDMapper()

    print("=" * 70)
    print("GAME ID MAPPER TEST")
    print("=" * 70)

    # Test schedule cache
    print(f"\n[INFO] Loaded {len(mapper._espn_schedule_cache)} games in cache")

    # Test populate games table
    print("\n[TEST] Populating games table for Week 13...")
    inserted = mapper.populate_games_table(season=2025, week=13)
    print(f"Result: {inserted} games inserted/updated")

    # Test mapping
    print(
        "\n[TEST] Testing game_id mapping (Overtime -> ESPN)..."
    )
    # This would require actual Overtime game data to test

    mapper.close()
