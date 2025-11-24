#!/usr/bin/env python3
"""Get weather for all home teams in NFL Week 13 and NCAAF Week 14"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from data.espn_api_client import ESPNAPIClient


def main():
    client = ESPNAPIClient()

    print("=" * 80)
    print("NFL WEEK 13 SCHEDULE")
    print("=" * 80)

    try:
        # Get NFL Week 13 schedule
        nfl_schedule = client.get_nfl_schedule()

        # Parse NFL schedule
        if "events" in nfl_schedule:
            events = nfl_schedule["events"]
            print(f"\nFound {len(events)} NFL games\n")

            nfl_home_teams = {}
            for event in events:
                competitions = event.get("competitions", [])
                for comp in competitions:
                    date = event.get("date", "TBD")
                    competitors = comp.get("competitors", [])

                    away_team = None
                    home_team = None
                    for competitor in competitors:
                        team = competitor.get("team", {})
                        if competitor.get("homeAway") == "home":
                            home_team = team.get("displayName")
                            home_loc = team.get("location")
                        else:
                            away_team = team.get("displayName")

                    if home_team and away_team:
                        print(f"{away_team:28s} @ {home_team:28s} | {date}")
                        if home_team:
                            nfl_home_teams[home_team] = {
                                "away": away_team,
                                "date": date,
                                "location": home_loc,
                            }

            print(f"\nNFL Week 13: {len(nfl_home_teams)} home teams")
        else:
            print("[ERROR] No events found in NFL schedule")
            nfl_home_teams = {}

    except Exception as e:
        print(f"[ERROR] Failed to fetch NFL schedule: {e}")
        nfl_home_teams = {}

    print("\n" + "=" * 80)
    print("NCAAF WEEK 14 SCHEDULE")
    print("=" * 80)

    try:
        # Get NCAAF Week 14 schedule
        ncaaf_schedule = client.get_ncaaf_schedule()

        # Parse NCAAF schedule
        if "events" in ncaaf_schedule:
            events = ncaaf_schedule["events"]
            print(f"\nFound {len(events)} NCAAF games")
            print("(Showing first 20)\n")

            ncaaf_home_teams = {}
            for i, event in enumerate(events):
                competitions = event.get("competitions", [])
                for comp in competitions:
                    date = event.get("date", "TBD")
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
                        if i < 20:  # Show first 20
                            print(
                                f"{away_team:28s} @ {home_team:28s} | {date[:10]}"
                            )
                        if home_team:
                            ncaaf_home_teams[home_team] = {
                                "away": away_team,
                                "date": date,
                                "location": home_loc,
                            }

            if len(events) > 20:
                print(f"... and {len(events) - 20} more games")

            print(f"\nNCAAF Week 14: {len(ncaaf_home_teams)} home teams")
        else:
            print("[ERROR] No events found in NCAAF schedule")
            ncaaf_home_teams = {}

    except Exception as e:
        print(f"[ERROR] Failed to fetch NCAAF schedule: {e}")
        ncaaf_home_teams = {}

    print("\n" + "=" * 80)
    print(f"TOTAL: {len(nfl_home_teams)} NFL + {len(ncaaf_home_teams)} NCAAF home teams")
    print("=" * 80)

    # Return home teams for weather checking
    return nfl_home_teams, ncaaf_home_teams


if __name__ == "__main__":
    nfl_teams, ncaaf_teams = main()
