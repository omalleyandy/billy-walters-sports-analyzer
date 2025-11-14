#!/usr/bin/env python3
"""Quick analysis script for Northern Illinois vs UMass"""

import asyncio
import sys

sys.path.insert(0, "src")

from data.espn_api_client import ESPNAPIClient


async def main():
    client = ESPNAPIClient()

    # Get team statistics
    print("Fetching team statistics from ESPN...")
    niu = await client.get_team_statistics(2459, "college-football")
    umass = await client.get_team_statistics(113, "college-football")

    print("\n" + "=" * 70)
    print("NORTHERN ILLINOIS HUSKIES")
    print("=" * 70)
    print(f"  Points Per Game:          {niu.get('points_per_game', 'N/A')}")
    print(f"  Total Yards/Game:         {niu.get('yards_per_game', 'N/A')}")
    print(f"  Passing Yards/Game:       {niu.get('passing_yards_per_game', 'N/A')}")
    print(f"  Rushing Yards/Game:       {niu.get('rushing_yards_per_game', 'N/A')}")
    print(f"  Points Allowed/Game:      {niu.get('points_allowed_per_game', 'N/A')}")
    print(f"  Yards Allowed/Game:       {niu.get('yards_allowed_per_game', 'N/A')}")
    print(f"  Turnover Margin:          {niu.get('turnover_margin', 'N/A')}")
    print(f"  3rd Down %:               {niu.get('third_down_pct', 'N/A')}")

    print("\n" + "=" * 70)
    print("MASSACHUSETTS MINUTEMEN")
    print("=" * 70)
    print(f"  Points Per Game:          {umass.get('points_per_game', 'N/A')}")
    print(f"  Total Yards/Game:         {umass.get('yards_per_game', 'N/A')}")
    print(f"  Passing Yards/Game:       {umass.get('passing_yards_per_game', 'N/A')}")
    print(f"  Rushing Yards/Game:       {umass.get('rushing_yards_per_game', 'N/A')}")
    print(f"  Points Allowed/Game:      {umass.get('points_allowed_per_game', 'N/A')}")
    print(f"  Yards Allowed/Game:       {umass.get('yards_allowed_per_game', 'N/A')}")
    print(f"  Turnover Margin:          {umass.get('turnover_margin', 'N/A')}")
    print(f"  3rd Down %:               {umass.get('third_down_pct', 'N/A')}")

    # Calculate matchup metrics
    print("\n" + "=" * 70)
    print("MATCHUP ANALYSIS")
    print("=" * 70)

    niu_ppg = niu.get("points_per_game", 0)
    umass_ppg = umass.get("points_per_game", 0)
    niu_papg = niu.get("points_allowed_per_game", 0)
    umass_papg = umass.get("points_allowed_per_game", 0)

    if niu_ppg and umass_papg:
        print(
            f"  NIU Offense vs UMass Defense: {niu_ppg:.1f} PPG vs {umass_papg:.1f} PA/G"
        )
    if umass_ppg and niu_papg:
        print(
            f"  UMass Offense vs NIU Defense: {umass_ppg:.1f} PPG vs {niu_papg:.1f} PA/G"
        )

    # Predicted total
    if all([niu_ppg, umass_ppg, niu_papg, umass_papg]):
        predicted_total = (niu_ppg + umass_ppg + niu_papg + umass_papg) / 2
        print(f"\n  Predicted Total (avg method): {predicted_total:.1f}")


if __name__ == "__main__":
    asyncio.run(main())
