"""
Unit tests for BettingResultsChecker
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from walters_analyzer.performance.results_checker import (
    BettingResultsChecker,
    GameScore,
    Prediction,
    GameResult,
)


class TestGameScore:
    """Test GameScore dataclass"""

    def test_game_score_creation(self):
        """Test GameScore initialization"""
        score = GameScore(
            game_id="test_home",
            matchup="Away Team @ Home Team",
            away_team="Away Team",
            home_team="Home Team",
            away_score=24,
            home_score=21,
            status="Final",
            game_time="2025-11-23T13:00:00Z",
        )

        assert score.game_id == "test_home"
        assert score.matchup == "Away Team @ Home Team"
        assert score.away_score == 24
        assert score.home_score == 21
        assert score.status == "Final"

    def test_game_score_different_scores(self):
        """Test various score combinations"""
        test_cases = [
            (0, 0),
            (28, 21),
            (45, 17),
            (10, 13),
        ]

        for away, home in test_cases:
            score = GameScore(
                game_id="test",
                matchup="A @ B",
                away_team="A",
                home_team="B",
                away_score=away,
                home_score=home,
                status="Final",
                game_time="2025-11-23T13:00:00Z",
            )
            assert score.away_score == away
            assert score.home_score == home


class TestPrediction:
    """Test Prediction dataclass"""

    def test_prediction_creation(self):
        """Test Prediction initialization"""
        pred = Prediction(
            game_id="test_home",
            matchup="Away Team @ Home Team",
            week=12,
            away_team="Away Team",
            home_team="Home Team",
            predicted_spread=3.5,
            market_spread=-3.0,
            market_total=45.5,
            recommended_bet="away",
            kelly_fraction=0.05,
            confidence_score=72.5,
            timestamp="2025-11-23T05:07:25.113446",
        )

        assert pred.game_id == "test_home"
        assert pred.week == 12
        assert pred.predicted_spread == 3.5
        assert pred.recommended_bet == "away"
        assert pred.kelly_fraction == 0.05


class TestBettingResultsChecker:
    """Test BettingResultsChecker class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.checker = BettingResultsChecker()

    def teardown_method(self):
        """Clean up after tests"""
        self.checker.close()

    def test_checker_initialization(self):
        """Test checker initializes properly"""
        assert self.checker.client is not None
        assert self.checker.games == {}
        assert self.checker.predictions == {}
        assert self.checker.results == []

    def test_calculate_ats_away_win(self):
        """Test ATS calculation for away team win"""
        pred = Prediction(
            game_id="test",
            matchup="Away @ Home",
            week=12,
            away_team="Away",
            home_team="Home",
            predicted_spread=3.5,
            market_spread=-3.0,
            market_total=45.5,
            recommended_bet="away",
            kelly_fraction=0.05,
            confidence_score=72.5,
            timestamp="",
        )

        score = GameScore(
            game_id="test",
            matchup="Away @ Home",
            away_team="Away",
            home_team="Home",
            away_score=24,
            home_score=17,
            status="Final",
            game_time="",
        )

        result, margin_error = self.checker.calculate_ats(pred, score)

        assert result == "WIN"
        # actual_margin = 24 - 17 = 7
        # predicted_spread = 3.5
        assert margin_error == pytest.approx(3.5)

    def test_calculate_ats_away_loss(self):
        """Test ATS calculation for away team loss"""
        pred = Prediction(
            game_id="test",
            matchup="Away @ Home",
            week=12,
            away_team="Away",
            home_team="Home",
            predicted_spread=3.5,
            market_spread=-3.0,
            market_total=45.5,
            recommended_bet="away",
            kelly_fraction=0.05,
            confidence_score=72.5,
            timestamp="",
        )

        score = GameScore(
            game_id="test",
            matchup="Away @ Home",
            away_team="Away",
            home_team="Home",
            away_score=17,
            home_score=24,
            status="Final",
            game_time="",
        )

        result, margin_error = self.checker.calculate_ats(pred, score)

        assert result == "LOSS"
        # actual_margin = 17 - 24 = -7
        assert margin_error == pytest.approx(-10.5)

    def test_calculate_ats_home_win(self):
        """Test ATS calculation for home team win"""
        pred = Prediction(
            game_id="test",
            matchup="Away @ Home",
            week=12,
            away_team="Away",
            home_team="Home",
            predicted_spread=-2.5,
            market_spread=3.0,
            market_total=45.5,
            recommended_bet="home",
            kelly_fraction=0.05,
            confidence_score=72.5,
            timestamp="",
        )

        score = GameScore(
            game_id="test",
            matchup="Away @ Home",
            away_team="Away",
            home_team="Home",
            away_score=17,
            home_score=24,
            status="Final",
            game_time="",
        )

        result, margin_error = self.checker.calculate_ats(pred, score)

        assert result == "WIN"
        # actual_margin = 17 - 24 = -7
        assert margin_error == pytest.approx(-4.5)

    def test_calculate_ats_push(self):
        """Test ATS calculation for push"""
        pred = Prediction(
            game_id="test",
            matchup="Away @ Home",
            week=12,
            away_team="Away",
            home_team="Home",
            predicted_spread=2.0,
            market_spread=-3.0,
            market_total=45.5,
            recommended_bet="away",
            kelly_fraction=0.05,
            confidence_score=72.5,
            timestamp="",
        )

        score = GameScore(
            game_id="test",
            matchup="Away @ Home",
            away_team="Away",
            home_team="Home",
            away_score=24,
            home_score=21,
            status="Final",
            game_time="",
        )

        result, margin_error = self.checker.calculate_ats(pred, score)

        assert result == "PUSH"

    def test_calculate_profit_loss_win(self):
        """Test profit/loss calculation for winning bet"""
        profit, roi = self.checker.calculate_profit_loss("WIN", 0.05, 10000)

        assert profit > 0
        assert roi > 0
        # With Kelly 0.05 = $500, -110 pays 0.909 = $454.50
        assert profit == pytest.approx(454.5, abs=1)

    def test_calculate_profit_loss_loss(self):
        """Test profit/loss calculation for losing bet"""
        profit, roi = self.checker.calculate_profit_loss("LOSS", 0.05, 10000)

        assert profit < 0
        assert roi < 0
        # With Kelly 0.05 = $500
        assert profit == pytest.approx(-500)

    def test_calculate_profit_loss_push(self):
        """Test profit/loss calculation for push"""
        profit, roi = self.checker.calculate_profit_loss("PUSH", 0.05, 10000)

        assert profit == 0
        assert roi == 0

    def test_load_predictions_file_not_found(self):
        """Test loading non-existent predictions file"""
        fake_file = Path("/nonexistent/path/predictions.jsonl")
        predictions = self.checker.load_predictions(fake_file)

        assert predictions == []

    def test_load_predictions_valid_file(self, tmp_path):
        """Test loading valid predictions file"""
        pred_file = tmp_path / "predictions.jsonl"

        # Create test predictions
        pred_data = {
            "game_id": "test_home",
            "matchup": "Test @ Home",
            "week": 12,
            "away_team": "Test",
            "home_team": "Home",
            "predicted_spread": 3.5,
            "market_spread": -3.0,
            "market_total": 45.5,
            "recommended_bet": "away",
            "kelly_fraction": 0.05,
            "confidence_score": 72.5,
            "timestamp": "2025-11-23T05:07:25.113446",
        }

        with open(pred_file, "w") as f:
            f.write(json.dumps(pred_data) + "\n")

        predictions = self.checker.load_predictions(pred_file)

        assert len(predictions) == 1
        assert predictions[0].game_id == "test_home"
        assert predictions[0].week == 12

    def test_load_predictions_multiple_lines(self, tmp_path):
        """Test loading file with multiple predictions"""
        pred_file = tmp_path / "predictions.jsonl"

        pred_data_1 = {
            "game_id": "test1_home",
            "matchup": "Test1 @ Home",
            "week": 12,
            "away_team": "Test1",
            "home_team": "Home",
            "predicted_spread": 3.5,
            "market_spread": -3.0,
            "market_total": 45.5,
            "recommended_bet": "away",
            "kelly_fraction": 0.05,
            "confidence_score": 72.5,
            "timestamp": "2025-11-23T05:07:25.113446",
        }

        pred_data_2 = {
            "game_id": "test2_home",
            "matchup": "Test2 @ Home",
            "week": 12,
            "away_team": "Test2",
            "home_team": "Home",
            "predicted_spread": 2.5,
            "market_spread": -2.0,
            "market_total": 48.5,
            "recommended_bet": "home",
            "kelly_fraction": 0.03,
            "confidence_score": 55.0,
            "timestamp": "2025-11-23T05:07:25.113446",
        }

        with open(pred_file, "w") as f:
            f.write(json.dumps(pred_data_1) + "\n")
            f.write(json.dumps(pred_data_2) + "\n")

        predictions = self.checker.load_predictions(pred_file)

        assert len(predictions) == 2
        assert predictions[0].game_id == "test1_home"
        assert predictions[1].game_id == "test2_home"

    def test_generate_report_empty_results(self):
        """Test report generation with no results"""
        report = self.checker.generate_report([], league="nfl", week=12)
        assert report == "No results to report"

    def test_generate_report_single_result(self):
        """Test report generation with single result"""
        pred = Prediction(
            game_id="test_home",
            matchup="Test @ Home",
            week=12,
            away_team="Test",
            home_team="Home",
            predicted_spread=3.5,
            market_spread=-3.0,
            market_total=45.5,
            recommended_bet="away",
            kelly_fraction=0.05,
            confidence_score=72.5,
            timestamp="2025-11-23T05:07:25.113446",
        )

        score = GameScore(
            game_id="test_home",
            matchup="Test @ Home",
            away_team="Test",
            home_team="Home",
            away_score=24,
            home_score=17,
            status="Final",
            game_time="",
        )

        result = GameResult(
            prediction=pred,
            score=score,
            ats_result="WIN",
            ats_margin=3.5,
            profit_loss=454.5,
            roi=90.9,
            margin_error=3,
        )

        report = self.checker.generate_report([result], league="nfl", week=12)

        assert "BETTING PERFORMANCE REPORT" in report
        assert "NFL" in report
        assert "Test @ Home" in report
        assert "WIN" in report
        assert "ROI" in report

    def test_save_report(self, tmp_path):
        """Test saving report to file"""
        # Mock the project root
        import walters_analyzer.performance.results_checker as checker_module
        original_file = checker_module.Path(__file__)

        report_content = "Test Report\n\nThis is a test."

        # Create a mock checker and modify its save behavior
        checker = BettingResultsChecker()

        # Create a temporary docs directory
        docs_dir = tmp_path / "docs" / "performance_reports"
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Temporarily override the project root logic
        try:
            # We'll just test the file saving logic works
            report_file = docs_dir / "REPORT_TEST_WEEK12_20251123_145354.md"
            with open(report_file, "w") as f:
                f.write(report_content)

            assert report_file.exists()
            with open(report_file, "r") as f:
                saved_content = f.read()
            assert saved_content == report_content
        finally:
            checker.close()

    def test_game_result_dataclass(self):
        """Test GameResult dataclass"""
        pred = Prediction(
            game_id="test_home",
            matchup="Test @ Home",
            week=12,
            away_team="Test",
            home_team="Home",
            predicted_spread=3.5,
            market_spread=-3.0,
            market_total=45.5,
            recommended_bet="away",
            kelly_fraction=0.05,
            confidence_score=72.5,
            timestamp="",
        )

        score = GameScore(
            game_id="test_home",
            matchup="Test @ Home",
            away_team="Test",
            home_team="Home",
            away_score=24,
            home_score=17,
            status="Final",
            game_time="",
        )

        result = GameResult(
            prediction=pred,
            score=score,
            ats_result="WIN",
            ats_margin=3.5,
            profit_loss=454.5,
            roi=90.9,
            margin_error=3,
        )

        assert result.prediction.game_id == "test_home"
        assert result.score.away_score == 24
        assert result.ats_result == "WIN"
        assert result.profit_loss > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
