# Overtime.ag Scraper Fix Summary

## Problem

The overtime.ag pregame odds scraper was extracting invalid data:

**Before Fix:**
```json
{
  "away_team": "🆕NEW VERSION",
  "home_team": "SPORTS",
  "markets": { ...all null... }
}
```

The scraper was picking up navigation elements instead of actual game data, and extracting 0 valid games.

## Root Cause

**overtime.ag uses AngularJS** which renders content dynamically as text rather than structured DOM elements. The original extraction code used DOM queries like:

```javascript
document.querySelectorAll('ul li, .event-row, [class*="game"]')
const headings = item.querySelectorAll('h4, h3, [class*="team"]')
```

These selectors didn't match the Angular-rendered structure, causing the scraper to fail.

## Solution

### Text-Based Parsing Approach

The fix replaces DOM queries with **text content parsing**:

```javascript
// Parse document.body.innerText instead of DOM structure
const allText = document.body.innerText;
const lines = allText.split('\n');

// Find rotation numbers + team names in text
for (let i = 0; i < lines.length; i++) {
    const match = line.match(/^(\d{3,4})\s+(.+)$/);
    // Extract: "109 Las Vegas Raiders" → {rotation: "109", team: "Las Vegas Raiders"}
}
```

### Key Changes

1. **Wait for Angular rendering**: Added 10-second wait for page to fully render
   ```python
   await page.wait_for_timeout(10000)
   ```

2. **Text-based team extraction**: Parse `document.body.innerText` to find rotation numbers
   - Pattern: `109 Las Vegas Raiders`
   - Validates team names (length ≥ 3, no emojis, valid characters)
   - Filters out UI elements: "NEW VERSION", "SPORTS", "GAME", etc.

3. **Pair consecutive rotation numbers**: Games have consecutive rotation numbers (away=N, home=N+1)
   - `109 Las Vegas Raiders` + `110 Denver Broncos` → one game
   - Validates: `homeRotation === awayRotation + 1`

4. **Button ID-based odds extraction**: Collect all buttons by ID and parse odds
   - `S1_*` = away spread, `S2_*` = home spread
   - `L1_*` = over, `L2_*` = under
   - `M1_*` = away moneyline, `M2_*` = home moneyline

### Expected Output

**After Fix:**
```json
{
  "rotation_number": "109-110",
  "away_team": "Las Vegas Raiders",
  "home_team": "Denver Broncos",
  "markets": {
    "spread": {
      "away": {"line": 3.5, "price": -113},
      "home": {"line": -3.5, "price": -107}
    },
    "total": {
      "over": {"line": 54.0, "price": -103},
      "under": {"line": 54.0, "price": -117}
    }
  }
}
```

## Testing

### Validation Tests (All Pass)
```bash
$ uv run pytest tests/test_pregame_scraper_validation.py -v
✓ test_rotation_number_extraction
✓ test_spread_parsing
✓ test_total_parsing
✓ test_date_time_parsing
✓ test_team_name_validation
✓ test_button_id_assignment
✓ test_complete_game_extraction
... 10 passed
```

### Test Coverage

The validation tests (`tests/test_pregame_scraper_validation.py`) verify:

1. **Rotation number extraction**: `"475 ARIZONA CARDINALS"` → `{rotation: "475", team: "ARIZONA CARDINALS"}`
2. **Spread parsing**: `"+3½ -113"` → `{line: 3.5, price: -113}`
3. **Total parsing**: `"O 54 -103"` → `{line: 54.0, price: -103}`
4. **Date/time parsing**: `"Mon Nov 3"`, `"8:15 PM"` → `"2025-11-03"`, `"8:15 PM ET"`
5. **Team name validation**: Filters invalid names (emojis, short names, special characters)
6. **Button ID mapping**: `S1_*` → away, `S2_*` → home, etc.

## Known Limitations

### Button-to-Game Association

The current implementation collects **all buttons on the page** and attempts to parse them for each game. This works when:
- The page is filtered to a single sport (NFL, NBA, etc.)
- All displayed games belong to that sport

**Potential issue**: If multiple sports are displayed simultaneously, buttons might be incorrectly associated with games.

**Future improvement**: Map button event IDs to rotation numbers for precise association.

## Files Changed

1. **scrapers/overtime_live/spiders/pregame_odds_spider.py**
   - Line 414-632: Replaced `_extract_games_js()` function
   - Added 10-second Angular wait
   - Implemented text-based parsing
   - Added logging: `"Raw extraction found {N} games"`

2. **test_text_extraction.py** (new)
   - Playwright-based test with mock Angular page
   - Validates team extraction, pairing, and market parsing

## Commits

1. `56effd0` - Replace DOM-based extraction with text-parsing for Angular compatibility
2. `906a7dd` - Add test for text-based extraction logic

## How to Run

```bash
# Scrape NFL games from overtime.ag
uv run walters-analyzer scrape-overtime --sport nfl

# Expected output:
# ✓ Login successful
# ✓ Navigated to NFL page
# ✓ Waiting 10 seconds for Angular to render games...
# ✓ Raw extraction found 14 games
# ✓ Extracted 14 NFL games
```

## Previous Session Context

This fix addresses issues identified in a previous Windows session where:
- Test script (`test_extraction.py`) successfully found 28 teams (14 games) using text parsing
- The spider's DOM-based approach extracted 0 valid games
- Invalid data: `"🆕NEW VERSION"` and `"SPORTS"` instead of team names

The text-parsing approach was proven to work and has now been integrated into the spider.
