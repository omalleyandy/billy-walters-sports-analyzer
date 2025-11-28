"""
Record E-Factor Prediction

Called immediately after generating picks to record edge and E-Factor details.

Usage:
    uv run python scripts/deployment/record_prediction.py \\
        --game KC@DAL \\
        --week 13 \\
        --edge 5.5 \\
        --efactor -2.0 \\
        --sources espn_injuries,nfl_news

Example workflow:
    1. Run /edge-detector → generates picks with edges and E-Factors
    2. Run this script → records prediction to DB
    3. Play the game
    4. Run record_outcome.py → records result and calculates impact
    5. Run /efactor-calibration → view impact analysis
"""

import asyncio
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def record_prediction(
    game: str,
    week: int,
    edge: float,
    efactor: float = 0.0,
    sources: str = "",
    league: str = "nfl",
) -> bool:
    """
    Record edge prediction with E-Factor details.

    Args:
        game: Game ID (e.g., "KC@DAL")
        week: Week number
        edge: Predicted edge percentage
        efactor: E-Factor adjustment in points
        sources: Comma-separated list of E-Factor sources
        league: "nfl" or "ncaaf"

    Returns:
        True if successful
    """
    try:
        from walters_analyzer.core.efactor_calibration import EFactorCalibrator

        calibrator = EFactorCalibrator()
        await calibrator.initialize()

        # Parse game ID
        away_team, home_team = game.split("@")

        # Record prediction
        await calibrator.record_prediction(
            game_id=game,
            week=week,
            team=away_team,
            league=league,
            predicted_edge_pct=edge,
            efactor_adjustment=efactor,
            efactor_sources=sources.split(",") if sources else [],
        )

        logger.info(
            f"✓ Recorded prediction: {game} Week {week}, "
            f"edge={edge:+.1f}%, E-Factor={efactor:+.1f}pts"
        )

        await calibrator.close()
        return True

    except Exception as e:
        logger.error(f"✗ Failed to record prediction: {e}")
        return False


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Record edge prediction")
    parser.add_argument("--game", required=True, help="Game ID (e.g., KC@DAL)")
    parser.add_argument("--week", type=int, required=True, help="Week number")
    parser.add_argument("--edge", type=float, required=True, help="Predicted edge %")
    parser.add_argument(
        "--efactor", type=float, default=0.0, help="E-Factor adjustment (pts)"
    )
    parser.add_argument(
        "--sources", default="", help="Comma-separated E-Factor sources"
    )
    parser.add_argument(
        "--league", default="nfl", choices=["nfl", "ncaaf"], help="League"
    )

    args = parser.parse_args()

    success = await record_prediction(
        game=args.game,
        week=args.week,
        edge=args.edge,
        efactor=args.efactor,
        sources=args.sources,
        league=args.league,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
