#!/usr/bin/env python3
"""
Auto Edge Detector Hook
Automatically runs edge detection when new odds data is available.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def check_for_new_odds() -> tuple[bool, dict]:
    """Check if new odds data is available."""
    output_dir = Path("output")

    # Find most recent Overtime odds file
    overtime_files = sorted(
        output_dir.glob("overtime_nfl_walters_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not overtime_files:
        return (False, {"message": "No Overtime odds files found"})

    latest_file = overtime_files[0]
    last_modified = datetime.fromtimestamp(latest_file.stat().st_mtime)
    age_minutes = (datetime.now() - last_modified).total_seconds() / 60

    # Consider odds "new" if less than 5 minutes old
    is_new = age_minutes < 5

    # Load game count
    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
            game_count = len(data.get("games", []))
    except Exception as e:
        return (False, {"message": f"Error reading odds file: {e}"})

    return (
        is_new,
        {
            "file": latest_file.name,
            "games": game_count,
            "age_minutes": age_minutes,
            "last_modified": last_modified.isoformat(),
        },
    )


def check_edge_detection_status() -> dict:
    """Check if edge detection was recently run."""
    edge_dir = Path("data/current")
    edge_files = sorted(
        edge_dir.glob("edge_detection_week_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not edge_files:
        return {"exists": False, "message": "No edge detection results found"}

    latest_file = edge_files[0]
    last_modified = datetime.fromtimestamp(latest_file.stat().st_mtime)
    age_minutes = (datetime.now() - last_modified).total_seconds() / 60

    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
            edge_count = len(data.get("edges", []))

        return {
            "exists": True,
            "file": latest_file.name,
            "edges": edge_count,
            "age_minutes": age_minutes,
            "last_modified": last_modified.isoformat(),
        }
    except Exception as e:
        return {"exists": False, "message": f"Error reading edge file: {e}"}


def run_edge_detector(week: int) -> bool:
    """Run edge detection analysis."""
    print(f"\n🔍 Running edge detection for week {week}...")
    print("-" * 70)

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "walters_analyzer.valuation.billy_walters_edge_detector",
                "--week",
                str(week),
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            print("[OK] Edge detection completed successfully")
            print()
            print("Output:")
            print(result.stdout)
            return True
        else:
            print("[ERROR] Edge detection failed")
            print("Error:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("[ERROR] Edge detection timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Error running edge detector: {e}")
        return False


def main():
    """Main hook execution."""
    print("=" * 70)
    print("AUTO EDGE DETECTION HOOK")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Check for new odds
    print("1. Checking for new odds data...")
    has_new_odds, odds_info = check_for_new_odds()

    if not has_new_odds:
        message = odds_info.get('message', 'No new odds available')
        print(f"   No new odds data: {message}")
        print()
        print("   Recommendation: Run /scrape-overtime to collect odds")
        sys.exit(0)

    print(f"   [OK] New odds detected: {odds_info['games']} games")
    print(f"   Age: {odds_info['age_minutes']:.1f} minutes")
    print()

    # Check edge detection status
    print("2. Checking edge detection status...")
    edge_status = check_edge_detection_status()

    if edge_status["exists"]:
        age_diff = edge_status["age_minutes"] - odds_info["age_minutes"]

        if age_diff > -10:  # Edge detection is recent enough
            print(
                f"   [OK] Edge detection already run {edge_status['age_minutes']:.1f} minutes ago"
            )
            print(f"   Found {edge_status['edges']} edges")
            print()
            print("   No need to re-run edge detection")
            sys.exit(0)

    print("   Edge detection needed")
    print()

    # Determine week from odds data
    try:
        with open(Path("output") / odds_info["file"], "r") as f:
            data = json.load(f)
            week = data.get("week", 10)  # Default to week 10
    except:
        week = 10

    # Run edge detector
    print(f"3. Running edge detector for week {week}...")
    success = run_edge_detector(week)

    print()
    print("=" * 70)
    if success:
        print("[OK] AUTO EDGE DETECTION COMPLETE")
        print()
        print("Next steps:")
        print("  -> Review edge detection results")
        print("  -> Run: /betting-card to generate picks")
        print("  -> Run: /clv-tracker to track performance")
    else:
        print("[ERROR] AUTO EDGE DETECTION FAILED")
        print()
        print("Troubleshooting:")
        print("  -> Check data/current for required input files")
        print("  -> Run: /validate-data to check data quality")
        print("  -> Manually run: /edge-detector")

    print("=" * 70)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
