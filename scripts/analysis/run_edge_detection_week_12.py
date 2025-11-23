#!/usr/bin/env python3
"""
Run Billy Walters edge detection for Week 12 using Overtime.ag API odds data
"""

import os
import json
import sys
import asyncio
import glob
from datetime import datetime
from pathlib import Path

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.walters_analyzer.valuation.billy_walters_edge_detector import (
    BillyWaltersEdgeDetector,
)
from src.walters_analyzer.valuation.billy_walters_totals_detector import (
    BillyWaltersTotalsDetector,
)
from src.data.accuweather_client import AccuWeatherClient
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def load_overtime_odds():
    """Load most recent Overtime.ag API odds file"""
    odds_dir = Path("output/overtime/nfl/pregame")
    api_files = sorted(odds_dir.glob("api_walters_*.json"), reverse=True)

    if not api_files:
        logger.error("No Overtime API odds files found")
        return None

    latest_file = api_files[0]
    logger.info(f"Loading odds from: {latest_file}")

    with open(latest_file) as f:
        return json.load(f)


def find_latest_massey_file():
    """Find the most recent Massey ratings file"""
    massey_files = sorted(glob.glob("output/massey/nfl_ratings*.json"))
    if not massey_files:
        logger.warning("No Massey ratings files found")
        return None
    return massey_files[-1]


def convert_game_time_to_iso(game_time: str) -> str:
    """Convert Overtime game time format (MM/DD/YYYY HH:MM) to ISO format

    Args:
        game_time: Time string in format "MM/DD/YYYY HH:MM" (e.g., "11/23/2025 13:00")

    Returns:
        ISO format string with UTC timezone, or empty string if conversion fails
    """
    if not game_time or not isinstance(game_time, str):
        return ""

    try:
        # Try parsing with dateutil if available (flexible parsing)
        if date_parser:
            dt = date_parser.parse(game_time)
            # Assume all times are in UTC and format as ISO
            return dt.replace(tzinfo=None).isoformat() + "Z"

        # Fallback: manual parsing if dateutil not available
        # Expected format: "MM/DD/YYYY HH:MM"
        parts = game_time.split(" ")
        if len(parts) != 2:
            return ""

        date_part, time_part = parts
        date_components = date_part.split("/")
        if len(date_components) != 3:
            return ""

        month, day, year = date_components
        return f"{year}-{month}-{day}T{time_part}:00Z"
    except Exception as e:
        logger.warning(f"Could not convert game time '{game_time}': {e}")
        return ""


def normalize_team_name_for_massey(team_name: str) -> str:
    """Convert Overtime team name to Massey format"""
    # Map from Overtime full names to Massey short names
    mapping = {
        "Arizona Cardinals": "Arizona",
        "Atlanta Falcons": "Atlanta",
        "Baltimore Ravens": "Baltimore",
        "Buffalo Bills": "Buffalo",
        "Carolina Panthers": "Carolina",
        "Chicago Bears": "Chicago",
        "Cincinnati Bengals": "Cincinnati",
        "Cleveland Browns": "Cleveland",
        "Dallas Cowboys": "Dallas",
        "Denver Broncos": "Denver",
        "Detroit Lions": "Detroit",
        "Green Bay Packers": "Green Bay",
        "Houston Texans": "Houston",
        "Indianapolis Colts": "Indianapolis",
        "Jacksonville Jaguars": "Jacksonville",
        "Kansas City Chiefs": "Kansas City",
        "Las Vegas Raiders": "Las Vegas",
        "LA Chargers": "LA Chargers",
        "LA Rams": "LA Rams",
        "Los Angeles Chargers": "LA Chargers",
        "Los Angeles Rams": "LA Rams",
        "Miami Dolphins": "Miami",
        "Minnesota Vikings": "Minnesota",
        "New England Patriots": "New England",
        "New Orleans Saints": "New Orleans",
        "NY Giants": "NY Giants",
        "New York Giants": "NY Giants",
        "NY Jets": "NY Jets",
        "New York Jets": "NY Jets",
        "Philadelphia Eagles": "Philadelphia",
        "Pittsburgh Steelers": "Pittsburgh",
        "San Francisco 49ers": "San Francisco",
        "Seattle Seahawks": "Seattle",
        "Tampa Bay Buccaneers": "Tampa Bay",
        "Tennessee Titans": "Tennessee",
        "Washington Commanders": "Washington",
    }
    return mapping.get(team_name, team_name)


def convert_overtime_to_games_data(overtime_odds: dict) -> dict:
    """Convert Overtime.ag odds format to games data format

    Handles duplicate entries from multiple sportsbooks by selecting
    the median spread and total (consensus line)
    """
    games_data = {}
    games_by_matchup = {}

    # First pass: group games by matchup
    for game in overtime_odds.get("games", []):
        away_team = normalize_team_name_for_massey(game.get("away_team", ""))
        home_team = normalize_team_name_for_massey(game.get("home_team", ""))

        if not away_team or not home_team:
            continue

        game_key = f"{away_team}_{home_team}"
        if game_key not in games_by_matchup:
            # Convert game time to ISO format
            raw_time = game.get("game_time", "")
            iso_time = convert_game_time_to_iso(raw_time) if raw_time else ""

            games_by_matchup[game_key] = {
                "game_id": game.get("game_id", ""),
                "game_time": iso_time,
                "teams": [
                    {"display_name": away_team},
                    {"display_name": home_team},
                ],
                "spreads": [],
                "totals": [],
            }

        # Collect spread and total values
        spread_data = game.get("spread", {})
        total_data = game.get("total", {})

        if spread_data.get("home") is not None:
            games_by_matchup[game_key]["spreads"].append(spread_data.get("home"))
        if total_data.get("points") is not None:
            games_by_matchup[game_key]["totals"].append(total_data.get("points"))

    # Second pass: pick first (primary) values
    # Overtime API returns entries in order: primary market first, then other books
    # We want the first entry which represents the main consensus line
    for game_key, game_info in games_by_matchup.items():
        # Use FIRST entry (primary market) not median
        # API orders by primary market first
        primary_spread = game_info["spreads"][0] if game_info["spreads"] else 0.0
        primary_total = game_info["totals"][0] if game_info["totals"] else 47.0

        games_data[game_key] = {
            "id": game_info["game_id"],
            "teams": game_info["teams"],
            "start_time": game_info["game_time"],
            "markets": {
                "sportsbook_1": {
                    "event": {
                        "spread": [
                            {
                                "value": primary_spread,
                                "odds": -110,
                            }
                        ],
                        "total": [
                            {
                                "value": primary_total,
                                "odds": -110,
                            }
                        ],
                    }
                }
            },
            "week": 12,
        }

    return games_data


def main():
    """Run edge detection on Week 12 with Overtime odds"""
    logger.info("=" * 80)
    logger.info("BILLY WALTERS EDGE DETECTION - WEEK 12")
    logger.info("=" * 80)

    # Load Overtime odds
    overtime_odds = load_overtime_odds()
    if not overtime_odds:
        logger.error("Failed to load Overtime odds")
        return

    logger.info(f"Loaded {len(overtime_odds.get('games', []))} games from Overtime")

    # Convert to games data format
    games_data = convert_overtime_to_games_data(overtime_odds)
    logger.info(f"Converted {len(games_data)} games for analysis")

    # Initialize edge detector
    detector = BillyWaltersEdgeDetector()

    # Load proprietary 90/10 power ratings
    logger.info("=" * 80)
    logger.info("USING BILLY WALTERS PROPRIETARY 90/10 POWER RATINGS FOR SPREADS")
    logger.info("=" * 80)
    detector.load_proprietary_ratings(week=11)

    # Load Massey ratings for totals (with Off/Def)
    logger.info("=" * 80)
    logger.info("LOADING MASSEY OFF/DEF RATINGS FOR TOTALS ANALYSIS")
    logger.info("=" * 80)
    massey_file = find_latest_massey_file()
    massey_ratings_for_totals = {}
    if massey_file and os.path.exists(massey_file):
        logger.info(f"Found Massey file: {massey_file}")
        spread_ratings = detector.power_ratings.copy()
        detector.load_massey_ratings(massey_file, league="nfl")
        massey_ratings_for_totals = detector.power_ratings.copy()
        detector.power_ratings = spread_ratings
        logger.info(
            f"Loaded {len(massey_ratings_for_totals)} Massey ratings with Off/Def"
        )
    else:
        logger.warning("No Massey ratings file found - using defaults")

    # Initialize totals detector
    totals_detector = BillyWaltersTotalsDetector()
    totals_detector.load_power_ratings(massey_ratings_for_totals)
    totals_detector.injury_data = {}

    # Load injury data
    detector.load_injury_data()
    totals_detector.injury_data = detector.injury_data

    # Initialize weather client
    weather_client = AccuWeatherClient()
    if not weather_client.api_key:
        logger.warning("No AccuWeather API key - weather analysis will be skipped")

    # Analyze each game
    edges = []
    totals_edges = []

    for game_id, game in games_data.items():
        teams = game.get("teams", [])
        if len(teams) < 2:
            continue

        # Teams already normalized to Massey format in convert function
        away_team = teams[0]["display_name"]
        home_team = teams[1]["display_name"]

        markets = game.get("markets", {})
        if not markets:
            continue

        first_book = list(markets.values())[0]
        event_markets = first_book.get("event", {})

        spread_data = event_markets.get("spread", [])
        if not spread_data:
            continue

        market_spread = spread_data[0].get("value", 0)
        total_data = event_markets.get("total", [])
        market_total = total_data[0].get("value", 47.0) if total_data else 47.0

        sharp = None

        # Fetch weather
        weather_impact = None
        game_time_str = game.get("start_time", "")
        if weather_client.api_key and game_time_str:
            try:
                game_time = datetime.fromisoformat(game_time_str.replace("Z", "+00:00"))

                async def fetch_weather():
                    await weather_client.connect()
                    return await weather_client.get_game_weather(home_team, game_time)

                weather_data = asyncio.run(fetch_weather())

                if weather_data:
                    weather_impact = detector.calculate_weather_impact(
                        temperature=weather_data.get("temperature"),
                        wind_speed=weather_data.get("wind_speed"),
                        precipitation=weather_data.get("precipitation"),
                        indoor=weather_data.get("indoor", False),
                    )

                    logger.info(
                        f"Weather for {home_team}: "
                        f"{weather_data.get('temperature')}F, "
                        f"{weather_data.get('wind_speed')} MPH wind"
                    )
            except Exception as e:
                logger.warning(f"Could not fetch weather for {home_team}: {e}")

        # Detect edge
        edge = detector.detect_edge(
            game_id=game_id,
            away_team=away_team,
            home_team=home_team,
            market_spread=market_spread,
            market_total=market_total,
            week=12,
            game_time=game_time_str,
            weather=weather_impact,
            sharp_action=sharp,
        )

        if edge:
            edges.append(edge)

        # Detect totals edge
        totals_edge = totals_detector.detect_totals_edge(
            game_id=game_id,
            away_team=away_team,
            home_team=home_team,
            market_total=market_total,
            market_over_odds=(total_data[0].get("odds", -110) if total_data else -110),
            market_under_odds=(
                total_data[1].get("odds", -110) if len(total_data) > 1 else -110
            ),
            week=12,
            game_time=game_time_str,
            weather=weather_impact,
            sharp_action=sharp,
            away_injuries=detector.calculate_team_injury_impact(away_team),
            home_injuries=detector.calculate_team_injury_impact(home_team),
        )

        if totals_edge:
            totals_edges.append(totals_edge)

    # Save and report edges
    if edges:
        detector.save_edges_jsonl(edges, "nfl_edges_detected_week_12.jsonl")
        report = detector.generate_report(edges)
        print("\n" + report)

        with open(f"{detector.output_dir}/edge_report_week_12.txt", "w") as f:
            f.write(report)
        logger.info(f"[OK] Saved {len(edges)} spread edges")
    else:
        logger.info("No spread edges detected above threshold")

    if totals_edges:
        totals_detector.save_totals_edges(
            totals_edges, "nfl_totals_detected_week_12.jsonl"
        )
        totals_report = totals_detector.generate_totals_report(totals_edges)

        try:
            print("\n" + totals_report)
        except UnicodeEncodeError:
            print("\n" + totals_report.encode("ascii", "replace").decode("ascii"))

        with open(
            f"{totals_detector.output_dir}/totals_report_week_12.txt",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(totals_report)
        logger.info(f"[OK] Saved {len(totals_edges)} totals edges")
    else:
        logger.info("No totals edges detected above threshold")

    logger.info("=" * 80)
    logger.info(
        f"Edge detection complete: {len(edges)} spread, {len(totals_edges)} totals"
    )
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
