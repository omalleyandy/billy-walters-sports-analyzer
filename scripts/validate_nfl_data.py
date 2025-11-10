#!/usr/bin/env python3
"""
NFL Data Validation Script
Validates game data, power ratings, and team records against known reality
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class NFLDataValidator:
    """Comprehensive NFL data validation"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.valid_teams = {
            # AFC East
            "Buffalo",
            "Miami",
            "New England",
            "NY Jets",
            # AFC North
            "Baltimore",
            "Cincinnati",
            "Cleveland",
            "Pittsburgh",
            # AFC South
            "Houston",
            "Indianapolis",
            "Jacksonville",
            "Tennessee",
            # AFC West
            "Denver",
            "Kansas City",
            "Las Vegas",
            "LA Chargers",
            # NFC East
            "Dallas",
            "NY Giants",
            "Philadelphia",
            "Washington",
            # NFC North
            "Chicago",
            "Detroit",
            "Green Bay",
            "Minnesota",
            # NFC South
            "Atlanta",
            "Carolina",
            "New Orleans",
            "Tampa Bay",
            # NFC West
            "Arizona",
            "LA Rams",
            "San Francisco",
            "Seattle",
        }

    def validate_games_file(self, games_file: Path) -> bool:
        """Validate game data file"""
        print("\n1. VALIDATING GAME DATA FILE")
        print("-" * 70)

        if not games_file.exists():
            self.errors.append(f"Games file not found: {games_file}")
            print(f"  [ERROR] File not found: {games_file}")
            return False

        with open(games_file, "r") as f:
            data = json.load(f)

        # Check metadata
        season = data.get("season")
        weeks = data.get("weeks")
        source = data.get("source", "")
        games = data.get("games", [])

        print(f"  Season: {season}")
        print(f"  Weeks: {weeks}")
        print(f"  Source: {source}")
        print(f"  Total Games: {len(games)}")

        # Check for simulated/fake data indicators
        if "simulated" in source.lower() or "placeholder" in source.lower():
            self.errors.append("Data source indicates simulated/fake data")
            print("  [ERROR] Data appears to be simulated/fake")

        # Validate each game
        week_counts = {}
        invalid_teams = set()

        for i, game in enumerate(games):
            week = game.get("week")
            home_team = game.get("home_team")
            away_team = game.get("away_team")
            home_score = game.get("home_score")
            away_score = game.get("away_score")
            game_date = game.get("date")

            # Track week counts
            if week not in week_counts:
                week_counts[week] = 0
            week_counts[week] += 1

            # Validate team names
            if home_team not in self.valid_teams:
                invalid_teams.add(home_team)
            if away_team not in self.valid_teams:
                invalid_teams.add(away_team)

            # Validate scores
            if not isinstance(home_score, int) or not isinstance(away_score, int):
                self.errors.append(f"Game {i}: Invalid scores")

            if home_score < 0 or away_score < 0:
                self.errors.append(f"Game {i}: Negative scores")

            # Check for unrealistic scores
            if home_score > 70 or away_score > 70:
                self.warnings.append(
                    f"Week {week}: {away_team} @ {home_team} ({away_score}-{home_score}) - Unusually high score"
                )

            # Validate date format
            if game_date:
                try:
                    datetime.fromisoformat(game_date)
                except ValueError:
                    self.errors.append(f"Game {i}: Invalid date format: {game_date}")

        if invalid_teams:
            self.errors.append(f"Invalid team names found: {invalid_teams}")
            print(f"  [ERROR] Invalid teams: {invalid_teams}")

        # Check week distribution
        print("\n  Games per week:")
        for week in sorted(week_counts.keys()):
            count = week_counts[week]
            status = "OK" if 14 <= count <= 16 else "WARNING"
            print(f"    Week {week:2d}: {count:2d} games [{status}]")
            if count < 14 or count > 16:
                self.warnings.append(f"Week {week}: Unusual game count ({count})")

        return len(self.errors) == 0

    def validate_team_records(self, games_file: Path) -> Dict[str, Dict]:
        """Calculate and validate team records"""
        print("\n2. VALIDATING TEAM RECORDS")
        print("-" * 70)

        with open(games_file, "r") as f:
            data = json.load(f)

        games = data["games"]
        teams = {
            team: {"wins": 0, "losses": 0, "pf": 0, "pa": 0}
            for team in self.valid_teams
        }

        for game in games:
            home = game["home_team"]
            away = game["away_team"]
            home_score = game["home_score"]
            away_score = game["away_score"]

            if home not in teams or away not in teams:
                continue

            if home_score > away_score:
                teams[home]["wins"] += 1
                teams[away]["losses"] += 1
            else:
                teams[away]["wins"] += 1
                teams[home]["losses"] += 1

            teams[home]["pf"] += home_score
            teams[home]["pa"] += away_score
            teams[away]["pf"] += away_score
            teams[away]["pa"] += home_score

        # Sort by record
        sorted_teams = sorted(
            teams.items(),
            key=lambda x: (x[1]["wins"], x[1]["pf"] - x[1]["pa"]),
            reverse=True,
        )

        print("\n  Top 5 Teams:")
        for i, (team, record) in enumerate(sorted_teams[:5], 1):
            diff = record["pf"] - record["pa"]
            print(
                f"    {i}. {team:20s} {record['wins']}-{record['losses']}  ({diff:+4d} diff)"
            )

        print("\n  Bottom 5 Teams:")
        for i, (team, record) in enumerate(sorted_teams[-5:], 1):
            diff = record["pf"] - record["pa"]
            print(
                f"    {i}. {team:20s} {record['wins']}-{record['losses']}  ({diff:+4d} diff)"
            )

        # Check for suspicious records
        for team, record in teams.items():
            total_games = record["wins"] + record["losses"]

            # Check for undefeated teams (very rare)
            if total_games >= 9 and record["losses"] == 0:
                self.warnings.append(
                    f"{team} is undefeated ({record['wins']}-0) - verify data accuracy"
                )

            # Check for winless teams
            if total_games >= 9 and record["wins"] == 0:
                self.warnings.append(
                    f"{team} is winless (0-{record['losses']}) - verify data accuracy"
                )

            # Check for extreme point differentials
            diff = record["pf"] - record["pa"]
            if abs(diff) > 200:
                self.warnings.append(
                    f"{team} has extreme point differential ({diff:+d}) - verify data accuracy"
                )

        return teams

    def validate_power_ratings(self, ratings_file: Path, team_records: Dict) -> bool:
        """Validate power ratings alignment with team records"""
        print("\n3. VALIDATING POWER RATINGS")
        print("-" * 70)

        if not ratings_file.exists():
            self.errors.append(f"Power ratings file not found: {ratings_file}")
            print(f"  [ERROR] File not found: {ratings_file}")
            return False

        with open(ratings_file, "r") as f:
            data = json.load(f)

        ratings = data.get("ratings", {})
        print(f"  Total teams rated: {len(ratings)}")

        # Check for duplicate teams
        team_names = list(ratings.keys())
        if len(team_names) != len(set(team_names)):
            duplicates = [t for t in team_names if team_names.count(t) > 1]
            self.errors.append(f"Duplicate teams in ratings: {set(duplicates)}")
            print(f"  [ERROR] Duplicate teams found: {set(duplicates)}")

        # Check that all NFL teams are present
        missing_teams = self.valid_teams - set(ratings.keys())
        if missing_teams:
            self.warnings.append(f"Missing teams in ratings: {missing_teams}")
            print(f"  [WARNING] Missing teams: {missing_teams}")

        # Validate ratings reasonableness
        sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)

        print("\n  Top 5 Rated Teams:")
        for i, (team, rating) in enumerate(sorted_ratings[:5], 1):
            record = team_records.get(team, {})
            wins = record.get("wins", 0)
            losses = record.get("losses", 0)
            print(f"    {i}. {team:20s} {rating:6.2f}  (Record: {wins}-{losses})")

        print("\n  Bottom 5 Rated Teams:")
        for i, (team, rating) in enumerate(sorted_ratings[-5:], 1):
            record = team_records.get(team, {})
            wins = record.get("wins", 0)
            losses = record.get("losses", 0)
            print(f"    {i}. {team:20s} {rating:6.2f}  (Record: {wins}-{losses})")

        # Check for misalignment between ratings and records
        print("\n  Checking for rating/record misalignments...")
        misalignments = []

        for team, rating in sorted_ratings[:10]:  # Top 10 rated teams
            record = team_records.get(team, {})
            wins = record.get("wins", 0)
            losses = record.get("losses", 0)

            # Top 10 rated team with losing record
            if losses > wins:
                misalignments.append(
                    f"{team}: Top 10 rating ({rating:.2f}) but losing record ({wins}-{losses})"
                )

        for team, rating in sorted_ratings[-10:]:  # Bottom 10 rated teams
            record = team_records.get(team, {})
            wins = record.get("wins", 0)
            losses = record.get("losses", 0)

            # Bottom 10 rated team with winning record
            if wins > losses + 2:
                misalignments.append(
                    f"{team}: Bottom 10 rating ({rating:.2f}) but winning record ({wins}-{losses})"
                )

        if misalignments:
            print(f"  [WARNING] Found {len(misalignments)} misalignments:")
            for misalignment in misalignments:
                print(f"    - {misalignment}")
                self.warnings.append(misalignment)
        else:
            print("  [OK] No significant misalignments detected")

        return len(self.errors) == 0

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)

        if not self.errors and not self.warnings:
            print("[SUCCESS] All validations passed!")
            print("Data appears accurate and ready for analysis")
            return True

        if self.errors:
            print(f"\n[ERRORS] {len(self.errors)} critical issues found:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n[WARNINGS] {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("\n" + "=" * 70)

        return len(self.errors) == 0


def main():
    """Main validation workflow"""
    print("=" * 70)
    print("NFL DATA VALIDATION")
    print("=" * 70)

    validator = NFLDataValidator()

    # File paths
    games_file = project_root / "data" / "nfl_2025_games_weeks_1_9.json"
    ratings_file = project_root / "data" / "power_ratings" / "nfl_2025_week_09.json"

    # Run validations
    games_valid = validator.validate_games_file(games_file)
    team_records = validator.validate_team_records(games_file)
    ratings_valid = validator.validate_power_ratings(ratings_file, team_records)

    # Print summary
    success = validator.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
