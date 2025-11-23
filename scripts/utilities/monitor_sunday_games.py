#!/usr/bin/env python3
"""
Monitor Sunday NFL Week 12 games for line movement and sharp action.

Tracks:
- Opening vs closing line movement
- Public betting percentages
- Sharp action indicators
- Game results and final scores
- CLV (Closing Line Value) calculation
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Week 12 Sunday games configuration
SUNDAY_GAMES = [
    {
        "game_id": "min_gb",
        "matchup": "Minnesota @ Green Bay",
        "kickoff": "2025-11-23T13:00:00Z",
        "our_pick": "Green Bay -6.5",
        "predicted_line": "GB +2.6",
        "edge": 9.1,
        "kelly": 25.0,
        "confidence": 91,
    },
    {
        "game_id": "ne_cin",
        "matchup": "New England @ Cincinnati",
        "kickoff": "2025-11-23T13:00:00Z",
        "our_pick": "New England +7.5",
        "predicted_line": "NE +1.1",
        "edge": 7.2,
        "kelly": 25.0,
        "confidence": 72,
    },
    {
        "game_id": "cle_lv",
        "matchup": "Cleveland @ Las Vegas",
        "kickoff": "2025-11-23T16:05:00Z",
        "our_pick": "PASS (QB adjusted)",
        "predicted_line": "CLE +2.3 (unadjusted)",
        "edge": 2.8,
        "kelly": 0.0,
        "confidence": 34,
        "note": "DTR starting - edge below threshold",
    },
    {
        "game_id": "pit_chi",
        "matchup": "Pittsburgh @ Chicago",
        "kickoff": "2025-11-23T13:00:00Z",
        "our_pick": "Chicago -2.5",
        "predicted_line": "CHI +2.3",
        "edge": 4.8,
        "kelly": 17.3,
        "confidence": 48,
    },
    {
        "game_id": "atl_no",
        "matchup": "Atlanta @ New Orleans",
        "kickoff": "2025-11-23T16:25:00Z",
        "our_pick": "New Orleans -2.0",
        "predicted_line": "NO +2.1",
        "edge": 4.1,
        "kelly": 14.6,
        "confidence": 41,
    },
    {
        "game_id": "ind_kc",
        "matchup": "Indianapolis @ Kansas City",
        "kickoff": "2025-11-23T13:00:00Z",
        "our_pick": "Kansas City -3.5",
        "predicted_line": "KC +2.1",
        "edge": 5.6,
        "kelly": 20.1,
        "confidence": 56,
    },
    {
        "game_id": "tb_lar",
        "matchup": "Tampa Bay @ LA Rams",
        "kickoff": "2025-11-23T20:20:00Z",
        "our_pick": "LA Rams -7.0",
        "predicted_line": "LAR +2.6",
        "edge": 9.6,
        "kelly": 25.0,
        "confidence": 96,
    },
]


def format_time_remaining(kickoff_str: str) -> str:
    """Calculate and format time until kickoff."""
    try:
        kickoff = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = kickoff - now

        if delta.total_seconds() < 0:
            return "LIVE/FINISHED"

        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "N/A"


def print_game_header() -> None:
    """Print header for game monitoring."""
    print("\n" + "=" * 100)
    print("WEEK 12 SUNDAY GAME MONITORING - Billy Walters Sports Analyzer")
    print(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 100)


def print_early_games_section() -> None:
    """Print early Sunday games (13:00 ET kickoff)."""
    print("\n[EARLY WINDOW] 13:00 ET Kickoffs")
    print("-" * 100)

    early_games = [g for g in SUNDAY_GAMES if "13:00" in g["kickoff"]]

    for game in early_games:
        print(f"\n{game['matchup'].upper()}")
        print(f"  Kickoff: {game['kickoff']} ({format_time_remaining(game['kickoff'])} remaining)")
        print(f"  Our Pick: {game['our_pick']}")
        print(f"  Edge: {game['edge']:.1f} pts | Kelly: {game['kelly']:.1f}% | Confidence: {game['confidence']}/100")

        # Status section
        if "note" in game:
            print(f"  [NOTE] {game['note']}")

        # Line tracking template
        print(f"  Opening Line: [TO BE RECORDED]")
        print(f"  Current Line: [MONITORING...]")
        print(f"  Closing Line: [UPDATED 5 MIN BEFORE KICKOFF]")
        print(f"  CLV: [CALCULATED AFTER GAME]")


def print_afternoon_games_section() -> None:
    """Print afternoon Sunday games (16:05+ ET kickoffs)."""
    print("\n[AFTERNOON WINDOW] 16:05+ ET Kickoffs")
    print("-" * 100)

    afternoon_games = [g for g in SUNDAY_GAMES if "16:05" in g["kickoff"] or "20:20" in g["kickoff"]]

    for game in afternoon_games:
        print(f"\n{game['matchup'].upper()}")
        print(f"  Kickoff: {game['kickoff']} ({format_time_remaining(game['kickoff'])} remaining)")
        print(f"  Our Pick: {game['our_pick']}")
        print(f"  Edge: {game['edge']:.1f} pts | Kelly: {game['kelly']:.1f}% | Confidence: {game['confidence']}/100")

        if "note" in game:
            print(f"  [NOTE] {game['note']}")

        print(f"  Opening Line: [TO BE RECORDED]")
        print(f"  Current Line: [MONITORING...]")
        print(f"  Closing Line: [UPDATED 5 MIN BEFORE KICKOFF]")
        print(f"  CLV: [CALCULATED AFTER GAME]")


def print_monitoring_guide() -> None:
    """Print instructions for manual monitoring."""
    print("\n" + "=" * 100)
    print("MONITORING INSTRUCTIONS")
    print("=" * 100)

    guide = """
KEY METRICS TO TRACK:

1. OPENING LINE (Record Now):
   - Check Overnight.ag, DraftKings, FanDuel, or other sportsbooks
   - Record the consensus opening line (primary market)
   - Time recorded: [NOW]

2. CURRENT LINE (Monitor Throughout Day):
   - Track line movement from opening
   - Look for sharp action: Does Vegas move against public or with public?
   - Monitor public betting percentages if available

3. CLOSING LINE (Record 5 Minutes Before Kickoff):
   - Final line just before games begin
   - This is crucial for CLV calculation
   - Set phone reminder for 12:55 ET (early games), 16:00 ET (afternoon), 20:15 ET (night)

4. CLOSING LINE VALUE (CLV) CALCULATION:
   For each bet: CLV = Closing Line - Your Picking Line

   Example (MIN @ GB, you like GB -6.5):
   - Your Pick: GB -6.5
   - Opening Line: GB -6.5
   - Closing Line: GB -4.5 (sharp action moved it)
   - CLV = -4.5 - (-6.5) = +2.0 (favorable!)

5. GAME RESULT:
   - Final score and winner
   - Did our prediction win/lose?
   - What was actual spread push?

6. SHARP ACTION INDICATORS:
   - If line moves in your favor: Sharps agree with you
   - If line moves against you: Sharps disagree (re-evaluate)
   - Reverse line movement: Line moving opposite of public % (sharp action)
   - Steam move: Rapid line movement in one direction

================================================================================
SPECIAL CASES FOR WEEK 12:

CLEVELAND @ LAS VEGAS (16:05 ET):
  Status: PASS (DTR starting, QB adjustment below threshold)
  Monitor: Watch opening line for repricing from Watson absence
  Interest: Will Vegas repricing reach fair value (-2.5/-3.0)?
  Note: You did NOT place this bet, but monitor for learning

================================================================================
RECORDING TEMPLATE (Copy & Fill In):

Game: Minnesota @ Green Bay
Date: 2025-11-23
Kickoff: 13:00 ET

Opening Line: [Record from sportsbook] (e.g., GB -6.5)
Our Pick: GB -6.5
Predicted Line: GB +2.6
Edge: 9.1 pts | Confidence: 91%

10:00 ET: [Line update] - No movement yet / Moving vs public / Sharp action?
11:00 ET: [Line update]
12:30 ET: [Final update before kickoff]
12:55 ET: CLOSING LINE: [Record final]

Game Result:
  Final Score: [MIN vs GB score]
  Winner: [Team]
  Spread Result: [Push/Win/Lose]

CLV Calculation:
  Closing Line: [from above]
  Your Pick: GB -6.5
  CLV = [Closing] - [Opening] = [CLV amount]

Notes: [Any observations about sharp action, public betting, etc.]

================================================================================
WHY THIS MATTERS:

Billy Walters success metric is NOT win/loss %, it's CLV (Closing Line Value).
- Professional target: +1.5 CLV average
- Elite target: +2.0 CLV average
- Win rate target: 55%+ (not 60%+)

By tracking CLV, you measure if:
1. Your predictions are accurate (independent of luck)
2. You're getting good odds when you place bets
3. Your picks have edge vs market consensus
4. You're improving your prediction model

This is the difference between profitable and unprofitable betting.

================================================================================
NEXT STEPS:

1. RIGHT NOW: Record opening lines for all 7 games before sharp action begins
2. SUNDAY 12:50 ET: Set reminder to record early game closing lines
3. SUNDAY 16:00 ET: Record afternoon game closing lines
4. SUNDAY 20:15 ET: Record night game closing lines
5. SUNDAY NIGHT: Enter game results and calculate CLV for each game
6. MONDAY: Review CLV performance and update learning notes
"""

    print(guide)


def print_clv_tracker_template() -> None:
    """Print template for CLV tracking."""
    print("\n" + "=" * 100)
    print("CLV TRACKING TEMPLATE - Copy to Spreadsheet or Text File")
    print("=" * 100)

    print("""
[Game] | [Kickoff] | [Open] | [Our Pick] | [Close] | [CLV] | [Result] | [Notes]
-------|-----------|--------|-----------|--------|-------|---------|--------
MIN@GB | 13:00 ET  | -6.5   | GB -6.5   | [RECORD] | [+X.X] | W/L/P   | Sharp action?
NE@CIN | 13:00 ET  | +7.5   | NE +7.5   | [RECORD] | [+X.X] | W/L/P   | Key number 3?
PIT@CHI| 13:00 ET  | -2.5   | CHI -2.5  | [RECORD] | [+X.X] | W/L/P   | Even matchup
IND@KC | 13:00 ET  | -3.5   | KC -3.5   | [RECORD] | [+X.X] | W/L/P   | Public fade?
CLE@LV | 16:05 ET  | PASS   | (DTR adj) | [MONITOR]| [N/A]  | N/A     | QB repricing?
ATL@NO | 16:25 ET  | -2.0   | NO -2.0   | [RECORD] | [+X.X] | W/L/P   | Lower conf edge
TB@LAR | 20:20 ET  | -7.0   | LAR -7.0  | [RECORD] | [+X.X] | W/L/P   | Very strong edge

SUMMARY:
- Total Bets: 6 (excluding PASS on Cleveland)
- Average CLV Target: +2.0 per game
- Ideal Performance: 5+ wins with +2.0 CLV average = Professional level
- Acceptable Performance: 3-4 wins with +1.0 CLV average = Above average
- Learning: Any result, calculate CLV - that's the real metric

================================================================================
""")


def main() -> None:
    """Main monitoring display."""
    print_game_header()
    print_early_games_section()
    print_afternoon_games_section()
    print_monitoring_guide()
    print_clv_tracker_template()

    # Summary statistics
    total_kelly = sum(g["kelly"] for g in SUNDAY_GAMES if g["kelly"] > 0)
    active_bets = sum(1 for g in SUNDAY_GAMES if g["kelly"] > 0)

    print("\n" + "=" * 100)
    print("WEEK 12 SUNDAY SUMMARY")
    print("=" * 100)
    print(f"Total Games Monitored: {len(SUNDAY_GAMES)}")
    print(f"Active Bets (Recommended): {active_bets}")
    print(f"Total Kelly Allocation: {total_kelly:.1f}%")
    print(f"Bankroll Suggested: $10,000 minimum (at 50% Kelly = $3,250 in bets)")
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
