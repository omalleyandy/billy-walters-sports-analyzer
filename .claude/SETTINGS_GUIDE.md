# Claude Code Settings Guide
## Billy Walters Sports Analyzer - Enhanced Configuration

This document explains the enhanced `.claude/settings.local.json` configuration and how it improves your workflow.

---

## What's New

Your local settings have been enhanced with:

1. **Expanded Bash Permissions** - Pre-approved common operations
2. **Automated Validation Hooks** - Auto-run checks before data collection
3. **Post-Collection Validation** - Verify data quality after collection
4. **Enhanced Status Line** - Real-time project status
5. **Environment Variables** - Project-specific Python path
6. **Safety Guards** - Prevent destructive operations

---

## Bash Permissions

### Pre-Approved Commands (No Prompts)

**Git Operations:**
- `git push`, `git pull`, `git add`, `git commit`
- `git status`, `git diff`, `git log`
- `git checkout`, `git branch`

**Package Management:**
- `uv run python`, `uv run pytest`, `uv run ruff`, `uv run pyright`
- `uv add`, `uv sync`, `uv remove`
- `python` (direct execution)

**GitHub CLI:**
- `gh pr`, `gh run`, `gh issue`

**File Operations:**
- `ls`, `cat`, `tail`, `head`, `grep`, `find`, `mkdir`, `cd`

### Denied Commands (Always Blocked)

For your safety, these are always blocked:
- `rm -rf` (recursive delete)
- `git push --force` (force push)
- `git reset --hard` (hard reset)
- `git clean -fd` (force clean)

---

## Automated Hooks

### Pre-Data Collection Hook

**Triggers Before:**
- `/collect-all-data`
- `/scrape-overtime`
- `/power-ratings`
- `/update-data`

**What It Does:**
```
PRE-DATA COLLECTION VALIDATION
===============================
1. Checking environment variables...
   ✓ OV_CUSTOMER_ID present
   ✓ OV_PASSWORD present
   ⚠ ACCUWEATHER_API_KEY recommended

2. Checking output directories...
   ✓ All directories ready

3. Detecting current NFL week...
   ✓ Week 11 (auto-detected)

4. Checking last data collection...
   ✓ Last collected 2h ago (FRESH)

VALIDATION SUMMARY
==================
✓ PRE-FLIGHT CHECKS PASSED
Ready to collect data for week 11
```

**Benefits:**
- Prevents collection with missing credentials
- Ensures output directories exist
- Detects current NFL week automatically
- Warns if data is stale (>24 hours old)

**If Validation Fails:**
The command won't execute. Fix the reported issues first.

### Post-Data Collection Hook

**Triggers After:**
- `/collect-all-data` completes

**What It Does:**
```
POST-DATA COLLECTION VALIDATION
================================
1. Checking required files...
   ✓ nfl_week_11_games.json (245 KB)
   ✓ nfl_power_ratings_2025.json (12 KB)
   ✓ overtime_nfl_walters_*.json (88 KB)
   ✗ nfl_weather_week_11.json (MISSING)
   ✓ nfl_injuries_week_11.json (32 KB)

2. Data Quality Score: 80/100 (GOOD)

NEXT STEPS
==========
✓ Data collection successful
⚠ Weather data missing (optional but recommended)
→ Run: /weather to collect weather forecasts
→ Run: /validate-data for detailed quality check
→ Run: /edge-detector to find betting edges
```

**Benefits:**
- Verifies all expected files exist
- Checks file sizes (detect empty files)
- Provides quality score (EXCELLENT/GOOD/FAIR/POOR)
- Suggests next steps based on results

---

## Status Line

### What You See

Bottom of your terminal shows:
```
Billy Walters | Week 11 | Odds: 2h ago [OK] | Edges: 3 STRONG + 5 MOD
```

### Status Components

**Week Number:**
- Auto-detects current NFL week
- Shows "Offseason" during off-season/playoffs

**Odds Freshness:**
- `[FRESH]` - <1 hour old (excellent)
- `[OK]` - 1-6 hours old (good)
- `[STALE]` - 6-24 hours old (refresh recommended)
- `[OLD]` - >24 hours (refresh required)

**Edge Count:**
- `STRONG` - 4+ point edges (max bet territory)
- `MOD` - 2-4 point edges (moderate bet)
- Only shown if edges detected

### How It Updates

The status line runs `.claude/status_line.py` which:
1. Reads `src/walters_analyzer/season_calendar.py` for current week
2. Checks latest odds file timestamp in `output/`
3. Counts edges from `output/edge_detection/nfl_edges_detected.jsonl`

**Performance:** Fast (<100ms), runs automatically when terminal refreshes

---

## Environment Variables

### Project-Specific Env

```json
"env": {
  "PYTHONPATH": "..\\src",
  "PROJECT_ROOT": "..\\"
}
```

**Benefits:**
- Python can import from `src/` directory
- Scripts know project root location
- Consistent across all commands

**Note:** These are Claude Code session variables, not system environment variables. Your `.env` file (API keys) remains separate.

---

## Model Selection

```json
"model": "sonnet"
```

**What This Does:**
- Sets Claude Sonnet 4.5 as default model
- Balances intelligence with speed
- Optimal for Billy Walters workflow

**When to Change:**
- `"sonnet"` - Default (recommended)
- `"opus"` - Maximum reasoning (complex analysis)
- `"haiku"` - Speed priority (simple tasks)

---

## Co-Authoring Attribution

```json
"includeCoAuthoredBy": true
```

**What This Does:**
Every commit includes:
```
feat(edge-detector): add weather adjustments

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Benefits:**
- Transparent AI collaboration
- Tracks which commits involved Claude
- GitHub shows co-author statistics

**To Disable:** Set to `false` (not recommended)

---

## Usage Examples

### Scenario 1: Tuesday Data Collection

```bash
# You type:
/collect-all-data

# What happens:
# 1. Pre-hook runs (validates environment) - 2 seconds
# 2. If validation passes, data collection starts
# 3. Post-hook runs (validates data quality) - 5 seconds
# 4. You see comprehensive report with next steps
```

### Scenario 2: Quick Odds Refresh

```bash
# You type:
/scrape-overtime

# What happens:
# 1. Pre-hook validates credentials
# 2. Scraper runs if validation passes
# 3. Status line updates with new odds timestamp
```

### Scenario 3: Manual Hook Execution

```bash
# Run validation manually (without triggering command)
uv run python .claude/hooks/pre_data_collection.py

# Check data quality after manual changes
uv run python .claude/hooks/post_data_collection.py 11
```

---

## Troubleshooting

### Hook Failed - Environment Variables Missing

**Symptom:**
```
[ERROR] Missing required: OV_CUSTOMER_ID (Overtime.ag authentication)
PRE-FLIGHT CHECKS FAILED
```

**Solution:**
Check your `.env` file has:
```bash
OV_CUSTOMER_ID=your_customer_id
OV_PASSWORD=your_password
```

### Hook Failed - Week Detection Error

**Symptom:**
```
[ERROR] Could not determine current week (offseason/playoffs?)
```

**Solution:**
- Check if it's actually offseason (June-August)
- Verify `src/walters_analyzer/season_calendar.py` exists
- Run manually: `uv run python -m walters_analyzer.season_calendar`

### Post-Hook Shows Poor Data Quality

**Symptom:**
```
Data Quality Score: 40/100 (POOR)
POST-FLIGHT CHECKS FAILED
```

**Solution:**
- Review missing files list
- Check file sizes (0 KB = empty file)
- Re-run specific data collection: `/scrape-overtime`, `/power-ratings`, etc.
- Run `/validate-data` for detailed diagnosis

### Status Line Not Updating

**Symptom:**
Status line stuck on old data

**Solution:**
- Status line caches for performance
- Force refresh: Press `Ctrl+C` then re-run command
- Check `.claude/status_line.py` runs without errors:
  ```bash
  uv run python .claude/status_line.py
  ```

---

## Customization

### Add More Pre-Collection Checks

Edit `.claude/hooks/pre_data_collection.py`:

```python
def check_internet_connection() -> tuple[bool, list[str]]:
    """Verify internet connection before scraping."""
    try:
        import httpx
        response = httpx.get("https://www.google.com", timeout=5)
        return (response.status_code == 200, [])
    except Exception as e:
        return (False, [f"No internet connection: {e}"])
```

Then add to `main()` function.

### Add Hook for Edge Detection

Add to `.claude/settings.local.json`:

```json
{
  "matcher": "/edge-detector",
  "hooks": [
    {
      "type": "command",
      "command": "uv run python .claude/hooks/validate_data.py",
      "timeout": 30
    }
  ]
}
```

### Disable Hooks Temporarily

Add to settings:
```json
"disableAllHooks": true
```

Or run command directly (bypasses hooks):
```bash
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
```

---

## Performance Impact

### Hook Execution Time

| Hook | Duration | When |
|------|----------|------|
| Pre-Data Collection | 1-3 seconds | Before data commands |
| Post-Data Collection | 3-5 seconds | After `/collect-all-data` |
| Status Line | <100ms | Terminal refresh |

**Total Overhead:** <10 seconds per workflow (saves minutes of manual validation)

### Optimization Tips

1. **Skip hooks during debugging:**
   - Run Python scripts directly: `uv run python script.py`
   - Temporarily disable: `"disableAllHooks": true`

2. **Reduce status line frequency:**
   - Status line only runs when terminal refreshes
   - No background polling

3. **Parallel hook execution:**
   - Pre-hooks run before command (sequential)
   - Post-hooks run after command (sequential)
   - No parallel execution (intentional for data consistency)

---

## Best Practices

### When to Use Hooks

**✅ Always Use (Recommended):**
- Weekly data collection Tuesday/Wednesday
- Before betting decisions (ensure fresh data)
- After manual data file changes

**⚠️ Skip If:**
- Debugging specific scripts
- Testing new code
- Hooks are failing repeatedly (fix hooks first)

### When to Disable Hooks

**Temporary Disable (Debug Mode):**
```json
"disableAllHooks": true
```

**Selective Disable:**
Remove specific hook from settings, or run scripts directly:
```bash
# Bypass hooks
uv run python scripts/scrapers/scrape_overtime_api.py --nfl

# With hooks (via command)
/scrape-overtime
```

---

## Related Documentation

- **CLAUDE.md** - Complete development guidelines
- **LESSONS_LEARNED.md** - Troubleshooting guide
- **.claude/commands/README.md** - All slash commands
- **.claude/hooks/README.md** - Hook development guide (create this)

---

## Support

### Common Questions

**Q: Can I add my own hooks?**
A: Yes! Follow the pattern in existing hooks, then add to settings.

**Q: Do hooks slow down commands?**
A: Minimal (<5 seconds). They save time by catching errors early.

**Q: What if hook fails but I want to proceed anyway?**
A: Run the script directly or fix the validation issue.

**Q: Can hooks modify data?**
A: Currently they only validate. Consider adding auto-fix logic to post-hooks.

---

**Last Updated:** 2025-11-12
**Version:** 1.0
**Applies To:** `.claude/settings.local.json`
