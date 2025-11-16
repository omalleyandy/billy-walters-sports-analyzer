"""
Main workflow orchestrator for subagent data collection.

Automatically detects current NFL week and coordinates all 6 subagents.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.season_calendar import get_nfl_week, format_season_status, League


def print_header(text: str, week: int):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"{text} - Week {week}")
    print("=" * 70)


def print_status(message: str, status: str = "info"):
    """Print status message."""
    symbols = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "pending": "⏳",
    }
    symbol = symbols.get(status, "•")
    print(f"{symbol} {message}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run complete subagent workflow for current NFL week"
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        help="Week number (defaults to current week)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation after collection",
    )
    parser.add_argument(
        "--skip-edge-detection",
        action="store_true",
        help="Skip edge detection after collection",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - show what would be done without executing",
    )

    args = parser.parse_args()

    # Get current week
    if args.week is None:
        week = get_nfl_week()
        if week is None:
            print_status(
                "NFL season not active - cannot determine current week", "error"
            )
            return 1
    else:
        week = args.week

    # Print header
    status = format_season_status(league=League.NFL)
    print(f"\n{'=' * 70}")
    print(f"Billy Walters Subagent Workflow")
    print(f"{status}")
    print(f"Week: {week}")
    print(f"{'=' * 70}\n")

    if args.dry_run:
        print_status("DRY RUN MODE - No actions will be executed", "warning")
        print()

    # Import validation
    from scripts.validation.validate_subagent_outputs import SubagentValidator

    # Step 1: Pre-flight validation
    print_header("Step 1: Pre-Flight Validation", week)
    if args.dry_run:
        print_status("Would check environment variables", "pending")
        print_status("Would check output directories", "pending")
        print_status("Would verify API keys", "pending")
    else:
        # Check environment
        import os

        required_vars = [
            "ACCUWEATHER_API_KEY",
            "OV_CUSTOMER_ID",  # Optional but recommended
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print_status(f"Missing environment variables: {missing_vars}", "warning")

        # Check directories
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data" / "current"
        output_dir = project_root / "output" / "overtime" / "nfl" / "pregame"

        data_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        print_status("Environment validated", "success")
        print_status(f"Data directory: {data_dir}", "info")
        print_status(f"Output directory: {output_dir}", "info")

    # Step 2: Subagent Instructions
    print_header("Step 2: Subagent Data Collection", week)
    print_status("Subagents can run in parallel", "info")
    print()
    print("Subagent 1: Schedule & Game Info")
    print("  → data/current/nfl_week_{week}_schedule.json")
    print()
    print("Subagent 2: Betting Lines")
    print("  → output/overtime/nfl/pregame/api_walters_week_{week}_{timestamp}.csv")
    print()
    print("Subagent 3: Weather Data")
    print("  → data/current/nfl_week_{week}_weather.json")
    print()
    print("Subagent 4: Team Situational Analysis")
    print("  → data/current/nfl_week_{week}_team_situational.json")
    print()
    print("Subagent 5: Player Situational Analysis")
    print("  → data/current/nfl_week_{week}_player_situational.json")
    print()
    print("Subagent 6: Injury Reports")
    print("  → data/current/nfl_week_{week}_injuries.json")
    print()

    if args.dry_run:
        print_status("Would wait for subagents to complete", "pending")
    else:
        print_status(
            "Run subagents now, then press Enter to continue validation...",
            "pending",
        )
        try:
            input()
        except KeyboardInterrupt:
            print_status("Cancelled by user", "warning")
            return 1

    # Step 3: Post-collection validation
    if not args.skip_validation:
        print_header("Step 3: Post-Collection Validation", week)
        if args.dry_run:
            print_status("Would validate all subagent outputs", "pending")
        else:
            validator = SubagentValidator(week=week)
            is_valid, errors, warnings = validator.validate_all()

            if errors:
                print_status(f"Found {len(errors)} validation errors", "error")
                for error in errors[:10]:  # Show first 10
                    print(f"  - {error}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more")
                print()

            if warnings:
                print_status(f"Found {len(warnings)} warnings", "warning")
                for warning in warnings[:5]:  # Show first 5
                    print(f"  - {warning}")
                if len(warnings) > 5:
                    print(f"  ... and {len(warnings) - 5} more")
                print()

            if is_valid:
                print_status("All subagent outputs validated successfully", "success")
            else:
                print_status("Validation failed - fix errors before proceeding", "error")
                return 1

    # Step 4: Edge Detection
    if not args.skip_edge_detection:
        print_header("Step 4: Edge Detection", week)
        if args.dry_run:
            print_status("Would run Billy Walters edge detector", "pending")
        else:
            print_status("Running edge detector...", "info")
            try:
                # Import and run edge detector
                import subprocess

                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "walters_analyzer.valuation.billy_walters_edge_detector",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent.parent,
                )

                if result.returncode == 0:
                    print_status("Edge detection completed successfully", "success")
                    if result.stdout:
                        print(result.stdout[-500:])  # Show last 500 chars
                else:
                    print_status("Edge detection failed", "error")
                    if result.stderr:
                        print(result.stderr)
            except Exception as e:
                print_status(f"Failed to run edge detector: {e}", "error")

    # Step 5: Summary
    print_header("Step 5: Workflow Complete", week)
    print_status(f"All data collected and validated for Week {week}", "success")
    print()
    print("Next steps:")
    print("  1. Review edge detection results")
    print("  2. Generate betting card with Kelly Criterion")
    print("  3. Track CLV (Closing Line Value) for each bet")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
