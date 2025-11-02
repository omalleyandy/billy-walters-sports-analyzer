"""
Billy Walters Master Analyzer

This module integrates all core components:
- Power Ratings
- S/W/E Factors
- Key Numbers
- Bet Sizing (Star System)
- CLV Tracking

Provides a unified interface for complete game analysis and bet recommendations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime

from .power_ratings import PowerRatingEngine, GameResult
from .situational_factors import SWEFactorCalculator, GameContext
from .key_numbers import KeyNumberCalculator, KeyNumberAnalysis
from .bet_sizing import BetSizingCalculator, BetRecommendation, BetType
from .clv_tracker import CLVTracker


@dataclass
class ComprehensiveAnalysis:
    """Complete analysis of a game from all perspectives."""
    # Game info
    game: str
    sport: str
    away_team: str
    home_team: str

    # Power ratings
    away_rating: float
    home_rating: float
    predicted_spread: float
    predicted_total: float

    # S/W/E factors
    swe_spread_adjustment: float
    swe_total_adjustment: float
    swe_summary: str
    swe_details: dict

    # Market comparison
    market_spread: float
    market_total: Optional[float]
    spread_price: int
    total_price: int

    # Key number analysis
    key_number_analysis: KeyNumberAnalysis
    edge_percentage: float

    # Bet recommendation
    recommendation: Optional[BetRecommendation]
    should_bet: bool

    # Context
    reasoning: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'game': self.game,
            'sport': self.sport,
            'away_team': self.away_team,
            'home_team': self.home_team,
            'power_ratings': {
                'away_rating': round(self.away_rating, 2),
                'home_rating': round(self.home_rating, 2),
                'predicted_spread': round(self.predicted_spread, 1),
                'predicted_total': round(self.predicted_total, 1),
            },
            'swe_factors': {
                'spread_adjustment': round(self.swe_spread_adjustment, 1),
                'total_adjustment': round(self.swe_total_adjustment, 1),
                'summary': self.swe_summary,
                'details': self.swe_details
            },
            'market': {
                'spread': self.market_spread,
                'total': self.market_total,
                'spread_price': self.spread_price,
                'total_price': self.total_price
            },
            'key_numbers': {
                'crossed': self.key_number_analysis.key_numbers_crossed,
                'edge_percentage': self.key_number_analysis.edge_percentage
            },
            'recommendation': self.recommendation.to_dict() if self.recommendation else None,
            'should_bet': self.should_bet,
            'reasoning': self.reasoning
        }


class BillyWaltersAnalyzer:
    """
    Master analyzer integrating all Billy Walters methodology components.
    """

    def __init__(
        self,
        bankroll: float,
        ratings_file: str = "data/power_ratings/team_ratings.json",
        bets_db: str = "data/bets/bets.db",
        kelly_fraction: float = 0.25
    ):
        """
        Initialize the complete analyzer.

        Args:
            bankroll: Current bankroll
            ratings_file: Path to power ratings storage
            bets_db: Path to bet tracking database
            kelly_fraction: Fraction of Kelly to use (default 0.25 = 25%)
        """
        self.bankroll = bankroll

        # Initialize all components
        self.power_engine = PowerRatingEngine(ratings_file)
        self.swe_calculator = SWEFactorCalculator()
        self.key_calc = KeyNumberCalculator()
        self.bet_sizer = BetSizingCalculator(bankroll, kelly_fraction)
        self.clv_tracker = CLVTracker(bets_db)

    def analyze_game(
        self,
        away_team: str,
        home_team: str,
        sport: str,
        market_spread: float,
        market_total: Optional[float] = None,
        spread_price: int = -110,
        total_price: int = -110,
        game_context: Optional[GameContext] = None,
        game_date: Optional[str] = None
    ) -> ComprehensiveAnalysis:
        """
        Perform complete Billy Walters analysis on a game.

        Args:
            away_team: Away team name
            home_team: Home team name
            sport: 'nfl' or 'cfb'
            market_spread: Current market spread (negative = home favored)
            market_total: Current market total (optional)
            spread_price: Spread price (default -110)
            total_price: Total price (default -110)
            game_context: GameContext with S/W/E data (optional)
            game_date: Game date YYYY-MM-DD (optional)

        Returns:
            ComprehensiveAnalysis with complete breakdown
        """
        # Step 1: Get power ratings
        away_rating = self.power_engine.get_rating(away_team, sport)
        home_rating = self.power_engine.get_rating(home_team, sport)

        # Step 2: Calculate S/W/E adjustments
        swe_adjustments = {'total_spread_adjustment': 0, 'total_adjustment': 0, 'summary': 'No context provided'}
        if game_context:
            swe_adjustments = self.swe_calculator.calculate_all_factors(game_context)

        swe_spread_adj = swe_adjustments['total_spread_adjustment']
        swe_total_adj = swe_adjustments['total_adjustment']

        # Step 3: Calculate predicted lines (power ratings + S/W/E)
        base_spread = self.power_engine.calculate_predicted_spread(
            away_team, home_team, sport
        )
        predicted_spread = base_spread + swe_spread_adj

        predicted_total = self.power_engine.calculate_predicted_total(
            away_team, home_team, sport,
            weather_adjustment=abs(swe_total_adj)  # Weather reduces total
        )

        # Step 4: Key number analysis
        key_analysis = self.key_calc.calculate_edge_value(
            predicted_spread, market_spread, sport
        )

        edge_percentage = key_analysis.edge_percentage / 100  # Convert to decimal

        # Step 5: Generate bet recommendation
        recommendation = None
        should_bet = False

        if edge_percentage >= 0.055:  # 5.5% minimum (0.5 star threshold)
            game_desc = f"{away_team} @ {home_team}"

            # Determine side
            if predicted_spread < market_spread:
                side = "home"
                bet_line = market_spread
            else:
                side = "away"
                bet_line = market_spread

            # Create reasoning
            reasoning = self._build_reasoning(
                away_team, home_team, away_rating, home_rating,
                predicted_spread, market_spread, swe_adjustments, key_analysis
            )

            recommendation = self.bet_sizer.create_bet_recommendation(
                game=game_desc,
                bet_type=BetType.SPREAD,
                side=side,
                line=bet_line,
                price=spread_price,
                edge_percentage=edge_percentage,
                reasoning=reasoning,
                use_kelly=False  # Use star system
            )

            should_bet = recommendation.stars > 0
        else:
            reasoning = (
                f"Edge {edge_percentage*100:.1f}% below 5.5% minimum threshold. "
                f"Predicted spread: {predicted_spread:.1f}, Market: {market_spread:.1f}"
            )

        # Build complete analysis
        return ComprehensiveAnalysis(
            game=f"{away_team} @ {home_team}",
            sport=sport,
            away_team=away_team,
            home_team=home_team,
            away_rating=away_rating,
            home_rating=home_rating,
            predicted_spread=predicted_spread,
            predicted_total=predicted_total,
            swe_spread_adjustment=swe_spread_adj,
            swe_total_adjustment=swe_total_adj,
            swe_summary=swe_adjustments['summary'],
            swe_details=swe_adjustments,
            market_spread=market_spread,
            market_total=market_total,
            spread_price=spread_price,
            total_price=total_price,
            key_number_analysis=key_analysis,
            edge_percentage=edge_percentage,
            recommendation=recommendation,
            should_bet=should_bet,
            reasoning=reasoning if not recommendation else recommendation.reasoning
        )

    def place_bet(
        self,
        analysis: ComprehensiveAnalysis,
        game_date: str
    ) -> int:
        """
        Log a bet in the CLV tracker based on analysis.

        Args:
            analysis: ComprehensiveAnalysis with bet recommendation
            game_date: Game date YYYY-MM-DD

        Returns:
            bet_id
        """
        if not analysis.recommendation or not analysis.should_bet:
            raise ValueError("Cannot place bet - no valid recommendation")

        rec = analysis.recommendation

        bet_id = self.clv_tracker.log_bet(
            game=analysis.game,
            game_date=game_date,
            sport=analysis.sport,
            bet_type=rec.bet_type.value,
            side=rec.side,
            your_line=analysis.predicted_spread,
            opening_line=analysis.market_spread,
            price=rec.price,
            edge_percentage=rec.edge_percentage / 100,  # Store as decimal
            stars=rec.stars,
            bet_amount=rec.bet_amount,
            bankroll=self.bankroll,
            reasoning=rec.reasoning,
            swe_factors=analysis.swe_details
        )

        # Update bankroll
        self.bankroll -= rec.bet_amount
        self.bet_sizer.update_bankroll(self.bankroll)

        return bet_id

    def update_game_result(
        self,
        bet_id: int,
        closing_line: float,
        actual_result: str,
        profit: float
    ) -> None:
        """
        Update bet result and CLV after game completes.

        Args:
            bet_id: ID of bet to update
            closing_line: Closing line at game start
            actual_result: 'win', 'loss', or 'push'
            profit: Profit or loss amount
        """
        # Update closing line and calculate CLV
        self.clv_tracker.update_closing_line(bet_id, closing_line)

        # Update result and profit
        self.clv_tracker.update_result(bet_id, actual_result, profit)

        # Update bankroll
        self.bankroll += profit
        self.bet_sizer.update_bankroll(self.bankroll)

    def update_power_ratings(self, game_result: GameResult) -> None:
        """
        Update power ratings after a game completes.

        Args:
            game_result: GameResult with complete game data
        """
        self.power_engine.update_rating(game_result)
        self.power_engine.save_ratings()

    def get_performance_report(self) -> str:
        """
        Generate comprehensive performance report.

        Returns:
            Formatted report string
        """
        return self.clv_tracker.generate_report()

    def get_team_ratings(self, sport: Optional[str] = None) -> List[dict]:
        """
        Get all team ratings.

        Args:
            sport: Optional sport filter

        Returns:
            List of team ratings sorted by rating
        """
        ratings = self.power_engine.get_all_ratings(sport)
        return [r.to_dict() for r in ratings]

    def save_state(self) -> None:
        """Save all state (ratings, etc.)."""
        self.power_engine.save_ratings()

    def close(self) -> None:
        """Clean up resources."""
        self.clv_tracker.close()

    # Private helper methods

    def _build_reasoning(
        self,
        away_team: str,
        home_team: str,
        away_rating: float,
        home_rating: float,
        predicted_spread: float,
        market_spread: float,
        swe_factors: dict,
        key_analysis: KeyNumberAnalysis
    ) -> str:
        """Build detailed reasoning for bet recommendation."""
        lines = []

        # Power rating edge
        rating_diff = home_rating - away_rating
        lines.append(
            f"Power Ratings: {home_team} {rating_diff:+.1f} vs {away_team} "
            f"(Home: {home_rating:.1f}, Away: {away_rating:.1f})"
        )

        # S/W/E factors
        if swe_factors['total_spread_adjustment'] != 0:
            lines.append(f"S/W/E Adjustment: {swe_factors['summary']}")

        # Predicted vs market
        edge_points = abs(predicted_spread - market_spread)
        lines.append(
            f"Predicted: {predicted_spread:.1f}, Market: {market_spread:.1f} "
            f"({edge_points:.1f} point edge)"
        )

        # Key numbers
        if key_analysis.key_numbers_crossed:
            lines.append(
                f"Key numbers crossed: {key_analysis.key_numbers_crossed} "
                f"({key_analysis.edge_percentage:.1f}% value)"
            )

        return " | ".join(lines)


# Convenience function

def create_analyzer(
    bankroll: float,
    ratings_file: str = "data/power_ratings/team_ratings.json",
    bets_db: str = "data/bets/bets.db"
) -> BillyWaltersAnalyzer:
    """Create a new analyzer instance."""
    return BillyWaltersAnalyzer(bankroll, ratings_file, bets_db)
