"""
Data Collection Orchestrator

Coordinates parallel data collection from multiple sources with health monitoring,
automatic fallbacks, and comprehensive error handling.
"""

if __name__ == "__main__" and __package__ is None:
    # Allow running as a standalone script (python src/data/data_orchestrator.py)
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))
    __package__ = "src.data"

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal

from .action_network_client import ActionNetworkClient
from .espn_client import ESPNClient
from .massey_ratings_scraper import MasseyRatingsScraper
from .nfl_com_client import NFLComClient
from .overtime_api_client import (
    OvertimeApiClient as OvertimeAPIClient,
)  # Updated to use new API client
from .validated_espn import DataQualityReport, ESPNDataValidator
from .weather_client import WeatherClient

logger = logging.getLogger(__name__)
action_network_client = ActionNetworkClient(headless=False)

class DataSource(str, Enum):
    """Available data sources."""

    ESPN = "espn"
    ACTION_NETWORK = "action_network"
    OVERTIME = "overtime"
    NFL_COM = "nfl_com"
    MASSEY = "massey"
    WEATHER = "weather"


class CollectionStatus(str, Enum):
    """Status of a data collection task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEGRADED = "degraded"  # Completed with warnings


@dataclass
class CollectionTask:
    """A single data collection task."""

    source: DataSource
    description: str
    function: Callable
    priority: int = 1  # Lower = higher priority
    timeout: float = 120.0
    retry_count: int = 0
    max_retries: int = 3
    status: CollectionStatus = CollectionStatus.PENDING
    result: Any = None
    error: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    quality_report: DataQualityReport | None = None


@dataclass
class CollectionReport:
    """Report of all data collection activities."""

    start_time: datetime
    end_time: datetime | None = None
    tasks: list[CollectionTask] = field(default_factory=list)
    total_sources: int = 0
    successful_sources: int = 0
    failed_sources: int = 0
    degraded_sources: int = 0

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_sources == 0:
            return 0.0
        return (self.successful_sources / self.total_sources) * 100

    @property
    def is_healthy(self) -> bool:
        """Check if overall collection is healthy (>80% success)."""
        return self.success_rate >= 80.0

    def get_failed_tasks(self) -> list[CollectionTask]:
        """Get list of failed tasks."""
        return [t for t in self.tasks if t.status == CollectionStatus.FAILED]

    def get_degraded_tasks(self) -> list[CollectionTask]:
        """Get list of degraded tasks."""
        return [t for t in self.tasks if t.status == CollectionStatus.DEGRADED]


class DataOrchestrator:
    """
    Orchestrates data collection from multiple sources.

    Features:
    - Parallel execution with priority queuing
    - Automatic retries with exponential backoff
    - Health monitoring and circuit breaking
    - Quality validation for all data
    - Comprehensive reporting
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 5,
        enable_retries: bool = True,
        enable_validation: bool = True,
    ):
        """
        Initialize data orchestrator.

        Args:
            max_concurrent_tasks: Maximum number of parallel tasks
            enable_retries: Enable automatic retries on failure
            enable_validation: Enable data quality validation
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.enable_retries = enable_retries
        self.enable_validation = enable_validation
        self._tasks: list[CollectionTask] = []
        self._semaphore: asyncio.Semaphore | None = None

    async def collect_all_nfl_data(
        self,
        week: int | None = None,
        season: int | None = None,
        include_weather: bool = False,
        include_nfl_com: bool = False,
        include_massey: bool = False,
        include_action_network: bool = True,
        include_overtime: bool = True,
    ) -> CollectionReport:
        """
        Collect all available NFL data from all sources.

        Args:
            week: Week number (optional)
            season: Season year (optional, used for NFL.com schedule)
            include_weather: Include weather data for games
            include_nfl_com: Include NFL.com official schedule
            include_massey: Include Massey Ratings power numbers
            include_action_network: Include Action Network odds
            include_overtime: Include Overtime.ag odds

        Returns:
            Collection report with results and quality metrics
        """
        logger.info(f"Starting NFL data collection for week {week or 'current'}")

        self._tasks = []
        report = CollectionReport(start_time=datetime.now())

        resolved_week, resolved_season = await self._resolve_week_and_season(
            "NFL", week, season
        )

        # Add ESPN tasks
        self._add_task(
            CollectionTask(
                source=DataSource.ESPN,
                description=f"ESPN NFL scoreboard week {resolved_week or week}",
                function=lambda: self._collect_espn_scoreboard("NFL", resolved_week),
                priority=1,
            )
        )

        self._add_task(
            CollectionTask(
                source=DataSource.ESPN,
                description="ESPN NFL teams",
                function=lambda: self._collect_espn_teams("NFL"),
                priority=2,
            )
        )

        # Add Action Network task
        if include_action_network:
            self._add_task(
                CollectionTask(
                    source=DataSource.ACTION_NETWORK,
                    description="Action Network NFL odds",
                    function=lambda: self._collect_action_network_odds("NFL"),
                    priority=1,
                )
            )

        # Add Overtime task
        if include_overtime:
            self._add_task(
                CollectionTask(
                    source=DataSource.OVERTIME,
                    description=f"Overtime NFL games week {resolved_week or week}",
                    function=lambda: self._collect_overtime_games("NFL", resolved_week),
                    priority=1,
                )
            )

        # Add NFL.com schedule task
        if include_nfl_com and resolved_week is not None and resolved_season is not None:
            self._add_task(
                CollectionTask(
                    source=DataSource.NFL_COM,
                    description=f"NFL.com schedule week {resolved_week}",
                    function=lambda: self._collect_nfl_com_schedule(
                        resolved_week, resolved_season
                    ),
                    priority=2,
                )
            )
        elif include_nfl_com:
            logger.warning(
                "NFL.com schedule requested but week/season could not be resolved"
            )

        # Add Massey Ratings
        if include_massey:
            self._add_task(
                CollectionTask(
                    source=DataSource.MASSEY,
                    description="Massey Ratings NFL power numbers",
                    function=lambda: self._collect_massey_ratings("NFL"),
                    priority=2,
                )
            )

        # Execute all tasks
        await self._execute_tasks()

        # Generate report
        report.end_time = datetime.now()
        report.tasks = self._tasks
        report.total_sources = len(self._tasks)
        report.successful_sources = sum(
            1 for t in self._tasks if t.status == CollectionStatus.COMPLETED
        )
        report.failed_sources = sum(
            1 for t in self._tasks if t.status == CollectionStatus.FAILED
        )
        report.degraded_sources = sum(
            1 for t in self._tasks if t.status == CollectionStatus.DEGRADED
        )

        self._log_report(report)
        return report

    async def collect_all_ncaaf_data(
        self,
        week: int | None = None,
        season: int | None = None,
        include_massey: bool = False,
        include_action_network: bool = True,
        include_overtime: bool = True,
    ) -> CollectionReport:
        """
        Collect all available NCAAF data from all sources.

        Args:
            week: Week number (optional)
            season: Season year (optional, currently used for ESPN inference)
            include_massey: Include Massey Ratings power numbers
            include_action_network: Include Action Network odds
            include_overtime: Include Overtime.ag odds

        Returns:
            Collection report with results and quality metrics
        """
        logger.info(f"Starting NCAAF data collection for week {week or 'current'}")

        self._tasks = []
        report = CollectionReport(start_time=datetime.now())

        resolved_week, resolved_season = await self._resolve_week_and_season(
            "NCAAF", week, season
        )

        # Add ESPN tasks
        self._add_task(
            CollectionTask(
                source=DataSource.ESPN,
                description=f"ESPN NCAAF scoreboard week {resolved_week or week}",
                function=lambda: self._collect_espn_scoreboard(
                    "NCAAF", resolved_week
                ),
                priority=1,
            )
        )

        self._add_task(
            CollectionTask(
                source=DataSource.ESPN,
                description="ESPN NCAAF teams",
                function=lambda: self._collect_espn_teams("NCAAF"),
                priority=2,
            )
        )

        # Add Action Network task
        if include_action_network:
            self._add_task(
                CollectionTask(
                    source=DataSource.ACTION_NETWORK,
                    description="Action Network NCAAF odds",
                    function=lambda: self._collect_action_network_odds("NCAAF"),
                    priority=1,
                )
            )

        # Add Overtime task
        if include_overtime:
            self._add_task(
                CollectionTask(
                    source=DataSource.OVERTIME,
                    description=f"Overtime NCAAF games week {resolved_week or week}",
                    function=lambda: self._collect_overtime_games(
                        "NCAAF", resolved_week
                    ),
                    priority=1,
                )
            )

        # Add Massey Ratings
        if include_massey:
            self._add_task(
                CollectionTask(
                    source=DataSource.MASSEY,
                    description="Massey Ratings NCAAF power numbers",
                    function=lambda: self._collect_massey_ratings("NCAAF"),
                    priority=2,
                )
            )

        # Execute all tasks
        await self._execute_tasks()

        # Generate report
        report.end_time = datetime.now()
        report.tasks = self._tasks
        report.total_sources = len(self._tasks)
        report.successful_sources = sum(
            1 for t in self._tasks if t.status == CollectionStatus.COMPLETED
        )
        report.failed_sources = sum(
            1 for t in self._tasks if t.status == CollectionStatus.FAILED
        )
        report.degraded_sources = sum(
            1 for t in self._tasks if t.status == CollectionStatus.DEGRADED
        )

        self._log_report(report)
        return report

    async def collect_weather_for_games(
        self,
        games: list[dict[str, Any]],
    ) -> CollectionReport:
        """
        Collect weather data for a list of games.

        Args:
            games: List of game dictionaries with venue information

        Returns:
            Collection report
        """
        logger.info(f"Collecting weather for {len(games)} games")

        self._tasks = []
        report = CollectionReport(start_time=datetime.now())

        for game in games:
            venue = game.get("venue", {})
            city = venue.get("city")
            state = venue.get("state")
            game_time = game.get("date")

            if city and state and game_time:
                self._add_task(
                    CollectionTask(
                        source=DataSource.WEATHER,
                        description=f"Weather for {city}, {state}",
                        function=lambda c=city,
                        s=state,
                        t=game_time: self._collect_weather(c, s, t),
                        priority=2,
                    )
                )

        await self._execute_tasks()

        report.end_time = datetime.now()
        report.tasks = self._tasks
        report.total_sources = len(self._tasks)
        report.successful_sources = sum(
            1 for t in self._tasks if t.status == CollectionStatus.COMPLETED
        )
        report.failed_sources = sum(
            1 for t in self._tasks if t.status == CollectionStatus.FAILED
        )

        self._log_report(report)
        return report

    def _add_task(self, task: CollectionTask) -> None:
        """Add a task to the queue."""
        self._tasks.append(task)

    async def _execute_tasks(self) -> None:
        """Execute all tasks with controlled concurrency."""
        # Sort by priority
        self._tasks.sort(key=lambda t: t.priority)

        # Create semaphore for concurrency control
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

        # Execute tasks
        await asyncio.gather(
            *[self._execute_task(task) for task in self._tasks],
            return_exceptions=True,
        )

    async def _execute_task(self, task: CollectionTask) -> None:
        """Execute a single task with retry logic."""
        async with self._semaphore:  # type: ignore
            task.start_time = datetime.now()
            task.status = CollectionStatus.RUNNING

            logger.info(f"Starting: {task.description}")

            for attempt in range(task.max_retries if self.enable_retries else 1):
                try:
                    # Execute with timeout
                    task.result = await asyncio.wait_for(
                        task.function(), timeout=task.timeout
                    )

                    # Validate if enabled
                    if self.enable_validation:
                        await self._validate_result(task)

                    task.status = CollectionStatus.COMPLETED
                    logger.info(f"[OK] Completed: {task.description}")
                    break

                except asyncio.TimeoutError:
                    error_msg = f"Timeout after {task.timeout}s"
                    logger.warning(
                        f"Attempt {attempt + 1}/{task.max_retries} failed: {task.description} - {error_msg}"
                    )
                    task.error = error_msg
                    task.retry_count = attempt + 1

                    if attempt < task.max_retries - 1:
                        # Exponential backoff
                        wait_time = 2**attempt
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        task.status = CollectionStatus.FAILED
                        logger.error(f"[X] Failed: {task.description}")

                except Exception as e:
                    error_msg = str(e)
                    logger.warning(
                        f"Attempt {attempt + 1}/{task.max_retries} failed: {task.description} - {error_msg}"
                    )
                    task.error = error_msg
                    task.retry_count = attempt + 1

                    if attempt < task.max_retries - 1:
                        wait_time = 2**attempt
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        task.status = CollectionStatus.FAILED
                        logger.error(f"[X] Failed: {task.description}")

            task.end_time = datetime.now()

    async def _validate_result(self, task: CollectionTask) -> None:
        """Validate task result and update status."""
        if not task.result:
            task.status = CollectionStatus.DEGRADED
            logger.warning(f"No data returned from {task.description}")
            return

        # Validate based on source
        if task.source == DataSource.ESPN:
            await self._validate_espn_result(task)

    async def _validate_espn_result(self, task: CollectionTask) -> None:
        """Validate ESPN data result."""
        if isinstance(task.result, list):
            validator = ESPNDataValidator()

            # Determine data type
            if "teams" in task.description.lower():
                _, report = validator.validate_teams(task.result)
            elif (
                "games" in task.description.lower()
                or "scoreboard" in task.description.lower()
            ):
                # Convert scoreboard to game format if needed
                games_data = self._extract_games_from_scoreboard(task.result)
                _, report = validator.validate_games(games_data)
            else:
                return

            task.quality_report = report

            if not report.is_acceptable:
                task.status = CollectionStatus.DEGRADED
                logger.warning(
                    f"Low quality data from {task.description}: "
                    f"{report.validation_rate:.1f}% valid"
                )

    def _extract_games_from_scoreboard(
        self, scoreboard_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract games from ESPN scoreboard format."""
        events = scoreboard_data.get("events", [])
        games = []

        for event in events:
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])

            if len(competitors) >= 2:
                home = competitors[1]
                away = competitors[0]

                game = {
                    "id": event.get("id", ""),
                    "name": event.get("name", ""),
                    "short_name": event.get("shortName", ""),
                    "date": event.get("date", ""),
                    "status": event.get("status", {}).get("type", {}).get("name", ""),
                    "home_team_id": home.get("team", {}).get("id", ""),
                    "home_team_name": home.get("team", {}).get("displayName", ""),
                    "home_team_score": home.get("score"),
                    "away_team_id": away.get("team", {}).get("id", ""),
                    "away_team_name": away.get("team", {}).get("displayName", ""),
                    "away_team_score": away.get("score"),
                    "venue_name": competition.get("venue", {}).get("fullName"),
                    "venue_city": competition.get("venue", {})
                    .get("address", {})
                    .get("city"),
                    "venue_state": competition.get("venue", {})
                    .get("address", {})
                    .get("state"),
                    "is_indoor": competition.get("venue", {}).get("indoor", False),
                    "league": scoreboard_data.get("league", ""),
                    "week": event.get("week", {}).get("number"),
                    "season": event.get("season", {}).get("year"),
                    "source": "espn",
                    "fetch_time": datetime.now().isoformat(),
                }
                games.append(game)

        return games

    async def _resolve_week_and_season(
        self,
        league: Literal["NFL", "NCAAF"],
        week: int | None,
        season: int | None,
    ) -> tuple[int | None, int | None]:
        """
        Resolve week/season using ESPN when not provided.

        Falls back to provided values if inference fails.
        """
        resolved_week = week
        resolved_season = season

        if week is not None and season is not None:
            return resolved_week, resolved_season

        try:
            async with ESPNClient() as client:
                scoreboard = await client.get_scoreboard(
                    league, week=week, season=season
                )

            resolved_week = resolved_week or scoreboard.get("week", {}).get("number")
            resolved_season = resolved_season or scoreboard.get("season", {}).get("year")
        except Exception as exc:
            logger.warning(
                f"Could not infer {league} week/season from ESPN: {exc}"
            )

        return resolved_week, resolved_season

    async def _collect_espn_scoreboard(
        self, league: Literal["NFL", "NCAAF"], week: int | None
    ) -> dict[str, Any]:
        """Collect ESPN scoreboard data."""
        async with ESPNClient() as client:
            return await client.get_scoreboard(league, week=week)

    async def _collect_espn_teams(
        self, league: Literal["NFL", "NCAAF"]
    ) -> list[dict[str, Any]]:
        """Collect ESPN teams data."""
        async with ESPNClient() as client:
            return await client.get_teams(league)

    async def _collect_action_network_odds(
        self, league: Literal["NFL", "NCAAF"]
    ) -> list[dict[str, Any]]:
        """Collect Action Network odds data."""
        async with ActionNetworkClient() as client:
            return await client.fetch_odds(league)

    async def _collect_overtime_games(
        self, league: Literal["NFL", "NCAAF"], week: int | None
    ) -> list[dict[str, Any]]:
        """Collect Overtime games data."""
        client = OvertimeAPIClient()
        sport_sub_type = "NFL" if league == "NFL" else "College Football"
        return await client.fetch_games(
            sport_type="Football",
            sport_sub_type=sport_sub_type,
        )

    async def _collect_nfl_com_schedule(
        self, week: int, season: int
    ) -> list[dict[str, Any]]:
        """Collect NFL.com official schedule."""
        client = NFLComClient()
        try:
            games = await client.get_schedule(season=season, week=week)
            return [game.model_dump(mode="json") for game in games]
        finally:
            await client.close()

    async def _collect_massey_ratings(
        self, league: Literal["NFL", "NCAAF"]
    ) -> dict[str, Any]:
        """Collect Massey Ratings power numbers."""
        scraper = MasseyRatingsScraper()
        if league == "NFL":
            return await scraper.scrape_nfl_ratings(save=False)
        return await scraper.scrape_ncaaf_ratings(save=False)

    async def _collect_weather(
        self, city: str, state: str, game_time: datetime
    ) -> dict[str, Any]:
        """Collect weather data."""
        async with WeatherClient() as client:
            return await client.get_game_forecast(city, state, game_time)

    def _log_report(self, report: CollectionReport) -> None:
        """Log comprehensive report."""
        logger.info("\n" + "=" * 60)
        logger.info("DATA COLLECTION REPORT")
        logger.info("=" * 60)
        logger.info(f"Duration: {report.duration_seconds:.1f}s")
        logger.info(f"Total Sources: {report.total_sources}")
        logger.info(f"Successful: {report.successful_sources}")
        logger.info(f"Failed: {report.failed_sources}")
        logger.info(f"Degraded: {report.degraded_sources}")
        logger.info(f"Success Rate: {report.success_rate:.1f}%")
        logger.info(
            f"Health Status: {'[OK] HEALTHY' if report.is_healthy else '[X] UNHEALTHY'}"
        )

        if report.get_failed_tasks():
            logger.info("\nFailed Tasks:")
            for task in report.get_failed_tasks():
                logger.info(f"  [X] {task.description}: {task.error}")

        if report.get_degraded_tasks():
            logger.info("\nDegraded Tasks:")
            for task in report.get_degraded_tasks():
                logger.info(f"  [WARNING] {task.description}")
                if task.quality_report:
                    logger.info(
                        f"    Quality: {task.quality_report.validation_rate:.1f}%"
                    )

        logger.info("=" * 60 + "\n")


# Example usage
async def main():
    """Example usage of DataOrchestrator."""
    orchestrator = DataOrchestrator(
        max_concurrent_tasks=5,
        enable_retries=True,
        enable_validation=True,
    )

    # Collect all NFL data for week 10
    report = await orchestrator.collect_all_nfl_data(week=10)

    print(f"\nCollection completed in {report.duration_seconds:.1f}s")
    print(f"Success rate: {report.success_rate:.1f}%")
    print(f"Healthy: {report.is_healthy}")


if __name__ == "__main__":
    asyncio.run(main())
