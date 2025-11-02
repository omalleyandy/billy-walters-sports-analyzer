# Quick Upgrade Guide: Top 3 Improvements

## 🚀 Get Started in 30 Minutes

This guide helps you implement the **3 highest-impact upgrades** from the vNext SDK:
1. HTTP Client (15 min)
2. Caching System (10 min)
3. Models Consolidation (5 min)

---

## Step 1: Add HTTP Client (15 minutes)

### What You're Adding
- Centralized async HTTP client with connection pooling
- Automatic error handling
- Better performance (reuses connections)

### Implementation

#### 1.1 Create the HTTP Client Module

Create file: `walters_analyzer/core/http_client.py`

```python
"""
Centralized async HTTP client for Billy Walters Sports Analyzer.
Provides connection pooling, error handling, and consistent interface.
"""

import aiohttp
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

_CLIENT_SESSION: Optional[aiohttp.ClientSession] = None


async def get_client_session() -> aiohttp.ClientSession:
    """
    Get or create singleton aiohttp session with connection pooling.
    
    Returns:
        Configured aiohttp ClientSession
    """
    global _CLIENT_SESSION
    
    if _CLIENT_SESSION is None or _CLIENT_SESSION.closed:
        connector = aiohttp.TCPConnector(
            limit=100,              # Max 100 connections total
            limit_per_host=30,      # Max 30 per host
            ttl_dns_cache=300       # DNS cache for 5 min
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,               # Total timeout 30s
            connect=10,             # Connection timeout 10s
            sock_read=20            # Read timeout 20s
        )
        
        _CLIENT_SESSION = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Billy-Walters-Analyzer/1.0'}
        )
        
        logger.info("Created new HTTP client session")
    
    return _CLIENT_SESSION


async def async_get(
    url: str, 
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Async GET request with error handling.
    
    Args:
        url: URL to request
        params: Query parameters
        headers: Additional headers
    
    Returns:
        Dict with 'status', 'data', and optional 'error'
    """
    session = await get_client_session()
    
    try:
        async with session.get(url, params=params, headers=headers) as response:
            if response.content_type == 'application/json':
                data = await response.json()
            else:
                data = await response.text()
            
            return {
                'status': response.status,
                'data': data,
                'headers': dict(response.headers)
            }
    
    except aiohttp.ClientError as e:
        logger.error(f"HTTP client error for {url}: {e}")
        return {
            'status': 0,
            'error': f"Client error: {str(e)}",
            'data': None
        }
    
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}")
        return {
            'status': 0,
            'error': f"Unexpected error: {str(e)}",
            'data': None
        }


async def async_post(
    url: str,
    data: Optional[Dict] = None,
    json: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Async POST request with error handling.
    
    Args:
        url: URL to request
        data: Form data
        json: JSON data
        headers: Additional headers
    
    Returns:
        Dict with 'status', 'data', and optional 'error'
    """
    session = await get_client_session()
    
    try:
        async with session.post(url, data=data, json=json, headers=headers) as response:
            response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            
            return {
                'status': response.status,
                'data': response_data
            }
    
    except Exception as e:
        logger.error(f"POST error for {url}: {e}")
        return {
            'status': 0,
            'error': str(e),
            'data': None
        }


async def cleanup_http_client():
    """
    Cleanup HTTP client session.
    Call this on application shutdown.
    """
    global _CLIENT_SESSION
    
    if _CLIENT_SESSION and not _CLIENT_SESSION.closed:
        await _CLIENT_SESSION.close()
        logger.info("Closed HTTP client session")
        _CLIENT_SESSION = None


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test GET
        result = await async_get("https://api.github.com/users/github")
        print(f"Status: {result['status']}")
        print(f"Data: {result['data']['name']}")
        
        # Cleanup
        await cleanup_http_client()
    
    asyncio.run(test())
```

#### 1.2 Update Weather Fetcher

Edit: `walters_analyzer/weather_fetcher.py`

```python
# Add at top:
from walters_analyzer.core.http_client import async_get

# Replace aiohttp calls:

# OLD:
# async with aiohttp.ClientSession() as session:
#     async with session.get(url, params=params) as response:
#         data = await response.json()

# NEW:
response = await async_get(url, params=params)
if response['status'] == 200:
    data = response['data']
else:
    logger.error(f"API error: {response.get('error')}")
    return None
```

#### 1.3 Test

```bash
# Run existing tests
pytest tests/

# Test weather fetcher specifically
uv run walters-analyzer scrape-weather --stadium "Highmark Stadium" --location "Buffalo, NY"
```

---

## Step 2: Add Caching System (10 minutes)

### What You're Adding
- Automatic caching of API calls
- Configurable TTL (time-to-live)
- Saves API costs and improves speed

### Implementation

#### 2.1 Create Cache Module

Create file: `walters_analyzer/core/cache.py`

```python
"""
Caching system for Billy Walters Sports Analyzer.
Reduces API calls and improves performance.
"""

import functools
import hashlib
import json
import time
import logging
from typing import Any, Callable, Dict, Tuple

logger = logging.getLogger(__name__)

# In-memory cache: {key: (timestamp, result)}
_CACHE: Dict[str, Tuple[float, Any]] = {}


def _make_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Create unique cache key from function and arguments.
    
    Args:
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments
    
    Returns:
        MD5 hash as cache key
    """
    # Serialize args and kwargs
    key_data = {
        'func': func_name,
        'args': str(args),
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
    }
    
    key_string = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{func_name}:{key_hash}"


def cache_result(ttl: int = 300):
    """
    Cache decorator for async functions.
    
    Args:
        ttl: Time-to-live in seconds (default 300 = 5 min)
    
    Usage:
        @cache_result(ttl=600)  # Cache for 10 minutes
        async def expensive_function(arg1, arg2):
            return await do_something_expensive()
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = _make_cache_key(func.__name__, args, kwargs)
            
            # Check cache
            if cache_key in _CACHE:
                timestamp, cached_result = _CACHE[cache_key]
                age = time.time() - timestamp
                
                if age < ttl:
                    logger.debug(
                        f"Cache HIT for {func.__name__} "
                        f"(age: {age:.1f}s, ttl: {ttl}s)"
                    )
                    return cached_result
                else:
                    logger.debug(
                        f"Cache EXPIRED for {func.__name__} "
                        f"(age: {age:.1f}s > ttl: {ttl}s)"
                    )
            
            # Cache miss - call function
            logger.debug(f"Cache MISS for {func.__name__}, fetching...")
            result = await func(*args, **kwargs)
            
            # Store in cache
            _CACHE[cache_key] = (time.time(), result)
            
            return result
        
        return wrapper
    return decorator


# Convenience decorators for specific use cases

def cache_weather_data(ttl: int = 1800):
    """Cache weather data for 30 minutes (default)."""
    return cache_result(ttl=ttl)


def cache_injury_data(ttl: int = 900):
    """Cache injury data for 15 minutes (default)."""
    return cache_result(ttl=ttl)


def cache_analysis_result(ttl: int = 300):
    """Cache analysis results for 5 minutes (default)."""
    return cache_result(ttl=ttl)


def clear_cache():
    """Clear all cached data."""
    global _CACHE
    count = len(_CACHE)
    _CACHE.clear()
    logger.info(f"Cleared {count} items from cache")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    if not _CACHE:
        return {'size': 0, 'items': []}
    
    current_time = time.time()
    
    items = []
    for key, (timestamp, _) in _CACHE.items():
        age = current_time - timestamp
        items.append({
            'key': key,
            'age_seconds': round(age, 1)
        })
    
    return {
        'size': len(_CACHE),
        'items': items
    }


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    @cache_result(ttl=5)  # 5 second cache
    async def expensive_operation(n: int):
        print(f"Computing {n}...")
        await asyncio.sleep(1)  # Simulate slow operation
        return n * 2
    
    async def test():
        print("First call:")
        result1 = await expensive_operation(5)  # Takes 1s
        print(f"Result: {result1}")
        
        print("\nSecond call (cached):")
        result2 = await expensive_operation(5)  # Instant!
        print(f"Result: {result2}")
        
        print("\nWait 6 seconds...")
        await asyncio.sleep(6)
        
        print("\nThird call (cache expired):")
        result3 = await expensive_operation(5)  # Takes 1s again
        print(f"Result: {result3}")
    
    asyncio.run(test())
```

#### 2.2 Add Caching to Weather Fetcher

Edit: `walters_analyzer/weather_fetcher.py`

```python
# Add at top:
from walters_analyzer.core.cache import cache_weather_data

# Add decorator to main function:
@cache_weather_data(ttl=1800)  # Cache for 30 minutes
async def fetch_game_weather(
    stadium: str,
    location: str,
    is_dome: bool = False,
    game_date: Optional[str] = None,
    game_time: Optional[str] = None,
    sport: str = "nfl",
    use_cache: bool = True  # Keep for backward compatibility
):
    # ... existing code
```

#### 2.3 Test

```bash
# Test caching
uv run python -c "
import asyncio
from walters_analyzer.weather_fetcher import fetch_game_weather

async def test():
    # First call - hits API
    print('Call 1:')
    w1 = await fetch_game_weather('Highmark Stadium', 'Buffalo, NY')
    
    # Second call - uses cache (instant!)
    print('Call 2 (cached):')
    w2 = await fetch_game_weather('Highmark Stadium', 'Buffalo, NY')
    
    print(f'Same result: {w1 == w2}')

asyncio.run(test())
"
```

---

## Step 3: Consolidate Models (5 minutes)

### What You're Adding
- Single file with all data structures
- Better code organization
- Easier to find and maintain models

### Implementation

#### 3.1 Create Models File

Create file: `walters_analyzer/core/__init__.py`

```python
"""Core Billy Walters analysis components."""

# Make submodules importable
__all__ = ['models', 'http_client', 'cache']
```

Create file: `walters_analyzer/core/models.py`

```python
"""
Data models for Billy Walters Sports Analyzer.
All dataclasses and enums in one place.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class BetType(Enum):
    """Types of bets supported."""
    SPREAD = "spread"
    TOTAL = "total"
    MONEYLINE = "moneyline"
    TEASER = "teaser"
    PARLAY = "parlay"


# ============================================================================
# Power Ratings
# ============================================================================

@dataclass
class TeamRating:
    """Power rating for a single team."""
    team: str
    sport: str
    rating: float = 0.0
    games_played: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    rating_history: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'team': self.team,
            'sport': self.sport,
            'rating': round(self.rating, 2),
            'games_played': self.games_played,
            'last_updated': self.last_updated,
            'rating_history': [round(r, 2) for r in self.rating_history[-10:]]
        }


@dataclass
class GameResult:
    """Represents a completed game for rating updates."""
    team: str
    opponent: str
    team_score: int
    opponent_score: int
    is_home: bool
    sport: str
    date: str
    injury_differential: float = 0.0

    @property
    def score_differential(self) -> int:
        return self.team_score - self.opponent_score


# ============================================================================
# Situational Factors (S/W/E)
# ============================================================================

@dataclass
class GameContext:
    """Context information for S/W/E factor calculations."""
    team: str
    opponent: str
    sport: str
    is_home: bool
    game_date: str
    
    # Situational factors
    team_rest_days: int = 7
    opponent_rest_days: int = 7
    travel_miles: int = 0
    is_divisional: bool = False
    is_conference: bool = False
    is_rivalry: bool = False
    is_revenge: bool = False
    team_ats_last_5: int = 0
    opponent_ats_last_5: int = 0
    
    # Weather factors
    wind_speed_mph: float = 0.0
    precipitation_prob: float = 0.0
    precipitation_type: Optional[str] = None
    temperature_f: float = 70.0
    is_dome: bool = False
    
    # Emotional factors
    playoff_implications: str = "none"
    coaching_change: bool = False
    injury_motivation: bool = False
    public_betting_pct: Optional[float] = None


# ============================================================================
# Injuries
# ============================================================================

@dataclass
class InjuryReport:
    """Player injury information."""
    player_name: str
    position: str
    injury_type: str
    status: str
    point_value: float = 0.0
    replacement_value: float = 0.0
    severity: str = "MODERATE"
    confidence: float = 0.5
    source: str = "Manual"
    prognosis: str = ""
    timestamp: Optional[datetime] = None


# ============================================================================
# Betting
# ============================================================================

@dataclass
class BetRecommendation:
    """Complete bet recommendation with sizing."""
    game: str
    bet_type: BetType
    side: str
    line: float
    price: int
    edge_percentage: float
    stars: float
    confidence: str
    bankroll: float
    bet_amount: float
    bet_percentage: float
    kelly_full: float
    kelly_fraction: float
    risk_of_ruin: float
    expected_value: float
    reasoning: str

    def to_dict(self) -> dict:
        return {
            'game': self.game,
            'bet_type': self.bet_type.value,
            'side': self.side,
            'line': self.line,
            'price': self.price,
            'edge_percentage': round(self.edge_percentage, 2),
            'stars': self.stars,
            'confidence': self.confidence,
            'bet_amount': round(self.bet_amount, 2),
            'expected_value': round(self.expected_value, 2),
            'reasoning': self.reasoning
        }


@dataclass
class KeyNumberAnalysis:
    """Key number analysis results."""
    predicted_spread: float
    market_spread: float
    key_numbers_crossed: List[float]
    edge_percentage: float
    edge_value: float


@dataclass
class ComprehensiveAnalysis:
    """Complete analysis of a game."""
    game: str
    sport: str
    away_team: str
    home_team: str
    away_rating: float
    home_rating: float
    predicted_spread: float
    predicted_total: float
    swe_spread_adjustment: float
    swe_total_adjustment: float
    swe_summary: str
    swe_details: dict
    market_spread: float
    market_total: Optional[float]
    spread_price: int
    total_price: int
    key_number_analysis: KeyNumberAnalysis
    edge_percentage: float
    recommendation: Optional[BetRecommendation]
    should_bet: bool
    reasoning: str

    def to_dict(self) -> dict:
        return {
            'game': self.game,
            'sport': self.sport,
            'power_ratings': {
                'away_rating': round(self.away_rating, 2),
                'home_rating': round(self.home_rating, 2),
                'predicted_spread': round(self.predicted_spread, 1),
            },
            'edge_percentage': self.edge_percentage,
            'should_bet': self.should_bet,
            'recommendation': self.recommendation.to_dict() if self.recommendation else None
        }
```

#### 3.2 Update Imports (Gradually)

You can do this gradually - old imports will still work. When you're ready:

```python
# Old way (still works):
from walters_analyzer.power_ratings import TeamRating, GameResult
from walters_analyzer.situational_factors import GameContext
from walters_analyzer.bet_sizing import BetRecommendation, BetType

# New way (preferred):
from walters_analyzer.core.models import (
    TeamRating,
    GameResult,
    GameContext,
    BetRecommendation,
    BetType,
    InjuryReport,
    KeyNumberAnalysis
)
```

---

## ✅ Verification Checklist

After implementing all 3 upgrades:

- [ ] HTTP client works (weather fetches successfully)
- [ ] Caching reduces API calls (second call is instant)
- [ ] Models file created (can import from core.models)
- [ ] All existing tests pass
- [ ] CLI commands still work

```bash
# Run full test suite
pytest tests/ -v

# Test CLI commands
uv run walters-analyzer scrape-weather --card cards/wk-card-2025-10-31.json
uv run walters-analyzer weekly-nfl-update --week 10

# Check performance improvement
python -m cProfile -s cumtime scripts/demo_weather.py
```

---

## 📊 Expected Improvements

### Before Upgrades:
- Weather API call: ~500ms per call
- 10 weather calls: ~5 seconds
- HTTP connections: Created/closed each call
- API costs: Every call charged

### After Upgrades:
- First weather call: ~500ms
- Next 9 calls (cached): ~1ms each
- 10 weather calls: ~510ms (10x faster!)
- HTTP connections: Reused via pooling
- API costs: Only 1 charge for 30 minutes

---

## Next Steps

After these 3 quick wins, consider:

1. **ProFootballDoc Integration** (1-2 hours)
   - Better injury analysis
   - Medical expert insights

2. **Module Reorganization** (1-2 days)
   - Move files to core/research/cli structure
   - Cleaner long-term architecture

3. **Slash Commands** (optional, 1 hour)
   - AI integration features
   - Natural language interface

---

## Need Help?

If you run into issues:

1. Check the logs: `tail -f *.log`
2. Test individual components: `pytest tests/test_specific.py -v`
3. Rollback if needed: `git reset --hard HEAD`

**Questions? Let me know and I can help debug!** 🚀

