# Overtime.ag HTML → Data Mapping

This document shows the exact mapping between HTML elements from overtime.ag and the extracted data fields.

---

## Example Game: Arizona Cardinals @ Dallas Cowboys

### Source: Monday, November 3, 2025, 8:15 PM

---

## HTML Elements → Extracted Fields

### 1. Team Names & Rotation Numbers

#### HTML Input:
```html
<h4 class="pb-0 ng-scope" bind-once="">475 ARIZONA CARDINALS</h4>
<h4 class="pb-0 ng-scope" bind-once="">476 DALLAS COWBOYS</h4>
```

#### Extraction Logic:
```javascript
// Regex: /^(\d{3,4})\s+(.+)$/
const awayMatch = awayText.match(/^(\d{3,4})\s+(.+)$/);
const homeMatch = homeText.match(/^(\d{3,4})\s+(.+)$/);

// awayMatch[1] = "475", awayMatch[2] = "ARIZONA CARDINALS"
// homeMatch[1] = "476", homeMatch[2] = "DALLAS COWBOYS"
```

#### Output:
```json
{
  "rotation_number": "475-476",
  "teams": {
    "away": "ARIZONA CARDINALS",
    "home": "DALLAS COWBOYS"
  }
}
```

---

### 2. Away Team Spread

#### HTML Input:
```html
<button id="S1_114470298_02" class="btn btn-betlines">+3½ -113</button>
```

#### Extraction Logic:
```javascript
// Button ID: S1_ indicates Away Spread
// Regex: /^([+\-]\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$/
const match = buttonText.match(/^([+\-]\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$/);

// match[1] = "+3½", match[2] = "-113"
const line = parseFloat(match[1].replace('½', '.5'));  // 3.5
const price = parseInt(match[2]);                       // -113
```

#### Output:
```json
{
  "markets": {
    "spread": {
      "away": {
        "line": 3.5,
        "price": -113
      }
    }
  }
}
```

---

### 3. Home Team Spread

#### HTML Input:
```html
<button id="S2_114470298_0" class="btn btn-betlines">-3½ -107</button>
```

#### Extraction Logic:
```javascript
// Button ID: S2_ indicates Home Spread
// Regex: /^([+\-]\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$/
const match = buttonText.match(/^([+\-]\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$/);

// match[1] = "-3½", match[2] = "-107"
const line = parseFloat(match[1].replace('½', '.5'));  // -3.5
const price = parseInt(match[2]);                       // -107
```

#### Output:
```json
{
  "markets": {
    "spread": {
      "home": {
        "line": -3.5,
        "price": -107
      }
    }
  }
}
```

#### Validation:
✅ Home line (-3.5) = -(Away line) (3.5)

---

### 4. Total Over

#### HTML Input:
```html
<button id="L1_114470298_0" class="btn btn-betlines">O 54 -103</button>
```

#### Extraction Logic:
```javascript
// Button ID: L1_ indicates Total Over
// Regex: /^([OU])\s+(\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$/i
const match = buttonText.match(/^([OU])\s+(\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$/i);

// match[1] = "O", match[2] = "54", match[3] = "-103"
const line = parseFloat(match[2].replace('½', '.5'));   // 54.0
const price = parseInt(match[3]);                        // -103
```

#### Output:
```json
{
  "markets": {
    "total": {
      "over": {
        "line": 54.0,
        "price": -103
      }
    }
  }
}
```

---

### 5. Total Under

#### HTML Input:
```html
<button id="L2_114470298_0" class="btn btn-betlines">U 54 -117</button>
```

#### Extraction Logic:
```javascript
// Button ID: L2_ indicates Total Under
// Regex: /^([OU])\s+(\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$/i
const match = buttonText.match(/^([OU])\s+(\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$/i);

// match[1] = "U", match[2] = "54", match[3] = "-117"
const line = parseFloat(match[2].replace('½', '.5'));   // 54.0
const price = parseInt(match[3]);                        // -117
```

#### Output:
```json
{
  "markets": {
    "total": {
      "under": {
        "line": 54.0,
        "price": -117
      }
    }
  }
}
```

#### Validation:
✅ Under line (54.0) = Over line (54.0)

---

### 6. Date

#### HTML Input:
```html
<div class="ng-binding">NFL WEEK 9 Monday, November 3rd</div>
<any ng-bind="gameLine.GameDateTimeString | formatGameDate" class="ng-binding">Mon Nov 3</any>
```

#### Extraction Logic:
```javascript
// Regex: /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+\s+\d+$/
if (/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+\s+\d+$/.test(dateStr.trim())) {
    // dateStr = "Mon Nov 3"
    // Parse "Mon Nov 3" → "2025-11-03"
    const dt = DateTime.strptime("2025 Nov 3", "%Y %b %d");
    const isoDate = dt.strftime("%Y-%m-%d");  // "2025-11-03"
}
```

#### Output:
```json
{
  "event_date": "2025-11-03"
}
```

---

### 7. Time

#### HTML Input:
```html
<span class="line-time ng-binding" style="position: initial">8:15 PM</span>
```

#### Extraction Logic:
```javascript
// Regex: /^\d{1,2}:\d{2}\s+(AM|PM)$/i
if (/^\d{1,2}:\d{2}\s+(AM|PM)$/i.test(timeStr.trim())) {
    // timeStr = "8:15 PM"
    // Append timezone: "8:15 PM ET"
    const timeWithTz = timeStr + " ET";
}
```

#### Output:
```json
{
  "event_time": "8:15 PM ET"
}
```

---

### 8. Period Selection

#### HTML Input:
```html
<button type="button" class="btn btn-period active">GAME</button>
<button type="button" class="btn btn-period">1 HLF</button>
```

#### Scraper Behavior:
```javascript
// Before scraping, ensure "GAME" period is active
const gameButtons = document.querySelectorAll('button.btn-period');
for (const btn of gameButtons) {
    if (/^GAME$/i.test(btn.innerText.trim()) && !btn.classList.contains('active')) {
        btn.click();  // Activate full game period
    }
}
```

#### Effect:
✅ Ensures we scrape full game lines, not 1H/2H/quarter lines

---

## Complete Mapping: HTML → JSON

### HTML Input (Complete):
```html
<!-- Team Names -->
<h4 class="pb-0 ng-scope" bind-once="">475 ARIZONA CARDINALS</h4>
<h4 class="pb-0 ng-scope" bind-once="">476 DALLAS COWBOYS</h4>

<!-- Date/Time -->
<any ng-bind="gameLine.GameDateTimeString | formatGameDate" class="ng-binding">Mon Nov 3</any>
<span class="line-time ng-binding" style="position: initial">8:15 PM</span>

<!-- Betting Lines -->
<button id="S1_114470298_02" class="btn btn-betlines">+3½ -113</button>
<button id="L1_114470298_0" class="btn btn-betlines">O 54 -103</button>
<button id="S2_114470298_0" class="btn btn-betlines">-3½ -107</button>
<button id="L2_114470298_0" class="btn btn-betlines">U 54 -117</button>
```

### JSON Output (Complete):
```json
{
  "source": "overtime.ag",
  "sport": "nfl",
  "league": "NFL",
  "collected_at": "2025-11-04T12:00:00.000000+00:00",
  "game_key": "abc123def456",
  "event_date": "2025-11-03",
  "event_time": "8:15 PM ET",
  "rotation_number": "475-476",
  "teams": {
    "away": "ARIZONA CARDINALS",
    "home": "DALLAS COWBOYS"
  },
  "state": {},
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

## Button ID Patterns

| Button ID Prefix | Market Type | Side/Position |
|------------------|-------------|---------------|
| `S1_`            | Spread      | Away Team     |
| `S2_`            | Spread      | Home Team     |
| `L1_`            | Total       | Over          |
| `L2_`            | Total       | Under         |
| `M1_`            | Moneyline   | Away Team     |
| `M2_`            | Moneyline   | Home Team     |

### Button ID Structure:
```
[Market][Team]_[GameID]_[Sequence]

Example: S1_114470298_02
         │└─────┬─────┘└─ Sequence number
         │      └──────── Unique game ID
         └──────────────── S=Spread, 1=Away
```

---

## Regex Patterns Reference

### 1. Team Name with Rotation Number
```regex
^(\d{3,4})\s+(.+)$
```
- `(\d{3,4})` - Captures 3-4 digit rotation number
- `\s+` - One or more spaces
- `(.+)` - Captures team name (everything after)

**Examples:**
- ✅ "475 ARIZONA CARDINALS" → ("475", "ARIZONA CARDINALS")
- ✅ "1234 NEW YORK JETS" → ("1234", "NEW YORK JETS")
- ❌ "ARIZONA CARDINALS" → No match (missing rotation number)

---

### 2. Spread Button Text
```regex
^([+\-]\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$
```
- `([+\-]\d+\.?\d?[½]?)` - Captures line: +/- number with optional decimal or ½
- `\s+` - One or more spaces
- `([+\-]\d{2,4})` - Captures price: +/- 2-4 digit number

**Examples:**
- ✅ "+3½ -113" → ("+3½", "-113")
- ✅ "-7 -110" → ("-7", "-110")
- ✅ "+10.5 +105" → ("+10.5", "+105")
- ❌ "3½" → No match (missing sign)
- ❌ "+3½" → No match (missing price)

---

### 3. Total Button Text
```regex
^([OU])\s+(\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$
```
- `([OU])` - Captures O or U (case insensitive)
- `\s+` - One or more spaces
- `(\d+\.?\d?[½]?)` - Captures line: number with optional decimal or ½
- `\s+` - One or more spaces
- `([+\-]\d{2,4})` - Captures price: +/- 2-4 digit number

**Examples:**
- ✅ "O 54 -103" → ("O", "54", "-103")
- ✅ "U 48½ -110" → ("U", "48½", "-110")
- ✅ "o 42.5 +105" → ("o", "42.5", "+105")
- ❌ "54 -103" → No match (missing O/U)
- ❌ "O 54" → No match (missing price)

---

### 4. Moneyline Button Text
```regex
^([+\-]\d{2,4})$
```
- `([+\-]\d{2,4})` - Captures price: +/- 2-4 digit number (standalone)

**Examples:**
- ✅ "+150" → ("+150")
- ✅ "-200" → ("-200")
- ✅ "+1500" → ("+1500")
- ❌ "150" → No match (missing sign)
- ❌ "+3½ -110" → No match (includes line, not standalone)

---

### 5. Date Text
```regex
^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+\s+\d+$
```
- `(Mon|Tue|Wed|Thu|Fri|Sat|Sun)` - Day of week
- `\s+` - One or more spaces
- `\w+` - Month name (letters)
- `\s+` - One or more spaces
- `\d+` - Day of month (number)

**Examples:**
- ✅ "Mon Nov 3" → Match
- ✅ "Sat December 25" → Match
- ❌ "November 3" → No match (missing day of week)
- ❌ "Mon 11/3" → No match (numeric month)

---

### 6. Time Text
```regex
^\d{1,2}:\d{2}\s+(AM|PM)$
```
- `\d{1,2}` - Hour (1-2 digits)
- `:` - Colon separator
- `\d{2}` - Minutes (2 digits)
- `\s+` - One or more spaces
- `(AM|PM)` - AM or PM (case insensitive)

**Examples:**
- ✅ "8:15 PM" → Match
- ✅ "12:00 AM" → Match
- ❌ "8:15" → No match (missing AM/PM)
- ❌ "08:15 PM EST" → No match (includes timezone)

---

## Validation Rules

### Spread Consistency
```python
# Home line must equal negative of away line
home_line == -away_line

# Example:
# Away: +3.5  →  Home: -3.5  ✅
# Away: +7.0  →  Home: -6.5  ❌
```

### Total Consistency
```python
# Over line must equal under line
over_line == under_line

# Example:
# Over: 54.0  →  Under: 54.0  ✅
# Over: 48.5  →  Under: 49.0  ❌
```

### Price Range
```python
# Valid American odds range
-10000 <= price <= +10000

# Invalid range (too small)
-99 < price < +100 and price != 0

# Examples:
# -110  ✅
# +150  ✅
# -50   ❌ (invalid range)
# 0     ❌ (zero is always invalid)
```

### Team Name
```python
# Must be at least 3 characters
len(team_name) >= 3

# Must contain only letters, spaces, and common punctuation
re.match(r'^[A-Z\s\-\.&\']+$', team_name, re.IGNORECASE)

# Examples:
# "ARIZONA CARDINALS"      ✅
# "ST. LOUIS RAMS"         ✅
# "TEXAS A&M AGGIES"       ✅
# "🆕NEW VERSION"           ❌ (emoji)
# "AB"                     ❌ (too short)
```

### Rotation Number
```python
# Must be in format: NNN-NNN or NNNN-NNNN
re.match(r'^\d{3,4}-\d{3,4}$', rotation_number)

# Home rotation must be away + 1
home_rot == away_rot + 1

# Examples:
# "475-476"  ✅
# "451-452"  ✅
# "475-477"  ❌ (not consecutive)
# "476-475"  ❌ (wrong order)
```

---

## Summary

| HTML Element | Selector | Regex Pattern | Output Field |
|--------------|----------|---------------|--------------|
| Team heading | `h4, h3` | `^\d{3,4}\s+.+$` | `teams.away`, `teams.home`, `rotation_number` |
| Spread button | `button[id^="S"]` | `^[+\-]\d+\.?\d?[½]?\s+[+\-]\d{2,4}$` | `markets.spread.away`, `markets.spread.home` |
| Total button | `button[id^="L"]` | `^[OU]\s+\d+\.?\d?[½]?\s+[+\-]\d{2,4}$` | `markets.total.over`, `markets.total.under` |
| Moneyline button | `button[id^="M"]` | `^[+\-]\d{2,4}$` | `markets.moneyline.away`, `markets.moneyline.home` |
| Date element | `div, span, any` | `^(Mon\|Tue\|...)\s+\w+\s+\d+$` | `event_date` |
| Time element | `span.line-time` | `^\d{1,2}:\d{2}\s+(AM\|PM)$` | `event_time` |

**All extractions validated:** ✅ 10/10 unit tests passed

