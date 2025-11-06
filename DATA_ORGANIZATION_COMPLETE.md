# Data Organization Complete
**Generated:** 2025-11-06  
**Separated by Source and Sport**

---

## New Directory Structure

### ✅ **ORGANIZED BY SOURCE AND SPORT**

```
data/
  injuries/                 ← Player injury data (ESPN)
    nfl/                    ← NFL injury reports
      nfl-injuries-*.jsonl
      nfl-injuries-*.parquet
      README.md
    ncaaf/                  ← College Football injury reports  
      ncaaf-injuries-*.jsonl
      ncaaf-injuries-*.parquet
      README.md
      
  odds/                     ← Betting odds (overtime.ag)
    nfl/                    ← NFL betting lines
      nfl-odds-*.jsonl
      nfl-odds-*.json
      nfl-odds-*.csv
      README.md
    ncaaf/                  ← College Football betting lines
      ncaaf-odds-*.jsonl
      ncaaf-odds-*.json
      ncaaf-odds-*.csv
      README.md
      
  archive/                  ← Old files (backup)
    old_overtime_live/      ← Original mixed files
```

---

## Current Files

### NFL Injury Data (5 files)

**Directory:** `data/injuries/nfl/`

```
overtime-live-20251103-122354.jsonl  (566 records)
overtime-live-20251103-122903.jsonl  (566 records)
overtime-live-20251103-122939.jsonl  (566 records)
overtime-live-20251103-123147.jsonl  (566 records)
overtime-live-20251106-130035.jsonl  (519 records) ← Latest
```

**Total:** 2,783 NFL injury records across 5 scraping runs

### NCAAF Injury Data (2 files)

**Directory:** `data/injuries/ncaaf/`

```
overtime-live-20251103-120640.jsonl  (566 records)
overtime-live-20251103-120822.jsonl  (566 records)
```

**Total:** 1,132 NCAAF injury records across 2 scraping runs

### NFL Odds Data (3 files)

**Directory:** `data/odds/nfl/`

```
nfl-odds-20251106-053534.jsonl  (13 games)
nfl-odds-20251106-053534.json   (13 games, pretty format)
nfl-odds-20251106-053534.csv    (13 games, spreadsheet)
```

**Total:** 13 NFL games with complete betting odds

### NCAAF Odds Data (1 file)

**Directory:** `data/odds/ncaaf/`

```
overtime-live-20251101-064653.jsonl  (1 invalid record - archived)
```

**Total:** 0 valid NCAAF odds (need to scrape)

---

## Updated Commands

### Scrape NFL Injuries

**Command:**
```bash
uv run walters-analyzer scrape-injuries --sport nfl
```

**Output:** `data/injuries/nfl/nfl-injuries-YYYYMMDD-HHMMSS.jsonl`

### Scrape NCAAF Injuries

**Command:**
```bash
uv run walters-analyzer scrape-injuries --sport cfb
```

**Output:** `data/injuries/ncaaf/ncaaf-injuries-YYYYMMDD-HHMMSS.jsonl`

### Scrape NFL Odds (Chrome DevTools)

**Method:** Via agent with MCP chrome-devtools
1. Navigate to https://overtime.ag/sports/
2. Click NFL filter
3. Take snapshot
4. Run: `python scrape_odds_mcp.py <snapshot_file> --sport nfl`

**Output:** `data/odds/nfl/nfl-odds-YYYYMMDD-HHMMSS.jsonl`

### Scrape NCAAF Odds (Chrome DevTools)

**Method:** Via agent with MCP chrome-devtools
1. Navigate to https://overtime.ag/sports/
2. Click College Football filter
3. Take snapshot
4. Run: `python scrape_odds_mcp.py <snapshot_file> --sport ncaaf`

**Output:** `data/odds/ncaaf/ncaaf-odds-YYYYMMDD-HHMMSS.jsonl`

---

## Benefits of New Structure

### 1. Clear Separation by Source ✅

**Before:**
```
data/overtime_live/  ← Mixed injuries AND odds (confusing!)
```

**After:**
```
data/injuries/  ← Only injury data (ESPN)
data/odds/      ← Only odds data (overtime.ag)
```

### 2. Clear Separation by Sport ✅

**Before:**
```
All NFL and NCAAF files mixed together
```

**After:**
```
data/injuries/nfl/    ← NFL injuries only
data/injuries/ncaaf/  ← NCAAF injuries only
data/odds/nfl/        ← NFL odds only
data/odds/ncaaf/      ← NCAAF odds only
```

### 3. Easier Data Loading ✅

**Example:**
```python
# Load latest NFL injury data
nfl_injuries = load_latest_injuries("data/injuries/nfl")

# Load latest NFL odds
nfl_odds = load_latest_odds("data/odds/nfl")

# Combine for analysis
nfl_analysis = combine_odds_and_injuries(nfl_odds, nfl_injuries)
```

### 4. Better Organization ✅

- **Injuries:** All ESPN injury reports together
- **Odds:** All overtime.ag odds together
- **NFL:** All NFL data together
- **NCAAF:** All NCAAF data together

---

## File Counts by Category

| Category | NFL Files | NCAAF Files | Total |
|----------|-----------|-------------|-------|
| **Injury Data** | 5 | 2 | 7 |
| **Odds Data** | 3 | 0 | 3 |
| **Total** | 8 | 2 | 10 |

### Records by Category:

| Category | NFL Records | NCAAF Records | Total |
|----------|-------------|---------------|-------|
| **Injury Records** | 2,783 | 1,132 | 3,915 |
| **Odds Records** | 13 games | 0 games | 13 games |

---

## Usage Examples

### Analyze NFL Games with Injuries

```python
# Load NFL data only
nfl_odds = load_jsonl("data/odds/nfl/nfl-odds-20251106-053534.jsonl")
nfl_injuries = load_jsonl("data/injuries/nfl/overtime-live-20251106-130035.jsonl")

# Run Billy Walters analysis on NFL
for game in nfl_odds:
    analyze_game_with_injuries(game, nfl_injuries)
```

### Analyze NCAAF Games (when odds available)

```python
# Load NCAAF data only
ncaaf_odds = load_jsonl("data/odds/ncaaf/ncaaf-odds-*.jsonl")
ncaaf_injuries = load_jsonl("data/injuries/ncaaf/ncaaf-injuries-*.jsonl")

# Run Billy Walters analysis on NCAAF
for game in ncaaf_odds:
    analyze_game_with_injuries(game, ncaaf_injuries)
```

### Compare NFL vs NCAAF

```python
nfl_impact = analyze_all_nfl()
ncaaf_impact = analyze_all_ncaaf()

print(f"NFL average injury impact: {nfl_impact}")
print(f"NCAAF average injury impact: {ncaaf_impact}")
```

---

## README Files Created

Each directory now has a README explaining:
- Data source
- File formats
- Scraping commands
- Usage examples

**Files:**
- `data/injuries/nfl/README.md`
- `data/injuries/ncaaf/README.md`
- `data/odds/nfl/README.md`
- `data/odds/ncaaf/README.md`

---

## Migration Summary

### Files Moved:

**NFL Injuries:** 5 files → `data/injuries/nfl/`
- overtime-live-20251103-122354.jsonl
- overtime-live-20251103-122903.jsonl
- overtime-live-20251103-122939.jsonl
- overtime-live-20251103-123147.jsonl
- overtime-live-20251106-130035.jsonl (LATEST - 519 records)

**NCAAF Injuries:** 2 files → `data/injuries/ncaaf/`
- overtime-live-20251103-120640.jsonl
- overtime-live-20251103-120822.jsonl

**NFL Odds:** 3 files → `data/odds/nfl/`
- nfl-odds-20251106-053534.jsonl (LATEST - 13 games)
- nfl-odds-20251106-053534.json
- nfl-odds-20251106-053534.csv

**NCAAF Odds:** 1 file → `data/odds/ncaaf/`
- overtime-live-20251101-064653.jsonl (invalid UI capture - for reference)

**Archived:** Invalid/unknown files → `data/archive/old_overtime_live/`

**Original files preserved in `data/overtime_live/` and `data/odds_chrome/` (can delete if desired)**

---

## Next Steps

### 1. Scrape NCAAF Odds ⏸️

**To get College Football odds:**
1. Use agent with Chrome DevTools MCP
2. Navigate to overtime.ag/sports/
3. Click "COLLEGE FB(1H/2H/Q)" filter
4. Take snapshot
5. Run: `python scrape_odds_mcp.py <snapshot> --sport ncaaf`

### 2. Update Analysis Scripts

Modify `analyze_games_with_injuries.py` to use new paths:
```python
# Old:
odds = load_data("data/overtime_live")

# New:
nfl_odds = load_data("data/odds/nfl")
nfl_injuries = load_data("data/injuries/nfl")
```

### 3. Build Sport-Specific Analyzers

Create separate analysis workflows:
- `analyze_nfl.py` - NFL only
- `analyze_ncaaf.py` - College Football only  
- `analyze_all.py` - Both sports

---

## Verification

### Check NFL Injury Data:

```bash
# Count records
wc -l data/injuries/nfl/*.jsonl

# View latest
head -5 data/injuries/nfl/overtime-live-20251106-130035.jsonl
```

### Check NFL Odds Data:

```bash
# Count games  
wc -l data/odds/nfl/*.jsonl

# View all games
cat data/odds/nfl/nfl-odds-20251106-053534.json | jq '.[] | .teams'
```

### Check NCAAF Data:

```bash
# Check what's available
ls -la data/injuries/ncaaf/
ls -la data/odds/ncaaf/
```

---

## Benefits Summary

✅ **Clear separation** - Injuries vs Odds  
✅ **Sport-specific** - NFL vs NCAAF  
✅ **Easy to find** - Logical directory names  
✅ **Scalable** - Ready for NBA, MLB, etc.  
✅ **Documented** - README in each directory  
✅ **Preserved** - Original files backed up  

---

**Organization Complete:** 2025-11-06  
**Status:** ✅ **CLEAN AND ORGANIZED**  
**Next Action:** Build integration script for NFL (use new paths)


