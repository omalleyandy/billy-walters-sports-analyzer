# E501 Line Length Violation Reduction Plan

**Created**: 2025-11-20
**Current Status**: 430 violations (164 in src/, 266 in scripts/scrapers/tests/examples/)
**Goal**: Reduce to 0 violations incrementally
**Standard**: 88 characters (Black/Ruff standard)

---

## Current Violation Breakdown

### By Directory
| Directory | Violations | Priority |
|-----------|-----------|----------|
| `src/walters_analyzer/` | 164 | **HIGH** (core source code) |
| `scripts/` | ~200 | **MEDIUM** (utility scripts) |
| `scrapers/` | ~40 | **MEDIUM** (data collection) |
| `tests/` | ~20 | **LOW** (test code) |
| `examples/` | ~6 | **LOW** (documentation) |
| **TOTAL** | **~430** | |

### By File (Top Offenders in src/)
| File | Violations | Difficulty |
|------|-----------|-----------|
| `ingest/chrome_devtools_ai_scraper.py` | 19 | Hard (complex scraping logic) |
| `cli.py` | 17 | Medium (CLI formatting) |
| `ingest/nfl_site_scraper.py` | 12 | Medium (scraping logic) |
| `cli/clv_cli.py` | 9 | Medium (CLI formatting) |
| `valuation/billy_walters_totals_detector.py` | 8 | Easy (mostly f-strings) |
| `valuation/analyze_injuries_by_position.py` | 8 | Easy |
| `valuation/analyze_games_with_injuries.py` | 8 | Easy |
| `slash_commands.py` | 8 | Medium |
| `models/core.py` | 8 | Medium (data models) |
| Files with 1-2 violations | 16 files | **Quick wins!** |

---

## Incremental Reduction Strategy

### Phase 1: Quick Wins (16 files, ~25 violations) ⚡
**Timeline**: 1-2 hours
**Impact**: 6% reduction

**Files with 1-2 violations** (easiest to fix):
```
✓ valuation/power_ratings.py (1)
✓ valuation/core.py (1)
✓ valuation/billy_walters_edge_detector.py (1)
✓ validate_odds.py (1)
✓ season_calendar.py (1)
✓ research/engine.py (1)
✓ pipelines/test_knowledge_graph_integration.py (1)
✓ monitoring/simple_monitor.py (1)
✓ monitoring/quick_monitor.py (1)
✓ ingest/chrome_devtools_scraper.py (1)
✓ feeds/highlightly_client.py (1)
✓ data_collection/schedule_history_calculator.py (1)
✓ config/settings.py (1)
✓ updates/power_ratings.py (2)
✓ query/show_week_odds.py (2)
✓ monitoring/continuous_scraper.py (2)
```

**How to fix**:
```bash
# For each file, run:
cd src
uv run ruff check --select E501 --isolated walters_analyzer/FILE.py

# Manual fixes (common patterns):
# 1. Break long f-strings:
#    Before: f"This is a very long string with {var1} and {var2} and {var3}"
#    After:  f"This is a very long string with {var1} " \
#            f"and {var2} and {var3}"

# 2. Split function arguments:
#    Before: some_function(arg1, arg2, arg3, arg4, arg5, arg6)
#    After:  some_function(
#                arg1, arg2, arg3,
#                arg4, arg5, arg6
#            )

# 3. Use variables for complex expressions:
#    Before: result = calculate(foo.bar.baz.qux.very_long_chain + another.long.chain)
#    After:  first_value = foo.bar.baz.qux.very_long_chain
#            second_value = another.long.chain
#            result = calculate(first_value + second_value)

# After fixing, verify:
uv run ruff check --select E501 --isolated walters_analyzer/FILE.py
uv run ruff format walters_analyzer/FILE.py
```

---

### Phase 2: Moderate Effort (12 files, ~60 violations) 🔧
**Timeline**: 3-4 hours
**Impact**: 14% reduction

**Files with 3-5 violations**:
```
✓ query/odds_viewer.py (3)
✓ models/sfactor_data_models.py (2)
✓ models/knowledge_graph.py (2)
✓ feeds/market_monitor.py (2)
✓ valuation/market_analysis.py (4)
✓ query/watch_alerts.py (4)
✓ ingest/scrape_with_ai.py (4)
✓ backtest/power_rating_backtest.py (4)
✓ agent_data_loader.py (4)
✓ wkcard.py (5)
```

**Strategy**: Focus on one file per session, commit after each fix.

---

### Phase 3: Focused Effort (8 files, ~60 violations) 🎯
**Timeline**: 4-5 hours
**Impact**: 14% reduction

**Files with 6-10 violations**:
```
⚠ valuation/sfactor_wfactor.py (7)
⚠ scrapers/overtime_direct.py (7)
⚠ valuation/billy_walters_totals_detector.py (8)
⚠ valuation/analyze_injuries_by_position.py (8)
⚠ valuation/analyze_games_with_injuries.py (8)
⚠ slash_commands.py (8)
⚠ models/core.py (8)
⚠ cli/clv_cli.py (9)
```

**Strategy**:
- Allocate 30-60 minutes per file
- Test thoroughly after changes (complex logic files)
- Commit each file separately

---

### Phase 4: Major Refactoring (3 files, ~50 violations) 🔨
**Timeline**: 6-8 hours
**Impact**: 12% reduction

**Files with 10+ violations** (hardest):
```
🔥 ingest/chrome_devtools_ai_scraper.py (19) - complex scraping
🔥 cli.py (17) - main CLI entry point
🔥 ingest/nfl_site_scraper.py (12) - complex scraping
```

**Strategy**:
- May require refactoring (extract helper functions)
- Consider breaking into smaller modules
- Thorough testing required
- Get code review before committing

---

### Phase 5: Scripts & Tests (~266 violations) 📝
**Timeline**: 8-10 hours
**Impact**: 54% reduction

**Lower priority** since these are:
- Utility scripts (one-off usage)
- Test files (less critical)
- Examples (documentation)

**Strategy**: Fix opportunistically when editing these files.

---

## Automation Opportunities

### Semi-Automated Fixing Script

```bash
#!/bin/bash
# fix_e501_batch.sh - Semi-automated E501 fixer

# Get list of files with 1-2 violations
FILES=$(cd src && uv run ruff check --select E501 --isolated --output-format=concise walters_analyzer/ 2>&1 | \
  awk -F':' '{print $1}' | sort | uniq -c | sort -rn | awk '$1 <= 2 {print $2}')

for file in $FILES; do
  echo "=== Processing: $file ==="

  # Show violations
  cd src && uv run ruff check --select E501 --isolated "walters_analyzer/$file"

  # Open in editor for manual fix
  code "src/walters_analyzer/$file"

  # Wait for user to fix
  read -p "Press Enter after fixing (or 's' to skip): " response

  if [ "$response" != "s" ]; then
    # Verify fix
    cd src && uv run ruff check --select E501 --isolated "walters_analyzer/$file"

    # Format
    uv run ruff format "src/walters_analyzer/$file"

    # Commit
    git add "src/walters_analyzer/$file"
    git commit -m "fix(code-quality): fix E501 violations in $file"

    echo "✓ Fixed and committed: $file"
  fi
done
```

### Fully Automated (for simple cases)

Some violations can be auto-fixed with regex:

```python
# Example: Break long print statements
import re

def auto_fix_simple_violations(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern 1: Long print statements
    content = re.sub(
        r'print\(f"(.{60,})"\)',
        lambda m: f'print(\n    f"{m.group(1)[60:]}"\n)',
        content
    )

    # Add more patterns...

    with open(file_path, 'w') as f:
        f.write(content)
```

**⚠️ Warning**: Always review auto-fixed code before committing!

---

## Tracking Progress

### Weekly Goal
- Week 1: Phase 1 complete (16 files, 25 violations) → 405 remaining
- Week 2: Phase 2 complete (12 files, 60 violations) → 345 remaining
- Week 3: Phase 3 complete (8 files, 60 violations) → 285 remaining
- Week 4: Phase 4 complete (3 files, 50 violations) → 235 remaining
- Ongoing: Phase 5 (opportunistic fixes)

### Metrics to Track
```bash
# Run weekly to track progress
uv run python -c "
import subprocess
import json

result = subprocess.run(
    ['uv', 'run', 'ruff', 'check', '--select', 'E501', '--isolated',
     '--statistics', 'src/walters_analyzer/'],
    capture_output=True,
    text=True,
    cwd='src'
)

# Parse output
lines = result.stderr.split('\n')
for line in lines:
    if 'E501' in line:
        print(f'Core source violations: {line.split()[0]}')
"

# Log to file
echo "$(date): $(violations count)" >> docs/e501_progress.log
```

---

## Best Practices During Fixing

### 1. Test After Every Fix
```bash
# Run tests for the module you changed
uv run pytest tests/test_MODULE.py -v

# Run type check
uv run pyright src/walters_analyzer/MODULE.py
```

### 2. Commit Frequently
```bash
# One file per commit (easier to review/revert)
git add src/walters_analyzer/FILE.py
git commit -m "fix(code-quality): fix E501 violations in FILE.py

- Split long f-strings across multiple lines
- Broke function arguments into multiple lines
- Used parentheses for implicit line continuation

Violations: 8 → 0"
```

### 3. Document Complex Changes
If fixing requires refactoring:
```bash
# Add comments explaining the change
git commit -m "refactor(cli): extract long CLI help text to separate function

Fixes E501 violations by moving long help strings from inline to
helper function. No functional changes.

Before: 17 violations
After: 0 violations"
```

---

## Common Line-Breaking Patterns

### F-Strings
```python
# Before (92 chars)
message = f"Game: {home_team} vs {away_team}, Spread: {spread}, Edge: {edge}%, Confidence: {conf}%"

# After (88 chars max per line)
message = (
    f"Game: {home_team} vs {away_team}, "
    f"Spread: {spread}, Edge: {edge}%, Confidence: {conf}%"
)
```

### Function Calls
```python
# Before
result = analyze_game(home_team, away_team, spread, total, weather, injuries, power_rating)

# After
result = analyze_game(
    home_team, away_team,
    spread, total,
    weather, injuries,
    power_rating
)
```

### Long Strings
```python
# Before
help_text = "This is a very long help message that explains what this option does in detail"

# After
help_text = (
    "This is a very long help message that explains "
    "what this option does in detail"
)
```

### URLs/Paths
```python
# Before
url = "https://api.example.com/v1/sports/football/games?season=2025&week=10&include_stats=true"

# After
url = (
    "https://api.example.com/v1/sports/football/games"
    "?season=2025&week=10&include_stats=true"
)
```

---

## Integration with CI/CD

### Current State (Informational Only)
```yaml
# .github/workflows/ci.yml
- name: Check line length (informational only)
  run: |
    echo "Checking for line length violations (88 char limit)..."
    uv run ruff check . --select E501 --statistics || echo "⚠️ Violations found"
  continue-on-error: true
```

### Future State (Once All Fixed)
```yaml
# Remove continue-on-error to enforce
- name: Enforce line length
  run: uv run ruff check . --select E501
```

Update `pyproject.toml`:
```toml
[tool.ruff.lint]
ignore = [
    "E402",  # Module level import not at top of file
    # "E501",  # REMOVED - now enforcing! 🎉
    "E722",  # Bare except
    # ...
]
```

---

## When to Skip/Postpone Fixing

**Skip** if:
- File is in `archive/` directory (excluded)
- File is generated code
- File will be deleted soon
- Violation is in a URL that must stay on one line

**Postpone** if:
- File has >15 violations (major refactor needed)
- File is complex and lacks tests
- You're unfamiliar with the code
- There's an active PR modifying the file

**Document** skipped files:
```python
# ruff: noqa: E501
# TODO: Fix line length violations when refactoring this module
```

---

## Success Criteria

- ✅ All files in `src/walters_analyzer/` comply (0 E501 violations)
- ✅ CI enforces E501 (no continue-on-error)
- ✅ E501 removed from ignore list in pyproject.toml
- ✅ Documentation updated
- ✅ All tests passing

**Target Date**: End of December 2025

---

## Quick Commands Reference

```bash
# Check current violations count
cd src && uv run ruff check --select E501 --isolated --statistics walters_analyzer/

# Check specific file
cd src && uv run ruff check --select E501 --isolated walters_analyzer/FILE.py

# Fix and verify
# 1. Edit file manually
# 2. uv run ruff format src/walters_analyzer/FILE.py
# 3. cd src && uv run ruff check --select E501 --isolated walters_analyzer/FILE.py

# Commit
git add src/walters_analyzer/FILE.py
git commit -m "fix(code-quality): fix E501 violations in FILE.py"
git push

# Track progress
echo "$(date +%Y-%m-%d): $(cd src && uv run ruff check --select E501 --isolated --statistics walters_analyzer/ 2>&1 | grep 'E501' | awk '{print $1}') violations" >> docs/e501_progress.log
```

---

**Next Steps**: Start with Phase 1 (Quick Wins) - pick any file with 1-2 violations and fix it in 5-10 minutes!
