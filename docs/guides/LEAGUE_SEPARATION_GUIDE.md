# League Separation Guide: NFL vs NCAAF

**Purpose:** Master guide for keeping NFL and NCAAF data completely separated
**Last Updated:** 2025-11-25
**Status:** Core Operational Guide

---

## Quick Reference

### Key Principle

> **NFL and NCAAF data are collected, stored, and analyzed completely separately.**
> No data mixing at any level.

### File Structure Rule

```
output/
├── {source}/nfl/       ← NFL ONLY
└── {source}/ncaaf/     ← NCAAF ONLY
```

**Sources:** `action_network`, `espn`, `overtime`, `weather`, `analysis`, `massey`

---

## Collection Commands

### NFL Collection

```bash
# Pregame odds only
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# With monitoring
uv run python scripts/scrapers/scrape_overtime_hybrid.py --nfl --duration 10800

# Team stats
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl

# Weather
python src/data/weather_client.py --league nfl

# Action Network
uv run python scripts/scrapers/scrape_action_network_sitemap.py --nfl
```

### NCAAF Collection

```bash
# Pregame odds only
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# With monitoring
uv run python scripts/scrapers/scrape_overtime_hybrid.py --ncaaf --duration 14400

# Team stats
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf

# Weather
python src/data/weather_client.py --league ncaaf

# Action Network
uv run python scripts/scrapers/scrape_action_network_sitemap.py --ncaaf
```

### ❌ NEVER DO THIS

```bash
# WRONG - mixes leagues
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf

# WRONG - no league specified (ambiguous)
uv run python scripts/scrapers/scrape_action_network_sitemap.py
```

---

## Complete Workflows

### NFL Weekly Workflow (Tuesday 2:00 PM)

**Step-by-step with proper separation:**

```bash
echo "=== NFL WEEKLY DATA COLLECTION ==="

# 1. Overtime pregame odds (only NFL)
echo "[1/5] Collecting NFL odds from Overtime..."
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
# Output: output/overtime/nfl/pregame/*.json

# 2. ESPN stats (only NFL)
echo "[2/5] Collecting NFL team statistics..."
uv run python scripts/scrapers/scrape_espn_team_stats.py --league nfl
# Output: output/espn/nfl/*.parquet

# 3. Massey ratings (will separate next step)
echo "[3/5] Collecting power ratings..."
uv run python scripts/scrapers/scrape_massey_games.py
# Output: output/massey/{nfl,ncaaf}_ratings_*.json

# 4. Weather (only NFL)
echo "[4/5] Collecting NFL weather..."
python src/data/weather_client.py --league nfl
# Output: output/weather/nfl/*.json

# 5. Action Network (only NFL)
echo "[5/5] Collecting Action Network lines..."
uv run python scripts/scrapers/scrape_action_network_sitemap.py --nfl
# Output: output/action_network/nfl/*.json

echo "=== NFL COLLECTION COMPLETE ==="
echo "Verify with: ls output/*/nfl/"
```

### NCAAF Weekly Workflow (Wednesday 2:00 PM)

**Step-by-step with proper separation:**

```bash
echo "=== NCAAF WEEKLY DATA COLLECTION ==="

# 1. Overtime pregame odds (only NCAAF)
echo "[1/5] Collecting NCAAF odds from Overtime..."
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
# Output: output/overtime/ncaaf/pregame/*.json

# 2. ESPN stats (only NCAAF)
echo "[2/5] Collecting NCAAF team statistics..."
uv run python scripts/scrapers/scrape_espn_team_stats.py --league ncaaf
# Output: output/espn/ncaaf/*.parquet

# 3. Massey ratings (only college)
echo "[3/5] Collecting college power ratings..."
uv run python scripts/scrapers/scrape_massey_games.py --league college
# Output: output/massey/ncaaf_ratings_*.json

# 4. Weather (only NCAAF)
echo "[4/5] Collecting NCAAF weather..."
python src/data/weather_client.py --league ncaaf
# Output: output/weather/ncaaf/*.json

# 5. Action Network (only NCAAF)
echo "[5/5] Collecting Action Network lines..."
uv run python scripts/scrapers/scrape_action_network_sitemap.py --ncaaf
# Output: output/action_network/ncaaf/*.json

echo "=== NCAAF COLLECTION COMPLETE ==="
echo "Verify with: ls output/*/ncaaf/"
```

---

## Directory Structure

### By League

```
output/
├── action_network/
│   ├── nfl/
│   │   ├── all_odds_2025_week12.json
│   │   ├── game_lines_2025_week12.parquet
│   │   └── sportsbooks_reference.json
│   │
│   └── ncaaf/
│       ├── all_odds_2025_week1.json
│       ├── game_lines_2025_week1.parquet
│       └── sportsbooks_reference.json

├── espn/
│   ├── nfl/
│   │   ├── team_stats_2025_week12.parquet
│   │   ├── injuries_2025_week12.json
│   │   ├── schedules_2025.json
│   │   └── teams_reference.json  (32 teams)
│   │
│   └── ncaaf/
│       ├── team_stats_2025_week1.parquet
│       ├── injuries_2025_week1.json
│       ├── schedules_2025.json
│       ├── standings_2025_week1.json
│       └── teams_reference.json  (130+ teams)

├── overtime/
│   ├── nfl/
│   │   ├── pregame/
│   │   │   ├── 2025-01-12_pregame.json
│   │   │   └── 2025-01-19_pregame.json
│   │   └── live/
│   │       ├── 2025-01-12_1000_stream.json
│   │       └── 2025-01-12_1010_stream.json
│   │
│   └── ncaaf/
│       ├── pregame/
│       │   ├── 2025-09-06_pregame.json
│       │   └── 2025-09-13_pregame.json
│       └── live/
│           ├── 2025-09-06_1000_stream.json
│           └── 2025-09-06_1300_stream.json

├── weather/
│   ├── nfl/
│   │   ├── game_forecasts_2025_week12.json
│   │   ├── stadium_conditions_2025_week12.parquet
│   │   └── stadiums_reference.json  (32 stadiums)
│   │
│   └── ncaaf/
│       ├── game_forecasts_2025_week1.json
│       ├── stadium_conditions_2025_week1.parquet
│       ├── regional_weather_2025_week1.json
│       └── stadiums_reference.json  (130+ stadiums)

├── massey/
│   ├── nfl_ratings_2025_week12.json
│   └── ncaaf_ratings_2025_week1.json

└── analysis/
    ├── nfl/
    │   ├── edge_detection_2025_week12.json
    │   ├── power_ratings_2025_week12.json
    │   ├── clv_tracking_2025.parquet
    │   └── recommendations_2025_week12.json
    │
    └── ncaaf/
        ├── edge_detection_2025_week1.json
        ├── power_ratings_2025_week1.json
        ├── clv_tracking_2025.parquet
        ├── conference_edges_2025_week1.json
        └── recommendations_2025_week1.json
```

---

## Data Extraction Examples

### Load NFL Data Only

```python
import json
import pandas as pd

# Load NFL odds
with open('output/overtime/nfl/pregame/2025-01-12_pregame.json') as f:
    nfl_odds = json.load(f)  # Pure NFL games

# Load NFL stats
nfl_stats = pd.read_parquet('output/espn/nfl/team_stats_2025_week12.parquet')
# 32 teams, NFL only

# Load NFL edges
with open('output/analysis/nfl/edge_detection_2025_week12.json') as f:
    nfl_edges = json.load(f)
```

### Load NCAAF Data Only

```python
import json
import pandas as pd

# Load NCAAF odds
with open('output/overtime/ncaaf/pregame/2025-09-06_pregame.json') as f:
    ncaaf_odds = json.load(f)  # Pure NCAAF games

# Load NCAAF stats
ncaaf_stats = pd.read_parquet('output/espn/ncaaf/team_stats_2025_week1.parquet')
# 130+ teams, college only

# Load NCAAF edges
with open('output/analysis/ncaaf/edge_detection_2025_week1.json') as f:
    ncaaf_edges = json.load(f)
```

### Cross-Check No Contamination

```python
import json
from pathlib import Path

def verify_no_mixing():
    """Ensure no NFL data in NCAAF and vice versa"""

    # Check NFL files have NFL data
    with open('output/espn/nfl/teams_reference.json') as f:
        nfl_teams = json.load(f)
    assert len(nfl_teams) == 32, f"NFL should have 32 teams, got {len(nfl_teams)}"

    # Check NCAAF files have NCAAF data
    with open('output/espn/ncaaf/teams_reference.json') as f:
        ncaaf_teams = json.load(f)
    assert len(ncaaf_teams) >= 130, f"NCAAF should have 130+ teams, got {len(ncaaf_teams)}"

    # Check no mixed files
    for f in Path('output').rglob('*'):
        name = f.name.lower()
        if 'nfl' in name and 'ncaaf' in name:
            raise ValueError(f"Mixed file found: {f}")

    print("[OK] No data contamination detected!")

verify_no_mixing()
```

---

## Verification Checklist

**Before running analysis:**

- [ ] Collect with **single league flag** (`--nfl` OR `--ncaaf`, not both)
- [ ] Verify output in separate directories:
  ```bash
  ls output/*/nfl/    # Should have files
  ls output/*/ncaaf/  # Should have files (separate)
  ```
- [ ] Check file sizes (not 0 bytes)
- [ ] Run verification script:
  ```bash
  uv run python scripts/validation/verify_data_structure.py
  ```
- [ ] Test data extraction (sample code above)
- [ ] Confirm team counts (32 NFL, 130+ NCAAF)

---

## Troubleshooting

### Problem: "Files are mixed in same directory"

**Cause:** Used `--nfl --ncaaf` together

**Solution:**
```bash
# WRONG (don't do this)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf

# RIGHT (do this instead)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf
```

### Problem: "Can't find NFL data"

**Check 1:** Is it in the right directory?
```bash
ls output/*/nfl/ | grep -i "pregame\|stats\|odds"
```

**Check 2:** Was it collected?
```bash
# Verify it was collected recently
ls -lh output/overtime/nfl/pregame/*.json | tail -1
```

**Check 3:** Is it empty?
```bash
# Check file size
du -sh output/overnight/nfl/pregame/*.json
```

### Problem: "Accidentally mixed NFL and NCAAF"

**Minimal fix:**
```bash
# Move mixed files to correct league
# Then re-collect the affected league separately
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
uv run python scripts/scrapers/scrape_overtime_api.py --ncaaf

# Verify
uv run python scripts/validation/verify_data_structure.py
```

---

## Documentation Reference

For detailed information, see:

| Topic | Document |
|-------|----------|
| **NFL Collection Details** | [NFL_DATA_COLLECTION_WORKFLOW.md](NFL_DATA_COLLECTION_WORKFLOW.md) |
| **NCAAF Collection Details** | [NCAAF_DATA_COLLECTION_WORKFLOW.md](NCAAF_DATA_COLLECTION_WORKFLOW.md) |
| **Verification Tools** | [DATA_OUTPUT_STRUCTURE_VERIFICATION.md](DATA_OUTPUT_STRUCTURE_VERIFICATION.md) |
| **Architecture Overview** | [DATA_COLLECTION_ARCHITECTURE.md](DATA_COLLECTION_ARCHITECTURE.md) |
| **Quick Reference** | [DATA_COLLECTION_QUICK_REFERENCE.md](../../DATA_COLLECTION_QUICK_REFERENCE.md) |

---

## Summary

**Key Rules:**

1. ✅ Collect NFL only: `--nfl`
2. ✅ Collect NCAAF only: `--ncaaf`
3. ✅ Store in separate directories: `nfl/` and `ncaaf/`
4. ✅ Load only what you need (no intermixing)
5. ✅ Verify after collection

**Never:**

1. ❌ Use `--nfl --ncaaf` together
2. ❌ Store NFL data in NCAAF folder
3. ❌ Store NCAAF data in NFL folder
4. ❌ Mix data when extracting
5. ❌ Skip verification

---

**Document Version:** 1.0
**Last Updated:** 2025-11-25
**Maintained By:** Billy Walters Sports Analyzer Team
