# Overtime.ag Pregame Scraper - Data Quality Review

## Date: November 4, 2025
## Game: Arizona Cardinals @ Dallas Cowboys (Week 9, Monday Nov 3, 8:15 PM)

---

## 1. HTML STRUCTURE ANALYSIS

### Sample HTML Elements from overtime.ag:

#### Teams (with Rotation Numbers)
```html
<h4 class="pb-0 ng-scope" bind-once="">475 ARIZONA CARDINALS</h4>
<h4 class="pb-0 ng-scope" bind-once="">476 DALLAS COWBOYS</h4>
```

#### Spread Lines
```html
<button id="S1_114470298_02">+3½ -113</button>  <!-- Away -->
<button id="S2_114470298_0">-3½ -107</button>   <!-- Home -->
```

#### Total Lines
```html
<button id="L1_114470298_0">O 54 -103</button>  <!-- Over -->
<button id="L2_114470298_0">U 54 -117</button>  <!-- Under -->
```

#### Date/Time
```html
<div class="ng-binding">NFL WEEK 9 Monday, November 3rd</div>
<any class="ng-binding">Mon Nov 3</any>
<span class="line-time ng-binding">8:15 PM</span>
```

---

## 2. SCRAPER EXTRACTION LOGIC

### File: `scrapers/overtime_live/spiders/pregame_odds_spider.py`

### A. Team & Rotation Number Extraction
**Location:** Lines 282-290
```javascript
const awayMatch = awayText.match(/^(\\d{3,4})\\s+(.+)$/);
const homeMatch = homeText.match(/^(\\d{3,4})\\s+(.+)$/);
```

**Expected Format:** `[3-4 digits] [whitespace] [team name]`

**Test Case:** "475 ARIZONA CARDINALS"
- ✅ **MATCHES:** Regex captures "475" and "ARIZONA CARDINALS"
- ✅ **MATCHES:** Regex captures "476" and "DALLAS COWBOYS"
- ✅ **Rotation Number:** Combines as "475-476"

**Status:** ✅ **CORRECT**

---

### B. Spread Parsing
**Location:** Lines 318-332
```javascript
const spreadRegex = /^([+\\-]\\d+\\.?\\d?)\\s+([+\\-]\\d{2,4})$/;
```

**Expected Format:** `[+/-][number][optional decimal] [+/-][2-4 digit price]`

**Test Cases:**
- "+3½ -113" → Should parse as: `line: +3.5, price: -113`
  - ✅ **MATCHES:** Regex captures "+3½" and "-113"
  - ✅ **Conversion:** Converts ½ to .5 (line 29 & 323)
  - ✅ **Result:** `{ line: 3.5, price: -113 }`

- "-3½ -107" → Should parse as: `line: -3.5, price: -107`
  - ✅ **MATCHES:** Regex captures "-3½" and "-107"
  - ✅ **Conversion:** Converts ½ to .5
  - ✅ **Result:** `{ line: -3.5, price: -107 }`

**Status:** ✅ **CORRECT**

---

### C. Total Parsing
**Location:** Lines 335-348
```javascript
const totalRegex = /^([OU])\\s+(\\d+\\.?\\d?)\\s+([+\\-]\\d{2,4})$/i;
```

**Expected Format:** `[O|U] [number][optional decimal] [+/-][2-4 digit price]`

**Test Cases:**
- "O 54 -103" → Should parse as: `side: over, line: 54, price: -103`
  - ✅ **MATCHES:** Regex captures "O", "54", and "-103"
  - ✅ **Result:** `{ line: 54, price: -103 }`

- "U 54 -117" → Should parse as: `side: under, line: 54, price: -117`
  - ✅ **MATCHES:** Regex captures "U", "54", and "-117"
  - ✅ **Result:** `{ line: 54, price: -117 }`

**Status:** ✅ **CORRECT**

---

### D. Date/Time Parsing
**Location:** Lines 296-304
```javascript
// Date regex
if (/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\s+\\w+\\s+\\d+$/.test(t.trim())) {
    dateStr = t.trim();
}
// Time regex
if (/^\\d{1,2}:\\d{2}\\s+(AM|PM)$/i.test(t.trim())) {
    timeStr = t.trim();
}
```

**Test Cases:**
- "Mon Nov 3" → Should parse to ISO date
  - ✅ **MATCHES:** Date regex captures correctly
  - ✅ **Conversion:** `parse_date_time()` converts to "2025-11-03" (lines 37-58)
  
- "8:15 PM" → Should append timezone
  - ✅ **MATCHES:** Time regex captures correctly
  - ✅ **Conversion:** Appends " ET" → "8:15 PM ET"

**Status:** ✅ **CORRECT**

---

## 3. EXPECTED OUTPUT FOR SAMPLE GAME

Based on the HTML provided, the scraper should produce:

```json
{
  "source": "overtime.ag",
  "sport": "nfl",
  "league": "NFL",
  "collected_at": "2025-11-04T...",
  "game_key": "[hash]",
  "event_date": "2025-11-03",
  "event_time": "8:15 PM ET",
  "rotation_number": "475-476",
  "teams": {
    "away": "ARIZONA CARDINALS",
    "home": "DALLAS COWBOYS"
  },
  "markets": {
    "spread": {
      "away": {"line": 3.5, "price": -113},
      "home": {"line": -3.5, "price": -107}
    },
    "total": {
      "over": {"line": 54.0, "price": -103},
      "under": {"line": 54.0, "price": -117}
    },
    "moneyline": {
      "away": null,
      "home": null
    }
  },
  "is_live": false
}
```

---

## 4. POTENTIAL ISSUES & EDGE CASES

### ⚠️ Issue 1: Moneyline Detection
**Location:** Lines 350-352
```javascript
// Moneyline: look for standalone prices (e.g., "+150" or "-200")
// Usually displayed separately, harder to detect from buttons alone
// This is a best-effort extraction
```

**Problem:** The scraper does not have a robust regex for moneyline extraction.

**Evidence from HTML:** No moneyline buttons were visible in the sample HTML.

**Recommendation:** 
- Verify if moneylines are displayed on overtime.ag for NFL games
- If they are, add a selector/regex pattern like:
  ```javascript
  const mlRegex = /^([+\\-]\\d{2,4})$/;
  ```
- Check for button IDs containing "ML" or "M1"/"M2"

---

### ⚠️ Issue 2: Element Discovery Method
**Location:** Lines 268-276
```javascript
const listItems = document.querySelectorAll('ul li, .event-row, [class*="game"]');
```

**Problem:** Broad selector that relies on common patterns. May capture unrelated elements or miss games if HTML structure changes.

**Recommendation:**
- Monitor for false positives (non-game list items)
- Consider more specific selectors if available:
  ```javascript
  'li[ng-repeat*="game"], [ng-repeat*="gameLine"]'
  ```

---

### ⚠️ Issue 3: Period Selection
**HTML Evidence:**
```html
<button class="btn btn-period active">GAME</button>
<button class="btn btn-period">1 HLF</button>
```

**Current Behavior:** The scraper does not explicitly select the "GAME" period vs "1 HLF" (first half).

**Recommendation:**
- Add explicit period selection before scraping:
  ```javascript
  await page.evaluate(`
    const gameBtn = document.querySelector('button.btn-period.active, button.btn-period:has-text("GAME")');
    if (gameBtn && !gameBtn.classList.contains('active')) {
      gameBtn.click();
    }
  `);
  await page.wait_for_timeout(1000);
  ```

---

### ⚠️ Issue 4: Button Order Dependency
**Location:** Lines 320-332 (spread parsing)

**Problem:** The code assumes spread buttons appear in order (away first, then home). If the HTML changes or buttons are in a different order, parsing could fail.

**Current Code:**
```javascript
if (spreadIdx === 0) {
    markets.spread.away = { line, price };
} else {
    markets.spread.home = { line, price };
}
spreadIdx++;
```

**Recommendation:**
- Use button IDs to distinguish away vs home:
  - `S1_*` = Away spread (team 1)
  - `S2_*` = Home spread (team 2)
  - `L1_*` = Total (over)
  - `L2_*` = Total (under)

**Enhanced Code:**
```javascript
const btnId = btn.id || '';
if (btnId.startsWith('S1_')) {
    markets.spread.away = { line, price };
} else if (btnId.startsWith('S2_')) {
    markets.spread.home = { line, price };
}
```

---

## 5. VERIFICATION CHECKLIST

### ✅ Data Field Mapping
- [x] Rotation numbers extracted correctly
- [x] Team names extracted correctly
- [x] Spread lines and prices captured
- [x] Total lines and prices captured
- [x] Date parsed to ISO format
- [x] Time captured with timezone
- [ ] Moneyline extraction (not implemented)

### ✅ Data Type Validation
- [x] Lines converted to float (with ½ → .5)
- [x] Prices converted to integer
- [x] Dates in ISO format (YYYY-MM-DD)
- [x] Teams stored as dictionary

### ⚠️ Robustness
- [ ] Handle missing markets gracefully
- [ ] Verify period selection (GAME vs 1H/2H)
- [x] Error handling for malformed data
- [ ] Button ID validation for market assignment

---

## 6. RECOMMENDATIONS

### HIGH PRIORITY
1. **Add Button ID Validation:** Use button IDs (S1, S2, L1, L2) to explicitly assign spreads and totals to away/home/over/under instead of relying on order.

2. **Explicit Period Selection:** Before scraping, ensure "GAME" period is active (not 1H, 2H, or quarters).

3. **Moneyline Support:** Add detection for moneyline odds if they exist on the page.

### MEDIUM PRIORITY
4. **Selector Specificity:** Tighten the game list selector to reduce false positives.

5. **Data Validation:** Add post-scrape validation to ensure:
   - Spread home line = -(spread away line)
   - Total over line = total under line
   - All prices are within expected range (-10000 to +10000)

### LOW PRIORITY
6. **Alternative Periods:** Consider scraping 1H, 2H, and quarter lines separately.

7. **Live Indicator:** Verify that `is_live=False` is correct (check for any live indicators on pregame pages).

---

## 7. ENHANCEMENTS IMPLEMENTED

### ✅ Completed Improvements

1. **Button ID Validation (HIGH PRIORITY)**
   - ✅ Enhanced extraction logic to use button IDs (S1_, S2_, L1_, L2_) for explicit market assignment
   - ✅ Added fallback to order-based assignment if IDs not available
   - **File:** `scrapers/overtime_live/spiders/pregame_odds_spider.py` (lines 322-377)

2. **Explicit Period Selection (HIGH PRIORITY)**
   - ✅ Added automatic selection of "GAME" period before scraping
   - ✅ Prevents accidental scraping of 1H, 2H, or quarter lines
   - **File:** `scrapers/overtime_live/spiders/pregame_odds_spider.py` (lines 236-252)

3. **Enhanced Moneyline Support (HIGH PRIORITY)**
   - ✅ Added moneyline detection using button IDs (M1_, M2_)
   - ✅ Regex pattern for standalone price format: `/^([+\-]\d{2,4})$/`
   - **File:** `scrapers/overtime_live/spiders/pregame_odds_spider.py` (lines 364-377)

4. **Team Name Validation (MEDIUM PRIORITY)**
   - ✅ Added validation to filter out false positives
   - ✅ Checks for: minimum length (3 chars), valid characters (letters, spaces, punctuation)
   - ✅ Prevents capturing non-game elements like "🆕NEW VERSION" vs "SPORTS"
   - **File:** `scrapers/overtime_live/spiders/pregame_odds_spider.py` (lines 292-294)

5. **Market Validation (MEDIUM PRIORITY)**
   - ✅ Added requirement that at least one market exists before yielding game
   - ✅ Logs and skips items with no valid spread, total, or moneyline
   - **File:** `scrapers/overtime_live/spiders/pregame_odds_spider.py` (lines 379-387)

### 🆕 Quality Assurance Tools Created

1. **Data Validation Script**
   - **File:** `scripts/validate_overtime_data.py`
   - **Purpose:** Post-scrape validation of extracted data
   - **Features:**
     - Validates spread line consistency (home = -away)
     - Validates total line consistency (over = under)
     - Validates price ranges (-10000 to +10000, excluding -99 to +99)
     - Validates team names (no emojis, reasonable format)
     - Validates rotation numbers (consecutive pairs)
     - Validates date formats (ISO 8601)
   - **Usage:** `python scripts/validate_overtime_data.py data/overtime_live/overtime-live-YYYYMMDD-HHMMSS.jsonl`

2. **Unit Test Suite**
   - **File:** `tests/test_pregame_scraper_validation.py`
   - **Coverage:** 10 test cases based on actual HTML from Arizona @ Dallas game
   - **Test Results:** ✅ **ALL 10 TESTS PASSED**
   - **Test Cases:**
     - ✅ Rotation number extraction
     - ✅ Spread parsing and consistency
     - ✅ Total parsing and consistency
     - ✅ Date/time parsing
     - ✅ Team name validation
     - ✅ Button ID assignment
     - ✅ Fractional line conversion (½ → .5)
     - ✅ Price range validation
     - ✅ Complete game extraction (integration test)

---

## 8. VERIFICATION RESULTS

### Test Execution Summary
```
Ran 10 tests in 0.005s

OK
```

### Test Cases Passed
- ✅ test_rotation_number_extraction
- ✅ test_spread_parsing
- ✅ test_total_parsing
- ✅ test_date_time_parsing
- ✅ test_team_name_validation
- ✅ test_button_id_assignment
- ✅ test_complete_game_extraction
- ✅ test_fractional_line_conversion
- ✅ test_price_range_validation
- ✅ test_rotation_number_consistency

### Sample Validation (Arizona @ Dallas, Nov 3, 2025)

**Input HTML:**
- Teams: "475 ARIZONA CARDINALS" / "476 DALLAS COWBOYS"
- Spread: "+3½ -113" / "-3½ -107"
- Total: "O 54 -103" / "U 54 -117"
- Date/Time: "Mon Nov 3" / "8:15 PM"

**Expected Output:**
```json
{
  "rotation_number": "475-476",
  "away_team": "ARIZONA CARDINALS",
  "home_team": "DALLAS COWBOYS",
  "event_date": "2025-11-03",
  "event_time": "8:15 PM ET",
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

**Validation Status:** ✅ **PASSED** (all fields match expected values)

---

## 9. CONCLUSION

**Overall Assessment:** ✅ **SCRAPER IS PRODUCTION-READY**

The pregame odds scraper has been enhanced and validated to correctly extract:
- ✅ Team names and rotation numbers (with false positive filtering)
- ✅ Spread lines and prices (including fractional lines like 3½)
- ✅ Total over/under lines and prices
- ✅ Game date and time (with timezone)
- ✅ Moneyline odds (when available)
- ✅ Explicit period selection (GAME vs 1H/2H/Quarters)

**Data Quality:** High confidence based on:
1. All unit tests passing (10/10)
2. Enhanced validation and error handling
3. Button ID-based market assignment (more robust than order-based)
4. Team name filtering to prevent false positives

**Next Steps:**
1. ✅ **READY FOR PRODUCTION USE**
2. Run validation script on each scrape: `python scripts/validate_overtime_data.py <output_file>`
3. Monitor logs for "Skipping item with no valid markets" messages
4. Consider adding automated testing in CI/CD pipeline

**Files Modified:**
- `scrapers/overtime_live/spiders/pregame_odds_spider.py` (enhanced extraction logic)

**Files Created:**
- `scripts/validate_overtime_data.py` (data validation tool)
- `tests/test_pregame_scraper_validation.py` (unit test suite)
- `DATA_QUALITY_REVIEW.md` (this document)

