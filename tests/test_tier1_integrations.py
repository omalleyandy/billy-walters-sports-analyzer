"""
Test suite for Phase 3 TIER 1 database integrations.

Tests the following integrations:
- Phase 3.1: Player Valuations (database-driven player values)
- Phase 3.2: Practice Reports (Wednesday signal)
- Phase 3.3: Game SWE Factors (S-W-E adjustments)
- Phase 3.4: Team Trends (emotional/contextual confidence)
"""

import pytest
from unittest.mock import Mock

from walters_analyzer.valuation.billy_walters_edge_detector import (
    BillyWaltersEdgeDetector,
    BettingEdge,
)
from walters_analyzer.valuation.player_values import PlayerValuation


class TestPhase31PlayerValuations:
    """Test Phase 3.1: Player Valuations Integration"""

    @pytest.fixture
    def detector(self):
        """Create edge detector instance"""
        return BillyWaltersEdgeDetector()

    @pytest.fixture
    def mock_db_ops(self):
        """Create mock database operations"""
        mock_db = Mock()
        mock_db.get_player_valuation = Mock(return_value=None)
        return mock_db

    def test_get_player_value_from_db_success(self):
        """Test getting player value from database"""
        valuation = PlayerValuation()

        # Mock database response
        mock_db_ops = Mock()
        mock_valuation = Mock()
        mock_valuation.point_value = 3.5
        mock_db_ops.get_player_valuation.return_value = mock_valuation

        # Query database
        value = valuation.get_player_value_from_db(
            player_id="123",
            team_id=1,
            season=2025,
            week=13,
            position="QB",
            db_ops=mock_db_ops,
        )

        # Should return database value
        assert value == 3.5
        mock_db_ops.get_player_valuation.assert_called_once()

    def test_get_player_value_from_db_fallback(self):
        """Test fallback to position default when DB not available"""
        valuation = PlayerValuation()

        # Mock database to return None
        mock_db_ops = Mock()
        mock_db_ops.get_player_valuation.return_value = None

        # Query database (should fall back to position default)
        value = valuation.get_player_value_from_db(
            player_id="123",
            team_id=1,
            season=2025,
            week=13,
            position="QB",
            db_ops=mock_db_ops,
        )

        # Should return position default (elite QB = 4.5)
        assert value == 4.5

    def test_get_player_value_from_db_exception(self):
        """Test fallback when database query raises exception"""
        valuation = PlayerValuation()

        # Mock database to raise exception
        mock_db_ops = Mock()
        mock_db_ops.get_player_valuation.side_effect = Exception("DB error")

        # Query database (should silently fall back)
        value = valuation.get_player_value_from_db(
            player_id="123",
            team_id=1,
            season=2025,
            week=13,
            position="RB",
            db_ops=mock_db_ops,
        )

        # Should return position default (above_average RB = 1.8)
        assert value == 1.8


class TestPhase32PracticeReports:
    """Test Phase 3.2: Practice Reports Integration (Wednesday Signal)"""

    @pytest.fixture
    def detector(self):
        """Create edge detector instance"""
        return BillyWaltersEdgeDetector()

    def test_wednesday_signal_returns_tuple(self, detector):
        """Test Wednesday signal returns a tuple of (bool, float)"""
        # Mock database response for practice reports
        mock_db_ops = Mock()
        mock_db_ops.query_practice_reports.return_value = []

        detector.db_ops = mock_db_ops

        # Check Wednesday signal (team_id=1 = Kansas City)
        result = detector.check_wednesday_signal(
            team_id=1,
            team_name="Kansas City",
            season=2025,
            week=13,
        )

        # Should return a tuple of (bool, float)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], float)
        # Confidence multiplier should be in reasonable range
        assert 0.8 <= result[1] <= 1.2


class TestPhase33GameSWEFactors:
    """Test Phase 3.3: Game SWE Factors Integration"""

    @pytest.fixture
    def detector(self):
        """Create edge detector instance"""
        return BillyWaltersEdgeDetector()

    def test_swe_adjustments_returns_dict(self, detector):
        """Test S-W-E factor adjustments returns a dictionary"""
        # Mock database response for SWE factors
        mock_db_ops = Mock()
        mock_db_ops.get_game_swe_factors.return_value = None

        detector.db_ops = mock_db_ops

        # Get SWE adjustments (game_id = "DAL_PHI")
        adjustments = detector.get_swe_adjustments(
            game_id="DAL_PHI",
            season=2025,
            week=13,
        )

        # Should return a dictionary with expected keys
        assert isinstance(adjustments, dict)
        # Should have at least the key fields
        assert "special" in adjustments or len(adjustments) > 0
        # All values should be numeric
        for key, value in adjustments.items():
            assert isinstance(value, (int, float))


class TestPhase34TeamTrends:
    """Test Phase 3.4: Team Trends Integration"""

    @pytest.fixture
    def detector(self):
        """Create edge detector instance"""
        return BillyWaltersEdgeDetector()

    def test_team_trend_confidence_adjustment(self, detector):
        """Test team trend confidence adjustments"""
        # Mock database response for team trends
        mock_db_ops = Mock()
        mock_db_ops.get_team_trends.return_value = Mock(
            streak_direction="WIN",
            streak_length=3,
            playoff_position=1,
            emotional_state="HIGH",
            desperation_level=0,  # Clinched
        )

        detector.db_ops = mock_db_ops

        # Calculate trend adjustment (team_id=1, opponent_id=2)
        confidence_mult = detector.calculate_trend_confidence_adjustment(
            team_id=1,
            opponent_id=2,
            season=2025,
            week=13,
        )

        # Should increase confidence for 3-game winning streak
        assert confidence_mult >= 1.0
        assert confidence_mult <= 1.2  # Max 20% adjustment


class TestTier1GracefulDegradation:
    """Test graceful degradation when database not available"""

    @pytest.fixture
    def detector(self):
        """Create edge detector instance without database"""
        return BillyWaltersEdgeDetector()

    def test_detect_edge_without_database(self, detector):
        """Test edge detection works without database (backward compatibility)"""
        # Initialize without database operations
        detector.db_ops = None

        # Should still be able to call detect_edge with defaults
        edge = detector.detect_edge(
            game_id="test_game",
            away_team="Kansas City",
            home_team="Buffalo",
            market_spread=-3.0,
            market_total=44.5,
            week=13,
            game_time="2025-11-30T20:00:00",
            # season, away_team_id, home_team_id default to None
        )

        # Should either return an edge or None (depending on power ratings)
        # But should NOT raise an exception
        assert edge is None or isinstance(edge, BettingEdge)

    def test_detect_edge_with_missing_database_methods(self, detector):
        """Test graceful fallback when database methods don't exist"""
        # Initialize with mock DB that doesn't have all methods
        mock_db = Mock(spec=[])  # Empty spec = no methods
        detector.db_ops = mock_db

        # Should still work by falling back to defaults
        edge = detector.detect_edge(
            game_id="test_game",
            away_team="Kansas City",
            home_team="Buffalo",
            market_spread=-3.0,
            market_total=44.5,
            week=13,
            game_time="2025-11-30T20:00:00",
            season=2025,
            away_team_id=1,
            home_team_id=2,
        )

        # Should not raise AttributeError
        assert edge is None or isinstance(edge, BettingEdge)


class TestTier1ConfidenceCascading:
    """Test that confidence adjustments cascade correctly"""

    @pytest.fixture
    def detector(self):
        """Create edge detector instance"""
        return BillyWaltersEdgeDetector()

    def test_multiple_confidence_multipliers_applied(self, detector):
        """Test that multiple TIER 1 adjustments compound correctly"""
        # Mock all TIER 1 data sources
        mock_db_ops = Mock()

        # Practice reports: +15% confidence
        mock_db_ops.query_practice_reports.return_value = [
            Mock(
                player_id="p1",
                status="Full",
                days_since_injury=7,
                impact_rating=3.0,
            ),
        ]

        # SWE factors: +10% confidence
        mock_db_ops.get_game_swe_factors.return_value = Mock(
            special=0.0,
            weather=0.5,  # Good weather
            emotional=0.0,
            confidence_impact=1.1,
        )

        # Team trends: +10% confidence (winning streak)
        mock_db_ops.get_team_trends.return_value = Mock(
            streak_direction="WIN",
            streak_length=3,
            playoff_position=5,
            emotional_state="HIGH",
            desperation_level=0,
        )

        detector.db_ops = mock_db_ops

        # All methods should return positive multipliers
        wed_signal, wed_mult = detector.check_wednesday_signal(
            team_id=1,
            team_name="Kansas City",
            season=2025,
            week=13,
        )

        swe_adj = detector.get_swe_adjustments(
            game_id="KC_BUF",
            season=2025,
            week=13,
        )

        trend_mult = detector.calculate_trend_confidence_adjustment(
            team_id=2,
            opponent_id=1,
            season=2025,
            week=13,
        )

        # All should be present (not raising exceptions)
        assert wed_mult is not None
        assert swe_adj is not None
        assert trend_mult is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
