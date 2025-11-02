# Code Patterns Comparison: Current vs vNext

## Side-by-Side Pattern Analysis

### 1. HTTP Requests

#### ❌ Current Pattern (Scattered)
```python
# In weather_fetcher.py
async with aiohttp.ClientSession() as session:
    async with session.get(url, params=params) as response:
        data = await response.json()

# In injury scraper
async with aiohttp.ClientSession() as session:
    async with session.get(injury_url) as response:
        html = await response.text()

# Problem: Multiple sessions, no connection pooling, repeated code
```

#### ✅ vNext Pattern (Centralized)
```python
# core/http_client.py - SINGLETON SESSION
_CLIENT_SESSION: Optional[aiohttp.ClientSession] = None

async def async_get(url: str, params: Optional[Dict] = None):
    session = await get_client_session()  # Reuses same session
    try:
        async with session.get(url, params=params) as response:
            return {'status': response.status, 'data': await response.json()}
    except Exception as e:
        return {'status': 0, 'error': str(e)}

# Usage everywhere:
from walters_analyzer.core.http_client import async_get

data = await async_get(weather_url, params={'city': 'Buffalo'})
```

**Benefits:**
- Connection pooling (faster)
- Consistent error handling
- Easy to add retries, timeouts
- Single place to update HTTP logic

---

### 2. Caching

#### ❌ Current Pattern (No Caching)
```python
async def fetch_weather_data(city: str):
    # Always calls API, even if just called 1 minute ago
    response = await async_get(weather_api_url, params={'city': city})
    return response

# Every call = new API request = costs money + slow
```

#### ✅ vNext Pattern (Decorator-Based)
```python
from walters_analyzer.core.cache import cache_weather_data

@cache_weather_data(ttl=1800)  # Cache for 30 minutes
async def fetch_weather_data(city: str):
    response = await async_get(weather_api_url, params={'city': city})
    return response

# First call: Fetches from API
# Calls within 30 min: Returns cached data
# After 30 min: Fetches fresh data
```

**Benefits:**
- Saves API costs
- Faster response times
- Respects API rate limits
- Simple to implement

**Real Impact:**
```python
# Without caching:
await fetch_weather_data("Buffalo")  # API call
await fetch_weather_data("Buffalo")  # API call (wasted)
await fetch_weather_data("Buffalo")  # API call (wasted)

# With caching:
await fetch_weather_data("Buffalo")  # API call
await fetch_weather_data("Buffalo")  # Cached (instant)
await fetch_weather_data("Buffalo")  # Cached (instant)
```

---

### 3. Data Models

#### ❌ Current Pattern (Scattered)
```python
# In power_ratings.py
@dataclass
class TeamRating:
    team: str
    sport: str
    rating: float = 0.0

# In situational_factors.py
@dataclass
class GameContext:
    team: str
    opponent: str
    # ...

# In bet_sizing.py
@dataclass
class BetRecommendation:
    game: str
    stars: float
    # ...

# Problem: Models spread across many files, hard to find
```

#### ✅ vNext Pattern (Centralized)
```python
# core/models.py - ALL MODELS HERE
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class TeamRating:
    team: str
    sport: str
    rating: float = 0.0
    games_played: int = 0
    rating_history: List[float] = field(default_factory=list)

@dataclass
class GameContext:
    team: str
    opponent: str
    sport: str
    # ... all context fields

@dataclass
class BetRecommendation:
    game: str
    bet_type: BetType
    stars: float
    edge_percentage: float
    # ... all bet fields

@dataclass
class InjuryReport:
    player_name: str
    position: str
    injury_type: str
    status: str
    point_value: float = 0.0
    severity: str = "MODERATE"
    confidence: float = 0.5
    source: str = "Manual"
    timestamp: Optional[datetime] = None

# Usage:
from walters_analyzer.core.models import (
    TeamRating, GameContext, BetRecommendation, InjuryReport
)
```

**Benefits:**
- Single source of truth
- Easy to find all data structures
- Better IDE autocomplete
- Easier to add shared functionality

---

### 4. Module Organization

#### ❌ Current Structure (Flat)
```
walters_analyzer/
├── analyzer.py              # Everything mixed together
├── power_ratings.py
├── situational_factors.py
├── bet_sizing.py
├── key_numbers.py
├── clv_tracker.py
├── weather_fetcher.py       # Data fetching
├── weather_pipeline.py
├── nfl_data.py
├── cli.py                   # CLI
└── wkcard.py
```

**Problem:** Hard to understand what each file does at a glance

#### ✅ vNext Structure (Modular)
```
walters_analyzer/
├── core/                    # CALCULATION ENGINE
│   ├── __init__.py
│   ├── models.py           # All data structures
│   ├── analyzer.py         # Main analyzer
│   ├── power_ratings.py    # Power rating calculations
│   ├── calculator.py       # Core math
│   ├── point_analyzer.py   # Edge/star calculations
│   ├── bankroll.py         # Money management
│   ├── cache.py            # Caching system
│   └── http_client.py      # HTTP abstraction
│
├── research/                # DATA GATHERING
│   ├── __init__.py
│   ├── engine.py           # Main research coordinator
│   ├── weather.py          # Weather fetching
│   ├── injuries.py         # Injury research
│   ├── profootballdoc.py   # Medical analysis
│   ├── highlightly.py      # Sports data API
│   ├── analyst.py          # Research analysis
│   └── x_feed.py           # Social media (optional)
│
├── cli/                     # USER INTERFACE
│   ├── __init__.py
│   ├── commands.py         # CLI commands
│   ├── slash_commands.py   # AI integration
│   └── interactive.py      # Interactive mode
│
└── backtest/                # BACKTESTING (keep as is)
    ├── __init__.py
    ├── engine.py
    ├── metrics.py
    └── validation.py
```

**Benefits:**
- Clear separation of concerns
- Easy to navigate
- New developers understand structure immediately
- Can work on one area without affecting others

---

### 5. Error Handling

#### ❌ Current Pattern (Basic)
```python
async def fetch_weather_data(city: str):
    try:
        response = await async_get(url, params={'city': city})
        return response['main']['temp']
    except Exception as e:
        print(f"Error: {e}")
        return None
```

#### ✅ vNext Pattern (Comprehensive)
```python
import logging

logger = logging.getLogger(__name__)

async def fetch_weather_data(
    city: str,
    date: str = None,
    *,
    state: Optional[str] = None,
    country_code: str = "US",
) -> Dict[str, Any]:
    """
    Enhanced weather data fetching with fallbacks.
    
    Args:
        city: City name
        date: Optional date
        state: Optional state (improves accuracy)
        country_code: Country (default US)
    
    Returns:
        Weather data dict or error dict
    """
    weather_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not weather_key:
        logger.warning("Weather API key not configured")
        return {
            "temperature": None,
            "conditions": "Weather API not configured",
            "source": "Educational framework"
        }
    
    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {'q': city, 'appid': weather_key, 'units': 'imperial'}
        
        response = await async_get(url, params=params)
        
        if response['status'] == 200:
            weather = response['data']
            return {
                "temperature": weather['main']['temp'],
                "conditions": weather['weather'][0]['description'],
                "humidity": weather['main']['humidity'],
                "wind_speed": weather['wind'].get('speed', 0),
                "source": "OpenWeatherMap API"
            }
        else:
            logger.error(f"Weather API error: {response['status']}")
            return {
                "temperature": None,
                "conditions": f"Weather API error: {response['status']}",
                "source": "API Error"
            }
            
    except Exception as e:
        logger.exception(f"Weather fetch failed: {e}")
        return {
            "temperature": None,
            "conditions": f"Weather fetch failed: {e}",
            "source": "Error"
        }
```

**Benefits:**
- Proper logging for debugging
- Graceful fallbacks
- Clear error messages
- Type hints for IDE support

---

### 6. Injury Research

#### ❌ Current Pattern (Single Source)
```python
# Only ESPN injuries
async def fetch_injury_reports(team: str):
    # Scrape ESPN injury report page
    injuries = await scrape_espn_injuries(team)
    return injuries
```

#### ✅ vNext Pattern (Multiple Sources)
```python
async def comprehensive_injury_research(
    team: str, 
    include_profootballdoc: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive injury research combining multiple sources.
    """
    all_injuries = []
    sources_used = []
    
    # 1. ProFootballDoc Medical Analysis
    if include_profootballdoc:
        profootballdoc_analyses = await self.profootballdoc.fetch_team_injuries(team)
        for analysis in profootballdoc_analyses:
            injury_report = InjuryReport(
                player_name=analysis.player,
                injury_type=analysis.injury,
                severity=analysis.severity,
                confidence=analysis.confidence,
                source="ProFootballDoc",
                prognosis=analysis.prognosis
            )
            all_injuries.append(injury_report)
        sources_used.append("ProFootballDoc Medical Analysis")
    
    # 2. ESPN Injury Reports
    espn_injuries = await fetch_espn_injuries(team)
    all_injuries.extend(espn_injuries)
    sources_used.append("ESPN Injury Reports")
    
    # 3. News API Search
    news_injuries = await self._fetch_news_injuries(team)
    all_injuries.extend(news_injuries)
    sources_used.append("News API Reports")
    
    # Aggregate and analyze
    return self._generate_comprehensive_analysis(team, all_injuries, sources_used)
```

**Benefits:**
- Multiple data sources = more accuracy
- Confidence scoring per source
- Medical expert analysis (ProFootballDoc)
- Fallback if one source fails

---

### 7. CLI Interface

#### ✅ Current Pattern (Already Good!)
```python
# cli.py
def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    
    # wk-card command
    wk = sub.add_parser("wk-card")
    wk.add_argument("--file", required=True)
    wk.add_argument("--dry-run", action="store_true")
    
    # scrape-nfl-schedule command
    nfl = sub.add_parser("scrape-nfl-schedule")
    nfl.add_argument("--season", type=int, default=2025)
    # ...

# Usage:
# uv run walters-analyzer wk-card --file cards/week10.json
# uv run walters-analyzer scrape-nfl-schedule --week 10
```

**Your CLI is already excellent! No changes needed here.**

#### ➕ vNext Addition (Slash Commands for AI)
```python
# cli/slash_commands.py
class SlashCommandHandler:
    """Handler for Claude Code slash commands."""
    
    async def execute_command(self, command_text: str):
        # Parse: "/analyze Chiefs vs Bills date=2024-12-15"
        parsed = self._parse_command(command_text)
        
        if parsed['command'] == 'analyze':
            return await self.cmd_analyze(parsed['args'], parsed['options'])

# Usage in Claude/ChatGPT:
# /analyze Kansas City Chiefs vs Buffalo Bills date=2024-12-15
# /research injuries Eagles
# /update ratings
```

**Benefits:**
- Natural language interface
- AI assistant integration
- Demo/presentation friendly
- **Optional - only if you want AI features**

---

## Quick Implementation Checklist

### 🎯 Immediate Wins (1-2 hours each)

1. **Add HTTP Client** (1 hour)
   ```bash
   # Copy vNext's core/http_client.py
   # Update weather_fetcher.py to use it
   # Update injury fetchers to use it
   ```

2. **Add Caching** (1 hour)
   ```bash
   # Copy vNext's core/cache.py
   # Add @cache_weather_data decorator
   # Add @cache_injury_data decorator
   ```

3. **Consolidate Models** (2 hours)
   ```bash
   # Create walters_analyzer/core/models.py
   # Move all @dataclass definitions there
   # Update imports
   ```

### 📦 Structural Refactor (1-2 days)

4. **Create Directory Structure**
   ```bash
   mkdir -p walters_analyzer/core
   mkdir -p walters_analyzer/research
   mkdir -p walters_analyzer/cli
   ```

5. **Move Files to Core**
   ```bash
   mv walters_analyzer/power_ratings.py walters_analyzer/core/
   mv walters_analyzer/bet_sizing.py walters_analyzer/core/
   mv walters_analyzer/key_numbers.py walters_analyzer/core/
   # Update imports in analyzer.py
   ```

6. **Move Files to Research**
   ```bash
   mv walters_analyzer/weather_fetcher.py walters_analyzer/research/weather.py
   # Copy profootballdoc_fetcher.py from vNext
   ```

7. **Update Imports Everywhere**
   ```bash
   # Find/replace:
   # from walters_analyzer.power_ratings import
   # → from walters_analyzer.core.power_ratings import
   ```

### 🧪 Testing (ongoing)

8. **Run Tests After Each Change**
   ```bash
   pytest tests/
   ```

---

## Example: Adding Caching to Weather

### Before (No Caching)
```python
# walters_analyzer/weather_fetcher.py
async def fetch_game_weather(
    stadium: str,
    location: str,
    is_dome: bool = False
):
    if is_dome:
        return {"conditions": "Indoor (dome)"}
    
    # Always calls AccuWeather API
    weather = await get_accuweather_data(location)
    return weather
```

### After (With Caching)
```python
# walters_analyzer/research/weather.py
from walters_analyzer.core.cache import cache_weather_data
from walters_analyzer.core.http_client import async_get

@cache_weather_data(ttl=1800)  # Cache for 30 minutes
async def fetch_game_weather(
    stadium: str,
    location: str,
    is_dome: bool = False
):
    if is_dome:
        return {"conditions": "Indoor (dome)"}
    
    # Cached - only calls API once per 30 min per location
    weather = await get_accuweather_data(location)
    return weather
```

**Result:** 
- Same function signature
- Same return value
- But now much faster and cheaper!

---

## Summary

### What to Adopt from vNext:
1. ✅ **HTTP Client** - Easy win, big impact
2. ✅ **Caching** - Saves money, improves speed
3. ✅ **Models consolidation** - Better organization
4. ✅ **Module structure** - Long-term maintainability
5. ⚠️ **ProFootballDoc** - If you want better injury analysis
6. ❌ **Slash commands** - Only if you want AI integration

### What NOT to Change:
- Your CLI (already excellent)
- Your scrapers (already working)
- Your backtesting (unique to your project)
- Your data pipelines (production-ready)
- Your power ratings logic (correct implementation)

### Philosophy:
- **Your project is the production version**
- **vNext is the architectural refinement**
- **Cherry-pick the best patterns from each**

---

Ready to implement? Let me know which pattern you want to tackle first! 🚀

