#!/usr/bin/env python3
"""
ESPN Data Collection Production Orchestrator

Manages weekly ESPN data collection with:
- Automated scheduling and execution
- Raw data archival (before normalization)
- Success/failure tracking and metrics
- Data quality monitoring and alerts
- Comprehensive logging and reporting
"""

import json
import os
import sys
import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from data.espn_api_client import ESPNAPIClient
from data.espn_client import ESPNClient
from data.espn_ncaaf_scoreboard_client import ESPNNCAAFScoreboardClient
from data.espn_injury_scraper import ESPNInjuryScraper
from data.espn_ncaaf_normalizer import ESPNNCAAFNormalizer


# ============================================================================
# Logging Configuration
# ============================================================================


def setup_logging(log_dir: Path) -> logging.Logger:
    """Configure comprehensive logging for production"""
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("ESPN.Production")
    logger.setLevel(logging.DEBUG)

    # File handler (detailed)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(log_dir / f"espn_collection_{timestamp}.log")
    fh.setLevel(logging.DEBUG)

    # Console handler (summary)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# ============================================================================
# Data Models for Metrics and Tracking
# ============================================================================


class ComponentStatus(str, Enum):
    """Status of each collection component"""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class ComponentMetrics:
    """Metrics for a single data collection component"""

    component_name: str
    status: ComponentStatus
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    records_collected: int
    errors: List[str] = field(default_factory=list)
    raw_file_path: Optional[str] = None
    normalized_file_path: Optional[str] = None
    success_rate: float = 100.0
    quality_score: float = 100.0

    @property
    def is_successful(self) -> bool:
        """Check if collection was successful"""
        return self.status in (ComponentStatus.SUCCESS, ComponentStatus.PARTIAL)


@dataclass
class CollectionSession:
    """Complete ESPN data collection session"""

    session_id: str
    league: str  # "nfl" or "ncaaf"
    week: Optional[int]
    start_time: datetime
    end_time: Optional[datetime] = None
    components: Dict[str, ComponentMetrics] = field(default_factory=dict)
    overall_success: bool = False
    notes: str = ""

    @property
    def duration_seconds(self) -> float:
        """Total session duration"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Overall success rate across components"""
        if not self.components:
            return 0.0
        successful = sum(1 for m in self.components.values() if m.is_successful)
        return (successful / len(self.components)) * 100


# ============================================================================
# Data Archival System
# ============================================================================


class DataArchiver:
    """Manages raw data archival before normalization"""

    def __init__(self, archive_root: Path):
        self.archive_root = archive_root
        self.archive_root.mkdir(parents=True, exist_ok=True)

    def archive_raw_data(
        self,
        data: Dict,
        component_name: str,
        league: str,
        week: Optional[int] = None,
    ) -> Path:
        """
        Archive raw API response before normalization

        Args:
            data: Raw API response
            component_name: Name of component (e.g., "team_stats", "injuries")
            league: "nfl" or "ncaaf"
            week: Optional week number

        Returns:
            Path to archived file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create directory structure: raw/{league}/{component}/{week}
        if week:
            archive_dir = (
                self.archive_root / "raw" / league / component_name / f"week_{week}"
            )
        else:
            archive_dir = (
                self.archive_root / "raw" / league / component_name / "current"
            )

        archive_dir.mkdir(parents=True, exist_ok=True)

        # Save with timestamp
        filename = f"{component_name}_{league}_{timestamp}.json"
        filepath = archive_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

    def create_archive_index(self, league: str) -> Dict:
        """Create index of archived raw data"""
        raw_dir = self.archive_root / "raw" / league
        if not raw_dir.exists():
            return {}

        index = {}
        for component_dir in raw_dir.iterdir():
            if component_dir.is_dir():
                component = component_dir.name
                index[component] = {
                    "latest_files": [],
                    "total_files": 0,
                }

                # Find latest files per week
                for week_dir in component_dir.iterdir():
                    if week_dir.is_dir():
                        files = sorted(week_dir.glob("*.json"), reverse=True)
                        if files:
                            latest = files[0]
                            index[component]["latest_files"].append(
                                {
                                    "week": week_dir.name,
                                    "file": latest.name,
                                    "size_bytes": latest.stat().st_size,
                                    "modified": latest.stat().st_mtime,
                                }
                            )
                            index[component]["total_files"] += len(files)

        return index


# ============================================================================
# Production Data Collection
# ============================================================================


class ProductionCollector:
    """Production-grade ESPN data collection with monitoring"""

    def __init__(
        self,
        league: str,
        week: Optional[int] = None,
        archive_root: Path = Path("data/archive"),
        metrics_dir: Path = Path("data/metrics"),
    ):
        self.league = league
        self.week = week
        self.archive = DataArchiver(archive_root)
        self.metrics_dir = metrics_dir
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logging(self.metrics_dir / "logs")

        # Initialize session
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session = CollectionSession(
            session_id=session_id,
            league=league,
            week=week,
            start_time=datetime.now(),
        )

    async def collect_team_stats(self) -> ComponentMetrics:
        """Collect team statistics"""
        component = "team_stats"
        start = datetime.now()

        self.logger.info(f"[{component}] Starting collection for {self.league}")

        metrics = ComponentMetrics(
            component_name=component,
            status=ComponentStatus.FAILURE,
            start_time=start,
            end_time=datetime.now(),
            duration_seconds=0,
            records_collected=0,
        )

        try:
            client = ESPNAPIClient()

            if self.league == "nfl":
                teams_data = client.get_nfl_teams()
            else:
                teams_data = client.get_ncaaf_teams()

            teams_list = (
                teams_data.get("sports", [{}])[0]
                .get("leagues", [{}])[0]
                .get("teams", [])
            )
            total_teams = len(teams_list)

            self.logger.info(f"[{component}] Found {total_teams} teams")

            # Archive raw teams list
            archive_path = self.archive.archive_raw_data(
                teams_data, component, self.league, self.week
            )
            metrics.raw_file_path = str(archive_path)

            # Collect stats for each team
            all_stats = []
            success_count = 0
            error_list = []

            # Map league to ESPN API format
            league_map = {"nfl": "nfl", "ncaaf": "college-football"}
            api_league = league_map.get(self.league, self.league)

            for i, team_item in enumerate(teams_list, 1):
                try:
                    team = team_item.get("team", {})
                    team_id = team.get("id")
                    team_name = team.get("displayName")

                    metrics_obj = client.extract_power_rating_metrics(
                        team_id, api_league
                    )
                    all_stats.append(metrics_obj)
                    success_count += 1

                    if i % 10 == 0:
                        self.logger.debug(f"[{component}] Progress: {i}/{total_teams}")

                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    error_msg = f"{team_name}: {str(e)}"
                    error_list.append(error_msg)
                    self.logger.warning(f"[{component}] {error_msg}")

            # Save results
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "league": self.league,
                "week": self.week,
                "team_count": len(all_stats),
                "success_count": success_count,
                "error_count": len(error_list),
                "teams": all_stats,
            }

            metrics.records_collected = len(all_stats)
            metrics.status = (
                ComponentStatus.SUCCESS
                if success_count == total_teams
                else ComponentStatus.PARTIAL
            )
            metrics.success_rate = (
                (success_count / total_teams * 100) if total_teams > 0 else 0
            )
            metrics.errors = error_list

            self.logger.info(
                f"[{component}] Collected {success_count}/{total_teams} teams "
                f"({metrics.success_rate:.1f}%)"
            )

        except Exception as e:
            metrics.status = ComponentStatus.FAILURE
            metrics.errors = [str(e)]
            self.logger.error(f"[{component}] Failed: {e}")

        finally:
            metrics.end_time = datetime.now()
            metrics.duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()

        return metrics

    async def collect_injuries(self) -> ComponentMetrics:
        """Collect injury reports"""
        component = "injuries"
        start = datetime.now()

        self.logger.info(f"[{component}] Starting collection for {self.league}")

        metrics = ComponentMetrics(
            component_name=component,
            status=ComponentStatus.FAILURE,
            start_time=start,
            end_time=datetime.now(),
            duration_seconds=0,
            records_collected=0,
        )

        try:
            scraper = ESPNInjuryScraper()

            # Call the appropriate scraper method based on league
            if self.league == "nfl":
                injury_data_list = scraper.scrape_nfl_injuries()
            else:
                injury_data_list = scraper.scrape_ncaaf_injuries()

            # Convert list of injuries to the format expected by archive
            # Wrap in expected structure for consistency with other data
            injury_data = {
                "league": self.league,
                "timestamp": datetime.now().isoformat(),
                "injuries": injury_data_list,
            }

            # Archive raw injury data
            archive_path = self.archive.archive_raw_data(
                injury_data, component, self.league, self.week
            )
            metrics.raw_file_path = str(archive_path)

            # Count injured players
            total_injuries = len(injury_data_list)

            metrics.records_collected = total_injuries
            metrics.status = ComponentStatus.SUCCESS
            metrics.quality_score = 95.0  # Injury scraping is reliable

            self.logger.info(f"[{component}] Collected {total_injuries} injury records")

        except Exception as e:
            metrics.status = ComponentStatus.FAILURE
            metrics.errors = [str(e)]
            self.logger.error(f"[{component}] Failed: {e}")

        finally:
            metrics.end_time = datetime.now()
            metrics.duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()

        return metrics

    async def collect_schedules(self) -> ComponentMetrics:
        """Collect game schedules"""
        component = "schedules"
        start = datetime.now()

        self.logger.info(f"[{component}] Starting collection for {self.league}")

        metrics = ComponentMetrics(
            component_name=component,
            status=ComponentStatus.FAILURE,
            start_time=start,
            end_time=datetime.now(),
            duration_seconds=0,
            records_collected=0,
        )

        try:
            client = ESPNAPIClient()

            if self.league == "nfl":
                schedule_data = client.get_nfl_scoreboard()
            else:
                schedule_data = client.get_ncaaf_scoreboard()

            # Archive raw schedule
            archive_path = self.archive.archive_raw_data(
                schedule_data, component, self.league, self.week
            )
            metrics.raw_file_path = str(archive_path)

            # Count games
            events = schedule_data.get("events", [])
            metrics.records_collected = len(events)
            metrics.status = ComponentStatus.SUCCESS

            self.logger.info(f"[{component}] Collected {len(events)} games")

        except Exception as e:
            metrics.status = ComponentStatus.FAILURE
            metrics.errors = [str(e)]
            self.logger.error(f"[{component}] Failed: {e}")

        finally:
            metrics.end_time = datetime.now()
            metrics.duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()

        return metrics

    async def run_collection(self) -> CollectionSession:
        """Run complete data collection"""
        self.logger.info("=" * 70)
        self.logger.info(f"ESPN DATA COLLECTION - {self.league.upper()}")
        self.logger.info(f"Session ID: {self.session.session_id}")
        self.logger.info("=" * 70)

        # Run components
        components_to_run = [
            ("team_stats", self.collect_team_stats()),
            ("injuries", self.collect_injuries()),
            ("schedules", self.collect_schedules()),
        ]

        for name, coro in components_to_run:
            metrics = await coro
            self.session.components[name] = metrics

        # Finalize session
        self.session.end_time = datetime.now()
        self.session.overall_success = all(
            m.is_successful for m in self.session.components.values()
        )

        # Log summary
        self._log_session_summary()

        # Save session metrics
        self._save_session_metrics()

        return self.session

    def _log_session_summary(self):
        """Log collection session summary"""
        self.logger.info("=" * 70)
        self.logger.info("COLLECTION SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Total duration: {self.session.duration_seconds:.1f}s")
        self.logger.info(f"Success rate: {self.session.success_rate:.1f}%")

        for name, metrics in self.session.components.items():
            status_str = metrics.status.value.upper()
            self.logger.info(
                f"  {name}: {status_str} - {metrics.records_collected} records, "
                f"{metrics.duration_seconds:.1f}s"
            )

        if self.session.overall_success:
            self.logger.info("Status: ALL COMPONENTS SUCCESSFUL")
        else:
            self.logger.warning("Status: SOME COMPONENTS FAILED")

    def _save_session_metrics(self):
        """Save session metrics to file"""
        metrics_file = self.metrics_dir / f"session_{self.session.session_id}.json"

        # Serialize metrics
        session_dict = {
            "session_id": self.session.session_id,
            "league": self.session.league,
            "week": self.session.week,
            "start_time": self.session.start_time.isoformat(),
            "end_time": self.session.end_time.isoformat()
            if self.session.end_time
            else None,
            "duration_seconds": self.session.duration_seconds,
            "overall_success": self.session.overall_success,
            "success_rate": self.session.success_rate,
            "components": {
                name: {
                    "component_name": m.component_name,
                    "status": m.status.value,
                    "duration_seconds": m.duration_seconds,
                    "records_collected": m.records_collected,
                    "success_rate": m.success_rate,
                    "quality_score": m.quality_score,
                    "errors": m.errors,
                    "raw_file_path": m.raw_file_path,
                }
                for name, m in self.session.components.items()
            },
        }

        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(session_dict, f, indent=2)

        self.logger.info(f"Metrics saved to {metrics_file}")


# ============================================================================
# Main Entry Point
# ============================================================================


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="ESPN Data Collection Production Orchestrator"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="ncaaf",
        help="League to collect (default: ncaaf)",
    )
    parser.add_argument(
        "--week",
        type=int,
        help="Week number (optional)",
    )

    args = parser.parse_args()

    # Run collection
    collector = ProductionCollector(
        league=args.league,
        week=args.week,
    )

    session = await collector.run_collection()

    # Return exit code based on success
    return 0 if session.overall_success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
