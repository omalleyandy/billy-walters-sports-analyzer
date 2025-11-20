#!/usr/bin/env python3
"""
Team Context Builder - Billy Walters S-Factor System
====================================================

Builds comprehensive team profiles by combining:
- Massey Ratings (power ratings, rankings)
- ESPN Stats (records, performance metrics)
- Schedule analysis (strength, remaining games)

Creates validated TeamContext objects ready for S-Factor calculations.

Version: 1.0
Created: November 20, 2025
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from pathlib import Path

from walters_analyzer.models.sfactor_data_models import (
    TeamContext,
    Record,
    TeamQualityTier,
    classify_quality_tier
)

logger = logging.getLogger(__name__)


# ===== HELPER FUNCTIONS =====

def classify_recent_performance(
    last_5_record: Record,
    current_streak: Optional[str] = None
) -> str:
    """
    Classify team's recent performance trend.
    
    Args:
        last_5_record: Record over last 5 games
        current_streak: Current streak (e.g., "W3", "L2")
        
    Returns:
        Performance classification: "hot", "trending_up", "neutral", 
        "trending_down", "cold"
        
    Examples:
        >>> classify_recent_performance(Record(wins=5, losses=0))
        'hot'
        >>> classify_recent_performance(Record(wins=0, losses=5))
        'cold'
        >>> classify_recent_performance(Record(wins=3, losses=2))
        'neutral'
    """
    win_pct = last_5_record.win_percentage
    
    # Hot: 4-1 or better
    if win_pct >= 0.8:
        return "hot"
    
    # Cold: 1-4 or worse
    elif win_pct <= 0.2:
        return "cold"
    
    # Trending: 3-2 or 2-3 with streak context
    elif 0.5 < win_pct < 0.8:
        if current_streak and current_streak.startswith("W"):
            return "trending_up"
        return "neutral"
    
    elif 0.2 < win_pct <= 0.5:
        if current_streak and current_streak.startswith("L"):
            return "trending_down"
        return "neutral"
    
    else:
        return "neutral"


def calculate_schedule_difficulty(
    opponents_power_ratings: List[float]
) -> float:
    """
    Calculate strength of schedule from opponent power ratings.
    
    Args:
        opponents_power_ratings: List of opponent power ratings
        
    Returns:
        Average opponent power rating (strength of schedule)
        
    Examples:
        >>> calculate_schedule_difficulty([8.5, 7.2, 9.0, 6.5])
        7.8
    """
    if not opponents_power_ratings:
        return 0.0
    
    return sum(opponents_power_ratings) / len(opponents_power_ratings)


# ===== TEAM CONTEXT BUILDER =====

class TeamContextBuilder:
    """
    Builds comprehensive team profiles from multiple data sources.
    
    This class orchestrates data collection and validation to produce
    complete TeamContext objects ready for S-Factor analysis.
    
    Data Sources:
    - Massey Ratings: Power ratings, rankings
    - ESPN: Records, statistics, schedules
    
    Usage:
        >>> builder = TeamContextBuilder()
        >>> context = builder.build_context(
        ...     team_name="Kansas City Chiefs",
        ...     power_rating=9.2,
        ...     espn_record={"wins": 10, "losses": 1}
        ... )
        >>> print(context.quality_tier)
        TeamQualityTier.ELITE
    """
    
    def __init__(
        self,
        massey_data: Optional[Dict[str, Any]] = None,
        espn_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize builder with optional pre-loaded data.
        
        Args:
            massey_data: Pre-loaded Massey ratings data
            espn_data: Pre-loaded ESPN statistics data
        """
        self.massey_data = massey_data or {}
        self.espn_data = espn_data or {}
        
        logger.info("TeamContextBuilder initialized")
    
    def build_context(
        self,
        team_name: str,
        power_rating: float,
        power_rating_rank: Optional[int] = None,
        espn_record: Optional[Dict[str, int]] = None,
        espn_conference: Optional[str] = None,
        espn_division: Optional[str] = None,
        espn_stats: Optional[Dict[str, float]] = None,
        last_5_record: Optional[Dict[str, int]] = None,
        current_streak: Optional[str] = None,
        strength_of_schedule: Optional[float] = None,
        games_remaining: Optional[int] = None
    ) -> TeamContext:
        """
        Build a complete team context from provided data.
        
        Args:
            team_name: Full team name (e.g., "Kansas City Chiefs")
            power_rating: Billy Walters power rating (-10 to +10)
            power_rating_rank: Rank among all teams (1=best)
            espn_record: Overall record {"wins": X, "losses": Y, "ties": Z}
            espn_conference: Conference (AFC/NFC)
            espn_division: Division (e.g., "AFC West")
            espn_stats: Stats dict with "ppg", "papg", "point_diff"
            last_5_record: Last 5 games record
            current_streak: Current streak (e.g., "W3", "L2")
            strength_of_schedule: Average opponent rating
            games_remaining: Games left in season
            
        Returns:
            Complete validated TeamContext object
            
        Raises:
            ValueError: If power_rating out of range or team_name empty
            
        Example:
            >>> builder = TeamContextBuilder()
            >>> context = builder.build_context(
            ...     team_name="Kansas City Chiefs",
            ...     power_rating=9.2,
            ...     power_rating_rank=1,
            ...     espn_record={"wins": 10, "losses": 1},
            ...     espn_conference="AFC",
            ...     espn_division="AFC West",
            ...     espn_stats={"ppg": 28.5, "papg": 19.2, "point_diff": 9.3}
            ... )
            >>> context.quality_tier
            <TeamQualityTier.ELITE: 'elite'>
        """
        
        logger.info(f"Building context for {team_name}")
        
        # Validate inputs
        if not team_name or not team_name.strip():
            raise ValueError("team_name cannot be empty")
        
        if not -10.0 <= power_rating <= 10.0:
            raise ValueError(f"power_rating {power_rating} out of range [-10, +10]")
        
        # Extract team abbreviation (last word typically)
        team_abbrev = team_name.split()[-1].upper()[:3]
        
        # Build overall record
        overall_record = Record(
            wins=espn_record.get("wins", 0) if espn_record else 0,
            losses=espn_record.get("losses", 0) if espn_record else 0,
            ties=espn_record.get("ties", 0) if espn_record else 0
        )
        
        # Build performance stats
        ppg = None
        papg = None
        point_diff = None
        
        if espn_stats:
            ppg = espn_stats.get("ppg")
            papg = espn_stats.get("papg")
            point_diff = espn_stats.get("point_diff")
        
        # Build last 5 record
        last_5 = None
        if last_5_record:
            last_5 = Record(
                wins=last_5_record.get("wins", 0),
                losses=last_5_record.get("losses", 0),
                ties=last_5_record.get("ties", 0)
            )
        
        # Create context
        context = TeamContext(
            team_name=team_name.strip(),
            team_abbrev=team_abbrev,
            conference=espn_conference,
            division=espn_division,
            power_rating=power_rating,
            power_rating_rank=power_rating_rank,
            overall_record=overall_record,
            points_per_game=ppg,
            points_allowed_per_game=papg,
            point_differential=point_diff,
            last_5_record=last_5,
            current_streak=current_streak,
            strength_of_schedule=strength_of_schedule,
            games_remaining=games_remaining,
            data_source="massey_espn"
        )
        
        logger.info(
            f"Built context for {team_name}: "
            f"Rating={power_rating:.1f}, Tier={context.quality_tier.value}"
        )
        
        return context
    
    def build_contexts_from_massey_and_espn(
        self,
        massey_ratings: Dict[str, Dict[str, Any]],
        espn_teams: Dict[str, Dict[str, Any]]
    ) -> List[TeamContext]:
        """
        Build contexts for all teams from Massey and ESPN data.
        
        This is the batch processing method that builds contexts for
        all 32 NFL teams at once.
        
        Args:
            massey_ratings: Dict of {team_name: {rating: float, rank: int}}
            espn_teams: Dict of {team_name: {record: {}, stats: {}, etc.}}
            
        Returns:
            List of TeamContext objects, one per team
            
        Example:
            >>> massey = {
            ...     "Kansas City Chiefs": {"rating": 9.2, "rank": 1},
            ...     "Buffalo Bills": {"rating": 8.5, "rank": 2}
            ... }
            >>> espn = {
            ...     "Kansas City Chiefs": {
            ...         "record": {"wins": 10, "losses": 1},
            ...         "conference": "AFC",
            ...         "division": "AFC West",
            ...         "stats": {"ppg": 28.5, "papg": 19.2}
            ...     },
            ...     "Buffalo Bills": {
            ...         "record": {"wins": 9, "losses": 2},
            ...         "conference": "AFC",
            ...         "division": "AFC East",
            ...         "stats": {"ppg": 27.0, "papg": 20.5}
            ...     }
            ... }
            >>> builder = TeamContextBuilder()
            >>> contexts = builder.build_contexts_from_massey_and_espn(massey, espn)
            >>> len(contexts)
            2
        """
        
        logger.info(
            f"Building contexts for {len(massey_ratings)} teams from batch data"
        )
        
        contexts = []
        errors = []
        
        for team_name, massey_info in massey_ratings.items():
            try:
                # Get ESPN data for this team
                espn_info = espn_teams.get(team_name, {})
                
                # Build context
                context = self.build_context(
                    team_name=team_name,
                    power_rating=massey_info.get("rating", 0.0),
                    power_rating_rank=massey_info.get("rank"),
                    espn_record=espn_info.get("record"),
                    espn_conference=espn_info.get("conference"),
                    espn_division=espn_info.get("division"),
                    espn_stats=espn_info.get("stats"),
                    last_5_record=espn_info.get("last_5"),
                    current_streak=espn_info.get("streak"),
                    strength_of_schedule=espn_info.get("sos"),
                    games_remaining=espn_info.get("games_remaining")
                )
                
                contexts.append(context)
                
            except Exception as e:
                error_msg = f"Failed to build context for {team_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        logger.info(f"Successfully built {len(contexts)} contexts")
        if errors:
            logger.warning(f"Encountered {len(errors)} errors during batch build")
        
        return contexts
    
    def validate_context(self, context: TeamContext) -> Tuple[bool, List[str]]:
        """
        Validate a team context for completeness and quality.
        
        Checks:
        - Power rating is valid
        - Record exists
        - Quality tier calculated correctly
        - Stats are reasonable (if present)
        
        Args:
            context: TeamContext to validate
            
        Returns:
            Tuple of (is_valid: bool, issues: List[str])
            
        Example:
            >>> builder = TeamContextBuilder()
            >>> context = builder.build_context(
            ...     team_name="Kansas City Chiefs",
            ...     power_rating=9.2,
            ...     espn_record={"wins": 10, "losses": 1}
            ... )
            >>> is_valid, issues = builder.validate_context(context)
            >>> is_valid
            True
            >>> issues
            []
        """
        
        issues = []
        
        # Check power rating
        if context.power_rating < -10 or context.power_rating > 10:
            issues.append(f"Invalid power rating: {context.power_rating}")
        
        # Check quality tier matches rating
        expected_tier = classify_quality_tier(context.power_rating)
        if context.quality_tier != expected_tier:
            issues.append(
                f"Quality tier mismatch: got {context.quality_tier}, "
                f"expected {expected_tier}"
            )
        
        # Check record exists
        if context.overall_record.total_games == 0:
            issues.append("No games played (record is 0-0)")
        
        # Check stats are reasonable (if present)
        if context.points_per_game is not None:
            if context.points_per_game < 0 or context.points_per_game > 60:
                issues.append(f"Unreasonable PPG: {context.points_per_game}")
        
        if context.points_allowed_per_game is not None:
            if context.points_allowed_per_game < 0 or context.points_allowed_per_game > 60:
                issues.append(f"Unreasonable PA/G: {context.points_allowed_per_game}")
        
        # Check win percentage is calculated correctly
        expected_win_pct = (
            context.overall_record.wins / context.overall_record.total_games
            if context.overall_record.total_games > 0
            else 0.0
        )
        actual_win_pct = context.overall_record.win_percentage
        if abs(expected_win_pct - actual_win_pct) > 0.01:
            issues.append(
                f"Win % calculation error: got {actual_win_pct:.3f}, "
                f"expected {expected_win_pct:.3f}"
            )
        
        is_valid = len(issues) == 0
        
        if is_valid:
            logger.info(f"Context validation passed for {context.team_name}")
        else:
            logger.warning(
                f"Context validation failed for {context.team_name}: "
                f"{len(issues)} issues"
            )
        
        return is_valid, issues
    
    def _estimate_power_rank(
        self,
        power_rating: float,
        all_ratings: List[float]
    ) -> int:
        """
        Estimate power rank if not provided.
        
        Args:
            power_rating: Team's power rating
            all_ratings: List of all team power ratings
            
        Returns:
            Estimated rank (1-32)
        """
        sorted_ratings = sorted(all_ratings, reverse=True)
        
        try:
            rank = sorted_ratings.index(power_rating) + 1
        except ValueError:
            # Rating not in list, find where it would fit
            rank = len([r for r in sorted_ratings if r > power_rating]) + 1
        
        return rank


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    """Example usage demonstrating the TeamContextBuilder"""
    
    print("Team Context Builder - Example Usage")
    print("=" * 70)
    
    # Example 1: Build single team context
    print("\n1. Building Single Team Context")
    print("-" * 70)
    
    builder = TeamContextBuilder()
    
    chiefs_context = builder.build_context(
        team_name="Kansas City Chiefs",
        power_rating=9.2,
        power_rating_rank=1,
        espn_record={"wins": 10, "losses": 1},
        espn_conference="AFC",
        espn_division="AFC West",
        espn_stats={
            "ppg": 28.5,
            "papg": 19.2,
            "point_diff": 9.3
        },
        last_5_record={"wins": 4, "losses": 1},
        current_streak="W3",
        strength_of_schedule=5.2,
        games_remaining=6
    )
    
    print(f"✓ Team: {chiefs_context.team_name}")
    print(f"  Power Rating: {chiefs_context.power_rating}")
    print(f"  Rank: #{chiefs_context.power_rating_rank}")
    print(f"  Quality Tier: {chiefs_context.quality_tier.value.title()}")
    print(f"  Record: {chiefs_context.overall_record}")
    print(f"  Win %: {chiefs_context.overall_record.win_percentage:.1%}")
    print(f"  PPG: {chiefs_context.points_per_game}")
    print(f"  PA/G: {chiefs_context.points_allowed_per_game}")
    print(f"  Offensive Quality: {chiefs_context.offensive_quality}")
    print(f"  Defensive Quality: {chiefs_context.defensive_quality}")
    print(f"  Is Elite: {chiefs_context.is_elite}")
    print(f"  Is Playoff Team: {chiefs_context.is_playoff_team}")
    
    # Validate context
    is_valid, issues = builder.validate_context(chiefs_context)
    print(f"\n  Validation: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    if issues:
        for issue in issues:
            print(f"    - {issue}")
    
    # Example 2: Batch build from sample data
    print("\n\n2. Batch Building Multiple Teams")
    print("-" * 70)
    
    massey_sample = {
        "Kansas City Chiefs": {"rating": 9.2, "rank": 1},
        "Buffalo Bills": {"rating": 8.5, "rank": 2},
        "San Francisco 49ers": {"rating": 8.0, "rank": 3},
        "Detroit Lions": {"rating": 7.5, "rank": 4},
        "Miami Dolphins": {"rating": 6.8, "rank": 5}
    }
    
    espn_sample = {
        "Kansas City Chiefs": {
            "record": {"wins": 10, "losses": 1},
            "conference": "AFC",
            "division": "AFC West",
            "stats": {"ppg": 28.5, "papg": 19.2, "point_diff": 9.3}
        },
        "Buffalo Bills": {
            "record": {"wins": 9, "losses": 2},
            "conference": "AFC",
            "division": "AFC East",
            "stats": {"ppg": 27.0, "papg": 20.5, "point_diff": 6.5}
        },
        "San Francisco 49ers": {
            "record": {"wins": 8, "losses": 3},
            "conference": "NFC",
            "division": "NFC West",
            "stats": {"ppg": 26.5, "papg": 21.0, "point_diff": 5.5}
        },
        "Detroit Lions": {
            "record": {"wins": 8, "losses": 3},
            "conference": "NFC",
            "division": "NFC North",
            "stats": {"ppg": 29.0, "papg": 22.5, "point_diff": 6.5}
        },
        "Miami Dolphins": {
            "record": {"wins": 6, "losses": 5},
            "conference": "AFC",
            "division": "AFC East",
            "stats": {"ppg": 24.5, "papg": 23.0, "point_diff": 1.5}
        }
    }
    
    contexts = builder.build_contexts_from_massey_and_espn(
        massey_sample,
        espn_sample
    )
    
    print(f"✓ Built {len(contexts)} team contexts\n")
    
    # Show summary
    print("Team Quality Distribution:")
    tier_counts = {}
    for ctx in contexts:
        tier = ctx.quality_tier.value
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    for tier, count in sorted(tier_counts.items()):
        print(f"  {tier.title()}: {count} teams")
    
    # Example 3: Helper functions
    print("\n\n3. Helper Functions")
    print("-" * 70)
    
    # Recent performance
    hot_team = Record(wins=5, losses=0)
    cold_team = Record(wins=1, losses=4)
    neutral_team = Record(wins=3, losses=2)
    
    print("Recent Performance Classification:")
    print(f"  5-0: {classify_recent_performance(hot_team)}")
    print(f"  1-4: {classify_recent_performance(cold_team)}")
    print(f"  3-2: {classify_recent_performance(neutral_team)}")
    
    # Schedule difficulty
    tough_schedule = [9.0, 8.5, 7.8, 8.2, 7.5]
    easy_schedule = [3.0, 2.5, 4.0, 3.5, 2.0]
    
    print("\nStrength of Schedule:")
    print(f"  Tough: {calculate_schedule_difficulty(tough_schedule):.1f}")
    print(f"  Easy: {calculate_schedule_difficulty(easy_schedule):.1f}")
    
    print("\n" + "=" * 70)
    print("✓ All examples completed successfully!")
    print("\nTeamContextBuilder is ready for use!")
    print("Next: Create ScheduleHistoryCalculator (Task 1.3)")
