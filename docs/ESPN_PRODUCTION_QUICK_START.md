# ESPN Data Collection - Production Quick Start

Get the ESPN data collection pipeline up and running in minutes.

## 5-Minute Setup

### 1. Verify Components Are Installed

```bash
# Check production orchestrator exists
ls -la scripts/dev/espn_production_orchestrator.py

# Check metrics monitor exists
ls -la scripts/dev/espn_metrics_monitor.py

# Check GitHub Actions workflow
ls -la .github/workflows/espn-data-collection.yml
```

All three should exist and show file size > 0.

### 2. Run Your First Collection

```bash
# Test NCAAF collection
uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf

# Expected: ~140-160 seconds, 100% success
```

### 3. Check the Results

```bash
# View quality report
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --report

# Check archived raw data
ls -la data/archive/raw/ncaaf/
```

### 4. Enable GitHub Actions

1. Go to GitHub repository
2. Click "Actions" tab
3. Find "ESPN Weekly Data Collection"
4. Verify it shows a green checkmark (enabled)

That's it! Collections will run automatically every Tuesday & Friday at 9 AM UTC.

---

## Key Commands (Copy & Paste)

### Weekly NCAAF Collection
```bash
uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf
```

### Weekly NFL Collection
```bash
uv run python scripts/dev/espn_production_orchestrator.py --league nfl
```

### View Quality Report
```bash
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --report
```

### Detect Anomalies
```bash
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --anomalies
```

### Export Metrics to CSV
```bash
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --export-csv metrics.csv
```

### View Latest Logs
```bash
tail -50 data/metrics/logs/espn_collection_*.log
```

### Find Raw Data Archive
```bash
# NCAAF team stats
ls -lt data/archive/raw/ncaaf/team_stats/*/team_stats*.json | head -5

# NFL injuries
ls -lt data/archive/raw/nfl/injuries/current/*.json | head -5
```

---

## Understanding Success

### ✓ Success Indicators

When you see this in output/logs, everything is working:

```
Status: ALL COMPONENTS SUCCESSFUL
Success rate: 100.0%

  team_stats: SUCCESS - 136 records, 120.5s
  injuries: SUCCESS - 24 records, 18.2s
  schedules: SUCCESS - 56 records, 6.6s
```

### ✓ Healthy Quality Report

```
Average quality score: 97.2/100
Grade: EXCELLENT
```

### ✓ Healthy Metrics

```
Current success rate: 100.0%
Average duration: 142.1s
Latest session: 436 records
```

---

## What Happens Behind the Scenes

```
PRODUCTION ORCHESTRATOR
├─ 1. Logs to data/metrics/logs/
├─ 2. Collects team statistics
│  └─ Saves raw data to data/archive/raw/ncaaf/team_stats/
├─ 3. Collects injury reports
│  └─ Saves raw data to data/archive/raw/ncaaf/injuries/
├─ 4. Collects game schedules
│  └─ Saves raw data to data/archive/raw/ncaaf/schedules/
└─ 5. Saves metrics to data/metrics/session_*.json

METRICS MONITOR
├─ Reads all session_*.json files
├─ Analyzes trends
├─ Detects anomalies
└─ Generates reports
```

---

## File Locations

| What | Where |
|------|-------|
| Production Orchestrator | `scripts/dev/espn_production_orchestrator.py` |
| Metrics Monitor | `scripts/dev/espn_metrics_monitor.py` |
| GitHub Workflow | `.github/workflows/espn-data-collection.yml` |
| Collection Logs | `data/metrics/logs/` |
| Session Metrics | `data/metrics/session_*.json` |
| Raw Team Stats | `data/archive/raw/ncaaf/team_stats/` |
| Raw Injuries | `data/archive/raw/ncaaf/injuries/` |
| Raw Schedules | `data/archive/raw/ncaaf/schedules/` |

---

## Troubleshooting (Common Issues)

### "ModuleNotFoundError: No module named 'data.espn_api_client'"

**Solution:**
```bash
# Make sure you're in the project root
cd /path/to/billy-walters-sports-analyzer

# Install dependencies
uv sync --all-extras --dev

# Try again
uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf
```

### "data/archive/raw/ doesn't exist"

**Solution:**
```bash
# Create directory structure
mkdir -p data/archive/raw/ncaaf/{team_stats,injuries,schedules}
mkdir -p data/archive/raw/nfl/{team_stats,injuries,schedules}
```

### "Collection fails with HTTP error"

**Solution:**
1. Check if ESPN API is down: https://status.espn.com/
2. Wait 5 minutes and try again
3. Check logs: `tail -50 data/metrics/logs/espn_collection_*.log`

### "No quality report data"

**Solution:**
```bash
# Run a collection first
uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf

# Then check report (need at least one session)
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --report
```

---

## Next Steps

1. ✓ **Run first collection** (done above)
2. ✓ **Verify results** (check quality report)
3. **Enable GitHub Actions** (workflow will run Tue/Fri)
4. **Monitor weekly** (check report each week)
5. **Integrate with edge detector** (use archived data in power ratings)

---

## Weekly Checklist

### Every Tuesday (After 9 AM UTC)

- [ ] Workflow runs automatically
- [ ] Check results in GitHub Actions
- [ ] Verify data archived to `data/archive/raw/`

### Weekly Review

- [ ] Run quality report: `uv run python scripts/dev/espn_metrics_monitor.py --report`
- [ ] Check for anomalies: `uv run python scripts/dev/espn_metrics_monitor.py --anomalies`
- [ ] Review latest logs: `tail -100 data/metrics/logs/*.log`

### Monthly Review (First of Month)

- [ ] Export metrics CSV: `uv run python scripts/dev/espn_metrics_monitor.py --export-csv metrics.csv`
- [ ] Review trends in CSV
- [ ] Archive old logs: `mv data/metrics/logs/*.log data/metrics/archive/`
- [ ] Check disk usage: `du -sh data/archive/`

---

## How It Works (3-Minute Overview)

### Data Collection Flow

```
GitHub Actions (every Tue/Fri 9 AM UTC)
    ↓
ESPN Production Orchestrator
    ├─ Collects team statistics (120s)
    ├─ Collects injury reports (18s)
    └─ Collects schedules (7s)
    ↓
Raw data archived (before normalization)
    ├─ data/archive/raw/ncaaf/team_stats/
    ├─ data/archive/raw/ncaaf/injuries/
    └─ data/archive/raw/ncaaf/schedules/
    ↓
Metrics saved
    └─ data/metrics/session_20251123_090000.json
    ↓
Metrics Monitor (continuous)
    ├─ Analyzes success rates
    ├─ Detects anomalies
    ├─ Generates reports
    └─ Exports CSV trends
```

### Why This Matters

1. **Raw Data**: Unprocessed API responses (perfect for audits)
2. **Metrics**: Track success/failure/performance over time
3. **Quality Reports**: Know if data is good (EXCELLENT) or bad (POOR)
4. **Anomaly Detection**: Alerts you to problems automatically
5. **History**: 90 days of data for analysis

---

## Integration Examples

### Use Archived Team Stats in Power Ratings

```python
import json
from pathlib import Path

# Load archived team stats
archive = Path("data/archive/raw/ncaaf/team_stats/week_12")
latest_file = sorted(archive.glob("*.json"))[-1]  # Get latest

with open(latest_file) as f:
    data = json.load(f)

# Extract metrics for specific team
for team in data["teams"]:
    if team["team_name"] == "Ohio State":
        ppg = team["points_per_game"]
        papg = team["points_allowed_per_game"]
        to_margin = team["turnover_margin"]

        # Use in power rating calculation
        adjustment = (ppg - 28.5) * 0.15 + (28.5 - papg) * 0.15 + to_margin * 0.3
        print(f"Power rating adjustment: {adjustment:.2f}")
```

### Monitor Collection Success Rate

```bash
# Show success trend
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --report | grep "success rate"

# Expected: 95-100% (anything <90% needs investigation)
```

### Export Data for Analysis

```bash
# Get CSV with metrics
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --export-csv metrics.csv

# Open in Excel/Sheets for analysis
# Track: success rate, duration, records collected over time
```

---

## Getting Help

1. **Check CLAUDE.md**: ESPN API integration section
2. **Check LESSONS_LEARNED.md**: Common issues and fixes
3. **Review logs**: `data/metrics/logs/`
4. **Run quality report**: `uv run python scripts/dev/espn_metrics_monitor.py --report`
5. **Check GitHub Issues**: Existing problems/solutions

---

## Performance Summary

| Metric | Value |
|--------|-------|
| NCAAF collection time | 140-160 seconds |
| NFL collection time | 40-60 seconds |
| Records per session | 400-500 (NCAAF) |
| Data size per run | 7-10 MB |
| Archive growth (30-90 days) | 3-5 GB |
| Quality grade | EXCELLENT (95+/100) |
| Uptime target | 99%+ (ESPN API dependent) |

---

## You're Ready!

The ESPN data collection pipeline is now in production. Collections will run automatically every Tuesday and Friday. Check the quality reports weekly to ensure everything is running smoothly.

For detailed information, see [ESPN_PRODUCTION_DEPLOYMENT.md](ESPN_PRODUCTION_DEPLOYMENT.md)
