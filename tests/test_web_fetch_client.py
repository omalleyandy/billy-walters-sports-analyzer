"""
Unit tests for web_fetch_client module.

Tests cover:
- Client initialization
- URL validation
- Cache management
- Content fetching
- Error handling
- Convenience functions
"""

import os
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import anthropic

from web_fetch_client import (
    WebFetchClient,
    FetchResult,
    FetchMetadata,
    fetch_nfl_schedule,
    fetch_vegas_lines,
    fetch_weather_forecast,
    fetch_massey_ratings,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_api_key(monkeypatch):
    """Set mock API key environment variable."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-12345")
    return "test-key-12345"


@pytest.fixture
def client(mock_api_key):
    """Create WebFetchClient instance for testing."""
    return WebFetchClient()


@pytest.fixture
def mock_response():
    """Create a mock Anthropic API response."""
    response = Mock()
    response.model = "claude-sonnet-4-20250514"
    response.usage = Mock()
    response.usage.input_tokens = 100
    response.usage.output_tokens = 200
    response.usage.server_tool_use = {"web_fetch_requests": 1}

    # Mock content blocks
    text_block = Mock()
    text_block.type = "text"
    text_block.text = "Sample content from the web"
    text_block.citations = [{"url": "https://example.com", "title": "Example"}]

    response.content = [text_block]

    return response


# =============================================================================
# Initialization Tests
# =============================================================================


def test_client_initialization_with_env_var(mock_api_key):
    """Test client initializes with API key from environment."""
    client = WebFetchClient()
    assert client.api_key == mock_api_key
    assert client.max_uses == 10
    assert client.max_content_tokens == 100000
    assert client.enable_citations is True
    assert client.enable_cache is True
    assert client.cache_ttl_seconds == 3600


def test_client_initialization_with_explicit_key():
    """Test client initializes with explicitly provided API key."""
    client = WebFetchClient(api_key="explicit-key")
    assert client.api_key == "explicit-key"


def test_client_initialization_without_key(monkeypatch):
    """Test client raises ValueError when no API key provided."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
        WebFetchClient()


def test_client_initialization_with_custom_params(mock_api_key):
    """Test client initializes with custom parameters."""
    client = WebFetchClient(
        max_uses=5,
        max_content_tokens=50000,
        enable_citations=False,
        enable_cache=False,
        cache_ttl_seconds=1800,
    )
    assert client.max_uses == 5
    assert client.max_content_tokens == 50000
    assert client.enable_citations is False
    assert client.enable_cache is False
    assert client.cache_ttl_seconds == 1800


# =============================================================================
# URL Validation Tests
# =============================================================================


def test_validate_url_allowed_domain(client):
    """Test URL validation accepts allowed domains."""
    assert client.validate_url("https://www.espn.com/nfl/schedule") is True
    assert client.validate_url("https://masseyratings.com/CF") is True
    assert client.validate_url("https://www.accuweather.com/forecast") is True


def test_validate_url_disallowed_domain(client):
    """Test URL validation rejects disallowed domains."""
    assert client.validate_url("https://malicious-site.com/data") is False
    assert client.validate_url("https://random.org/numbers") is False


def test_validate_url_strict_invalid_scheme(client):
    """Test strict validation rejects invalid URL schemes."""
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        client._validate_url_strict("ftp://espn.com/data")

    with pytest.raises(ValueError, match="Invalid URL scheme"):
        client._validate_url_strict("espn.com/data")


def test_validate_url_strict_disallowed_domain(client):
    """Test strict validation rejects disallowed domains."""
    with pytest.raises(ValueError, match="URL domain not in allowed list"):
        client._validate_url_strict("https://bad-domain.com/data")


def test_validate_url_strict_valid_url(client):
    """Test strict validation accepts valid URLs."""
    # Should not raise any exception
    client._validate_url_strict("https://www.espn.com/nfl/schedule")
    client._validate_url_strict("http://www.espn.com/nfl/schedule")


# =============================================================================
# Cache Tests
# =============================================================================


def test_cache_key_generation(client):
    """Test cache key generation is consistent."""
    url = "https://www.espn.com/nfl/schedule"
    prompt = "Extract schedule data"

    key1 = client._generate_cache_key(url, prompt)
    key2 = client._generate_cache_key(url, prompt)

    assert key1 == key2
    assert len(key1) == 64  # SHA-256 hex digest length


def test_cache_key_uniqueness(client):
    """Test different URLs/prompts generate different cache keys."""
    key1 = client._generate_cache_key("https://espn.com", "prompt1")
    key2 = client._generate_cache_key("https://espn.com", "prompt2")
    key3 = client._generate_cache_key("https://nfl.com", "prompt1")

    assert key1 != key2
    assert key1 != key3
    assert key2 != key3


def test_cache_result_storage(client):
    """Test caching stores and retrieves results."""
    result = FetchResult(
        url="https://espn.com",
        content="test content",
        citations=[],
        metadata=FetchMetadata(
            url="https://espn.com",
            timestamp=datetime.now().isoformat(),
            input_tokens=100,
            output_tokens=200,
            web_fetch_requests=1,
            model="claude-sonnet-4-20250514",
            duration_seconds=1.5,
        ),
        success=True,
    )

    cache_key = client._generate_cache_key("https://espn.com", "test prompt")
    client._cache_result(cache_key, result)

    cached = client._get_cached_result(cache_key)
    assert cached is not None
    assert cached.url == result.url
    assert cached.content == result.content


def test_cache_expiration(client):
    """Test cache entries expire after TTL."""
    client.cache_ttl_seconds = 1  # 1 second TTL

    result = FetchResult(
        url="https://espn.com",
        content="test content",
        citations=[],
        metadata=FetchMetadata(
            url="https://espn.com",
            timestamp=datetime.now().isoformat(),
            input_tokens=100,
            output_tokens=200,
            web_fetch_requests=1,
            model="claude-sonnet-4-20250514",
            duration_seconds=1.5,
        ),
        success=True,
    )

    cache_key = client._generate_cache_key("https://espn.com", "test")
    client._cache_result(cache_key, result)

    # Should be cached immediately
    assert client._get_cached_result(cache_key) is not None

    # Wait for expiration
    time.sleep(1.1)

    # Should be expired
    assert client._get_cached_result(cache_key) is None


def test_clear_cache(client):
    """Test clearing cache removes all entries."""
    # Add multiple cache entries
    for i in range(5):
        result = FetchResult(
            url=f"https://espn.com/{i}",
            content="test",
            citations=[],
            metadata=FetchMetadata(
                url=f"https://espn.com/{i}",
                timestamp=datetime.now().isoformat(),
                input_tokens=100,
                output_tokens=200,
                web_fetch_requests=1,
                model="claude-sonnet-4-20250514",
                duration_seconds=1.5,
            ),
            success=True,
        )
        cache_key = client._generate_cache_key(f"https://espn.com/{i}", "test")
        client._cache_result(cache_key, result)

    assert len(client._cache) == 5

    count = client.clear_cache()
    assert count == 5
    assert len(client._cache) == 0


def test_cleanup_expired_cache(client):
    """Test cleanup removes only expired entries."""
    client.cache_ttl_seconds = 2

    # Add fresh entry
    result1 = FetchResult(
        url="https://espn.com/fresh",
        content="fresh",
        citations=[],
        metadata=FetchMetadata(
            url="https://espn.com/fresh",
            timestamp=datetime.now().isoformat(),
            input_tokens=100,
            output_tokens=200,
            web_fetch_requests=1,
            model="claude-sonnet-4-20250514",
            duration_seconds=1.5,
        ),
        success=True,
    )

    # Add old entry (manually set timestamp)
    result2 = FetchResult(
        url="https://espn.com/old",
        content="old",
        citations=[],
        metadata=FetchMetadata(
            url="https://espn.com/old",
            timestamp=datetime.now().isoformat(),
            input_tokens=100,
            output_tokens=200,
            web_fetch_requests=1,
            model="claude-sonnet-4-20250514",
            duration_seconds=1.5,
        ),
        success=True,
    )

    key_fresh = client._generate_cache_key("https://espn.com/fresh", "test")
    key_old = client._generate_cache_key("https://espn.com/old", "test")

    client._cache[key_fresh] = (result1, time.time())
    client._cache[key_old] = (result2, time.time() - 10)  # 10 seconds old

    removed = client.cleanup_expired_cache()
    assert removed == 1
    assert key_fresh in client._cache
    assert key_old not in client._cache


def test_cache_disabled(client):
    """Test caching can be disabled."""
    client.enable_cache = False

    result = FetchResult(
        url="https://espn.com",
        content="test",
        citations=[],
        metadata=FetchMetadata(
            url="https://espn.com",
            timestamp=datetime.now().isoformat(),
            input_tokens=100,
            output_tokens=200,
            web_fetch_requests=1,
            model="claude-sonnet-4-20250514",
            duration_seconds=1.5,
        ),
        success=True,
    )

    cache_key = client._generate_cache_key("https://espn.com", "test")
    client._cache_result(cache_key, result)

    # Should not cache when disabled
    assert client._get_cached_result(cache_key) is None


# =============================================================================
# Response Processing Tests
# =============================================================================


def test_process_response_success(client, mock_response):
    """Test successful response processing."""
    result = client._process_response(mock_response, "https://espn.com", 1.5)

    assert result.success is True
    assert result.url == "https://espn.com"
    assert result.content == "Sample content from the web"
    assert len(result.citations) == 1
    assert result.metadata.input_tokens == 100
    assert result.metadata.output_tokens == 200
    assert result.metadata.duration_seconds == 1.5


def test_process_response_without_citations(client):
    """Test response processing without citations."""
    response = Mock()
    response.model = "claude-sonnet-4-20250514"
    response.usage = Mock()
    response.usage.input_tokens = 100
    response.usage.output_tokens = 200
    response.usage.server_tool_use = None

    text_block = Mock()
    text_block.type = "text"
    text_block.text = "Content without citations"
    text_block.citations = None

    response.content = [text_block]

    result = client._process_response(response, "https://espn.com", 1.0)

    assert result.success is True
    assert len(result.citations) == 0


# =============================================================================
# Fetch Content Tests
# =============================================================================


@patch("web_fetch_client.anthropic.Anthropic")
def test_fetch_content_success(mock_anthropic_class, client, mock_response):
    """Test successful content fetching."""
    mock_client = Mock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_class.return_value = mock_client

    # Recreate client to use mocked Anthropic
    client.client = mock_client

    result = client.fetch_content("https://www.espn.com/nfl/schedule", use_cache=False)

    assert result.success is True
    assert result.content == "Sample content from the web"
    mock_client.messages.create.assert_called_once()


@patch("web_fetch_client.anthropic.Anthropic")
def test_fetch_content_with_cache(mock_anthropic_class, client, mock_response):
    """Test fetch content uses cache."""
    mock_client = Mock()
    mock_client.messages.create.return_value = mock_response
    client.client = mock_client

    url = "https://www.espn.com/nfl/schedule"
    prompt = "Extract schedule"

    # First fetch (cache miss)
    result1 = client.fetch_content(url, prompt, use_cache=True)
    assert result1.success is True
    assert mock_client.messages.create.call_count == 1

    # Second fetch (cache hit)
    result2 = client.fetch_content(url, prompt, use_cache=True)
    assert result2.success is True
    assert result2.content == result1.content
    # Should still be 1 call (cached)
    assert mock_client.messages.create.call_count == 1


def test_fetch_content_invalid_url(client):
    """Test fetch content rejects invalid URLs."""
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        client.fetch_content("not-a-valid-url")

    with pytest.raises(ValueError, match="URL domain not in allowed list"):
        client.fetch_content("https://malicious-site.com")


# =============================================================================
# Cache Stats Tests
# =============================================================================


def test_get_cache_stats_empty(client):
    """Test cache stats when cache is empty."""
    stats = client.get_cache_stats()

    assert stats["enabled"] is True
    assert stats["size"] == 0
    assert stats["ttl_seconds"] == 3600


def test_get_cache_stats_with_entries(client):
    """Test cache stats with cached entries."""
    # Add some cache entries
    for i in range(3):
        result = FetchResult(
            url=f"https://espn.com/{i}",
            content="test",
            citations=[],
            metadata=FetchMetadata(
                url=f"https://espn.com/{i}",
                timestamp=datetime.now().isoformat(),
                input_tokens=100,
                output_tokens=200,
                web_fetch_requests=1,
                model="claude-sonnet-4-20250514",
                duration_seconds=1.5,
            ),
            success=True,
        )
        cache_key = client._generate_cache_key(f"https://espn.com/{i}", "test")
        client._cache_result(cache_key, result)

    stats = client.get_cache_stats()

    assert stats["enabled"] is True
    assert stats["size"] == 3
    assert "oldest_entry_age_seconds" in stats
    assert "newest_entry_age_seconds" in stats
    assert "average_entry_age_seconds" in stats


# =============================================================================
# Save Result Tests
# =============================================================================


def test_save_result(client, tmp_path):
    """Test saving fetch result to file."""
    result = FetchResult(
        url="https://www.espn.com/nfl/schedule",
        content="Test content",
        citations=[],
        metadata=FetchMetadata(
            url="https://www.espn.com/nfl/schedule",
            timestamp=datetime.now().isoformat(),
            input_tokens=100,
            output_tokens=200,
            web_fetch_requests=1,
            model="claude-sonnet-4-20250514",
            duration_seconds=1.5,
        ),
        success=True,
    )

    output_dir = str(tmp_path / "test_output")
    filepath = client.save_result(result, output_dir=output_dir)

    assert filepath.exists()
    assert filepath.suffix == ".json"
    assert "www_espn_com" in filepath.name


# =============================================================================
# Convenience Function Tests
# =============================================================================


@patch("web_fetch_client.WebFetchClient")
def test_fetch_nfl_schedule(mock_client_class):
    """Test NFL schedule fetching convenience function."""
    mock_client = Mock()
    mock_result = Mock(success=True)
    mock_client.fetch_content.return_value = mock_result
    mock_client_class.return_value = mock_client

    result = fetch_nfl_schedule(week=11)

    assert result.success is True
    mock_client.fetch_content.assert_called_once()
    call_args = mock_client.fetch_content.call_args
    assert "week/11" in call_args[0][0]


@patch("web_fetch_client.WebFetchClient")
def test_fetch_vegas_lines(mock_client_class):
    """Test Vegas lines fetching convenience function."""
    mock_client = Mock()
    mock_result = Mock(success=True)
    mock_client.fetch_content.return_value = mock_result
    mock_client_class.return_value = mock_client

    result = fetch_vegas_lines("nfl")

    assert result.success is True
    mock_client.fetch_content.assert_called_once()


@patch("web_fetch_client.WebFetchClient")
def test_fetch_weather_forecast(mock_client_class):
    """Test weather forecast fetching convenience function."""
    mock_client = Mock()
    mock_result = Mock(success=True)
    mock_client.fetch_content.return_value = mock_result
    mock_client_class.return_value = mock_client

    result = fetch_weather_forecast("Pittsburgh, PA", stadium_name="Heinz Field")

    assert result.success is True
    mock_client.fetch_content.assert_called_once()


@patch("web_fetch_client.WebFetchClient")
def test_fetch_massey_ratings(mock_client_class):
    """Test Massey ratings fetching convenience function."""
    mock_client = Mock()
    mock_result = Mock(success=True)
    mock_client.fetch_content.return_value = mock_result
    mock_client_class.return_value = mock_client

    result = fetch_massey_ratings("nfl")

    assert result.success is True
    mock_client.fetch_content.assert_called_once()


# =============================================================================
# FetchResult Tests
# =============================================================================


def test_fetch_result_to_dict():
    """Test FetchResult to_dict conversion."""
    metadata = FetchMetadata(
        url="https://espn.com",
        timestamp="2025-11-17T10:00:00",
        input_tokens=100,
        output_tokens=200,
        web_fetch_requests=1,
        model="claude-sonnet-4-20250514",
        duration_seconds=1.5,
    )

    result = FetchResult(
        url="https://espn.com",
        content="test content",
        citations=[{"title": "Test"}],
        metadata=metadata,
        success=True,
    )

    result_dict = result.to_dict()

    assert result_dict["url"] == "https://espn.com"
    assert result_dict["content"] == "test content"
    assert result_dict["success"] is True
    assert "metadata" in result_dict
    assert result_dict["timestamp"] == "2025-11-17T10:00:00"
