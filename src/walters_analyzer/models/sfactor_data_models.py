#!/usr/bin/env python3
"""
S-Factor Data Models - Billy Walters Methodology
=================================================

Complete Pydantic data models for the Billy Walters S-Factor system.
These models provide validation, auto-calculation, and type safety for
the entire data enrichment pipeline.

Key Principles:
- Power ratings on Billy Walters scale: -10 to +10
- Quality tiers: Elite/Great/Good/Average/Poor (auto-calculated)
- 95% completeness threshold for production use
- All data validated at instantiation

Version: 1.0
Created: November 20, 2025
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field
from decimal import Decimal


# ===== ENUMERATIONS =====


class TeamQualityTier(str, Enum):
    """
    Team quality classifications based on Billy Walters power rating scale.

    Scale: -10 (worst) to +10 (best)
    - ELITE: +8 to +10 (Top 3-4 teams)
    - GREAT: +4 to +8 (Playoff contenders)
    - GOOD: 0 to +4 (Above average)
    - AVERAGE: 0 (League average baseline)
    - POOR: Below 0 (Below average)
    """

    ELITE = "elite"  # +8 to +10
    GREAT = "great"  # +4 to +8
    GOOD = "good"  # 0 to +4
    AVERAGE = "average"  # 0
    POOR = "poor"  # Below 0


class GameTime(str, Enum):
    """Game time classifications for scheduling analysis"""

    EARLY_MORNING = "early_morning"  # 10am-12pm local
    AFTERNOON = "afternoon"  # 12pm-4pm local
    PRIME_TIME = "prime_time"  # 4pm-8pm local
    NIGHT = "night"  # 8pm+ local


class DayOfWeek(str, Enum):
    """Days of week for game scheduling"""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class Surface(str, Enum):
    """Playing surface types"""

    NATURAL_GRASS = "grass"
    ARTIFICIAL_TURF = "turf"
    DOME = "dome"


class Precipitation(str, Enum):
    """Precipitation types for weather analysis"""

    NONE = "none"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    LIGHT_SNOW = "light_snow"
    HEAVY_SNOW = "heavy_snow"
    MIXED = "mixed"


class WindCondition(str, Enum):
    """Wind speed classifications"""

    CALM = "calm"  # 0-5 mph
    LIGHT = "light"  # 5-10 mph
    MODERATE = "moderate"  # 10-20 mph
    STRONG = "strong"  # 20-30 mph
    SEVERE = "severe"  # 30+ mph


class ScheduleStrain(str, Enum):
    """Schedule difficulty classifications"""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class DataFreshness(str, Enum):
    """Data age classifications"""

    CURRENT = "current"  # <1 hour
    RECENT = "recent"  # 1-6 hours
    STALE = "stale"  # 6-24 hours
    OUTDATED = "outdated"  # >24 hours


# ===== BASIC DATA STRUCTURES =====


class Record(BaseModel):
    """Team win-loss record"""

    wins: int = Field(ge=0, description="Number of wins")
    losses: int = Field(ge=0, description="Number of losses")
    ties: int = Field(default=0, ge=0, description="Number of ties")

    @computed_field
    @property
    def total_games(self) -> int:
        """Total games played"""
        return self.wins + self.losses + self.ties

    @computed_field
    @property
    def win_percentage(self) -> float:
        """Win percentage (0.0 to 1.0)"""
        if self.total_games == 0:
            return 0.0
        return self.wins / self.total_games

    def __str__(self) -> str:
        if self.ties > 0:
            return f"{self.wins}-{self.losses}-{self.ties}"
        return f"{self.wins}-{self.losses}"


# ===== TEAM CONTEXT =====


class TeamContext(BaseModel):
    """
    Complete team profile with power rating and quality classification.

    This is the foundational team information used across all S-Factor
    calculations and edge detection.
    """

    # Identity
    team_name: str = Field(min_length=1, description="Full team name")
    team_abbrev: Optional[str] = Field(default=None, description="Team abbreviation")
    conference: Optional[str] = Field(default=None, description="Conference (AFC/NFC)")
    division: Optional[str] = Field(default=None, description="Division")

    # Power Rating (Billy Walters Scale)
    power_rating: float = Field(
        ge=-10.0, le=10.0, description="Billy Walters power rating (-10 to +10)"
    )
    power_rating_rank: Optional[int] = Field(
        default=None, ge=1, le=32, description="Rank among all teams (1=best)"
    )

    # Record
    overall_record: Record = Field(description="Overall season record")
    home_record: Optional[Record] = Field(default=None, description="Home record")
    away_record: Optional[Record] = Field(default=None, description="Away record")
    conference_record: Optional[Record] = Field(
        default=None, description="Conference record"
    )

    # Performance Metrics
    points_per_game: Optional[float] = Field(
        default=None, ge=0, description="Average PPG"
    )
    points_allowed_per_game: Optional[float] = Field(
        default=None, ge=0, description="Average PA/G"
    )
    point_differential: Optional[float] = Field(
        default=None, description="Point differential"
    )

    # Recent Form
    last_5_record: Optional[Record] = Field(default=None, description="Last 5 games")
    current_streak: Optional[str] = Field(default=None, description="W3, L2, etc.")

    # Schedule Context
    strength_of_schedule: Optional[float] = Field(
        default=None, ge=-10.0, le=10.0, description="Average opponent power rating"
    )
    games_remaining: Optional[int] = Field(default=None, ge=0, description="Games left")

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    data_source: str = Field(default="massey_espn", description="Data source")

    @computed_field
    @property
    def quality_tier(self) -> TeamQualityTier:
        """Auto-calculate quality tier from power rating"""
        return classify_quality_tier(self.power_rating)

    @computed_field
    @property
    def is_elite(self) -> bool:
        """Is this an elite team?"""
        return self.quality_tier == TeamQualityTier.ELITE

    @computed_field
    @property
    def is_playoff_team(self) -> bool:
        """Likely playoff team (Great or Elite)"""
        return self.quality_tier in [TeamQualityTier.ELITE, TeamQualityTier.GREAT]

    @computed_field
    @property
    def offensive_quality(self) -> str:
        """Offensive quality assessment"""
        if self.points_per_game is None:
            return "unknown"
        if self.points_per_game >= 28:
            return "elite"
        elif self.points_per_game >= 24:
            return "above_average"
        elif self.points_per_game >= 20:
            return "average"
        else:
            return "below_average"

    @computed_field
    @property
    def defensive_quality(self) -> str:
        """Defensive quality assessment"""
        if self.points_allowed_per_game is None:
            return "unknown"
        if self.points_allowed_per_game <= 17:
            return "elite"
        elif self.points_allowed_per_game <= 21:
            return "above_average"
        elif self.points_allowed_per_game <= 24:
            return "average"
        else:
            return "below_average"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "team_name": "Kansas City Chiefs",
                "team_abbrev": "KC",
                "conference": "AFC",
                "division": "AFC West",
                "power_rating": 9.2,
                "power_rating_rank": 1,
                "overall_record": {"wins": 10, "losses": 1},
                "points_per_game": 28.5,
                "points_allowed_per_game": 19.2,
            }
        }
    )


# ===== SCHEDULE HISTORY =====


class ScheduleHistory(BaseModel):
    """
    Team's recent schedule history for rest/travel/density analysis.

    Tracks:
    - Rest days since last game
    - Travel distance and time zones
    - Schedule density (games in last N days)
    - Consecutive away games
    - Bye week status
    """

    # Rest Analysis
    days_since_last_game: int = Field(ge=0, description="Days of rest")
    coming_off_bye: bool = Field(default=False, description="Just had bye week")
    rest_advantage_vs_opponent: Optional[int] = Field(
        default=None, description="Extra rest days vs opponent (can be negative)"
    )

    # Travel Analysis
    previous_game_location: Optional[str] = Field(
        default=None, description="City of last game"
    )
    travel_distance_miles: Optional[float] = Field(
        default=None, ge=0, description="Miles traveled since last game"
    )
    time_zones_crossed: int = Field(
        default=0, ge=0, le=3, description="Time zones crossed (0-3)"
    )
    consecutive_away_games: int = Field(
        default=0, ge=0, description="Number of consecutive away games"
    )

    # Schedule Density
    games_in_last_14_days: int = Field(
        default=0, ge=0, le=3, description="Recent game density"
    )
    games_in_last_21_days: int = Field(
        default=0, ge=0, le=4, description="3-week density"
    )

    # Schedule Strain Assessment
    @computed_field
    @property
    def schedule_strain(self) -> ScheduleStrain:
        """
        Assess overall schedule difficulty.

        Factors:
        - Short rest (<6 days)
        - Heavy travel (>1000 miles)
        - Multiple time zones (2+)
        - High game density (3+ in 14 days)
        """
        strain_score = 0

        # Rest penalty
        if self.days_since_last_game < 6:
            strain_score += 2
        elif self.days_since_last_game < 7:
            strain_score += 1

        # Travel penalty
        if self.travel_distance_miles:
            if self.travel_distance_miles > 2000:
                strain_score += 2
            elif self.travel_distance_miles > 1000:
                strain_score += 1

        # Time zone penalty
        if self.time_zones_crossed >= 2:
            strain_score += 2
        elif self.time_zones_crossed == 1:
            strain_score += 1

        # Density penalty
        if self.games_in_last_14_days >= 3:
            strain_score += 2
        elif self.games_in_last_14_days >= 2:
            strain_score += 1

        # Consecutive away
        if self.consecutive_away_games >= 3:
            strain_score += 2
        elif self.consecutive_away_games >= 2:
            strain_score += 1

        # Classify
        if strain_score >= 7:
            return ScheduleStrain.EXTREME
        elif strain_score >= 5:
            return ScheduleStrain.HIGH
        elif strain_score >= 3:
            return ScheduleStrain.MODERATE
        else:
            return ScheduleStrain.LOW

    @computed_field
    @property
    def has_rest_advantage(self) -> bool:
        """Team has significant rest advantage"""
        return (self.rest_advantage_vs_opponent or 0) >= 2

    @computed_field
    @property
    def has_travel_disadvantage(self) -> bool:
        """Team has significant travel burden"""
        return (
            (self.travel_distance_miles or 0) > 1500
            or self.time_zones_crossed >= 2
            or self.consecutive_away_games >= 3
        )


# ===== GAME CONTEXT =====


class GameContext(BaseModel):
    """
    Game-specific situational information.

    Captures:
    - Matchup details (division, rivalry, etc.)
    - Game importance (playoff implications)
    - Revenge/lookahead situations
    - Bounce-back spots
    """

    # Game Identity
    game_id: str = Field(description="Unique game identifier")
    game_date: date = Field(description="Game date")
    game_time: GameTime = Field(description="Time of day classification")
    day_of_week: DayOfWeek = Field(description="Day of week")
    week_number: int = Field(ge=1, le=18, description="NFL week number")

    # Teams
    home_team: str = Field(description="Home team name")
    away_team: str = Field(description="Away team name")

    # Matchup Classification
    is_division_game: bool = Field(default=False)
    is_conference_game: bool = Field(default=True)
    is_rivalry_game: bool = Field(default=False)

    # Game Importance
    playoff_implications: Optional[str] = Field(
        default=None, description="Description of playoff stakes"
    )
    home_team_playoff_probability: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Home team playoff probability"
    )
    away_team_playoff_probability: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Away team playoff probability"
    )

    # Situational Factors
    is_primetime: bool = Field(
        default=False, description="Thursday/Sunday/Monday night"
    )
    is_thanksgiving: bool = Field(default=False)
    is_international: bool = Field(default=False, description="London/Mexico/Germany")
    neutral_site: bool = Field(default=False)

    # Revenge/Lookahead
    is_revenge_game: Optional[bool] = Field(
        default=None, description="Rematch from last season"
    )
    has_lookahead_spot: Optional[bool] = Field(
        default=None, description="Team looking ahead to next opponent"
    )

    # Recent Results (for bounce-back)
    home_team_previous_margin: Optional[int] = Field(
        default=None, description="Home team's margin in last game (negative = loss)"
    )
    away_team_previous_margin: Optional[int] = Field(
        default=None, description="Away team's margin in last game (negative = loss)"
    )

    @computed_field
    @property
    def home_bounce_back_spot(self) -> bool:
        """Home team in bounce-back situation (lost by 19+)"""
        if self.home_team_previous_margin is None:
            return False
        return self.home_team_previous_margin <= -19

    @computed_field
    @property
    def away_bounce_back_spot(self) -> bool:
        """Away team in bounce-back situation (lost by 19+)"""
        if self.away_team_previous_margin is None:
            return False
        return self.away_team_previous_margin <= -19


# ===== WEATHER CONTEXT =====


class WeatherContext(BaseModel):
    """
    Weather conditions for game analysis.

    Includes:
    - Temperature (F)
    - Precipitation
    - Wind
    - Indoor/outdoor
    - Data freshness
    """

    # Location
    game_location: str = Field(description="City/stadium")
    is_indoor: bool = Field(default=False, description="Dome/retractable roof")

    # Temperature
    temperature_f: Optional[int] = Field(
        default=None, ge=-20, le=120, description="Temperature in Fahrenheit"
    )
    feels_like_f: Optional[int] = Field(
        default=None, description="Feels-like temperature"
    )

    # Precipitation
    precipitation_type: Precipitation = Field(default=Precipitation.NONE)
    precipitation_probability: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Chance of precipitation (0-1)"
    )

    # Wind
    wind_speed_mph: Optional[int] = Field(default=None, ge=0, le=100)
    wind_direction: Optional[str] = Field(default=None)
    wind_condition: Optional[WindCondition] = Field(default=None)

    # Data Quality
    forecast_timestamp: datetime = Field(description="When forecast was generated")
    hours_until_kickoff: Optional[float] = Field(default=None, ge=0)

    @computed_field
    @property
    def data_freshness(self) -> DataFreshness:
        """Classify data age"""
        age_hours = (datetime.now() - self.forecast_timestamp).total_seconds() / 3600

        if age_hours < 1:
            return DataFreshness.CURRENT
        elif age_hours < 6:
            return DataFreshness.RECENT
        elif age_hours < 24:
            return DataFreshness.STALE
        else:
            return DataFreshness.OUTDATED

    @computed_field
    @property
    def is_cold_weather(self) -> bool:
        """Temperature below 35°F"""
        if self.temperature_f is None or self.is_indoor:
            return False
        return self.temperature_f < 35

    @computed_field
    @property
    def is_extreme_cold(self) -> bool:
        """Temperature at or below 20°F"""
        if self.temperature_f is None or self.is_indoor:
            return False
        return self.temperature_f <= 20

    @computed_field
    @property
    def has_significant_precipitation(self) -> bool:
        """Heavy rain or any snow"""
        if self.is_indoor:
            return False
        return self.precipitation_type in [
            Precipitation.HEAVY_RAIN,
            Precipitation.LIGHT_SNOW,
            Precipitation.HEAVY_SNOW,
            Precipitation.MIXED,
        ]

    @computed_field
    @property
    def has_high_wind(self) -> bool:
        """Wind speed over 20 mph"""
        if self.is_indoor or self.wind_speed_mph is None:
            return False
        return self.wind_speed_mph > 20


# ===== COMPLETE GAME PACKAGE =====


class SFactorGamePackage(BaseModel):
    """
    Complete game context package for S-Factor analysis.

    This is the top-level data structure that combines all contexts
    for a single game. It's what the S-Factor calculator receives.
    """

    # Game Identity
    game_id: str = Field(description="Unique game identifier")
    sport: str = Field(default="NFL")
    season: int = Field(ge=2000, le=2100)
    week: int = Field(ge=1, le=18)

    # Team Contexts
    home_team_context: TeamContext = Field(description="Home team profile")
    away_team_context: TeamContext = Field(description="Away team profile")

    # Schedule Contexts
    home_schedule: ScheduleHistory = Field(description="Home team schedule history")
    away_schedule: ScheduleHistory = Field(description="Away team schedule history")

    # Game Context
    game_context: GameContext = Field(description="Game situation")

    # Weather Context
    weather: Optional[WeatherContext] = Field(
        default=None, description="Weather forecast"
    )

    # Surface Information
    playing_surface: Surface = Field(description="Playing surface type")

    # Metadata
    package_created: datetime = Field(default_factory=datetime.now)
    data_sources: Dict[str, str] = Field(
        default_factory=dict, description="Source tracking"
    )

    @computed_field
    @property
    def completeness_score(self) -> float:
        """
        Calculate data completeness percentage (0-100).

        Required fields:
        - Team contexts (power ratings, records)
        - Schedule histories (rest, travel)
        - Game context (matchup type, importance)
        - Weather (if outdoor game)

        Returns percentage complete.
        """
        total_checks = 0
        passed_checks = 0

        # Team contexts (weight: 30%)
        total_checks += 6
        if self.home_team_context.power_rating is not None:
            passed_checks += 1
        if self.away_team_context.power_rating is not None:
            passed_checks += 1
        if self.home_team_context.overall_record.total_games > 0:
            passed_checks += 1
        if self.away_team_context.overall_record.total_games > 0:
            passed_checks += 1
        if self.home_team_context.points_per_game is not None:
            passed_checks += 1
        if self.away_team_context.points_per_game is not None:
            passed_checks += 1

        # Schedule histories (weight: 25%)
        total_checks += 5
        if self.home_schedule.days_since_last_game >= 0:
            passed_checks += 1
        if self.away_schedule.days_since_last_game >= 0:
            passed_checks += 1
        if self.home_schedule.travel_distance_miles is not None:
            passed_checks += 1
        if self.away_schedule.travel_distance_miles is not None:
            passed_checks += 1
        if self.home_schedule.rest_advantage_vs_opponent is not None:
            passed_checks += 1

        # Game context (weight: 20%)
        total_checks += 4
        passed_checks += 1  # Always have basic game info
        if self.game_context.playoff_implications is not None:
            passed_checks += 1
        if self.game_context.home_team_previous_margin is not None:
            passed_checks += 1
        if self.game_context.away_team_previous_margin is not None:
            passed_checks += 1

        # Weather (weight: 25%, critical for outdoor games)
        if not self.weather or self.weather.is_indoor:
            # Indoor game - weather not needed
            total_checks += 1
            passed_checks += 1
        else:
            total_checks += 5
            if self.weather.temperature_f is not None:
                passed_checks += 2
            if self.weather.wind_speed_mph is not None:
                passed_checks += 2
            if self.weather.precipitation_type != Precipitation.NONE:
                passed_checks += 1

        return (passed_checks / total_checks) * 100

    @computed_field
    @property
    def is_production_ready(self) -> bool:
        """Package meets 95% completeness threshold"""
        return self.completeness_score >= 95.0

    @computed_field
    @property
    def power_rating_differential(self) -> float:
        """Home team power rating advantage"""
        return self.home_team_context.power_rating - self.away_team_context.power_rating

    @computed_field
    @property
    def quality_matchup_description(self) -> str:
        """Human-readable matchup quality"""
        home_tier = self.home_team_context.quality_tier.value
        away_tier = self.away_team_context.quality_tier.value
        return f"{home_tier.title()} vs {away_tier.title()}"


# ===== UTILITY FUNCTIONS =====


def classify_quality_tier(power_rating: float) -> TeamQualityTier:
    """
    Classify team quality tier from Billy Walters power rating.

    Scale:
    - Elite: +8 to +10 (Top 3-4 teams)
    - Great: +4 to +8 (Playoff contenders)
    - Good: 0 to +4 (Above average)
    - Average: 0 (League average baseline)
    - Poor: Below 0 (Below average)

    Args:
        power_rating: Billy Walters power rating (-10 to +10)

    Returns:
        TeamQualityTier enum value

    Examples:
        >>> classify_quality_tier(9.2)
        TeamQualityTier.ELITE
        >>> classify_quality_tier(5.5)
        TeamQualityTier.GREAT
        >>> classify_quality_tier(-2.0)
        TeamQualityTier.POOR
    """
    if power_rating >= 8.0:
        return TeamQualityTier.ELITE
    elif power_rating >= 4.0:
        return TeamQualityTier.GREAT
    elif power_rating > 0:
        return TeamQualityTier.GOOD
    elif power_rating == 0:
        return TeamQualityTier.AVERAGE
    else:
        return TeamQualityTier.POOR


# ===== EXAMPLE DATA =====

if __name__ == "__main__":
    """Example usage and validation"""

    print("Billy Walters S-Factor Data Models")
    print("=" * 60)

    # Example 1: Create a team context
    chiefs = TeamContext(
        team_name="Kansas City Chiefs",
        team_abbrev="KC",
        conference="AFC",
        division="AFC West",
        power_rating=9.2,
        power_rating_rank=1,
        overall_record=Record(wins=10, losses=1),
        home_record=Record(wins=5, losses=0),
        points_per_game=28.5,
        points_allowed_per_game=19.2,
    )

    print(f"\n✓ Created team: {chiefs.team_name}")
    print(f"  Power Rating: {chiefs.power_rating}")
    print(f"  Quality Tier: {chiefs.quality_tier.value.title()}")
    print(f"  Record: {chiefs.overall_record}")
    print(f"  Win %: {chiefs.overall_record.win_percentage:.1%}")

    # Example 2: Schedule history
    schedule = ScheduleHistory(
        days_since_last_game=14,
        coming_off_bye=True,
        travel_distance_miles=1200,
        time_zones_crossed=2,
        games_in_last_14_days=1,
        rest_advantage_vs_opponent=7,
    )

    print("\n✓ Created schedule history")
    print(f"  Rest: {schedule.days_since_last_game} days (bye week)")
    print(
        f"  Travel: {schedule.travel_distance_miles} miles, {schedule.time_zones_crossed} zones"
    )
    print(f"  Schedule Strain: {schedule.schedule_strain.value.title()}")

    # Example 3: Complete game package
    game = SFactorGamePackage(
        game_id="2025_WK12_BUF_DET",
        season=2025,
        week=12,
        home_team_context=chiefs,
        away_team_context=TeamContext(
            team_name="Buffalo Bills",
            team_abbrev="BUF",
            power_rating=8.5,
            overall_record=Record(wins=9, losses=2),
            points_per_game=27.0,
            points_allowed_per_game=20.5,
        ),
        home_schedule=schedule,
        away_schedule=ScheduleHistory(
            days_since_last_game=7, travel_distance_miles=800, games_in_last_14_days=2
        ),
        game_context=GameContext(
            game_id="2025_WK12_BUF_DET",
            game_date=date(2025, 11, 24),
            game_time=GameTime.AFTERNOON,
            day_of_week=DayOfWeek.SUNDAY,
            week_number=12,
            home_team="Kansas City Chiefs",
            away_team="Buffalo Bills",
            is_conference_game=True,
            is_primetime=False,
        ),
        playing_surface=Surface.NATURAL_GRASS,
    )

    print("\n✓ Created complete game package")
    print(
        f"  Game: {game.away_team_context.team_name} @ {game.home_team_context.team_name}"
    )
    print(f"  Matchup: {game.quality_matchup_description}")
    print(
        f"  Power Rating Diff: {game.power_rating_differential:+.1f} (home advantage)"
    )
    print(f"  Completeness: {game.completeness_score:.1f}%")
    print(f"  Production Ready: {'✓' if game.is_production_ready else '✗'}")

    print("\n" + "=" * 60)
    print("✓ All examples completed successfully!")
    print("Models are ready for use in team_context_builder.py")
