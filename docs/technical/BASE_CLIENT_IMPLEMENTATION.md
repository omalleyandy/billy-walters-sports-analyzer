# BaseHTTPClient Implementation Guide

**Purpose**: Create a reusable base class for all HTTP-based data clients
**Scope**: Consolidate retry logic, rate limiting, and circuit breaker patterns
**Target Clients**: ESPNClient, OvertimeApiClient, WeatherClient, AccuWeatherClient

---

## Design Goals

1. **DRY**: Eliminate duplicate retry/rate limit/circuit breaker code
2. **Consistency**: All clients follow same error handling patterns
3. **Testability**: Mock circuit breaker and rate limiting easily
4. **Observability**: Centralized metrics for request success/failure
5. **Flexibility**: Easy to override behavior in subclasses

---

## Architecture

```
BaseHTTPClient
├── Retry Logic (via tenacity decorator)
├── Rate Limiting (per-client and global)
├── Circuit Breaker (5 failures = 5 min timeout)
├── Request Tracking (for metrics)
└── Error Handling (consistent across clients)

ESPNClient(BaseHTTPClient)
├── ESPN-specific URL patterns
├── ESPN-specific data enrichment
└── Inherits retry/rate limit/circuit breaker

OvertimeApiClient(BaseHTTPClient)
├── Overtime API endpoint
├── Request/response format
└── Inherits shared reliability patterns

WeatherClient(BaseHTTPClient)
├── Multi-provider support
├── Location-based requests
└── Shared error handling
```

---

## Implementation Plan

### Step 1: Create BaseHTTPClient

```python
# src/data/base_client.py

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Literal

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """Track circuit breaker state."""

    failures: int = 0
    last_failure_time: Optional[datetime] = None
    is_open: bool = False
    opened_at: Optional[datetime] = None

    def record_failure(self, threshold: int = 5, reset_time_seconds: int = 300):
        """Record a failure and potentially open the breaker."""
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.failures >= threshold:
            self.is_open = True
            self.opened_at = datetime.now()
            logger.error(
                f"Circuit breaker opened after {self.failures} failures. "
                f"Will reset at {datetime.now() + timedelta(seconds=reset_time_seconds)}"
            )

    def record_success(self):
        """Record a successful request and decay failures."""
        if self.failures > 0:
            self.failures = max(0, self.failures - 1)

    def check_reset(self, reset_time_seconds: int = 300) -> bool:
        """Check if circuit breaker should reset."""
        if not self.is_open:
            return True

        if self.opened_at is None:
            return True

        elapsed = (datetime.now() - self.opened_at).total_seconds()
        if elapsed > reset_time_seconds:
            logger.info("Circuit breaker reset")
            self.is_open = False
            self.failures = 0
            self.opened_at = None
            return True

        return False


class BaseHTTPClient:
    """
    Base class for all HTTP-based data clients.

    Provides:
    - Automatic retry with exponential backoff
    - Rate limiting (per-client)
    - Circuit breaker pattern
    - Unified error handling
    - Request logging and metrics
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_reset_seconds: int = 300,
    ):
        """
        Initialize base HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            rate_limit_delay: Minimum seconds between requests
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_reset_seconds: Seconds to wait before resetting
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_reset_seconds = circuit_breaker_reset_seconds

        # Initialize state
        self.last_request_time: float = 0.0
        self._circuit_breaker = CircuitBreakerState()
        self._client: httpx.AsyncClient | None = None

        # Metrics
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.retry_count = 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP client."""
        logger.info("Initializing HTTP client")
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                ),
            },
        )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.info("HTTP client closed")

    def _check_circuit_breaker(self) -> None:
        """Check if circuit breaker is open."""
        if not self._circuit_breaker.check_reset(self.circuit_breaker_reset_seconds):
            raise RuntimeError(
                f"Circuit breaker is open. Too many failures. "
                f"Will reset at {datetime.now() + timedelta(seconds=self.circuit_breaker_reset_seconds)}"
            )

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = asyncio.get_event_loop().time()

    @retry(
        retry=retry_if_exception_type(
            (httpx.RequestError, httpx.HTTPStatusError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _make_request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request with automatic retry and circuit breaker.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            params: Query parameters
            json: JSON body
            headers: Additional headers

        Returns:
            Response JSON data

        Raises:
            RuntimeError: If circuit breaker is open or request fails
            ValueError: If response is not JSON
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Call connect() first.")

        # Check circuit breaker
        self._check_circuit_breaker()

        # Rate limit
        await self._rate_limit()

        # Make request
        self.request_count += 1
        try:
            logger.debug(f"{method} {url}")

            response = await self._client.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
            )
            response.raise_for_status()

            # Record success
            self._circuit_breaker.record_success()
            self.success_count += 1

            # Return JSON response
            try:
                return response.json()
            except ValueError as e:
                raise ValueError(f"Response is not valid JSON: {e}") from e

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code}: {url}")
            self._circuit_breaker.record_failure(
                threshold=self.circuit_breaker_threshold,
                reset_time_seconds=self.circuit_breaker_reset_seconds,
            )
            self.failure_count += 1

            # Don't retry 4xx errors (client errors)
            if 400 <= e.response.status_code < 500:
                raise RuntimeError(
                    f"Client error {e.response.status_code}: {e.response.text}"
                ) from e

            # Retry 5xx errors (server errors)
            raise

        except httpx.RequestError as e:
            logger.warning(f"Request error for {url}: {e}")
            self._circuit_breaker.record_failure(
                threshold=self.circuit_breaker_threshold,
                reset_time_seconds=self.circuit_breaker_reset_seconds,
            )
            self.failure_count += 1
            raise

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Convenience method for GET requests."""
        return await self._make_request("GET", url, params=params, headers=headers)

    async def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Convenience method for POST requests."""
        return await self._make_request(
            "POST", url, params=params, json=json, headers=headers
        )

    def get_metrics(self) -> dict[str, Any]:
        """Get request metrics."""
        return {
            "total_requests": self.request_count,
            "successful": self.success_count,
            "failed": self.failure_count,
            "success_rate": (
                self.success_count / self.request_count
                if self.request_count > 0
                else 0
            ),
            "circuit_breaker_failures": self._circuit_breaker.failures,
            "circuit_breaker_open": self._circuit_breaker.is_open,
        }
```

---

### Step 2: Update ESPNClient to Inherit from BaseHTTPClient

**Changes**:
- Remove `__init__` parameters for retry/rate limit (inherit from base)
- Remove `_check_circuit_breaker()`, `_record_failure()`, `_record_success()` (inherit)
- Remove `_rate_limit()` (inherit)
- Remove `@retry` decorator (inherit behavior)
- Update `_make_request()` to call `super()._make_request()`
- Keep ESPN-specific logic

```python
# src/data/espn_client.py

from .base_client import BaseHTTPClient

class ESPNClient(BaseHTTPClient):
    """ESPN API client (inherits retry, rate limit, circuit breaker from base)."""

    NFL_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    NCAAF_BASE_URL = (
        "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
    )

    def __init__(
        self,
        rate_limit_delay: float = 0.5,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize ESPN client."""
        super().__init__(
            timeout=timeout,
            max_retries=max_retries,
            rate_limit_delay=rate_limit_delay,
        )

    async def get_scoreboard(
        self,
        league: Literal["NFL", "NCAAF"],
        week: int | None = None,
        season: int | None = None,
    ) -> dict[str, Any]:
        """Get scoreboard with games for a specific week."""
        base_url = self.NFL_BASE_URL if league == "NFL" else self.NCAAF_BASE_URL
        url = f"{base_url}/scoreboard"

        params = {}
        if week is not None:
            params["week"] = week
        if season is not None:
            params["seasonYear"] = season

        logger.info(
            f"Fetching {league} scoreboard"
            + (f" week {week}" if week else "")
            + (f" season {season}" if season else "")
        )

        # Use inherited _make_request (replaces @retry decorator)
        data = await self.get(url, params=params)
        return self._enrich_scoreboard(data, league)

    # ... rest of methods unchanged ...
```

**Removed Code** (~50 lines):
- `_check_circuit_breaker()` - inherited
- `_record_failure()` - inherited
- `_record_success()` - inherited
- `_rate_limit()` - inherited
- `@retry` decorator setup - inherited
- Circuit breaker state management - inherited

---

### Step 3: Update OvertimeApiClient

```python
# src/data/overtime_api_client.py

from .base_client import BaseHTTPClient

class OvertimeApiClient(BaseHTTPClient):
    """Overtime API client."""

    BASE_URL = "https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering"

    def __init__(self, output_dir: str | Path = "output/overtime"):
        """Initialize with rate limiting for Overtime."""
        super().__init__(
            timeout=30.0,
            max_retries=3,
            rate_limit_delay=1.0,  # Overtime-specific rate limit
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_games(
        self,
        sport_type: str = "Football",
        sport_sub_type: str = "NFL",
        wager_type: str = "Straight Bet",
        period_number: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch games from Overtime API."""
        payload = {
            "sportType": sport_type,
            "sportSubType": sport_sub_type,
            "wagerType": wager_type,
            "hoursAdjustment": 0,
            "periodNumber": period_number,
            "gameNum": None,
            "parentGameNum": None,
            "teaserName": "",
            "requestMode": "G",
        }

        # Use inherited post method
        data = await self.post(self.BASE_URL, json=payload)

        if "d" in data and "Data" in data["d"] and "GameLines" in data["d"]["Data"]:
            return data["d"]["Data"]["GameLines"]

        return []
```

---

### Step 4: Consolidate Weather Clients

```python
# src/data/weather_client.py

from .base_client import BaseHTTPClient
from .accuweather_client import AccuWeatherClient
from .openweather_client import OpenWeatherClient

class WeatherClient(BaseHTTPClient):
    """Unified weather client with multi-provider support."""

    def __init__(
        self,
        provider: Literal["accuweather", "openweather"] = "accuweather",
        api_key: str | None = None,
    ):
        """Initialize with selected provider."""
        super().__init__(timeout=30.0, rate_limit_delay=0.5)

        self.provider = provider
        if provider == "accuweather":
            self._provider = AccuWeatherClient(api_key=api_key)
        elif provider == "openweather":
            self._provider = OpenWeatherClient(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def connect(self) -> None:
        """Initialize base and provider."""
        await super().connect()
        await self._provider.connect()

    async def close(self) -> None:
        """Close base and provider."""
        await super().close()
        await self._provider.close()

    async def get_forecast(
        self,
        location: str,
        stadium_name: str | None = None,
    ) -> dict[str, Any]:
        """Get weather forecast for location."""
        return await self._provider.get_forecast(location, stadium_name)

    async def get_stadium_weather(self, stadium_name: str) -> dict[str, Any]:
        """Get weather for NFL stadium."""
        return await self._provider.get_stadium_weather(stadium_name)
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_base_client.py

import pytest
from unittest.mock import AsyncMock, patch
from src.data.base_client import BaseHTTPClient, CircuitBreakerState


class TestCircuitBreakerState:
    """Test circuit breaker state machine."""

    def test_circuit_breaker_opens_after_threshold(self):
        """Circuit breaker opens after 5 failures."""
        breaker = CircuitBreakerState()

        for i in range(5):
            breaker.record_failure(threshold=5)
            if i < 4:
                assert not breaker.is_open
            else:
                assert breaker.is_open

    def test_circuit_breaker_resets(self):
        """Circuit breaker resets after timeout."""
        breaker = CircuitBreakerState()
        breaker.failures = 5
        breaker.is_open = True
        breaker.opened_at = datetime.now() - timedelta(seconds=301)

        assert breaker.check_reset(reset_time_seconds=300)
        assert not breaker.is_open
        assert breaker.failures == 0


class TestBaseHTTPClient:
    """Test base HTTP client."""

    @pytest.fixture
    async def client(self):
        """Provide base client."""
        async with BaseHTTPClient() as client:
            yield client

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Rate limiting enforces minimum delay."""
        start = asyncio.get_event_loop().time()
        client.last_request_time = start - 0.1  # 0.1s ago
        client.rate_limit_delay = 0.5

        await client._rate_limit()

        end = asyncio.get_event_loop().time()
        assert end - start >= 0.4  # ~0.4s wait

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, client):
        """Circuit breaker opens after threshold failures."""
        for _ in range(5):
            client._circuit_breaker.record_failure(threshold=5)

        with pytest.raises(RuntimeError, match="Circuit breaker is open"):
            client._check_circuit_breaker()

    @pytest.mark.asyncio
    async def test_get_metrics(self, client):
        """Metrics are tracked correctly."""
        client.request_count = 100
        client.success_count = 95
        client.failure_count = 5

        metrics = client.get_metrics()
        assert metrics["total_requests"] == 100
        assert metrics["success_rate"] == 0.95
```

### Integration Tests

```python
# tests/test_espn_client_consolidated.py

@pytest.mark.asyncio
async def test_espn_client_inherits_base_functionality():
    """ESPNClient correctly inherits retry/rate limit/circuit breaker."""
    async with ESPNClient() as client:
        # Verify metrics tracking
        metrics = client.get_metrics()
        assert "success_rate" in metrics
        assert "circuit_breaker_open" in metrics

        # Verify rate limiting is inherited
        assert client.rate_limit_delay == 0.5

        # Verify circuit breaker is inherited
        assert client._circuit_breaker is not None
```

---

## Migration Checklist

- [ ] Create `src/data/base_client.py` with BaseHTTPClient
- [ ] Update `src/data/espn_client.py` to inherit from BaseHTTPClient
- [ ] Update `src/data/overtime_api_client.py` to inherit
- [ ] Consolidate `weather_client.py`, `accuweather_client.py`, `openweather_client.py`
- [ ] Write unit tests for BaseHTTPClient
- [ ] Write integration tests for updated clients
- [ ] Run full test suite (pytest)
- [ ] Verify backwards compatibility (all scrapers still work)
- [ ] Update documentation
- [ ] Create commit with all changes

---

## Expected Outcomes

### Code Reduction
- **ESPNClient**: -50 LOC (remove retry/rate limit/circuit breaker)
- **OvertimeApiClient**: -30 LOC
- **WeatherClient(s)**: -100 LOC (consolidate 3 clients to 1)
- **BaseHTTPClient**: +200 LOC (shared logic)
- **Net**: -80 LOC, more maintainable

### Consistency
- All HTTP clients use identical retry/rate limit patterns
- All HTTP clients have circuit breaker protection
- All HTTP clients expose same metrics interface
- All HTTP clients have consistent error handling

### Observability
- Central place to monitor all HTTP clients
- Metrics available on all clients (`get_metrics()`)
- Consistent logging across all requests
- Circuit breaker state visible to callers

---

## References

- **Base**: `src/data/espn_client.py` (retry/rate limit logic)
- **Target**: `src/data/overtime_api_client.py` (simplest client to inherit)
- **Complex**: `src/data/nfl_game_stats_client.py` (will benefit from base later)

---

**Status**: Ready for implementation
**Effort**: 8-10 hours total
**Priority**: High (foundation for other consolidations)
