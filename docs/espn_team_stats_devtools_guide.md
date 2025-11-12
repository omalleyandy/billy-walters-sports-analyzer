# ESPN NCAAF Team Stats - Chrome DevTools Investigation Guide

**Date**: 2025-11-12
**Objective**: Reverse engineer ESPN's API endpoints for NCAA College Football team statistics to integrate into Billy Walters power ratings

---

## Investigation Steps

### 1. Open Chrome DevTools

```bash
# Navigate to ESPN NCAAF teams page
https://www.espn.com/college-football/teams

# Open DevTools: F12 or Ctrl+Shift+I (Windows) or Cmd+Option+I (Mac)
# Go to Network tab
# Check "Preserve log" to keep requests after page navigation
```

### 2. Filter Network Requests

**What to look for:**
- API calls to `api.espn.com` or `site.api.espn.com`
- JSON responses containing team statistics
- XHR/Fetch requests (filter by type)

**Common ESPN API patterns:**
- `https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams`
- `https://sports.core.api.espn.com/v2/sports/football/leagues/college-football`
- Team-specific stats: `/teams/{team_id}/statistics`

### 3. Click on a Team (e.g., Ohio State)

When you click on a specific team, watch the Network tab for:
- Team roster API calls
- Team statistics API calls
- Season stats endpoints
- Game-by-game stats

**Expected endpoints:**
```
GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}
GET https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{year}/teams/{team_id}/statistics
```

### 4. Analyze the Response Structure

**Key data points for power ratings:**

**Offensive Stats:**
- Total yards per game
- Points per game
- Passing yards per game
- Rushing yards per game
- Red zone efficiency
- Third down conversion %
- Turnovers

**Defensive Stats:**
- Points allowed per game
- Total yards allowed per game
- Passing yards allowed
- Rushing yards allowed
- Sacks
- Turnovers forced
- Red zone defense

**Special Teams:**
- Field goal %
- Punt return average
- Kick return average

**Advanced Metrics:**
- Yards per play (offense)
- Yards per play allowed (defense)
- Turnover margin
- Time of possession

### 5. Document the API Call

For each relevant endpoint, document:

**Request Details:**
```
Method: GET
URL: [full URL]
Headers: [required headers]
Query Params: [any parameters]
Authentication: [none expected for public ESPN APIs]
```

**Response Structure:**
```json
{
  "team": {
    "id": "...",
    "displayName": "...",
    "abbreviation": "..."
  },
  "statistics": {
    "splits": {
      "categories": [
        {
          "name": "passing",
          "stats": [...]
        },
        {
          "name": "rushing",
          "stats": [...]
        }
      ]
    }
  }
}
```

### 6. Test the API Endpoint

Once you find a promising endpoint:

1. **Copy as cURL**: Right-click the request → Copy → Copy as cURL
2. **Test in PowerShell**: Convert cURL to Python/requests
3. **Verify data quality**: Check if stats are current and complete

**Example test script:**
```python
import requests

team_id = "194"  # Ohio State
url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers, timeout=30)
print(response.status_code)
print(response.json())
```

---

## Data Points to Extract

### For Billy Walters Power Ratings

**Priority 1 (Core Metrics):**
- [ ] Points per game (offensive efficiency)
- [ ] Points allowed per game (defensive efficiency)
- [ ] Yards per play (offensive effectiveness)
- [ ] Yards per play allowed (defensive effectiveness)
- [ ] Turnover margin (critical for power ratings)

**Priority 2 (Advanced Metrics):**
- [ ] Third down conversion % (situational success)
- [ ] Red zone scoring % (finishing drives)
- [ ] Sacks (pass rush effectiveness)
- [ ] Time of possession (game control)

**Priority 3 (Special Teams):**
- [ ] Field goal accuracy
- [ ] Net punting average
- [ ] Kick/punt return averages

---

## Expected API Endpoints

Based on existing ESPN API structure, likely endpoints:

### Team List
```
GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams
Returns: All NCAAF teams with basic info
```

### Team Statistics (Season)
```
GET https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{year}/teams/{team_id}/statistics
Returns: Complete season statistics for team
```

### Team Statistics (Split by Category)
```
GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/statistics
Returns: Offensive, defensive, special teams stats
```

### Team Schedule/Results
```
GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/schedule
Returns: Game-by-game results with scores
```

---

## Investigation Checklist

- [ ] Identified team statistics API endpoint
- [ ] Documented request/response structure
- [ ] Tested endpoint with sample team IDs
- [ ] Verified data is current (2025 season)
- [ ] Confirmed no authentication required
- [ ] Extracted key metrics for power ratings
- [ ] Documented rate limits (if any)
- [ ] Created sample data file for testing

---

## Next Steps

1. **Document findings** in `docs/espn_team_stats_devtools_analysis_results.md`
2. **Extend ESPN client** with `get_team_statistics()` method
3. **Create extraction script** to collect stats for all NCAAF teams
4. **Integrate into power ratings** calculation in Billy Walters methodology
5. **Test with real data** from current season

---

## Billy Walters Integration Plan

Once we have team statistics, integrate into power ratings:

**Current Power Rating Formula:**
```
Power Rating = 90% * Previous Rating + 10% * Massey Composite
```

**Enhanced Formula with Team Stats:**
```
Power Rating = Base Rating + Offensive Adjustment + Defensive Adjustment + Special Teams

Where:
- Base Rating: Massey Composite (existing)
- Offensive Adjustment: Points per game vs league average
- Defensive Adjustment: Points allowed vs league average
- Special Teams: Turnover margin impact
```

**Example Calculation:**
```python
def calculate_power_rating_with_stats(team_id: str) -> float:
    # Get Massey rating (base)
    massey_rating = get_massey_rating(team_id)

    # Get team stats
    stats = espn_client.get_team_statistics(team_id, league="college-football")

    # Calculate adjustments
    offensive_adj = (stats.points_per_game - league_avg_points) * 0.1
    defensive_adj = (league_avg_points_allowed - stats.points_allowed) * 0.1
    turnover_adj = stats.turnover_margin * 0.5

    # Final rating
    power_rating = massey_rating + offensive_adj + defensive_adj + turnover_adj

    return power_rating
```

---

## Resources

- **ESPN API Documentation**: Limited public docs, reverse engineering required
- **Existing ESPN Client**: `src/data/espn_api_client.py`
- **Reference Implementation**: `docs/overtime_devtools_analysis_results.md` (Overtime.ag API)
- **Billy Walters Power Ratings**: `src/walters_analyzer/valuation/billy_walters_edge_detector.py`

---

## Notes

- ESPN APIs are public and don't require authentication (same as existing ESPN client)
- Rate limits unknown - implement respectful request delays
- Focus on FBS teams (group 80) for initial implementation
- Consider caching team stats (don't change frequently during week)
- Update stats weekly (Tuesday after games) similar to power ratings workflow

---

**Investigation Date**: 2025-11-12
**Status**: Ready to begin investigation
**Next Action**: Open Chrome DevTools on ESPN NCAAF teams page and document API calls
