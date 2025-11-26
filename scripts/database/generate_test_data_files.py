#!/usr/bin/env python3
"""
Generate Test Data Files for Edge Detection
Creates sample power ratings, odds, and game data for testing edge detector
"""

import json
from pathlib import Path


def generate_power_ratings():
    """Generate sample power ratings for Week 12"""
    ratings_dict = {}
    teams = {
        "Buffalo Bills": 92.5,
        "Kansas City Chiefs": 94.0,
        "Detroit Lions": 91.5,
        "Chicago Bears": 80.0,
        "Denver Broncos": 88.5,
        "New England Patriots": 82.0,
        "Dallas Cowboys": 89.5,
        "Washington Commanders": 85.0,
        "Green Bay Packers": 90.5,
        "Minnesota Vikings": 87.5,
    }

    for team, rating in teams.items():
        ratings_dict[team] = rating

    # Format expected by load_proprietary_ratings
    data = {"ratings": ratings_dict}

    path = Path("data/power_ratings")
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / "nfl_2025_week_12.json"

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[OK] Generated power ratings: {filepath}")
    return ratings_dict


def generate_action_network_odds():
    """Generate sample Action Network odds in expected format"""
    games = [
        {
            "id": 1,
            "sport": "nfl",
            "teams": [
                {"display_name": "Kansas City Chiefs", "id": "KCC"},
                {"display_name": "Buffalo Bills", "id": "BUF"},
            ],
            "start_time": "2025-11-24T22:30:00Z",
            "markets": {
                "draftkings": {
                    "event": {
                        "spread": [{"value": -3.5, "odds": -110}],
                        "total": [
                            {"value": 44.5, "odds": -110},
                            {"value": 44.5, "odds": -110},
                        ],
                    }
                }
            },
        },
        {
            "id": 2,
            "sport": "nfl",
            "teams": [
                {"display_name": "Detroit Lions", "id": "DET"},
                {"display_name": "Chicago Bears", "id": "CHI"},
            ],
            "start_time": "2025-11-27T12:30:00Z",
            "markets": {
                "draftkings": {
                    "event": {
                        "spread": [{"value": -11.0, "odds": -110}],
                        "total": [
                            {"value": 48.5, "odds": -110},
                            {"value": 48.5, "odds": -110},
                        ],
                    }
                }
            },
        },
        {
            "id": 3,
            "sport": "nfl",
            "teams": [
                {"display_name": "Denver Broncos", "id": "DEN"},
                {"display_name": "New England Patriots", "id": "NE"},
            ],
            "start_time": "2025-11-27T15:15:00Z",
            "markets": {
                "draftkings": {
                    "event": {
                        "spread": [{"value": -6.0, "odds": -110}],
                        "total": [
                            {"value": 41.5, "odds": -110},
                            {"value": 41.5, "odds": -110},
                        ],
                    }
                }
            },
        },
        {
            "id": 4,
            "sport": "nfl",
            "teams": [
                {"display_name": "Dallas Cowboys", "id": "DAL"},
                {"display_name": "Washington Commanders", "id": "WAS"},
            ],
            "start_time": "2025-11-27T15:15:00Z",
            "markets": {
                "draftkings": {
                    "event": {
                        "spread": [{"value": -4.5, "odds": -110}],
                        "total": [
                            {"value": 48.0, "odds": -110},
                            {"value": 48.0, "odds": -110},
                        ],
                    }
                }
            },
        },
        {
            "id": 5,
            "sport": "nfl",
            "teams": [
                {"display_name": "Green Bay Packers", "id": "GB"},
                {"display_name": "Minnesota Vikings", "id": "MIN"},
            ],
            "start_time": "2025-11-27T20:20:00Z",
            "markets": {
                "draftkings": {
                    "event": {
                        "spread": [{"value": -3.0, "odds": -110}],
                        "total": [
                            {"value": 46.0, "odds": -110},
                            {"value": 46.0, "odds": -110},
                        ],
                    }
                }
            },
        },
    ]

    odds_response = [{"url": "scoreboard", "data": {"games": games}}]

    path = Path("output/action_network")
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / "nfl_api_responses_week_11.json"

    with open(filepath, "w") as f:
        json.dump(odds_response, f, indent=2)

    print(f"[OK] Generated odds data: {filepath}")
    return odds_response


def generate_massey_ratings():
    """Generate sample Massey ratings in expected format"""
    teams = [
        {
            "team": "Buffalo Bills",
            "rating": 9.25,  # Massey scale: 7-10
            "rawData": {
                "wins": 10,
                "losses": 2,
                "off": 20.5,
                "def": -18.0,
            },
        },
        {
            "team": "Kansas City Chiefs",
            "rating": 9.4,
            "rawData": {
                "wins": 10,
                "losses": 2,
                "off": 22.0,
                "def": -20.5,
            },
        },
        {
            "team": "Detroit Lions",
            "rating": 9.15,
            "rawData": {
                "wins": 9,
                "losses": 3,
                "off": 19.5,
                "def": -17.5,
            },
        },
        {
            "team": "Chicago Bears",
            "rating": 8.0,
            "rawData": {
                "wins": 4,
                "losses": 8,
                "off": 5.0,
                "def": -25.0,
            },
        },
        {
            "team": "Denver Broncos",
            "rating": 8.85,
            "rawData": {
                "wins": 8,
                "losses": 4,
                "off": 16.5,
                "def": -19.0,
            },
        },
        {
            "team": "New England Patriots",
            "rating": 8.2,
            "rawData": {
                "wins": 5,
                "losses": 7,
                "off": 7.0,
                "def": -23.0,
            },
        },
        {
            "team": "Dallas Cowboys",
            "rating": 8.95,
            "rawData": {
                "wins": 9,
                "losses": 3,
                "off": 17.5,
                "def": -18.0,
            },
        },
        {
            "team": "Washington Commanders",
            "rating": 8.5,
            "rawData": {
                "wins": 7,
                "losses": 5,
                "off": 12.0,
                "def": -21.0,
            },
        },
        {
            "team": "Green Bay Packers",
            "rating": 9.05,
            "rawData": {
                "wins": 9,
                "losses": 3,
                "off": 18.5,
                "def": -17.5,
            },
        },
        {
            "team": "Minnesota Vikings",
            "rating": 8.75,
            "rawData": {
                "wins": 8,
                "losses": 4,
                "off": 15.5,
                "def": -20.0,
            },
        },
    ]

    massey_data = {"teams": teams}

    path = Path("output/massey")
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / "nfl_ratings_20251113_153241.json"

    with open(filepath, "w") as f:
        json.dump(massey_data, f, indent=2)

    print(f"[OK] Generated Massey ratings: {filepath}")
    return massey_data


def main():
    """Generate all test data files"""
    print("=" * 80)
    print("GENERATING TEST DATA FILES FOR EDGE DETECTION")
    print("=" * 80)

    generate_power_ratings()
    generate_action_network_odds()
    generate_massey_ratings()

    print("=" * 80)
    print("[OK] All test data files generated!")
    print("You can now run edge detector:")
    print("uv run python -m walters_analyzer.valuation.billy_walters_edge_detector")
    print("=" * 80)


if __name__ == "__main__":
    main()
