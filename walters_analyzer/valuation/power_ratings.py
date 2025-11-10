"""
Billy Walters Power Rating System
Implements the exact 90/10 power rating update formula

New Rating = (0.90 × Old Rating) + (0.10 × True Game Performance Level)

Where True Game Performance =
    Net Score
    + Opponent Rating
    + Injury Differential
    - Home Field Adjustment

Reference: Billy Walters Analytics PRD v1.5, Lines 278-335
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Team:
    """Represents a team with its power rating"""

    name: str
    power_rating: float
    league: str = "NFL"

    def __post_init__(self):
        """Normalize team name"""
        self.name = self.name.strip()


@dataclass
class GameResult:
    """Represents a completed game result for rating updates"""

    date: date
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_injury_level: float = 0.0
    away_injury_level: float = 0.0
    location: str = "home"  # "home", "away", "neutral"

    @property
    def winner(self) -> str:
        """Return the winning team name"""
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return "TIE"

    @property
    def margin(self) -> int:
        """Return margin of victory (positive = home win)"""
        return self.home_score - self.away_score


class PowerRatingSystem:
    """
    Implements Billy Walters' exact power rating update formula

    Constants from Billy Walters methodology:
    - 90% weight on previous rating (continuity)
    - 10% weight on last game performance (responsiveness)
    - 2.0 points home field advantage (standard)

    Usage:
        >>> prs = PowerRatingSystem()
        >>> prs.set_rating("Kansas City", 12.5)
        >>> prs.set_rating("Buffalo", 11.0)
        >>> result = GameResult(
        ...     date=date.today(),
        ...     home_team="Kansas City",
        ...     away_team="Buffalo",
        ...     home_score=27,
        ...     away_score=24
        ... )
        >>> prs.update_ratings_from_game(result)
        >>> print(prs.get_rating("Kansas City"))
        12.62
    """

    # Constants from Billy Walters methodology
    OLD_RATING_WEIGHT = 0.90  # 90% weight on previous rating
    TRUE_PERFORMANCE_WEIGHT = 0.10  # 10% weight on last game
    HOME_FIELD_ADVANTAGE = 2.0  # Standard home field points

    def __init__(self, ratings_file: Optional[Path] = None):
        """
        Initialize the Power Rating System

        Args:
            ratings_file: Optional path to JSON file for persistent storage
        """
        self.ratings: Dict[str, float] = {}
        self.history: List[Dict] = []
        self.ratings_file = ratings_file

        # Load existing ratings if file provided
        if ratings_file and ratings_file.exists():
            self.load_ratings(ratings_file)

    def set_rating(self, team: str, rating: float) -> None:
        """
        Set or update a team's power rating

        Args:
            team: Team name
            rating: Power rating value
        """
        team = self._normalize_team_name(team)
        self.ratings[team] = round(rating, 2)
        logger.debug(f"Set {team} rating to {rating:.2f}")

    def get_rating(self, team: str) -> Optional[float]:
        """
        Get a team's current power rating

        Args:
            team: Team name

        Returns:
            Current power rating or None if team not found
        """
        team = self._normalize_team_name(team)
        return self.ratings.get(team)

    def update_power_rating(
        self, team: Team, opponent: Team, game_result: GameResult
    ) -> float:
        """
        Update power rating using Billy Walters' exact formula

        Formula:
            New Rating = 90% of Old Rating + 10% of True Game Performance Level

        True Game Performance Level =
            Net Score +
            Opponent Rating +
            Injury Differential +
            Home Field Adjustment

        Example from PRD:
            Bears beat Vikings 27-20 on neutral field
            Bears injuries: 3.5, Vikings injuries: 1.7
            Bears old rating: 10, Vikings old rating: 4

            True Performance = 7 + 4 + (3.5 - 1.7) = 12.8
            New Rating = 0.9(10) + 0.1(12.8) = 10.28

        Args:
            team: Team object with current rating
            opponent: Opponent Team object
            game_result: GameResult with scores and context

        Returns:
            New power rating for the team
        """
        # Determine if this team is home or away
        is_home = game_result.home_team == team.name

        # Calculate net score from team's perspective
        if is_home:
            net_score = game_result.home_score - game_result.away_score
            team_injury = game_result.home_injury_level
            opp_injury = game_result.away_injury_level
        else:
            net_score = game_result.away_score - game_result.home_score
            team_injury = game_result.away_injury_level
            opp_injury = game_result.home_injury_level

        # Get opponent rating
        opponent_rating = opponent.power_rating

        # Calculate injury differential (positive = team was more injured)
        injury_differential = team_injury - opp_injury

        # Adjust for home field advantage
        home_adjustment = 0.0
        if game_result.location == "home":
            if is_home:
                # This team had home advantage, subtract it
                home_adjustment = -self.HOME_FIELD_ADVANTAGE
            else:
                # Opponent had home advantage, add it
                home_adjustment = self.HOME_FIELD_ADVANTAGE
        elif game_result.location == "away":
            if is_home:
                # Opponent had home advantage, add it
                home_adjustment = self.HOME_FIELD_ADVANTAGE
            else:
                # This team had home advantage, subtract it
                home_adjustment = -self.HOME_FIELD_ADVANTAGE
        # If neutral, home_adjustment stays 0.0

        # Calculate True Game Performance Level
        true_performance = (
            net_score + opponent_rating + injury_differential + home_adjustment
        )

        # Apply 90/10 formula
        new_rating = (
            self.OLD_RATING_WEIGHT * team.power_rating
            + self.TRUE_PERFORMANCE_WEIGHT * true_performance
        )

        logger.debug(
            f"{team.name} rating update: "
            f"net_score={net_score}, opp_rating={opponent_rating:.1f}, "
            f"inj_diff={injury_differential:.1f}, home_adj={home_adjustment:.1f}, "
            f"true_perf={true_performance:.1f}, "
            f"old={team.power_rating:.2f} → new={new_rating:.2f}"
        )

        return round(new_rating, 2)

    def update_ratings_from_game(self, game_result: GameResult) -> Tuple[float, float]:
        """
        Update ratings for both teams from a game result

        Args:
            game_result: Completed game with scores

        Returns:
            Tuple of (home_new_rating, away_new_rating)
        """
        home_name = self._normalize_team_name(game_result.home_team)
        away_name = self._normalize_team_name(game_result.away_team)

        # Get current ratings (default to 0.0 if team not found)
        home_rating = self.ratings.get(home_name, 0.0)
        away_rating = self.ratings.get(away_name, 0.0)

        # Create team objects
        home_team = Team(name=home_name, power_rating=home_rating)
        away_team = Team(name=away_name, power_rating=away_rating)

        # Update home team rating
        home_new = self.update_power_rating(home_team, away_team, game_result)

        # Update away team rating
        away_new = self.update_power_rating(away_team, home_team, game_result)

        # Store new ratings
        self.ratings[home_name] = home_new
        self.ratings[away_name] = away_new

        # Record in history
        self.history.append(
            {
                "date": game_result.date.isoformat()
                if isinstance(game_result.date, date)
                else game_result.date,
                "home_team": home_name,
                "away_team": away_name,
                "home_score": game_result.home_score,
                "away_score": game_result.away_score,
                "home_rating_before": home_rating,
                "home_rating_after": home_new,
                "away_rating_before": away_rating,
                "away_rating_after": away_new,
            }
        )

        logger.info(
            f"Updated ratings from {home_name} {game_result.home_score} - "
            f"{game_result.away_score} {away_name}: "
            f"{home_name} {home_rating:.2f}→{home_new:.2f}, "
            f"{away_name} {away_rating:.2f}→{away_new:.2f}"
        )

        # Auto-save if file configured
        if self.ratings_file:
            self.save_ratings(self.ratings_file)

        return home_new, away_new

    def calculate_matchup_spread(
        self, home_team: str, away_team: str, include_hfa: bool = True
    ) -> Optional[float]:
        """
        Calculate predicted spread for a matchup

        Spread = Home Rating - Away Rating + Home Field Advantage (2.0)

        Positive spread = home team favored
        Negative spread = away team favored

        Args:
            home_team: Home team name
            away_team: Away team name
            include_hfa: Whether to include home field advantage (default True)

        Returns:
            Predicted spread from home team perspective, or None if teams not found

        Examples:
            >>> prs.calculate_matchup_spread("Kansas City", "Buffalo")
            3.5  # KC favored by 3.5 (12.5 - 11.0 + 2.0)
        """
        home_name = self._normalize_team_name(home_team)
        away_name = self._normalize_team_name(away_team)

        home_rating = self.ratings.get(home_name)
        away_rating = self.ratings.get(away_name)

        if home_rating is None or away_rating is None:
            logger.warning(
                f"Cannot calculate spread: missing rating for "
                f"{home_name if home_rating is None else away_name}"
            )
            return None

        # Base spread from power ratings
        spread = home_rating - away_rating

        # Add home field advantage
        if include_hfa:
            spread += self.HOME_FIELD_ADVANTAGE

        return round(spread, 1)

    def get_top_teams(self, n: int = 10) -> List[Tuple[str, float]]:
        """
        Get top N teams by power rating

        Args:
            n: Number of teams to return

        Returns:
            List of (team_name, rating) tuples sorted by rating descending
        """
        sorted_teams = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        return sorted_teams[:n]

    def get_bottom_teams(self, n: int = 10) -> List[Tuple[str, float]]:
        """
        Get bottom N teams by power rating

        Args:
            n: Number of teams to return

        Returns:
            List of (team_name, rating) tuples sorted by rating ascending
        """
        sorted_teams = sorted(self.ratings.items(), key=lambda x: x[1])
        return sorted_teams[:n]

    def export_ratings(self) -> Dict[str, float]:
        """
        Export all current ratings as dictionary

        Returns:
            Dictionary mapping team names to ratings
        """
        return self.ratings.copy()

    def import_ratings(self, ratings: Dict[str, float]) -> None:
        """
        Import ratings from dictionary

        Args:
            ratings: Dictionary mapping team names to ratings
        """
        for team, rating in ratings.items():
            self.set_rating(team, rating)
        logger.info(f"Imported {len(ratings)} team ratings")

    def save_ratings(self, filepath: Path) -> None:
        """
        Save ratings and history to JSON file

        Args:
            filepath: Path to save file
        """
        data = {
            "ratings": self.ratings,
            "history": self.history,
            "last_updated": datetime.now().isoformat(),
            "system_constants": {
                "old_rating_weight": self.OLD_RATING_WEIGHT,
                "true_performance_weight": self.TRUE_PERFORMANCE_WEIGHT,
                "home_field_advantage": self.HOME_FIELD_ADVANTAGE,
            },
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(self.ratings)} ratings to {filepath}")

    def load_ratings(self, filepath: Path) -> None:
        """
        Load ratings and history from JSON file

        Args:
            filepath: Path to load file
        """
        if not filepath.exists():
            logger.warning(f"Ratings file not found: {filepath}")
            return

        with open(filepath, "r") as f:
            data = json.load(f)

        self.ratings = data.get("ratings", {})
        self.history = data.get("history", [])

        logger.info(
            f"Loaded {len(self.ratings)} ratings from {filepath} "
            f"(last updated: {data.get('last_updated', 'unknown')})"
        )

    def _normalize_team_name(self, team: str) -> str:
        """
        Normalize team name for consistent storage

        Args:
            team: Raw team name

        Returns:
            Normalized team name
        """
        # Basic normalization: strip whitespace, title case
        normalized = team.strip()

        # Optional: Add more sophisticated normalization
        # e.g., "KC" -> "Kansas City", "SF" -> "San Francisco"

        return normalized

    def reset_ratings(self) -> None:
        """Reset all ratings and history"""
        self.ratings = {}
        self.history = []
        logger.info("Reset all power ratings")

    def __repr__(self) -> str:
        return f"PowerRatingSystem(teams={len(self.ratings)}, games_processed={len(self.history)})"


def initialize_nfl_ratings() -> Dict[str, float]:
    """
    Initialize NFL power ratings with reasonable starting values
    Based on 2025 season preseason projections and historical data

    Scale:
        15+ = Elite Super Bowl contenders
        10-15 = Playoff caliber
        5-10 = Average/Below average
        0-5 = Rebuilding teams

    Returns:
        Dictionary of team name to initial rating
    """
    return {
        # Elite Tier (15+)
        "Kansas City": 15.0,
        "San Francisco": 14.5,
        "Baltimore": 14.0,
        "Buffalo": 13.5,
        # Strong Playoff Tier (12-13)
        "Philadelphia": 13.0,
        "Detroit": 12.5,
        "Dallas": 12.0,
        "Miami": 12.0,
        # Playoff Contenders (10-12)
        "Cincinnati": 11.5,
        "Cleveland": 11.0,
        "Jacksonville": 10.5,
        "Los Angeles Rams": 10.5,
        "Green Bay": 10.0,
        "Seattle": 10.0,
        # Average Tier (7-10)
        "Houston": 9.5,
        "Los Angeles Chargers": 9.0,
        "Pittsburgh": 9.0,
        "Tampa Bay": 9.0,
        "Atlanta": 8.5,
        "Minnesota": 8.5,
        "New Orleans": 8.0,
        "Las Vegas": 7.5,
        "Indianapolis": 7.5,
        "Tennessee": 7.0,
        # Below Average (5-7)
        "Chicago": 6.5,
        "Washington": 6.5,
        "New York Jets": 6.0,
        "New York Giants": 5.5,
        "Denver": 5.5,
        "Arizona": 5.0,
        # Rebuilding (0-5)
        "New England": 4.5,
        "Carolina": 4.0,
    }


def initialize_ncaaf_ratings() -> Dict[str, float]:
    """
    Initialize College Football power ratings
    Based on 2025 season preseason rankings

    Scale:
        20+ = National championship contenders
        15-20 = Top 10 teams
        10-15 = Top 25 teams
        5-10 = Bowl eligible
        0-5 = Struggling programs

    Returns:
        Dictionary of team name to initial rating
    """
    return {
        # Elite Tier
        "Georgia": 22.0,
        "Ohio State": 21.0,
        "Michigan": 20.5,
        "Alabama": 20.0,
        "Texas": 19.5,
        "Oregon": 19.0,
        # Top 10
        "Florida State": 18.5,
        "Penn State": 18.0,
        "Washington": 17.5,
        "USC": 17.0,
        "LSU": 17.0,
        "Oklahoma": 16.5,
        # Top 25
        "Notre Dame": 16.0,
        "Ole Miss": 15.5,
        "Tennessee": 15.0,
        "Clemson": 15.0,
        "Utah": 14.5,
        "Kansas State": 14.0,
        "Louisville": 14.0,
        "Oregon State": 13.5,
        "Missouri": 13.5,
        "Iowa": 13.0,
        # Bowl Tier
        "North Carolina": 12.5,
        "UCLA": 12.0,
        "Wisconsin": 11.5,
        "Miami": 11.5,
        "Texas A&M": 11.0,
        "Oklahoma State": 11.0,
        "Arizona": 10.5,
        "Liberty": 10.0,
        # More teams can be added as needed
    }
