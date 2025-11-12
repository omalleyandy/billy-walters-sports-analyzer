# Overtime.ag Scraper Quick Reference

## TL;DR - When to Scrape

### OPTIMAL WINDOW
**Tuesday-Thursday, 12 PM - 6 PM ET**
- Lines post after Monday Night Football
- Maximum data availability
- Stable odds before sharp action

### AVOID
**Sunday/Monday, 6 PM - 11 PM ET**
- Games in progress
- Lines removed from site
- Result: 0 games (expected)

---

## Quick Commands

### Pre-Game NFL Scraper (Recommended)

```bash
# Basic scrape (visible browser)
uv run python scripts/scrape_overtime_nfl.py

# Production (headless + convert)
uv run python scripts/scrape_overtime_nfl.py --headless --convert

# Without proxy
uv run python scripts/scrape_overtime_nfl.py --proxy ""
```

### Live Odds Scraper (NCAAF)

```bash
# Run Scrapy spider
cd scrapers/overtime_live
uv run scrapy crawl overtime_live -o ../../output/overtime_live.json
```

---

## Weekly Schedule

```
Monday:     Wait for MNF to finish
Tuesday:    SCRAPE (2 PM ET) - New lines post
Wednesday:  SCRAPE (2 PM ET) - Verify stability
Thursday:   SCRAPE (12 PM ET) - Before TNF
Friday-Sun: Avoid (games in progress)
```

---

## Validation Checklist

After scraping, check output JSON:

```json
"data_validation": {
  "is_valid": true,          // ← Must be true
  "game_count": 14,          // ← Should be 14-16 for NFL
  "has_odds": true,          // ← Must be true
  "has_team_names": true,    // ← Must be true
  "warnings": []             // ← Should be empty
}
```

If `is_valid: false`, check warnings and timing.

---

## Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| 0 games found | Check time - scrape Tue-Thu 12-6 PM ET |
| Proxy auth failed | `uv run python src/data/proxy_manager.py` |
| Login failed | Verify `.env` credentials |
| Invalid data | Check `data_validation.warnings` |

---

## Integration with Billy Walters Workflow

```bash
# 1. Scrape (Tuesday-Thursday)
uv run python scripts/scrape_overtime_nfl.py --headless --convert

# 2. Auto-triggered by hook (or manual)
/edge-detector

# 3. Generate picks
/betting-card

# 4. Track performance
/clv-tracker
```

---

## Environment Setup

Required in `.env`:

```bash
OV_CUSTOMER_ID=your_customer_id
OV_PASSWORD=your_password
OVERTIME_PROXY=http://user:pass@host:port  # Optional
```

---

## Data Quality Indicators

**Good Scrape**:
- Game count: 14-16 (NFL regular season)
- All games have team names
- All games have spreads OR totals OR moneylines
- No validation warnings
- Scraped Tuesday-Thursday

**Bad Scrape** (retry later):
- Game count: 0
- Warning: "No games found"
- Scraped Sunday/Monday evening
- Games in progress

---

## Full Documentation

- [Complete Usage Guide](OVERTIME_SCRAPER_USAGE.md)
- [Technical Reference](OVERTIME_TECHNICAL_REFERENCE.md)
- [Integration Guide](OVERTIME_INTEGRATION_COMPLETE.md)
