"""
Unit tests for Billy Walters Power Rating System

Tests the 90/10 update formula and all core functionality
"""

import pytest
from datetime import date
from pathlib import Path
import tempfile
import json

from walters_analyzer.valuation.power_ratings import (
    PowerRatingSystem,
    Team,
    GameResult,
    initialize_nfl_ratings,
    initialize_ncaaf_ratings,
)


class TestTeam:
    """Test Team dataclass"""
    
    def test_team_creation(self):
        team = Team(name="Kansas City", power_rating=15.0)
        assert team.name == "Kansas City"
        assert team.power_rating == 15.0
        assert team.league == "NFL"
    
    def test_team_normalization(self):
        team = Team(name="  Kansas City  ", power_rating=15.0)
        assert team.name == "Kansas City"


class TestGameResult:
    """Test GameResult dataclass"""
    
    def test_game_result_creation(self):
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Kansas City",
            away_team="Buffalo",
            home_score=27,
            away_score=24
        )
        assert result.home_team == "Kansas City"
        assert result.away_team == "Buffalo"
        assert result.home_score == 27
        assert result.away_score == 24
    
    def test_winner_property(self):
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Kansas City",
            away_team="Buffalo",
            home_score=27,
            away_score=24
        )
        assert result.winner == "Kansas City"
        
        # Away win
        result2 = GameResult(
            date=date(2024, 11, 7),
            home_team="Kansas City",
            away_team="Buffalo",
            home_score=20,
            away_score=24
        )
        assert result2.winner == "Buffalo"
        
        # Tie
        result3 = GameResult(
            date=date(2024, 11, 7),
            home_team="Kansas City",
            away_team="Buffalo",
            home_score=24,
            away_score=24
        )
        assert result3.winner == "TIE"
    
    def test_margin_property(self):
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Kansas City",
            away_team="Buffalo",
            home_score=27,
            away_score=24
        )
        assert result.margin == 3


class TestPowerRatingSystem:
    """Test PowerRatingSystem core functionality"""
    
    def test_initialization(self):
        prs = PowerRatingSystem()
        assert len(prs.ratings) == 0
        assert len(prs.history) == 0
        assert prs.OLD_RATING_WEIGHT == 0.90
        assert prs.TRUE_PERFORMANCE_WEIGHT == 0.10
        assert prs.HOME_FIELD_ADVANTAGE == 2.0
    
    def test_set_and_get_rating(self):
        prs = PowerRatingSystem()
        prs.set_rating("Kansas City", 15.0)
        assert prs.get_rating("Kansas City") == 15.0
        
        # Test non-existent team
        assert prs.get_rating("Nonexistent") is None
    
    def test_90_10_formula_prd_example(self):
        """
        Test the exact example from PRD (lines 301-307):
        
        Bears beat Vikings 27-20 on neutral field
        Bears injuries: 3.5, Vikings injuries: 1.7
        Bears old rating: 10, Vikings old rating: 4
        
        True Performance = 7 + 4 + (3.5 - 1.7) = 12.8
        New Rating = 0.9(10) + 0.1(12.8) = 10.28
        """
        prs = PowerRatingSystem()
        
        # Set up teams
        bears = Team(name="Bears", power_rating=10.0)
        vikings = Team(name="Vikings", power_rating=4.0)
        
        # Create game result (neutral field)
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Bears",
            away_team="Vikings",
            home_score=27,
            away_score=20,
            home_injury_level=3.5,
            away_injury_level=1.7,
            location="neutral"
        )
        
        # Update Bears rating
        new_rating = prs.update_power_rating(bears, vikings, result)
        
        # Expected calculation:
        # Net score = 27 - 20 = 7
        # Opponent rating = 4
        # Injury differential = 3.5 - 1.7 = 1.8
        # Home adjustment = 0 (neutral)
        # True performance = 7 + 4 + 1.8 + 0 = 12.8
        # New rating = 0.9 * 10 + 0.1 * 12.8 = 9.0 + 1.28 = 10.28
        
        assert new_rating == 10.28
    
    def test_90_10_formula_home_game(self):
        """Test 90/10 formula with home field advantage"""
        prs = PowerRatingSystem()
        
        # Set up teams
        home_team = Team(name="Home", power_rating=10.0)
        away_team = Team(name="Away", power_rating=8.0)
        
        # Home team wins at home
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Home",
            away_team="Away",
            home_score=24,
            away_score=20,
            location="home"
        )
        
        new_rating = prs.update_power_rating(home_team, away_team, result)
        
        # Expected:
        # Net score = 24 - 20 = 4
        # Opponent rating = 8
        # Injury differential = 0
        # Home adjustment = -2 (we had HFA, so subtract it)
        # True performance = 4 + 8 + 0 - 2 = 10
        # New rating = 0.9 * 10 + 0.1 * 10 = 10.0
        
        assert new_rating == 10.0
    
    def test_update_ratings_from_game(self):
        """Test updating both teams from a game"""
        prs = PowerRatingSystem()
        prs.set_rating("Kansas City", 15.0)
        prs.set_rating("Buffalo", 13.5)
        
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Kansas City",
            away_team="Buffalo",
            home_score=27,
            away_score=24
        )
        
        home_new, away_new = prs.update_ratings_from_game(result)
        
        # Both ratings should have changed
        assert home_new != 15.0
        assert away_new != 13.5
        
        # KC won by 3, but expected to win by 3.5 (15.0 - 13.5 + 2.0 HFA)
        # So they underperformed slightly - rating should decrease
        # True perf = 3 + 13.5 + 0 - 2.0 = 14.5
        # New = 0.9 * 15 + 0.1 * 14.5 = 14.95
        assert home_new == 14.95
        
        # Buffalo lost but covered the spread (lost by 3, expected to lose by 3.5)
        # Their rating should improve slightly
        assert away_new > 13.5
        
        # History should be recorded
        assert len(prs.history) == 1
        assert prs.history[0]["home_team"] == "Kansas City"
    
    def test_calculate_matchup_spread(self):
        """Test spread calculation from power ratings"""
        prs = PowerRatingSystem()
        prs.set_rating("Kansas City", 15.0)
        prs.set_rating("Buffalo", 13.5)
        
        # KC at home vs Buffalo
        spread = prs.calculate_matchup_spread("Kansas City", "Buffalo")
        
        # Expected: 15.0 - 13.5 + 2.0 (HFA) = 3.5
        assert spread == 3.5
        
        # Without HFA
        spread_no_hfa = prs.calculate_matchup_spread(
            "Kansas City", "Buffalo", include_hfa=False
        )
        assert spread_no_hfa == 1.5
    
    def test_calculate_matchup_spread_missing_team(self):
        """Test spread calculation with missing team"""
        prs = PowerRatingSystem()
        prs.set_rating("Kansas City", 15.0)
        
        spread = prs.calculate_matchup_spread("Kansas City", "Nonexistent")
        assert spread is None
    
    def test_get_top_teams(self):
        """Test getting top teams by rating"""
        prs = PowerRatingSystem()
        prs.set_rating("Team A", 15.0)
        prs.set_rating("Team B", 12.0)
        prs.set_rating("Team C", 18.0)
        prs.set_rating("Team D", 10.0)
        
        top_2 = prs.get_top_teams(n=2)
        
        assert len(top_2) == 2
        assert top_2[0] == ("Team C", 18.0)
        assert top_2[1] == ("Team A", 15.0)
    
    def test_get_bottom_teams(self):
        """Test getting bottom teams by rating"""
        prs = PowerRatingSystem()
        prs.set_rating("Team A", 15.0)
        prs.set_rating("Team B", 12.0)
        prs.set_rating("Team C", 18.0)
        prs.set_rating("Team D", 10.0)
        
        bottom_2 = prs.get_bottom_teams(n=2)
        
        assert len(bottom_2) == 2
        assert bottom_2[0] == ("Team D", 10.0)
        assert bottom_2[1] == ("Team B", 12.0)
    
    def test_export_import_ratings(self):
        """Test exporting and importing ratings"""
        prs = PowerRatingSystem()
        prs.set_rating("Team A", 15.0)
        prs.set_rating("Team B", 12.0)
        
        # Export
        exported = prs.export_ratings()
        assert exported == {"Team A": 15.0, "Team B": 12.0}
        
        # Import to new system
        prs2 = PowerRatingSystem()
        prs2.import_ratings(exported)
        assert prs2.get_rating("Team A") == 15.0
        assert prs2.get_rating("Team B") == 12.0
    
    def test_save_and_load_ratings(self):
        """Test saving and loading ratings from file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_ratings.json"
            
            # Create and save
            prs = PowerRatingSystem(ratings_file=filepath)
            prs.set_rating("Team A", 15.0)
            prs.set_rating("Team B", 12.0)
            prs.save_ratings(filepath)
            
            # Load into new system
            prs2 = PowerRatingSystem(ratings_file=filepath)
            assert prs2.get_rating("Team A") == 15.0
            assert prs2.get_rating("Team B") == 12.0
    
    def test_november_7_memphis_example(self):
        """
        Test the November 7, 2025 example from PRD (lines 547-551):
        
        Tulane @ Memphis
        Market spread: Memphis -3.5
        Our spread: Memphis -6
        Result: Memphis -3.5 has 2.5-point edge - BET MEMPHIS
        """
        prs = PowerRatingSystem()
        
        # Set up ratings to produce -6 spread
        # Memphis home: need Memphis rating - Tulane rating + 2.0 = -6
        # So: Memphis rating - Tulane rating = -8
        # Let's say Memphis = 10, Tulane = 2
        # 10 - 2 + 2 = 10 (not -6, we need Memphis stronger)
        
        # Actually, spread is from HOME perspective
        # Memphis -6 means Memphis favored by 6
        # So: Memphis rating - Tulane rating + 2 = 6
        # Memphis rating - Tulane rating = 4
        # Memphis = 9.5, Tulane = 9.0 from our initial ratings
        
        prs.set_rating("Memphis", 11.0)
        prs.set_rating("Tulane", 7.0)
        
        our_spread = prs.calculate_matchup_spread("Memphis", "Tulane")
        
        # Expected: 11 - 7 + 2 = 6.0
        assert our_spread == 6.0
        
        # Market spread is -3.5
        market_spread = 3.5
        
        # Edge calculation (will be in edge_detection.py)
        edge = our_spread - market_spread
        assert edge == 2.5
        
        # This is a 2.5-point edge on Memphis (favorite)
        # PRD says: "Memphis -3.5 has 2.5-point edge - BET MEMPHIS"
        assert edge >= 2.5  # Meets minimum threshold


class TestInitializers:
    """Test initial rating generation functions"""
    
    def test_initialize_nfl_ratings(self):
        nfl_ratings = initialize_nfl_ratings()
        
        assert len(nfl_ratings) > 0
        assert "Kansas City" in nfl_ratings
        assert "San Francisco" in nfl_ratings
        
        # Kansas City should be highly rated
        assert nfl_ratings["Kansas City"] >= 14.0
    
    def test_initialize_ncaaf_ratings(self):
        ncaaf_ratings = initialize_ncaaf_ratings()
        
        assert len(ncaaf_ratings) > 0
        assert "Georgia" in ncaaf_ratings
        assert "Ohio State" in ncaaf_ratings
        
        # Georgia should be highly rated
        assert ncaaf_ratings["Georgia"] >= 20.0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_blowout_game(self):
        """Test rating update from blowout game (PRD line 635)"""
        prs = PowerRatingSystem()
        
        home_team = Team(name="Elite", power_rating=15.0)
        away_team = Team(name="Weak", power_rating=3.0)
        
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Elite",
            away_team="Weak",
            home_score=45,
            away_score=10,
            location="home"
        )
        
        new_rating = prs.update_power_rating(home_team, away_team, result)
        
        # Rating should increase significantly after blowout
        assert new_rating > home_team.power_rating
    
    def test_upset_loss(self):
        """Test rating update when favorite loses"""
        prs = PowerRatingSystem()
        
        home_team = Team(name="Favorite", power_rating=14.0)
        away_team = Team(name="Underdog", power_rating=6.0)
        
        # Underdog wins
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Favorite",
            away_team="Underdog",
            home_score=17,
            away_score=20,
            location="home"
        )
        
        new_rating = prs.update_power_rating(home_team, away_team, result)
        
        # Favorite's rating should decrease after loss
        assert new_rating < home_team.power_rating
    
    def test_neutral_site_game(self):
        """Test rating update at neutral site"""
        prs = PowerRatingSystem()
        
        team1 = Team(name="Team1", power_rating=10.0)
        team2 = Team(name="Team2", power_rating=10.0)
        
        result = GameResult(
            date=date(2024, 11, 7),
            home_team="Team1",  # Listed as "home" but neutral site
            away_team="Team2",
            home_score=24,
            away_score=21,
            location="neutral"
        )
        
        new_rating = prs.update_power_rating(team1, team2, result)
        
        # Rating should increase (won by 3 against equal opponent)
        assert new_rating > 10.0
    
    def test_reset_ratings(self):
        """Test resetting all ratings"""
        prs = PowerRatingSystem()
        prs.set_rating("Team A", 15.0)
        prs.history.append({"test": "data"})
        
        prs.reset_ratings()
        
        assert len(prs.ratings) == 0
        assert len(prs.history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

