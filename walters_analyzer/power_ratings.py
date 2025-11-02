"""
Billy Walters Power Rating Engine

Core methodology from Billy Walters Advanced Masterclass:
- Power ratings updated after each game using exponential weighted formula
- True game performance accounts for opponent strength, injuries, and home field
- Ratings are sport-specific (NFL, CFB) with different home field adjustments
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List
import json
import os


@dataclass
class TeamRating:
    """Power rating for a single team."""
    team: str
    sport: str
    rating: float = 0.0
    games_played: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    # Historical tracking
    rating_history: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'team': self.team,
            'sport': self.sport,
            'rating': round(self.rating, 2),
            'games_played': self.games_played,
            'last_updated': self.last_updated,
            'rating_history': [round(r, 2) for r in self.rating_history[-10:]]  # Last 10 games
        }


@dataclass
class GameResult:
    """Represents a completed game for rating updates."""
    team: str
    opponent: str
    team_score: int
    opponent_score: int
    is_home: bool
    sport: str
    date: str
    injury_differential: float = 0.0  # Team injuries - opponent injuries (in points)

    @property
    def score_differential(self) -> int:
        """Raw score differential (positive = win)."""
        return self.team_score - self.opponent_score

    @property
    def points_scored(self) -> int:
        return self.team_score

    @property
    def points_allowed(self) -> int:
        return self.opponent_score


class PowerRatingEngine:
    """
    Billy Walters Power Rating System

    Formula: new_rating = (old_rating × 0.9) + (true_game_performance × 0.1)

    Where true_game_performance =
        score_differential +
        opponent_rating +
        injury_differential -
        home_field_adjustment
    """

    # Billy Walters home field advantages (in points)
    HOME_FIELD = {
        'nfl': 2.5,
        'cfb': 3.5,  # College has more HFA due to crowd/environment
    }

    # Exponential weighting factor (Billy Walters uses 90/10 split)
    MOMENTUM_WEIGHT = 0.9  # Weight of existing rating
    GAME_WEIGHT = 0.1      # Weight of new game performance

    def __init__(self, ratings_file: Optional[str] = None):
        """
        Initialize power rating engine.

        Args:
            ratings_file: Path to JSON file for persisting ratings
        """
        self.ratings: Dict[str, TeamRating] = {}
        self.ratings_file = ratings_file or "data/power_ratings/team_ratings.json"

        # Load existing ratings if available
        if os.path.exists(self.ratings_file):
            self.load_ratings()

    def get_rating(self, team: str, sport: str) -> float:
        """
        Get current power rating for a team.

        Args:
            team: Team name
            sport: 'nfl' or 'cfb'

        Returns:
            Current power rating (0.0 if team not rated yet)
        """
        key = self._make_key(team, sport)
        if key in self.ratings:
            return self.ratings[key].rating
        return 0.0

    def update_rating(self, game: GameResult) -> TeamRating:
        """
        Update team rating based on game result using Billy Walters formula.

        Args:
            game: GameResult with all necessary data

        Returns:
            Updated TeamRating object
        """
        key = self._make_key(game.team, game.sport)

        # Get or create team rating
        if key not in self.ratings:
            self.ratings[key] = TeamRating(team=game.team, sport=game.sport)

        team_rating = self.ratings[key]

        # Get opponent rating
        opponent_rating = self.get_rating(game.opponent, game.sport)

        # Calculate home field adjustment
        home_field = self._get_home_field_adjustment(game)

        # Calculate true game performance
        true_performance = self._calculate_true_performance(
            score_diff=game.score_differential,
            opponent_rating=opponent_rating,
            injury_diff=game.injury_differential,
            home_field=home_field
        )

        # Apply Billy Walters exponential weighted formula
        old_rating = team_rating.rating
        new_rating = (old_rating * self.MOMENTUM_WEIGHT) + (true_performance * self.GAME_WEIGHT)

        # Update team rating
        team_rating.rating = new_rating
        team_rating.games_played += 1
        team_rating.last_updated = datetime.now().isoformat()
        team_rating.rating_history.append(new_rating)

        return team_rating

    def calculate_predicted_spread(
        self,
        away_team: str,
        home_team: str,
        sport: str,
        injury_diff: float = 0.0
    ) -> float:
        """
        Calculate predicted spread using power ratings.

        Formula: spread = (home_rating - away_rating) + home_field + injury_adjustment

        Args:
            away_team: Away team name
            home_team: Home team name
            sport: 'nfl' or 'cfb'
            injury_diff: Home injuries - away injuries (in points)

        Returns:
            Predicted spread (negative = home favored)
        """
        away_rating = self.get_rating(away_team, sport)
        home_rating = self.get_rating(home_team, sport)
        home_field = self.HOME_FIELD.get(sport, 2.5)

        # Home team advantage
        spread = (home_rating - away_rating) + home_field - injury_diff

        return round(spread, 1)

    def calculate_predicted_total(
        self,
        away_team: str,
        home_team: str,
        sport: str,
        weather_adjustment: float = 0.0
    ) -> float:
        """
        Calculate predicted total points using power ratings.

        This is a simplified approach - you may want to track offensive/defensive
        ratings separately for more accuracy.

        Args:
            away_team: Away team name
            home_team: Home team name
            sport: 'nfl' or 'cfb'
            weather_adjustment: Points to subtract for weather (wind/precip)

        Returns:
            Predicted total points
        """
        # Average points per game varies by sport
        base_total = {
            'nfl': 45.0,
            'cfb': 55.0
        }.get(sport, 50.0)

        # Higher rated teams tend to score more points
        away_rating = self.get_rating(away_team, sport)
        home_rating = self.get_rating(home_team, sport)
        avg_rating = (away_rating + home_rating) / 2

        # Adjust total based on team strength
        # Rule of thumb: 1 point in power rating ≈ 0.3 points in total
        rating_adjustment = avg_rating * 0.3

        predicted_total = base_total + rating_adjustment - weather_adjustment

        return round(predicted_total, 1)

    def get_edge_vs_market(
        self,
        away_team: str,
        home_team: str,
        sport: str,
        market_spread: float,
        injury_diff: float = 0.0
    ) -> dict:
        """
        Calculate betting edge vs market spread.

        Args:
            away_team: Away team name
            home_team: Home team name
            sport: 'nfl' or 'cfb'
            market_spread: Current market spread (negative = home favored)
            injury_diff: Home injuries - away injuries (in points)

        Returns:
            Dict with edge analysis
        """
        predicted_spread = self.calculate_predicted_spread(
            away_team, home_team, sport, injury_diff
        )

        edge = abs(predicted_spread - market_spread)

        # Determine recommendation
        if edge >= 2.0:  # Billy Walters 2-point threshold
            if predicted_spread < market_spread:
                # Your rating favors home more than market
                recommendation = f"BET {home_team} (home)"
                side = "home"
            else:
                # Your rating favors away more than market
                recommendation = f"BET {away_team} (away)"
                side = "away"
        else:
            recommendation = "NO BET - Edge insufficient"
            side = None

        return {
            'away_team': away_team,
            'home_team': home_team,
            'predicted_spread': predicted_spread,
            'market_spread': market_spread,
            'edge': round(edge, 1),
            'recommendation': recommendation,
            'side': side,
            'away_rating': self.get_rating(away_team, sport),
            'home_rating': self.get_rating(home_team, sport)
        }

    def save_ratings(self) -> None:
        """Save ratings to JSON file."""
        os.makedirs(os.path.dirname(self.ratings_file), exist_ok=True)

        ratings_data = {
            'last_updated': datetime.now().isoformat(),
            'ratings': {
                key: rating.to_dict()
                for key, rating in self.ratings.items()
            }
        }

        with open(self.ratings_file, 'w') as f:
            json.dump(ratings_data, f, indent=2)

    def load_ratings(self) -> None:
        """Load ratings from JSON file."""
        if not os.path.exists(self.ratings_file):
            return

        # Check if file is empty
        if os.path.getsize(self.ratings_file) == 0:
            return

        with open(self.ratings_file, 'r') as f:
            data = json.load(f)

        for key, rating_dict in data.get('ratings', {}).items():
            self.ratings[key] = TeamRating(
                team=rating_dict['team'],
                sport=rating_dict['sport'],
                rating=rating_dict['rating'],
                games_played=rating_dict['games_played'],
                last_updated=rating_dict['last_updated'],
                rating_history=rating_dict.get('rating_history', [])
            )

    def get_all_ratings(self, sport: Optional[str] = None) -> List[TeamRating]:
        """
        Get all team ratings, optionally filtered by sport.

        Args:
            sport: Optional sport filter ('nfl' or 'cfb')

        Returns:
            List of TeamRating objects, sorted by rating (descending)
        """
        ratings = list(self.ratings.values())

        if sport:
            ratings = [r for r in ratings if r.sport == sport]

        return sorted(ratings, key=lambda r: r.rating, reverse=True)

    # Private helper methods

    def _make_key(self, team: str, sport: str) -> str:
        """Create unique key for team/sport combination."""
        return f"{sport}:{team.lower()}"

    def _get_home_field_adjustment(self, game: GameResult) -> float:
        """
        Calculate home field adjustment for the team in question.

        If team was home: subtract HFA (they had advantage)
        If team was away: add HFA (opponent had advantage)
        """
        hfa = self.HOME_FIELD.get(game.sport, 2.5)
        return -hfa if game.is_home else hfa

    def _calculate_true_performance(
        self,
        score_diff: int,
        opponent_rating: float,
        injury_diff: float,
        home_field: float
    ) -> float:
        """
        Calculate true game performance per Billy Walters methodology.

        Args:
            score_diff: Team score - opponent score
            opponent_rating: Opponent's power rating
            injury_diff: Team injuries - opponent injuries (in points)
            home_field: Home field adjustment (+/- based on location)

        Returns:
            True game performance value
        """
        true_performance = (
            score_diff +
            opponent_rating +
            injury_diff -
            home_field
        )

        return true_performance


# Convenience functions for quick access

def create_engine(ratings_file: Optional[str] = None) -> PowerRatingEngine:
    """Create a new power rating engine instance."""
    return PowerRatingEngine(ratings_file)


def calculate_spread(
    engine: PowerRatingEngine,
    away_team: str,
    home_team: str,
    sport: str,
    injury_diff: float = 0.0
) -> float:
    """Quick spread calculation."""
    return engine.calculate_predicted_spread(away_team, home_team, sport, injury_diff)


def calculate_edge(
    engine: PowerRatingEngine,
    away_team: str,
    home_team: str,
    sport: str,
    market_spread: float,
    injury_diff: float = 0.0
) -> dict:
    """Quick edge calculation."""
    return engine.get_edge_vs_market(away_team, home_team, sport, market_spread, injury_diff)
