#!/usr/bin/env python3
"""
Pre-Edge Detection Hook
Validates required data exists before running edge detector.
Prevents wasted computation on missing/stale data.
"""

import sys
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_nfl_week() -> int:
    """Get current NFL week."""
    try:
        project_root = get_project_root()
        sys.path.insert(0, str(project_root / "src"))

        from walters_analyzer.season_calendar import get_nfl_week

        week = get_nfl_week()
        return week if week else 0
    except Exception:
        return 0


def check_required_data() -> tuple[bool, list[str], list[str]]:
    """
    Check if required data exists for edge detection.

    Returns:
        tuple: (all_required_exist, required_errors, optional_warnings)
    """
    project_root = get_project_root()
    current_week = get_nfl_week()

    required_errors = []
    optional_warnings = []

    # Required data
    required_files = {
        "Power Ratings": project_root / "data" / "current" / "nfl_power_ratings_2025.json",
        "Game Schedule": project_root / "data" / "current" / f"nfl_week_{current_week}_games.json",
        "Odds Data": project_root / "output" / "overtime_nfl_walters_*.json",
    }

    # Optional data
    optional_files = {
        "Injury Reports": project_root / "data" / "current" / f"nfl_injuries_week_{current_week}.json",
        "Weather Data": project_root / "data" / "current" / f"nfl_weather_week_{current_week}.json",
    }

    # Check required files
    for name, path in required_files.items():
        if '*' in str(path):
            # Handle glob patterns
            matches = list(path.parent.glob(path.name))
            if not matches:
                required_errors.append(f"{name}: No files found")
            else:
                # Check freshness
                latest = max(matches, key=lambda f: f.stat().st_mtime)
                age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600

                if name == "Odds Data" and age_hours > 24:
                    required_errors.append(
                        f"{name}: Data is {age_hours:.0f}h old (STALE - should be <24h)"
                    )
        else:
            if not path.exists():
                required_errors.append(f"{name}: File not found ({path.name})")

    # Check optional files
    for name, path in optional_files.items():
        if not path.exists():
            optional_warnings.append(f"{name}: Not collected (edges will be less accurate)")

    all_required_exist = len(required_errors) == 0

    return all_required_exist, required_errors, optional_warnings


def display_validation_results(
    can_proceed: bool,
    errors: list[str],
    warnings: list[str]
) -> None:
    """Display validation results."""
    print("=" * 70)
    print("PRE-EDGE DETECTION VALIDATION")
    print("=" * 70)
    print()

    print("Required Data:")

    if not errors:
        print("  [OK] Power ratings: Present")
        print("  [OK] Game schedule: Present")
        print("  [OK] Odds data: Present and fresh")
    else:
        for error in errors:
            print(f"  [X] {error}")

    print()

    if warnings:
        print("Optional Data:")
        for warning in warnings:
            print(f"  [!] {warning}")
        print()

    # Validation result
    print("=" * 70)

    if can_proceed:
        if warnings:
            print("VALIDATION: PASSED (with warnings)")
            print()
            print("Edge detection can proceed, but results may be less accurate")
            print("without injury/weather data.")
            print()
            print("Recommendations:")
            if any("Injury" in w for w in warnings):
                print("  -> Run: /injury-report nfl")
            if any("Weather" in w for w in warnings):
                print("  -> Run: /weather to collect game-day forecasts")
            print()
            print("Proceeding with edge detection...")
        else:
            print("VALIDATION: PASSED")
            print()
            print("All required and optional data present.")
            print("Edge detection ready to run.")
    else:
        print("VALIDATION: FAILED")
        print()
        print("Cannot proceed with edge detection - missing required data.")
        print()
        print("Please run the following commands to collect data:")
        print("  1. /collect-all-data (recommended - collects everything)")
        print("  OR run individual commands:")
        if any("Power Ratings" in e for e in errors):
            print("  2. /power-ratings")
        if any("Game Schedule" in e for e in errors):
            print("  3. /update-data (to fetch schedule)")
        if any("Odds Data" in e for e in errors):
            print("  4. /scrape-overtime")

    print("=" * 70)
    print()


def main():
    """Main validation routine."""
    can_proceed, errors, warnings = check_required_data()

    display_validation_results(can_proceed, errors, warnings)

    # Exit code: 0 = proceed, 1 = block
    sys.exit(0 if can_proceed else 1)


if __name__ == "__main__":
    main()
