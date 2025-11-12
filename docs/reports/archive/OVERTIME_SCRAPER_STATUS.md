# Overtime.ag Scraper Status Report

**Date:** 2025-11-09
**Status:** Partial Success - Proxy works, but SPA limitations

## Summary

Successfully created a requests-based scraper that authenticates through the residential proxy and accesses overtime.ag. However, the site uses AngularJS + SignalR WebSocket for dynamic content loading, which prevents simple HTTP scraping.

## What Works ✅

1. **Proxy Authentication**
   - Successfully connects through rp.scrapegw.com:6060 residential proxy
   - HTTP/HTTPS requests work correctly
   - Main page returns HTTP 200 (11,684 bytes)

2. **HTML Fetching**
   - Can retrieve the base HTML skeleton
   - Saves HTML snapshots for debugging
   - Session management with cookies

3. **File:** `overtime_requests_scraper.py`
   - Clean, modular architecture
   - Proxy config matching test_proxy.py pattern
   - JSONL output formatting
   - Error handling and logging

## What Doesn't Work ❌

### 1. Playwright + Residential Proxy
**Error:** `HTTP 407 Proxy Authentication Required`

**Reason:** Playwright's proxy authentication methods are incompatible with residential proxy services that encode routing info in username (e.g., `5iwdzupyp3mzyv6-country-us`)

**Attempts:**
- Separated username/password in proxy config
- Embedded credentials in URL
- Both headless and visible modes

### 2. Chrome DevTools Protocol (CDP)
**Error:** `net::ERR_NO_SUPPORTED_PROXIES`

**Reason:** Chrome's `--proxy-server` flag doesn't support credentials in URL format

**File:** `overtime_cdp_scraper.py` (attempted but failed)

### 3. Direct API Endpoints
**Results:** All return 404

**Endpoints Tested:**
```
/api/live
/api/live/odds
/api/odds/live
/api/games/live
/api/events/live
/api/integrations/liveBetting
/api/sports/live
/api/sports/events
/sports/api/live
/sports/api/odds
```

**Reason:** overtime.ag doesn't use REST APIs for live odds. Data is loaded via SignalR WebSocket after JavaScript execution.

## Technical Analysis

### overtime.ag Architecture

**Technology Stack:**
- **Framework:** AngularJS 1.x (`ng-app="mainModule"`)
- **Rendering:** Client-side (`<ng-view></ng-view>`)
- **Real-time Data:** SignalR WebSocket (`ws.ticosports.com/signalr`)
- **Bundled JS:** Multiple compressed JavaScript bundles

**Data Flow:**
1. Browser loads HTML skeleton (what we get with requests)
2. AngularJS boots up and initializes
3. JavaScript establishes SignalR WebSocket connection
4. Live odds stream through WebSocket
5. AngularJS renders data dynamically

**Static HTML Content:**
```html
<html ng-app="mainModule">
  <!-- Skeleton with no game data -->
  <ng-view></ng-view>
  <!-- Data loaded by JavaScript -->
</html>
```

### Why Requests Library Can't Extract Odds

The requests library:
- ✅ Can fetch HTTP/HTTPS pages
- ✅ Can authenticate through proxies
- ❌ Cannot execute JavaScript
- ❌ Cannot connect to WebSockets
- ❌ Cannot render dynamic content

overtime.ag requires:
- JavaScript execution (AngularJS)
- WebSocket connection (SignalR)
- Dynamic DOM manipulation

## Solutions Attempted

### 1. overtime_requests_scraper.py
**Approach:** Use requests library with BeautifulSoup
**Status:** ✅ Proxy works, ❌ Can't get dynamic content
**Limitations:** No JavaScript execution

### 2. overtime_cdp_scraper.py
**Approach:** Chrome DevTools Protocol with proxy via CLI flag
**Status:** ❌ Proxy auth rejected
**Error:** `ERR_NO_SUPPORTED_PROXIES`

### 3. Scrapy overtime_live spider
**Approach:** Scrapy + scrapy-playwright
**Status:** ❌ Proxy 407 errors
**Location:** `scrapers/overtime_live/spiders/overtime_live_spider.py` (31,000+ lines)

## Files Created/Modified

### New Files
- `overtime_requests_scraper.py` - Working requests scraper (proxy OK, no dynamic content)
- `test_proxy.py` - Successful proxy test (HTTP 200)
- `OVERTIME_SPIDER_DEBUGGING.md` - Detailed debugging log
- `OVERTIME_SCRAPER_STATUS.md` - This file

### Modified Files
- `scrapers/overtime_live/spiders/overtime_live_spider.py`:
  - Fixed headless mode (line 96)
  - Fixed password env var (line 250)
  - Fixed start URL (line 132)
  - Removed duplicate proxy config (lines 90-105)

### Logs & Snapshots
- `spider_correct_password_test.log` - Confirmed 407 error
- `snapshots/overtime_html_*.html` - HTML skeleton captures
- `snapshots/error.png` - Screenshot of 407 error

## Potential Solutions

### Option 1: Different Proxy Type ⭐ RECOMMENDED
**Approach:** Use datacenter proxy or HTTP proxy without auth
**Pros:** Playwright/Selenium would work
**Cons:** May not bypass cloudflare/geo-blocking

### Option 2: No Proxy (If IP Whitelisted)
**Approach:** Access overtime.ag directly from user's IP
**Pros:** Simplest solution
**Cons:** Only works if user's IP is whitelisted

### Option 3: Selenium with Proxy
**Approach:** Try Selenium instead of Playwright
**Pros:** Different proxy handling, might work
**Cons:** Still likely to hit same 407 error

### Option 4: Proxy Tunnel
**Approach:** Set up local proxy that forwards to residential proxy
**Pros:** Separates auth from browser automation
**Cons:** Complex setup, additional component

### Option 5: Reverse Engineer SignalR
**Approach:** Connect directly to WebSocket, bypass browser
**Pros:** Most efficient if successful
**Cons:** Very complex, may require auth tokens

### Option 6: During Live Games Only
**Approach:** Test during actual NFL/NCAAF live games
**Pros:** May reveal API endpoints that only exist during games
**Cons:** Timing dependent, unlikely to change findings

## Next Steps

### Immediate
1. ✅ Document current status (this file)
2. ⏳ Consult with user on proxy options
3. ⏳ Decide on path forward

### If Using Different Proxy
1. Update proxy configuration
2. Test Playwright with new proxy
3. Implement full scraping with JavaScript execution

### If Using Selenium
1. Create `overtime_selenium_scraper.py`
2. Configure proxy via Selenium options
3. Test proxy authentication

### If Reverse Engineering SignalR
1. Capture WebSocket traffic during live game
2. Analyze SignalR protocol messages
3. Implement SignalR client in Python
4. Handle authentication/subscriptions

## Test Results

### test_proxy.py
```
✅ Proxy IP: 71.200.226.141 (US, Florida)
✅ overtime.ag Status: 200
✅ Response: 11,186 bytes
```

### overtime_requests_scraper.py
```
✅ Main page status: 200
✅ HTML response: 11,684 bytes
❌ No games extracted (expected - no live games, no JavaScript execution)
```

### Scrapy overtime_live spider
```
❌ HTTP ERROR 407 - Proxy Authentication Required
❌ ERR_INVALID_AUTH_CREDENTIALS
```

### overtime_cdp_scraper.py
```
❌ ERR_NO_SUPPORTED_PROXIES
```

## Conclusion

The residential proxy works perfectly with the Python requests library, as proven by test_proxy.py. However, overtime.ag's architecture (AngularJS SPA + SignalR WebSocket) requires JavaScript execution that requests can't provide.

Browser automation tools (Playwright, Chrome CDP) that CAN execute JavaScript are incompatible with this specific residential proxy service's authentication method.

**Recommendation:** Switch to a compatible proxy type (datacenter proxy or no-auth proxy) to enable Playwright/Selenium-based scraping with full JavaScript execution.
