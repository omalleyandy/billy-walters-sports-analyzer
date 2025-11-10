# Scraper Testing - Quick Start Guide

Fast-track guide to validate scraper functionality and data quality.

---

## Prerequisites

```bash
# 1. Install dependencies
uv sync

# 2. Install Playwright browser
uv run playwright install chromium

# 3. Create .env file
cp .env.example .env
# Edit .env with your credentials
```

---

## Step 1: Run Scrapers (Generate Test Data)

### Option A: Pre-Game Odds (Recommended First)

```bash
# NFL only (faster)
uv run walters-analyzer scrape-overtime --sport nfl

# Both NFL + College Football
uv run walters-analyzer scrape-overtime --sport both
```

**Expected Output:**
```
✓ Using residential proxy: rp.scrapegw.com:6060
✓ Proxy IP verified: 45.67.89.123 (Miami, FL, US)
✓ Login successful
Extracted 45 NFL games
Output: data/overtime_live/overtime-live-20251106-*.jsonl
```

### Option B: Live Betting Odds

```bash
uv run walters-analyzer scrape-overtime --live
```

### Option C: Injury Reports

```bash
# NFL injuries
uv run walters-analyzer scrape-injuries --sport nfl

# College Football injuries
uv run walters-analyzer scrape-injuries --sport cfb
```

---

## Step 2: Run Data Validation

```bash
# Analyze all data in default directory
uv run python test_scraper_backtest.py

# Or specify custom directory
uv run python test_scraper_backtest.py ./data/custom_dir
```

**What It Checks:**
- ✅ Schema validation (all required fields present)
- ✅ Data quality metrics (valid team names, etc.)
- ✅ Market coverage (spread, total, moneyline)
- ✅ Quote completeness (line + price present)
- ✅ Timestamp accuracy
- ✅ Sample record inspection

**Expected Output:**
```
================================================================================
SCRAPER DATA VALIDATION & BACKTESTING REPORT
================================================================================

📊 Files Found:
   - JSONL: 3
   - Parquet: 3
   - CSV: 3

📋 Required Fields (out of 150 records):
   ✓ source              :    150 (100.0%)
   ✓ sport               :    150 (100.0%)
   ✓ league              :    150 (100.0%)
   ✓ game_key            :    150 (100.0%)
   ✓ teams               :    150 (100.0%)
   ✓ markets             :    150 (100.0%)

📈 Market Presence:
   • Spread:    145 ( 96.7%)
   • Total:     148 ( 98.7%)
   • Moneyline: 150 (100.0%)
   • Complete:  143 ( 95.3%)

🎉 EXCELLENT: No issues detected!
```

---

## Step 3: Manual Data Inspection

### View Raw Data

```bash
# View JSONL (prettified)
cat data/overtime_live/*.jsonl | head -n 5 | jq '.'

# View CSV (tabular)
head -20 data/overtime_live/*.csv | column -ts,

# Check file sizes
ls -lh data/overtime_live/
```

### Check Debug Snapshots

```bash
# List all screenshots
ls -lh snapshots/

# View with image viewer (if GUI available)
open snapshots/pregame_main.png          # macOS
xdg-open snapshots/pregame_main.png      # Linux
explorer snapshots\pregame_main.png      # Windows
```

---

## Step 4: Test Proxy (Optional)

```bash
# Test proxy connection
curl -x "$PROXY_URL" "https://ipinfo.io/json"

# Should show residential IP, not your local IP
# Example output:
# {
#   "ip": "45.67.89.123",
#   "city": "Miami",
#   "region": "Florida",
#   "country": "US",
#   "org": "AS12345 Residential ISP"
# }
```

---

## Expected Results (Success Criteria)

### ✅ Pre-Game Odds Scraper:

- [ ] **Files Created:** JSONL, CSV, Parquet in `data/overtime_live/`
- [ ] **Record Count:** 30-100 games per run (depending on season)
- [ ] **Market Coverage:** > 90% complete (spread + total + ML)
- [ ] **Team Names:** Valid (no emojis, UI elements)
- [ ] **Rotation Numbers:** Present (e.g., "451-452")
- [ ] **Event Dates:** Present (e.g., "2025-11-10")
- [ ] **Prices:** Valid American odds (e.g., -110, +150)
- [ ] **No Errors:** No JSON parsing errors

### ✅ Live Odds Scraper:

- [ ] **`is_live: true`** in all records
- [ ] **Game State:** Quarter and clock present
- [ ] **Market Data:** Real-time lines and prices
- [ ] **Updates:** Different data on subsequent runs

### ✅ Injury Scraper:

- [ ] **Player Data:** Names, positions, injury status
- [ ] **Team Assignment:** Correct team attribution
- [ ] **Status Codes:** Out, Doubtful, Questionable, Probable
- [ ] **Notes:** Injury details when available

---

## Common Issues & Quick Fixes

### Issue: "No data scraped"

**Check:**
```bash
# 1. Verify credentials in .env
cat .env | grep OV_

# 2. Check snapshots for errors
ls -lh snapshots/

# 3. Check logs (if logging enabled)
tail -f logs/scraper.log
```

**Fix:**
- Ensure valid overtime.ag credentials
- Check if proxy is working (run proxy test)
- Review snapshots for Cloudflare blocks

### Issue: "Market coverage < 90%"

**Possible Causes:**
- Scraped during maintenance window
- UI selectors changed (site redesign)
- Filtered out invalid games correctly

**Actions:**
1. Run scraper again at different time
2. Check `snapshots/` for UI changes
3. Review validation logic in spider code

### Issue: "Proxy connection failed"

**Check:**
```bash
# Test proxy directly
curl -x "$PROXY_URL" "https://ipinfo.io/json"

# If fails, check:
echo $PROXY_URL  # Should show valid URL
```

**Fix:**
- Verify proxy credentials at proxyscrape.com
- Check subscription is active
- Try without proxy temporarily (comment out in .env)

### Issue: "Invalid team names (emojis, UI text)"

**Example:**
```json
{"away": "🆕NEW VERSION", "home": "SPORTS"}
```

**Fix:** This is caught by validation. The spider's validation logic should filter these out. If they appear in output:
1. Check spider validation rules in `_extract_games_js()`
2. Ensure team name regex is working: `/^[A-Z\s\-\.&']+$/i`
3. Add min length check (e.g., > 3 characters)

---

## Data Quality Metrics (Targets)

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| **Market Coverage** | > 95% | > 90% | < 85% |
| **Quote Completeness** | > 95% | > 90% | < 85% |
| **Valid Team Names** | 100% | > 98% | < 95% |
| **Timestamps Present** | 100% | 100% | < 100% |
| **JSON Parse Errors** | 0 | < 1% | > 1% |
| **Scraping Speed** | < 5s/game | < 10s | > 15s |

---

## Advanced Testing

### A/B Testing (With/Without Proxy)

```bash
# Without proxy
PROXY_URL= uv run walters-analyzer scrape-overtime --sport nfl
mv data/overtime_live/overtime-live-*.jsonl test_no_proxy.jsonl

# With proxy
uv run walters-analyzer scrape-overtime --sport nfl
mv data/overtime_live/overtime-live-*.jsonl test_with_proxy.jsonl

# Compare
uv run python test_scraper_backtest.py ./
```

### Time Series Testing

```bash
# Run scraper every hour for 5 hours
for i in {1..5}; do
  echo "Run $i at $(date)"
  uv run walters-analyzer scrape-overtime --sport nfl
  sleep 3600
done

# Analyze all outputs
uv run python test_scraper_backtest.py
```

### Market Movement Tracking

```bash
# Scrape same games multiple times
uv run walters-analyzer scrape-overtime --sport nfl > run1.log
sleep 300  # Wait 5 minutes
uv run walters-analyzer scrape-overtime --sport nfl > run2.log

# Compare outputs to detect line movements
diff <(jq -S . data/overtime_live/*run1*.jsonl) \
     <(jq -S . data/overtime_live/*run2*.jsonl)
```

---

## Integration with Billy Walters Analysis

Once you have quality odds + injury data:

```bash
# Combined game + injury analysis
uv run python analyze_games_with_injuries.py

# Position-based injury analysis
uv run python analyze_injuries_by_position.py
```

**Expected Output:**
- Point spread impacts for each injury
- Market inefficiency detection
- Betting recommendations with historical win rates
- Kelly Criterion bet sizing

---

## Automated Testing Script

Save this as `run_full_test.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 Starting comprehensive scraper testing..."

# 1. Setup
echo "📦 Checking dependencies..."
uv sync

# 2. Run scrapers
echo "🕷️  Running pre-game odds scraper..."
uv run walters-analyzer scrape-overtime --sport nfl

echo "⚡ Running live odds scraper..."
uv run walters-analyzer scrape-overtime --live

echo "🏥 Running injury scraper..."
uv run walters-analyzer scrape-injuries --sport nfl

# 3. Validate data
echo "✅ Validating data quality..."
uv run python test_scraper_backtest.py

# 4. Check snapshots
echo "📸 Checking debug snapshots..."
ls -lh snapshots/

echo "✅ Testing complete! Review output above."
```

Make executable and run:
```bash
chmod +x run_full_test.sh
./run_full_test.sh
```

---

## Summary Checklist

**Before Running:**
- [ ] `.env` file created with credentials
- [ ] Proxy configured (optional but recommended)
- [ ] Dependencies installed (`uv sync`)
- [ ] Playwright browser installed

**After Running:**
- [ ] Data files created (JSONL, CSV, Parquet)
- [ ] Validation script shows > 90% market coverage
- [ ] Snapshots look correct (no error pages)
- [ ] Team names are valid (no UI elements)
- [ ] Prices in valid range (-1000 to +1000)

**For Production:**
- [ ] Test over multiple days
- [ ] Verify proxy rotation (different IPs)
- [ ] Check Cloudflare bypass working
- [ ] Monitor for rate limiting
- [ ] Set up automated scraping schedule

---

## Help & Resources

- **Full Report:** `SCRAPER_TESTING_REPORT.md`
- **Proxy Setup:** `PROXY_SETUP.md`
- **General Usage:** `README.md`
- **Validation Tool:** `test_scraper_backtest.py`

**Quick Help:**
```bash
uv run walters-analyzer --help
uv run walters-analyzer scrape-overtime --help
uv run python test_scraper_backtest.py --help
```

---

**Good luck with testing! 🚀**
