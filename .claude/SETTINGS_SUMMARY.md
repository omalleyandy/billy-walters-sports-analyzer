# Settings Configuration Summary

## ✅ PHASE 1 COMPLETE (2025-11-12)

All Phase 1 essential enhancements have been implemented and tested!

## What Changed

Your `.claude/settings.local.json` has been enhanced with automated validation, session hooks, and workflow improvements.

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

### 7. SessionStart Hook ⭐⭐⭐⭐⭐ NEW!

**Runs automatically at the beginning of every Claude Code session**

Shows:
- Git status (ahead/behind, uncommitted files)
- Current NFL week
- Data freshness for all key files
- Edge detection opportunities
- Actionable recommendations

**Example output:**
```
=== BILLY WALTERS SESSION START ===
Git: [WARNING] 13 uncommitted files

Week: NFL 2025 Week 10

Data Status:
  [X] Power Ratings: MISSING
  [!] Odds: 43h old (STALE)
  [X] Injuries: MISSING
  [!] Schedule: 35h old (STALE)

Opportunities:
  -> 14 NFL games this week
  -> Run /collect-all-data to refresh critical data
  -> 7 STRONG edges detected
  -> Run /betting-card to review picks
```

---

### 8. SessionEnd Hook ⭐⭐⭐⭐ NEW!

**Runs automatically when you close Claude Code session**

Shows:
- Uncommitted files summary
- Suggested commit message
- Pending tasks (edges, CLV tracking)
- Next session priorities (day-specific)

**Example output:**
```
=== SESSION END ===
Git: [WARNING] 13 uncommitted files
  Suggested commit:
    git add . && git commit -m "feat(claude): update settings and hooks"

Pending Tasks:
  -> Review 7 STRONG edges (/betting-card)
  -> Track CLV for detected edges (/clv-tracker)

Next Session:
  1. Run /collect-all-data (optimal for Tuesday/Wednesday)
  2. Run /edge-detector after data collection
```

---

### 9. PreToolUse Hook ⭐⭐⭐⭐ NEW!

**Validates data BEFORE running edge detector**

Prevents wasted computation by checking:
- Power ratings exist
- Odds data exists and is fresh (<24h)
- Game schedule exists
- Warns about missing weather/injuries

**If validation fails:** Edge detector won't run, shows what data is missing

**Example output (blocking):**
```
=== PRE-EDGE DETECTION VALIDATION ===
Required Data:
  [X] Power Ratings: File not found
  [X] Odds Data: 43h old (STALE)

VALIDATION: FAILED
Please run: /collect-all-data
```

---

### 10. Extended Thinking Mode ⭐⭐⭐ NEW!

```json
"alwaysThinkingEnabled": true
```

**What it does:**
- Claude uses extended reasoning for all responses
- Better analysis of Billy Walters methodology
- Catches subtle patterns and edge cases
- More thorough injury/weather impact analysis

**Trade-off:** 10-20% slower responses (worth it for sports betting)

---

### 11. MCP Auto-Approve ⭐⭐⭐ NEW!

```json
"enableAllProjectMcpServers": true
```

**What it does:**
- Auto-approves your billy-walters-expert MCP server
- No prompts when MCP server starts
- Faster session initialization

---

## Phase 1 Implementation Complete

**Files Created:**
- `.claude/hooks/session_start.py` (236 lines)
- `.claude/hooks/session_end.py` (284 lines)
- `.claude/hooks/pre_edge_detection.py` (184 lines)

**Files Updated:**
- `.claude/settings.local.json` - Added 5 new features

**All Hooks Tested:** ✅ Working perfectly

---

## Next Steps

1. **Restart Claude Code:** New session hooks will activate
2. **Check SessionStart:** You'll see data status immediately
3. **Test Edge Detection:** Try `/edge-detector` to see pre-validation
4. **Close Session:** See SessionEnd summary when you exit

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
