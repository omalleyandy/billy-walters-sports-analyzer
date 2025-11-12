#!/usr/bin/env python3
"""
Validate Action Network odds freshness and game status.
Since Overtime odds are often unavailable during games,
this validates the Action Network data that the edge detector actually uses.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def parse_timestamp(ts_str: str) -> datetime:
    """Parse timestamp from Action Network format."""
    try:
        # Try ISO format
        if "T" in ts_str:
            if ts_str.endswith("Z"):
                return datetime.fromisoformat(ts_str[:-1] + "+00:00")
            return datetime.fromisoformat(ts_str)
        # Try epoch timestamp
        return datetime.fromtimestamp(int(ts_str) / 1000, tz=timezone.utc)
    except Exception:
        return None


def get_game_status_from_action(game_data: dict) -> str:
    """Extract game status from Action Network game data."""
    status = game_data.get("status", "unknown")

    if status in ["scheduled", "pre_game"]:
        return "PRE_GAME"
    elif status in ["in_progress", "live"]:
        return "IN_PLAY"
    elif status in ["final", "completed", "closed"]:
        return "COMPLETED"
    else:
        return status.upper()


def main():
    """Validate Action Network odds data."""
    project_root = get_project_root()
    action_dir = project_root / "output" / "action_network"

    print("=" * 80)
    print("ACTION NETWORK ODDS VALIDATION")
    print("(Primary odds source for Billy Walters edge detection)")
    print("=" * 80)
    print()

    # Find latest Action Network file
    action_files = list(action_dir.glob("nfl_api_responses_*.json"))

    if not action_files:
        print("[ERROR] No Action Network data files found!")
        print(f"Expected location: {action_dir}")
        return 1

    latest_file = max(action_files, key=lambda f: f.stat().st_mtime)
    file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
    now = datetime.now()

    # Calculate file age
    age_seconds = (now - file_time).total_seconds()
    age_minutes = int(age_seconds / 60)
    age_hours = age_seconds / 3600

    print(f"Latest Data File: {latest_file.name}")
    print(f"File Timestamp: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"File Age: {age_minutes} minutes ({age_hours:.1f} hours)")
    print()

    # Determine freshness
    if age_hours < 1:
        freshness = "[FRESH]"
        desc = "Excellent - data is current"
    elif age_hours < 6:
        freshness = "[OK]"
        desc = "Good - data is recent"
    elif age_hours < 24:
        freshness = "[STALE]"
        desc = "Warning - data may be outdated"
    else:
        freshness = "[OLD]"
        desc = "Critical - data is very old"

    print(f"Freshness: {freshness} - {desc}")
    print()

    # Load Action Network data
    try:
        with open(latest_file, "r") as f:
            api_responses = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load file: {e}")
        return 1

    # Find scoreboard data
    scoreboard_data = None
    for response in api_responses:
        url = response.get("url", "")
        if "scoreboard/nfl" in url and response.get("data"):
            scoreboard_data = response["data"]
            scrape_time = response.get("timestamp")
            break

    if not scoreboard_data:
        print("[ERROR] No scoreboard data found in Action Network responses")
        return 1

    games = scoreboard_data.get("games", [])

    if not games:
        print("[WARNING] No games found in scoreboard data")
        return 0

    print(f"Data Scraped: {scrape_time}")
    print(f"Total Games Found: {len(games)}")
    print()
    print("=" * 80)
    print("GAME STATUS AND ODDS VALIDATION")
    print("=" * 80)
    print()

    # Analyze each game
    pre_game = []
    in_play = []
    completed = []

    for game in games:
        teams = game.get("teams", [])
        if len(teams) < 2:
            continue

        away_team = teams[0].get("display_name", "Unknown")
        home_team = teams[1].get("display_name", "Unknown")

        game_id = game.get("id")
        start_time = game.get("start_time")
        status = game.get("status", "unknown")

        # Parse game time
        game_dt = parse_timestamp(start_time) if start_time else None

        # Get odds
        odds = game.get("odds", [])
        spread = "N/A"
        total = "N/A"

        if odds and len(odds) > 0:
            latest_odds = odds[0]
            spread_data = latest_odds.get("spread", {})
            total_data = latest_odds.get("total", {})

            if spread_data:
                spread_line = spread_data.get("point", "N/A")
                spread = f"{home_team} {spread_line}"

            if total_data:
                total = total_data.get("points", "N/A")

        game_info = {
            "away": away_team,
            "home": home_team,
            "time": game_dt,
            "status": status,
            "spread": spread,
            "total": total,
            "has_odds": len(odds) > 0,
        }

        # Categorize by status
        if status in ["scheduled", "pre_game"]:
            pre_game.append(game_info)
        elif status in ["in_progress", "live"]:
            in_play.append(game_info)
        else:
            completed.append(game_info)

    # Display games by status
    def print_games(games_list, title, indicator):
        if not games_list:
            return

        print(f"\n{indicator} {title} ({len(games_list)} games)")
        print("-" * 80)
        for g in games_list:
            time_str = g["time"].strftime("%Y-%m-%d %H:%M") if g["time"] else "Unknown"
            odds_str = (
                f"Spread: {g['spread']} | Total: {g['total']}"
                if g["has_odds"]
                else "No odds available"
            )
            print(f"{g['away']} @ {g['home']}")
            print(f"  Time: {time_str} | Status: {g['status']}")
            print(f"  {odds_str}")
            print()

    print_games(pre_game, "PRE-GAME (Bettable)", "[OK]")
    print_games(in_play, "IN-PLAY (Live betting)", "[LIVE]")
    print_games(completed, "COMPLETED", "[DONE]")

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Games: {len(games)}")
    print(f"Pre-Game (bettable): {len(pre_game)}")
    print(f"In-Play: {len(in_play)}")
    print(f"Completed: {len(completed)}")
    print()

    # Recommendations
    print("RECOMMENDATIONS:")
    print()

    if age_hours > 24:
        print("[ACTION REQUIRED] Data is over 24 hours old")
        print("  -> Run: /collect-all-data")
        print()

    if len(in_play) > 0:
        print(f"[INFO] {len(in_play)} game(s) currently in progress")
        print("  -> Odds in data are from pre-game (lines are closed)")
        print("  -> Edge detection uses last available pre-game odds")
        print()

    if len(completed) > 0 and len(pre_game) == 0:
        print(f"[INFO] All games completed - Week {10} finished")
        print("  -> Wait for new week's data (Tuesday-Wednesday)")
        print("  -> Run: /collect-all-data")
        print()

    if len(pre_game) > 0:
        print(f"[OK] {len(pre_game)} game(s) with pre-game odds")
        if age_hours < 6:
            print("  -> Odds are current, edge detection is valid")
        else:
            print("  -> Consider refreshing: /collect-all-data")
        print()

    # For edge detection validity
    print("EDGE DETECTION VALIDITY:")
    print()

    if age_hours < 12 and (len(pre_game) > 0 or len(in_play) > 0):
        print("[OK] Edge detection results are VALID")
        print("  -> Using recent pre-game odds")
        print("  -> Proceed with analysis")
    elif age_hours < 24 and len(in_play) > 0:
        print("[WARNING] Edge detection uses PRE-GAME odds")
        print("  -> Games are now in progress")
        print("  -> Odds shown are from before kickoff (accurate for analysis)")
        print("  -> Cannot place new bets until games complete")
    elif len(completed) == len(games):
        print("[INFO] All games completed")
        print("  -> Edge detection reflects final pre-game odds")
        print("  -> Use for CLV (Closing Line Value) tracking")
        print("  -> Run /collect-all-data for next week")
    else:
        print("[WARNING] Data freshness uncertain")
        print("  -> Consider running: /collect-all-data")

    return 0


if __name__ == "__main__":
    sys.exit(main())
