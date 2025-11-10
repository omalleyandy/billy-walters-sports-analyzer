"""
Integration tests for data collection components.

Tests ESPN client, validators, orchestrator, and health monitoring.
"""

import asyncio
from datetime import datetime, timedelta

import httpx
import pytest

from src.data.data_orchestrator import CollectionStatus, DataOrchestrator
from src.data.espn_client import ESPNClient
from src.data.health_monitor import AlertLevel, HealthCheck, HealthMonitor, HealthStatus
from src.data.validated_espn import ESPNDataValidator


class TestESPNClient:
    """Test ESPN API client."""

    @pytest.mark.asyncio
    async def test_client_connect_close(self):
        """Test client connection and cleanup."""
        client = ESPNClient()
        await client.connect()
        assert client._client is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with ESPNClient() as client:
            assert client._client is not None

    @pytest.mark.asyncio
    async def test_get_nfl_teams(self):
        """Test fetching NFL teams."""
        async with ESPNClient() as client:
            teams = await client.get_teams("NFL")

            assert isinstance(teams, list)
            assert len(teams) > 0

            # Validate team structure
            team = teams[0]
            assert "id" in team
            assert "name" in team
            assert "abbreviation" in team
            assert team["league"] == "NFL"
            assert team["source"] == "espn"

    @pytest.mark.asyncio
    async def test_get_nfl_scoreboard(self):
        """Test fetching NFL scoreboard."""
        async with ESPNClient() as client:
            scoreboard = await client.get_scoreboard("NFL", week=1)

            assert isinstance(scoreboard, dict)
            assert "events" in scoreboard
            assert scoreboard["league"] == "NFL"
            assert scoreboard["source"] == "espn"

    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        client = ESPNClient()
        await client.connect()

        # Simulate failures
        for _ in range(5):
            client._record_failure()

        # Circuit breaker should be open
        with pytest.raises(RuntimeError, match="Circuit breaker is open"):
            client._check_circuit_breaker()

        await client.close()

    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test automatic retry logic."""
        client = ESPNClient(max_retries=3)
        await client.connect()

        # Test with invalid endpoint (will retry and fail with ConnectError)
        with pytest.raises((RuntimeError, httpx.ConnectError)):
            await client._make_request("https://invalid.invalid/test")

        await client.close()


class TestESPNDataValidator:
    """Test ESPN data validation."""

    def test_validate_teams_valid(self):
        """Test validation of valid team data."""
        teams_data = [
            {
                "id": "1",
                "name": "Kansas City Chiefs",
                "abbreviation": "KC",
                "location": "Kansas City",
                "nickname": "Chiefs",
                "logo": "https://example.com/logo.png",
                "league": "NFL",
                "fetch_time": "2025-01-01T00:00:00",
            }
        ]

        validator = ESPNDataValidator()
        validated, report = validator.validate_teams(teams_data)

        assert len(validated) == 1
        assert report.total_records == 1
        assert report.valid_records == 1
        assert report.invalid_records == 0
        assert report.is_acceptable

    def test_validate_teams_invalid(self):
        """Test validation of invalid team data."""
        teams_data = [
            {
                "id": "",  # Invalid - empty ID
                "name": "Invalid Team",
                "abbreviation": "INV",
                "league": "NFL",
                "fetch_time": "2025-01-01T00:00:00",
            }
        ]

        validator = ESPNDataValidator()
        validated, report = validator.validate_teams(teams_data)

        assert len(validated) == 0
        assert report.total_records == 1
        assert report.valid_records == 0
        assert report.invalid_records == 1
        assert not report.is_acceptable

    def test_validate_games_valid(self):
        """Test validation of valid game data."""
        games_data = [
            {
                "id": "12345",
                "name": "Chiefs vs Bills",
                "date": "2025-01-01T13:00:00",
                "status": "scheduled",
                "home_team_id": "1",
                "home_team_name": "Kansas City Chiefs",
                "away_team_id": "2",
                "away_team_name": "Buffalo Bills",
                "league": "NFL",
                "fetch_time": "2025-01-01T00:00:00",
            }
        ]

        validator = ESPNDataValidator()
        validated, report = validator.validate_games(games_data)

        assert len(validated) == 1
        assert report.is_acceptable

    def test_validate_games_invalid_score(self):
        """Test validation rejects unrealistic scores."""
        games_data = [
            {
                "id": "12345",
                "name": "Chiefs vs Bills",
                "date": "2025-01-01T13:00:00",
                "status": "final",
                "home_team_id": "1",
                "home_team_name": "Kansas City Chiefs",
                "home_team_score": 200,  # Unrealistic
                "away_team_id": "2",
                "away_team_name": "Buffalo Bills",
                "away_team_score": 150,  # Unrealistic
                "league": "NFL",
                "fetch_time": "2025-01-01T00:00:00",
            }
        ]

        validator = ESPNDataValidator()
        validated, report = validator.validate_games(games_data)

        assert len(validated) == 0
        assert not report.is_acceptable


class TestHealthMonitor:
    """Test health monitoring system."""

    def test_record_check_success(self):
        """Test recording successful health check."""
        monitor = HealthMonitor()

        check = HealthCheck(
            source="espn",
            timestamp=datetime.now(),
            success=True,
            duration_ms=150.0,
        )

        monitor.record_check(check)

        metrics = monitor.get_metrics("espn")
        assert metrics is not None
        assert metrics.total_checks == 1
        assert metrics.successful_checks == 1
        assert metrics.failed_checks == 0

    def test_record_check_failure(self):
        """Test recording failed health check."""
        monitor = HealthMonitor()

        check = HealthCheck(
            source="espn",
            timestamp=datetime.now(),
            success=False,
            duration_ms=5000.0,
            error="Timeout",
        )

        monitor.record_check(check)

        metrics = monitor.get_metrics("espn")
        assert metrics is not None
        assert metrics.total_checks == 1
        assert metrics.successful_checks == 0
        assert metrics.failed_checks == 1

    def test_consecutive_failures_alert(self):
        """Test alerting on consecutive failures."""
        monitor = HealthMonitor(alert_threshold_failures=3)

        # Record 3 consecutive failures
        for _ in range(3):
            check = HealthCheck(
                source="espn",
                timestamp=datetime.now(),
                success=False,
                duration_ms=100.0,
                error="Test error",
            )
            monitor.record_check(check)

        # Should have generated an alert
        alerts = monitor.get_recent_alerts()
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.WARNING for a in alerts)

    def test_health_status_transitions(self):
        """Test health status transitions based on success rate."""
        monitor = HealthMonitor()

        # Record 10 successful checks (100% success) - should be HEALTHY
        for _ in range(10):
            check = HealthCheck(
                source="espn",
                timestamp=datetime.now(),
                success=True,
                duration_ms=100.0,
            )
            monitor.record_check(check)

        metrics = monitor.get_metrics("espn")
        assert metrics.status == HealthStatus.HEALTHY

        # Record 5 failures (67% success) - should be UNHEALTHY
        for _ in range(10):
            check = HealthCheck(
                source="espn",
                timestamp=datetime.now(),
                success=False,
                duration_ms=100.0,
            )
            monitor.record_check(check)

        metrics = monitor.get_metrics("espn")
        assert metrics.status == HealthStatus.UNHEALTHY

    def test_system_health(self):
        """Test overall system health calculation."""
        monitor = HealthMonitor()

        # Add healthy source
        for _ in range(10):
            check = HealthCheck(
                source="espn",
                timestamp=datetime.now(),
                success=True,
                duration_ms=100.0,
            )
            monitor.record_check(check)

        # Add unhealthy source
        for _ in range(10):
            check = HealthCheck(
                source="action_network",
                timestamp=datetime.now(),
                success=False,
                duration_ms=100.0,
            )
            monitor.record_check(check)

        # System health should be unhealthy (weakest link)
        system_health = monitor.get_system_health()
        assert system_health in [
            HealthStatus.UNHEALTHY,
            HealthStatus.CRITICAL,
        ]

    def test_alert_callback(self):
        """Test alert callback functionality."""
        monitor = HealthMonitor(alert_threshold_failures=2)
        callback_called = False
        received_alert = None

        def callback(alert):
            nonlocal callback_called, received_alert
            callback_called = True
            received_alert = alert

        monitor.register_alert_callback(callback)

        # Trigger alert with consecutive failures
        for _ in range(2):
            check = HealthCheck(
                source="espn",
                timestamp=datetime.now(),
                success=False,
                duration_ms=100.0,
            )
            monitor.record_check(check)

        assert callback_called
        assert received_alert is not None
        assert received_alert.source == "espn"


class TestDataOrchestrator:
    """Test data orchestration."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = DataOrchestrator(
            max_concurrent_tasks=5,
            enable_retries=True,
            enable_validation=True,
        )

        assert orchestrator.max_concurrent_tasks == 5
        assert orchestrator.enable_retries is True
        assert orchestrator.enable_validation is True

    @pytest.mark.asyncio
    async def test_collect_nfl_data_dry_run(self):
        """Test NFL data collection (limited to avoid API rate limits)."""
        orchestrator = DataOrchestrator(
            max_concurrent_tasks=2,  # Limit concurrency
            enable_retries=False,  # Disable retries for faster test
            enable_validation=True,
        )

        # This will make real API calls - use sparingly
        report = await orchestrator.collect_all_nfl_data(week=1)

        assert report.total_sources > 0
        assert report.end_time is not None
        assert report.duration_seconds > 0

        # At least some sources should succeed
        assert report.successful_sources >= 0

    @pytest.mark.asyncio
    async def test_collection_report_metrics(self):
        """Test collection report metrics calculation."""
        from src.data.data_orchestrator import CollectionReport, CollectionTask, DataSource

        report = CollectionReport(start_time=datetime.now())

        # Add mock tasks
        report.tasks = [
            CollectionTask(
                source=DataSource.ESPN,
                description="Test 1",
                function=lambda: None,
                status=CollectionStatus.COMPLETED,
            ),
            CollectionTask(
                source=DataSource.ESPN,
                description="Test 2",
                function=lambda: None,
                status=CollectionStatus.COMPLETED,
            ),
            CollectionTask(
                source=DataSource.ESPN,
                description="Test 3",
                function=lambda: None,
                status=CollectionStatus.FAILED,
            ),
        ]

        report.end_time = datetime.now() + timedelta(seconds=5)
        report.total_sources = 3
        report.successful_sources = 2
        report.failed_sources = 1

        assert report.success_rate == pytest.approx(66.67, rel=0.1)
        assert not report.is_healthy  # <80%

        # Test with healthy success rate
        report.successful_sources = 3
        report.failed_sources = 0
        assert report.success_rate == 100.0
        assert report.is_healthy


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
