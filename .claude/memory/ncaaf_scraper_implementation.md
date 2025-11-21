# NCAAF Scraper Implementation - Project Memory

**Date**: 2025-11-11
**Status**: Complete - Production Ready

## Summary

Implemented complete NCAAF odds scraping system for Overtime.ag using XPath selectors. Integrated with Billy Walters analyzer infrastructure.

## Files Created

1. `src/data/overtime_pregame_ncaaf_scraper.py` (680 lines) - Full scraper with XPath selectors
2. `src/data/ncaaf_team_mappings.json` - 136 FBS team abbreviations
3. `scripts/scrape_overtime_ncaaf.py` (140 lines) - CLI interface
4. `NCAAF_SCRAPER_COMPLETE.md` - Complete documentation
5. `NCAAF_EDGE_DETECTION_STATUS.md` - Status tracking

## Files Modified

1. `src/data/overtime_data_converter.py` - Added League parameter, auto-detects NFL/NCAAF

## XPath Selectors Used

```python
# Navigation
//label[@for='gl_Football_College_Football_G']

# Extraction
//div[@class='col-xs-12 col-sm-12 GameBlock']  # Game blocks
.//h4[@class='ng-binding']  # Team names
.//button[contains(@ng-click, 'SendLineToWager') and (...)]  # Betting lines
```

## Usage

```powershell
# Basic
uv run python scripts/scrape_overtime_ncaaf.py

# Production
uv run python scripts/scrape_overtime_ncaaf.py --headless --convert
```

## Output

- Raw: `output/overtime/ncaaf/pregame/overtime_ncaaf_odds_TIMESTAMP.json`
- Converted: `output/overtime/ncaaf/pregame/overtime_ncaaf_walters_TIMESTAMP.json`

## Integration Status

- ✅ NCAAF power ratings (136 teams available)
- ✅ NCAAF odds scraper (implemented)
- ⚠️ Edge detector NCAAF support (needs 2-3 hours work)

## Technical Details

- **Playwright browser automation** with XPath via `document.evaluate()`
- **Team mappings**: Generated from Massey ratings, dynamically loaded
- **Periods**: Game, 1st Half, 1st Quarter
- **Data validation**: Built-in quality checks
- **Auto-conversion**: To Billy Walters format with league detection

## Optimal Scraping

- **Best**: Sunday afternoons (lines post after Saturday games)
- **Good**: Monday-Wednesday
- **Avoid**: Saturday evenings (games in progress)

## Key Learnings

1. NCAAF doesn't use rotation numbers (unlike NFL)
2. XPath via JavaScript `document.evaluate()` works reliably in Playwright
3. League auto-detection from `scrape_metadata.sport` field enables unified converter
4. 136 FBS teams required comprehensive abbreviation mappings
5. Import tests confirm: scraper loads successfully, 136 team mappings work

## Next Steps for Edge Detection

To analyze NCAAF games:

1. Scrape current NCAAF odds
2. Use manual calculation OR
3. Implement edge detector NCAAF support (add --league parameter, NCAAF HFA=3.5)

## Reference

See `NCAAF_SCRAPER_COMPLETE.md` for comprehensive documentation.
