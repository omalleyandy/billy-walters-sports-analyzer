# Lessons Learned

This document captures issues encountered during development, their solutions, and best practices for the Billy Walters Sports Analyzer project.

---

## Session: 2025-11-09 - NFL Season Calendar Implementation

### Context
Implemented automated NFL week detection based on current date to ensure analysis always uses the correct week's data.

### Issue 1: Windows Console Unicode/Emoji Encoding

**Problem:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4c5' in position 0
```
Python console output on Windows (cp1252 encoding) cannot display emoji characters used in example scripts.

**Root Cause:**
- Windows console defaults to cp1252 encoding, not UTF-8
- Emoji characters (📅, ✅, 🏆, etc.) are outside cp1252 character set
- This affects any print statements with emoji

**Solution:**
Remove emoji from console output or use ASCII alternatives:
```python
# Before (causes error on Windows)
print(f"📅 {format_season_status()}\n")

# After (works cross-platform)
print(f"Status: {format_season_status()}\n")
```

**Prevention:**
- Avoid emoji in CLI tools and console output
- Use emoji only in web interfaces or when UTF-8 is guaranteed
- Consider adding `PYTHONIOENCODING=utf-8` to environment on Windows if emoji is essential

**Files Affected:**
- `examples/current_week_example.py:40-70`

---

### Issue 2: Module Import Path Configuration

**Problem:**
```
ModuleNotFoundError: No module named 'walters_analyzer.season_calendar'
```
New module `season_calendar.py` created in `src/walters_analyzer/` but couldn't be imported from example scripts.

**Root Cause:**
- Example scripts run from project root, not from `src/`
- Python doesn't automatically add `src/` to import path
- Package needs to be installed or path needs manual configuration

**Solutions:**

**Option 1: Run from src directory (preferred for development)**
```bash
cd src && uv run python -m walters_analyzer.season_calendar
```

**Option 2: Add path manipulation in examples**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

**Option 3: Install package in editable mode**
```bash
uv pip install -e .
```

**Best Practice:**
- For development/testing: Run from `src/` directory
- For production scripts: Install package properly
- For examples: Include path setup in file header with clear instructions

**Files Affected:**
- `examples/current_week_example.py:14-19`
- All future example scripts

---

### Issue 3: NFL Season Calendar Configuration

**Decision:**
Hardcoded NFL 2025 season dates in `season_calendar.py` rather than using dynamic configuration or API.

**Rationale:**
- NFL season dates are published well in advance
- Schedule structure (18 weeks, playoff format) is consistent
- Hardcoding is simpler and more reliable than API dependency
- Easy to update annually (once per year maintenance)

**Key Dates Configured:**
- Week 1 Start: September 4, 2025 (Thursday)
- Regular Season: 18 weeks
- Playoff Start: January 10, 2026
- Super Bowl LX: February 8, 2026

**Future Maintenance:**
Update these constants annually in `season_calendar.py:16-20` when NFL publishes next season's schedule.

**Files Affected:**
- `src/walters_analyzer/season_calendar.py:16-20`

---

### Success: Data Validation Hook Testing

**Achievement:**
Successfully tested data validation hook with multiple data types (odds, weather, game).

**Key Learnings:**
- Hook correctly validates realistic data ranges
- Returns proper JSON output for both valid and invalid data
- Exit codes work correctly (0 for valid, 1 for invalid)

**Test Command Pattern:**
```bash
echo '{"type": "odds", "data": {...}}' | python .claude/hooks/validate_data.py
```

**Validation Ranges Confirmed:**
- Spread: -50 to 50 points
- Over/Under: 20 to 100 points
- Moneyline: -10000 to 10000
- Temperature: -20°F to 130°F
- Wind Speed: 0 to 100 mph
- Precipitation: 0 to 1 (probability)

**Files:**
- `.claude/hooks/validate_data.py`

---

### Best Practices Established

1. **Season Calendar Usage**
   - Always check current week before fetching data
   - Use `get_nfl_week()` to auto-determine week number
   - Construct URLs dynamically: `f"https://www.nfl.com/schedules/2025/REG{week}"`

2. **Cross-Platform Compatibility**
   - Avoid emoji in console output
   - Test on Windows (cp1252) not just Unix (UTF-8)
   - Use ASCII alternatives for status indicators

3. **Module Organization**
   - Place utilities in `src/walters_analyzer/`
   - Examples in `examples/` with path setup
   - Run development code from `src/` directory

4. **Documentation**
   - Document issues immediately when solved
   - Include file references with line numbers
   - Provide both problem and solution code

---

## Template for Future Entries

### Session: YYYY-MM-DD - Brief Description

**Context:**
What were you working on?

**Issue: Problem Title**

**Problem:**
What went wrong? Include error messages.

**Root Cause:**
Why did it happen?

**Solution:**
How was it fixed? Include code examples.

**Prevention:**
How to avoid this in the future?

**Files Affected:**
- `path/to/file.py:line_numbers`

---

## Quick Reference

### Common Commands
```bash
# Check current NFL week
cd src && uv run python -m walters_analyzer.season_calendar

# Test data validation
echo '{"type": "odds", "data": {...}}' | python .claude/hooks/validate_data.py

# Run example scripts
python examples/current_week_example.py

# Install package in editable mode
uv pip install -e .
```

### Useful File Locations
- Season calendar: `src/walters_analyzer/season_calendar.py`
- Data validation: `.claude/hooks/validate_data.py`
- Validation logger: `.claude/hooks/validation_logger.py`
- MCP validation: `.claude/hooks/mcp_validation.py`
- Slash commands: `.claude/commands/*.md`
- Development guidelines: `CLAUDE.md`

---

## Session: 2025-11-09 - Validation System Implementation

### Context
Fixed broken validation code in autonomous agent and implemented a complete validation system with structured logging.

### Issue 1: Broken Imports in Autonomous Agent

**Problem:**
The `walters_autonomous_agent.py` file had non-existent imports that caused failures:
```python
from .hooks.validation_logger import ValidationLogger  # Module didn't exist
from .hooks.mcp_validation import fetch_and_validate_odds  # Module didn't exist
```

**Root Cause:**
- Imports were added but the modules were never created
- Orphaned `analyze_game()` function was never called
- Duplicate logger assignment (line 26 then line 46)

**Solution:**
1. Removed broken imports and orphaned code (lines 23-35)
2. Created `validation_logger.py` module
3. Created `mcp_validation.py` module
4. Re-integrated validation with proper error handling

**Files Affected:**
- `.claude/walters_autonomous_agent.py:23-35` (removed)
- `.claude/walters_autonomous_agent.py:23-36` (new imports)
- `.claude/walters_autonomous_agent.py:152-162` (validation integration)

---

### Success: Validation System Implementation

**Achievement:**
Built a complete validation system with three components:

**1. validate_data.py (Hook)**
- Standalone validation script
- Validates odds, weather, and game data
- Returns JSON results
- Can be called from command line or subprocess

**2. validation_logger.py (Logger)**
- Structured logging for validation events
- Tracks statistics (success rate, failures by type)
- Saves reports to JSON
- Singleton pattern with `get_logger()`

**3. mcp_validation.py (Integration)**
- Async validation functions
- Integrates validate_data.py and validation_logger
- Provides `fetch_and_validate_*` functions
- Handles both async and sync fetch functions

**Architecture:**
```
Autonomous Agent
    ↓
mcp_validation.py (async wrapper)
    ↓
validate_data.py (subprocess validation)
    ↓
validation_logger.py (structured logging)
```

**Key Functions:**
```python
# Validate data directly
result = await validate_odds_data(odds)

# Fetch and validate
odds = await fetch_and_validate_odds(game_id, fetch_function)

# Get validation statistics
stats = logger.get_statistics()
```

**Files Created:**
- `.claude/hooks/validation_logger.py` (248 lines)
- `.claude/hooks/mcp_validation.py` (370 lines)
- `.claude/test_validation_integration.py` (test suite)

---

### Issue 2: Relative Imports in Standalone Scripts

**Problem:**
```python
from .validation_logger import get_logger  # ImportError when run directly
```

Scripts with relative imports fail when executed as `python script.py`.

**Root Cause:**
- Relative imports require the module to be part of a package
- Running directly treats it as `__main__`, not a module

**Solution:**
Use try/except to handle both import scenarios:
```python
try:
    from .validation_logger import get_logger  # Package import
except ImportError:
    from validation_logger import get_logger  # Direct import
```

**Prevention:**
- Use this pattern for all modules that may be run standalone
- Consider adding `if __name__ == "__main__"` examples
- Test both import methods during development

**Files Affected:**
- `.claude/hooks/mcp_validation.py:14-18`

---

### Best Practices Established

1. **Validation Pattern**
   - Separate validation logic (validate_data.py)
   - Structured logging (validation_logger.py)
   - Integration layer (mcp_validation.py)
   - This creates testable, reusable components

2. **Error Handling**
   - Use try/except in autonomous agent to not block on validation
   - Log warnings for validation failures
   - Raise ValueError in fetch_and_validate for critical failures

3. **Testing Approach**
   - Create dedicated test scripts
   - Test each component independently
   - Test integration end-to-end
   - All tests passed successfully

4. **Windows Compatibility**
   - Remove ALL emoji from validation error messages
   - Use plain ASCII text for cross-platform compatibility
   - This fixed multiple UnicodeEncodeError issues

---

### Validation Ranges Reference

**Odds:**
- Spread: -50 to 50 points
- Over/Under: 20 to 100 points
- Moneyline: -10000 to 10000

**Weather:**
- Temperature: -20°F to 130°F
- Wind Speed: 0 to 100 mph
- Precipitation Probability: 0 to 1 (0-100%)

**Game:**
- Required fields: game_id, home_team, away_team, game_date
- Date format: ISO 8601 (e.g., "2025-11-16T13:00:00Z")
- League: Must be "NFL" or "NCAAF"

---
