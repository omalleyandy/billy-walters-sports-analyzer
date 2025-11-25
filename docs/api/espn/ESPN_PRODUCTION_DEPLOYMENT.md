# ESPN Data Collection Production Deployment

Complete guide for deploying and managing the ESPN data collection pipeline in production.

## Table of Contents

1. [Overview](#overview)
2. [Deployment Steps](#deployment-steps)
3. [Weekly Schedule](#weekly-schedule)
4. [Monitoring & Metrics](#monitoring--metrics)
5. [Raw Data Archival](#raw-data-archival)
6. [Troubleshooting](#troubleshooting)
7. [Performance Optimization](#performance-optimization)

---

## Overview

### Production Components

This deployment consists of five integrated components:

1. **Production Orchestrator** (`scripts/dev/espn_production_orchestrator.py`)
   - Manages data collection workflow
   - Handles retries and error recovery
   - Archives raw data before normalization
   - Tracks detailed metrics per component

2. **Metrics Monitor** (`scripts/dev/espn_metrics_monitor.py`)
   - Analyzes collection performance
   - Generates quality reports
   - Detects anomalies
   - Exports metrics for analysis

3. **GitHub Actions Workflow** (`.github/workflows/espn-data-collection.yml`)
   - Automated scheduling (Tuesday & Friday)
   - Manual trigger capability
   - Multi-league support (NFL & NCAAF)
   - Failure notifications

4. **Data Archival System**
   - Raw API responses preserved
   - Organized by league/component/week
   - Indexed for quick retrieval
   - Retention policies (30-90 days)

5. **Quality Monitoring**
   - Real-time success tracking
   - Performance trending
   - Anomaly detection
   - Alert generation

### File Structure

```
data/
├── archive/
│   └── raw/
│       ├── nfl/
│       │   ├── team_stats/week_10/
│       │   ├── injuries/current/
│       │   └── schedules/current/
│       └── ncaaf/
│           ├── team_stats/week_12/
│           ├── injuries/current/
│           └── schedules/current/
├── metrics/
│   ├── logs/
│   │   ├── espn_collection_20251123_090000.log
│   │   └── ...
│   ├── session_20251123_090000.json
│   └── ...
├── current/  (normalized data)
└── reports/
```

---

## Deployment Steps

### Step 1: Enable GitHub Actions Workflow

The workflow is already created at `.github/workflows/espn-data-collection.yml`

**Verify it's enabled:**

1. Go to GitHub repository → Actions tab
2. Find "ESPN Weekly Data Collection" workflow
3. Confirm it's enabled (green checkmark)
4. Check schedule in workflow file

**Current Schedule:**
- **Tuesday 9 AM UTC** (1 AM PST / 4 AM EST) - Primary collection
- **Friday 9 AM UTC** - Secondary refresh before weekend

### Step 2: Run Manual Collection (First Time)

Test the production system locally first:

```bash
# Collect NCAAF data
uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf

# Collect NFL data
uv run python scripts/dev/espn_production_orchestrator.py --league nfl --week 11

# Check results
uv run python scripts/dev/espn_metrics_monitor.py --report
```

**Expected Output:**
```
======================================================================
ESPN DATA COLLECTION - NCAAF
Session ID: 20251123_090000
======================================================================

[team_stats] Starting collection for ncaaf
[team_stats] Found 136 teams
[team_stats] Collected 136/136 teams (100.0%)

[injuries] Starting collection for ncaaf
[injuries] Collected 24 injury records

[schedules] Starting collection for ncaaf
[schedules] Collected 56 games

======================================================================
COLLECTION SUMMARY
======================================================================
Total duration: 145.3s
Success rate: 100.0%
  team_stats: SUCCESS - 136 records, 120.5s
  injuries: SUCCESS - 24 records, 18.2s
  schedules: SUCCESS - 56 records, 6.6s
Status: ALL COMPONENTS SUCCESSFUL
```

### Step 3: Verify Data Archival

Check that raw data is properly archived:

```bash
# View archive structure
dir data/archive/raw/ncaaf

# Expected directories:
# - team_stats/week_12/
# - injuries/current/
# - schedules/current/

# Check file sizes
dir data/archive/raw/ncaaf/team_stats/week_12/*.json
```

### Step 4: Configure Notifications

**GitHub Issues for Failures:**

The workflow automatically creates an issue when collection fails. To enable:

1. Go to GitHub repository Settings → General
2. Ensure "Issues" feature is enabled
3. Issues will be created with label `data-collection`

**To add Slack/Email notifications (optional):**

Edit `.github/workflows/espn-data-collection.yml`:

```yaml
- name: Notify Slack on Failure
  if: failure()
  uses: slackapi/slack-notify-action@v1
  with:
    status: ${{ job.status }}
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

### Step 5: Monitor First Week

After enabling, monitor the first collection:

1. Watch the workflow run in GitHub Actions
2. Check generated metrics report
3. Review raw data archive
4. Verify data quality

**Check workflow results:**
```bash
# Workflow should complete in ~3-5 minutes
# Check artifacts in GitHub Actions UI
# Download metrics reports and quality reports
```

---

## Weekly Schedule

### Optimal Collection Schedule

```
MONDAY
└─ Games complete, new week lines posted

TUESDAY 9 AM UTC ← PRIMARY COLLECTION
├─ Team statistics
├─ Injury reports
├─ Game schedules
└─ Raw data archived

WEDNESDAY
└─ Monday Night Football (data collection skipped)

FRIDAY 9 AM UTC ← SECONDARY REFRESH
├─ Updated team stats
├─ Updated injury reports
└─ Verified schedule data

SATURDAY
└─ TNF/MACtion games (live monitoring only)

SUNDAY
├─ NFL games (live odds monitoring)
└─ NCAAF games (live odds monitoring)
```

### Manual Collection (When Needed)

**Trigger via GitHub UI:**

1. Go to Actions → ESPN Weekly Data Collection
2. Click "Run workflow" dropdown
3. Select:
   - League: `ncaaf` or `nfl`
   - Week: (optional)
4. Click "Run workflow"

**Or via command line:**

```bash
# Collect specific week
uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf --week 12

# Monitor specific league
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --report
```

---

## Monitoring & Metrics

### Real-Time Metrics

**Access metrics anytime:**

```bash
# Full quality report
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --report

# Detect anomalies
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --anomalies

# Export to CSV
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --export-csv metrics.csv
```

### Metrics Tracked

**Per Component:**
- Success/failure status
- Records collected
- Processing duration
- Quality score
- Error messages
- Raw file location

**Per Session:**
- Overall success rate
- Total processing time
- Records collected per component
- Data quality assessment
- Trend analysis (improving/declining)

### Understanding Quality Reports

```
QUALITY REPORT - NCAAF
=====================

SUMMARY
- Total sessions: 12
- Latest session: 20251123_090000

SUCCESS METRICS
- Current success rate: 100.0%
- Average success rate: 98.3%
- Trend: improving

PERFORMANCE METRICS
- Current duration: 145.3s
- Average duration: 142.1s
- Fastest run: 128.5s
- Slowest run: 156.2s

DATA COMPLETENESS
- Total records: 4,896
- Average per session: 408
- Latest session: 436

QUALITY SCORES
- Average quality score: 97.2/100
- Grade: EXCELLENT
```

**Quality Grades:**
- **EXCELLENT**: 95-100 (no action needed)
- **GOOD**: 85-94 (monitor next run)
- **FAIR**: 75-84 (investigate issues)
- **POOR**: <75 (immediate action required)

### Anomaly Detection

The monitor automatically detects:

1. **Declining Success Rate**
   - Alert: Recent avg <80% of overall avg
   - Action: Check API status, review errors

2. **Slow Processing**
   - Alert: Current duration >150% of average
   - Action: Check network, API rate limits

3. **Missing Data**
   - Alert: Component collected 0 records
   - Action: Check component logs, API endpoint

4. **Component Failures**
   - Alert: Specific component status = FAILURE
   - Action: Review component-specific logs

---

## Raw Data Archival

### Why Archive Raw Data?

1. **Audit Trail**: Complete API responses preserved
2. **Debugging**: Reproduce issues with exact data
3. **Normalization**: Safely re-process without API calls
4. **Compliance**: Complete data history retained
5. **Validation**: Compare processed vs raw data

### Archive Structure

```
data/archive/raw/
├── ncaaf/
│   ├── team_stats/
│   │   ├── week_12/
│   │   │   ├── team_stats_ncaaf_20251123_090000.json
│   │   │   └── team_stats_ncaaf_20251123_140000.json
│   │   └── current/
│   ├── injuries/
│   │   ├── week_12/
│   │   └── current/
│   │       └── injuries_ncaaf_20251123_090000.json
│   └── schedules/
│       ├── week_12/
│       └── current/
│           └── schedules_ncaaf_20251123_090000.json
└── nfl/
    └── (same structure)
```

### Accessing Archived Data

**Find specific data:**

```bash
# Find latest team stats
ls -lt data/archive/raw/ncaaf/team_stats/week_12/*.json | head -1

# Find all injuries for NCAAF week 12
find data/archive/raw/ncaaf/injuries -name "*ncaaf*" -type f

# List all archived components
ls data/archive/raw/ncaaf/*/current/
```

**Load archived data:**

```python
import json

# Load latest team stats
with open("data/archive/raw/ncaaf/team_stats/week_12/team_stats_ncaaf_20251123_090000.json") as f:
    data = json.load(f)

# Access raw API response
teams = data.get("teams", [])
```

### Archive Retention Policy

- **Current week data**: 90 days retention
- **Historical data**: 30 days retention
- **Failed collections**: 60 days retention

**To clean up old archives:**

```bash
# Remove archives older than 30 days
find data/archive/raw -name "*.json" -mtime +30 -delete

# Or keep last N files per component
find data/archive/raw/ncaaf/team_stats/week_12 -name "*.json" | sort -r | tail -n +6 | xargs rm
```

---

## Troubleshooting

### Collection Fails with "API Error"

**Symptoms:**
- Status: FAILURE
- Component: team_stats
- Error: "HTTP 429 Rate Limited"

**Solution:**

1. Check API availability:
   ```bash
   curl https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams
   ```

2. Verify rate limiting:
   ```bash
   # Check if ESPN API rate limit exceeded
   # Default: 10 req/second (handled by 1-second delay)
   ```

3. Retry later:
   ```bash
   # Manual retry after 30 minutes
   uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf
   ```

### Metrics Directory Full

**Symptoms:**
- Large disk usage in `data/metrics/`
- Log files growing rapidly

**Solution:**

```bash
# Archive old metrics
mkdir -p data/metrics/archive
mv data/metrics/session_*.json data/metrics/archive/

# Clean old logs (keep last 50)
ls -t data/metrics/logs/*.log | tail -n +51 | xargs rm

# Compress archived metrics
tar -czf metrics_archive_$(date +%Y%m).tar.gz data/metrics/archive/
```

### Anomaly Detected: Success Rate Declining

**Investigation steps:**

```bash
# 1. Get latest logs
tail -50 data/metrics/logs/espn_collection_*.log

# 2. Check which component failed
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --report

# 3. Review errors in latest session
cat data/metrics/session_$(ls -t data/metrics/session_*.json | head -1 | xargs basename)

# 4. Check if ESPN API is down
# Visit: https://status.espn.com/
```

### Raw Archive Not Creating

**Verify:**

```bash
# Check directory exists and is writable
ls -la data/archive/raw/

# If missing, create it
mkdir -p data/archive/raw/ncaaf/{team_stats,injuries,schedules}
mkdir -p data/archive/raw/nfl/{team_stats,injuries,schedules}

# Verify permissions
chmod 755 data/archive/raw
```

---

## Performance Optimization

### Expected Performance

**Processing Times (per league):**
- NCAAF: 140-160 seconds (136 teams + injuries + schedule)
- NFL: 40-60 seconds (32 teams + injuries + schedule)

**Data Volume:**
- Team stats: 6-8 MB (full season stats for all teams)
- Injuries: 100-500 KB (varies by season)
- Schedules: 200-400 KB

**Archive Growth:**
- Per session: ~7-10 MB per league
- Per week: ~70-100 MB for both leagues
- Per year: ~3-5 GB (with 30-90 day retention)

### Optimization Tips

1. **Parallel Collection** (if NFL and NCAAF both needed):
   ```yaml
   # In workflow, run NFL and NCAAF in parallel
   needs: []  # Remove dependency
   ```

2. **Rate Limiting**:
   - Current: 1 request per second (respects ESPN API)
   - Can reduce to 0.5s between teams if ESPN allows

3. **Data Compression**:
   ```bash
   # Compress archives automatically
   gzip data/archive/raw/ncaaf/team_stats/week_12/*.json
   ```

4. **Incremental Collection**:
   - Only update changed teams (future enhancement)
   - Cache team IDs and only fetch changed metrics

### Monitoring Performance Trends

```bash
# Export CSV and analyze
uv run python scripts/dev/espn_metrics_monitor.py --league ncaaf --export-csv metrics.csv

# View trend data
cat metrics.csv

# Session,Duration (s),Records,Success Rate
# 20251123_090000,145.3,436,100.0%
# 20251120_090000,142.1,436,100.0%
# 20251117_090000,151.2,436,95.0%
```

---

## Next Steps

1. **Enable Workflow** (if not already):
   - Verify `.github/workflows/espn-data-collection.yml` is present
   - Check GitHub Actions settings allow workflows

2. **Test Collection**:
   - Run manual collection locally
   - Review metrics and raw data archive
   - Verify integration with edge detector

3. **Set Up Alerts**:
   - Configure Slack/email notifications
   - Set up dashboard for metrics

4. **Schedule Regular Reviews**:
   - Weekly: Check quality report
   - Monthly: Review trends and optimize
   - Quarterly: Archive and compress old data

5. **Integration with Edge Detector**:
   - Integrate ESPN team stats into power ratings
   - Use injured player adjustments in edge detection
   - Track CLV performance using archived data

---

## Support

For issues or questions:

1. Check logs: `data/metrics/logs/`
2. Review quality report: `uv run python scripts/dev/espn_metrics_monitor.py --report`
3. Check GitHub Actions: Actions tab → ESPN Weekly Data Collection
4. Review LESSONS_LEARNED.md for known issues
