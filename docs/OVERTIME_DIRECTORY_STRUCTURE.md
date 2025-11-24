# Overtime.ag Output Directory Structure

## Overview

All Overtime.ag scraper outputs are now organized into a clean directory structure under `output/overtime/` to keep data organized by sport, league, and scraper type.

## Directory Structure

```
output/overtime/
├── nfl/
│   ├── pregame/          # Pre-game NFL betting lines
│   │   ├── overtime_nfl_odds_YYYYMMDD_HHMMSS.json
│   │   ├── overtime_nfl_raw_YYYY-MM-DDTHH-MM-SS-mmmmmm.json
│   │   └── overtime_nfl_walters_YYYY-MM-DDTHH-MM-SS-mmmmmm.json
│   └── live/             # Live in-game NFL betting lines
│       └── overtime_nfl_live_YYYYMMDD_HHMMSS.json
└── ncaaf/
    ├── pregame/          # Pre-game NCAAF betting lines
    │   ├── api_walters_YYYY-MM-DDTHH-MM-SS-mmmmmm.json
    │   └── overtime_ncaaf_walters_YYYY-MM-DDTHH-MM-SS-mmmmmm.json
    └── live/             # Live in-game NCAAF betting lines
        └── overtime_ncaaf_live_YYYYMMDD_HHMMSS.json
```

## File Naming Conventions

### Pre-Game NFL Files

**Raw Overtime Format**:
- Pattern: `overtime_nfl_raw_YYYY-MM-DDTHH-MM-SS-mmmmmm.json`
- Example: `overtime_nfl_raw_2025-11-10T19-49-54-569103.json`
- Contains: Raw data directly from Overtime.ag

**Overtime Format with Metadata**:
- Pattern: `overtime_nfl_odds_YYYYMMDD_HHMMSS.json`
- Example: `overtime_nfl_odds_20251110_194954.json`
- Contains: Structured odds with scraper metadata and validation

**Billy Walters Format**:
- Pattern: `overtime_nfl_walters_YYYY-MM-DDTHH-MM-SS-mmmmmm.json`
- Example: `overtime_nfl_walters_2025-11-10T19-49-54-569103.json`
- Contains: Converted data ready for edge detection

### Pre-Game NCAAF Files

**API Client Format (Primary)**:
- Pattern: `api_walters_YYYY-MM-DDTHH-MM-SS-mmmmmm.json`
- Example: `api_walters_2025-11-23T00-08-15-234567.json`
- Contains: NCAAF odds from Overtime.ag API in Billy Walters format
- Source: Direct HTTP POST to Overtime.ag API endpoint
- Speed: ~5 seconds for full NCAAF slate

**Hybrid Scraper Format (Optional - Live Games)**:
- Pattern: `overtime_ncaaf_walters_YYYY-MM-DDTHH-MM-SS-mmmmmm.json`
- Example: `overtime_ncaaf_walters_2025-11-23T13-30-00-123456.json`
- Contains: NCAAF odds with live updates via SignalR WebSocket
- Use Case: Real-time line movement tracking during games

### Live Betting Files

**NFL Live**:
- Pattern: `overtime_nfl_live_YYYYMMDD_HHMMSS.json`
- Example: `overtime_nfl_live_20251110_181422.json`
- Contains: Live in-game betting lines for NFL

**NCAAF Live**:
- Pattern: `overtime_ncaaf_live_YYYYMMDD_HHMMSS.json`
- Example: `overtime_ncaaf_live_20251110_143022.json`
- Contains: Live in-game betting lines for NCAAF

## Scraper Configuration

### Pre-Game NFL Scraper

**Default Output Directory**: `output/overtime/nfl/pregame`

```bash
# Uses default directory
uv run python scripts/scrape_overtime_nfl.py --headless --convert

# Custom directory
uv run python scripts/scrape_overtime_nfl.py --output custom/path
```

**Code Reference**: [src/data/overtime_pregame_nfl_scraper.py:62](../src/data/overtime_pregame_nfl_scraper.py#L62)

### Live NFL Scraper

**Default Output Directory**: `output/overtime/nfl/live`

```bash
# Uses default directory
uv run python scripts/scrape_overtime_live.py
```

**Code Reference**: [scripts/scrape_overtime_live.py:36](../scripts/scrape_overtime_live.py#L36)

### Pre-Game NCAAF Scraper (API Client - Primary)

**Default Output Directory**: `output/overtime/ncaaf/pregame`

```bash
# Scrape NCAAF pre-game odds (RECOMMENDED - Fast & Simple)
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Scrape both NFL and NCAAF
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```

**Speed**: ~5 seconds for full NCAAF slate
**Authentication**: Not required
**Dependencies**: No browser automation needed

**Code Reference**: [src/data/overtime_api_client.py](../src/data/overtime_api_client.py)

### Pre-Game NCAAF Scraper (Hybrid - Optional)

**For Live Game Monitoring** (SignalR WebSocket):

```bash
# Monitor NCAAF games for 3 hours (live line movement)
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 10800 --headless
```

**Use Case**: Real-time line movement tracking during games
**Output**: `output/overtime/ncaaf/pregame/overtime_ncaaf_walters_*.json`

**Code Reference**: [src/data/overtime_hybrid_scraper.py](../src/data/overtime_hybrid_scraper.py)

### Live Scrapy Spider (NCAAF/NFL)

**Manual Output Specification**:

```bash
# NCAAF live
cd scrapers/overtime_live
uv run scrapy crawl overtime_live -o ../../output/overtime/ncaaf/live/overtime_ncaaf_live_$(date +%Y%m%d_%H%M%S).json

# NFL live
cd scrapers/overtime_live
uv run scrapy crawl overtime_live \
  -o ../../output/overtime/nfl/live/overtime_nfl_live_$(date +%Y%m%d_%H%M%S).json \
  -s OVERTIME_SPORT="Football" \
  -s OVERTIME_COMP="NFL"
```

## Benefits of This Structure

### 1. Organization
- **Sport Separation**: NFL and NCAAF data kept separate
- **Scraper Type Separation**: Pre-game vs live betting lines clearly distinguished
- **Easy Navigation**: Find data by sport/type/date

### 2. Automation-Friendly
- **Predictable Paths**: Scripts know where to find latest data
- **Pattern Matching**: Easy to glob for specific data types
- **Timestamped**: Never overwrite previous scrapes

### 3. Analysis Workflow
- **Sport-Specific Analysis**: Analyze NFL or NCAAF independently
- **Time-Series Data**: Track line movements over time
- **Archive Management**: Easily archive old data by sport/date

## Common Operations

### Find Latest Pre-Game NFL Odds

```bash
# Latest odds file
ls -t output/overtime/nfl/pregame/overtime_nfl_odds_*.json | head -1

# Latest Billy Walters format
ls -t output/overtime/nfl/pregame/overtime_nfl_walters_*.json | head -1
```

### Find Latest Live Odds

```bash
# Latest NFL live odds
ls -t output/overtime/nfl/live/overtime_nfl_live_*.json | head -1

# Latest NCAAF live odds
ls -t output/overtime/ncaaf/live/overtime_ncaaf_live_*.json | head -1
```

### Archive Old Data

```bash
# Archive NFL pre-game data older than 30 days
find output/overtime/nfl/pregame -name "*.json" -mtime +30 -exec mv {} archive/overtime/nfl/pregame/ \;

# Archive all Overtime data for a specific date
mkdir -p archive/overtime/2025-11-10
find output/overtime -name "*20251110*" -exec mv {} archive/overtime/2025-11-10/ \;
```

### Clean Up Test Data

```bash
# Remove all outputs (be careful!)
rm -rf output/overtime/*

# Remove only pre-game NFL data
rm -rf output/overtime/nfl/pregame/*

# Remove data older than 7 days
find output/overtime -name "*.json" -mtime +7 -delete
```

## Integration with Billy Walters Workflow

### Automated Collection (NFL + NCAAF)

The `/collect-all-data` command uses these directories:

```bash
# 1. Scrape pre-game NFL odds
output_dir: output/overtime/nfl/pregame
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# 2. Scrape pre-game NCAAF odds (NEW)
output_dir: output/overtime/ncaaf/pregame
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# 3. Auto-detect latest NFL odds for edge detection
latest_nfl=$(ls -t output/overtime/nfl/pregame/api_walters_*.json | head -1)
uv run python -m walters_analyzer.valuation.billy_walters_edge_detector --odds-file "$latest_nfl" --league nfl

# 4. Auto-detect latest NCAAF odds for edge detection (NEW)
latest_ncaaf=$(ls -t output/overtime/ncaaf/pregame/api_walters_*.json | head -1)
uv run python -m walters_analyzer.valuation.ncaaf_edge_detector --odds-file "$latest_ncaaf" --league ncaaf
```

### Manual Workflow (NFL + NCAAF)

```bash
# 1. Scrape both leagues
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf

# 2. Validate data quality
/validate-data

# 3. Detect edges (both NFL and NCAAF)
/edge-detector

# 4. Generate betting card
/betting-card
```

### League-Specific Workflows

**NFL Only**:
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
/edge-detector --league nfl
```

**NCAAF Only**:
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
/edge-detector --league ncaaf
```

## Migration from Old Structure

### Old Structure (Before)

```
output/
├── overtime_nfl_odds_20251110_*.json
├── overtime_nfl_raw_*.json
├── overtime_nfl_walters_*.json
├── overtime_live_nfl_*.json
└── overtime_live_current.json
```

### New Structure (After)

```
output/overtime/
├── nfl/
│   ├── pregame/
│   │   ├── overtime_nfl_odds_*.json
│   │   ├── overtime_nfl_raw_*.json
│   │   └── overtime_nfl_walters_*.json
│   └── live/
│       └── overtime_nfl_live_*.json
└── ncaaf/
    └── live/
        └── overtime_ncaaf_live_*.json
```

### Migration Command

```bash
# Create new directories
mkdir -p output/overtime/nfl/{pregame,live}
mkdir -p output/overtime/ncaaf/{pregame,live}

# Move existing files
mv output/overtime_nfl_odds_*.json output/overtime/nfl/pregame/ 2>/dev/null || true
mv output/overtime_nfl_raw_*.json output/overtime/nfl/pregame/ 2>/dev/null || true
mv output/overtime_nfl_walters_*.json output/overtime/nfl/pregame/ 2>/dev/null || true
mv output/overtime_live_nfl_*.json output/overtime/nfl/live/ 2>/dev/null || true
mv output/overtime_*ncaaf*.json output/overtime/ncaaf/live/ 2>/dev/null || true

# Clean up old files
rm output/overtime_live_current.json 2>/dev/null || true
```

## .gitignore Configuration

Add these patterns to `.gitignore`:

```gitignore
# Overtime.ag scraper outputs
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

## Best Practices

### 1. Regular Cleanup

```bash
# Weekly: Archive data older than 7 days
find output/overtime -name "*.json" -mtime +7 -exec mv {} archive/overtime/ \;

# Monthly: Delete archived data older than 90 days
find archive/overtime -name "*.json" -mtime +90 -delete
```

### 2. Backup Important Data

```bash
# Backup validated scrapes to S3/cloud storage
aws s3 sync output/overtime/nfl/pregame/ s3://bucket/overtime/nfl/pregame/ \
  --exclude "*" --include "overtime_nfl_walters_*.json"
```

### 3. Monitor Disk Usage

```bash
# Check size of Overtime data
du -sh output/overtime/

# Size by sport
du -sh output/overtime/*/

# Size by type
du -sh output/overtime/*/*/
```

### 4. Data Retention Policy

**Recommended**:
- Keep last 7 days in `output/overtime/` for active analysis
- Archive 8-30 days to `archive/overtime/`
- Delete data older than 90 days (or compress and store long-term)

## Troubleshooting

### Problem: Files in Wrong Directory

**Check scraper configuration**:
```bash
# Pre-game NFL scraper default
grep "output_dir" src/data/overtime_pregame_nfl_scraper.py

# Should show: output_dir: str = "output/overtime/nfl/pregame"
```

### Problem: Permission Denied Creating Directories

**Solution**:
```bash
# Ensure directory exists and is writable
mkdir -p output/overtime/nfl/{pregame,live}
chmod 755 output/overtime/nfl/{pregame,live}
```

### Problem: Old Files Still in output/

**Solution**:
```bash
# Move to organized structure
bash scripts/migrate_overtime_outputs.sh
```

## Summary

The new directory structure provides:
- ✅ **Clear organization** by sport and scraper type
- ✅ **Easy navigation** and pattern matching
- ✅ **Automation-friendly** with predictable paths
- ✅ **Archive-ready** with date-based cleanup
- ✅ **Scalable** for future sports (NBA, MLB, etc.)

All new Overtime.ag scrapes automatically use this structure, keeping your data organized and analysis workflows clean.
