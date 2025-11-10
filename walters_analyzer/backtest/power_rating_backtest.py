"""
Power Rating System Backtesting Engine

Tests the Billy Walters 90/10 power rating formula against actual NFL game results
to validate prediction accuracy and rating evolution.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from ..valuation.power_ratings import (
    PowerRatingSystem,
    GameResult,
    initialize_nfl_ratings,
)


@dataclass
class PredictionResult:
    """Result of a single game prediction"""

    date: date
    home_team: str
    away_team: str
    predicted_spread: float
    actual_home_score: int
    actual_away_score: int
    actual_margin: int  # Positive = home won
    prediction_error: float  # abs(predicted - actual)
    correct_winner: bool
    covered_spread: bool  # Did favorite cover?

    @property
    def favorite(self) -> str:
        """Return the favorite team"""
        return self.home_team if self.predicted_spread > 0 else self.away_team

    @property
    def underdog(self) -> str:
        """Return the underdog team"""
        return self.away_team if self.predicted_spread > 0 else self.home_team


@dataclass
class BacktestResult:
    """Complete backtest results with metrics"""

    start_date: date
    end_date: date
    total_games: int
    predictions: List[PredictionResult] = field(default_factory=list)

    # Accuracy metrics
    correct_winner_pct: float = 0.0
    ats_record: Tuple[int, int, int] = (0, 0, 0)  # (wins, losses, pushes)
    ats_win_pct: float = 0.0
    mean_absolute_error: float = 0.0
    median_absolute_error: float = 0.0

    # Rating evolution
    initial_ratings: Dict[str, float] = field(default_factory=dict)
    final_ratings: Dict[str, float] = field(default_factory=dict)
    biggest_movers: List[Tuple[str, float]] = field(default_factory=list)

    # Performance by week
    weekly_stats: Dict[int, Dict] = field(default_factory=dict)


class PowerRatingBacktest:
    """
    Backtest engine for Power Rating System

    Usage:
        >>> backtest = PowerRatingBacktest()
        >>> result = backtest.run_backtest(nfl_2024_week1_to_9_games)
        >>> print(result.ats_win_pct)
        0.547
    """

    def __init__(self, initial_ratings: Optional[Dict[str, float]] = None):
        """
        Initialize backtest engine

        Args:
            initial_ratings: Starting ratings (defaults to NFL 2024 preseason)
        """
        self.prs = PowerRatingSystem()

        if initial_ratings:
            self.prs.import_ratings(initial_ratings)
        else:
            self.prs.import_ratings(initialize_nfl_ratings())

        self.initial_ratings = self.prs.export_ratings()

    def run_backtest(
        self, games: List[Dict], week_labels: Optional[List[int]] = None
    ) -> BacktestResult:
        """
        Run backtest on historical games

        Args:
            games: List of game dicts with keys:
                - date: date object or ISO string
                - home_team: str
                - away_team: str
                - home_score: int
                - away_score: int
                - week: int (optional)
            week_labels: Optional list of week numbers for each game

        Returns:
            BacktestResult with comprehensive metrics
        """
        predictions: List[PredictionResult] = []
        weekly_stats: Dict[int, Dict] = {}

        for i, game_data in enumerate(games):
            # Parse game data
            game_date = self._parse_date(game_data["date"])
            home_team = game_data["home_team"]
            away_team = game_data["away_team"]
            home_score = game_data["home_score"]
            away_score = game_data["away_score"]
            week = game_data.get("week", week_labels[i] if week_labels else None)

            # Make prediction BEFORE updating ratings
            predicted_spread = self.prs.calculate_matchup_spread(home_team, away_team)

            if predicted_spread is None:
                # Skip if teams not in system
                continue

            # Calculate actual result
            actual_margin = home_score - away_score

            # Evaluate prediction
            prediction_error = abs(predicted_spread - actual_margin)
            correct_winner = (
                (
                    predicted_spread > 0 and actual_margin > 0
                )  # Predicted home win, home won
                or (
                    predicted_spread < 0 and actual_margin < 0
                )  # Predicted away win, away won
                or (predicted_spread == 0)  # Predicted tie (rare)
            )

            # ATS (Against The Spread) evaluation
            # Favorite covers if they win by MORE than the predicted spread
            if predicted_spread > 0:  # Home favored
                covered_spread = actual_margin > predicted_spread
            else:  # Away favored
                covered_spread = actual_margin < predicted_spread

            # Store prediction result
            pred_result = PredictionResult(
                date=game_date,
                home_team=home_team,
                away_team=away_team,
                predicted_spread=predicted_spread,
                actual_home_score=home_score,
                actual_away_score=away_score,
                actual_margin=actual_margin,
                prediction_error=prediction_error,
                correct_winner=correct_winner,
                covered_spread=covered_spread,
            )
            predictions.append(pred_result)

            # Track weekly stats
            if week:
                if week not in weekly_stats:
                    weekly_stats[week] = {
                        "games": 0,
                        "correct_winners": 0,
                        "ats_wins": 0,
                        "total_error": 0.0,
                    }
                weekly_stats[week]["games"] += 1
                weekly_stats[week]["correct_winners"] += int(correct_winner)
                weekly_stats[week]["ats_wins"] += int(covered_spread)
                weekly_stats[week]["total_error"] += prediction_error

            # NOW update ratings based on actual result
            result = GameResult(
                date=game_date,
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score,
                location="home",
            )
            self.prs.update_ratings_from_game(result)

        # Calculate aggregate metrics
        total_games = len(predictions)
        correct_winners = sum(p.correct_winner for p in predictions)
        ats_wins = sum(p.covered_spread for p in predictions)
        ats_losses = total_games - ats_wins

        errors = [p.prediction_error for p in predictions]
        mean_error = sum(errors) / len(errors) if errors else 0.0
        median_error = sorted(errors)[len(errors) // 2] if errors else 0.0

        # Calculate rating changes
        final_ratings = self.prs.export_ratings()
        rating_changes = []
        for team in self.initial_ratings:
            if team in final_ratings:
                change = final_ratings[team] - self.initial_ratings[team]
                rating_changes.append((team, change))

        biggest_movers = sorted(rating_changes, key=lambda x: abs(x[1]), reverse=True)[
            :10
        ]

        # Calculate weekly stats percentages
        for week, stats in weekly_stats.items():
            if stats["games"] > 0:
                stats["winner_accuracy"] = stats["correct_winners"] / stats["games"]
                stats["ats_accuracy"] = stats["ats_wins"] / stats["games"]
                stats["avg_error"] = stats["total_error"] / stats["games"]

        # Build result
        result = BacktestResult(
            start_date=predictions[0].date if predictions else date.today(),
            end_date=predictions[-1].date if predictions else date.today(),
            total_games=total_games,
            predictions=predictions,
            correct_winner_pct=correct_winners / total_games if total_games else 0.0,
            ats_record=(ats_wins, ats_losses, 0),
            ats_win_pct=ats_wins / total_games if total_games else 0.0,
            mean_absolute_error=mean_error,
            median_absolute_error=median_error,
            initial_ratings=self.initial_ratings,
            final_ratings=final_ratings,
            biggest_movers=biggest_movers,
            weekly_stats=weekly_stats,
        )

        return result

    def generate_report(
        self, result: BacktestResult, output_file: Optional[Path] = None
    ) -> str:
        """
        Generate detailed backtest report

        Args:
            result: BacktestResult from run_backtest()
            output_file: Optional file to save report

        Returns:
            Report as formatted string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("POWER RATING SYSTEM BACKTEST REPORT")
        lines.append("=" * 80)
        lines.append(f"Test Period: {result.start_date} to {result.end_date}")
        lines.append(f"Total Games: {result.total_games}")
        lines.append("")

        # Overall accuracy
        lines.append("=" * 80)
        lines.append("PREDICTION ACCURACY")
        lines.append("=" * 80)
        lines.append(
            f"Winner Prediction: {result.correct_winner_pct:.1%} "
            f"({sum(p.correct_winner for p in result.predictions)}/{result.total_games})"
        )
        lines.append(
            f"ATS Record: {result.ats_record[0]}-{result.ats_record[1]}-{result.ats_record[2]} "
            f"({result.ats_win_pct:.1%})"
        )
        lines.append(f"Mean Absolute Error: {result.mean_absolute_error:.2f} points")
        lines.append(
            f"Median Absolute Error: {result.median_absolute_error:.2f} points"
        )
        lines.append("")

        # Weekly performance
        if result.weekly_stats:
            lines.append("=" * 80)
            lines.append("WEEKLY PERFORMANCE")
            lines.append("=" * 80)
            lines.append(
                f"{'Week':<8} {'Games':<8} {'Winner%':<12} {'ATS%':<12} {'Avg Error'}"
            )
            lines.append("-" * 80)
            for week in sorted(result.weekly_stats.keys()):
                stats = result.weekly_stats[week]
                lines.append(
                    f"{week:<8} {stats['games']:<8} "
                    f"{stats['winner_accuracy']:<11.1%} "
                    f"{stats['ats_accuracy']:<11.1%} "
                    f"{stats['avg_error']:.2f}"
                )
            lines.append("")

        # Best predictions
        lines.append("=" * 80)
        lines.append("BEST PREDICTIONS (Smallest Errors)")
        lines.append("=" * 80)
        best_preds = sorted(result.predictions, key=lambda x: x.prediction_error)[:10]
        for pred in best_preds:
            lines.append(
                f"{pred.date} {pred.away_team} @ {pred.home_team}: "
                f"Predicted {pred.predicted_spread:+.1f}, Actual {pred.actual_margin:+d} "
                f"(Error: {pred.prediction_error:.1f})"
            )
        lines.append("")

        # Worst predictions
        lines.append("=" * 80)
        lines.append("WORST PREDICTIONS (Largest Errors)")
        lines.append("=" * 80)
        worst_preds = sorted(
            result.predictions, key=lambda x: x.prediction_error, reverse=True
        )[:10]
        for pred in worst_preds:
            lines.append(
                f"{pred.date} {pred.away_team} @ {pred.home_team}: "
                f"Predicted {pred.predicted_spread:+.1f}, Actual {pred.actual_margin:+d} "
                f"(Error: {pred.prediction_error:.1f})"
            )
        lines.append("")

        # Rating evolution
        lines.append("=" * 80)
        lines.append("RATING EVOLUTION (Biggest Movers)")
        lines.append("=" * 80)
        lines.append(f"{'Team':<25} {'Initial':<10} {'Final':<10} {'Change'}")
        lines.append("-" * 80)
        for team, change in result.biggest_movers:
            initial = result.initial_ratings[team]
            final = result.final_ratings[team]
            lines.append(f"{team:<25} {initial:<10.2f} {final:<10.2f} {change:+.2f}")
        lines.append("")

        # Final top 10
        lines.append("=" * 80)
        lines.append("FINAL TOP 10 TEAMS")
        lines.append("=" * 80)
        top_teams = sorted(
            result.final_ratings.items(), key=lambda x: x[1], reverse=True
        )[:10]
        for i, (team, rating) in enumerate(top_teams, 1):
            initial = result.initial_ratings.get(team, 0.0)
            change = rating - initial
            lines.append(f"{i:2d}. {team:<25} {rating:.2f} ({change:+.2f})")
        lines.append("")

        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        report = "\n".join(lines)

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(report)

        return report

    def _parse_date(self, date_input) -> date:
        """Parse date from various formats"""
        if isinstance(date_input, date):
            return date_input
        elif isinstance(date_input, str):
            # Try ISO format
            try:
                return datetime.fromisoformat(date_input).date()
            except:
                # Try other common formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
                    try:
                        return datetime.strptime(date_input, fmt).date()
                    except:
                        continue
        raise ValueError(f"Cannot parse date: {date_input}")
