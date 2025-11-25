# Documentation Index Automation Guide

**Purpose**: Automatically update documentation index (_INDEX.md) and memory file (CLAUDE.md) after major deliverables/summaries.

**Status**: ✅ IMPLEMENTED
**Setup Date**: 2025-11-23
**Hook Location**: `.claude/hooks/auto_index_updater.py`

---

## Overview

The documentation index automation system keeps your project documentation synchronized and discoverable. After creating reports, summaries, or major deliverables, this system automatically:

1. **Scans** for new documentation files
2. **Updates** _INDEX.md with proper navigation links
3. **Updates** CLAUDE.md Recent Updates section with summaries
4. **Maintains** cross-references between documentation

---

## How It Works

### Automatic Detection
The hook monitors for new files matching these patterns:
- `*QA*REPORT*.md` - Quality assurance reports
- `SESSION*.md` - Development session summaries
- `*_REPORT*.md` - Analysis reports
- `*_GUIDE*.md` - New user guides

### Manual Triggers
You can manually trigger updates for specific files:
```bash
# Add file to index
python .claude/hooks/auto_index_updater.py --add-index "Report Title" "docs/reports/file.md"

# Add to Recent Updates in CLAUDE.md
python .claude/hooks/auto_index_updater.py --add-update "Feature Name" "content.md"

# Auto-detect all new files
python .claude/hooks/auto_index_updater.py --auto
```

---

## Usage Patterns

### Pattern 1: After Creating a QA Report
```bash
# Create comprehensive QA testing
# ... create tests and report ...

# Update documentation automatically
python .claude/hooks/auto_index_updater.py --auto

# Or manually add specific report
python .claude/hooks/auto_index_updater.py --add-index "Component QA Report" "docs/reports/component_qa_report.md"
```

### Pattern 2: After Session Summary
```bash
# Create session summary document
# ... document session work ...

# Register in Recent Updates
python .claude/hooks/auto_index_updater.py --add-update "Session Summary" "docs/reports/SESSION_2025-11-23.md"
```

### Pattern 3: After Feature Guide
```bash
# Create new feature documentation guide
# ... write guide ...

# Scan for new guides
python .claude/hooks/auto_index_updater.py --scan-dir docs/guides
```

---

## What Gets Updated

### _INDEX.md Updates
**Location**: `## Testing & Quality` section

**Before**:
```markdown
### Quality Assurance
- [Example Output](guides/EXAMPLE_OUTPUT.md) - Expected output formats
- [Data Validation Guide](DATA_VALIDATION_GUIDE.md) - Quality standards
```

**After**:
```markdown
### Quality Assurance
- [ESPN Data QA Report](reports/ESPN_DATA_QA_REPORT_2025-11-23.md) - ✅ COMPLETE - 56/56 tests passed
- [ESPN Data QA Quick Reference](ESPN_DATA_QA_QUICK_REFERENCE.md) - Test execution guide
- [Example Output](guides/EXAMPLE_OUTPUT.md) - Expected output formats
- [Data Validation Guide](DATA_VALIDATION_GUIDE.md) - Quality standards
```

### CLAUDE.md Updates
**Location**: `## Recent Updates` section

**Before**:
```markdown
## Recent Updates (2025-11-12 to 2025-11-23)

### Action Network Integration ✅ NEW (2025-11-23)
```

**After**:
```markdown
## Recent Updates (2025-11-12 to 2025-11-23)

### ESPN Data QA Testing ✅ NEW (2025-11-23)

**What Changed:**
- Comprehensive QA test suite (56 tests, 100% pass rate)
- All 6 ESPN components validated
- Complete documentation package

...

### Action Network Integration ✅ NEW (2025-11-23)
```

---

## File Format Requirements

### For Index Updates
Files should follow standard Markdown:
```markdown
# Report Title

Description or summary of report content.

## Section 1
...

## Section 2
...
```

The hook reads:
- Filename for title (converted from snake_case)
- First `#` header as description
- Relative path for index link

### For Recent Updates
Create a separate content file:
```markdown
**What Changed:**
- Point 1
- Point 2

**Key Features:**
- Feature A
- Feature B

**Status:**
- ✅ Complete
- Ready for deployment
```

Then reference:
```bash
python .claude/hooks/auto_index_updater.py --add-update "Feature Name" "content.md"
```

---

## Making It Automatic (Future Enhancement)

### Option 1: Git Hook
Create `.git/hooks/post-commit`:
```bash
#!/bin/bash
python .claude/hooks/auto_index_updater.py --auto
git add docs/_INDEX.md CLAUDE.md
git commit --amend --no-edit 2>/dev/null || true
```

### Option 2: GitHub Action
Create `.github/workflows/auto-index.yml`:
```yaml
name: Auto-Index Documentation
on:
  push:
    paths:
      - 'docs/**'

jobs:
  update-index:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: python .claude/hooks/auto_index_updater.py --auto
      - run: |
          git config user.name "Claude Code"
          git config user.email "noreply@anthropic.com"
          git add docs/_INDEX.md CLAUDE.md
          git commit -m "docs: auto-update index and memory files" || true
      - run: git push
```

### Option 3: Pre-Commit Hook
Update `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: auto-index-docs
      name: Auto-index documentation
      entry: python .claude/hooks/auto_index_updater.py --auto
      language: system
      stages: [commit]
```

---

## Recommended Workflow

### After Creating Major Deliverables:

1. **Create Documentation**
   ```bash
   # Create report/guide/summary
   # Save in appropriate docs/ subdirectory
   ```

2. **Update Index Automatically** (Recommended)
   ```bash
   python .claude/hooks/auto_index_updater.py --auto
   ```

3. **Verify Changes**
   ```bash
   git diff docs/_INDEX.md
   git diff CLAUDE.md
   ```

4. **Commit** (if hook not auto-running)
   ```bash
   git add docs/_INDEX.md CLAUDE.md
   git commit -m "docs: update index and memory files for new deliverables"
   ```

### For Specific Files:

```bash
# Add specific report to index
python .claude/hooks/auto_index_updater.py --add-index "Title" "docs/reports/file.md"

# Add specific update to CLAUDE.md
python .claude/hooks/auto_index_updater.py --add-update "Title" "content.md"
```

---

## Examples in Action

### Real Example: ESPN QA Testing (2025-11-23)

**Step 1: Create deliverables**
```bash
# Created:
# - tests/test_espn_data_qa.py (test suite)
# - docs/reports/ESPN_DATA_QA_REPORT_2025-11-23.md (report)
# - docs/ESPN_DATA_QA_QUICK_REFERENCE.md (guide)
# - docs/ESPN_DATA_QA_TEST_INVENTORY.md (inventory)
# - docs/ESPN_DATA_QA_DELIVERABLES.md (summary)
```

**Step 2: Update documentation**
```bash
python .claude/hooks/auto_index_updater.py --auto
```

**Step 3: Verify**
```bash
# _INDEX.md now has:
# - ESPN Data QA Report under Testing & Quality > Quality Assurance
# - ESPN Data QA Reference, Inventory, Deliverables links

# CLAUDE.md now has:
# - New section: ESPN Data Collection Pipeline - QA Testing
# - Complete summary of work done
# - Links to all documentation
```

**Step 4: Commit**
```bash
git add docs/_INDEX.md CLAUDE.md
git commit -m "docs: update index and memory for ESPN QA testing deliverables"
```

---

## Troubleshooting

### Hook Not Finding Files
```bash
# Check scan directory
python .claude/hooks/auto_index_updater.py --scan-dir docs/reports

# Verify file exists and matches pattern
ls docs/reports/*QA*REPORT*.md
```

### Section Not Found in _INDEX.md
```bash
# Verify section exists
grep "## Testing & Quality" docs/_INDEX.md

# If missing, manually add section first
# Then use --add-index flag
```

### Recent Updates Not Appearing in CLAUDE.md
```bash
# Verify section exists
grep "## Recent Updates" CLAUDE.md

# Check content file format
cat content.md
```

### Changes Not Committing
```bash
# Check git status
git status

# Manually add files
git add docs/_INDEX.md CLAUDE.md

# Create commit
git commit -m "docs: auto-update documentation"
```

---

## Benefits

✅ **Automated**: No manual index updates needed
✅ **Consistent**: Standard format for all documentation
✅ **Discoverable**: All docs in one searchable index
✅ **Current**: Memory file always reflects recent work
✅ **Scalable**: Works as project grows
✅ **Linked**: Cross-references prevent duplicate info
✅ **Traceable**: Every change documented in Recent Updates

---

## Integration with Development Workflow

### Before This Hook
- Create docs manually → Remember to update _INDEX.md → Remember to update CLAUDE.md → Manual sync
- 🐌 Slow, error-prone, documentation drifts

### After This Hook
- Create docs → Run `auto_index_updater.py --auto` → Everything updated
- 🚀 Fast, reliable, always synchronized

### Recommended Additions to Your Workflow

**In your session end checklist**:
1. ✅ Document lessons learned
2. ✅ Create reports and summaries
3. ✅ **Run auto-index updater** (NEW)
4. ✅ Commit and push

---

## Future Enhancements

Possible improvements:
1. **Auto-detect on commit**: Trigger hook automatically via pre-commit or post-commit
2. **Schedule updates**: Nightly runs to sync all documentation
3. **Cross-linking**: Auto-generate "See Also" links between related docs
4. **Statistics**: Track documentation growth, completeness metrics
5. **Validation**: Verify all links in index point to existing files
6. **Archival**: Auto-move old reports to archives directory

---

## Documentation Standards

To make auto-update work best, follow these standards:

### File Naming
```
FEATURE_REPORT_2025-11-23.md          ✅ Detected as report
SESSION_2025-11-23_ANALYSIS.md        ✅ Detected as session
COMPONENT_QA_REPORT.md                ✅ Detected as QA report
quick_reference.md                    ❌ Won't auto-detect
```

### File Location
```
docs/reports/                         ✅ Standard location
docs/SESSION_*/                       ✅ Session archive
docs/guides/                          ✅ User guides
docs/api/                            ✅ API docs
docs/custom_location/                ❌ Won't auto-scan
```

### Content Format
```markdown
# Descriptive Title

Summary paragraph explaining what this document covers.

## Main Section 1
Content...

## Main Section 2
Content...
```

---

## Contact & Support

Questions about documentation automation?
- Check existing examples in `docs/_INDEX.md` (updated 2025-11-23)
- Review `CLAUDE.md` § Recent Updates for patterns
- Refer to this guide for all automation options

---

**Status**: ✅ READY FOR DAILY USE
**Last Updated**: 2025-11-23
**Implemented**: `.claude/hooks/auto_index_updater.py`
