"""
Strategy validation tools for optimizing factor weights and thresholds.

Provides tools for:
- Cross-validation
- Parameter optimization
- Statistical significance testing
- Bias detection
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy import stats
from itertools import product
from .engine import BacktestEngine
from .metrics import PerformanceMetrics


class StrategyValidator:
    """Validate and optimize betting strategy parameters."""

    def __init__(self, db_path: str = "data/historical/historical_games.db"):
        """Initialize validator.

        Args:
            db_path: Path to historical database
        """
        self.db_path = db_path

    def walk_forward_validation(self, start_season: int, end_season: int,
                                train_window: int = 2,
                                test_window: int = 1) -> Dict:
        """Perform walk-forward cross-validation.

        Args:
            start_season: Starting season
            end_season: Ending season
            train_window: Number of seasons for training
            test_window: Number of seasons for testing

        Returns:
            Validation results dictionary
        """
        print(f"Walk-forward validation: {start_season}-{end_season}")
        print(f"Train window: {train_window} seasons, Test window: {test_window} season(s)")
        print("="*60)

        all_results = []
        fold_summaries = []

        current_season = start_season

        while current_season + train_window + test_window <= end_season + 1:
            train_start = current_season
            train_end = current_season + train_window - 1
            test_start = train_end + 1
            test_end = test_start + test_window - 1

            print(f"\nFold: Train {train_start}-{train_end}, Test {test_start}-{test_end}")

            # Train on training window (find optimal parameters)
            # For now, just use default parameters
            # TODO: Implement parameter optimization

            # Test on test window
            engine = BacktestEngine(self.db_path)
            fold_results = engine.run_backtest(test_start, test_end)
            engine.close()

            fold_summaries.append({
                'train_seasons': f"{train_start}-{train_end}",
                'test_seasons': f"{test_start}-{test_end}",
                'results': fold_results
            })

            all_results.extend(engine.results)

            # Move window forward
            current_season += test_window

        # Calculate overall metrics
        metrics = PerformanceMetrics(all_results)
        overall = metrics.calculate_all_metrics()

        print("\n" + "="*60)
        print("WALK-FORWARD VALIDATION COMPLETE")
        print("="*60)
        print(f"Total folds: {len(fold_summaries)}")
        print(f"Overall win rate: {overall['win_rate']:.1f}%")
        print(f"Overall ROI: {overall['roi']:.1f}%")
        print(f"Overall Sharpe: {overall['sharpe_ratio']:.2f}")

        return {
            'fold_summaries': fold_summaries,
            'overall_metrics': overall,
            'all_results': all_results
        }

    def optimize_edge_threshold(self, season_start: int, season_end: int,
                                min_threshold: float = 1.0,
                                max_threshold: float = 8.0,
                                step: float = 0.5) -> Dict:
        """Find optimal edge threshold.

        Args:
            season_start: Starting season
            season_end: Ending season
            min_threshold: Minimum threshold to test
            max_threshold: Maximum threshold to test
            step: Step size for grid search

        Returns:
            Optimization results
        """
        print(f"Optimizing edge threshold: {min_threshold}-{max_threshold} by {step}")
        print("="*60)

        thresholds = np.arange(min_threshold, max_threshold + step, step)
        results = []

        for threshold in thresholds:
            print(f"\nTesting threshold: {threshold:.1f} points")

            engine = BacktestEngine(self.db_path)
            summary = engine.run_backtest(season_start, season_end,
                                         min_edge=threshold, max_edge=10.0)
            engine.close()

            results.append({
                'threshold': threshold,
                'roi': summary['roi'],
                'win_rate': summary['win_rate'],
                'total_bets': summary['total_bets'],
                'sharpe_ratio': summary['sharpe_ratio'],
                'total_profit': summary['total_profit']
            })

        # Find optimal threshold by ROI
        optimal = max(results, key=lambda x: x['roi'])

        print("\n" + "="*60)
        print("OPTIMIZATION COMPLETE")
        print("="*60)
        print(f"Optimal threshold: {optimal['threshold']:.1f} points")
        print(f"ROI: {optimal['roi']:.1f}%")
        print(f"Win rate: {optimal['win_rate']:.1f}%")
        print(f"Total bets: {optimal['total_bets']}")

        return {
            'optimal_threshold': optimal['threshold'],
            'optimal_metrics': optimal,
            'all_results': results
        }

    def test_statistical_significance(self, results: List[Dict],
                                     confidence_level: float = 0.95) -> Dict:
        """Test if results are statistically significant.

        Args:
            results: List of bet results
            confidence_level: Confidence level (e.g., 0.95 for 95%)

        Returns:
            Statistical test results
        """
        if len(results) < 30:
            return {
                'significant': False,
                'reason': 'Insufficient sample size (need at least 30 bets)'
            }

        # Extract profits
        profits = [r.get('bet_profit', 0) for r in results]

        # One-sample t-test (H0: mean profit = 0)
        t_stat, p_value = stats.ttest_1samp(profits, 0)

        # Calculate confidence interval
        mean_profit = np.mean(profits)
        std_error = stats.sem(profits)
        ci = stats.t.interval(confidence_level, len(profits)-1, mean_profit, std_error)

        # Check significance
        alpha = 1 - confidence_level
        significant = p_value < alpha and mean_profit > 0

        return {
            'significant': significant,
            'p_value': p_value,
            't_statistic': t_stat,
            'mean_profit': mean_profit,
            'confidence_interval': ci,
            'sample_size': len(results),
            'interpretation': (
                f"Results {'are' if significant else 'are not'} statistically significant "
                f"at {confidence_level*100:.0f}% confidence level."
            )
        }

    def detect_biases(self, results: List[Dict]) -> Dict:
        """Detect systematic biases in predictions.

        Args:
            results: List of bet results

        Returns:
            Bias analysis dictionary
        """
        biases = {}

        # Home/Away bias
        home_results = [r for r in results if r.get('bet_side') == r.get('home_team')]
        away_results = [r for r in results if r.get('bet_side') != r.get('home_team')]

        if home_results:
            home_metrics = PerformanceMetrics(home_results)
            biases['home_bets'] = {
                'count': len(home_results),
                'win_rate': home_metrics.calculate_win_rate(),
                'roi': home_metrics.calculate_roi()
            }

        if away_results:
            away_metrics = PerformanceMetrics(away_results)
            biases['away_bets'] = {
                'count': len(away_results),
                'win_rate': away_metrics.calculate_win_rate(),
                'roi': away_metrics.calculate_roi()
            }

        # Favorite/Underdog bias (based on line)
        favorite_results = [r for r in results if abs(r.get('bet_line', 0)) > 3]
        underdog_results = [r for r in results if abs(r.get('bet_line', 0)) <= 3]

        if favorite_results:
            fav_metrics = PerformanceMetrics(favorite_results)
            biases['favorites'] = {
                'count': len(favorite_results),
                'win_rate': fav_metrics.calculate_win_rate(),
                'roi': fav_metrics.calculate_roi()
            }

        if underdog_results:
            dog_metrics = PerformanceMetrics(underdog_results)
            biases['underdogs'] = {
                'count': len(underdog_results),
                'win_rate': dog_metrics.calculate_win_rate(),
                'roi': dog_metrics.calculate_roi()
            }

        return biases

    def compare_to_benchmark(self, results: List[Dict],
                            benchmark: str = "random") -> Dict:
        """Compare strategy to benchmark.

        Args:
            results: Strategy results
            benchmark: Benchmark type ('random', 'favorites', 'underdogs')

        Returns:
            Comparison results
        """
        strategy_metrics = PerformanceMetrics(results)
        strategy_roi = strategy_metrics.calculate_roi()
        strategy_win_rate = strategy_metrics.calculate_win_rate()

        # Benchmark assumptions
        if benchmark == "random":
            # Random betting at -110 juice requires 52.38% to break even
            benchmark_win_rate = 50.0
            benchmark_roi = -4.76  # Expected ROI at 50% with -110
        elif benchmark == "favorites":
            # Historically favorites cover ~48%
            benchmark_win_rate = 48.0
            benchmark_roi = -8.0
        elif benchmark == "underdogs":
            # Historically underdogs cover ~52%
            benchmark_win_rate = 52.0
            benchmark_roi = -0.8
        else:
            benchmark_win_rate = 50.0
            benchmark_roi = -4.76

        improvement = {
            'win_rate_diff': strategy_win_rate - benchmark_win_rate,
            'roi_diff': strategy_roi - benchmark_roi,
            'outperforms': strategy_roi > benchmark_roi
        }

        return {
            'strategy': {
                'win_rate': strategy_win_rate,
                'roi': strategy_roi
            },
            'benchmark': {
                'name': benchmark,
                'win_rate': benchmark_win_rate,
                'roi': benchmark_roi
            },
            'improvement': improvement
        }
