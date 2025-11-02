"""
Tests for Key Number Logic
"""

import pytest
from walters_analyzer.key_numbers import (
    KeyNumberCalculator,
    NFL_KEY_NUMBERS,
    CFB_KEY_NUMBERS
)


@pytest.fixture
def calculator():
    """Create calculator instance."""
    return KeyNumberCalculator()


class TestKeyNumberData:
    """Test key number data integrity."""

    def test_nfl_key_three_is_highest(self):
        """Test NFL 3 is the most valuable key number."""
        assert NFL_KEY_NUMBERS[3] == 0.08  # 8%
        assert NFL_KEY_NUMBERS[3] > NFL_KEY_NUMBERS[7]

    def test_nfl_seven_is_second(self):
        """Test NFL 7 is second most valuable."""
        assert NFL_KEY_NUMBERS[7] == 0.06  # 6%

    def test_cfb_keys_lower_than_nfl(self):
        """Test CFB key numbers have lower values than NFL."""
        assert CFB_KEY_NUMBERS[3] < NFL_KEY_NUMBERS[3]
        assert CFB_KEY_NUMBERS[7] < NFL_KEY_NUMBERS[7]


class TestEdgeCalculation:
    """Test edge value calculations."""

    def test_crossing_key_three(self, calculator):
        """Test crossing NFL key number 3."""
        # Your line -2.5, market -3.5 (crossing 3)
        analysis = calculator.calculate_edge_value(
            your_line=-2.5,
            market_line=-3.5,
            sport='nfl'
        )

        # Should recognize crossing key 3
        assert 3 in analysis.key_numbers_crossed
        assert analysis.edge_percentage > 0

    def test_crossing_key_seven(self, calculator):
        """Test crossing NFL key number 7."""
        analysis = calculator.calculate_edge_value(
            your_line=-6.5,
            market_line=-7.5,
            sport='nfl'
        )

        assert 7 in analysis.key_numbers_crossed
        assert analysis.edge_percentage > 0

    def test_multiple_key_numbers(self, calculator):
        """Test crossing multiple key numbers."""
        # Your line -2, market -8 (crosses 3, 4, 5, 6, 7)
        analysis = calculator.calculate_edge_value(
            your_line=-2.0,
            market_line=-8.0,
            sport='nfl'
        )

        # Should cross keys 3, 6, 7
        assert 3 in analysis.key_numbers_crossed
        assert 7 in analysis.key_numbers_crossed
        # Edge should be substantial
        assert analysis.edge_percentage > 10

    def test_no_key_numbers_crossed(self, calculator):
        """Test when no key numbers are crossed."""
        # -4.5 to -4.0 (crosses 4, which has minimal value)
        analysis = calculator.calculate_edge_value(
            your_line=-4.5,
            market_line=-4.0,
            sport='nfl'
        )

        # Should have minimal edge (key 4 = 3.8%)
        assert analysis.edge_percentage < 5  # Small edge, not major key
        assert 4 in analysis.key_numbers_crossed

    def test_cfb_vs_nfl_edge(self, calculator):
        """Test CFB has different edge values than NFL."""
        nfl_analysis = calculator.calculate_edge_value(-2.5, -3.5, 'nfl')
        cfb_analysis = calculator.calculate_edge_value(-2.5, -3.5, 'cfb')

        # NFL crossing 3 should be worth more than CFB
        assert nfl_analysis.edge_percentage > cfb_analysis.edge_percentage

    def test_edge_recommendation_threshold(self, calculator):
        """Test recommendation at different edge levels."""
        # Big edge (crossing 3)
        big_edge = calculator.calculate_edge_value(-2.5, -3.5, 'nfl')
        assert 'BET' in big_edge.recommendation

        # Small edge (half point, no keys)
        small_edge = calculator.calculate_edge_value(-4.5, -4.0, 'nfl')
        assert 'NO BET' in small_edge.recommendation


class TestHalfPointValue:
    """Test half-point value calculations."""

    def test_half_point_at_three(self, calculator):
        """Test half-point value at key 3."""
        value = calculator.get_half_point_value(-3.0, 'nfl')
        assert value == 0.08  # Full key 3 value

    def test_half_point_at_seven(self, calculator):
        """Test half-point value at key 7."""
        value = calculator.get_half_point_value(-7.0, 'nfl')
        assert value == 0.06  # Full key 7 value

    def test_half_point_between_keys(self, calculator):
        """Test half-point value between key numbers."""
        value = calculator.get_half_point_value(-3.5, 'nfl')

        # Should be average of 3 and 4
        expected = (NFL_KEY_NUMBERS[3] + NFL_KEY_NUMBERS[4]) / 2
        assert value == pytest.approx(expected, abs=0.001)

    def test_half_point_non_key(self, calculator):
        """Test half-point value at non-key number."""
        value = calculator.get_half_point_value(-5.0, 'nfl')

        # Should be the value of key 5
        assert value == NFL_KEY_NUMBERS[5]


class TestBuyingHalfPoint:
    """Test buying half-point analysis."""

    def test_should_buy_at_three(self, calculator):
        """Test buying half-point at key 3 is profitable."""
        result = calculator.should_buy_half_point(
            current_line=-3.0,
            price_difference=10,  # Pay 10 cents (e.g., -110 to -120)
            sport='nfl'
        )

        # 8% value vs ~2% cost = profitable
        assert result['is_profitable']
        assert result['recommendation'] == 'BUY'

    def test_should_not_buy_expensive(self, calculator):
        """Test not buying half-point when too expensive."""
        result = calculator.should_buy_half_point(
            current_line=-3.0,
            price_difference=50,  # Pay 50 cents (very expensive)
            sport='nfl'
        )

        # 8% value vs ~10% cost = not profitable
        assert not result['is_profitable']

    def test_should_not_buy_non_key(self, calculator):
        """Test not buying at non-key numbers."""
        result = calculator.should_buy_half_point(
            current_line=-5.0,
            price_difference=20,
            sport='nfl'
        )

        # Low value at 5, high cost
        assert not result['is_profitable']


class TestBetTiming:
    """Test optimal bet timing strategy."""

    def test_bet_favorite_early(self, calculator):
        """Test 'bet favorites early' strategy."""
        # Your line favors home more than market (betting favorite)
        timing = calculator.get_optimal_bet_timing(
            your_line=-4.0,
            current_market_line=-3.0,
            sport='nfl'
        )

        assert timing['bet_side'] == 'favorite'
        assert 'NOW' in timing['timing'] or 'early' in timing['timing'].lower()

    def test_bet_dog_late(self, calculator):
        """Test 'bet dogs late' strategy."""
        # Your line favors away more than market (betting dog)
        timing = calculator.get_optimal_bet_timing(
            your_line=-2.0,
            current_market_line=-3.0,
            sport='nfl'
        )

        assert timing['bet_side'] == 'underdog'
        assert 'WAIT' in timing['timing'] or 'late' in timing['timing'].lower()

    def test_urgency_near_key_number(self, calculator):
        """Test urgency is higher near key numbers."""
        # Near key 3
        near_key = calculator.get_optimal_bet_timing(-2.5, -3.0, 'nfl')

        # Far from keys
        far_key = calculator.get_optimal_bet_timing(-4.5, -5.0, 'nfl')

        assert near_key['urgency'] == 'HIGH'
        assert near_key['distance_to_key'] <= 0.5

    def test_closest_key_number(self, calculator):
        """Test finding closest key number."""
        timing = calculator.get_optimal_bet_timing(-3.5, -3.0, 'nfl')

        assert timing['closest_key_number'] == 3


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_crossing_zero(self, calculator):
        """Test penalty for crossing zero (upset)."""
        # Your line +2 (away favored), market -2 (home favored)
        analysis = calculator.calculate_edge_value(2.0, -2.0, 'nfl')

        # Should have penalty for upset prediction
        assert analysis.edge_percentage < 8  # Less than just crossing 3

    def test_same_line(self, calculator):
        """Test no edge when lines match."""
        analysis = calculator.calculate_edge_value(-3.0, -3.0, 'nfl')

        assert analysis.edge_percentage == 0
        assert 'NO BET' in analysis.recommendation

    def test_half_point_difference(self, calculator):
        """Test minimal difference (half-point)."""
        analysis = calculator.calculate_edge_value(-3.0, -3.5, 'nfl')

        # Should be worth approximately the key 3 value
        assert 3 in analysis.key_numbers_crossed

    def test_large_spread_difference(self, calculator):
        """Test large spread difference."""
        analysis = calculator.calculate_edge_value(-10.0, -3.0, 'nfl')

        # Should cross multiple keys (3, 6, 7, 10)
        assert len(analysis.key_numbers_crossed) >= 4
        assert analysis.edge_percentage > 15  # Very large edge
