# ESPN Data Collection Pipeline - QA Quick Reference

## Test Execution

```bash
# Run all 56 ESPN data QA tests
uv run pytest tests/test_espn_data_qa.py -v

# Run specific component tests
uv run pytest tests/test_espn_data_qa.py::TestESPNAPIClient -v
uv run pytest tests/test_espn_data_qa.py::TestESPNClient -v
uv run pytest tests/test_espn_data_qa.py::TestESPNInjuryScraper -v
uv run pytest tests/test_espn_data_qa.py::TestESPNNCAAFNormalizer -v
uv run pytest tests/test_espn_data_qa.py::TestESPNNCAAFScoreboardClient -v
uv run pytest tests/test_espn_data_qa.py::TestESPNNcaafTeamScraper -v
uv run pytest tests/test_espn_data_qa.py::TestDataPipelineIntegration -v
uv run pytest tests/test_espn_data_qa.py::TestDataCollectionPerformance -v
uv run pytest tests/test_espn_data_qa.py::TestErrorHandlingAndRecovery -v

# Run with coverage
uv run pytest tests/test_espn_data_qa.py --cov=src.data --cov-report=term
```

## Test Results Summary

| Component | Tests | Status | Notes |
|-----------|-------|--------|-------|
| ESPNAPIClient | 7 | ✅ PASS | Power ratings, team stats, file I/O |
| ESPNClient | 11 | ✅ PASS | Async, retry logic, rate limiting, circuit breaker |
| ESPNInjuryScraper | 5 | ✅ PASS | JSON/JSONL output, data format |
| ESPNNCAAFNormalizer | 9 | ✅ PASS | Parquet conversion, schema validation |
| ESPNNCAAFScoreboardClient | 6 | ✅ PASS | API parameters, verification, file I/O |
| ESPNNcaafTeamScraper | 4 | ✅ PASS | URL building, content parsing |
| Integration/Performance | 14 | ✅ PASS | Pipeline flow, large datasets, error handling |
| **TOTAL** | **56** | **✅ PASS** | 100% pass rate, 22s execution |

## Component Responsibilities

### 1. ESPNAPIClient
- Get team statistics for power ratings
- Extract offensive/defensive metrics
- Calculate derived metrics (total yards)
- Save data to organized JSON structure

**Key Methods**:
```python
client.extract_power_rating_metrics(team_id, league)
client.get_team_statistics(team_id, league)
client.save_to_json(data, data_type, league, output_dir)
```

### 2. ESPNClient
- Async REST client for all ESPN endpoints
- Implements rate limiting (0.5s default)
- Circuit breaker pattern (5 failures = 300s timeout)
- Automatic retry with exponential backoff

**Usage**:
```python
async with ESPNClient() as client:
    scoreboard = await client.get_scoreboard("NFL", week=10)
    stats = await client.get_team_stats("NCAAF", "194")
    standings = await client.get_standings("NFL")
```

### 3. ESPNInjuryScraper
- Fetch NFL injury reports
- Fetch NCAAF FBS injury reports
- Save as both JSON and JSONL
- Record timestamps and source

**Output Structure**:
```json
{
  "source": "espn",
  "league": "NFL|NCAAF",
  "team": "Team Name",
  "player_name": "Player Name",
  "position": "QB",
  "injury_status": "Out|Questionable|Doubtful",
  "date_reported": "2025-11-23T00:00Z",
  "collected_at": "2025-11-23T12:00Z"
}
```

### 4. ESPNNCAAFNormalizer
- Convert scoreboard JSON to 3 parquet tables
- Events: game-level data (venue, weather, broadcast)
- Competitors: team-level data (score, rank, record)
- Odds: betting line data (spread, total, moneylines)

**Data Pipeline**:
```python
normalizer = ESPNNCAAFNormalizer(output_dir)

# Normalize
events_df, competitors_df, odds_df = normalizer.normalize_scoreboard(raw_json)

# Save
paths = normalizer.save_parquet(events_df, competitors_df, odds_df)

# Load
events_df, competitors_df, odds_df = normalizer.load_parquet(date="20251123")
```

### 5. ESPNNCAAFScoreboardClient
- Fetch NCAAF scoreboard with games
- Fetch complete game summaries
- Fetch play-by-play data
- Fetch win probabilities
- Verify response quality

**API Parameters**:
- `week`: Week number (1-15 regular)
- `groups`: 80=FBS, 81=FCS, 55=CFP
- `limit`: Max games (default 400)
- `tz`: Timezone (default America/New_York)

### 6. ESPNNcaafTeamScraper
- Build team URLs for all page types
- Scrape team pages with Playwright
- Parse injury reports
- Parse team statistics
- Save matchup data

**Page Types**:
```python
scraper.build_team_url(team_id, "home")       # Overview
scraper.build_team_url(team_id, "injuries")   # Injury report
scraper.build_team_url(team_id, "stats")      # Statistics
scraper.build_team_url(team_id, "schedule")   # Schedule
scraper.build_team_url(team_id, "roster")     # Roster
```

## Data Quality Validation

### Required Fields by Component

**Injury Records** (10 fields):
- ✅ source, league, team, team_id, player_name
- ✅ position, injury_status, date_reported, collected_at

**Team Stats Metrics** (16 fields):
- ✅ team_id, team_name, games_played
- ✅ points_per_game, passing_yards_per_game, rushing_yards_per_game
- ✅ points_allowed_per_game, passing_yards_allowed_per_game, rushing_yards_allowed_per_game
- ✅ turnover_margin, third_down_pct, takeaways, giveaways
- ✅ total_yards_per_game, total_yards_allowed_per_game

**Scoreboard Events** (14 fields):
- ✅ event_id, name, date, season_type, week
- ✅ venue_name, venue_city, venue_state, venue_indoor
- ✅ temperature, condition, broadcast_network, attendance

**Competitors** (8 fields):
- ✅ event_id, team_id, team_name, home_away
- ✅ score, winner, rank, record

**Odds** (8 fields):
- ✅ event_id, provider, spread, over_under
- ✅ home_moneyline, away_moneyline, details, timestamp

## Performance Benchmarks

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Rate limit enforcement (3 calls, 0.1s delay) | <0.3s | 0.2s | ✅ |
| Normalize 50 games | <5s | <1s | ✅ |
| All 56 tests | <60s | 22s | ✅ |

## Common Issues & Solutions

### Issue: Client not connected
```python
# ❌ Wrong
client = ESPNClient()
data = await client._make_request(url)

# ✅ Correct
async with ESPNClient() as client:
    data = await client._make_request(url)
```

### Issue: Missing team stats metrics
```python
# Verify ESPN API response has all categories
required_categories = ["scoring", "passing", "rushing", "miscellaneous"]
for cat in required_categories:
    if cat not in data["results"]["stats"]["categories"]:
        raise ValueError(f"Missing {cat} category")
```

### Issue: Normalizer crashes with None venue
```python
# Scoreboard must have venue dict (even if empty)
competition = {
    "venue": {"fullName": "Stadium", "address": {}},  # ✅ Not None
    "weather": {},  # ✅ Not None
    # ...
}
```

## Integration Checklist

- [ ] Run ESPN data QA tests: `uv run pytest tests/test_espn_data_qa.py`
- [ ] Verify all 56 tests pass
- [ ] Check CLAUDE.md for component documentation
- [ ] Review ESPN_DATA_QA_REPORT_2025-11-23.md for details
- [ ] Deploy components to production
- [ ] Set up weekly data collection schedule
- [ ] Monitor API success rate and data quality
- [ ] Archive raw JSON before normalization
- [ ] Track metrics: success rate, completeness, processing time

## References

- Full QA Report: `docs/reports/ESPN_DATA_QA_REPORT_2025-11-23.md`
- Test Suite: `tests/test_espn_data_qa.py`
- Components: `src/data/espn_*.py`
- Integration: `scripts/analysis/collect_all_data.py`

---

**Last Updated**: 2025-11-23
**Status**: ✅ PRODUCTION READY
