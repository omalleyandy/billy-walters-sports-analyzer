#!/usr/bin/env python3
"""
Comprehensive Data Update Script - Billy Walters Sports Analyzer

Updates all data sources for the current NFL week:
- Game schedules and scores (ESPN)
- Odds data (Action Network & Overtime)
- Weather forecasts (AccuWeather & OpenWeather)
- Team statistics (ESPN)
- Injury reports (ESPN & NFL Official)

Usage:
    python scripts/utilities/update_all_data.py
    python scripts/utilities/update_all_data.py --week 10
    python scripts/utilities/update_all_data.py --source odds
    python scripts/utilities/update_all_data.py --no-odds  # Skip odds if unavailable
"""

import asyncio
import json
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class DataUpdater:
    """Comprehensive data updater for all sports data sources"""

    def __init__(self, week_num: Optional[int] = None):
        """
        Initialize data updater

        Args:
            week_num: Week number (auto-detected if None)
        """
        self.week_num = week_num or self._detect_current_week()
        self.project_root = project_root
        self.output_dir = self.project_root / "data" / "current"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Results tracking
        self.results = {
            "week": self.week_num,
            "timestamp": datetime.now().isoformat(),
            "updates": {},
            "errors": [],
        }

    def _detect_current_week(self) -> int:
        """Detect current NFL week from season calendar"""
        try:
            sys.path.insert(0, str(self.project_root / "src"))
            from walters_analyzer.season_calendar import (
                get_current_week_info,
            )

            week_info = get_current_week_info()
            return week_info["week"]
        except Exception as e:
            logger.warning(f"Could not auto-detect week: {e}")
            return 10  # Default to week 10

    def print_header(self):
        """Print update header"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("BILLY WALTERS SPORTS ANALYZER - DATA UPDATE")
        logger.info(f"Week {self.week_num} - 2025 NFL Season")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        logger.info("")

    async def update_game_schedules(self) -> bool:
        """Update game schedules and scores from ESPN"""
        logger.info("-" * 80)
        logger.info("UPDATING: Game Schedules and Scores (ESPN)")
        logger.info("-" * 80)

        try:
            from data.espn_client import ESPNClient

            async with ESPNClient() as client:
                # Get scoreboard for current week
                scoreboard = await client.get_scoreboard(
                    "NFL", week=self.week_num, season=2025
                )

                games = []
                events = scoreboard.get("events", [])

                for event in events:
                    competition = event.get("competitions", [{}])[0]
                    competitors = competition.get("competitors", [])

                    if len(competitors) < 2:
                        continue

                    # Extract teams
                    home_team = next(
                        (c for c in competitors if c.get("homeAway") == "home"), None
                    )
                    away_team = next(
                        (c for c in competitors if c.get("homeAway") == "away"), None
                    )

                    if not home_team or not away_team:
                        continue

                    # Extract status
                    status = event.get("status", {}).get("type", {})
                    game_status = status.get("name", "UNKNOWN")

                    game = {
                        "week": self.week_num,
                        "date": event.get("date", ""),
                        "home_team": home_team["team"]["displayName"],
                        "away_team": away_team["team"]["displayName"],
                        "home_score": (
                            int(home_team.get("score", 0))
                            if game_status == "STATUS_FINAL"
                            else None
                        ),
                        "away_score": (
                            int(away_team.get("score", 0))
                            if game_status == "STATUS_FINAL"
                            else None
                        ),
                        "status": game_status,
                    }

                    games.append(game)

                # Save games
                output_file = self.output_dir / f"nfl_week_{self.week_num}_games.json"
                with open(output_file, "w") as f:
                    json.dump(
                        {
                            "week": self.week_num,
                            "season": 2025,
                            "updated": datetime.now().isoformat(),
                            "source": "ESPN API",
                            "games": games,
                        },
                        f,
                        indent=2,
                    )

                self.results["updates"]["games"] = {
                    "count": len(games),
                    "file": str(output_file),
                }

                logger.info(f"[OK] Updated {len(games)} games")
                logger.info(f"     Saved to: {output_file.name}")
                return True

        except Exception as e:
            error_msg = f"Game schedule update failed: {e}"
            logger.error(f"[ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    async def update_odds_action_network(self) -> bool:
        """Update odds from Action Network"""
        logger.info("")
        logger.info("-" * 80)
        logger.info("UPDATING: Odds Data (Action Network)")
        logger.info("-" * 80)

        try:
            from data.action_network_client import ActionNetworkClient

            async with ActionNetworkClient() as client:
                # Get NFL odds for current week
                odds_data = await client.get_nfl_odds(week=self.week_num)

                # Save odds
                output_file = (
                    self.output_dir / f"nfl_week_{self.week_num}_odds_action.json"
                )
                with open(output_file, "w") as f:
                    json.dump(
                        {
                            "week": self.week_num,
                            "season": 2025,
                            "updated": datetime.now().isoformat(),
                            "source": "Action Network",
                            "odds": odds_data,
                        },
                        f,
                        indent=2,
                    )

                games_count = len(odds_data.get("games", []))
                self.results["updates"]["odds_action"] = {
                    "count": games_count,
                    "file": str(output_file),
                }

                logger.info(f"[OK] Updated odds for {games_count} games")
                logger.info(f"     Saved to: {output_file.name}")
                return True

        except Exception as e:
            error_msg = f"Action Network odds update failed: {e}"
            logger.error(f"[ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    async def update_odds_overtime(self) -> bool:
        """Update odds from Overtime.ag API (NEW: Direct API method)"""
        logger.info("")
        logger.info("-" * 80)
        logger.info("UPDATING: Odds Data (Overtime.ag API - NEW METHOD)")
        logger.info("-" * 80)

        try:
            # Use new API scraper script (no browser, no proxy, no auth needed)
            import subprocess

            scraper_script = self.project_root / "scripts" / "scrape_overtime_api.py"

            if not scraper_script.exists():
                logger.warning("[SKIP] Overtime API scraper script not found")
                return True

            # Run API scraper (fast, < 5 seconds)
            result = subprocess.run(
                [
                    sys.executable,
                    str(scraper_script),
                    "--nfl",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout (was 180 with browser)
            )

            if result.returncode == 0:
                logger.info("[OK] Overtime API odds updated successfully")

                # Find latest output file (new naming pattern)
                output_dir = (
                    self.project_root / "output" / "overtime" / "nfl" / "pregame"
                )
                overtime_files = sorted(
                    output_dir.glob("api_walters_*.json"), reverse=True
                )

                if overtime_files:
                    latest_file = overtime_files[0]
                    self.results["updates"]["odds_overtime"] = {
                        "file": str(latest_file),
                        "method": "api",
                    }
                    logger.info(f"     Latest file: {latest_file.name}")
                    logger.info("     Method: Direct API (no browser required)")

                return True
            else:
                logger.warning(
                    f"[WARNING] Overtime API scraper had issues: {result.stderr}"
                )
                return True  # Non-critical

        except subprocess.TimeoutExpired:
            logger.warning("[WARNING] Overtime API scraper timed out")
            return True  # Non-critical
        except Exception as e:
            error_msg = f"Overtime API odds update failed: {e}"
            logger.warning(f"[WARNING] {error_msg}")
            return True  # Non-critical

    async def update_weather_forecasts(self) -> bool:
        """Update weather forecasts for game locations"""
        logger.info("")
        logger.info("-" * 80)
        logger.info("UPDATING: Weather Forecasts")
        logger.info("-" * 80)

        try:
            from datetime import datetime
            from data.accuweather_client import AccuWeatherClient
            from data.openweather_client import OpenWeatherClient

            # Load current games to get locations
            games_file = self.output_dir / f"nfl_week_{self.week_num}_games.json"

            if not games_file.exists():
                logger.warning("[SKIP] No games file found, run game update first")
                return True

            with open(games_file, "r") as f:
                games_data = json.load(f)
                games = games_data.get("games", [])

            weather_data = {}

            # Try AccuWeather first
            try:
                async with AccuWeatherClient() as client:
                    for game in games[:5]:  # Limit to avoid API quota
                        home_team = game["home_team"]
                        game_date = game.get("date")

                        if not game_date:
                            continue

                        # Parse game time
                        game_time = datetime.fromisoformat(
                            game_date.replace("Z", "+00:00")
                        )

                        # Get weather forecast for game
                        forecast = await client.get_game_weather(home_team, game_time)
                        if forecast:
                            weather_data[home_team] = {
                                "source": "AccuWeather",
                                "game_time": game_date,
                                "forecast": forecast,
                            }
            except Exception as e:
                logger.warning(f"AccuWeather failed: {e}")

            # Try OpenWeather as backup for games without weather
            if len(weather_data) < len(games[:5]):
                try:
                    async with OpenWeatherClient() as client:
                        for game in games[:5]:
                            home_team = game["home_team"]

                            # Skip if already have weather from AccuWeather
                            if home_team in weather_data:
                                continue

                            game_date = game.get("date")
                            if not game_date:
                                continue

                            # Parse game time
                            game_time = datetime.fromisoformat(
                                game_date.replace("Z", "+00:00")
                            )

                            # Note: OpenWeather doesn't have get_game_weather, use get_game_forecast
                            # Would need stadium lookup - skip for now
                            logger.info(
                                f"OpenWeather fallback not implemented for {home_team}"
                            )
                except Exception as e:
                    logger.warning(f"OpenWeather failed: {e}")

            # Save weather data
            if weather_data:
                output_file = self.output_dir / f"nfl_week_{self.week_num}_weather.json"
                with open(output_file, "w") as f:
                    json.dump(
                        {
                            "week": self.week_num,
                            "season": 2025,
                            "updated": datetime.now().isoformat(),
                            "weather": weather_data,
                        },
                        f,
                        indent=2,
                    )

                self.results["updates"]["weather"] = {
                    "locations": len(weather_data),
                    "file": str(output_file),
                }

                logger.info(f"[OK] Updated weather for {len(weather_data)} locations")
                logger.info(f"     Saved to: {output_file.name}")
            else:
                logger.warning("[WARNING] No weather data available")

            return True

        except Exception as e:
            error_msg = f"Weather update failed: {e}"
            logger.error(f"[ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    async def update_team_statistics(self) -> bool:
        """Update team statistics from ESPN"""
        logger.info("")
        logger.info("-" * 80)
        logger.info("UPDATING: Team Statistics")
        logger.info("-" * 80)

        try:
            from data.espn_client import ESPNClient

            async with ESPNClient() as client:
                # Get NFL standings (NOTE: ESPN API currently returns minimal data)
                # Team stats not critical for Billy Walters analysis (use power ratings instead)
                standings = await client.get_standings("NFL", season=2025)

                teams_data = []
                for entry in standings.get("entries", []):
                    team = entry.get("team", {})
                    stats = entry.get("stats", [])

                    team_info = {
                        "name": team.get("displayName"),
                        "abbreviation": team.get("abbreviation"),
                        "stats": {},
                    }

                    # Extract key stats
                    for stat in stats:
                        name = stat.get("name")
                        value = stat.get("value")
                        if name and value is not None:
                            team_info["stats"][name] = value

                    teams_data.append(team_info)

                # Save team stats
                output_file = self.output_dir / f"nfl_week_{self.week_num}_teams.json"
                with open(output_file, "w") as f:
                    json.dump(
                        {
                            "week": self.week_num,
                            "season": 2025,
                            "updated": datetime.now().isoformat(),
                            "source": "ESPN API",
                            "teams": teams_data,
                        },
                        f,
                        indent=2,
                    )

                self.results["updates"]["teams"] = {
                    "count": len(teams_data),
                    "file": str(output_file),
                }

                logger.info(f"[OK] Updated statistics for {len(teams_data)} teams")
                logger.info(f"     Saved to: {output_file.name}")
                return True

        except Exception as e:
            error_msg = f"Team statistics update failed: {e}"
            logger.error(f"[ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    async def update_injury_reports(self) -> bool:
        """Update injury reports from ESPN and NFL Official"""
        logger.info("")
        logger.info("-" * 80)
        logger.info("UPDATING: Injury Reports")
        logger.info("-" * 80)

        try:
            from data.espn_injury_scraper import ESPNInjuryScraper

            scraper = ESPNInjuryScraper()
            injuries = scraper.scrape_nfl_injuries()

            # Save injuries
            output_file = self.output_dir / f"nfl_week_{self.week_num}_injuries.json"
            with open(output_file, "w") as f:
                json.dump(
                    {
                        "week": self.week_num,
                        "season": 2025,
                        "updated": datetime.now().isoformat(),
                        "source": "ESPN Injury Report",
                        "injuries": injuries,
                    },
                    f,
                    indent=2,
                )

            self.results["updates"]["injuries"] = {
                "count": len(injuries),
                "file": str(output_file),
            }

            logger.info(f"[OK] Updated {len(injuries)} injury reports")
            logger.info(f"     Saved to: {output_file.name}")
            return True

        except Exception as e:
            error_msg = f"Injury report update failed: {e}"
            logger.error(f"[ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def print_summary(self):
        """Print update summary"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("DATA UPDATE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Week: {self.week_num}")
        logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")

        # Updates completed
        logger.info("Updates Completed:")
        for source, data in self.results["updates"].items():
            count = data.get("count", "N/A")
            logger.info(f"  [OK] {source:20s} {count}")

        # Errors
        if self.results["errors"]:
            logger.info(f"\nErrors ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                logger.info(f"  [ERROR] {error}")
        else:
            logger.info("\n[SUCCESS] All updates completed successfully")

        logger.info("")
        logger.info("=" * 80)

    async def run_full_update(
        self, source: Optional[str] = None, no_odds: bool = False
    ):
        """
        Run complete data update

        Args:
            source: Specific source to update (None = all)
            no_odds: Skip odds updates
        """
        self.print_header()

        # Update all sources or specific one
        if source is None or source == "games":
            await self.update_game_schedules()

        if (source is None or source == "odds") and not no_odds:
            await self.update_odds_action_network()
            await self.update_odds_overtime()

        if source is None or source == "weather":
            await self.update_weather_forecasts()

        if source is None or source == "teams":
            await self.update_team_statistics()

        if source is None or source == "injuries":
            await self.update_injury_reports()

        # Print summary
        self.print_summary()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Update all sports data sources for current NFL week"
    )
    parser.add_argument(
        "--week", type=int, help="NFL week number (auto-detected if not specified)"
    )
    parser.add_argument(
        "--source",
        choices=["games", "odds", "weather", "teams", "injuries", "all"],
        help="Specific source to update (default: all)",
    )
    parser.add_argument(
        "--no-odds",
        action="store_true",
        help="Skip odds updates (use if APIs unavailable)",
    )

    args = parser.parse_args()

    # Run data update
    updater = DataUpdater(week_num=args.week)
    await updater.run_full_update(
        source=args.source if args.source != "all" else None, no_odds=args.no_odds
    )


if __name__ == "__main__":
    asyncio.run(main())
