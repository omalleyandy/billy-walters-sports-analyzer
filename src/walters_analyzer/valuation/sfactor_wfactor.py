#!/usr/bin/env python3
"""
Billy Walters S and W Factor Reference System
=============================================

This module implements the complete S-Factor (Special Factors) and W-Factor (Weather Factors)
system from Billy Walters' Advanced Master Class methodology.

Key Principle: 5 Factor Points = 1 Point Spread Adjustment

S-Factors cover situational advantages:
- Turf matchups
- Division/Conference factors  
- Schedule factors (bye weeks, short rest, night games)
- Travel distance and time zones
- Bounce-back situations
- Playoff implications

W-Factors cover weather impacts:
- Temperature extremes
- Precipitation (rain, snow)
- Wind conditions
- Dome team adjustments

Based on: "Gambler: Secrets from a Life at Risk" - Advanced Master Class
Version: 1.0
Date: November 19, 2025
"""

from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from enum import Enum


class TurfType(Enum):
    """Types of playing surfaces"""
    NATURAL_GRASS = "grass"
    ARTIFICIAL_TURF = "turf"
    DOME = "dome"


class TeamQuality(Enum):
    """Team quality tiers for bye week adjustments"""
    BELOW_AVERAGE = "below_average"  # Bottom 10 teams
    AVERAGE = "average"               # Middle 12 teams
    GREAT = "great"                   # Top 10 teams


@dataclass
class SFactorResult:
    """Result of S-Factor calculation"""
    total_points: float
    spread_adjustment: float
    breakdown: Dict[str, float]  # Details by category
    
    def __str__(self):
        return f"S-Factors: {self.total_points:.1f} pts → {self.spread_adjustment:.2f} spread"


@dataclass
class WFactorResult:
    """Result of W-Factor calculation"""
    total_points: float
    spread_adjustment: float
    breakdown: Dict[str, float]
    
    def __str__(self):
        return f"W-Factors: {self.total_points:.1f} pts → {self.spread_adjustment:.2f} spread"


class SFactorCalculator:
    """
    Calculate S-Factors (Situational Factors) per Billy Walters methodology.
    
    All factors are in S-Factor points where 5 points = 1 spread point.
    Convention: Positive values favor the team being analyzed.
    """
    
    # Conversion constant
    SPREAD_CONVERSION_RATIO = 5.0
    
    # ===== TURF FACTORS (Image 1) =====
    TURF_SAME = 1.0          # Visitor gets +1 when both teams same turf
    TURF_OPPOSITE = 1.0      # Home gets +1 when teams opposite turf
    
    # ===== DIVISION/CONFERENCE FACTORS (Image 1) =====
    SAME_DIVISION = 1.0      # Visitor gets +1 in division games
    DIFFERENT_CONFERENCE = 1.0  # Home gets +1 vs different conference
    
    # ===== SCHEDULE FACTORS (Images 1-2) =====
    # Thursday Night Football
    HOME_THURSDAY_NIGHT = 2.0           # Home team on TNF
    TEAMS_OFF_THURSDAY = 0.0            # Coming off Thursday = neutral
    
    # Sunday Night Football
    HOME_SUNDAY_NIGHT = 4.0             # Home team on SNF
    
    # Monday Night Football
    HOME_MONDAY_NIGHT = 2.0             # Home team on MNF
    HOME_OFF_MONDAY_HOME = 0.0          # Home team coming off MNF at home
    HOME_OFF_MONDAY_AWAY = 4.0          # Home team coming off MNF away
    AWAY_OFF_MONDAY_HOME = 6.0          # Away team coming off MNF home
    AWAY_OFF_MONDAY_AWAY = 8.0          # Away team coming off MNF away
    
    # Saturday Night
    HOME_SATURDAY_NIGHT = 0.0           # No advantage
    
    # Schedule density
    THIRD_AWAY_IN_FOUR = 2.0            # Home gets +2 when opponent 3rd away in 4
    
    # Overtime games
    HOME_OFF_OVERTIME = 4.0             # Team coming off OT at home
    AWAY_OFF_OVERTIME = 2.0             # Team coming off OT away
    
    # ===== BYE WEEK FACTORS (Image 2) =====
    # Quality tier determines bye week value
    BYE_BELOW_AVG = 4.0                 # Below average team off bye
    BYE_BELOW_AVG_AWAY = 5.0            # Below average team off bye + away
    BYE_AVERAGE = 5.0                   # Average team off bye
    BYE_AVERAGE_AWAY = 6.0              # Average team off bye + away
    BYE_GREAT = 7.0                     # Great team off bye
    BYE_GREAT_AWAY = 8.0                # Great team off bye + away
    
    # ===== PLAYOFF FACTORS (Image 2) =====
    BYE_IN_PLAYOFFS = 1.0               # Home team with playoff bye
    
    # Super Bowl winners
    SB_WINNER_FIRST_GAME = 4.0          # SB winner's first game next season
    SB_WINNER_FIRST_FOUR = 2.0          # SB winner's first 4 games
    
    # Super Bowl losers
    SB_LOSER_FIRST_GAME = 4.0           # Opponent of SB loser first game
    SB_LOSER_FIRST_FOUR = 2.0           # Opponent of SB loser first 4 games
    
    # ===== TRAVEL DISTANCE (Image 2) =====
    # Over 2000 miles - specific city pairs
    TRAVEL_2000_TB_JAC_MIA = 1.0        # Home advantage for TB/Jac/Mia
    TRAVEL_2000_DAL_HOU = 1.0           # Home advantage for Dal/Hou
    TRAVEL_2000_ATL_CAR = 1.0           # Visitor advantage for Atl/Car
    
    # Major travel pairs (Image 3)
    TRAVEL_LAR_LAC = 2.0                # Visitor from LA Rams/Chargers
    TRAVEL_LV_LA = 1.0                  # Visitor from LV to LA
    TRAVEL_IND_CIN = 1.0                # Visitor from Ind to Cin
    TRAVEL_PHI_NYG_NYJ_WAS_NE_BAL_BUF = 1.0  # Any combination
    TRAVEL_NYG_NYJ = 2.0                # Giants to Jets or vice versa
    TRAVEL_BAL_WAS = 2.0                # Baltimore to Washington
    TRAVEL_CHC_GB = 1.0                 # Chicago to Green Bay
    
    # ===== TIME ZONE FACTORS (Image 3) =====
    # 10:00 AM games (West coast early)
    TZ_10AM_WEST_TEAM = 2.0             # Penalize West teams in 10am games
    TZ_10AM_MOUNTAIN_TEAM = 1.0         # Penalize Mountain teams
    
    # Night games (East coast late)
    TZ_NIGHT_EAST_TEAM = 6.0            # Penalize East teams in night games
    TZ_NIGHT_CENTRAL_TEAM = 3.0         # Penalize Central teams
    TZ_NIGHT_MOUNTAIN_TEAM = 1.0        # Penalize Mountain teams
    
    # Consecutive games across time zones
    TZ_SECOND_GAME_2PLUS_ZONES = 2.0    # Home advantage if opponent played 2nd 
                                         # consecutive game 2+ time zones away
    
    # ===== BOUNCE BACK (Image 3) =====
    BOUNCE_LOST_19_PLUS = 2.0           # Team lost previous by 19+ points
    BOUNCE_LOST_29_PLUS = 4.0           # Team lost previous by 29+ points
    
    @classmethod
    def calculate_turf_factors(
        cls,
        team_turf: TurfType,
        opponent_turf: TurfType,
        is_home: bool
    ) -> Tuple[float, str]:
        """
        Calculate turf advantage factors.
        
        Args:
            team_turf: Playing surface team is used to
            opponent_turf: Playing surface opponent is used to
            is_home: Whether team being analyzed is home team
            
        Returns:
            Tuple of (factor_points, description)
        """
        if team_turf == opponent_turf:
            # Same turf - visitor gets advantage
            if not is_home:
                return (cls.TURF_SAME, "Visitor: Same turf advantage")
            else:
                return (0.0, "Home: No turf advantage (same turf)")
        else:
            # Opposite turf - home gets advantage
            if is_home:
                return (cls.TURF_OPPOSITE, "Home: Opposite turf advantage")
            else:
                return (0.0, "Visitor: No turf advantage (opposite turf)")
    
    @classmethod
    def calculate_division_factors(
        cls,
        same_division: bool,
        same_conference: bool,
        is_home: bool
    ) -> Tuple[float, str]:
        """Calculate division/conference factors."""
        if same_division:
            # Division game - visitor gets advantage
            if not is_home:
                return (cls.SAME_DIVISION, "Visitor: Division game advantage")
            else:
                return (0.0, "Home: Division game (no advantage)")
        elif not same_conference:
            # Different conference - home gets advantage
            if is_home:
                return (cls.DIFFERENT_CONFERENCE, "Home: Cross-conference advantage")
            else:
                return (0.0, "Visitor: Cross-conference (no advantage)")
        else:
            return (0.0, "Same conference, different division (neutral)")
    
    @classmethod
    def calculate_schedule_factors(
        cls,
        is_home: bool,
        is_thursday_night: bool = False,
        is_sunday_night: bool = False,
        is_monday_night: bool = False,
        is_saturday_night: bool = False,
        coming_off_thursday: bool = False,
        coming_off_monday_home: bool = False,
        coming_off_monday_away: bool = False,
        third_away_in_four: bool = False,
        coming_off_overtime_home: bool = False,
        coming_off_overtime_away: bool = False
    ) -> Tuple[float, str]:
        """Calculate schedule-related factors."""
        total = 0.0
        details = []
        
        # Night games
        if is_home:
            if is_thursday_night:
                total += cls.HOME_THURSDAY_NIGHT
                details.append(f"Home Thursday Night: +{cls.HOME_THURSDAY_NIGHT}")
            if is_sunday_night:
                total += cls.HOME_SUNDAY_NIGHT
                details.append(f"Home Sunday Night: +{cls.HOME_SUNDAY_NIGHT}")
            if is_monday_night:
                total += cls.HOME_MONDAY_NIGHT
                details.append(f"Home Monday Night: +{cls.HOME_MONDAY_NIGHT}")
            if is_saturday_night:
                # No advantage for Saturday night
                details.append("Home Saturday Night: +0")
        
        # Coming off games
        if coming_off_thursday:
            details.append("Coming off Thursday: +0 (neutral)")
        
        if is_home and coming_off_monday_away:
            total += cls.HOME_OFF_MONDAY_AWAY
            details.append(f"Home coming off MNF away: +{cls.HOME_OFF_MONDAY_AWAY}")
        elif not is_home and coming_off_monday_home:
            total += cls.AWAY_OFF_MONDAY_HOME
            details.append(f"Away coming off MNF home: +{cls.AWAY_OFF_MONDAY_HOME}")
        elif not is_home and coming_off_monday_away:
            total += cls.AWAY_OFF_MONDAY_AWAY
            details.append(f"Away coming off MNF away: +{cls.AWAY_OFF_MONDAY_AWAY}")
        
        # Schedule density
        if is_home and third_away_in_four:
            total += cls.THIRD_AWAY_IN_FOUR
            details.append(f"Opponent 3rd away in 4: +{cls.THIRD_AWAY_IN_FOUR}")
        
        # Overtime recovery
        if coming_off_overtime_home:
            total += cls.HOME_OFF_OVERTIME
            details.append(f"Coming off OT at home: +{cls.HOME_OFF_OVERTIME}")
        if coming_off_overtime_away:
            total += cls.AWAY_OFF_OVERTIME
            details.append(f"Coming off OT away: +{cls.AWAY_OFF_OVERTIME}")
        
        description = "; ".join(details) if details else "No schedule factors"
        return (total, description)
    
    @classmethod
    def calculate_bye_factors(
        cls,
        coming_off_bye: bool,
        team_quality: TeamQuality,
        is_away_game: bool
    ) -> Tuple[float, str]:
        """Calculate bye week rest advantage."""
        if not coming_off_bye:
            return (0.0, "No bye week advantage")
        
        if team_quality == TeamQuality.BELOW_AVERAGE:
            value = cls.BYE_BELOW_AVG_AWAY if is_away_game else cls.BYE_BELOW_AVG
            tier = "Below Average"
        elif team_quality == TeamQuality.AVERAGE:
            value = cls.BYE_AVERAGE_AWAY if is_away_game else cls.BYE_AVERAGE
            tier = "Average"
        else:  # GREAT
            value = cls.BYE_GREAT_AWAY if is_away_game else cls.BYE_GREAT
            tier = "Great"
        
        location = "away" if is_away_game else "home"
        return (value, f"{tier} team off bye ({location}): +{value}")
    
    @classmethod
    def calculate_time_zone_factors(
        cls,
        team_time_zone: str,  # "ET", "CT", "MT", "PT"
        game_time_zone: str,
        is_10am_game: bool,
        is_night_game: bool,
        second_consecutive_2plus_zones: bool
    ) -> Tuple[float, str]:
        """Calculate time zone travel penalties."""
        total = 0.0
        details = []
        
        if is_10am_game:
            if team_time_zone == "PT":
                total += cls.TZ_10AM_WEST_TEAM
                details.append(f"West team in 10am game: +{cls.TZ_10AM_WEST_TEAM}")
            elif team_time_zone == "MT":
                total += cls.TZ_10AM_MOUNTAIN_TEAM
                details.append(f"Mountain team in 10am game: +{cls.TZ_10AM_MOUNTAIN_TEAM}")
        
        if is_night_game:
            if team_time_zone == "ET":
                total += cls.TZ_NIGHT_EAST_TEAM
                details.append(f"East team in night game: +{cls.TZ_NIGHT_EAST_TEAM}")
            elif team_time_zone == "CT":
                total += cls.TZ_NIGHT_CENTRAL_TEAM
                details.append(f"Central team in night game: +{cls.TZ_NIGHT_CENTRAL_TEAM}")
            elif team_time_zone == "MT":
                total += cls.TZ_NIGHT_MOUNTAIN_TEAM
                details.append(f"Mountain team in night game: +{cls.TZ_NIGHT_MOUNTAIN_TEAM}")
        
        if second_consecutive_2plus_zones:
            total += cls.TZ_SECOND_GAME_2PLUS_ZONES
            details.append(f"2nd consecutive 2+ TZ away: +{cls.TZ_SECOND_GAME_2PLUS_ZONES}")
        
        description = "; ".join(details) if details else "No time zone factors"
        return (total, description)
    
    @classmethod
    def calculate_bounce_back_factors(
        cls,
        previous_loss_margin: Optional[int]
    ) -> Tuple[float, str]:
        """Calculate bounce-back factors from previous loss."""
        if previous_loss_margin is None or previous_loss_margin < 19:
            return (0.0, "No bounce-back factor")
        
        if previous_loss_margin >= 29:
            return (cls.BOUNCE_LOST_29_PLUS, 
                   f"Lost by {previous_loss_margin}+ (29+): +{cls.BOUNCE_LOST_29_PLUS}")
        else:  # 19-28
            return (cls.BOUNCE_LOST_19_PLUS,
                   f"Lost by {previous_loss_margin} (19+): +{cls.BOUNCE_LOST_19_PLUS}")
    
    @classmethod
    def calculate_complete_sfactors(
        cls,
        is_home: bool,
        team_turf: Optional[TurfType] = None,
        opponent_turf: Optional[TurfType] = None,
        same_division: bool = False,
        same_conference: bool = True,
        coming_off_bye: bool = False,
        team_quality: TeamQuality = TeamQuality.AVERAGE,
        is_thursday_night: bool = False,
        is_sunday_night: bool = False,
        is_monday_night: bool = False,
        previous_loss_margin: Optional[int] = None,
        team_time_zone: str = "ET",
        game_time_zone: str = "ET",
        is_10am_game: bool = False,
        is_night_game: bool = False,
        **kwargs
    ) -> SFactorResult:
        """
        Calculate complete S-Factor analysis for a team.
        
        This is the main entry point combining all S-Factor categories.
        
        Args:
            is_home: Whether team being analyzed is home team
            team_turf: Team's home playing surface
            opponent_turf: Opponent's home playing surface
            same_division: Whether teams in same division
            same_conference: Whether teams in same conference
            coming_off_bye: Team coming off bye week
            team_quality: Team quality tier for bye calculations
            is_thursday_night: Game on Thursday night
            is_sunday_night: Game on Sunday night
            is_monday_night: Game on Monday night
            previous_loss_margin: Points lost by in previous game (if applicable)
            team_time_zone: Team's home time zone
            game_time_zone: Game location time zone
            is_10am_game: 10:00 AM local kickoff
            is_night_game: Night game (after 6 PM local)
            **kwargs: Additional schedule factors
            
        Returns:
            SFactorResult with total points and breakdown
        """
        total_points = 0.0
        breakdown = {}
        
        # Turf factors
        if team_turf and opponent_turf:
            turf_pts, turf_desc = cls.calculate_turf_factors(
                team_turf, opponent_turf, is_home
            )
            total_points += turf_pts
            breakdown["turf"] = turf_pts
        
        # Division/conference factors
        div_pts, div_desc = cls.calculate_division_factors(
            same_division, same_conference, is_home
        )
        total_points += div_pts
        breakdown["division"] = div_pts
        
        # Schedule factors
        sched_pts, sched_desc = cls.calculate_schedule_factors(
            is_home,
            is_thursday_night=is_thursday_night,
            is_sunday_night=is_sunday_night,
            is_monday_night=is_monday_night,
            **kwargs
        )
        total_points += sched_pts
        breakdown["schedule"] = sched_pts
        
        # Bye week factors
        if coming_off_bye:
            bye_pts, bye_desc = cls.calculate_bye_factors(
                coming_off_bye, team_quality, not is_home
            )
            total_points += bye_pts
            breakdown["bye"] = bye_pts
        
        # Time zone factors
        tz_pts, tz_desc = cls.calculate_time_zone_factors(
            team_time_zone, game_time_zone, 
            is_10am_game, is_night_game,
            kwargs.get('second_consecutive_2plus_zones', False)
        )
        total_points += tz_pts
        breakdown["time_zone"] = tz_pts
        
        # Bounce-back factors
        if previous_loss_margin:
            bb_pts, bb_desc = cls.calculate_bounce_back_factors(previous_loss_margin)
            total_points += bb_pts
            breakdown["bounce_back"] = bb_pts
        
        # Convert to spread adjustment
        spread_adjustment = total_points / cls.SPREAD_CONVERSION_RATIO
        
        return SFactorResult(
            total_points=total_points,
            spread_adjustment=spread_adjustment,
            breakdown=breakdown
        )


class WFactorCalculator:
    """
    Calculate W-Factors (Weather Factors) per Billy Walters methodology.
    
    All factors in W-Factor points where 5 points = 1 spread point.
    """
    
    # Conversion constant
    SPREAD_CONVERSION_RATIO = 5.0
    
    # ===== WARM TEAM TO COLD OUTDOOR ENVIRONMENT (Image 3) =====
    WARM_TO_COLD_35F = 0.25      # Home +0.25 spread
    WARM_TO_COLD_30F = 0.50      # Home +0.50 spread
    WARM_TO_COLD_25F = 0.75      # Home +0.75 spread
    WARM_TO_COLD_20F = 1.00      # Home +1.00 spread
    WARM_TO_COLD_15F = 1.25      # Home +1.25 spread
    WARM_TO_COLD_10F = 1.75      # Home +1.75 spread (10 or below)
    
    # ===== COLD DOME TEAM TO COLD OUTDOOR ENVIRONMENT (Image 4) =====
    DOME_TO_COLD_30_20F = 0.25   # Home +0.25 spread
    DOME_TO_COLD_20_10F = 0.50   # Home +0.50 spread
    DOME_TO_COLD_10_5F = 0.75    # Home +0.75 spread
    
    # ===== PRECIPITATION (Image 4) =====
    RAIN = 0.25                  # Visitor +0.25 spread
    HARD_RAIN = 0.75             # Visitor +0.75 spread
    # SNOW and HEAVY_WIND are variable based on teams
    
    @classmethod
    def calculate_temperature_factors(
        cls,
        temperature_f: int,
        home_team_warm_weather: bool,
        visiting_team_warm_weather: bool,
        home_team_dome: bool,
        visiting_team_dome: bool
    ) -> Tuple[float, str]:
        """
        Calculate temperature-related factors.
        
        Args:
            temperature_f: Game temperature in Fahrenheit
            home_team_warm_weather: Home team from warm climate
            visiting_team_warm_weather: Visitor from warm climate
            home_team_dome: Home team plays in dome
            visiting_team_dome: Visitor plays in dome
            
        Returns:
            Tuple of (spread_adjustment, description)
            Positive = Home advantage, Negative = Visitor advantage
        """
        # Warm-weather team visiting cold outdoor environment
        if visiting_team_warm_weather and not visiting_team_dome:
            if temperature_f <= 10:
                return (cls.WARM_TO_COLD_10F, 
                       f"Warm visitor in {temperature_f}°F: +{cls.WARM_TO_COLD_10F} home")
            elif temperature_f <= 15:
                return (cls.WARM_TO_COLD_15F,
                       f"Warm visitor in {temperature_f}°F: +{cls.WARM_TO_COLD_15F} home")
            elif temperature_f <= 20:
                return (cls.WARM_TO_COLD_20F,
                       f"Warm visitor in {temperature_f}°F: +{cls.WARM_TO_COLD_20F} home")
            elif temperature_f <= 25:
                return (cls.WARM_TO_COLD_25F,
                       f"Warm visitor in {temperature_f}°F: +{cls.WARM_TO_COLD_25F} home")
            elif temperature_f <= 30:
                return (cls.WARM_TO_COLD_30F,
                       f"Warm visitor in {temperature_f}°F: +{cls.WARM_TO_COLD_30F} home")
            elif temperature_f <= 35:
                return (cls.WARM_TO_COLD_35F,
                       f"Warm visitor in {temperature_f}°F: +{cls.WARM_TO_COLD_35F} home")
        
        # Dome team visiting cold outdoor environment
        if visiting_team_dome and not home_team_dome:
            if 20 <= temperature_f < 30:
                return (cls.DOME_TO_COLD_30_20F,
                       f"Dome visitor in {temperature_f}°F: +{cls.DOME_TO_COLD_30_20F} home")
            elif 10 <= temperature_f < 20:
                return (cls.DOME_TO_COLD_20_10F,
                       f"Dome visitor in {temperature_f}°F: +{cls.DOME_TO_COLD_20_10F} home")
            elif 5 <= temperature_f < 10:
                return (cls.DOME_TO_COLD_10_5F,
                       f"Dome visitor in {temperature_f}°F: +{cls.DOME_TO_COLD_10_5F} home")
        
        return (0.0, f"Temperature {temperature_f}°F: No significant factor")
    
    @classmethod
    def calculate_precipitation_factors(
        cls,
        is_raining: bool,
        is_hard_rain: bool,
        is_snowing: bool
    ) -> Tuple[float, str]:
        """Calculate precipitation factors."""
        if is_hard_rain:
            # Hard rain favors visitor (run-heavy, low scoring)
            return (-cls.HARD_RAIN, 
                   f"Hard rain: +{cls.HARD_RAIN} visitor")
        elif is_raining:
            return (-cls.RAIN,
                   f"Rain: +{cls.RAIN} visitor")
        elif is_snowing:
            return (0.0, "Snow: Variable (team-dependent)")
        else:
            return (0.0, "No precipitation")
    
    @classmethod
    def calculate_wind_factors(
        cls,
        wind_speed_mph: int,
        home_team_pass_heavy: bool,
        visiting_team_pass_heavy: bool
    ) -> Tuple[float, str]:
        """
        Calculate wind impact (variable based on team styles).
        
        Heavy wind (>20 mph) significantly impacts passing games.
        This is team-dependent and should be evaluated based on offensive styles.
        """
        if wind_speed_mph > 20:
            # High wind hurts passing teams
            if visiting_team_pass_heavy and not home_team_pass_heavy:
                # Visitor relies on passing, home doesn't
                return (0.5, f"Wind {wind_speed_mph} mph hurts visitor passing game")
            elif home_team_pass_heavy and not visiting_team_pass_heavy:
                return (-0.5, f"Wind {wind_speed_mph} mph hurts home passing game")
            else:
                return (0.0, f"Wind {wind_speed_mph} mph: Affects both teams equally")
        else:
            return (0.0, f"Wind {wind_speed_mph} mph: Not significant")
    
    @classmethod
    def calculate_complete_wfactors(
        cls,
        temperature_f: Optional[int] = None,
        home_team_warm_weather: bool = False,
        visiting_team_warm_weather: bool = False,
        home_team_dome: bool = False,
        visiting_team_dome: bool = False,
        is_raining: bool = False,
        is_hard_rain: bool = False,
        is_snowing: bool = False,
        wind_speed_mph: int = 0,
        home_team_pass_heavy: bool = False,
        visiting_team_pass_heavy: bool = False
    ) -> WFactorResult:
        """
        Calculate complete W-Factor analysis.
        
        Args:
            temperature_f: Game temperature in Fahrenheit
            home_team_warm_weather: Home team from warm climate (MIA, TB, etc.)
            visiting_team_warm_weather: Visitor from warm climate
            home_team_dome: Home team plays in dome
            visiting_team_dome: Visitor plays in dome
            is_raining: Light to moderate rain
            is_hard_rain: Heavy rain
            is_snowing: Snow conditions
            wind_speed_mph: Wind speed in miles per hour
            home_team_pass_heavy: Home team pass-heavy offense
            visiting_team_pass_heavy: Visitor pass-heavy offense
            
        Returns:
            WFactorResult with spread adjustment and breakdown
        """
        total_adjustment = 0.0
        breakdown = {}
        
        # Temperature factors
        if temperature_f is not None:
            temp_adj, temp_desc = cls.calculate_temperature_factors(
                temperature_f,
                home_team_warm_weather,
                visiting_team_warm_weather,
                home_team_dome,
                visiting_team_dome
            )
            total_adjustment += temp_adj
            breakdown["temperature"] = temp_adj
        
        # Precipitation factors
        precip_adj, precip_desc = cls.calculate_precipitation_factors(
            is_raining, is_hard_rain, is_snowing
        )
        total_adjustment += precip_adj
        breakdown["precipitation"] = precip_adj
        
        # Wind factors
        wind_adj, wind_desc = cls.calculate_wind_factors(
            wind_speed_mph, home_team_pass_heavy, visiting_team_pass_heavy
        )
        total_adjustment += wind_adj
        breakdown["wind"] = wind_adj
        
        # Convert adjustment to W-Factor points
        total_points = total_adjustment * cls.SPREAD_CONVERSION_RATIO
        
        return WFactorResult(
            total_points=total_points,
            spread_adjustment=total_adjustment,
            breakdown=breakdown
        )


# ===== HELPER FUNCTIONS =====

def get_team_time_zone(team_abbrev: str) -> str:
    """Map team abbreviation to home time zone."""
    TIME_ZONES = {
        # Eastern Time
        "BUF": "ET", "MIA": "ET", "NE": "ET", "NYJ": "ET",
        "BAL": "ET", "CIN": "ET", "CLE": "ET", "PIT": "ET",
        "ATL": "ET", "CAR": "ET", "NO": "ET", "TB": "ET",
        "WAS": "ET", "NYG": "ET", "PHI": "ET", "DAL": "ET",
        "JAX": "ET", "TEN": "ET", "IND": "ET",
        
        # Central Time
        "CHI": "CT", "DET": "CT", "GB": "CT", "MIN": "CT",
        "HOU": "CT", "KC": "CT",
        
        # Mountain Time
        "DEN": "MT",
        
        # Pacific Time
        "LAR": "PT", "LAC": "PT", "SF": "PT", "SEA": "PT",
        "LV": "PT", "ARI": "PT"
    }
    return TIME_ZONES.get(team_abbrev, "ET")


def is_warm_weather_team(team_abbrev: str) -> bool:
    """Identify teams from warm climates."""
    WARM_TEAMS = {"MIA", "TB", "JAX", "NO", "ATL", "CAR", "ARI", "LAR", "LAC", "SF"}
    return team_abbrev in WARM_TEAMS


def is_dome_team(team_abbrev: str) -> bool:
    """Identify teams that play in domes."""
    DOME_TEAMS = {"ATL", "NO", "DET", "MIN", "IND", "LV", "LAR"}
    return team_abbrev in DOME_TEAMS


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    # Example: Bills @ Lions, Week 12
    print("Example: Buffalo Bills @ Detroit Lions (Week 12)")
    print("=" * 60)
    
    # Calculate S-Factors for Lions (home team)
    lions_sfactors = SFactorCalculator.calculate_complete_sfactors(
        is_home=True,
        team_turf=TurfType.DOME,
        opponent_turf=TurfType.ARTIFICIAL_TURF,
        same_division=False,
        same_conference=True,
        coming_off_bye=False,
        is_thursday_night=False,
        team_time_zone="ET",
        game_time_zone="ET"
    )
    
    print(f"\nLions S-Factors: {lions_sfactors}")
    print(f"Breakdown: {lions_sfactors.breakdown}")
    
    # Calculate W-Factors (indoor game)
    game_wfactors = WFactorCalculator.calculate_complete_wfactors(
        temperature_f=None,  # Indoor game
        home_team_dome=True,
        visiting_team_dome=False
    )
    
    print(f"\nW-Factors: {game_wfactors}")
    print(f"Breakdown: {game_wfactors.breakdown}")
    
    print("\n" + "=" * 60)
    print(f"Total adjustment for Lions: {lions_sfactors.spread_adjustment + game_wfactors.spread_adjustment:.2f} points")
