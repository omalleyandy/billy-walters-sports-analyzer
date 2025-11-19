"""
Data Collection Health Monitor

Tracks scraper health, generates alerts, and provides system status.
"""

import asyncio
import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"  # >95% success rate
    DEGRADED = "degraded"  # 80-95% success rate
    UNHEALTHY = "unhealthy"  # 50-80% success rate
    CRITICAL = "critical"  # <50% success rate
    UNKNOWN = "unknown"  # Not enough data


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Single health check result."""

    source: str
    timestamp: datetime
    success: bool
    duration_ms: float
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthMetrics:
    """Aggregated health metrics for a source."""

    source: str
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    last_success: datetime | None = None
    last_failure: datetime | None = None
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0
    status: HealthStatus = HealthStatus.UNKNOWN

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.successful_checks / self.total_checks) * 100

    def update_status(self) -> None:
        """Update health status based on success rate."""
        if self.total_checks < 5:
            self.status = HealthStatus.UNKNOWN
        elif self.success_rate >= 95.0:
            self.status = HealthStatus.HEALTHY
        elif self.success_rate >= 80.0:
            self.status = HealthStatus.DEGRADED
        elif self.success_rate >= 50.0:
            self.status = HealthStatus.UNHEALTHY
        else:
            self.status = HealthStatus.CRITICAL


@dataclass
class Alert:
    """Health alert."""

    level: AlertLevel
    source: str
    message: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "source": self.source,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class HealthMonitor:
    """
    Monitors data collection health and generates alerts.

    Features:
    - Real-time health tracking
    - Historical metrics retention
    - Automatic alerting
    - Performance monitoring
    - Uptime tracking
    """

    def __init__(
        self,
        history_size: int = 100,
        alert_threshold_failures: int = 3,
        alert_file: Path | None = None,
    ):
        """
        Initialize health monitor.

        Args:
            history_size: Number of health checks to retain per source
            alert_threshold_failures: Consecutive failures before alerting
            alert_file: Path to write alerts (optional)
        """
        self.history_size = history_size
        self.alert_threshold_failures = alert_threshold_failures
        self.alert_file = alert_file

        self._history: dict[str, deque[HealthCheck]] = {}
        self._metrics: dict[str, HealthMetrics] = {}
        self._alerts: deque[Alert] = deque(maxlen=1000)
        self._alert_callbacks: list = []

    def record_check(self, check: HealthCheck) -> None:
        """
        Record a health check.

        Args:
            check: Health check result
        """
        source = check.source

        # Initialize history if needed
        if source not in self._history:
            self._history[source] = deque(maxlen=self.history_size)
            self._metrics[source] = HealthMetrics(source=source)

        # Add to history
        self._history[source].append(check)

        # Update metrics
        self._update_metrics(source)

        # Check for alerts
        self._check_alerts(source)

    def get_metrics(self, source: str) -> HealthMetrics | None:
        """Get metrics for a specific source."""
        return self._metrics.get(source)

    def get_all_metrics(self) -> dict[str, HealthMetrics]:
        """Get metrics for all sources."""
        return self._metrics.copy()

    def get_system_health(self) -> HealthStatus:
        """Get overall system health status."""
        if not self._metrics:
            return HealthStatus.UNKNOWN

        statuses = [m.status for m in self._metrics.values()]

        # System is only as healthy as weakest link
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def get_recent_alerts(
        self, count: int = 10, level: AlertLevel | None = None
    ) -> list[Alert]:
        """
        Get recent alerts.

        Args:
            count: Number of alerts to return
            level: Filter by alert level (optional)

        Returns:
            List of recent alerts
        """
        alerts = list(self._alerts)

        if level:
            alerts = [a for a in alerts if a.level == level]

        return alerts[-count:]

    def register_alert_callback(self, callback: callable) -> None:
        """
        Register a callback for alerts.

        Args:
            callback: Function to call when alert is generated
        """
        self._alert_callbacks.append(callback)

    def _update_metrics(self, source: str) -> None:
        """Update metrics for a source."""
        history = self._history[source]
        metrics = self._metrics[source]

        # Calculate totals
        metrics.total_checks = len(history)
        metrics.successful_checks = sum(1 for c in history if c.success)
        metrics.failed_checks = metrics.total_checks - metrics.successful_checks

        # Calculate durations
        durations = [c.duration_ms for c in history]
        if durations:
            metrics.avg_duration_ms = sum(durations) / len(durations)
            metrics.min_duration_ms = min(durations)
            metrics.max_duration_ms = max(durations)

        # Update last success/failure
        for check in reversed(history):
            if check.success and not metrics.last_success:
                metrics.last_success = check.timestamp
            if not check.success and not metrics.last_failure:
                metrics.last_failure = check.timestamp
            if metrics.last_success and metrics.last_failure:
                break

        # Count consecutive failures
        metrics.consecutive_failures = 0
        for check in reversed(history):
            if not check.success:
                metrics.consecutive_failures += 1
            else:
                break

        # Calculate uptime
        metrics.uptime_percentage = metrics.success_rate

        # Update health status
        metrics.update_status()

    def _check_alerts(self, source: str) -> None:
        """Check if alerts should be generated."""
        metrics = self._metrics[source]

        # Alert on consecutive failures
        if metrics.consecutive_failures == self.alert_threshold_failures:
            self._generate_alert(
                AlertLevel.WARNING,
                source,
                f"{source} has {metrics.consecutive_failures} consecutive failures",
                {"consecutive_failures": metrics.consecutive_failures},
            )

        # Alert on critical status
        if metrics.status == HealthStatus.CRITICAL:
            self._generate_alert(
                AlertLevel.CRITICAL,
                source,
                f"{source} is in CRITICAL status ({metrics.success_rate:.1f}% success rate)",
                {"success_rate": metrics.success_rate},
            )

        # Alert on unhealthy status
        elif metrics.status == HealthStatus.UNHEALTHY:
            self._generate_alert(
                AlertLevel.ERROR,
                source,
                f"{source} is UNHEALTHY ({metrics.success_rate:.1f}% success rate)",
                {"success_rate": metrics.success_rate},
            )

        # Alert on degraded status
        elif metrics.status == HealthStatus.DEGRADED:
            # Only alert once for degraded status
            recent_alerts = [
                a
                for a in self._alerts
                if a.source == source
                and a.level == AlertLevel.WARNING
                and (datetime.now() - a.timestamp) < timedelta(hours=1)
            ]
            if not recent_alerts:
                self._generate_alert(
                    AlertLevel.WARNING,
                    source,
                    f"{source} is DEGRADED ({metrics.success_rate:.1f}% success rate)",
                    {"success_rate": metrics.success_rate},
                )

    def _generate_alert(
        self,
        level: AlertLevel,
        source: str,
        message: str,
        metadata: dict[str, Any],
    ) -> None:
        """Generate and record an alert."""
        alert = Alert(
            level=level,
            source=source,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata,
        )

        self._alerts.append(alert)

        # Log alert
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical,
        }[level]
        log_func(f"ALERT [{level.value.upper()}] {source}: {message}")

        # Write to file if configured
        if self.alert_file:
            self._write_alert_to_file(alert)

        # Call registered callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def _write_alert_to_file(self, alert: Alert) -> None:
        """Write alert to file."""
        try:
            self.alert_file.parent.mkdir(parents=True, exist_ok=True)  # type: ignore

            with open(self.alert_file, "a") as f:
                f.write(json.dumps(alert.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to write alert to file: {e}")

    def generate_health_report(self) -> dict[str, Any]:
        """Generate comprehensive health report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": self.get_system_health().value,
            "sources": {
                source: {
                    "status": metrics.status.value,
                    "success_rate": metrics.success_rate,
                    "total_checks": metrics.total_checks,
                    "consecutive_failures": metrics.consecutive_failures,
                    "avg_duration_ms": metrics.avg_duration_ms,
                    "last_success": (
                        metrics.last_success.isoformat()
                        if metrics.last_success
                        else None
                    ),
                    "last_failure": (
                        metrics.last_failure.isoformat()
                        if metrics.last_failure
                        else None
                    ),
                }
                for source, metrics in self._metrics.items()
            },
            "recent_alerts": [a.to_dict() for a in list(self._alerts)[-10:]],
        }

    def print_status_dashboard(self) -> None:
        """Print a status dashboard to console."""
        print("\n" + "=" * 70)
        print("HEALTH MONITORING DASHBOARD")
        print("=" * 70)

        # System health
        system_health = self.get_system_health()
        health_icon = {
            HealthStatus.HEALTHY: "[OK]",
            HealthStatus.DEGRADED: "[WARNING]",
            HealthStatus.UNHEALTHY: "[X]",
            HealthStatus.CRITICAL: "[*]",
            HealthStatus.UNKNOWN: "?",
        }[system_health]

        print(f"System Health: {health_icon} {system_health.value.upper()}")
        print()

        # Source metrics
        if not self._metrics:
            print("No data collected yet")
        else:
            print(f"{'Source':<30} {'Status':<12} {'Success Rate':<15} {'Checks':<10}")
            print("-" * 70)

            for source, metrics in sorted(self._metrics.items()):
                status_icon = health_icon
                status_str = f"{status_icon} {metrics.status.value}"
                success_str = f"{metrics.success_rate:.1f}%"
                checks_str = f"{metrics.successful_checks}/{metrics.total_checks}"

                print(
                    f"{source:<30} {status_str:<12} {success_str:<15} {checks_str:<10}"
                )

        # Recent alerts
        recent_alerts = list(self._alerts)[-5:]
        if recent_alerts:
            print("\nRecent Alerts:")
            print("-" * 70)
            for alert in recent_alerts:
                time_str = alert.timestamp.strftime("%H:%M:%S")
                print(
                    f"[{time_str}] {alert.level.value.upper()}: {alert.source} - {alert.message}"
                )

        print("=" * 70 + "\n")


# Example usage
async def main():
    """Example usage of HealthMonitor."""
    monitor = HealthMonitor(
        history_size=100,
        alert_threshold_failures=3,
        alert_file=Path("data/health_alerts.jsonl"),
    )

    # Register callback
    def alert_callback(alert: Alert):
        print(f"[*] ALERT: {alert.message}")

    monitor.register_alert_callback(alert_callback)

    # Simulate health checks
    sources = ["espn", "action_network", "overtime", "weather"]

    for i in range(20):
        for source in sources:
            # Simulate varying success rates
            import random

            success_prob = {
                "espn": 0.98,
                "action_network": 0.85,  # Degraded
                "overtime": 0.60,  # Unhealthy
                "weather": 0.95,
            }[source]

            success = random.random() < success_prob
            duration = random.uniform(100, 2000)

            check = HealthCheck(
                source=source,
                timestamp=datetime.now(),
                success=success,
                duration_ms=duration,
                error=None if success else "Simulated failure",
            )

            monitor.record_check(check)

        await asyncio.sleep(0.1)

    # Print dashboard
    monitor.print_status_dashboard()

    # Generate report
    report = monitor.generate_health_report()
    print("\nHealth Report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
