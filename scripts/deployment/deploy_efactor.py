"""
E-Factor Production Deployment Script

Initializes E-Factor system for production use:
1. Sets up real data integrator
2. Initializes calibration database
3. Creates output directories
4. Tests all components
5. Generates health report

Run once before production use:
    uv run python scripts/deployment/deploy_efactor.py --league nfl
    uv run python scripts/deployment/deploy_efactor.py --league ncaaf

Usage in production:
    - Data collection: Integrated into /collect-all-data
    - Edge detection: Integrated into /edge-detector
    - Calibration: After each game week with /efactor-calibration

Components initialized:
    - RealDataIntegrator: Fetches injuries/news from ESPN, NFL.com
    - EFactorCalibrator: SQLite DB at output/efactor/calibration.db
    - NewsDecayFunction: Time-based impact reduction
    - SourceQualityTracker: Source reliability scoring
    - NewsInjuryEFactorAggregator: Edge calculator integration
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def deploy_efactor(league: str = "nfl") -> bool:
    """
    Deploy E-Factor system to production.

    Args:
        league: "nfl" or "ncaaf"

    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 70)
    print("E-FACTOR PRODUCTION DEPLOYMENT")
    print("=" * 70)

    # Step 1: Create output directories
    print("\n[1/6] Creating output directories...")
    output_dir = Path("output/efactor")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data").mkdir(exist_ok=True)
    (output_dir / "reports").mkdir(exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)
    print(f"[OK] Created: {output_dir}")

    # Step 2: Initialize Real Data Integrator
    print("\n[2/6] Initializing Real Data Integrator...")
    try:
        from walters_analyzer.data_integration.real_data_integrator import (
            RealDataIntegrator,
        )

        integrator = RealDataIntegrator(output_dir=str(output_dir / "data"))
        await integrator.initialize()
        logger.info("[OK] Real Data Integrator initialized")

        # Test data fetch
        test_team = "DAL" if league == "nfl" else "LSU"
        injuries = await integrator.fetch_nfl_injuries(test_team)
        if injuries:
            logger.info(f"[OK] Test fetch successful: {test_team}")
        else:
            logger.warning(f"[WARNING] Test fetch returned no data for {test_team}")

        await integrator.close()

    except Exception as e:
        logger.error(f"[ERROR] Real Data Integrator failed: {e}")
        return False

    # Step 3: Initialize Calibration System
    print("\n[3/6] Initializing E-Factor Calibration...")
    try:
        from walters_analyzer.core.efactor_calibration import EFactorCalibrator

        calibrator = EFactorCalibrator(db_path=str(output_dir / "calibration.db"))
        await calibrator.initialize()
        logger.info(f"[OK] Calibration DB created: {output_dir / 'calibration.db'}")
        await calibrator.close()

    except Exception as e:
        logger.error(f"[ERROR] Calibration initialization failed: {e}")
        return False

    # Step 4: Test Decay Function
    print("\n[4/6] Testing Decay Function...")
    try:
        from walters_analyzer.core.efactor_decay import NewsDecayFunction

        decay = NewsDecayFunction()

        # Test decay calculation
        original = -8.0
        decayed = decay.apply_decay(
            original_impact=original,
            days_elapsed=3,
            event_type="key_player_out",
        )
        confidence = decay.get_recency_confidence(
            days_since_news=0,
            signal_strength="VERY_STRONG",
        )

        logger.info(
            f"[OK] Decay function working: {original} -> {decayed:.1f} pts, "
            f"confidence: {confidence:+.0%}"
        )

    except Exception as e:
        logger.error(f"[ERROR] Decay function test failed: {e}")
        return False

    # Step 5: Test Source Quality Tracker
    print("\n[5/6] Testing Source Quality Tracker...")
    try:
        from walters_analyzer.core.efactor_source_quality import (
            SourceQualityTracker,
        )

        tracker = SourceQualityTracker(data_dir=str(output_dir / "quality"))
        tracker.record_observation(
            source_name="espn_injuries",
            event_id="test_001",
            event_type="injury",
            observation={"player": "Test", "status": "out"},
            actual_outcome={"player": "Test", "status": "out"},
            accuracy_score=1.0,
            latency_hours=0.5,
        )
        score = tracker.get_source_score("espn_injuries")
        logger.info(
            f"[OK] Source quality tracker working: ESPN score = "
            f"{score.overall_score:.2f}"
        )

    except Exception as e:
        logger.error(f"[ERROR] Source quality tracker failed: {e}")
        return False

    # Step 6: Test Integration with Edge Calculator
    print("\n[6/6] Testing Edge Calculator Integration...")
    try:
        from walters_analyzer.core.integrated_edge_calculator import (
            IntegratedEdgeCalculator,
        )

        calc = IntegratedEdgeCalculator(enable_efactor=True)
        logger.info("[OK] Edge calculator with E-Factor support initialized")

    except Exception as e:
        logger.error(f"[ERROR] Edge calculator integration failed: {e}")
        return False

    # Print deployment summary
    print("\n" + "=" * 70)
    print("DEPLOYMENT SUMMARY")
    print("=" * 70)
    print("\n[OK] E-Factor system deployed successfully!")
    print(f"\nOutput directory: {output_dir}")
    print(f"Calibration DB: {output_dir / 'calibration.db'}")
    print(f"Data cache: {output_dir / 'data'}")
    print(f"Reports: {output_dir / 'reports'}")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Daily Data Collection:")
    print("   /collect-all-data  # E-Factor integrated")
    print("\n2. Run Edge Detection:")
    print("   /edge-detector     # Fetches E-Factor data automatically")
    print("\n3. Record Predictions (after generating picks):")
    print("   uv run python scripts/deployment/record_prediction.py \\")
    print("     --game KC@DAL --week 13 --edge 5.5 --efactor -2.0")
    print("\n4. Record Outcomes (after games):")
    print("   uv run python scripts/deployment/record_outcome.py \\")
    print("     --game KC@DAL --result WIN --margin 3.5")
    print("\n5. Generate Calibration Report (weekly):")
    print("   uv run python scripts/deployment/calibration_report.py --weeks 1")

    print("\n" + "=" * 70)
    print(f"Deployed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    return True


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy E-Factor system to production")
    parser.add_argument(
        "--league",
        default="nfl",
        choices=["nfl", "ncaaf"],
        help="League to deploy for",
    )

    args = parser.parse_args()

    success = await deploy_efactor(league=args.league)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
