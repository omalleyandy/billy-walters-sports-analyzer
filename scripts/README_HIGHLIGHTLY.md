# Highlightly Data Collection Scripts

PowerShell scripts for automated Highlightly API data collection.

## Overview

These scripts collect data from the Highlightly NFL/NCAA API using **FREE tier endpoints only**. The odds endpoint requires a paid plan, so we use overtime.ag for betting odds instead.

## Scripts

### 1. `highlightly_daily_static.ps1`

Collect static data that doesn't change frequently (run once daily).

**Usage:**
```powershell
.\scripts\highlightly_daily_static.ps1
```

**Collects:**
- ✅ Teams (NFL & NCAA) - 34 NFL + 744 NCAA teams
- ✅ Bookmakers list - 20 bookmakers

**Time:** ~5 seconds  
**API Requests:** 4 (2 per sport)

---

### 2. `highlightly_gameday.ps1`

Collect game day data (run on game days).

**Usage:**
```powershell
# For today
.\scripts\highlightly_gameday.ps1

# For specific date
.\scripts\highlightly_gameday.ps1 -Date "2024-11-10"
```

**Collects:**
- ✅ Matches (schedules, scores, venue, weather, injuries)
- ✅ Highlights (video highlights and game recaps)
- ✅ Standings (conference/division standings)

**Time:** ~10 seconds  
**API Requests:** 6 (3 per sport)

---

### 3. `collect_all_data.ps1` ⭐ (Recommended)

Complete data collection pipeline combining all sources.

**Usage:**
```powershell
# Full collection
.\scripts\collect_all_data.ps1

# Skip static data if already collected today
.\scripts\collect_all_data.ps1 -SkipStatic

# Specific date
.\scripts\collect_all_data.ps1 -Date "2024-11-10"

# Combination
.\scripts\collect_all_data.ps1 -Date "2024-11-10" -SkipStatic
```

**Collects:**
1. **Highlightly static data** (if not skipped)
   - Teams
   - Bookmakers

2. **Highlightly game day data**
   - Matches
   - Highlights
   - Standings

3. **overtime.ag betting odds**
   - NFL pre-game odds
   - College Football pre-game odds

4. **ESPN injury reports**
   - NFL injuries
   - College Football injuries

**Time:** ~60-90 seconds (full collection)  
**API Requests:** 10+ (Highlightly) + 0 (overtime.ag uses scraping) + 0 (ESPN uses scraping)

---

## Daily Workflow

### Morning Routine (Once Daily)
```powershell
# Collect static data
.\scripts\highlightly_daily_static.ps1
```

### Game Day Routine
```powershell
# Option 1: Just Highlightly game data
.\scripts\highlightly_gameday.ps1

# Option 2: Everything (Recommended)
.\scripts\collect_all_data.ps1 -SkipStatic
```

---

## Output Locations

All data is saved to organized directories:

```
data/
├── highlightly/
│   ├── nfl/
│   │   ├── teams-{timestamp}.jsonl
│   │   ├── bookmakers-{timestamp}.jsonl
│   │   ├── matches-{date}-{timestamp}.jsonl
│   │   ├── highlights-{date}-{timestamp}.jsonl
│   │   └── standings-{season}-{timestamp}.jsonl
│   └── ncaaf/
│       └── (same structure)
├── odds/
│   ├── nfl/
│   │   └── nfl-odds-{timestamp}.jsonl
│   └── ncaaf/
│       └── ncaaf-odds-{timestamp}.jsonl
└── injuries/
    ├── nfl/
    │   └── nfl-injuries-{timestamp}.jsonl
    └── ncaaf/
        └── ncaaf-injuries-{timestamp}.jsonl
```

---

## API Rate Limits

Highlightly FREE tier: **100 requests per day**

**Request Usage:**
- `highlightly_daily_static.ps1`: 4 requests
- `highlightly_gameday.ps1`: 6 requests
- `collect_all_data.ps1`: 10 requests (full)

**Monitor usage:**
Each command shows: `ℹ️ API requests remaining: XX`

---

## Troubleshooting

### "HIGHLIGHTLY_API_KEY not set"

**Solution:** Verify `.env` file exists with:
```
HIGHLIGHTLY_API_KEY=e674f79b-ad6f-47cb-88da-7895183dcbe8
```

### "401 Unauthorized - Odds are not available in Basic plan"

**Expected behavior.** The odds endpoint requires a paid plan. Use overtime.ag for betting odds:
```powershell
uv run walters-analyzer scrape-overtime --sport both
```

### "No matches found"

**Normal** - If there are no games scheduled for the specified date, no matches will be returned.

---

## Free Tier vs Paid Plan

| Feature | FREE Tier | Paid Plan |
|---------|-----------|-----------|
| Teams | ✅ | ✅ |
| Matches | ✅ | ✅ |
| Bookmakers | ✅ | ✅ |
| Highlights | ✅ | ✅ |
| Standings | ✅ | ✅ |
| Players | ✅ | ✅ |
| Lineups | ✅ | ✅ |
| Historical | ✅ | ✅ |
| **Odds** | ❌ | ✅ |
| **Geo Restrictions** | ❌ | ✅ |

**Our Solution:** Use overtime.ag for odds (already integrated) ✅

---

## Integration with Billy Walters Methodology

The collected data enhances Billy Walters analysis:

1. **Match Details** - Venue, weather, injuries for situational analysis
2. **Team Statistics** - Historical performance for power ratings
3. **Player Data** - Position-specific impact analysis
4. **Highlights** - Video review for qualitative assessment
5. **Standings** - Conference position and motivation factors

Combined with overtime.ag odds and ESPN injuries, you have comprehensive data for betting analysis.

---

## Scheduled Execution (Optional)

### Windows Task Scheduler

Create a scheduled task to run daily:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6:00 AM
4. Action: Start a program
   - Program: `pwsh.exe`
   - Arguments: `-File "C:\path\to\scripts\collect_all_data.ps1" -SkipStatic`
   - Start in: `C:\path\to\billy-walters-sports-analyzer`

### Manual Scheduling (Recommended for beginners)

Just run the script when you need data:
```powershell
.\scripts\collect_all_data.ps1
```

---

## Additional Resources

- **Highlightly API Docs**: https://highlightly.net/documentation/american-football/
- **Integration Guide**: `HIGHLIGHTLY_INTEGRATION.md`
- **Command Reference**: `CLAUDE.md`
- **Project README**: `README.md`

---

**Last Updated:** November 8, 2024  
**Status:** Production Ready ✅

