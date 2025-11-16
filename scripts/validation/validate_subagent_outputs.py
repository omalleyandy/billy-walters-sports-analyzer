"""
Validation helpers for subagent data collection outputs.

Validates each of the 6 subagent outputs against Billy Walters methodology requirements.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.season_calendar import get_nfl_week, get_week_date_range, League


class SubagentValidator:
    """Validates subagent data collection outputs."""

    def __init__(self, week: Optional[int] = None, data_dir: Path = None):
        """
        Initialize validator.

        Args:
            week: Week number (defaults to current week)
            data_dir: Base data directory (defaults to project root / data/current)
        """
        if week is None:
            week = get_nfl_week()
            if week is None:
                raise ValueError("NFL season not active - cannot determine week")

        self.week = week
        self.season = 2025

        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data" / "current"

        self.data_dir = Path(data_dir)
        self.output_dir = (
            Path(__file__).parent.parent.parent
            / "output"
            / "overtime"
            / "nfl"
            / "pregame"
        )

        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all subagent outputs.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()

        # Validate each subagent
        self.validate_schedule()
        self.validate_betting_lines()
        self.validate_weather()
        self.validate_team_situational()
        self.validate_player_situational()
        self.validate_injuries()

        # Cross-validation
        self.cross_validate_game_ids()

        is_valid = len(self.errors) == 0
        return (is_valid, self.errors.copy(), self.warnings.copy())

    def validate_schedule(self) -> bool:
        """Validate Subagent 1: Schedule & Game Info."""
        file_path = self.data_dir / f"nfl_week_{self.week}_schedule.json"

        if not file_path.exists():
            self.errors.append(f"Schedule file not found: {file_path}")
            return False

        try:
            with open(file_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in schedule file: {e}")
            return False

        # Validate structure
        required_keys = ["week", "season", "scraped_at", "games"]
        for key in required_keys:
            if key not in data:
                self.errors.append(f"Schedule missing required key: {key}")
                return False

        # Validate week matches
        if data["week"] != self.week:
            self.errors.append(
                f"Week mismatch in schedule: expected {self.week}, got {data['week']}"
            )

        # Validate games
        games = data["games"]
        if not isinstance(games, list):
            self.errors.append("Schedule 'games' must be a list")
            return False

        # Should have ~16 games (some teams on bye)
        if len(games) < 13 or len(games) > 16:
            self.warnings.append(
                f"Expected 13-16 games, found {len(games)} (some teams may be on bye)"
            )

        # Validate each game
        game_ids = set()
        for i, game in enumerate(games):
            if not isinstance(game, dict):
                self.errors.append(f"Game {i} is not a dictionary")
                continue

            # Required fields
            required_game_fields = [
                "game_id",
                "week",
                "date",
                "time",
                "home_team",
                "away_team",
                "stadium",
            ]
            for field in required_game_fields:
                if field not in game:
                    self.errors.append(f"Game {i} missing required field: {field}")

            # Validate game_id format
            if "game_id" in game:
                game_id = game["game_id"]
                if not game_id.startswith(f"NFL_{self.season}_{self.week}_"):
                    self.errors.append(
                        f"Game {i} has invalid game_id format: {game_id}"
                    )
                if game_id in game_ids:
                    self.errors.append(f"Duplicate game_id: {game_id}")
                game_ids.add(game_id)

            # Validate stadium has is_dome flag
            if "stadium" in game and isinstance(game["stadium"], dict):
                if "is_dome" not in game["stadium"]:
                    self.errors.append(
                        f"Game {i} stadium missing 'is_dome' flag (critical for weather)"
                    )

            # Validate dates fall within week
            if "date" in game:
                try:
                    game_date = datetime.fromisoformat(
                        game["date"].replace("Z", "+00:00")
                    )
                    week_start, week_end = get_week_date_range(self.week, League.NFL)
                    if not (week_start <= game_date.date() <= week_end):
                        self.warnings.append(
                            f"Game {i} date {game['date']} falls outside Week {self.week} range"
                        )
                except (ValueError, AttributeError):
                    self.errors.append(
                        f"Game {i} has invalid date format: {game.get('date')}"
                    )

        return len(self.errors) == 0

    def validate_betting_lines(self) -> bool:
        """Validate Subagent 2: Betting Lines."""
        # Find latest odds file for this week
        pattern = f"api_walters_week_{self.week}_*.csv"
        matching_files = list(self.output_dir.glob(pattern))

        if not matching_files:
            self.errors.append(
                f"No betting lines CSV found matching pattern: {pattern}"
            )
            return False

        # Use most recent file
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)

        try:
            df = pd.read_csv(latest_file)
        except Exception as e:
            self.errors.append(f"Failed to read betting lines CSV: {e}")
            return False

        # Required columns
        required_columns = [
            "game_id",
            "away_team",
            "home_team",
            "spread",
            "total",
            "moneyline_away",
            "moneyline_home",
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.errors.append(f"Betting lines CSV missing columns: {missing_columns}")
            return False

        # Validate game_id format
        invalid_game_ids = df[
            ~df["game_id"].str.startswith(f"NFL_{self.season}_{self.week}_")
        ]
        if not invalid_game_ids.empty:
            self.errors.append(
                f"{len(invalid_game_ids)} games have invalid game_id format"
            )

        # Validate spread is reasonable (-50 to +50)
        invalid_spreads = df[(df["spread"] < -50) | (df["spread"] > 50)]
        if not invalid_spreads.empty:
            self.errors.append(f"{len(invalid_spreads)} games have unrealistic spreads")

        # Validate total is reasonable (20 to 100)
        invalid_totals = df[(df["total"] < 20) | (df["total"] > 100)]
        if not invalid_totals.empty:
            self.errors.append(f"{len(invalid_totals)} games have unrealistic totals")

        # Validate book margin (should be ~4-5%)
        if "spread_odds_home" in df.columns and "spread_odds_away" in df.columns:
            # Check if odds sum to reasonable margin
            pass  # Could add margin calculation validation

        return len(self.errors) == 0

    def validate_weather(self) -> bool:
        """Validate Subagent 3: Weather Data."""
        file_path = self.data_dir / f"nfl_week_{self.week}_weather.json"

        if not file_path.exists():
            self.errors.append(f"Weather file not found: {file_path}")
            return False

        try:
            with open(file_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in weather file: {e}")
            return False

        # Validate structure
        if "games" not in data:
            self.errors.append("Weather file missing 'games' key")
            return False

        games = data["games"]
        if not isinstance(games, list):
            self.errors.append("Weather 'games' must be a list")
            return False

        # Validate each game
        for i, game in enumerate(games):
            if not isinstance(game, dict):
                self.errors.append(f"Weather game {i} is not a dictionary")
                continue

            # Required fields
            if "game_id" not in game:
                self.errors.append(f"Weather game {i} missing game_id")
                continue

            # Validate dome stadiums have weather: null
            if "is_dome" in game and game["is_dome"]:
                if "weather" in game and game["weather"] is not None:
                    self.warnings.append(
                        f"Game {game.get('game_id')} is dome but has weather data (should be null)"
                    )

            # Validate outdoor stadiums have weather data
            if "is_dome" in game and not game["is_dome"]:
                if "weather" not in game or game["weather"] is None:
                    self.errors.append(
                        f"Game {game.get('game_id')} is outdoor but missing weather data"
                    )
                elif isinstance(game["weather"], dict):
                    # Validate Billy Walters adjustments exist
                    if "billy_walters_adjustments" not in game:
                        self.warnings.append(
                            f"Game {game.get('game_id')} missing Billy Walters adjustments"
                        )

        return len(self.errors) == 0

    def validate_team_situational(self) -> bool:
        """Validate Subagent 4: Team Situational Analysis."""
        file_path = self.data_dir / f"nfl_week_{self.week}_team_situational.json"

        if not file_path.exists():
            self.errors.append(f"Team situational file not found: {file_path}")
            return False

        try:
            with open(file_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in team situational file: {e}")
            return False

        # Validate structure
        if "teams" not in data:
            self.errors.append("Team situational file missing 'teams' key")
            return False

        teams = data["teams"]
        if not isinstance(teams, list):
            self.errors.append("Team situational 'teams' must be a list")
            return False

        # Should have 32 teams
        if len(teams) != 32:
            self.warnings.append(f"Expected 32 teams, found {len(teams)}")

        # Validate each team
        for i, team in enumerate(teams):
            if not isinstance(team, dict):
                self.errors.append(f"Team {i} is not a dictionary")
                continue

            # Validate power ratings exist
            if "power_rating" not in team:
                self.errors.append(f"Team {i} missing power_rating")
                continue

            pr = team["power_rating"]
            if not isinstance(pr, dict):
                self.errors.append(f"Team {i} power_rating is not a dictionary")
                continue

            # Validate power rating values (70-100 scale)
            if "overall" in pr:
                overall = pr["overall"]
                if not isinstance(overall, (int, float)) or not (70 <= overall <= 100):
                    self.warnings.append(
                        f"Team {i} power rating {overall} outside expected range (70-100)"
                    )

            # Validate S-factors within caps
            if "situational_factors" in team:
                sf = team["situational_factors"]
                if "total_s_factor_adjustment" in sf:
                    adj = sf["total_s_factor_adjustment"]
                    if abs(adj) > 2.0:
                        self.errors.append(
                            f"Team {i} S-factor adjustment {adj} exceeds ±2.0 cap"
                        )

        # Validate game-level S-factors
        if "games" in data:
            for game in data["games"]:
                if "matchup_situational" in game:
                    ms = game["matchup_situational"]
                    if "net_s_factor" in ms:
                        net = ms["net_s_factor"]
                        if abs(net) > 3.0:
                            self.errors.append(
                                f"Game {game.get('game_id')} net S-factor {net} exceeds ±3.0 cap"
                            )

        return len(self.errors) == 0

    def validate_player_situational(self) -> bool:
        """Validate Subagent 5: Player Situational Analysis."""
        file_path = self.data_dir / f"nfl_week_{self.week}_player_situational.json"

        if not file_path.exists():
            self.errors.append(f"Player situational file not found: {file_path}")
            return False

        try:
            with open(file_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in player situational file: {e}")
            return False

        # Validate structure
        if "teams" not in data:
            self.errors.append("Player situational file missing 'teams' key")
            return False

        teams = data["teams"]
        if not isinstance(teams, list):
            self.errors.append("Player situational 'teams' must be a list")
            return False

        # Validate each team
        for i, team in enumerate(teams):
            if not isinstance(team, dict):
                self.errors.append(f"Team {i} is not a dictionary")
                continue

            # Validate cumulative impact within cap
            if "cumulative_player_impact" in team:
                impact = team["cumulative_player_impact"]
                if abs(impact) > 3.0:
                    self.errors.append(
                        f"Team {i} cumulative player impact {impact} exceeds ±3.0 cap"
                    )

        return len(self.errors) == 0

    def validate_injuries(self) -> bool:
        """Validate Subagent 6: Injury Reports."""
        file_path = self.data_dir / f"nfl_week_{self.week}_injuries.json"

        if not file_path.exists():
            self.errors.append(f"Injury file not found: {file_path}")
            return False

        try:
            with open(file_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in injury file: {e}")
            return False

        # Validate structure
        if "teams" not in data:
            self.errors.append("Injury file missing 'teams' key")
            return False

        teams = data["teams"]
        if not isinstance(teams, list):
            self.errors.append("Injury 'teams' must be a list")
            return False

        # Validate each team
        for team in teams:
            if not isinstance(team, dict):
                continue

            # Validate injury summary
            if "injury_summary" in team:
                summary = team["injury_summary"]
                if "cumulative_point_impact" in summary:
                    impact = summary["cumulative_point_impact"]
                    if abs(impact) > 3.0:
                        self.errors.append(
                            f"Team {team.get('team')} injury impact {impact} exceeds ±3.0 cap"
                        )

            # Validate status values
            if "injuries" in team:
                for injury in team["injuries"]:
                    if "status" in injury:
                        status = injury["status"]
                        valid_statuses = ["out", "doubtful", "questionable", "probable"]
                        if status not in valid_statuses:
                            self.errors.append(
                                f"Invalid injury status: {status} (must be one of {valid_statuses})"
                            )

        # Validate game-level injury caps
        if "games" in data:
            for game in data["games"]:
                if "injury_matchup" in game:
                    im = game["injury_matchup"]
                    if "net_injury_adjustment" in im:
                        net = im["net_injury_adjustment"]
                        if abs(net) > 5.0:
                            self.errors.append(
                                f"Game {game.get('game_id')} net injury adjustment {net} exceeds ±5.0 cap"
                            )

        return len(self.errors) == 0

    def cross_validate_game_ids(self) -> bool:
        """Cross-validate game_ids match across all files."""
        # Load schedule to get master game_id list
        schedule_path = self.data_dir / f"nfl_week_{self.week}_schedule.json"
        if not schedule_path.exists():
            return False

        try:
            with open(schedule_path) as f:
                schedule_data = json.load(f)
        except Exception:
            return False

        schedule_game_ids = {g["game_id"] for g in schedule_data.get("games", [])}

        # Check betting lines
        pattern = f"api_walters_week_{self.week}_*.csv"
        matching_files = list(self.output_dir.glob(pattern))
        if matching_files:
            try:
                df = pd.read_csv(max(matching_files, key=lambda p: p.stat().st_mtime))
                odds_game_ids = set(df["game_id"].unique())
                missing = schedule_game_ids - odds_game_ids
                if missing:
                    self.warnings.append(
                        f"{len(missing)} games in schedule missing from betting lines"
                    )
                extra = odds_game_ids - schedule_game_ids
                if extra:
                    self.warnings.append(
                        f"{len(extra)} games in betting lines not in schedule"
                    )
            except Exception:
                pass

        # Similar checks for other files could be added

        return True


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate subagent outputs")
    parser.add_argument(
        "--week", type=int, default=None, help="Week number (defaults to current week)"
    )
    parser.add_argument(
        "--data-dir", type=str, default=None, help="Data directory path"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show warnings")

    args = parser.parse_args()

    validator = SubagentValidator(week=args.week, data_dir=args.data_dir)
    is_valid, errors, warnings = validator.validate_all()

    # Print results
    if errors:
        print("❌ VALIDATION ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print()

    if warnings and args.verbose:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()

    if is_valid:
        print(
            f"✅ All subagent outputs validated successfully for Week {validator.week}"
        )
        return 0
    else:
        print(f"❌ Validation failed for Week {validator.week}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
