#!/usr/bin/env python3
"""Check how many FBS teams ESPN API returns"""

import sys
sys.path.insert(0, 'src')

from data.espn_api_client import ESPNAPIClient

client = ESPNAPIClient()
teams = client.get_all_fbs_teams()
team_list = teams['sports'][0]['leagues'][0]['teams']

print(f"Total FBS teams from API: {len(team_list)}")
print(f"\nFirst 10 teams:")
for t in team_list[:10]:
    print(f"  - {t['team']['displayName']} (ID: {t['team']['id']})")

print(f"\nLast 10 teams:")
for t in team_list[-10:]:
    print(f"  - {t['team']['displayName']} (ID: {t['team']['id']})")

# Check if Northern Illinois and UMass are included
niu = [t for t in team_list if 'Northern Illinois' in t['team']['displayName']]
umass = [t for t in team_list if 'Massachusetts' in t['team']['displayName'] or 'UMass' in t['team']['displayName']]

print(f"\nNorthern Illinois found: {len(niu) > 0}")
if niu:
    print(f"  - {niu[0]['team']['displayName']} (ID: {niu[0]['team']['id']})")

print(f"UMass found: {len(umass) > 0}")
if umass:
    print(f"  - {umass[0]['team']['displayName']} (ID: {umass[0]['team']['id']})")
