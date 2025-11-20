#!/usr/bin/env python3
"""
Schedule History Calculator - Billy Walters S-Factor System
===========================================================

Calculates comprehensive schedule history metrics for S-Factor analysis:
- Rest days since last game
- Travel distance (great circle Haversine formula)
- Time zones crossed
- Schedule density (games per time period)
- Schedule strain assessment

Uses actual NFL city coordinates and time zones for accurate calculations.

Version: 1.0
Created: November 20, 2025
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from dataclasses import dataclass
import math
import logging

from walters_analyzer.models.sfactor_data_models import (
    ScheduleHistory,
    ScheduleStrain
)

logger = logging.getLogger(__name__)


# ===== NFL CITIES DATABASE =====

# NFL team home cities with coordinates (lat, lon)
NFL_CITIES = {
    # AFC East
    "Buffalo Bills": (42.7738, -78.7870),
    "Miami Dolphins": (25.9580, -80.2389),
    "New England Patriots": (42.0909, -71.2643),
    "New York Jets": (40.8136, -74.0744),
    
    # AFC North
    "Baltimore Ravens": (39.2780, -76.6227),
    "Cincinnati Bengals": (39.0954, -84.5160),
    "Cleveland Browns": (41.5061, -81.6995),
    "Pittsburgh Steelers": (40.4468, -80.0158),
    
    # AFC South
    "Houston Texans": (29.6847, -95.4107),
    "Indianapolis Colts": (39.7601, -86.1639),
    "Jacksonville Jaguars": (30.3240, -81.6373),
    "Tennessee Titans": (36.1665, -86.7713),
    
    # AFC West
    "Denver Broncos": (39.7439, -105.0201),
    "Kansas City Chiefs": (39.0489, -94.4839),
    "Las Vegas Raiders": (36.0909, -115.1833),
    "Los Angeles Chargers": (33.9535, -118.3390),
    
    # NFC East
    "Dallas Cowboys": (32.7473, -97.0945),
    "New York Giants": (40.8136, -74.0744),
    "Philadelphia Eagles": (39.9008, -75.1675),
    "Washington Commanders": (38.9076, -76.8645),
    
    # NFC North
    "Chicago Bears": (41.8623, -87.6167),
    "Detroit Lions": (42.3400, -83.0456),
    "Green Bay Packers": (44.5013, -88.0622),
    "Minnesota Vikings": (44.9740, -93.2577),
    
    # NFC South
    "Atlanta Falcons": (33.7555, -84.4009),
    "Carolina Panthers": (35.2258, -80.8530),
    "New Orleans Saints": (29.9511, -90.0812),
    "Tampa Bay Buccaneers": (27.9759, -82.5033),
    
    # NFC West
    "Arizona Cardinals": (33.5276, -112.2626),
    "Los Angeles Rams": (33.9535, -118.3390),
    "San Francisco 49ers": (37.4032, -121.9698),
    "Seattle Seahawks": (47.5952, -122.3316),
}

# NFL team time zones
NFL_TIME_ZONES = {
    # Eastern Time
    "Buffalo Bills": "ET",
    "Miami Dolphins": "ET",
    "New England Patriots": "ET",
    "New York Jets": "ET",
    "Baltimore Ravens": "ET",
    "Cincinnati Bengals": "ET",
    "Cleveland Browns": "ET",
    "Pittsburgh Steelers": "ET",
    "Jacksonville Jaguars": "ET",
    "Tennessee Titans": "ET",
    "Indianapolis Colts": "ET",
    "Dallas Cowboys": "ET",
    "New York Giants": "ET",
    "Philadelphia Eagles": "ET",
    "Washington Commanders": "ET",
    "Atlanta Falcons": "ET",
    "Carolina Panthers": "ET",
    "New Orleans Saints": "ET",
    "Tampa Bay Buccaneers": "ET",
    
    # Central Time
    "Chicago Bears": "CT",
    "Detroit Lions": "CT",
    "Green Bay Packers": "CT",
    "Minnesota Vikings": "CT",
    "Houston Texans": "CT",
    "Kansas City Chiefs": "CT",
    
    # Mountain Time
    "Denver Broncos": "MT",
    
    # Pacific Time
    "Las Vegas Raiders": "PT",
    "Los Angeles Chargers": "PT",
    "Los Angeles Rams": "PT",
    "San Francisco 49ers": "PT",
    "Seattle Seahawks": "PT",
    "Arizona Cardinals": "PT",  # No DST, but use PT for calculations
}


# ===== UTILITY FUNCTIONS =====

def great_circle_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate great circle distance between two points using Haversine formula.
    
    This is the accurate way to calculate distance on a sphere (Earth).
    
    Args:
        lat1: Latitude of point 1 (degrees)
        lon1: Longitude of point 1 (degrees)
        lat2: Latitude of point 2 (degrees)
        lon2: Longitude of point 2 (degrees)
        
    Returns:
        Distance in miles
        
    Formula:
        a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
        c = 2 × atan2(√a, √(1-a))
        distance = R × c
        
        where R = Earth's radius in miles (3,959)
        
    Examples:
        >>> # NYC to LA
        >>> great_circle_distance(40.7128, -74.0060, 34.0522, -118.2437)
        2451.0  # approximately
    """
    # Earth's radius in miles
    R = 3959.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance


def calculate_travel_distance(
    team: str,
    previous_location: str
) -> float:
    """
    Calculate travel distance between two NFL cities.
    
    Args:
        team: Team name (home city)
        previous_location: Previous game city
        
    Returns:
        Distance in miles (0 if same city or not found)
        
    Examples:
        >>> calculate_travel_distance("Kansas City Chiefs", "Miami Dolphins")
        1241.0  # approximately
    """
    if team not in NFL_CITIES or previous_location not in NFL_CITIES:
        logger.warning(
            f"City not found: {team} or {previous_location}"
        )
        return 0.0
    
    if team == previous_location:
        return 0.0
    
    lat1, lon1 = NFL_CITIES[team]
    lat2, lon2 = NFL_CITIES[previous_location]
    
    return great_circle_distance(lat1, lon1, lat2, lon2)


def classify_time_zones(
    team: str,
    game_location: str
) -> int:
    """
    Calculate number of time zones crossed.
    
    Args:
        team: Team name
        game_location: Game location team
        
    Returns:
        Number of time zones crossed (0-3)
        
    Time zone order: PT (0) → MT (1) → CT (2) → ET (3)
        
    Examples:
        >>> classify_time_zones("Seattle Seahawks", "Miami Dolphins")
        3  # PT to ET = 3 zones
        >>> classify_time_zones("Denver Broncos", "Kansas City Chiefs")
        1  # MT to CT = 1 zone
    """
    if team not in NFL_TIME_ZONES or game_location not in NFL_TIME_ZONES:
        logger.warning(
            f"Time zone not found: {team} or {game_location}"
        )
        return 0
    
    # Time zone ordering (west to east)
    tz_order = {"PT": 0, "MT": 1, "CT": 2, "ET": 3}
    
    team_tz = NFL_TIME_ZONES[team]
    game_tz = NFL_TIME_ZONES[game_location]
    
    team_order = tz_order.get(team_tz, 0)
    game_order = tz_order.get(game_tz, 0)
    
    return abs(game_order - team_order)


def calculate_schedule_density(
    game_dates: List[date],
    analysis_date: date,
    days_back: int = 14
) -> int:
    """
    Calculate number of games in last N days.
    
    Args:
        game_dates: List of game dates
        analysis_date: Date to analyze from
        days_back: Days to look back (default 14)
        
    Returns:
        Number of games in period
        
    Examples:
        >>> dates = [
        ...     date(2025, 11, 3),
        ...     date(2025, 11, 10),
        ...     date(2025, 11, 17)
        ... ]
        >>> calculate_schedule_density(dates, date(2025, 11, 20), days_back=14)
        2  # Two games in last 14 days
    """
    cutoff_date = analysis_date - timedelta(days=days_back)
    
    games_in_period = [
        d for d in game_dates
        if cutoff_date <= d < analysis_date
    ]
    
    return len(games_in_period)


def assess_schedule_strain(
    days_rest: int,
    travel_distance: float,
    time_zones_crossed: int,
    games_in_14_days: int,
    consecutive_away: int
) -> ScheduleStrain:
    """
    Assess overall schedule difficulty.
    
    Factors weighted:
    - Short rest (<6 days): Heavy penalty
    - Long travel (>1000 miles): Moderate penalty
    - Time zone crossing (2+): Heavy penalty
    - High density (3+ games in 14 days): Moderate penalty
    - Consecutive away (3+): Heavy penalty
    
    Args:
        days_rest: Days since last game
        travel_distance: Miles traveled
        time_zones_crossed: Time zones crossed (0-3)
        games_in_14_days: Games in last 14 days
        consecutive_away: Consecutive away games
        
    Returns:
        ScheduleStrain classification
        
    Examples:
        >>> assess_schedule_strain(
        ...     days_rest=5,
        ...     travel_distance=2500,
        ...     time_zones_crossed=3,
        ...     games_in_14_days=3,
        ...     consecutive_away=3
        ... )
        <ScheduleStrain.EXTREME: 'extreme'>
    """
    strain_score = 0
    
    # Rest penalty (short rest is tough)
    if days_rest < 6:
        strain_score += 2
    elif days_rest < 7:
        strain_score += 1
    
    # Travel penalty
    if travel_distance > 2000:
        strain_score += 2
    elif travel_distance > 1000:
        strain_score += 1
    
    # Time zone penalty (jet lag)
    if time_zones_crossed >= 2:
        strain_score += 2
    elif time_zones_crossed == 1:
        strain_score += 1
    
    # Density penalty (too many games)
    if games_in_14_days >= 3:
        strain_score += 2
    elif games_in_14_days >= 2:
        strain_score += 1
    
    # Consecutive away penalty (no home field)
    if consecutive_away >= 3:
        strain_score += 2
    elif consecutive_away >= 2:
        strain_score += 1
    
    # Classify strain
    if strain_score >= 7:
        return ScheduleStrain.EXTREME
    elif strain_score >= 5:
        return ScheduleStrain.HIGH
    elif strain_score >= 3:
        return ScheduleStrain.MODERATE
    else:
        return ScheduleStrain.LOW


# ===== SCHEDULE HISTORY CALCULATOR =====

@dataclass
class GameRecord:
    """Simple game record for schedule analysis"""
    date: date
    opponent: str
    is_home: bool
    location: str  # Team name (home team)


class ScheduleHistoryCalculator:
    """
    Calculate comprehensive schedule history for S-Factor analysis.
    
    Analyzes:
    - Rest days
    - Travel distance (great circle)
    - Time zones crossed
    - Schedule density
    - Consecutive away games
    - Overall schedule strain
    
    Usage:
        >>> calc = ScheduleHistoryCalculator()
        >>> history = calc.calculate(
        ...     team="Kansas City Chiefs",
        ...     current_date=date(2025, 11, 20),
        ...     team_games=[...],
        ...     team_home_location="Kansas City Chiefs"
        ... )
        >>> print(history.schedule_strain)
        ScheduleStrain.LOW
    """
    
    def __init__(self):
        """Initialize calculator"""
        self.nfl_cities = NFL_CITIES
        self.nfl_time_zones = NFL_TIME_ZONES
        logger.info("ScheduleHistoryCalculator initialized")
    
    def calculate(
        self,
        team: str,
        current_date: date,
        team_games: List[GameRecord],
        team_home_location: str,
        opponent_last_game_date: Optional[date] = None
    ) -> ScheduleHistory:
        """
        Calculate complete schedule history for a team.
        
        Args:
            team: Team name
            current_date: Date to analyze from (usually game date)
            team_games: List of team's recent games
            team_home_location: Team's home city
            opponent_last_game_date: Opponent's last game date (for rest comparison)
            
        Returns:
            Complete ScheduleHistory object
            
        Example:
            >>> calc = ScheduleHistoryCalculator()
            >>> games = [
            ...     GameRecord(
            ...         date=date(2025, 11, 13),
            ...         opponent="Buffalo Bills",
            ...         is_home=False,
            ...         location="Buffalo Bills"
            ...     )
            ... ]
            >>> history = calc.calculate(
            ...     team="Kansas City Chiefs",
            ...     current_date=date(2025, 11, 20),
            ...     team_games=games,
            ...     team_home_location="Kansas City Chiefs"
            ... )
            >>> history.days_since_last_game
            7
        """
        logger.info(f"Calculating schedule history for {team}")
        
        if not team_games:
            logger.warning(f"No games provided for {team}")
            return ScheduleHistory(days_since_last_game=0)
        
        # Sort games by date (most recent first)
        sorted_games = sorted(team_games, key=lambda g: g.date, reverse=True)
        last_game = sorted_games[0]
        
        # Calculate rest days
        days_rest = (current_date - last_game.date).days
        
        # Check for bye week (14 days rest indicates bye)
        coming_off_bye = days_rest >= 14
        
        # Calculate rest advantage vs opponent
        rest_advantage = None
        if opponent_last_game_date:
            opponent_rest = (current_date - opponent_last_game_date).days
            rest_advantage = days_rest - opponent_rest
        
        # Calculate travel distance
        previous_location = last_game.location
        travel_distance = calculate_travel_distance(
            team_home_location,
            previous_location
        )
        
        # Calculate time zones crossed
        time_zones = classify_time_zones(team_home_location, previous_location)
        
        # Count consecutive away games
        consecutive_away = 0
        for game in sorted_games:
            if not game.is_home:
                consecutive_away += 1
            else:
                break
        
        # Calculate schedule density
        game_dates = [g.date for g in team_games]
        games_14_days = calculate_schedule_density(
            game_dates,
            current_date,
            days_back=14
        )
        games_21_days = calculate_schedule_density(
            game_dates,
            current_date,
            days_back=21
        )
        
        # Create schedule history
        history = ScheduleHistory(
            days_since_last_game=days_rest,
            coming_off_bye=coming_off_bye,
            rest_advantage_vs_opponent=rest_advantage,
            previous_game_location=previous_location,
            travel_distance_miles=travel_distance,
            time_zones_crossed=time_zones,
            consecutive_away_games=consecutive_away,
            games_in_last_14_days=games_14_days,
            games_in_last_21_days=games_21_days
        )
        
        logger.info(
            f"Schedule history for {team}: "
            f"{days_rest}d rest, {travel_distance:.0f}mi travel, "
            f"strain={history.schedule_strain.value}"
        )
        
        return history
    
    def calculate_batch(
        self,
        teams_games: Dict[str, List[GameRecord]],
        analysis_date: date
    ) -> Dict[str, ScheduleHistory]:
        """
        Calculate schedule histories for multiple teams.
        
        Args:
            teams_games: Dict of {team_name: [games]}
            analysis_date: Date to analyze from
            
        Returns:
            Dict of {team_name: ScheduleHistory}
        """
        logger.info(f"Calculating batch schedule histories for {len(teams_games)} teams")
        
        histories = {}
        
        for team, games in teams_games.items():
            try:
                history = self.calculate(
                    team=team,
                    current_date=analysis_date,
                    team_games=games,
                    team_home_location=team
                )
                histories[team] = history
                
            except Exception as e:
                logger.error(f"Error calculating history for {team}: {e}")
                continue
        
        logger.info(f"Successfully calculated {len(histories)} schedule histories")
        
        return histories
    
    def validate_history(
        self,
        history: ScheduleHistory
    ) -> Tuple[bool, List[str]]:
        """
        Validate schedule history for reasonableness.
        
        Args:
            history: ScheduleHistory to validate
            
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        # Check rest days reasonable
        if history.days_since_last_game < 0:
            issues.append(f"Negative rest days: {history.days_since_last_game}")
        elif history.days_since_last_game > 21:
            issues.append(f"Excessive rest days: {history.days_since_last_game}")
        
        # Check travel distance reasonable
        if history.travel_distance_miles and history.travel_distance_miles < 0:
            issues.append(f"Negative travel distance: {history.travel_distance_miles}")
        elif history.travel_distance_miles and history.travel_distance_miles > 3500:
            issues.append(f"Excessive travel distance: {history.travel_distance_miles}")
        
        # Check time zones reasonable
        if not 0 <= history.time_zones_crossed <= 3:
            issues.append(f"Invalid time zones: {history.time_zones_crossed}")
        
        # Check density reasonable
        if history.games_in_last_14_days > 3:
            issues.append(f"Too many games in 14 days: {history.games_in_last_14_days}")
        
        is_valid = len(issues) == 0
        return is_valid, issues


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    """Example usage demonstrating the ScheduleHistoryCalculator"""
    
    print("Schedule History Calculator - Example Usage")
    print("=" * 70)
    
    # Example 1: Calculate single team history
    print("\n1. Single Team Schedule History")
    print("-" * 70)
    
    calc = ScheduleHistoryCalculator()
    
    # Kansas City Chiefs coming off away game at Buffalo
    chiefs_games = [
        GameRecord(
            date=date(2025, 11, 13),
            opponent="Buffalo Bills",
            is_home=False,
            location="Buffalo Bills"
        ),
        GameRecord(
            date=date(2025, 11, 6),
            opponent="Tampa Bay Buccaneers",
            is_home=True,
            location="Kansas City Chiefs"
        )
    ]
    
    chiefs_history = calc.calculate(
        team="Kansas City Chiefs",
        current_date=date(2025, 11, 20),
        team_games=chiefs_games,
        team_home_location="Kansas City Chiefs",
        opponent_last_game_date=date(2025, 11, 17)  # Opponent played Sunday
    )
    
    print("Kansas City Chiefs Schedule Analysis:")
    print(f"  Days Rest: {chiefs_history.days_since_last_game}")
    print(f"  Coming off Bye: {chiefs_history.coming_off_bye}")
    print(f"  Rest Advantage: {chiefs_history.rest_advantage_vs_opponent:+d} days")
    print(f"  Last Game: {chiefs_history.previous_game_location}")
    print(f"  Travel Distance: {chiefs_history.travel_distance_miles:.0f} miles")
    print(f"  Time Zones Crossed: {chiefs_history.time_zones_crossed}")
    print(f"  Consecutive Away: {chiefs_history.consecutive_away_games}")
    print(f"  Games in 14 days: {chiefs_history.games_in_last_14_days}")
    print(f"  Schedule Strain: {chiefs_history.schedule_strain.value.upper()}")
    print(f"  Has Rest Advantage: {chiefs_history.has_rest_advantage}")
    print(f"  Has Travel Disadvantage: {chiefs_history.has_travel_disadvantage}")
    
    # Validate
    is_valid, issues = calc.validate_history(chiefs_history)
    print(f"\n  Validation: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    
    # Example 2: Team with bye week
    print("\n\n2. Team Coming Off Bye Week")
    print("-" * 70)
    
    lions_games = [
        GameRecord(
            date=date(2025, 11, 6),
            opponent="Green Bay Packers",
            is_home=True,
            location="Detroit Lions"
        )
    ]
    
    lions_history = calc.calculate(
        team="Detroit Lions",
        current_date=date(2025, 11, 20),
        team_games=lions_games,
        team_home_location="Detroit Lions"
    )
    
    print("Detroit Lions Schedule Analysis:")
    print(f"  Days Rest: {lions_history.days_since_last_game}")
    print(f"  Coming off Bye: {lions_history.coming_off_bye}")
    print(f"  Schedule Strain: {lions_history.schedule_strain.value.upper()}")
    
    # Example 3: Distance calculations
    print("\n\n3. Distance Calculations")
    print("-" * 70)
    
    print("Sample NFL Travel Distances:")
    distances = [
        ("Seattle Seahawks", "Miami Dolphins"),
        ("New England Patriots", "Los Angeles Rams"),
        ("Kansas City Chiefs", "Tampa Bay Buccaneers"),
        ("Green Bay Packers", "Chicago Bears"),
    ]
    
    for team1, team2 in distances:
        dist = calculate_travel_distance(team1, team2)
        print(f"  {team1} → {team2}: {dist:.0f} miles")
    
    # Example 4: Time zone calculations
    print("\n\n4. Time Zone Crossings")
    print("-" * 70)
    
    print("Sample Time Zone Crossings:")
    tz_pairs = [
        ("Seattle Seahawks", "Miami Dolphins"),  # PT → ET
        ("Denver Broncos", "Kansas City Chiefs"),  # MT → CT
        ("New England Patriots", "Los Angeles Rams"),  # ET → PT
        ("Chicago Bears", "Green Bay Packers"),  # Same
    ]
    
    for team1, team2 in tz_pairs:
        zones = classify_time_zones(team1, team2)
        print(f"  {team1} → {team2}: {zones} zones")
    
    # Example 5: Schedule strain assessment
    print("\n\n5. Schedule Strain Assessment")
    print("-" * 70)
    
    print("Various Schedule Scenarios:")
    scenarios = [
        ("Easy", 7, 0, 0, 1, 0),
        ("Moderate", 6, 800, 1, 2, 1),
        ("High", 5, 1500, 2, 3, 2),
        ("Extreme", 4, 2500, 3, 3, 3),
    ]
    
    for name, rest, travel, tz, density, away in scenarios:
        strain = assess_schedule_strain(rest, travel, tz, density, away)
        print(f"  {name}: {strain.value.upper()}")
        print(f"    Rest={rest}d, Travel={travel}mi, TZ={tz}, Density={density}, Away={away}")
    
    print("\n" + "=" * 70)
    print("✓ All examples completed successfully!")
    print("\nScheduleHistoryCalculator is ready for use!")
    print("Next: Integration testing and Week 2 builders")
