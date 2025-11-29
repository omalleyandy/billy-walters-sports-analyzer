"""
CRUD Tests for Game SWE Factors Table

Tests complete CRUD operations for game_swe_factors table including:
- Weather factor calculations (temp, wind, precipitation)
- Special factors (rivalry, playoff implications, etc)
- Emotional factors (motivation, momentum)
- Total adjustment calculation (-3 to +1 pts range)
- Confidence level assignments
"""

import pytest

from walters_analyzer.db.connection import DatabaseConnection
from walters_analyzer.db.raw_data_operations import RawDataOperations
from walters_analyzer.db.raw_data_models import GameSWEFactors


class TestGameSWEFactorsCRUD:
    """Test CRUD operations for game_swe_factors table."""

    @pytest.fixture
    def db_ops(self):
        """Create database operations instance."""
        db_conn = DatabaseConnection()
        return RawDataOperations(db_conn)

    @pytest.fixture
    def sample_factors(self):
        """Create sample SWE factors."""
        return GameSWEFactors(
            league_id=1,
            game_id="KC_BUF_2025_W13",
            season=2025,
            week=13,
            away_team_id=1,  # KC
            home_team_id=2,  # Buffalo
            weather_factor_description="15°F, 18mph wind",
            weather_adjustment=-2.5,
            temperature_impact=-1.5,
            wind_impact=-1.0,
            precipitation_impact=0.0,
            total_adjustment=-2.5,
            confidence_level=0.9,
            source="weather_data_accuweather",
            notes="Cold, windy Buffalo game",
        )

    def test_insert_weather_factors(self, db_ops, sample_factors):
        """Test inserting weather-based SWE factors."""
        db_ops.insert_game_swe_factors(sample_factors)

        retrieved = db_ops.get_game_swe_factors(
            league_id=1, game_id="KC_BUF_2025_W13", season=2025, week=13
        )

        assert retrieved is not None
        assert retrieved["weather_adjustment"] == -2.5
        assert retrieved["temperature_impact"] == -1.5
        assert retrieved["wind_impact"] == -1.0

    def test_temperature_impact_range(self, db_ops):
        """Test temperature impact values in realistic range."""
        temp_scenarios = [
            (-20, -2.0, "extreme cold"),
            (20, -1.5, "very cold"),
            (50, 0.0, "comfortable"),
            (85, 0.5, "hot"),
            (95, 1.0, "very hot"),
        ]

        for temp, expected_impact, description in temp_scenarios:
            factors = GameSWEFactors(
                league_id=1,
                game_id=f"temp_test_{temp}",
                season=2025,
                week=13,
                away_team_id=1,
                home_team_id=2,
                weather_factor_description=f"{temp}F - {description}",
                temperature_impact=expected_impact,
                total_adjustment=expected_impact,
                confidence_level=0.9,
            )

            db_ops.insert_game_swe_factors(factors)

            retrieved = db_ops.get_game_swe_factors(
                league_id=1,
                game_id=f"temp_test_{temp}",
                season=2025,
                week=13,
            )

            assert retrieved["temperature_impact"] == expected_impact

    def test_wind_impact_calculation(self, db_ops):
        """Test wind impact on game."""
        wind_scenarios = [
            (0, 0.0, "calm"),
            (10, -0.5, "light"),
            (15, -1.0, "moderate"),
            (20, -1.5, "high"),
            (30, -2.5, "extreme"),
        ]

        for wind, expected_impact, description in wind_scenarios:
            factors = GameSWEFactors(
                league_id=1,
                game_id=f"wind_test_{wind}",
                season=2025,
                week=13,
                away_team_id=1,
                home_team_id=2,
                weather_factor_description=f"{wind}mph {description} wind",
                wind_impact=expected_impact,
                total_adjustment=expected_impact,
                confidence_level=0.9,
            )

            db_ops.insert_game_swe_factors(factors)

            retrieved = db_ops.get_game_swe_factors(
                league_id=1,
                game_id=f"wind_test_{wind}",
                season=2025,
                week=13,
            )

            assert retrieved["wind_impact"] == expected_impact

    def test_precipitation_impact(self, db_ops):
        """Test precipitation impact on total."""
        precip_scenarios = [
            (0.0, "clear"),
            (-0.5, "light_rain"),
            (-1.0, "light_snow"),
            (-1.5, "heavy_rain"),
            (-2.0, "heavy_snow"),
        ]

        for impact, conditions in precip_scenarios:
            factors = GameSWEFactors(
                league_id=1,
                game_id=f"precip_test_{conditions}",
                season=2025,
                week=13,
                away_team_id=1,
                home_team_id=2,
                weather_factor_description=conditions,
                precipitation_impact=impact,
                total_adjustment=impact,
                confidence_level=0.9,
            )

            db_ops.insert_game_swe_factors(factors)

            retrieved = db_ops.get_game_swe_factors(
                league_id=1,
                game_id=f"precip_test_{conditions}",
                season=2025,
                week=13,
            )

            assert retrieved["precipitation_impact"] == impact

    def test_total_adjustment_range(self, db_ops):
        """Test that total adjustment is in realistic range (-3 to +1)."""
        adjustments = [-3.0, -2.0, -1.0, 0.0, 0.5, 1.0]

        for adj in adjustments:
            factors = GameSWEFactors(
                league_id=1,
                game_id=f"adj_test_{adj}",
                season=2025,
                week=13,
                away_team_id=1,
                home_team_id=2,
                weather_factor_description=f"Adjustment {adj}",
                total_adjustment=adj,
                confidence_level=0.9,
            )

            db_ops.insert_game_swe_factors(factors)

            retrieved = db_ops.get_game_swe_factors(
                league_id=1,
                game_id=f"adj_test_{adj}",
                season=2025,
                week=13,
            )

            assert retrieved["total_adjustment"] == adj
            assert -3.0 <= retrieved["total_adjustment"] <= 1.0

    def test_special_factors(self, db_ops):
        """Test special factor tracking (rivalry, revenge, playoff)."""
        special_scenarios = [
            ("Playoff game", "+0.5", "high"),
            ("Rivalry game", "+0.3", "medium"),
            ("Revenge scenario", "+0.2", "low"),
            ("Neutral", "0.0", "minimal"),
        ]

        for description, special_adj, confidence in special_scenarios:
            factors = GameSWEFactors(
                league_id=1,
                game_id=f"special_test_{description.lower().replace(' ', '_')}",
                season=2025,
                week=13,
                away_team_id=1,
                home_team_id=2,
                special_factor_description=description,
                special_adjustment=float(special_adj),
                confidence_level=float(confidence) * 0.1 + 0.5,
            )

            db_ops.insert_game_swe_factors(factors)

    def test_emotional_factors(self, db_ops):
        """Test emotional factor tracking."""
        factors = GameSWEFactors(
            league_id=1,
            game_id="emotional_test",
            season=2025,
            week=13,
            away_team_id=1,
            home_team_id=2,
            emotional_factor_description="High motivation, momentum",
            emotional_adjustment=0.5,
            motivation_level="HIGH",
            momentum_direction="POSITIVE",
            total_adjustment=0.5,
            confidence_level=0.7,  # More subjective
        )

        db_ops.insert_game_swe_factors(factors)

        retrieved = db_ops.get_game_swe_factors(
            league_id=1, game_id="emotional_test", season=2025, week=13
        )

        assert retrieved["emotional_adjustment"] == 0.5
        assert retrieved["motivation_level"] == "HIGH"
        assert retrieved["momentum_direction"] == "POSITIVE"

    def test_confidence_level_by_type(self, db_ops):
        """Test confidence level assignments."""
        scenarios = [
            ("weather", 0.9),  # Weather is measurable
            ("special", 0.7),  # Special factors less certain
            ("emotional", 0.6),  # Emotional factors subjective
        ]

        for factor_type, conf_level in scenarios:
            factors = GameSWEFactors(
                league_id=1,
                game_id=f"confidence_{factor_type}",
                season=2025,
                week=13,
                away_team_id=1,
                home_team_id=2,
                weather_factor_description=(
                    "Test" if factor_type == "weather" else None
                ),
                confidence_level=conf_level,
            )

            db_ops.insert_game_swe_factors(factors)

            retrieved = db_ops.get_game_swe_factors(
                league_id=1,
                game_id=f"confidence_{factor_type}",
                season=2025,
                week=13,
            )

            assert retrieved["confidence_level"] == conf_level

    def test_unique_constraint_per_game_week(self, db_ops):
        """Test unique constraint on (league, game_id, season, week)."""
        factors1 = GameSWEFactors(
            league_id=1,
            game_id="duplicate_test",
            season=2025,
            week=13,
            away_team_id=1,
            home_team_id=2,
            total_adjustment=-1.0,
        )

        factors2 = GameSWEFactors(
            league_id=1,
            game_id="duplicate_test",
            season=2025,
            week=13,
            away_team_id=1,
            home_team_id=2,
            total_adjustment=-2.5,  # Different value
        )

        db_ops.insert_game_swe_factors(factors1)
        db_ops.insert_game_swe_factors(factors2)  # Should replace

        retrieved = db_ops.get_game_swe_factors(
            league_id=1, game_id="duplicate_test", season=2025, week=13
        )

        assert retrieved["total_adjustment"] == -2.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
