# NFL.com API Discovery via Chrome DevTools

This guide helps you discover NFL.com's official API endpoints using Chrome DevTools reverse engineering techniques.

## Quick Start

1. Open Chrome DevTools (`F12`)
2. Go to **Network** tab
3. Filter: `XHR` or `Fetch` only
4. Navigate to NFL.com pages
5. Record API calls

---

## Target Pages & Expected APIs

### 1. Schedule API

**Page**: https://www.nfl.com/schedules/2025/REG12

**What to Look For**:
- Network calls containing `schedule`, `games`, or `week`
- JSON responses with game data
- Query parameters: `season=2025`, `week=12`

**Expected Endpoint Pattern**:
```
https://api.nfl.com/v3/shield/?query=...
https://static.www.nfl.com/liveupdate/scores/scores.json
https://feeds.nfl.com/feeds-rs/schedules/...
```

**Key Data Fields**:
- `gameId` - Unique game identifier
- `awayTeam`, `homeTeam` - Team abbrev

iations
- `gameTime` - ISO datetime
- `venue` - Stadium info
- `network` - TV broadcaster

---

### 2. Team News API

**Page**: https://www.nfl.com/teams/kansas-city-chiefs/

**What to Look For**:
- Network calls with `news`, `articles`, or `content`
- JSON with headline, summary, publish date
- Team-specific filters

**Expected Endpoint Pattern**:
```
https://api.nfl.com/v3/shield/news
https://www.nfl.com/feeds/article/...
```

**Key Data Fields**:
- `title` - Article headline
- `summary` - Brief description
- `publishedDate` - ISO timestamp
- `teamAbbreviation` - Team code
- `category` - injury, transaction, recap

---

### 3. Player Stats API

**Page**: https://www.nfl.com/stats/player-stats/

**What to Look For**:
- Calls containing `stats`, `player`, or `leaders`
- JSON with player performance metrics
- Position-specific data

**Expected Endpoint Pattern**:
```
https://api.nfl.com/v3/shield/player/{playerId}/stats
https://api.nfl.com/v3/shield/stats/...
```

**Key Data Fields**:
- `playerId` - Unique player ID
- `passingYards`, `rushingYards`, `receptions`
- `touchdowns`, `interceptions`
- Week-by-week or season totals

---

### 4. Injury Report API

**Page**: https://www.nfl.com/injuries/

**What to Look For**:
- Already have scraper: `src/data/nfl_official_injury_scraper.py`
- May have JSON API alternative to HTML scraping

**Existing Scraper**:
```python
from src.data.nfl_official_injury_scraper import NFLOfficialInjuryScraper

scraper = NFLOfficialInjuryScraper()
injuries = await scraper.scrape_injuries(week=12)
```

---

## Step-by-Step DevTools Workflow

### Step 1: Clear Network Log
```
1. Open DevTools (F12)
2. Go to Network tab
3. Click clear button (circle with slash)
```

### Step 2: Set Filters
```
1. Click "XHR" filter (only API calls)
2. OR type "api" in filter box
3. OR type "json" to find JSON responses
```

### Step 3: Navigate & Record
```
1. Go to target NFL.com page
2. Watch network calls populate
3. Look for calls with:
   - Type: xhr or fetch
   - Size: Large (indicates data payload)
   - Domain: api.nfl.com or similar
```

### Step 4: Inspect API Call
```
1. Click on API call
2. Headers tab: Copy full URL
3. Preview tab: See JSON structure
4. Response tab: Copy raw JSON
```

### Step 5: Test in Python
```python
import httpx

url = "https://api.nfl.com/..."  # From DevTools
headers = {
    "User-Agent": "Mozilla/5.0...",
    "Referer": "https://www.nfl.com/"
}

response = httpx.get(url, headers=headers)
print(response.json())
```

---

## Common NFL.com Patterns

### GraphQL Queries
NFL.com often uses GraphQL:
```
URL: https://api.nfl.com/v3/shield/
Query String: ?query=query{...}

Example:
?query=query{games(week:{season:2025,week:12}){id,awayTeam{abbr},homeTeam{abbr}}}
```

### REST Endpoints
Traditional REST APIs:
```
GET /v3/shield/schedule/{season}/{week}
GET /v3/shield/news?team=KC&limit=20
GET /v3/shield/player/{playerId}/stats
```

### Static JSON Files
Some data served as static JSON:
```
https://static.www.nfl.com/liveupdate/scores/scores.json
https://static.www.nfl.com/teams/{team}/roster.json
```

---

## Headers to Include

Always include these headers to mimic browser:

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nfl.com/",
    "Origin": "https://www.nfl.com",
}
```

---

## Testing Script

Use this to test discovered endpoints:

```python
# scripts/dev/test_nfl_com_api.py

import asyncio
import httpx

async def test_endpoint(url: str, headers: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Success: {url}")
            print(f"   Keys: {list(data.keys())}")
            return data
        except Exception as e:
            print(f"❌ Failed: {url}")
            print(f"   Error: {e}")
            return None

# Test schedule endpoint
await test_endpoint(
    "https://api.nfl.com/v3/shield/...",
    headers={...}
)
```

---

## Integration with nfl_com_client.py

Once you discover real endpoints:

1. Update `src/data/nfl_com_client.py`
2. Replace placeholder URLs with real ones
3. Adjust data parsing to match actual response structure
4. Test with `scripts/utilities/test_nfl_com_client.py`

---

## Troubleshooting

**403 Forbidden**:
- Add more headers (User-Agent, Referer, Origin)
- Check if authentication required
- Try from different IP (proxy)

**404 Not Found**:
- Endpoint pattern changed
- Check season/week format
- Verify URL structure in DevTools

**Empty Response**:
- Week/season might not have data yet
- Check current NFL calendar
- Try known past week (e.g., 2024 Week 10)

---

## Next Steps

1. **Discover Real Endpoints**: Use this guide with Chrome DevTools
2. **Update Client**: Modify `nfl_com_client.py` with real URLs
3. **Test**: Run test script to validate
4. **Integrate**: Add to `/collect-all-data` workflow

---

**Created**: 2025-11-23
**Purpose**: NFL.com API discovery for Billy Walters pipeline
**Related**: `src/data/nfl_com_client.py`, Action Network DevTools success
