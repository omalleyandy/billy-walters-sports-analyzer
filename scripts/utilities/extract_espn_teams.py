#!/usr/bin/env python3
"""
Extract NFL and NCAAF team IDs from ESPN API for use in other loaders.

This script helps identify the correct team structure from ESPN's API responses
and can be used as a reference for team ID extraction in other loaders.
"""

import sys
import os
import json

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.data.espn_api_client import ESPNAPIClient


def extract_nfl_teams() -> dict:
    """Extract NFL teams from ESPN API."""
    print("Fetching NFL teams from ESPN API...")
    api = ESPNAPIClient()
    data = api.get_nfl_teams()

    teams = {}
    try:
        sports = data.get("sports", [])
        if sports:
            sport = sports[0]
            leagues = sport.get("leagues", [])
            if leagues:
                league = leagues[0]
                team_list = league.get("teams", [])
                for team_entry in team_list:
                    team = team_entry.get("team", {})
                    team_id = team.get("id")
                    team_name = team.get("displayName")
                    if team_id and team_name:
                        teams[team_id] = team_name
    except Exception as e:
        print(f"Error parsing NFL teams: {e}")

    print(f"Extracted {len(teams)} NFL teams")
    return teams


def extract_ncaaf_teams() -> dict:
    """Extract NCAAF FBS teams from ESPN API."""
    print("Fetching NCAAF teams from ESPN API...")
    api = ESPNAPIClient()
    data = api.get_ncaaf_teams(group="80")  # FBS

    teams = {}
    try:
        sports = data.get("sports", [])
        if sports:
            sport = sports[0]
            leagues = sport.get("leagues", [])
            if leagues:
                league = leagues[0]
                team_list = league.get("teams", [])
                for team_entry in team_list:
                    team = team_entry.get("team", {})
                    team_id = team.get("id")
                    team_name = team.get("displayName")
                    if team_id and team_name:
                        teams[team_id] = team_name
    except Exception as e:
        print(f"Error parsing NCAAF teams: {e}")

    print(f"Extracted {len(teams)} NCAAF FBS teams")
    return teams


def main():
    """Extract and display teams."""
    print("=" * 70)
    print("EXTRACT ESPN TEAMS")
    print("=" * 70)

    nfl_teams = extract_nfl_teams()
    ncaaf_teams = extract_ncaaf_teams()

    print("\n" + "=" * 70)
    print("NFL TEAMS (32)")
    print("=" * 70)
    for team_id, team_name in sorted(nfl_teams.items(), key=lambda x: x[1]):
        print(f"  {team_id:3s}: {team_name}")

    print("\n" + "=" * 70)
    print("NCAAF FBS TEAMS (136+)")
    print("=" * 70)
    for team_id, team_name in sorted(ncaaf_teams.items(), key=lambda x: x[1]):
        print(f"  {team_id:3s}: {team_name}")

    # Save to JSON for reference
    output_file = os.path.join(os.getcwd(), "data", "current", "espn_teams.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump({"nfl": nfl_teams, "ncaaf": ncaaf_teams}, f, indent=2)
    print(f"\nSaved team list to: {output_file}")


if __name__ == "__main__":
    main()
