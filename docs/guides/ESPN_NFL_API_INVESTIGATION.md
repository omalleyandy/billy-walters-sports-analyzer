# ESPN.com and NFL.com API Investigation Report

**Date:** November 9, 2025
**Objective:** Investigate how ESPN.com and NFL.com deliver live game data, stats, schedules, and injury reports to determine optimal scraping approaches.

---

## Executive Summary

### ESPN.com
- **Protocol:** REST API (JSON)
- **Authentication:** None required (public endpoints)
- **Data Delivery:** Real-time REST API endpoints with comprehensive sports data
- **WebSocket:** Not detected for live scores
- **Recommendation:** Use direct REST API calls - highly reliable and well-structured

### NFL.com
- **Protocol:** Historically used JSON feeds, now mostly server-side rendered HTML
- **Authentication:** Official API requires NFL partnership
- **Data Delivery:** Mix of server-side rendering and protected API endpoints
- **Recommendation:** Use ESPN API instead - NFL.com endpoints are either deprecated or restricted

---

## ESPN API - Comprehensive Analysis

### 1. Core API Structure

ESPN provides an extensive "hidden" (undocumented but public) REST API with consistent patterns across all sports.

#### Base URLs

```
Primary Site API:
https://site.api.espn.com/apis/site/v2/sports/football/[league]/[resource]

Core Sports API:
https://sports.core.api.espn.com/v2/sports/football/leagues/[league]/[resource]

Web API:
https://site.web.api.espn.com/apis/[version]/sports/football/[league]/[resource]
```

#### Supported Leagues
- `nfl` - National Football League
- `college-football` - NCAA Football (all divisions)

---

### 2. NFL API Endpoints

#### Scoreboard & Live Games

**Current Week Scoreboard:**
```
GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
```

**Query Parameters:**
- `dates=YYYYMMDD` - Filter by specific date
- `week=N` - Filter by week number (1-18 for regular season)
- `seasontype=2` - Season type (1=preseason, 2=regular, 3=postseason)
- `limit=N` - Limit number of results

**Response Structure:**
```json
{
  "leagues": [...],
  "season": {"year": 2025, "type": 2},
  "week": {"number": 10},
  "events": [
    {
      "id": "401671820",
      "uid": "s:20~l:28~e:401671820",
      "date": "2025-11-09T18:00Z",
      "name": "Indianapolis Colts at Tennessee Titans",
      "shortName": "IND @ TEN",
      "competitions": [{
        "id": "401671820",
        "status": {
          "clock": 0.0,
          "displayClock": "0:00",
          "period": 4,
          "type": {
            "id": "3",
            "name": "STATUS_FINAL",
            "state": "post",
            "completed": true
          }
        },
        "competitors": [
          {
            "id": "10",
            "team": {...},
            "score": "20",
            "homeAway": "away",
            "records": [
              {"name": "overall", "summary": "4-5"}
            ],
            "leaders": [
              {
                "name": "passingYards",
                "displayName": "Passing Leader",
                "athlete": {...},
                "value": "189"
              }
            ]
          }
        ],
        "odds": [{
          "provider": {...},
          "details": "IND -2.5",
          "overUnder": 43.5
        }]
      }]
    }
  ]
}
```

**Available Data:**
- Game ID, date, time, venue
- Teams with logos, colors, abbreviations
- Live scores and game status
- Period/quarter information
- Statistical leaders (passing, rushing, receiving)
- Team records (overall, home, away, conference)
- Betting odds (spread, over/under, moneyline)
- Broadcast information
- Weather conditions
- Attendance

---

#### Game Summary & Details

**Game Summary:**
```
GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={EVENT_ID}
```

**Response Includes:**
- Complete box score
- Team statistics (total yards, passing, rushing, turnovers, possession time)
- Play-by-play drives
- Scoring plays with timestamps
- Game leaders
- Team records and standings

---

#### Teams

**All Teams:**
```
GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams
```

**Response:**
- All 32 NFL teams
- Team IDs, abbreviations, locations
- Logos (multiple formats)
- Primary/alternate colors
- Links to roster, schedule, stats, depth chart

**Specific Team:**
```
GET https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{YEAR}/teams/{TEAM_ID}
```

---

#### Schedule

**Full Season Schedule:**
```
GET https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{YEAR}/types/{TYPE}/weeks/{WEEK}/events?limit=1000
```

**Parameters:**
- `{YEAR}` - Season year (e.g., 2025)
- `{TYPE}` - 1=preseason, 2=regular season, 3=postseason
- `{WEEK}` - Week number

**Response:**
- Event references for all games in specified week
- Each reference: `$ref: "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{EVENT_ID}"`

---

#### Injuries

**Team Injury Report:**
```
GET https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/teams/{TEAM_ID}/injuries
```

**Response Structure:**
- Paginated list of injury references
- Each reference: `http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{YEAR}/athletes/{ATHLETE_ID}/injuries/{INJURY_ID}`

**Note:** Response provides references only. Full injury details require following each `$ref` link.

**Alternative - News Feed:**
```
GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/news
```
- Contains injury updates in news articles
- Includes player names, injury types, statuses
- More human-readable but less structured

---

#### Players/Athletes

**All Active Players:**
```
GET https://sports.core.api.espn.com/v3/sports/football/nfl/athletes?limit=20000&active=true
```

**Player Game Log:**
```
GET https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{ATHLETE_ID}/gamelog
```

**Player Statistics:**
```
GET https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{YEAR}/athletes/{ATHLETE_ID}/statistics
```

---

#### Odds & Betting

**Current Odds:**
```
GET https://site.web.api.espn.com/apis/v3/sports/football/nfl/odds
```

**Event Probabilities:**
```
GET https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{EVENT_ID}/competitions/{EVENT_ID}/probabilities
```

**Response:**
- Win probabilities
- Live win percentage updates
- Historical probability trends

---

### 3. NCAAF (College Football) API Endpoints

**Structure:** Nearly identical to NFL endpoints, replace `/nfl/` with `/college-football/`

**Scoreboard:**
```
GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard
```

**Key Differences from NFL:**
- `conferenceId` field for conference tracking
- `curatedRank.current` for team rankings (AP Poll, Coaches Poll)
- Conference-specific records ("vs. Conf.")
- Bowl game handling
- Different calendar structure (bowl season, CFP)

**Teams:**
```
GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams
```
- Returns 75+ major college football programs
- Includes FBS, FCS, and other divisions

**Week Events:**
```
GET https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/2025/types/2/weeks/11/events?limit=100
```

---

### 4. ESPN API Patterns & Best Practices

#### Data Structure
- **Hierarchical:** Sports → Leagues → Teams/Events → Competitions
- **RESTful:** Standard HTTP methods, resource-based URLs
- **Paginated:** Large datasets use `pageIndex`, `pageCount`, `count`
- **Reference-based:** Core API uses `$ref` links for nested resources

#### Rate Limiting
- No documented rate limits
- No API keys required
- Recommended: Implement client-side throttling (1-2 requests/second)

#### Caching
- Data updated every 15 seconds for live games
- Pregame data relatively static
- Implement local caching for teams, schedules

#### Error Handling
- Standard HTTP status codes
- 200: Success
- 404: Resource not found
- 401: Authentication required (for protected endpoints)
- 500: Server error

---

## NFL.com API - Analysis

### Historical Endpoints (Deprecated/Restricted)

#### Game Center JSON (Legacy)
```
http://www.nfl.com/liveupdate/game-center/{GAME_ID}/{GAME_ID}_gtd.json
```

**Game ID Format:** `YYYYMMDDNN`
- `YYYY` = Year
- `MM` = Month
- `DD` = Day
- `NN` = Game sequence number

**Status:** These endpoints appear to be deprecated or moved behind authentication as of 2018.

#### Scorestrip XML (Legacy)
```
Regular Season:
http://www.nfl.com/liveupdate/scorestrip/ss.xml

Postseason:
http://www.nfl.com/liveupdate/scorestrip/postseason/ss.xml
```

**Status:** No longer accessible via direct HTTP requests.

#### Fantasy API (Restricted)
```
http://api.fantasy.nfl.com/v1/players/stats?statType=seasonStats&season=2024&week=10&format=json
```

**Status:** Returns 404. Access restricted to NFL partners.

---

### Current NFL.com Architecture

**Data Delivery Method:**
- Server-side rendered HTML
- JavaScript-based dynamic content loading
- Protected API endpoints requiring authentication

**Observed Patterns:**
- `api.nfl.com/v3/shield/` - Requires 401 authentication
- Client-side framework: `p.nfltags.com` library
- No publicly accessible JSON feeds found

**Injury Reports:**
- Delivered as static HTML tables
- Server-side rendered
- Week-specific URLs: `/injuries/`
- Requires HTML parsing (not JSON)

---

## Recommendations

### For Billy Walters Sports Analyzer

#### Primary Data Source: ESPN API

**Why ESPN:**
1. **No Authentication:** Publicly accessible endpoints
2. **Comprehensive Data:** All required data types available
3. **Well-Structured:** Consistent JSON schemas
4. **Real-Time:** Live updates during games (15-second intervals)
5. **Stable:** Well-established, reverse-engineered by community
6. **Multi-Sport:** Same pattern for NFL and NCAAF

**Implementation Strategy:**

```python
# Base scraper structure
import httpx
from typing import Dict, List, Any
import asyncio

class ESPNScraper:
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_scoreboard(
        self,
        league: str = "nfl",
        week: int = None,
        season_type: int = 2
    ) -> Dict[str, Any]:
        """Get current scoreboard for specified league."""
        url = f"{self.BASE_URL}/{league}/scoreboard"
        params = {}
        if week:
            params["week"] = week
        if season_type:
            params["seasontype"] = season_type

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_team_injuries(
        self,
        league: str = "nfl",
        team_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get injury reports for team."""
        url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/{league}/teams/{team_id}/injuries"
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()

        # Follow $ref links to get full injury details
        injuries = []
        for item in data.get("items", []):
            injury_url = item.get("$ref")
            if injury_url:
                injury_response = await self.client.get(injury_url)
                injuries.append(injury_response.json())

        return injuries

    async def get_game_summary(
        self,
        league: str = "nfl",
        event_id: str = None
    ) -> Dict[str, Any]:
        """Get detailed game summary."""
        url = f"{self.BASE_URL}/{league}/summary"
        params = {"event": event_id}

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
```

---

#### Integration Points

**1. Live Scores & Schedules**
```python
# Get current week scoreboard
scoreboard = await scraper.get_scoreboard(league="nfl")

for event in scoreboard["events"]:
    game_id = event["id"]
    status = event["competitions"][0]["status"]["type"]["name"]

    if status in ["STATUS_IN_PROGRESS", "STATUS_HALFTIME"]:
        # Game is live - fetch detailed stats
        summary = await scraper.get_game_summary(
            league="nfl",
            event_id=game_id
        )
```

**2. Team Statistics**
```python
# Get all NFL teams
teams = await scraper.get_teams(league="nfl")

for team in teams["sports"][0]["leagues"][0]["teams"]:
    team_id = team["team"]["id"]

    # Get team injuries
    injuries = await scraper.get_team_injuries(
        league="nfl",
        team_id=team_id
    )
```

**3. Odds Integration**
```python
# Scoreboard includes odds
scoreboard = await scraper.get_scoreboard(league="nfl")

for event in scoreboard["events"]:
    competition = event["competitions"][0]
    odds = competition.get("odds", [])

    for odd in odds:
        provider = odd["provider"]["name"]  # e.g., "ESPN BET"
        spread = odd["details"]  # e.g., "IND -2.5"
        over_under = odd.get("overUnder")  # e.g., 43.5
```

**4. Injury Reports**

*Option A: Structured API (requires following refs)*
```python
injuries = await scraper.get_team_injuries(league="nfl", team_id=10)
```

*Option B: News Feed (easier, less structured)*
```python
news = await scraper.get_news(league="nfl")

injury_articles = [
    article for article in news["articles"]
    if "injury" in article["headline"].lower()
]
```

---

### Avoiding NFL.com Complexity

**Don't Use NFL.com For:**
- Live scores (use ESPN)
- Team statistics (use ESPN)
- Player data (use ESPN)
- Schedules (use ESPN)

**Consider NFL.com Only For:**
- Official injury reports HTML (if ESPN data insufficient)
- Requires HTML parsing with BeautifulSoup
- Example:
```python
from bs4 import BeautifulSoup
import httpx

async def scrape_nfl_injuries(week: int = None):
    url = "https://www.nfl.com/injuries/"
    if week:
        url = f"{url}?week={week}"

    response = await httpx.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Parse injury tables
    injury_tables = soup.find_all("table", class_="injury-table")
    # ... parse HTML structure
```

**Drawbacks:**
- Requires HTML parsing (fragile)
- Server-side rendered (slower)
- No structured JSON
- Subject to layout changes

---

## WebSocket Analysis

### ESPN
**Finding:** No WebSocket connections detected for live score updates.

**Mechanism:** ESPN uses polling-based updates with REST API calls approximately every 15 seconds during live games.

**Implementation:**
```python
async def monitor_live_game(event_id: str, interval: int = 15):
    """Poll game summary for live updates."""
    while True:
        summary = await scraper.get_game_summary(
            league="nfl",
            event_id=event_id
        )

        status = summary["header"]["competitions"][0]["status"]["type"]["name"]

        if status == "STATUS_FINAL":
            break

        await asyncio.sleep(interval)
```

### NFL.com
**Finding:** No WebSocket connections publicly accessible.

**Note:** NFL.com may use WebSockets internally behind authentication, but they are not available for public access.

---

## Comparison to overtime.ag SignalR

**overtime.ag Approach:**
- Uses SignalR (WebSocket-based)
- Real-time push updates
- Requires connection negotiation
- More complex implementation

**ESPN Approach:**
- REST API with polling
- 15-second update intervals
- Simple HTTP requests
- No connection management

**Recommendation:**
- ESPN's REST approach is simpler and sufficient for sports betting analysis
- 15-second latency is acceptable for pre-game and in-game analysis
- No need for WebSocket complexity

---

## API Endpoint Reference

### ESPN - NFL Quick Reference

| Resource | Endpoint | Description |
|----------|----------|-------------|
| Scoreboard | `/apis/site/v2/sports/football/nfl/scoreboard` | Current week scores |
| Teams | `/apis/site/v2/sports/football/nfl/teams` | All NFL teams |
| Game Summary | `/apis/site/v2/sports/football/nfl/summary?event={ID}` | Detailed game data |
| News | `/apis/site/v2/sports/football/nfl/news` | NFL news feed |
| Injuries | `/v2/sports/football/leagues/nfl/teams/{ID}/injuries` | Team injury reports |
| Odds | `/apis/v3/sports/football/nfl/odds` | Current betting odds |
| Players | `/v3/sports/football/nfl/athletes?limit=20000&active=true` | All active players |

### ESPN - NCAAF Quick Reference

| Resource | Endpoint | Description |
|----------|----------|-------------|
| Scoreboard | `/apis/site/v2/sports/football/college-football/scoreboard` | Current week scores |
| Teams | `/apis/site/v2/sports/football/college-football/teams` | All college teams |
| Game Summary | `/apis/site/v2/sports/football/college-football/summary?event={ID}` | Detailed game data |
| News | `/apis/site/v2/sports/football/college-football/news` | NCAAF news feed |

---

## Sample Data Structures

### Scoreboard Event
```json
{
  "id": "401671820",
  "date": "2025-11-09T18:00Z",
  "name": "Indianapolis Colts at Tennessee Titans",
  "shortName": "IND @ TEN",
  "competitions": [{
    "status": {
      "period": 4,
      "type": {"name": "STATUS_FINAL", "completed": true}
    },
    "competitors": [
      {
        "team": {"id": "10", "abbreviation": "IND"},
        "score": "20",
        "homeAway": "away",
        "records": [{"name": "overall", "summary": "4-5"}],
        "leaders": [
          {"name": "passingYards", "value": "189"}
        ]
      }
    ],
    "odds": [{
      "details": "IND -2.5",
      "overUnder": 43.5
    }]
  }]
}
```

### Team Object
```json
{
  "id": "10",
  "uid": "s:20~l:28~t:10",
  "slug": "indianapolis-colts",
  "location": "Indianapolis",
  "name": "Colts",
  "abbreviation": "IND",
  "displayName": "Indianapolis Colts",
  "color": "003b7b",
  "alternateColor": "ffffff",
  "logos": [
    {
      "href": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png",
      "width": 500,
      "height": 500
    }
  ],
  "links": [
    {"rel": ["clubhouse"], "href": "https://www.espn.com/nfl/team/_/name/ind"},
    {"rel": ["roster"], "href": "https://www.espn.com/nfl/team/roster/_/name/ind"},
    {"rel": ["stats"], "href": "https://www.espn.com/nfl/team/stats/_/name/ind"},
    {"rel": ["schedule"], "href": "https://www.espn.com/nfl/team/schedule/_/name/ind"}
  ]
}
```

---

## Implementation Checklist

- [ ] Create `ESPNScraper` class in `walters_analyzer/scrapers/espn.py`
- [ ] Implement async HTTP client with httpx
- [ ] Add scoreboard fetching (NFL & NCAAF)
- [ ] Add team data fetching
- [ ] Add injury report fetching (with ref following)
- [ ] Add game summary fetching
- [ ] Add odds fetching
- [ ] Implement rate limiting (1-2 req/sec)
- [ ] Add response caching layer
- [ ] Create data models with Pydantic
- [ ] Add error handling and retries
- [ ] Write unit tests with pytest
- [ ] Add integration tests
- [ ] Document API usage in project docs
- [ ] Update environment variables if needed
- [ ] Create example usage scripts

---

## Conclusion

**ESPN API is the clear winner for this project:**

✅ **Advantages:**
- No authentication required
- Comprehensive data coverage
- Well-structured JSON responses
- Real-time updates (15-second intervals)
- Stable and widely used
- Supports both NFL and NCAAF
- Simple REST implementation

❌ **NFL.com Limitations:**
- Official API requires partnership
- Public endpoints deprecated
- Server-side HTML rendering
- Requires complex parsing
- Less reliable

**Next Steps:**
1. Implement ESPN scraper module
2. Replace or supplement existing data sources with ESPN API
3. Add ESPN data to unified betting system
4. Integrate with existing power ratings and edge detection
5. Monitor API stability and adjust as needed

---

**Documentation References:**
- ESPN Hidden API Gist: https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c
- ESPN API Documentation: https://gist.github.com/akeaswaran/b48b02f1c94f873c6655e7129910fc3b
- Community Resources: Stack Overflow, GitHub discussions

**Last Updated:** November 9, 2025
