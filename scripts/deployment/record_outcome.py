"""
Record Game Outcome

Called after game finishes to record result and calculate E-Factor impact.

Usage:
    uv run python scripts/deployment/record_outcome.py \\
        --game KC@DAL \\
        --result WIN \\
        --margin 3.5 \\
        --clv 0.05

Example workflow:
    1. Run /edge-detector → generates picks with edges
    2. Run record_prediction.py → records prediction to DB
    3. Play the game
    4. Run this script → records result and calculates impact
    5. Run /efactor-calibration → view calibration report

Result options:
    WIN   - Prediction was correct (beat spread)
    LOSS  - Prediction was incorrect (lost to spread)
    PUSH  - Game landed exactly on spread
"""

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def record_outcome(
    game: str,
    result: str,
    margin: float,
    clv: float = 0.0,
    league: str = "nfl",
) -> bool:
    """
    Record game outcome and E-Factor impact.

    Args:
        game: Game ID (e.g., "KC@DAL")
        result: "WIN", "LOSS", or "PUSH"
        margin: Actual point margin
        clv: Closing Line Value (closing line - closing price you got)
        league: "nfl" or "ncaaf"

    Returns:
        True if successful
    """
    if result not in ["WIN", "LOSS", "PUSH"]:
        logger.error(f"✗ Invalid result: {result}. Use WIN/LOSS/PUSH")
        return False

    try:
        from walters_analyzer.core.efactor_calibration import EFactorCalibrator

        calibrator = EFactorCalibrator()
        await calibrator.initialize()

        # Record outcome
        await calibrator.record_outcome(
            game_id=game,
            actual_result=result,
            actual_margin=margin,
            closing_line_value=clv,
        )

        logger.info(
            f"✓ Recorded outcome: {game} {result}, margin={margin:+.1f}, CLV={clv:+.2f}"
        )

        # Get updated metrics
        metrics = await calibrator.get_calibration_report(league=league)
        logger.info(
            f"  ATS: {metrics.ats_win_rate:.1f}% ({metrics.ats_wins}-{metrics.ats_losses})"
        )
        logger.info(f"  ROI: {metrics.roi_per_bet_pct:+.2f}%")
        logger.info(f"  E-Factor impact: {metrics.efactor_impact_avg:+.2f} pts avg")

        await calibrator.close()
        return True

    except Exception as e:
        logger.error(f"✗ Failed to record outcome: {e}")
        return False


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Record game outcome")
    parser.add_argument("--game", required=True, help="Game ID (e.g., KC@DAL)")
    parser.add_argument(
        "--result",
        required=True,
        choices=["WIN", "LOSS", "PUSH"],
        help="Result (WIN/LOSS/PUSH)",
    )
    parser.add_argument("--margin", type=float, required=True, help="Point margin")
    parser.add_argument("--clv", type=float, default=0.0, help="Closing Line Value")
    parser.add_argument(
        "--league", default="nfl", choices=["nfl", "ncaaf"], help="League"
    )

    args = parser.parse_args()

    success = await record_outcome(
        game=args.game,
        result=args.result,
        margin=args.margin,
        clv=args.clv,
        league=args.league,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
