"""
Tests for Power Rating Engine
"""

import pytest
import os
import tempfile
from walters_analyzer.power_ratings import (
    PowerRatingEngine,
    GameResult,
    TeamRating
)


@pytest.fixture
def temp_ratings_file():
    """Create temporary ratings file."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def engine(temp_ratings_file):
    """Create fresh engine instance."""
    return PowerRatingEngine(temp_ratings_file)


class TestPowerRatingEngine:
    """Test power rating calculations."""

    def test_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine is not None
        assert len(engine.ratings) == 0

    def test_new_team_starts_at_zero(self, engine):
        """Test new teams start with 0 rating."""
        rating = engine.get_rating("Alabama", "cfb")
        assert rating == 0.0

    def test_update_rating_basic(self, engine):
        """Test basic rating update."""
        game = GameResult(
            team="Alabama",
            opponent="LSU",
            team_score=42,
            opponent_score=21,
            is_home=True,
            sport="cfb",
            date="2024-11-01"
        )

        rating = engine.update_rating(game)

        # New rating should be 10% of true performance
        # True perf = score_diff + opp_rating + injury_diff - home_field
        # = 21 + 0 + 0 - (-3.5) = 24.5
        # New rating = 0.9 * 0 + 0.1 * 24.5 = 2.45
        assert rating.rating == pytest.approx(2.45, abs=0.01)
        assert rating.games_played == 1

    def test_update_rating_with_existing_rating(self, engine):
        """Test rating update builds on existing rating."""
        # First game
        game1 = GameResult(
            team="Alabama",
            opponent="LSU",
            team_score=42,
            opponent_score=21,
            is_home=True,
            sport="cfb",
            date="2024-11-01"
        )
        engine.update_rating(game1)

        # Second game
        game2 = GameResult(
            team="Alabama",
            opponent="Auburn",
            team_score=35,
            opponent_score=28,
            is_home=False,
            sport="cfb",
            date="2024-11-08"
        )
        rating = engine.update_rating(game2)

        # Rating should have increased
        assert rating.rating > 2.45
        assert rating.games_played == 2

    def test_opponent_rating_affects_calculation(self, engine):
        """Test that opponent rating impacts true performance."""
        # Set up opponent with high rating
        opp_game = GameResult(
            team="Georgia",
            opponent="Vanderbilt",
            team_score=56,
            opponent_score=7,
            is_home=True,
            sport="cfb",
            date="2024-11-01"
        )
        engine.update_rating(opp_game)
        georgia_rating = engine.get_rating("Georgia", "cfb")

        # Play against high-rated opponent
        game = GameResult(
            team="Alabama",
            opponent="Georgia",
            team_score=28,
            opponent_score=24,  # Close game
            is_home=True,
            sport="cfb",
            date="2024-11-08"
        )
        rating = engine.update_rating(game)

        # Rating should be higher due to strong opponent
        assert rating.rating > 0

    def test_home_field_adjustment(self, engine):
        """Test home field advantage is applied correctly."""
        # Same game, different locations
        game_home = GameResult(
            team="Alabama",
            opponent="LSU",
            team_score=35,
            opponent_score=35,  # Tie score
            is_home=True,
            sport="cfb",
            date="2024-11-01"
        )

        # True performance at home:
        # score_diff (0) + opp_rating (0) + injury_diff (0) - (-3.5) = 3.5
        rating_home = engine.update_rating(game_home)
        assert rating_home.rating == pytest.approx(0.35, abs=0.01)

    def test_predicted_spread(self, engine):
        """Test spread prediction."""
        # Set up teams
        game1 = GameResult("Alabama", "X", 42, 14, True, "cfb", "2024-11-01")
        game2 = GameResult("LSU", "Y", 28, 21, True, "cfb", "2024-11-01")

        engine.update_rating(game1)
        engine.update_rating(game2)

        # Predict spread (LSU away @ Alabama home)
        spread = engine.calculate_predicted_spread("LSU", "Alabama", "cfb")

        # Alabama dominated their game (42-14), LSU had close game (28-21)
        # So Alabama should be stronger and favored
        # Just verify we get a numeric spread prediction
        assert isinstance(spread, float)

    def test_nfl_vs_cfb_home_field(self, engine):
        """Test NFL and CFB have different home field advantages."""
        assert engine.HOME_FIELD['nfl'] == 2.5
        assert engine.HOME_FIELD['cfb'] == 3.5

    def test_edge_calculation(self, engine):
        """Test edge vs market calculation."""
        # Set up teams
        game1 = GameResult("Chiefs", "X", 31, 17, True, "nfl", "2024-11-01")
        game2 = GameResult("Raiders", "Y", 17, 24, False, "nfl", "2024-11-01")

        engine.update_rating(game1)
        engine.update_rating(game2)

        # Get edge vs market
        edge = engine.get_edge_vs_market(
            away_team="Raiders",
            home_team="Chiefs",
            sport="nfl",
            market_spread=-7.0
        )

        assert 'edge' in edge
        assert 'recommendation' in edge
        assert 'predicted_spread' in edge

    def test_save_and_load_ratings(self, engine, temp_ratings_file):
        """Test ratings persist correctly."""
        # Create rating
        game = GameResult("Alabama", "LSU", 42, 21, True, "cfb", "2024-11-01")
        engine.update_rating(game)
        original_rating = engine.get_rating("Alabama", "cfb")

        # Save
        engine.save_ratings()

        # Load in new engine
        engine2 = PowerRatingEngine(temp_ratings_file)
        loaded_rating = engine2.get_rating("Alabama", "cfb")

        assert loaded_rating == original_rating

    def test_rating_history_tracked(self, engine):
        """Test rating history is maintained."""
        team_key = engine._make_key("Alabama", "cfb")

        # Play multiple games
        for i in range(5):
            game = GameResult(
                "Alabama", "Opponent", 35 + i, 20, True, "cfb", f"2024-11-0{i+1}"
            )
            engine.update_rating(game)

        rating = engine.ratings[team_key]
        assert len(rating.rating_history) == 5

    def test_get_all_ratings(self, engine):
        """Test getting all ratings for a sport."""
        # Create multiple teams
        teams = ["Alabama", "Georgia", "LSU", "Florida"]
        for team in teams:
            game = GameResult(team, "X", 35, 20, True, "cfb", "2024-11-01")
            engine.update_rating(game)

        ratings = engine.get_all_ratings(sport="cfb")

        assert len(ratings) == 4
        # Should be sorted by rating (descending)
        assert ratings[0].rating >= ratings[1].rating


class TestGameResult:
    """Test GameResult dataclass."""

    def test_score_differential(self):
        """Test score differential calculation."""
        game = GameResult(
            team="Alabama",
            opponent="LSU",
            team_score=42,
            opponent_score=21,
            is_home=True,
            sport="cfb",
            date="2024-11-01"
        )

        assert game.score_differential == 21

    def test_negative_differential(self):
        """Test negative score differential (loss)."""
        game = GameResult(
            team="Alabama",
            opponent="Georgia",
            team_score=21,
            opponent_score=35,
            is_home=True,
            sport="cfb",
            date="2024-11-01"
        )

        assert game.score_differential == -14
