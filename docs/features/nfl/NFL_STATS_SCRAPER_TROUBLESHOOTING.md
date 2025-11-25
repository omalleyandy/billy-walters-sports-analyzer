# NFL.com Game Stats Scraper - Troubleshooting Guide

## Issue: Page.goto Timeout Errors

**Error Message**:
```
Error fetching game stats: Page.goto: Timeout 30000ms exceeded.
navigating to "https://www.nfl.com/games/bills-at-texans-2025-reg-12?tab=stats",
waiting until "networkidle"
```

### Root Cause

NFL.com has **aggressive bot detection** that blocks automated browsers like Playwright, causing:
1. Timeouts during page navigation
2. Blank pages with no content
3. Redirects to security pages
4. Connection resets

This is a protective measure NFL.com takes to prevent automated scraping.

---

## Solutions

### Option 1: Use ESPN API Instead (Recommended)

The project already has **ESPN API integration** that works reliably. Use this instead:

```python
from src.data.espn_team_stats_client import ESPNTeamStatsClient

async with ESPNTeamStatsClient() as client:
    stats = await client.get_team_stats(
        team="New York Bills",
        league="nfl",
        week=12
    )
```

**Advantages**:
- ✅ No browser needed
- ✅ 100% reliable
- ✅ Fast (no timeouts)
- ✅ Already integrated in project
- ✅ Works with edge detection

**Trade-off**:
- ESPN stats structure is different from NFL.com
- May need different stat category names

### Option 2: Use Overtime.ag API

Overtime.ag has game statistics available:

```python
from src.data.overtime_api_client import OvertimeClient

async with OvertimeClient() as client:
    game_stats = await client.get_game_stats(
        game_id="some_game_id"
    )
```

**Advantages**:
- ✅ API-based (no browser)
- ✅ Specifically designed for sports data
- ✅ Already integrated

### Option 3: Increase Browser Timeouts (Workaround)

If you want to continue with Playwright despite bot detection, try:

```python
client = NFLGameStatsClient(headless=False)  # Show browser for debugging
await client.connect()

# Manually test a single game with longer timeout
game_url = "https://www.nfl.com/games/bills-at-texans-2025-reg-12?tab=stats"

# Set extremely long timeout
await client._page.goto(
    game_url,
    wait_until="domcontentloaded",
    timeout=120000  # 2 minutes
)
await asyncio.sleep(10)  # Extra wait for JS

stats = await client._extract_game_info()
```

**Trade-offs**:
- ❌ Very slow (2+ minutes per game)
- ❌ May still timeout randomly
- ❌ 16 games = 30+ minutes
- ⚠️ No guarantee of success

### Option 4: Add Cloudflare Bypass

NFL.com may use Cloudflare protection. Try:

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-web-resources",
            "--start-maximized",
        ],
    )

    page = await browser.new_page()

    # Set request headers to mimic real browser
    await page.set_extra_http_headers({
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
    })

    # ... rest of code
```

**Success Rate**: Low (Cloudflare detection is sophisticated)

---

## Recommended Path Forward

### For Your Project

Given the project's existing infrastructure, I recommend:

**Option A: Switch to ESPN API**
```python
# Already integrated, works perfectly
from src.data.espn_api_client import ESPNAPIClient
```

**Option B: Use Massey Ratings + Overtime.ag**
```python
# Get offensive/defensive ratings from Massey
# Get game odds from Overtime.ag API
# Combine for complete game picture
```

**Option C: Request from Action Network**
```python
# Action Network has game statistics
# Already integrated in project
from src.data.action_network_client import ActionNetworkClient
```

---

## What's Not Working & Why

### Current Implementation Issues

1. **Bot Detection** - NFL.com detects Playwright as automated browser
2. **JavaScript-Heavy** - Stats tables load via JavaScript, not in initial HTML
3. **Rate Limiting** - NFL.com rate limits based on request patterns
4. **Session Handling** - Some pages require proper session/cookie handling

### Why Playwright Alone Won't Work

Playwright is designed for testing, not scraping. NFL.com's bot detection specifically targets:
- Missing browser indicators (Playwright is detected)
- Suspicious request patterns
- Unusual timing of requests
- Lack of human-like behavior

---

## Alternative Approaches

### Approach 1: Puppeteer-Stealth + Browser Automation

Use `puppeteer-extra-plugin-stealth` (JavaScript) but would require Node.js

### Approach 2: Selenium with Anti-Detection

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome

# Use undetected-chromedriver
driver = Chrome()
```

**Problem**: Adds complexity, Python ecosystem is weaker for this

### Approach 3: Static HTML + Parsing

If NFL.com has server-rendered stats in initial HTML:
- No JavaScript needed
- No bot detection
- Lightning fast

**Current Status**: Stats appear to be JavaScript-rendered

### Approach 4: Third-Party Stats API

Services like:
- **RapidAPI** - NFL stats endpoints
- **TheOddsAPI** - Game data
- **ESPN Data Feeds** - Official stats
- **Sportradar** - Professional data provider

---

## Summary

**Current Status**: ❌ Playwright-based scraping is blocked by NFL.com bot detection

**Best Solution**: ✅ Use ESPN API or Action Network (already integrated)

**Why**: Your project already has reliable APIs integrated. Using those is faster, more reliable, and requires zero new dependencies.

---

## Next Steps

Would you like me to:

1. **Create ESPN API stats wrapper** - Unified interface for game statistics
2. **Create Action Network stats extractor** - Use existing Action Network client
3. **Create Massey + Overtime combined stats** - Ratings + odds combined
4. **Debug actual browser behavior** - Test with headless=False to see what's happening

Let me know which approach works best for your workflow!
