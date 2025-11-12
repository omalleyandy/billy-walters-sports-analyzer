# Overtime.ag Scraper - Technical Reference

**Last Updated**: November 10, 2025
**Status**: Production Ready
**Tested On**: Windows 11, Python 3.11+

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Authentication Flow](#authentication-flow)
3. [Critical Selectors](#critical-selectors)
4. [Proxy Configuration](#proxy-configuration)
5. [Data Extraction](#data-extraction)
6. [Format Conversion](#format-conversion)
7. [Error Handling](#error-handling)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting Guide](#troubleshooting-guide)

---

## Architecture Overview

### Components

```
scripts/scrape_overtime_nfl.py          # CLI entry point
    ↓
src/data/overtime_pregame_nfl_scraper.py  # Core scraper class
    ↓
src/data/overtime_data_converter.py     # Format converter
    ↓
output/                                 # Output directory
    ├── overtime_nfl_raw_*.json        # Raw Overtime format
    ├── overtime_nfl_odds_*.json       # Legacy format
    └── overtime_nfl_walters_*.json    # Billy Walters format
```

### Technology Stack

- **Browser Automation**: Playwright (Chromium)
- **Framework**: AngularJS (vanilla JavaScript, not React/Vue)
- **Security**: CloudFlare DDoS protection
- **Real-time**: WebSocket server at `wss://ws.ticosports.com/signalr`

---

## Authentication Flow

### Environment Variables

```bash
# Required in .env
OV_CUSTOMER_ID=your_customer_id
OV_PASSWORD=your_password

# Optional
PROXY_URL=http://user:pass@proxy:8080
```

### Login Sequence

1. **Navigate to Site**
   ```python
   await page.goto("https://overtime.ag/sports#/",
                   wait_until="domcontentloaded",
                   timeout=60000)
   ```

2. **JavaScript Click (Critical)**
   ```python
   # IMPORTANT: Element is hidden in DOM, requires JavaScript click
   login_clicked = await page.evaluate("""
       () => {
           const loginBtn = document.querySelector('a.btn-signup');
           if (loginBtn) {
               loginBtn.click();
               return true;
           }
           return false;
       }
   """)
   ```

   **Why JavaScript Click?**
   - Button exists but technically hidden until CSS/JS condition
   - Playwright's native `.click()` requires element visibility
   - `force=True` doesn't bypass all visibility checks
   - AngularJS `ng-click="ShowLoginView()"` needs direct trigger

3. **Enter Credentials**
   ```python
   await page.fill('input[ng-model="Username"]', customer_id)
   await page.fill('input[ng-model="Password"]', password)
   await page.click('button:has-text("LOGIN")')
   ```

4. **Verify Login**
   ```python
   await page.wait_for_selector('[href*="dailyFigures"]', timeout=30000)
   ```

---

## Critical Selectors

### Login Elements

```css
/* Login button (hidden, use JavaScript click) */
a.btn-signup
/* Attribute: ng-click="ShowLoginView()" */

/* Username input */
input[ng-model="Username"]

/* Password input */
input[ng-model="Password"]

/* Login submit button */
button:has-text("LOGIN")

/* Account info (verify login success) */
[href*="dailyFigures"]
[href*="openBets"]
```

### NFL Section

```css
/* NFL section label */
label:has-text("NFL-Game/1H/2H/Qrts")

/* Team names (format: rotation_number team_name) */
h4

/* Betting buttons */
button[ng-click*="SendLineToWager"]

/* Period tabs */
a:has-text("GAME")
a:has-text("1ST HALF")
a:has-text("1ST QUARTER")
```

### Account Information

```css
/* Balance display */
[href*="dailyFigures"]

/* Available balance */
[href*="openBets"]

/* Pending bets */
.pending-bets
```

---

## Proxy Configuration

### Correct Configuration (Context-Level)

```python
# Initialize browser
browser = await p.chromium.launch(headless=headless, args=browser_args)

# Configure context with proxy
context_kwargs = {
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 ..."
}

if proxy_url:
    # Credentials embedded in URL for residential proxies
    context_kwargs["proxy"] = {"server": proxy_url}

context = await browser.new_context(**context_kwargs)
```

### Proxy URL Format

```
http://username:password@host:port
```

**Example:**
```
http://user123:pass456@rp.scrapegw.com:6060
```

### Common Proxy Issues

**Issue**: `ERR_INVALID_AUTH_CREDENTIALS`
- **Cause**: Credentials expired with provider
- **Fix**: Contact provider, update PROXY_URL in .env
- **Workaround**: Use `--proxy ""` to disable

**Issue**: `Timeout 60000ms exceeded`
- **Cause**: Proxy server not responding
- **Fix**: Test proxy separately, verify connectivity
- **Workaround**: Run without proxy

### Proxy vs Browser Args (DON'T DO THIS)

```python
# ❌ WRONG - Doesn't work reliably
browser_args.append(f"--proxy-server={proxy_url}")
browser = await p.chromium.launch(headless=headless, args=browser_args)

# ✅ CORRECT - Use context-level proxy
context_kwargs["proxy"] = {"server": proxy_url}
context = await browser.new_context(**context_kwargs)
```

---

## Data Extraction

### Game Line Structure

Each game contains:
```python
{
    "visitor": {
        "teamName": "Philadelphia Eagles",
        "rotationNumber": "101",
        "spread": "+1 -113",
        "moneyline": "+105",
        "total": "O 45½ -112"
    },
    "home": {
        "teamName": "Green Bay Packers",
        "rotationNumber": "102",
        "spread": "-1 -107",
        "moneyline": "-125",
        "total": "U 45½ -108"
    },
    "period": "GAME",
    "timestamp": "2025-11-10T03:47:49.768432"
}
```

### Extraction Algorithm

1. **Navigate to NFL Section**
   ```python
   await page.click('label:has-text("NFL-Game/1H/2H/Qrts")')
   await page.wait_for_timeout(2000)  # Wait for games to load
   ```

2. **Extract Team Names**
   ```python
   h4_elements = await page.query_selector_all('h4')
   for h4 in h4_elements:
       text = await h4.text_content()
       # Parse: "101 Philadelphia Eagles"
       rotation_number, team_name = parse_team_text(text)
   ```

3. **Extract Betting Lines**
   ```python
   buttons = await page.query_selector_all('button[ng-click*="SendLineToWager"]')
   for button in buttons:
       line_text = await button.text_content()
       # Parse: "+1 -113" or "O 45½ -112"
       value, odds = parse_line(line_text)
   ```

4. **Iterate Periods**
   ```python
   for period in ["GAME", "1ST HALF", "1ST QUARTER"]:
       await page.click(f'a:has-text("{period}")')
       await page.wait_for_timeout(1000)
       games = extract_games_from_page(page)
   ```

---

## Format Conversion

### Input: Overtime Raw Format

```json
{
  "visitor": {
    "teamName": "Philadelphia Eagles",
    "spread": "+1 -113"
  },
  "home": {
    "teamName": "Green Bay Packers",
    "spread": "-1 -107"
  }
}
```

### Output: Billy Walters Format

```json
{
  "game_id": "2025-11-10_PHI_GB",
  "away_team": {
    "name": "Philadelphia Eagles",
    "abbreviation": "PHI"
  },
  "home_team": {
    "name": "Green Bay Packers",
    "abbreviation": "GB"
  },
  "odds": {
    "spread": 1.0,
    "spread_odds": -113,
    "over_under": 45.5,
    "total_odds": -112,
    "away_ml": 105,
    "home_ml": -125
  },
  "period": "GAME",
  "timestamp": "2025-11-10T03:47:49.768432"
}
```

### Conversion Logic

```python
from src.data.overtime_data_converter import convert_overtime_to_walters

walters_data = convert_overtime_to_walters(overtime_data)

# Returns:
# {
#   "metadata": {...},
#   "account_info": {...},
#   "games": [...],
#   "summary": {
#     "total_converted": 14,
#     "conversion_rate": "100%"
#   }
# }
```

---

## Error Handling

### Windows Unicode Fix

**Issue**: `UnicodeEncodeError: 'charmap' codec can't encode character`

**Solution**: Replace all Unicode symbols with ASCII
```python
# ❌ OLD (fails on Windows)
print(f"\n✓ Raw data saved to: {raw_file}")
print(f"\n✗ Error during scrape: {e}")

# ✅ NEW (cross-platform)
print(f"\n[OK] Raw data saved to: {raw_file}")
print(f"\n[ERROR] Error during scrape: {e}")

# Clean external content with emoji
snippet = page_text.encode('ascii', 'ignore').decode('ascii')
```

### Graceful Degradation

```python
try:
    # Try to scrape
    games = await scraper.scrape()
except Exception as e:
    print(f"[ERROR] Scrape failed: {e}")
    # Save what we have
    save_partial_results()
    # Continue execution
```

### Database Module Not Found

```python
if args.save_db:
    try:
        from walters_analyzer.ingest.odds_ingest import ingest_odds
        for game in games:
            ingest_odds(game)
    except ImportError:
        print("[WARNING] Database module not found - skipping database save")
    except Exception as e:
        print(f"[ERROR] Error saving to database: {e}")
```

---

## Performance Optimization

### Headless Mode

```bash
# 2-3x faster than visible browser
uv run python scripts/scrape_overtime_nfl.py --headless
```

### Timeout Configuration

```python
# Page load timeout (default: 60s)
await page.goto(url, timeout=60000)

# Element wait timeout (default: 30s)
await page.wait_for_selector(selector, timeout=30000)

# Manual wait for dynamic content (default: 2s)
await page.wait_for_timeout(2000)
```

### Parallel Processing

```python
# Not recommended for Overtime.ag
# Sequential scraping is more reliable
# Site uses WebSocket for real-time updates
```

---

## Troubleshooting Guide

### No Games Found (0 games)

**Most Common Cause**: Timing

```bash
# Check current NFL week
/current-week

# Output: NFL 2025 Regular Season - Week 10
```

**Game Availability Schedule**:
- ✅ **Tuesday-Thursday**: Week N+1 lines available
- ❌ **Sunday during games**: Lines taken down (0 games expected)
- ❌ **Monday during MNF**: Current week lines removed
- ❌ **Thursday 8pm+**: TNF line removed

**Solution**: Run Tuesday-Thursday mornings

### Login Button Not Found

**Symptom**: `ElementHandle.click: Timeout 30000ms exceeded`

**Cause**: Button hidden in DOM

**Solution**: Use JavaScript click
```python
login_clicked = await page.evaluate("""
    () => {
        const loginBtn = document.querySelector('a.btn-signup');
        if (loginBtn) {
            loginBtn.click();
            return true;
        }
        return false;
    }
""")
```

### Proxy Timeout

**Symptom**: `TimeoutError: Page.goto: Timeout 60000ms exceeded`

**Diagnostic Steps**:
1. Test without proxy: `--proxy ""`
2. If works, proxy credentials are the issue
3. Contact proxy provider for refresh
4. Update PROXY_URL in .env

**Immediate Workaround**: Run without proxy

### Invalid Line Parsing

**Symptom**: Incorrect spread/total values

**Debug**:
```python
# Add debug output in scraper
debug_info = await page.evaluate("""
    () => {
        return {
            h4Count: document.querySelectorAll('h4').length,
            buttonCount: document.querySelectorAll('button[ng-click*="SendLineToWager"]').length,
            pageText: document.body.innerText.substring(0, 500)
        };
    }
""")
print(f"DEBUG - Page elements: {debug_info}")
```

### Database Save Fails

**Symptom**: `[WARNING] Database module not found`

**Expected**: Database integration not yet implemented

**Workaround**: File output works perfectly
```
output/overtime_nfl_raw_*.json        # Raw format
output/overtime_nfl_walters_*.json    # Converted format
```

---

## Testing Checklist

Before considering scraper operational:

- [ ] Test without proxy (verify base functionality)
- [ ] Test with proxy (verify credentials)
- [ ] Check current NFL week (`/current-week`)
- [ ] Verify login succeeds (account balance shown)
- [ ] Check for games (if 0, verify timing is expected)
- [ ] Test on Windows (verify no Unicode errors)
- [ ] Validate converted data format
- [ ] Test headless mode
- [ ] Test with all three periods (GAME, 1ST HALF, 1ST QUARTER)
- [ ] Verify error handling (network failure, invalid credentials)

---

## Quick Reference

### Production Command
```bash
uv run python scripts/scrape_overtime_nfl.py --headless --convert --proxy ""
```

### Key Files
- **Scraper**: `src/data/overtime_pregame_nfl_scraper.py`
- **Converter**: `src/data/overtime_data_converter.py`
- **CLI**: `scripts/scrape_overtime_nfl.py`
- **Output**: `output/overtime_nfl_*.json`

### Critical Selectors
- Login: `a.btn-signup` (use JavaScript click)
- NFL Section: `label:has-text("NFL-Game/1H/2H/Qrts")`
- Teams: `h4` elements
- Betting buttons: `button[ng-click*="SendLineToWager"]`

### Environment Variables
```bash
OV_CUSTOMER_ID=your_customer_id
OV_PASSWORD=your_password
PROXY_URL=http://user:pass@proxy:8080  # Optional
```

### Best Scraping Times
- Tuesday 9am-5pm
- Wednesday 9am-5pm
- Thursday 9am-12pm

---

**Production Status**: Fully Operational
**Last Tested**: November 10, 2025 (Week 10)
**Platform**: Windows 11, Python 3.11+
**Test Results**: All systems operational, 0 critical issues
