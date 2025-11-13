#!/usr/bin/env python3
"""
Extract complete FBS team list from ESPN scoreboard data
Uses actual game schedule to identify all active FBS teams
"""

import json
import sys
from pathlib import Path

# Load scoreboard data
scoreboard_file = Path("data/raw/espn/scoreboard/20251112/20251112_153224_scoreboard.json")

if not scoreboard_file.exists():
    print(f"[ERROR] Scoreboard file not found: {scoreboard_file}")
    sys.exit(1)

with open(scoreboard_file) as f:
    scoreboard = json.load(f)

# Extract all teams from games
teams_dict = {}
events = scoreboard.get("events", [])

for event in events:
    competitions = event.get("competitions", [])
    for comp in competitions:
        competitors = comp.get("competitors", [])
        for competitor in competitors:
            team = competitor.get("team", {})
            team_id = team.get("id")
            team_name = team.get("displayName")
            team_abbr = team.get("abbreviation")

            if team_id and team_name:
                teams_dict[team_id] = {
                    "id": team_id,
                    "name": team_name,
                    "abbreviation": team_abbr,
                    "logo": team.get("logo"),
                    "location": team.get("location"),
                }

# Sort by name
teams_list = sorted(teams_dict.values(), key=lambda x: x["name"])

print("=" * 70)
print("FBS TEAMS EXTRACTED FROM SCOREBOARD")
print("=" * 70)
print(f"Total teams: {len(teams_list)}")
print(f"\nAll teams:")
for i, team in enumerate(teams_list, 1):
    print(f"{i:3d}. {team['name']:<40} ({team['abbreviation']}) - ID: {team['id']}")

# Check for specific teams
print("\n" + "=" * 70)
print("CHECKING SPECIFIC TEAMS")
print("=" * 70)

niu = [t for t in teams_list if 'Northern Illinois' in t['name']]
umass = [t for t in teams_list if 'Massachusetts' in t['name'] or 'UMass' in t['name']]

print(f"Northern Illinois found: {len(niu) > 0}")
if niu:
    print(f"  - {niu[0]['name']} (ID: {niu[0]['id']})")

print(f"UMass found: {len(umass) > 0}")
if umass:
    print(f"  - {umass[0]['name']} (ID: {umass[0]['id']})")

# Save to file for future use
output_file = Path("data/current/fbs_teams_from_scoreboard.json")
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w') as f:
    json.dump({
        "source": "ESPN scoreboard",
        "extracted_date": "2025-11-12",
        "week": 12,
        "team_count": len(teams_list),
        "teams": teams_list
    }, f, indent=2)

print(f"\n[OK] Saved team list to: {output_file}")
