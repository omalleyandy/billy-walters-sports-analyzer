# ESPN NCAAF Scoreboard Integration

Complete implementation of ESPN NCAAF scoreboard data collection mirroring Chrome DevTools workflow.

**Status:** Production-ready (2025-11-11)

## Overview

This integration provides direct access to ESPN's public APIs for NCAA College Football data, including:
- Complete scoreboard with all games
- Game summaries with box scores
- Play-by-play data with EPA context
- Live win probabilities
- Betting odds from multiple providers

## Architecture

### Components

**Client** (`src/data/espn_ncaaf_scoreboard_client.py`)
- Async HTTP client using httpx
- Retry logic with exponential backoff
- Rate limiting (0.5s default, mirrors ESPN's 15s re-polling)
- Four primary API endpoints:
  - Scoreboard (master endpoint)
  - Game summary (box score, drives, injuries)
  - Play-by-play (drive feed with EPA context)
  - Win probability (live projections)

**Normalizer** (`src/data/espn_ncaaf_normalizer.py`)
- Converts ESPN JSON to parquet tables
- Three primary tables:
  - `events.parquet` (game-level data)
  - `competitors.parquet` (team-level data)
  - `odds.parquet` (betting lines)
- Extracts box scores, drives, scoring plays, injuries

**CLI Script** (`scripts/scrape_espn_ncaaf_scoreboard.py`)
- Command-line interface for data collection
- Supports week/date-based queries
- Live monitoring with continuous polling
- Complete game data fetching (all APIs)
- Parquet normalization and storage

**Slash Command** (`.claude/commands/espn-ncaaf-scoreboard.md`)
- Quick access via `/espn-ncaaf-scoreboard`
- Integrated into Claude Code workflow

### API Endpoints (DevTools-Mirrored)

**Base URLs:**
- Site API: `https://site.api.espn.com`
- Core API: `https://sports.core.api.espn.com`

**Scoreboard:**
```
GET /apis/site/v2/sports/football/college-football/scoreboard
Params: week, dates, groups, limit, lang, region, tz
```

**Game Summary:**
```
GET /apis/site/v2/sports/football/college-football/summary
Params: event={EVENT_ID}
```

**Play-by-Play:**
```
GET /v2/sports/football/leagues/college-football/events/{EVENT_ID}/competitions/{EVENT_ID}/plays
Params: limit, page, lang, region
```

**Win Probability:**
```
GET /v2/sports/football/leagues/college-football/events/{EVENT_ID}/competitions/{EVENT_ID}/probabilities
Params: lang, region
```

## Usage

### Basic Usage

```bash
# Current week FBS games
uv run python scripts/scrape_espn_ncaaf_scoreboard.py

# Specific week with verification
uv run python scripts/scrape_espn_ncaaf_scoreboard.py --week 12 --verify --parquet

# Rivalry week (high game count)
uv run python scripts/scrape_espn_ncaaf_scoreboard.py --date 20251129 --limit 400 --parquet

# Complete game data (all APIs)
uv run python scripts/scrape_espn_ncaaf_scoreboard.py --week 12 --complete --parquet

# Monitor live games (polls every 15 seconds like ESPN)
uv run python scripts/scrape_espn_ncaaf_scoreboard.py --week 12 --monitor --interval 15
```

### Command-Line Options

**Query Parameters:**
- `--week N` - Week number (1-15 regular season, 16+ postseason)
- `--date YYYYMMDD` - Specific date (alternative to --week)
- `--groups 80 81 55` - Group IDs (80=FBS, 81=FCS, 55=CFP)
- `--limit 400` - Max games to return (ESPN defaults to 300)
- `--tz TZ` - Timezone for game times (default: America/New_York)

**Data Collection:**
- `--complete` - Fetch complete game data (summary + plays + win prob)
- `--parquet` - Save normalized data as parquet tables
- `--verify` - Run verification checklist on data

**Monitoring:**
- `--monitor` - Monitor live games with continuous polling
- `--interval N` - Polling interval in seconds (default: 15)
- `--duration N` - Monitoring duration in seconds (indefinite if not set)

**Output:**
- `--output-dir PATH` - Output directory for raw JSON (default: data/raw/espn/scoreboard)
- `--parquet-dir PATH` - Output directory for parquet (default: data/normalized/espn)
- `--quiet` - Suppress output except errors

### Python API

```python
from src.data.espn_ncaaf_scoreboard_client import ESPNNCAAFScoreboardClient
from src.data.espn_ncaaf_normalizer import ESPNNCAAFNormalizer

# Initialize client
async with ESPNNCAAFScoreboardClient() as client:
    # Get scoreboard for specific week
    scoreboard = await client.get_scoreboard(week=12, groups=80, limit=400)

    # Verify data quality
    verification = client.verify_scoreboard_response(scoreboard)
    print(f"Valid: {verification['valid']}")
    print(f"Events: {verification['event_count']}")
    print(f"Providers: {verification['providers']}")

    # Get complete game data
    for event in scoreboard['events']:
        event_id = event['id']
        game_data = await client.get_complete_game_data(event_id)

        # game_data contains:
        # - summary (box score, drives, scoring plays, injuries)
        # - plays (play-by-play with EPA context)
        # - win_probability (live projections)

    # Save raw JSON
    await client.save_scoreboard_raw(
        scoreboard,
        Path("data/raw/espn/scoreboard"),
        date="20251123"
    )

# Normalize to parquet
normalizer = ESPNNCAAFNormalizer(Path("data/normalized/espn"))
events_df, competitors_df, odds_df = normalizer.normalize_scoreboard(scoreboard)

# Save parquet tables
paths = normalizer.save_parquet(events_df, competitors_df, odds_df, date="20251123")
print(f"Events: {paths['events']}")
print(f"Competitors: {paths['competitors']}")
print(f"Odds: {paths['odds']}")
```

## Data Format

### Raw JSON Storage

**Directory Structure:**
```
data/raw/espn/scoreboard/
├── 20251123/
│   ├── 20251123_120000_scoreboard.json
│   ├── 20251123_120030_game_401628532.json
│   └── ...
└── 20251130/
    └── ...
```

**Scoreboard JSON:**
```json
{
  "leagues": [...],
  "season": {"year": 2025, "type": 2, "slug": "regular-season"},
  "week": {"number": 12},
  "events": [
    {
      "id": "401628532",
      "name": "Ohio State at Michigan",
      "date": "2025-11-23T17:00Z",
      "status": {...},
      "competitions": [
        {
          "competitors": [...],
          "odds": [...],
          "venue": {...},
          "weather": {...}
        }
      ]
    }
  ]
}
```

**Game Data JSON:**
```json
{
  "event_id": "401628532",
  "summary": {
    "boxscore": {...},
    "drives": {...},
    "scoringPlays": [...],
    "injuries": [...]
  },
  "plays": {
    "items": [...]
  },
  "win_probability": {
    "homeWinPercentage": 65.5,
    "awayWinPercentage": 34.5
  },
  "fetched_at": "2025-11-23T12:00:00"
}
```

### Parquet Tables

**events.parquet** (game-level data)
- event_id, name, date, season_type, week
- status, status_detail
- venue_name, venue_city, venue_state, venue_indoor
- temperature, condition
- broadcast_network, attendance

**competitors.parquet** (team-level data)
- event_id, team_id, team_name
- home_away, score, winner
- rank, record

**odds.parquet** (betting lines)
- event_id, provider
- spread, over_under
- home_moneyline, away_moneyline
- details, timestamp

## Verification Checklist

The client includes automatic verification of data quality:

**Checks Performed:**
1. **Season/Week Validation**
   - Confirms `season.type` matches requested slate
   - Verifies `week.number` matches requested week

2. **Odds Provider Validation**
   - Checks `competitions[].odds[].provider` for expected books
   - Common providers: Caesars, ESPN BET, DraftKings, FanDuel
   - ESPN occasionally changes provider ordering

3. **Game Status Validation**
   - Identifies postponed games (`status.type.state == "postponed"`)
   - Identifies canceled games (`status.type.state == "canceled"`)
   - Ensures downstream analytics skip bankroll allocation

**Usage:**
```python
verification = client.verify_scoreboard_response(scoreboard)

if not verification['valid']:
    print("Errors:", verification['errors'])

for warning in verification['warnings']:
    print("Warning:", warning)
```

## Integration with Billy Walters System

### Odds Comparison

The normalizer includes support for comparing ESPN odds with Overtime.ag lines:

```python
# Compare odds for edge detection
comparison_df = normalizer.compare_odds_with_overtime(
    espn_odds_df,
    overtime_data
)

# comparison_df contains:
# - event_id
# - espn_spread, espn_total
# - overtime_spread, overtime_total
# - spread_diff, total_diff (for value opportunities)
```

### Workflow Integration

**Weekly Workflow:**
```bash
# Tuesday/Wednesday - Collect NCAAF data
/espn-ncaaf-scoreboard --week 12 --complete --parquet

# Compare with Overtime odds
uv run python scripts/compare_ncaaf_odds.py

# Run Billy Walters edge detection
/edge-detector --league NCAAF

# Generate betting card
/betting-card --league NCAAF
```

### Live Monitoring

**Game Day Usage:**
```bash
# Start live monitoring (Saturday games)
uv run python scripts/scrape_espn_ncaaf_scoreboard.py \
  --week 12 \
  --monitor \
  --interval 15 \
  --duration 14400 \
  --complete \
  --parquet

# 14400 seconds = 4 hours (typical game slate duration)
# Polls every 15 seconds (matches ESPN's refresh rate)
# Fetches complete data (summary + plays + win prob)
```

## Testing

**Test Suite:** `tests/test_espn_ncaaf_scoreboard_client.py`

**Coverage:**
- Client initialization and connection
- All API endpoints (scoreboard, summary, plays, win prob)
- Data verification and validation
- File I/O operations
- Retry logic and error handling

**Running Tests:**
```bash
# Run all tests (asyncio only)
uv run pytest tests/test_espn_ncaaf_scoreboard_client.py -v -k "not trio"

# Run with coverage
uv run pytest tests/test_espn_ncaaf_scoreboard_client.py -v --cov=src.data.espn_ncaaf_scoreboard_client
```

**Test Results (2025-11-11):**
- 18 tests passing (asyncio)
- 15 tests skipped (trio - not installed)
- 100% pass rate for installed backend

## Performance

**Rate Limiting:**
- Default: 0.5s between requests
- ESPN re-polls: Every 15 seconds
- Configurable via `rate_limit_delay` parameter

**Retry Logic:**
- Default max retries: 3
- Exponential backoff: 2^attempt seconds
- Handles transient network errors

**Monitoring Performance:**
- 15-second polling interval (matches ESPN)
- ~240 polls per hour
- ~1GB raw JSON per 4-hour game slate (with --complete)
- ~100MB parquet per 4-hour game slate

## Group IDs Reference

**Primary Groups:**
- `80` - FBS (Division I FBS)
- `81` - FCS (Division I FCS)
- `55` - CFP (College Football Playoff)

**Usage:**
```bash
# FBS only (default)
--groups 80

# FBS + FCS
--groups 80 81

# CFP games only
--groups 55
```

## Common Issues

**No games found:**
- Check current week: `/current-week` (for NFL, NCAAF uses ESPN's week system)
- Verify week number is within season (1-15 regular, 16+ postseason)
- Some weeks have fewer games (rivalry week has 400+)

**Odds providers missing:**
- ESPN occasionally changes provider ordering
- Use `--verify` flag to check which providers are present
- Some games don't have odds (FCS, lower-tier games)

**Parquet errors:**
- Ensure output directory exists and is writable
- Check disk space (large game slates can be 100MB+)
- Verify pandas and pyarrow are installed: `uv sync`

## Future Enhancements

**Planned Features:**
1. Team name mapping (ESPN ↔ Overtime.ag)
2. Automatic odds comparison with edge detection
3. Historical data backfill (past weeks/seasons)
4. Advanced stats extraction (EPA, success rate, etc.)
5. Player-level data (passing, rushing, receiving)

**Integration Opportunities:**
1. Billy Walters power ratings (compare with ESPN's metrics)
2. Weather impact analysis (game-time conditions)
3. Injury impact quantification (position-specific)
4. Home field advantage calculation
5. Conference strength analysis

## Files Created (2025-11-11)

**Implementation:**
- `src/data/espn_ncaaf_scoreboard_client.py` (585 lines) - Main API client
- `src/data/espn_ncaaf_normalizer.py` (338 lines) - Data normalizer
- `scripts/scrape_espn_ncaaf_scoreboard.py` (328 lines) - CLI script

**Tests:**
- `tests/test_espn_ncaaf_scoreboard_client.py` (414 lines) - 18 passing tests

**Documentation:**
- `.claude/commands/espn-ncaaf-scoreboard.md` - Slash command
- `docs/ESPN_NCAAF_SCOREBOARD.md` (this file) - Complete documentation

**Total:** 1,665 lines of production-ready code

## References

**ESPN API Documentation:**
- No official public API docs (reverse-engineered from DevTools)
- Site API: `site.api.espn.com`
- Core API: `sports.core.api.espn.com`
- League: `college-football` (not `ncaaf`)

**Chrome DevTools Workflow:**
1. Load https://www.espn.com/college-football/scoreboard
2. Open DevTools → Network tab
3. Enable XHR + Fetch filters
4. Enable "Preserve log"
5. Use week selector to trigger API calls
6. Copy requests via "Copy as fetch"

**Related Documentation:**
- [Billy Walters Edge Detection](../src/walters_analyzer/valuation/billy_walters_edge_detector.py)
- [Overtime.ag Integration](OVERTIME_HYBRID_SCRAPER.md)
- [NCAAF Analysis Guide](../NCAAF_EDGE_DETECTION_STATUS.md)

## Support

**Questions or Issues:**
- Check LESSONS_LEARNED.md for similar problems
- Review test suite for usage examples
- Use `/document-lesson` to capture new issues

**Contributing:**
- Follow development guidelines in CLAUDE.md
- Add tests for new features
- Update documentation with changes
- Run `uv run pytest` before committing
