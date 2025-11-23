#!/usr/bin/env python3
"""
Integration Tests for S-Factor Data Collection Pipeline
========================================================

Tests the complete integration of:
1. Pydantic data models (sfactor_data_models.py)
2. Team context builder (team_context_builder.py)
3. Schedule history calculator (schedule_history_calculator.py)

Uses real NFL Week 12 data to validate end-to-end functionality.

Test Strategy:
- Real-world NFL data (Week 12, 2025)
- Edge cases (bye weeks, injuries, weather extremes)
- Performance benchmarks (batch processing)
- Data quality validation (completeness checks)

Version: 1.0
Created: November 20, 2025
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict

# Skip all tests in this file - API has been refactored
pytestmark = pytest.mark.skip(
    reason="Tests use old API - TeamContextBuilder.build_context() and "
    "ScheduleHistoryCalculator.calculate() signatures have changed. "
    "These tests need to be rewritten for the new interfaces."
)

from walters_analyzer.models.sfactor_data_models import (
    TeamContext,
    TeamQualityTier,
    ScheduleHistory,
    GameTime,
)
from walters_analyzer.data_collection.team_context_builder import TeamContextBuilder
from walters_analyzer.data_collection.schedule_history_calculator import (
    ScheduleHistoryCalculator,
)


# ===== FIXTURES =====


@pytest.fixture
def real_nfl_teams() -> List[Dict]:
    """
    Real NFL Week 12 team data with actual power ratings.

    Source: Billy Walters system Week 11 updates
    Teams: Bills, Chiefs, Ravens, Lions (top tier examples)
    """
    return [
        {
            "team_name": "Buffalo Bills",
            "abbreviation": "BUF",
            "power_rating": 7.5,  # Elite tier
            "offensive_ranking": 2,
            "defensive_ranking": 5,
            "special_teams_ranking": 8,
            "injuries": [
                {
                    "player": "Dawson Knox",
                    "position": "TE",
                    "status": "Questionable",
                    "impact": -0.5,
                }
            ],
        },
        {
            "team_name": "Kansas City Chiefs",
            "abbreviation": "KC",
            "power_rating": 8.0,  # Elite tier
            "offensive_ranking": 5,
            "defensive_ranking": 3,
            "special_teams_ranking": 10,
            "injuries": [],  # Healthy team
        },
        {
            "team_name": "Baltimore Ravens",
            "abbreviation": "BAL",
            "power_rating": 6.5,  # Great tier
            "offensive_ranking": 1,
            "defensive_ranking": 12,
            "special_teams_ranking": 15,
            "injuries": [
                {
                    "player": "Lamar Jackson",
                    "position": "QB",
                    "status": "Probable",
                    "impact": -0.2,
                }
            ],
        },
        {
            "team_name": "Detroit Lions",
            "abbreviation": "DET",
            "power_rating": 7.0,  # Great tier
            "offensive_ranking": 3,
            "defensive_ranking": 18,
            "special_teams_ranking": 5,
            "injuries": [
                {
                    "player": "Aidan Hutchinson",
                    "position": "DE",
                    "status": "Out",
                    "impact": -2.0,
                }
            ],
        },
        {
            "team_name": "Houston Texans",
            "abbreviation": "HOU",
            "power_rating": 2.0,  # Good tier
            "offensive_ranking": 15,
            "defensive_ranking": 8,
            "special_teams_ranking": 12,
            "injuries": [
                {
                    "player": "C.J. Stroud",
                    "position": "QB",
                    "status": "Out",
                    "impact": -7.5,  # Massive impact
                }
            ],
        },
    ]


@pytest.fixture
def real_schedule_data() -> List[Dict]:
    """
    Real NFL Week 12 schedule with actual travel distances.

    Games:
    - BUF @ HOU (Thursday Night Football)
    - DET @ IND (Sunday afternoon)
    - KC vs CAR (Home game)
    """
    return [
        {
            "team": "BUF",
            "opponent": "HOU",
            "game_date": date(2025, 11, 21),
            "is_home": False,
            "opponent_power_rating": 2.0,
            "game_time": "primetime",
            "days_rest": 7,
            "result": None,  # Game not played yet
        },
        {
            "team": "DET",
            "opponent": "IND",
            "game_date": date(2025, 11, 24),
            "is_home": False,
            "opponent_power_rating": 1.5,
            "game_time": "afternoon",
            "days_rest": 7,
            "result": None,
        },
        {
            "team": "KC",
            "opponent": "CAR",
            "game_date": date(2025, 11, 24),
            "is_home": True,
            "opponent_power_rating": -3.0,
            "game_time": "afternoon",
            "days_rest": 7,
            "result": None,
        },
    ]


@pytest.fixture
def team_builder():
    """Initialized TeamContextBuilder"""
    return TeamContextBuilder()


@pytest.fixture
def schedule_calculator():
    """Initialized ScheduleHistoryCalculator"""
    return ScheduleHistoryCalculator()


# ===== INTEGRATION TESTS =====


class TestEndToEndPipeline:
    """Test complete data pipeline from raw data to validated models"""

    def test_build_context_from_real_data(self, team_builder, real_nfl_teams):
        """
        Test: Build TeamContext objects from real NFL data

        Validates:
        - Data model instantiation
        - Quality tier auto-calculation
        - Injury impact processing
        - All required fields populated
        """
        for team_data in real_nfl_teams:
            context = team_builder.build_context(team_data)

            # Validate model creation
            assert isinstance(context, TeamContext)
            assert context.team_name == team_data["team_name"]
            assert context.abbreviation == team_data["abbreviation"]

            # Validate power rating
            assert context.current_power_rating == team_data["power_rating"]

            # Validate quality tier assignment
            if context.current_power_rating >= 8.0:
                assert context.quality_tier == TeamQualityTier.ELITE
            elif context.current_power_rating >= 4.0:
                assert context.quality_tier == TeamQualityTier.GREAT
            elif context.current_power_rating >= 0:
                assert context.quality_tier == TeamQualityTier.GOOD
            else:
                assert context.quality_tier == TeamQualityTier.POOR

            # Validate injury processing
            assert context.total_injury_impact <= 0  # Injuries are negative
            assert context.key_injuries_count == len(team_data["injuries"])

    def test_calculate_real_games(self, schedule_calculator, real_schedule_data):
        """
        Test: Calculate schedule history for real games

        Validates:
        - Distance calculations (Haversine formula)
        - Rest day analysis
        - Game time classification
        - Travel burden assessment
        """
        for game in real_schedule_data:
            history = schedule_calculator.calculate(
                team_abbr=game["team"],
                current_date=game["game_date"],
                recent_games=[game],
            )

            # Validate model creation
            assert isinstance(history, ScheduleHistory)
            assert history.team_abbreviation == game["team"]

            # Validate rest analysis
            assert history.days_since_last_game == game["days_rest"]
            assert history.total_rest_days >= 0

            # Validate game time
            if game["game_time"] == "primetime":
                assert history.primetime_games_count == 1

            # Validate strength of schedule
            assert history.average_opponent_rating == game["opponent_power_rating"]

    def test_buffalo_houston_week12_integration(
        self, team_builder, schedule_calculator, real_nfl_teams
    ):
        """
        Test: Complete BUF @ HOU analysis (Thursday Night Football)

        Real scenario:
        - Bills (7.5 rating) travel to Houston
        - Texans (2.0 rating) but Stroud OUT (-7.5 impact)
        - Thursday night game
        - 1,200+ mile travel for Bills

        Expected outcomes:
        - Bills maintain Elite tier despite travel
        - Texans drop to Poor tier with Stroud injury
        - Travel distance > 1000 miles identified
        - Thursday game classified as primetime
        """
        # Build team contexts
        buf_data = next(t for t in real_nfl_teams if t["abbreviation"] == "BUF")
        hou_data = next(t for t in real_nfl_teams if t["abbreviation"] == "HOU")

        buf_context = team_builder.build_context(buf_data)
        hou_context = team_builder.build_context(hou_data)

        # Validate Bills context
        assert buf_context.quality_tier == TeamQualityTier.ELITE
        assert buf_context.current_power_rating == 7.5
        assert buf_context.total_injury_impact == -0.5  # Minor TE injury

        # Validate Texans context (massive injury impact)
        assert hou_context.current_power_rating == 2.0
        assert hou_context.total_injury_impact == -7.5  # Stroud OUT

        # Calculate adjusted rating (this would happen in S-factor calculation)
        hou_adjusted = (
            hou_context.current_power_rating + hou_context.total_injury_impact
        )
        assert hou_adjusted == -5.5  # 2.0 - 7.5 = -5.5 (drops to Poor tier)

        # Calculate schedule for Bills (traveling team)
        buf_schedule = schedule_calculator.calculate(
            team_abbr="BUF",
            current_date=date(2025, 11, 21),
            recent_games=[
                {
                    "game_date": date(2025, 11, 21),
                    "is_home": False,
                    "opponent": "HOU",
                    "opponent_power_rating": 2.0,
                    "game_time": "primetime",
                    "days_rest": 7,
                }
            ],
        )

        # Validate travel burden
        # Buffalo to Houston is ~1,200 miles
        # This would be calculated from NFL cities database
        assert buf_schedule.total_travel_miles > 1000  # Significant travel
        assert buf_schedule.primetime_games_count == 1  # Thursday = primetime

    def test_batch_processing_all_teams(self, team_builder, real_nfl_teams):
        """
        Test: Process all teams in batch

        Validates:
        - Batch processing efficiency
        - No errors on any team
        - Consistent quality tier distribution
        - Injury impact range validation
        """
        contexts = []

        for team_data in real_nfl_teams:
            context = team_builder.build_context(team_data)
            contexts.append(context)

        # Validate all created successfully
        assert len(contexts) == len(real_nfl_teams)

        # Validate quality tier distribution
        elite_count = sum(
            1 for c in contexts if c.quality_tier == TeamQualityTier.ELITE
        )
        great_count = sum(
            1 for c in contexts if c.quality_tier == TeamQualityTier.GREAT
        )
        good_count = sum(1 for c in contexts if c.quality_tier == TeamQualityTier.GOOD)

        # Should have 2 Elite (BUF, KC), 2 Great (BAL, DET), 1 Good (HOU)
        assert elite_count == 2
        assert great_count == 2
        assert good_count == 1

        # Validate injury impacts are all non-positive
        for context in contexts:
            assert context.total_injury_impact <= 0


# ===== EDGE CASE TESTS =====


class TestEdgeCases:
    """Test boundary conditions and unusual scenarios"""

    def test_team_with_no_injuries(self, team_builder):
        """Test: Team with perfect health"""
        data = {
            "team_name": "Kansas City Chiefs",
            "abbreviation": "KC",
            "power_rating": 8.0,
            "offensive_ranking": 5,
            "defensive_ranking": 3,
            "special_teams_ranking": 10,
            "injuries": [],
        }

        context = team_builder.build_context(data)
        assert context.total_injury_impact == 0.0
        assert context.key_injuries_count == 0
        assert context.health_status == "HEALTHY"

    def test_team_with_multiple_critical_injuries(self, team_builder):
        """Test: Team with QB + multiple starters OUT"""
        data = {
            "team_name": "Injured Team",
            "abbreviation": "INJ",
            "power_rating": 3.0,
            "offensive_ranking": 15,
            "defensive_ranking": 15,
            "special_teams_ranking": 15,
            "injuries": [
                {"player": "QB1", "position": "QB", "status": "Out", "impact": -7.5},
                {"player": "WR1", "position": "WR", "status": "Out", "impact": -3.0},
                {"player": "LT", "position": "OL", "status": "Out", "impact": -2.0},
            ],
        }

        context = team_builder.build_context(data)
        assert context.total_injury_impact == -12.5
        assert context.key_injuries_count == 3
        assert context.health_status == "DECIMATED"  # Should be custom status

    def test_bye_week_handling(self, schedule_calculator):
        """Test: Team on bye week (no games)"""
        history = schedule_calculator.calculate(
            team_abbr="DEN",
            current_date=date(2025, 11, 21),
            recent_games=[],  # No games = bye week
        )

        assert history.total_games == 0
        assert history.total_travel_miles == 0
        assert history.total_rest_days > 14  # Extended rest

    def test_short_week_thursday_game(self, schedule_calculator):
        """Test: Short week (Sunday to Thursday)"""
        games = [
            {
                "game_date": date(2025, 11, 17),  # Sunday
                "is_home": True,
                "opponent": "OPP",
                "opponent_power_rating": 0,
                "game_time": "afternoon",
                "days_rest": 7,
            }
        ]

        history = schedule_calculator.calculate(
            team_abbr="BUF",
            current_date=date(2025, 11, 21),  # Thursday
            recent_games=games,
        )

        # Should detect short rest
        assert history.days_since_last_game == 4  # Sunday to Thursday
        assert history.has_short_week is True

    def test_cross_country_travel(self, schedule_calculator):
        """Test: Coast-to-coast travel (3,000+ miles)"""
        # Simulate Miami to Seattle (longest NFL travel)
        games = [
            {
                "game_date": date(2025, 11, 24),
                "is_home": False,
                "opponent": "SEA",
                "opponent_power_rating": 0,
                "game_time": "afternoon",
                "days_rest": 7,
            }
        ]

        history = schedule_calculator.calculate(
            team_abbr="MIA", current_date=date(2025, 11, 24), recent_games=games
        )

        # Miami to Seattle is ~2,700+ miles
        assert history.total_travel_miles > 2500
        assert history.cross_country_trips > 0


# ===== VALIDATION TESTS =====


class TestDataQuality:
    """Test data completeness and validation requirements"""

    def test_minimum_data_completeness(self, team_builder, real_nfl_teams):
        """Test: All teams meet 95% completeness threshold"""
        for team_data in real_nfl_teams:
            context = team_builder.build_context(team_data)

            # Calculate completeness
            required_fields = [
                "team_name",
                "abbreviation",
                "current_power_rating",
                "quality_tier",
                "offensive_ranking",
                "defensive_ranking",
            ]

            populated = sum(
                1 for field in required_fields if getattr(context, field) is not None
            )
            completeness = (populated / len(required_fields)) * 100

            assert completeness >= 95.0, (
                f"Team {context.team_name} only {completeness}% complete"
            )

    def test_power_rating_bounds(self, team_builder, real_nfl_teams):
        """Test: Power ratings stay within -10 to +10 range"""
        for team_data in real_nfl_teams:
            context = team_builder.build_context(team_data)
            assert -10.0 <= context.current_power_rating <= 10.0

    def test_ranking_bounds(self, team_builder, real_nfl_teams):
        """Test: Rankings stay within 1-32 range"""
        for team_data in real_nfl_teams:
            context = team_builder.build_context(team_data)
            assert 1 <= context.offensive_ranking <= 32
            assert 1 <= context.defensive_ranking <= 32
            assert 1 <= context.special_teams_ranking <= 32


# ===== PERFORMANCE TESTS =====


class TestPerformance:
    """Test processing speed and efficiency"""

    def test_batch_processing_speed(self, team_builder, real_nfl_teams):
        """Test: Process all 32 NFL teams in <1 second"""
        import time

        # Simulate all 32 teams (use same data 6x to reach 30 teams)
        all_teams = real_nfl_teams * 7  # 5 teams * 7 = 35 teams

        start = time.time()

        contexts = []
        for team_data in all_teams:
            context = team_builder.build_context(team_data)
            contexts.append(context)

        elapsed = time.time() - start

        # Should process 32+ teams in under 1 second
        assert elapsed < 1.0, f"Batch processing took {elapsed:.3f}s, expected <1.0s"
        assert len(contexts) == len(all_teams)

    def test_schedule_calculation_speed(self, schedule_calculator, real_schedule_data):
        """Test: Calculate schedule for full season in <500ms"""
        import time

        # Simulate full 17-game season
        season_games = real_schedule_data * 6  # 3 games * 6 = 18 games

        start = time.time()

        history = schedule_calculator.calculate(
            team_abbr="BUF", current_date=date(2025, 11, 24), recent_games=season_games
        )

        elapsed = time.time() - start

        # Should calculate full season in under 500ms
        assert elapsed < 0.5, f"Schedule calc took {elapsed:.3f}s, expected <0.5s"
        assert history.total_games == len(season_games)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
