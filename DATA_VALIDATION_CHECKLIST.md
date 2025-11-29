# Data Validation Checklist

**Purpose**: Prevent data quality issues before they cause incorrect analysis

**When to Use**:
- Before running weekly edge detection
- When integrating new data source
- Before major feature release
- When fixing data-related bugs

---

## Pre-Analysis Validation

### Weather Data (CRITICAL)
- [ ] ESPN scraper successfully fetches latest schedule
  ```bash
  python -c "
  import asyncio
  from src.data.espn_weather_scraper import ESPNWeatherLinkScraper
  async def test():
      zips = await ESPNWeatherLinkScraper.get_stadium_zipcodes('cfb')
      print(f'Found {len(zips)} stadiums')
      assert len(zips) > 0, 'No stadiums found'
  asyncio.run(test())
  "
  ```

- [ ] Zipcode extraction pattern still valid
  - Verify ESPN URL format: `/en/us/[stadium]/[ZIPCODE]/hourly-weather-forecast/`
  - If format changed, update regex in `espn_weather_scraper.py` line 92

- [ ] AccuWeather postal code API works
  ```bash
  python -c "
  import asyncio
  from src.scrapers.weather.accuweather import AccuWeatherClient
  async def test():
      client = AccuWeatherClient()
      await client.connect()
      key = await client.get_location_key_by_zipcode('19711')
      print(f'Zipcode 19711 → {key}')
      assert key, 'Failed to lookup location key'
      await client.close()
  asyncio.run(test())
  "
  ```

- [ ] Known stadiums return expected temperatures
  ```bash
  # Test Delaware Stadium (should be in range -10°F to 90°F)
  python -m walters_analyzer.cli.main analyze game "UTEP" "Delaware" --sport ncaaf

  # Verify output shows:
  # - Found: Delaware Stadium, Newark, DE (Zipcode: 19711)
  # - Location key: 8079_PC
  # - Temperature: [valid number]°F
  ```

- [ ] No fallback to ESPN-scraper method in logs
  - Search logs for: `Found: [Stadium] (ESPN)`
  - Should always be: `Zipcode-based lookup` (authoritative method)

### Power Ratings Data
- [ ] Latest power ratings file exists
  ```bash
  ls -la data/power_ratings/ncaaf_2025_week_*.json | tail -1
  ls -la data/power_ratings/nfl_2025_week_*.json | tail -1
  ```

- [ ] Power ratings are reasonable
  - Ratings should be in range: -20 to +20
  - Most teams should be between -5 and +10

- [ ] All required teams present
  ```python
  python -c "
  import json
  with open('data/power_ratings/ncaaf_2025_week_13.json') as f:
      data = json.load(f)
  print(f'Loaded {len(data[\"ratings\"])} teams')
  assert len(data['ratings']) > 100, 'Missing teams'
  "
  ```

### Odds Data (Overtime.ag)
- [ ] Latest odds file exists
  ```bash
  ls -la output/overtime/ncaaf/pregame/ncaaf_odds_*.json | tail -1
  ls -la output/overtime/nfl/pregame/nfl_odds_*.json | tail -1
  ```

- [ ] Odds contain expected fields
  ```python
  python -c "
  import json
  with open('output/overtime/ncaaf/pregame/ncaaf_odds_latest.json') as f:
      data = json.load(f)
  game = data['games'][0]
  assert 'spread' in game
  assert 'total' in game
  assert 'away_team' in game
  print(f'Loaded {len(data[\"games\"])} games')
  "
  ```

- [ ] Odds are reasonable
  - Spreads: typically -20 to +20
  - Totals: typically 20 to 75+ points
  - Moneyline odds: ±100 to ±500

### Schedule Data
- [ ] Current week schedule exists
  ```bash
  python -c "
  from src.walters_analyzer.utils.schedule_validator import get_current_week
  week = get_current_week()
  print(f'Current week: {week}')
  "
  ```

- [ ] All games in schedule have required fields
  ```python
  python -c "
  import json
  with open('data/current/ncaaf_week_13_games.json') as f:
      games = json.load(f)
  for game in games:
      assert 'away_team' in game
      assert 'home_team' in game
      assert 'game_time' in game
      assert 'venue' in game
  print(f'Validated {len(games)} games')
  "
  ```

---

## Edge Detection Validation

### Pre-Detection Checks
- [ ] Power ratings loaded successfully
  - Check console output: `[green]Loaded X power ratings[/green]`

- [ ] Weather data available for all stadiums
  - Check console output: `Found: [Stadium] (Zipcode: [ZIP])`
  - Not: `ESPN weather links unavailable`

- [ ] Odds matched for all games
  - Check console output: `[green][OK] Found market odds[/green]`
  - Not: `[WARNING] Odds not found`

### During Detection
- [ ] Check for any warning messages
  ```
  ❌ WARNING: Insufficient data
  ❌ ERROR: Missing power rating
  ❌ No temperature data
  ```

- [ ] S-Factors calculated
  ```
  ✓ Divisional game detection working
  ✓ Travel penalty calculated
  ✓ Rest advantage assessed
  ```

- [ ] W-Factors applied correctly
  ```
  ✓ Temperature adjustment present
  ✓ Billy Walters cold bonus calculated
  ✓ Wind/precipitation impact considered
  ```

### Edge Results Validation
- [ ] Edges are reasonable
  - Min edge: ≥ 3.5 pts
  - Max edge: ≤ 30 pts (sanity check)
  - Most edges: 5-15 pts range

- [ ] Edge breakdown makes sense
  - Power differential reasonable
  - S/W factors in expected ranges
  - Injury adjustments minor (unless major injuries)

---

## Data Quality Metrics

### Per-Game Checklist
For each analyzed game:

- [ ] **Power Ratings**
  - Away team rating: exists and reasonable (-5 to +10)
  - Home team rating: exists and reasonable (-5 to +10)
  - Spread from ratings: mathematically correct (home - away + HFA)

- [ ] **Weather Data**
  - Temperature: exists and in valid range (-50°F to 120°F)
  - Zipcode correctly extracted from ESPN URL
  - Location key verified through AccuWeather API
  - W-Factor adjustment applied per Billy Walters spec

- [ ] **Odds Data**
  - Spread: reasonable for sport/teams (-25 to +25)
  - Total: reasonable for sport (-10 to +100)
  - Moneyline: plausible odds (-1000 to +1000)

- [ ] **Edge Calculation**
  - Our line = home power - away power + HFA + adjustments
  - Edge = our line - market spread
  - Edge strength classification matches point value
  - Recommended bet is consistent with edge direction

---

## Common Validation Failures & Fixes

### "Temperature way too low (10°F)"
**Check**: Is zipcode being correctly extracted and looked up?
```python
python -c "
import asyncio
from src.data.espn_weather_scraper import ESPNWeatherLinkScraper
from src.scrapers.weather.accuweather import AccuWeatherClient

async def debug():
    # Get zipcodes
    zips = await ESPNWeatherLinkScraper.get_stadium_zipcodes('cfb')
    delaware_zip = zips.get('Delaware Stadium, Newark, DE')
    print(f'Delaware zipcode: {delaware_zip}')

    # Lookup location key
    client = AccuWeatherClient()
    await client.connect()
    key = await client.get_location_key_by_zipcode(delaware_zip)
    print(f'Location key: {key}')

    # Get weather
    weather = await client.get_weather_by_location_key(key)
    print(f'Temperature: {weather.get(\"temperature\")}°F')

    await client.close()

asyncio.run(debug())
"
```

### "No weather data available"
**Check**: Is ESPN scraper working?
```bash
python -c "
import asyncio
from src.data.espn_weather_scraper import ESPNWeatherLinkScraper

async def test():
    zips = await ESPNWeatherLinkScraper.get_stadium_zipcodes('ncaaf')
    if not zips:
        print('FAILED: ESPN scraper returned no zipcodes')
    else:
        print(f'SUCCESS: Found {len(zips)} stadiums')
        # Show first few
        for stadium, zipcode in list(zips.items())[:3]:
            print(f'  {stadium}: {zipcode}')

asyncio.run(test())
"
```

### "Missing power ratings for team"
**Check**: Is latest power rating file available?
```bash
ls -la data/power_ratings/ncaaf_2025_week_*.json | tail -1

# File should be less than 1 day old for current week
```

### "Odds not found for game"
**Check**: Is Overtime.ag API working?
```bash
python -c "
import asyncio
from src.scrapers.overtime.api_client import OvertimeApiClient

async def test():
    client = OvertimeApiClient()
    games = await client.fetch_games(
        sport_type='Football',
        sport_sub_type='College Football'
    )
    print(f'Found {len(games)} games from Overtime.ag')

asyncio.run(test())
"
```

---

## Weekly Validation Routine

**When**: Every Tuesday before edge detection
**Time**: ~5 minutes

1. **Data Freshness Check** (1 min)
   ```bash
   ls -la data/power_ratings/ncaaf_2025_week_*.json | tail -1
   ls -la output/overtime/ncaaf/pregame/ncaaf_odds_*.json | tail -1
   ```

2. **Weather System Check** (2 min)
   ```bash
   python -c "
   import asyncio
   from src.data.espn_weather_scraper import ESPNWeatherLinkScraper
   async def test():
       zips = await ESPNWeatherLinkScraper.get_stadium_zipcodes('ncaaf')
       assert len(zips) > 100, f'Only found {len(zips)} stadiums'
       print(f'✓ ESPN scraper: {len(zips)} stadiums')
   asyncio.run(test())
   "
   ```

3. **Sample Game Analysis** (2 min)
   ```bash
   python -m walters_analyzer.cli.main analyze game "Ohio State" "Michigan" \
     --sport ncaaf --verbose

   # Verify output shows:
   # - Power ratings loaded
   # - Weather data found
   # - Odds matched
   # - Edge detected (or no edge, both OK)
   ```

---

## Validation Automation

### GitHub Actions / CI Pipeline
Add to CI checks:
```yaml
- name: Validate Weather Data
  run: |
    python -c "
    import asyncio
    from src.data.espn_weather_scraper import ESPNWeatherLinkScraper
    async def test():
        zips = await ESPNWeatherLinkScraper.get_stadium_zipcodes('ncaaf')
        assert len(zips) > 50, 'Insufficient stadiums'
    asyncio.run(test())
    "

- name: Validate Power Ratings
  run: |
    python -c "
    import json
    with open('data/power_ratings/ncaaf_2025_week_*.json') as f:
        data = json.load(f)
    assert len(data['ratings']) > 100, 'Missing teams'
    "
```

### Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Quick validation before allowing commit
python -m pytest tests/test_data_validation.py -q || exit 1
```

---

## References

### Weather Validation
- [Weather Integration Guide](docs/guides/WEATHER_INTEGRATION_GUIDE.md)
- [Lessons Learned](LESSONS_LEARNED_WEATHER_INTEGRATION.md)

### Data Sources
- Power Ratings: Massey Ratings
- Odds: Overtime.ag API
- Schedule: ESPN
- Weather: AccuWeather

### Related Files
- ESPN Scraper: `src/data/espn_weather_scraper.py`
- AccuWeather Client: `src/scrapers/weather/accuweather.py`
- Schedule Validator: `src/walters_analyzer/utils/schedule_validator.py`

---

**Last Updated**: November 29, 2025
**Status**: Production Ready
**Maintainer**: Claude Code
