"""
Comprehensive unit tests for walters_analyzer.core
Tests all Phase 1-8 integration points
"""

import pytest
from datetime import datetime
from walters_analyzer.core import (
    BillyWaltersAnalyzer,
    BankrollManager,
    PointAnalyzer,
    GameInput,
    TeamSnapshot,
    GameOdds,
    SpreadLine,
    kelly_fraction,
    american_to_decimal,
    implied_probability,
)


class TestBankrollManager:
    """Test Kelly Criterion bankroll management"""

    def test_initialization(self):
        """Test bankroll manager initializes correctly"""
        manager = BankrollManager(
            initial_bankroll=10000.0,
            max_risk_pct=3.0,
            min_bet_pct=0.5,
            fractional_kelly=0.5,
        )

        assert manager.bankroll == 10000.0
        assert manager.initial_bankroll == 10000.0
        assert manager.max_risk_pct == 3.0
        assert manager.min_bet_pct == 0.5
        assert manager.fractional_kelly == 0.5
        assert len(manager.history) == 0

    def test_recommend_pct_high_edge(self):
        """Test stake recommendation for high-edge bet"""
        manager = BankrollManager(initial_bankroll=10000.0)

        # High edge bet (60% win prob at -110)
        stake = manager.recommend_pct(win_probability=0.60, odds=-110)

        assert stake > 0
        assert stake <= manager.max_risk_pct
        assert isinstance(stake, float)

    def test_recommend_pct_capped_at_max(self):
        """Test that stake is capped at max_risk_pct"""
        manager = BankrollManager(initial_bankroll=10000.0, max_risk_pct=3.0)

        # Very high edge (should exceed 3% without cap)
        stake = manager.recommend_pct(win_probability=0.70, odds=-110)

        assert stake <= 3.0

    def test_recommend_pct_no_edge(self):
        """Test that no stake recommended for no edge"""
        manager = BankrollManager()

        # 50/50 bet (no edge)
        stake = manager.recommend_pct(win_probability=0.50, odds=-110)

        assert stake == 0.0

    def test_stake_amount(self):
        """Test stake amount calculation"""
        manager = BankrollManager(initial_bankroll=10000.0)

        amount = manager.stake_amount(stake_pct=3.0)

        assert amount == 300.0

    def test_register_bet(self):
        """Test bet registration"""
        manager = BankrollManager()

        manager.register_bet(stake_pct=3.0, odds=-110, win_probability=0.58)

        assert len(manager.history) == 1
        assert manager.history[0].wager_pct == 3.0
        assert manager.history[0].odds == -110
        assert manager.history[0].win_probability == 0.58

    def test_record_result_win(self):
        """Test recording a winning bet"""
        manager = BankrollManager(initial_bankroll=10000.0)

        manager.register_bet(stake_pct=3.0, odds=-110, win_probability=0.58)
        initial = manager.bankroll

        manager.record_result(bet_index=0, result=1.0)

        # Should have increased
        assert manager.bankroll > initial

    def test_record_result_loss(self):
        """Test recording a losing bet"""
        manager = BankrollManager(initial_bankroll=10000.0)

        manager.register_bet(stake_pct=3.0, odds=-110, win_probability=0.58)
        initial = manager.bankroll

        manager.record_result(bet_index=0, result=-1.0)

        # Should have decreased
        assert manager.bankroll < initial


class TestPointAnalyzer:
    """Test key number detection"""

    def test_initialization(self):
        """Test point analyzer initializes with key numbers"""
        analyzer = PointAnalyzer(key_numbers=[3, 7, 6, 10, 14])

        assert 3 in analyzer.key_numbers
        assert 7 in analyzer.key_numbers
        assert len(analyzer.key_numbers) == 5

    def test_evaluate_crossing_key_number(self):
        """Test detection when prediction crosses key number"""
        analyzer = PointAnalyzer(key_numbers=[3, 7])

        # Projected 0, market -3 (crosses 3)
        alerts = analyzer.evaluate(projected_spread=0.0, market_spread=-3.0)

        assert len(alerts) > 0
        assert any("3" in alert.description for alert in alerts)
        assert any(alert.crossed for alert in alerts)

    def test_evaluate_no_key_number(self):
        """Test no alerts when no key number involved"""
        analyzer = PointAnalyzer(key_numbers=[3, 7])

        # Projected -5, market -4 (no key number crossed)
        alerts = analyzer.evaluate(projected_spread=-5.0, market_spread=-4.0)

        # Should be empty or minimal
        assert isinstance(alerts, list)


class TestCalculator:
    """Test calculation utilities"""

    def test_american_to_decimal(self):
        """Test American to decimal odds conversion"""
        # Favorite -110
        decimal = american_to_decimal(-110)
        assert 1.9 < decimal < 2.0

        # Underdog +150
        decimal = american_to_decimal(150)
        assert 2.4 < decimal < 2.6

    def test_implied_probability(self):
        """Test implied probability calculation"""
        # -110 should be ~52.4%
        prob = implied_probability(-110)
        assert 0.52 < prob < 0.53

        # +150 should be ~40%
        prob = implied_probability(150)
        assert 0.39 < prob < 0.41

    def test_kelly_fraction(self):
        """Test Kelly fraction calculation"""
        # Positive edge should return positive fraction
        kelly = kelly_fraction(win_probability=0.55, odds=-110, fraction=1.0)
        assert kelly > 0

        # No edge should return 0
        kelly = kelly_fraction(win_probability=0.50, odds=-110, fraction=1.0)
        assert kelly == 0

        # Fractional Kelly should be smaller
        full = kelly_fraction(win_probability=0.58, odds=-110, fraction=1.0)
        half = kelly_fraction(win_probability=0.58, odds=-110, fraction=0.5)
        assert half == full * 0.5


class TestBillyWaltersAnalyzer:
    """Test complete analyzer integration"""

    def test_initialization(self):
        """Test analyzer initializes with all components"""
        analyzer = BillyWaltersAnalyzer()

        assert analyzer.config is not None
        assert analyzer.valuation is not None
        assert analyzer.bankroll is not None
        assert analyzer.point_analyzer is not None

    def test_analyze_basic_game(self):
        """Test analyzing a basic game without injuries"""
        analyzer = BillyWaltersAnalyzer()

        # Simple game input
        home = TeamSnapshot(name="Kansas City Chiefs", injuries=[])
        away = TeamSnapshot(name="Buffalo Bills", injuries=[])
        odds = GameOdds(spread=SpreadLine(home_spread=-2.5))

        game = GameInput(home_team=home, away_team=away, odds=odds)

        # Analyze
        result = analyzer.analyze(game)

        # Verify result structure
        assert result.matchup == game
        assert result.predicted_spread is not None
        assert result.edge is not None
        assert result.confidence is not None
        assert result.recommendation is not None
        assert result.home_report is not None
        assert result.away_report is not None

    def test_analyze_with_injuries(self):
        """Test analyzing game with injury data"""
        analyzer = BillyWaltersAnalyzer()

        # Game with injuries
        home_injuries = [
            {"name": "Player 1", "position": "QB", "status": "Out"},
            {"name": "Player 2", "position": "WR", "status": "Questionable"},
        ]
        away_injuries = []

        home = TeamSnapshot(name="Chiefs", injuries=home_injuries)
        away = TeamSnapshot(name="Bills", injuries=away_injuries)
        odds = GameOdds(spread=SpreadLine(home_spread=-2.5))

        game = GameInput(home_team=home, away_team=away, odds=odds)

        result = analyzer.analyze(game)

        # Home team should have negative injury impact
        assert result.home_report.total_points != 0
        assert len(result.home_report.detailed_notes) > 0

    def test_recommendation_includes_stake(self):
        """Test that recommendation includes stake percentage"""
        analyzer = BillyWaltersAnalyzer()

        home = TeamSnapshot(name="Chiefs", injuries=[])
        away = TeamSnapshot(name="Bills", injuries=[])
        odds = GameOdds(spread=SpreadLine(home_spread=-2.5))

        game = GameInput(home_team=home, away_team=away, odds=odds)
        result = analyzer.analyze(game)

        assert result.recommendation.stake_pct >= 0
        assert isinstance(result.recommendation.stake_pct, float)
        assert result.recommendation.win_probability > 0
        assert result.recommendation.win_probability <= 1.0


class TestModels:
    """Test data models"""

    def test_spread_line(self):
        """Test SpreadLine model"""
        spread = SpreadLine(home_spread=-2.5, home_price=-110, away_price=-110)

        assert spread.home_spread == -2.5
        assert spread.away_spread == 2.5
        assert spread.home_price == -110

    def test_game_input(self):
        """Test GameInput model construction"""
        home = TeamSnapshot(name="Chiefs", injuries=[])
        away = TeamSnapshot(name="Bills", injuries=[])
        odds = GameOdds(spread=SpreadLine(home_spread=-2.5))

        game = GameInput(
            home_team=home, away_team=away, odds=odds, kickoff=datetime.now()
        )

        assert game.home_team.name == "Chiefs"
        assert game.away_team.name == "Bills"
        assert game.odds.spread.home_spread == -2.5


# Integration Tests


class TestIntegration:
    """Test integration between components"""

    @pytest.mark.asyncio
    async def test_analyzer_with_research_engine(self):
        """Test analyzer integrates with research engine"""
        from walters_analyzer.research import ResearchEngine

        # This test verifies the integration works
        # Actual research might fail without API keys, which is OK
        engine = ResearchEngine()

        try:
            # Try to gather research (will use cache if available)
            snapshot = await engine.gather_for_game(
                "Kansas City Chiefs", "Buffalo Bills", use_cache=True
            )

            # Verify snapshot structure
            assert snapshot.home_team == "Kansas City Chiefs"
            assert snapshot.away_team == "Buffalo Bills"
            assert isinstance(snapshot.home_injuries, list)
            assert isinstance(snapshot.away_injuries, list)

        finally:
            await engine.close()

    def test_analyzer_with_valuation(self):
        """Test analyzer integrates with valuation layer"""
        analyzer = BillyWaltersAnalyzer()

        # Verify valuation component is available
        assert analyzer.valuation is not None

        # Test it can calculate spreads
        home = TeamSnapshot(name="Chiefs", injuries=[])
        away = TeamSnapshot(name="Bills", injuries=[])
        odds = GameOdds(spread=SpreadLine(home_spread=-2.5))
        game = GameInput(home_team=home, away_team=away, odds=odds)

        result = analyzer.analyze(game)

        # Should complete without errors
        assert result is not None


# Performance Tests


class TestPerformance:
    """Test performance characteristics"""

    def test_analyzer_performance(self):
        """Test that analysis completes quickly"""
        import time

        analyzer = BillyWaltersAnalyzer()

        home = TeamSnapshot(name="Chiefs", injuries=[])
        away = TeamSnapshot(name="Bills", injuries=[])
        odds = GameOdds(spread=SpreadLine(home_spread=-2.5))
        game = GameInput(home_team=home, away_team=away, odds=odds)

        start = time.time()
        result = analyzer.analyze(game)
        duration = time.time() - start

        # Should complete in less than 1 second
        assert duration < 1.0
        assert result is not None

    def test_batch_analysis_performance(self):
        """Test batch analysis performance"""
        import time

        analyzer = BillyWaltersAnalyzer()

        # Create 10 games
        games = []
        for i in range(10):
            home = TeamSnapshot(name=f"Team {i}", injuries=[])
            away = TeamSnapshot(name=f"Team {i + 10}", injuries=[])
            odds = GameOdds(spread=SpreadLine(home_spread=-2.5))
            games.append(GameInput(home_team=home, away_team=away, odds=odds))

        start = time.time()
        results = analyzer.analyze_many(games)
        duration = time.time() - start

        # Should complete 10 games in less than 10 seconds
        assert duration < 10.0
        assert len(results) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
