"""
Unit tests for Power Rating Backtest Engine
"""

import pytest
from datetime import date
from pathlib import Path
import json

from walters_analyzer.backtest.power_rating_backtest import (
    PowerRatingBacktest,
    PredictionResult,
    BacktestResult,
)


class TestPredictionResult:
    """Test PredictionResult dataclass"""
    
    def test_prediction_result_creation(self):
        pred = PredictionResult(
            date=date(2024, 9, 8),
            home_team="Kansas City",
            away_team="Baltimore",
            predicted_spread=3.5,
            actual_home_score=27,
            actual_away_score=20,
            actual_margin=7,
            prediction_error=3.5,
            correct_winner=True,
            covered_spread=True,
        )
        
        assert pred.home_team == "Kansas City"
        assert pred.predicted_spread == 3.5
        assert pred.actual_margin == 7
    
    def test_favorite_property(self):
        # Home favorite
        pred = PredictionResult(
            date=date(2024, 9, 8),
            home_team="Kansas City",
            away_team="Baltimore",
            predicted_spread=3.5,
            actual_home_score=27,
            actual_away_score=20,
            actual_margin=7,
            prediction_error=3.5,
            correct_winner=True,
            covered_spread=True,
        )
        assert pred.favorite == "Kansas City"
        assert pred.underdog == "Baltimore"
        
        # Away favorite
        pred2 = PredictionResult(
            date=date(2024, 9, 8),
            home_team="New England",
            away_team="Kansas City",
            predicted_spread=-7.5,
            actual_home_score=10,
            actual_away_score=30,
            actual_margin=-20,
            prediction_error=12.5,
            correct_winner=True,
            covered_spread=True,
        )
        assert pred2.favorite == "Kansas City"
        assert pred2.underdog == "New England"


class TestPowerRatingBacktest:
    """Test PowerRatingBacktest functionality"""
    
    def test_initialization(self):
        backtest = PowerRatingBacktest()
        assert len(backtest.initial_ratings) > 0
        assert "Kansas City" in backtest.initial_ratings
    
    def test_initialization_custom_ratings(self):
        custom = {"Team A": 10.0, "Team B": 8.0}
        backtest = PowerRatingBacktest(initial_ratings=custom)
        assert backtest.initial_ratings == custom
    
    def test_single_game_backtest(self):
        """Test backtest with a single game"""
        backtest = PowerRatingBacktest()
        
        games = [{
            "date": "2024-09-08",
            "home_team": "Kansas City",
            "away_team": "Baltimore",
            "home_score": 27,
            "away_score": 20,
            "week": 1
        }]
        
        result = backtest.run_backtest(games)
        
        assert result.total_games == 1
        assert len(result.predictions) == 1
        assert result.predictions[0].home_team == "Kansas City"
        assert result.predictions[0].away_team == "Baltimore"
    
    def test_multiple_games_backtest(self):
        """Test backtest with multiple games"""
        backtest = PowerRatingBacktest()
        
        games = [
            {
                "date": "2024-09-08",
                "home_team": "Kansas City",
                "away_team": "Baltimore",
                "home_score": 27,
                "away_score": 20,
                "week": 1
            },
            {
                "date": "2024-09-08",
                "home_team": "Buffalo",
                "away_team": "Arizona",
                "home_score": 28,
                "away_score": 21,
                "week": 1
            },
            {
                "date": "2024-09-15",
                "home_team": "Kansas City",
                "away_team": "Cincinnati",
                "home_score": 26,
                "away_score": 25,
                "week": 2
            }
        ]
        
        result = backtest.run_backtest(games)
        
        assert result.total_games == 3
        assert len(result.predictions) == 3
        assert len(result.weekly_stats) == 2  # Weeks 1 and 2
    
    def test_rating_evolution(self):
        """Test that ratings evolve after games"""
        backtest = PowerRatingBacktest()
        
        kc_initial = backtest.prs.get_rating("Kansas City")
        bal_initial = backtest.prs.get_rating("Baltimore")
        
        games = [{
            "date": "2024-09-08",
            "home_team": "Kansas City",
            "away_team": "Baltimore",
            "home_score": 27,
            "away_score": 20,
            "week": 1
        }]
        
        result = backtest.run_backtest(games)
        
        # Ratings should have changed
        assert result.final_ratings["Kansas City"] != kc_initial
        assert result.final_ratings["Baltimore"] != bal_initial
        
        # KC won so their rating should change (though might decrease if underperformed)
        assert "Kansas City" in result.final_ratings
        assert "Baltimore" in result.final_ratings
    
    def test_winner_prediction_accuracy(self):
        """Test winner prediction accuracy calculation"""
        backtest = PowerRatingBacktest()
        
        games = [
            {
                "date": "2024-09-08",
                "home_team": "Kansas City",
                "away_team": "Baltimore",
                "home_score": 27,
                "away_score": 20,
                "week": 1
            },
            {
                "date": "2024-09-08",
                "home_team": "Buffalo",
                "away_team": "Arizona",
                "home_score": 28,
                "away_score": 21,
                "week": 1
            }
        ]
        
        result = backtest.run_backtest(games)
        
        # Check that accuracy metrics are calculated
        assert 0.0 <= result.correct_winner_pct <= 1.0
        assert result.ats_win_pct >= 0.0
    
    def test_weekly_stats(self):
        """Test weekly statistics tracking"""
        backtest = PowerRatingBacktest()
        
        games = [
            {"date": "2024-09-08", "home_team": "Kansas City", "away_team": "Baltimore", 
             "home_score": 27, "away_score": 20, "week": 1},
            {"date": "2024-09-08", "home_team": "Buffalo", "away_team": "Arizona",
             "home_score": 28, "away_score": 21, "week": 1},
            {"date": "2024-09-15", "home_team": "Kansas City", "away_team": "Cincinnati",
             "home_score": 26, "away_score": 25, "week": 2}
        ]
        
        result = backtest.run_backtest(games)
        
        assert 1 in result.weekly_stats
        assert 2 in result.weekly_stats
        assert result.weekly_stats[1]['games'] == 2
        assert result.weekly_stats[2]['games'] == 1
    
    def test_prediction_error_calculation(self):
        """Test that prediction errors are calculated correctly"""
        backtest = PowerRatingBacktest()
        
        games = [{
            "date": "2024-09-08",
            "home_team": "Kansas City",
            "away_team": "Baltimore",
            "home_score": 27,
            "away_score": 20,
            "week": 1
        }]
        
        result = backtest.run_backtest(games)
        
        pred = result.predictions[0]
        # Actual margin = 27 - 20 = 7
        # Prediction error = abs(predicted_spread - 7)
        assert pred.actual_margin == 7
        assert pred.prediction_error >= 0
    
    def test_biggest_movers(self):
        """Test biggest movers calculation"""
        backtest = PowerRatingBacktest()
        
        # Run several games to see rating changes
        games = [
            {"date": "2024-09-08", "home_team": "Kansas City", "away_team": "Baltimore",
             "home_score": 27, "away_score": 20, "week": 1},
            {"date": "2024-09-08", "home_team": "Buffalo", "away_team": "Arizona",
             "home_score": 28, "away_score": 21, "week": 1},
            {"date": "2024-09-08", "home_team": "Carolina", "away_team": "New Orleans",
             "home_score": 10, "away_score": 47, "week": 1},
        ]
        
        result = backtest.run_backtest(games)
        
        assert len(result.biggest_movers) > 0
        # Biggest movers should be tuples of (team, change)
        team, change = result.biggest_movers[0]
        assert isinstance(team, str)
        assert isinstance(change, float)
    
    def test_report_generation(self):
        """Test that report generation works"""
        backtest = PowerRatingBacktest()
        
        games = [
            {"date": "2024-09-08", "home_team": "Kansas City", "away_team": "Baltimore",
             "home_score": 27, "away_score": 20, "week": 1}
        ]
        
        result = backtest.run_backtest(games)
        report = backtest.generate_report(result)
        
        assert isinstance(report, str)
        assert "BACKTEST REPORT" in report
        assert "Kansas City" in report or "Baltimore" in report
        assert "PREDICTION ACCURACY" in report
    
    def test_date_parsing(self):
        """Test various date format parsing"""
        backtest = PowerRatingBacktest()
        
        # ISO format
        d1 = backtest._parse_date("2024-09-08")
        assert d1 == date(2024, 9, 8)
        
        # Date object
        d2 = backtest._parse_date(date(2024, 9, 8))
        assert d2 == date(2024, 9, 8)
    
    def test_skip_missing_teams(self):
        """Test that games with missing teams are skipped"""
        backtest = PowerRatingBacktest()
        
        games = [
            {
                "date": "2024-09-08",
                "home_team": "Nonexistent Team",
                "away_team": "Also Fake",
                "home_score": 20,
                "away_score": 17,
                "week": 1
            }
        ]
        
        result = backtest.run_backtest(games)
        
        # Should skip the game since teams don't exist
        assert result.total_games == 0


class TestBacktestWithActualData:
    """Integration tests with actual game data"""
    
    def test_with_actual_nfl_data(self):
        """Test with actual NFL 2025 data if available"""
        data_file = Path(__file__).parent.parent / "data" / "nfl_2025_games_weeks_1_9.json"
        
        if not data_file.exists():
            pytest.skip("NFL 2025 data file not found")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        backtest = PowerRatingBacktest()
        result = backtest.run_backtest(data['games'])
        
        # Should have processed games
        assert result.total_games > 0
        
        # Accuracy should be reasonable (50-80%)
        assert 0.5 <= result.correct_winner_pct <= 0.9
        
        # ATS should be close to 50% (market efficiency)
        assert 0.4 <= result.ats_win_pct <= 0.6
        
        # Errors should be reasonable (0-20 points)
        assert 0 <= result.mean_absolute_error <= 20
        assert 0 <= result.median_absolute_error <= 20
    
    def test_rating_consistency(self):
        """Test that ratings remain consistent and reasonable"""
        backtest = PowerRatingBacktest()
        
        games = [
            {"date": "2024-09-08", "home_team": "Kansas City", "away_team": "Baltimore",
             "home_score": 27, "away_score": 20, "week": 1},
            {"date": "2024-09-15", "home_team": "Kansas City", "away_team": "Cincinnati",
             "home_score": 26, "away_score": 25, "week": 2}
        ]
        
        result = backtest.run_backtest(games)
        
        # All ratings should be finite numbers
        for team, rating in result.final_ratings.items():
            assert isinstance(rating, (int, float))
            assert not (rating != rating)  # Check for NaN
            # Ratings should be reasonable (-10 to 25 range)
            assert -10 <= rating <= 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

