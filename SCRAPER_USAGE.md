# Overtime.ag Pregame Scraper - Usage Guide

## Quick Start

### 1. Set Up Environment Variables

Create a `.env` file in the project root with your overtime.ag credentials:

```bash
# Overtime.ag Authentication
OV_CUSTOMER_ID=your_customer_id_here
OV_CUSTOMER_PASSWORD=your_password_here

# Optional: Output directory
OVERTIME_OUT_DIR=./data/overtime_live
```

### 2. Run the Scraper

#### Scrape NFL Games Only
```bash
uv run walters-analyzer scrape-overtime --sport nfl
```

#### Scrape College Football Only
```bash
uv run walters-analyzer scrape-overtime --sport cfb
```

#### Scrape Both NFL and College Football
```bash
uv run walters-analyzer scrape-overtime --sport both
```

### 3. Validate the Scraped Data

After scraping, validate the data quality:

```bash
python3 scripts/validate_overtime_data.py data/overtime_live/overtime-live-20251103-*.jsonl
```

The validation script will check:
- ✅ Spread line consistency (home = -away)
- ✅ Total line consistency (over = under)
- ✅ Price ranges are valid
- ✅ Team names are properly formatted
- ✅ Rotation numbers are consecutive
- ✅ Dates are in ISO format

---

## What Gets Scraped

The pregame scraper extracts:

### Game Information
- **Rotation Numbers**: e.g., "475-476"
- **Teams**: Away and Home team names
- **Event Date**: ISO format (e.g., "2025-11-03")
- **Event Time**: With timezone (e.g., "8:15 PM ET")

### Betting Markets
- **Spread**: Away and home lines with prices
  - Example: Away +3½ -113, Home -3½ -107
- **Total**: Over and under lines with prices
  - Example: O 54 -103, U 54 -117
- **Moneyline**: Away and home prices (when available)
  - Example: Away +150, Home -180

### Output Formats
The scraper produces three output formats:
1. **JSONL** (`.jsonl`) - One JSON object per line, easy to stream
2. **Parquet** (`.parquet`) - Compressed columnar format for analysis
3. **CSV** (`.csv`) - Flattened format with columns for each market

---

## Output Files

Files are saved to: `data/overtime_live/`

File naming format: `overtime-live-YYYYMMDD-HHMMSS.[jsonl|parquet|csv]`

Example:
```
data/overtime_live/
├── overtime-live-20251103-120640.jsonl
├── overtime-live-20251103-120640.parquet
└── overtime-live-20251103-120640.csv
```

---

## Sample Output

### JSONL Format
```json
{
  "source": "overtime.ag",
  "sport": "nfl",
  "league": "NFL",
  "collected_at": "2025-11-03T12:06:40.123456+00:00",
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

### CSV Format
```csv
source,sport,league,event_date,event_time,rotation_number,away_team,home_team,spread_away_line,spread_away_price,spread_home_line,spread_home_price,total_over_line,total_over_price,total_under_line,total_under_price,moneyline_away_price,moneyline_home_price
overtime.ag,nfl,NFL,2025-11-03,8:15 PM ET,475-476,ARIZONA CARDINALS,DALLAS COWBOYS,3.5,-113,-3.5,-107,54.0,-103,54.0,-117,,
```

---

## Enhanced Features

### 1. Automatic Period Selection
The scraper automatically selects the "GAME" period (full game lines) to avoid accidentally scraping 1H, 2H, or quarter lines.

### 2. Button ID-Based Market Assignment
Markets are assigned using button IDs for robustness:
- `S1_*` = Away spread
- `S2_*` = Home spread
- `L1_*` = Total over
- `L2_*` = Total under
- `M1_*` = Away moneyline
- `M2_*` = Home moneyline

### 3. False Positive Filtering
Team name validation prevents capturing non-game elements:
- Minimum 3 characters
- Only letters, spaces, and common punctuation
- No emojis or special characters

### 4. Market Validation
Games must have at least one valid market (spread, total, or moneyline) to be included in output.

---

## Validation Script Output

### Successful Validation
```
================================================================================
VALIDATION SUMMARY
================================================================================
Total Games Validated: 45
Passed: 45
Warnings: 0
Errors: 0

================================================================================
✅ VALIDATION PASSED
================================================================================
```

### Validation with Warnings
```
================================================================================
VALIDATION SUMMARY
================================================================================
Total Games Validated: 50
Passed: 48
Warnings: 2
Errors: 0

--------------------------------------------------------------------------------
WARNINGS:
--------------------------------------------------------------------------------
[WARN] TEAM A @ TEAM B: Rotation numbers not consecutive: 475-477
[WARN] TEAM C @ TEAM D: Missing rotation number

================================================================================
⚠️  VALIDATION PASSED WITH WARNINGS
================================================================================
```

### Validation with Errors
```
================================================================================
VALIDATION SUMMARY
================================================================================
Total Games Validated: 40
Passed: 37
Warnings: 1
Errors: 2

--------------------------------------------------------------------------------
WARNINGS:
--------------------------------------------------------------------------------
[WARN] TEAM A @ TEAM B: Rotation numbers not consecutive: 451-453

--------------------------------------------------------------------------------
ERRORS:
--------------------------------------------------------------------------------
[ERROR] 🆕NEW VERSION @ SPORTS: Invalid away team name: '🆕NEW VERSION'
[ERROR] TEAM X @ TEAM Y: Spread inconsistency: away=3.5, home=4.5 (expected -3.5)

================================================================================
❌ VALIDATION FAILED
================================================================================
```

---

## Troubleshooting

### Issue: No games scraped

**Possible causes:**
1. Login credentials not set in `.env`
2. Overtime.ag website structure changed
3. No games available at the time of scraping

**Solutions:**
1. Verify `.env` file has correct `OV_CUSTOMER_ID` and `OV_CUSTOMER_PASSWORD`
2. Check scraper logs for errors
3. Try scraping during peak betting hours

### Issue: Validation errors for spread/total consistency

**Possible causes:**
1. Button order changed on website
2. Button IDs not available
3. Website displaying different line types

**Solutions:**
1. Check that period is set to "GAME" (not 1H/2H)
2. Review scraped HTML in `snapshots/pregame_main.png`
3. Update button ID patterns if needed

### Issue: False positive games captured

**Possible causes:**
1. Website added new promotional banners
2. HTML structure changed

**Solutions:**
1. Review team name validation regex
2. Add additional filtering in `_extract_games_js()`
3. Check scraper logs for "Skipping item with no valid markets"

---

## Testing

Run the unit test suite to verify scraper logic:

```bash
python3 tests/test_pregame_scraper_validation.py
```

Expected output:
```
test_rotation_number_extraction ... ok
test_spread_parsing ... ok
test_total_parsing ... ok
test_date_time_parsing ... ok
test_team_name_validation ... ok
test_button_id_assignment ... ok
test_complete_game_extraction ... ok
test_fractional_line_conversion ... ok
test_price_range_validation ... ok
test_rotation_number_consistency ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.005s

OK
```

---

## Integration with Billy Walters Analyzer

Once you have validated data, you can use it in your betting analysis:

```bash
# Example: Load overtime.ag data for analysis
python3 -c "
from walters_analyzer.ingest.overtime_loader import load_overtime_data
games = load_overtime_data('data/overtime_live/overtime-live-20251103-120640.jsonl')
print(f'Loaded {len(games)} games')
"
```

---

## Best Practices

1. **Always validate data after scraping**
   ```bash
   uv run walters-analyzer scrape-overtime --sport nfl && \
   python3 scripts/validate_overtime_data.py data/overtime_live/overtime-live-*.jsonl | tail -1
   ```

2. **Schedule scraping during optimal times**
   - NFL: Thursday-Monday (game days)
   - CFB: Tuesday-Saturday (game days)
   - Best times: 2-4 hours before kickoff

3. **Monitor for website changes**
   - Check `snapshots/pregame_main.png` periodically
   - Review scraper logs for warnings
   - Run validation tests regularly

4. **Keep credentials secure**
   - Never commit `.env` file
   - Use environment variables in production
   - Rotate credentials periodically

---

## Support

For issues or questions:
1. Check `DATA_QUALITY_REVIEW.md` for detailed scraper analysis
2. Review scraper logs in console output
3. Run validation script to identify data quality issues
4. Check `snapshots/` directory for debugging screenshots

