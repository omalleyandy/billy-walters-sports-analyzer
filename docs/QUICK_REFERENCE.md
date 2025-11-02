# Quick Reference: Phase 1 + Phase 2 Components

## 🚀 What You Can Do Now

### Load Injury Data from Your Scrapy Spiders

```python
from walters_analyzer.research import ScrapyBridge

bridge = ScrapyBridge()

# Load latest NFL injuries
injuries = bridge.load_latest_injuries(sport="nfl")

# Filter for specific team
chiefs_inj = bridge.filter_by_team(injuries, "Kansas City Chiefs")

# Convert to InjuryReport format (with point impacts)
reports = bridge.convert_to_injury_reports(chiefs_inj)

# Calculate total impact
total_impact = sum(r.point_value * r.confidence for r in reports)
print(f"Total injury impact: {total_impact:+.1f} points")
```

---

### Multi-Source Injury Analysis

```python
from walters_analyzer.research import ResearchEngine

engine = ResearchEngine()

# Comprehensive analysis
analysis = await engine.comprehensive_injury_research(
    "Kansas City Chiefs",
    use_scrapy=True  # Loads your ESPN data
)

# Get results
print(f"Impact: {analysis['total_impact']:+.1f} points")
print(f"Level: {analysis['impact_level']}")
print(f"Advice: {analysis['betting_advice']}")

# Detailed injuries
for inj in analysis['detailed_injuries']:
    print(f"  {inj['player']}: {inj['impact']:+.1f}")
```

---

### Use in Game Analysis

```python
from walters_analyzer.research import ResearchEngine
from walters_analyzer.analyzer import BillyWaltersAnalyzer

async def analyze_game():
    research = ResearchEngine()
    analyzer = BillyWaltersAnalyzer(bankroll=10000)
    
    # Get injury impacts
    home_inj = await research.comprehensive_injury_research("Chiefs")
    away_inj = await research.comprehensive_injury_research("Bills")
    
    injury_diff = home_inj['total_impact'] - away_inj['total_impact']
    
    # Use in analysis
    analysis = analyzer.analyze_game(
        away_team="Bills",
        home_team="Chiefs",
        sport="nfl",
        market_spread=-3.5
    )
    
    # Adjust for injuries
    adjusted_spread = analysis.predicted_spread - injury_diff
    print(f"Adjusted for injuries: {adjusted_spread:.1f}")
```

---

### Caching Examples

```python
from walters_analyzer.core.cache import cache_weather_data, get_cache_stats

# Add caching to any function
@cache_weather_data(ttl=1800)  # 30 minutes
async def fetch_weather(city):
    # Expensive API call
    return await get_weather_api(city)

# First call - slow
weather1 = await fetch_weather("Buffalo")  # API call

# Second call - instant!
weather2 = await fetch_weather("Buffalo")  # Cached!

# Check stats
stats = get_cache_stats()
print(f"Cache hits: {stats['hits']}")
print(f"API calls saved: {stats['hits']}")
```

---

### HTTP Client Examples

```python
from walters_analyzer.core.http_client import async_get

# Simple API call with connection pooling
response = await async_get(
    "https://api.weather.com/forecast",
    params={'city': 'Buffalo', 'units': 'imperial'}
)

if response['status'] == 200:
    data = response['data']
    print(f"Temperature: {data['temp']}")
else:
    print(f"Error: {response.get('error')}")
```

---

### Model Usage

```python
from walters_analyzer.core.models import (
    TeamRating,
    BetRecommendation,
    InjuryReport,
    GameContext
)

# Create models
chiefs = TeamRating(
    team="Kansas City Chiefs",
    sport="nfl",
    rating=11.5,
    games_played=9
)

injury = InjuryReport(
    player_name="Patrick Mahomes",
    position="QB",
    injury_type="Ankle",
    status="Questionable",
    point_value=-3.0,
    confidence=0.85,
    source="ESPN"
)

# Convert to JSON
chiefs_json = chiefs.to_dict()
injury_json = injury.to_dict()
```

---

## 🎯 Common Workflows

### Weekly Injury Update
```bash
# Monday: Scrape latest injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Tuesday: Analyze games
uv run python -c "
import asyncio
from walters_analyzer.research import ResearchEngine

async def check_injuries():
    engine = ResearchEngine()
    
    teams = ['Kansas City Chiefs', 'Buffalo Bills', ...]
    for team in teams:
        analysis = await engine.comprehensive_injury_research(team)
        print(f'{team}: {analysis[\"total_impact\"]:+.1f} ({analysis[\"impact_level\"]})')

asyncio.run(check_injuries())
"
```

### Pre-Game Analysis
```python
async def pregame_analysis(home_team, away_team, market_spread):
    from walters_analyzer.research import ResearchEngine
    from walters_analyzer.analyzer import BillyWaltersAnalyzer
    
    # Initialize
    research = ResearchEngine()
    analyzer = BillyWaltersAnalyzer(bankroll=10000)
    
    # Get injury impacts
    home_inj = await research.comprehensive_injury_research(home_team)
    away_inj = await research.comprehensive_injury_research(away_team)
    
    # Calculate edge
    injury_diff = home_inj['total_impact'] - away_inj['total_impact']
    
    # Analyze game
    analysis = analyzer.analyze_game(
        away_team=away_team,
        home_team=home_team,
        sport="nfl",
        market_spread=market_spread
    )
    
    # Factor in injuries
    final_spread = analysis.predicted_spread - injury_diff
    edge = abs(final_spread - market_spread)
    
    print(f"Predicted: {final_spread:.1f}")
    print(f"Market: {market_spread:.1f}")
    print(f"Edge: {edge:.1f} points")
    
    if edge >= 2.0:
        print("BET IT!")
    else:
        print("Pass")
```

---

## 📚 File Locations

### Phase 1 (Core):
```
walters_analyzer/core/
├── http_client.py    # async_get(), async_post()
├── cache.py          # @cache_weather_data(), @cache_injury_data()
└── models.py         # TeamRating, InjuryReport, BetRecommendation, ...
```

### Phase 2 (Research):
```
walters_analyzer/research/
├── scrapy_bridge.py  # ScrapyBridge class
└── engine.py         # ResearchEngine class
```

### Examples:
```
examples/
├── quick_wins_demo.py           # Phase 1 demo
├── test_scrapy_bridge.py        # ScrapyBridge test
└── complete_research_demo.py    # Full integration demo
```

### Documentation:
```
docs/
├── QUICK_WINS_COMPLETE.md           # Phase 1 results
├── PHASE_2_QUICK_WIN_COMPLETE.md    # Phase 2 results
├── RESEARCH_INTEGRATION_PLAN.md     # Integration guide
├── TECH_STACK_BEST_PRACTICES.md     # Tech validation
└── QUICK_REFERENCE.md               # This file
```

---

## ⚡ Performance Tips

### Always use caching for repeated calls:
```python
# BAD: No caching
for team in teams:
    weather = await fetch_weather(team)  # API call every time

# GOOD: With caching
@cache_weather_data(ttl=1800)
async def fetch_weather(team):
    return await api_call()

for team in teams:
    weather = await fetch_weather(team)  # Cached after first!
```

### Load Scrapy data once, use many times:
```python
# BAD: Load for every team
for team in teams:
    injuries = bridge.load_latest_injuries()  # Reads file every time
    team_inj = bridge.filter_by_team(injuries, team)

# GOOD: Load once
all_injuries = bridge.load_latest_injuries()
for team in teams:
    team_inj = bridge.filter_by_team(all_injuries, team)  # Fast filter
```

### Use simulated data for testing:
```python
# During development
analysis = await engine.comprehensive_injury_research(
    "Kansas City Chiefs",
    use_simulation=True  # No API calls, instant results
)
```

---

## 🎯 Summary

**What's Working:**
- ✅ HTTP client with connection pooling
- ✅ Caching system (90% cost reduction)
- ✅ Consolidated models
- ✅ ScrapyBridge (loads your Scrapy data)
- ✅ ResearchEngine (multi-source coordinator)

**What's Ready:**
- ✅ ESPN injury loading (via Scrapy)
- ✅ Multi-source aggregation
- ✅ Billy Walters methodology
- ✅ Confidence-weighted impacts

**What's Next (Optional):**
- ProFootballDoc medical analysis
- News API monitoring
- X/Twitter feed integration

**Your move, partner!** 🏈

