# Data Collection Guide

Comprehensive guide to the Billy Walters Sports Analyzer data collection infrastructure.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Data Sources](#data-sources)
4. [Components](#components)
5. [Usage Examples](#usage-examples)
6. [Configuration](#configuration)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Best Practices](#best-practices)

## Overview

The data collection system provides:

- **Multiple Data Sources**: ESPN, Action Network, Overtime, Weather APIs
- **Robust Error Handling**: Automatic retries, circuit breakers, fallbacks
- **Data Validation**: Quality checks and completeness scoring
- **Health Monitoring**: Real-time status tracking and alerting
- **Parallel Execution**: Efficient concurrent data collection
- **Comprehensive Testing**: Integration tests for reliability

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Orchestrator                         │
│  • Parallel execution with priority queuing                 │
│  • Automatic retries and circuit breaking                   │
│  • Health monitoring and quality validation                 │
└───────────┬─────────────────────────────────────────────────┘
            │
            ├──── ESPN Client
            │     ├── Teams, Stats, Schedules
            │     ├── Circuit breaker pattern
            │     └── Exponential backoff retry
            │
            ├──── Action Network Client
            │     ├── Odds scraping (Playwright)
            │     ├── NFL & NCAAF support
            │     └── Rate limiting
            │
            ├──── Overtime Client
            │     ├── Game data & schedules
            │     ├── API authentication
            │     └── Auto-retry logic
            │
            └──── Weather Client
                  ├── AccuWeather + OpenWeather
                  ├── Automatic fallback
                  └── Game forecast integration
```

## Quick Start

### 1. Basic ESPN Data Collection

```python
import asyncio
from src.data.espn_client import ESPNClient

async def collect_espn_data():
    async with ESPNClient() as client:
        # Get NFL teams
        teams = await client.get_teams("NFL")
        print(f"Fetched {len(teams)} NFL teams")

        # Get current week scoreboard
        scoreboard = await client.get_scoreboard("NFL", week=10)
        games = scoreboard.get("events", [])
        print(f"Fetched {len(games)} games")

        # Get team statistics
        if teams:
            team_id = teams[0]["id"]
            stats = await client.get_team_stats("NFL", team_id)
            print(f"Fetched stats for {teams[0]['name']}")

asyncio.run(collect_espn_data())
```

### 2. Parallel Data Collection with Orchestrator

```python
import asyncio
from src.data.data_orchestrator import DataOrchestrator

async def collect_all_data():
    orchestrator = DataOrchestrator(
        max_concurrent_tasks=5,
        enable_retries=True,
        enable_validation=True,
    )

    # Collect all NFL data for week 10
    report = await orchestrator.collect_all_nfl_data(week=10)

    print(f"Collection completed in {report.duration_seconds:.1f}s")
    print(f"Success rate: {report.success_rate:.1f}%")
    print(f"Successful: {report.successful_sources}/{report.total_sources}")

    # Check for failures
    if report.failed_sources > 0:
        print("\nFailed tasks:")
        for task in report.get_failed_tasks():
            print(f"  - {task.description}: {task.error}")

asyncio.run(collect_all_data())
```

### 3. Health Monitoring

```python
from datetime import datetime
from src.data.health_monitor import HealthMonitor, HealthCheck

# Initialize monitor
monitor = HealthMonitor(
    history_size=100,
    alert_threshold_failures=3,
)

# Register alert callback
def alert_handler(alert):
    print(f"🚨 ALERT: {alert.message}")

monitor.register_alert_callback(alert_handler)

# Record health checks
check = HealthCheck(
    source="espn",
    timestamp=datetime.now(),
    success=True,
    duration_ms=150.0,
)
monitor.record_check(check)

# View status dashboard
monitor.print_status_dashboard()
```

## Data Sources

### ESPN API

**Base URLs:**
- NFL: `https://site.api.espn.com/apis/site/v2/sports/football/nfl`
- NCAAF: `https://site.api.espn.com/apis/site/v2/sports/football/college-football`

**Endpoints:**
- `/teams` - List of all teams
- `/scoreboard` - Games and scores
- `/teams/{id}/statistics` - Team statistics
- `/teams/{id}/roster` - Team roster
- `/standings` - League standings
- `/summary?event={id}` - Game details

**Features:**
- Circuit breaker after 5 consecutive failures
- Exponential backoff retry (1s, 2s, 4s)
- Rate limiting (0.5s between requests)
- Automatic metadata enrichment

**Example:**
```python
async with ESPNClient() as client:
    # Get all NFL teams
    teams = await client.get_teams("NFL")

    # Get week 10 scoreboard
    scoreboard = await client.get_scoreboard("NFL", week=10)

    # Get team stats
    stats = await client.get_team_stats("NFL", "16", season=2024)
```

### Action Network (Playwright)

**Features:**
- Playwright-based web scraping
- Handles authentication
- Rate limiting (2s between requests)
- Supports NFL and NCAAF

**Configuration:**
```bash
# Required environment variables
ACTION_USERNAME=your_username
ACTION_PASSWORD=your_password
```

**Example:**
```python
from src.data.action_network_client import ActionNetworkClient

async with ActionNetworkClient(headless=True) as client:
    # Fetch NFL odds
    nfl_odds = await client.fetch_nfl_odds()

    # Fetch NCAAF odds
    ncaaf_odds = await client.fetch_ncaaf_odds()
```

### Overtime API

**Features:**
- Game schedules and data
- Team statistics
- Authentication handling
- Rate limiting (1s between requests)

**Configuration:**
```bash
# Required environment variables
OV_CUSTOMER_ID=your_customer_id
OV_PASSWORD=your_password
```

**Example:**
```python
from src.data.overtime_client import OvertimeAPIClient

async with OvertimeAPIClient() as client:
    # Fetch NFL games
    games = await client.fetch_nfl_games(week=10)

    # Fetch game details
    details = await client.fetch_game_details("game_id_123")
```

### Weather APIs

**Features:**
- AccuWeather + OpenWeather fallback
- Game forecast integration
- Automatic source failover
- Rate limiting

**Configuration:**
```bash
# At least one required
ACCUWEATHER_API_KEY=your_accuweather_key
OPENWEATHER_API_KEY=your_openweather_key
```

**Example:**
```python
from src.data.weather_client import WeatherClient
from datetime import datetime

async with WeatherClient() as client:
    game_time = datetime(2024, 11, 10, 13, 0)  # 1 PM

    forecast = await client.get_game_forecast(
        city="Kansas City",
        state="MO",
        game_time=game_time,
    )

    print(f"Temperature: {forecast['temperature_f']}°F")
    print(f"Wind: {forecast['wind_speed_mph']} mph")
```

## Components

### ESPN Client (`src/data/espn_client.py`)

Robust ESPN API client with:
- Circuit breaker pattern (opens after 5 failures)
- Automatic retry with exponential backoff
- Rate limiting (0.5s default)
- Data enrichment with metadata

**Key Methods:**
- `get_teams(league)` - Get all teams
- `get_scoreboard(league, week, season)` - Get games
- `get_team_stats(league, team_id, season)` - Get statistics
- `get_team_roster(league, team_id)` - Get roster
- `get_standings(league, season)` - Get standings
- `get_game_details(league, game_id)` - Get game details

### Data Validator (`src/data/validated_espn.py`)

Validates and scores data quality:
- Schema validation with Pydantic
- Completeness scoring (0-100%)
- Quality scoring (0-100%)
- Detailed error reporting

**Models:**
- `ESPNTeamValidated` - Team data validation
- `ESPNGameValidated` - Game data validation
- `ESPNStatsValidated` - Statistics validation
- `DataQualityReport` - Quality assessment report

**Example:**
```python
from src.data.validated_espn import ESPNDataValidator

validator = ESPNDataValidator()
validated_teams, report = validator.validate_teams(raw_teams_data)

print(f"Valid: {report.valid_records}/{report.total_records}")
print(f"Quality Score: {report.quality_score:.1f}%")
print(f"Acceptable: {report.is_acceptable}")
```

### Data Orchestrator (`src/data/data_orchestrator.py`)

Coordinates parallel collection from multiple sources:
- Priority-based task queuing
- Controlled concurrency (semaphore)
- Automatic retries per task
- Quality validation
- Comprehensive reporting

**Key Methods:**
- `collect_all_nfl_data(week)` - Collect all NFL sources
- `collect_all_ncaaf_data(week)` - Collect all NCAAF sources
- `collect_weather_for_games(games)` - Collect weather data

**CollectionReport includes:**
- Duration and timing
- Success/failure counts
- Task-level details
- Quality reports

### Health Monitor (`src/data/health_monitor.py`)

Real-time health tracking and alerting:
- Success rate tracking
- Consecutive failure detection
- Alert generation
- Status dashboard
- Alert callbacks

**Health Status Levels:**
- `HEALTHY`: >95% success rate
- `DEGRADED`: 80-95% success rate
- `UNHEALTHY`: 50-80% success rate
- `CRITICAL`: <50% success rate
- `UNKNOWN`: Insufficient data

**Alert Levels:**
- `INFO` - Informational
- `WARNING` - Degraded performance
- `ERROR` - Unhealthy status
- `CRITICAL` - Critical failures

## Usage Examples

### Complete NFL Data Collection Pipeline

```python
import asyncio
from datetime import datetime
from pathlib import Path

from src.data.data_orchestrator import DataOrchestrator
from src.data.health_monitor import HealthMonitor

async def nfl_collection_pipeline(week: int):
    """Complete NFL data collection with monitoring."""

    # Initialize health monitor
    monitor = HealthMonitor(
        history_size=100,
        alert_threshold_failures=3,
        alert_file=Path("data/health_alerts.jsonl"),
    )

    # Register alert handler
    def handle_alert(alert):
        print(f"🚨 [{alert.level.value.upper()}] {alert.message}")

    monitor.register_alert_callback(handle_alert)

    # Initialize orchestrator
    orchestrator = DataOrchestrator(
        max_concurrent_tasks=5,
        enable_retries=True,
        enable_validation=True,
    )

    # Collect all NFL data
    print(f"Collecting NFL data for week {week}...")
    report = await orchestrator.collect_all_nfl_data(week=week)

    # Record health checks
    for task in report.tasks:
        from src.data.health_monitor import HealthCheck

        check = HealthCheck(
            source=task.source.value,
            timestamp=task.start_time or datetime.now(),
            success=task.status.value == "completed",
            duration_ms=(
                (task.end_time - task.start_time).total_seconds() * 1000
                if task.end_time and task.start_time
                else 0
            ),
            error=task.error,
        )
        monitor.record_check(check)

    # Print results
    print(f"\nCollection Report:")
    print(f"  Duration: {report.duration_seconds:.1f}s")
    print(f"  Success Rate: {report.success_rate:.1f}%")
    print(f"  Successful: {report.successful_sources}")
    print(f"  Failed: {report.failed_sources}")
    print(f"  Degraded: {report.degraded_sources}")

    # Print health dashboard
    monitor.print_status_dashboard()

    # Generate health report
    health_report = monitor.generate_health_report()

    # Save report
    import json
    report_file = Path(f"data/reports/nfl_week{week}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w") as f:
        json.dump(health_report, f, indent=2)

    print(f"\nHealth report saved to: {report_file}")

    return report, health_report

# Run pipeline
asyncio.run(nfl_collection_pipeline(week=10))
```

### Custom Data Collection Task

```python
from src.data.data_orchestrator import CollectionTask, DataSource, CollectionStatus
from src.data.espn_client import ESPNClient

async def custom_collection():
    """Create custom collection tasks."""

    tasks = []

    # Add custom ESPN task
    async def collect_top_25_stats():
        async with ESPNClient() as client:
            teams = await client.get_teams("NCAAF")
            # Filter to top 25 (custom logic)
            top_25 = teams[:25]

            stats = []
            for team in top_25:
                team_stats = await client.get_team_stats("NCAAF", team["id"])
                stats.append(team_stats)

            return stats

    task = CollectionTask(
        source=DataSource.ESPN,
        description="Top 25 NCAAF team statistics",
        function=collect_top_25_stats,
        priority=1,
        timeout=300.0,  # 5 minutes
    )

    tasks.append(task)

    # Execute custom tasks
    # (integrate with orchestrator or run directly)
    result = await task.function()
    print(f"Collected {len(result)} team stats")

asyncio.run(custom_collection())
```

## Configuration

### Environment Variables

```bash
# ESPN (no auth required - public API)
# No configuration needed

# Action Network (required for odds scraping)
ACTION_USERNAME=your_username
ACTION_PASSWORD=your_password

# Overtime API (required for game data)
OV_CUSTOMER_ID=your_customer_id
OV_PASSWORD=your_password

# Weather APIs (at least one required)
ACCUWEATHER_API_KEY=your_accuweather_key
OPENWEATHER_API_KEY=your_openweather_key

# Optional: Proxy for scraping
PROXY_URL=http://user:pass@proxy:port
PROXY_USER=proxy_username
PROXY_PASS=proxy_password
```

### Client Configuration

```python
# ESPN Client
client = ESPNClient(
    rate_limit_delay=0.5,  # Seconds between requests
    timeout=30.0,           # Request timeout
    max_retries=3,          # Retry attempts
)

# Data Orchestrator
orchestrator = DataOrchestrator(
    max_concurrent_tasks=5,      # Parallel tasks
    enable_retries=True,          # Auto-retry on failure
    enable_validation=True,       # Quality validation
)

# Health Monitor
monitor = HealthMonitor(
    history_size=100,                     # Checks to retain
    alert_threshold_failures=3,           # Failures before alert
    alert_file=Path("alerts.jsonl"),     # Alert log file
)
```

## Monitoring & Troubleshooting

### Health Dashboard

```python
from src.data.health_monitor import HealthMonitor

monitor = HealthMonitor()

# ... record health checks ...

# Print status dashboard
monitor.print_status_dashboard()
```

**Output:**
```
======================================================================
HEALTH MONITORING DASHBOARD
======================================================================
System Health: ✓ HEALTHY

Source                         Status       Success Rate    Checks
----------------------------------------------------------------------
espn                           ✓ healthy    98.5%           67/68
action_network                 ⚠ degraded   87.2%           41/47
overtime                       ✓ healthy    96.3%           52/54
weather                        ✓ healthy    100.0%          23/23

Recent Alerts:
----------------------------------------------------------------------
[14:23:15] WARNING: action_network - action_network is DEGRADED (87.2% success rate)
======================================================================
```

### Common Issues

#### 1. Circuit Breaker Open

**Symptom:** `RuntimeError: Circuit breaker is open`

**Cause:** Too many consecutive failures (5+)

**Solution:**
```python
# Circuit breaker resets automatically after 5 minutes
# Or manually reset:
client._circuit_breaker_failures = 0
client._circuit_breaker_reset_time = None
```

#### 2. Rate Limit Errors

**Symptom:** HTTP 429 errors

**Solution:**
```python
# Increase rate limit delay
client = ESPNClient(rate_limit_delay=2.0)  # 2 seconds

# Reduce concurrent tasks
orchestrator = DataOrchestrator(max_concurrent_tasks=2)
```

#### 3. Timeout Errors

**Symptom:** `asyncio.TimeoutError`

**Solution:**
```python
# Increase timeout
client = ESPNClient(timeout=60.0)  # 60 seconds

# Increase task timeout
task = CollectionTask(
    ...
    timeout=300.0,  # 5 minutes
)
```

#### 4. Low Quality Data

**Symptom:** Data validation failures

**Solution:**
```python
# Check quality report
validator = ESPNDataValidator()
validated, report = validator.validate_teams(data)

print(f"Quality Score: {report.quality_score:.1f}%")
print(f"Completeness: {report.completeness_score:.1f}%")
print("Errors:", report.validation_errors)

# Adjust quality thresholds
# Acceptable if >80% validation rate
if not report.is_acceptable:
    print("Data quality below threshold!")
```

### Logs

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Best Practices

### 1. Always Use Context Managers

```python
# ✅ Good - automatic cleanup
async with ESPNClient() as client:
    teams = await client.get_teams("NFL")

# ❌ Bad - manual cleanup required
client = ESPNClient()
await client.connect()
teams = await client.get_teams("NFL")
await client.close()  # Easy to forget!
```

### 2. Handle Errors Gracefully

```python
from src.data.espn_client import ESPNClient

async def safe_collection():
    try:
        async with ESPNClient() as client:
            teams = await client.get_teams("NFL")
            return teams
    except RuntimeError as e:
        logger.error(f"Collection failed: {e}")
        # Implement fallback or alert
        return []
    except Exception as e:
        logger.exception("Unexpected error")
        return []
```

### 3. Monitor Health Continuously

```python
# Set up continuous monitoring
monitor = HealthMonitor()

async def collect_with_monitoring():
    async with ESPNClient() as client:
        start = datetime.now()

        try:
            teams = await client.get_teams("NFL")
            duration = (datetime.now() - start).total_seconds() * 1000

            check = HealthCheck(
                source="espn",
                timestamp=start,
                success=True,
                duration_ms=duration,
            )
        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000

            check = HealthCheck(
                source="espn",
                timestamp=start,
                success=False,
                duration_ms=duration,
                error=str(e),
            )

        monitor.record_check(check)
```

### 4. Validate All Data

```python
from src.data.validated_espn import ESPNDataValidator

async def validated_collection():
    async with ESPNClient() as client:
        teams = await client.get_teams("NFL")

        # Always validate
        validator = ESPNDataValidator()
        validated, report = validator.validate_teams(teams)

        if not report.is_acceptable:
            logger.warning(f"Low quality data: {report.validation_rate:.1f}%")
            # Handle low quality data

        return validated
```

### 5. Use Orchestrator for Multiple Sources

```python
# ✅ Good - parallel collection with monitoring
orchestrator = DataOrchestrator()
report = await orchestrator.collect_all_nfl_data(week=10)

# ❌ Bad - sequential collection
async with ESPNClient() as espn:
    espn_data = await espn.get_teams("NFL")

async with ActionNetworkClient() as action:
    odds_data = await action.fetch_nfl_odds()

# Much slower!
```

### 6. Set Appropriate Timeouts

```python
# Short timeout for simple requests
client = ESPNClient(timeout=30.0)

# Long timeout for complex requests
task = CollectionTask(
    ...
    timeout=300.0,  # 5 minutes for team stats collection
)
```

### 7. Implement Graceful Degradation

```python
async def collect_with_fallback():
    """Collect data with fallback sources."""

    # Try primary source
    try:
        async with ESPNClient() as client:
            return await client.get_teams("NFL")
    except Exception as e:
        logger.warning(f"ESPN failed: {e}, trying fallback...")

        # Try fallback source
        try:
            async with OvertimeAPIClient() as client:
                return await client.fetch_nfl_games()
        except Exception as e2:
            logger.error(f"All sources failed: {e2}")
            return []
```

## Testing

Run integration tests:

```bash
# Run all data collection tests
uv run pytest tests/test_data_collection.py -v

# Run specific test
uv run pytest tests/test_data_collection.py::TestESPNClient::test_get_nfl_teams -v

# Run with coverage
uv run pytest tests/test_data_collection.py --cov=src/data --cov-report=html
```

## Additional Resources

- [Billy Walters Methodology](BILLY_WALTERS_METHODOLOGY.md)
- [Proxy Setup Guide](PROXY_SETUP.md)
- [Chrome DevTools Scraping](../reports/CHROME_DEVTOOLS_BREAKTHROUGH.md)
- [Data Quality Review](../reports/DATA_QUALITY_REVIEW.md)

---

**Last Updated:** January 2025
**Maintainer:** Billy Walters Sports Analyzer Team
