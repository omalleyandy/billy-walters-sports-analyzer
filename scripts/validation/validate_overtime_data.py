#!/usr/bin/env python3
"""
Data Quality Validation Script for Overtime.ag Scraped Data

This script validates scraped odds data to ensure:
1. Spread lines are inverse (home = -away)
2. Total lines are equal (over = under)
3. Prices are within reasonable range
4. Team names are valid
5. Dates and times are properly formatted
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple
from datetime import datetime


class ValidationResult:
    def __init__(self):
        self.total_games = 0
        self.passed = 0
        self.warnings = []
        self.errors = []

    def add_warning(self, game_key: str, message: str):
        self.warnings.append(f"[WARN] {game_key}: {message}")

    def add_error(self, game_key: str, message: str):
        self.errors.append(f"[ERROR] {game_key}: {message}")

    def print_summary(self):
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total Games Validated: {self.total_games}")
        print(f"Passed: {self.passed}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Errors: {len(self.errors)}")

        if self.warnings:
            print("\n" + "-" * 80)
            print("WARNINGS:")
            print("-" * 80)
            for warning in self.warnings[:20]:  # Limit to first 20
                print(warning)
            if len(self.warnings) > 20:
                print(f"... and {len(self.warnings) - 20} more warnings")

        if self.errors:
            print("\n" + "-" * 80)
            print("ERRORS:")
            print("-" * 80)
            for error in self.errors[:20]:  # Limit to first 20
                print(error)
            if len(self.errors) > 20:
                print(f"... and {len(self.errors) - 20} more errors")

        print("\n" + "=" * 80)
        if self.errors:
            print("❌ VALIDATION FAILED")
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS")
        else:
            print("✅ VALIDATION PASSED")
        print("=" * 80 + "\n")


def validate_team_name(name: str) -> bool:
    """Validate that team name is reasonable"""
    if not name or len(name) < 3:
        return False
    # Should contain mostly letters, spaces, and common punctuation
    # No emojis or weird characters
    import re

    return bool(re.match(r"^[A-Za-z0-9\s\-\.&\']+$", name))


def validate_price(price: int, field_name: str) -> Tuple[bool, str]:
    """Validate that price is within reasonable range for American odds"""
    if price is None:
        return True, ""

    if not isinstance(price, int):
        return False, f"{field_name} is not an integer: {type(price)}"

    # American odds typically range from -10000 to +10000
    # Most common range is -1000 to +1000
    if price < -10000 or price > 10000:
        return False, f"{field_name} out of range: {price}"

    if price == 0:
        return False, f"{field_name} is zero (invalid)"

    if -99 < price < 100 and price != 0:
        return False, f"{field_name} is in invalid range (-99 to +99): {price}"

    return True, ""


def validate_line(line: float, field_name: str) -> Tuple[bool, str]:
    """Validate that line is reasonable"""
    if line is None:
        return True, ""

    if not isinstance(line, (int, float)):
        return False, f"{field_name} is not numeric: {type(line)}"

    # Spreads typically -50 to +50
    # Totals typically 0 to 150
    if abs(line) > 150:
        return False, f"{field_name} seems unreasonable: {line}"

    return True, ""


def validate_date(date_str: str) -> Tuple[bool, str]:
    """Validate ISO date format"""
    if not date_str:
        return True, ""  # Date is optional

    try:
        datetime.fromisoformat(date_str)
        return True, ""
    except Exception:
        return False, f"Invalid date format: {date_str}"


def validate_rotation_number(rot_num: str) -> Tuple[bool, str]:
    """Validate rotation number format"""
    if not rot_num:
        return False, "Missing rotation number"

    import re

    # Expected format: "475-476" or "451-452"
    if not re.match(r"^\d{3,4}-\d{3,4}$", rot_num):
        return False, f"Invalid rotation number format: {rot_num}"

    parts = rot_num.split("-")
    away_rot = int(parts[0])
    home_rot = int(parts[1])

    # Typically consecutive odd-even pairs
    if home_rot != away_rot + 1:
        return False, f"Rotation numbers not consecutive: {rot_num}"

    return True, ""


def validate_spread_consistency(away_line: float, home_line: float) -> Tuple[bool, str]:
    """Validate that spread lines are inverse of each other"""
    if away_line is None or home_line is None:
        return True, ""  # Can't validate if missing

    # Home line should be negative of away line
    expected_home = -away_line
    tolerance = 0.01  # Allow tiny floating point differences

    if abs(home_line - expected_home) > tolerance:
        return (
            False,
            f"Spread inconsistency: away={away_line}, home={home_line} (expected {expected_home})",
        )

    return True, ""


def validate_total_consistency(over_line: float, under_line: float) -> Tuple[bool, str]:
    """Validate that total lines are equal"""
    if over_line is None or under_line is None:
        return True, ""  # Can't validate if missing

    tolerance = 0.01

    if abs(over_line - under_line) > tolerance:
        return False, f"Total inconsistency: over={over_line}, under={under_line}"

    return True, ""


def validate_game(game: Dict[str, Any], result: ValidationResult) -> bool:
    """Validate a single game entry"""
    result.total_games += 1

    # Build a game identifier
    away_team = game.get("teams", {}).get("away", "UNKNOWN")
    home_team = game.get("teams", {}).get("home", "UNKNOWN")
    game_key = f"{away_team} @ {home_team}"

    has_errors = False

    # 1. Validate source
    if game.get("source") != "overtime.ag":
        result.add_warning(game_key, f"Unexpected source: {game.get('source')}")

    # 2. Validate team names
    if not validate_team_name(away_team):
        result.add_error(game_key, f"Invalid away team name: '{away_team}'")
        has_errors = True

    if not validate_team_name(home_team):
        result.add_error(game_key, f"Invalid home team name: '{home_team}'")
        has_errors = True

    # 3. Validate rotation number
    rot_num = game.get("rotation_number")
    valid, msg = validate_rotation_number(rot_num)
    if not valid:
        result.add_warning(game_key, msg)

    # 4. Validate date
    event_date = game.get("event_date")
    valid, msg = validate_date(event_date)
    if not valid:
        result.add_error(game_key, msg)
        has_errors = True

    # 5. Validate markets
    markets = game.get("markets", {})

    # Spread market
    spread = markets.get("spread", {})
    away_spread = spread.get("away")
    home_spread = spread.get("home")

    if away_spread:
        valid, msg = validate_line(away_spread.get("line"), "spread.away.line")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

        valid, msg = validate_price(away_spread.get("price"), "spread.away.price")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

    if home_spread:
        valid, msg = validate_line(home_spread.get("line"), "spread.home.line")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

        valid, msg = validate_price(home_spread.get("price"), "spread.home.price")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

    # Check spread consistency
    if away_spread and home_spread:
        valid, msg = validate_spread_consistency(
            away_spread.get("line"), home_spread.get("line")
        )
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

    # Total market
    total = markets.get("total", {})
    over = total.get("over")
    under = total.get("under")

    if over:
        valid, msg = validate_line(over.get("line"), "total.over.line")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

        valid, msg = validate_price(over.get("price"), "total.over.price")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

    if under:
        valid, msg = validate_line(under.get("line"), "total.under.line")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

        valid, msg = validate_price(under.get("price"), "total.under.price")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

    # Check total consistency
    if over and under:
        valid, msg = validate_total_consistency(over.get("line"), under.get("line"))
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

    # Moneyline market
    moneyline = markets.get("moneyline", {})
    ml_away = moneyline.get("away")
    ml_home = moneyline.get("home")

    if ml_away:
        valid, msg = validate_price(ml_away.get("price"), "moneyline.away.price")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

    if ml_home:
        valid, msg = validate_price(ml_home.get("price"), "moneyline.home.price")
        if not valid:
            result.add_error(game_key, msg)
            has_errors = True

    # 6. Check that at least one market exists
    has_spread = bool(away_spread or home_spread)
    has_total = bool(over or under)
    has_ml = bool(ml_away or ml_home)

    if not (has_spread or has_total or has_ml):
        result.add_error(game_key, "No markets found (no spread, total, or moneyline)")
        has_errors = True

    if not has_errors:
        result.passed += 1

    return not has_errors


def validate_jsonl_file(file_path: Path) -> ValidationResult:
    """Validate a JSONL file containing scraped games"""
    result = ValidationResult()

    print(f"Validating: {file_path}")
    print("-" * 80)

    try:
        with open(file_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    game = json.loads(line)

                    # Skip non-overtime.ag sources (e.g., injury data)
                    if game.get("source") not in ["overtime.ag", None]:
                        if (
                            "injury" in str(game.get("source", "")).lower()
                            or "player_name" in game
                        ):
                            continue  # Skip injury reports

                    validate_game(game, result)

                except json.JSONDecodeError as e:
                    result.add_error(f"Line {line_num}", f"JSON parse error: {e}")
                except Exception as e:
                    result.add_error(f"Line {line_num}", f"Validation error: {e}")

    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read file: {e}")
        sys.exit(1)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_overtime_data.py <path_to_jsonl_file>")
        print("\nExample:")
        print(
            "  python validate_overtime_data.py data/overtime_live/overtime-live-20251103-120640.jsonl"
        )
        sys.exit(1)

    file_path = Path(sys.argv[1])

    result = validate_jsonl_file(file_path)
    result.print_summary()

    # Exit with appropriate code
    if result.errors:
        sys.exit(1)  # Errors found
    elif result.warnings:
        sys.exit(0)  # Warnings but no errors
    else:
        sys.exit(0)  # All good


if __name__ == "__main__":
    main()
