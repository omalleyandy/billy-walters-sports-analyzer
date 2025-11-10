Get instant live odds for a specific matchup.

This command immediately fetches current betting lines (spread, total, moneyline) for any NFL game. Perfect for quick checks during live games.

## Usage

```bash
/in-play-matchup-now [team1] [team2]
```

## Arguments

- `team1` - First team name (partial match works - e.g., "Chiefs", "KC", "Kansas")
- `team2` - Second team name (partial match works)

## Examples

```bash
# Tonight's game
/in-play-matchup-now Steelers Chargers

# Monday night
/in-play-matchup-now Eagles Packers

# Sunday matchups
/in-play-matchup-now Chiefs Broncos
/in-play-matchup-now Lions Eagles
```

## What You'll See

- **Current odds** (spread, total, moneyline)
- **Line movements** (if previously tracked)
- **Timestamp** of odds
- **API quota** remaining

## Behind the Scenes

1. Fetches live odds from The Odds API
2. Finds your matchup by team names
3. Shows current lines from sharp books
4. Compares to last check (if available)
5. Alerts on significant movements (±0.5 points)

## Pro Tips

- Use this just before kickoff to get closing lines
- Check multiple times to track live line movements
- Pair with `/analyze-matchup` for full analysis
- Partial team names work ("Chiefs" or "KC" both work)

## Related Commands

- `/in-play-matchup-interval` - Start continuous 15-min monitoring
- `/analyze-matchup` - Full Billy Walters analysis
- `/scrape-live-odds` - Get all games

Execute:
```bash
uv run python live_odds_monitor.py "$1" "$2" --now
```
