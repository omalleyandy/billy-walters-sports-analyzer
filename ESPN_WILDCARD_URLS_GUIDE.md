# ESPN College Football Wildcard URLs Guide

## Overview

This document explains how ESPN's wildcard URL system works for college football and how to systematically scrape all available data.

---

## 1. Understanding Wildcards

The `*` symbol in URLs represents a **wildcard** that must be replaced with specific identifiers:

### Team ID Wildcards
- **Pattern**: `/college-football/team/_/id/*`
- **Wildcard**: Team ID (numeric)
- **Example**: `/college-football/team/_/id/228` (Clemson Tigers)

### Game ID Wildcards
- **Pattern**: `/college-football/game/_/gameId/*`
- **Wildcard**: Game ID (numeric)
- **Example**: `/college-football/game/_/gameId/401754577`

---

## 2. All Wildcard URL Patterns

### 2.1 Team-Based Wildcards

#### Team Homepage
```
https://www.espn.com/college-football/team/_/id/*
```
**Replace `*` with**: Team ID (e.g., 228, 103, 59)

**Examples**:
- Clemson: `https://www.espn.com/college-football/team/_/id/228/clemson-tigers`
- Alabama: `https://www.espn.com/college-football/team/_/id/333/alabama-crimson-tide`
- Ohio State: `https://www.espn.com/college-football/team/_/id/194/ohio-state-buckeyes`

**Data Available**:
- Latest team news
- Recent game results
- Upcoming schedule
- Team leaders
- Quick stats

---

#### Team Statistics
```
https://www.espn.com/college-football/team/stats/_/id/*
```
**Replace `*` with**: Team ID

**Examples**:
- Georgia Tech: `https://www.espn.com/college-football/team/stats/_/id/59`
- Michigan: `https://www.espn.com/college-football/team/stats/_/id/130`

**Data Available**:
- Offensive statistics (yards, points, etc.)
- Defensive statistics
- Per-game averages
- Season totals
- Situational stats (3rd down, red zone)

---

#### Team Statistics by Type
```
https://www.espn.com/college-football/team/stats/_/type/team/id/*
```
**Replace `*` with**: Team ID

**Examples**:
- Texas: `https://www.espn.com/college-football/team/stats/_/type/team/id/251`

**Data Available**:
- Detailed team-level statistics
- Advanced metrics
- Split stats (home/away, conference/non-conference)

---

#### Team Roster
```
https://www.espn.com/college-football/team/roster/_/id/*
```
**Replace `*` with**: Team ID

**Examples**:
- Notre Dame: `https://www.espn.com/college-football/team/roster/_/id/87`
- USC: `https://www.espn.com/college-football/team/roster/_/id/30`

**Data Available**:
- Complete player roster
- Player names, numbers, positions
- Height, weight, class year
- Hometown information
- Player profile links

---

### 2.2 Game-Based Wildcards

#### Game Details
```
https://www.espn.com/college-football/game/_/gameId/*
```
**Replace `*` with**: Game ID (e.g., 401754577)

**Examples**:
- Duke vs Clemson: `https://www.espn.com/college-football/game/_/gameId/401754577/duke-clemson`

**Data Available**:
- Live/final score
- Play-by-play
- Box score
- Team statistics comparison
- Player statistics
- Scoring summary
- Game flow chart
- Win probability graph
- Drive summaries
- Injuries
- Weather conditions
- Odds/betting lines

---

## 3. How to Get IDs

### 3.1 Getting All Team IDs

**Method 1: Scrape the Teams Page**
```
URL: https://www.espn.com/college-football/teams
```

All team links follow this pattern:
```
/college-football/team/_/id/[TEAM_ID]/[team-name-slug]
```

Extract the numeric ID from each team link.

**Method 2: Use the Provided Team List**

See `ESPN_CFB_DATA_ANALYSIS.md` for the complete list of all 136 FBS team IDs organized by conference.

---

### 3.2 Getting Game IDs

**Method 1: Scrape the Schedule Page**
```
URL: https://www.espn.com/college-football/schedule
```

Game links follow this pattern:
```
/college-football/game/_/gameId/[GAME_ID]/[team1-team2]
```

**Method 2: Scrape the Scoreboard**
```
URL: https://www.espn.com/college-football/scoreboard
```

Similar game link structure.

**Method 3: From Team Schedules**

Each team's page includes their schedule with game IDs.

---

## 4. Systematic Crawling Strategy

### Step 1: Collect Team IDs
```python
# Pseudo-code
teams_page = fetch("https://www.espn.com/college-football/teams")
team_ids = extract_team_ids(teams_page)  # Returns list of 136 team IDs
```

### Step 2: Iterate Through Teams
```python
for team_id in team_ids:
    # Get team stats
    stats_url = f"https://www.espn.com/college-football/team/stats/_/id/{team_id}"
    stats = fetch_and_parse(stats_url)
    
    # Get team roster
    roster_url = f"https://www.espn.com/college-football/team/roster/_/id/{team_id}"
    roster = fetch_and_parse(roster_url)
    
    # Get team schedule (contains game IDs)
    team_url = f"https://www.espn.com/college-football/team/_/id/{team_id}"
    schedule = fetch_and_parse(team_url)
    
    # Store data
    save_team_data(team_id, stats, roster, schedule)
```

### Step 3: Collect Game IDs
```python
# From schedule page
schedule_page = fetch("https://www.espn.com/college-football/schedule")
game_ids = extract_game_ids(schedule_page)
```

### Step 4: Iterate Through Games
```python
for game_id in game_ids:
    game_url = f"https://www.espn.com/college-football/game/_/gameId/{game_id}"
    game_data = fetch_and_parse(game_url)
    
    # Extract relevant data
    game_details = {
        "game_id": game_id,
        "score": extract_score(game_data),
        "stats": extract_stats(game_data),
        "odds": extract_odds(game_data),
        "weather": extract_weather(game_data)
    }
    
    save_game_data(game_id, game_details)
```

---

## 5. Complete URL Expansion Examples

### Example: Scraping All SEC Teams

```python
sec_team_ids = [333, 8, 2, 57, 61, 96, 99, 344, 142, 201, 145, 2579, 2633, 245, 251, 238]

for team_id in sec_team_ids:
    # Team overview
    f"https://www.espn.com/college-football/team/_/id/{team_id}"
    
    # Team stats
    f"https://www.espn.com/college-football/team/stats/_/id/{team_id}"
    
    # Team roster
    f"https://www.espn.com/college-football/team/roster/_/id/{team_id}"
```

**Expands to**:
- Alabama (333):
  - `https://www.espn.com/college-football/team/_/id/333`
  - `https://www.espn.com/college-football/team/stats/_/id/333`
  - `https://www.espn.com/college-football/team/roster/_/id/333`
- Arkansas (8):
  - `https://www.espn.com/college-football/team/_/id/8`
  - `https://www.espn.com/college-football/team/stats/_/id/8`
  - `https://www.espn.com/college-football/team/roster/_/id/8`
- ... (continues for all 16 SEC teams)

---

### Example: Scraping This Week's Games

```python
# Get current week's game IDs
scoreboard = fetch("https://www.espn.com/college-football/scoreboard")
current_game_ids = extract_game_ids(scoreboard)  # e.g., [401754577, 401752758, ...]

for game_id in current_game_ids:
    game_url = f"https://www.espn.com/college-football/game/_/gameId/{game_id}"
    # Scrape game data
```

**Expands to**:
- Game 401754577: `https://www.espn.com/college-football/game/_/gameId/401754577`
- Game 401752758: `https://www.espn.com/college-football/game/_/gameId/401752758`
- ... (continues for all games this week)

---

## 6. Using the Provided Scraper

### Installation
```bash
# Install dependencies
pip install -r requirements_espn_scraper.txt

# Install Playwright browsers
playwright install chromium
```

### Basic Usage
```bash
# Run the scraper (limited to 5 teams for testing)
python scripts/espn_cfb_scraper.py
```

### Configuration Options

**Scrape All Teams**:
```python
# In espn_cfb_scraper.py, modify main():
await scraper.run_full_scrape(
    scrape_teams=True,
    teams_limit=None  # None = all 136 teams
)
```

**Scrape Only Main Pages (No Teams)**:
```python
await scraper.run_full_scrape(
    scrape_teams=False  # Skip individual team scraping
)
```

**Scrape First 10 Teams**:
```python
await scraper.run_full_scrape(
    scrape_teams=True,
    teams_limit=10
)
```

---

## 7. Data Output Structure

The scraper saves data in organized directories:

```
data/espn_cfb/
├── teams_list.json              # All 136 team IDs and metadata
├── schedule.json                # Current season schedule
├── fpi_data.json               # FPI ratings
├── teams/
│   ├── team_228_roster.json    # Clemson roster
│   ├── team_333_roster.json    # Alabama roster
│   └── ...
├── stats/
│   ├── team_228_stats.json     # Clemson stats
│   ├── team_333_stats.json     # Alabama stats
│   └── ...
├── games/
│   ├── game_401754577.json     # Individual game data
│   └── ...
├── odds/
│   ├── odds_20251101_120000.json  # Odds snapshot
│   └── ...
└── rankings/
    ├── rankings_20251101.json  # Daily rankings
    └── ...
```

---

## 8. Recursive Link Discovery

For truly comprehensive coverage, implement recursive link discovery:

```python
def discover_all_links(base_url, visited=set()):
    """
    Recursively discover all ESPN CFB links
    """
    if base_url in visited:
        return []
    
    visited.add(base_url)
    page = fetch(base_url)
    links = extract_all_links(page)
    
    cfb_links = [link for link in links if '/college-football/' in link]
    
    all_links = [base_url]
    for link in cfb_links:
        all_links.extend(discover_all_links(link, visited))
    
    return all_links
```

---

## 9. Key Data Points for Betting Analysis

### From Team Pages:
- **Offensive efficiency**: Points per game, yards per play
- **Defensive efficiency**: Points allowed, yards allowed
- **Turnover margins**: Critical for outcomes
- **Special teams**: Field goal %, punt coverage
- **Roster depth**: Injury impacts

### From Game Pages:
- **Historical matchups**: Head-to-head trends
- **Weather conditions**: Impacts on totals
- **Betting lines**: Spread, moneyline, total
- **Line movement**: Sharp vs public money
- **Injuries**: Key player availability

### From Rankings/Ratings:
- **SP+ ratings**: Predictive power
- **FPI scores**: Win probabilities
- **Strength of schedule**: Context for records

---

## 10. Best Practices

### 10.1 Respectful Crawling
- Add delays between requests (1-2 seconds)
- Use appropriate User-Agent headers
- Respect robots.txt
- Don't overwhelm servers

### 10.2 Error Handling
- Handle network timeouts gracefully
- Retry failed requests (with backoff)
- Log all errors for debugging
- Validate data after scraping

### 10.3 Data Validation
- Check for missing fields
- Verify team IDs match across pages
- Ensure data types are correct
- Cross-reference with multiple sources

### 10.4 Update Schedule
- **Daily**: Odds, injuries, news
- **Weekly**: Stats, rankings, schedules
- **Seasonal**: Rosters, team info
- **Real-time**: Game scores (if needed)

---

## 11. Summary of All Wildcard Patterns

| URL Pattern | Wildcard Type | Example ID | What It Represents |
|-------------|---------------|------------|-------------------|
| `/team/_/id/*` | Team ID | 228 | Clemson Tigers |
| `/team/stats/_/id/*` | Team ID | 333 | Alabama stats |
| `/team/stats/_/type/team/id/*` | Team ID | 59 | GT advanced stats |
| `/team/roster/_/id/*` | Team ID | 130 | Michigan roster |
| `/game/_/gameId/*` | Game ID | 401754577 | Duke vs Clemson |

---

## 12. Quick Reference: Finding IDs

### Team IDs
```bash
# Scrape from teams page
curl https://www.espn.com/college-football/teams | grep -o 'id/[0-9]*' | sort -u
```

### Game IDs
```bash
# Scrape from scoreboard
curl https://www.espn.com/college-football/scoreboard | grep -o 'gameId/[0-9]*' | sort -u
```

---

## Conclusion

ESPN's wildcard URL system allows systematic access to all 136 FBS teams and thousands of games. By:

1. **Collecting team IDs** from the teams page
2. **Collecting game IDs** from schedule/scoreboard pages
3. **Substituting wildcards** with collected IDs
4. **Scraping systematically** with proper delays

You can build a comprehensive database of college football data for betting analysis.

The provided scraper (`scripts/espn_cfb_scraper.py`) implements this strategy and can be customized for your specific needs.

---

**Total URLs to Scrape**:
- **136 teams** × 3 pages = 408 team pages
- **Hundreds of games** per season
- **10+ main pages** (rankings, odds, etc.)
- **Total**: 500+ unique URLs

**With wildcards expanded**: Understanding the wildcard system lets you access ALL available data systematically.

