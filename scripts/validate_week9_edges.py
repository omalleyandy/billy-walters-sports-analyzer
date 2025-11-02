"""
Validate Week 9 edge calculations against live data.

This script:
1. Loads the Week 9 edges CSV
2. Scrapes current odds, injuries, and weather
3. Recalculates edges using live data
4. Compares with CSV predictions
5. Generates validation report
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
import click
from datetime import datetime
from typing import Dict, List
import pandas as pd

from walters_analyzer.power_ratings import PowerRatingsEngine
from walters_analyzer.situational_factors import SituationalFactorCalculator
from walters_analyzer.bet_sizing import BetSizeCalculator
from walters_analyzer.key_numbers import KeyNumberAnalyzer


class Week9Validator:
    """Validates Week 9 predictions against live data."""

    def __init__(self):
        """Initialize validator with Billy Walters components."""
        self.power_ratings = PowerRatingsEngine()
        self.swe_calculator = SituationalFactorCalculator()
        self.bet_sizer = BetSizeCalculator()
        self.key_numbers = KeyNumberAnalyzer()

    def load_csv_predictions(self, csv_path: str) -> List[Dict]:
        """Load Week 9 predictions from CSV.

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
                    'csv_home_spread': float(row['home_spread']),
                    'csv_home_price': int(row['home_price']),
                    'csv_away_price': int(row['away_price']),
                    'csv_travel_miles': float(row['travel_miles']),
                    'csv_travel_delta_pts': float(row['travel_delta_pts']),
                    'csv_tz_delta_pts': float(row['tz_delta_pts']),
                    'csv_ratings_prior_margin': float(row['ratings_prior_margin']),
                    'csv_fair_pre_situational': float(row['fair_pre_situational']),
                    'csv_final_fair_spread_home': float(row['final_fair_spread_home']),
                    'csv_bet_side': row['bet_side'],
                    'csv_bet_side_flag': row['bet_side_flag'],
                    'csv_line': float(row['line']),
                    'csv_price': int(row['price']),
                    'csv_win_prob_pct': float(row['win_prob_pct']),
                    'csv_ev_pct': float(row['ev_pct']),
                    'csv_stake_suggested': float(row['stake_suggested']),
                    'csv_is_divisional': row['is_divisional'] == 'TRUE',
                    'csv_edge_points_final': float(row['edge_points_final'])
                }
                predictions.append(pred)

        return predictions

    def recalculate_edge(self, prediction: Dict, live_odds: Dict = None,
                        live_injuries: List[Dict] = None,
                        live_weather: Dict = None) -> Dict:
        """Recalculate edge using live data.

        Args:
            prediction: Prediction dictionary from CSV
            live_odds: Live odds data (optional)
            live_injuries: Live injury data (optional)
            live_weather: Live weather data (optional)

        Returns:
            Recalculated prediction dictionary
        """
        home_team = prediction['home_team']
        away_team = prediction['away_team']

        # Get current power ratings
        home_rating = self.power_ratings.get_rating(home_team, 'NFL')
        away_rating = self.power_ratings.get_rating(away_team, 'NFL')

        # Calculate pre-situational margin
        if home_rating is None or away_rating is None:
            # Use CSV values if ratings not available
            ratings_margin = prediction['csv_ratings_prior_margin']
        else:
            ratings_margin = home_rating - away_rating

        home_field_advantage = 2.5
        pre_situational_margin = ratings_margin + home_field_advantage

        # Apply situational factors (use CSV values for now)
        travel_adj = prediction['csv_travel_delta_pts']
        tz_adj = prediction['csv_tz_delta_pts']

        # TODO: Calculate injury differential from live data
        injury_adj = 0

        # TODO: Calculate weather adjustment from live data
        weather_adj = 0

        # Calculate final margin
        final_margin = pre_situational_margin + travel_adj + tz_adj + injury_adj + weather_adj

        # Get market line (use live if available, otherwise CSV)
        if live_odds:
            market_line = live_odds.get('home_spread', prediction['csv_home_spread'])
            market_price = live_odds.get('home_price', prediction['csv_home_price'])
        else:
            market_line = prediction['csv_home_spread']
            market_price = prediction['csv_home_price']

        # Calculate edge
        edge_points = abs(final_margin - market_line)

        # Determine bet side
        if final_margin < market_line - 0.5:
            bet_side = f"{away_team} (away)"
            bet_line = -market_line
        elif final_margin > market_line + 0.5:
            bet_side = f"{home_team} (home)"
            bet_line = market_line
        else:
            bet_side = "NO BET"
            bet_line = market_line

        # Calculate win probability (simplified)
        base_prob = 52.38
        win_prob = min(base_prob + (edge_points * 2.0), 75.0)

        # Calculate expected value
        if market_price < 0:
            decimal_payout = 1 + (100 / abs(market_price))
        else:
            decimal_payout = 1 + (market_price / 100)

        ev = ((win_prob / 100) * decimal_payout) - 1
        ev_pct = ev * 100

        # Calculate star rating and stake
        star_rating = self.bet_sizer.calculate_star_rating(edge_points, win_prob)
        stake = self.bet_sizer.calculate_stake(star_rating, 10000.0)

        return {
            'recalc_pre_situational_margin': pre_situational_margin,
            'recalc_final_margin': final_margin,
            'recalc_market_line': market_line,
            'recalc_edge_points': edge_points,
            'recalc_bet_side': bet_side,
            'recalc_win_prob': win_prob,
            'recalc_ev_pct': ev_pct,
            'recalc_star_rating': star_rating,
            'recalc_stake': stake
        }

    def compare_predictions(self, csv_pred: Dict, recalc_pred: Dict) -> Dict:
        """Compare CSV prediction with recalculated prediction.

        Args:
            csv_pred: CSV prediction
            recalc_pred: Recalculated prediction

        Returns:
            Comparison dictionary
        """
        comparison = {
            'home_team': csv_pred['home_team'],
            'away_team': csv_pred['away_team'],
            'window': csv_pred['window'],

            # Edge comparison
            'csv_edge': csv_pred['csv_edge_points_final'],
            'recalc_edge': recalc_pred['recalc_edge_points'],
            'edge_diff': recalc_pred['recalc_edge_points'] - csv_pred['csv_edge_points_final'],

            # Bet side comparison
            'csv_bet_side': csv_pred['csv_bet_side'],
            'recalc_bet_side': recalc_pred['recalc_bet_side'],
            'bet_side_matches': csv_pred['csv_bet_side'] == recalc_pred['recalc_bet_side'],

            # Stake comparison
            'csv_stake': csv_pred['csv_stake_suggested'],
            'recalc_stake': recalc_pred['recalc_stake'],
            'stake_diff': recalc_pred['recalc_stake'] - csv_pred['csv_stake_suggested'],

            # Win probability comparison
            'csv_win_prob': csv_pred['csv_win_prob_pct'],
            'recalc_win_prob': recalc_pred['recalc_win_prob'],
            'win_prob_diff': recalc_pred['recalc_win_prob'] - csv_pred['csv_win_prob_pct'],

            # EV comparison
            'csv_ev': csv_pred['csv_ev_pct'],
            'recalc_ev': recalc_pred['recalc_ev_pct'],
            'ev_diff': recalc_pred['recalc_ev_pct'] - csv_pred['csv_ev_pct'],
        }

        # Determine agreement level
        edge_diff_abs = abs(comparison['edge_diff'])
        if edge_diff_abs < 0.5:
            comparison['agreement'] = 'STRONG'
        elif edge_diff_abs < 1.0:
            comparison['agreement'] = 'GOOD'
        elif edge_diff_abs < 2.0:
            comparison['agreement'] = 'MODERATE'
        else:
            comparison['agreement'] = 'WEAK'

        return comparison

    def generate_validation_report(self, comparisons: List[Dict]) -> str:
        """Generate formatted validation report.

        Args:
            comparisons: List of comparison dictionaries

        Returns:
            Multi-line report string
        """
        report = []
        report.append("="*80)
        report.append("WEEK 9 EDGE VALIDATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*80)
        report.append("")

        # Overall statistics
        total_games = len(comparisons)
        strong_agreement = sum(1 for c in comparisons if c['agreement'] == 'STRONG')
        good_agreement = sum(1 for c in comparisons if c['agreement'] == 'GOOD')
        moderate_agreement = sum(1 for c in comparisons if c['agreement'] == 'MODERATE')
        weak_agreement = sum(1 for c in comparisons if c['agreement'] == 'WEAK')

        bet_side_matches = sum(1 for c in comparisons if c['bet_side_matches'])

        avg_edge_diff = sum(abs(c['edge_diff']) for c in comparisons) / total_games if total_games > 0 else 0

        report.append("OVERALL VALIDATION SUMMARY")
        report.append("-"*80)
        report.append(f"Total games analyzed: {total_games}")
        report.append(f"Average edge difference: {avg_edge_diff:.2f} points")
        report.append(f"Bet side agreement: {bet_side_matches}/{total_games} ({bet_side_matches/total_games*100:.1f}%)")
        report.append("")
        report.append("Agreement Distribution:")
        report.append(f"  Strong (<0.5 pts): {strong_agreement} ({strong_agreement/total_games*100:.1f}%)")
        report.append(f"  Good (0.5-1.0 pts): {good_agreement} ({good_agreement/total_games*100:.1f}%)")
        report.append(f"  Moderate (1.0-2.0 pts): {moderate_agreement} ({moderate_agreement/total_games*100:.1f}%)")
        report.append(f"  Weak (>2.0 pts): {weak_agreement} ({weak_agreement/total_games*100:.1f}%)")
        report.append("")

        # Game-by-game breakdown
        report.append("GAME-BY-GAME VALIDATION")
        report.append("-"*80)

        for comp in comparisons:
            report.append(f"\n{comp['away_team']} @ {comp['home_team']} ({comp['window']})")
            report.append(f"  Agreement: {comp['agreement']}")
            report.append(f"  CSV Edge: {comp['csv_edge']:.2f} pts | Recalc Edge: {comp['recalc_edge']:.2f} pts | Diff: {comp['edge_diff']:+.2f} pts")
            report.append(f"  CSV Bet: {comp['csv_bet_side']} | Recalc Bet: {comp['recalc_bet_side']}")
            report.append(f"  CSV Stake: ${comp['csv_stake']:.2f} | Recalc Stake: ${comp['recalc_stake']:.2f} | Diff: ${comp['stake_diff']:+.2f}")
            report.append(f"  CSV Win%: {comp['csv_win_prob']:.1f}% | Recalc Win%: {comp['recalc_win_prob']:.1f}% | Diff: {comp['win_prob_diff']:+.1f}%")

        report.append("")
        report.append("="*80)

        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-"*80)

        if avg_edge_diff < 0.5:
            report.append("✓ Edge calculations are highly consistent. CSV predictions validated.")
        elif avg_edge_diff < 1.0:
            report.append("✓ Edge calculations are reasonably consistent. Minor discrepancies expected.")
        elif avg_edge_diff < 2.0:
            report.append("⚠ Moderate discrepancies detected. Review situational factors and data sources.")
        else:
            report.append("✗ Significant discrepancies detected. Manual review required before betting.")

        report.append("")

        if bet_side_matches / total_games >= 0.9:
            report.append("✓ Bet side recommendations are highly consistent.")
        elif bet_side_matches / total_games >= 0.75:
            report.append("⚠ Some bet side disagreements. Review edge cases.")
        else:
            report.append("✗ Significant bet side disagreements. Manual review required.")

        report.append("")
        report.append("="*80)

        return "\n".join(report)


@click.command()
@click.option('--csv-path', required=True, type=click.Path(exists=True),
              help='Path to Week 9 edges CSV file')
@click.option('--scrape-live', is_flag=True,
              help='Scrape live odds/injuries/weather (requires implementation)')
@click.option('--output', type=click.Path(),
              help='Output path for validation report (optional)')
def main(csv_path: str, scrape_live: bool, output: str):
    """Validate Week 9 edge calculations against live data."""

    click.echo("="*80)
    click.echo("WEEK 9 EDGE VALIDATION")
    click.echo("="*80)

    validator = Week9Validator()

    # Load CSV predictions
    click.echo(f"\nLoading CSV predictions from: {csv_path}")
    csv_predictions = validator.load_csv_predictions(csv_path)
    click.echo(f"Loaded {len(csv_predictions)} predictions")

    # Scrape live data if requested
    if scrape_live:
        click.echo("\n⚠ Live scraping not yet implemented")
        click.echo("Using CSV data for validation...")
        # TODO: Implement live scraping
        # live_odds = scrape_overtime_odds()
        # live_injuries = scrape_espn_injuries()
        # live_weather = scrape_weather()

    # Recalculate and compare
    click.echo("\nRecalculating edges with current data...")
    comparisons = []

    for pred in csv_predictions:
        recalc = validator.recalculate_edge(pred)
        comparison = validator.compare_predictions(pred, recalc)
        comparisons.append(comparison)

    # Generate report
    report = validator.generate_validation_report(comparisons)

    # Output report
    if output:
        with open(output, 'w') as f:
            f.write(report)
        click.echo(f"\nValidation report saved to: {output}")

    click.echo("\n" + report)


if __name__ == '__main__':
    main()
