"""
Core backtesting engine for simulating historical betting performance.

This engine runs the Billy Walters methodology on historical games, tracking:
- Power rating evolution
- S/W/E factor calculations
- Bet recommendations
- P&L and CLV
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from ..historical_db import HistoricalDatabase
from ..power_ratings import PowerRatingsEngine
from ..situational_factors import SituationalFactorCalculator
from ..key_numbers import KeyNumberAnalyzer
from ..bet_sizing import BetSizeCalculator
from .metrics import PerformanceMetrics


class BacktestEngine:
    """Simulates betting strategy on historical data."""

    def __init__(self, db_path: str = "data/historical/historical_games.db",
                 ratings_path: str = "data/power_ratings",
                 bankroll: float = 10000.0,
                 model_version: str = "v1.0"):
        """Initialize backtest engine.

        Args:
            db_path: Path to historical database
            ratings_path: Path to power ratings storage
            bankroll: Starting bankroll
            model_version: Model version identifier
        """
        self.db = HistoricalDatabase(db_path)
        self.ratings_engine = PowerRatingsEngine(ratings_dir=ratings_path)
        self.swe_calculator = SituationalFactorCalculator()
        self.key_numbers = KeyNumberAnalyzer()
        self.bet_sizer = BetSizeCalculator(bankroll=bankroll)
        self.model_version = model_version

        self.bankroll = bankroll
        self.initial_bankroll = bankroll
        self.results = []

    def run_backtest(self, start_season: int, end_season: int,
                    min_edge: float = 2.0, max_edge: float = 10.0) -> Dict:
        """Run complete backtest across multiple seasons.

        Args:
            start_season: Starting season year
            end_season: Ending season year
            min_edge: Minimum edge threshold (points)
            max_edge: Maximum edge threshold (points)

        Returns:
            Dictionary with complete backtest results
        """
        print(f"Running backtest: {start_season}-{end_season}")
        print(f"Starting bankroll: ${self.bankroll:,.2f}")
        print(f"Edge threshold: {min_edge}-{max_edge} points")
        print("="*60)

        # Reset for fresh backtest
        self.bankroll = self.initial_bankroll
        self.results = []

        for season in range(start_season, end_season + 1):
            print(f"\nSeason {season}")
            print("-"*60)

            season_results = self.run_season_backtest(season, min_edge, max_edge)

            print(f"Season {season} Summary:")
            print(f"  Games analyzed: {season_results['games_analyzed']}")
            print(f"  Bets placed: {season_results['bets_placed']}")
            print(f"  Wins: {season_results['wins']}")
            print(f"  Win rate: {season_results['win_rate']:.1f}%")
            print(f"  ROI: {season_results['roi']:.1f}%")
            print(f"  Profit: ${season_results['profit']:,.2f}")
            print(f"  Ending bankroll: ${self.bankroll:,.2f}")

        # Calculate overall metrics
        metrics = PerformanceMetrics(self.results)
        summary = metrics.calculate_all_metrics()

        print("\n" + "="*60)
        print("BACKTEST COMPLETE")
        print("="*60)
        print(f"Total games analyzed: {summary['total_games']}")
        print(f"Total bets placed: {summary['total_bets']}")
        print(f"Win rate: {summary['win_rate']:.1f}%")
        print(f"ROI: {summary['roi']:.1f}%")
        print(f"Total profit: ${summary['total_profit']:,.2f}")
        print(f"Final bankroll: ${self.bankroll:,.2f}")
        print(f"Sharpe ratio: {summary['sharpe_ratio']:.2f}")
        print(f"Max drawdown: {summary['max_drawdown']:.1f}%")
        print(f"Average CLV: {summary['avg_clv']:.2f} points")

        return summary

    def run_season_backtest(self, season: int, min_edge: float = 2.0,
                           max_edge: float = 10.0) -> Dict:
        """Run backtest for a single season.

        Args:
            season: Season year
            min_edge: Minimum edge threshold
            max_edge: Maximum edge threshold

        Returns:
            Season summary dictionary
        """
        games = self.db.get_games(season=season)

        games_analyzed = 0
        bets_placed = 0
        wins = 0
        total_staked = 0
        total_profit = 0

        for game in games:
            # Only backtest completed games with results
            if game['game_status'] != 'completed':
                continue
            if game['away_score'] is None or game['home_score'] is None:
                continue

            games_analyzed += 1

            # Get odds for this game
            opening_odds = self.db.get_odds(game['game_id'], is_opening=True)
            closing_odds = self.db.get_odds(game['game_id'], is_closing=True)

            if not opening_odds or not closing_odds:
                continue  # Skip games without odds data

            # Analyze game and generate prediction
            prediction = self.analyze_game(game, opening_odds[0])

            if not prediction:
                continue

            # Store prediction
            prediction_id = self.db.insert_prediction(prediction)

            # Check if bet meets criteria
            edge_points = abs(prediction.get('edge_points', 0))

            if edge_points >= min_edge and edge_points <= max_edge:
                # Calculate bet result
                result = self.calculate_bet_result(
                    game, prediction, opening_odds[0], closing_odds[0]
                )

                result['prediction_id'] = prediction_id

                # Track result
                self.db.insert_result(result)
                self.results.append(result)

                # Update bankroll
                profit = result.get('bet_profit', 0)
                self.bankroll += profit

                bets_placed += 1
                total_staked += result.get('stake', 0)
                total_profit += profit

                if result.get('bet_won'):
                    wins += 1

        # Calculate season metrics
        win_rate = (wins / bets_placed * 100) if bets_placed > 0 else 0
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        return {
            'season': season,
            'games_analyzed': games_analyzed,
            'bets_placed': bets_placed,
            'wins': wins,
            'win_rate': win_rate,
            'roi': roi,
            'profit': total_profit,
            'total_staked': total_staked
        }

    def analyze_game(self, game: Dict, odds: Dict) -> Optional[Dict]:
        """Analyze a single game and generate prediction.

        Args:
            game: Game dictionary from database
            odds: Opening odds dictionary

        Returns:
            Prediction dictionary or None
        """
        try:
            sport = game['sport']
            away_team = game['away_team']
            home_team = game['home_team']

            # Get power ratings
            away_rating = self.ratings_engine.get_rating(away_team, sport)
            home_rating = self.ratings_engine.get_rating(home_team, sport)

            if away_rating is None or home_rating is None:
                return None

            # Calculate pre-situational margin
            home_field_advantage = 2.5 if sport == 'NFL' else 3.5
            pre_situational_margin = home_rating - away_rating + home_field_advantage

            # Get injuries (if available)
            injuries = self.db.get_injuries(game['game_id'])
            injury_differential = self._calculate_injury_differential(injuries, home_team, away_team)

            # Get weather (if available)
            weather = self.db.get_weather(game['game_id'])
            weather_adjustment = self._calculate_weather_adjustment(weather) if weather else 0

            # Calculate S/W/E factors
            situational_factors = {
                'rest_advantage': 0,  # Would need rest days data
                'travel_distance': 0,  # Would need travel data
                'is_divisional': game.get('is_divisional', 0),
                'is_playoff': game.get('is_playoff', 0),
            }

            situational_adj = self.swe_calculator.calculate_total_adjustment(
                situational_factors
            )

            # Calculate final predicted margin
            final_margin = pre_situational_margin + injury_differential + weather_adjustment + situational_adj

            # Get market line
            market_line = odds.get('home_line', 0)
            market_price = odds.get('home_price', -110)

            # Calculate edge
            edge_points = abs(final_margin - market_line)

            # Determine bet side
            if final_margin < market_line - 0.5:
                # Bet on away team
                bet_side = away_team
                bet_line = odds.get('away_line', -market_line)
                bet_price = odds.get('away_price', -110)
            elif final_margin > market_line + 0.5:
                # Bet on home team
                bet_side = home_team
                bet_line = market_line
                bet_price = market_price
            else:
                # No bet
                return None

            # Calculate win probability and EV
            win_prob = self._calculate_win_probability(final_margin, market_line, bet_side == home_team)
            ev = self._calculate_expected_value(win_prob, bet_price)

            # Calculate bet sizing
            star_rating = self.bet_sizer.calculate_star_rating(edge_points, win_prob)
            stake = self.bet_sizer.calculate_stake(star_rating, self.bankroll)

            # Create prediction dictionary
            prediction = {
                'game_id': game['game_id'],
                'prediction_date': game['game_date'],
                'model_version': self.model_version,
                'away_power_rating': away_rating,
                'home_power_rating': home_rating,
                'pre_situational_margin': pre_situational_margin,
                'situational_adjustment': situational_adj,
                'weather_adjustment': weather_adjustment,
                'emotional_adjustment': 0,  # Would need emotional factors
                'final_predicted_margin': final_margin,
                'predicted_total': None,  # TODO: Add total predictions
                'bet_recommendation': f"{bet_side} {bet_line}",
                'bet_side': bet_side,
                'bet_line': bet_line,
                'bet_price': bet_price,
                'star_rating': star_rating,
                'suggested_stake': stake,
                'win_probability': win_prob,
                'expected_value': ev,
                'edge_points': edge_points,
                'factors': {
                    'injury_differential': injury_differential,
                    'weather': weather_adjustment,
                    'situational': situational_adj
                }
            }

            return prediction

        except Exception as e:
            print(f"Error analyzing game {game.get('game_id')}: {e}")
            return None

    def calculate_bet_result(self, game: Dict, prediction: Dict,
                            opening_odds: Dict, closing_odds: Dict) -> Dict:
        """Calculate result of a bet.

        Args:
            game: Game dictionary with final scores
            prediction: Prediction dictionary
            opening_odds: Opening odds (what we bet)
            closing_odds: Closing odds (for CLV calculation)

        Returns:
            Result dictionary
        """
        away_score = game['away_score']
        home_score = game['home_score']
        actual_margin = home_score - away_score  # Positive if home wins

        bet_side = prediction['bet_side']
        bet_line = prediction['bet_line']
        bet_price = prediction['bet_price']
        stake = prediction['suggested_stake']

        home_team = game['home_team']

        # Determine if bet won
        if bet_side == home_team:
            # Bet on home team
            bet_won = (actual_margin + bet_line) > 0
        else:
            # Bet on away team
            bet_won = (actual_margin + bet_line) < 0

        # Calculate profit
        if bet_won:
            if bet_price < 0:
                profit = stake * (100 / abs(bet_price))
            else:
                profit = stake * (bet_price / 100)
        else:
            profit = -stake

        # Calculate CLV (Closing Line Value)
        opening_line = bet_line
        closing_line = closing_odds.get('home_line', opening_line)

        if bet_side == home_team:
            clv = closing_line - opening_line
        else:
            clv = opening_line - closing_line

        result = {
            'prediction_id': None,  # Will be set by caller
            'game_id': game['game_id'],
            'bet_placed': 1,
            'actual_margin': actual_margin,
            'actual_total': away_score + home_score,
            'bet_won': 1 if bet_won else 0,
            'bet_profit': profit,
            'clv': clv,
            'closing_line': closing_line,
            'closing_price': closing_odds.get('home_price', -110),
            'result_date': game['game_date'],
            'notes': None,
            'stake': stake,
            'bet_side': bet_side,
            'bet_line': bet_line,
            'star_rating': prediction.get('star_rating', 0)
        }

        return result

    def _calculate_injury_differential(self, injuries: List[Dict],
                                      home_team: str, away_team: str) -> float:
        """Calculate injury impact differential.

        Args:
            injuries: List of injury dictionaries
            home_team: Home team name
            away_team: Away team name

        Returns:
            Adjustment in points (positive favors home)
        """
        home_impact = 0
        away_impact = 0

        for injury in injuries:
            impact = injury.get('impact_score', 0)
            if injury['team'] == home_team:
                home_impact += impact
            elif injury['team'] == away_team:
                away_impact += impact

        # Positive differential favors home team
        return away_impact - home_impact

    def _calculate_weather_adjustment(self, weather: Dict) -> float:
        """Calculate weather impact on total/spread.

        Args:
            weather: Weather dictionary

        Returns:
            Adjustment in points
        """
        impact_score = weather.get('weather_impact_score', 0)

        # Weather impact is typically on totals, but can affect spreads
        # For now, return minimal spread adjustment
        return impact_score * 0.1

    def _calculate_win_probability(self, predicted_margin: float,
                                   market_line: float, bet_on_home: bool) -> float:
        """Calculate win probability for a bet.

        Args:
            predicted_margin: Our predicted margin
            market_line: Market line
            bet_on_home: Whether betting on home team

        Returns:
            Win probability (0-100)
        """
        # Simplified win probability calculation
        # In reality, this would use historical distribution of spreads

        edge = abs(predicted_margin - market_line)

        # Base probability (50% at breakeven)
        # Add 2% for each point of edge
        base_prob = 52.38  # Breakeven at -110

        win_prob = base_prob + (edge * 2.0)

        # Cap at reasonable maximum
        win_prob = min(win_prob, 75.0)

        return win_prob

    def _calculate_expected_value(self, win_prob: float, price: int) -> float:
        """Calculate expected value percentage.

        Args:
            win_prob: Win probability (0-100)
            price: American odds

        Returns:
            EV percentage
        """
        win_prob_decimal = win_prob / 100

        if price < 0:
            decimal_payout = 1 + (100 / abs(price))
        else:
            decimal_payout = 1 + (price / 100)

        ev = (win_prob_decimal * decimal_payout) - 1
        return ev * 100

    def close(self):
        """Close database connection."""
        self.db.close()
