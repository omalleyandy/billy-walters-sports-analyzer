#!/usr/bin/env python3
"""
Historical Backtesting - ESPN Enhancement Impact

Evaluates how ESPN team statistics would have improved spread predictions
over historical games. Measures:
- Spread prediction accuracy with/without ESPN
- CLV with/without ESPN metrics
- Consistency of improvement across different game types
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.valuation.billy_walters_edge_detector import (
    BillyWaltersEdgeDetector,
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
class BacktestResult:
    """Result of backtesting ESPN enhancement"""

    game_id: str
    date: str
    matchup: str
    away_team: str
    home_team: str
    final_score: str

    # Baseline predictions (without ESPN)
    baseline_predicted_spread: float
    baseline_predicted_winner: str

    # Enhanced predictions (with ESPN)
    enhanced_predicted_spread: float
    enhanced_predicted_winner: str

    # Actual outcome
    actual_spread: float
    actual_winner: str

    # Accuracy metrics
    baseline_accuracy: float  # Points off from actual
    enhanced_accuracy: float  # Points off from actual
    accuracy_improvement: float  # How much better (negative = worse)

    # Edge analysis
    market_spread: float
    baseline_edge: float
    enhanced_edge: float
    edge_improvement: float

    def __str__(self) -> str:
        """Format for display"""
        acc_arrow = "↑" if self.accuracy_improvement < 0 else "↓"
        edge_arrow = "↑" if self.edge_improvement > 0 else "↓"

        return (
            f"{self.matchup} ({self.date})\n"
            f"  Final: {self.final_score} (spread: {self.actual_spread:+.1f})\n"
            f"  Baseline: {self.baseline_predicted_spread:+.1f} "
            f"(off by {self.baseline_accuracy:.1f}) {acc_arrow}\n"
            f"  Enhanced: {self.enhanced_predicted_spread:+.1f} "
            f"(off by {self.enhanced_accuracy:.1f})\n"
            f"  Edge improvement: {self.edge_improvement:+.1f} {edge_arrow}"
        )


@dataclass
class BacktestSummary:
    """Summary statistics for backtest"""

    league: str
    start_date: str
    end_date: str
    games_analyzed: int

    # Accuracy metrics
    avg_baseline_error: float
    avg_enhanced_error: float
    avg_accuracy_improvement: float
    games_with_improvement: int

    # Edge metrics
    avg_baseline_edge: float
    avg_enhanced_edge: float
    avg_edge_improvement: float

    # Statistical significance
    improvement_stdev: float
    consistent: bool  # >70% of games improved

    timestamp: datetime


class ESPNBacktester:
    """Backtest ESPN enhancement impact"""

    def __init__(self, league: str = "nfl"):
        """Initialize backtester"""
        self.league = league.lower()
        self.results: List[BacktestResult] = []

    def load_historical_games(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Load historical game data"""

        # This would load from a historical database or archive
        # For now, returning placeholder
        logger.info(
            f"Loading games from {start_date.date()} to {end_date.date()}"
        )

        games_dir = Path("data/archive/games") / self.league
        if not games_dir.exists():
            logger.warning(f"Games directory not found: {games_dir}")
            return []

        games = []
        for game_file in games_dir.glob("*.json"):
            try:
                with open(game_file, "r") as f:
                    game = json.load(f)
                    game_date = datetime.fromisoformat(game.get("date", ""))

                    if start_date <= game_date <= end_date:
                        games.append(game)
            except Exception as e:
                logger.debug(f"Error loading {game_file}: {e}")

        logger.info(f"Loaded {len(games)} historical games")
        return games

    def predict_spread_baseline(
        self, away_team: str, home_team: str
    ) -> float:
        """Predict spread without ESPN enhancement"""

        # Would use baseline power ratings
        # For now, returning placeholder
        return 0.0

    def predict_spread_enhanced(
        self, away_team: str, home_team: str
    ) -> float:
        """Predict spread with ESPN enhancement"""

        # Would use enhanced power ratings
        # For now, returning placeholder
        return 0.0

    def calculate_actual_spread(self, away_score: int, home_score: int) -> float:
        """Calculate actual spread from final score"""
        return home_score - away_score

    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        min_games: int = 10,
    ) -> Optional[BacktestSummary]:
        """Run backtest for date range"""

        logger.info(
            f"Running backtest from {start_date.date()} to {end_date.date()}"
        )

        games = self.load_historical_games(start_date, end_date)
        if len(games) < min_games:
            logger.error(
                f"Insufficient games ({len(games)} < {min_games} required)"
            )
            return None

        self.results = []

        for game in games:
            try:
                # Get game data
                game_id = game.get("id", "unknown")
                date_str = game.get("date", "")
                matchup = game.get("matchup", "")
                away_team = game.get("away_team", "")
                home_team = game.get("home_team", "")

                # Get predictions
                baseline_spread = self.predict_spread_baseline(
                    away_team, home_team
                )
                enhanced_spread = self.predict_spread_enhanced(
                    away_team, home_team
                )

                # Get actual result
                away_score = game.get("away_score", 0)
                home_score = game.get("home_score", 0)
                actual_spread = self.calculate_actual_spread(
                    away_score, home_score
                )

                # Calculate accuracy
                baseline_error = abs(baseline_spread - actual_spread)
                enhanced_error = abs(enhanced_spread - actual_spread)
                accuracy_improvement = baseline_error - enhanced_error

                # Create result
                result = BacktestResult(
                    game_id=game_id,
                    date=date_str,
                    matchup=matchup,
                    away_team=away_team,
                    home_team=home_team,
                    final_score=f"{away_score}-{home_score}",
                    baseline_predicted_spread=baseline_spread,
                    baseline_predicted_winner=away_team
                    if baseline_spread < 0
                    else home_team,
                    enhanced_predicted_spread=enhanced_spread,
                    enhanced_predicted_winner=away_team
                    if enhanced_spread < 0
                    else home_team,
                    actual_spread=actual_spread,
                    actual_winner=away_team
                    if actual_spread < 0
                    else home_team,
                    baseline_accuracy=baseline_error,
                    enhanced_accuracy=enhanced_error,
                    accuracy_improvement=accuracy_improvement,
                    market_spread=game.get("opening_spread", 0),
                    baseline_edge=0.0,  # Would calculate from comparisons
                    enhanced_edge=0.0,  # Would calculate from comparisons
                    edge_improvement=0.0,  # Would calculate
                )

                self.results.append(result)

            except Exception as e:
                logger.debug(f"Error processing game {game_id}: {e}")

        # Calculate summary
        return self.generate_summary(start_date, end_date)

    def generate_summary(
        self, start_date: datetime, end_date: datetime
    ) -> BacktestSummary:
        """Generate summary statistics"""

        if not self.results:
            logger.error("No results to summarize")
            return None

        accuracy_improvements = [r.accuracy_improvement for r in self.results]
        edge_improvements = [r.edge_improvement for r in self.results]

        improved_games = sum(1 for a in accuracy_improvements if a < 0)
        improvement_rate = improved_games / len(self.results)
        consistent = improvement_rate > 0.7

        summary = BacktestSummary(
            league=self.league.upper(),
            start_date=start_date.date().isoformat(),
            end_date=end_date.date().isoformat(),
            games_analyzed=len(self.results),
            avg_baseline_error=statistics.mean(
                [r.baseline_accuracy for r in self.results]
            ),
            avg_enhanced_error=statistics.mean(
                [r.enhanced_accuracy for r in self.results]
            ),
            avg_accuracy_improvement=statistics.mean(accuracy_improvements),
            games_with_improvement=improved_games,
            avg_baseline_edge=statistics.mean(
                [r.baseline_edge for r in self.results]
            ),
            avg_enhanced_edge=statistics.mean(
                [r.enhanced_edge for r in self.results]
            ),
            avg_edge_improvement=statistics.mean(edge_improvements),
            improvement_stdev=statistics.stdev(accuracy_improvements)
            if len(accuracy_improvements) > 1
            else 0,
            consistent=consistent,
            timestamp=datetime.now(),
        )

        return summary

    def save_results(self) -> Path:
        """Save backtest results"""

        output_dir = Path("output/backtests")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = (
            output_dir
            / f"backtest_espn_{self.league}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "game_id": r.game_id,
                    "date": r.date,
                    "matchup": r.matchup,
                    "baseline_predicted_spread": r.baseline_predicted_spread,
                    "enhanced_predicted_spread": r.enhanced_predicted_spread,
                    "actual_spread": r.actual_spread,
                    "baseline_accuracy": r.baseline_accuracy,
                    "enhanced_accuracy": r.enhanced_accuracy,
                    "accuracy_improvement": r.accuracy_improvement,
                }
                for r in self.results
            ],
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Results saved to {output_file}")
        return output_file

    def print_summary(self, summary: Optional[BacktestSummary]) -> None:
        """Print backtest summary"""

        if not summary:
            return

        print("\n" + "=" * 70)
        print("ESPN ENHANCEMENT BACKTEST REPORT")
        print("=" * 70)
        print(f"League:                    {summary.league}")
        print(f"Period:                    {summary.start_date} to {summary.end_date}")
        print(f"Games Analyzed:            {summary.games_analyzed}")
        print()
        print("ACCURACY METRICS:")
        print(
            f"  Baseline avg error:      {summary.avg_baseline_error:+.2f} points"
        )
        print(
            f"  Enhanced avg error:      {summary.avg_enhanced_error:+.2f} points"
        )
        print(
            f"  Improvement:             {summary.avg_accuracy_improvement:+.2f} points"
        )
        print(
            f"  Games improved:          {summary.games_with_improvement} "
            f"({summary.games_with_improvement/summary.games_analyzed:.1%})"
        )
        print()
        print("EDGE METRICS:")
        print(f"  Baseline avg edge:       {summary.avg_baseline_edge:+.2f} points")
        print(f"  Enhanced avg edge:       {summary.avg_enhanced_edge:+.2f} points")
        print(
            f"  Edge improvement:        {summary.avg_edge_improvement:+.2f} points"
        )
        print()
        print("CONSISTENCY:")
        print(f"  Improvement stdev:       {summary.improvement_stdev:.2f}")
        print(f"  Consistent:              {'YES' if summary.consistent else 'NO'}")
        print("=" * 70 + "\n")


def main():
    """Main entry point"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Backtest ESPN enhancement impact"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="nfl",
        help="League to backtest",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=4,
        help="Number of weeks to backtest",
    )
    parser.add_argument(
        "--show-results",
        action="store_true",
        help="Show individual game results",
    )

    args = parser.parse_args()

    backtester = ESPNBacktester(league=args.league)

    # Run backtest for past N weeks
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=args.weeks)

    summary = backtester.run_backtest(start_date, end_date)

    if summary:
        backtester.print_summary(summary)
        backtester.save_results()

        if args.show_results and backtester.results:
            print("\nTop 10 Improvements:")
            print("-" * 70)
            sorted_results = sorted(
                backtester.results,
                key=lambda r: r.accuracy_improvement,
                reverse=True,
            )
            for result in sorted_results[:10]:
                print(result)
                print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
