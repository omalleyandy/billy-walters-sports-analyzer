# Web Fetch Client - Documentation

## Overview

The `web_fetch_client.py` module provides a production-ready integration with Anthropic's web_fetch tool for the Billy Walters Sports Analyzer project. It enables robust web content fetching with automatic retry, caching, domain validation, and comprehensive error handling.

## Features

- **Automatic Retry**: Exponential backoff for rate limits and connection errors
- **Smart Caching**: Response caching with configurable TTL to avoid redundant API calls
- **Domain Validation**: Whitelist-based security to prevent unauthorized data access
- **Error Handling**: Comprehensive error handling with detailed logging
- **Billy Walters Alignment**: Built specifically for sports betting data collection
- **Type Safety**: Full type hints for better IDE support and code quality

## Installation

Add the required dependency to your project:

```bash
uv add anthropic
```

Or ensure it's in your `pyproject.toml`:

```toml
dependencies = [
    "anthropic>=0.40.0",
]
```

## Quick Start

### Basic Usage

```python
from web_fetch_client import WebFetchClient

# Initialize client (uses ANTHROPIC_API_KEY environment variable)
client = WebFetchClient()

# Fetch content from a URL
result = client.fetch_content(
    "https://www.espn.com/nfl/schedule",
    prompt="Extract the NFL schedule including teams and game times"
)

if result.success:
    print(result.content)
    print(f"Citations: {len(result.citations)}")
else:
    print(f"Error: {result.error}")
```

### Convenience Functions

```python
from web_fetch_client import (
    fetch_nfl_schedule,
    fetch_vegas_lines,
    fetch_weather_forecast,
    fetch_massey_ratings
)

# Fetch NFL schedule
schedule = fetch_nfl_schedule(week=11)

# Fetch betting lines
lines = fetch_vegas_lines("nfl")

# Fetch weather forecast
weather = fetch_weather_forecast("Pittsburgh, PA", stadium_name="Acrisure Stadium")

# Fetch power ratings
ratings = fetch_massey_ratings("nfl")
```

## Configuration

### Client Initialization

```python
client = WebFetchClient(
    api_key="your-api-key",          # Optional: defaults to env var
    max_uses=10,                      # Max web fetches per request
    max_content_tokens=100000,        # Max tokens per fetch
    enable_citations=True,            # Enable source citations
    enable_cache=True,                # Enable response caching
    cache_ttl_seconds=3600            # Cache TTL (1 hour)
)
```

### Allowed Domains

The client restricts fetches to these domains:

- `espn.com` - NFL schedules and scores
- `nfl.com` - Official NFL data
- `masseyratings.com` - Power ratings
- `overtime.ag` - Live odds
- `covers.com` - Historical betting data
- `actionnetwork.com` - Betting analytics
- `vegasinsider.com` - Vegas odds
- `accuweather.com` - Weather forecasts

To add domains, modify the `ALLOWED_DOMAINS` list in [web_fetch_client.py:173](web_fetch_client.py#L173).

## API Reference

### WebFetchClient Class

#### Methods

##### `fetch_content(url, prompt=None, model="claude-sonnet-4-20250514", max_tokens=4096, use_cache=True)`

Fetch and analyze content from a URL.

**Parameters:**
- `url` (str): URL to fetch (must be from allowed domains)
- `prompt` (str, optional): Analysis prompt (defaults to content extraction)
- `model` (str): Claude model to use
- `max_tokens` (int): Max response tokens
- `use_cache` (bool): Use cached result if available

**Returns:**
- `FetchResult`: Result object with content, citations, and metadata

**Raises:**
- `ValueError`: If URL domain not in allowed list or invalid scheme
- `anthropic.APIError`: If API request fails after retries

**Example:**
```python
result = client.fetch_content(
    "https://www.espn.com/nfl/scoreboard",
    prompt="Extract current NFL game scores and spreads"
)
```

##### `fetch_multiple(urls, prompt_template=None, model="claude-sonnet-4-20250514", max_tokens=4096, use_cache=True, delay_between_requests=1.0)`

Fetch content from multiple URLs with rate limiting.

**Parameters:**
- `urls` (List[str]): List of URLs to fetch
- `prompt_template` (str, optional): Template for prompts (use `{url}` placeholder)
- `model` (str): Claude model to use
- `max_tokens` (int): Max response tokens per fetch
- `use_cache` (bool): Use cached results if available
- `delay_between_requests` (float): Seconds to wait between requests

**Returns:**
- `Dict[str, FetchResult]`: Dict mapping URL to FetchResult

**Example:**
```python
urls = [
    "https://www.espn.com/nfl/scoreboard",
    "https://www.vegasinsider.com/nfl/odds/las-vegas/"
]
results = client.fetch_multiple(
    urls,
    prompt_template="Extract betting data from {url}",
    delay_between_requests=2.0
)
```

##### `validate_url(url)`

Validate URL is from allowed domain.

**Parameters:**
- `url` (str): URL to validate

**Returns:**
- `bool`: True if valid, False otherwise

##### `clear_cache()`

Clear all cached results.

**Returns:**
- `int`: Number of cached entries cleared

##### `cleanup_expired_cache()`

Remove expired cache entries.

**Returns:**
- `int`: Number of expired entries removed

##### `save_result(result, output_dir="betting_data/web_fetch")`

Save fetch result to JSON file.

**Parameters:**
- `result` (FetchResult): FetchResult to save
- `output_dir` (str): Output directory

**Returns:**
- `Path`: Path to saved file

##### `get_cache_stats()`

Get cache statistics.

**Returns:**
- `Dict[str, Any]`: Dict with cache stats (size, oldest entry, etc.)

### Data Classes

#### FetchResult

Standardized result from web fetch operation.

**Fields:**
- `url` (str): URL that was fetched
- `content` (str): Extracted content
- `citations` (List[Dict[str, Any]]): Source citations
- `metadata` (FetchMetadata): Fetch metadata
- `success` (bool): Whether fetch succeeded
- `error` (str, optional): Error message if failed

**Methods:**
- `to_dict()`: Convert to dictionary for JSON serialization

#### FetchMetadata

Metadata about a web fetch operation.

**Fields:**
- `url` (str): URL fetched
- `timestamp` (str): ISO timestamp
- `input_tokens` (int): Input tokens used
- `output_tokens` (int): Output tokens generated
- `web_fetch_requests` (int): Number of web fetch requests
- `model` (str): Model used
- `duration_seconds` (float): Time taken
- `cache_hit` (bool): Whether result came from cache

## Caching

The client includes an intelligent caching system to reduce API calls and costs.

### How Caching Works

1. **Cache Key Generation**: SHA-256 hash of URL + prompt
2. **Storage**: In-memory dictionary with (result, timestamp) tuples
3. **Expiration**: Automatic expiration after TTL
4. **Validation**: Age check on every retrieval

### Cache Management

```python
# Check cache stats
stats = client.get_cache_stats()
print(f"Cache size: {stats['size']} entries")
print(f"Oldest entry: {stats['oldest_entry_age_seconds']:.0f}s ago")

# Clean up expired entries
removed = client.cleanup_expired_cache()
print(f"Removed {removed} expired entries")

# Clear all cache
count = client.clear_cache()
print(f"Cleared {count} entries")
```

### Cache Configuration

```python
# Disable caching
client = WebFetchClient(enable_cache=False)

# Custom TTL (30 minutes)
client = WebFetchClient(cache_ttl_seconds=1800)

# Per-request cache bypass
result = client.fetch_content(url, use_cache=False)
```

## Error Handling

### Retry Logic

The client automatically retries on:
- **Rate Limit Errors**: Exponential backoff (2s, 4s, 8s)
- **Connection Errors**: Exponential backoff (2s, 4s, 8s)

Non-retryable errors (validation, authentication) fail immediately.

### Error Responses

Failed fetches return a `FetchResult` with:
- `success=False`
- `error` field with error message
- Empty content and citations
- Metadata with 0 tokens

```python
result = client.fetch_content("https://bad-url.com")
if not result.success:
    print(f"Fetch failed: {result.error}")
```

## Best Practices

### 1. Use Environment Variables

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### 2. Enable Caching for Repeated Requests

```python
# First call hits API
result1 = client.fetch_content(url, use_cache=True)

# Second call uses cache
result2 = client.fetch_content(url, use_cache=True)
```

### 3. Rate Limit Multiple Fetches

```python
results = client.fetch_multiple(
    urls,
    delay_between_requests=2.0  # 2 seconds between requests
)
```

### 4. Save Important Results

```python
if result.success:
    filepath = client.save_result(result)
    print(f"Saved to: {filepath}")
```

### 5. Clean Up Cache Periodically

```python
# In a scheduled task or before long-running operations
client.cleanup_expired_cache()
```

### 6. Handle Errors Gracefully

```python
try:
    result = client.fetch_content(url)
    if result.success:
        process_content(result.content)
    else:
        logger.error(f"Fetch failed: {result.error}")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
```

## Testing

The module includes comprehensive unit tests covering:
- Client initialization
- URL validation
- Cache management
- Content fetching
- Error handling
- Convenience functions

### Run Tests

```bash
uv run pytest test_web_fetch_client.py -v
```

### Test Coverage

```bash
uv run pytest test_web_fetch_client.py --cov=web_fetch_client --cov-report=html
```

## Changelog

### Version 2.0.0 (2025-11-17)

**Breaking Changes:**
- Updated model name to `claude-sonnet-4-20250514`
- Changed cache key hash from MD5 to SHA-256

**Improvements:**
- Added URL scheme validation
- Added `cleanup_expired_cache()` method
- Improved type safety with better null handling
- Fixed Windows console emoji issues
- Enhanced error handling for missing response attributes

**Bug Fixes:**
- Fixed `server_tool_use` null reference
- Fixed `citations` attribute access
- Fixed weather forecast URL construction

**Documentation:**
- Added comprehensive README
- Added unit test suite
- Improved inline documentation

## Billy Walters Methodology Alignment

This module supports the Billy Walters sports betting methodology:

1. **Data Validation**: Domain whitelist ensures only trusted sources
2. **Citation Tracking**: Full citation support for source verification
3. **Error Logging**: Comprehensive logging for audit trails
4. **Caching**: Reduces costs while maintaining data freshness
5. **Retry Logic**: Ensures reliable data collection

## Troubleshooting

### Issue: ValueError - API key not found

**Solution:** Set the `ANTHROPIC_API_KEY` environment variable:
```bash
export ANTHROPIC_API_KEY="your-key"
```

### Issue: ValueError - URL domain not in allowed list

**Solution:** Add the domain to `ALLOWED_DOMAINS` in [web_fetch_client.py:173](web_fetch_client.py#L173).

### Issue: Rate limit errors

**Solution:** Increase `delay_between_requests` or enable caching:
```python
results = client.fetch_multiple(urls, delay_between_requests=3.0)
```

### Issue: Cache growing too large

**Solution:** Reduce TTL or clean up periodically:
```python
client = WebFetchClient(cache_ttl_seconds=600)  # 10 minutes
client.cleanup_expired_cache()
```

### Issue: Windows console emoji errors

**Solution:** Use plain text output (already fixed in v2.0.0):
```python
print("[OK] Success")  # Instead of "✅ Success"
```

## Contributing

When contributing to this module:

1. Follow PEP 8 style guide
2. Add type hints for all functions
3. Write unit tests for new features
4. Update documentation
5. Run formatting and linting:
   ```bash
   uv run ruff format web_fetch_client.py
   uv run ruff check web_fetch_client.py
   ```

## License

Part of the Billy Walters Sports Analyzer project.

## Support

For issues or questions:
- Check this documentation
- Review unit tests for usage examples
- Check logs for error details
- Consult Anthropic API documentation

## Related Files

- [web_fetch_client.py](web_fetch_client.py) - Main module
- [test_web_fetch_client.py](test_web_fetch_client.py) - Unit tests
- [pyproject.toml](pyproject.toml) - Dependencies
