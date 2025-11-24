#!/usr/bin/env python3
"""
2025 NCAAF Historical Season Statistics Loader
Loads collected 2025 season data (weeks 1-16, all 136 FBS teams) into PostgreSQL
Follows Boston College Eagles (Team ID 103) data structure pattern
"""

import json
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class NCAAF2025HistoricalLoader:
    """Loads 2025 NCAAF historical season data into PostgreSQL"""

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

    def load_week_file(self, filepath: Path) -> List[Dict]:
        """Load team statistics from week JSON file"""
        try:
            with open(filepath) as f:
                data = json.load(f)
            return data.get("teams", [])
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return []

    def insert_team_stats(self, team_stats: Dict) -> bool:
        """Insert single team statistics record into database"""
        try:
            cursor = self.conn.cursor()

            # Extract values
            team_id = team_stats.get("team_id")
            team_name = team_stats.get("team_name")
            week = team_stats.get("week")
            season = team_stats.get("season")
            games_played = team_stats.get("games_played")
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
            total_yards_allowed_per_game = team_stats.get(
                "total_yards_allowed_per_game"
            )
            turnover_margin = team_stats.get("turnover_margin")
            third_down_pct = team_stats.get("third_down_pct")
            takeaways = team_stats.get("takeaways")
            giveaways = team_stats.get("giveaways")

            # Insert or update
            insert_query = """
                INSERT INTO ncaaf_team_stats (
                    team_id, team_name, week, season_year,
                    games_played, points_per_game, total_points,
                    passing_yards_per_game, rushing_yards_per_game,
                    total_yards_per_game, points_allowed_per_game,
                    passing_yards_allowed_per_game,
                    rushing_yards_allowed_per_game,
                    total_yards_allowed_per_game, turnover_margin,
                    third_down_pct, takeaways, giveaways
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (team_id, week, season_year)
                DO UPDATE SET
                    games_played = EXCLUDED.games_played,
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

            cursor.execute(
                insert_query,
                (
                    team_id,
                    team_name,
                    week,
                    season,
                    games_played,
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
            logger.error(f"Failed to insert team stats for {team_id}: {e}")
            self.conn.rollback()
            return False

    def load_week_data(self, week: int, data_dir: Path) -> tuple[int, int]:
        """Load all team stats for a specific week"""
        logger.info(f"Loading Week {week} data...")

        # Find week file in directory
        week_file = None
        for file in data_dir.glob(f"ncaaf_team_stats_week_{week}_2025_*.json"):
            week_file = file
            break

        if not week_file:
            logger.warning(f"No data file found for Week {week}")
            return 0, 0

        logger.info(f"Loading from: {week_file}")
        team_stats_list = self.load_week_file(week_file)

        success_count = 0
        error_count = 0

        for idx, team_stats in enumerate(team_stats_list, 1):
            team_name = team_stats.get("team_name", "Unknown")
            if self.insert_team_stats(team_stats):
                success_count += 1
                if idx % 10 == 0:
                    logger.info(f"[{idx:3d}/{len(team_stats_list)}] {team_name}")
            else:
                error_count += 1

        logger.info(
            f"Week {week} Complete: {success_count}/{len(team_stats_list)} teams loaded"
        )
        return success_count, error_count

    def load_full_season(self, data_dir: Path) -> Dict:
        """Load all 16 weeks of 2025 NCAAF season"""
        logger.info(
            "Loading 2025 NCAAF historical season (weeks 1-16, all 136 FBS teams)..."
        )

        season_summary = {
            "season": 2025,
            "weeks_loaded": [],
            "total_success": 0,
            "total_errors": 0,
            "loaded_at": datetime.now().isoformat(),
        }

        for week in range(1, 17):
            separator = "=" * 80
            logger.info(separator)
            logger.info(f"WEEK {week} OF 16")
            logger.info(separator)

            success, error = self.load_week_data(week, data_dir)

            week_summary = {
                "week": week,
                "success_count": success,
                "error_count": error,
            }
            season_summary["weeks_loaded"].append(week_summary)

            season_summary["total_success"] += success
            season_summary["total_errors"] += error

        return season_summary

    def verify_load(self) -> Dict:
        """Verify data was loaded correctly"""
        logger.info("Verifying loaded data...")

        try:
            cursor = self.conn.cursor()

            # Total records loaded
            cursor.execute(
                "SELECT COUNT(*) FROM ncaaf_team_stats WHERE season_year = 2025;"
            )
            total_records = cursor.fetchone()[0]

            # By week distribution
            cursor.execute(
                "SELECT week, COUNT(*) as count "
                "FROM ncaaf_team_stats WHERE season_year = 2025 "
                "GROUP BY week ORDER BY week;"
            )
            by_week = cursor.fetchall()

            # Boston College verification
            cursor.execute(
                "SELECT team_name, week, points_per_game, "
                "points_allowed_per_game, turnover_margin "
                "FROM ncaaf_team_stats "
                "WHERE team_id = '103' AND season_year = 2025 "
                "ORDER BY week;"
            )
            bc_records = cursor.fetchall()

            cursor.close()

            logger.info(f"[OK] Total records loaded: {total_records}")
            logger.info("Records by week:")
            for week, count in by_week:
                logger.info(f"  Week {week}: {count} teams")

            if bc_records:
                logger.info(
                    "[OK] Boston College (ID 103) verified: "
                    f"{len(bc_records)} weeks loaded"
                )
            else:
                logger.warning("[WARNING] Boston College (ID 103) not found")

            return {
                "total_records": total_records,
                "weeks": dict(by_week),
                "bc_weeks_loaded": len(bc_records),
            }

        except psycopg2.Error as e:
            logger.error(f"Verification failed: {e}")
            return {}


async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Load 2025 NCAAF historical season data into PostgreSQL "
            "(weeks 1-16, all 136 FBS teams)"
        )
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/historical/ncaaf_2025",
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

    loader = NCAAF2025HistoricalLoader(
        dbname=args.dbname,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port,
    )

    try:
        loader.connect()

        logger.info(f"Loading from: {data_dir}")
        season_summary = loader.load_full_season(data_dir)

        logger.info("Verifying load...")
        verification = loader.verify_load()

        logger.info("2025 NCAAF historical season load complete!")
        logger.info(
            f"Total: {season_summary['total_success']} records, "
            f"{season_summary['total_errors']} errors"
        )

    finally:
        loader.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
