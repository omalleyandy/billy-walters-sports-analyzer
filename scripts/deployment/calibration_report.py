"""
E-Factor Calibration Report

Generate weekly calibration report showing:
- Edge accuracy (RMSE)
- ATS performance
- ROI per bet
- E-Factor impact analysis
- Source quality assessment
- Automatic recommendations

Usage:
    # Weekly report (last week)
    uv run python scripts/deployment/calibration_report.py --weeks 1

    # Monthly report (last 4 weeks)
    uv run python scripts/deployment/calibration_report.py --weeks 4

    # Export to JSON
    uv run python scripts/deployment/calibration_report.py --weeks 1 --export

Example workflow:
    1. Week finishes (all games played)
    2. Record all outcomes with record_outcome.py
    3. Run this script to see impact
    4. Review recommendations
    5. Adjust parameters if needed
"""

import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_report(
    weeks: int = 1,
    league: str = "nfl",
    export: bool = False,
) -> bool:
    """
    Generate calibration report.

    Args:
        weeks: Number of weeks to include (default: 1)
        league: "nfl" or "ncaaf"
        export: Export to JSON file

    Returns:
        True if successful
    """
    try:
        from walters_analyzer.core.efactor_calibration import EFactorCalibrator

        calibrator = EFactorCalibrator()
        await calibrator.initialize()

        print("\n" + "=" * 70)
        print(f"E-FACTOR CALIBRATION REPORT - {league.upper()}")
        print("=" * 70)

        # Print report
        await calibrator.print_report(league=league, weeks=weeks)

        # Export if requested
        if export:
            export_path = Path("output/efactor/reports") / (
                f"calibration_{league}_weeks{weeks}.json"
            )
            export_path.parent.mkdir(parents=True, exist_ok=True)
            await calibrator.export_report(str(export_path), league=league, weeks=weeks)
            logger.info(f"✓ Report exported to {export_path}")

        await calibrator.close()
        return True

    except Exception as e:
        logger.error(f"✗ Failed to generate report: {e}")
        return False


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate E-Factor calibration report")
    parser.add_argument(
        "--weeks",
        type=int,
        default=1,
        help="Number of weeks to include (default: 1)",
    )
    parser.add_argument(
        "--league",
        default="nfl",
        choices=["nfl", "ncaaf"],
        help="League",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export to JSON file",
    )

    args = parser.parse_args()

    success = await generate_report(
        weeks=args.weeks,
        league=args.league,
        export=args.export,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
