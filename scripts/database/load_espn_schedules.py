#!/usr/bin/env python3
"""
Load ESPN game schedules into database.

Parses ESPN schedule JSON files from output/espn/schedule/ directory and
populates the espn_schedules table with game dates, times, venues, and
scheduling information (neutral site, prime time, etc).
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


class ESPNScheduleLoader:
    """Load ESPN schedules from JSON files into database."""

    def __init__(self):
        self.db = get_db_connection()
        self.schedule_dir = Path(os.getcwd()) / "output" / "espn" / "schedule"

    def get_latest_schedule_file(self, league: str) -> Path | None:
        """Get the latest schedule file for a league."""
        pattern = f"schedule_{league.lower()}_*.json"
        league_dir = self.schedule_dir / league.lower()
        files = sorted(league_dir.glob(pattern)) if league_dir.exists() else []
        return files[-1] if files else None

    def parse_schedule_file(self, file_path: Path) -> dict:
        """Parse schedule file and extract games."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"  [ERROR] Failed to parse {file_path.name}: {str(e)}")
            return {}

    def extract_game_data(self, game: dict, league: str) -> dict | None:
        """Extract relevant fields from game data."""
        try:
            # ESPN uses 'competitions' array, not 'competitors'
            competitions = game.get("competitions", [])
            if not competitions:
                return None

            competition = competitions[0]
            competitors = competition.get("competitors", [])
            if len(competitors) < 2:
                return None

            # Determine home and away teams
            home_team = None
            away_team = None
            stadium = None
            for comp in competitors:
                team_name = comp.get("team", {}).get("displayName")
                if comp.get("homeAway") == "home":
                    home_team = team_name
                    # Get venue from home team
                    venue_info = comp.get("venue", {})
                    if venue_info:
                        stadium = venue_info.get("fullName")
                elif comp.get("homeAway") == "away":
                    away_team = team_name

            if not home_team or not away_team:
                return None

            # Parse date
            date_str = game.get("date", "")
            try:
                game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except Exception:
                return None

            # Extract week and season
            week_info = game.get("week", {})
            week = (
                week_info.get("number")
                if isinstance(week_info, dict)
                else int(week_info)
                if isinstance(week_info, (int, str))
                else 1
            )

            # Season is in leagues[0].season.year
            season_data = game.get("season")
            if isinstance(season_data, dict):
                season = season_data.get("year", 2025) or 2025
            else:
                season = int(season_data) if season_data else 2025

            # Parse stadium name to extract city and state
            city = None
            state = None
            if stadium:
                parts = stadium.split(",")
                if len(parts) >= 2:
                    city = parts[0].strip()
                    state = parts[1].strip()

            # Determine if it's neutral site and prime time
            # Neutral site: when venue is not the home team's primary venue
            # Prime time: games starting after 7 PM ET
            is_neutral_site = False  # Would need additional data to determine
            is_prime_time = game_date.hour >= 23 or (
                game_date.hour == 20  # 8 PM ET
            )

            # Determine if outdoor (would need stadium data)
            is_outdoor = True  # Default to outdoor unless we have specific info

            # Get game ID
            game_id = game.get("id", "")

            # Get day of week
            day_of_week = game_date.strftime("%A")

            return {
                "game_id": game_id,
                "season": season,
                "week": week,
                "league": "NFL" if league.lower() == "nfl" else "NCAAF",
                "home_team": home_team,
                "away_team": away_team,
                "stadium": stadium,
                "city": city,
                "state": state,
                "is_outdoor": is_outdoor,
                "game_date": game_date,
                "day_of_week": day_of_week,
                "is_neutral_site": is_neutral_site,
                "is_prime_time": is_prime_time,
            }
        except Exception as e:
            print(f"  [WARNING] Failed to extract game data: {str(e)}")
            return None

    def load_schedules_for_league(self, league: str) -> tuple[int, int]:
        """Load schedules for a league (NFL or NCAAF)."""
        print(f"\n[LOAD] {league.upper()} Schedules...")

        file_path = self.get_latest_schedule_file(league)
        if not file_path:
            print(f"  [WARNING] No ESPN {league.upper()} schedule file found")
            return 0, 0

        print(f"  Loading {file_path.name}...")
        data = self.parse_schedule_file(file_path)
        games = data.get("events", [])

        if not games:
            print(f"  [WARNING] No games found in {file_path.name}")
            return 0, 0

        conn = self.db.get_connection()
        cursor = conn.cursor()

        inserted = 0
        skipped = 0

        for idx, game in enumerate(games):
            try:
                extracted = self.extract_game_data(game, league)
                if not extracted:
                    print(f"    Game {idx + 1}: Failed to extract")
                    skipped += 1
                    continue

                # Check for dict values
                for key, val in extracted.items():
                    if isinstance(val, dict):
                        print(f"    Game {idx + 1}: ERROR - {key} is dict!")
                        skipped += 1
                        continue

                # Build values tuple
                values = (
                    extracted["game_id"],
                    extracted["season"],
                    extracted["week"],
                    extracted["league"],
                    extracted["home_team"],
                    extracted["away_team"],
                    extracted["stadium"],
                    extracted["city"],
                    extracted["state"],
                    extracted["is_outdoor"],
                    extracted["game_date"],
                    extracted["day_of_week"],
                    extracted["is_neutral_site"],
                    extracted["is_prime_time"],
                    "espn",
                )

                cursor.execute(
                    """
                    INSERT INTO espn_schedules
                    (game_id, season, week, league, home_team, away_team,
                     stadium, city, state, is_outdoor, game_date,
                     day_of_week, is_neutral_site, is_prime_time,
                     data_source, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, NOW())
                """,
                    values,
                )

                inserted += 1

            except Exception as e:
                print(f"    Game {idx + 1}: Error - {str(e)}")
                skipped += 1

        conn.commit()
        cursor.close()

        print(f"  Inserted {inserted} games, skipped {skipped} duplicates")
        return inserted, skipped

    def verify_data(self):
        """Verify data loaded successfully."""
        print("\n[VERIFY] ESPN Schedules in Database...")

        result = self.db.execute_query("""
            SELECT league, COUNT(*) as count
            FROM espn_schedules
            GROUP BY league
            ORDER BY league
        """)

        total = 0
        for row in result:
            count = row["count"]
            total += count
            print(f"  {row['league']}: {count} games")

        # Show by week
        result = self.db.execute_query("""
            SELECT league, week, COUNT(*) as count
            FROM espn_schedules
            WHERE league = 'NFL'
            GROUP BY league, week
            ORDER BY week
            LIMIT 5
        """)

        if result:
            print("\n  NFL games by week:")
            for row in result:
                print(f"    Week {row['week']}: {row['count']} games")

        print(f"  Total: {total} games")
        return total

    def main(self):
        """Run full load."""
        print("=" * 70)
        print("LOAD ESPN SCHEDULES")
        print("=" * 70)

        try:
            # Load NFL and NCAAF schedules
            nfl_inserted, nfl_skipped = self.load_schedules_for_league("nfl")
            ncaaf_inserted, ncaaf_skipped = self.load_schedules_for_league("ncaaf")

            # Verify
            total = self.verify_data()

            print("\n" + "=" * 70)
            print("[OK] ESPN SCHEDULES LOADED")
            print("=" * 70)
            print("\nSummary:")
            print(f"  NFL:   {nfl_inserted} inserted, {nfl_skipped} skipped")
            print(f"  NCAAF: {ncaaf_inserted} inserted, {ncaaf_skipped} skipped")
            print(f"  Total: {total} games in database")
            print("\nNext steps:")
            print("  1. Load ESPN injury data")
            print("  2. Load ESPN team statistics")
            print("  3. Load ESPN standings and scoreboards")
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
    loader = ESPNScheduleLoader()
    success = loader.main()
    sys.exit(0 if success else 1)
