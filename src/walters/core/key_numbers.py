"""
Billy Walters Key Number Analysis

Key numbers are point margins that occur more frequently than others.
Understanding key numbers is critical for:
1. Evaluating the true value of buying/selling half-points
2. Calculating precise edge percentages
3. Timing bet placement (bet favorites early, dogs late)

Billy Walters Key Number Values (from Advanced Masterclass):
- NFL 3: 8% of games (worth $20-$22 to buy half-point)
- NFL 7: 6% of games (worth $13 to buy)
- NFL 6, 10, 14: 4-5% of games
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


# Billy Walters NFL Key Numbers (from historical data analysis)
# Values represent percentage of games landing on that exact margin
NFL_KEY_NUMBERS = {
    1: 0.023,   # 2.3%
    2: 0.028,   # 2.8%
    3: 0.080,   # 8.0% - CRITICAL
    4: 0.038,   # 3.8%
    5: 0.023,   # 2.3%
    6: 0.050,   # 5.0% - IMPORTANT
    7: 0.060,   # 6.0% - CRITICAL
    8: 0.028,   # 2.8%
    9: 0.025,   # 2.5%
    10: 0.045,  # 4.5% - IMPORTANT
    11: 0.020,  # 2.0%
    12: 0.018,  # 1.8%
    13: 0.023,  # 2.3%
    14: 0.050,  # 5.0% - IMPORTANT
    15: 0.015,  # 1.5%
    16: 0.013,  # 1.3%
    17: 0.028,  # 2.8%
    20: 0.020,  # 2.0%
    21: 0.023,  # 2.3%
}

# CFB Key Numbers (different from NFL - more variance)
CFB_KEY_NUMBERS = {
    1: 0.020,   # 2.0%
    2: 0.025,   # 2.5%
    3: 0.070,   # 7.0% - Still important but less than NFL
    4: 0.035,   # 3.5%
    5: 0.020,   # 2.0%
    6: 0.045,   # 4.5%
    7: 0.050,   # 5.0% - Important but less than NFL
    8: 0.025,   # 2.5%
    9: 0.023,   # 2.3%
    10: 0.040,  # 4.0%
    11: 0.018,  # 1.8%
    13: 0.020,  # 2.0%
    14: 0.045,  # 4.5%
    17: 0.030,  # 3.0%
    20: 0.025,  # 2.5%
    21: 0.028,  # 2.8%
}

# Average value for non-key numbers
DEFAULT_VALUE = 0.015  # 1.5%


@dataclass
class KeyNumberAnalysis:
    """Analysis of key numbers between two lines."""
    sport: str
    line1: float
    line2: float
    key_numbers_crossed: List[int]
    total_value: float  # Sum of key number values crossed
    edge_percentage: float  # Total edge as percentage
    recommendation: str


class KeyNumberCalculator:
    """
    Calculate key number value and edge analysis.

    Billy Walters methodology:
    1. Identify all key numbers crossed between your line and market line
    2. Sum their values to get total edge percentage
    3. Consider half-point positions relative to key numbers
    4. Adjust for directional bias (favorites vs underdogs)
    """

    def __init__(self):
        self.nfl_keys = NFL_KEY_NUMBERS
        self.cfb_keys = CFB_KEY_NUMBERS

    def get_key_numbers(self, sport: str) -> Dict[int, float]:
        """Get key numbers for a sport."""
        sport = sport.lower()
        if sport == 'nfl':
            return self.nfl_keys
        elif sport in ['cfb', 'ncaaf', 'college_football']:
            return self.cfb_keys
        else:
            return self.nfl_keys  # Default to NFL

    def calculate_edge_value(
        self,
        your_line: float,
        market_line: float,
        sport: str = 'nfl'
    ) -> KeyNumberAnalysis:
        """
        Calculate edge value considering key numbers.

        Billy Walters approach:
        - Each key number crossed adds its percentage value
        - Half-points matter based on proximity to key numbers
        - Crossing zero (upset) deducts value

        Args:
            your_line: Your predicted spread (negative = home favored)
            market_line: Market spread (negative = home favored)
            sport: 'nfl' or 'cfb'

        Returns:
            KeyNumberAnalysis with complete breakdown
        """
        key_numbers = self.get_key_numbers(sport)

        # If lines are identical, no edge
        if your_line == market_line:
            return KeyNumberAnalysis(
                sport=sport,
                line1=your_line,
                line2=market_line,
                key_numbers_crossed=[],
                total_value=0.0,
                edge_percentage=0.0,
                recommendation="NO BET - No edge (lines match)"
            )

        # Find range and direction
        start = min(abs(your_line), abs(market_line))
        end = max(abs(your_line), abs(market_line))

        # Track key numbers crossed
        crossed = []
        total_value = 0.0

        # Analyze each point in the range
        for point in range(int(start), int(end) + 1):
            point_value = key_numbers.get(point, DEFAULT_VALUE)

            # Check if this key number was actually crossed
            if start <= point <= end:
                crossed.append(point)

                # Full value if we crossed the whole number
                # Half value if we're on a half-point
                if self._is_on_whole_number(your_line) or self._is_on_whole_number(market_line):
                    # One line is on the key number exactly
                    if point == int(your_line) or point == int(market_line):
                        total_value += point_value / 2
                    else:
                        total_value += point_value
                else:
                    total_value += point_value

        # Penalty for crossing zero (upset prediction vs market)
        if self._crosses_zero(your_line, market_line):
            # Deduct one point value (upset picks are harder)
            total_value -= DEFAULT_VALUE

        # Convert to edge percentage
        edge_percentage = total_value * 100

        # Generate recommendation
        recommendation = self._generate_recommendation(
            edge_percentage, your_line, market_line, crossed
        )

        return KeyNumberAnalysis(
            sport=sport,
            line1=your_line,
            line2=market_line,
            key_numbers_crossed=crossed,
            total_value=round(total_value, 4),
            edge_percentage=round(edge_percentage, 2),
            recommendation=recommendation
        )

    def get_half_point_value(
        self,
        line: float,
        sport: str = 'nfl'
    ) -> float:
        """
        Get the value of a half-point at a specific line.

        Billy Walters: The value of a half-point depends on proximity to key numbers.

        Args:
            line: Current line (e.g., -3.0, -2.5, -3.5)
            sport: 'nfl' or 'cfb'

        Returns:
            Value as decimal (e.g., 0.08 = 8%)
        """
        key_numbers = self.get_key_numbers(sport)
        abs_line = abs(line)

        # If on a whole number, check if it's a key number
        if abs_line == int(abs_line):
            return key_numbers.get(int(abs_line), DEFAULT_VALUE)

        # If on a half-point, check the adjacent key numbers
        lower = int(abs_line)
        upper = lower + 1

        lower_value = key_numbers.get(lower, DEFAULT_VALUE)
        upper_value = key_numbers.get(upper, DEFAULT_VALUE)

        # Value is average of adjacent key numbers
        return (lower_value + upper_value) / 2

    def should_buy_half_point(
        self,
        current_line: float,
        price_difference: int,
        sport: str = 'nfl'
    ) -> dict:
        """
        Determine if buying a half-point is +EV.

        Billy Walters rule: Only buy half-points if the value justifies the price.

        Args:
            current_line: Your current line (e.g., -3.0)
            price_difference: Additional juice to buy half-point (e.g., 20 means -110 → -130)
            sport: 'nfl' or 'cfb'

        Returns:
            Dict with recommendation and analysis
        """
        half_point_value = self.get_half_point_value(current_line, sport)

        # Convert price difference to percentage
        # Rule of thumb: -110 = 52.38% break-even, -130 = 56.52%
        # Difference of 20 cents ≈ 4.14% additional risk
        price_cost = self._price_diff_to_percentage(price_difference)

        # Compare value to cost
        is_profitable = half_point_value > price_cost

        return {
            'current_line': current_line,
            'half_point_value': round(half_point_value * 100, 2),  # As percentage
            'price_cost': round(price_cost * 100, 2),
            'price_difference': price_difference,
            'is_profitable': is_profitable,
            'recommendation': 'BUY' if is_profitable else 'DO NOT BUY'
        }

    def get_optimal_bet_timing(
        self,
        your_line: float,
        current_market_line: float,
        sport: str = 'nfl'
    ) -> dict:
        """
        Billy Walters timing strategy: "Bet favorites early, dogs late"

        Reasoning:
        - Favorites: Public bets them, line moves up, lock in early
        - Underdogs: Public avoids them, line may improve, wait for better price

        Args:
            your_line: Your predicted spread
            current_market_line: Current market spread
            sport: 'nfl' or 'cfb'

        Returns:
            Dict with timing recommendation
        """
        # Determine if bet is on favorite or underdog
        if your_line < current_market_line:
            # You favor home more than market (bet home, likely favorite)
            bet_side = 'favorite'
            timing = 'BET NOW (early)'
            reasoning = 'Favorites attract public money. Line likely to move against you.'
        else:
            # You favor away more than market (bet away, likely underdog)
            bet_side = 'underdog'
            timing = 'WAIT (if possible)'
            reasoning = 'Underdogs get less public action. Line may improve closer to game time.'

        # Check proximity to key numbers
        key_numbers = self.get_key_numbers(sport)
        closest_key = self._find_closest_key_number(current_market_line, key_numbers)

        # If close to key number, timing matters more
        distance_to_key = abs(abs(current_market_line) - closest_key)
        if distance_to_key <= 0.5:
            urgency = 'HIGH'
            reasoning += f' Line is near key number {closest_key}.'
        else:
            urgency = 'MEDIUM'

        return {
            'bet_side': bet_side,
            'timing': timing,
            'urgency': urgency,
            'reasoning': reasoning,
            'closest_key_number': closest_key,
            'distance_to_key': round(distance_to_key, 1)
        }

    # Private helper methods

    def _is_on_whole_number(self, line: float) -> bool:
        """Check if line is on a whole number (e.g., -3.0 vs -3.5)."""
        return line == int(line)

    def _crosses_zero(self, line1: float, line2: float) -> bool:
        """Check if lines cross zero (one favors home, other favors away)."""
        return (line1 < 0 and line2 > 0) or (line1 > 0 and line2 < 0)

    def _generate_recommendation(
        self,
        edge_percentage: float,
        your_line: float,
        market_line: float,
        crossed: List[int]
    ) -> str:
        """Generate betting recommendation based on edge."""
        if edge_percentage >= 7.0:  # 1 star threshold
            side = 'HOME' if your_line < market_line else 'AWAY'
            return f"STRONG BET {side} - {edge_percentage:.1f}% edge (key numbers: {crossed})"
        elif edge_percentage >= 5.5:  # 0.5 star threshold
            side = 'HOME' if your_line < market_line else 'AWAY'
            return f"BET {side} - {edge_percentage:.1f}% edge (key numbers: {crossed})"
        else:
            return f"NO BET - Insufficient edge ({edge_percentage:.1f}%)"

    def _price_diff_to_percentage(self, price_diff: int) -> float:
        """
        Convert price difference to percentage cost.

        Approximate conversion:
        -110 = 52.38% break-even
        -120 = 54.55%
        -130 = 56.52%

        Each 10 cents ≈ 2% additional cost
        """
        return (price_diff / 10) * 0.02

    def _find_closest_key_number(self, line: float, key_numbers: Dict[int, float]) -> int:
        """Find the closest key number to a given line."""
        abs_line = abs(line)
        closest = min(key_numbers.keys(), key=lambda k: abs(k - abs_line))
        return closest


# Convenience functions

def calculate_edge(
    your_line: float,
    market_line: float,
    sport: str = 'nfl'
) -> KeyNumberAnalysis:
    """Quick edge calculation with key number analysis."""
    calc = KeyNumberCalculator()
    return calc.calculate_edge_value(your_line, market_line, sport)


def should_buy_half(
    line: float,
    price_diff: int,
    sport: str = 'nfl'
) -> dict:
    """Quick half-point buy analysis."""
    calc = KeyNumberCalculator()
    return calc.should_buy_half_point(line, price_diff, sport)


def get_bet_timing(
    your_line: float,
    market_line: float,
    sport: str = 'nfl'
) -> dict:
    """Quick bet timing recommendation."""
    calc = KeyNumberCalculator()
    return calc.get_optimal_bet_timing(your_line, market_line, sport)
