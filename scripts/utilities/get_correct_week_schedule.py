#!/usr/bin/env python3
"""Get CORRECT schedule for NFL Week 13 (starting Nov 28) and NCAAF Week 14"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from data.espn_api_client import ESPNAPIClient


def main():
    client = ESPNAPIClient()

    print("=" * 80)
    print("VERIFYING CURRENT DATE")
    print("=" * 80)
    today = datetime.now()
    print(f"Today: {today.strftime('%A, %B %d, %Y')}")
    print(f"Current NFL Week: 12 (ending tonight with MNF)")
    print(f"Next NFL Week: 13 (starts Thursday, Nov 28 - Thanksgiving)")
    print()

    print("=" * 80)
    print("NFL WEEK 13 SCHEDULE (Starting Nov 28 - Thanksgiving)")
    print("=" * 80)

    try:
        # Get ALL upcoming NFL games
        nfl_schedule = client.get_nfl_schedule()

        if "events" in nfl_schedule:
            events = nfl_schedule["events"]

            print(f"Total NFL events in API: {len(events)}")

            # Filter for games starting Nov 28 or later (Week 13)
            week_13_start = datetime(2025, 11, 28)
            week_14_start = datetime(2025, 12, 5)

            # Debug: Show date range of all events
            if events:
                dates = []
                for e in events:
                    date_str = e.get("date", "")
                    if date_str:
                        dates.append(
                            datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                        )
                if dates:
                    print(
                        f"NFL games date range: {min(dates).strftime('%b %d')} to {max(dates).strftime('%b %d')}"
                    )

            week_13_games = []
            for event in events:
                game_date_str = event.get("date", "")
                if game_date_str:
                    game_date = datetime.fromisoformat(
                        game_date_str.replace("Z", "+00:00")
                    )
                    # Remove timezone for comparison
                    game_date_naive = game_date.replace(tzinfo=None)

                    if week_13_start <= game_date_naive < week_14_start:
                        week_13_games.append(event)

            print(f"\nFound {len(week_13_games)} NFL Week 13 games (Nov 28 - Dec 4)\n")

            nfl_home_teams = {}
            for event in week_13_games:
                competitions = event.get("competitions", [])
                for comp in competitions:
                    date = event.get("date", "TBD")
                    game_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    date_display = game_date.strftime("%a %b %d, %I:%M %p ET")

                    competitors = comp.get("competitors", [])

                    away_team = None
                    home_team = None
                    home_loc = None
                    for competitor in competitors:
                        team = competitor.get("team", {})
                        if competitor.get("homeAway") == "home":
                            home_team = team.get("displayName")
                            home_loc = team.get("location")
                        else:
                            away_team = team.get("displayName")

                    if home_team and away_team:
                        print(f"{away_team:28s} @ {home_team:28s} | {date_display}")
                        if home_team:
                            nfl_home_teams[home_team] = {
                                "away": away_team,
                                "date": date,
                                "date_display": date_display,
                                "location": home_loc,
                            }

            print(f"\n[OK] NFL Week 13: {len(nfl_home_teams)} home teams")
        else:
            print("[ERROR] No events found in NFL schedule")
            nfl_home_teams = {}

    except Exception as e:
        print(f"[ERROR] Failed to fetch NFL schedule: {e}")
        import traceback

        traceback.print_exc()
        nfl_home_teams = {}

    print("\n" + "=" * 80)
    print("NCAAF WEEK 14 SCHEDULE (Rivalry Week: Nov 28-30)")
    print("=" * 80)

    try:
        # Get NCAAF schedule
        ncaaf_schedule = client.get_ncaaf_schedule()

        if "events" in ncaaf_schedule:
            events = ncaaf_schedule["events"]

            # Filter for games starting Nov 28-30 (Week 14 - Rivalry Week)
            week_14_start = datetime(2025, 11, 28)
            week_14_end = datetime(2025, 12, 1)

            week_14_games = []
            for event in events:
                game_date_str = event.get("date", "")
                if game_date_str:
                    game_date = datetime.fromisoformat(
                        game_date_str.replace("Z", "+00:00")
                    )
                    game_date_naive = game_date.replace(tzinfo=None)

                    if week_14_start <= game_date_naive < week_14_end:
                        week_14_games.append(event)

            print(f"\nFound {len(week_14_games)} NCAAF Week 14 games (Nov 28-30)")
            print("(Showing first 25)\n")

            ncaaf_home_teams = {}
            for i, event in enumerate(week_14_games):
                competitions = event.get("competitions", [])
                for comp in competitions:
                    date = event.get("date", "TBD")
                    game_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    date_display = game_date.strftime("%a %b %d")

                    competitors = comp.get("competitors", [])

                    away_team = None
                    home_team = None
                    home_loc = None
                    for competitor in competitors:
                        team = competitor.get("team", {})
                        if competitor.get("homeAway") == "home":
                            home_team = team.get("displayName")
                            home_loc = team.get("location")
                        else:
                            away_team = team.get("displayName")

                    if home_team and away_team:
                        if i < 25:  # Show first 25
                            print(f"{away_team:28s} @ {home_team:28s} | {date_display}")
                        if home_team:
                            ncaaf_home_teams[home_team] = {
                                "away": away_team,
                                "date": date,
                                "date_display": date_display,
                                "location": home_loc,
                            }

            if len(week_14_games) > 25:
                print(f"... and {len(week_14_games) - 25} more games")

            print(f"\n[OK] NCAAF Week 14: {len(ncaaf_home_teams)} home teams")
        else:
            print("[ERROR] No events found in NCAAF schedule")
            ncaaf_home_teams = {}

    except Exception as e:
        print(f"[ERROR] Failed to fetch NCAAF schedule: {e}")
        import traceback

        traceback.print_exc()
        ncaaf_home_teams = {}

    print("\n" + "=" * 80)
    print(
        f"CORRECTED TOTALS: {len(nfl_home_teams)} NFL + {len(ncaaf_home_teams)} NCAAF"
    )
    print("=" * 80)

    return nfl_home_teams, ncaaf_home_teams


if __name__ == "__main__":
    nfl_teams, ncaaf_teams = main()
