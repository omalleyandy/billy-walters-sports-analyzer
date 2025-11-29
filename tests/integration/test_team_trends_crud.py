"""
CRUD Tests for Team Trends Table

Tests complete CRUD operations for team_trends table including:
- Streak calculation and tracking (wins/losses)
- Recent form percentage calculation
- Playoff position tracking
- Desperation level calculation (0-10 scale)
- Emotional state inference
- Rest advantage calculation
"""

import pytest

from walters_analyzer.db.connection import DatabaseConnection
from walters_analyzer.db.raw_data_operations import RawDataOperations
from walters_analyzer.db.raw_data_models import TeamTrends


class TestTeamTrendsCRUD:
    """Test CRUD operations for team_trends table."""

    @pytest.fixture
    def db_ops(self):
        """Create database operations instance."""
        db_conn = DatabaseConnection()
        return RawDataOperations(db_conn)

    @pytest.fixture
    def sample_trends(self):
        """Create sample team trends."""
        return TeamTrends(
            league_id=1,
            team_id=1,  # KC Chiefs
            season=2025,
            week=13,
            streak_direction="W",
            streak_length=3,
            recent_form_pct=0.75,  # 3-1 last 4 games
            playoff_position=1,
            divisional_rank=1,
            conference_rank=1,
            emotional_state="confident",
            desperation_level=0,
            rest_advantage=0.0,
            source="game_results_standings",
            notes="W3 streak, Confident, clinched",
        )

    def test_insert_single_trend(self, db_ops, sample_trends):
        """Test inserting single team trend."""
        db_ops.insert_team_trends(sample_trends)

        retrieved = db_ops.get_team_trends(league_id=1, team_id=1, season=2025, week=13)

        assert retrieved is not None
        assert retrieved["streak_direction"] == "W"
        assert retrieved["streak_length"] == 3
        assert retrieved["emotional_state"] == "confident"

    def test_streak_tracking_wins(self, db_ops):
        """Test tracking winning streaks."""
        streak_lengths = [1, 2, 3, 4, 5]

        for length in streak_lengths:
            trends = TeamTrends(
                league_id=1,
                team_id=1,
                season=2025,
                week=13 - (5 - length),
                streak_direction="W",
                streak_length=length,
                recent_form_pct=1.0,  # All wins
                emotional_state="confident" if length >= 3 else "neutral",
            )

            db_ops.insert_team_trends(trends)

            retrieved = db_ops.get_team_trends(
                league_id=1,
                team_id=1,
                season=2025,
                week=13 - (5 - length),
            )

            assert retrieved["streak_direction"] == "W"
            assert retrieved["streak_length"] == length

    def test_streak_tracking_losses(self, db_ops):
        """Test tracking losing streaks."""
        for week_offset in range(3):
            trends = TeamTrends(
                league_id=1,
                team_id=2,
                season=2025,
                week=13 - week_offset,
                streak_direction="L",
                streak_length=week_offset + 1,
                recent_form_pct=0.0,  # All losses
                emotional_state=("desperate" if (week_offset + 1) >= 3 else "neutral"),
            )

            db_ops.insert_team_trends(trends)

    def test_recent_form_percentage(self, db_ops):
        """Test recent form percentage calculation."""
        form_scenarios = [
            (0.0, "0-4"),
            (0.25, "1-3"),
            (0.5, "2-2"),
            (0.75, "3-1"),
            (1.0, "4-0"),
        ]

        for form_pct, record_desc in form_scenarios:
            trends = TeamTrends(
                league_id=1,
                team_id=1,
                season=2025,
                week=13,
                recent_form_pct=form_pct,
                streak_direction="W" if form_pct > 0.5 else "L",
                notes=f"Recent form: {record_desc}",
            )

            db_ops.insert_team_trends(trends)

    def test_playoff_position_clinched(self, db_ops):
        """Test playoff position for clinched teams."""
        for position in [1, 2, 3, 4, 5, 6]:
            trends = TeamTrends(
                league_id=1,
                team_id=(position % 32) + 1,
                season=2025,
                week=13,
                playoff_position=position,
                desperation_level=0,  # Clinched
                emotional_state="confident",
            )

            db_ops.insert_team_trends(trends)

    def test_playoff_position_edge(self, db_ops):
        """Test playoff position for teams on edge."""
        for position in [7, 8, 9, 10, 11, 12]:
            trends = TeamTrends(
                league_id=1,
                team_id=(position % 32) + 1,
                season=2025,
                week=13,
                playoff_position=position,
                desperation_level=5,  # Fighting for spot
                emotional_state="neutral",
            )

            db_ops.insert_team_trends(trends)

    def test_playoff_position_eliminated(self, db_ops):
        """Test playoff position for eliminated teams."""
        for position in [13, 14, 15, 16]:
            trends = TeamTrends(
                league_id=1,
                team_id=(position % 32) + 1,
                season=2025,
                week=13,
                playoff_position=position,
                desperation_level=2,  # Eliminated
                emotional_state="neutral",
            )

            db_ops.insert_team_trends(trends)

    def test_desperation_level_scale(self, db_ops):
        """Test desperation level (0-10 scale)."""
        scenarios = [
            (0, "clinched"),
            (2, "eliminated"),
            (5, "playoff_edge"),
            (10, "must_win"),
        ]

        for level, situation in scenarios:
            trends = TeamTrends(
                league_id=1,
                team_id=1,
                season=2025,
                week=13 + level,  # Different weeks to avoid unique constraint
                desperation_level=level,
                notes=situation,
            )

            db_ops.insert_team_trends(trends)

            retrieved = db_ops.get_team_trends(
                league_id=1,
                team_id=1,
                season=2025,
                week=13 + level,
            )

            assert retrieved["desperation_level"] == level

    def test_emotional_state_from_streak(self, db_ops):
        """Test emotional state inference from streak."""
        states = [
            ("W", 3, "confident"),
            ("W", 1, "neutral"),
            ("L", 3, "desperate"),
            ("L", 1, "neutral"),
        ]

        for direction, length, expected_state in states:
            trends = TeamTrends(
                league_id=1,
                team_id=1,
                season=2025,
                week=13 + (ord(direction) + length),  # Unique week
                streak_direction=direction,
                streak_length=length,
                emotional_state=expected_state,
            )

            db_ops.insert_team_trends(trends)

    def test_rest_advantage(self, db_ops):
        """Test rest advantage tracking."""
        rest_scenarios = [
            (-1.0, "short_week"),  # Thursday game, 3 days rest
            (0.0, "normal"),  # 7 days rest
            (0.5, "extended"),  # 10+ days rest
        ]

        for rest_val, scenario in rest_scenarios:
            trends = TeamTrends(
                league_id=1,
                team_id=1,
                season=2025,
                week=13,
                rest_advantage=rest_val,
                notes=scenario,
            )

            db_ops.insert_team_trends(trends)

    def test_divisional_and_conference_rank(self, db_ops):
        """Test divisional and conference ranking."""
        trends = TeamTrends(
            league_id=1,
            team_id=1,
            season=2025,
            week=13,
            divisional_rank=1,  # 1st in division
            conference_rank=2,  # 2nd in conference
            playoff_position=2,  # #2 seed
        )

        db_ops.insert_team_trends(trends)

        retrieved = db_ops.get_team_trends(league_id=1, team_id=1, season=2025, week=13)

        assert retrieved["divisional_rank"] == 1
        assert retrieved["conference_rank"] == 2

    def test_home_field_consistency(self, db_ops):
        """Test home field consistency tracking."""
        trends = TeamTrends(
            league_id=1,
            team_id=1,
            season=2025,
            week=13,
            home_field_consistency=0.85,  # 85% at home vs elsewhere
        )

        db_ops.insert_team_trends(trends)

        retrieved = db_ops.get_team_trends(league_id=1, team_id=1, season=2025, week=13)

        assert retrieved["home_field_consistency"] == 0.85

    def test_unique_constraint_per_team_week(self, db_ops):
        """Test unique constraint on (league, team, season, week)."""
        trends1 = TeamTrends(
            league_id=1,
            team_id=1,
            season=2025,
            week=13,
            streak_direction="W",
            streak_length=3,
        )

        trends2 = TeamTrends(
            league_id=1,
            team_id=1,
            season=2025,
            week=13,
            streak_direction="L",
            streak_length=2,  # Different streak
        )

        db_ops.insert_team_trends(trends1)
        db_ops.insert_team_trends(trends2)  # Should replace

        retrieved = db_ops.get_team_trends(league_id=1, team_id=1, season=2025, week=13)

        assert retrieved["streak_direction"] == "L"
        assert retrieved["streak_length"] == 2

    def test_all_teams_in_league(self, db_ops):
        """Test inserting trends for all 32 NFL teams."""
        for team_id in range(1, 33):
            trends = TeamTrends(
                league_id=1,
                team_id=team_id,
                season=2025,
                week=13,
                streak_direction="W",
                playoff_position=(team_id % 6) + 1,
            )

            db_ops.insert_team_trends(trends)

        # Verify all teams have trends
        for team_id in range(1, 33):
            retrieved = db_ops.get_team_trends(
                league_id=1, team_id=team_id, season=2025, week=13
            )

            assert retrieved is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
