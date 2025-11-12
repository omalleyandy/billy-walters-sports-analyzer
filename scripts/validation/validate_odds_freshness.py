#!/usr/bin/env python3
"""
Validate Overtime odds freshness and game status.

Checks:
1. Odds file timestamps
2. Game times vs current time
3. Which games are pre-game, in-play, or completed
4. Data freshness warnings
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO format datetime string."""
    # Handle various ISO formats
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        # Try without timezone
        return datetime.fromisoformat(dt_str.replace("Z", ""))


def get_game_status(game_time: datetime, now: datetime) -> tuple[str, str]:
    """
    Determine game status based on time.

    Returns:
        (status, color) where status is PRE_GAME, IN_PLAY, or COMPLETED
    """
    time_diff = (game_time - now).total_seconds() / 3600  # hours

    if time_diff > 0.5:  # More than 30 minutes before
        return "PRE_GAME", "[OK]"
    elif time_diff > -3.5:  # Within 3.5 hours after start (game duration)
        return "IN_PLAY", "[LIVE]"
    else:
        return "COMPLETED", "[DONE]"


def validate_odds_freshness():
    """Validate Overtime odds freshness and game status."""
    project_root = get_project_root()
    output_dir = project_root / "output"

    print("=" * 80)
    print("OVERTIME ODDS FRESHNESS VALIDATION")
    print("=" * 80)
    print()

    # Find latest walters format odds file
    odds_files = list(output_dir.glob("overtime_nfl_walters_*.json"))

    if not odds_files:
        print("[ERROR] No Overtime odds files found!")
        print(f"Expected location: {output_dir}")
        return 1

    latest_file = max(odds_files, key=lambda f: f.stat().st_mtime)
    file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
    now = datetime.now()

    # Calculate file age
    age_seconds = (now - file_time).total_seconds()
    age_minutes = int(age_seconds / 60)
    age_hours = age_seconds / 3600

    print(f"Latest Odds File: {latest_file.name}")
    print(f"File Timestamp: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"File Age: {age_minutes} minutes ({age_hours:.1f} hours)")
    print()

    # Determine freshness level
    if age_hours < 1:
        freshness = "[FRESH]"
        freshness_desc = "Excellent - odds are current"
    elif age_hours < 6:
        freshness = "[OK]"
        freshness_desc = "Good - odds are recent"
    elif age_hours < 24:
        freshness = "[STALE]"
        freshness_desc = "Warning - odds may have moved"
    else:
        freshness = "[OLD]"
        freshness_desc = "Critical - odds are outdated"

    print(f"Freshness Status: {freshness}")
    print(f"Assessment: {freshness_desc}")
    print()

    # Load and analyze odds data
    try:
        with open(latest_file, "r") as f:
            odds_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load odds file: {e}")
        return 1

    games = odds_data.get("games", [])

    if not games:
        print("[WARNING] No games found in odds file!")
        print("This is normal if:")
        print("  - Games are currently in progress")
        print("  - Lines have been taken down")
        print("  - Scraped between game weeks")
        print()
        print("Recommended action: Run /scrape-overtime Tuesday-Wednesday")
        return 0

    print(f"Total Games in File: {len(games)}")
    print()
    print("=" * 80)
    print("GAME STATUS ANALYSIS")
    print("=" * 80)
    print()

    # Analyze each game
    pre_game_count = 0
    in_play_count = 0
    completed_count = 0

    for i, game in enumerate(games, 1):
        home = game.get("home_team", "Unknown")
        away = game.get("away_team", "Unknown")
        game_time_str = game.get("game_time", "")

        try:
            game_time = parse_iso_datetime(game_time_str)

            # Make timezone aware if needed
            if game_time.tzinfo is None:
                game_time = game_time.replace(tzinfo=timezone.utc)
            if now.tzinfo is None:
                now_aware = now.replace(tzinfo=timezone.utc)
            else:
                now_aware = now

            status, indicator = get_game_status(game_time, now_aware)

            # Count by status
            if status == "PRE_GAME":
                pre_game_count += 1
            elif status == "IN_PLAY":
                in_play_count += 1
            else:
                completed_count += 1

            # Format time remaining/elapsed
            time_diff_hours = (game_time - now_aware).total_seconds() / 3600

            if status == "PRE_GAME":
                time_str = f"in {abs(time_diff_hours):.1f}h"
            elif status == "IN_PLAY":
                time_str = f"{abs(time_diff_hours):.1f}h ago"
            else:
                time_str = f"{abs(time_diff_hours):.1f}h ago"

            # Get spread and total
            spread = game.get("spread", {})
            total = game.get("total", {})
            home_spread = spread.get("home", "N/A")
            total_line = total.get("over", "N/A")

            print(f"{i}. {away} @ {home}")
            print(f"   Status: {status} {indicator} ({time_str})")
            print(f"   Game Time: {game_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   Spread: {home} {home_spread} | Total: {total_line}")
            print()

        except Exception as e:
            print(f"{i}. {away} @ {home}")
            print("   Status: ERROR - Could not parse game time")
            print(f"   Raw time: {game_time_str}")
            print(f"   Error: {e}")
            print()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Games: {len(games)}")
    print(f"Pre-Game (bettable): {pre_game_count}")
    print(f"In-Play (live betting): {in_play_count}")
    print(f"Completed: {completed_count}")
    print()

    # Recommendations
    print("RECOMMENDATIONS:")
    print()

    if age_hours > 24:
        print("[ACTION REQUIRED] Odds data is over 24 hours old")
        print("  -> Run: /scrape-overtime")
        print()

    if in_play_count > 0:
        print(f"[INFO] {in_play_count} game(s) currently in progress")
        print("  -> Betting lines are unavailable during games")
        print("  -> Wait for games to complete and run /scrape-overtime")
        print()

    if completed_count > 0:
        print(f"[INFO] {completed_count} game(s) completed")
        print("  -> These games are no longer bettable")
        print("  -> Run /scrape-overtime to get new week's lines")
        print()

    if pre_game_count > 0:
        print(f"[OK] {pre_game_count} game(s) available for betting")
        if age_hours < 6:
            print("  -> Odds are current, proceed with analysis")
        else:
            print("  -> Consider refreshing odds: /scrape-overtime")
        print()

    if pre_game_count == 0 and in_play_count == 0 and completed_count > 0:
        print("[INFO] All games completed - Week finished")
        print("  -> Wait for Tuesday/Wednesday for next week's lines")
        print("  -> Optimal scraping: Tuesday-Wednesday after MNF")
        print()

    # Determine exit code
    if age_hours > 48:
        return 1  # Critical - data too old
    return 0


if __name__ == "__main__":
    sys.exit(validate_odds_freshness())
