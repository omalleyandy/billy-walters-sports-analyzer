Start monitoring a specific matchup at 15-minute intervals.

This command launches a background monitoring service that tracks betting lines every 15 minutes and alerts you to significant line movements. Essential for tracking sharp action during game day.

## Usage

```bash
/in-play-matchup-interval [team1] [team2] [interval]
```

## Arguments

- `team1` - First team name (partial match works)
- `team2` - Second team name (partial match works)
- `interval` - (Optional) Minutes between checks (default: 15)

## Examples

```bash
# Monitor tonight's game every 15 minutes
/in-play-matchup-interval Steelers Chargers

# Monitor with custom 5-minute interval
/in-play-matchup-interval Eagles Packers 5

# Track Sunday afternoon game
/in-play-matchup-interval Chiefs Broncos
```

## What Happens

1. **Starts monitoring** - Fetches odds immediately
2. **Checks every 15 min** - Automatic updates
3. **Detects movements** - Alerts on ±0.5 point changes
4. **Saves history** - Creates tracking file
5. **Runs until stopped** - Press Ctrl+C to end

## Output

Each check shows:
- Current timestamp
- Full odds (spread, total, ML)
- Line movement alerts
- Direction of movement
- API quota status

## Movement Alerts

The monitor flags significant changes:

**Spread Movement**
- ±0.5 or more triggers alert
- Shows direction (toward favorite/dog)
- Indicates sharp vs public money

**Total Movement**
- ±0.5 or more triggers alert
- Shows direction (up/down)
- Weather or injury driven

## History Tracking

All odds snapshots saved to:
```
data/odds/monitoring/[team1]_vs_[team2].json
```

This creates a complete line movement history for post-game analysis.

## Stopping the Monitor

Press `Ctrl+C` to gracefully stop monitoring. History will be saved automatically.

## Use Cases

**Pre-Game (2-4 hours before kickoff)**
- Track sharp money movement
- Identify closing line value
- Catch late injury news impact

**Live Game**
- Monitor in-game line shifts
- Identify live betting opportunities
- Track quarter-by-quarter movements

**Billy Walters Strategy**
- Wait for optimal number (3, 7)
- Track until you get your price
- Identify reverse line movement

## Pro Tips

1. **Start early** - Begin monitoring 4 hours before kickoff
2. **Watch for steam** - Rapid movement = sharp action
3. **Key numbers** - Alert when crossing 3, 7, 10, 14
4. **Compare books** - Use with `/scrape-live-odds` for multiple sources
5. **CLV tracking** - Compare entry price to closing line

## API Usage

Monitors use 1 API call per check:
- 15-min intervals = 4 calls/hour
- 4 hours of monitoring = 16 calls
- You have 125 calls remaining

## Related Commands

- `/in-play-matchup-now` - Single instant check
- `/analyze-matchup` - Full game analysis
- `/scrape-live-odds` - All games snapshot

Execute:
```bash
# Convert interval to seconds if provided, default 900 (15 min)
INTERVAL_SEC=$((${3:-15} * 60))
uv run python live_odds_monitor.py "$1" "$2" --interval $INTERVAL_SEC
```
