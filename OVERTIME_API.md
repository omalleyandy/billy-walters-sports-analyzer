# Overtime.ag API Documentation

## Overview

This document describes the Overtime.ag API endpoint used for fetching college football and NFL odds data. This API powers the `overtime_api` spider, which is **45x faster** than the browser-based Playwright spider.

## API Endpoint

```
POST https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering
```

## Request Format

### Headers

```http
POST /sports/Api/Offering.asmx/GetSportOffering HTTP/1.1
Host: overtime.ag
Content-Type: application/json
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.9
Cache-Control: no-cache
Origin: https://overtime.ag
Referer: https://overtime.ag/sports
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36
```

### Request Payload

#### College Football
```json
{
  "sportType": "Football",
  "sportSubType": "College Football",
  "wagerType": "Straight Bet",
  "hoursAdjustment": 0,
  "periodNumber": null,
  "gameNum": null,
  "parentGameNum": null,
  "teaserName": "",
  "requestMode": null
}
```

#### NFL
```json
{
  "sportType": "Football",
  "sportSubType": "NFL",
  "wagerType": "Straight Bet",
  "hoursAdjustment": 0,
  "periodNumber": null,
  "gameNum": null,
  "parentGameNum": null,
  "teaserName": "",
  "requestMode": null
}
```

### Parameter Breakdown

| Parameter | Type | Description | Values |
|-----------|------|-------------|--------|
| `sportType` | string | Sport category | "Football", "Basketball", etc. |
| `sportSubType` | string | Specific league | "College Football", "NFL", etc. |
| `wagerType` | string | Type of wager | "Straight Bet", "Parlay", etc. |
| `hoursAdjustment` | int | Time offset for filtering | 0 (all games) |
| `periodNumber` | null/int | Specific period | null (full game) |
| `gameNum` | null/int | Specific game ID | null (all games) |
| `parentGameNum` | null/int | Parent game reference | null |
| `teaserName` | string | Teaser configuration | "" (none) |
| `requestMode` | null/string | Request mode | null |

## Response Format

The API returns data in ASP.NET Web Services format, where the actual data is nested under the `"d"` key.

### Response Structure

```json
{
  "d": {
    "Data": {
      "GameLines": [/* array of game objects */]
    },
    "Code": 0,
    "Message": null,
    "Server": "server-name",
    "IsSuccess": true,
    "AppLastUpdate": "/Date(timestamp)/",
    "SessionExpired": false
  }
}
```

### Game Object Structure

Each game in the `GameLines` array contains:

#### Team Information
```json
{
  "Team1ID": "Kent State",           // Away team
  "Team2ID": "Ball State",           // Home team
  "Team1RotNum": 105,                // Away rotation number
  "Team2RotNum": 106,                // Home rotation number
  "FavoredTeamID": "Ball State"      // Current favorite
}
```

#### Game Timing
```json
{
  "GameNum": 114504200,
  "GameDateTime": "/Date(1762387201000)/",
  "GameDateTimeString": "11/05/2025 19:00",
  "GameDate": "11/05/2025",
  "PeriodWagerCutoff": "/Date(1762387200000)/"
}
```

#### Spread Market
```json
{
  "Spread1": 1.5,                    // Away spread
  "Spread2": -1.5,                   // Home spread
  "SpreadAdj1": -105,                // Away price (juice)
  "SpreadAdj2": -115,                // Home price (juice)
  "BaseSpread1": 1.5,                // Original spread
  "BaseSpread2": -1.5,               // Original spread
  "SpreadChanged": false             // Line movement flag
}
```

#### Total Market
```json
{
  "TotalPoints": 47,                 // Total line
  "TotalPoints1": 47,                // Over line
  "TotalPoints2": 47,                // Under line
  "TtlPtsAdj1": -115,                // Over price
  "TtlPtsAdj2": -105,                // Under price
  "BaseTotalPoints1": 47,            // Original total
  "BaseTotalPoints2": 47,            // Original total
  "TotalPointsChanged": false        // Line movement flag
}
```

#### Moneyline Market
```json
{
  "MoneyLine1": 110,                 // Away moneyline
  "MoneyLine2": -130,                // Home moneyline
  "OrigMoneyLine1": 110,             // Original ML
  "OrigMoneyLine2": -130,            // Original ML
  "MoneyLineChanged": false          // Line movement flag
}
```

#### Team Totals
```json
{
  "Team1TotalPoints": 21.5,          // Away team total
  "Team1TtlPtsAdj1": -120,           // Over price
  "Team1TtlPtsAdj2": -110,           // Under price
  "Team2TotalPoints": 24.5,          // Home team total
  "Team2TtlPtsAdj1": -105,           // Over price
  "Team2TtlPtsAdj2": -125            // Under price
}
```

#### Market Status
```json
{
  "SpreadLineStatus": "O",           // O=Open, C=Closed
  "MoneyLineStatus": "O",
  "TotalsLineStatus": "O",
  "TeamTotalsLineStatus": "O",
  "Status": "O",                     // Overall game status
  "Disabled": false
}
```

#### Metadata
```json
{
  "SportType": "Football",
  "SportSubType": "College Football",
  "SportSubTypeId": 2504,
  "PeriodDescription": "Game",
  "PeriodNumber": 0,
  "Comments": "COLLEGE FOOTBALL Wednesday, November 5th",
  "Team1LogoURL": "Kent_State",
  "Team2LogoURL": "Ball_State",
  "CorrelationID": "Foot-Coll SU Kent Sta@Ball Sta"
}
```

## Data Type Conversions

### Date/Time Parsing

ASP.NET dates use the format: `/Date(1762387201000)/`

This is a Unix timestamp in milliseconds. Convert to Python datetime:

```python
import datetime

def parse_aspnet_date(date_str):
    """Parse /Date(1762387201000)/ format"""
    timestamp = int(date_str.split("(")[1].split(")")[0])
    return datetime.datetime.fromtimestamp(timestamp / 1000)
```

### American Odds

Odds are represented as integers:
- Positive: `+110` means bet $100 to win $110
- Negative: `-130` means bet $130 to win $100

### Line Conventions

The API follows these conventions:
- **Spread**: Positive = underdog, Negative = favorite
- **Total**: No sign (same line for over/under, different prices)
- **Moneyline**: Positive = underdog, Negative = favorite

## Example Response (Abbreviated)

```json
{
  "d": {
    "Data": {
      "GameLines": [
        {
          "GameNum": 114504200,
          "Team1ID": "Kent State",
          "Team2ID": "Ball State",
          "Team1RotNum": 105,
          "Team2RotNum": 106,
          "GameDateTimeString": "11/05/2025 19:00",
          "Spread1": 1.5,
          "Spread2": -1.5,
          "SpreadAdj1": -105,
          "SpreadAdj2": -115,
          "TotalPoints": 47,
          "TtlPtsAdj1": -115,
          "TtlPtsAdj2": -105,
          "MoneyLine1": 110,
          "MoneyLine2": -130,
          "SportSubType": "College Football"
        }
      ]
    },
    "IsSuccess": true
  }
}
```

## Authentication

The API does **not require authentication** for reading odds. Cookies may be used for session management:
- `ASP.NET_SessionId`: Session identifier
- `cf_clearance`: Cloudflare clearance token

However, the spider works fine without these cookies.

## Rate Limiting

No explicit rate limiting was observed during testing. The API responded successfully to:
- Multiple sequential requests
- Requests for different sports

**Recommended Practice:**
- Use AutoThrottle in Scrapy (default: 1 second delay)
- Avoid concurrent requests to the same endpoint
- Be respectful of the API

## SSL/TLS Considerations

The API uses Cloudflare SSL. Some SSL verification issues may occur:

**Issue:** `TLS error: CERTIFICATE_VERIFY_FAILED`

**Solutions:**
1. Use Scrapy's built-in SSL handling (works automatically)
2. For manual requests, use `verify=False` (testing only):
   ```python
   response = requests.post(url, json=payload, verify=False)
   ```

## Error Handling

### Successful Response
```json
{
  "d": {
    "IsSuccess": true,
    "Code": 0,
    "Message": null
  }
}
```

### Error Response
```json
{
  "d": {
    "IsSuccess": false,
    "Code": 1,
    "Message": "Error description"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Parse response |
| 403 | Forbidden | Check headers/cookies |
| 429 | Too Many Requests | Implement backoff |
| 500 | Internal Server Error | Retry |
| 503 | Service Unavailable | Retry with backoff |

## Performance Metrics

Based on testing with 58 College Football games:

| Metric | Value |
|--------|-------|
| **Response Time** | ~2 seconds |
| **Response Size (gzipped)** | ~11 KB |
| **Response Size (uncompressed)** | ~216 KB |
| **Items Scraped** | 58 games |
| **Throughput** | ~1,740 items/minute |

## Comparison: API vs. Playwright

| Aspect | API Spider | Playwright Spider |
|--------|------------|-------------------|
| **Speed** | 2.2 seconds | ~100 seconds |
| **Dependencies** | Requests only | Playwright + Chromium |
| **Reliability** | High | Medium (DOM changes) |
| **Data Completeness** | 100% | 100% |
| **Resource Usage** | Low | High (browser overhead) |
| **Maintenance** | Low | Medium (selector updates) |

## Usage in Spider

See `scrapers/overtime_live/spiders/overtime_api_spider.py` for the complete implementation.

**Key Features:**
- Automatic JSON parsing
- Date/time conversion
- Market structure conversion
- Error handling
- Retry logic

## Future Enhancements

Potential improvements to the API spider:

1. **Live Odds Endpoint**: Discover API endpoint for live betting data
2. **Alternate Lines**: Parse alternate spreads/totals if available
3. **Player Props**: Extract player prop markets
4. **Line Movement Tracking**: Track line changes over time
5. **Multiple Sports**: Extend to Basketball, Baseball, etc.

## Discovery Process

The API endpoint was discovered through:
1. Browser DevTools network capture
2. Identifying the POST request to `GetSportOffering`
3. Analyzing request payload structure
4. Testing different parameter combinations
5. Validating response format

**Key Insight:** Using string-based sport identifiers (`"College Football"`) instead of numeric IDs (`2504`) in the request payload was the breakthrough that made the API work.

## References

- **Overtime.ag**: https://overtime.ag/sports
- **Spider Code**: `scrapers/overtime_live/spiders/overtime_api_spider.py`
- **Test Script**: `test_overtime_api.py`

---

Last Updated: November 5, 2025
