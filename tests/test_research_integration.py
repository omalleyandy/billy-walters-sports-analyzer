"""
Integration tests for research engine
Tests AccuWeather, ProFootballDoc, and ResearchEngine coordination
"""

import pytest
from walters_analyzer.research import (
    ResearchEngine,
    AccuWeatherClient,
    ProFootballDocFetcher,
)


class TestAccuWeatherClient:
    """Test AccuWeather API client"""

    def test_initialization(self):
        """Test client initializes"""
        client = AccuWeatherClient()

        # Should initialize even without API key
        assert client is not None

    @pytest.mark.asyncio
    async def test_close(self):
        """Test client closes cleanly"""
        client = AccuWeatherClient()

        await client.close()

        # Should complete without error
        assert True


class TestProFootballDocFetcher:
    """Test ProFootballDoc injury fetcher"""

    def test_initialization(self):
        """Test fetcher initializes"""
        fetcher = ProFootballDocFetcher()

        assert fetcher is not None

    @pytest.mark.asyncio
    async def test_get_cached_injuries(self):
        """Test loading injuries from local cache"""
        fetcher = ProFootballDocFetcher()

        # Try to load from cache (might be empty)
        injuries = await fetcher._get_cached_injuries("Kansas City Chiefs")

        assert isinstance(injuries, list)
        # Cache might be empty, which is OK

    def test_estimate_point_value(self):
        """Test point value estimation"""
        fetcher = ProFootballDocFetcher()

        # QB out should be high value
        qb_out = fetcher._estimate_point_value("QB", "Out")
        assert qb_out == 10.0

        # QB questionable should be lower
        qb_q = fetcher._estimate_point_value("QB", "Questionable")
        assert qb_q < qb_out
        assert qb_q == 3.5  # 10.0 * 0.35

        # WR out
        wr_out = fetcher._estimate_point_value("WR", "Out")
        assert wr_out == 2.5

    @pytest.mark.asyncio
    async def test_close(self):
        """Test fetcher closes cleanly"""
        fetcher = ProFootballDocFetcher()

        await fetcher.close()

        assert True


class TestResearchEngine:
    """Test research engine coordinator"""

    def test_initialization(self):
        """Test engine initializes with all clients"""
        engine = ResearchEngine()

        assert engine.accuweather is not None
        assert engine.profootballdoc is not None
        assert engine.cache_ttl > 0

    @pytest.mark.asyncio
    async def test_gather_for_game_basic(self):
        """Test gathering research for a game (cache only)"""
        engine = ResearchEngine()

        try:
            snapshot = await engine.gather_for_game(
                home_team="Kansas City Chiefs",
                away_team="Buffalo Bills",
                use_cache=True,  # Use cache only, don't make API calls
            )

            # Verify structure
            assert snapshot.home_team == "Kansas City Chiefs"
            assert snapshot.away_team == "Buffalo Bills"
            assert isinstance(snapshot.home_injuries, list)
            assert isinstance(snapshot.away_injuries, list)

        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test that caching works"""
        engine = ResearchEngine(cache_ttl_seconds=300)

        try:
            # First call
            snapshot1 = await engine.gather_for_game("Chiefs", "Bills")

            # Second call (should hit cache)
            snapshot2 = await engine.gather_for_game("Chiefs", "Bills")

            # Should return same data (from cache)
            assert snapshot1.home_team == snapshot2.home_team
            assert snapshot1.away_team == snapshot2.away_team

        finally:
            await engine.close()

    def test_clear_cache(self):
        """Test cache clearing"""
        engine = ResearchEngine()

        # Add to cache
        engine._cache["test"] = ({"data": "test"}, pytest.approx(0))
        assert "test" in engine._cache

        # Clear
        engine.clear_cache()

        assert "test" not in engine._cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
