#!/usr/bin/env python3
"""
ESPN Data Collection Metrics Monitor

Monitors and reports on:
- API success rates across time
- Data completeness percentages
- Processing time trends
- Quality scores by component
- Alert generation for failures
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import statistics


@dataclass
class MetricsSnapshot:
    """Single point in time metrics"""
    timestamp: datetime
    league: str
    success_rate: float
    records_collected: int
    avg_duration_seconds: float
    quality_score: float
    components_successful: int
    components_total: int


class MetricsMonitor:
    """Monitor and analyze ESPN collection metrics"""

    def __init__(self, metrics_dir: Path = Path("data/metrics")):
        self.metrics_dir = metrics_dir

    def load_session_metrics(self, session_file: Path) -> Dict:
        """Load metrics from session file"""
        with open(session_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_sessions(self, league: Optional[str] = None) -> List[Dict]:
        """Get all collected session metrics"""
        sessions = []

        if not self.metrics_dir.exists():
            return sessions

        for metrics_file in sorted(self.metrics_dir.glob("session_*.json")):
            try:
                metrics = self.load_session_metrics(metrics_file)

                if league is None or metrics.get("league") == league:
                    sessions.append(metrics)

            except Exception as e:
                print(f"Error loading {metrics_file}: {e}")

        return sessions

    def calculate_trends(self, sessions: List[Dict]) -> Dict:
        """Calculate trends across sessions"""
        if not sessions:
            return {}

        # Extract metrics
        success_rates = [s.get("success_rate", 0) for s in sessions]
        durations = [s.get("duration_seconds", 0) for s in sessions]
        total_records = [
            sum(c.get("records_collected", 0) for c in s.get("components", {}).values())
            for s in sessions
        ]

        return {
            "sessions_count": len(sessions),
            "success_rate": {
                "current": success_rates[-1] if success_rates else 0,
                "average": statistics.mean(success_rates) if success_rates else 0,
                "trend": "improving" if success_rates[-1] > statistics.mean(success_rates[:-1]) else "declining",
            },
            "processing_time": {
                "current": durations[-1] if durations else 0,
                "average": statistics.mean(durations) if durations else 0,
                "fastest": min(durations) if durations else 0,
                "slowest": max(durations) if durations else 0,
            },
            "records_collected": {
                "total": sum(total_records),
                "average": statistics.mean(total_records) if total_records else 0,
                "latest": total_records[-1] if total_records else 0,
            },
        }

    def generate_quality_report(self, league: str = "ncaaf") -> str:
        """Generate data quality report"""
        sessions = self.get_all_sessions(league)

        if not sessions:
            return f"No sessions found for {league}"

        trends = self.calculate_trends(sessions)
        latest = sessions[-1]

        report = []
        report.append("=" * 70)
        report.append(f"ESPN DATA COLLECTION QUALITY REPORT - {league.upper()}")
        report.append("=" * 70)
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 70)
        report.append(f"Total sessions: {trends.get('sessions_count', 0)}")
        report.append(f"Latest session: {latest.get('session_id', 'N/A')}")
        report.append("")

        # Success metrics
        report.append("SUCCESS METRICS")
        report.append("-" * 70)
        success = trends.get("success_rate", {})
        report.append(f"Current success rate: {success.get('current', 0):.1f}%")
        report.append(f"Average success rate: {success.get('average', 0):.1f}%")
        report.append(f"Trend: {success.get('trend', 'unknown')}")
        report.append("")

        # Performance metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 70)
        perf = trends.get("processing_time", {})
        report.append(f"Current duration: {perf.get('current', 0):.1f}s")
        report.append(f"Average duration: {perf.get('average', 0):.1f}s")
        report.append(f"Fastest run: {perf.get('fastest', 0):.1f}s")
        report.append(f"Slowest run: {perf.get('slowest', 0):.1f}s")
        report.append("")

        # Data completeness
        report.append("DATA COMPLETENESS")
        report.append("-" * 70)
        records = trends.get("records_collected", {})
        report.append(f"Total records collected: {records.get('total', 0)}")
        report.append(f"Average per session: {records.get('average', 0):.0f}")
        report.append(f"Latest session: {records.get('latest', 0)}")
        report.append("")

        # Component status
        report.append("LATEST COMPONENT STATUS")
        report.append("-" * 70)
        for comp_name, comp_metrics in latest.get("components", {}).items():
            status = comp_metrics.get("status", "unknown").upper()
            records = comp_metrics.get("records_collected", 0)
            duration = comp_metrics.get("duration_seconds", 0)
            report.append(f"  {comp_name}: {status} - {records} records, {duration:.1f}s")

        if comp_metrics.get("errors"):
            report.append("    Errors:")
            for error in comp_metrics.get("errors", [])[:3]:  # Show first 3 errors
                report.append(f"      - {error}")

        report.append("")

        # Quality score
        report.append("QUALITY SCORES")
        report.append("-" * 70)
        total_quality = 0
        component_count = 0

        for comp_metrics in latest.get("components", {}).values():
            quality = comp_metrics.get("quality_score", 0)
            total_quality += quality
            component_count += 1

        avg_quality = total_quality / component_count if component_count > 0 else 0
        report.append(f"Average quality score: {avg_quality:.1f}/100")

        # Quality grading
        if avg_quality >= 95:
            grade = "EXCELLENT"
        elif avg_quality >= 85:
            grade = "GOOD"
        elif avg_quality >= 75:
            grade = "FAIR"
        else:
            grade = "POOR"

        report.append(f"Grade: {grade}")
        report.append("")

        report.append("=" * 70)

        return "\n".join(report)

    def detect_anomalies(self, league: str = "ncaaf") -> List[str]:
        """Detect anomalies in collection patterns"""
        sessions = self.get_all_sessions(league)

        if not sessions:
            return []

        anomalies = []
        trends = self.calculate_trends(sessions)

        # Check for declining success rate
        success_rates = [s.get("success_rate", 0) for s in sessions]
        if len(success_rates) >= 3:
            recent_avg = statistics.mean(success_rates[-3:])
            overall_avg = statistics.mean(success_rates)

            if recent_avg < overall_avg * 0.8:  # 20% below average
                anomalies.append(
                    f"ALERT: Success rate declining ({recent_avg:.1f}% vs {overall_avg:.1f}%)"
                )

        # Check for slow processing
        durations = [s.get("duration_seconds", 0) for s in sessions]
        if durations:
            avg_duration = statistics.mean(durations)
            latest_duration = durations[-1]

            if latest_duration > avg_duration * 1.5:  # 50% slower than average
                anomalies.append(
                    f"ALERT: Processing time increased ({latest_duration:.1f}s vs {avg_duration:.1f}s avg)"
                )

        # Check for missing data
        latest = sessions[-1]
        for comp_metrics in latest.get("components", {}).values():
            if comp_metrics.get("records_collected", 0) == 0:
                anomalies.append(
                    f"ALERT: {comp_metrics.get('component_name', 'Unknown')} "
                    f"collected no data"
                )

        return anomalies

    def export_metrics_csv(self, output_file: Path, league: str = "ncaaf"):
        """Export metrics to CSV for analysis"""
        sessions = self.get_all_sessions(league)

        if not sessions:
            print(f"No sessions found for {league}")
            return

        # CSV header
        rows = [
            "session_id,league,week,success_rate,duration_seconds,records_collected,"
            "team_stats_status,injuries_status,schedules_status"
        ]

        for session in sessions:
            components = session.get("components", {})
            row = (
                f"{session.get('session_id')},"
                f"{session.get('league')},"
                f"{session.get('week') or 'N/A'},"
                f"{session.get('success_rate', 0):.1f},"
                f"{session.get('duration_seconds', 0):.1f},"
                f"{sum(c.get('records_collected', 0) for c in components.values())},"
                f"{components.get('team_stats', {}).get('status', 'unknown')},"
                f"{components.get('injuries', {}).get('status', 'unknown')},"
                f"{components.get('schedules', {}).get('status', 'unknown')}"
            )
            rows.append(row)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(rows))

        print(f"Metrics exported to {output_file}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ESPN Metrics Monitor")
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="ncaaf",
        help="League to monitor (default: ncaaf)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Show quality report",
    )
    parser.add_argument(
        "--anomalies",
        action="store_true",
        help="Detect anomalies",
    )
    parser.add_argument(
        "--export-csv",
        type=Path,
        help="Export metrics to CSV file",
    )

    args = parser.parse_args()

    monitor = MetricsMonitor()

    # Show quality report
    if args.report or not any([args.anomalies, args.export_csv]):
        print(monitor.generate_quality_report(args.league))
        print()

    # Detect anomalies
    if args.anomalies:
        anomalies = monitor.detect_anomalies(args.league)
        if anomalies:
            print("DETECTED ANOMALIES:")
            for anomaly in anomalies:
                print(f"  - {anomaly}")
        else:
            print("No anomalies detected")
        print()

    # Export CSV
    if args.export_csv:
        monitor.export_metrics_csv(args.export_csv, args.league)


if __name__ == "__main__":
    main()
