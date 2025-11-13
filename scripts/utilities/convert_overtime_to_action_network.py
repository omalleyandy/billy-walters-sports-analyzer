#!/usr/bin/env python3
"""
Convert Overtime API odds format to Action Network format for edge detector

This script bridges the gap between Overtime's clean API format and the
Action Network format expected by the Billy Walters edge detector.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def convert_overtime_to_action_network(overtime_file: str, output_file: str):
    """
    Convert Overtime API format to Action Network format

    Args:
        overtime_file: Path to Overtime API walters format JSON
        output_file: Path to save Action Network format JSON
    """
    # Load Overtime data
    with open(overtime_file, "r") as f:
        overtime_data = json.load(f)

    # Create Action Network structure
    action_network_data = [
        {
            "url": "https://api.actionnetwork.com/web/v2/scoreboard/nfl",
            "data": {
                "league": {"id": 1, "name": "nfl", "display_name": "NFL"},
                "games": [],
            },
            "timestamp": datetime.now().isoformat(),
        }
    ]

    # Convert each game
    game_id_counter = 300000  # Start with high ID to avoid conflicts

    for game in overtime_data.get("games", []):
        # Skip duplicate entries (Overtime has game + half lines)
        if game.get("period") != "Game":
            continue

        # Parse game time (format: "11/13/2025 20:15")
        game_time_str = game.get("game_time", "")
        try:
            # Convert to ISO format
            dt = datetime.strptime(game_time_str, "%m/%d/%Y %H:%M")
            start_time = dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except:
            start_time = datetime.now().isoformat() + "Z"

        # Extract teams
        away_team = game.get("away_team", "")
        home_team = game.get("home_team", "")

        # Create game entry
        converted_game = {
            "id": game_id_counter,
            "league_id": 1,
            "status": "scheduled",
            "start_time": start_time,
            "league_name": "nfl",
            "type": "reg",
            "season": 2025,
            "week": 11,  # TODO: Auto-detect week
            "teams": [
                {
                    "id": game_id_counter * 10,
                    "display_name": home_team.split()[
                        -1
                    ],  # Extract team name (e.g., "Patriots" from "New England Patriots")
                    "location": " ".join(home_team.split()[:-1]),  # Extract location
                    "full_name": home_team,
                },
                {
                    "id": game_id_counter * 10 + 1,
                    "display_name": away_team.split()[-1],
                    "location": " ".join(away_team.split()[:-1]),
                    "full_name": away_team,
                },
            ],
            "markets": {
                "15": {  # Sportsbook ID
                    "event": {
                        "spread": [
                            {
                                "value": game.get("spread", {}).get("home", 0),
                                "line": game.get("spread", {}).get("home_odds", -110),
                                "bet_info": {
                                    "money": {"percent": 50},
                                    "tickets": {"percent": 50},
                                },
                            }
                        ],
                        "total": [
                            {
                                "value": game.get("total", {}).get("points", 47.0),
                                "over_line": game.get("total", {}).get(
                                    "over_odds", -110
                                ),
                                "under_line": game.get("total", {}).get(
                                    "under_odds", -110
                                ),
                            }
                        ],
                        "moneyline": [
                            {
                                "away": game.get("moneyline", {}).get("away", 100),
                                "home": game.get("moneyline", {}).get("home", -120),
                            }
                        ],
                    }
                }
            },
        }

        action_network_data[0]["data"]["games"].append(converted_game)
        game_id_counter += 1

    # Save converted data
    with open(output_file, "w") as f:
        json.dump(action_network_data, f, indent=2)

    print(f"[OK] Converted {len(action_network_data[0]['data']['games'])} games")
    print(f"[OK] Saved to: {output_file}")

    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python convert_overtime_to_action_network.py <overtime_file> [output_file]"
        )
        sys.exit(1)

    overtime_file = sys.argv[1]
    output_file = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "output/action_network/nfl_api_responses_converted.json"
    )

    convert_overtime_to_action_network(overtime_file, output_file)
