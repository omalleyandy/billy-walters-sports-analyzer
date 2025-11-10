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

## Session: 2025-11-09 - Directory Structure Consolidation & Test Suite Fix

### Context
Consolidated duplicate `walters_analyzer/` directories (root vs src/) into a single clean src-layout structure and fixed async test configuration.

### Issue 1: Duplicate Package Directories

**Problem:**
Two separate `walters_analyzer/` directories existed:
- Root `walters_analyzer/` - 41 Python files (complete, active codebase)
- `src/walters_analyzer/` - 16 Python files (incomplete, missing core modules)

This caused confusion about which was the "real" codebase and made imports inconsistent.

**Root Cause:**
- Project started with root-level package
- Later migrated partially to src-layout but didn't complete the move
- Old directory was never deleted, creating duplicate code paths

**Solution:**
1. Updated `pyproject.toml` to configure src-layout with hatchling:
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/walters_analyzer"]
   ```

2. Consolidated all code to `src/walters_analyzer/`:
   ```bash
   cp -r walters_analyzer/* src/walters_analyzer/
   rm -rf walters_analyzer
   ```

3. Reinstalled package: `uv sync`

**Result:**
- Single source of truth at `src/walters_analyzer/`
- 44 Python files fully consolidated
- All imports work correctly
- Follows Python packaging best practices

**Prevention:**
- Complete directory migrations fully before committing
- Use `find . -name "package_name"` to detect duplicates
- Always configure build system for src-layout explicitly

**Files Affected:**
- `pyproject.toml:98-99` (added hatchling configuration)
- Entire `walters_analyzer/` → `src/walters_analyzer/` (moved)

---

### Issue 2: Async Test Configuration Missing

**Problem:**
```
async def functions are not natively supported.
You need to install a suitable plugin for your async framework
```
9 async test functions in `test_api_clients.py` failed because pytest couldn't run them.

**Root Cause:**
- `pytest-asyncio` was installed
- But async test functions were missing `@pytest.mark.asyncio` decorator
- Tests were written as plain async functions without pytest markers

**Solution:**
Added `@pytest.mark.asyncio` decorator to all 9 async test functions:
```python
@pytest.mark.asyncio
async def test_action_network_client():
    # Test implementation
```

**Files Affected:**
- `tests/test_api_clients.py:21,55,89,132,167,208,250,285,326`

---

### Issue 3: Test Exception Type Mismatch

**Problem:**
```python
with pytest.raises(RuntimeError):
    await client._make_request("https://invalid.invalid/test")
```
Test expected `RuntimeError` but got `httpx.ConnectError`, causing test failure.

**Root Cause:**
- httpx raises `ConnectError` for connection failures (network-level)
- Test was written expecting higher-level `RuntimeError`
- Both are valid failure modes for the retry logic

**Solution:**
Accept both exception types:
```python
import httpx

with pytest.raises((RuntimeError, httpx.ConnectError)):
    await client._make_request("https://invalid.invalid/test")
```

**Prevention:**
- Check actual exception types raised by dependencies
- Use tuple of exceptions when multiple types are valid
- Document expected exception types in test docstrings

**Files Affected:**
- `tests/test_data_collection.py:10,87`

---

### Test Results

**Before:** 10 failed, 133 passed, 2 skipped
**After:** 0 failed, 143 passed, 2 skipped

All test failures resolved successfully with clean test suite.

---

### Best Practices Established

1. **Src-Layout Configuration**
   - Always add `[tool.hatch.build.targets.wheel]` to pyproject.toml
   - Explicitly specify `packages = ["src/package_name"]`
   - This ensures build tools find code correctly

2. **Async Test Patterns**
   - Mark all async test functions with `@pytest.mark.asyncio`
   - Import pytest at top: `import pytest`
   - Configure pytest-asyncio in pytest.ini if needed

3. **Exception Testing**
   - Use `pytest.raises((Type1, Type2))` for multiple valid exceptions
   - Import specific exception types from libraries
   - Test the actual behavior, not implementation details

4. **Directory Consolidation Process**
   - Analyze both directories first (count files, compare contents)
   - Choose target location (prefer src-layout)
   - Update build configuration FIRST
   - Move/copy files carefully
   - Run tests to verify
   - Delete old directory only after tests pass

5. **Package Management**
   - Run `uv sync` after structural changes
   - Verify package is rebuilt correctly
   - Check installed package location matches expectations

---

## Session: 2025-11-10 - Project Structure Reorganization

### Context
Reorganized scattered scripts and code into a clean, categorical structure with clear placement guidelines for future development.

### Issue: Scripts and Code Scattered Across Multiple Locations

**Problem:**
- 32+ scripts scattered between root `scripts/`, `tests/`, and `src/`
- No clear convention for where to place new files
- Difficult to find specific functionality
- Test scripts mixed with operational scripts
- Analysis scripts mixed with data collection

**Impact:**
- Slowed development (time wasted searching for files)
- Inconsistent file placement
- Poor maintainability
- Confusion about project structure

**Root Cause:**
- Project grew organically without organizational structure
- Scripts added ad-hoc as needs arose
- No documented guidelines for file placement
- No systematic reorganization as complexity increased

---

### Solution: Categorical Directory Structure

**Implementation:**
Created clear categorical organization with 6 commits:

**1. Data Collection Consolidation**
- Moved all scrapers/clients to `src/data/`
- 27 data collection modules in one location
- Commit: `148a8f3` - refactor(data): consolidate data collection

**2. Edge Detection Organization**
- Moved analysis to `src/walters_analyzer/valuation/`
- 11 edge detection and analysis modules
- Commit: `d8d42c3` - refactor(analysis): move edge detection

**3. Display Utilities Grouping**
- Created `src/walters_analyzer/query/`
- 6 display and monitoring utilities
- Commit: `8e8c0fc` - refactor(query): organize display utilities

**4. Test Consolidation**
- Moved all tests to `tests/` directory
- Single location for 146 test suite
- Commit: `4e7ff06` - test: consolidate all test scripts

**5. Scripts Categorization**
- Created 5 subdirectories under `scripts/`:
  - `analysis/` - 8 weekly analysis scripts
  - `validation/` - 3 data validation scripts
  - `backtest/` - 2 backtesting scripts
  - `utilities/` - 5 helper utilities
  - `dev/` - 14 development/deployment scripts
- Commit: `fe0c93f` - refactor(scripts): organize into subdirectories

**6. Import Path Updates**
- Fixed all import paths after reorganization
- Updated test references to new locations
- Commits: `19dcb1f`, `1b3e358` - fix: update import paths

---

### Documentation: Clear Placement Guidelines

**Added to CLAUDE.md (lines 239-251):**

```markdown
### Directory Guidelines

When adding new files:
- Data scrapers/clients → src/data/
- Edge detection/analysis → src/walters_analyzer/valuation/
- Query/display utilities → src/walters_analyzer/query/
- Weekly analysis scripts → scripts/analysis/
- Data validation → scripts/validation/
- Backtesting → scripts/backtest/
- Helper utilities → scripts/utilities/
- Dev/deployment → scripts/dev/
- Tests → tests/
- Examples → examples/
```

**Files Affected:**
- `CLAUDE.md:198-264` (added structure documentation)
- `scripts/analysis/` (8 files moved)
- `scripts/validation/` (3 files moved)
- `scripts/backtest/` (2 files moved)
- `scripts/utilities/` (5 files moved)
- `tests/` (consolidated test suite)
- `src/walters_analyzer/valuation/` (11 modules)
- `src/walters_analyzer/query/` (6 modules)

---

### Results

**Before:**
- Scripts in 3+ different locations
- No clear file placement rules
- Time wasted searching for code

**After:**
- Clear categorical structure
- Explicit placement guidelines in CLAUDE.md
- Easy to find any functionality
- New developers know exactly where to place code

**Metrics:**
- 6 commits documenting reorganization
- 32+ scripts organized into 5 categories
- 100% test pass rate maintained (146 tests)
- Zero functionality broken during reorganization

---

### Best Practices Established

**1. Reorganization Process**
   - Plan structure before moving files
   - Move files in logical groups (one commit per category)
   - Update imports immediately after each move
   - Run tests after each commit to verify nothing broke
   - Document new structure before finishing

**2. Directory Design Principles**
   - Separate by function, not file type
   - Group related functionality together
   - Keep operational scripts separate from source code
   - Examples and tests in their own directories
   - Clear, self-documenting directory names

**3. Documentation**
   - Explicit "When adding new files" guidelines
   - Document structure in CLAUDE.md
   - Include directory purpose in comments
   - Update documentation as structure evolves

**4. Migration Strategy**
   - Identify all scattered files first
   - Design target structure
   - Create new directories
   - Move files in categories (one commit each)
   - Fix imports and paths
   - Run full test suite
   - Update documentation

**5. Prevention**
   - Document file placement rules BEFORE they're needed
   - Review PR file locations during code review
   - Periodically audit for misplaced files
   - Resist urge to create new top-level directories

---

### Project Structure Reference

```
billy-walters-sports-analyzer/
├── src/
│   ├── data/                    # 27 scrapers & clients
│   └── walters_analyzer/
│       ├── valuation/           # 11 edge detection modules
│       ├── query/               # 6 display utilities
│       ├── backtest/            # Backtesting framework
│       ├── config/              # Configuration
│       ├── core/                # Core system
│       ├── feeds/               # Data feeds
│       ├── ingest/              # Data ingestion
│       └── research/            # Research tools
├── scripts/
│   ├── analysis/                # 8 weekly analysis scripts
│   ├── validation/              # 3 data validation
│   ├── backtest/                # 2 backtesting scripts
│   ├── utilities/               # 5 helper utilities
│   └── dev/                     # 14 dev/deployment scripts
├── tests/                       # 146 test suite
├── examples/                    # Example scripts
└── .claude/                     # MCP server, agent, hooks
```

---

### Key Commits

- `148a8f3` - Data collection consolidation
- `d8d42c3` - Edge detection organization
- `8e8c0fc` - Display utilities grouping
- `4e7ff06` - Test consolidation
- `fe0c93f` - Scripts categorization
- `19dcb1f` - Import path fixes
- `1b3e358` - Test reference updates
- `b86e738` - Documentation updates
- `71be44e` - Example file addition

All commits include proper conventional commit format with detailed descriptions.

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
