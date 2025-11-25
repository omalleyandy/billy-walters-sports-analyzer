# Billy Walters Automation Hooks

Complete documentation for all 14 automation hooks in `.claude/hooks/`.

## Overview

The project includes automation hooks for peak performance and robustness. These hooks validate environments, monitor data quality, detect betting edges automatically, and maintain code security.

**Location**: `.claude/hooks/`
**Quick Start**: See [Billy Walters Weekly Workflow](#billy-walters-weekly-workflow) below

---

## Session Management Hooks

### session_start.py
Runs at session start to provide context and opportunities.

```bash
python .claude/hooks/session_start.py
```

**Outputs:**
- Git status (ahead/behind, uncommitted changes)
- Data freshness (odds, weather, injuries)
- Opportunities (new edges, stale data to refresh)

**Use Case**: Start every development session

---

### session_end.py
Runs at session end to prepare for next session.

```bash
python .claude/hooks/session_end.py
```

**Outputs:**
- Uncommitted changes summary
- Pending tasks and next steps
- Recommended actions before closing

**Use Case**: End of session (before closing IDE)

---

## Data Collection Hooks

### pre_data_collection.py
Validates environment before running `/collect-all-data`.

```bash
python .claude/hooks/pre_data_collection.py
```

**Validates:**
- API keys present (AccuWeather, Overtime, Action Network, etc.)
- Output directories exist
- Current NFL week detected
- Last data collection timestamp

**Exit Codes:**
- `0` = All checks passed, safe to proceed
- `1` = Missing API keys or directories, cannot proceed

**Use Case**: Tuesday/Wednesday morning before data collection

---

### post_data_collection.py
Validates data quality after collection completes.

```bash
python .claude/hooks/post_data_collection.py [week]
```

**Parameters:**
- `[week]` (optional): NFL week number (auto-detected if omitted)

**Validates:**
- Required files present (5 minimum: power ratings, schedules, odds, etc.)
- Data freshness (<24 hours)
- Generates quality score (EXCELLENT/GOOD/FAIR/POOR)
- Provides actionable next steps

**Output:**
```
Data Quality Assessment - Week 10
File Status: ✓ All 5 required files present
Data Freshness: Excellent (collected 2 hours ago)
Quality Score: EXCELLENT
Recommendations: Ready for edge detection
```

**Use Case**: Immediately after `/collect-all-data` completes

---

## Edge Detection Hooks

### pre_edge_detection.py
Validates required data before running edge detection.

```bash
python .claude/hooks/pre_edge_detection.py
```

**Checks:**
- Power ratings exist
- Game schedule present
- Odds data available
- Prevents wasted computation on missing data

**Use Case**: Before `/edge-detector` command

---

### auto_edge_detector.py
Auto-triggers edge detection when conditions are met.

```bash
python .claude/hooks/auto_edge_detector.py
```

**Monitors:**
- Odds freshness (<5 minutes = trigger)
- Checks if already processed
- Auto-runs edge detection when conditions met
- Prevents redundant processing

**Triggering Conditions:**
- New odds data collected (< 5 min old)
- Edge detection hasn't run for this week yet
- All required data files present

**Use Case**: Automated workflow (optional, manual execution preferred)

---

### auto_odds_monitor.py
Continuous odds monitoring and edge detection triggering.

```bash
python .claude/hooks/auto_odds_monitor.py
```

**Features:**
- Database-backed odds tracking
- Detects new odds automatically
- Triggers edge detection pipeline
- Maintains processing cache

**Use Case**: Live game monitoring (optional, advanced)

---

## Code Quality Hooks

### pre_commit_check.py
Validates code before commits to prevent security issues.

```bash
python .claude/hooks/pre_commit_check.py
```

**Validates:**
- No exposed API keys (sk-ant-, sk-, ghp-, etc.)
- Python files have proper structure
- JSON files are valid
- No secrets in staged files

**Exit Codes:**
- `0` = Safe to commit
- `1` = Security issues found, fix before committing

**Use Case**: Before every `git commit`

---

## Documentation Hooks

### auto_index_updater.py
Auto-updates documentation index with new files.

```bash
# Auto-detect and update all docs
python .claude/hooks/auto_index_updater.py --auto

# Scan specific directory
python .claude/hooks/auto_index_updater.py --scan-dir docs/reports

# Add entry to _INDEX.md
python .claude/hooks/auto_index_updater.py --add-index "Title" "path/to/file.md"
```

**Updates:**
- `docs/_INDEX.md` with new documentation links
- `CLAUDE.md` Recent Updates section
- Maintains cross-references

**Use Case**: After creating new documentation files

---

## Data Validation Hooks

### validate_data.py
Core data validation logic for all data types.

```bash
python .claude/hooks/validate_data.py < data.json
```

**Validates:**
- Odds data format and completeness
- Weather data structure
- Game schedule integrity
- Power ratings format

**Usage in Code:**
```python
from .claude.hooks.validate_data import validate_odds

result = validate_odds(odds_data)
# Returns: {'valid': True/False, 'errors': [], 'message': '...'}
```

---

### mcp_validation.py
MCP server validation integration for autonomous agents.

```python
# Used by autonomous agent and MCP server
from .claude.hooks.mcp_validation import validate_data

result = await validate_data('odds', odds_data)
# Returns: {'valid': True/False, 'errors': [], 'message': '...'}
```

---

### validation_logger.py
Structured logging utilities for all validation hooks.

```python
# Provides structured logging for validation operations
from .claude.hooks.validation_logger import get_logger

logger = get_logger()
logger.info("Data validation started")
logger.error("Validation failed: missing file")
```

---

## Billy Walters Weekly Workflow

Complete workflow using automation hooks:

### Tuesday/Wednesday (Data Collection - 10 minutes)

```bash
# 1. Pre-flight validation
python .claude/hooks/pre_data_collection.py

# 2. Collect all data (automated 7-step process)
/collect-all-data

# 3. Post-flight validation (automatic after collection)
python .claude/hooks/post_data_collection.py

# 4. Validate before edge detection
python .claude/hooks/pre_edge_detection.py

# 5. Auto-trigger edge detection (if new odds)
python .claude/hooks/auto_edge_detector.py
```

### Thursday (Line Refresh - 5 minutes)

```bash
# Refresh odds before Thursday Night Football
/scrape-overtime
python .claude/hooks/pre_edge_detection.py
/edge-detector
```

### Sunday (Game Day)

```bash
# Pre-game check (recommended)
/scrape-overtime
python .claude/hooks/pre_edge_detection.py
/edge-detector

# OR live monitoring (optional)
python .claude/hooks/auto_odds_monitor.py
```

### Monday (Performance Review)

```bash
# Track performance
/clv-tracker

# Session end summary
python .claude/hooks/session_end.py
```

---

## Hook Integration Best Practices

### Git Workflow

```bash
# Before committing (ALWAYS)
python .claude/hooks/pre_commit_check.py
git add . && git commit -m "feat: add feature"

# After session
python .claude/hooks/session_end.py
```

### Data Collection Workflow

```bash
# Tuesday/Wednesday workflow
python .claude/hooks/pre_data_collection.py  # Pre-flight check
/collect-all-data                            # Collect data
python .claude/hooks/post_data_collection.py # Post-flight validation
python .claude/hooks/auto_edge_detector.py   # Auto-trigger edges
```

### Continuous Monitoring (Optional)

```bash
# Set up continuous odds monitoring
# Can be scheduled via cron or run manually
python .claude/hooks/auto_odds_monitor.py
```

---

## Error Handling & Recovery

### If pre_data_collection fails

```bash
# Check environment variables
echo $ACCUWEATHER_API_KEY  # Should not be empty
echo $OV_CUSTOMER_ID        # Should not be empty

# Verify output directories exist
ls -la data/current/
ls -la output/

# Fix and retry
python .claude/hooks/pre_data_collection.py
```

### If post_data_collection shows POOR quality

```bash
# Check what files are missing
ls -la data/current/
ls -la output/edge_detection/

# Re-run data collection
/collect-all-data

# Validate again
python .claude/hooks/post_data_collection.py
```

### If pre_commit_check finds secrets

```bash
# Identify the exposed secret
python .claude/hooks/pre_commit_check.py  # Shows which file

# Remove from staging
git reset HEAD filename

# Edit file to remove secret, update .env
vi filename

# Re-stage and commit
git add filename
git commit -m "fix: remove exposed secret"
```

---

## Hook Exit Codes Reference

| Hook | Exit 0 | Exit 1 |
|------|--------|--------|
| pre_data_collection | Ready to proceed | Missing API keys/dirs |
| post_data_collection | Data validated | Poor quality/missing files |
| pre_edge_detection | Ready to detect | Missing required data |
| auto_edge_detector | Triggered or skipped | Already processed |
| pre_commit_check | Safe to commit | Secrets found |

---

## Customizing Hooks

All hooks are Python scripts in `.claude/hooks/`. You can:
1. Read the source to understand logic
2. Modify validation thresholds
3. Add new validation checks
4. Extend for additional data sources

**Example**: Modify post_data_collection quality thresholds in `post_data_collection.py`

---

## Related Documentation

- **Main Workflow**: [CLAUDE.md](../../CLAUDE.md)
- **Complete Docs**: [docs/_INDEX.md](../../docs/_INDEX.md)
- **Commands Reference**: [.claude/commands/README.md](../commands/README.md)
- **Billy Walters Methodology**: [docs/guides/BILLY_WALTERS_METHODOLOGY.md](../../docs/guides/BILLY_WALTERS_METHODOLOGY.md)
