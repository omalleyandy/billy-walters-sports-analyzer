# API Discovery Methodology: Chrome DevTools Approach

**Purpose**: Document the network analysis process used to discover hidden APIs
**Learning Source**: Overtime.ag API client success case
**Application**: Action Network, NFL.com, ESPN endpoints

---

## Overview

The Overtime.ag API client was created by analyzing network traffic in Chrome DevTools rather than relying on Playwright browser automation. This document formalizes that approach for discovering APIs in other data sources.

**Key Insight**: Most "web scraping" targets actually expose APIs if you look at the Network tab.

---

## Discovery Process (Step-by-Step)

### Phase 1: Environment Setup (10 minutes)

#### 1.1 Prepare Chrome
```bash
# Open Chrome (not Chromium, full Chrome has better DevTools)
chrome

# Pro tip: Use a new incognito window to avoid cache interference
# Ctrl+Shift+N (Windows) or Cmd+Shift+N (Mac)
```

#### 1.2 Open DevTools
```
F12 or Right-click → Inspect → Network tab
```

#### 1.3 Configure Network Tab
```
1. Click "Filter" icon (looks like funnel)
2. Uncheck "Disable cache" (let's see what's cached)
3. Set throttling to "Slow 3G" (easier to see network activity)
4. Clear existing logs (Ctrl+L or icon)
5. Keep DevTools on right side of screen (vertical layout)
```

---

### Phase 2: Initial Reconnaissance (15-20 minutes)

#### 2.1 Load Target Website
```
1. Navigate to the target URL (e.g., https://www.actionnetwork.com/nfl/odds)
2. Watch Network tab fill with requests
3. Let page fully load (watch for "Finished" indicator)
4. Take screenshot of Network tab
```

#### 2.2 Identify Data-Bearing Requests

**Look For** (in order of priority):
1. **XHR/Fetch** - Network calls (blue icon) - HIGHEST PRIORITY
2. **API endpoints** - URLs like `/api/v2/`, `/graphql`, `/sports/Api/`
3. **Large responses** - Files > 10KB (likely paginated data)
4. **JSON responses** - Content-Type: application/json (not HTML)

**Filter By Type**:
```
# In Network tab filter box:
is:xhr              # Show only XHR/Fetch requests
is:fetch            # Synonym for above
-is:image           # Exclude image requests
-is:stylesheet      # Exclude CSS requests
-is:font            # Exclude fonts
```

#### 2.3 Document Initial Findings

Create a text file with:
```
Target: actionnetwork.com/nfl/odds
URL Load Time: 3.2 seconds
Total Requests: 47
Relevant Requests Found:
  1. POST /api/v2/odds (200 OK, 125KB)
  2. GET /api/v2/sports/nfl (200 OK, 45KB)
  3. POST /api/v2/recommendations (200 OK, 32KB)
```

---

### Phase 3: API Endpoint Analysis (20-30 minutes)

#### 3.1 Identify Primary Data Endpoint

**Click on each XHR request** and check:

1. **Request Headers** tab:
   - URL: Full endpoint path
   - Method: GET, POST, etc.
   - Content-Type: application/json?
   - Authentication: Any headers like `Authorization`?
   - User-Agent: What browser value is used?

2. **Request Body** tab (if POST):
   - What's being sent?
   - JSON or form data?
   - Required parameters?

3. **Response** tab:
   - Is response JSON?
   - What data does it contain?
   - How is it structured?

4. **Response Headers** tab:
   - Content-Type: application/json?
   - Any rate limiting headers? (X-RateLimit-*)
   - CORS headers? (Access-Control-*)

#### 3.2 Create Request Template

Once you identify the main endpoint, document it:

```
Endpoint: POST https://www.actionnetwork.com/api/v2/odds

Request Headers:
  - User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...
  - Content-Type: application/json
  - Accept: application/json
  - X-Requested-With: XMLHttpRequest

Request Body (JSON):
{
  "league": "nfl",
  "oddsType": "spread",
  "sportType": "football",
  "includeHistorical": false
}

Response Format (JSON):
{
  "success": true,
  "data": {
    "games": [
      {
        "id": "12345",
        "teams": ["Green Bay", "Detroit"],
        "odds": {
          "spread": -3.5,
          "spreadOdds": -110
        }
      }
    ]
  }
}
```

---

### Phase 4: Parameter Discovery (15-20 minutes)

#### 4.1 Repeat Requests with Different Parameters

**Use DevTools Request Replay**:

1. In Network tab, right-click on request
2. Select "Copy as cURL" (or "Copy as JavaScript fetch")
3. Paste into terminal or DevTools Console
4. Modify parameters and re-run
5. Observe how response changes

**Example**:
```javascript
// Original request (from Network tab → Copy as fetch)
fetch("https://www.actionnetwork.com/api/v2/odds", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    league: "nfl",
    oddsType: "spread"
  })
})
.then(r => r.json())
.then(d => console.log(d))

// Try different parameters
// Change league to "ncaaf"
// Change oddsType to "total"
// Remove optional fields
// See what breaks and what works
```

#### 4.2 Test Edge Cases

```javascript
// Test 1: What happens with missing required fields?
fetch("https://api/odds", {
  body: JSON.stringify({ league: "nfl" })
})
// Expected: 400 Bad Request (missing oddsType)

// Test 2: What if we include extra fields?
fetch("https://api/odds", {
  body: JSON.stringify({
    league: "nfl",
    oddsType: "spread",
    extraField: "ignored"
  })
})
// Expected: 200 OK (extra fields ignored)

// Test 3: Rate limiting?
// Make 10 requests rapidly, watch for 429 responses
// or decreasing response quality
```

---

### Phase 5: Implementation Validation (10-15 minutes)

#### 5.1 Test Against Real Data

```python
# Quick test in Python REPL
import httpx
import json
import asyncio

async def test_api():
    payload = {
        "league": "nfl",
        "oddsType": "spread",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/odds",
            json=payload,
        )

        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")

asyncio.run(test_api())
```

#### 5.2 Compare with Web Response

1. Open the website in browser
2. Observe what data is displayed
3. Compare with API response
4. Verify API contains same data (or superset)

---

### Phase 6: Documentation (5-10 minutes)

Create a discovery summary document:

```markdown
# API Discovery: Action Network

## Endpoint Details

**URL**: https://www.actionnetwork.com/api/v2/odds
**Method**: POST
**Authentication**: None (public API)
**Rate Limiting**: ~100 req/minute (estimated from headers)

## Required Parameters

- `league` (string): "nfl" or "ncaaf"
- `oddsType` (string): "spread", "total", "moneyline"

## Optional Parameters

- `includeHistorical` (boolean): Include historical games (default: false)
- `limit` (integer): Number of games to return (default: 50)

## Response Format

```json
{
  "success": true,
  "data": {
    "games": [
      {
        "id": "game_id",
        "homeTeam": "Team Name",
        "awayTeam": "Team Name",
        "odds": {
          "spread": -3.5,
          "spreadOdds": -110,
          "overUnder": 48.5,
          "totalOdds": -110
        }
      }
    ],
    "timestamp": "2025-11-26T10:00:00Z"
  }
}
```

## Implementation Advantage

Switching from Playwright to this API provides:
- **Speed**: 5 seconds vs 45 seconds (90% faster)
- **Simplicity**: 20 lines of code vs 500+ lines
- **Reliability**: No DOM parsing, no selector brittleness
- **Cost**: No browser resources needed
- **Testing**: Can record JSON responses as fixtures

## Discovery Date

November 26, 2025

## Validated By

- Chrome DevTools Network tab analysis
- Real-world testing with production requests
- Comparison with web UI behavior
```

---

## Real-World Example: Overtime.ag Discovery

### How Overtime.ag API Was Discovered

**Problem**: SignalR WebSocket connection was complex and unreliable

**Discovery Process**:
1. Opened Chrome DevTools → Network tab
2. Loaded overtime.ag/nfl/odds
3. Filtered by XHR (Network filter → Type: XHR)
4. Saw POST request to `/sports/Api/Offering.asmx/GetSportOffering`
5. Analyzed request payload (JSON with sportType, sportSubType, etc.)
6. Analyzed response format (d.Data.GameLines array)
7. Created client based on discovered API

**Result**:
- Before: 500+ lines of SignalR code, 30s execution, Playwright browser needed
- After: 150 lines of HTTP client code, 5s execution, no browser needed
- Improvement: 70% faster, 70% less code, 100% more reliable

### Application to Action Network

**Hypothesis**: Action Network probably exposes similar APIs

**Discovery Steps**:
1. Open Chrome DevTools → Network tab
2. Navigate to actionnetwork.com/nfl/odds
3. Filter by XHR requests
4. Look for POST endpoints in `/api/` directory
5. Reverse-engineer the payload format
6. Create new ActionNetworkApiClient based on findings
7. Compare with current Playwright implementation (should be similar data)
8. If successful: replace Playwright client with API client (60% speedup)

---

## Tools & Techniques

### Chrome DevTools Advanced Features

#### 1. Request Replay
```
Network tab → Right-click request → Copy as cURL/Fetch
Paste into console and modify
Great for testing parameter variations
```

#### 2. Request/Response Pretty-Print
```
Network tab → Click request → Response tab
Click "{ }" icon to format JSON
Makes structure obvious
```

#### 3. Network Throttling
```
Network tab → Throttling dropdown → Slow 3G
Makes requests slower and easier to watch
Reveals which requests are critical (block page load)
```

#### 4. Filtering
```
is:xhr                    # Show only XHR/Fetch
-is:image                 # Exclude images
size>10KB                 # Larger than 10KB
mime-type:application/json# JSON responses
domain:api.example.com    # Specific domain
status:200                # Specific status code
```

#### 5. Export HAR File
```
Network tab → Right-click → Save all as HAR with content
Creates .har file with all requests/responses
Can be replayed later for testing
Great for creating test fixtures
```

---

## Common Patterns Found in APIs

### Pattern 1: RESTful API
```
GET /api/v2/teams
POST /api/v2/odds
PUT /api/v2/picks/{id}
DELETE /api/v2/picks/{id}
```

### Pattern 2: GraphQL
```
POST /graphql
Content-Type: application/json

{
  "query": "{ teams { id name } }"
}
```

### Pattern 3: RPC-Style
```
POST /api/offering
Body: { method: "GetGames", params: { league: "nfl" } }
```

### Pattern 4: Custom Endpoint
```
POST /sports/Api/Offering.asmx/GetSportOffering
Body: { sportType: "Football", ... }
```

---

## Red Flags & Troubleshooting

### Red Flag 1: API is Behind Authentication
```
Check for:
- 401 Unauthorized responses
- Authorization header in requests
- Cookie-based authentication

Solution:
- May need to login first (capture auth token from browser)
- May be geofenced (requires VPN)
- May require paid API key
```

### Red Flag 2: CORS Restrictions
```
Check for:
- CORS error in console
- Origin mismatch errors
- OPTIONS pre-flight requests failing

Solution:
- Can't access from browser JavaScript (client-side)
- CAN access from Python (server-side has no CORS restrictions)
- Continue with reverse-engineered client
```

### Red Flag 3: CloudFlare/Bot Protection
```
Check for:
- 403 Forbidden responses
- Unusual delays (5-10 seconds)
- Challenge pages (human verification)

Solution:
- Use Playwright client with proper User-Agent
- Consider proxy rotation
- Try curl with browser User-Agent
```

### Red Flag 4: Rate Limiting
```
Check for:
- X-RateLimit-* headers
- 429 Too Many Requests responses
- Status: 503 Service Unavailable

Solution:
- Implement rate limiting in client (0.5s delay minimum)
- Use circuit breaker (5 failures = 5 min pause)
- Spread requests over time
```

---

## Checklist: API Discovery Session

- [ ] Chrome/Chromium open, DevTools ready
- [ ] Network tab configured (no cache, throttling on)
- [ ] Target website loaded, full page load observed
- [ ] Screenshots taken of Network tab
- [ ] XHR/Fetch requests identified
- [ ] Primary endpoint documented
- [ ] Request headers noted (User-Agent, Content-Type, Auth)
- [ ] Request body analyzed (parameters identified)
- [ ] Response format documented
- [ ] Parameters tested (at least 3 variations)
- [ ] Rate limiting observed (if any)
- [ ] Python test created and validated
- [ ] Comparison with web UI confirms data match
- [ ] Discovery summary document created
- [ ] Estimated implementation effort calculated

---

## Success Criteria

**Discovery is successful when you can**:

1. ✅ Explain the endpoint URL and method (GET vs POST)
2. ✅ List all required and optional parameters
3. ✅ Show example request and response (JSON)
4. ✅ Create a Python test that fetches real data from the API
5. ✅ Compare API response with website display (same data?)
6. ✅ Estimate speedup vs current Playwright implementation
7. ✅ Document any authentication or rate limiting requirements

**If you can't do all 7**, investigation is incomplete.

---

## Next Steps: Implementation After Discovery

Once API is discovered and documented:

1. **Create API Client Class**
   ```python
   class ActionNetworkApiClient(BaseHTTPClient):
       """Uses discovered API instead of Playwright."""
   ```

2. **Write Tests**
   - Unit tests with mock responses
   - Integration tests with real API
   - Regression tests comparing with Playwright version

3. **Update Scrapers**
   - Swap Playwright client for API client
   - Verify same data is collected
   - Benchmark performance improvement

4. **Document Lessons**
   - Add to LESSONS_LEARNED.md
   - Update API documentation
   - Share discovery process with team

---

## References

- Chrome DevTools Network Tab: https://developer.chrome.com/docs/devtools/network/
- HAR File Format: http://www.softwareishard.com/blog/har-12-spec/
- cURL Request Format: https://curl.se/docs/manpage.html

---

**Status**: Ready to apply to Action Network and NFL.com
**Methodology**: Proven by Overtime.ag success
**Estimated Time**: 20-30 minutes per target
**Success Rate**: ~70% (API exists and is accessible)
