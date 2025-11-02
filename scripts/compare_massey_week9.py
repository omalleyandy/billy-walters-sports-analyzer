"""
Compare Week 9 predictions with Massey Ratings.

This script:
1. Loads Week 9 edges CSV
2. Scrapes current Massey predictions for Week 9
3. Compares Billy Walters edges vs Massey edges
4. Identifies agreement/disagreement zones
5. Generates comparison report
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
import click
from typing import Dict, List
import pandas as pd


class MasseyComparator:
    """Compare Billy Walters predictions with Massey Ratings."""

    def __init__(self):
        """Initialize comparator."""
        pass

    def load_week9_csv(self, csv_path: str) -> List[Dict]:
        """Load Week 9 Billy Walters predictions.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of prediction dictionaries
        """
        predictions = []

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                pred = {
                    'home_team': row['home'],
                    'away_team': row['away'],
                    'window': row['window'],
                    'bw_spread': float(row['final_fair_spread_home']),
                    'bw_edge': float(row['edge_points_final']),
                    'bw_bet_side': row['bet_side'],
                    'market_line': float(row['home_spread']),
                }
                predictions.append(pred)

        return predictions

    def load_massey_predictions(self, massey_path: str = None) -> Dict:
        """Load Massey predictions from scraped data.

        Args:
            massey_path: Path to Massey CSV (optional)

        Returns:
            Dictionary mapping matchups to Massey predictions
        """
        # TODO: Implement Massey data loading from scraped files
        # For now, return placeholder

        massey_data = {}

        if massey_path:
            try:
                with open(massey_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        matchup_key = f"{row.get('away_team')}@{row.get('home_team')}"
                        massey_data[matchup_key] = {
                            'massey_spread': float(row.get('predicted_spread', 0)),
                            'massey_home_win_prob': float(row.get('home_win_prob', 0)),
                            'massey_predicted_total': float(row.get('predicted_total', 0))
                        }
            except Exception as e:
                click.echo(f"Error loading Massey data: {e}", err=True)

        return massey_data

    def compare_predictions(self, bw_predictions: List[Dict],
                           massey_data: Dict) -> List[Dict]:
        """Compare Billy Walters vs Massey predictions.

        Args:
            bw_predictions: Billy Walters predictions
            massey_data: Massey predictions dictionary

        Returns:
            List of comparison dictionaries
        """
        comparisons = []

        for bw_pred in bw_predictions:
            matchup_key = f"{bw_pred['away_team']}@{bw_pred['home_team']}"

            massey_pred = massey_data.get(matchup_key, {})

            if not massey_pred:
                # Try alternate key format
                matchup_key_alt = f"{bw_pred['away_team']} @ {bw_pred['home_team']}"
                massey_pred = massey_data.get(matchup_key_alt, {})

            comparison = {
                'matchup': f"{bw_pred['away_team']} @ {bw_pred['home_team']}",
                'window': bw_pred['window'],
                'market_line': bw_pred['market_line'],
                'bw_spread': bw_pred['bw_spread'],
                'bw_edge': bw_pred['bw_edge'],
                'bw_bet_side': bw_pred['bw_bet_side'],
            }

            if massey_pred:
                massey_spread = massey_pred.get('massey_spread', 0)
                comparison['massey_spread'] = massey_spread

                # Calculate Massey edge vs market
                massey_edge = abs(massey_spread - bw_pred['market_line'])
                comparison['massey_edge'] = massey_edge

                # Calculate agreement
                spread_diff = abs(bw_pred['bw_spread'] - massey_spread)
                comparison['spread_diff'] = spread_diff

                # Determine agreement level
                if spread_diff < 1.0:
                    comparison['agreement'] = 'STRONG'
                elif spread_diff < 2.0:
                    comparison['agreement'] = 'GOOD'
                elif spread_diff < 3.0:
                    comparison['agreement'] = 'MODERATE'
                else:
                    comparison['agreement'] = 'WEAK'

                # Check if both models agree on bet side
                bw_favors_home = bw_pred['bw_spread'] > bw_pred['market_line']
                massey_favors_home = massey_spread > bw_pred['market_line']
                comparison['side_agreement'] = bw_favors_home == massey_favors_home

            else:
                comparison['massey_spread'] = None
                comparison['massey_edge'] = None
                comparison['spread_diff'] = None
                comparison['agreement'] = 'NO DATA'
                comparison['side_agreement'] = None

            comparisons.append(comparison)

        return comparisons

    def generate_comparison_report(self, comparisons: List[Dict]) -> str:
        """Generate formatted comparison report.

        Args:
            comparisons: List of comparison dictionaries

        Returns:
            Multi-line report string
        """
        report = []
        report.append("="*80)
        report.append("WEEK 9: BILLY WALTERS vs MASSEY RATINGS COMPARISON")
        report.append("="*80)
        report.append("")

        # Overall statistics
        total_games = len(comparisons)
        games_with_massey = sum(1 for c in comparisons if c['massey_spread'] is not None)

        if games_with_massey > 0:
            strong_agreement = sum(1 for c in comparisons if c['agreement'] == 'STRONG')
            good_agreement = sum(1 for c in comparisons if c['agreement'] == 'GOOD')
            moderate_agreement = sum(1 for c in comparisons if c['agreement'] == 'MODERATE')
            weak_agreement = sum(1 for c in comparisons if c['agreement'] == 'WEAK')

            side_agreement = sum(1 for c in comparisons if c.get('side_agreement'))

            report.append("OVERALL COMPARISON SUMMARY")
            report.append("-"*80)
            report.append(f"Total games: {total_games}")
            report.append(f"Games with Massey data: {games_with_massey}")
            report.append(f"Side agreement: {side_agreement}/{games_with_massey} ({side_agreement/games_with_massey*100:.1f}%)")
            report.append("")
            report.append("Spread Agreement Distribution:")
            report.append(f"  Strong (<1.0 pts): {strong_agreement} ({strong_agreement/games_with_massey*100:.1f}%)")
            report.append(f"  Good (1.0-2.0 pts): {good_agreement} ({good_agreement/games_with_massey*100:.1f}%)")
            report.append(f"  Moderate (2.0-3.0 pts): {moderate_agreement} ({moderate_agreement/games_with_massey*100:.1f}%)")
            report.append(f"  Weak (>3.0 pts): {weak_agreement} ({weak_agreement/games_with_massey*100:.1f}%)")
            report.append("")

        # Game-by-game breakdown
        report.append("GAME-BY-GAME COMPARISON")
        report.append("-"*80)

        for comp in comparisons:
            report.append(f"\n{comp['matchup']} ({comp['window']})")
            report.append(f"  Market line: {comp['market_line']:+.1f}")
            report.append(f"  Billy Walters spread: {comp['bw_spread']:+.1f} (Edge: {comp['bw_edge']:.2f} pts)")
            report.append(f"  Billy Walters bet: {comp['bw_bet_side']}")

            if comp['massey_spread'] is not None:
                report.append(f"  Massey spread: {comp['massey_spread']:+.1f} (Edge: {comp['massey_edge']:.2f} pts)")
                report.append(f"  Spread difference: {comp['spread_diff']:.2f} pts")
                report.append(f"  Agreement: {comp['agreement']} | Side agreement: {'YES' if comp['side_agreement'] else 'NO'}")
            else:
                report.append(f"  Massey spread: NO DATA")

        report.append("")
        report.append("="*80)

        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-"*80)

        if games_with_massey == 0:
            report.append("⚠ No Massey data available for comparison.")
            report.append("Run: uv run walters-analyzer scrape-massey --data-type games")
        elif side_agreement / games_with_massey >= 0.8:
            report.append("✓ Strong agreement with Massey Ratings.")
            report.append("  High confidence in bet recommendations.")
        elif side_agreement / games_with_massey >= 0.6:
            report.append("✓ Moderate agreement with Massey Ratings.")
            report.append("  Reasonable confidence in bets with strong edges.")
        else:
            report.append("⚠ Significant disagreement with Massey Ratings.")
            report.append("  Manual review recommended for all bets.")

        report.append("")

        # Identify highest confidence bets
        report.append("HIGHEST CONFIDENCE BETS (Both models agree):")
        report.append("-"*80)

        high_confidence = [
            c for c in comparisons
            if c.get('side_agreement') and c.get('bw_edge', 0) >= 3.0
        ]

        if high_confidence:
            high_confidence.sort(key=lambda x: x['bw_edge'], reverse=True)
            for comp in high_confidence[:5]:
                report.append(f"  {comp['matchup']}: {comp['bw_bet_side']} ({comp['bw_edge']:.2f} pt edge)")
        else:
            report.append("  None identified")

        report.append("")
        report.append("="*80)

        return "\n".join(report)


@click.command()
@click.option('--csv-path', required=True, type=click.Path(exists=True),
              help='Path to Week 9 Billy Walters edges CSV')
@click.option('--massey-path', type=click.Path(exists=True),
              help='Path to Massey predictions CSV (optional)')
@click.option('--scrape-massey', is_flag=True,
              help='Scrape latest Massey predictions first')
@click.option('--output', type=click.Path(),
              help='Output path for comparison report')
def main(csv_path: str, massey_path: str, scrape_massey: bool, output: str):
    """Compare Week 9 Billy Walters predictions with Massey Ratings."""

    click.echo("="*80)
    click.echo("WEEK 9: BILLY WALTERS vs MASSEY RATINGS")
    click.echo("="*80)

    # Scrape Massey if requested
    if scrape_massey:
        click.echo("\nScraping latest Massey predictions...")
        click.echo("Run: uv run walters-analyzer scrape-massey --data-type games")
        click.echo("Then specify --massey-path to load the data")
        return

    comparator = MasseyComparator()

    # Load Billy Walters predictions
    click.echo(f"\nLoading Billy Walters predictions from: {csv_path}")
    bw_predictions = comparator.load_week9_csv(csv_path)
    click.echo(f"Loaded {len(bw_predictions)} predictions")

    # Load Massey predictions
    if massey_path:
        click.echo(f"\nLoading Massey predictions from: {massey_path}")
        massey_data = comparator.load_massey_predictions(massey_path)
        click.echo(f"Loaded {len(massey_data)} Massey predictions")
    else:
        click.echo("\nNo Massey data provided. Generating report without comparison.")
        massey_data = {}

    # Compare
    click.echo("\nComparing predictions...")
    comparisons = comparator.compare_predictions(bw_predictions, massey_data)

    # Generate report
    report = comparator.generate_comparison_report(comparisons)

    # Output report
    if output:
        with open(output, 'w') as f:
            f.write(report)
        click.echo(f"\nComparison report saved to: {output}")

    click.echo("\n" + report)


if __name__ == '__main__':
    main()
