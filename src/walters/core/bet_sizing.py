"""
Billy Walters Star System and Kelly Criterion Bet Sizing

The Star System converts edge percentage into bet size using Billy Walters' methodology:
- 0.5 stars = 5.5-7% edge = 0.5% of bankroll
- 1.0 stars = 7-9% edge = 1% of bankroll
- 1.5 stars = 9-11% edge = 1.5% of bankroll
- 2.0 stars = 11-13% edge = 2% of bankroll
- 2.5 stars = 13-15% edge = 2.5% of bankroll
- 3.0 stars = 15%+ edge = 3% of bankroll

Kelly Criterion is used for mathematical optimization, but Billy Walters
uses fractional Kelly for risk management.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class BetType(Enum):
    """Types of bets supported."""
    SPREAD = "spread"
    TOTAL = "total"
    MONEYLINE = "moneyline"
    TEASER = "teaser"
    PARLAY = "parlay"


@dataclass
class BetRecommendation:
    """Complete bet recommendation with sizing."""
    game: str
    bet_type: BetType
    side: str  # 'home', 'away', 'over', 'under'
    line: float
    price: int  # American odds (e.g., -110)

    # Edge analysis
    edge_percentage: float
    stars: float
    confidence: str  # 'Low', 'Medium', 'High', 'Very High'

    # Sizing
    bankroll: float
    bet_amount: float
    bet_percentage: float  # % of bankroll
    kelly_full: float  # Full Kelly recommendation
    kelly_fraction: float  # Fractional Kelly (recommended)

    # Risk metrics
    risk_of_ruin: float  # Probability of losing entire bankroll
    expected_value: float  # Expected profit

    # Context
    reasoning: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'game': self.game,
            'bet_type': self.bet_type.value,
            'side': self.side,
            'line': self.line,
            'price': self.price,
            'edge_percentage': round(self.edge_percentage, 2),
            'stars': self.stars,
            'confidence': self.confidence,
            'bankroll': round(self.bankroll, 2),
            'bet_amount': round(self.bet_amount, 2),
            'bet_percentage': round(self.bet_percentage, 2),
            'kelly_full': round(self.kelly_full, 2),
            'kelly_fraction': round(self.kelly_fraction, 2),
            'risk_of_ruin': round(self.risk_of_ruin, 4),
            'expected_value': round(self.expected_value, 2),
            'reasoning': self.reasoning
        }


class BetSizingCalculator:
    """
    Calculate optimal bet sizing using Billy Walters Star System and Kelly Criterion.
    """

    # Billy Walters Star Thresholds (from Advanced Masterclass)
    STAR_THRESHOLDS = [
        (0.155, 3.0, 'Very High'),  # 15.5%+ edge = 3 stars
        (0.130, 2.5, 'High'),       # 13-15.5% edge = 2.5 stars
        (0.110, 2.0, 'High'),       # 11-13% edge = 2 stars
        (0.090, 1.5, 'Medium'),     # 9-11% edge = 1.5 stars
        (0.070, 1.0, 'Medium'),     # 7-9% edge = 1 star
        (0.055, 0.5, 'Low'),        # 5.5-7% edge = 0.5 stars
    ]

    # Kelly Criterion parameters
    DEFAULT_KELLY_FRACTION = 0.25  # Use 25% of full Kelly (conservative)
    MAX_BET_PERCENTAGE = 0.05      # Never bet more than 5% of bankroll (safety)

    def __init__(
        self,
        bankroll: float,
        kelly_fraction: float = DEFAULT_KELLY_FRACTION,
        max_bet_pct: float = MAX_BET_PERCENTAGE
    ):
        """
        Initialize bet sizing calculator.

        Args:
            bankroll: Current bankroll in dollars
            kelly_fraction: Fraction of full Kelly to use (default 0.25 = 25%)
            max_bet_pct: Maximum bet as % of bankroll (default 0.05 = 5%)
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.max_bet_pct = max_bet_pct

    def edge_to_stars(self, edge_percentage: float) -> tuple[float, str]:
        """
        Convert edge percentage to star rating.

        Args:
            edge_percentage: Edge as decimal (e.g., 0.08 = 8%)

        Returns:
            Tuple of (stars, confidence_level)
        """
        for threshold, stars, confidence in self.STAR_THRESHOLDS:
            if edge_percentage >= threshold:
                return stars, confidence

        # Below minimum threshold
        return 0.0, 'None'

    def stars_to_bet_percentage(self, stars: float) -> float:
        """
        Convert stars to bet percentage using Billy Walters methodology.

        Rule: 1 star = 1% of bankroll

        Args:
            stars: Star rating (0.5 to 3.0)

        Returns:
            Bet percentage as decimal (e.g., 0.01 = 1%)
        """
        return stars / 100.0

    def calculate_kelly(
        self,
        edge: float,
        price: int,
        fractional: bool = True
    ) -> float:
        """
        Calculate Kelly Criterion bet size.

        Kelly formula: f = (bp - q) / b
        Where:
            f = fraction of bankroll to bet
            b = odds received (decimal)
            p = probability of winning
            q = probability of losing (1 - p)

        Args:
            edge: Your edge as decimal (e.g., 0.08 = 8%)
            price: American odds (e.g., -110, +150)
            fractional: Use fractional Kelly (default True)

        Returns:
            Bet size as fraction of bankroll
        """
        # Convert American odds to decimal
        if price < 0:
            decimal_odds = 100 / abs(price)
        else:
            decimal_odds = price / 100

        # Calculate implied probability from odds
        if price < 0:
            implied_prob = abs(price) / (abs(price) + 100)
        else:
            implied_prob = 100 / (price + 100)

        # Your actual win probability (implied + edge)
        win_prob = implied_prob + edge

        # Kelly formula
        q = 1 - win_prob
        kelly_full = (decimal_odds * win_prob - q) / decimal_odds

        # Apply fractional Kelly if requested
        if fractional:
            kelly_bet = kelly_full * self.kelly_fraction
        else:
            kelly_bet = kelly_full

        # Safety check - never negative, never above max
        kelly_bet = max(0, min(kelly_bet, self.max_bet_pct))

        return kelly_bet

    def calculate_bet_size(
        self,
        edge_percentage: float,
        price: int,
        use_kelly: bool = False
    ) -> dict:
        """
        Calculate bet size using Star System or Kelly Criterion.

        Args:
            edge_percentage: Your edge as decimal (e.g., 0.08 = 8%)
            price: American odds (e.g., -110)
            use_kelly: Use Kelly instead of Star System (default False)

        Returns:
            Dict with complete bet sizing analysis
        """
        # Convert edge to stars
        stars, confidence = self.edge_to_stars(edge_percentage)

        # No bet if below threshold
        if stars == 0.0:
            return {
                'bet': False,
                'stars': 0.0,
                'confidence': 'None',
                'edge_percentage': round(edge_percentage * 100, 2),
                'reason': f'Edge {edge_percentage*100:.1f}% below 5.5% minimum threshold'
            }

        # Calculate Star System bet size
        star_pct = self.stars_to_bet_percentage(stars)
        star_amount = self.bankroll * star_pct

        # Calculate Kelly bet size
        kelly_full = self.calculate_kelly(edge_percentage, price, fractional=False)
        kelly_frac = self.calculate_kelly(edge_percentage, price, fractional=True)
        kelly_amount = self.bankroll * kelly_frac

        # Choose bet size method
        if use_kelly:
            bet_pct = kelly_frac
            bet_amount = kelly_amount
            method = 'Kelly Criterion (fractional)'
        else:
            bet_pct = star_pct
            bet_amount = star_amount
            method = 'Star System'

        # Calculate expected value
        ev = self._calculate_expected_value(bet_amount, edge_percentage, price)

        # Calculate risk of ruin (simplified)
        ror = self._calculate_risk_of_ruin(bet_pct, edge_percentage)

        return {
            'bet': True,
            'stars': stars,
            'confidence': confidence,
            'edge_percentage': round(edge_percentage * 100, 2),
            'method': method,
            'bet_amount': round(bet_amount, 2),
            'bet_percentage': round(bet_pct * 100, 2),
            'kelly_full': round(kelly_full * 100, 2),
            'kelly_fraction': round(kelly_frac * 100, 2),
            'expected_value': round(ev, 2),
            'risk_of_ruin': round(ror, 4),
            'recommendation': self._generate_recommendation(
                stars, bet_amount, confidence, edge_percentage
            )
        }

    def create_bet_recommendation(
        self,
        game: str,
        bet_type: BetType,
        side: str,
        line: float,
        price: int,
        edge_percentage: float,
        reasoning: str,
        use_kelly: bool = False
    ) -> BetRecommendation:
        """
        Create complete bet recommendation.

        Args:
            game: Game description (e.g., "Alabama @ LSU")
            bet_type: Type of bet
            side: Which side to bet
            line: Betting line
            price: American odds
            edge_percentage: Your calculated edge
            reasoning: Why this bet has value
            use_kelly: Use Kelly instead of Star System

        Returns:
            Complete BetRecommendation object
        """
        sizing = self.calculate_bet_size(edge_percentage, price, use_kelly)

        if not sizing['bet']:
            # Return minimal recommendation for no bet
            return BetRecommendation(
                game=game,
                bet_type=bet_type,
                side=side,
                line=line,
                price=price,
                edge_percentage=0,
                stars=0,
                confidence='None',
                bankroll=self.bankroll,
                bet_amount=0,
                bet_percentage=0,
                kelly_full=0,
                kelly_fraction=0,
                risk_of_ruin=0,
                expected_value=0,
                reasoning=sizing['reason']
            )

        return BetRecommendation(
            game=game,
            bet_type=bet_type,
            side=side,
            line=line,
            price=price,
            edge_percentage=sizing['edge_percentage'],
            stars=sizing['stars'],
            confidence=sizing['confidence'],
            bankroll=self.bankroll,
            bet_amount=sizing['bet_amount'],
            bet_percentage=sizing['bet_percentage'],
            kelly_full=sizing['kelly_full'],
            kelly_fraction=sizing['kelly_fraction'],
            risk_of_ruin=sizing['risk_of_ruin'],
            expected_value=sizing['expected_value'],
            reasoning=reasoning
        )

    def update_bankroll(self, new_bankroll: float) -> None:
        """
        Update bankroll after wins/losses.

        Args:
            new_bankroll: New bankroll amount
        """
        self.bankroll = new_bankroll

    # Private helper methods

    def _calculate_expected_value(
        self,
        bet_amount: float,
        edge: float,
        price: int
    ) -> float:
        """
        Calculate expected value of bet.

        EV = (Win Probability × Profit) - (Loss Probability × Loss)
        """
        # Convert price to decimal payout
        if price < 0:
            profit_if_win = bet_amount * (100 / abs(price))
            implied_prob = abs(price) / (abs(price) + 100)
        else:
            profit_if_win = bet_amount * (price / 100)
            implied_prob = 100 / (price + 100)

        # Actual win probability (implied + edge)
        win_prob = implied_prob + edge
        loss_prob = 1 - win_prob

        # Expected value
        ev = (win_prob * profit_if_win) - (loss_prob * bet_amount)

        return ev

    def _calculate_risk_of_ruin(self, bet_pct: float, edge: float) -> float:
        """
        Simplified risk of ruin calculation.

        This is a simplified version. True RoR requires more sophisticated modeling.

        Args:
            bet_pct: Bet size as % of bankroll
            edge: Edge as decimal

        Returns:
            Probability of losing entire bankroll
        """
        # Simplified formula (for equal bet sizes)
        # RoR increases exponentially with bet size and decreases with edge
        if edge <= 0:
            return 1.0  # Certain ruin with no edge

        # Conservative estimate
        risk_factor = (bet_pct * 100) / (edge * 100)
        ror = 1 / (1 + edge / bet_pct) ** (1 / bet_pct)

        # Cap at 1.0
        return min(ror, 1.0)

    def _generate_recommendation(
        self,
        stars: float,
        bet_amount: float,
        confidence: str,
        edge: float
    ) -> str:
        """Generate human-readable recommendation."""
        return (
            f"{stars} STAR BET - Bet ${bet_amount:.2f} ({confidence} confidence, "
            f"{edge*100:.1f}% edge)"
        )


# Convenience functions

def calculate_bet_size(
    bankroll: float,
    edge_percentage: float,
    price: int = -110,
    use_kelly: bool = False
) -> dict:
    """Quick bet size calculation."""
    calc = BetSizingCalculator(bankroll)
    return calc.calculate_bet_size(edge_percentage, price, use_kelly)


def edge_to_stars(edge_percentage: float) -> tuple[float, str]:
    """Quick edge-to-stars conversion."""
    calc = BetSizingCalculator(bankroll=10000)  # Bankroll doesn't matter for this
    return calc.edge_to_stars(edge_percentage)


def create_recommendation(
    game: str,
    bet_type: str,
    side: str,
    line: float,
    price: int,
    edge_percentage: float,
    bankroll: float,
    reasoning: str
) -> BetRecommendation:
    """Quick recommendation creation."""
    calc = BetSizingCalculator(bankroll)
    return calc.create_bet_recommendation(
        game=game,
        bet_type=BetType(bet_type),
        side=side,
        line=line,
        price=price,
        edge_percentage=edge_percentage,
        reasoning=reasoning
    )
