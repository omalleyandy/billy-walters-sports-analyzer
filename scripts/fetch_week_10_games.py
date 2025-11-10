#!/usr/bin/env python3
"""Fetch Week 10 NFL game results from ESPN."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.espn_client import ESPNClient


async def fetch_week_10_games():
    """Fetch Week 10 NFL games from ESPN."""
    print("Fetching NFL Week 10 games from ESPN...")
    print("-" * 60)

    async with ESPNClient() as client:
        # Get Week 10 scoreboard
        scoreboard = await client.get_scoreboard("NFL", week=10, season=2024)
        events = scoreboard.get("events", [])

        print(f"Found {len(events)} games for Week 10")

        games = []

        for event in events:
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

            # Check if game is completed
            status = event.get("status", {}).get("type", {}).get("name", "")
            if status != "STATUS_FINAL":
                print(f"  Skipping {away_team['team']['displayName']} @ {home_team['team']['displayName']} - Status: {status}")
                continue

            # Extract scores
            home_score = int(home_team.get("score", 0))
            away_score = int(away_team.get("score", 0))

            # Get date
            date_str = event.get("date", "")
            if date_str:
                game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date().isoformat()
            else:
                game_date = "2024-11-10"  # Default for Week 10

            game = {
                "week": 10,
                "date": game_date,
                "home_team": home_team["team"]["displayName"],
                "away_team": away_team["team"]["displayName"],
                "home_score": home_score,
                "away_score": away_score,
                "home_injury_level": 0.0,
                "away_injury_level": 0.0,
                "location": "home"
            }

            games.append(game)
            print(f"  [OK] {away_team['team']['displayName']} @ {home_team['team']['displayName']} ({away_score}-{home_score})")

        # Save to file
        output_dir = project_root / "output" / "unified"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "nfl_week_10_games.json"

        with open(output_file, 'w') as f:
            json.dump({"games": games}, f, indent=2)

        print(f"\n[SUCCESS] Saved {len(games)} completed games to {output_file}")
        return len(games)


if __name__ == "__main__":
    result = asyncio.run(fetch_week_10_games())
    sys.exit(0 if result > 0 else 1)
