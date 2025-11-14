#!/usr/bin/env python3
"""Check final scores for MACtion games on Nov 12, 2025"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, "src")

from data.espn_ncaaf_scoreboard_client import ESPNNCAAFScoreboardClient


async def main():
    print("=" * 70)
    print("MACTION TUESDAY - NOVEMBER 12, 2025 - FINAL SCORES")
    print("=" * 70)

    client = ESPNNCAAFScoreboardClient()
    await client.connect()

    try:
        # Get today's scoreboard (Nov 12)
        scoreboard = await client.get_scoreboard(
            date="20251112",
            groups=80,  # FBS
            limit=400,
        )

        events = scoreboard.get("events", [])

        # Find our three games
        target_games = [
            ("Northern Illinois", "Massachusetts"),
            ("Buffalo", "Central Michigan"),
            ("Toledo", "Miami"),
        ]

        found_games = []

        for event in events:
            name = event.get("name", "")
            competitions = event.get("competitions", [])

            if not competitions:
                continue

            comp = competitions[0]
            competitors = comp.get("competitors", [])

            if len(competitors) != 2:
                continue

            # Get team names
            teams = [c.get("team", {}).get("displayName", "") for c in competitors]

            # Check if this is one of our target games
            for target in target_games:
                if any(target[0] in t for t in teams) and any(
                    target[1] in t for t in teams
                ):
                    # Get scores
                    away_comp = [c for c in competitors if c.get("homeAway") == "away"][
                        0
                    ]
                    home_comp = [c for c in competitors if c.get("homeAway") == "home"][
                        0
                    ]

                    away_team = away_comp.get("team", {}).get("displayName", "")
                    home_team = home_comp.get("team", {}).get("displayName", "")
                    away_score = away_comp.get("score", "?")
                    home_score = home_comp.get("score", "?")

                    status = comp.get("status", {})
                    status_type = status.get("type", {}).get("description", "Unknown")
                    completed = status.get("type", {}).get("completed", False)

                    found_games.append(
                        {
                            "away_team": away_team,
                            "home_team": home_team,
                            "away_score": away_score,
                            "home_score": home_score,
                            "status": status_type,
                            "completed": completed,
                        }
                    )
                    break

        # Display results
        if not found_games:
            print("\n[WARNING] No games found - scoreboard may not be updated yet")
            print("\nTry manual check:")
            print("  https://www.espn.com/college-football/scoreboard/_/date/20251112")
        else:
            print(f"\nGames Found: {len(found_games)}/3\n")

            for i, game in enumerate(found_games, 1):
                print(f"\n{i}. {game['away_team']} @ {game['home_team']}")
                print(f"   Score: {game['away_score']} - {game['home_score']}")
                print(f"   Status: {game['status']}")

                if game["completed"]:
                    # Calculate margin
                    try:
                        margin = int(game["away_score"]) - int(game["home_score"])
                        winner = game["away_team"] if margin > 0 else game["home_team"]
                        print(f"   Winner: {winner} by {abs(margin)}")
                    except:
                        pass
                else:
                    print("   [INFO] Game not yet final")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
