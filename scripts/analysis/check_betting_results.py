#!/usr/bin/env python3
"""
Betting Results Checker CLI
Fetches actual scores, calculates performance vs predictions, generates reports.

Usage:
    python check_betting_results.py --league nfl --week 12
    python check_betting_results.py --league ncaaf --week 13
"""

import sys
from datetime import datetime
from pathlib import Path
from argparse import ArgumentParser

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.performance.results_checker import BettingResultsChecker
from walters_analyzer.season_calendar import get_nfl_week


def main():
    """Main CLI entry point"""
    parser = ArgumentParser(
        description="Check betting predictions against actual results"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="nfl",
        help="League to check (default: nfl)",
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        help="Week number (auto-detect NFL if not provided)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        default=True,
        help="Save report to file (default: true)",
    )

    args = parser.parse_args()

    # Auto-detect NFL week if not provided
    if args.league == "nfl" and args.week is None:
        args.week = get_nfl_week()
        if args.week is None:
            print("[ERROR] Could not auto-detect NFL week - provide --week")
            return 1

    print(f"[*] Checking {args.league.upper()} Week {args.week} results...")
    print()

    # Initialize checker
    checker = BettingResultsChecker()

    try:
        # Check results
        results = checker.check_results(league=args.league, week=args.week)

        if not results:
            print(
                f"[WARNING] No results found for {args.league.upper()} Week {args.week}"
            )
            return 0

        # Generate report
        print(f"[*] Generating performance report for {len(results)} games...")
        report = checker.generate_report(results, league=args.league, week=args.week)

        # Print report
        print()
        print(report)
        print()

        # Save report
        if args.save:
            filepath = checker.save_report(report, league=args.league, week=args.week)
            print()
            print(f"[OK] Report saved to: {filepath}")

        return 0

    except Exception as e:
        print(f"[ERROR] {e}")
        return 1

    finally:
        checker.close()


if __name__ == "__main__":
    sys.exit(main())
