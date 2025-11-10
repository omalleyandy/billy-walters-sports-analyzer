#!/usr/bin/env python3
"""
Odds Data Validation Script

Validates scraped betting odds data for quality, completeness, and consistency.
"""

import json
import sys
from pathlib import Path
from typing import Any
from collections import defaultdict
from datetime import datetime


class OddsValidator:
    """Validate scraped odds data quality"""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.stats = defaultdict(int)

    def validate_game(self, game: dict[str, Any], index: int) -> bool:
        """
        Validate a single game record.

        Args:
            game: Game dictionary
            index: Game index for error reporting

        Returns:
            True if valid, False if critical errors found
        """
        game_id = f"Game #{index + 1}"
        has_errors = False

        # Check required top-level fields
        required_fields = [
            "source",
            "sport",
            "league",
            "collected_at",
            "rotation_number",
            "event_date",
            "event_time",
            "teams",
            "markets",
            "game_key",
        ]

        for field in required_fields:
            if field not in game or game[field] is None:
                self.issues.append(f"{game_id}: Missing required field '{field}'")
                has_errors = True

        if has_errors:
            return False

        # Validate teams
        teams = game.get("teams", {})
        if not teams.get("away"):
            self.issues.append(f"{game_id}: Missing away team")
            has_errors = True
        if not teams.get("home"):
            self.issues.append(f"{game_id}: Missing home team")
            has_errors = True

        # Validate markets
        markets = game.get("markets", {})
        if not markets:
            self.issues.append(f"{game_id}: No markets data")
            has_errors = True
            return False

        # Validate spread
        spread = markets.get("spread", {})
        if spread:
            self._validate_spread(spread, game_id)

        # Validate total
        total = markets.get("total", {})
        if total:
            self._validate_total(total, game_id)

        # Validate moneyline
        ml = markets.get("moneyline", {})
        if ml:
            self._validate_moneyline(ml, game_id)

        # Validate rotation number format
        rotation = game.get("rotation_number", "")
        if rotation and "-" not in rotation:
            self.warnings.append(
                f"{game_id}: Unusual rotation format '{rotation}'"
            )

        # Validate date format
        event_date = game.get("event_date", "")
        try:
            datetime.fromisoformat(event_date)
        except (ValueError, TypeError):
            self.warnings.append(
                f"{game_id}: Invalid date format '{event_date}'"
            )

        return not has_errors

    def _validate_spread(self, spread: dict[str, Any], game_id: str) -> None:
        """Validate spread market"""
        away = spread.get("away", {})
        home = spread.get("home", {})

        if not away or not home:
            self.warnings.append(f"{game_id}: Incomplete spread data")
            return

        away_line = away.get("line")
        home_line = home.get("line")

        if away_line is None or home_line is None:
            self.issues.append(f"{game_id}: Missing spread lines")
            return

        # Spread lines should be inverse
        if abs(away_line + home_line) > 0.01:  # Allow small floating point error
            self.issues.append(
                f"{game_id}: Spread lines not inverse "
                f"({away_line:+.1f} / {home_line:+.1f})"
            )

        # Validate prices
        away_price = away.get("price")
        home_price = home.get("price")

        if away_price is None or home_price is None:
            self.issues.append(f"{game_id}: Missing spread prices")
        else:
            # Prices should be reasonable
            if not -500 <= away_price <= 500:
                self.warnings.append(
                    f"{game_id}: Unusual away spread price {away_price}"
                )
            if not -500 <= home_price <= 500:
                self.warnings.append(
                    f"{game_id}: Unusual home spread price {home_price}"
                )

    def _validate_total(self, total: dict[str, Any], game_id: str) -> None:
        """Validate total (over/under) market"""
        over = total.get("over", {})
        under = total.get("under", {})

        if not over or not under:
            self.warnings.append(f"{game_id}: Incomplete total data")
            return

        over_line = over.get("line")
        under_line = under.get("line")

        if over_line is None or under_line is None:
            self.issues.append(f"{game_id}: Missing total lines")
            return

        # Over/under lines should match
        if abs(over_line - under_line) > 0.01:
            self.issues.append(
                f"{game_id}: Over/Under lines don't match "
                f"(O {over_line:.1f} / U {under_line:.1f})"
            )

        # Validate prices
        over_price = over.get("price")
        under_price = under.get("price")

        if over_price is None or under_price is None:
            self.issues.append(f"{game_id}: Missing total prices")
        else:
            if not -500 <= over_price <= 500:
                self.warnings.append(
                    f"{game_id}: Unusual over price {over_price}"
                )
            if not -500 <= under_price <= 500:
                self.warnings.append(
                    f"{game_id}: Unusual under price {under_price}"
                )

    def _validate_moneyline(self, ml: dict[str, Any], game_id: str) -> None:
        """Validate moneyline market"""
        away = ml.get("away", {})
        home = ml.get("home", {})

        if not away and not home:
            # Moneyline is optional
            return

        away_price = away.get("price") if away else None
        home_price = home.get("price") if home else None

        if away_price is not None and not -2000 <= away_price <= 2000:
            self.warnings.append(
                f"{game_id}: Unusual away ML price {away_price}"
            )

        if home_price is not None and not -2000 <= home_price <= 2000:
            self.warnings.append(
                f"{game_id}: Unusual home ML price {home_price}"
            )

    def validate_file(self, file_path: str) -> dict[str, Any]:
        """
        Validate entire odds file.

        Args:
            file_path: Path to JSON or JSONL file

        Returns:
            Validation report dictionary
        """
        self.issues = []
        self.warnings = []
        self.stats = defaultdict(int)

        file_path = Path(file_path)

        if not file_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {file_path}",
                "valid": False,
            }

        # Load games
        try:
            if file_path.suffix == ".jsonl":
                games = []
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            games.append(json.loads(line))
            else:  # Assume .json
                with open(file_path, "r", encoding="utf-8") as f:
                    games = json.load(f)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"JSON decode error: {e}",
                "valid": False,
            }

        if not games:
            return {
                "status": "error",
                "error": "No games found in file",
                "valid": False,
            }

        # Validate each game
        valid_games = 0
        for i, game in enumerate(games):
            if self.validate_game(game, i):
                valid_games += 1

            # Collect stats
            self.stats["total_games"] += 1
            if game.get("markets", {}).get("spread"):
                self.stats["games_with_spread"] += 1
            if game.get("markets", {}).get("total"):
                self.stats["games_with_total"] += 1
            if game.get("markets", {}).get("moneyline"):
                self.stats["games_with_moneyline"] += 1

        # Calculate health score (0-100)
        score = 100
        score -= len(self.issues) * 10  # -10 per critical issue
        score -= len(self.warnings) * 2  # -2 per warning
        score = max(0, score)

        return {
            "status": "success",
            "file": str(file_path),
            "total_games": len(games),
            "valid_games": valid_games,
            "issues": self.issues,
            "warnings": self.warnings,
            "stats": dict(self.stats),
            "health_score": score,
            "valid": len(self.issues) == 0,
        }

    def display_report(self, report: dict[str, Any]) -> None:
        """Display formatted validation report"""
        if report["status"] == "error":
            print("\n" + "=" * 80)
            print("VALIDATION ERROR")
            print("=" * 80)
            print(f"\nError: {report['error']}")
            return

        print("\n" + "=" * 80)
        print("ODDS DATA VALIDATION REPORT")
        print("=" * 80)

        print(f"\nFile: {report['file']}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\n>> SUMMARY:")
        print(f"   Total Games: {report['total_games']}")
        print(f"   Valid Games: {report['valid_games']}")
        print(f"   Health Score: {report['health_score']}/100")

        stats = report["stats"]
        print(f"\n>> MARKET COVERAGE:")
        print(
            f"   Spread: {stats.get('games_with_spread', 0)}"
            f"/{report['total_games']} "
            f"({stats.get('games_with_spread', 0)/report['total_games']*100:.1f}%)"
        )
        print(
            f"   Total:  {stats.get('games_with_total', 0)}"
            f"/{report['total_games']} "
            f"({stats.get('games_with_total', 0)/report['total_games']*100:.1f}%)"
        )
        print(
            f"   Moneyline: {stats.get('games_with_moneyline', 0)}"
            f"/{report['total_games']} "
            f"({stats.get('games_with_moneyline', 0)/report['total_games']*100:.1f}%)"
        )

        if report["issues"]:
            print(f"\n>> CRITICAL ISSUES ({len(report['issues'])}):")
            for issue in report["issues"][:10]:  # Show first 10
                print(f"   [!] {issue}")
            if len(report["issues"]) > 10:
                print(f"   ... and {len(report['issues']) - 10} more")
        else:
            print(f"\n>> CRITICAL ISSUES: None found")

        if report["warnings"]:
            print(f"\n>> WARNINGS ({len(report['warnings'])}):")
            for warning in report["warnings"][:10]:
                print(f"   [*] {warning}")
            if len(report["warnings"]) > 10:
                print(f"   ... and {len(report['warnings']) - 10} more")
        else:
            print(f"\n>> WARNINGS: None found")

        # Overall status
        print(f"\n>> STATUS:", end=" ")
        if report["valid"]:
            print("PASS (Excellent quality)")
        elif report["health_score"] >= 80:
            print("PASS (Good quality with minor warnings)")
        elif report["health_score"] >= 60:
            print("WARNING (Acceptable quality, issues found)")
        else:
            print("FAIL (Poor quality, significant issues)")

        print("\n" + "=" * 80 + "\n")


def main():
    """CLI interface for odds validation"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate scraped betting odds data"
    )
    parser.add_argument(
        "file", nargs="?", help="Path to JSON or JSONL odds file"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of formatted report",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Validate latest odds file from data/odds/nfl/",
    )

    args = parser.parse_args()

    # Determine file to validate
    if args.latest:
        odds_dir = Path("data/odds/nfl")
        if not odds_dir.exists():
            print(
                f"Error: Odds directory not found: {odds_dir}", file=sys.stderr
            )
            sys.exit(1)

        json_files = sorted(odds_dir.glob("*.json"))
        if not json_files:
            print(f"Error: No odds files found in {odds_dir}", file=sys.stderr)
            sys.exit(1)

        file_path = json_files[-1]  # Most recent
        print(f"Validating latest file: {file_path.name}")
    elif args.file:
        file_path = Path(args.file)
    else:
        parser.error("Either provide a file argument or use --latest")

    # Validate
    validator = OddsValidator()
    report = validator.validate_file(str(file_path))

    # Output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        validator.display_report(report)

    # Exit code based on validation result
    if report["status"] == "error":
        sys.exit(2)
    elif not report["valid"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
