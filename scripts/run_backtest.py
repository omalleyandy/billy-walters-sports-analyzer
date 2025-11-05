"""
Run backtesting on historical NFL data.

This script runs the Billy Walters methodology on historical games
to validate strategy performance and optimize parameters.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from datetime import datetime

from walters.backtest import BacktestEngine, PerformanceMetrics, StrategyValidator


@click.group()
def cli():
    """Billy Walters backtesting suite."""
    pass


@cli.command()
@click.option('--start-season', default=2020, type=int,
              help='Starting season year')
@click.option('--end-season', default=2023, type=int,
              help='Ending season year')
@click.option('--min-edge', default=2.0, type=float,
              help='Minimum edge threshold (points)')
@click.option('--max-edge', default=10.0, type=float,
              help='Maximum edge threshold (points)')
@click.option('--bankroll', default=10000.0, type=float,
              help='Starting bankroll')
@click.option('--db-path', default='data/historical/historical_games.db',
              help='Path to historical database')
@click.option('--output', type=click.Path(),
              help='Output path for detailed report')
def run(start_season: int, end_season: int, min_edge: float, max_edge: float,
        bankroll: float, db_path: str, output: str):
    """Run standard backtest on historical data."""

    click.echo("="*80)
    click.echo("BILLY WALTERS METHODOLOGY BACKTEST")
    click.echo("="*80)
    click.echo(f"Seasons: {start_season}-{end_season}")
    click.echo(f"Edge threshold: {min_edge}-{max_edge} points")
    click.echo(f"Starting bankroll: ${bankroll:,.2f}")
    click.echo(f"Database: {db_path}")
    click.echo("")

    # Initialize engine
    engine = BacktestEngine(
        db_path=db_path,
        bankroll=bankroll
    )

    # Run backtest
    summary = engine.run_backtest(
        start_season=start_season,
        end_season=end_season,
        min_edge=min_edge,
        max_edge=max_edge
    )

    # Generate detailed report
    metrics = PerformanceMetrics(engine.results)
    report = metrics.generate_report()

    click.echo("\n" + report)

    # Save to file if requested
    if output:
        with open(output, 'w') as f:
            f.write(report)
            f.write("\n\n")
            f.write("="*80)
            f.write("\nDETAILED RESULTS\n")
            f.write("="*80)
            f.write("\n\n")

            # Write detailed results
            for i, result in enumerate(engine.results, 1):
                f.write(f"Bet #{i}\n")
                f.write(f"  Game: {result['game_id']}\n")
                f.write(f"  Side: {result['bet_side']} {result['bet_line']}\n")
                f.write(f"  Stake: ${result['stake']:.2f}\n")
                f.write(f"  Result: {'WIN' if result['bet_won'] else 'LOSS'}\n")
                f.write(f"  Profit: ${result['bet_profit']:+.2f}\n")
                f.write(f"  CLV: {result['clv']:+.2f} points\n")
                f.write(f"  Star rating: {result['star_rating']:.1f}\n")
                f.write("\n")

        click.echo(f"\nDetailed report saved to: {output}")

    engine.close()


@cli.command()
@click.option('--start-season', default=2020, type=int,
              help='Starting season year')
@click.option('--end-season', default=2023, type=int,
              help='Ending season year')
@click.option('--train-window', default=2, type=int,
              help='Training window (seasons)')
@click.option('--test-window', default=1, type=int,
              help='Testing window (seasons)')
@click.option('--db-path', default='data/historical/historical_games.db',
              help='Path to historical database')
def walk_forward(start_season: int, end_season: int, train_window: int,
                test_window: int, db_path: str):
    """Run walk-forward cross-validation."""

    click.echo("="*80)
    click.echo("WALK-FORWARD CROSS-VALIDATION")
    click.echo("="*80)

    validator = StrategyValidator(db_path)

    results = validator.walk_forward_validation(
        start_season=start_season,
        end_season=end_season,
        train_window=train_window,
        test_window=test_window
    )

    click.echo("\nWalk-forward validation complete!")


@cli.command()
@click.option('--start-season', default=2020, type=int,
              help='Starting season year')
@click.option('--end-season', default=2023, type=int,
              help='Ending season year')
@click.option('--min-threshold', default=1.0, type=float,
              help='Minimum threshold to test')
@click.option('--max-threshold', default=8.0, type=float,
              help='Maximum threshold to test')
@click.option('--step', default=0.5, type=float,
              help='Step size for grid search')
@click.option('--db-path', default='data/historical/historical_games.db',
              help='Path to historical database')
def optimize(start_season: int, end_season: int, min_threshold: float,
            max_threshold: float, step: float, db_path: str):
    """Optimize edge threshold parameter."""

    click.echo("="*80)
    click.echo("EDGE THRESHOLD OPTIMIZATION")
    click.echo("="*80)

    validator = StrategyValidator(db_path)

    results = validator.optimize_edge_threshold(
        season_start=start_season,
        season_end=end_season,
        min_threshold=min_threshold,
        max_threshold=max_threshold,
        step=step
    )

    click.echo("\nOptimization complete!")
    click.echo(f"Optimal threshold: {results['optimal_threshold']:.1f} points")


@cli.command()
@click.option('--db-path', default='data/historical/historical_games.db',
              help='Path to historical database')
@click.option('--season', type=int,
              help='Specific season to analyze (optional)')
def analyze(db_path: str, season: int):
    """Analyze backtest results for biases and significance."""

    click.echo("="*80)
    click.echo("BACKTEST ANALYSIS")
    click.echo("="*80)

    from walters.historical_db import HistoricalDatabase

    db = HistoricalDatabase(db_path)

    # Get results
    results = db.get_results(season=season)

    if not results:
        click.echo("No backtest results found in database.")
        click.echo("Run a backtest first using: python scripts/run_backtest.py run")
        return

    click.echo(f"\nAnalyzing {len(results)} bet results...")

    validator = StrategyValidator(db_path)

    # Statistical significance
    click.echo("\n" + "="*80)
    click.echo("STATISTICAL SIGNIFICANCE TEST")
    click.echo("="*80)
    sig_results = validator.test_statistical_significance(results)
    click.echo(sig_results['interpretation'])
    click.echo(f"P-value: {sig_results['p_value']:.4f}")
    click.echo(f"Mean profit per bet: ${sig_results['mean_profit']:.2f}")
    click.echo(f"95% CI: ${sig_results['confidence_interval'][0]:.2f} to ${sig_results['confidence_interval'][1]:.2f}")

    # Bias detection
    click.echo("\n" + "="*80)
    click.echo("BIAS DETECTION")
    click.echo("="*80)
    biases = validator.detect_biases(results)

    if 'home_bets' in biases:
        click.echo(f"\nHome Bets:")
        click.echo(f"  Count: {biases['home_bets']['count']}")
        click.echo(f"  Win rate: {biases['home_bets']['win_rate']:.1f}%")
        click.echo(f"  ROI: {biases['home_bets']['roi']:.1f}%")

    if 'away_bets' in biases:
        click.echo(f"\nAway Bets:")
        click.echo(f"  Count: {biases['away_bets']['count']}")
        click.echo(f"  Win rate: {biases['away_bets']['win_rate']:.1f}%")
        click.echo(f"  ROI: {biases['away_bets']['roi']:.1f}%")

    if 'favorites' in biases:
        click.echo(f"\nFavorites (>3 point lines):")
        click.echo(f"  Count: {biases['favorites']['count']}")
        click.echo(f"  Win rate: {biases['favorites']['win_rate']:.1f}%")
        click.echo(f"  ROI: {biases['favorites']['roi']:.1f}%")

    if 'underdogs' in biases:
        click.echo(f"\nUnderdogs (≤3 point lines):")
        click.echo(f"  Count: {biases['underdogs']['count']}")
        click.echo(f"  Win rate: {biases['underdogs']['win_rate']:.1f}%")
        click.echo(f"  ROI: {biases['underdogs']['roi']:.1f}%")

    # Benchmark comparison
    click.echo("\n" + "="*80)
    click.echo("BENCHMARK COMPARISON")
    click.echo("="*80)

    for benchmark in ['random', 'favorites', 'underdogs']:
        comparison = validator.compare_to_benchmark(results, benchmark)
        click.echo(f"\nvs. {benchmark.upper()}:")
        click.echo(f"  Strategy ROI: {comparison['strategy']['roi']:.1f}%")
        click.echo(f"  Benchmark ROI: {comparison['benchmark']['roi']:.1f}%")
        click.echo(f"  Improvement: {comparison['improvement']['roi_diff']:+.1f}%")
        click.echo(f"  Outperforms: {'YES' if comparison['improvement']['outperforms'] else 'NO'}")

    db.close()


if __name__ == '__main__':
    cli()
