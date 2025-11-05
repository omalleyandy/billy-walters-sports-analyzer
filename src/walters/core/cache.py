"""
Caching system for Billy Walters Sports Analyzer.

Provides decorator-based caching with TTL (time-to-live) to:
- Reduce API calls (save money on AccuWeather, News API, etc.)
- Improve response times (10-100x faster for cached calls)
- Respect API rate limits
- Avoid redundant data fetching

Usage:
    from walters.core.cache import cache_weather_data, cache_injury_data
    
    @cache_weather_data(ttl=1800)  # Cache for 30 minutes
    async def fetch_weather(city: str):
        # This expensive API call only happens once per 30 min per city
        response = await async_get(f"https://api.weather.com?city={city}")
        return response['data']
    
    # First call - hits API (slow)
    weather1 = await fetch_weather("Buffalo")  # ~500ms
    
    # Second call - uses cache (fast!)
    weather2 = await fetch_weather("Buffalo")  # ~1ms

Cache Statistics:
    from walters.core.cache import get_cache_stats
    
    stats = get_cache_stats()
    print(f"Cached items: {stats['size']}")
    print(f"Hit rate: {stats['hit_rate']:.1%}")
"""

import functools
import hashlib
import json
import time
import logging
from typing import Any, Callable, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# In-memory cache: {key: (timestamp, result)}
_CACHE: Dict[str, Tuple[float, Any]] = {}

# Cache statistics
_CACHE_HITS = 0
_CACHE_MISSES = 0


def _make_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Create unique cache key from function name and arguments.
    
    Args:
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments
    
    Returns:
        MD5 hash as cache key
    """
    # Serialize args and kwargs to create unique key
    key_data = {
        'func': func_name,
        'args': str(args),
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
    }
    
    try:
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{func_name}:{key_hash[:16]}"  # Use first 16 chars
    except Exception as e:
        logger.warning(f"Failed to create cache key: {e}, using fallback")
        # Fallback: simple concatenation
        return f"{func_name}:{hash(str(args) + str(kwargs))}"


def cache_result(ttl: int = 300):
    """
    Cache decorator for async functions with time-to-live.
    
    Args:
        ttl: Time-to-live in seconds (default 300 = 5 minutes)
    
    Returns:
        Decorator function
    
    Example:
        @cache_result(ttl=600)  # Cache for 10 minutes
        async def expensive_function(arg1, arg2):
            result = await do_something_expensive()
            return result
        
        # First call - slow
        data1 = await expensive_function("a", "b")  # Cache MISS
        
        # Second call - fast!
        data2 = await expensive_function("a", "b")  # Cache HIT
        
        # Different args - slow
        data3 = await expensive_function("x", "y")  # Cache MISS
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            global _CACHE_HITS, _CACHE_MISSES
            
            # Create cache key
            cache_key = _make_cache_key(func.__name__, args, kwargs)
            
            # Check cache
            if cache_key in _CACHE:
                timestamp, cached_result = _CACHE[cache_key]
                age = time.time() - timestamp
                
                if age < ttl:
                    # Cache HIT
                    _CACHE_HITS += 1
                    logger.debug(
                        f"Cache HIT for {func.__name__} "
                        f"(age: {age:.1f}s, ttl: {ttl}s)"
                    )
                    return cached_result
                else:
                    # Cache EXPIRED
                    logger.debug(
                        f"Cache EXPIRED for {func.__name__} "
                        f"(age: {age:.1f}s > ttl: {ttl}s)"
                    )
            
            # Cache MISS - call function
            _CACHE_MISSES += 1
            logger.debug(f"Cache MISS for {func.__name__}, fetching...")
            
            result = await func(*args, **kwargs)
            
            # Store in cache
            _CACHE[cache_key] = (time.time(), result)
            logger.debug(f"Cached result for {func.__name__} (ttl: {ttl}s)")
            
            return result
        
        return wrapper
    return decorator


# Convenience decorators for specific use cases

def cache_weather_data(ttl: int = 1800):
    """
    Cache weather data (default 30 minutes).
    
    Weather doesn't change much in 30 minutes, so this is safe
    and saves significant API costs.
    
    Example:
        @cache_weather_data(ttl=1800)
        async def fetch_game_weather(stadium, location):
            return await get_accuweather_data(location)
    """
    return cache_result(ttl=ttl)


def cache_injury_data(ttl: int = 900):
    """
    Cache injury data (default 15 minutes).
    
    Injury reports update frequently, so use shorter TTL.
    
    Example:
        @cache_injury_data(ttl=900)
        async def fetch_injury_reports(team):
            return await scrape_espn_injuries(team)
    """
    return cache_result(ttl=ttl)


def cache_analysis_result(ttl: int = 300):
    """
    Cache analysis results (default 5 minutes).
    
    Game analysis can change as lines move, so use short TTL.
    
    Example:
        @cache_analysis_result(ttl=300)
        async def analyze_game(home_team, away_team, spread):
            return await full_analysis(home_team, away_team, spread)
    """
    return cache_result(ttl=ttl)


def cache_odds_data(ttl: int = 60):
    """
    Cache odds data (default 1 minute).
    
    Odds change quickly, so use very short TTL.
    
    Example:
        @cache_odds_data(ttl=60)
        async def fetch_current_odds(game_id):
            return await scrape_overtime_odds(game_id)
    """
    return cache_result(ttl=ttl)


def clear_cache():
    """
    Clear all cached data.
    
    Useful for:
    - Testing
    - Forcing fresh data
    - Memory management
    
    Example:
        # Clear cache before important update
        clear_cache()
        ratings = await update_power_ratings()
    """
    global _CACHE, _CACHE_HITS, _CACHE_MISSES
    
    count = len(_CACHE)
    _CACHE.clear()
    _CACHE_HITS = 0
    _CACHE_MISSES = 0
    
    logger.info(f"Cleared {count} items from cache")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dict with:
            - size: Number of cached items
            - hits: Total cache hits
            - misses: Total cache misses
            - hit_rate: Hit rate percentage (0.0 - 1.0)
            - items: List of cached item info
    
    Example:
        stats = get_cache_stats()
        print(f"Cache size: {stats['size']}")
        print(f"Hit rate: {stats['hit_rate']:.1%}")
        print(f"Saved {stats['hits']} API calls!")
    """
    total_requests = _CACHE_HITS + _CACHE_MISSES
    hit_rate = _CACHE_HITS / total_requests if total_requests > 0 else 0
    
    if not _CACHE:
        return {
            'size': 0,
            'hits': _CACHE_HITS,
            'misses': _CACHE_MISSES,
            'hit_rate': hit_rate,
            'items': []
        }
    
    current_time = time.time()
    
    items = []
    for key, (timestamp, _) in _CACHE.items():
        age = current_time - timestamp
        items.append({
            'key': key,
            'age_seconds': round(age, 1)
        })
    
    # Sort by age (newest first)
    items.sort(key=lambda x: x['age_seconds'])
    
    return {
        'size': len(_CACHE),
        'hits': _CACHE_HITS,
        'misses': _CACHE_MISSES,
        'hit_rate': hit_rate,
        'items': items[:10]  # Return newest 10 items
    }


def cache_info(func_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get info about specific function's cache usage.
    
    Args:
        func_name: Function name to filter by (optional)
    
    Returns:
        Dict with cache info for the function
    """
    if not func_name:
        return get_cache_stats()
    
    matching_items = [
        (key, timestamp, result)
        for key, (timestamp, result) in _CACHE.items()
        if key.startswith(func_name)
    ]
    
    return {
        'function': func_name,
        'cached_calls': len(matching_items),
        'items': [{'key': k, 'age': time.time() - t} for k, t, _ in matching_items]
    }


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    # Example expensive function
    @cache_result(ttl=5)  # 5 second cache for demo
    async def expensive_operation(n: int) -> int:
        """Simulate expensive API call."""
        print(f"  [API CALL] Computing {n}...")
        await asyncio.sleep(0.5)  # Simulate 500ms API call
        return n * 2
    
    async def test_caching():
        """Test the caching system."""
        print("Testing Caching System...")
        print("=" * 50)
        
        # Test 1: First call (cache miss)
        print("\n1. First call (cache MISS - slow):")
        start = time.time()
        result1 = await expensive_operation(5)
        time1 = time.time() - start
        print(f"  Result: {result1}, Time: {time1:.3f}s")
        
        # Test 2: Second call (cache hit)
        print("\n2. Second call (cache HIT - fast!):")
        start = time.time()
        result2 = await expensive_operation(5)
        time2 = time.time() - start
        print(f"  Result: {result2}, Time: {time2:.3f}s")
        print(f"  [SPEEDUP] {time1/time2:.0f}x faster!")
        
        # Test 3: Different arguments (cache miss)
        print("\n3. Different arguments (cache MISS):")
        result3 = await expensive_operation(10)
        print(f"  Result: {result3}")
        
        # Test 4: Original arguments still cached
        print("\n4. Original arguments (cache HIT):")
        start = time.time()
        result4 = await expensive_operation(5)
        time4 = time.time() - start
        print(f"  Result: {result4}, Time: {time4:.3f}s")
        
        # Test 5: Cache statistics
        print("\n5. Cache statistics:")
        stats = get_cache_stats()
        print(f"  Cached items: {stats['size']}")
        print(f"  Cache hits: {stats['hits']}")
        print(f"  Cache misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate']:.1%}")
        print(f"  [SAVINGS] Saved {stats['hits']} API calls!")
        
        # Test 6: Wait for expiration
        print("\n6. Waiting for cache expiration (5s)...")
        await asyncio.sleep(5.5)
        print("  Cache expired, next call will be slow again:")
        start = time.time()
        result5 = await expensive_operation(5)
        time5 = time.time() - start
        print(f"  Result: {result5}, Time: {time5:.3f}s (cache expired)")
        
        # Test 7: Clear cache
        print("\n7. Clearing cache...")
        clear_cache()
        stats = get_cache_stats()
        print(f"  Cache size after clear: {stats['size']}")
        
        print("\n" + "=" * 50)
        print("Caching test complete!")
        print("\n[KEY TAKEAWAY]")
        print("  - First call:  ~500ms (API)")
        print("  - Cached call: ~0.1ms (100-500x faster!)")
        print("  - Saves API costs and respects rate limits")
    
    # Run tests
    asyncio.run(test_caching())

