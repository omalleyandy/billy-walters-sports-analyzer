#!/usr/bin/env python3
"""
ESPN Impact Analysis - Compare spread predictions with/without ESPN metrics

Measures how ESPN team statistics affect Billy Walters spread predictions
by running edge detection twice:
1. WITHOUT ESPN enhancement (baseline)
2. WITH ESPN enhancement (enhanced)

Tracks differences in spread predictions and identifies which metrics drive changes.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.valuation.billy_walters_edge_detector import (
    BillyWaltersEdgeDetector,
    PowerRating,
)
from walters_analyzer.valuation.espn_integration import (
    ESPNDataLoader,
    PowerRatingEnhancer,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SpreadComparison:
    """Comparison of a single spread prediction"""

    game_id: str
    matchup: str
    away_team: str
    home_team: str
    away_rating_baseline: float
    home_rating_baseline: float
    away_rating_enhanced: float
    home_rating_enhanced: float
    predicted_spread_baseline: float
    predicted_spread_enhanced: float
    spread_delta: float
    market_spread: float
    edge_baseline: float
    edge_enhanced: float
    edge_improvement: float

    def __str__(self) -> str:
        """Format for display"""
        arrow = "↑" if self.spread_delta > 0 else "↓" if self.spread_delta < 0 else "→"
        return (
            f"{self.matchup}\n"
            f"  Baseline: {self.predicted_spread_baseline:+.1f} "
            f"(edge: {self.edge_baseline:+.1f})\n"
            f"  Enhanced: {self.predicted_spread_enhanced:+.1f} "
            f"(edge: {self.edge_enhanced:+.1f}) {arrow}{self.spread_delta:+.1f}\n"
            f"  Market:   {self.market_spread:+.1f}"
        )


@dataclass
class AnalysisSummary:
    """Summary statistics for ESPN impact analysis"""

    league: str
    games_analyzed: int
    avg_spread_delta: float
    max_spread_delta: float
    games_with_edge_improvement: int
    avg_edge_improvement: float
    largest_improvement: float
    largest_degradation: float
    timestamp: datetime
    data_files_used: Dict[str, str]


class ESPNImpactAnalyzer:
    """Analyze impact of ESPN metrics on spread predictions"""

    def __init__(self, league: str = "nfl"):
        """Initialize analyzer"""
        self.league = league.lower()
        self.detector_baseline = BillyWaltersEdgeDetector()
        self.detector_enhanced = BillyWaltersEdgeDetector()
        self.comparisons: List[SpreadComparison] = []
        self.output_dir = Path("output/espn_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_power_ratings(self) -> Tuple[bool, str]:
        """
        Load power ratings for both baseline and enhanced detectors

        Returns:
            (success: bool, message: str)
        """
        logger.info(f"Loading power ratings for {self.league.upper()}...")

        # Try to load Massey ratings (required for both)
        massey_path = Path("data/current") / f"massey_ratings_{self.league}.json"

        if not massey_path.exists():
            return (
                False,
                f"Massey ratings not found: {massey_path}",
            )

        # Load for baseline
        if not self.detector_baseline.load_massey_ratings(
            str(massey_path), league=self.league
        ):
            return False, "Failed to load Massey ratings for baseline"

        # Load for enhanced
        if not self.detector_enhanced.load_massey_ratings(
            str(massey_path), league=self.league
        ):
            return False, "Failed to load Massey ratings for enhanced"

        logger.info(
            f"Loaded {len(self.detector_baseline.power_ratings)} teams "
            f"from Massey ratings"
        )

        return True, "Power ratings loaded"

    def enhance_with_espn(self) -> Tuple[bool, str]:
        """
        Load and apply ESPN enhancement to enhanced detector

        Returns:
            (success: bool, message: str)
        """
        logger.info(f"Loading ESPN team statistics for {self.league.upper()}...")

        # Load ESPN stats for enhanced detector
        espn_loader = ESPNDataLoader()
        latest_file = espn_loader.find_latest_team_stats(league=self.league)

        if not latest_file:
            return False, "No ESPN team stats files found"

        # Load team stats
        espn_stats = espn_loader.load_team_stats(latest_file)
        if not espn_stats:
            return False, "Failed to load ESPN team statistics"

        # Store in detector
        self.detector_enhanced.espn_team_stats = espn_stats

        # Apply enhancement
        self.detector_enhanced.enhance_power_ratings_with_espn(league=self.league)

        logger.info(f"Enhanced {len(self.detector_enhanced.power_ratings)} ratings")
        return True, f"ESPN stats loaded from {latest_file.name}"

    def load_game_schedules(self) -> Tuple[bool, str]:
        """
        Load game schedules with odds

        Returns:
            (success: bool, message: str)
        """
        logger.info("Loading game schedules...")

        schedule_path = (
            Path("data/current") / f"game_schedule_{self.league}.json"
        )

        if not schedule_path.exists():
            return False, f"Schedule not found: {schedule_path}"

        try:
            with open(schedule_path, "r") as f:
                schedule_data = json.load(f)
            logger.info(f"Loaded {len(schedule_data)} games")
            return True, "Schedule loaded"
        except Exception as e:
            return False, f"Error loading schedule: {e}"

    def compare_spreads(self) -> List[SpreadComparison]:
        """
        Compare spread predictions between baseline and enhanced

        Returns:
            List of spread comparisons
        """
        logger.info("Comparing spread predictions...")

        self.comparisons = []

        # Get games from detector (power ratings)
        for team_name, power_rating in (
            self.detector_baseline.power_ratings.items()
        ):
            if not hasattr(power_rating, "game_id"):
                continue

            # Find matching enhanced rating
            if team_name not in self.detector_enhanced.power_ratings:
                logger.warning(f"Team {team_name} not found in enhanced ratings")
                continue

            baseline_rating = self.detector_baseline.power_ratings[team_name]
            enhanced_rating = self.detector_enhanced.power_ratings[team_name]

            # Calculate spread difference
            spread_delta = (
                enhanced_rating.rating - baseline_rating.rating
            )

            # Create comparison (you'll need to extract actual game data)
            # For now, this is a template
            comparison = SpreadComparison(
                game_id=getattr(baseline_rating, "game_id", "unknown"),
                matchup=f"{team_name} matchup",
                away_team=getattr(baseline_rating, "away_team", ""),
                home_team=getattr(baseline_rating, "home_team", ""),
                away_rating_baseline=baseline_rating.rating,
                home_rating_baseline=0.0,  # Will be populated
                away_rating_enhanced=enhanced_rating.rating,
                home_rating_enhanced=0.0,  # Will be populated
                predicted_spread_baseline=baseline_rating.rating,
                predicted_spread_enhanced=enhanced_rating.rating,
                spread_delta=spread_delta,
                market_spread=0.0,  # Load from odds data
                edge_baseline=0.0,  # Calculate from comparisons
                edge_enhanced=0.0,  # Calculate from comparisons
                edge_improvement=0.0,  # Calculate
            )

            self.comparisons.append(comparison)

        logger.info(f"Created {len(self.comparisons)} comparisons")
        return self.comparisons

    def generate_report(self) -> AnalysisSummary:
        """Generate impact analysis report"""

        logger.info("Generating analysis report...")

        if not self.comparisons:
            logger.warning("No comparisons available")
            return None

        # Calculate statistics
        spread_deltas = [c.spread_delta for c in self.comparisons]
        edge_improvements = [
            c.edge_improvement for c in self.comparisons if c.edge_improvement != 0
        ]

        avg_spread_delta = sum(spread_deltas) / len(spread_deltas)
        max_spread_delta = max(abs(d) for d in spread_deltas)
        games_with_improvement = sum(
            1 for c in self.comparisons if c.edge_improvement > 0
        )
        avg_edge_improvement = (
            sum(edge_improvements) / len(edge_improvements)
            if edge_improvements
            else 0
        )
        largest_improvement = max(edge_improvements) if edge_improvements else 0
        largest_degradation = (
            min(edge_improvements) if edge_improvements else 0
        )

        summary = AnalysisSummary(
            league=self.league.upper(),
            games_analyzed=len(self.comparisons),
            avg_spread_delta=avg_spread_delta,
            max_spread_delta=max_spread_delta,
            games_with_edge_improvement=games_with_improvement,
            avg_edge_improvement=avg_edge_improvement,
            largest_improvement=largest_improvement,
            largest_degradation=largest_degradation,
            timestamp=datetime.now(),
            data_files_used={},
        )

        return summary

    def save_results(self, summary: AnalysisSummary) -> Path:
        """Save comparison results to file"""

        if not summary:
            logger.warning("No summary to save")
            return None

        output_file = (
            self.output_dir
            / f"espn_impact_{self.league}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        results = {
            "summary": asdict(summary),
            "comparisons": [asdict(c) for c in self.comparisons],
        }

        # Handle datetime serialization
        results["summary"]["timestamp"] = (
            summary.timestamp.isoformat()
        )

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {output_file}")
        return output_file

    def print_summary(self, summary: AnalysisSummary) -> None:
        """Print summary to console"""

        if not summary:
            return

        print("\n" + "=" * 70)
        print("ESPN IMPACT ANALYSIS REPORT")
        print("=" * 70)
        print(f"League:                    {summary.league}")
        print(f"Games Analyzed:            {summary.games_analyzed}")
        print(
            f"Average Spread Delta:      {summary.avg_spread_delta:+.2f} points"
        )
        print(f"Max Spread Delta:          {summary.max_spread_delta:+.2f} points")
        print(
            f"Games with Edge Improvement: {summary.games_with_edge_improvement}"
        )
        print(
            f"Average Edge Improvement:  {summary.avg_edge_improvement:+.2f} points"
        )
        print(
            f"Largest Improvement:       {summary.largest_improvement:+.2f} points"
        )
        print(
            f"Largest Degradation:       {summary.largest_degradation:+.2f} points"
        )
        print(f"Timestamp:                 {summary.timestamp.isoformat()}")
        print("=" * 70 + "\n")


def main():
    """Main entry point"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Compare ESPN impact on spread predictions"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="nfl",
        help="League to analyze",
    )
    parser.add_argument(
        "--show-comparisons",
        action="store_true",
        help="Show individual game comparisons",
    )

    args = parser.parse_args()

    analyzer = ESPNImpactAnalyzer(league=args.league)

    # Load data
    success, msg = analyzer.load_power_ratings()
    if not success:
        logger.error(f"Failed to load power ratings: {msg}")
        return 1

    logger.info(msg)

    # Enhance with ESPN
    success, msg = analyzer.enhance_with_espn()
    if not success:
        logger.warning(f"ESPN enhancement not available: {msg}")
        logger.info("Continuing with baseline comparison...")
    else:
        logger.info(msg)

    # Load schedules
    success, msg = analyzer.load_game_schedules()
    if not success:
        logger.warning(f"Could not load schedules: {msg}")

    # Compare spreads
    analyzer.compare_spreads()

    # Generate report
    summary = analyzer.generate_report()

    if summary:
        analyzer.print_summary(summary)
        output_file = analyzer.save_results(summary)
        logger.info(f"Results saved to {output_file}")

        if args.show_comparisons and analyzer.comparisons:
            print("\nTop 10 Spread Changes:")
            print("-" * 70)
            sorted_comparisons = sorted(
                analyzer.comparisons, key=lambda c: abs(c.spread_delta),
                reverse=True
            )
            for comp in sorted_comparisons[:10]:
                print(comp)
                print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
