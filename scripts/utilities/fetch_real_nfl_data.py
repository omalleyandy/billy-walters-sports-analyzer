#!/usr/bin/env python3
"""
Fetch REAL 2024 NFL game results from ESPN API
Replaces the placeholder data with actual game outcomes
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.espn_client import ESPNClient


async def fetch_real_2024_nfl_data():
    """Fetch actual 2024 NFL game results for weeks 1-10"""
    print("=" * 70)
    print("FETCHING REAL 2024 NFL DATA FROM ESPN")
    print("=" * 70)
    print()

    all_games = []

    async with ESPNClient() as client:
        # Fetch weeks 1-10
        for week in range(1, 11):
            print(f"\nFetching Week {week}...")

            try:
                scoreboard = await client.get_scoreboard("NFL", week=week, season=2024)
                events = scoreboard.get("events", [])

                week_games = []

                for event in events:
                    # Only process completed games
                    status = event.get("status", {}).get("type", {})
                    if status.get("name") != "STATUS_FINAL":
                        continue

                    competition = event.get("competitions", [{}])[0]
                    competitors = competition.get("competitors", [])

                    if len(competitors) < 2:
                        continue

                    # Find home and away teams
                    home_team = None
                    away_team = None

                    for comp in competitors:
                        if comp.get("homeAway") == "home":
                            home_team = comp
                        elif comp.get("homeAway") == "away":
                            away_team = comp

                    if not home_team or not away_team:
                        continue

                    # Extract game data
                    game_date = event.get("date", "")
                    if game_date:
                        game_date = (
                            datetime.fromisoformat(game_date.replace("Z", "+00:00"))
                            .date()
                            .isoformat()
                        )

                    game = {
                        "week": week,
                        "date": game_date,
                        "home_team": home_team["team"]["displayName"],
                        "away_team": away_team["team"]["displayName"],
                        "home_score": int(home_team.get("score", 0)),
                        "away_score": int(away_team.get("score", 0)),
                        "home_injury_level": 0.0,
                        "away_injury_level": 0.0,
                        "location": "home",
                    }

                    week_games.append(game)
                    all_games.append(game)

                print(f"  [OK] Fetched {len(week_games)} completed games")

                # Show sample
                if week_games:
                    sample = week_games[0]
                    print(
                        f"  Example: {sample['away_team']} @ {sample['home_team']} ({sample['away_score']}-{sample['home_score']})"
                    )

            except Exception as e:
                print(f"  ERROR fetching Week {week}: {e}")
                continue

    # Save to file
    output_file = project_root / "data" / "nfl_2024_games_weeks_1_10_REAL.json"

    output_data = {
        "season": "2024",
        "weeks": "1-10",
        "source": "ESPN API - Actual 2024 NFL Season Results",
        "fetched": datetime.now().isoformat(),
        "note": "Real game data from ESPN - NOT simulated",
        "total_games": len(all_games),
        "games": all_games,
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print()
    print("=" * 70)
    print(f"[SUCCESS] Saved {len(all_games)} real games to:")
    print(f"  {output_file}")
    print("=" * 70)
    print()

    # Validate New Orleans data
    print("VALIDATING NEW ORLEANS DATA:")
    print("-" * 70)

    no_games = [
        g
        for g in all_games
        if "New Orleans" in g["home_team"] or "New Orleans" in g["away_team"]
    ]

    wins = 0
    losses = 0

    for game in no_games[:9]:  # First 9 weeks
        home = game["home_team"]
        away = game["away_team"]
        home_score = game["home_score"]
        away_score = game["away_score"]

        if "New Orleans" in home:
            result = "W" if home_score > away_score else "L"
            score = f"{home_score}-{away_score}"
        else:
            result = "W" if away_score > home_score else "L"
            score = f"{away_score}-{home_score}"

        if result == "W":
            wins += 1
        else:
            losses += 1

        opponent = away if "New Orleans" in home else home
        print(f"Week {game['week']:2d}: {result} vs {opponent:20s} {score}")

    print(f"\nNew Orleans Record (Weeks 1-9): {wins}-{losses}")
    print()

    return len(all_games)


if __name__ == "__main__":
    result = asyncio.run(fetch_real_2024_nfl_data())
    sys.exit(0 if result > 0 else 1)
