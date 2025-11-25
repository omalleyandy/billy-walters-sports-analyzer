# NFL.com API Discovery Session - Live Guide

**Date**: 2025-11-23
**Goal**: Discover real NFL.com API endpoints for schedules, news, and stats
**Method**: Chrome DevTools Network inspection

---

## 🎯 Discovery Mission Checklist

- [ ] Schedule API endpoint
- [ ] News API endpoint
- [ ] Player Stats API endpoint
- [ ] Team Stats API endpoint (bonus)

---

## 📋 Step-by-Step Discovery Process

### Mission 1: Schedule API

**Target URL**: https://www.nfl.com/schedules/2025/REG12

**Steps**:
1. **Open Chrome** (not in incognito - we want normal behavior)

2. **Open DevTools BEFORE navigating**:
   - Press `F12` (or `Ctrl+Shift+I`)
   - Click **Network** tab
   - Check the **Preserve log** checkbox (important!)

3. **Set up filters**:
   - Click **XHR** button (filters to only API calls)
   - OR type `api` in the filter box

4. **Clear the log**:
   - Click the clear button (🚫 circle with slash)

5. **Navigate to the schedule page**:
   - Paste: https://www.nfl.com/schedules/2025/REG12
   - Press Enter
   - **Watch the Network tab fill up!**

6. **Find the schedule API call**:
   - Look for calls with:
     - Domain: `api.nfl.com` or similar
     - Name containing: `schedule`, `games`, `week`, or `2025`
     - Type: `xhr` or `fetch`
     - Size: Large (indicates game data)

7. **Capture the endpoint**:
   - Click on the API call
   - **Headers tab**:
     - Copy the full **Request URL**
     - Note any **Query String Parameters**
   - **Preview tab**:
     - Verify it shows game data
   - **Response tab**:
     - Copy a sample of the JSON

**What to Record**:
```
Endpoint URL: _________________________________
Method: GET / POST
Query Params: _________________________________
Auth Required?: Yes / No
Sample Response: (paste first game object)
```

---

### Mission 2: News API

**Target URL**: https://www.nfl.com/news/

**Steps**:
1. **Keep DevTools open** from previous mission
2. **Clear network log** (🚫 button)
3. **Navigate**: https://www.nfl.com/news/
4. **Look for**:
   - Calls with `news`, `articles`, `content`
   - JSON responses with headlines/summaries
5. **Click on a news article** to see more API calls
6. **Capture the endpoint**

**What to Record**:
```
Endpoint URL: _________________________________
Method: GET / POST
Query Params: _________________________________
Response Structure: (headline, date, author, etc.)
```

---

### Mission 3: Player Stats API

**Target URL**: https://www.nfl.com/stats/player-stats/

**Steps**:
1. **Clear network log**
2. **Navigate**: https://www.nfl.com/stats/player-stats/
3. **Filter to current week**: Use the week dropdown
4. **Look for**:
   - Calls with `stats`, `player`, `leaders`
   - Position filter changes (QB, RB, WR)
5. **Try clicking a player name** to see detail endpoint
6. **Capture both endpoints** (list + detail)

**What to Record**:
```
List Endpoint: _________________________________
Detail Endpoint: _________________________________
Player ID format: _________________________________
```

---

### Mission 4: Team Page (Bonus)

**Target URL**: https://www.nfl.com/teams/kansas-city-chiefs/

**Steps**:
1. **Clear network log**
2. **Navigate to Chiefs page**
3. **Click through tabs**:
   - Roster
   - Stats
   - Schedule
   - News
4. **Watch for API calls** on each tab change
5. **Capture any team-specific endpoints**

---

## 🔍 What Good API Calls Look Like

**Schedule API Example**:
```
URL: https://api.nfl.com/v3/shield/schedule/2025/REG/12
Method: GET
Response: { "games": [...], "week": 12, "season": 2025 }
```

**News API Example**:
```
URL: https://api.nfl.com/v1/rss/news?team=KC&limit=20
Method: GET
Response: { "articles": [...], "total": 20 }
```

**Stats API Example**:
```
URL: https://api.nfl.com/v2/stats/player/12345
Method: GET
Response: { "playerId": "12345", "stats": {...} }
```

---

## 🚨 Troubleshooting

**Problem**: No API calls appear
- **Solution**: Uncheck "Preserve log", refresh page, re-check it

**Problem**: Too many calls, can't find the right one
- **Solution**: Type `api.nfl.com` in filter box to narrow down

**Problem**: API returns 403 Forbidden
- **Solution**: Check if headers needed (Referer, Origin, etc.)

**Problem**: Response is garbled/compressed
- **Solution**: Click "Preview" tab instead of "Response"

---

## 📝 Recording Template

Copy this and fill it in as you discover endpoints:

```markdown
## Schedule API
- URL:
- Method:
- Params:
- Sample Response:

## News API
- URL:
- Method:
- Params:
- Sample Response:

## Player Stats API
- URL:
- Method:
- Params:
- Sample Response:

## Additional Endpoints Found
1.
2.
3.
```

---

## ✅ Success Criteria

You've succeeded when you have:
- [ ] Working schedule endpoint that returns game list
- [ ] Working news endpoint that returns articles
- [ ] Working stats endpoint that returns player data
- [ ] Copied sample JSON responses for each
- [ ] Documented any auth/headers required

---

## 🎯 Next Steps After Discovery

Once you have the endpoints:

1. **Share with me**: Paste the discovered URLs
2. **I'll update**: `src/data/nfl_com_client.py` with real endpoints
3. **We'll test**: Run `test_nfl_com_client.py`
4. **We'll integrate**: Add to `/collect-all-data` workflow

---

## 💡 Pro Tips

1. **Right-click API call** → "Copy as cURL" to get full request
2. **Preview tab** shows formatted JSON (easier to read)
3. **Response tab** shows raw data (for copying)
4. **Headers tab** shows all request details
5. **Timing tab** shows how fast the API is

---

**Ready to start the discovery mission?** 🚀

Open Chrome, press F12, and let's find those endpoints!
