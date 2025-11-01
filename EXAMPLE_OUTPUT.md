# Example Scraper Output

This document shows example output from the overtime.ag scraper to help you understand the data structure.

## Example CSV Output

```csv
source,sport,league,collected_at,event_date,event_time,rotation_number,is_live,game_key,away_team,home_team,spread_away_line,spread_away_price,spread_home_line,spread_home_price,total_over_line,total_over_price,total_under_line,total_under_price,moneyline_away_price,moneyline_home_price,quarter,clock
overtime.ag,nfl,NFL,2025-11-01T12:34:56.789Z,2025-11-02,1:00 PM ET,451-452,False,abc123def456,Chicago Bears,Cincinnati Bengals,-2.5,-115,2.5,-105,51,-110,51,-110,-130,110,,
overtime.ag,nfl,NFL,2025-11-01T12:34:56.789Z,2025-11-02,1:00 PM ET,453-454,False,def789ghi012,San Francisco 49ers,New York Giants,-2.5,-110,2.5,-110,48.5,-110,48.5,-110,-140,120,,
overtime.ag,college_football,NCAAF,2025-11-01T12:34:56.789Z,2025-10-31,7:30 PM ET,317-318,False,ghi345jkl678,North Carolina,Syracuse,1,-110,-1,-110,45,-110,45,-110,105,-125,,
```

## Example JSONL Output

Each line is a complete JSON object:

```jsonl
{"source":"overtime.ag","sport":"nfl","league":"NFL","collected_at":"2025-11-01T12:34:56.789Z","game_key":"abc123def456","event_date":"2025-11-02","event_time":"1:00 PM ET","rotation_number":"451-452","teams":{"away":"Chicago Bears","home":"Cincinnati Bengals"},"state":{},"markets":{"spread":{"away":{"line":-2.5,"price":-115},"home":{"line":2.5,"price":-105}},"total":{"over":{"line":51,"price":-110},"under":{"line":51,"price":-110}},"moneyline":{"away":{"price":-130},"home":{"price":110}}},"is_live":false}
{"source":"overtime.ag","sport":"nfl","league":"NFL","collected_at":"2025-11-01T12:34:56.789Z","game_key":"def789ghi012","event_date":"2025-11-02","event_time":"1:00 PM ET","rotation_number":"453-454","teams":{"away":"San Francisco 49ers","home":"New York Giants"},"state":{},"markets":{"spread":{"away":{"line":-2.5,"price":-110},"home":{"line":2.5,"price":-110}},"total":{"over":{"line":48.5,"price":-110},"under":{"line":48.5,"price":-110}},"moneyline":{"away":{"price":-140},"home":{"price":120}}},"is_live":false}
```

## Example Parquet Schema

```
source: string
league: string
sport: string
game_key: string
collected_at: string
event_date: string (nullable)
event_time: string (nullable)
rotation_number: string (nullable)
is_live: boolean
teams_json: string (JSON-encoded)
state_json: string (JSON-encoded)
markets_json: string (JSON-encoded)
```

## Understanding the Data

### Rotation Numbers
- Format: "XXX-YYY" where XXX is away team, YYY is home team
- Example: "451-452" means Bears (451) at Bengals (452)
- Used by bookmakers to identify games

### Spread Lines
- Negative line (-2.5) = favorite, must win by more than 2.5
- Positive line (+2.5) = underdog, can lose by less than 2.5
- Price in American odds format (-110 means risk 110 to win 100)

### Totals (Over/Under)
- Over 51 -110 = Bet over 51 total points at -110 odds
- Under 51 -110 = Bet under 51 total points at -110 odds

### Moneyline
- Negative (-130) = favorite, risk 130 to win 100
- Positive (+110) = underdog, risk 100 to win 110

### Date/Time Format
- Date: ISO format "YYYY-MM-DD" (e.g., "2025-11-02")
- Time: Display format with timezone (e.g., "1:00 PM ET")
- Collected at: UTC timestamp in ISO8601 format

## Live Betting Example

```csv
source,sport,league,collected_at,event_date,event_time,rotation_number,is_live,game_key,away_team,home_team,spread_away_line,spread_away_price,spread_home_line,spread_home_price,total_over_line,total_over_price,total_under_line,total_under_price,moneyline_away_price,moneyline_home_price,quarter,clock
overtime.ag,nfl,NFL,2025-11-01T15:23:45.123Z,,,True,live123abc,Kansas City Chiefs,Buffalo Bills,-1.5,-108,1.5,-112,52.5,-110,52.5,-110,-105,-115,3,5:32
```

Note the differences in live betting data:
- `is_live` = True
- `quarter` and `clock` fields populated
- `event_date` and `event_time` may be null (game already started)
- Odds update in real-time during the game

## Python Usage Example

```python
import pandas as pd

# Read the CSV
df = pd.read_csv('data/overtime_live/overtime-live-20251101-123456.csv')

# Filter for NFL games only
nfl_games = df[df['sport'] == 'nfl']

# Find favorites (negative spread)
favorites = nfl_games[nfl_games['spread_away_line'] < 0]

# Calculate implied probability from moneyline
def american_to_probability(odds):
    if odds < 0:
        return -odds / (-odds + 100)
    else:
        return 100 / (odds + 100)

nfl_games['away_win_prob'] = nfl_games['moneyline_away_price'].apply(american_to_probability)
nfl_games['home_win_prob'] = nfl_games['moneyline_home_price'].apply(american_to_probability)

# Find best value bets (high implied probability, good price)
print(nfl_games[['away_team', 'home_team', 'away_win_prob', 'spread_away_price']])

# Compare odds across time
df1 = pd.read_csv('data/overtime_live/overtime-live-20251101-090000.csv')  # Morning
df2 = pd.read_csv('data/overtime_live/overtime-live-20251101-120000.csv')  # Noon

# Merge on game_key to track line movement
merged = df1.merge(df2, on='game_key', suffixes=('_morning', '_noon'))
merged['spread_movement'] = merged['spread_away_line_noon'] - merged['spread_away_line_morning']

print("Line Movement:")
print(merged[['away_team_morning', 'spread_away_line_morning', 'spread_away_line_noon', 'spread_movement']])
```

## SQL Query Example (if loaded into database)

```sql
-- Find games with line movement > 1 point
SELECT 
    away_team,
    home_team,
    spread_away_line,
    total_over_line,
    event_date,
    event_time
FROM overtime_odds
WHERE sport = 'nfl'
  AND spread_away_line < -7  -- Big favorites
  AND total_over_line > 50   -- High-scoring expected
ORDER BY event_date, event_time;

-- Compare morning vs evening lines
SELECT 
    a.away_team,
    a.home_team,
    a.spread_away_line as morning_spread,
    b.spread_away_line as evening_spread,
    (b.spread_away_line - a.spread_away_line) as movement
FROM overtime_odds a
JOIN overtime_odds b ON a.game_key = b.game_key
WHERE a.collected_at < '2025-11-01T12:00:00Z'
  AND b.collected_at > '2025-11-01T18:00:00Z'
  AND ABS(b.spread_away_line - a.spread_away_line) > 1;
```

## Excel Pivot Table Example

1. Open the CSV in Excel
2. Select all data → Insert → PivotTable
3. Drag fields:
   - Rows: `sport`, `league`
   - Values: Count of `game_key`
   - Filters: `is_live`, `event_date`

Result:
```
Sport            | League | Game Count
-----------------+--------+-----------
nfl             | NFL    | 14
college_football| NCAAF  | 23
```

4. Create another pivot:
   - Rows: `away_team`
   - Values: Average of `spread_away_price`, Count of `game_key`
   - This shows average odds and number of games per team

## File Size Estimates

For reference, typical file sizes:
- **CSV**: ~5-10 KB per game
- **JSONL**: ~3-6 KB per game
- **Parquet**: ~1-2 KB per game (most efficient)

Example: Scraping 30 NFL games + 40 CFB games (70 total)
- CSV: ~350-700 KB
- JSONL: ~210-420 KB
- Parquet: ~70-140 KB

All three formats contain the same data, just in different structures.

