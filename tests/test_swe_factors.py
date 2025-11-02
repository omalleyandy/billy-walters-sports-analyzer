"""
Tests for S/W/E Factor System
"""

import pytest
from walters_analyzer.situational_factors import (
    SWEFactorCalculator,
    GameContext
)


@pytest.fixture
def calculator():
    """Create calculator instance."""
    return SWEFactorCalculator()


@pytest.fixture
def base_context():
    """Create base game context."""
    return GameContext(
        team="Alabama",
        opponent="LSU",
        sport="cfb",
        is_home=True,
        game_date="2024-11-09"
    )


class TestSFactors:
    """Test situational factors."""

    def test_rest_advantage(self, calculator, base_context):
        """Test rest advantage calculation."""
        base_context.team_rest_days = 10
        base_context.opponent_rest_days = 7

        result = calculator.calculate_s_factors(base_context)

        assert result['total_points'] > 0
        assert 'rest_advantage' in result['factors']

    def test_rest_disadvantage(self, calculator, base_context):
        """Test rest disadvantage calculation."""
        base_context.team_rest_days = 5
        base_context.opponent_rest_days = 9

        result = calculator.calculate_s_factors(base_context)

        assert result['total_points'] < 0

    def test_travel_fatigue(self, calculator, base_context):
        """Test travel fatigue for away team."""
        base_context.is_home = False
        base_context.travel_miles = 2500  # Cross-country

        result = calculator.calculate_s_factors(base_context)

        assert result['total_points'] < 0
        assert 'cross_country_travel' in result['factors']

    def test_no_travel_penalty_for_home(self, calculator, base_context):
        """Test home team doesn't get travel penalty."""
        base_context.is_home = True
        base_context.travel_miles = 2500

        result = calculator.calculate_s_factors(base_context)

        assert 'travel' not in str(result['factors']).lower()

    def test_divisional_game(self, calculator, base_context):
        """Test divisional game bonus."""
        base_context.is_divisional = True

        result = calculator.calculate_s_factors(base_context)

        assert result['total_points'] > 0
        assert 'divisional_game' in result['factors']

    def test_rivalry_game(self, calculator, base_context):
        """Test rivalry game bonus."""
        base_context.is_rivalry = True

        result = calculator.calculate_s_factors(base_context)

        # Rivalry worth more than divisional
        assert result['factors']['rivalry_game'] == 2

    def test_revenge_game(self, calculator, base_context):
        """Test revenge game motivation."""
        base_context.is_revenge = True

        result = calculator.calculate_s_factors(base_context)

        assert result['total_points'] > 0
        assert 'revenge_game' in result['factors']

    def test_ats_hot_streak(self, calculator, base_context):
        """Test ATS hot streak bonus."""
        base_context.team_ats_last_5 = 4  # 4-1 ATS

        result = calculator.calculate_s_factors(base_context)

        assert result['total_points'] > 0
        assert 'ats_hot_streak' in result['factors']

    def test_ats_cold_streak(self, calculator, base_context):
        """Test ATS cold streak penalty."""
        base_context.team_ats_last_5 = -4  # 1-4 ATS

        result = calculator.calculate_s_factors(base_context)

        assert result['total_points'] < 0

    def test_spread_adjustment_conversion(self, calculator, base_context):
        """Test 5 S-factor points = 1 spread point."""
        base_context.is_revenge = True  # 2 points
        base_context.is_rivalry = True  # 2 points
        base_context.team_ats_last_5 = 1  # 1 point (momentum)

        result = calculator.calculate_s_factors(base_context)

        # 5 total points should = 1.0 spread adjustment
        assert result['total_points'] == 5
        assert result['spread_adjustment'] == 1.0


class TestWFactors:
    """Test weather factors."""

    def test_dome_game_no_weather(self, calculator, base_context):
        """Test dome game ignores weather."""
        base_context.is_dome = True
        base_context.wind_speed_mph = 30
        base_context.precipitation_prob = 100

        result = calculator.calculate_w_factors(base_context)

        assert result['total_points'] == 0
        assert 'dome' in result['factors']

    def test_moderate_wind(self, calculator, base_context):
        """Test moderate wind impact."""
        base_context.wind_speed_mph = 18

        result = calculator.calculate_w_factors(base_context)

        assert result['total_points'] == 20
        assert 'wind_moderate' in result['factors']

    def test_high_wind(self, calculator, base_context):
        """Test high wind impact."""
        base_context.wind_speed_mph = 23

        result = calculator.calculate_w_factors(base_context)

        assert result['total_points'] == 30
        assert 'wind_high' in result['factors']

    def test_extreme_wind(self, calculator, base_context):
        """Test extreme wind impact."""
        base_context.wind_speed_mph = 28

        result = calculator.calculate_w_factors(base_context)

        assert result['total_points'] == 40
        assert 'wind_extreme' in result['factors']

    def test_snow(self, calculator, base_context):
        """Test snow impact."""
        base_context.precipitation_prob = 80
        base_context.precipitation_type = 'snow'

        result = calculator.calculate_w_factors(base_context)

        assert result['total_points'] >= 35
        assert 'snow' in result['factors']

    def test_heavy_rain(self, calculator, base_context):
        """Test heavy rain impact."""
        base_context.precipitation_prob = 80
        base_context.precipitation_type = 'rain'

        result = calculator.calculate_w_factors(base_context)

        assert result['total_points'] >= 25
        assert 'heavy_rain' in result['factors']

    def test_extreme_cold(self, calculator, base_context):
        """Test extreme cold impact."""
        base_context.temperature_f = 15

        result = calculator.calculate_w_factors(base_context)

        assert 'extreme_cold' in result['factors']

    def test_freezing_temp(self, calculator, base_context):
        """Test freezing temperature impact."""
        base_context.temperature_f = 30

        result = calculator.calculate_w_factors(base_context)

        assert 'freezing' in result['factors']

    def test_total_adjustment(self, calculator, base_context):
        """Test weather reduces total points."""
        base_context.wind_speed_mph = 25
        base_context.precipitation_prob = 80
        base_context.precipitation_type = 'snow'

        result = calculator.calculate_w_factors(base_context)

        # Severe conditions should reduce total
        assert result['total_adjustment'] < 0


class TestEFactors:
    """Test emotional factors."""

    def test_playoff_elimination(self, calculator, base_context):
        """Test playoff elimination motivation."""
        base_context.playoff_implications = 'elimination'

        result = calculator.calculate_e_factors(base_context)

        assert result['total_points'] == 5
        assert 'playoff_elimination' in result['factors']

    def test_playoff_clinch(self, calculator, base_context):
        """Test playoff clinch motivation."""
        base_context.playoff_implications = 'clinch'

        result = calculator.calculate_e_factors(base_context)

        assert result['total_points'] == 3
        assert 'playoff_clinch' in result['factors']

    def test_playoff_seeding(self, calculator, base_context):
        """Test playoff seeding motivation."""
        base_context.playoff_implications = 'seeding'

        result = calculator.calculate_e_factors(base_context)

        assert result['total_points'] == 2

    def test_new_coach(self, calculator, base_context):
        """Test new coach motivation."""
        base_context.coaching_change = True

        result = calculator.calculate_e_factors(base_context)

        assert result['total_points'] > 0
        assert 'new_coach' in result['factors']

    def test_injury_motivation(self, calculator, base_context):
        """Test injury emotional impact."""
        base_context.injury_motivation = True

        result = calculator.calculate_e_factors(base_context)

        assert result['total_points'] > 0

    def test_e_factor_spread_conversion(self, calculator, base_context):
        """Test E-factors use 5:1 ratio like S-factors."""
        base_context.playoff_implications = 'elimination'  # 5 points

        result = calculator.calculate_e_factors(base_context)

        assert result['spread_adjustment'] == 1.0  # 5 points = 1 spread point


class TestAllFactors:
    """Test combined S/W/E analysis."""

    def test_all_factors_combined(self, calculator, base_context):
        """Test all factors work together."""
        # Set up strong situational + emotional
        base_context.is_revenge = True  # 2 S-points
        base_context.playoff_implications = 'elimination'  # 5 E-points
        base_context.wind_speed_mph = 22  # Weather

        result = calculator.calculate_all_factors(base_context)

        # S + E should combine
        total_spread_adj = result['total_spread_adjustment']
        assert total_spread_adj == pytest.approx(1.4, abs=0.1)  # 7 points / 5

        # Should have summary
        assert len(result['summary']) > 0

    def test_summary_generation(self, calculator, base_context):
        """Test summary is human-readable."""
        base_context.is_rivalry = True
        base_context.wind_speed_mph = 20

        result = calculator.calculate_all_factors(base_context)

        summary = result['summary']
        assert 'S-factors' in summary or 'Weather' in summary
