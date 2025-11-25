# Pre-Flight Validation - Verify Environment Before Data Collection

Quick pre-flight check to ensure your environment is ready for data collection.

## Usage

```bash
/pre-validate
```

## What This Command Does

Runs comprehensive pre-flight validation that checks:

1. **API Keys Present**
   - ACCUWEATHER_API_KEY for weather data
   - OV_CUSTOMER_ID and OV_PASSWORD for Overtime.ag odds
   - ACTION_USERNAME and ACTION_PASSWORD for Action Network (optional)
   - OPENWEATHER_API_KEY for weather backup (optional)

2. **Database Connection**
   - Verifies database is accessible
   - Tests read/write permissions
   - Confirms schema exists

3. **Output Directories**
   - `output/` exists and is writable
   - `data/current/` exists for raw data
   - `data/raw/` exists for backup data
   - All required subdirectories ready

4. **Current Week Detection**
   - Automatically detects current NFL/NCAAF week from system date
   - Validates week number (1-18 for NFL, 1-15 for NCAAF)
   - Shows detected week in output

5. **Process Locking**
   - Ensures no data collection already running
   - Prevents concurrent collection (which would corrupt data)
   - Shows running process info if one is detected

## Exit Codes

- **0** = All checks passed ✅
  - Safe to proceed with `/collect-all-data`
  - All API keys present and valid
  - Database ready
  - Week detected successfully

- **1** = Critical issue found ❌
  - Missing required API key (cannot proceed)
  - Database connection failed (cannot proceed)
  - Missing output directories (cannot proceed)
  - Fix issues before running `/collect-all-data`

## Output Example

```
============================================================
PRE-FLIGHT VALIDATION - 2025-11-24
============================================================

ENVIRONMENT CHECKS
- API Keys: PASS (4/4 required)
  ✓ ACCUWEATHER_API_KEY present
  ✓ OV_CUSTOMER_ID present
  ✓ OV_PASSWORD present
  ✓ OPENWEATHER_API_KEY present

DATABASE CONNECTION
- Status: PASS
  ✓ Connected to database
  ✓ Schema verified
  ✓ Read/write permissions OK

OUTPUT DIRECTORIES
- Status: PASS (5/5 directories)
  ✓ output/
  ✓ data/current/
  ✓ data/raw/
  ✓ output/overtime/
  ✓ output/edge_detection/

WEEK DETECTION
- Current NFL Week: 12
- System Date: 2025-11-24 (Nov 20-26, Week 12 range)
- Detection: PASS

PROCESS LOCKING
- Status: PASS
- No data collection in progress
- Safe to proceed

============================================================
OVERALL: READY TO PROCEED ✓
Run: /collect-all-data
============================================================
```

## Common Issues & Fixes

### Missing API Key
```
ERROR: ACCUWEATHER_API_KEY not found
Action: Add ACCUWEATHER_API_KEY=your_key to .env file
```

### Database Connection Failed
```
ERROR: Cannot connect to database
Action: Verify database is running
        Check database credentials in .env
        Run: python -c "from src.db import get_db_connection; get_db_connection()"
```

### Missing Output Directories
```
ERROR: output/ directory not found
Action: Create directories: mkdir -p output data/current data/raw
```

### Week Detection Failed
```
WARNING: Could not auto-detect week
Info: Using system date fallback
Action: Run: /current-week to verify detected week
```

### Data Collection Already Running
```
ERROR: Data collection process detected (PID: 12345)
Action: Wait for process to complete, or kill it: kill 12345
```

## Related Commands

- `/collect-all-data` - Run after this passes (main workflow)
- `/validate-data` - Check data quality after collection
- `/current-week` - Verify current week number
- `/pre-edge-detection` - Pre-flight check before edge detection

## Manual Alternative

If you prefer to run pre-flight validation manually:

```bash
python .claude/hooks/pre_data_collection_validator.py
```

This runs the same checks and is useful for debugging environment issues.

---

**When to Run:** Before starting data collection workflow (`/collect-all-data`)
**Time Required:** <10 seconds
**Frequency:** Once per session (automatic before `/collect-all-data`)
