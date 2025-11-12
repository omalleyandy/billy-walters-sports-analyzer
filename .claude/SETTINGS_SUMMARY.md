# Settings Configuration Summary

## What Changed

Your `.claude/settings.local.json` has been enhanced with automated validation and workflow improvements.

## Key Improvements

### 1. Automated Pre-Flight Checks ✅

**Before These Commands:**
- `/collect-all-data`
- `/scrape-overtime`
- `/power-ratings`
- `/update-data`

**Auto-Validates:**
- ✅ Environment variables (API keys)
- ✅ Output directories exist
- ✅ Current NFL week detected
- ✅ Last collection timestamp
- ⚠️ Warns if data stale (>24 hours)

**If Validation Fails:** Command won't run. Fix issues first.

---

### 2. Post-Collection Validation ✅

**After `/collect-all-data` Completes:**

**Auto-Checks:**
- ✅ Required files exist
- ✅ File sizes reasonable (detect empty files)
- ✅ Data quality score (0-100)
- ✅ Suggests next steps

**Quality Levels:**
- 90-100: EXCELLENT
- 70-89: GOOD
- 50-69: FAIR
- <50: POOR (blocks edge detection)

---

### 3. Enhanced Bash Permissions ✅ EXPANDED

**Pre-Approved (No Prompts) - 64 Commands:**

**Git Operations (15):**
- `push`, `pull`, `add`, `commit`, `status`, `diff`, `log`
- `checkout`, `branch`, `fetch`, `merge`, `rebase`, `stash`
- `show`, `remote`, `tag`

**Package Management (9):**
- `uv run python/pytest/ruff/pyright`
- `uv add/sync/remove/lock/pip`

**GitHub CLI (10):**
- `gh pr`, `gh run`, `gh issue`, `gh workflow`, `gh release`
- `gh repo`, `gh api`, `gh auth`, `gh label`, `gh project`

**File Operations (18):**
- Basic: `ls`, `cat`, `tail`, `head`, `grep`, `find`, `mkdir`, `cd`
- Advanced: `cp`, `mv`, `touch`, `echo`, `pwd`, `which`
- Text: `wc`, `sort`, `uniq`, `diff`

**Network (2):**
- `curl`, `wget`

**Node/NPM (3):**
- `npm`, `npx`, `node`

**Always Denied (Safety):**
- `rm -rf` (recursive delete)
- `git push --force`
- `git reset --hard`
- `git clean -fd`

---

### 4. Smart Status Line ✅

**Shows:**
```
Billy Walters | Week 11 | Odds: 2h ago [OK] | Edges: 3 STRONG + 5 MOD
```

**Updates Automatically:**
- Current NFL week (auto-detected)
- Odds freshness (`[FRESH]`, `[OK]`, `[STALE]`, `[OLD]`)
- Edge count (STRONG ≥4 pts, MOD ≥2 pts)

---

### 5. Environment Setup ✅

**Added:**
```json
"env": {
  "PYTHONPATH": "..\\src",
  "PROJECT_ROOT": "..\\"
}
```

**Benefits:**
- Python can import from `src/` without sys.path hacks
- Scripts know project root location

---

### 6. Model Selection ⚠️ Manual Only

**Current Setting:** `"model": "sonnet"`

**Model Limitation:**
Claude Code settings only support a **single global model** - you cannot set different models for different commands (e.g., Haiku for GitHub, Sonnet for analysis).

**Workaround for GitHub Operations:**
Manually select Haiku in Claude Code UI when doing quick GitHub tasks:
1. Type your GitHub command (e.g., "check PR status")
2. Click model selector in UI
3. Choose "Haiku" temporarily
4. After GitHub task completes, switch back to "Sonnet"

**Model Recommendations:**
- **Sonnet (Default):** Optimal for Billy Walters analysis workflow
- **Haiku (Manual):** Use for quick GitHub operations, file listing, simple tasks
- **Opus (Manual):** Use for complex debugging, architecture decisions

**Why Sonnet as Default:**
- Superior reasoning for edge detection
- Better at Billy Walters methodology
- Handles complex sports analytics
- GitHub tasks are infrequent enough to switch manually

---

## Usage Examples

### Example 1: Tuesday Data Collection

```bash
/collect-all-data
```

**What Happens:**
1. ⏱️ Pre-hook validates (2 sec)
2. 📊 Collects all data (2-5 min)
3. ✅ Post-hook validates (5 sec)
4. 📋 Shows quality report + next steps

### Example 2: Quick Odds Refresh

```bash
/scrape-overtime
```

**What Happens:**
1. ⏱️ Pre-hook validates credentials (2 sec)
2. 🎯 Scrapes Overtime.ag (5 sec)
3. 📈 Status line updates

### Example 3: Manual Validation

```bash
# Check environment before starting
uv run python .claude/hooks/pre_data_collection.py

# Validate data quality after manual changes
uv run python .claude/hooks/post_data_collection.py 11
```

---

## When Hooks Run

| Command | Pre-Hook | Post-Hook |
|---------|----------|-----------|
| `/collect-all-data` | ✅ Pre-flight | ✅ Quality check |
| `/scrape-overtime` | ✅ Pre-flight | ❌ |
| `/power-ratings` | ✅ Pre-flight | ❌ |
| `/update-data` | ✅ Pre-flight | ❌ |
| `/edge-detector` | ❌ | ❌ |
| Manual scripts | ❌ | ❌ |

---

## Troubleshooting Quick Fixes

### "Missing required: OV_CUSTOMER_ID"

**Fix:** Check `.env` file:
```bash
OV_CUSTOMER_ID=your_id
OV_PASSWORD=your_password
```

### "Could not determine current week"

**Fix:**
- Check if offseason (June-August)
- Verify: `uv run python -m walters_analyzer.season_calendar`

### "Data Quality Score: 40/100 (POOR)"

**Fix:**
1. Review missing files list
2. Check file sizes (0 KB = problem)
3. Re-run failing data collection
4. Run `/validate-data` for details

### Status Line Not Updating

**Fix:**
- Press `Ctrl+C` then retry
- Test: `uv run python .claude/status_line.py`

---

## Disable Hooks (If Needed)

### Temporary Disable All Hooks

Add to `.claude/settings.local.json`:
```json
"disableAllHooks": true
```

### Run Without Hooks

```bash
# Direct script execution (bypasses hooks)
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

---

## Performance Impact

| Component | Time | When |
|-----------|------|------|
| Pre-hook | 1-3 sec | Before data commands |
| Post-hook | 3-5 sec | After `/collect-all-data` |
| Status line | <100ms | Terminal refresh |

**Total:** <10 seconds per workflow (saves minutes of manual checks)

---

## Next Steps

1. **Try It Out:** Run `/collect-all-data` and watch the validation
2. **Check Status:** Look at your status line (bottom of terminal)
3. **Read Details:** See `.claude/SETTINGS_GUIDE.md` for comprehensive guide
4. **Customize:** Add your own hooks or permissions as needed

---

## Quick Reference

**Settings File:** `.claude/settings.local.json`
**Detailed Guide:** `.claude/SETTINGS_GUIDE.md`
**Hook Scripts:** `.claude/hooks/`
**Status Line:** `.claude/status_line.py`

**Test Everything:**
```bash
# Validate environment
uv run python .claude/hooks/pre_data_collection.py

# Check status line
uv run python .claude/status_line.py

# Run full workflow (with hooks)
/collect-all-data
```

---

**Created:** 2025-11-12
**Version:** 1.0
