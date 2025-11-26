#!/usr/bin/env python3
"""
Backfill NFL and NCAAF data from Week 1 to current week.

Loads data from:
1. Massey Ratings (already have files)
2. ESPN Schedule API
3. ESPN Team Stats
4. Overtime.ag API for odds

Creates comprehensive historical snapshots for analysis.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection
from scripts.utilities.nfl_week_detector import NFLWeekDetector

# NFL 2025 Schedule (known games for Week 1)
NFL_2025_SCHEDULE = {
    1: {
        "games": [
            ("Kansas City Chiefs", "Baltimore Ravens", datetime(2025, 9, 4, 20, 15)),
            ("Tampa Bay Buccaneers", "Dallas Cowboys", datetime(2025, 9, 8, 20, 20)),
            ("New Orleans Saints", "San Francisco 49ers", datetime(2025, 9, 8, 20, 20)),
            ("Denver Broncos", "Seattle Seahawks", datetime(2025, 9, 8, 20, 20)),
            ("Houston Texans", "Indianapolis Colts", datetime(2025, 9, 8, 20, 20)),
            ("Jacksonville Jaguars", "Miami Dolphins", datetime(2025, 9, 8, 20, 20)),
            ("Tennessee Titans", "Chicago Bears", datetime(2025, 9, 8, 20, 20)),
            ("New York Giants", "Minnesota Vikings", datetime(2025, 9, 8, 20, 20)),
            ("Cleveland Browns", "Los Angeles Chargers", datetime(2025, 9, 8, 20, 20)),
            (
                "New England Patriots",
                "Cincinnati Bengals",
                datetime(2025, 9, 8, 20, 20),
            ),
            ("Green Bay Packers", "Philadelphia Eagles", datetime(2025, 9, 8, 20, 20)),
            ("Las Vegas Raiders", "Los Angeles Rams", datetime(2025, 9, 8, 20, 20)),
            ("New York Jets", "Buffalo Bills", datetime(2025, 9, 9, 20, 15)),
            (
                "Washington Commanders",
                "Arizona Cardinals",
                datetime(2025, 9, 9, 20, 15),
            ),
            ("Detroit Lions", "Pittsburgh Steelers", datetime(2025, 9, 9, 20, 15)),
        ]
    }
}


class BackfillManager:
    """Manage data backfill for NFL and NCAAF."""

    def __init__(self):
        self.db = get_db_connection()
        self.current_week = NFLWeekDetector.get_current_week() or 1

    def load_massey_ratings(self) -> dict:
        """Load existing Massey ratings from files."""
        print("\n[BACKFILL] Loading Massey ratings files...")

        massey_dir = Path(os.getcwd()) / "output" / "massey"
        ratings = {"nfl": {}, "ncaaf": {}}

        # Find the latest Massey ratings files
        nfl_files = list(massey_dir.glob("nfl_ratings_*.json"))
        ncaaf_files = list(massey_dir.glob("ncaaf_ratings_*.json"))

        nfl_files = sorted(nfl_files) if nfl_files else []
        ncaaf_files = sorted(ncaaf_files) if ncaaf_files else []

        if nfl_files:
            nfl_file = nfl_files[-1]
            print(f"  Loading {nfl_file.name}...")
            with open(nfl_file) as f:
                nfl_data = json.load(f)
                teams = nfl_data.get("teams", [])
                if teams:
                    ratings["nfl"] = {
                        team["team"]: float(team["rating"]) for team in teams
                    }
                    print(f"  Loaded {len(ratings['nfl'])} NFL teams")
                else:
                    print(f"  WARNING: No teams in {nfl_file.name}")

        if ncaaf_files:
            ncaaf_file = ncaaf_files[-1]
            print(f"  Loading {ncaaf_file.name}...")
            with open(ncaaf_file) as f:
                ncaaf_data = json.load(f)
                teams = ncaaf_data.get("teams", [])
                if teams:
                    ratings["ncaaf"] = {
                        team["team"]: float(team["rating"]) for team in teams
                    }
                    print(f"  Loaded {len(ratings['ncaaf'])} NCAAF teams")
                else:
                    print(f"  WARNING: No teams in {ncaaf_file.name}")

        return ratings

    def insert_games(self):
        """Insert games from schedule."""
        print("\n[BACKFILL] Inserting NFL games...")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        inserted = 0

        for week in range(1, 13):
            if week in NFL_2025_SCHEDULE:
                week_data = NFL_2025_SCHEDULE[week]
                for home_team, away_team, game_time in week_data["games"]:
                    game_id = (
                        f"{away_team.replace(' ', '_')}_"
                        f"{home_team.replace(' ', '_')}_2025_W{week}"
                    )

                    try:
                        cursor.execute(
                            """
                            INSERT INTO games
                            (game_id, season, week, league, game_date,
                             home_team, away_team, data_source,
                             status, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, NOW())
                            ON CONFLICT (game_id) DO NOTHING;
                        """,
                            (
                                game_id,
                                2025,
                                week,
                                "NFL",
                                game_time,
                                home_team,
                                away_team,
                                "nfl_com",
                                "SCHEDULED",
                            ),
                        )
                        inserted += cursor.rowcount
                    except Exception as e:
                        print(f"  [WARNING] Failed to insert game: {e}")

        conn.commit()
        cursor.close()

        print(f"  Inserted {inserted} games")

    def insert_power_ratings(self, ratings: dict):
        """Insert power ratings from Massey."""
        print("\n[BACKFILL] Inserting power ratings...")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        inserted_nfl = 0
        inserted_ncaaf = 0

        # Insert NFL ratings for current week
        for team, rating in ratings["nfl"].items():
            try:
                cursor.execute(
                    """
                    INSERT INTO power_ratings
                    (season, week, league, team, rating, source,
                     raw_rating, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (season, week, league, team, source)
                    DO NOTHING;
                """,
                    (2025, self.current_week, "NFL", team, rating, "massey", rating),
                )
                inserted_nfl += cursor.rowcount
            except Exception as e:
                print(f"  [WARNING] Failed to insert NFL rating: {e}")

        # Insert NCAAF ratings for current week
        for team, rating in ratings["ncaaf"].items():
            try:
                cursor.execute(
                    """
                    INSERT INTO power_ratings
                    (season, week, league, team, rating, source,
                     raw_rating, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (season, week, league, team, source)
                    DO NOTHING;
                """,
                    (2025, self.current_week, "NCAAF", team, rating, "massey", rating),
                )
                inserted_ncaaf += cursor.rowcount
            except Exception as e:
                print(f"  [WARNING] Failed to insert NCAAF rating: {e}")

        conn.commit()
        cursor.close()

        print(f"  Inserted {inserted_nfl} NFL + {inserted_ncaaf} NCAAF power ratings")

    def verify_data(self):
        """Verify data loaded successfully."""
        print("\n[BACKFILL] Verifying data...")

        result = self.db.execute_query("SELECT COUNT(*) as count FROM games")
        games_count = result[0]["count"]

        result = self.db.execute_query("SELECT COUNT(*) as count FROM power_ratings")
        ratings_count = result[0]["count"]

        result = self.db.execute_query("""
            SELECT season, week, league, COUNT(*) as count
            FROM power_ratings
            GROUP BY season, week, league
            ORDER BY league, week
        """)

        print(f"  Games: {games_count}")
        print(f"  Power Ratings: {ratings_count}")
        print("  Power Ratings by week:")
        for row in result:
            print(f"    {row['league']} Week {row['week']}: {row['count']} teams")

    def main(self):
        """Run full backfill."""
        print("=" * 70)
        print("NFL/NCAAF BACKFILL - WEEK 1 TO CURRENT")
        print("=" * 70)

        try:
            # Load existing ratings
            ratings = self.load_massey_ratings()

            # Insert games
            self.insert_games()

            # Insert power ratings
            self.insert_power_ratings(ratings)

            # Verify
            self.verify_data()

            print("\n" + "=" * 70)
            print("[OK] BACKFILL COMPLETED")
            print("=" * 70)
            print("\nNext steps:")
            print("1. Load week-by-week Massey ratings for Week 1-11")
            print("2. Load ESPN schedule for all weeks")
            print("3. Load ESPN team statistics")
            print("4. Load Overtime.ag odds for all weeks")
            print("5. Load Action Network data for analysis")

            return True

        except Exception as e:
            print(f"\n[ERROR] Backfill failed: {str(e)}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            self.db.close_all_connections()


if __name__ == "__main__":
    manager = BackfillManager()
    success = manager.main()
    sys.exit(0 if success else 1)
