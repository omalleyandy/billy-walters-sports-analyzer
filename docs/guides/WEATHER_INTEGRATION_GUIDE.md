# Weather Integration Guide

**Critical Document**: This guide prevents a major class of bugs that plagued the weather data pipeline.

---

## The Problem We Solved

### What Went Wrong (November 2025)

The original weather integration extracted **POI (point of interest) location keys** from ESPN's embedded AccuWeather URLs:

```
ESPN URL: https://www.accuweather.com/en/us/delaware-stadium/19711/hourly-weather-forecast/209212_poi
Extract: 209212_poi ← WRONG (points to different location)
Result:  10°F (Minneapolis, not Delaware)
Impact:  Completely wrong edge calculations
```

**Root Cause**: POI keys are not authoritative. ESPN's embedded links can point to nearby locations, similar names, or outdated references.

### The Fix: Zipcode-Based Approach

Instead of extracting complex POI keys, extract the **simple, authoritative zipcode**:

```
ESPN URL: https://www.accuweather.com/en/us/delaware-stadium/19711/hourly-weather-forecast/209212_poi
Extract: 19711 ← ZIPCODE (authoritative)
Lookup:  AccuWeather postal code search → 8079_PC (correct location key)
Result:  28°F (Delaware, correct)
```

---

## Architecture: Three-Layer System

### Layer 1: ESPN Scraper
**File**: `src/data/espn_weather_scraper.py`

**Purpose**: Extract stadium zipcodes from ESPN schedule

**Method**: `ESPNWeatherLinkScraper.get_stadium_zipcodes()`

```python
# Input: ESPN schedule HTML
# Process: Find AccuWeather links, extract ZIPCODE from URL path
# Output: {"Delaware Stadium, Newark, DE": "19711", ...}

# URL Pattern:
# /en/us/[stadium-slug]/[ZIPCODE]/hourly-weather-forecast/
#                        ↑
#                   Extract this 5-digit number
```

**Regex Pattern** (immutable):
```regex
r"/en/us/[^/]+/(\d{5})/hourly-weather-forecast"
```

**Why This Works**:
- Zipcode is embedded directly in ESPN's AccuWeather URL structure
- 5-digit format is stable and authoritative
- Can be verified independently

### Layer 2: AccuWeather Lookup
**File**: `src/scrapers/weather/accuweather.py`

**Purpose**: Convert zipcode → verified location key

**Method**: `AccuWeatherClient.get_location_key_by_zipcode(zipcode)`

```python
async def get_location_key_by_zipcode(self, zipcode: str) -> str | None:
    """
    Look up AccuWeather location key using postal code.

    Uses official AccuWeather postal code search API endpoint:
    /locations/v1/postalcodes/search?q=19711

    Returns location key from AccuWeather's official database.
    """
```

**Why This Works**:
- Official AccuWeather API (not scraped)
- Postal code is authoritative
- Returns verified location key

**Expected Output**:
```
19711 → 8079_PC (format: [number]_PC for postal codes)
```

### Layer 3: Game Analysis
**File**: `src/walters_analyzer/cli/commands/analyze.py`

**Purpose**: Orchestrate weather data fetching

**Flow**:
```
1. Extract stadium zipcode from ESPN
   ↓
2. Get location key from AccuWeather postal code API
   ↓
3. Fetch weather using verified location key
   ↓
4. Calculate Billy Walters W-Factor
```

---

## Implementation Details

### Adding a New Stadium

To add a new stadium to the authoritative mapping:

**File**: `src/data/stadium_accuweather_keys.py`

```python
COLLEGE_STADIUM_KEYS = {
    "Delaware Stadium": {
        "city": "Newark",
        "state": "DE",
        "zipcode": "19711",
        "location_key": "8079_PC",  # From AccuWeather postal code API
    },
    # Add new stadiums here
    "New Stadium Name": {
        "city": "City Name",
        "state": "ST",
        "zipcode": "12345",
        "location_key": "VERIFIED_KEY",
    },
}
```

**Process to Verify**:
1. Find stadium zipcode (postal code)
2. Call AccuWeather postal code search API
3. Verify returned location key with current weather
4. Test in game analysis to confirm correct temperature

---

## Validation Procedures

### Before Any Changes

1. **Verify ESPN URL Pattern**
   ```python
   # Check that ESPN still uses format:
   # /en/us/[stadium]/[ZIPCODE]/hourly-weather-forecast/

   # If format changes, update regex in:
   # src/data/espn_weather_scraper.py line 92
   ```

2. **Verify AccuWeather API**
   ```python
   # Confirm postal code search endpoint still works:
   # GET /locations/v1/postalcodes/search?q=19711

   # If API changes, update:
   # src/scrapers/weather/accuweather.py get_location_key_by_zipcode()
   ```

3. **Test with Known Stadium**
   ```bash
   python -m walters_analyzer.cli.main analyze game "UTEP" "Delaware" \
     --sport ncaaf

   # Expected output:
   # Found: Delaware Stadium, Newark, DE (Zipcode: 19711)
   # Location key: 8079_PC
   # Temperature: 28.0°F (or current actual temp)
   ```

### During Game Analysis

Every game analysis should print:
```
Calculating W-factors (weather)...
Found: [Stadium Name] (Zipcode: [ZIP])
Location key: [KEY]
Temperature: [TEMP]°F
Billy Walters Cold Bonus (Home): +[ADJ] pts
```

**Red Flags** (these indicate problems):
- ❌ "ESPN weather links unavailable" (ESPN scraper failed)
- ❌ No temperature shown (location key lookup failed)
- ❌ "Found: [Stadium] (ESPN)" (fallback to unreliable method)
- ❌ Unexpected temperature (wrong location key used)

### Regression Testing

Before committing weather-related changes:

```bash
# Test multiple stadiums across seasons
python -m pytest tests/test_weather_integration.py -v

# Manual verification of known stadiums
python -c "
import asyncio
from src.data.espn_weather_scraper import ESPNWeatherLinkScraper

async def test():
    zips = await ESPNWeatherLinkScraper.get_stadium_zipcodes('cfb')
    # Should find Delaware Stadium with zipcode 19711
    assert zips.get('Delaware Stadium, Newark, DE') == '19711'

asyncio.run(test())
"
```

---

## Common Issues & Solutions

### Issue: "ESPN weather links unavailable"

**Cause**: ESPN scraper failed to fetch or parse schedule

**Solution**:
```python
# Check:
1. ESPN URL is still accessible: curl https://www.espn.com/college-football/schedule
2. Regex pattern still matches: grep -r "hourly-weather-forecast" [html]
3. Network connectivity

# Debug:
python -c "
import asyncio
from src.data.espn_weather_scraper import ESPNWeatherLinkScraper

async def debug():
    html = await ESPNWeatherLinkScraper.fetch_schedule_html('cfb')
    if html:
        print(f'Fetched {len(html)} bytes')
    else:
        print('Failed to fetch ESPN schedule')

asyncio.run(debug())
"
```

### Issue: Location key not found for stadium

**Cause**: Stadium name doesn't match ESPN's stadium name format

**Solution**:
```python
# Get exact stadium name from ESPN:
import asyncio
from src.data.espn_weather_scraper import ESPNWeatherLinkScraper

async def find_stadium():
    zips = await ESPNWeatherLinkScraper.get_stadium_zipcodes('cfb')
    for stadium in sorted(zips.keys()):
        if 'delaware' in stadium.lower():
            print(f"Found: {stadium}")

asyncio.run(find_stadium())
```

### Issue: Temperature seems wrong

**Cause**: Wrong location key being used

**Solution**:
```python
# Verify location key with AccuWeather API directly:
python -c "
import asyncio
from src.scrapers.weather.accuweather import AccuWeatherClient

async def verify():
    client = AccuWeatherClient()
    await client.connect()

    # Test zipcode lookup
    key = await client.get_location_key_by_zipcode('19711')
    print(f'Zipcode 19711 → Location Key: {key}')

    # Verify weather
    if key:
        weather = await client.get_weather_by_location_key(key)
        print(f'Temperature: {weather.get(\"temperature\")}°F')

    await client.close()

asyncio.run(verify())
"
```

---

## Design Principles (Never Violate)

1. **Never Extract POI Keys from URLs**
   - ❌ `209212_poi` (points of interest change)
   - ✅ `19711` (zipcode is stable)

2. **Always Use Official APIs**
   - ❌ Parsing ESPN's embedded location keys
   - ✅ Using AccuWeather's official postal code search

3. **Validate Every New Stadium**
   - ❌ Adding stadiums without testing
   - ✅ Verify zipcode → location key → weather

4. **Never Fabricate Data**
   - ❌ If ESPN scraper fails, don't guess
   - ✅ Report failure, user must fix data source

5. **Simple is Better Than Complex**
   - ❌ Complex regex for POI key extraction
   - ✅ Simple regex for 5-digit zipcode

---

## References

### Related Files
- Weather scraper: `src/data/espn_weather_scraper.py`
- AccuWeather client: `src/scrapers/weather/accuweather.py`
- Game analysis: `src/walters_analyzer/cli/commands/analyze.py`
- Stadium mapping: `src/data/stadium_accuweather_keys.py`

### Test Files
- Weather integration tests: `tests/test_weather_integration.py`
- Game analysis tests: `tests/test_analyze_command.py`

### Billy Walters Reference
- W-Factor specification: `docs/guides/methodology/advanced-master-class-section-3.md` (lines 154-175)
- Edge detection: `docs/guides/EDGE_DETECTOR_WORKFLOW.md`

---

## Change Log

### November 29, 2025 - MAJOR REFACTOR
- Replaced POI-based extraction with zipcode-based approach
- Added `get_location_key_by_zipcode()` to AccuWeatherClient
- Implemented three-layer architecture for weather data
- Created this guide to prevent future issues

**Commit**: `fe5a94c - refactor: Replace POI-based weather lookup with zipcode approach`

---

## Future Considerations

### If ESPN Changes URL Structure

Update the regex in `espn_weather_scraper.py`:

```python
# Current pattern (as of Nov 2025):
match = re.search(r"/en/us/[^/]+/(\d{5})/hourly-weather-forecast", href)

# If ESPN changes to different format, update here
# Always verify pattern with real ESPN schedule URL before deploying
```

### If AccuWeather API Changes

The postal code search endpoint is AccuWeather's standard. If it changes:

1. Check AccuWeather API documentation
2. Update `get_location_key_by_zipcode()` method
3. Test with known zipcodes (e.g., 19711 → 8079_PC)
4. Run full test suite before deploying

### Adding Support for Other Sports

The zipcode-based approach works for any sport:

```python
# For NFL stadiums, same process:
NFL_STADIUM_KEYS = {
    "FedExForum": {
        "city": "Foxborough",
        "state": "MA",
        "zipcode": "02035",
        "location_key": "339739",  # Verified
    },
}

# ESPN has weather links for NFL too:
# https://www.espn.com/nfl/schedule
```

---

**Last Updated**: November 29, 2025
**Status**: Complete and Production Ready
**Maintainer**: Claude Code
