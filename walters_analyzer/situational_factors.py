"""
Billy Walters S/W/E Factor System

S = Situational Factors (rest, travel, divisional, revenge, trends)
W = Weather Factors (wind, precipitation, temperature)
E = Emotional Factors (motivation, playoff implications, coaching)

Billy Walters Rule: 5 S-factor points = 1 point spread point
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class GameContext:
    """
    Context information for a game needed to calculate S/W/E factors.
    """
    # Team identifiers
    team: str
    opponent: str
    sport: str
    is_home: bool
    game_date: str

    # Situational factors
    team_rest_days: int = 7  # Days since last game
    opponent_rest_days: int = 7
    travel_miles: int = 0  # Travel distance for away team
    is_divisional: bool = False
    is_conference: bool = False
    is_rivalry: bool = False
    is_revenge: bool = False  # Lost to this opponent recently
    team_ats_last_5: int = 0  # ATS record last 5 games (-5 to +5)
    opponent_ats_last_5: int = 0

    # Weather factors (if applicable)
    wind_speed_mph: float = 0.0
    precipitation_prob: float = 0.0
    precipitation_type: Optional[str] = None  # 'rain', 'snow', None
    temperature_f: float = 70.0
    is_dome: bool = False

    # Emotional factors
    playoff_implications: str = "none"  # 'none', 'elimination', 'clinch', 'seeding'
    coaching_change: bool = False  # New coach this season
    injury_motivation: bool = False  # Star player returning/out (emotional impact)
    public_betting_pct: Optional[float] = None  # % of public on this team


class SWEFactorCalculator:
    """
    Calculate S/W/E factors per Billy Walters methodology.

    Returns point values that translate to spread adjustments:
    - 5 S-factor points = 1 point spread adjustment
    - Weather points directly reduce totals, impact spreads minimally
    - E-factor points add to S-factor points (same 5:1 ratio)
    """

    # S-Factor point values (Billy Walters guidelines)
    S_FACTOR_VALUES = {
        'rest_advantage_1day': 1,      # 1 extra day rest
        'rest_advantage_2day': 2,      # 2+ extra days rest
        'rest_advantage_3day': 3,      # 3+ extra days rest (significant)
        'long_travel': 1,              # 1000+ mile travel
        'very_long_travel': 2,         # 2000+ mile travel
        'cross_country': 3,            # Coast-to-coast (3+ time zones)
        'divisional_game': 1,          # Familiarity, intensity
        'conference_game': 1,          # Conference pride
        'rivalry_game': 2,             # Historic rivalry
        'revenge_game': 2,             # Lost to opponent recently
        'ats_hot_streak': 2,           # 4-1 or 5-0 ATS last 5
        'ats_cold_streak': -2,         # 0-5 or 1-4 ATS last 5
        'ats_momentum': 1,             # 3-2 ATS last 5
    }

    # E-Factor point values (Billy Walters guidelines)
    E_FACTOR_VALUES = {
        'playoff_elimination': 5,       # Must-win game
        'playoff_clinch': 3,           # Can clinch playoff spot
        'playoff_seeding': 2,          # Seeding implications
        'new_coach_motivation': 2,     # New coach, first season energy
        'star_return': 1,              # Star player returning (emotional lift)
        'star_loss_motivation': 1,     # Rally around injured star
    }

    # Weather thresholds (from weather_fetcher.py, Billy Walters methodology)
    WEATHER_THRESHOLDS = {
        'wind_moderate': 15,    # mph
        'wind_high': 20,
        'wind_extreme': 25,
        'precip_significant': 50,  # % probability
        'temp_freezing': 32,    # Fahrenheit
        'temp_extreme_cold': 20,
    }

    def calculate_s_factors(self, context: GameContext) -> dict:
        """
        Calculate situational factors.

        Args:
            context: GameContext with all necessary data

        Returns:
            Dict with total points and breakdown
        """
        factors = {}
        total_points = 0

        # Rest advantage/disadvantage
        rest_diff = context.team_rest_days - context.opponent_rest_days
        if rest_diff >= 3:
            factors['rest_advantage'] = self.S_FACTOR_VALUES['rest_advantage_3day']
            total_points += factors['rest_advantage']
        elif rest_diff == 2:
            factors['rest_advantage'] = self.S_FACTOR_VALUES['rest_advantage_2day']
            total_points += factors['rest_advantage']
        elif rest_diff == 1:
            factors['rest_advantage'] = self.S_FACTOR_VALUES['rest_advantage_1day']
            total_points += factors['rest_advantage']
        elif rest_diff <= -3:
            factors['rest_disadvantage'] = -self.S_FACTOR_VALUES['rest_advantage_3day']
            total_points += factors['rest_disadvantage']
        elif rest_diff == -2:
            factors['rest_disadvantage'] = -self.S_FACTOR_VALUES['rest_advantage_2day']
            total_points += factors['rest_disadvantage']
        elif rest_diff == -1:
            factors['rest_disadvantage'] = -self.S_FACTOR_VALUES['rest_advantage_1day']
            total_points += factors['rest_disadvantage']

        # Travel fatigue (only for away team)
        if not context.is_home:
            if context.travel_miles >= 2500:  # Cross-country
                factors['cross_country_travel'] = -self.S_FACTOR_VALUES['cross_country']
                total_points += factors['cross_country_travel']
            elif context.travel_miles >= 2000:
                factors['very_long_travel'] = -self.S_FACTOR_VALUES['very_long_travel']
                total_points += factors['very_long_travel']
            elif context.travel_miles >= 1000:
                factors['long_travel'] = -self.S_FACTOR_VALUES['long_travel']
                total_points += factors['long_travel']

        # Game importance (divisional, conference, rivalry)
        if context.is_rivalry:
            factors['rivalry_game'] = self.S_FACTOR_VALUES['rivalry_game']
            total_points += factors['rivalry_game']
        elif context.is_divisional:
            factors['divisional_game'] = self.S_FACTOR_VALUES['divisional_game']
            total_points += factors['divisional_game']
        elif context.is_conference:
            factors['conference_game'] = self.S_FACTOR_VALUES['conference_game']
            total_points += factors['conference_game']

        # Revenge game
        if context.is_revenge:
            factors['revenge_game'] = self.S_FACTOR_VALUES['revenge_game']
            total_points += factors['revenge_game']

        # ATS trends (momentum indicator)
        if context.team_ats_last_5 >= 4:  # 4-1 or 5-0
            factors['ats_hot_streak'] = self.S_FACTOR_VALUES['ats_hot_streak']
            total_points += factors['ats_hot_streak']
        elif context.team_ats_last_5 <= -4:  # 0-5 or 1-4
            factors['ats_cold_streak'] = self.S_FACTOR_VALUES['ats_cold_streak']
            total_points += factors['ats_cold_streak']
        elif context.team_ats_last_5 >= 1:  # 3-2
            factors['ats_momentum'] = self.S_FACTOR_VALUES['ats_momentum']
            total_points += factors['ats_momentum']

        return {
            'total_points': total_points,
            'spread_adjustment': round(total_points / 5, 1),  # 5 points = 1 spread point
            'factors': factors
        }

    def calculate_w_factors(self, context: GameContext) -> dict:
        """
        Calculate weather factors.

        Args:
            context: GameContext with weather data

        Returns:
            Dict with impact score and adjustments
        """
        if context.is_dome:
            return {
                'total_points': 0,
                'total_adjustment': 0.0,
                'spread_adjustment': 0.0,
                'factors': {'dome': 'Weather irrelevant (dome)'}
            }

        factors = {}
        impact_score = 0

        # Wind (Billy Walters thresholds from masterclass)
        if context.wind_speed_mph >= self.WEATHER_THRESHOLDS['wind_extreme']:
            factors['wind_extreme'] = 40
            impact_score += 40
        elif context.wind_speed_mph >= self.WEATHER_THRESHOLDS['wind_high']:
            factors['wind_high'] = 30
            impact_score += 30
        elif context.wind_speed_mph >= self.WEATHER_THRESHOLDS['wind_moderate']:
            factors['wind_moderate'] = 20
            impact_score += 20

        # Precipitation
        if context.precipitation_prob >= self.WEATHER_THRESHOLDS['precip_significant']:
            if context.precipitation_type == 'snow':
                factors['snow'] = 35
                impact_score += 35
            elif context.precipitation_type == 'rain':
                factors['heavy_rain'] = 25
                impact_score += 25

        # Temperature
        if context.temperature_f <= self.WEATHER_THRESHOLDS['temp_extreme_cold']:
            factors['extreme_cold'] = 20
            impact_score += 20
        elif context.temperature_f <= self.WEATHER_THRESHOLDS['temp_freezing']:
            factors['freezing'] = 15
            impact_score += 15

        # Weather primarily impacts totals, minimally impacts spreads
        # Billy Walters: severe weather = 3-7 point total reduction
        total_adjustment = 0.0
        if impact_score >= 80:
            total_adjustment = -7.0  # Extreme conditions
        elif impact_score >= 60:
            total_adjustment = -5.0  # Severe conditions
        elif impact_score >= 40:
            total_adjustment = -3.0  # Moderate conditions

        # Spread adjustment is minimal (weather affects both teams)
        # Only adjust if one team is significantly more impacted
        spread_adjustment = 0.0

        return {
            'total_points': impact_score,
            'total_adjustment': total_adjustment,
            'spread_adjustment': spread_adjustment,
            'factors': factors
        }

    def calculate_e_factors(self, context: GameContext) -> dict:
        """
        Calculate emotional/motivational factors.

        Args:
            context: GameContext with emotional data

        Returns:
            Dict with total points and breakdown
        """
        factors = {}
        total_points = 0

        # Playoff implications (huge motivator)
        if context.playoff_implications == 'elimination':
            factors['playoff_elimination'] = self.E_FACTOR_VALUES['playoff_elimination']
            total_points += factors['playoff_elimination']
        elif context.playoff_implications == 'clinch':
            factors['playoff_clinch'] = self.E_FACTOR_VALUES['playoff_clinch']
            total_points += factors['playoff_clinch']
        elif context.playoff_implications == 'seeding':
            factors['playoff_seeding'] = self.E_FACTOR_VALUES['playoff_seeding']
            total_points += factors['playoff_seeding']

        # New coach motivation
        if context.coaching_change:
            factors['new_coach'] = self.E_FACTOR_VALUES['new_coach_motivation']
            total_points += factors['new_coach']

        # Injury emotional impact
        if context.injury_motivation:
            # This could be star return OR rallying around injured star
            # Context determines which
            factors['injury_motivation'] = self.E_FACTOR_VALUES['star_return']
            total_points += factors['injury_motivation']

        return {
            'total_points': total_points,
            'spread_adjustment': round(total_points / 5, 1),  # Same 5:1 ratio as S-factors
            'factors': factors
        }

    def calculate_all_factors(self, context: GameContext) -> dict:
        """
        Calculate all S/W/E factors for a game.

        Args:
            context: GameContext with all data

        Returns:
            Comprehensive dict with all factors and adjustments
        """
        s_factors = self.calculate_s_factors(context)
        w_factors = self.calculate_w_factors(context)
        e_factors = self.calculate_e_factors(context)

        # Total spread adjustment (S + E factors, W minimal)
        total_spread_adjustment = (
            s_factors['spread_adjustment'] +
            e_factors['spread_adjustment'] +
            w_factors['spread_adjustment']
        )

        # Total adjustment (for totals)
        total_adjustment = w_factors['total_adjustment']

        return {
            's_factors': s_factors,
            'w_factors': w_factors,
            'e_factors': e_factors,
            'total_spread_adjustment': round(total_spread_adjustment, 1),
            'total_adjustment': round(total_adjustment, 1),
            'summary': self._generate_summary(s_factors, w_factors, e_factors)
        }

    def _generate_summary(self, s_factors: dict, w_factors: dict, e_factors: dict) -> str:
        """Generate human-readable summary of factors."""
        summary_parts = []

        # S-factors
        if s_factors['total_points'] != 0:
            summary_parts.append(
                f"S-factors: {s_factors['total_points']} pts "
                f"({s_factors['spread_adjustment']:+.1f} spread)"
            )

        # W-factors
        if w_factors['total_points'] > 0:
            summary_parts.append(
                f"Weather: {w_factors['total_points']} impact "
                f"({w_factors['total_adjustment']:+.1f} total)"
            )

        # E-factors
        if e_factors['total_points'] != 0:
            summary_parts.append(
                f"E-factors: {e_factors['total_points']} pts "
                f"({e_factors['spread_adjustment']:+.1f} spread)"
            )

        return " | ".join(summary_parts) if summary_parts else "No significant factors"


# Convenience functions

def calculate_factors(context: GameContext) -> dict:
    """Quick calculation of all S/W/E factors."""
    calculator = SWEFactorCalculator()
    return calculator.calculate_all_factors(context)


def get_spread_adjustment(context: GameContext) -> float:
    """Get total spread adjustment from all factors."""
    calculator = SWEFactorCalculator()
    result = calculator.calculate_all_factors(context)
    return result['total_spread_adjustment']


def get_total_adjustment(context: GameContext) -> float:
    """Get total points adjustment from weather."""
    calculator = SWEFactorCalculator()
    result = calculator.calculate_all_factors(context)
    return result['total_adjustment']
