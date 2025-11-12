# Overtime Spider Debugging Session

**Date**: November 9, 2025
**Goal**: Get overtime_live spider working to scrape live NFL/NCAAF odds from overtime.ag

---

## Issues Found and Fixed

### 1. Login Credentials Environment Variable Mismatch
**Location**: `scrapers/overtime_live/spiders/overtime_live_spider.py:250`

**Problem**:
```python
# Spider was looking for:
password = os.getenv("OV_CUSTOMER_PASSWORD")

# But .env has:
OV_PASSWORD=Foot...
```

**Fix**: Changed to support both names:
```python
password = os.getenv("OV_PASSWORD") or os.getenv("OV_CUSTOMER_PASSWORD")
```

### 2. Proxy Credentials Not Parsed (PLAYWRIGHT_LAUNCH_OPTIONS)
**Location**: Line 90-105

**Problem**: Passing full proxy URL with embedded credentials directly to Playwright:
```python
_proxy_server = "http://username:password@host:port"
{"proxy": {"server": _proxy_server}}  # Playwright rejected embedded credentials
```

**Initial Fix Attempt**: Parsed credentials separately:
```python
{
    "server": "http://host:port",
    "username": "username",
    "password": "password"
}
```

**Result**: Still getting authentication errors

### 3. Duplicate Proxy Configuration
**Problem**: Proxy configured in TWO places:
- PLAYWRIGHT_LAUNCH_OPTIONS (line 94-105)
- context_kwargs in start() method (line 134-164)

**Fix**: Removed from PLAYWRIGHT_LAUNCH_OPTIONS, kept only in context_kwargs

### 4. Starting URL
**Location**: Line 129-132

**Problem**: Spider tried to navigate directly to live betting page:
```python
target_url = live or start  # Was using live betting URL first
```

**Fix**: Changed to start at main page for login:
```python
target_url = start  # https://overtime.ag (login first, then navigate)
```

---

## Current Status: HTTP 407 / ERR_INVALID_AUTH_CREDENTIALS

### Error Screenshots
- Screenshot saved: `snapshots/error.png`
- Shows: "HTTP ERROR 407" - Proxy Authentication Required

### Proxy Details
- Service: rp.scrapegw.com:6060 (residential proxy)
- Format: `http://username:password@host:port`
- Username: `5iwdzupyp3mzyv6-country-us` (includes country specification)
- Password: `9cz69tojhtqot8f`

### Tested Approaches

1. **Separated credentials** (username/password as separate fields)
   - Result: ERR_INVALID_AUTH_CREDENTIALS

2. **Embedded credentials in server URL**
   - Result: ERR_INVALID_AUTH_CREDENTIALS

3. **Removed duplicate proxy config**
   - Result: Still authentication failure

---

## Root Cause Analysis

**Playwright + Residential Proxies = Authentication Challenge**

Residential proxy services like rp.scrapegw.com often use:
- Custom authentication methods
- Username encoding for routing (e.g., `-country-us`)
- May not support standard HTTP proxy auth headers

Playwright's proxy authentication:
- Supports username/password fields
- Supports embedded credentials in some cases
- May not work with all residential proxy auth methods

---

## Next Steps / Recommendations

### Option 1: Test Without Proxy (Recommended First)
Temporarily disable proxy to isolate the issue:

```bash
# Comment out PROXY_URL in .env
# PROXY_URL=http://...

# Test spider
uv run scrapy crawl overtime_live -O output/test_no_proxy.json
```

**Expected outcomes**:
- ✅ If works: Proxy is the blocker, need alternative auth method
- ❌ If fails: overtime.ag has other protections (CloudFlare, rate limiting, etc.)

### Option 2: Contact Proxy Provider
Ask rp.scrapegw.com about:
- Playwright-specific configuration
- Alternative authentication methods
- SOCKS5 proxy support (Playwright handles SOCKS5 better)
- Whitelist IP option (no authentication needed)

### Option 3: Alternative Proxy Configuration
Try SOCKS5 proxy if available:
```python
{
    "proxy": {
        "server": "socks5://rp.scrapegw.com:6060",
        "username": "5iwdzupyp3mzyv6-country-us",
        "password": "9cz69tojhtqot8f"
    }
}
```

### Option 4: Use Persistent Browser Context
Save authenticated session and reuse:
```python
# Login once, save state
browser.new_context(storage_state="auth_state.json")

# Reuse in future runs
browser.new_context(storage_state="auth_state.json")
```

### Option 5: Manual Browser Testing
Test proxy in regular Chrome with Playwright:
```python
# Test script to verify proxy works
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        proxy={
            "server": "http://rp.scrapegw.com:6060",
            "username": "5iwdzupyp3mzyv6-country-us",
            "password": "9cz69tojhtqot8f"
        }
    )
    page = browser.new_page()
    page.goto("https://ipinfo.io")  # Test proxy IP
    page.screenshot(path="proxy_test.png")
    browser.close()
```

---

## Important Context from User

**Live Odds Availability**:
- Live odds only available when NFL/NCAAF games are actively being played
- Need to build logic to handle:
  - Empty results when no games active
  - Graceful failure messages
  - Retry logic during game windows

**Typical NFL Game Times**:
- Thursday Night: 8:15 PM ET
- Sunday: 1:00 PM, 4:05 PM, 4:25 PM, 8:20 PM ET
- Monday Night: 8:15 PM ET

**NCAAF Game Times**:
- Saturday: All day (12 PM - 11 PM ET)
- Occasional weeknight games

---

## Bugs Fixed Summary

| Bug # | Issue | Status | File:Line |
|-------|-------|--------|-----------|
| 1 | Wrong env var for password | ✅ Fixed | overtime_live_spider.py:250 |
| 2 | Proxy credentials not parsed | ⚠️ Attempted | overtime_live_spider.py:90-105 |
| 3 | Duplicate proxy config | ✅ Fixed | overtime_live_spider.py (removed duplication) |
| 4 | Wrong start URL | ✅ Fixed | overtime_live_spider.py:132 |
| 5 | Proxy auth method incompatible | ❌ Unresolved | Playwright + rp.scrapegw.com |

---

## Working Code Changes

All changes made to: `scrapers/overtime_live/spiders/overtime_live_spider.py`

### Change 1: Login Credentials
```python
# Line 250
password = os.getenv("OV_PASSWORD") or os.getenv("OV_CUSTOMER_PASSWORD")
```

### Change 2: Removed Proxy from Launch Options
```python
# Lines 90-97
custom_settings = {
    "BOT_NAME": "overtime_live",
    "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90_000,
    "PLAYWRIGHT_LAUNCH_OPTIONS": {
        "headless": False,
        # Proxy will be configured per-request in start() method
    },
```

### Change 3: Start URL
```python
# Line 132
target_url = start  # Always start with main page for login
```

### Change 4: Proxy in Context (Current - Not Working)
```python
# Lines 136-140
proxy_url = os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")
context_kwargs = None
if proxy_url:
    context_kwargs = {"proxy": {"server": proxy_url}}
```

---

## Test Commands

### With Proxy (Currently Failing)
```bash
cd C:/Users/omall/Documents/python_projects/billy-walters-sports-analyzer
uv run scrapy crawl overtime_live -O output/test_live_odds.json
```

### Without Proxy (Recommended Test)
```bash
# Temporarily comment out PROXY_URL in .env
uv run scrapy crawl overtime_live -O output/test_no_proxy.json
```

### Check Proxy IP
```bash
curl --proxy http://5iwdzupyp3mzyv6-country-us:9cz69tojhtqot8f@rp.scrapegw.com:6060 https://ipinfo.io
```

---

## Output Files from Testing

- `spider_test_output.log` - Initial headless test
- `spider_visible_test.log` - Non-headless browser test
- `spider_fixed_test.log` - After proxy parsing fix
- `spider_final_test.log` - After all fixes
- `spider_proxy_url_test.log` - Testing credentials in URL
- `snapshots/error.png` - HTTP 407 error screenshot

---

## Next Session TODO

1. Test spider **without proxy** to isolate the issue
2. If no-proxy works:
   - Contact rp.scrapegw.com for Playwright config
   - Try SOCKS5 if available
   - Consider IP whitelist option

3. If no-proxy also fails:
   - Check CloudFlare blocking
   - Add stealth plugins
   - Verify overtime.ag hasn't changed structure

4. Once connection works:
   - Implement game time logic
   - Handle empty results gracefully
   - Test during actual live games
   - Verify data extraction

---

## Lessons Learned

1. **Residential proxies ≠ Standard HTTP proxies**
   - May use custom auth methods
   - Username can encode routing info
   - Not all work with Playwright

2. **Test without complexity first**
   - Should have tested no-proxy first
   - Isolate variables to find root cause

3. **Playwright proxy auth is tricky**
   - Works better with SOCKS5
   - Some services incompatible
   - IP whitelist is simpler

4. **scrapy-playwright config layers**
   - Launch options vs. context options
   - Per-request vs. global config
   - Easy to create conflicts
