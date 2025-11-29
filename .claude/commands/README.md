# Billy Walters Sports Analyzer - Slash Commands Reference

Complete reference for all slash commands organized by Billy Walters methodology workflow.

## Quick Start Commands

| Command             | Description                                   | Usage               |
| ------------------- | --------------------------------------------- | ------------------- |
| `/current-week`     | Show current NFL week                         | `/current-week`     |
| `/pre-validate`     | ✨ NEW: Check environment before collection   | `/pre-validate`     |
| `/collect-all-data` | Complete data collection with auto-validation | `/collect-all-data` |
| `/post-validate`    | ✨ NEW: Check data quality after collection   | `/post-validate`    |
| `/edge-detector`    | Find betting value with auto-validation       | `/edge-detector`    |
| `/betting-card`     | Generate weekly picks                         | `/betting-card`     |

## Billy Walters Workflow Commands

### 1. Foundation Data (Run First)

#### `/power-ratings` - Team Strength Ratings

Fetch and update power ratings for all NFL teams.

```bash
/power-ratings              # Current week, all sources
/power-ratings 13 massey    # Week 13, Massey only
/power-ratings 13 all       # Week 13, all sources
```

**What it does:**

- Scrapes Massey Ratings (composite of 100+ systems)
- Applies Billy Walters 90/10 update formula
- Adjusts for draft, coaching, free agency
- Outputs: Power ratings (70-100 scale) for all teams

**When to run:** Monday after games, before line release

---

#### `/scrape-massey` - Massey Ratings Scraper

Direct access to Massey Ratings scraper.

```bash
/scrape-massey nfl          # NFL current season
/scrape-massey ncaaf 2025   # NCAAF 2025 season
/scrape-massey both         # Both sports
```

**What it does:**

- Fetches composite rankings from Massey
- Extracts offensive/defensive sub-ratings
- Stores historical data

**When to run:** As needed for power rating updates

---

### 2. Game Context (Core Data)

#### `/team-stats` - Team Performance Metrics

Fetch current season statistics for teams.

```bash
/team-stats "Kansas City Chiefs" nfl
/team-stats "Georgia Bulldogs" ncaaf
/team-stats "Buffalo" nfl
```

**What it does:**

- ESPN API team statistics
- Offensive/defensive efficiency
- Situational performance (home/away)

**When to run:** Weekly on Tuesday

---

#### `/espn-ncaaf` - ESPN Hub DevTools Capture

Use Chrome DevTools to copy the JSON feeds that power https://www.espn.com/college-football/.

```bash
/espn-ncaaf --week 12 --date 20251116 --group 80
```

**What it does:**

- Captures the `scoreboard` payload (events, odds, injuries)
- Pulls AP/Coaches/CFP rankings via the `rankings` endpoint
- Copies standings references from `sports.core` `/standings/0`
- Saves the headline/news feed for narrative context

#### `/espn-ncaaf-scoreboard` - Full Scoreboard Harvest

Mirror all XHRs from https://www.espn.com/college-football/scoreboard.

```bash
/espn-ncaaf-scoreboard --week {} --limit 400 --groups 80
```

**What it does:**

- Downloads the master scoreboard feed for any week/date
- Follows each `event` into `summary`, `plays`, and `probabilities`
- Archives raw + normalized tables for odds and win percentages

**Workflow:**

1. Keep DevTools open while switching weeks—each change replays `scoreboard`.
2. Copy additional calls (summary, win probability) per event ID.
3. Store JSON under `data/raw/espn/scoreboard/<date>/`.

---

#### `/espn-player-stats` - Player Leaderboards

Reverse engineer the ESPN player stats tab for season/weekly leaders.

```bash
/espn-player-stats --season 2025 --type reg --group 80 --category passingYards
```

**What it does:**

- Hits `sports.core` `/leaders` endpoint for passing, rushing, defense, etc.
- Follows `$ref`s to grab athlete bios and full stat splits
- Builds CSV/parquet for top-N players per category

**Workflow:**

1. In DevTools, filter by `leaders`, switch categories to trigger new calls.
2. Copy as fetch, replay outside the browser (swap `.pvt` → `.com`).
3. Save both the leaders payload and enriched athlete stats.

#### `/espn-team-stats` - Team Efficiency Tables

Capture the team-tab XHR traffic for offense/defense splits.

```bash
/espn-team-stats --season 2025 --type reg --group 80
```

**What it does:**

- Downloads `teams?groups=80` directory and every `teams/{id}/statistics`
- Pulls per-team leaders for quick “star player” references
- Feeds ResearchEngine with ESPN’s per-game values for validation

**Workflow:**

1. Use DevTools to copy `teams/{id}/statistics?season=YYYY` requests.
2. Iterate every FBS team (respect ~2 req/sec).
3. Flatten categories (passing, rushing, defense, efficiency) into parquet.

---

#### `/injury-report` - Billy Walters Injury Analysis

Analyze injuries with position-specific point values.

```bash
/injury-report "team: {_/name}" nfl
/injury-report "team: {_/id}" ncaaf
/injury-report nfl
```

**What it does:**

- Fetches ESPN + NFL official injury reports
- Calculates Billy Walters position values
- QB Elite OUT = -4.5 pts, WR1 = -1.8 pts, etc.
- Identifies position group crises (O-line, secondary)
- Tracks recovery timelines

**When to run:**

- Wednesday: Initial report
- Friday: Final report before weekend

---

#### `/weather` - Weather Impact Analysis

Calculate Billy Walters weather adjustments.

```bash
/weather "Green Bay" "2025-11-17 13:00"
/weather "Kansas City"
/weather                    # Prompt for details
```

**What it does:**

- AccuWeather + OpenWeather forecasts
- Wind >15 MPH: -3 to -5 points on total
- Temp <32°F: -2 to -3 points on total
- Indoor stadium detection (no adjustment)

**When to run:** Thursday-Saturday for game-week forecasts

---

### 3. Market Data (Odds & Lines)

#### Data Sources Overview ✨ UPDATED 2025-11-25

Two primary odds sources with different strengths:

| Source         | Method  | Speed   | Data                        | Best For                 |
| -------------- | ------- | ------- | --------------------------- | ------------------------ |
| Overtime.ag    | API     | ~5 sec  | Spread, ML, Total           | Fast bulk collection     |
| Action Network | Browser | ~15 sec | Spread, ML, **Total (O/U)** | Complete odds, real-time |

**Action Network Phase 3** (NEW): Now extracts complete over/under via dropdown switching.

---

#### `/scrape-overtime` - Overtime.ag Odds Scraper

Scrape live odds from Overtime.ag.

```bash
/scrape-overtime                    # Default: headless, convert
/scrape-overtime --visible          # Show browser
/scrape-overtime --no-proxy         # Skip proxy (recommended)
```

**What it does:**

- Playwright browser automation
- Extracts spreads, totals, moneylines
- Converts to Billy Walters format
- Tracks line movements

**When to run:**

- Tuesday-Wednesday: Best for new week lines
- Thursday morning: Pre-TNF
- Avoid Sunday: Lines down during games

---

#### `/odds-analysis` - Line Movement Analysis

Analyze betting line movements and sharp action.

```bash
/odds-analysis              # All games
/odds-analysis BUF_KC       # Specific game
```

**What it does:**

- Opening vs current lines
- Public betting percentages
- Sharp money indicators (reverse line movement)
- Implied probabilities
- Historical closing line value

**When to run:** Daily during betting week

---

#### `/scrape-live-odds` - Live In-Game Odds

Monitor live odds during games (advanced).

```bash
/scrape-live-odds           # All live games
/scrape-live-odds BUF_KC    # Specific game
```

**What it does:**

- Real-time odds during games
- In-game betting opportunities
- Line movement tracking

**When to run:** During games (advanced users only)

---

### 4. Analysis & Edge Detection

#### `/edge-detector` - Billy Walters Edge Detection

Find betting value by comparing your line to market.

```bash
/edge-detector                      # All games, all types
/edge-detector BUF_KC spread        # Specific game, spread only
/edge-detector BUF_KC moneyline     # Specific game, moneyline only
/edge-detector all totals           # All games, totals only
/edge-detector 13                   # Week 13, all games
```

**What it does:**

- Calculates your predicted spread/total
- Compares to market lines
- Identifies edges (point differential)
- Applies Billy Walters thresholds:
  - 7+ pts: MAX BET (5% Kelly, 77% win rate)
  - 4-7 pts: STRONG (3% Kelly, 64% win rate)
  - 2-4 pts: MODERATE (2% Kelly, 58% win rate)
  - 1-2 pts: LEAN (1% Kelly, 54% win rate)
  - <1 pt: NO PLAY

**When to run:** After collecting all data (Wednesday-Thursday)

---

#### `/analyze-matchup` - Deep Dive Matchup Analysis

Comprehensive analysis of specific matchup.

```bash
/analyze-matchup "Kansas City" "Buffalo"
/analyze-matchup KC BUF
```

**What it does:**

- Power rating differential
- Injury impact analysis
- Weather adjustments
- Historical head-to-head
- Sharp action indicators
- Generates full report

**When to run:** For high-confidence plays or complex games

---

#### `/betting-card` - Weekly Betting Recommendations

Generate formatted betting card with all recommendations.

```bash
/betting-card                       # Current week, all formats
/betting-card 13 json               # Week 13, JSON export
/betting-card 13 terminal           # Week 13, terminal display
```

**What it does:**

- Runs complete edge detection
- Filters to actionable plays (edge ≥1.5 pts)
- Ranks by edge size and confidence
- Calculates Kelly Criterion sizes
- Formats betting card with:
  - Play ranking
  - Edge analysis
  - Key factors
  - Line shopping recommendations
  - Timing advice

**When to run:** Wednesday-Thursday after all data collected

---

### 5. Performance Tracking

#### `/clv-tracker` - Closing Line Value Tracking

Track the key metric for long-term success.

```bash
/clv-tracker                        # Current week summary
/clv-tracker 13 analyze             # Week 13 detailed analysis
/clv-tracker season report          # Full season report
/clv-tracker add BUF_KC -2.5 -3.0   # Manual entry
```

**What it does:**

- Tracks your line vs closing line
- Calculates CLV in points
- Measures edge capture rate
- Identifies systematic biases
- Reports:
  - +2.0 avg CLV: Elite (top 1%)
  - +1.5 avg CLV: Professional
  - +1.0 avg CLV: Very Good
  - +0.5 avg CLV: Good
  - <0.0 avg CLV: Review process

**When to run:** After games complete (Sunday night/Monday)

---

### 6. Data Management

#### `/update-data` - Update Specific Data Source

Update individual data sources.

```bash
/update-data                # All sources
/update-data overtime       # Overtime only
/update-data action         # Action Network only
/update-data weather        # Weather only
```

**What it does:**

- Selective data updates
- Faster than full collection
- Useful for refreshing specific data

**When to run:** As needed for data refreshes

---

#### `/collect-all-data` - Complete Data Collection

**RECOMMENDED**: Run complete Billy Walters workflow in correct order.

```bash
/collect-all-data                   # Auto-detect week
/collect-all-data 13                # Week 13
/collect-all-data 13 --no-odds      # Skip odds if APIs down
```

**What it does:**

1. Power Ratings (Massey)
2. Game Schedules (ESPN)
3. Team Statistics (ESPN)
4. Injury Reports (ESPN + NFL)
5. Weather Forecasts (AccuWeather + OpenWeather)
6. Odds Data (Overtime.ag + Action Network)
7. Validation checks
8. Generates summary report

**When to run:**

- **BEST**: Tuesday-Wednesday (new week lines available)
- Thursday: Before TNF
- Avoid Sunday: Games in progress

---

#### `/pre-validate` - Pre-Flight Environment Check ✨ NEW

Quick check before data collection to verify environment is ready.

```bash
/pre-validate                       # Quick environment check
```

**What it does:**

- Verifies all API keys present
- Tests database connection
- Checks output directories exist
- Detects current week from system date
- Ensures no concurrent data collection

**When to run:**

- Before `/collect-all-data` (recommended)
- If you're unsure environment is ready

**Exit codes:**

- 0 = Ready to proceed
- 1 = Critical issue found

---

#### `/post-validate` - Post-Flight Data Quality Check ✨ NEW

Comprehensive validation after data collection completes.

```bash
/post-validate                      # All sources, current week
/post-validate nfl                  # NFL only
/post-validate ncaaf 13             # NCAAF week 13
/post-validate nfl --detailed       # Detailed quality report
```

**What it does:**

- Checks all required files collected
- Quality scores each data source (0-100%)
- Cross-validates consistency
- League separation verification
- Ready for analysis assessment

**When to run:**

- After data collection (automated)
- Before edge detection
- If you want detailed quality report

**Exit codes:**

- 0 = Ready for analysis
- 1 = Quality issues found, review needed

---

#### `/validate-data` - Data Quality Checks (Legacy)

Validate all data sources for quality and completeness.

```bash
/validate-data                      # All sources
/validate-data odds 13             # Odds data, week 13
/validate-data injuries             # Injury reports only
/validate-data all --detailed       # Full detailed report
```

**What it does:**

- Checks data completeness
- Validates ranges (spreads, totals, temp, wind)
- Cross-checks consistency
- Quality scoring (0-100%)
- Alerts on issues

**When to run:**

- After data collection (automated)
- Before edge detection (pre-flight check)
- Daily at 10 AM (scheduled)

**Note:** `/pre-validate` and `/post-validate` are newer, more focused alternatives

---

### 7. Development & Documentation

#### `/document-lesson` - Record Lessons Learned

Document problems solved and solutions.

```bash
/document-lesson
```

**What it does:**

- Adds entry to LESSONS_LEARNED.md
- Captures:
  - Problem description
  - Root cause
  - Solution implemented
  - Prevention tips

**When to run:** After solving non-trivial problems

---

#### `/lessons` - View Lessons Learned

Review past problems and solutions.

```bash
/lessons                    # View recent lessons
/lessons search "odds"      # Search for specific topic
```

**What it does:**

- Displays lessons learned history
- Searchable troubleshooting guide
- Institutional knowledge

**When to run:** When encountering similar problems

---

#### `/current-week` - Show Current NFL Week

Display current NFL week and schedule status.

```bash
/current-week
```

**What it does:**

- Shows current NFL week number
- Displays schedule status
- Lists upcoming games

**When to run:** Anytime to check week number

---

## Recommended Weekly Workflow

### Tuesday (Data Collection Day)

```bash
/current-week                    # Verify week number
/pre-validate                    # Check environment ready (optional)
/collect-all-data                # Complete data collection (with auto-validation)
/post-validate                   # Check data quality (automatic after collection)
```

### Wednesday (Analysis Day)

```bash
/power-ratings                   # Update team ratings
/edge-detector                   # Find betting edges (with auto-validation)
/betting-card                    # Generate weekly picks
```

### Thursday (Line Shopping)

```bash
/odds-analysis                   # Check line movements
/weather                         # Update weather forecasts
/injury-report nfl               # Check Friday injury report
```

### Friday-Saturday (Final Prep)

```bash
/injury-report nfl               # Final injury check
/weather                         # Final weather check
/edge-detector                   # Refresh edges with latest data
```

### Sunday-Monday (Post-Game)

```bash
/clv-tracker                     # Track CLV performance
/document-lesson                 # Document any issues
```

---

## Command Categories

### Data Collection (Step 1-2)

- `/collect-all-data` - Complete workflow ⭐ RECOMMENDED
- `/power-ratings` - Team strength
- `/scrape-massey` - Massey ratings
- `/scrape-overtime` - Odds data
- `/team-stats` - Team performance
- `/injury-report` - Injury analysis
- `/weather` - Weather impact
- `/update-data` - Selective updates

### Analysis (Step 3)

- `/edge-detector` - Find value ⭐ CORE
- `/analyze-matchup` - Deep dive
- `/betting-card` - Weekly picks ⭐ OUTPUT
- `/odds-analysis` - Line movements

### Performance (Step 4)

- `/clv-tracker` - Success metric ⭐ KEY
- `/validate-data` - Quality checks

### Utilities

- `/current-week` - Week info
- `/document-lesson` - Record learnings
- `/lessons` - View history
- `/scrape-live-odds` - Live betting (advanced)

---

## Billy Walters Methodology Map

```
STEP 1: FOUNDATION
├── /power-ratings → Team strength (70-100 scale)
└── /scrape-massey → Massey composite rankings

STEP 2: GAME CONTEXT
├── /team-stats → Performance metrics
├── /injury-report → Position-specific impact
└── /weather → Environmental adjustments

STEP 3: MARKET ANALYSIS
├── /scrape-overtime → Current lines
└── /odds-analysis → Line movements & sharp action

STEP 4: EDGE DETECTION
├── /edge-detector → Compare your line vs market
├── /analyze-matchup → Deep dive analysis
└── /betting-card → Formatted recommendations

STEP 5: EXECUTION & TRACKING
└── /clv-tracker → Measure success (not W/L)

AUTOMATION
├── /collect-all-data → Steps 1-3 automated
└── /validate-data → Quality assurance
```

---

## Tips for Success

1. **Run in Order**: Foundation → Context → Market → Analysis
2. **Tuesday-Wednesday**: Best time for data collection (new lines)
3. **Validate Data**: Always check quality before analysis
4. **Track CLV**: Judge your process, not individual results
5. **Line Shop**: Check 3+ sportsbooks for best prices
6. **Discipline**: Only bet when edge ≥1.5 points
7. **Kelly Sizing**: Respect position sizing based on edge

---

## Environment Variables Required

```bash
# Weather (at least one)
ACCUWEATHER_API_KEY=your_key
OPENWEATHER_API_KEY=your_key

# Overtime.ag (required for odds)
OV_CUSTOMER_ID=your_id
OV_PASSWORD=your_password

# Action Network (optional, for sharp action)
ACTION_USERNAME=your_username
ACTION_PASSWORD=your_password

# Proxy (optional)
PROXY_URL=http://user:pass@host:port
```

---

## Support & Troubleshooting

- **Documentation**: See LESSONS_LEARNED.md for common issues
- **Data Quality**: Run `/validate-data` to diagnose problems
- **Odds Issues**: Check Overtime.ag credentials in .env
- **Weather Errors**: Verify API keys for AccuWeather/OpenWeather

---

**Last Updated:** 2025-11-25 (Action Network Phase 3: Totals Extraction - 2.3)
**Version:** 2.3

---

## Validator Integration ✨ NEW (2025-11-24)

This update integrates the validation hooks directly into the workflow:

### What Changed

- `/collect-all-data` now includes automatic pre-flight validation
- `/collect-all-data` now includes automatic post-flight validation
- `/edge-detector` now includes automatic pre-flight validation
- New `/pre-validate` command for manual environment checks
- New `/post-validate` command for detailed quality reports

### How It Works

1. **Pre-Flight** (automatic): Runs before operations to ensure readiness
2. **Operation**: Collects data or detects edges
3. **Post-Flight** (automatic): Validates success and data quality

### Exit Codes

All validators use consistent exit codes:

- `0` = Success, ready to proceed
- `1` = Issues found, action required

### Manual Alternative

If you prefer manual control, you can run validators directly:

```bash
python .claude/hooks/pre_data_collection_validator.py
python .claude/hooks/post_data_collection_validator.py --league nfl
python .claude/hooks/pre_edge_detection.py
```

See [.claude/hooks/README.md](./../hooks/README.md) for complete hook documentation.
