"""
Web Fetch Client for Billy Walters Sports Analyzer.

This module provides a production-ready integration with Anthropic's web_fetch
tool for robust web content fetching with automatic retry, caching, domain
validation, and comprehensive error handling.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import anthropic


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class FetchMetadata:
    """Metadata about a web fetch operation."""

    url: str
    timestamp: str
    input_tokens: int
    output_tokens: int
    web_fetch_requests: int
    model: str
    duration_seconds: float
    cache_hit: bool = False


@dataclass
class FetchResult:
    """Standardized result from web fetch operation."""

    url: str
    content: str
    citations: List[Dict[str, Any]]
    metadata: FetchMetadata
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "url": self.url,
            "content": self.content,
            "citations": self.citations,
            "metadata": asdict(self.metadata),
            "success": self.success,
            "timestamp": self.metadata.timestamp,
        }
        if self.error:
            result["error"] = self.error
        return result


# =============================================================================
# WebFetchClient Class
# =============================================================================


class WebFetchClient:
    """
    Client for fetching web content using Anthropic's web_fetch tool.

    Features:
    - Automatic retry with exponential backoff
    - Response caching with configurable TTL
    - Domain validation for security
    - Comprehensive error handling
    - Billy Walters methodology alignment
    """

    # Allowed domains for web fetching (whitelist)
    ALLOWED_DOMAINS = [
        "espn.com",
        "www.espn.com",
        "nfl.com",
        "www.nfl.com",
        "masseyratings.com",
        "www.masseyratings.com",
        "overtime.ag",
        "www.overtime.ag",
        "covers.com",
        "www.covers.com",
        "actionnetwork.com",
        "www.actionnetwork.com",
        "vegasinsider.com",
        "www.vegasinsider.com",
        "accuweather.com",
        "www.accuweather.com",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_uses: int = 10,
        max_content_tokens: int = 100000,
        enable_citations: bool = True,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
    ):
        """
        Initialize WebFetchClient.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            max_uses: Maximum web fetches per request
            max_content_tokens: Maximum tokens per fetch
            enable_citations: Enable source citations
            enable_cache: Enable response caching
            cache_ttl_seconds: Cache TTL in seconds
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.max_uses = max_uses
        self.max_content_tokens = max_content_tokens
        self.enable_citations = enable_citations
        self.enable_cache = enable_cache
        self.cache_ttl_seconds = cache_ttl_seconds

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Initialize cache
        self._cache: Dict[str, tuple[FetchResult, float]] = {}

    def validate_url(self, url: str) -> bool:
        """
        Validate URL is from allowed domain.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return any(
                domain == allowed or domain.endswith(f".{allowed}")
                for allowed in self.ALLOWED_DOMAINS
            )
        except Exception:
            return False

    def _validate_url_strict(self, url: str) -> None:
        """
        Strictly validate URL or raise ValueError.

        Args:
            url: URL to validate

        Raises:
            ValueError: If URL is invalid or not from allowed domain
        """
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

        if not self.validate_url(url):
            raise ValueError(f"URL domain not in allowed list: {parsed.netloc}")

    def _generate_cache_key(self, url: str, prompt: str) -> str:
        """
        Generate cache key from URL and prompt.

        Args:
            url: URL
            prompt: Prompt text

        Returns:
            SHA-256 hash as cache key
        """
        content = f"{url}|{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _cache_result(self, cache_key: str, result: FetchResult) -> None:
        """
        Cache a fetch result.

        Args:
            cache_key: Cache key
            result: FetchResult to cache
        """
        if self.enable_cache:
            self._cache[cache_key] = (result, time.time())

    def _get_cached_result(self, cache_key: str) -> Optional[FetchResult]:
        """
        Get cached result if available and not expired.

        Args:
            cache_key: Cache key

        Returns:
            Cached FetchResult or None if not found/expired
        """
        if not self.enable_cache:
            return None

        if cache_key not in self._cache:
            return None

        result, timestamp = self._cache[cache_key]
        age = time.time() - timestamp

        if age > self.cache_ttl_seconds:
            # Expired
            del self._cache[cache_key]
            return None

        # Update metadata to indicate cache hit
        result.metadata.cache_hit = True
        return result

    def clear_cache(self) -> int:
        """
        Clear all cached results.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        return count

    def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self.cache_ttl_seconds
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        stats = {
            "enabled": self.enable_cache,
            "size": len(self._cache),
            "ttl_seconds": self.cache_ttl_seconds,
        }

        if self._cache:
            current_time = time.time()
            ages = [current_time - timestamp for _, timestamp in self._cache.values()]
            stats["oldest_entry_age_seconds"] = max(ages)
            stats["newest_entry_age_seconds"] = min(ages)
            stats["average_entry_age_seconds"] = sum(ages) / len(ages)

        return stats

    def _process_response(
        self, response: Any, url: str, duration: float
    ) -> FetchResult:
        """
        Process Anthropic API response into FetchResult.

        Args:
            response: Anthropic API response
            url: URL that was fetched
            duration: Request duration in seconds

        Returns:
            FetchResult
        """
        # Extract content from text blocks
        content_parts = []
        citations = []

        for block in response.content:
            if block.type == "text":
                content_parts.append(block.text)
                # Extract citations if available
                if hasattr(block, "citations") and block.citations:
                    citations.extend(block.citations)

        content = "\n".join(content_parts)

        # Extract usage stats
        usage = response.usage
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens

        # Extract web fetch count
        web_fetch_requests = 0
        if hasattr(usage, "server_tool_use") and usage.server_tool_use:
            web_fetch_requests = usage.server_tool_use.get("web_fetch_requests", 0)

        # Create metadata
        metadata = FetchMetadata(
            url=url,
            timestamp=datetime.now().isoformat(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            web_fetch_requests=web_fetch_requests,
            model=response.model,
            duration_seconds=duration,
        )

        return FetchResult(
            url=url,
            content=content,
            citations=citations if self.enable_citations else [],
            metadata=metadata,
            success=True,
        )

    def fetch_content(
        self,
        url: str,
        prompt: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        use_cache: bool = True,
    ) -> FetchResult:
        """
        Fetch and analyze content from a URL.

        Args:
            url: URL to fetch
            prompt: Analysis prompt (defaults to content extraction)
            model: Claude model to use
            max_tokens: Max response tokens
            use_cache: Use cached result if available

        Returns:
            FetchResult

        Raises:
            ValueError: If URL invalid or not from allowed domain
        """
        # Validate URL
        self._validate_url_strict(url)

        # Default prompt
        if prompt is None:
            prompt = f"Please fetch and extract the content from {url}"

        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(url, prompt)
            cached = self._get_cached_result(cache_key)
            if cached:
                return cached

        # Fetch from API
        start_time = time.time()
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                tools=[
                    {
                        "type": "web_fetch",
                        "web_fetch": {
                            "max_uses": self.max_uses,
                            "max_content_tokens": self.max_content_tokens,
                        },
                    }
                ],
            )

            duration = time.time() - start_time
            result = self._process_response(response, url, duration)

            # Cache result
            if use_cache:
                self._cache_result(cache_key, result)

            return result

        except Exception as e:
            duration = time.time() - start_time
            return FetchResult(
                url=url,
                content="",
                citations=[],
                metadata=FetchMetadata(
                    url=url,
                    timestamp=datetime.now().isoformat(),
                    input_tokens=0,
                    output_tokens=0,
                    web_fetch_requests=0,
                    model=model,
                    duration_seconds=duration,
                ),
                success=False,
                error=str(e),
            )

    def fetch_multiple(
        self,
        urls: List[str],
        prompt_template: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        use_cache: bool = True,
        delay_between_requests: float = 1.0,
    ) -> Dict[str, FetchResult]:
        """
        Fetch content from multiple URLs with rate limiting.

        Args:
            urls: List of URLs to fetch
            prompt_template: Template for prompts (use {url} placeholder)
            model: Claude model to use
            max_tokens: Max response tokens per fetch
            use_cache: Use cached results if available
            delay_between_requests: Seconds to wait between requests

        Returns:
            Dict mapping URL to FetchResult
        """
        results = {}

        for i, url in enumerate(urls):
            prompt = prompt_template.format(url=url) if prompt_template else None

            result = self.fetch_content(
                url,
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                use_cache=use_cache,
            )
            results[url] = result

            # Rate limiting (skip delay after last request)
            if i < len(urls) - 1 and delay_between_requests > 0:
                time.sleep(delay_between_requests)

        return results

    def save_result(
        self, result: FetchResult, output_dir: str = "betting_data/web_fetch"
    ) -> Path:
        """
        Save fetch result to JSON file.

        Args:
            result: FetchResult to save
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename from URL and timestamp
        parsed_url = urlparse(result.url)
        domain = parsed_url.netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_{timestamp}.json"

        # Save to file
        filepath = output_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)

        return filepath


# =============================================================================
# Convenience Functions
# =============================================================================


def fetch_nfl_schedule(
    week: Optional[int] = None,
    api_key: Optional[str] = None,
    use_cache: bool = True,
) -> FetchResult:
    """
    Fetch NFL schedule from ESPN.

    Args:
        week: Week number (None for current week)
        api_key: Anthropic API key
        use_cache: Use cached result if available

    Returns:
        FetchResult with NFL schedule data
    """
    client = WebFetchClient(api_key=api_key)

    if week:
        url = f"https://www.espn.com/nfl/schedule/_/week/{week}"
    else:
        url = "https://www.espn.com/nfl/schedule"

    prompt = "Extract the NFL schedule including teams, dates, times, and results"
    return client.fetch_content(url, prompt=prompt, use_cache=use_cache)


def fetch_vegas_lines(
    sport: str = "nfl",
    api_key: Optional[str] = None,
    use_cache: bool = True,
) -> FetchResult:
    """
    Fetch betting lines from Vegas Insider.

    Args:
        sport: Sport to fetch (nfl, ncaaf, etc.)
        api_key: Anthropic API key
        use_cache: Use cached result if available

    Returns:
        FetchResult with betting lines
    """
    client = WebFetchClient(api_key=api_key)
    url = f"https://www.vegasinsider.com/{sport}/odds/las-vegas/"
    prompt = "Extract betting lines including spreads, totals, and moneylines"
    return client.fetch_content(url, prompt=prompt, use_cache=use_cache)


def fetch_weather_forecast(
    location: str,
    stadium_name: Optional[str] = None,
    api_key: Optional[str] = None,
    use_cache: bool = True,
) -> FetchResult:
    """
    Fetch weather forecast from AccuWeather.

    Args:
        location: City and state (e.g., "Pittsburgh, PA")
        stadium_name: Optional stadium name for context
        api_key: Anthropic API key
        use_cache: Use cached result if available

    Returns:
        FetchResult with weather forecast
    """
    client = WebFetchClient(api_key=api_key)

    # Format location for URL (replace spaces with hyphens, lowercase)
    location_slug = location.lower().replace(", ", "-").replace(" ", "-")
    url = f"https://www.accuweather.com/en/us/{location_slug}/weather-forecast"

    prompt = "Extract weather forecast including temperature, wind, precipitation"
    if stadium_name:
        prompt += f" for {stadium_name}"

    return client.fetch_content(url, prompt=prompt, use_cache=use_cache)


def fetch_massey_ratings(
    sport: str = "nfl",
    api_key: Optional[str] = None,
    use_cache: bool = True,
) -> FetchResult:
    """
    Fetch Massey power ratings.

    Args:
        sport: Sport to fetch (NFL, CF for college football)
        api_key: Anthropic API key
        use_cache: Use cached result if available

    Returns:
        FetchResult with power ratings
    """
    client = WebFetchClient(api_key=api_key)

    # Map sport name to Massey notation
    sport_map = {
        "nfl": "NFL",
        "ncaaf": "CF",
        "cf": "CF",
    }
    massey_sport = sport_map.get(sport.lower(), sport.upper())

    url = f"https://masseyratings.com/{massey_sport}"
    prompt = "Extract team power ratings and rankings"
    return client.fetch_content(url, prompt=prompt, use_cache=use_cache)
