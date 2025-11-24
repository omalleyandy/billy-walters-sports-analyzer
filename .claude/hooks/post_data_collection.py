#!/usr/bin/env python3
"""
Post-Data Collection Hook
Runs after data collection to validate quality and prepare for analysis.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for season calendar import
sys.path.insert(0, "src")
from walters_analyzer.season_calendar import get_nfl_week, get_ncaaf_week


def load_collection_report(week: int) -> dict:
    """Load the data collection report."""
    report_dir = Path("data/reports")
    report_files = sorted(
        report_dir.glob(f"nfl_week{week}_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not report_files:
        return None

    with open(report_files[0], "r") as f:
        return json.load(f)


def validate_collected_data(week: int) -> dict:
    """Validate data completeness and quality."""
    data_dir = Path("data/current")

    expected_files = [
        f"nfl_week_{week}_games.json",
        f"nfl_week_{week}_teams.json",
        f"nfl_week_{week}_injuries.json",
        f"nfl_week_{week}_weather.json",
        f"nfl_week_{week}_odds_action.json",
    ]

    results = {
        "total_files": len(expected_files),
        "present_files": 0,
        "missing_files": [],
        "file_details": {},
    }

    for filename in expected_files:
        file_path = data_dir / filename
        if file_path.exists():
            results["present_files"] += 1

            # Get file size and last modified
            stat = file_path.stat()
            results["file_details"][filename] = {
                "size_kb": stat.st_size / 1024,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "status": "present",
            }

            # Load and check record count
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                    # Count records based on file type
                    if "games" in data:
                        results["file_details"][filename]["records"] = len(
                            data["games"]
                        )
                    elif "teams" in data:
                        results["file_details"][filename]["records"] = len(
                            data["teams"]
                        )
                    elif "injuries" in data:
                        results["file_details"][filename]["records"] = len(
                            data["injuries"]
                        )
                    elif "weather" in data:
                        results["file_details"][filename]["records"] = len(
                            data["weather"]
                        )
                    elif "odds" in data:
                        results["file_details"][filename]["records"] = len(
                            data.get("odds", {}).get("games", [])
                        )

            except Exception as e:
                results["file_details"][filename]["error"] = str(e)

        else:
            results["missing_files"].append(filename)
            results["file_details"][filename] = {"status": "missing"}

    # Calculate quality score
    completeness_pct = (results["present_files"] / results["total_files"]) * 100
    results["completeness_pct"] = completeness_pct

    if completeness_pct == 100:
        results["quality"] = "EXCELLENT"
    elif completeness_pct >= 80:
        results["quality"] = "GOOD"
    elif completeness_pct >= 60:
        results["quality"] = "FAIR"
    else:
        results["quality"] = "POOR"

    return results


def check_overtime_odds() -> dict:
    """Check for most recent Overtime.ag odds."""
    output_dir = Path("output")
    overtime_files = sorted(
        output_dir.glob("overtime_nfl_walters_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not overtime_files:
        return {"status": "missing", "message": "No Overtime odds files found"}

    latest = overtime_files[0]
    last_modified = datetime.fromtimestamp(latest.stat().st_mtime)
    age_hours = (datetime.now() - last_modified).total_seconds() / 3600

    # Load and count games
    try:
        with open(latest, "r") as f:
            data = json.load(f)
            game_count = len(data.get("games", []))

        return {
            "status": "present",
            "file": latest.name,
            "games": game_count,
            "age_hours": age_hours,
            "last_modified": last_modified.isoformat(),
            "message": f"Found {game_count} games, {age_hours:.1f} hours old",
        }
    except Exception as e:
        return {"status": "error", "message": f"Error reading file: {e}"}


def generate_next_steps(validation_results: dict, overtime_results: dict) -> list:
    """Generate recommended next steps based on results."""
    steps = []

    if validation_results["quality"] == "EXCELLENT":
        steps.append("[OK] Data quality excellent - ready for analysis")
        steps.append("-> Run: /validate-data for detailed quality checks")
        steps.append("-> Run: /edge-detector to find betting value")
        steps.append("-> Run: /betting-card to generate weekly picks")
    elif validation_results["quality"] == "GOOD":
        steps.append("[WARNING] Data quality good - some missing data")
        steps.append(f"-> Missing: {', '.join(validation_results['missing_files'])}")
        steps.append("-> Run: /validate-data for detailed analysis")
        steps.append("-> Consider re-running collection for missing sources")
    else:
        steps.append("[ERROR] Data quality poor - do not proceed with analysis")
        steps.append(f"-> Missing: {', '.join(validation_results['missing_files'])}")
        steps.append("-> Re-run: /collect-all-data to fix issues")

    # Overtime-specific recommendations
    if overtime_results["status"] == "present":
        if overtime_results["games"] == 0:
            steps.append("[WARNING] Overtime scraper found 0 games")
            steps.append("-> Run on Tuesday-Wednesday for best results")
            steps.append("-> Lines may be down (games in progress/completed)")
        elif overtime_results["age_hours"] > 24:
            steps.append("[WARNING] Overtime odds are stale (>24 hours)")
            steps.append("-> Run: /scrape-overtime to refresh")
    else:
        steps.append("[ERROR] No Overtime odds data")
        steps.append("-> Run: /scrape-overtime to collect odds")

    return steps


def main():
    """Run post-collection validation."""
    # Week parameter is now optional - auto-detect if not provided
    if len(sys.argv) >= 2:
        week = int(sys.argv[1])
    else:
        week = get_nfl_week()
        if week is None:
            print("[ERROR] Could not determine current week (offseason/playoffs?)")
            print("Usage: python post_data_collection.py [week]")
            sys.exit(1)
        print(f"Auto-detected current week: {week}")

    print("=" * 70)
    print("POST-DATA COLLECTION VALIDATION")
    print(f"Week {week} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Validate collected data
    print("1. Validating collected data...")
    validation_results = validate_collected_data(week)
    print(f"   Completeness: {validation_results['completeness_pct']:.0f}%")
    print(f"   Quality: {validation_results['quality']}")
    print()

    # File details
    print("2. File details:")
    for filename, details in validation_results["file_details"].items():
        if details["status"] == "present":
            records = details.get("records", "N/A")
            size = details.get("size_kb", 0)
            print(f"   [OK] {filename} ({records} records, {size:.1f} KB)")
        else:
            print(f"   [ERROR] {filename} (missing)")
    print()

    # Check Overtime odds
    print("3. Checking Overtime.ag odds...")
    overtime_results = check_overtime_odds()
    print(f"   {overtime_results['message']}")
    print()

    # Generate next steps
    print("=" * 70)
    print("RECOMMENDED NEXT STEPS")
    print("=" * 70)
    next_steps = generate_next_steps(validation_results, overtime_results)
    for step in next_steps:
        print(step)
    print()

    # Exit code based on quality
    if validation_results["quality"] in ["EXCELLENT", "GOOD"]:
        print("[OK] Data collection complete and validated")
        sys.exit(0)
    else:
        print("[ERROR] Data collection issues detected")
        sys.exit(1)


if __name__ == "__main__":
    main()
