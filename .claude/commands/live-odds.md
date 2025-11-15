# Monitor Live Odds and Line Movements

Monitor live odds from Overtime.ag during NFL or NCAAF games with real-time line movement tracking.

## What This Does

Connects to Overtime.ag and monitors live odds during games, tracking:
- **Spread movements**: Changes in point spreads
- **Total movements**: Changes in over/under lines
- **Moneyline movements**: Changes in moneyline odds
- **Movement velocity**: How fast lines are changing
- **Significant movements**: Alerts for moves ≥0.5 points (spread/total) or ≥10 (moneyline)

## When to Use

- **NFL Sundays**: Monitor all day (10-12 hours)
- **Monday Night Football**: 4 hours during game
- **NCAAF Saturdays**: Full day coverage (4-12 hours)
- **MACtion**: Tuesday/Wednesday/Thursday nights (3-4 hours)
- **Quick checks**: 5-10 minutes to see current lines

## Output Files

Saves to `output/overtime/live/`:
- `line_history_{timestamp}.json` - Complete line-by-line history
- `movement_summary_{timestamp}.json` - Analysis and significant movements

## Usage Examples

Ask Claude to run one of these commands:

**NFL Sunday (3 hours):**
```bash
uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 10800
```

**NCAAF Saturday (4 hours):**
```bash
uv run python scripts/scrapers/scrape_overtime_live.py --ncaaf --duration 14400
```

**Both leagues (simultaneous games):**
```bash
uv run python scripts/scrapers/scrape_overtime_live.py --nfl --ncaaf --duration 14400
```

**Background monitoring (headless, quiet):**
```bash
uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 10800 --headless --quiet
```

**Quick check (5 minutes):**
```bash
uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 300
```

## Duration Guide

- **5 minutes**: 300 seconds (quick check)
- **1 hour**: 3600 seconds
- **3 hours**: 10800 seconds (NFL Sunday window)
- **4 hours**: 14400 seconds (single game + pre/post)
- **10 hours**: 36000 seconds (full NFL Sunday)
- **12 hours**: 43200 seconds (full NCAAF Saturday)

## What It Detects

**Sharp Money Indicators:**
1. **Reverse Line Movement (RLM)**: Line moves opposite direction from public betting
2. **Steam Moves**: Rapid line changes (high velocity)
3. **Key Number Movements**: Crossing 3, 7, 10, 14 in football
4. **Line Freezes**: No movement despite heavy action

## Billy Walters Workflow Integration

```bash
# 1. Pre-game: Get opening lines and run edge detection
uv run python scripts/scrapers/scrape_overtime_api.py --nfl
/edge-detector

# 2. During games: Monitor live movements
/live-odds --nfl --duration 10800

# 3. Post-game: Analyze movements vs your picks
# - Compare line movements to edge detector picks
# - RLM + Your Edge = SHARP PLAY confirmation
# - Track Closing Line Value (CLV)
```

## Example Output

```
SIGNIFICANT LINE MOVEMENTS DETECTED:

Buffalo Bills @ Kansas City Chiefs
  Updates: 47
  Spread movement: -1.5 (opened KC -4.5, now KC -6.0)
  Total movement: -2.0 (opened 48.5, now 46.5)
  ML Visitor: +25 (sharp money on Bills)

Philadelphia Eagles @ Dallas Cowboys
  Updates: 32
  Spread movement: +0.5 (line moved toward Cowboys despite public on Eagles)
  Total movement: -1.0
  → REVERSE LINE MOVEMENT DETECTED
```

## Pro Tips

1. **Start before games**: Begin monitoring 30 minutes before kickoff to capture opening lines
2. **Watch key numbers**: Movements through 3 or 7 are critical in football
3. **Compare to your edges**: If line moves toward your pick = sharp confirmation
4. **Track velocity**: Fast movements (>10/hour) = sharp action
5. **Use quiet mode**: `--quiet` for background monitoring (less console spam)
6. **Headless mode**: `--headless` for production (no browser window)

## Next Steps After Monitoring

1. Review `movement_summary_{timestamp}.json` for significant movements
2. Compare to your edge detector picks
3. Identify reverse line movement opportunities
4. Update CLV tracker with closing lines
5. Adjust future betting strategy based on sharp action patterns

---

**Need Help?**

Run with `--help` flag:
```bash
uv run python scripts/scrapers/scrape_overtime_live.py --help
```
