#!/usr/bin/env python3
"""
2025 NFL Historical Season Statistics Loader
Loads collected 2025 season game data (weeks 1-18, all games) into PostgreSQL
Follows Billy Walters Analysis Package data structure pattern
"""

import json
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class NFL2025HistoricalLoader:
    """Loads 2025 NFL historical season data into PostgreSQL"""

    def __init__(
        self,
        dbname: str = "sports_db",
        user: str = "postgres",
        password: str = "postgres",
        host: str = "localhost",
        port: int = 5432,
    ):
        """Initialize database connection"""
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None

    def connect(self) -> None:
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            )
            logger.info("[OK] Connected to PostgreSQL")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("[OK] Disconnected from PostgreSQL")

    def load_week_file(self, filepath: Path) -> Dict:
        """Load game data from week JSON file"""
        try:
            with open(filepath) as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return {}

    def insert_game(self, game_data: Dict) -> bool:
        """Insert single game record into database"""
        try:
            cursor = self.conn.cursor()

            # Extract values
            game_id = game_data.get("game_id")
            season = game_data.get("season")
            week = game_data.get("week")
            league = game_data.get("league", "NFL")
            game_date = game_data.get("game_date_iso")
            home_team = game_data.get("home_team")
            away_team = game_data.get("away_team")
            home_score = game_data.get("home_score")
            away_score = game_data.get("away_score")
            final_margin = game_data.get("final_margin")
            total_points = game_data.get("total_points")
            status = game_data.get("status", "SCHEDULED")
            stadium = game_data.get("stadium")
            is_outdoor = game_data.get("is_outdoor")
            is_neutral = False  # NFL games not neutral site (only some international games)

            # Insert or update game
            insert_query = """
                INSERT INTO games (
                    game_id, season, week, league, game_date,
                    home_team, away_team, home_score, away_score,
                    final_margin, total_points, status, stadium,
                    is_outdoor, is_neutral_site
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (game_id)
                DO UPDATE SET
                    game_date = EXCLUDED.game_date,
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    final_margin = EXCLUDED.final_margin,
                    total_points = EXCLUDED.total_points,
                    status = EXCLUDED.status,
                    updated_at = NOW();
            """

            cursor.execute(
                insert_query,
                (
                    game_id,
                    season,
                    week,
                    league,
                    game_date,
                    home_team,
                    away_team,
                    home_score,
                    away_score,
                    final_margin,
                    total_points,
                    status,
                    stadium,
                    is_outdoor,
                    is_neutral,
                ),
            )

            self.conn.commit()
            cursor.close()
            return True

        except psycopg2.Error as e:
            logger.error(f"Failed to insert game {game_id}: {e}")
            self.conn.rollback()
            return False

    def insert_team_stats(self, team_stats: Dict) -> bool:
        """Insert team weekly statistics record into database"""
        try:
            cursor = self.conn.cursor()

            # Extract values
            team_abbr = team_stats.get("team_abbr")
            team_name = team_stats.get("team_name")
            week = team_stats.get("week")
            season = team_stats.get("season")
            points_per_game = team_stats.get("points_per_game")
            total_points = team_stats.get("total_points")
            passing_yards_per_game = team_stats.get("passing_yards_per_game")
            rushing_yards_per_game = team_stats.get("rushing_yards_per_game")
            total_yards_per_game = team_stats.get("total_yards_per_game")
            points_allowed_per_game = team_stats.get("points_allowed_per_game")
            passing_yards_allowed_per_game = team_stats.get(
                "passing_yards_allowed_per_game"
            )
            rushing_yards_allowed_per_game = team_stats.get(
                "rushing_yards_allowed_per_game"
            )
            total_yards_allowed_per_game = team_stats.get("total_yards_allowed_per_game")
            turnover_margin = team_stats.get("turnover_margin")
            third_down_pct = team_stats.get("third_down_pct")
            takeaways = team_stats.get("takeaways")
            giveaways = team_stats.get("giveaways")

            # Check if nfl_team_stats table exists
            # If not, we'll skip this for now (can be added later)
            check_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'nfl_team_stats'
                );
            """

            cursor.execute(check_query)
            table_exists = cursor.fetchone()[0]
            cursor.close()

            if not table_exists:
                # Table doesn't exist yet, skip team stats
                return True

            # Insert into nfl_team_stats
            insert_query = """
                INSERT INTO nfl_team_stats (
                    team_abbr, team_name, week, season_year,
                    points_per_game, total_points,
                    passing_yards_per_game, rushing_yards_per_game,
                    total_yards_per_game, points_allowed_per_game,
                    passing_yards_allowed_per_game,
                    rushing_yards_allowed_per_game,
                    total_yards_allowed_per_game, turnover_margin,
                    third_down_pct, takeaways, giveaways
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (team_abbr, week, season_year)
                DO UPDATE SET
                    points_per_game = EXCLUDED.points_per_game,
                    total_points = EXCLUDED.total_points,
                    passing_yards_per_game =
                        EXCLUDED.passing_yards_per_game,
                    rushing_yards_per_game =
                        EXCLUDED.rushing_yards_per_game,
                    total_yards_per_game =
                        EXCLUDED.total_yards_per_game,
                    points_allowed_per_game =
                        EXCLUDED.points_allowed_per_game,
                    passing_yards_allowed_per_game =
                        EXCLUDED.passing_yards_allowed_per_game,
                    rushing_yards_allowed_per_game =
                        EXCLUDED.rushing_yards_allowed_per_game,
                    total_yards_allowed_per_game =
                        EXCLUDED.total_yards_allowed_per_game,
                    turnover_margin = EXCLUDED.turnover_margin,
                    third_down_pct = EXCLUDED.third_down_pct,
                    takeaways = EXCLUDED.takeaways,
                    giveaways = EXCLUDED.giveaways;
            """

            cursor = self.conn.cursor()
            cursor.execute(
                insert_query,
                (
                    team_abbr,
                    team_name,
                    week,
                    season,
                    points_per_game,
                    total_points,
                    passing_yards_per_game,
                    rushing_yards_per_game,
                    total_yards_per_game,
                    points_allowed_per_game,
                    passing_yards_allowed_per_game,
                    rushing_yards_allowed_per_game,
                    total_yards_allowed_per_game,
                    turnover_margin,
                    third_down_pct,
                    takeaways,
                    giveaways,
                ),
            )

            self.conn.commit()
            cursor.close()
            return True

        except psycopg2.Error as e:
            logger.error(f"Failed to insert team stats for {team_abbr}: {e}")
            self.conn.rollback()
            return False

    def load_week_data(self, week: int, data_dir: Path) -> Tuple[int, int, int, int]:
        """Load all game data for a specific week"""
        logger.info(f"Loading Week {week} data...")

        # Find week file in directory
        week_file = None
        for file in data_dir.glob(f"nfl_games_week_{week}_2025_*.json"):
            week_file = file
            break

        if not week_file:
            logger.warning(f"No data file found for Week {week}")
            return 0, 0, 0, 0

        logger.info(f"Loading from: {week_file}")
        week_data = self.load_week_file(week_file)

        games = week_data.get("games", [])
        team_stats_list = week_data.get("team_stats", [])

        game_success = 0
        game_error = 0
        stats_success = 0
        stats_error = 0

        # Load games
        for idx, game in enumerate(games, 1):
            if self.insert_game(game):
                game_success += 1
                if idx % 5 == 0:
                    logger.info(
                        f"[{idx:2d}/{len(games)}] "
                        f"{game.get('away_team_abbr')}@{game.get('home_team_abbr')}"
                    )
            else:
                game_error += 1

        logger.info(f"Games: {game_success}/{len(games)} loaded")

        # Load team stats
        for idx, stats in enumerate(team_stats_list, 1):
            if self.insert_team_stats(stats):
                stats_success += 1
            else:
                stats_error += 1

        if team_stats_list:
            logger.info(f"Team Stats: {stats_success}/{len(team_stats_list)} loaded")

        logger.info(
            f"Week {week} Complete: {game_success} games, {stats_success} team stats"
        )
        return game_success, game_error, stats_success, stats_error

    def load_full_season(self, data_dir: Path) -> Dict:
        """Load all 18 weeks of 2025 NFL season"""
        logger.info(
            "Loading 2025 NFL historical season (weeks 1-18, all games)..."
        )

        season_summary = {
            "season": 2025,
            "league": "NFL",
            "weeks_loaded": [],
            "total_games_success": 0,
            "total_games_errors": 0,
            "total_team_stats_success": 0,
            "total_team_stats_errors": 0,
            "loaded_at": datetime.now().isoformat(),
        }

        for week in range(1, 19):
            separator = "=" * 80
            logger.info(separator)
            logger.info(f"WEEK {week} OF 18")
            logger.info(separator)

            game_success, game_error, stats_success, stats_error = self.load_week_data(
                week, data_dir
            )

            week_summary = {
                "week": week,
                "games_success": game_success,
                "games_errors": game_error,
                "team_stats_success": stats_success,
                "team_stats_errors": stats_error,
            }
            season_summary["weeks_loaded"].append(week_summary)

            season_summary["total_games_success"] += game_success
            season_summary["total_games_errors"] += game_error
            season_summary["total_team_stats_success"] += stats_success
            season_summary["total_team_stats_errors"] += stats_error

        return season_summary

    def verify_load(self) -> Dict:
        """Verify data was loaded correctly"""
        logger.info("Verifying loaded data...")

        try:
            cursor = self.conn.cursor()

            # Total records loaded
            cursor.execute(
                "SELECT COUNT(*) FROM games WHERE league = 'NFL' AND season = 2025;"
            )
            total_games = cursor.fetchone()[0]

            # By week distribution
            cursor.execute(
                "SELECT week, COUNT(*) as count "
                "FROM games WHERE league = 'NFL' AND season = 2025 "
                "GROUP BY week ORDER BY week;"
            )
            by_week = cursor.fetchall()

            # Sample games for verification
            cursor.execute(
                "SELECT game_id, home_team, away_team, status, week "
                "FROM games WHERE league = 'NFL' AND season = 2025 "
                "ORDER BY week, game_date LIMIT 5;"
            )
            sample_games = cursor.fetchall()

            cursor.close()

            logger.info(f"[OK] Total games loaded: {total_games}")
            logger.info("Games by week:")
            for week, count in by_week:
                logger.info(f"  Week {week}: {count} games")

            if sample_games:
                logger.info("[OK] Sample games:")
                for game in sample_games:
                    logger.info(
                        f"  Week {game[4]}: {game[2]}@{game[1]} ({game[3]})"
                    )

            return {
                "total_games": total_games,
                "by_week": dict(by_week),
                "sample_games": len(sample_games),
            }

        except psycopg2.Error as e:
            logger.error(f"Verification failed: {e}")
            return {}

    def verify_schema(self) -> bool:
        """Verify required tables exist"""
        try:
            cursor = self.conn.cursor()

            # Check if games table exists
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'games'
                );
            """
            )
            games_exists = cursor.fetchone()[0]

            if not games_exists:
                logger.error("Required 'games' table not found!")
                logger.error("Please run: psql -f database/schema.sql")
                return False

            cursor.close()
            logger.info("[OK] Required tables exist")
            return True

        except psycopg2.Error as e:
            logger.error(f"Schema verification failed: {e}")
            return False


async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Load 2025 NFL historical season data into PostgreSQL "
            "(weeks 1-18, all games, team statistics)"
        )
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/historical/nfl_2025",
        help="Directory containing collected week data files",
    )
    parser.add_argument(
        "--dbname",
        type=str,
        default="sports_db",
        help="Database name (default: sports_db)",
    )
    parser.add_argument(
        "--user",
        type=str,
        default="postgres",
        help="Database user (default: postgres)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="postgres",
        help="Database password (default: postgres)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Database host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5432,
        help="Database port (default: 5432)",
    )

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return

    loader = NFL2025HistoricalLoader(
        dbname=args.dbname,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port,
    )

    try:
        loader.connect()

        # Verify schema
        if not loader.verify_schema():
            logger.error("Schema verification failed, exiting.")
            return

        logger.info(f"Loading from: {data_dir}")
        season_summary = loader.load_full_season(data_dir)

        logger.info("Verifying load...")
        verification = loader.verify_load()

        logger.info("=" * 80)
        logger.info("2025 NFL HISTORICAL SEASON LOAD COMPLETE!")
        logger.info("=" * 80)
        logger.info(
            f"Games: {season_summary['total_games_success']} loaded, "
            f"{season_summary['total_games_errors']} errors"
        )
        if season_summary['total_team_stats_success'] > 0:
            logger.info(
                f"Team Stats: {season_summary['total_team_stats_success']} loaded, "
                f"{season_summary['total_team_stats_errors']} errors"
            )

    finally:
        loader.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
