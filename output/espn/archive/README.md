# ESPN Data Archive

This directory contains legacy ESPN data files that have been consolidated and reorganized into proper directory structures.

## Archive Contents

### investigation/
Investigation files from API endpoint testing and data structure exploration.

**Files:**
- `investigation_core_api_-_team_profile_(2025).json` (9.3 KB) - Core API team profile exploration
- `investigation_site_api_v2_-_team_profile.json` (30 KB) - Site API v2 team profile testing
- `investigation_site_api_v2_-_team_schedule.json` (806 KB) - Site API v2 schedule exploration
- `investigation_site_api_v2_-_team_statistics.json` (94 KB) - Site API v2 statistics testing

**Purpose:** These files document API endpoint discovery and structure analysis performed during initial development.
**Date:** November 12, 2025
**Status:** Reference only - not used in active data pipelines

### Legacy Scoreboards (Deprecated)
- `nfl_scoreboard.json` (1.8 MB) - Old NFL scoreboard format
- `ncaaf_scoreboard.json` (417 KB) - Old NCAAF scoreboard format

**Status:** DEPRECATED - Use `scores/nfl/` and `scores/ncaaf/` instead

### Legacy Odds Files (Deprecated)
- `nfl_odds.json` (274 KB) - Old NFL odds format

**Status:** DEPRECATED - Odds now integrated into scoreboard data

### Legacy Teams File (Deprecated)
- `nfl_teams.json` (170 KB) - Old team listing format

**Status:** DEPRECATED - Team data available from current ESPN API endpoints

## Current Data Organization

As of 2025-11-24, ESPN data is organized in these proper directories:

```
output/espn/
├── scores/
│   ├── nfl/              # NFL game scores (organized)
│   └── ncaaf/            # NCAAF game scores (organized)
├── standings/
│   ├── nfl/              # NFL standings
│   └── ncaaf/            # NCAAF standings
├── stats/
│   ├── nfl/              # NFL team statistics
│   └── ncaaf/            # NCAAF team statistics
├── schedule/
│   ├── nfl/              # NFL schedule data
│   └── ncaaf/            # NCAAF schedule data
└── archive/              # This directory - legacy files only
```

## Migration Notes

**When these files were archived:**
- Date: November 24, 2025
- Reason: Consolidation and standardization of ESPN data output structure
- Impact: No active pipelines - all production code uses new directory structure

**Backward Compatibility:**
- No symlinks needed - new code doesn't reference old locations
- Safe to delete if space needed
- Kept for historical reference during transition period

## Reference Information

### NFL Scoreboard Changes
- **Old location:** `output/espn/nfl_scoreboard.json`
- **New location:** `output/espn/scores/nfl/scores_nfl_YYYYMMDD_HHMMSS.json`
- **Change date:** November 24, 2025
- **Reason:** Organize by data type and league

### NCAAF Scoreboard Changes
- **Old location:** `output/espn/ncaaf_scoreboard.json` (root)
- **Old location 2:** `output/espn/scoreboard/ncaaf/` (intermediate)
- **New location:** `output/espn/scores/ncaaf/scores_ncaaf_YYYYMMDD_HHMMSS.json`
- **Change date:** November 24, 2025
- **Reason:** Standardize with NFL and organize by data type

### Updated Clients
- `src/data/espn_nfl_scoreboard_client.py` - Updated to save to `output/espn/scores/nfl/`
- `src/data/espn_ncaaf_scoreboard_client.py` - Updated to save to `output/espn/scores/ncaaf/`
- `scripts/scrapers/scrape_espn_ncaaf_scoreboard.py` - Updated default output directory

## Cleanup Timeline

1. **Phase 1 (2025-11-24):** Archive legacy files in place
2. **Phase 2 (2025-12-08):** Review for any unexpected dependencies
3. **Phase 3 (2025-12-22):** Delete if no issues found

This allows a safe transition period to catch any issues before permanent deletion.
