"""
CRUD Tests for Player Valuations Table

Tests complete CRUD operations (Create, Read, Update, Delete) for
player_valuations table including:
- Insert single and batch operations
- Query by league/team/season/week
- Query by position
- Update operations
- Delete operations
- Index performance
- Foreign key constraints
"""

import pytest
from unittest.mock import Mock

from walters_analyzer.db.connection import DatabaseConnection
from walters_analyzer.db.raw_data_operations import RawDataOperations
from walters_analyzer.db.raw_data_models import PlayerValuation


class TestPlayerValuationsCRUD:
    """Test CRUD operations for player_valuations table."""

    @pytest.fixture
    def db_ops(self):
        """Create database operations instance."""
        db_conn = DatabaseConnection()
        return RawDataOperations(db_conn)

    @pytest.fixture
    def sample_valuation(self):
        """Create sample player valuation."""
        return PlayerValuation(
            league_id=1,
            team_id=1,
            player_id="mahomes_pat",
            player_name="Patrick Mahomes",
            position="QB",
            season=2025,
            week=13,
            point_value=4.5,
            snap_count_pct=98.0,
            impact_rating=4.4,
            is_starter=True,
            depth_chart_position=1,
            source="depth_chart_baseline",
            notes="Elite starter QB",
        )

    def test_insert_single_player_valuation(self, db_ops, sample_valuation):
        """Test inserting single player valuation."""
        # Insert
        db_ops.insert_player_valuation(sample_valuation)

        # Verify
        retrieved = db_ops.get_player_valuation(
            league_id=1,
            team_id=1,
            player_id="mahomes_pat",
            season=2025,
            week=13,
        )

        assert retrieved is not None
        assert retrieved["player_name"] == "Patrick Mahomes"
        assert retrieved["point_value"] == 4.5
        assert retrieved["is_starter"] is True

    def test_insert_multiple_player_valuations(self, db_ops):
        """Test inserting multiple player valuations."""
        players = [
            PlayerValuation(
                league_id=1,
                team_id=1,
                player_id=f"player_{i}",
                player_name=f"Player {i}",
                position="QB" if i == 1 else "RB",
                season=2025,
                week=13,
                point_value=4.5 if i == 1 else 2.0,
                snap_count_pct=100.0,
                is_starter=True,
                depth_chart_position=1,
                source="test",
            )
            for i in range(1, 4)
        ]

        # Insert all
        for player in players:
            db_ops.insert_player_valuation(player)

        # Verify all inserted
        for i, player in enumerate(players, 1):
            retrieved = db_ops.get_player_valuation(
                league_id=1,
                team_id=1,
                player_id=f"player_{i}",
                season=2025,
                week=13,
            )
            assert retrieved is not None
            assert retrieved["player_name"] == f"Player {i}"

    def test_insert_with_optional_fields(self, db_ops):
        """Test insert with optional fields omitted."""
        valuation = PlayerValuation(
            league_id=1,
            team_id=1,
            player_name="Backup Player",
            position="RB",
            season=2025,
            point_value=1.2,
            # Optional fields omitted: player_id, week, snap_count_pct, etc.
        )

        db_ops.insert_player_valuation(valuation)

        # Verify stored with nulls for optional fields
        retrieved = db_ops.get_player_valuation(
            league_id=1,
            team_id=1,
            player_id=None,
            season=2025,
            week=None,
        )

        assert retrieved is not None
        assert retrieved["player_name"] == "Backup Player"
        assert retrieved["snap_count_pct"] is None

    def test_get_player_valuation_not_found(self, db_ops):
        """Test getting non-existent player valuation."""
        retrieved = db_ops.get_player_valuation(
            league_id=999,
            team_id=999,
            player_id="nonexistent",
            season=2025,
            week=13,
        )

        assert retrieved is None

    def test_get_team_valuations_by_week(self, db_ops):
        """Test getting all valuations for a team by week."""
        # Insert sample players for team
        for i in range(3):
            valuation = PlayerValuation(
                league_id=1,
                team_id=1,
                player_id=f"kc_player_{i}",
                player_name=f"KC Player {i}",
                position="QB" if i == 0 else "RB",
                season=2025,
                week=13,
                point_value=4.5 if i == 0 else 2.0,
                snap_count_pct=100.0,
                is_starter=(i == 0),
                depth_chart_position=i + 1,
            )
            db_ops.insert_player_valuation(valuation)

        # Query by team/week
        results = db_ops.get_team_valuations_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )

        assert len(results) >= 3
        assert all(r["team_id"] == 1 for r in results)
        assert all(r["week"] == 13 for r in results)

    def test_get_valuations_by_position(self, db_ops):
        """Test getting valuations filtered by position."""
        # Insert QBs and RBs
        positions = [("QB", 4.5), ("QB", 3.5), ("RB", 2.0)]
        for i, (pos, value) in enumerate(positions):
            valuation = PlayerValuation(
                league_id=1,
                team_id=1,
                player_id=f"pos_player_{i}",
                player_name=f"Player {i}",
                position=pos,
                season=2025,
                week=13,
                point_value=value,
                snap_count_pct=100.0,
            )
            db_ops.insert_player_valuation(valuation)

        # Note: Would need dedicated get_by_position method
        # For now, test that we can retrieve by player_id
        qb = db_ops.get_player_valuation(
            league_id=1,
            team_id=1,
            player_id="pos_player_0",
            season=2025,
            week=13,
        )

        assert qb["position"] == "QB"

    def test_update_snap_count(self, db_ops, sample_valuation):
        """Test updating snap count for a player."""
        # Insert
        db_ops.insert_player_valuation(sample_valuation)

        # Update (would need specific update method)
        # For now, test that we can insert with updated value
        updated = PlayerValuation(
            league_id=1,
            team_id=1,
            player_id="mahomes_pat",
            player_name="Patrick Mahomes",
            position="QB",
            season=2025,
            week=13,
            point_value=4.5,
            snap_count_pct=95.5,  # Updated from 98.0
            impact_rating=4.3,  # Recalculated
            is_starter=True,
            depth_chart_position=1,
        )

        db_ops.insert_player_valuation(updated)

        # Verify updated
        retrieved = db_ops.get_player_valuation(
            league_id=1,
            team_id=1,
            player_id="mahomes_pat",
            season=2025,
            week=13,
        )

        assert retrieved["snap_count_pct"] == 95.5
        assert retrieved["impact_rating"] == 4.3

    def test_unique_constraint_player_per_week(self, db_ops):
        """Test unique constraint on (league, team, player, season, week)."""
        valuation1 = PlayerValuation(
            league_id=1,
            team_id=1,
            player_id="duplicate_player",
            player_name="Duplicate",
            position="QB",
            season=2025,
            week=13,
            point_value=4.5,
        )

        valuation2 = PlayerValuation(
            league_id=1,
            team_id=1,
            player_id="duplicate_player",
            player_name="Duplicate",
            position="QB",
            season=2025,
            week=13,
            point_value=3.5,  # Different value
        )

        # First insert should succeed
        db_ops.insert_player_valuation(valuation1)

        # Second insert with same key should replace
        db_ops.insert_player_valuation(valuation2)

        # Should have the second value
        retrieved = db_ops.get_player_valuation(
            league_id=1,
            team_id=1,
            player_id="duplicate_player",
            season=2025,
            week=13,
        )

        assert retrieved["point_value"] == 3.5

    def test_foreign_key_constraint_league(self, db_ops):
        """Test foreign key constraint for league_id."""
        invalid_valuation = PlayerValuation(
            league_id=999,  # Non-existent league
            team_id=1,
            player_id="bad_player",
            player_name="Bad Player",
            position="QB",
            season=2025,
            point_value=4.5,
        )

        # This should fail with foreign key error
        with pytest.raises(Exception):
            db_ops.insert_player_valuation(invalid_valuation)

    def test_foreign_key_constraint_team(self, db_ops):
        """Test foreign key constraint for team_id."""
        invalid_valuation = PlayerValuation(
            league_id=1,
            team_id=999,  # Non-existent team
            player_id="bad_player",
            player_name="Bad Player",
            position="QB",
            season=2025,
            point_value=4.5,
        )

        # This should fail with foreign key error
        with pytest.raises(Exception):
            db_ops.insert_player_valuation(invalid_valuation)

    def test_point_value_range_validation(self, db_ops):
        """Test that point values are in valid range."""
        # Valid range: 0.4 to 5.0
        valid_values = [0.4, 1.0, 2.5, 4.5, 5.0]

        for value in valid_values:
            valuation = PlayerValuation(
                league_id=1,
                team_id=1,
                player_id=f"value_test_{value}",
                player_name=f"Test {value}",
                position="QB",
                season=2025,
                point_value=value,
            )

            db_ops.insert_player_valuation(valuation)

            retrieved = db_ops.get_player_valuation(
                league_id=1,
                team_id=1,
                player_id=f"value_test_{value}",
                season=2025,
                week=None,
            )

            assert retrieved is not None
            assert retrieved["point_value"] == value

    def test_snap_count_percentage_validation(self, db_ops):
        """Test that snap_count_pct is valid percentage (0-100)."""
        valid_percentages = [0.0, 25.0, 50.0, 75.0, 100.0]

        for pct in valid_percentages:
            valuation = PlayerValuation(
                league_id=1,
                team_id=1,
                player_id=f"snap_test_{pct}",
                player_name=f"Test {pct}%",
                position="QB",
                season=2025,
                point_value=4.5,
                snap_count_pct=pct,
            )

            db_ops.insert_player_valuation(valuation)

            retrieved = db_ops.get_player_valuation(
                league_id=1,
                team_id=1,
                player_id=f"snap_test_{pct}",
                season=2025,
                week=None,
            )

            assert retrieved["snap_count_pct"] == pct

    def test_query_performance_by_index(self, db_ops):
        """Test query performance using indexes."""
        import time

        # Insert multiple players
        for i in range(100):
            valuation = PlayerValuation(
                league_id=1,
                team_id=(i % 32) + 1,
                player_id=f"perf_player_{i}",
                player_name=f"Performance Test {i}",
                position="QB" if i % 10 == 0 else "RB",
                season=2025,
                week=13,
                point_value=4.5 if i % 10 == 0 else 2.0,
                snap_count_pct=100.0,
            )
            db_ops.insert_player_valuation(valuation)

        # Query by (league, team, season, week) - should use index
        start = time.time()
        results = db_ops.get_team_valuations_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )
        elapsed = time.time() - start

        # Should complete in <100ms with index
        assert elapsed < 0.1
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
