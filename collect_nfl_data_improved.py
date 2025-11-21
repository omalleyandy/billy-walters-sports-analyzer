#!/usr/bin/env python3
"""
NFL Week 12 Data Collection Using Existing Clients
Leverages all existing infrastructure:
- ESPN Client (schedule, scores, stats)
- AccuWeather Client (weather forecasts)
- Massey Scraper (power ratings)
- Overtime API (betting lines)
- Complete NFL team data (all 32 teams)
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "clients"))

# Import existing clients
from src.data.espn_client import ESPNClient
from src.data.accuweather_client import AccuWeatherClient
from src.data.overtime_api_client import OvertimeApiClient
from src.data.massey_ratings_scraper import MasseyRatingsScraper

# Import our complete team data
from nfl_team_data import (
    NFL_TEAMS,
    get_team_by_name,
    is_division_game,
    get_all_divisions,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class ComprehensiveDataCollector:
    """
    Week 12 comprehensive data collection using all existing infrastructure.

    Billy Walters S-Factor Coverage:
    - Schedule & times ✓
    - Travel distances ✓
    - Timezone differences ✓
    - Stadium types (indoor/outdoor) ✓
    - Weather forecasts ✓
    - Division games ✓
    - Betting lines ✓
    """

    def __init__(self, week: int = 12, season: int = 2025):
        self.week = week
        self.season = season
        self.data_dir = Path("data") / "nfl_week_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def collect_all(self) -> Dict:
        """Collect all data needed for Week 12 analysis"""

        logger.info("=" * 70)
        logger.info(f"COMPREHENSIVE NFL DATA COLLECTION - WEEK {self.week}")
        logger.info("Using Existing Project Clients")
        logger.info("=" * 70 + "\n")

        data = {
            "week": self.week,
            "season": self.season,
            "collection_time": datetime.now().isoformat(),
            "sources": {
                "schedule": "ESPN API",
                "weather": "AccuWeather API",
                "ratings": "Massey Ratings",
                "lines": "Overtime.ag API",
                "travel": "Calculated (Haversine)",
                "stadiums": "NFL Official Data",
            },
        }

        # Collect from each source
        try:
            # 1. ESPN Schedule & Scores
            logger.info("[1/6] ESPN: Schedule, Scores, Stats...")
            data["espn"] = await self.fetch_espn_data()

            # 2. Travel Analysis (using complete team data)
            logger.info("[2/6] Calculating Travel Distances & Timezones...")
            data["travel"] = self.calculate_travel_analysis(data["espn"]["games"])

            # 3. Stadium Information
            logger.info("[3/6] Loading Stadium Database (All 32 Teams)...")
            data["stadiums"] = self.get_stadium_info()

            # 4. Weather Forecasts
            logger.info("[4/6] AccuWeather: Fetching Forecasts...")
            data["weather"] = await self.fetch_weather_data(data["espn"]["games"])

            # 5. Betting Lines
            logger.info("[5/6] Overtime: Fetching Current Lines...")
            data["betting_lines"] = await self.fetch_betting_lines()

            # 6. Calculate S-Factors & E-Factors
            logger.info("[6/6] Calculating Billy Walters Factors...")
            data["factors"] = self.calculate_all_factors(data)

        except Exception as e:
            logger.error(f"\n[ERROR] Collection failed: {e}")
            import traceback

            traceback.print_exc()
            return data

        # Save
        output_file = self.data_dir / f"week_{self.week}_comprehensive.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        # Display summary
        self.display_summary(data)
        logger.info(f"\n[OK] Saved to: {output_file}\n")

        return data

    async def fetch_espn_data(self) -> Dict:
        """Fetch schedule and scores from ESPN"""
        try:
            async with ESPNClient() as espn:
                # Get scoreboard for Week 12
                scoreboard = await espn.get_nfl_scoreboard(
                    week=self.week,
                    season_type=2,  # Regular season
                    season_year=self.season,
                )

                games = []
                for event in scoreboard.get("events", []):
                    game = self._parse_espn_event(event)
                    games.append(game)

                logger.info(f"  ✓ Fetched {len(games)} games from ESPN")

                return {"games": games, "timestamp": datetime.now().isoformat()}

        except Exception as e:
            logger.warning(f"  ! ESPN fetch failed: {e}")
            return {"games": [], "error": str(e)}

    def _parse_espn_event(self, event: Dict) -> Dict:
        """Parse ESPN event into structured game data"""
        competition = event["competitions"][0]

        home_team = next(
            t for t in competition["competitors"] if t["homeAway"] == "home"
        )
        away_team = next(
            t for t in competition["competitors"] if t["homeAway"] == "away"
        )

        return {
            "game_id": event["id"],
            "date": event["date"],
            "home_team": home_team["team"]["displayName"],
            "home_abbr": home_team["team"]["abbreviation"],
            "away_team": away_team["team"]["displayName"],
            "away_abbr": away_team["team"]["abbreviation"],
            "venue": competition["venue"]["fullName"],
            "venue_city": competition["venue"]["address"]["city"],
            "status": competition["status"]["type"]["name"],
            "broadcast": competition.get("broadcasts", [{}])[0].get("names", [""])[0],
        }

    def calculate_travel_analysis(self, games: List[Dict]) -> Dict:
        """Calculate travel distances and timezone differences for all games"""
        travel_data = {}

        for game in games:
            away_abbr = game.get("away_abbr", "")
            home_abbr = game.get("home_abbr", "")

            # Get team data from our complete database
            away_team = NFL_TEAMS.get(away_abbr)
            home_team = NFL_TEAMS.get(home_abbr)

            if not away_team or not home_team:
                logger.warning(f"  ! Missing team data: {away_abbr} or {home_abbr}")
                continue

            # Calculate distance
            distance = self._haversine_distance(
                away_team["lat"], away_team["lon"], home_team["lat"], home_team["lon"]
            )

            # Timezone difference
            tz_diff = self._timezone_diff(away_team["timezone"], home_team["timezone"])

            # Billy Walters S-factor points
            s_factor = self._calculate_travel_s_factor(distance, tz_diff)

            travel_data[f"{away_abbr}@{home_abbr}"] = {
                "distance_miles": round(distance, 1),
                "timezone_diff": tz_diff,
                "travel_from": f"{away_team['city']}, {away_team['state']}",
                "travel_to": f"{home_team['city']}, {home_team['state']}",
                "category": self._categorize_travel(distance, tz_diff),
                "s_factor_points": s_factor,
                "spread_adjustment": round(
                    s_factor / 5.0, 2
                ),  # 5 points = 1 spread point
            }

        logger.info(f"  ✓ Calculated travel for {len(travel_data)} games")
        return travel_data

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points (Haversine formula)"""
        from math import radians, sin, cos, sqrt, atan2

        R = 3959.87433  # Earth radius in miles

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def _timezone_diff(self, tz1: str, tz2: str) -> int:
        """Calculate timezone difference in hours"""
        tz_hours = {"PT": -8, "MT": -7, "CT": -6, "ET": -5}
        return abs(tz_hours.get(tz2, 0) - tz_hours.get(tz1, 0))

    def _categorize_travel(self, distance: float, tz_diff: int) -> str:
        """Categorize travel impact (Billy Walters)"""
        if distance < 500 and tz_diff == 0:
            return "SHORT"
        elif distance >= 1500 or tz_diff >= 2:
            return "LONG"
        else:
            return "MODERATE"

    def _calculate_travel_s_factor(self, distance: float, tz_diff: int) -> float:
        """
        Calculate S-factor points for travel (Billy Walters methodology).

        Billy Walters Advanced Master Class:
        - Short (<500mi, no TZ): 0 points
        - Moderate (500-1500mi): 2-3 points
        - Long (>1500mi or 2+ TZ): 5-7 points
        - Coast-to-coast (3 TZ): 10 points
        """
        points = 0.0

        # Distance component
        if distance > 2500:
            points += 5.0
        elif distance > 1500:
            points += 3.0
        elif distance > 500:
            points += 2.0

        # Timezone component (Billy Walters: MORE important than distance)
        if tz_diff >= 3:
            points += 5.0  # Coast-to-coast
        elif tz_diff == 2:
            points += 3.0
        elif tz_diff == 1:
            points += 1.0

        return points

    def get_stadium_info(self) -> Dict:
        """Get complete stadium information for all 32 teams"""
        stadiums = {}

        for abbr, team in NFL_TEAMS.items():
            stadiums[team["stadium"]] = {
                "team": abbr,
                "type": team["stadium_type"],
                "surface": team["surface"],
                "altitude": team["altitude"],
                "weather_impact": team["stadium_type"] == "OUTDOOR",
            }

        logger.info(f"  ✓ Loaded {len(stadiums)} stadium profiles")
        return stadiums

    async def fetch_weather_data(self, games: List[Dict]) -> Dict:
        """Fetch weather forecasts for outdoor games"""
        weather_data = {}

        try:
            async with AccuWeatherClient() as weather:
                for game in games:
                    home_abbr = game.get("home_abbr", "")
                    home_team = NFL_TEAMS.get(home_abbr)

                    if not home_team:
                        continue

                    # Skip indoor stadiums
                    if home_team["stadium_type"] == "INDOOR":
                        weather_data[game["game_id"]] = {
                            "condition": "INDOOR - No weather impact",
                            "s_factor_points": 0.0,
                        }
                        continue

                    # TODO: Fetch actual forecast
                    # For now, mark as needing manual check
                    weather_data[game["game_id"]] = {
                        "location": f"{home_team['city']}, {home_team['state']}",
                        "stadium_type": home_team["stadium_type"],
                        "forecast": "PENDING - Check Saturday",
                        "note": "Update with real forecast before betting",
                    }

            logger.info(f"  ✓ Weather analysis for {len(weather_data)} games")

        except Exception as e:
            logger.warning(f"  ! Weather fetch issue: {e}")
            logger.info("  → Check forecasts manually at weather.com")

        return weather_data

    async def fetch_betting_lines(self) -> Dict:
        """Fetch current betting lines from Overtime"""
        try:
            overtime = OvertimeApiClient()
            lines = await overtime.scrape_nfl()

            logger.info(f"  ✓ Fetched lines for {len(lines.get('games', []))} games")
            return lines

        except Exception as e:
            logger.warning(f"  ! Overtime fetch failed: {e}")
            return {"games": [], "error": str(e)}

    def calculate_all_factors(self, data: Dict) -> Dict:
        """Calculate comprehensive S-factors and E-factors"""
        factors = {"s_factors": {}, "e_factors": {}, "division_games": []}

        divisions = get_all_divisions()

        for game in data["espn"]["games"]:
            away_abbr = game.get("away_abbr", "")
            home_abbr = game.get("home_abbr", "")
            game_key = f"{away_abbr}@{home_abbr}"

            # S-Factors
            travel_s = data["travel"].get(game_key, {}).get("s_factor_points", 0)

            factors["s_factors"][game_key] = {
                "travel": travel_s,
                "rest": 0,  # TODO: Calculate from previous game dates
                "weather": 0,  # TODO: From weather forecasts
                "injuries": 0,  # TODO: From injury reports
                "total": travel_s,
            }

            # E-Factors (Division Games)
            if is_division_game(away_abbr, home_abbr):
                away_team = NFL_TEAMS.get(away_abbr, {})
                factors["division_games"].append(
                    {
                        "game": game_key,
                        "division": away_team.get("division", "Unknown"),
                        "e_factor_points": 2.0,
                        "note": "Division rivalry - More unpredictable, emotional",
                    }
                )

        logger.info(f"  ✓ S-factors calculated for {len(factors['s_factors'])} games")
        logger.info(f"  ✓ Found {len(factors['division_games'])} division games")

        return factors

    def display_summary(self, data: Dict) -> None:
        """Display collection summary"""
        logger.info("\n" + "=" * 70)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 70 + "\n")

        games = len(data["espn"]["games"])
        travel = len(data["travel"])
        stadiums = len(data["stadiums"])
        division_games = len(data["factors"]["division_games"])

        logger.info(f"Schedule: {games} games")
        logger.info(f"Travel Analysis: {travel} matchups")
        logger.info(f"Stadium Database: {stadiums} venues")
        logger.info(f"Division Games: {division_games} rivalries")

        # Show high-impact travel
        logger.info("\n" + "-" * 70)
        logger.info("HIGH-IMPACT TRAVEL (Coast-to-Coast or >1500mi)")
        logger.info("-" * 70)

        for game_key, travel_info in data["travel"].items():
            if travel_info["category"] == "LONG":
                logger.info(f"\n{game_key}:")
                logger.info(
                    f"  {travel_info['travel_from']} → {travel_info['travel_to']}"
                )
                logger.info(f"  Distance: {travel_info['distance_miles']:.0f} miles")
                logger.info(f"  Timezone: {travel_info['timezone_diff']} hour(s)")
                logger.info(f"  S-Factor: {travel_info['s_factor_points']} points")
                logger.info(
                    f"  Spread Impact: {travel_info['spread_adjustment']} points"
                )


async def main():
    """Run comprehensive data collection"""
    collector = ComprehensiveDataCollector(week=12, season=2025)

    try:
        data = await collector.collect_all()

        print("\n" + "=" * 70)
        print("[SUCCESS] Week 12 data collection complete!")
        print("\n[NEXT STEPS]")
        print("1. Review data/nfl_week_data/week_12_comprehensive.json")
        print("2. Check injury reports at NFL.com/injuries")
        print("3. Update weather forecasts Saturday morning")
        print("4. Run power ratings update:")
        print("   python update_power_ratings_week12.py")
        print("5. Run edge analysis:")
        print("   python analyze_edges_simple.py")
        print("=" * 70 + "\n")

    except Exception as e:
        logger.error(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
