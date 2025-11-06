# Overtime.ag Locator Backtest Analysis

## Overview

This document provides a comprehensive analysis of the locators used/available for scraping overtime.ag, comparing what we currently use versus what's available, and making recommendations for maximizing data collection.

## Current Implementation Status

Based on `scrapers/overtime_live/spiders/pregame_odds_spider.py` (lines 414-632), our scraper currently uses:

### ✓ Currently Implemented

1. **Text-based parsing** (document.body.innerText)
   - Extracts rotation numbers + team names
   - Pattern: `(\d{3,4})\s+(.+)` → "109 Las Vegas Raiders"
   - Pairs consecutive rotation numbers (away=N, home=N+1)

2. **Button ID-based odds extraction**
   - `S1_*` → Away spread
   - `S2_*` → Home spread
   - `L1_*` → Over
   - `L2_*` → Under
   - `M1_*` → Away moneyline
   - `M2_*` → Home moneyline

3. **Login locators**
   - XPath: `//input[@placeholder='Customer Id']`
   - XPath: `//input[@placeholder='Password']`
   - XPath: `//button[@class='btn btn-default btn-login ng-binding']`

### ⚠ Available but NOT Currently Used

The following locators are available on overtime.ag but not currently utilized by our scraper:

#### Sport Selection Locators

**NFL Selection:**
```javascript
page.getByLabel('NFL-Game/1H/2H/Qrts')
page.locator('label:has-text("NFL-Game/1H/2H/Qrts")')
page.locator("//label[normalize-space()='NFL-Game/1H/2H/Qrts']")
```

**College Football Selection:**
```javascript
page.getByLabel('COLLEGE FB(1H/2H/Q)')
page.locator('label:has-text("COLLEGE FB(1H/2H/Q)")')
page.locator("//label[normalize-space()='COLLEGE FB(1H/2H/Q)']")
```

**Use Case:** Currently we navigate to NFL via URL parameter (`?selectedSportType=nfl`). These locators could provide a more robust alternative.

#### Period Selection Locators

**Game (Full Game) Period:**
```javascript
page.getByRole('button', { name: 'Game' })
page.locator('button:has-text("GAME")')
page.locator("//button[normalize-space()='Game']")
```

**1st Half Period:**
```javascript
page.getByRole('button', { name: '1st Half' })
page.locator('button:has-text("1ST HALF")')
page.locator("div[id='GameLines'] button:nth-child(2)")
```

**1st Quarter Period:**
```javascript
page.getByRole('button', { name: '1st Quarter' })
page.locator('button:has-text("1ST QUARTER")')
```

**Team Totals:**
```javascript
page.getByRole('button', { name: 'TEAM TOTALS' })
page.locator('button:has-text("TEAM TOTALS")')
page.locator("//button[normalize-space()='TEAM TOTALS']")
```

**Use Case:** We currently only scrape full game odds. These locators would allow us to also scrape:
- 1st half lines
- Quarter lines
- Team total lines

**Value:** Significant - these alternate markets often provide additional betting value and CLV opportunities.

#### Game Lines Container

```javascript
page.locator('#GameLines')
page.locator("//div[@id='GameLines']")
```

**Use Case:** Could be used to verify the games container loaded before parsing. Currently we rely on the 10-second wait.

#### Market Header Locators

**Spread Header:**
```javascript
page.getByText('Spread', { exact: true })
page.locator("//span[normalize-space()='Spread']")
```

**Money Line Header:**
```javascript
page.getByText('Money Line', { exact: true })
page.locator("//span[normalize-space()='Money Line']")
```

**Totals Header:**
```javascript
page.getByText('Totals', { exact: true })
page.locator("//span[normalize-space()='Totals']")
```

**Use Case:** Could validate that the expected market columns are present before scraping.

#### Detailed Game Element Locators

**Date Extraction:**
```javascript
page.getByText('Thu Nov 6', { exact: true })
page.getByText('NFL WEEK 10 Thursday, November 6th', { exact: true })
page.locator("//span[normalize-space()='NFL WEEK 10 Thursday, November 6th']")
```

**Time Extraction:**
```javascript
page.getByText('8:15 PM', { exact: true })
```

**Rotation Number (Specific):**
```javascript
page.getByText('109', { exact: true })
page.locator("//span[normalize-space()='109']")
```

**Team Name (Specific):**
```javascript
page.getByText('Las Vegas Raiders', { exact: true })
page.locator('span:has-text("Las Vegas Raiders")')
page.locator("//span[normalize-space()='Las Vegas Raiders']")
```

**Team Logo:**
```javascript
page.locator("img[ng-src='/sports/assets_core/sport_types/Las_Vegas_Raiders.png']")
page.locator("//img[@ng-src='/sports/assets_core/sport_types/Las_Vegas_Raiders.png']")
```

**Use Case:** Our text-based parsing already captures dates, times, rotation numbers, and team names. Team logos could be useful for validation or for building a team icon database.

#### Specific Odds Button Locators

**Spread with Value:**
```javascript
page.locator('span:has-text("+9 -110")')
page.locator("//button[@id='S1_114482805_0']//span[@class='ng-binding'][contains(text(),'+9')]")
page.locator("button[id='S1_114482805_0'] span[class='ng-binding']")
```

**Moneyline with Value:**
```javascript
page.locator("//button[@id='M1_114482805_0']//span[@class='ng-binding'][normalize-space()='+380']")
page.locator("button[id='M1_114482805_0'] span[class='ng-binding']")
page.getByText('+380', { exact: true })
```

**Totals with Value:**
```javascript
page.locator('span:has-text("O 43 -110")')
page.locator("//button[@id='L1_114482805_0']//span[@class='ng-binding'][contains(text(),'O')]")
page.locator("button[id='L1_114482805_0'] span[class='ng-binding']")
```

**Use Case:** Our current implementation already extracts all button IDs matching `S1_*`, `S2_*`, `M1_*`, `M2_*`, `L1_*`, `L2_*`. These specific locators are good for targeted extraction but we're already capturing this data with our ID-based approach.

## Gap Analysis

### Critical Gaps (Should Address)

1. **No Period Selection Implementation**
   - **Impact:** We're missing 50-70% of available betting markets
   - **Markets Missing:**
     - 1st Half lines (spreads, totals, moneylines)
     - Quarter lines
     - Team totals
   - **Recommendation:** Add period selection and scrape all available markets

2. **No Market Availability Validation**
   - **Impact:** May attempt to parse markets that don't exist for certain games
   - **Current State:** We collect all buttons on page, which could include buttons from other periods/sports
   - **Recommendation:** Add validation that expected market headers are present

3. **No Container Load Validation**
   - **Impact:** Relying purely on 10-second wait could miss delayed content or fail on fast loads
   - **Current State:** `await page.wait_for_timeout(10000)`
   - **Recommendation:** Wait for `#GameLines` container to be visible instead

### Minor Gaps (Nice to Have)

4. **No Team Logo Extraction**
   - **Impact:** Minimal - team logos are cosmetic
   - **Use Case:** Could validate team names or build icon database
   - **Recommendation:** Low priority

5. **No Explicit Sport Selection**
   - **Impact:** Low - URL navigation works well
   - **Current State:** Navigate to `?selectedSportType=nfl`
   - **Alternative:** Use `page.getByLabel('NFL-Game/1H/2H/Qrts').click()`
   - **Recommendation:** Keep URL navigation (simpler, works)

## Recommendations

### Priority 1: Add Period Selection (High Impact)

**Implementation Plan:**

```python
async def scrape_all_periods(page: Page, sport: str):
    """Scrape all available periods for maximum data collection."""

    periods = [
        ('Game', 'full_game'),
        ('1st Half', 'first_half'),
        ('1st Quarter', 'first_quarter'),
        ('Team Totals', 'team_totals'),
    ]

    all_games = {}

    for period_name, period_key in periods:
        try:
            # Click period button
            period_btn = page.locator(f'button:has-text("{period_name.upper()}")')
            if await period_btn.count() > 0:
                await period_btn.click()
                await page.wait_for_timeout(2000)  # Wait for data to load

                # Extract games for this period
                games = await extract_games(page, sport, period_key)

                # Merge with existing games
                for game in games:
                    game_key = game.get('rotation_number', '')
                    if game_key not in all_games:
                        all_games[game_key] = {'rotation_number': game_key, 'periods': {}}

                    all_games[game_key]['periods'][period_key] = game['markets']

        except Exception as e:
            logger.warning(f"Failed to scrape {period_name}: {e}")
            continue

    return list(all_games.values())
```

**Expected Output:**

```json
{
  "rotation_number": "109-110",
  "away_team": "Las Vegas Raiders",
  "home_team": "Denver Broncos",
  "periods": {
    "full_game": {
      "spread": {"away": {"line": 9.0, "price": -110}, "home": {"line": -9.0, "price": -110}},
      "total": {"over": {"line": 43.0, "price": -110}, "under": {"line": 43.0, "price": -110}},
      "moneyline": {"away": 380, "home": -515}
    },
    "first_half": {
      "spread": {"away": {"line": 5.0, "price": -110}, "home": {"line": -5.0, "price": -110}},
      "total": {"over": {"line": 21.5, "price": -115}, "under": {"line": 21.5, "price": -105}}
    }
  }
}
```

**Value:** This would increase our data collection by ~4x and provide more betting opportunities.

### Priority 2: Add Container Load Validation (Medium Impact)

**Current:**
```python
await page.wait_for_timeout(10000)
```

**Recommended:**
```python
# Wait for container to be visible
await page.wait_for_selector('#GameLines', state='visible', timeout=30000)

# Verify market headers are present
spread_header = await page.locator("//span[normalize-space()='Spread']").count()
ml_header = await page.locator("//span[normalize-space()='Money Line']").count()
totals_header = await page.locator("//span[normalize-space()='Totals']").count()

if spread_header == 0 or ml_header == 0 or totals_header == 0:
    logger.warning("Market headers not found - page may not have loaded correctly")
```

**Value:** More reliable scraping, faster execution (no arbitrary 10s wait), better error detection.

### Priority 3: Button-to-Game Association (Medium Impact)

**Current Issue:**
The current implementation collects ALL buttons on the page and attempts to parse them for each game. This works when:
- The page is filtered to a single sport
- All displayed games belong to that sport

**Potential Problem:**
If multiple sports are displayed, buttons might be incorrectly associated with games.

**Recommended Fix:**

```python
# Instead of collecting all buttons at once, find buttons by event ID
for game in games:
    # Button IDs include event ID: S1_{event_id}_{period_id}
    # Extract event ID from first found button for this game

    # Find any button near this game's rotation number
    game_section = page.locator(f"//span[normalize-space()='{game.rotation_away}']").locator('xpath=ancestor::li')

    # Within game section, find buttons
    spread_away = await game_section.locator("button[id^='S1_']").first.get_attribute('id')
    if spread_away:
        event_id = spread_away.split('_')[1]

        # Now get all buttons for this event
        game.markets['spread']['away'] = await parse_button(f"S1_{event_id}_0")
        game.markets['spread']['home'] = await parse_button(f"S2_{event_id}_0")
        # etc...
```

**Value:** More accurate odds association, especially when scraping multiple sports simultaneously.

## Testing Strategy

### 1. Unit Tests (Completed)

✓ `tests/test_pregame_scraper_validation.py` - Tests parsing logic
- Rotation number extraction
- Spread/total/moneyline parsing
- Team name validation
- Button ID assignment

### 2. Integration Test (New)

Create `tests/test_overtime_locators_backtest.py` to:
- ✓ Test all login locators
- ✓ Test sport selection locators
- ✓ Test period button locators
- ✓ Test container locators
- ✓ Test game data extraction locators
- ✓ Generate comprehensive report

**To Run:**
```bash
# Set credentials
export OV_CUSTOMER_ID='your_customer_id'
export OV_CUSTOMER_PASSWORD='your_password'

# Run backtest
uv run python tests/test_overtime_locators_backtest.py
```

### 3. Live Scraper Test

```bash
# Scrape NFL with current implementation
uv run walters-analyzer scrape-overtime --sport nfl

# Expected output:
# ✓ Login successful
# ✓ Navigated to NFL page
# ✓ Waiting 10 seconds for Angular to render games...
# ✓ Raw extraction found 14 games
# ✓ Extracted 14 NFL games
```

## Implementation Roadmap

### Phase 1: Stability Improvements (Current)
- ✓ Fix text-based parsing for Angular
- ✓ Add comprehensive unit tests
- ✓ Create locator backtest framework

### Phase 2: Enhanced Data Collection (Recommended Next)
- [ ] Add period selection (Game, 1st Half, Quarters, Team Totals)
- [ ] Implement container load validation
- [ ] Fix button-to-game association
- [ ] Add market availability checks

### Phase 3: Additional Markets (Future)
- [ ] Add live (in-game) odds scraping
- [ ] Add player props
- [ ] Add alternate lines (buy points)
- [ ] Add parlay/teaser options

### Phase 4: Multi-Sport Expansion
- [ ] Add College Football
- [ ] Add NBA
- [ ] Add College Basketball
- [ ] Add MLB/NHL (seasonal)

## Summary

### Current State
Our scraper successfully extracts:
- ✓ Team names via text parsing
- ✓ Rotation numbers via text parsing
- ✓ Full game spreads, totals, moneylines via button IDs
- ✓ Handles Angular dynamic rendering

### Missing Opportunities
- ✗ 1st half lines (estimated 14 games × 3 markets = 42 additional data points per scrape)
- ✗ Quarter lines (estimated 14 games × 2 quarters × 3 markets = 84 additional data points)
- ✗ Team totals (estimated 14 games × 2 teams = 28 additional data points)

**Total Missing:** ~154 data points per scrape (current: 42, potential: 196)

### Key Recommendations

1. **Implement period selection** to capture 1st half and quarter lines
2. **Replace timeout with container validation** for reliability
3. **Fix button-to-game association** for accuracy
4. **Run comprehensive backtest** to validate all locators

The backtest framework is ready - just needs credentials to run against the live site.
