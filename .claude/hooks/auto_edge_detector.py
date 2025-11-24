#!/usr/bin/env python3
"""
Auto Edge Detector Hook
Automatically runs edge detection for both NFL and NCAAF when new odds data
is available.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for season calendar import
sys.path.insert(0, "src")
from walters_analyzer.season_calendar import get_nfl_week, get_ncaaf_week


def check_for_new_nfl_odds() -> tuple[bool, dict]:
    """Check if new NFL odds data is available."""
    output_dir = Path("output/overtime/nfl/pregame")

    # Find most recent NFL odds file
    overtime_files = sorted(
        output_dir.glob("api_walters_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not overtime_files:
        return (False, {"message": "No NFL odds files found"})

    latest_file = overtime_files[0]
    last_modified = datetime.fromtimestamp(latest_file.stat().st_mtime)
    age_minutes = (datetime.now() - last_modified).total_seconds() / 60

    # Consider odds "new" if less than 5 minutes old
    is_new = age_minutes < 5

    return (
        is_new,
        {
            "file": latest_file.name,
            "age_minutes": age_minutes,
            "last_modified": last_modified.isoformat(),
        },
    )


def check_for_new_ncaaf_odds() -> tuple[bool, dict]:
    """Check if new NCAAF odds data is available."""
    output_dir = Path("output/overtime/ncaaf/pregame")

    # Find most recent NCAAF odds file
    overtime_files = sorted(
        output_dir.glob("api_walters_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not overtime_files:
        return (False, {"message": "No NCAAF odds files found"})

    latest_file = overtime_files[0]
    last_modified = datetime.fromtimestamp(latest_file.stat().st_mtime)
    age_minutes = (datetime.now() - last_modified).total_seconds() / 60

    # Consider odds "new" if less than 5 minutes old
    is_new = age_minutes < 5

    return (
        is_new,
        {
            "file": latest_file.name,
            "age_minutes": age_minutes,
            "last_modified": last_modified.isoformat(),
        },
    )


def run_nfl_edge_detector(week: int) -> bool:
    """Run NFL edge detection analysis."""
    print(f"\n[SEARCH] Running NFL edge detection for week {week}...")
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
            print("[OK] NFL edge detection completed successfully")
            return True
        else:
            print("[ERROR] NFL edge detection failed")
            print("Error:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("[ERROR] NFL edge detection timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Error running NFL edge detector: {e}")
        return False


def run_ncaaf_edge_detector(week: int) -> bool:
    """Run NCAAF edge detection analysis."""
    print(f"\n[SEARCH] Running NCAAF edge detection for week {week}...")
    print("-" * 70)

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "walters_analyzer.valuation.ncaaf_edge_detector",
                "--week",
                str(week),
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            print("[OK] NCAAF edge detection completed successfully")
            return True
        else:
            print("[ERROR] NCAAF edge detection failed")
            print("Error:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("[ERROR] NCAAF edge detection timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Error running NCAAF edge detector: {e}")
        return False


def main():
    """Main hook execution."""
    print("=" * 70)
    print("AUTO EDGE DETECTION HOOK (NFL + NCAAF)")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    nfl_success = False
    ncaaf_success = False

    # Check for new NFL odds
    print("1. Checking for new NFL odds data...")
    has_new_nfl_odds, nfl_odds_info = check_for_new_nfl_odds()

    if has_new_nfl_odds:
        nfl_week = get_nfl_week()
        if nfl_week is not None:
            print(f"   [OK] New NFL odds detected")
            print(f"   Age: {nfl_odds_info['age_minutes']:.1f} minutes")
            print()
            nfl_success = run_nfl_edge_detector(nfl_week)
        else:
            print("   [WARNING] NFL offseason - skipping NFL edge detection")
    else:
        message = nfl_odds_info.get("message", "No new NFL odds available")
        print(f"   No new NFL odds: {message}")

    print()

    # Check for new NCAAF odds
    print("2. Checking for new NCAAF odds data...")
    has_new_ncaaf_odds, ncaaf_odds_info = check_for_new_ncaaf_odds()

    if has_new_ncaaf_odds:
        ncaaf_week = get_ncaaf_week()
        if ncaaf_week is not None:
            print(f"   [OK] New NCAAF odds detected")
            print(f"   Age: {ncaaf_odds_info['age_minutes']:.1f} minutes")
            print()
            ncaaf_success = run_ncaaf_edge_detector(ncaaf_week)
        else:
            print("   [WARNING] NCAAF offseason - skipping NCAAF edge detection")
    else:
        message = ncaaf_odds_info.get("message", "No new NCAAF odds available")
        print(f"   No new NCAAF odds: {message}")

    print()
    print("=" * 70)

    # Summary
    if nfl_success or ncaaf_success:
        print("[OK] AUTO EDGE DETECTION COMPLETE")
        print()
        if nfl_success:
            print("  -> NFL edges generated")
        if ncaaf_success:
            print("  -> NCAAF edges generated")
        print()
        print("Next steps:")
        print("  -> Review edge detection results")
        print("  -> Run: /betting-card to generate picks")
        print("  -> Run: /clv-tracker to track performance")
    else:
        print("[INFO] NO EDGE DETECTION NEEDED")
        print()
        print("Recommendations:")
        print("  -> Run: /scrape-overtime to collect fresh odds")
        print("  -> Or manually run: /edge-detector")

    print("=" * 70)

    sys.exit(0)


if __name__ == "__main__":
    main()
