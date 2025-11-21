"""
Robox-based HTTP client for Billy Walters SDK.

Centralizes:
- Construction of AsyncRobox with standard headers, timeouts, retries.
- Logging and error classification.
- Simple helper API so edge models can say "give me this URL" without
  caring about how HTTP is done under the hood.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Union, TYPE_CHECKING

import httpx

# Runtime check for robox availability
try:
    from robox import AsyncRobox, Options  # type: ignore[import]

    ROBOX_AVAILABLE = True
except ImportError:
    ROBOX_AVAILABLE = False
    # No need to define placeholders - we'll use string annotations

from ..config import config, Config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------


class ErrorCategory(str, Enum):
    TIMEOUT = "timeout"
    NETWORK = "network"
    HTTP_4XX = "http_4xx"
    HTTP_5XX = "http_5xx"
    OTHER = "other"


@dataclass
class NetError:
    category: ErrorCategory
    message: str
    status_code: Optional[int] = None
    url: Optional[str] = None
    service: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class NetResponse:
    url: str
    status_code: int
    headers: Mapping[str, str]
    data: Any
    raw: Any
    service: str


class NetClientError(RuntimeError):
    """Raised when a network call fails in a classified way."""

    def __init__(self, error: NetError):
        self.error = error
        super().__init__(
            f"[{error.category}] {error.message} (status={error.status_code})"
        )


# ---------------------------------------------------------------------------
# Simple circuit breaker (per-process, per-client)
# ---------------------------------------------------------------------------


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout_seconds: int = 30,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds

        self._failure_count = 0
        self._opened_at: Optional[float] = None
        self._lock = asyncio.Lock()

    async def before_call(self) -> None:
        async with self._lock:
            if self._opened_at is None:
                return

            loop = asyncio.get_running_loop()
            elapsed = loop.time() - self._opened_at

            if elapsed >= self.reset_timeout_seconds:
                # Half-open: allow a call and reset on success/failure.
                self._failure_count = 0
                self._opened_at = None
            else:
                raise NetClientError(
                    NetError(
                        category=ErrorCategory.OTHER,
                        message="Circuit breaker is open; skipping external HTTP call",
                    )
                )

    async def record_success(self) -> None:
        async with self._lock:
            self._failure_count = 0
            self._opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                loop = asyncio.get_running_loop()
                self._opened_at = loop.time()
                logger.warning(
                    "Circuit breaker opened after %d consecutive failures",
                    self._failure_count,
                )


# ---------------------------------------------------------------------------
# Core Robox wrapper
# ---------------------------------------------------------------------------


class RoboxClient:
    """
    Thin wrapper around AsyncRobox.

    Responsibilities:
    - Build AsyncRobox with our standard config (UA, timeout, retries).
    - Provide a small, typed API used by the rest of the project.
    - Centralize logging + error classification.
    """

    def __init__(self, cfg: Optional[Config] = None) -> None:
        if not ROBOX_AVAILABLE:
            raise ImportError(
                "robox package is not available. "
                "This module is a placeholder for future implementation. "
                "Uncomment 'robox' in pyproject.toml and install to use."
            )
        self._cfg: Config = cfg or config
        self._robox: Optional[Any] = None  # AsyncRobox when available
        self._lock = asyncio.Lock()
        self._circuit = CircuitBreaker()

    async def _ensure_client(self) -> Any:  # Returns AsyncRobox when available
        if self._robox is not None:
            return self._robox

        async with self._lock:
            if self._robox is not None:
                return self._robox

            # Robox Options -> retries + raising on 4xx/5xx so we can classify.
            options = Options(
                retry=True,
                retry_max_attempts=3,
                raise_on_4xx_5xx=True,
            )

            # Base client; per-request headers will still be passed explicitly.
            timeout = self._cfg.request_timeout_seconds

            self._robox = AsyncRobox(
                follow_redirects=True,
                timeout=timeout,
                options=options,
            )

            logger.info(
                "Initialized AsyncRobox client (timeout=%s, retries=%s)",
                timeout,
                3,
            )
            return self._robox

    # -------------------------------
    # Public API
    # -------------------------------

    async def get(
        self,
        url: str,
        *,
        service: str = "generic",
        params: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        expect_json: bool = True,
    ) -> NetResponse:
        """
        Fetch a URL via GET and return a structured NetResponse.

        - `service` is a logical name: "odds_api", "news_api", "openweather",
          "accuweather", "highlightly", etc. It feeds into Config.get_api_headers().
        - `expect_json` controls whether we try to JSON-decode the body.
        """
        await self._circuit.before_call()
        client = await self._ensure_client()

        full_url = self._build_url(url, params)

        headers = self._build_headers(service, extra_headers)

        try:
            logger.debug(
                "RoboxClient GET start",
                extra={"service": service, "url": full_url},
            )

            page = await client.open(full_url, headers=headers)

            # If raise_on_4xx_5xx=True, we only get here for 2xx/3xx.
            data: Any
            if expect_json:
                data = self._parse_json(page.text, full_url, service)
            else:
                data = page.text

            resp = NetResponse(
                url=str(page.url),
                status_code=page.status_code,
                headers=page.headers or {},
                data=data,
                raw=page,
                service=service,
            )

            await self._circuit.record_success()

            logger.info(
                "RoboxClient GET success",
                extra={
                    "service": service,
                    "url": str(page.url),
                    "status_code": page.status_code,
                },
            )
            return resp

        except httpx.TimeoutException as exc:
            error = self._classify_timeout(exc, full_url, service)
            await self._circuit.record_failure()
            self._log_error(error)
            raise NetClientError(error) from exc

        except httpx.HTTPStatusError as exc:
            error = self._classify_status_error(exc, full_url, service)
            await self._circuit.record_failure()
            self._log_error(error)
            raise NetClientError(error) from exc

        except httpx.TransportError as exc:
            error = self._classify_network_error(exc, full_url, service)
            await self._circuit.record_failure()
            self._log_error(error)
            raise NetClientError(error) from exc

        except Exception as exc:
            error = NetError(
                category=ErrorCategory.OTHER,
                message=str(exc),
                url=full_url,
                service=service,
            )
            await self._circuit.record_failure()
            self._log_error(error)
            raise NetClientError(error) from exc

    async def close(self) -> None:
        """Manually close the underlying AsyncRobox client."""
        if self._robox is not None:
            await self._robox.aclose()
            self._robox = None
            logger.info("AsyncRobox client closed")

    # -------------------------------
    # Internals
    # -------------------------------

    def _build_headers(
        self,
        service: str,
        extra_headers: Optional[Dict[str, str]],
    ) -> Dict[str, str]:
        """
        Use Config.get_api_headers(service) as the base, then overlay extras.

        This keeps:
        - UA centralized
        - API keys / auth / host headers centralized
        """
        base_headers = self._cfg.get_api_headers(service)
        headers: Dict[str, str] = dict(base_headers)

        if extra_headers:
            headers.update(extra_headers)

        return headers

    @staticmethod
    def _build_url(url: str, params: Optional[Dict[str, Any]]) -> str:
        """Basic query param injection, without relying on httpx params."""
        if not params:
            return url

        from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

        split = urlsplit(url)
        existing = dict(parse_qsl(split.query))
        existing.update({k: str(v) for k, v in params.items()})
        query = urlencode(existing, doseq=True)
        return urlunsplit(
            (split.scheme, split.netloc, split.path, query, split.fragment)
        )

    @staticmethod
    def _parse_json(body: str, url: str, service: str) -> Any:
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            error = NetError(
                category=ErrorCategory.OTHER,
                message=f"Failed to parse JSON response: {exc}",
                url=url,
                service=service,
            )
            logger.error(
                "RoboxClient JSON parse error",
                extra={
                    "service": service,
                    "url": url,
                    "error": str(exc),
                },
            )
            # Raise a NetClientError so callers don't happily use a bad payload.
            raise NetClientError(error) from exc

    @staticmethod
    def _classify_timeout(
        exc: httpx.TimeoutException,
        url: str,
        service: str,
    ) -> NetError:
        return NetError(
            category=ErrorCategory.TIMEOUT,
            message="Request timed out",
            url=url,
            service=service,
            details={"exc_type": type(exc).__name__},
        )

    @staticmethod
    def _classify_status_error(
        exc: httpx.HTTPStatusError,
        url: str,
        service: str,
    ) -> NetError:
        status = exc.response.status_code if exc.response is not None else None
        if status is not None and 400 <= status < 500:
            cat = ErrorCategory.HTTP_4XX
        else:
            cat = ErrorCategory.HTTP_5XX

        return NetError(
            category=cat,
            message=f"HTTP error {status}",
            status_code=status,
            url=url,
            service=service,
            details={
                "reason": exc.response.reason_phrase
                if exc.response is not None
                else None
            },
        )

    @staticmethod
    def _classify_network_error(
        exc: httpx.TransportError,
        url: str,
        service: str,
    ) -> NetError:
        return NetError(
            category=ErrorCategory.NETWORK,
            message="Network/transport error",
            url=url,
            service=service,
            details={"exc_type": type(exc).__name__},
        )

    @staticmethod
    def _log_error(error: NetError) -> None:
        logger.error(
            "RoboxClient request failed",
            extra={
                "category": error.category,
                "message": error.message,
                "status_code": error.status_code,
                "url": error.url,
                "service": error.service,
                "details": error.details,
            },
        )


# ---------------------------------------------------------------------------
# Module-level singleton + helpers
# ---------------------------------------------------------------------------

_client: Optional[RoboxClient] = None
_client_lock = asyncio.Lock()


async def get_robox_client() -> RoboxClient:
    """Get the process-wide RoboxClient instance."""
    global _client
    if _client is not None:
        return _client

    async with _client_lock:
        if _client is None:
            _client = RoboxClient()
    return _client


async def net_get_json(
    url: str,
    *,
    service: str = "generic",
    params: Optional[Dict[str, Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Any:
    """
    Convenience helper for the 90% case:

    - GET the URL
    - Expect JSON
    - Return the decoded payload directly

    Edge models and data loaders should generally call this, not RoboxClient
    directly. That keeps "how we talk to the internet" behind one small wall.
    """
    client = await get_robox_client()
    resp = await client.get(
        url,
        service=service,
        params=params,
        extra_headers=extra_headers,
        expect_json=True,
    )
    return resp.data
