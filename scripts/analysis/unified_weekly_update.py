#!/usr/bin/env python3
"""
Unified Weekly Update Script - Billy Walters Sports Analyzer

Complete workflow to be run every Tuesday after Monday Night Football:
1. Fetch completed game results
2. Update power ratings with 90/10 formula
3. Run edge detection (spreads + totals)
4. Generate comprehensive reports
5. Save weekly snapshots

Usage:
    python scripts/unified_weekly_update.py --week 11
    python scripts/unified_weekly_update.py --week 11 --skip-edge-detection
    python scripts/unified_weekly_update.py --week 11 --games-file custom_games.json
"""

import json
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class UnifiedWeeklyUpdater:
    """
    Complete weekly update workflow for Billy Walters system
    """

    def __init__(self, week_num: int, skip_edge_detection: bool = False):
        """
        Initialize unified updater

        Args:
            week_num: Week number to update (1-18)
            skip_edge_detection: Skip edge detection step (for testing)
        """
        self.week_num = week_num
        self.skip_edge_detection = skip_edge_detection
        self.project_root = project_root

        # Output directories
        self.ratings_dir = self.project_root / "data" / "power_ratings"
        self.reports_dir = self.project_root / "output" / "weekly_reports"
        self.edge_dir = self.project_root / "output" / "edge_detection"

        # Create directories
        self.ratings_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.edge_dir.mkdir(parents=True, exist_ok=True)

        # Results storage
        self.results = {
            "week": week_num,
            "timestamp": datetime.now().isoformat(),
            "steps_completed": [],
            "errors": [],
        }

    def print_header(self) -> None:
        """Print workflow header"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("BILLY WALTERS SPORTS ANALYZER - UNIFIED WEEKLY UPDATE")
        logger.info(f"Week {self.week_num} - 2025 NFL Season")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        logger.info("")

    def step_1_update_power_ratings(self, games_file: Optional[str] = None) -> bool:
        """
        Step 1: Update power ratings with 90/10 formula

        Args:
            games_file: Optional custom games file

        Returns:
            True if successful, False otherwise
        """
        logger.info("")
        logger.info("-" * 80)
        logger.info("STEP 1: UPDATE POWER RATINGS (90/10 FORMULA)")
        logger.info("-" * 80)

        try:
            # Import updater
            sys.path.insert(0, str(self.project_root / "scripts"))
            from weekly_power_rating_update import WeeklyPowerRatingUpdater

            # Run power rating update
            updater = WeeklyPowerRatingUpdater(week_num=self.week_num)
            updater.run_update(games_file=games_file)

            self.results["steps_completed"].append("power_ratings")
            logger.info("[OK] Power ratings updated successfully")
            return True

        except Exception as e:
            error_msg = f"Power rating update failed: {e}"
            logger.error(f"[FAILED] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def step_2_run_edge_detection_spreads(self) -> bool:
        """
        Step 2: Run edge detection for spreads

        Returns:
            True if successful, False otherwise
        """
        if self.skip_edge_detection:
            logger.info("\n[SKIPPED] Edge detection (--skip-edge-detection flag)")
            return True

        logger.info("")
        logger.info("-" * 80)
        logger.info("STEP 2: EDGE DETECTION - SPREADS")
        logger.info("-" * 80)

        try:
            # Run edge detector
            edge_detector_path = self.project_root / "billy_walters_edge_detector.py"

            if not edge_detector_path.exists():
                logger.warning(f"Edge detector not found: {edge_detector_path}")
                return False

            # Execute edge detector
            result = subprocess.run(
                [sys.executable, str(edge_detector_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("[OK] Spread edge detection completed")
                logger.info(f"\nEdge Detection Output:\n{result.stdout}")
                self.results["steps_completed"].append("edge_detection_spreads")
                return True
            else:
                logger.error(f"[FAILED] Edge detection failed: {result.stderr}")
                self.results["errors"].append(f"Edge detection: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            error_msg = "Edge detection timed out after 5 minutes"
            logger.error(f"[FAILED] {error_msg}")
            self.results["errors"].append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Edge detection failed: {e}"
            logger.error(f"[FAILED] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def step_3_run_totals_detection(self) -> bool:
        """
        Step 3: Run totals edge detection

        Returns:
            True if successful, False otherwise
        """
        if self.skip_edge_detection:
            logger.info("\n[SKIPPED] Totals detection (--skip-edge-detection flag)")
            return True

        logger.info("")
        logger.info("-" * 80)
        logger.info("STEP 3: EDGE DETECTION - TOTALS (OVER/UNDER)")
        logger.info("-" * 80)

        try:
            # Run totals detector
            totals_detector_path = (
                self.project_root / "billy_walters_totals_detector.py"
            )

            if not totals_detector_path.exists():
                logger.warning(f"Totals detector not found: {totals_detector_path}")
                logger.info("Skipping totals detection")
                return True

            # Execute totals detector
            result = subprocess.run(
                [sys.executable, str(totals_detector_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                logger.info("[OK] Totals edge detection completed")
                logger.info(f"\nTotals Detection Output:\n{result.stdout}")
                self.results["steps_completed"].append("edge_detection_totals")
                return True
            else:
                logger.warning(
                    f"[WARNING] Totals detection had issues: {result.stderr}"
                )
                return True  # Non-critical, don't fail workflow

        except subprocess.TimeoutExpired:
            logger.warning("[WARNING] Totals detection timed out")
            return True  # Non-critical
        except Exception as e:
            logger.warning(f"[WARNING] Totals detection failed: {e}")
            return True  # Non-critical

    def step_4_generate_weekly_report(self) -> bool:
        """
        Step 4: Generate comprehensive weekly report

        Returns:
            True if successful, False otherwise
        """
        logger.info("")
        logger.info("-" * 80)
        logger.info("STEP 4: GENERATE WEEKLY REPORT")
        logger.info("-" * 80)

        try:
            # Load week's power ratings
            ratings_file = self.ratings_dir / f"nfl_2025_week_{self.week_num:02d}.json"

            if not ratings_file.exists():
                logger.warning(f"Ratings file not found: {ratings_file}")
                return False

            with open(ratings_file, "r") as f:
                ratings_data = json.load(f)

            # Generate report
            report = {
                "week": self.week_num,
                "season": "2025",
                "timestamp": datetime.now().isoformat(),
                "power_ratings": {
                    "top_10_teams": self._get_top_10_from_ratings(ratings_data),
                    "total_teams": len(ratings_data.get("ratings", {})),
                    "games_processed": ratings_data.get("games_processed_total", 0),
                },
                "edges_detected": self._load_edges_summary(),
                "workflow_results": self.results,
            }

            # Save report
            report_file = self.reports_dir / f"week_{self.week_num:02d}_report.json"
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

            logger.info(f"[OK] Weekly report saved to: {report_file}")

            # Print summary
            self._print_report_summary(report)

            self.results["steps_completed"].append("weekly_report")
            return True

        except Exception as e:
            error_msg = f"Report generation failed: {e}"
            logger.error(f"[FAILED] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def _get_top_10_from_ratings(self, ratings_data: Dict) -> List[Dict]:
        """Extract top 10 teams from ratings data"""
        ratings = ratings_data.get("ratings", {})

        # Convert to list and sort
        teams_list = [
            {"team": team, "rating": rating} for team, rating in ratings.items()
        ]
        teams_list.sort(key=lambda x: x["rating"], reverse=True)

        return teams_list[:10]

    def _load_edges_summary(self) -> Dict:
        """Load summary of detected edges"""
        summary = {
            "spreads": {"count": 0, "file": None},
            "totals": {"count": 0, "file": None},
        }

        # Check for spread edges
        spread_file = self.edge_dir / "nfl_edges_detected.jsonl"
        if spread_file.exists():
            with open(spread_file, "r") as f:
                edges = [json.loads(line) for line in f]
                summary["spreads"]["count"] = len(edges)
                summary["spreads"]["file"] = str(spread_file)

        # Check for totals edges
        totals_file = self.edge_dir / "totals_report.txt"
        if totals_file.exists():
            summary["totals"]["file"] = str(totals_file)
            # Count edges in totals file
            with open(totals_file, "r") as f:
                content = f.read()
                # Simple count of "Edge:" occurrences
                summary["totals"]["count"] = content.count("Edge:")

        return summary

    def _print_report_summary(self, report: Dict) -> None:
        """Print summary of weekly report"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("WEEKLY UPDATE SUMMARY")
        logger.info("=" * 80)

        # Power ratings
        logger.info(f"\nPower Ratings (Week {self.week_num}):")
        top_10 = report["power_ratings"]["top_10_teams"]
        for i, team_data in enumerate(top_10, 1):
            logger.info(f"  {i:2d}. {team_data['team']:20s} {team_data['rating']:.2f}")

        # Edges detected
        edges = report["edges_detected"]
        logger.info("\nEdges Detected:")
        logger.info(f"  Spreads: {edges['spreads']['count']}")
        logger.info(f"  Totals:  {edges['totals']['count']}")

        # Steps completed
        logger.info("\nWorkflow Status:")
        for step in [
            "power_ratings",
            "edge_detection_spreads",
            "edge_detection_totals",
            "weekly_report",
        ]:
            status = "[OK]" if step in self.results["steps_completed"] else "[SKIP]"
            logger.info(f"  {status} {step}")

        # Errors
        if self.results["errors"]:
            logger.info(f"\nErrors ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")

        logger.info("")
        logger.info("=" * 80)

    def run_full_workflow(self, games_file: Optional[str] = None) -> bool:
        """
        Execute complete weekly update workflow

        Args:
            games_file: Optional custom games file

        Returns:
            True if all critical steps succeeded, False otherwise
        """
        self.print_header()

        # Step 1: Update power ratings (CRITICAL)
        if not self.step_1_update_power_ratings(games_file):
            logger.error("\n[FAILED] Workflow aborted - Power ratings update failed")
            return False

        # Step 2: Edge detection - spreads (CRITICAL)
        if not self.step_2_run_edge_detection_spreads():
            logger.warning("\n[WARNING] Edge detection failed, continuing workflow")

        # Step 3: Edge detection - totals (NON-CRITICAL)
        self.step_3_run_totals_detection()

        # Step 4: Generate report (NON-CRITICAL)
        self.step_4_generate_weekly_report()

        # Final summary
        logger.info("")
        logger.info("=" * 80)
        if not self.results["errors"]:
            logger.info("[SUCCESS] WEEKLY UPDATE COMPLETED SUCCESSFULLY")
        else:
            logger.info("[WARNING] WEEKLY UPDATE COMPLETED WITH ERRORS")
        logger.info(f"Week {self.week_num} ready for betting analysis")
        logger.info("=" * 80)
        logger.info("")

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified weekly update for Billy Walters system"
    )
    parser.add_argument(
        "--week", type=int, required=True, help="NFL week number to update (1-18)"
    )
    parser.add_argument(
        "--games-file",
        type=str,
        help="Path to JSON file containing game results (optional)",
    )
    parser.add_argument(
        "--skip-edge-detection",
        action="store_true",
        help="Skip edge detection steps (for testing power ratings only)",
    )

    args = parser.parse_args()

    # Validate week number
    if not 1 <= args.week <= 18:
        logger.error(f"Invalid week number: {args.week}. Must be 1-18")
        sys.exit(1)

    # Run unified workflow
    updater = UnifiedWeeklyUpdater(
        week_num=args.week, skip_edge_detection=args.skip_edge_detection
    )

    success = updater.run_full_workflow(games_file=args.games_file)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
