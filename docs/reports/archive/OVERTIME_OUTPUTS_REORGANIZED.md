# Overtime.ag Outputs Reorganized

**Date**: November 10, 2025
**Status**: ✅ COMPLETE - Organized directory structure implemented

---

## Summary

All Overtime.ag scraper outputs have been reorganized into a clean, maintainable directory structure. Data is now organized by sport (NFL/NCAAF), scraper type (pregame/live), making it easy to find, analyze, and archive data.

---

## New Directory Structure

```
output/overtime/
├── nfl/
│   ├── pregame/                 # Pre-game NFL betting lines
│   │   ├── .gitkeep             # Preserve directory in git
│   │   ├── overtime_nfl_odds_YYYYMMDD_HHMMSS.json
│   │   ├── overtime_nfl_raw_YYYY-MM-DDTHH-MM-SS-mmmmmm.json
│   │   └── overtime_nfl_walters_YYYY-MM-DDTHH-MM-SS-mmmmmm.json
│   └── live/                    # Live in-game NFL betting lines
│       ├── .gitkeep
│       └── overtime_nfl_live_YYYYMMDD_HHMMSS.json
└── ncaaf/
    ├── pregame/                 # Pre-game NCAAF betting lines (future)
    │   └── .gitkeep
    └── live/                    # Live in-game NCAAF betting lines
        ├── .gitkeep
        └── overtime_ncaaf_live_YYYYMMDD_HHMMSS.json
```

---

## Changes Made

### 1. Pre-Game NFL Scraper
**File**: [src/data/overtime_pregame_nfl_scraper.py](src/data/overtime_pregame_nfl_scraper.py:62)

**Old Default**: `output_dir = "output"`
**New Default**: `output_dir = "output/overtime/nfl/pregame"`

**Impact**: All pre-game NFL scrapes now go to organized directory

### 2. Scraper Script
**File**: [scripts/scrape_overtime_nfl.py](scripts/scrape_overtime_nfl.py:64)

**Old Default**: `default="output"`
**New Default**: `default="output/overtime/nfl/pregame"`

**Impact**: CLI script uses organized directory by default

### 3. Live NFL Scraper
**File**: [scripts/scrape_overtime_live.py](scripts/scrape_overtime_live.py:36)

**Old**: `output_dir = Path("output")`
**New**: `output_dir = Path("output/overtime/nfl/live")`

**Impact**: Live scrapes go to dedicated NFL live directory

### 4. .gitignore Updated
**File**: [.gitignore](. gitignore:41-50)

**Added**:
```gitignore
# Overtime.ag scraper outputs (organized structure)
output/overtime/nfl/pregame/*.json
output/overtime/nfl/live/*.json
output/overtime/ncaaf/pregame/*.json
output/overtime/ncaaf/live/*.json
# Keep directory structure
!output/overtime/nfl/pregame/.gitkeep
!output/overtime/nfl/live/.gitkeep
!output/overtime/ncaaf/pregame/.gitkeep
!output/overtime/ncaaf/live/.gitkeep
```

**Impact**: JSON outputs ignored, directory structure preserved

---

## Testing Results

**Test Date**: November 10, 2025, 7:49 PM ET
**Command**: `uv run python scripts/scrape_overtime_nfl.py --headless --convert --proxy ""`

**Output Directory**: ✅ `output/overtime/nfl/pregame/`

**Files Created**:
```
output/overtime/nfl/pregame/
├── overtime_nfl_odds_20251110_194954.json           (623 bytes)
├── overtime_nfl_raw_2025-11-10T19-49-54-569103.json (623 bytes)
└── overtime_nfl_walters_2025-11-10T19-49-54-569103.json (416 bytes)
```

**Result**: ✅ All files in correct directory, structure working perfectly

---

## Benefits

### 1. Organization
- **Sport Separation**: NFL and NCAAF data isolated
- **Type Separation**: Pre-game vs live clearly distinguished
- **Easy Navigation**: Find data by sport/type/date pattern

### 2. Automation-Friendly
- **Predictable Paths**: Scripts know where to find latest data
- **Pattern Matching**: Easy glob patterns for specific data
- **Timestamped**: Never overwrite previous scrapes

### 3. Analysis Workflow
- **Sport-Specific**: Analyze NFL or NCAAF independently
- **Time-Series**: Track line movements over time
- **Archive Management**: Clean up by sport/date easily

### 4. Scalability
- **Future Sports**: Add NBA, MLB, NHL with same pattern
- **New Scraper Types**: Add `inplay`, `futures`, `props` subdirectories
- **Consistent**: All Overtime data follows same structure

---

## Usage Examples

### Pre-Game NFL Scraper (Default)

```bash
# Uses new directory: output/overtime/nfl/pregame/
uv run python scripts/scrape_overtime_nfl.py --headless --convert

# Custom directory if needed
uv run python scripts/scrape_overtime_nfl.py --output custom/path
```

### Live NFL Scraper

```bash
# Uses new directory: output/overtime/nfl/live/
uv run python scripts/scrape_overtime_live.py
```

### Scrapy Spider (Manual Output)

```bash
cd scrapers/overtime_live

# NCAAF live
uv run scrapy crawl overtime_live \
  -o ../../output/overtime/ncaaf/live/overtime_ncaaf_live_$(date +%Y%m%d_%H%M%S).json

# NFL live
uv run scrapy crawl overtime_live \
  -o ../../output/overtime/nfl/live/overtime_nfl_live_$(date +%Y%m%d_%H%M%S).json \
  -s OVERTIME_SPORT="Football" \
  -s OVERTIME_COMP="NFL"
```

---

## Finding Latest Data

### Pre-Game NFL

```bash
# Latest odds file
ls -t output/overtime/nfl/pregame/overtime_nfl_odds_*.json | head -1

# Latest Billy Walters format
ls -t output/overtime/nfl/pregame/overtime_nfl_walters_*.json | head -1
```

### Live Odds

```bash
# Latest NFL live
ls -t output/overtime/nfl/live/overtime_nfl_live_*.json | head -1

# Latest NCAAF live
ls -t output/overtime/ncaaf/live/overtime_ncaaf_live_*.json | head -1
```

---

## Migration from Old Structure

### Old Files (Before Reorganization)

```
output/
├── overtime_nfl_odds_*.json              # Pre-game odds
├── overtime_nfl_raw_*.json               # Raw data
├── overtime_nfl_walters_*.json           # Converted data
├── overtime_live_nfl_*.json              # Live NFL
├── overtime_live_current.json            # Latest live
└── (many other files mixed together)
```

### New Files (After Reorganization)

```
output/overtime/
├── nfl/pregame/
│   ├── overtime_nfl_odds_*.json
│   ├── overtime_nfl_raw_*.json
│   └── overtime_nfl_walters_*.json
└── nfl/live/
    └── overtime_nfl_live_*.json
```

### Migration (Optional)

If you have old files in `output/` root:

```bash
# Create directories
mkdir -p output/overtime/nfl/{pregame,live}
mkdir -p output/overtime/ncaaf/{pregame,live}

# Move existing files
mv output/overtime_nfl_odds_*.json output/overtime/nfl/pregame/ 2>/dev/null || true
mv output/overtime_nfl_raw_*.json output/overtime/nfl/pregame/ 2>/dev/null || true
mv output/overtime_nfl_walters_*.json output/overtime/nfl/pregame/ 2>/dev/null || true
mv output/overtime_live_nfl_*.json output/overtime/nfl/live/ 2>/dev/null || true

# Clean up
rm output/overtime_live_current.json 2>/dev/null || true
```

---

## Documentation

**Complete Guide Created**: [docs/OVERTIME_DIRECTORY_STRUCTURE.md](docs/OVERTIME_DIRECTORY_STRUCTURE.md)

**Covers**:
- Full directory structure
- File naming conventions
- Scraper configuration
- Common operations
- Archive management
- Integration with workflows
- Migration guide
- Troubleshooting

**Quick Reference**:
- Directory structure
- Naming patterns
- Find latest data commands
- Archive operations

---

## .gitkeep Files

**Purpose**: Preserve empty directories in git

**Created**:
```
output/overtime/nfl/pregame/.gitkeep
output/overtime/nfl/live/.gitkeep
output/overtime/ncaaf/pregame/.gitkeep
output/overtime/ncaaf/live/.gitkeep
```

**Why**: Git doesn't track empty directories. .gitkeep files ensure the structure exists when cloning the repo, even if no data files are present.

---

## Integration with Billy Walters Workflow

### `/collect-all-data` Command

Now uses organized directories:

```bash
# 1. Pre-game scrape → output/overtime/nfl/pregame/
uv run python scripts/scrape_overtime_nfl.py --headless --convert

# 2. Auto-detect latest Billy Walters format
latest_odds=$(ls -t output/overtime/nfl/pregame/overtime_nfl_walters_*.json | head -1)

# 3. Edge detection uses latest file
/edge-detector
```

### Manual Analysis

```bash
# Scrape (organized output)
uv run python scripts/scrape_overtime_nfl.py --headless --convert

# Validate
/validate-data

# Edge detect (auto-finds latest in pregame/)
/edge-detector

# Generate card
/betting-card

# Track CLV
/clv-tracker
```

---

## Cleanup and Maintenance

### Regular Cleanup

```bash
# Remove files older than 7 days
find output/overtime -name "*.json" -mtime +7 -delete

# Archive to separate directory
find output/overtime -name "*.json" -mtime +7 -exec mv {} archive/overtime/ \;
```

### Check Disk Usage

```bash
# Total Overtime data
du -sh output/overtime/

# By sport
du -sh output/overtime/*/

# By type
du -sh output/overtime/*/*/
```

---

## Future Enhancements

### Potential Additions

1. **More Sports**:
   ```
   output/overtime/nba/{pregame,live}/
   output/overtime/mlb/{pregame,live}/
   output/overtime/nhl/{pregame,live}/
   ```

2. **More Bet Types**:
   ```
   output/overtime/nfl/futures/
   output/overtime/nfl/props/
   output/overtime/nfl/parlays/
   ```

3. **Automated Archival**:
   - Cron job to archive weekly
   - Compress old data
   - Upload to cloud storage

---

## Summary

**What Changed**:
- ✅ Reorganized all Overtime.ag outputs into `output/overtime/` structure
- ✅ Updated 3 scraper files with new default directories
- ✅ Created `.gitkeep` files to preserve empty directories
- ✅ Updated `.gitignore` to ignore JSON outputs, keep structure
- ✅ Documented complete directory structure guide
- ✅ Tested with live scrape - working perfectly

**Benefits**:
- Clean organization by sport and scraper type
- Easy to find latest data with predictable paths
- Automation-friendly with standard patterns
- Scalable for future sports and bet types
- Archive-ready with date-based cleanup

**Result**: ✅ **Production-ready organized output structure**

The Overtime.ag scrapers now save data in a clean, organized structure that makes analysis, archival, and automation straightforward!
