#!/usr/bin/env python3
"""
Load Massey ratings from JSON files into database.

Parses Massey ratings JSON files from output/massey/ directory and
populates the massey_ratings table with team ratings, rankings, and
components (offense, defense, strength of schedule).

This serves as the fallback/reference source for custom power ratings.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection


class MasseyRatingsLoader:
    """Load Massey ratings from JSON files into database."""

    def __init__(self):
        self.db = get_db_connection()
        self.massey_dir = Path(os.getcwd()) / "output" / "massey"

    def get_latest_ratings_file(self, league: str) -> Path | None:
        """Get the latest ratings file for a league."""
        pattern = f"{league.lower()}_ratings_*.json"
        files = sorted(self.massey_dir.glob(pattern))
        return files[-1] if files else None

    def parse_ratings_file(self, file_path: Path) -> list[dict]:
        """Parse ratings file and extract team data."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            teams = data.get("teams", [])
            if not teams:
                print(f"  [WARNING] No teams found in {file_path.name}")
                return []

            return teams
        except Exception as e:
            print(f"  [ERROR] Failed to parse {file_path.name}: {str(e)}")
            return []

    def extract_team_data(self, team_data: dict) -> dict:
        """Extract relevant fields from team data."""
        # rawData array structure (from observation):
        # [0] Team name + conference
        # [1] Record + win percentage
        # [2] Delta (ranking change)
        # [3] Rating ranking + rating value
        # [4] Power rating ranking + power rating
        # [5] Offense ranking + offense rating
        # [6] Defense ranking + defense rating
        # [7] Strength of schedule
        # [8] Recent ranking + recent rating
        # [9] Other ranking + other rating
        # [10-11] Additional metrics

        raw_data = team_data.get("rawData", [])

        # Parse record (format: "wins-losses" or "wins-losses-ties")
        record_str = team_data.get("record", "0-0")
        record_parts = record_str.split("-")
        wins = int(record_parts[0]) if len(record_parts) > 0 else 0
        losses = int(record_parts[1]) if len(record_parts) > 1 else 0
        ties = int(record_parts[2]) if len(record_parts) > 2 else 0

        # Extract ratings from rawData array
        # Index 4 contains power rating (format: "ranking\nrating")
        power_rating = None
        offense_rating = None
        defense_rating = None

        if len(raw_data) > 4:
            parts = raw_data[4].split("\n")
            if len(parts) > 1:
                try:
                    power_rating = float(parts[1])
                except ValueError:
                    pass

        if len(raw_data) > 5:
            parts = raw_data[5].split("\n")
            if len(parts) > 1:
                try:
                    offense_rating = float(parts[1])
                except ValueError:
                    pass

        if len(raw_data) > 6:
            parts = raw_data[6].split("\n")
            if len(parts) > 1:
                try:
                    defense_rating = float(parts[1])
                except ValueError:
                    pass

        return {
            "team": team_data.get("team", ""),
            "ranking": int(team_data.get("rank", 0)) if team_data.get("rank") else 0,
            "rating": float(team_data.get("rating", 0))
            if team_data.get("rating")
            else 0.0,
            "power_rating": power_rating or float(team_data.get("powerRating", 0))
            if team_data.get("powerRating")
            else 0.0,
            "offense_rating": offense_rating or 0.0,
            "defense_rating": defense_rating or 0.0,
            "sos_rating": 0.0,  # Strength of schedule - not clearly in data
            "wins": wins,
            "losses": losses,
            "ties": ties,
        }

    def load_ratings_for_league(self, league: str) -> tuple[int, int]:
        """Load ratings for a league (NFL or NCAAF)."""
        print(f"\n[LOAD] {league.upper()} Massey Ratings...")

        file_path = self.get_latest_ratings_file(league)
        if not file_path:
            print(f"  [WARNING] No Massey {league.upper()} ratings file found")
            return 0, 0

        print(f"  Loading {file_path.name}...")
        teams = self.parse_ratings_file(file_path)

        if not teams:
            return 0, 0

        conn = self.db.get_connection()
        cursor = conn.cursor()

        inserted = 0
        skipped = 0

        # Determine league code and week from file
        league_code = "NFL" if league.lower() == "nfl" else "NCAAF"
        # For now, use week 12 as we're loading current week data
        week = 12
        season = 2025

        for team_data in teams:
            try:
                extracted = self.extract_team_data(team_data)

                cursor.execute(
                    """
                    INSERT INTO massey_ratings
                    (season, week, league, team, ranking, rating,
                     offense_rating, defense_rating, sos_rating,
                     wins, losses, ties, data_source, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, NOW())
                    ON CONFLICT (season, week, league, team) DO NOTHING;
                """,
                    (
                        season,
                        week,
                        league_code,
                        extracted["team"],
                        extracted["ranking"],
                        extracted["rating"],
                        extracted["offense_rating"],
                        extracted["defense_rating"],
                        extracted["sos_rating"],
                        extracted["wins"],
                        extracted["losses"],
                        extracted["ties"],
                        "massey",
                    ),
                )

                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1

            except Exception as e:
                print(f"  [WARNING] Failed to insert {team_data.get('team')}: {str(e)}")
                skipped += 1

        conn.commit()
        cursor.close()

        print(f"  Inserted {inserted} teams, skipped {skipped} duplicates")
        return inserted, skipped

    def verify_data(self):
        """Verify data loaded successfully."""
        print("\n[VERIFY] Massey Ratings in Database...")

        result = self.db.execute_query("""
            SELECT league, COUNT(*) as count
            FROM massey_ratings
            GROUP BY league
            ORDER BY league
        """)

        total = 0
        for row in result:
            count = row["count"]
            total += count
            print(f"  {row['league']}: {count} teams")

        print(f"  Total: {total} teams")
        return total

    def main(self):
        """Run full load."""
        print("=" * 70)
        print("LOAD MASSEY RATINGS")
        print("=" * 70)

        try:
            # Load NFL and NCAAF ratings
            nfl_inserted, nfl_skipped = self.load_ratings_for_league("nfl")
            ncaaf_inserted, ncaaf_skipped = self.load_ratings_for_league("ncaaf")

            # Verify
            total = self.verify_data()

            print("\n" + "=" * 70)
            print("[OK] MASSEY RATINGS LOADED")
            print("=" * 70)
            print("\nSummary:")
            print(f"  NFL:   {nfl_inserted} inserted, {nfl_skipped} skipped")
            print(f"  NCAAF: {ncaaf_inserted} inserted, {ncaaf_skipped} skipped")
            print(f"  Total: {total} teams in database")
            print("\nNext steps:")
            print("  1. Build ESPN schedule parser")
            print("  2. Build ESPN injury parser")
            print("  3. Build ESPN team stats parser")
            print("  4. Build custom power rating engine")

            return True

        except Exception as e:
            print(f"\n[ERROR] Load failed: {str(e)}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            self.db.close_all_connections()


if __name__ == "__main__":
    loader = MasseyRatingsLoader()
    success = loader.main()
    sys.exit(0 if success else 1)
