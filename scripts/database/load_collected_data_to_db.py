#!/usr/bin/env python3
"""
Load Collected Data into PostgreSQL Database

This script populates the PostgreSQL database with data collected by /collect-all-data command.
Reads from JSON files and inserts into appropriate tables.

Usage:
    uv run python scripts/database/load_collected_data_to_db.py --week 13
    uv run python scripts/database/load_collected_data_to_db.py --week 13 --league nfl
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.connection import get_db_connection


class DataLoader:
    """Load collected data into PostgreSQL."""

    def __init__(self, week: int, league: str = "nfl"):
        """
        Initialize loader.

        Args:
            week: NFL/NCAAF week number
            league: 'nfl' or 'ncaaf'
        """
        self.week = week
        self.league = league.upper()
        self.db = get_db_connection()
        self.stats = {
            "schedules": 0,
            "team_stats": 0,
            "weather": 0,
            "odds": 0,
            "errors": 0,
        }

    def load_schedules(self) -> bool:
        """Load game schedules from ESPN data."""
        print(f"\n[1/4] Loading {self.league} Schedules (Week {self.week})...")

        try:
            schedules_file = Path(
                f"data/current/{self.league.lower()}_week_{self.week}_games.json"
            )

            if not schedules_file.exists():
                print(f"  [WARNING] File not found: {schedules_file}")
                return False

            with open(schedules_file) as f:
                data = json.load(f)

            # Handle both array and object formats
            games = data if isinstance(data, list) else data.get("games", [])
            print(f"  [INFO] Found {len(games)} games in file")

            for game in games:
                try:
                    # Extract game data
                    game_id = game.get("id") or game.get("game_id")
                    game_date = game.get("date") or game.get("game_date")
                    status = game.get("status", "SCHEDULED")

                    # Handle nested ESPN API format
                    home_team = game.get("home_team")
                    away_team = game.get("away_team")

                    # Try nested competitions format
                    if not home_team and "competitions" in game:
                        competitions = game.get("competitions", [])
                        if competitions:
                            competitors = competitions[0].get("competitors", [])
                            for competitor in competitors:
                                home_away = competitor.get("homeAway")
                                team_name = competitor.get("team", {}).get(
                                    "displayName"
                                )
                                if home_away == "home":
                                    home_team = team_name
                                elif home_away == "away":
                                    away_team = team_name

                    if not all([game_id, home_team, away_team, game_date]):
                        continue

                    # Convert game_date if it's a dict
                    if isinstance(game_date, dict):
                        game_date = game_date.get("value", game_date)

                    # Insert into database (simple insert)
                    self.db.execute_query(
                        """
                        INSERT INTO espn_schedules
                        (game_id, season, week, league, home_team,
                         away_team, game_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            game_id,
                            2025,
                            self.week,
                            self.league,
                            home_team,
                            away_team,
                            game_date,
                        ),
                        fetch=False,
                    )
                    self.stats["schedules"] += 1

                except Exception as e:
                    print(f"  [WARNING] Failed to load game {game_id}: {e}")
                    self.stats["errors"] += 1

            print(f"  [OK] Loaded {self.stats['schedules']} schedules")
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to load schedules: {e}")
            self.stats["errors"] += 1
            return False

    def load_team_stats(self) -> bool:
        """Load team statistics from ESPN data."""
        print(f"\n[2/4] Loading {self.league} Team Statistics...")

        try:
            stats_file = Path(
                f"data/current/{self.league.lower()}_team_stats_week_{self.week}.json"
            )

            if not stats_file.exists():
                print(f"  [WARNING] File not found: {stats_file}")
                return False

            with open(stats_file) as f:
                data = json.load(f)

            teams = data.get("teams", [])
            print(f"  [INFO] Found {len(teams)} teams in file")

            for team in teams:
                try:
                    team_name = team.get("team_name") or team.get("name")

                    if not team_name:
                        continue

                    # Map stats from collected data to database columns
                    # espn_team_stats expects specific column names
                    self.db.execute_query(
                        """
                        INSERT INTO espn_team_stats
                        (season, week, league, team,
                         points_per_game,
                         points_allowed_per_game,
                         turnover_margin,
                         data_source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            2025,
                            self.week,
                            self.league,
                            team_name,
                            team.get("points_per_game"),
                            team.get("points_allowed_per_game"),
                            team.get("turnover_margin"),
                            "espn_collected",
                        ),
                        fetch=False,
                    )
                    self.stats["team_stats"] += 1

                except Exception as e:
                    print(f"  [WARNING] Failed to load stats for {team_name}: {e}")
                    self.stats["errors"] += 1

            print(f"  [OK] Loaded {self.stats['team_stats']} team records")
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to load team stats: {e}")
            self.stats["errors"] += 1
            return False

    def load_weather(self) -> bool:
        """Load weather data.

        Note: Weather table requires game_id FK, but collected data
        has city names. Need to map city -> game via schedules.
        For now, skipping weather load until mapping is available.
        """
        print(f"\n[3/4] Loading {self.league} Weather Data...")
        print("  [INFO] Weather data requires game_id mapping (city -> game)")
        print("  [INFO] Weather records collected but skipping database insert")
        print("  [INFO] Weather data available in:")
        print("    data/current/weather_forecasts_*.json (by city name)")
        return True

    def load_odds(self) -> bool:
        """Load odds data from Overtime.ag."""
        print(f"\n[4/4] Loading {self.league} Odds Data...")

        try:
            # Find Overtime API odds file
            league_dir = self.league.lower()
            odds_files = list(
                Path(f"output/overtime/{league_dir}/pregame").glob("api_walters_*.json")
            )

            if not odds_files:
                print(
                    f"  [WARNING] No odds files found in output/overtime/{league_dir}/"
                )
                return False

            odds_file = sorted(odds_files, reverse=True)[0]
            print(f"  [INFO] Using {odds_file.name}")

            with open(odds_file) as f:
                data = json.load(f)

            games = data.get("games", [])
            print(f"  [INFO] Found {len(games)} games with odds in file")

            for game in games:
                try:
                    game_id = game.get("id") or game.get("game_id")

                    # Extract team names, handling nested dict format
                    home_team = game.get("home_team")
                    away_team = game.get("away_team")

                    if not home_team and "home" in game:
                        home_data = game.get("home")
                        if isinstance(home_data, dict):
                            home_team = home_data.get("team")
                        else:
                            home_team = home_data

                    if not away_team and "away" in game:
                        away_data = game.get("away")
                        if isinstance(away_data, dict):
                            away_team = away_data.get("team")
                        else:
                            away_team = away_data

                    # Extract odds, converting None values for numbers
                    spread = game.get("spread")
                    if isinstance(spread, dict):
                        spread = spread.get("value")
                    spread = float(spread) if spread else None

                    moneyline_home = game.get("moneyline_home")
                    if isinstance(moneyline_home, dict):
                        moneyline_home = moneyline_home.get("value")
                    moneyline_home = int(moneyline_home) if moneyline_home else None

                    moneyline_away = game.get("moneyline_away")
                    if isinstance(moneyline_away, dict):
                        moneyline_away = moneyline_away.get("value")
                    moneyline_away = int(moneyline_away) if moneyline_away else None

                    total = game.get("total")
                    if isinstance(total, dict):
                        total = total.get("value")
                    total = float(total) if total else None

                    sportsbook = game.get("sportsbook", "overtime")

                    if not all([game_id, home_team, away_team]):
                        continue

                    # Insert odds (with odds_type)
                    self.db.execute_query(
                        """
                        INSERT INTO odds
                        (game_id, sportsbook, odds_type, home_spread,
                         away_spread, home_moneyline,
                         away_moneyline, total, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            game_id,
                            sportsbook,
                            "opening",  # odds_type (opening/current/closing)
                            spread,
                            -spread if spread else None,
                            moneyline_home,
                            moneyline_away,
                            total,
                            datetime.now(),
                        ),
                        fetch=False,
                    )
                    self.stats["odds"] += 1

                except Exception as e:
                    print(f"  [WARNING] Failed to load odds for game {game_id}: {e}")
                    self.stats["errors"] += 1

            print(f"  [OK] Loaded {self.stats['odds']} odds records")
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to load odds: {e}")
            self.stats["errors"] += 1
            return False

    def run(self) -> None:
        """Run all data loading tasks."""
        print("=" * 70)
        print("LOADING COLLECTED DATA INTO POSTGRESQL DATABASE")
        print("=" * 70)
        print(f"Week: {self.week}")
        print(f"League: {self.league}")
        print()

        try:
            self.load_schedules()
            self.load_team_stats()
            self.load_weather()
            self.load_odds()

            # Summary
            print("\n" + "=" * 70)
            print("LOAD SUMMARY")
            print("=" * 70)
            print(f"Schedules:   {self.stats['schedules']} records")
            print(f"Team Stats:  {self.stats['team_stats']} records")
            print(f"Weather:     {self.stats['weather']} records")
            print(f"Odds:        {self.stats['odds']} records")
            print(f"Errors:      {self.stats['errors']}")
            print("=" * 70)

            if self.stats["errors"] == 0:
                print("[OK] All data loaded successfully!")
            else:
                print(
                    f"[WARNING] {self.stats['errors']} errors occurred during loading"
                )

        finally:
            self.db.close_all_connections()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load collected data into PostgreSQL database"
    )
    parser.add_argument("--week", type=int, required=True, help="Week number")
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="nfl",
        help="League (default: nfl)",
    )

    args = parser.parse_args()

    loader = DataLoader(week=args.week, league=args.league)
    loader.run()


if __name__ == "__main__":
    main()
