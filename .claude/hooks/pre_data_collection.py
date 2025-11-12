#!/usr/bin/env python3
"""
Pre-Data Collection Hook
Runs before data collection to validate environment and prerequisites.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def check_environment_variables() -> tuple[bool, list[str]]:
    """Check required environment variables are set."""
    required = {
        "OV_CUSTOMER_ID": "Overtime.ag authentication",
        "OV_PASSWORD": "Overtime.ag authentication",
    }

    optional = {
        "ACCUWEATHER_API_KEY": "Weather forecasting",
        "OPENWEATHER_API_KEY": "Weather forecasting (fallback)",
        "ACTION_USERNAME": "Action Network odds",
        "ACTION_PASSWORD": "Action Network odds",
    }

    errors = []
    warnings = []

    # Check required
    for var, purpose in required.items():
        if not os.getenv(var):
            errors.append(f"Missing required: {var} ({purpose})")

    # Check optional (at least one weather API)
    weather_apis = [
        os.getenv("ACCUWEATHER_API_KEY"),
        os.getenv("OPENWEATHER_API_KEY"),
    ]
    if not any(weather_apis):
        warnings.append(
            "No weather API keys found (ACCUWEATHER_API_KEY or OPENWEATHER_API_KEY)"
        )

    # Check Action Network (optional but recommended)
    if not os.getenv("ACTION_USERNAME") or not os.getenv("ACTION_PASSWORD"):
        warnings.append(
            "Action Network credentials not found (sharp action data unavailable)"
        )

    return (len(errors) == 0, errors + warnings)


def check_output_directories() -> tuple[bool, list[str]]:
    """Ensure output directories exist."""
    dirs_to_check = [
        "data/current",
        "output",
        "logs/validation",
        "data/reports",
    ]

    errors = []

    for dir_path in dirs_to_check:
        path = Path(dir_path)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")

    return (len(errors) == 0, errors)


def check_current_week() -> tuple[int, str]:
    """Detect current NFL week."""
    try:
        # Try to import season calendar
        sys.path.insert(0, "src")
        from walters_analyzer.season_calendar import get_nfl_week

        week = get_nfl_week()
        if week is None:
            return (None, "offseason or playoffs")
        return (week, "auto-detected")
    except Exception as e:
        # If import fails, return None to indicate error
        return (None, f"detection failed: {e}")


def check_last_collection() -> dict:
    """Check when data was last collected."""
    data_dir = Path("data/current")

    if not data_dir.exists():
        return {
            "last_collected": None,
            "age_hours": None,
            "stale": True,
            "message": "No previous data collection found",
        }

    # Find most recent file
    files = list(data_dir.glob("nfl_week_*_games.json"))
    if not files:
        return {
            "last_collected": None,
            "age_hours": None,
            "stale": True,
            "message": "No game data files found",
        }

    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    last_modified = datetime.fromtimestamp(latest_file.stat().st_mtime)
    age_hours = (datetime.now() - last_modified).total_seconds() / 3600

    # Data is stale if >24 hours old
    stale = age_hours > 24

    return {
        "last_collected": last_modified.isoformat(),
        "age_hours": age_hours,
        "stale": stale,
        "file": latest_file.name,
        "message": f"Last collected {age_hours:.1f} hours ago"
        + (" (STALE)" if stale else " (FRESH)"),
    }


def main():
    """Run pre-collection checks."""
    print("=" * 70)
    print("PRE-DATA COLLECTION VALIDATION")
    print("=" * 70)
    print()

    all_checks_passed = True
    warnings = []

    # Check 1: Environment variables
    print("1. Checking environment variables...")
    env_ok, env_messages = check_environment_variables()
    if env_ok:
        print("   [OK] All required environment variables present")
    else:
        print("   [ERROR] Environment variable issues:")
        for msg in env_messages:
            if "Missing required" in msg:
                print(f"     ERROR: {msg}")
                all_checks_passed = False
            else:
                print(f"     WARNING: {msg}")
                warnings.append(msg)
    print()

    # Check 2: Output directories
    print("2. Checking output directories...")
    dirs_ok, dir_messages = check_output_directories()
    if dirs_ok:
        print("   [OK] All output directories ready")
    else:
        print("   [ERROR] Directory issues:")
        for msg in dir_messages:
            print(f"     ERROR: {msg}")
        all_checks_passed = False
    print()

    # Check 3: Current week
    print("3. Detecting current NFL week...")
    current_week, detection_method = check_current_week()
    print(f"   Current week: {current_week} ({detection_method})")
    print()

    # Check 4: Last collection
    print("4. Checking last data collection...")
    last_collection = check_last_collection()
    print(f"   {last_collection['message']}")
    if last_collection["stale"]:
        warnings.append("Data is stale (>24 hours old) - collection recommended")
        print("   [WARNING] Data collection recommended")
    print()

    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if all_checks_passed:
        print("[OK] PRE-FLIGHT CHECKS PASSED")
        print()
        print("Ready to collect data for week", current_week)

        if warnings:
            print()
            print(f"Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  [WARNING] {warning}")

        print()
        print("Recommended command:")
        print(
            f"  uv run python scripts/utilities/update_all_data.py --week {current_week}"
        )

        sys.exit(0)
    else:
        print("[ERROR] PRE-FLIGHT CHECKS FAILED")
        print()
        print("Please resolve the errors above before collecting data.")
        sys.exit(1)


if __name__ == "__main__":
    main()
