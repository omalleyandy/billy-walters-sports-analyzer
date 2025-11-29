#!/usr/bin/env python3
"""
Game SWE Factors - Weather Population Script

Populates game_swe_factors table with weather adjustments:
- Temperature impact rules
- Wind impact rules
- Precipitation impact
- Calculates total weather adjustment

Data source: weather_data table (already populated by AccuWeather)

Usage:
    python populate_swe_weather.py --league nfl --week 13 --season 2025
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.connection import DatabaseConnection  # noqa: E402
from src.db.raw_data_operations import RawDataOperations  # noqa: E402
from src.db.raw_data_models import GameSWEFactors  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class WeatherSWEPopulator:
    """Populate game_swe_factors with weather-based adjustments."""

    # Weather impact rules (in points)
    TEMPERATURE_RANGES = {
        # (temp_threshold, impact)
        (90, 1.0),  # Very hot favors passing
        (80, 0.5),  # Hot favors passing
        (70, 0.0),  # Comfortable
        (50, 0.0),  # Cool
        (32, -0.5),  # Cold reduces yardage
        (20, -1.5),  # Very cold favors rushing
        (-100, -2.0),  # Extreme cold (rare)
    }

    WIND_RANGES = {
        # (wind_threshold, impact)
        (30, -2.5),  # Extreme wind kills kicking/passing
        (20, -1.5),  # High wind hurts passing
        (15, -1.0),  # Moderate wind reduces scoring
        (10, -0.5),  # Light wind minimal impact
        (0, 0.0),  # Calm
    }

    PRECIPITATION_IMPACT = {
        # Precipitation type -> impact
        "heavy_rain": -1.5,
        "heavy_snow": -2.0,
        "light_rain": -0.5,
        "light_snow": -1.0,
        "clear": 0.0,
        "partly_cloudy": 0.0,
        "overcast": 0.0,
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

    def get_games_for_week(self, league_id: int, season: int, week: int) -> list:
        """Get all games for a week."""
        query = """
            SELECT id, game_id, away_team_id, home_team_id
            FROM game_schedules
            WHERE league_id = ? AND season = ? AND week = ?
            ORDER BY game_datetime
        """
        results = self.db_conn.execute_query(query, (league_id, season, week))
        return [dict(row) for row in results] if results else []

    def get_weather_data(self, game_id: str) -> Optional[Dict]:
        """Get weather data for a game."""
        query = """
            SELECT *
            FROM weather_data
            WHERE game_id = ?
            ORDER BY collected_at DESC
            LIMIT 1
        """
        results = self.db_conn.execute_query(query, (game_id,))
        return dict(results[0]) if results else None

    def calculate_temperature_impact(self, temperature_f: Optional[float]) -> float:
        """
        Calculate impact of temperature on game.

        Args:
            temperature_f: Temperature in Fahrenheit

        Returns:
            Impact in points (negative = hurts passing/kicking)
        """
        if temperature_f is None:
            return 0.0

        # Indoor stadiums (dome, covered)
        if temperature_f > 100 or temperature_f < -10:
            return 0.0  # Assume indoor

        # Cold reduces yardage, favors rushing
        if temperature_f < 20:
            return -1.5  # Very cold
        elif temperature_f < 32:
            return -1.0  # Freezing
        elif temperature_f < 50:
            return -0.5  # Cool

        # Heat favors passing
        if temperature_f > 90:
            return 1.0  # Very hot
        elif temperature_f > 80:
            return 0.5  # Hot

        return 0.0  # Comfortable

    def calculate_wind_impact(self, wind_speed_mph: Optional[float]) -> float:
        """
        Calculate impact of wind on game.

        Args:
            wind_speed_mph: Wind speed in miles per hour

        Returns:
            Impact in points (negative = hurts passing/kicking)
        """
        if wind_speed_mph is None:
            return 0.0

        # Wind affects passing and kicking (totals go down)
        if wind_speed_mph > 20:
            return -1.5  # High wind
        elif wind_speed_mph > 15:
            return -1.0  # Moderate wind
        elif wind_speed_mph > 10:
            return -0.5  # Light wind

        return 0.0  # Calm

    def calculate_precipitation_impact(self, conditions: Optional[str]) -> float:
        """
        Calculate impact of precipitation.

        Args:
            conditions: Weather conditions string

        Returns:
            Impact in points
        """
        if not conditions:
            return 0.0

        conditions_lower = conditions.lower()

        # Check precipitation type
        if "snow" in conditions_lower:
            if "heavy" in conditions_lower:
                return -2.0
            else:
                return -1.0

        if "rain" in conditions_lower:
            if "heavy" in conditions_lower:
                return -1.5
            else:
                return -0.5

        # Clear conditions
        if any(
            word in conditions_lower for word in ["clear", "sunny", "partly", "cloudy"]
        ):
            return 0.0

        return 0.0  # Unknown, assume neutral

    def calculate_weather_adjustment(
        self,
        temperature_f: Optional[float],
        wind_speed_mph: Optional[float],
        conditions: Optional[str],
    ) -> Tuple[float, float, float, float]:
        """
        Calculate total weather adjustment.

        Returns: (temp_impact, wind_impact, precip_impact, total_adjustment)
        """
        temp_impact = self.calculate_temperature_impact(temperature_f)
        wind_impact = self.calculate_wind_impact(wind_speed_mph)
        precip_impact = self.calculate_precipitation_impact(conditions)

        total = temp_impact + wind_impact + precip_impact

        # Clamp total to realistic range (-3 to +1 points)
        total = max(-3.0, min(1.0, total))

        return temp_impact, wind_impact, precip_impact, total

    def populate_week(self, league: str, season: int, week: int) -> None:
        """Populate weather SWE factors for a week."""
        logger.info(
            f"Populating weather SWE factors for {league.upper()} "
            f"Season {season}, Week {week}"
        )

        league_id = self.get_league_id(league)
        games = self.get_games_for_week(league_id, season, week)

        if not games:
            logger.warning(f"No games found for week {week}")
            return

        inserted = 0
        skipped = 0
        errors = 0

        for game in games:
            try:
                game_id = game["game_id"]
                away_team_id = game["away_team_id"]
                home_team_id = game["home_team_id"]

                # Get weather data
                weather = self.get_weather_data(game_id)

                if not weather:
                    logger.debug(f"  No weather data for {game_id}")
                    skipped += 1
                    continue

                # Extract weather metrics
                temperature_f = weather.get("temperature_f")
                wind_speed_mph = weather.get("wind_speed_mph")
                conditions = weather.get("conditions")

                # Calculate adjustments
                (
                    temp_impact,
                    wind_impact,
                    precip_impact,
                    total_adjustment,
                ) = self.calculate_weather_adjustment(
                    temperature_f, wind_speed_mph, conditions
                )

                # Create GameSWEFactors model
                swe_factors = GameSWEFactors(
                    league_id=league_id,
                    game_id=game_id,
                    season=season,
                    week=week,
                    away_team_id=away_team_id,
                    home_team_id=home_team_id,
                    weather_factor_description=(
                        f"{temperature_f:.0f}F, "
                        f"{wind_speed_mph:.0f} mph wind, "
                        f"{conditions}"
                    ),
                    weather_adjustment=total_adjustment,
                    temperature_impact=temp_impact,
                    wind_impact=wind_impact,
                    precipitation_impact=precip_impact,
                    total_adjustment=total_adjustment,
                    confidence_level=0.9,  # Weather is measurable
                    source="weather_data_accuweather",
                    notes=(
                        f"Temp: {temp_impact:+.1f}, "
                        f"Wind: {wind_impact:+.1f}, "
                        f"Precip: {precip_impact:+.1f}"
                    ),
                )

                # Insert to database
                self.db_ops.insert_game_swe_factors(swe_factors)
                inserted += 1

                logger.info(
                    f"  {game_id}: "
                    f"{temperature_f:.0f}F, "
                    f"{wind_speed_mph:.0f} mph → {total_adjustment:+.1f} pts"
                )

            except Exception as e:
                logger.error(f"  Error processing {game_id}: {e}")
                errors += 1

        logger.info(
            f"Completed: {inserted} games updated, "
            f"{skipped} skipped (no data), {errors} errors"
        )

    def populate_all_weeks(self, league: str, season: int) -> None:
        """Populate weather SWE factors for all weeks in a season."""
        max_weeks = 17 if league.lower() == "nfl" else 15

        for week in range(1, max_weeks + 1):
            try:
                self.populate_week(league, season, week)
            except Exception as e:
                logger.error(f"Error processing week {week}: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Populate game_swe_factors with weather adjustments"
    )
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
        "--week", type=int, help="Week to populate (if not specified, do all weeks)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    populator = WeatherSWEPopulator()

    if args.week:
        populator.populate_week(args.league, args.season, args.week)
    else:
        populator.populate_all_weeks(args.league, args.season)

    logger.info("Weather SWE factors population complete!")


if __name__ == "__main__":
    main()
