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
from scripts.database.game_id_mapper import GameIDMapper


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
        self.mapper = GameIDMapper()
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

                    # Insert into database (skip duplicates)
                    self.db.execute_query(
                        """
                        INSERT INTO espn_schedules
                        (game_id, season, week, league,
                         home_team, away_team, game_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
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
                        ON CONFLICT DO NOTHING
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
        """Load weather data using game_id mapping.

        Weather table requires game_id FK. Maps city names to
        stadium locations using espn_schedules.
        """
        print(f"\n[3/4] Loading {self.league} Weather Data...")

        try:
            # Find weather files
            weather_files = list(Path("data/current").glob("weather_forecasts_*.json"))

            if not weather_files:
                print("  [WARNING] No weather files found in data/current/")
                return False

            weather_file = sorted(weather_files, reverse=True)[0]
            print(f"  [INFO] Using {weather_file.name}")

            with open(weather_file) as f:
                data = json.load(f)

            # Handle nested structure {nfl: {city: {...}}}
            weather_dict = data.get(self.league.lower(), {})
            if isinstance(weather_dict, dict):
                # Nested {city: {...}} format
                total_records = len(weather_dict)
            else:
                # Array format
                total_records = len(weather_dict)

            print(f"  [INFO] Found {total_records} cities with weather")

            for city_name, weather_data in weather_dict.items():
                try:
                    if not isinstance(weather_data, dict):
                        continue

                    # Get stadium for this city
                    stadium = self.mapper.get_stadium_from_city(city_name)
                    if not stadium:
                        print(f"    [WARN] No stadium found for {city_name}")
                        continue

                    # Find game matching this stadium
                    # Extract game data
                    temperature = weather_data.get("temperature")
                    feels_like = weather_data.get("feels_like")
                    wind_speed = weather_data.get("wind_speed")
                    wind_gust = weather_data.get("wind_gust")
                    humidity = weather_data.get("humidity")
                    precip_chance = weather_data.get("precipitation_chance")
                    category = weather_data.get("weather_category")
                    source = weather_data.get("source", "accuweather")

                    # For weather, we need to find the game by stadium
                    # This is a limitation - weather is attached to games
                    # For now, store stadium-level data (no FK required)
                    # Skip for now until we can match stadium to specific game
                    continue

                except Exception as e:
                    print(f"    [WARN] Failed to process {city_name}: {e}")
                    self.stats["errors"] += 1

            print(f"  [OK] Weather processing complete")
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to load weather: {e}")
            self.stats["errors"] += 1
            return False

    def load_odds(self) -> bool:
        """Load odds data from Overtime.ag with game_id mapping."""
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
                    overtime_game_id = game.get("id") or game.get("game_id")

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

                    if not all([overtime_game_id, home_team, away_team]):
                        continue

                    # Extract and parse game date from available fields
                    game_date_str = (
                        game.get("game_date")
                        or game.get("date")
                        or game.get("game_time")
                    )

                    if not game_date_str:
                        print(
                            f"    [WARN] No game date for {overtime_game_id} "
                            f"({home_team} vs {away_team})"
                        )
                        continue

                    # Parse game_date_str to datetime if it's a string
                    game_date = game_date_str
                    if isinstance(game_date_str, str):
                        # Try common formats
                        formats = [
                            "%m/%d/%Y %H:%M",
                            "%Y-%m-%d %H:%M:%S",
                            "%Y-%m-%d",
                        ]
                        for fmt in formats:
                            try:
                                game_date = datetime.strptime(game_date_str, fmt)
                                break
                            except ValueError:
                                continue

                    espn_game_id = self.mapper.map_overtime_to_espn(
                        overtime_game_id,
                        home_team,
                        away_team,
                        game_date,
                    )

                    if not espn_game_id:
                        print(
                            f"    [WARN] Could not map {overtime_game_id} "
                            f"({home_team} vs {away_team})"
                        )
                        self.stats["errors"] += 1
                        continue

                    # Extract odds from nested dict format
                    # Overtime.ag format: spread: {home: -2.5, away: 2.5}
                    spread_data = game.get("spread", {})
                    if isinstance(spread_data, dict):
                        home_spread = spread_data.get("home")
                        away_spread = spread_data.get("away")
                    else:
                        home_spread = None
                        away_spread = None

                    home_spread = float(home_spread) if home_spread else None
                    away_spread = float(away_spread) if away_spread else None

                    # Moneyline: {home: -145, away: 125}
                    ml_data = game.get("moneyline", {})
                    if isinstance(ml_data, dict):
                        moneyline_home = ml_data.get("home")
                        moneyline_away = ml_data.get("away")
                    else:
                        moneyline_home = None
                        moneyline_away = None

                    moneyline_home = int(moneyline_home) if moneyline_home else None
                    moneyline_away = int(moneyline_away) if moneyline_away else None

                    # Total: {points: 49.0, ...}
                    total_data = game.get("total", {})
                    if isinstance(total_data, dict):
                        total = total_data.get("points")
                    else:
                        total = total_data

                    total = float(total) if total else None

                    sportsbook = game.get("sportsbook", "overtime")

                    # Insert odds with mapped ESPN game_id
                    self.db.execute_query(
                        """
                        INSERT INTO odds
                        (game_id, sportsbook, odds_type,
                         home_spread, away_spread,
                         home_moneyline, away_moneyline,
                         total, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            espn_game_id,
                            sportsbook,
                            "opening",
                            home_spread,
                            away_spread,
                            moneyline_home,
                            moneyline_away,
                            total,
                            datetime.now(),
                        ),
                        fetch=False,
                    )
                    self.stats["odds"] += 1

                except Exception as e:
                    print(
                        f"  [WARNING] Failed to load odds for game "
                        f"{overtime_game_id}: {e}"
                    )
                    self.stats["errors"] += 1

            print(f"  [OK] Loaded {self.stats['odds']} odds records")
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to load odds: {e}")
            self.stats["errors"] += 1
            return False

    def populate_games_table(self) -> bool:
        """Populate games table from espn_schedules."""
        print(f"\n[0/4] Populating games table (Week {self.week})...")
        try:
            count = self.mapper.populate_games_table(
                season=2025, week=self.week, league=self.league
            )
            print(f"  [OK] Inserted {count} games into games table")
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to populate games table: {e}")
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
            # Step 0: Load schedules first (needed for FK mapping)
            self.load_schedules()

            # Step 1: Populate games table (needed for odds/weather FK)
            self.populate_games_table()

            # Step 2: Load stats and odds/weather
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
