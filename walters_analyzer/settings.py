"""
Environment bootstrap for the Billy Walters Sports Analyzer.

Loads values from a `.env` file (if present) via python-dotenv and provides
typed accessors with sensible defaults. Required keys are validated eagerly so
startup fails fast with an actionable error message.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional, TypeVar

from dotenv import load_dotenv

T = TypeVar("T")

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH, override=False)


class SettingsError(ValueError):
    """Raised when required configuration is missing or invalid."""


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_value(
    key: str,
    *,
    required: bool = False,
    default: Optional[T] = None,
    cast: Optional[Callable[[str], T]] = None,
    validator: Optional[Callable[[T], None]] = None,
) -> T | None:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        if required and default is None:
            raise SettingsError(
                f"Environment variable {key!r} is required. "
                "Set it in your .env file or OS environment."
            )
        value = default
    else:
        raw = raw.strip()
        if cast:
            try:
                value = cast(raw)
            except (TypeError, ValueError) as exc:
                raise SettingsError(f"Invalid value for {key!r}: {exc}") from exc
        else:
            value = raw  # type: ignore[assignment]

    if validator and value is not None:
        try:
            validator(value)  # type: ignore[arg-type]
        except ValueError as exc:
            raise SettingsError(f"Invalid value for {key!r}: {exc}") from exc

    return value


def _validate_positive(value: float) -> None:
    if value <= 0:
        raise ValueError("value must be greater than zero")


def _validate_fraction(value: float) -> None:
    if not 0 < value <= 1:
        raise ValueError("value must be between 0 and 1 (exclusive of 0)")


@dataclass(frozen=True)
class Settings:
    """Strongly-typed application configuration."""

    ov_customer_id: str
    ov_customer_password: str
    accuweather_api_key: str

    openweather_api_key: Optional[str]
    news_api_key: Optional[str]
    profootballdoc_api_key: Optional[str]
    highlightly_api_key: Optional[str]

    bankroll: float
    kelly_fraction: float
    max_bet_percentage: float
    minimum_edge_percentage: float

    cache_ttl_weather: int
    cache_ttl_injury: int
    cache_ttl_analysis: int
    cache_ttl_odds: int

    http_max_connections: int
    http_max_per_host: int
    http_timeout: int

    enable_web_fetch: bool
    enable_caching: bool
    enable_research: bool
    enable_profootballdoc: bool
    enable_news_api: bool

    proxy_url: Optional[str]
    overtime_proxy: Optional[str]

    @property
    def overtime_credentials(self) -> tuple[str, str]:
        """Handy tuple of Overtime.ag credentials."""
        return self.ov_customer_id, self.ov_customer_password


def _load_settings() -> Settings:
    return Settings(
        ov_customer_id=_get_value("OV_CUSTOMER_ID", required=True, cast=str),
        ov_customer_password=_get_value("OV_CUSTOMER_PASSWORD", required=True, cast=str),
        accuweather_api_key=_get_value("ACCUWEATHER_API_KEY", required=True, cast=str),
        openweather_api_key=_get_value("OPENWEATHER_API_KEY"),
        news_api_key=_get_value("NEWS_API_KEY"),
        profootballdoc_api_key=_get_value("PROFOOTBALLDOC_API_KEY"),
        highlightly_api_key=_get_value("HIGHLIGHTLY_API_KEY"),
        bankroll=_get_value(
            "BANKROLL",
            default=10000.0,
            cast=float,
            validator=_validate_positive,
        ),
        kelly_fraction=_get_value(
            "KELLY_FRACTION",
            default=0.25,
            cast=float,
            validator=_validate_fraction,
        ),
        max_bet_percentage=_get_value(
            "MAX_BET_PERCENTAGE",
            default=0.03,
            cast=float,
            validator=_validate_fraction,
        ),
        minimum_edge_percentage=_get_value(
            "MINIMUM_EDGE_PERCENTAGE",
            default=5.5,
            cast=float,
            validator=_validate_positive,
        ),
        cache_ttl_weather=_get_value(
            "CACHE_TTL_WEATHER",
            default=1800,
            cast=int,
            validator=_validate_positive,
        ),
        cache_ttl_injury=_get_value(
            "CACHE_TTL_INJURY",
            default=900,
            cast=int,
            validator=_validate_positive,
        ),
        cache_ttl_analysis=_get_value(
            "CACHE_TTL_ANALYSIS",
            default=300,
            cast=int,
            validator=_validate_positive,
        ),
        cache_ttl_odds=_get_value(
            "CACHE_TTL_ODDS",
            default=60,
            cast=int,
            validator=_validate_positive,
        ),
        http_max_connections=_get_value(
            "HTTP_MAX_CONNECTIONS",
            default=100,
            cast=int,
            validator=_validate_positive,
        ),
        http_max_per_host=_get_value(
            "HTTP_MAX_PER_HOST",
            default=30,
            cast=int,
            validator=_validate_positive,
        ),
        http_timeout=_get_value(
            "HTTP_TIMEOUT",
            default=30,
            cast=int,
            validator=_validate_positive,
        ),
        enable_web_fetch=_get_value(
            "ENABLE_WEB_FETCH",
            default=True,
            cast=_to_bool,
        ),
        enable_caching=_get_value(
            "ENABLE_CACHING",
            default=True,
            cast=_to_bool,
        ),
        enable_research=_get_value(
            "ENABLE_RESEARCH",
            default=True,
            cast=_to_bool,
        ),
        enable_profootballdoc=_get_value(
            "ENABLE_PROFOOTBALLDOC",
            default=False,
            cast=_to_bool,
        ),
        enable_news_api=_get_value(
            "ENABLE_NEWS_API",
            default=False,
            cast=_to_bool,
        ),
        proxy_url=_get_value("PROXY_URL"),
        overtime_proxy=_get_value("OVERTIME_PROXY"),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return memoised settings for the current process.

    Use ``reload_settings`` in tests or scripts that intentionally mutate
    ``os.environ`` after import.
    """

    return _load_settings()


def reload_settings() -> Settings:
    """Clear the cached Settings instance and return a freshly loaded copy."""

    get_settings.cache_clear()  # type: ignore[attr-defined]
    return get_settings()


__all__ = ["Settings", "SettingsError", "get_settings", "reload_settings"]
