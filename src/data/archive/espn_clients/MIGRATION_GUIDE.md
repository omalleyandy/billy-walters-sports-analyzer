# ESPN API Client Migration Guide

**Status:** `espn_api_client.py` is archived (deprecated)
**Date Archived:** 2025-11-25
**Archive Location:** `src/data/archive/espn_clients/`

## Quick Summary

The old `espn_api_client.py` has been archived in favor of `espn_client.py` (AsyncESPNClient). Both files are available in this folder for reference during migration.

## Why Archive?

The new AsyncESPNClient is superior:
- ✅ Async/await support for better concurrency
- ✅ Automatic retry logic with exponential backoff
- ✅ Circuit breaker pattern for resilience
- ✅ Rate limiting (respects ESPN's API)
- ✅ Superior error handling
- ✅ Same methods, same API

## Files in This Archive

1. **espn_api_client.py** - Old synchronous client (reference only)
2. **MIGRATION_GUIDE.md** - This file

## Legacy Code Using Old Client

The following files import the old client and need migration:

### Database Loaders (src/data/archive or scripts/database/)
- `scripts/database/load_espn_injuries.py`
- `scripts/database/load_espn_scoreboards_standings.py`
- `scripts/database/load_espn_team_stats.py`

### Utilities (scripts/utilities/)
- `scripts/utilities/extract_espn_teams.py`

### Tests (tests/)
- `tests/test_espn_data_qa.py`

### Archive (src/data/archive/)
- `src/data/archive/unified_data_orchestrator.py`

## Migration Path

### Step 1: Update Import

**Old:**
```python
from src.data.espn_api_client import ESPNAPIClient

api = ESPNAPIClient()
data = api.get_nfl_teams()
```

**New:**
```python
from src.data import AsyncESPNClient

async with AsyncESPNClient() as client:
    data = await client.get_teams("NFL")
```

### Step 2: Convert to Async

The new client requires async/await. If migrating a sync script:

```python
import asyncio
from src.data import AsyncESPNClient

async def get_data():
    async with AsyncESPNClient() as client:
        teams = await client.get_teams("NFL")
        return teams

if __name__ == "__main__":
    result = asyncio.run(get_data())
```

### Step 3: Method Mapping

| Old Method | New Method | Notes |
|-----------|-----------|-------|
| `get_nfl_teams()` | `get_teams("NFL")` | Async |
| `get_ncaaf_teams(group='80')` | `get_teams("NCAAF")` | Async, group param removed |
| `get_nfl_scoreboard()` | `get_scoreboard("NFL", week)` | Async, week optional |
| `get_ncaaf_scoreboard()` | `get_scoreboard("NCAAF", week)` | Async, week optional |
| `get_nfl_standings()` | `get_standings("NFL")` | Async |
| `get_ncaaf_standings()` | `get_standings("NCAAF")` | Async |
| `get_team_statistics()` | `get_team_stats()` | Async |
| `get_team_injuries()` | `get_team_injuries()` | Async |

## Reference: Archived Methods

Keep this file for reference when migrating older code. The old client's implementation is preserved here for comparison.

## Next Steps

1. Migrate database loading scripts (can be deferred)
2. Migrate test utilities (can be deferred)
3. Update any custom scripts using old client
4. Once all migrated, this archive can be removed (not urgent)

## Questions?

See `docs/guides/DATA_COLLECTION_ARCHITECTURE.md` for detailed architecture and ESPN client information.

---

**Archive Created:** 2025-11-25
**Archiver:** Claude (Billy Walters Sports Analyzer cleanup session)
