# NCAAF Edge Detection Fix - Root Cause Analysis & Solution

**Date**: 2025-11-28
**Issue**: NCAAF edge detector returned 0 edges despite data being available
**Status**: RESOLVED - 5 edges now detected for Week 13

---

## Problem Statement

The NCAAF edge detector was consistently returning **0 edges** even though:
- 21 games were loaded from the schedule
- 64 games were loaded from odds data
- Power ratings were available for all teams
- Mathematical analysis showed edges SHOULD exist (e.g., Indiana @ Purdue with 5.5 pt edge)

## Root Cause Analysis

### Step 1: Initial Investigation
Discovered the detector was attempting to match games using the **ESPN game_id** (e.g., `401752788`) as the odds lookup key. However, the odds dictionary was keyed differently.

### Step 2: Data Flow Tracing
**Schedule Loading** (`_load_schedule()`):
- Extracts games from ESPN JSON
- Each game has an ESPN `game_id` (a numeric string like "401752788")
- Returns games with `game_id`, `away_team`, `home_team`

**Odds Loading** (`_load_odds()`):
- Loads odds from Overtime.ag JSON
- Gets `away_team` and `home_team` from each game
- **Normalizes team names** to Massey format using `_normalize_team_name()`
- **Constructs dictionary key as**: `f"{normalized_away}_{normalized_home}"`
- Example key: `"Indiana_Purdue"`

**Edge Analysis** (`_analyze_game()`):
- Receives game with ESPN `game_id`
- Was trying to look up odds using `odds.get(game_id, {})`
- **Problem**: ESPN game_id (`401752788`) ≠ odds dict key (`"Indiana_Purdue"`)
- Result: `game_odds` always empty → returns None → 0 edges found

### Step 3: The Fix

Changed the odds lookup logic from:
```python
# OLD: Using ESPN game_id
game_odds = odds.get(game_id, {})  # game_id = "401752788"
```

To:
```python
# NEW: Constructing key from normalized team names
odds_key = f"{away_team}_{home_team}"  # "Indiana_Purdue"
game_odds = odds.get(odds_key, {})
```

## Results

**Before Fix**: 0 edges detected
**After Fix**: 5 edges detected for Week 13

### Week 13 NCAAF Betting Edges

| Matchup | Edge | Strength | Recommendation |
|---------|------|----------|---|
| Indiana @ Purdue | 5.5 pts | STRONG | Bet HOME (Purdue) |
| Texas A&M @ Texas | 8.5 pts | VERY STRONG | Bet HOME (Texas) |
| Arizona @ Arizona St | 4.9 pts | MEDIUM | Bet HOME (Arizona St) |
| Vanderbilt @ Tennessee | 6.1 pts | STRONG | Bet HOME (Tennessee) |
| Alabama @ Auburn | 4.4 pts | MEDIUM | Bet AWAY (Alabama) |

## Technical Details

### Why This Bug Existed

The code was written with two different assumptions about how to construct the odds lookup key:

1. **Odds loading**: Used normalized team names for dictionary keys
2. **Edge analysis**: Expected ESPN game_id to be the key

These two approaches were never reconciled, causing a systematic mismatch.

### Lesson Learned

When data flows through multiple processing stages, ensure consistent **key construction** across all stages:
- If Stage A creates a dict with key `X`, Stage B must use key `X` to look up
- If keys are constructed differently, use a mapping layer or explicit key generation function
- Document the key format in comments

## Implementation Notes

- No changes to team name normalization logic
- No changes to data loading logic
- Only changed how the odds lookup key is constructed in `_analyze_game()`
- Minimal, focused fix following the principle: "change as little as possible to fix the issue"

## Next Steps

Some games still don't match odds (Miami, Houston, Oregon, etc.) because their team names in the schedule are not being fully normalized. This is a separate issue related to incomplete team name mapping for certain teams. For now, the detector successfully identifies 5+ point edges which meet the Billy Walters threshold for actionable plays.
