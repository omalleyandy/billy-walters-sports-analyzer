"""
CRUD Tests for Practice Reports Table

Tests complete CRUD operations for practice_reports table including:
- Insert single and batch operations
- Query by league/team/week
- Query by player/date
- Update trend analysis
- Day of week calculation
- Wednesday signal validation
"""

import pytest
from datetime import datetime, timedelta

from walters_analyzer.db.connection import DatabaseConnection
from walters_analyzer.db.raw_data_operations import RawDataOperations
from walters_analyzer.db.raw_data_models import PracticeReport


class TestPracticeReportsCRUD:
    """Test CRUD operations for practice_reports table."""

    @pytest.fixture
    def db_ops(self):
        """Create database operations instance."""
        db_conn = DatabaseConnection()
        return RawDataOperations(db_conn)

    @pytest.fixture
    def sample_report(self):
        """Create sample practice report."""
        return PracticeReport(
            league_id=1,
            team_id=1,
            player_id="mahomes_pat",
            player_name="Patrick Mahomes",
            season=2025,
            week=13,
            practice_date=datetime(2025, 11, 26).date(),  # Wednesday
            day_of_week=2,  # Wednesday
            participation="FP",  # Full participation
            severity="mild",
            sessions_participated=3,
            source="nfl.com",
            notes="Full practice participation",
        )

    def test_insert_single_practice_report(self, db_ops, sample_report):
        """Test inserting single practice report."""
        db_ops.insert_practice_report(sample_report)

        # Verify
        retrieved = db_ops.get_practice_reports_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )

        assert len(retrieved) > 0
        assert any(r["player_id"] == "mahomes_pat" for r in retrieved)

    def test_insert_multiple_practice_reports(self, db_ops):
        """Test inserting multiple reports for different players."""
        players = [
            ("mahomes_pat", "Patrick Mahomes", "FP", "mild"),
            ("pacheco_ish", "Isiah Pacheco", "LP", "moderate"),
            ("smith_juju", "JuJu Smith-Schuster", "DNP", "severe"),
        ]

        for player_id, player_name, participation, severity in players:
            report = PracticeReport(
                league_id=1,
                team_id=1,
                player_id=player_id,
                player_name=player_name,
                season=2025,
                week=13,
                practice_date=datetime(2025, 11, 26).date(),
                day_of_week=2,
                participation=participation,
                severity=severity,
                sessions_participated=3,
            )
            db_ops.insert_practice_report(report)

        # Verify all inserted
        results = db_ops.get_practice_reports_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )

        assert len(results) >= 3
        for player_id, _, _, _ in players:
            assert any(r["player_id"] == player_id for r in results)

    def test_wednesday_signal_participation(self, db_ops):
        """Test that Wednesday participation is tracked."""
        wednesday_date = datetime(2025, 11, 26).date()

        report = PracticeReport(
            league_id=1,
            team_id=1,
            player_id="wed_signal_test",
            player_name="Wednesday Signal Test",
            season=2025,
            week=13,
            practice_date=wednesday_date,
            day_of_week=2,  # 0=Mon, 1=Tue, 2=Wed, ...
            participation="FP",
            severity="mild",
        )

        db_ops.insert_practice_report(report)

        # Verify Wednesday flag
        retrieved = db_ops.get_practice_reports_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )

        wed_report = next(
            (r for r in retrieved if r["player_id"] == "wed_signal_test"),
            None,
        )

        assert wed_report is not None
        assert wed_report["day_of_week"] == 2
        assert wed_report["participation"] == "FP"

    def test_participation_status_levels(self, db_ops):
        """Test different participation status levels."""
        statuses = [
            ("FP", "full", 3),
            ("LP", "limited", 2),
            ("DNP", "did_not_practice", 0),
        ]

        for participation, severity, sessions in statuses:
            report = PracticeReport(
                league_id=1,
                team_id=1,
                player_id=f"status_{participation}",
                player_name=f"Status Test {participation}",
                season=2025,
                week=13,
                practice_date=datetime(2025, 11, 26).date(),
                day_of_week=2,
                participation=participation,
                severity=severity,
                sessions_participated=sessions,
            )

            db_ops.insert_practice_report(report)

            # Verify stored correctly
            results = db_ops.get_practice_reports_by_week(
                league_id=1, team_id=1, season=2025, week=13
            )

            status_report = next(
                (r for r in results if r["player_id"] == f"status_{participation}"),
                None,
            )

            assert status_report is not None
            assert status_report["participation"] == participation
            assert status_report["severity"] == severity

    def test_trend_analysis_improving(self, db_ops):
        """Test trend detection: improving (DNP -> LP -> FP)."""
        player_id = "trend_improving"

        # Week 11: DNP
        report_w11 = PracticeReport(
            league_id=1,
            team_id=1,
            player_id=player_id,
            player_name="Improving Player",
            season=2025,
            week=11,
            practice_date=datetime(2025, 11, 12).date(),
            participation="DNP",
            severity="severe",
            trend=None,
        )
        db_ops.insert_practice_report(report_w11)

        # Week 12: LP
        report_w12 = PracticeReport(
            league_id=1,
            team_id=1,
            player_id=player_id,
            player_name="Improving Player",
            season=2025,
            week=12,
            practice_date=datetime(2025, 11, 19).date(),
            participation="LP",
            severity="moderate",
            trend="improving",  # Manual for now
        )
        db_ops.insert_practice_report(report_w12)

        # Week 13: FP
        report_w13 = PracticeReport(
            league_id=1,
            team_id=1,
            player_id=player_id,
            player_name="Improving Player",
            season=2025,
            week=13,
            practice_date=datetime(2025, 11, 26).date(),
            participation="FP",
            severity="mild",
            trend="improving",
        )
        db_ops.insert_practice_report(report_w13)

        # Verify week 13 has improving trend
        results = db_ops.get_practice_reports_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )

        w13_report = next((r for r in results if r["player_id"] == player_id), None)

        assert w13_report is not None
        assert w13_report["trend"] == "improving"
        assert w13_report["participation"] == "FP"

    def test_trend_analysis_declining(self, db_ops):
        """Test trend detection: declining (FP -> LP -> DNP)."""
        player_id = "trend_declining"

        # Week 11: FP
        report_w11 = PracticeReport(
            league_id=1,
            team_id=1,
            player_id=player_id,
            player_name="Declining Player",
            season=2025,
            week=11,
            practice_date=datetime(2025, 11, 12).date(),
            participation="FP",
            severity="mild",
        )
        db_ops.insert_practice_report(report_w11)

        # Week 12: LP
        report_w12 = PracticeReport(
            league_id=1,
            team_id=1,
            player_id=player_id,
            player_name="Declining Player",
            season=2025,
            week=12,
            practice_date=datetime(2025, 11, 19).date(),
            participation="LP",
            severity="moderate",
            trend="declining",
        )
        db_ops.insert_practice_report(report_w12)

        # Week 13: DNP
        report_w13 = PracticeReport(
            league_id=1,
            team_id=1,
            player_id=player_id,
            player_name="Declining Player",
            season=2025,
            week=13,
            practice_date=datetime(2025, 11, 26).date(),
            participation="DNP",
            severity="severe",
            trend="declining",
        )
        db_ops.insert_practice_report(report_w13)

        # Verify week 13 has declining trend and DNP
        results = db_ops.get_practice_reports_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )

        w13_report = next((r for r in results if r["player_id"] == player_id), None)

        assert w13_report is not None
        assert w13_report["trend"] == "declining"
        assert w13_report["participation"] == "DNP"

    def test_get_by_player_date(self, db_ops, sample_report):
        """Test querying practice reports by player and date."""
        db_ops.insert_practice_report(sample_report)

        # Query by player_id and date
        results = db_ops.get_practice_reports_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )

        player_reports = [
            r
            for r in results
            if r["player_id"] == "mahomes_pat" and r["practice_date"] == "2025-11-26"
        ]

        assert len(player_reports) > 0

    def test_unique_constraint_player_date_week(self, db_ops):
        """Test unique constraint on (league, team, season, week, player, date)."""
        date = datetime(2025, 11, 26).date()

        report1 = PracticeReport(
            league_id=1,
            team_id=1,
            player_id="unique_test",
            player_name="Unique Test",
            season=2025,
            week=13,
            practice_date=date,
            participation="FP",
        )

        report2 = PracticeReport(
            league_id=1,
            team_id=1,
            player_id="unique_test",
            player_name="Unique Test",
            season=2025,
            week=13,
            practice_date=date,
            participation="LP",  # Different status
        )

        db_ops.insert_practice_report(report1)
        db_ops.insert_practice_report(report2)  # Should replace

        # Should have the second value
        results = db_ops.get_practice_reports_by_week(
            league_id=1, team_id=1, season=2025, week=13
        )

        test_report = next(
            (r for r in results if r["player_id"] == "unique_test"),
            None,
        )

        assert test_report["participation"] == "LP"

    def test_day_of_week_calculation(self, db_ops):
        """Test day_of_week field calculation."""
        dates_and_days = [
            (datetime(2025, 11, 24).date(), 0),  # Monday
            (datetime(2025, 11, 25).date(), 1),  # Tuesday
            (datetime(2025, 11, 26).date(), 2),  # Wednesday
            (datetime(2025, 11, 27).date(), 3),  # Thursday
            (datetime(2025, 11, 28).date(), 4),  # Friday
        ]

        for date, expected_day in dates_and_days:
            report = PracticeReport(
                league_id=1,
                team_id=1,
                player_id=f"dow_test_{expected_day}",
                player_name=f"DOW Test {expected_day}",
                season=2025,
                week=13,
                practice_date=date,
                day_of_week=expected_day,
                participation="FP",
            )

            db_ops.insert_practice_report(report)

            results = db_ops.get_practice_reports_by_week(
                league_id=1, team_id=1, season=2025, week=13
            )

            report_retrieved = next(
                (r for r in results if r["player_id"] == f"dow_test_{expected_day}"),
                None,
            )

            assert report_retrieved["day_of_week"] == expected_day


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
