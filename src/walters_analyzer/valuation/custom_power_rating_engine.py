"""
Custom Billy Walters Power Rating Engine

Builds proprietary power ratings from ESPN component data instead of relying
on Massey composite ratings. Uses the following components:

1. Offensive Efficiency: Points per game, yards per game, efficiency metrics
2. Defensive Efficiency: Points allowed, yards allowed, takeaways
3. Injury Impact: Position-specific injury burden differential
4. Team Momentum: Recent performance trends (win/loss streaks)
5. Home Field Advantage: Venue-specific historical data

This engine is designed to:
- Provide transparency in rating calculations
- Enable custom weighting of factors (Billy Walters formula)
- Track component contributions for analysis
- Scale appropriately for NFL (70-100) and NCAAF (60-105)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Tuple, List
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class League(Enum):
    """Supported sports leagues"""

    NFL = "NFL"
    NCAAF = "NCAAF"


@dataclass
class OffensiveMetrics:
    """Team offensive statistics"""

    points_per_game: Optional[float] = None
    total_yards_per_game: Optional[float] = None
    passing_yards_per_game: Optional[float] = None
    rushing_yards_per_game: Optional[float] = None
    completion_percentage: Optional[float] = None
    yards_per_attempt: Optional[float] = None
    touchdowns_passing: Optional[int] = None
    touchdowns_rushing: Optional[int] = None
    interceptions: Optional[int] = None
    fumbles: Optional[int] = None


@dataclass
class DefensiveMetrics:
    """Team defensive statistics"""

    points_allowed_per_game: Optional[float] = None
    yards_allowed_per_game: Optional[float] = None
    passing_yards_allowed_per_game: Optional[float] = None
    rushing_yards_allowed_per_game: Optional[float] = None
    sacks: Optional[int] = None
    interceptions_gained: Optional[int] = None
    fumbles_recovered: Optional[int] = None
    turnover_margin: Optional[float] = None
    third_down_percentage: Optional[float] = None
    fourth_down_percentage: Optional[float] = None
    red_zone_percentage: Optional[float] = None


@dataclass
class InjuryImpact:
    """Team injury burden assessment"""

    elite_players_out: int = 0  # Number of elite players unavailable
    starter_players_out: int = 0
    backup_players_out: int = 0
    total_impact_points: float = 0.0  # Sum of position-specific impacts
    injury_level: str = "HEALTHY"  # HEALTHY, MINOR, MODERATE, SEVERE


@dataclass
class TeamStatus:
    """Team recent performance and status"""

    wins: int = 0
    losses: int = 0
    streak_type: str = ""  # "W" or "L"
    streak_count: int = 0
    home_wins: int = 0
    home_losses: int = 0
    away_wins: int = 0
    away_losses: int = 0


@dataclass
class ComponentRating:
    """Individual component rating with explanation"""

    component: str
    rating_contribution: float
    percentage_weight: float
    explanation: str


@dataclass
class PowerRating:
    """Complete power rating with component breakdown"""

    team: str
    league: League
    overall_rating: float
    week: int
    season: int
    calculation_date: datetime

    # Component ratings
    offensive_rating: float
    defensive_rating: float
    injury_rating: float
    momentum_rating: float
    home_field_rating: float

    # Component weights
    offensive_weight: float = 0.30
    defensive_weight: float = 0.25
    injury_weight: float = 0.15
    momentum_weight: float = 0.15
    home_field_weight: float = 0.15

    # Detailed breakdown
    components: List[ComponentRating] = field(default_factory=list)

    # Comparison with Massey
    massey_rating: Optional[float] = None
    massey_differential: Optional[float] = None

    # Metadata
    data_source: str = "custom_espn"
    confidence_score: float = 1.0


class CustomPowerRatingEngine:
    """
    Generates custom power ratings from ESPN component data.

    Billy Walters Methodology:
    - Focus on information edges, not consensus
    - Weight recent performance more heavily
    - Account for injury impact on specific positions
    - Use home field advantage as regression factor
    - Compare against Massey as validation check

    Scales:
    - NFL: 70-100 (baseline ~85)
    - NCAAF: 60-105 (baseline ~80)
    """

    # NFL scales and constants
    NFL_RATING_MIN = 70.0
    NFL_RATING_MAX = 100.0
    NFL_RATING_BASELINE = 85.0
    NFL_HOME_FIELD_ADVANTAGE = 3.0  # Points advantage at home

    # NCAAF scales and constants
    NCAAF_RATING_MIN = 60.0
    NCAAF_RATING_MAX = 105.0
    NCAAF_RATING_BASELINE = 80.0
    NCAAF_HOME_FIELD_ADVANTAGE = 3.5  # Slightly higher in college

    # Position-specific injury impact values
    NFL_INJURY_IMPACTS = {
        "QB": {"ELITE": 4.5, "STARTER": 2.5, "BACKUP": 0.5},
        "RB": {"ELITE": 2.5, "STARTER": 1.5, "BACKUP": 0.3},
        "WR": {"ELITE": 1.8, "STARTER": 1.0, "BACKUP": 0.2},
        "TE": {"ELITE": 1.5, "STARTER": 0.8, "BACKUP": 0.1},
        "DE": {"ELITE": 1.5, "STARTER": 0.8, "BACKUP": 0.1},
        "DT": {"ELITE": 1.3, "STARTER": 0.7, "BACKUP": 0.1},
        "LB": {"ELITE": 1.2, "STARTER": 0.6, "BACKUP": 0.1},
        "CB": {"ELITE": 1.2, "STARTER": 0.6, "BACKUP": 0.1},
        "S": {"ELITE": 1.0, "STARTER": 0.5, "BACKUP": 0.1},
    }

    NCAAF_INJURY_IMPACTS = {
        "QB": {"ELITE": 5.0, "STARTER": 3.0, "BACKUP": 0.8},
        "RB": {"ELITE": 3.5, "STARTER": 2.0, "BACKUP": 0.5},
        "WR": {"ELITE": 2.5, "STARTER": 1.5, "BACKUP": 0.3},
        "TE": {"ELITE": 2.0, "STARTER": 1.2, "BACKUP": 0.2},
        "OL": {"ELITE": 1.5, "STARTER": 1.0, "BACKUP": 0.2},
        "DL": {"ELITE": 2.0, "STARTER": 1.2, "BACKUP": 0.2},
        "LB": {"ELITE": 1.8, "STARTER": 1.0, "BACKUP": 0.2},
        "DB": {"ELITE": 1.5, "STARTER": 0.8, "BACKUP": 0.1},
    }

    def __init__(self, league: League = League.NFL):
        """
        Initialize the custom power rating engine.

        Args:
            league: NFL or NCAAF
        """
        self.league = league
        self.ratings: Dict[str, PowerRating] = {}
        self.history: List[PowerRating] = []

        # Set league-specific constants
        if league == League.NFL:
            self.rating_min = self.NFL_RATING_MIN
            self.rating_max = self.NFL_RATING_MAX
            self.rating_baseline = self.NFL_RATING_BASELINE
            self.home_field_advantage = self.NFL_HOME_FIELD_ADVANTAGE
            self.injury_impacts = self.NFL_INJURY_IMPACTS
        else:
            self.rating_min = self.NCAAF_RATING_MIN
            self.rating_max = self.NCAAF_RATING_MAX
            self.rating_baseline = self.NCAAF_RATING_BASELINE
            self.home_field_advantage = self.NCAAF_HOME_FIELD_ADVANTAGE
            self.injury_impacts = self.NCAAF_INJURY_IMPACTS

    def calculate_offensive_rating(self, metrics: OffensiveMetrics) -> float:
        """
        Calculate offensive efficiency rating (0-100, baseline 50).

        Billy Walters principle: Recent offensive performance indicates team quality.

        Factors:
        - Points per game (primary indicator)
        - Yards per game (volume)
        - Efficiency metrics (completion %, yards per attempt)
        - TD:INT ratio (decision quality)

        Args:
            metrics: Offensive statistics

        Returns:
            Rating contribution (-15 to +15 points typically)
        """
        if not metrics.points_per_game:
            return 0.0

        # League-specific averages (2025 expected)
        if self.league == League.NFL:
            avg_ppg = 23.0
            avg_ypg = 350.0
        else:
            avg_ppg = 28.5  # College football higher scoring
            avg_ypg = 400.0

        # Points per game is primary (60% of offensive rating)
        ppg_differential = (metrics.points_per_game - avg_ppg) / avg_ppg
        ppg_rating = ppg_differential * 10.0  # Scale to -10 to +10 range

        # Yards per game secondary (40% of offensive rating)
        if metrics.total_yards_per_game:
            ypg_differential = (metrics.total_yards_per_game - avg_ypg) / avg_ypg
            ypg_rating = ypg_differential * 10.0  # Scale to -10 to +10 range
        else:
            ypg_rating = 0.0

        # Combined offensive rating
        offensive_rating = (ppg_rating * 0.6) + (ypg_rating * 0.4)

        logger.debug(
            f"Offensive Rating: PPG={metrics.points_per_game:.1f} "
            f"(diff={ppg_differential:.2%}), YPG={metrics.total_yards_per_game}, "
            f"Rating={offensive_rating:.1f}"
        )

        return round(offensive_rating, 1)

    def calculate_defensive_rating(self, metrics: DefensiveMetrics) -> float:
        """
        Calculate defensive efficiency rating.

        Billy Walters principle: Defense that prevents scores is valuable.

        Factors:
        - Points allowed per game (primary)
        - Yards allowed per game (volume)
        - Turnover margin (ball security advantage)

        Args:
            metrics: Defensive statistics

        Returns:
            Rating contribution (-15 to +15 points typically)
        """
        if not metrics.points_allowed_per_game:
            return 0.0

        # League-specific averages
        if self.league == League.NFL:
            avg_papg = 23.0
            avg_yapg = 350.0
        else:
            avg_papg = 28.5  # College football higher scoring
            avg_yapg = 400.0

        # Points allowed (60% of defensive rating) - lower is better
        papg_differential = (avg_papg - metrics.points_allowed_per_game) / avg_papg
        papg_rating = papg_differential * 10.0

        # Yards allowed (40% of defensive rating)
        if metrics.yards_allowed_per_game:
            yapg_differential = (avg_yapg - metrics.yards_allowed_per_game) / avg_yapg
            yapg_rating = yapg_differential * 10.0
        else:
            yapg_rating = 0.0

        defensive_rating = (papg_rating * 0.6) + (yapg_rating * 0.4)

        logger.debug(
            f"Defensive Rating: PAPG={metrics.points_allowed_per_game:.1f} "
            f"(advantage={papg_differential:.2%}), YAPG={metrics.yards_allowed_per_game}, "
            f"Rating={defensive_rating:.1f}"
        )

        return round(defensive_rating, 1)

    def calculate_injury_rating(self, injury: InjuryImpact) -> float:
        """
        Calculate injury impact on team rating.

        Billy Walters principle: Injuries to key positions significantly impact teams.

        Algorithm:
        - Each position has tier-specific impact values
        - Sum total impact points
        - Convert to rating adjustment (-10 to 0, lower is worse)

        Args:
            injury: Team injury assessment

        Returns:
            Rating adjustment (typically -5 to 0)
        """
        # Impact is negative (injuries hurt the team)
        injury_rating = -(injury.total_impact_points / 2.0)

        # Cap the injury impact
        injury_rating = max(injury_rating, -10.0)

        logger.debug(
            f"Injury Rating: {injury.elite_players_out} elite out, "
            f"{injury.starter_players_out} starters out, "
            f"Total impact={injury.total_impact_points:.1f}, "
            f"Rating adjustment={injury_rating:.1f}"
        )

        return round(injury_rating, 1)

    def calculate_momentum_rating(self, status: TeamStatus) -> float:
        """
        Calculate team momentum from recent performance.

        Billy Walters principle: Recent results indicate current team quality.

        Factors:
        - Current winning/losing streak (recent performance)
        - Win percentage (overall consistency)
        - Home/away split (venue-specific strength)

        Args:
            status: Team recent performance

        Returns:
            Rating adjustment (-5 to +5 typically)
        """
        momentum_rating = 0.0

        # Streak impact (most recent performance)
        if status.streak_type == "W":
            # Winning streak adds points
            streak_points = min(status.streak_count, 5) * 0.5  # 0.5 per win, capped
            momentum_rating += streak_points
        elif status.streak_type == "L":
            # Losing streak removes points
            streak_points = min(status.streak_count, 5) * 0.5  # 0.5 per loss, capped
            momentum_rating -= streak_points

        # Win percentage (consistency)
        if status.wins + status.losses > 0:
            win_pct = status.wins / (status.wins + status.losses)
            # Deviation from 50%: -5% to +5% rating impact
            momentum_rating += (win_pct - 0.5) * 10.0

        logger.debug(
            f"Momentum Rating: Streak={status.streak_type}{status.streak_count}, "
            f"Record={status.wins}-{status.losses}, "
            f"Rating adjustment={momentum_rating:.1f}"
        )

        return round(momentum_rating, 1)

    def calculate_home_field_rating(self) -> float:
        """
        Calculate home field advantage component.

        Billy Walters uses home field advantage as a baseline adjustment,
        not specific to individual teams.

        Returns:
            Home field advantage rating (typically 1.5-3.0 points)
        """
        # This is a constant for the league, applied contextually
        return self.home_field_advantage

    def calculate_overall_rating(
        self,
        team_name: str,
        offensive: OffensiveMetrics,
        defensive: DefensiveMetrics,
        injury: InjuryImpact,
        status: TeamStatus,
        week: int,
        season: int,
        massey_rating: Optional[float] = None,
    ) -> PowerRating:
        """
        Calculate complete power rating from all components.

        Weighting (Billy Walters Methodology):
        - Offensive Efficiency: 30% (what team scores)
        - Defensive Efficiency: 25% (what opponent scores)
        - Injury Impact: 15% (roster health)
        - Momentum: 15% (recent form)
        - Home Field: 15% (venue advantage)

        Args:
            team_name: Team name
            offensive: Offensive metrics
            defensive: Defensive metrics
            injury: Injury status
            status: Recent performance
            week: Current week
            season: Current season
            massey_rating: Massey rating for comparison

        Returns:
            Complete PowerRating object
        """
        # Calculate component ratings
        off_rating = self.calculate_offensive_rating(offensive)
        def_rating = self.calculate_defensive_rating(defensive)
        inj_rating = self.calculate_injury_rating(injury)
        mom_rating = self.calculate_momentum_rating(status)
        hf_rating = self.calculate_home_field_rating()

        # Apply weights
        weighted_rating = (
            (off_rating * 0.30)
            + (def_rating * 0.25)
            + (inj_rating * 0.15)
            + (mom_rating * 0.15)
            + (hf_rating * 0.15)
        )

        # Convert to team rating scale
        # Baseline is self.rating_baseline, weighted adjustments applied
        overall_rating = self.rating_baseline + weighted_rating

        # Constrain to league-specific range
        overall_rating = max(self.rating_min, min(self.rating_max, overall_rating))

        # Calculate Massey differential if provided
        massey_diff = None
        if massey_rating:
            massey_diff = overall_rating - massey_rating

        # Create component breakdown
        components = [
            ComponentRating(
                component="Offensive Efficiency",
                rating_contribution=off_rating,
                percentage_weight=0.30,
                explanation=f"PPG: {offensive.points_per_game}, "
                f"YPG: {offensive.total_yards_per_game}",
            ),
            ComponentRating(
                component="Defensive Efficiency",
                rating_contribution=def_rating,
                percentage_weight=0.25,
                explanation=f"PAPG: {defensive.points_allowed_per_game}, "
                f"YAPG: {defensive.yards_allowed_per_game}",
            ),
            ComponentRating(
                component="Injury Impact",
                rating_contribution=inj_rating,
                percentage_weight=0.15,
                explanation=f"Elite out: {injury.elite_players_out}, "
                f"Total impact: {injury.total_impact_points:.1f}",
            ),
            ComponentRating(
                component="Momentum",
                rating_contribution=mom_rating,
                percentage_weight=0.15,
                explanation=f"Streak: {status.streak_type}{status.streak_count}, "
                f"Record: {status.wins}-{status.losses}",
            ),
            ComponentRating(
                component="Home Field Advantage",
                rating_contribution=hf_rating,
                percentage_weight=0.15,
                explanation=f"{hf_rating:.1f} point advantage",
            ),
        ]

        power_rating = PowerRating(
            team=team_name,
            league=self.league,
            overall_rating=round(overall_rating, 2),
            week=week,
            season=season,
            calculation_date=datetime.now(),
            offensive_rating=off_rating,
            defensive_rating=def_rating,
            injury_rating=inj_rating,
            momentum_rating=mom_rating,
            home_field_rating=hf_rating,
            components=components,
            massey_rating=massey_rating,
            massey_differential=round(massey_diff, 2) if massey_diff else None,
        )

        logger.info(
            f"Calculated rating for {team_name}: {overall_rating:.2f} "
            f"(Off={off_rating:+.1f}, Def={def_rating:+.1f}, "
            f"Inj={inj_rating:+.1f}, Mom={mom_rating:+.1f})"
        )

        return power_rating

    def calculate_spread(
        self, home_team: str, away_team: str, include_home_field: bool = True
    ) -> Optional[float]:
        """
        Calculate predicted spread between two teams.

        Spread = Home Rating - Away Rating + Home Field Advantage

        Args:
            home_team: Home team name
            away_team: Away team name
            include_home_field: Whether to include home field advantage

        Returns:
            Predicted spread (positive = home favored) or None if teams not found
        """
        home_rating = self.ratings.get(home_team)
        away_rating = self.ratings.get(away_team)

        if not home_rating or not away_rating:
            logger.warning(
                f"Cannot calculate spread: "
                f"{home_team if not home_rating else away_team} not found"
            )
            return None

        spread = home_rating.overall_rating - away_rating.overall_rating

        if include_home_field:
            spread += self.home_field_advantage

        return round(spread, 1)

    def store_rating(self, rating: PowerRating) -> None:
        """Store a calculated rating."""
        self.ratings[rating.team] = rating
        self.history.append(rating)
        logger.debug(f"Stored rating for {rating.team}: {rating.overall_rating}")

    def get_rating(self, team_name: str) -> Optional[PowerRating]:
        """Retrieve a stored rating."""
        return self.ratings.get(team_name)

    def get_top_teams(self, n: int = 10) -> List[PowerRating]:
        """Get top N teams by overall rating."""
        sorted_ratings = sorted(
            self.ratings.values(), key=lambda x: x.overall_rating, reverse=True
        )
        return sorted_ratings[:n]

    def get_bottom_teams(self, n: int = 10) -> List[PowerRating]:
        """Get bottom N teams by overall rating."""
        sorted_ratings = sorted(self.ratings.values(), key=lambda x: x.overall_rating)
        return sorted_ratings[:n]

    def compare_with_massey(self) -> Dict[str, Dict]:
        """
        Generate comparison report between custom and Massey ratings.

        Returns:
            Dictionary with comparison statistics and outliers
        """
        comparison = {
            "ratings_count": len([r for r in self.ratings.values() if r.massey_rating]),
            "average_differential": 0.0,
            "max_positive_diff": None,
            "max_negative_diff": None,
            "outliers": [],
        }

        diffs = []
        for rating in self.ratings.values():
            if rating.massey_differential:
                diffs.append(rating.massey_differential)

                # Track outliers (>2 point difference)
                if abs(rating.massey_differential) > 2.0:
                    comparison["outliers"].append(
                        {
                            "team": rating.team,
                            "custom": rating.overall_rating,
                            "massey": rating.massey_rating,
                            "difference": rating.massey_differential,
                        }
                    )

        if diffs:
            comparison["average_differential"] = round(sum(diffs) / len(diffs), 2)
            comparison["max_positive_diff"] = max(diffs)
            comparison["max_negative_diff"] = min(diffs)

        return comparison
