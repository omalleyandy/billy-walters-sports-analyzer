"""
S-Factor Data Collection Module
================================

This module contains builders and calculators for gathering and processing
team and game data for S-Factor analysis.

Components:
- TeamContextBuilder: Builds team profiles from Massey + ESPN
- ScheduleHistoryCalculator: Analyzes rest, travel, and schedule density
"""

from .team_context_builder import (
    TeamContextBuilder,
    classify_recent_performance,
    calculate_schedule_difficulty
)

from .schedule_history_calculator import (
    ScheduleHistoryCalculator,
    GameRecord,
    great_circle_distance,
    calculate_travel_distance,
    classify_time_zones,
    calculate_schedule_density,
    assess_schedule_strain
)

__all__ = [
    # Team Context Builder
    "TeamContextBuilder",
    "classify_recent_performance",
    "calculate_schedule_difficulty",
    
    # Schedule History Calculator
    "ScheduleHistoryCalculator",
    "GameRecord",
    "great_circle_distance",
    "calculate_travel_distance",
    "classify_time_zones",
    "calculate_schedule_density",
    "assess_schedule_strain",
]
