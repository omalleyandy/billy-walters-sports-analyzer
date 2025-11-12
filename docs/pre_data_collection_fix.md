# Pre-Data Collection Hook Fix - Week Validation

**Date**: 2025-11-12  
**Status**: ✅ FIXED  
**Commit**: 55f7a2b

---

## Issue Discovered

### The Bug
**File**: `.claude/hooks/pre_data_collection.py`

**Problem**: When `current_week` was `None` (during offseason/playoffs), the hook would:
1. ❌ Still pass validation (`all_checks_passed` remained `True`)
2. ❌ Generate invalid command: `--week None`
3. ❌ Exit with code 0 (success) instead of code 1 (failure)

**Inconsistency**: Other hooks (`post_data_collection.py`, `auto_edge_detector.py`) properly handle `None` week by exiting with code 1.

### Root Cause

**Line 173**: `current_week, detection_method = check_current_week()`
- Returns `(None, "offseason or playoffs")` during offseason
- Returns `(None, "detection failed: ...")` on error

**Missing**: No validation to check if `current_week is None`
- Code continued to success block at line 191
- Generated invalid command at line 205: `--week None`
- Exited with code 0 (wrong!)

---

## The Fix

### Code Changes

**Location**: `.claude/hooks/pre_data_collection.py` lines 176-179

**Added**:
```python
# Validate week detection (offseason/playoffs check)
if current_week is None:
    print("   [ERROR] Could not determine current week (offseason/playoffs?)")
    all_checks_passed = False
```

### Logic Flow (After Fix)

```
1. Line 173: current_week = check_current_week()
   → Returns None during offseason/playoffs

2. Lines 177-179: if current_week is None:
   → Prints error message
   → Sets all_checks_passed = False

3. Line 191: if all_checks_passed:
   → FALSE (skips success block)

4. Line 209: else:
   → Prints "PRE-FLIGHT CHECKS FAILED"
   → sys.exit(1) ✅ Correct!
```

### Consistency with Other Hooks

**post_data_collection.py** (lines 191-194):
```python
if week is None:
    print("[ERROR] Could not determine current week (offseason/playoffs?)")
    print("Usage: python post_data_collection.py [week]")
    sys.exit(1)
```

**auto_edge_detector.py** (lines 183-185):
```python
if week is None:
    print("[ERROR] Could not determine current week (offseason/playoffs?)")
    sys.exit(1)
```

**pre_data_collection.py** (NOW FIXED, lines 177-179):
```python
if current_week is None:
    print("   [ERROR] Could not determine current week (offseason/playoffs?)")
    all_checks_passed = False  # → Eventually calls sys.exit(1)
```

---

## Testing

### During NFL Season (Current - Week 10)

**Command**: `python .claude/hooks/pre_data_collection.py`

**Output**:
```
3. Detecting current NFL week...
   Current week: 10 (auto-detected)

[OK] PRE-FLIGHT CHECKS PASSED

Ready to collect data for week 10

Recommended command:
  uv run python scripts/utilities/update_all_data.py --week 10
```

**Result**: ✅ Works correctly, validation passes, valid command generated

### During Offseason/Playoffs (Simulated)

**Expected Behavior** (when `check_current_week()` returns `None`):

**Output**:
```
3. Detecting current NFL week...
   Current week: None (offseason or playoffs)
   [ERROR] Could not determine current week (offseason/playoffs?)

[ERROR] PRE-FLIGHT CHECKS FAILED

Please resolve the errors above before collecting data.
```

**Exit Code**: 1 (failure) ✅

**Result**: ✅ Properly fails validation, no invalid command generated

---

## Impact

### Before Fix
- ❌ Hook would pass during offseason
- ❌ Invalid command generated: `--week None`
- ❌ Exit code 0 (misleading success)
- ❌ Downstream scripts would fail with confusing errors

### After Fix
- ✅ Hook fails during offseason (correct)
- ✅ Clear error message displayed
- ✅ Exit code 1 (proper failure)
- ✅ Prevents invalid command execution
- ✅ Consistent with other hooks

---

## Documentation

### Where to Find This

**CLAUDE.md** - Not yet documented (should be added to Troubleshooting)

**LESSONS_LEARNED.md** - Should be added for future reference

**This File** - `docs/pre_data_collection_fix.md` (detailed analysis)

### Recommended Documentation Updates

Add to **CLAUDE.md** Troubleshooting section:
```markdown
**Pre-data collection hook failing:**
```bash
# Symptom: Hook passes during offseason with "week None"
# Symptom: Invalid command generated: --week None

# Root Cause: Missing validation for current_week is None

# Fix Applied: Added validation check (line 177-179)
# - Checks if current_week is None
# - Sets all_checks_passed = False
# - Prevents invalid command generation

# Verify Fix Working:
python .claude/hooks/pre_data_collection.py

# Expected during season:
# Current week: 10 (auto-detected)
# [OK] PRE-FLIGHT CHECKS PASSED

# Expected during offseason:
# Current week: None (offseason or playoffs)
# [ERROR] Could not determine current week
# [ERROR] PRE-FLIGHT CHECKS FAILED

# Commit: 55f7a2b
# Documentation: docs/pre_data_collection_fix.md
```
```

---

## Git History

### Commit Details

**Commit**: `55f7a2b`  
**Type**: `fix(hooks)`  
**Summary**: Prevent pre_data_collection from passing when week is None

**Files Changed**: 1
- `.claude/hooks/pre_data_collection.py` (7 insertions, 1 deletion)

**Lines Modified**:
- Added: 176-179 (validation check)
- Modified: 220 (newline at EOF)

**Status**: ✅ Pushed to GitHub (origin/main)

---

## Future Considerations

### Offseason Handling

When the NFL offseason arrives:
1. ✅ pre_data_collection.py will properly fail
2. ✅ Error message will explain why (offseason/playoffs)
3. ✅ No invalid commands will be generated
4. ✅ User can manually override with specific week if needed

### Testing Recommendations

**During Season**:
- Run hook regularly to ensure it detects current week
- Verify recommended command is valid

**Before Offseason**:
- Test hook behavior when season ends
- Verify proper failure with clear error message
- Document any edge cases

### Similar Patterns to Check

Other hooks that use `get_nfl_week()`:
- ✅ post_data_collection.py - Properly validates week
- ✅ auto_edge_detector.py - Properly validates week
- ✅ pre_data_collection.py - NOW properly validates week

**Consistency**: All three hooks now handle `None` week identically.

---

## Summary

✅ **Critical bug fixed**: pre_data_collection hook now properly fails when week cannot be determined  
✅ **Validation added**: Checks `current_week is None` → sets `all_checks_passed = False`  
✅ **Error handling**: Exits with code 1 (failure) during offseason/playoffs  
✅ **Consistency**: Matches behavior of other hooks  
✅ **Tested**: Works correctly during NFL season (Week 10)  
✅ **Committed**: 55f7a2b pushed to GitHub  

**Result**: Robust validation prevents invalid commands and provides clear error messages.

