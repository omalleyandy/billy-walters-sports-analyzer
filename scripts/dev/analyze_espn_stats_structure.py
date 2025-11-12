#!/usr/bin/env python3
"""
Analyze ESPN Team Statistics Response Structure
Extracts key metrics for Billy Walters power ratings
"""

import json


def extract_stat_value(stats_list, stat_name):
    """Extract a specific stat value from stats list"""
    for stat in stats_list:
        if stat["name"] == stat_name:
            return stat.get("value"), stat.get("displayValue")
    return None, None


def analyze_team_stats(file_path):
    """Analyze team statistics from ESPN API response"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    team = data.get("team", {})
    print("=" * 70)
    print(f"TEAM: {team.get('displayName', 'Unknown')}")
    print("=" * 70)

    categories = data["results"]["stats"]["categories"]

    # Key metrics for Billy Walters power ratings
    key_metrics = {
        "Offensive Metrics": [],
        "Defensive Metrics": [],
        "Special Teams": [],
        "Scoring": [],
    }

    # Process each category
    for category in categories:
        cat_name = category["name"]
        stats = category["stats"]

        if cat_name == "general":
            print(f"\n{'=' * 70}")
            print("GENERAL STATS")
            print("=" * 70)
            for stat in stats:
                print(
                    f"{stat['displayName']}: {stat.get('displayValue', 'N/A')} ({stat['name']})"
                )
                if "perGame" in stat["name"].lower():
                    key_metrics["Offensive Metrics"].append(
                        (stat["displayName"], stat.get("displayValue"))
                    )

        elif cat_name == "scoring":
            print(f"\n{'=' * 70}")
            print("SCORING STATS")
            print("=" * 70)
            for stat in stats:
                print(
                    f"{stat['displayName']}: {stat.get('displayValue', 'N/A')} ({stat['name']})"
                )
                key_metrics["Scoring"].append(
                    (stat["displayName"], stat.get("displayValue"))
                )

        elif cat_name == "defensive":
            print(f"\n{'=' * 70}")
            print("DEFENSIVE STATS")
            print("=" * 70)
            for stat in stats[:15]:  # Show first 15
                print(
                    f"{stat['displayName']}: {stat.get('displayValue', 'N/A')} ({stat['name']})"
                )
                if "perGame" in stat["name"].lower() or stat["name"] in [
                    "sacks",
                    "totalTackles",
                ]:
                    key_metrics["Defensive Metrics"].append(
                        (stat["displayName"], stat.get("displayValue"))
                    )

        elif cat_name == "miscellaneous":
            print(f"\n{'=' * 70}")
            print("MISCELLANEOUS STATS (Turnovers, etc.)")
            print("=" * 70)
            for stat in stats:
                print(
                    f"{stat['displayName']}: {stat.get('displayValue', 'N/A')} ({stat['name']})"
                )
                if stat["name"] in ["turnovers", "giveaways", "takeaways"]:
                    key_metrics["Offensive Metrics"].append(
                        (stat["displayName"], stat.get("displayValue"))
                    )

    # Print summary of key metrics for power ratings
    print(f"\n\n{'#' * 70}")
    print("# KEY METRICS FOR BILLY WALTERS POWER RATINGS")
    print(f"{'#' * 70}")

    for section, metrics in key_metrics.items():
        if metrics:
            print(f"\n{section}:")
            for name, value in metrics:
                print(f"  - {name}: {value}")

    # Identify most important stats
    print(f"\n\n{'*' * 70}")
    print("RECOMMENDED STATS FOR POWER RATING INTEGRATION")
    print("*" * 70)
    print(
        """
Priority 1 (Core):
  - Points Per Game (scoring)
  - Total Yards Per Game (general)
  - Turnovers (miscellaneous)
  - Yards Per Play (general - if available)

Priority 2 (Offensive):
  - Passing Yards Per Game (passing)
  - Rushing Yards Per Game (rushing)
  - Third Down Conversion % (general)
  - Red Zone Scoring % (general)

Priority 3 (Defensive):
  - Points Allowed Per Game (defensive)
  - Total Yards Allowed Per Game (defensive)
  - Sacks (defensive)
  - Takeaways (miscellaneous)
"""
    )


if __name__ == "__main__":
    file_path = "output/espn/investigation_site_api_v2_-_team_statistics.json"
    analyze_team_stats(file_path)
