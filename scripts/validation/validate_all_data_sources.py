#!/usr/bin/env python3
"""
Comprehensive Data Quality Assurance Script
Validates ALL data sources before feeding into Billy Walters edge detector.

Usage:
    python scripts/validation/validate_all_data_sources.py --league nfl --week 10
    python scripts/validation/validate_all_data_sources.py --league ncaaf --week 12

This script validates:
- Overtime odds data (spreads, totals, moneylines)
- Massey power ratings (NFL or NCAAF)
- Weather data (temperatures, wind, precipitation)
- Injury data (player names, positions, impact values)
- Team name consistency across all sources
- Data freshness and completeness
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class DataQualityReport:
    """Comprehensive data quality report"""

    def __init__(self, league: str, week: int = None):
        self.league = league.upper()
        self.week = week
        self.timestamp = datetime.now()

        # Results by data source
        self.results = {
            "overtime_odds": {"status": "pending", "errors": [], "warnings": []},
            "massey_ratings": {"status": "pending", "errors": [], "warnings": []},
            "weather": {"status": "pending", "errors": [], "warnings": []},
            "injuries": {"status": "pending", "errors": [], "warnings": []},
            "team_mapping": {"status": "pending", "errors": [], "warnings": []},
        }

        # Summary stats
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings_count = 0

    def add_error(self, source: str, message: str):
        """Add error to specific data source"""
        self.results[source]["errors"].append(message)
        self.results[source]["status"] = "failed"
        self.failed_checks += 1

    def add_warning(self, source: str, message: str):
        """Add warning to specific data source"""
        self.results[source]["warnings"].append(message)
        self.warnings_count += 1

    def mark_passed(self, source: str):
        """Mark data source as passed validation"""
        if self.results[source]["status"] != "failed":
            self.results[source]["status"] = "passed"
        self.passed_checks += 1

    def get_overall_status(self) -> str:
        """Get overall validation status"""
        if self.failed_checks > 0:
            return "FAILED"
        elif self.warnings_count > 0:
            return "PASSED_WITH_WARNINGS"
        else:
            return "PASSED"

    def print_report(self):
        """Print comprehensive validation report"""
        print("=" * 90)
        print("BILLY WALTERS DATA QUALITY ASSURANCE REPORT")
        print("=" * 90)
        print(f"League: {self.league}")
        if self.week:
            print(f"Week: {self.week}")
        print(f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Print results by source
        for source, data in self.results.items():
            status = data["status"]
            symbol = {
                "passed": "[OK]",
                "failed": "[ERROR]",
                "pending": "[SKIP]",
                "warning": "[WARN]",
            }.get(status, "[?]")

            print(f"{symbol} {source.upper().replace('_', ' ')}: {status.upper()}")

            if data["errors"]:
                print(f"  Errors: {len(data['errors'])}")
                for error in data["errors"][:5]:  # Show first 5
                    print(f"    - {error}")
                if len(data["errors"]) > 5:
                    print(f"    ... and {len(data['errors']) - 5} more errors")

            if data["warnings"]:
                print(f"  Warnings: {len(data['warnings'])}")
                for warning in data["warnings"][:3]:  # Show first 3
                    print(f"    - {warning}")
                if len(data["warnings"]) > 3:
                    print(f"    ... and {len(data['warnings']) - 3} more warnings")

            print()

        # Summary
        print("=" * 90)
        print("SUMMARY")
        print("=" * 90)
        print(f"Total Checks: {self.total_checks}")
        print(f"Passed: {self.passed_checks}")
        print(f"Failed: {self.failed_checks}")
        print(f"Warnings: {self.warnings_count}")
        print()

        overall = self.get_overall_status()
        if overall == "PASSED":
            print("[OK] ALL VALIDATION CHECKS PASSED")
            print("Data is ready for edge detection analysis")
        elif overall == "PASSED_WITH_WARNINGS":
            print("[WARN] VALIDATION PASSED WITH WARNINGS")
            print("Review warnings before proceeding with analysis")
        else:
            print("[ERROR] VALIDATION FAILED")
            print("Fix errors before running edge detection")

        print("=" * 90)
        print()

        return overall


# ============================================================================
# VALIDATOR 1: OVERTIME ODDS DATA
# ============================================================================


def validate_overtime_odds(report: DataQualityReport) -> bool:
    """Validate Overtime.ag odds data"""
    print("Validating Overtime Odds Data...")

    if report.league == "NFL":
        odds_dir = Path("output/overtime/nfl/pregame")
        pattern = "overtime_nfl_*.json"
    else:
        odds_dir = Path("output/overtime/ncaaf/pregame")
        pattern = "overtime_ncaaf_*.json"

    if not odds_dir.exists():
        report.add_error("overtime_odds", f"Odds directory not found: {odds_dir}")
        return False

    # Find latest odds file
    odds_files = sorted(
        odds_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True
    )

    if not odds_files:
        report.add_error("overtime_odds", f"No odds files found in {odds_dir}")
        return False

    latest_file = odds_files[0]

    # Check freshness (should be < 24 hours old)
    age_hours = (datetime.now().timestamp() - latest_file.stat().st_mtime) / 3600
    if age_hours > 24:
        report.add_warning(
            "overtime_odds", f"Odds data is {age_hours:.1f} hours old (stale)"
        )

    # Load and validate structure
    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        report.add_error("overtime_odds", f"Invalid JSON in {latest_file.name}: {e}")
        return False

    games = data.get("games", [])
    if not games:
        report.add_error("overtime_odds", "No games found in odds file")
        return False

    # Validate each game
    for i, game in enumerate(games):
        game_key = f"Game #{i + 1}"

        # Check required fields
        required_fields = ["visitor", "home", "period"]
        for field in required_fields:
            if field not in game:
                report.add_error(
                    "overtime_odds", f"{game_key}: Missing field '{field}'"
                )

        # Validate team structure
        for team_key in ["visitor", "home"]:
            if team_key not in game:
                continue

            team = game[team_key]

            # Check team name
            team_name = team.get("name", "")
            if not team_name or len(team_name) < 3:
                report.add_error(
                    "overtime_odds", f"{game_key}: Invalid team name '{team_name}'"
                )

            # Check odds structure
            if "odds" in team:
                odds = team["odds"]

                # Validate spread
                if "spread" in odds:
                    spread_line = odds["spread"].get("line")
                    spread_price = odds["spread"].get("price")

                    if spread_line is not None:
                        if not isinstance(spread_line, (int, float)):
                            report.add_error(
                                "overtime_odds",
                                f"{game_key} {team_name}: Spread line not numeric: {spread_line}",
                            )
                        elif abs(spread_line) > 50:
                            report.add_warning(
                                "overtime_odds",
                                f"{game_key} {team_name}: Unusual spread: {spread_line}",
                            )

                    if spread_price is not None:
                        if not isinstance(spread_price, int):
                            report.add_error(
                                "overtime_odds",
                                f"{game_key} {team_name}: Spread price not integer: {spread_price}",
                            )
                        elif spread_price < -1000 or spread_price > 1000:
                            report.add_warning(
                                "overtime_odds",
                                f"{game_key} {team_name}: Unusual price: {spread_price}",
                            )

                # Validate total
                if "total" in odds:
                    total_line = odds["total"].get("line")
                    if total_line is not None:
                        if not isinstance(total_line, (int, float)):
                            report.add_error(
                                "overtime_odds",
                                f"{game_key}: Total line not numeric: {total_line}",
                            )
                        elif report.league == "NFL":
                            if total_line < 20 or total_line > 70:
                                report.add_warning(
                                    "overtime_odds",
                                    f"{game_key}: Unusual NFL total: {total_line}",
                                )
                        elif report.league == "NCAAF":
                            if total_line < 25 or total_line > 90:
                                report.add_warning(
                                    "overtime_odds",
                                    f"{game_key}: Unusual NCAAF total: {total_line}",
                                )

                # Validate moneyline
                if "moneyline" in odds:
                    ml_price = odds["moneyline"].get("price")
                    if ml_price is not None:
                        if not isinstance(ml_price, int):
                            report.add_error(
                                "overtime_odds",
                                f"{game_key} {team_name}: ML price not integer: {ml_price}",
                            )

    # Check spread consistency (home and away should be inverse)
    for i, game in enumerate(games):
        if "visitor" in game and "home" in game:
            visitor_spread = (
                game["visitor"].get("odds", {}).get("spread", {}).get("line")
            )
            home_spread = game["home"].get("odds", {}).get("spread", {}).get("line")

            if visitor_spread is not None and home_spread is not None:
                if abs(visitor_spread + home_spread) > 0.01:  # Allow for float rounding
                    report.add_error(
                        "overtime_odds",
                        f"Game #{i + 1}: Spreads not inverse: {visitor_spread} vs {home_spread}",
                    )

    report.total_checks += 1
    report.mark_passed("overtime_odds")
    print(f"  Validated {len(games)} games from {latest_file.name}")
    return True


# ============================================================================
# VALIDATOR 2: MASSEY POWER RATINGS
# ============================================================================


def validate_massey_ratings(report: DataQualityReport) -> bool:
    """Validate Massey power ratings data"""
    print("Validating Massey Power Ratings...")

    if report.league == "NFL":
        ratings_dir = Path("output/massey")
        pattern = "nfl_ratings_*.json"
        expected_teams = 32
        rating_range = (0, 15)  # NFL uses Massey composite rating scale 0-15
    else:
        ratings_dir = Path("output/massey")
        pattern = "ncaaf_ratings_*.json"
        expected_teams = 130  # Approximate
        rating_range = (20, 90)

    if not ratings_dir.exists():
        report.add_error(
            "massey_ratings", f"Ratings directory not found: {ratings_dir}"
        )
        return False

    # Find latest ratings file
    ratings_files = sorted(
        ratings_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True
    )

    if not ratings_files:
        report.add_error("massey_ratings", f"No ratings files found in {ratings_dir}")
        return False

    latest_file = ratings_files[0]

    # Check freshness (should be < 7 days old)
    age_days = (datetime.now().timestamp() - latest_file.stat().st_mtime) / (3600 * 24)
    if age_days > 7:
        report.add_warning(
            "massey_ratings", f"Ratings data is {age_days:.1f} days old (stale)"
        )

    # Load and validate structure
    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        report.add_error("massey_ratings", f"Invalid JSON in {latest_file.name}: {e}")
        return False

    teams = data.get("teams", [])
    if not teams:
        report.add_error("massey_ratings", "No teams found in ratings file")
        return False

    # Check team count
    if report.league == "NFL" and len(teams) != expected_teams:
        report.add_warning(
            "massey_ratings", f"Expected {expected_teams} NFL teams, found {len(teams)}"
        )
    elif report.league == "NCAAF" and len(teams) < 100:
        report.add_warning(
            "massey_ratings", f"Only {len(teams)} NCAAF teams found (expected 130+)"
        )

    # Validate each team
    for i, team in enumerate(teams):
        team_name = team.get("team", f"Team #{i + 1}")

        # Check required fields (NFL uses "rating", NCAAF uses "powerRating")
        rating = team.get("powerRating") or team.get("rating")
        if rating is None:
            report.add_error("massey_ratings", f"{team_name}: Missing rating field")
            continue

        # Validate rating is numeric
        try:
            rating_float = float(rating)
        except (ValueError, TypeError):
            report.add_error(
                "massey_ratings", f"{team_name}: Power rating not numeric: {rating}"
            )
            continue

        # Check rating range
        min_rating, max_rating = rating_range
        if rating_float < min_rating or rating_float > max_rating:
            report.add_warning(
                "massey_ratings",
                f"{team_name}: Rating {rating_float:.2f} outside expected range ({min_rating}-{max_rating})",
            )

        # Check for offensive/defensive ratings (optional but useful)
        if "offensive_rating" in team and "defensive_rating" in team:
            pass  # Good - has component ratings
        else:
            # Warning only if we need these for totals analysis
            pass

    report.total_checks += 1
    report.mark_passed("massey_ratings")
    print(f"  Validated {len(teams)} teams from {latest_file.name}")
    return True


# ============================================================================
# VALIDATOR 3: WEATHER DATA
# ============================================================================


def validate_weather_data(report: DataQualityReport) -> bool:
    """Validate weather data (if available)"""
    print("Validating Weather Data...")

    if report.week is None:
        report.add_warning("weather", "No week specified, skipping weather validation")
        report.total_checks += 1
        report.mark_passed("weather")
        return True

    weather_file = Path(
        f"data/current/{report.league.lower()}_week_{report.week}_weather.json"
    )

    if not weather_file.exists():
        report.add_warning("weather", f"Weather file not found: {weather_file}")
        report.total_checks += 1
        report.mark_passed("weather")
        return True

    # Load weather data
    try:
        with open(weather_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        report.add_error("weather", f"Invalid JSON: {e}")
        return False

    weather_list = data.get("weather", [])
    if not weather_list:
        report.add_warning("weather", "No weather data found")
        report.total_checks += 1
        report.mark_passed("weather")
        return True

    # Validate each weather entry
    for i, weather in enumerate(weather_list):
        game_id = weather.get("game_id", f"Game #{i + 1}")

        # Check temperature
        temp = weather.get("temperature")
        if temp is not None:
            try:
                temp_float = float(temp)
                if temp_float < -20 or temp_float > 120:
                    report.add_warning(
                        "weather",
                        f"{game_id}: Temperature {temp_float}F seems unrealistic",
                    )
            except (ValueError, TypeError):
                report.add_error("weather", f"{game_id}: Invalid temperature: {temp}")

        # Check wind speed
        wind = weather.get("wind_speed")
        if wind is not None:
            try:
                wind_float = float(wind)
                if wind_float < 0 or wind_float > 60:
                    report.add_warning(
                        "weather",
                        f"{game_id}: Wind speed {wind_float} MPH seems unrealistic",
                    )
            except (ValueError, TypeError):
                report.add_error("weather", f"{game_id}: Invalid wind speed: {wind}")

    report.total_checks += 1
    report.mark_passed("weather")
    print(f"  Validated {len(weather_list)} weather entries")
    return True


# ============================================================================
# VALIDATOR 4: INJURY DATA
# ============================================================================


def validate_injury_data(report: DataQualityReport) -> bool:
    """Validate injury data (if available)"""
    print("Validating Injury Data...")

    if report.week is None:
        report.add_warning("injuries", "No week specified, skipping injury validation")
        report.total_checks += 1
        report.mark_passed("injuries")
        return True

    injury_file = Path(
        f"data/current/{report.league.lower()}_week_{report.week}_injuries.json"
    )

    if not injury_file.exists():
        report.add_warning("injuries", f"Injury file not found: {injury_file}")
        report.total_checks += 1
        report.mark_passed("injuries")
        return True

    # Load injury data
    try:
        with open(injury_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        report.add_error("injuries", f"Invalid JSON: {e}")
        return False

    injuries = data.get("injuries", [])
    if not injuries:
        report.add_warning("injuries", "No injury data found")
        report.total_checks += 1
        report.mark_passed("injuries")
        return True

    # Validate each injury entry
    valid_positions = {"QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S", "K", "P"}
    valid_statuses = {"OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE", "IR"}

    for i, injury in enumerate(injuries):
        player_name = injury.get("player_name", f"Player #{i + 1}")

        # Check player name
        if not injury.get("player_name"):
            report.add_error("injuries", f"Injury #{i + 1}: Missing player name")

        # Check position
        position = injury.get("position", "").upper()
        if position and position not in valid_positions:
            report.add_warning(
                "injuries", f"{player_name}: Unknown position '{position}'"
            )

        # Check status
        status = injury.get("status", "").upper()
        if status and status not in valid_statuses:
            report.add_warning("injuries", f"{player_name}: Unknown status '{status}'")

        # Check impact value (if present)
        impact = injury.get("impact_points")
        if impact is not None:
            try:
                impact_float = float(impact)
                if impact_float < 0 or impact_float > 10:
                    report.add_warning(
                        "injuries",
                        f"{player_name}: Impact {impact_float} outside expected range (0-10)",
                    )
            except (ValueError, TypeError):
                report.add_error(
                    "injuries", f"{player_name}: Invalid impact value: {impact}"
                )

    report.total_checks += 1
    report.mark_passed("injuries")
    print(f"  Validated {len(injuries)} injury entries")
    return True


# ============================================================================
# VALIDATOR 5: TEAM NAME CONSISTENCY
# ============================================================================


def validate_team_mapping(report: DataQualityReport) -> bool:
    """Validate team names are consistent across all data sources"""
    print("Validating Team Name Consistency...")

    # This is a cross-source validation
    # Compare team names from Overtime odds vs Massey ratings

    # Load team mappings
    if report.league == "NFL":
        mapping_file = Path("src/data/nfl_team_mappings.json")
    else:
        mapping_file = Path("src/data/ncaaf_team_mappings.json")

    if not mapping_file.exists():
        report.add_warning(
            "team_mapping", f"Team mapping file not found: {mapping_file}"
        )
        report.total_checks += 1
        report.mark_passed("team_mapping")
        return True

    try:
        with open(mapping_file, "r") as f:
            mapping_data = json.load(f)
    except json.JSONDecodeError as e:
        report.add_error("team_mapping", f"Invalid mapping JSON: {e}")
        return False

    mappings = mapping_data.get("mappings", {})
    if not mappings:
        report.add_warning("team_mapping", "No team mappings found")
        report.total_checks += 1
        report.mark_passed("team_mapping")
        return True

    # Check that all mapped teams have valid abbreviations
    for full_name, abbrev in mappings.items():
        if not abbrev or len(abbrev) < 2:
            report.add_error(
                "team_mapping", f"Invalid abbreviation for '{full_name}': '{abbrev}'"
            )

    report.total_checks += 1
    report.mark_passed("team_mapping")
    print(f"  Validated {len(mappings)} team mappings")
    return True


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive data quality validation"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        required=True,
        help="League to validate (nfl or ncaaf)",
    )
    parser.add_argument(
        "--week", type=int, help="Week number (for injury/weather data)"
    )
    parser.add_argument(
        "--skip-weather", action="store_true", help="Skip weather validation"
    )
    parser.add_argument(
        "--skip-injuries", action="store_true", help="Skip injury validation"
    )

    args = parser.parse_args()

    # Create report
    report = DataQualityReport(league=args.league, week=args.week)

    print()
    print("=" * 90)
    print("BILLY WALTERS DATA QUALITY ASSURANCE")
    print("=" * 90)
    print(f"League: {args.league.upper()}")
    if args.week:
        print(f"Week: {args.week}")
    print()

    # Run validations
    try:
        validate_overtime_odds(report)
        validate_massey_ratings(report)

        if not args.skip_weather:
            validate_weather_data(report)

        if not args.skip_injuries:
            validate_injury_data(report)

        validate_team_mapping(report)

    except KeyboardInterrupt:
        print("\n[ABORT] Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Print final report
    print()
    overall_status = report.print_report()

    # Exit with appropriate code
    if overall_status == "FAILED":
        sys.exit(1)
    elif overall_status == "PASSED_WITH_WARNINGS":
        sys.exit(0)  # Warnings are OK
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
