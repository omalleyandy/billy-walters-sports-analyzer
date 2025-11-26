#!/usr/bin/env python3
"""
Load Sample NFL Data for Testing
Creates sample 2025 NFL games and team statistics for development
Useful when ESPN API is unavailable
"""

import psycopg2
from datetime import datetime, timedelta
from typing import List
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class SampleNFLDataLoader:
    """Loads sample NFL data for testing"""

    # 2025 NFL Teams
    TEAMS = [
        # AFC East
        ("Buffalo Bills", "BUF"),
        ("Miami Dolphins", "MIA"),
        ("New England Patriots", "NE"),
        ("New York Jets", "NYJ"),
        # AFC North
        ("Baltimore Ravens", "BAL"),
        ("Pittsburgh Steelers", "PIT"),
        ("Cleveland Browns", "CLE"),
        ("Cincinnati Bengals", "CIN"),
        # AFC South
        ("Houston Texans", "HOU"),
        ("Indianapolis Colts", "IND"),
        ("Jacksonville Jaguars", "JAX"),
        ("Tennessee Titans", "TEN"),
        # AFC West
        ("Kansas City Chiefs", "KC"),
        ("Los Angeles Chargers", "LAC"),
        ("Las Vegas Raiders", "LV"),
        ("Denver Broncos", "DEN"),
        # NFC East
        ("Dallas Cowboys", "DAL"),
        ("Philadelphia Eagles", "PHI"),
        ("Washington Commanders", "WAS"),
        ("New York Giants", "NYG"),
        # NFC North
        ("Green Bay Packers", "GB"),
        ("Detroit Lions", "DET"),
        ("Chicago Bears", "CHI"),
        ("Minnesota Vikings", "MIN"),
        # NFC South
        ("Atlanta Falcons", "ATL"),
        ("New Orleans Saints", "NO"),
        ("Tampa Bay Buccaneers", "TB"),
        ("Carolina Panthers", "CAR"),
        # NFC West
        ("San Francisco 49ers", "SF"),
        ("Los Angeles Rams", "LAR"),
        ("Seattle Seahawks", "SEA"),
        ("Arizona Cardinals", "ARI"),
    ]

    # Sample games for Week 12, 2025
    SAMPLE_GAMES = [
        {
            "home_team": "Kansas City Chiefs",
            "away_team": "Buffalo Bills",
            "game_date": datetime(2025, 11, 24, 22, 30),  # Monday Night
            "week": 12,
            "stadium": "Arrowhead Stadium",
            "home_score": 27,
            "away_score": 21,
        },
        {
            "home_team": "Detroit Lions",
            "away_team": "Chicago Bears",
            "game_date": datetime(2025, 11, 27, 12, 30),  # Thursday
            "week": 12,
            "stadium": "Ford Field",
            "home_score": 35,
            "away_score": 14,
        },
        {
            "home_team": "Denver Broncos",
            "away_team": "New England Patriots",
            "game_date": datetime(2025, 11, 27, 15, 15),  # Sunday
            "week": 12,
            "stadium": "Empower Field at Mile High",
            "home_score": 28,
            "away_score": 17,
        },
        {
            "home_team": "Dallas Cowboys",
            "away_team": "Washington Commanders",
            "game_date": datetime(2025, 11, 27, 15, 15),  # Sunday
            "week": 12,
            "stadium": "AT&T Stadium",
            "home_score": 31,
            "away_score": 28,
        },
        {
            "home_team": "Green Bay Packers",
            "away_team": "Minnesota Vikings",
            "game_date": datetime(2025, 11, 27, 20, 20),  # Sunday Night
            "week": 12,
            "stadium": "Lambeau Field",
            "home_score": 24,
            "away_score": 19,
        },
    ]

    def __init__(
        self,
        dbname: str = "sports_db",
        user: str = "postgres",
        password: str = "postgres",
        host: str = "localhost",
        port: int = 5432,
    ):
        """Initialize loader"""
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None

    def connect(self) -> None:
        """Connect to PostgreSQL"""
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

    def load_teams(self) -> None:
        """Load NFL teams to database"""
        try:
            cursor = self.conn.cursor()

            logger.info("Loading teams...")

            for team_name, team_abbr in self.TEAMS:
                try:
                    insert_query = """
                        INSERT INTO teams (team_name, team_abbr, league, active)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (team_name) DO NOTHING
                    """
                    cursor.execute(insert_query, (team_name, team_abbr, "NFL", True))
                except psycopg2.Error:
                    pass  # Ignore duplicates

            self.conn.commit()
            logger.info(f"[OK] Loaded {len(self.TEAMS)} teams")
            cursor.close()

        except Exception as e:
            logger.error(f"Failed to load teams: {e}")
            self.conn.rollback()

    def load_sample_games(self) -> None:
        """Load sample games"""
        try:
            cursor = self.conn.cursor()

            logger.info("Loading sample games...")

            for game_data in self.SAMPLE_GAMES:
                home_team = game_data["home_team"]
                away_team = game_data["away_team"]
                game_date = game_data["game_date"]
                week = game_data["week"]

                # Find team abbreviations
                home_abbr = next(
                    (abbr for name, abbr in self.TEAMS if name == home_team), None
                )
                away_abbr = next(
                    (abbr for name, abbr in self.TEAMS if name == away_team), None
                )

                if not home_abbr or not away_abbr:
                    logger.warning(f"Team not found: {home_team} or {away_team}")
                    continue

                game_id = f"{home_abbr}_{away_abbr}_2025_W{week}"

                insert_query = """
                    INSERT INTO games (
                        game_id, season, week, league, game_date,
                        home_team, away_team, home_score, away_score,
                        final_margin, total_points, status, stadium,
                        is_outdoor, is_neutral_site
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (game_id) DO NOTHING
                """

                home_score = game_data.get("home_score")
                away_score = game_data.get("away_score")
                final_margin = (
                    home_score - away_score if home_score and away_score else None
                )
                total_points = (
                    home_score + away_score if home_score and away_score else None
                )
                status = "FINAL" if home_score is not None else "SCHEDULED"

                cursor.execute(
                    insert_query,
                    (
                        game_id,
                        2025,
                        week,
                        "NFL",
                        game_date,
                        home_team,
                        away_team,
                        home_score,
                        away_score,
                        final_margin,
                        total_points,
                        status,
                        game_data["stadium"],
                        True,  # is_outdoor
                        False,  # is_neutral_site
                    ),
                )

            self.conn.commit()
            logger.info(f"[OK] Loaded {len(self.SAMPLE_GAMES)} sample games")
            cursor.close()

        except Exception as e:
            logger.error(f"Failed to load games: {e}")
            self.conn.rollback()

    def load_sample_team_stats(self) -> None:
        """Load sample team statistics"""
        try:
            cursor = self.conn.cursor()

            logger.info("Loading sample team statistics...")

            # Create sample stats for all teams through Week 12
            for week in range(1, 13):
                for team_name, team_abbr in self.TEAMS:
                    # Generate realistic-ish stats
                    import random

                    ppg = round(random.uniform(18, 32), 2)
                    papg = round(random.uniform(18, 30), 2)
                    total_yards = round(random.uniform(320, 420), 2)
                    yards_allowed = round(random.uniform(310, 400), 2)

                    insert_query = """
                        INSERT INTO nfl_team_stats (
                            team_abbr, team_name, week, season_year,
                            points_per_game, points_allowed_per_game,
                            total_yards_per_game, total_yards_allowed_per_game,
                            turnover_margin, third_down_pct
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (team_abbr, week, season_year) DO NOTHING
                    """

                    cursor.execute(
                        insert_query,
                        (
                            team_abbr,
                            team_name,
                            week,
                            2025,
                            ppg,
                            papg,
                            total_yards,
                            yards_allowed,
                            random.randint(-3, 5),
                            round(random.uniform(35, 50), 1),
                        ),
                    )

            self.conn.commit()
            logger.info("[OK] Loaded team statistics for 12 weeks")
            cursor.close()

        except Exception as e:
            logger.error(f"Failed to load team stats: {e}")
            self.conn.rollback()

    def verify_load(self) -> None:
        """Verify data was loaded"""
        try:
            cursor = self.conn.cursor()

            # Check games
            cursor.execute("SELECT COUNT(*) FROM games WHERE season = 2025")
            game_count = cursor.fetchone()[0]
            logger.info(f"[OK] Games loaded: {game_count}")

            # Check teams
            cursor.execute("SELECT COUNT(*) FROM teams WHERE league = 'NFL'")
            team_count = cursor.fetchone()[0]
            logger.info(f"[OK] Teams loaded: {team_count}")

            # Check team stats
            cursor.execute(
                "SELECT COUNT(*) FROM nfl_team_stats WHERE season_year = 2025"
            )
            stats_count = cursor.fetchone()[0]
            logger.info(f"[OK] Team stats loaded: {stats_count}")

            cursor.close()

        except Exception as e:
            logger.error(f"Verification failed: {e}")

    def load_all(self) -> None:
        """Load all sample data"""
        try:
            self.connect()
            self.load_teams()
            self.load_sample_games()
            self.load_sample_team_stats()
            self.verify_load()
            self.close()
            logger.info("[OK] Sample data load complete!")
        except Exception as e:
            logger.error(f"Load failed: {e}")
            if self.conn:
                self.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load sample NFL data for testing")
    parser.add_argument(
        "--dbname",
        default="sports_db",
        help="Database name (default: sports_db)",
    )
    parser.add_argument(
        "--user",
        default="postgres",
        help="PostgreSQL user (default: postgres)",
    )
    parser.add_argument(
        "--password",
        default="postgres",
        help="PostgreSQL password",
    )
    parser.add_argument(
        "--host",
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

    loader = SampleNFLDataLoader(
        dbname=args.dbname,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port,
    )
    loader.load_all()
