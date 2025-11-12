Fetch ESPN NCAAF scoreboard data mirroring Chrome DevTools workflow.

Pulls games, box scores, and live win probabilities from ESPN's public APIs.

**Implementation:** `scripts/scrapers/scrape_espn_ncaaf_scoreboard.py`

Usage:
```bash
# Current week FBS games
uv run python scripts/scrapers/scrape_espn_ncaaf_scoreboard.py

# Specific week with verification
uv run python scripts/scrapers/scrape_espn_ncaaf_scoreboard.py --week 12 --verify --parquet

# Rivalry week (high game count)
uv run python scripts/scrapers/scrape_espn_ncaaf_scoreboard.py --date 20251129 --limit 400 --parquet

# Complete game data (all APIs)
uv run python scripts/scrapers/scrape_espn_ncaaf_scoreboard.py --week 12 --complete --parquet

# Monitor live games (polls every 15 seconds like ESPN)
uv run python scripts/scrapers/scrape_espn_ncaaf_scoreboard.py --week 12 --monitor --interval 15
```

Options:
- `--week N` - Week number (1-15 regular, 16+ postseason)
- `--date YYYYMMDD` - Specific date (alternative to --week)
- `--groups 80 81 55` - Group IDs (80=FBS, 81=FCS, 55=CFP)
- `--limit 400` - Max games to return
- `--complete` - Fetch complete game data (summary + plays + win prob)
- `--parquet` - Save normalized data as parquet tables
- `--verify` - Run verification checklist
- `--monitor` - Monitor live games with continuous polling

API Endpoints:
- Scoreboard: `/apis/site/v2/sports/football/college-football/scoreboard`
- Summary: `/apis/site/v2/sports/football/college-football/summary`
- Plays: `/v2/sports/football/leagues/college-football/events/{id}/competitions/{id}/plays`
- Win Probability: `/v2/sports/football/leagues/college-football/events/{id}/competitions/{id}/probabilities`

Output:
- Raw JSON: `data/raw/espn/scoreboard/{date}/{timestamp}_scoreboard.json`
- Parquet tables: `data/normalized/espn/{date}/events.parquet`, `competitors.parquet`, `odds.parquet`
- Game data: `data/raw/espn/scoreboard/{date}/{timestamp}_game_{event_id}.json`

Verification:
- Confirms season.type + week.number match requested slate
- Checks odds providers (Caesars, ESPN BET, etc.) are present
- Identifies postponed/canceled games for bankroll logic
