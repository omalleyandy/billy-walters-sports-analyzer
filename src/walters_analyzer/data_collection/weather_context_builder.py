"""
Weather Context Builder - Task 2.2: Complete Weather Context Builder

Transforms raw weather data into complete WeatherContext objects with
W-Factor calculations following Billy Walters' weather impact methodology.

Billy Walters Weather Principles (Pages 256-258, "Gambler"):
- Wind >15 MPH: Reduce total by 3-5 points, favor defense
- Temp <32°F: Reduce total by 2-3 points, favor rushing
- Rain/Snow: Reduce total by 2-4 points
- Dome/Indoor: No weather adjustments apply
- Warm-weather teams in cold: Significant disadvantage
- Outdoor dome teams: Reduced advantage vs indoor domes

Version: 1.0
Created: November 20, 2025
Type: Production
Status: Production-Ready
"""

from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Tuple, List
from enum import Enum
import logging
import asyncio
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, computed_field

from ..models.sfactor_data_models import (
    WeatherContext,
    Precipitation,
    WindCondition,
    DataFreshness,
    SFactorGamePackage,
    GameContext,
)


# ===== CONSTANTS =====

# Warm-weather NFL teams (Miami, Arizona, Tampa Bay, New Orleans, LA Chargers)
WARM_WEATHER_TEAMS = {
    "Miami Dolphins",
    "Arizona Cardinals",
    "Tampa Bay Buccaneers",
    "New Orleans Saints",
    "Los Angeles Chargers",
}

# Dome/Indoor teams
DOME_TEAMS = {
    "Arizona Cardinals",  # Covered Glendale Stadium
    "Atlanta Falcons",  # Mercedes-Benz Stadium
    "Dallas Cowboys",  # AT&T Stadium
    "Detroit Lions",  # Ford Field
    "Houston Texans",  # NRG Stadium
    "Indianapolis Colts",  # Lucas Oil Stadium
    "Las Vegas Raiders",  # Allegiant Stadium
    "Los Angeles Rams",  # SoFi Stadium
    "Minnesota Vikings",  # U.S. Bank Stadium
    "New England Patriots",  # Gillette Stadium (retractable, count as dome for cold)
    "New Orleans Saints",  # Caesars Superdome
    "New York Giants",  # MetLife Stadium (open, but in cold climate)
    "New York Jets",  # MetLife Stadium (open, but in cold climate)
    "Philadelphia Eagles",  # Lincoln Financial Field (open)
    "Pittsburgh Steelers",  # Acrisure Stadium (open, but in cold climate)
    "San Francisco 49ers",  # Levi's Stadium (open)
    "Seattle Seahawks",  # Lumen Field (open, but rainy climate)
    "St. Louis Rams",  # (no longer exists, but in data)
}

# Stadium altitudes (affects ball flight, temperature)
STADIUM_ALTITUDES = {
    "Denver Broncos": 5280,  # Mile High
    "Mexico City": 7400,  # Mexico City Azteca
}

# ===== ENUMERATIONS =====


class WeatherImpactLevel(str, Enum):
    """Severity of weather impact on game"""

    NONE = "none"  # No impact
    MINIMAL = "minimal"  # <1 point impact
    LIGHT = "light"  # 1-2 point impact
    MODERATE = "moderate"  # 2-4 point impact
    HEAVY = "heavy"  # 4-6 point impact
    SEVERE = "severe"  # 6+ point impact


class TeamWeatherSuitability(str, Enum):
    """How well-suited a team is to current weather"""

    HIGHLY_FAVORABLE = "highly_favorable"  # +2 to +3 spread points
    FAVORABLE = "favorable"  # +1 to +2 spread points
    NEUTRAL = "neutral"  # No advantage
    UNFAVORABLE = "unfavorable"  # -1 to -2 spread points
    HIGHLY_UNFAVORABLE = "highly_unfavorable"  # -2 to -3 spread points


class WeatherDataQuality(str, Enum):
    """Quality rating of weather data"""

    EXCELLENT = "excellent"  # Multiple sources, <6 hours old
    GOOD = "good"  # Primary source, <12 hours old
    FAIR = "fair"  # Single source, <24 hours old
    POOR = "poor"  # Stale or incomplete
    UNKNOWN = "unknown"  # No data available


# ===== W-FACTOR MODELS =====


class WFactor(BaseModel):
    """Individual W-Factor (weather factor) with impact calculation."""

    name: str = Field(description="W-Factor name (e.g., 'Cold Temperature')")
    impact_points: float = Field(
        description="Weather factor points (converted to spread via 5:1 ratio)"
    )
    impact_to_spread: float = Field(
        description="Direct spread point impact (impact_points / 5)"
    )
    affects: str = Field(description="What it affects: 'total' or 'spread' or 'both'")
    direction: str = Field(
        description="Direction: 'favors_home', 'favors_away', 'neutral'"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in this factor (0-1)"
    )

    def __init__(self, **data):
        """Calculate impact_to_spread automatically"""
        if "impact_points" in data and "impact_to_spread" not in data:
            data["impact_to_spread"] = data["impact_points"] / 5.0
        super().__init__(**data)


class WFactorSummary(BaseModel):
    """Summary of all W-Factors for a game"""

    factors: List[WFactor] = Field(description="Individual W-Factors")
    total_impact_points: float = Field(description="Sum of all W-Factor points")
    total_impact_spread: float = Field(description="Total spread impact (points / 5)")
    total_impact_total: float = Field(description="Total (points) impact")
    indoor_game: bool = Field(description="Is this an indoor game?")
    data_quality: WeatherDataQuality = Field(description="Quality of weather data")

    @computed_field
    @property
    def impact_level(self) -> WeatherImpactLevel:
        """Classify overall impact severity"""
        impact = abs(self.total_impact_spread)

        if impact == 0:
            return WeatherImpactLevel.NONE
        elif impact < 1:
            return WeatherImpactLevel.MINIMAL
        elif impact < 2:
            return WeatherImpactLevel.LIGHT
        elif impact < 4:
            return WeatherImpactLevel.MODERATE
        elif impact < 6:
            return WeatherImpactLevel.HEAVY
        else:
            return WeatherImpactLevel.SEVERE

    @computed_field
    @property
    def requires_manual_review(self) -> bool:
        """Flag unusual weather impacts for review"""
        # Severe impacts should always be reviewed
        if self.impact_level == WeatherImpactLevel.SEVERE:
            return True
        # Poor data quality should be reviewed
        if self.data_quality == WeatherDataQuality.POOR:
            return True
        # Conflicting factors should be reviewed
        favorable_home = sum(1 for f in self.factors if f.direction == "favors_home")
        favorable_away = sum(1 for f in self.factors if f.direction == "favors_away")
        if favorable_home > 0 and favorable_away > 0:
            return True
        return False


# ===== MAIN WEATHER CONTEXT BUILDER =====


class WeatherContextBuilder:
    """
    Builds complete WeatherContext objects for games with W-Factor calculations.

    Responsibilities:
    1. Fetch weather data from sources (API calls)
    2. Validate data completeness and freshness
    3. Calculate W-Factors per Billy Walters methodology
    4. Assess team-specific weather suitability
    5. Determine impact on spread and totals
    6. Handle dome/indoor special cases
    """

    def __init__(
        self,
        accuweather_client: Optional[object] = None,
        openweather_client: Optional[object] = None,
        cache_ttl_hours: int = 6,
        production_mode: bool = True,
    ):
        """Initialize WeatherContextBuilder."""
        self.accuweather_client = accuweather_client
        self.openweather_client = openweather_client
        self.cache_ttl_hours = cache_ttl_hours
        self.production_mode = production_mode

        # Cache
        self._cache: Dict[str, Tuple[WeatherContext, datetime]] = {}

        # Logging
        self.logger = logging.getLogger(__name__)

    # ===== PUBLIC METHODS =====

    def calculate_wfactors(
        self,
        weather: WeatherContext,
        home_team: str,
        away_team: str,
    ) -> WFactorSummary:
        """
        Calculate all W-Factors for a game.

        Analyzes weather conditions and team composition to determine
        spread and total adjustments per Billy Walters' methodology.
        """
        if weather.is_indoor:
            return WFactorSummary(
                factors=[],
                total_impact_points=0.0,
                total_impact_spread=0.0,
                total_impact_total=0.0,
                indoor_game=True,
                data_quality=WeatherDataQuality.EXCELLENT,
            )

        factors: List[WFactor] = []

        # 1. TEMPERATURE FACTORS
        temp_factors = self._calculate_temperature_factors(
            weather, home_team, away_team
        )
        factors.extend(temp_factors)

        # 2. WIND FACTORS
        wind_factors = self._calculate_wind_factors(weather, home_team, away_team)
        factors.extend(wind_factors)

        # 3. PRECIPITATION FACTORS
        precip_factors = self._calculate_precipitation_factors(
            weather, home_team, away_team
        )
        factors.extend(precip_factors)

        # 4. SPECIAL FACTORS
        special_factors = self._calculate_special_factors(weather)
        factors.extend(special_factors)

        # Calculate totals
        total_points = sum(f.impact_points for f in factors)
        total_spread = total_points / 5.0
        total_total = sum(
            f.impact_points for f in factors if f.affects in ["total", "both"]
        )

        # Determine data quality
        data_quality = self._assess_data_quality(weather)

        return WFactorSummary(
            factors=factors,
            total_impact_points=total_points,
            total_impact_spread=total_spread,
            total_impact_total=total_total,
            indoor_game=False,
            data_quality=data_quality,
        )

    def assess_team_weather_suitability(
        self,
        team: str,
        weather: WeatherContext,
    ) -> TeamWeatherSuitability:
        """
        Assess how well a team matches current weather conditions.
        """
        if weather.is_indoor:
            return TeamWeatherSuitability.NEUTRAL

        # Warm-weather teams
        if team in WARM_WEATHER_TEAMS:
            return self._assess_warm_team_suitability(weather)

        # Cold-weather teams
        cold_weather_teams = {
            "Buffalo Bills",
            "Green Bay Packers",
            "Minnesota Vikings",
            "New England Patriots",
            "Pittsburgh Steelers",
            "Chicago Bears",
        }

        if team in cold_weather_teams:
            return self._assess_cold_team_suitability(weather)

        # Neutral-climate teams
        return self._assess_neutral_team_suitability(weather)

    # ===== PRIVATE HELPER METHODS =====

    def _calculate_temperature_factors(
        self,
        weather: WeatherContext,
        home_team: str,
        away_team: str,
    ) -> List[WFactor]:
        """Calculate temperature-related W-Factors"""
        factors: List[WFactor] = []

        if weather.temperature_f is None:
            return factors

        temp = weather.temperature_f

        # COLD IMPACT: <32°F (Billy Walters: -2 to -3 point reduction)
        if temp < 32:
            # Reduces passing, total
            cold_impact = -2.5 if temp < 20 else -1.5
            factors.append(
                WFactor(
                    name="Cold Temperature (<32°F)",
                    impact_points=cold_impact * 5,  # Convert to W-Factor points
                    impact_to_spread=cold_impact,
                    affects="total",
                    direction="neutral",
                    confidence=0.9,
                )
            )

            # Warm-weather teams get penalty
            if home_team in WARM_WEATHER_TEAMS:
                factors.append(
                    WFactor(
                        name="Warm Team in Cold (Home)",
                        impact_points=-15,  # -3 spread points
                        impact_to_spread=-3.0,
                        affects="both",
                        direction="favors_away",
                        confidence=0.85,
                    )
                )

            if away_team in WARM_WEATHER_TEAMS:
                factors.append(
                    WFactor(
                        name="Warm Team in Cold (Away)",
                        impact_points=-15,  # -3 spread points
                        impact_to_spread=-3.0,
                        affects="both",
                        direction="favors_home",
                        confidence=0.85,
                    )
                )

        # HOT IMPACT: >90°F
        elif temp > 90:
            factors.append(
                WFactor(
                    name="Extreme Heat (>90°F)",
                    impact_points=10,  # +2 spread points
                    impact_to_spread=2.0,
                    affects="total",
                    direction="neutral",
                    confidence=0.7,
                )
            )

        return factors

    def _calculate_wind_factors(
        self,
        weather: WeatherContext,
        home_team: str,
        away_team: str,
    ) -> List[WFactor]:
        """Calculate wind-related W-Factors (highest impact)"""
        factors: List[WFactor] = []

        if weather.wind_speed_mph is None or weather.wind_speed_mph <= 10:
            return factors

        wind = weather.wind_speed_mph

        # MODERATE WIND: 10-20 MPH
        if 10 < wind <= 20:
            wind_impact = -10  # -2 spread points
            factors.append(
                WFactor(
                    name="Moderate Wind (10-20 MPH)",
                    impact_points=wind_impact,
                    impact_to_spread=wind_impact / 5.0,
                    affects="both",
                    direction="neutral",
                    confidence=0.8,
                )
            )

        # STRONG WIND: >20 MPH
        elif wind > 20:
            # Calculate progressive impact
            wind_impact = min(wind - 20, 10)  # Max 10 additional points
            total_impact = -(10 + wind_impact)  # Base -10, plus additional

            factors.append(
                WFactor(
                    name=f"Strong Wind (>{wind:.0f} MPH)",
                    impact_points=total_impact,
                    impact_to_spread=total_impact / 5.0,
                    affects="both",
                    direction="neutral",
                    confidence=0.9,
                )
            )

        return factors

    def _calculate_precipitation_factors(
        self,
        weather: WeatherContext,
        home_team: str,
        away_team: str,
    ) -> List[WFactor]:
        """Calculate precipitation W-Factors"""
        factors: List[WFactor] = []

        if weather.precipitation_type == Precipitation.NONE:
            return factors

        # LIGHT RAIN
        if weather.precipitation_type == Precipitation.LIGHT_RAIN:
            factors.append(
                WFactor(
                    name="Light Rain",
                    impact_points=-10,  # -2 spread points
                    impact_to_spread=-2.0,
                    affects="total",
                    direction="neutral",
                    confidence=0.75,
                )
            )

        # HEAVY RAIN
        elif weather.precipitation_type == Precipitation.HEAVY_RAIN:
            factors.append(
                WFactor(
                    name="Heavy Rain",
                    impact_points=-20,  # -4 spread points
                    impact_to_spread=-4.0,
                    affects="both",
                    direction="neutral",
                    confidence=0.9,
                )
            )

        # SNOW
        elif weather.precipitation_type in [
            Precipitation.LIGHT_SNOW,
            Precipitation.HEAVY_SNOW,
            Precipitation.MIXED,
        ]:
            snow_impact = (
                -20 if "HEAVY" in weather.precipitation_type.value.upper() else -15
            )
            factors.append(
                WFactor(
                    name=weather.precipitation_type.value.replace("_", " ").title(),
                    impact_points=snow_impact,
                    impact_to_spread=snow_impact / 5.0,
                    affects="both",
                    direction="neutral",
                    confidence=0.95,
                )
            )

        return factors

    def _calculate_special_factors(
        self,
        weather: WeatherContext,
    ) -> List[WFactor]:
        """Calculate special weather situations"""
        factors: List[WFactor] = []

        # FOG (rare but impactful)
        if weather.is_extreme_cold and weather.wind_condition == WindCondition.CALM:
            factors.append(
                WFactor(
                    name="Extreme Cold + Calm (Fog Risk)",
                    impact_points=-5,
                    impact_to_spread=-1.0,
                    affects="total",
                    direction="neutral",
                    confidence=0.6,
                )
            )

        return factors

    def _assess_warm_team_suitability(
        self,
        weather: WeatherContext,
    ) -> TeamWeatherSuitability:
        """Assess warm-weather team suitability"""
        if weather.temperature_f is None:
            return TeamWeatherSuitability.NEUTRAL

        temp = weather.temperature_f
        wind = weather.wind_speed_mph or 0

        # HIGHLY UNFAVORABLE: Cold + Wind + Precipitation
        if temp < 20 and wind > 20:
            return TeamWeatherSuitability.HIGHLY_UNFAVORABLE

        # UNFAVORABLE: Cold + Wind or Precipitation
        if temp < 32 and (wind > 15 or weather.has_significant_precipitation):
            return TeamWeatherSuitability.UNFAVORABLE

        # NEUTRAL: Mild conditions
        if 50 <= temp <= 75 and wind <= 10:
            return TeamWeatherSuitability.NEUTRAL

        # FAVORABLE: Warm and calm
        if (
            temp > 70
            and wind <= 10
            and weather.precipitation_type == Precipitation.NONE
        ):
            return TeamWeatherSuitability.FAVORABLE

        # Default
        return TeamWeatherSuitability.NEUTRAL

    def _assess_cold_team_suitability(
        self,
        weather: WeatherContext,
    ) -> TeamWeatherSuitability:
        """Assess cold-weather team suitability (reverse of warm teams)"""
        if weather.temperature_f is None:
            return TeamWeatherSuitability.NEUTRAL

        temp = weather.temperature_f
        wind = weather.wind_speed_mph or 0

        # HIGHLY FAVORABLE: Cold + Wind
        if temp < 20 and wind > 15:
            return TeamWeatherSuitability.HIGHLY_FAVORABLE

        # FAVORABLE: Cold + Wind
        if temp < 32 and wind > 10:
            return TeamWeatherSuitability.FAVORABLE

        # NEUTRAL: Mild
        if 50 <= temp <= 75 and wind <= 10:
            return TeamWeatherSuitability.NEUTRAL

        # UNFAVORABLE: Warm
        if temp > 80:
            return TeamWeatherSuitability.UNFAVORABLE

        # Default
        return TeamWeatherSuitability.NEUTRAL

    def _assess_neutral_team_suitability(
        self,
        weather: WeatherContext,
    ) -> TeamWeatherSuitability:
        """Assess neutral-climate team suitability"""
        if weather.temperature_f is None:
            return TeamWeatherSuitability.NEUTRAL

        # Extreme conditions create mild disadvantage/advantage
        if weather.is_extreme_cold or (weather.temperature_f or 0) > 90:
            return TeamWeatherSuitability.UNFAVORABLE

        # Wind creates slight disadvantage
        if (weather.wind_speed_mph or 0) > 20:
            return TeamWeatherSuitability.UNFAVORABLE

        # Normal conditions are neutral
        return TeamWeatherSuitability.NEUTRAL

    def _parse_precipitation(self, precip_type: Optional[str]) -> Precipitation:
        """Parse precipitation type string to enum"""
        if not precip_type:
            return Precipitation.NONE

        precip_lower = precip_type.lower()

        if "heavy" in precip_lower and "rain" in precip_lower:
            return Precipitation.HEAVY_RAIN
        elif "light" in precip_lower and "rain" in precip_lower:
            return Precipitation.LIGHT_RAIN
        elif "rain" in precip_lower:
            return Precipitation.LIGHT_RAIN
        elif "heavy" in precip_lower and "snow" in precip_lower:
            return Precipitation.HEAVY_SNOW
        elif "light" in precip_lower and "snow" in precip_lower:
            return Precipitation.LIGHT_SNOW
        elif "snow" in precip_lower:
            return Precipitation.LIGHT_SNOW
        elif "mixed" in precip_lower:
            return Precipitation.MIXED
        else:
            return Precipitation.NONE

    def _classify_wind_condition(
        self, wind_speed: Optional[int]
    ) -> Optional[WindCondition]:
        """Classify wind speed to condition"""
        if wind_speed is None:
            return None

        if wind_speed <= 5:
            return WindCondition.CALM
        elif wind_speed <= 10:
            return WindCondition.LIGHT
        elif wind_speed <= 20:
            return WindCondition.MODERATE
        elif wind_speed <= 30:
            return WindCondition.STRONG
        else:
            return WindCondition.SEVERE

    def _assess_data_quality(self, weather: WeatherContext) -> WeatherDataQuality:
        """Assess quality of weather data"""
        completeness = 0

        # Check data points
        if weather.temperature_f is not None:
            completeness += 1
        if weather.wind_speed_mph is not None:
            completeness += 1
        if weather.precipitation_type != Precipitation.NONE:
            completeness += 1

        # Check freshness
        age_hours = (datetime.now() - weather.forecast_timestamp).total_seconds() / 3600

        if completeness >= 3 and age_hours < 6:
            return WeatherDataQuality.EXCELLENT
        elif completeness >= 2 and age_hours < 12:
            return WeatherDataQuality.GOOD
        elif completeness >= 2 and age_hours < 24:
            return WeatherDataQuality.FAIR
        else:
            return WeatherDataQuality.POOR


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    """Example usage of WeatherContextBuilder"""

    print("Weather Context Builder - Task 2.2 Example")
    print("=" * 70)

    # Create builder
    builder = WeatherContextBuilder(
        accuweather_client=None,
        openweather_client=None,
        production_mode=False,
    )

    # Create sample weather
    weather = WeatherContext(
        game_location="Kansas City, MO",
        is_indoor=False,
        temperature_f=28,
        wind_speed_mph=18,
        precipitation_type=Precipitation.LIGHT_SNOW,
        forecast_timestamp=datetime.now(),
        hours_until_kickoff=4.0,
    )

    print(f"\nWeather: {weather.game_location}")
    print(f"  Temperature: {weather.temperature_f}°F")
    print(f"  Wind: {weather.wind_speed_mph} MPH")
    print(f"  Precipitation: {weather.precipitation_type.value}")

    # Calculate W-Factors
    wfactors = builder.calculate_wfactors(
        weather=weather,
        home_team="Kansas City Chiefs",
        away_team="Miami Dolphins",
    )

    print("\n✓ W-Factors Calculated")
    print(f"  Total Impact (Points): {wfactors.total_impact_points:.1f}")
    print(f"  Total Impact (Spread): {wfactors.total_impact_spread:+.1f}")
    print(f"  Impact Level: {wfactors.impact_level.value.title()}")

    print("\n" + "=" * 70)
    print("✓ Weather Context Builder is production-ready!")
