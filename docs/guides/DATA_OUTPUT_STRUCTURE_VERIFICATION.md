# Data Output Structure Verification Guide

**Purpose:** Ensure NFL and NCAAF data remain properly separated and easily extractable
**Last Updated:** 2025-11-25
**Status:** Verification Checklist & Tools

---

## Table of Contents

1. [Quick Verification](#quick-verification)
2. [Directory Structure Audit](#directory-structure-audit)
3. [File Organization Verification](#file-organization-verification)
4. [Data Integrity Checks](#data-integrity-checks)
5. [Automated Verification Scripts](#automated-verification-scripts)
6. [Common Issues & Fixes](#common-issues--fixes)
7. [Best Practices](#best-practices)

---

## Quick Verification

### One-Minute Status Check

```bash
# Check if NFL and NCAAF data are properly separated
echo "[CHECK] NFL/NCAAF Separation"
find output -type d -name "nfl" -o -name "ncaaf" | sort

# Expected output:
# output/action_network/nfl
# output/action_network/ncaaf
# output/espn/nfl
# output/espn/ncaaf
# output/overtime/nfl
# output/overtime/ncaaf
# output/weather/nfl
# output/weather/ncaaf

# List recent files by league
echo -e "\n[CHECK] Recent NFL Files"
find output -name "*nfl*" -type f -newer +1d | head -5

echo -e "\n[CHECK] Recent NCAAF Files"
find output -name "*ncaaf*" -type f -newer +1d | head -5
```

### File Count Verification

```bash
# Count files per league
echo "[CHECK] File Counts by League"
echo "NFL files: $(find output -path "*nfl*" -type f | wc -l)"
echo "NCAAF files: $(find output -path "*ncaaf*" -type f | wc -l)"
echo "Total: $(find output -type f | wc -l)"
```

---

## Directory Structure Audit

### Expected Structure

```
output/
├── action_network/
│   ├── nfl/                    # ← NFL ONLY
│   │   ├── all_odds_*.json
│   │   ├── game_lines_*.parquet
│   │   └── sportsbooks_reference.json
│   └── ncaaf/                  # ← NCAAF ONLY
│       ├── all_odds_*.json
│       ├── game_lines_*.parquet
│       ├── steam_tracking_*.json
│       └── sportsbooks_reference.json
│
├── espn/
│   ├── nfl/                    # ← NFL ONLY
│   │   ├── team_stats_*.parquet
│   │   ├── team_stats_*.json
│   │   ├── injuries_*.json
│   │   ├── schedules_*.json
│   │   └── teams_reference.json
│   └── ncaaf/                  # ← NCAAF ONLY
│       ├── team_stats_*.parquet
│       ├── team_stats_*.json
│       ├── injuries_*.json
│       ├── schedules_*.json
│       ├── standings_*.json
│       └── teams_reference.json
│
├── overtime/
│   ├── nfl/                    # ← NFL ONLY
│   │   ├── pregame/
│   │   │   ├── 2025-01-12_pregame.json
│   │   │   ├── 2025-01-19_pregame.json
│   │   │   └── ...
│   │   ├── live/
│   │   │   ├── 2025-01-12_1000_stream.json
│   │   │   ├── 2025-01-12_1010_stream.json
│   │   │   └── ...
│   │   └── archive/
│   └── ncaaf/                  # ← NCAAF ONLY
│       ├── pregame/
│       │   ├── 2025-09-06_pregame.json
│       │   ├── 2025-09-13_pregame.json
│       │   └── ...
│       ├── live/
│       │   ├── 2025-09-06_1000_stream.json
│       │   ├── 2025-09-06_1300_stream.json
│       │   └── ...
│       └── archive/
│
├── massey/
│   ├── nfl_ratings_*.json
│   ├── ncaaf_ratings_*.json
│   ├── college_rankings_*.parquet
│   └── ...
│
├── weather/
│   ├── nfl/                    # ← NFL ONLY
│   │   ├── game_forecasts_*.json
│   │   ├── stadium_conditions_*.parquet
│   │   └── stadiums_reference.json
│   └── ncaaf/                  # ← NCAAF ONLY
│       ├── game_forecasts_*.json
│       ├── stadium_conditions_*.parquet
│       ├── regional_weather_*.json
│       └── stadiums_reference.json
│
└── analysis/
    ├── nfl/                    # ← NFL ONLY
    │   ├── edge_detection_*.json
    │   ├── power_ratings_*.json
    │   ├── clv_tracking_*.parquet
    │   └── recommendations_*.json
    └── ncaaf/                  # ← NCAAF ONLY
        ├── edge_detection_*.json
        ├── power_ratings_*.json
        ├── clv_tracking_*.parquet
        ├── conference_edges_*.json
        └── recommendations_*.json
```

### Structure Validation Script

```bash
#!/bin/bash
# verify_structure.sh - Validate output directory structure

echo "========================================="
echo "DATA STRUCTURE VERIFICATION"
echo "========================================="

# Check critical directories exist
critical_dirs=(
    "output/action_network/nfl"
    "output/action_network/ncaaf"
    "output/espn/nfl"
    "output/espn/ncaaf"
    "output/overtime/nfl/pregame"
    "output/overtime/nfl/live"
    "output/overtime/ncaaf/pregame"
    "output/overtime/ncaaf/live"
    "output/weather/nfl"
    "output/weather/ncaaf"
    "output/analysis/nfl"
    "output/analysis/ncaaf"
)

missing=0
for dir in "${critical_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "[OK] $dir"
    else
        echo "[MISSING] $dir"
        missing=$((missing + 1))
    fi
done

echo ""
echo "========================================="
if [ $missing -eq 0 ]; then
    echo "STRUCTURE: VALID"
else
    echo "STRUCTURE: MISSING $missing directories"
fi
echo "========================================="
```

---

## File Organization Verification

### Verify League Separation

```bash
#!/bin/bash
# check_league_separation.sh - Ensure NFL and NCAAF are separated

echo "Checking file organization..."

# Find any mixed files (shouldn't exist)
echo "[CHECK] Looking for mixed league files..."
mixed_files=$(find output -type f \( -name "*nfl*ncaaf*" -o -name "*ncaaf*nfl*" \))

if [ -z "$mixed_files" ]; then
    echo "[OK] No mixed league files found"
else
    echo "[WARNING] Found mixed files:"
    echo "$mixed_files"
fi

# Check directory nesting
echo ""
echo "[CHECK] Verifying directory nesting..."
echo "NFL directories:"
find output -type d -name "nfl" | sort

echo ""
echo "NCAAF directories:"
find output -type d -name "ncaaf" | sort

# Verify no league subdirs under other leagues
echo ""
echo "[CHECK] Cross-contamination test..."
nfl_contains_ncaaf=$(find output/*/nfl -name "*ncaaf*" 2>/dev/null)
ncaaf_contains_nfl=$(find output/*/ncaaf -name "*nfl*" 2>/dev/null)

if [ -z "$nfl_contains_ncaaf" ] && [ -z "$ncaaf_contains_nfl" ]; then
    echo "[OK] No cross-contamination detected"
else
    echo "[WARNING] Cross-contamination detected:"
    [ -n "$nfl_contains_ncaaf" ] && echo "  NFL dir contains NCAAF: $nfl_contains_ncaaf"
    [ -n "$ncaaf_contains_nfl" ] && echo "  NCAAF dir contains NFL: $ncaaf_contains_nfl"
fi
```

---

## Data Integrity Checks

### Validate File Formats

```python
#!/usr/bin/env python3
"""Validate all output files are well-formed"""

import json
import pandas as pd
from pathlib import Path
import sys

def validate_json_files():
    """Check all JSON files are valid"""
    print("[CHECK] JSON File Validation")
    errors = []

    for json_file in Path('output').rglob('*.json'):
        try:
            with open(json_file) as f:
                json.load(f)
            print(f"  [OK] {json_file.relative_to('output')}")
        except json.JSONDecodeError as e:
            errors.append((str(json_file), str(e)))
            print(f"  [ERROR] {json_file.relative_to('output')}: {e}")

    return errors

def validate_parquet_files():
    """Check all parquet files are readable"""
    print("\n[CHECK] Parquet File Validation")
    errors = []

    for parquet_file in Path('output').rglob('*.parquet'):
        try:
            df = pd.read_parquet(parquet_file)
            rows = len(df)
            cols = len(df.columns)
            print(f"  [OK] {parquet_file.relative_to('output')} ({rows} rows, {cols} cols)")
        except Exception as e:
            errors.append((str(parquet_file), str(e)))
            print(f"  [ERROR] {parquet_file.relative_to('output')}: {e}")

    return errors

def check_file_sizes():
    """Ensure no empty files (data collection errors)"""
    print("\n[CHECK] File Size Validation")
    empty_files = []

    for data_file in Path('output').rglob('*'):
        if data_file.is_file() and data_file.stat().st_size == 0:
            empty_files.append(str(data_file.relative_to('output')))
            print(f"  [WARNING] Empty file: {data_file.relative_to('output')}")

    if not empty_files:
        print("  [OK] No empty files found")

    return empty_files

if __name__ == "__main__":
    json_errors = validate_json_files()
    parquet_errors = validate_parquet_files()
    empty = check_file_sizes()

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"JSON errors: {len(json_errors)}")
    print(f"Parquet errors: {len(parquet_errors)}")
    print(f"Empty files: {len(empty)}")

    if not (json_errors or parquet_errors or empty):
        print("[OK] All files valid!")
        sys.exit(0)
    else:
        print("[ERROR] Found data integrity issues")
        sys.exit(1)
```

### Verify Data Completeness

```python
#!/usr/bin/env python3
"""Verify collected data has expected content"""

import json
from pathlib import Path
from datetime import datetime

def check_nfl_completeness():
    """Verify NFL data has expected games and records"""
    print("[CHECK] NFL Data Completeness")

    # NFL has 16 regular season weeks + 2 playoff weeks
    pregame_files = list(Path('output/overtime/nfl/pregame').glob('*.json'))
    print(f"  Pregame files: {len(pregame_files)} (expected: 18)")

    # ESPN should have 32 teams
    try:
        with open('output/espn/nfl/teams_reference.json') as f:
            teams = json.load(f)
        print(f"  NFL teams: {len(teams)} (expected: 32)")
    except FileNotFoundError:
        print("  [WARNING] NFL teams reference not found")

def check_ncaaf_completeness():
    """Verify NCAAF data has expected games and records"""
    print("\n[CHECK] NCAAF Data Completeness")

    # NCAAF has 15 regular season weeks + bowl season
    pregame_files = list(Path('output/overtime/ncaaf/pregame').glob('*.json'))
    print(f"  Pregame files: {len(pregame_files)} (expected: ~17)")

    # NCAAF should have 130+ FBS teams
    try:
        with open('output/espn/ncaaf/teams_reference.json') as f:
            teams = json.load(f)
        print(f"  NCAAF teams: {len(teams)} (expected: 130+)")
    except FileNotFoundError:
        print("  [WARNING] NCAAF teams reference not found")

def check_stadium_weather():
    """Verify weather data covers all stadiums"""
    print("\n[CHECK] Weather Coverage")

    # NFL: 32 stadiums
    try:
        with open('output/weather/nfl/stadiums_reference.json') as f:
            nfl_stadiums = json.load(f)
        print(f"  NFL stadiums: {len(nfl_stadiums)} (expected: 32)")
    except FileNotFoundError:
        print("  [WARNING] NFL stadiums reference not found")

    # NCAAF: 130+ stadiums
    try:
        with open('output/weather/ncaaf/stadiums_reference.json') as f:
            ncaaf_stadiums = json.load(f)
        print(f"  NCAAF stadiums: {len(ncaaf_stadiums)} (expected: 130+)")
    except FileNotFoundError:
        print("  [WARNING] NCAAF stadiums reference not found")

if __name__ == "__main__":
    check_nfl_completeness()
    check_ncaaf_completeness()
    check_stadium_weather()
```

---

## Automated Verification Scripts

### Master Verification Script

Create `scripts/validation/verify_data_structure.py`:

```python
#!/usr/bin/env python3
"""
Master verification script for data collection structure.
Runs all checks and generates verification report.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess

class DataStructureVerifier:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': [],
            'warnings': []
        }

    def check_directories(self):
        """Verify critical directories exist"""
        print("Checking directory structure...")
        critical_dirs = [
            'output/action_network/nfl',
            'output/action_network/ncaaf',
            'output/espn/nfl',
            'output/espn/ncaaf',
            'output/overtime/nfl/pregame',
            'output/overtime/nfl/live',
            'output/overtime/ncaaf/pregame',
            'output/overtime/ncaaf/live',
            'output/weather/nfl',
            'output/weather/ncaaf',
            'output/analysis/nfl',
            'output/analysis/ncaaf'
        ]

        missing = []
        for dir_path in critical_dirs:
            if not Path(dir_path).exists():
                missing.append(dir_path)

        self.results['checks']['directories'] = {
            'total': len(critical_dirs),
            'present': len(critical_dirs) - len(missing),
            'missing': missing
        }

        return len(missing) == 0

    def check_league_separation(self):
        """Verify NFL and NCAAF data don't intermix"""
        print("Checking league separation...")

        # Find any files with both "nfl" and "ncaaf" in name
        mixed_files = []
        for f in Path('output').rglob('*'):
            name = f.name.lower()
            if 'nfl' in name and 'ncaaf' in name:
                mixed_files.append(str(f.relative_to('output')))

        self.results['checks']['league_separation'] = {
            'status': 'ok' if not mixed_files else 'warning',
            'mixed_files': mixed_files
        }

        if mixed_files:
            self.results['warnings'].append(f"Found {len(mixed_files)} mixed league files")
            return False
        return True

    def check_file_counts(self):
        """Verify reasonable number of files"""
        print("Checking file counts...")

        nfl_files = len(list(Path('output').rglob('*nfl*')))
        ncaaf_files = len(list(Path('output').rglob('*ncaaf*')))
        total_files = len(list(Path('output').rglob('*')))

        self.results['checks']['file_counts'] = {
            'nfl': nfl_files,
            'ncaaf': ncaaf_files,
            'total': total_files
        }

        return nfl_files > 0 and ncaaf_files > 0

    def check_data_completeness(self):
        """Verify expected data was collected"""
        print("Checking data completeness...")

        completeness = {
            'nfl_teams': self._count_teams('output/espn/nfl/teams_reference.json', 32),
            'ncaaf_teams': self._count_teams('output/espn/ncaaf/teams_reference.json', 130),
            'nfl_games': self._count_pregame_files('output/overtime/nfl/pregame', 18),
            'ncaaf_games': self._count_pregame_files('output/overtime/ncaaf/pregame', 15)
        }

        self.results['checks']['data_completeness'] = completeness

        # All should have content
        return all(v['found'] > 0 for v in completeness.values())

    def _count_teams(self, file_path, expected):
        """Count teams in reference file"""
        try:
            with open(file_path) as f:
                teams = json.load(f)
            count = len(teams) if isinstance(teams, (list, dict)) else 0
            return {
                'found': count,
                'expected': expected,
                'status': 'ok' if count >= expected * 0.8 else 'warning'
            }
        except FileNotFoundError:
            return {'found': 0, 'expected': expected, 'status': 'missing'}

    def _count_pregame_files(self, dir_path, expected):
        """Count pregame JSON files"""
        count = len(list(Path(dir_path).glob('*.json')))
        return {
            'found': count,
            'expected': expected,
            'status': 'ok' if count >= expected * 0.5 else 'warning'
        }

    def generate_report(self):
        """Generate verification report"""
        print("\n" + "="*60)
        print("DATA STRUCTURE VERIFICATION REPORT")
        print("="*60)
        print(f"Timestamp: {self.results['timestamp']}")
        print()

        # Directory check
        dirs = self.results['checks']['directories']
        print(f"Directories: {dirs['present']}/{dirs['total']} present")
        if dirs['missing']:
            print(f"  Missing: {', '.join(dirs['missing'][:3])}")

        # League separation
        sep = self.results['checks']['league_separation']
        print(f"League Separation: {sep['status'].upper()}")
        if sep.get('mixed_files'):
            print(f"  Mixed files: {len(sep['mixed_files'])}")

        # File counts
        counts = self.results['checks']['file_counts']
        print(f"File Counts: NFL={counts['nfl']}, NCAAF={counts['ncaaf']}, Total={counts['total']}")

        # Completeness
        comp = self.results['checks']['data_completeness']
        print("Data Completeness:")
        for key, val in comp.items():
            status = val['status']
            print(f"  {key}: {val['found']}/{val['expected']} ({status})")

        # Summary
        print()
        print("="*60)
        if self.results['errors']:
            print(f"[ERROR] {len(self.results['errors'])} errors found")
            return False
        elif self.results['warnings']:
            print(f"[WARNING] {len(self.results['warnings'])} warnings")
            return True
        else:
            print("[OK] All checks passed!")
            return True

if __name__ == "__main__":
    verifier = DataStructureVerifier()
    verifier.check_directories()
    verifier.check_league_separation()
    verifier.check_file_counts()
    verifier.check_data_completeness()

    success = verifier.generate_report()

    # Save report
    report_file = 'output/verification_report.json'
    with open(report_file, 'w') as f:
        json.dump(verifier.results, f, indent=2)
    print(f"\nReport saved to: {report_file}")

    sys.exit(0 if success else 1)
```

**Run verification:**

```bash
uv run python scripts/validation/verify_data_structure.py
```

---

## Common Issues & Fixes

### Issue: "Mixed NFL/NCAAF data in same directory"

**Cause:** Used `--nfl --ncaaf` flag together

**Fix:**
```bash
# Collect separately
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Verify separation
ls output/overtime/nfl/pregame/
ls output/overtime/ncaaf/pregame/
```

### Issue: "Files in wrong locations"

**Cause:** Manual file moves or incorrect output paths

**Fix:**
```bash
# Reorganize files to correct locations
# Example: move misplaced files back to correct league directory
find output -name "*nfl*" -type f | xargs -I {} mv {} output/\{source\}/nfl/

# Or rebuild from scratch (safe approach)
rm -rf output/
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```

### Issue: "Data not found during extraction"

**Cause:** Files in unexpected directory

**Fix:**
```bash
# Find where files actually are
find output -name "team_stats*" -type f

# Update import paths if needed
# Or reorganize to standard structure
```

---

## Best Practices

### 1. **Always Collect with Single League Flag**

```bash
# Good: Separate collections
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Bad: Mixed collection (creates problems)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf
```

### 2. **Verify After Collection**

```bash
# After any collection, run verification
uv run python scripts/validation/verify_data_structure.py

# Or quick check
ls -lh output/*/nfl/ output/*/ncaaf/ | grep -E "nfl|ncaaf"
```

### 3. **Use Standardized Output Paths**

All scripts should output to:
- `output/{source}/nfl/...` for NFL
- `output/{source}/ncaaf/...` for NCAAF

Never use:
- `output/nfl_data/` (inconsistent)
- `output/2025_nfl/` (misleading)
- `output/{component}/...` (loses league info)

### 4. **Document File Modifications**

If you manually reorganize files, document the changes:

```bash
# Create a log file
echo "$(date): Reorganized X files to fix structure" >> output/MODIFICATION_LOG.txt
```

### 5. **Archive Old Data Safely**

```bash
# Move old season data to archive
mkdir -p output/*/archive/2024_season/
mv output/*/2024_*.* output/*/archive/2024_season/ 2>/dev/null

# Verify structure still intact
uv run python scripts/validation/verify_data_structure.py
```

---

## Testing Data Extraction

### Test NFL Extraction

```python
import json
import pandas as pd

# Load NFL data
with open('output/overtime/nfl/pregame/2025-01-12_pregame.json') as f:
    nfl_odds = json.load(f)

# Should only have NFL games (32 teams, 16 weeks)
print(f"NFL games: {len(nfl_odds)}")
assert len(nfl_odds) <= 32 * 2, "More games than expected!"

# Load stats
nfl_stats = pd.read_parquet('output/espn/nfl/team_stats_2025_week12.parquet')
assert len(nfl_stats) == 32, "Should have exactly 32 NFL teams"
```

### Test NCAAF Extraction

```python
import json
import pandas as pd

# Load NCAAF data
with open('output/overtime/ncaaf/pregame/2025-09-06_pregame.json') as f:
    ncaaf_odds = json.load(f)

# Should have college games (130+ teams, 15 weeks)
print(f"NCAAF games: {len(ncaaf_odds)}")
assert len(ncaaf_odds) >= 50, "Fewer games than expected!"

# Load stats
ncaaf_stats = pd.read_parquet('output/espn/ncaaf/team_stats_2025_week1.parquet')
assert len(ncaaf_stats) >= 130, "Should have 130+ NCAAF teams"
```

---

## Summary Checklist

Before running analysis or exporting data:

- [ ] Run `verify_data_structure.py` script
- [ ] Confirm zero mixed NFL/NCAAF files
- [ ] Verify directory structure matches expected format
- [ ] Check file sizes are not empty (>1 KB)
- [ ] Validate JSON files parse correctly
- [ ] Validate parquet files read correctly
- [ ] Confirm expected team/game counts
- [ ] Test extraction with sample code

---

**Document Version:** 1.0
**Last Updated:** 2025-11-25
**Maintained By:** Billy Walters Sports Analyzer Team
