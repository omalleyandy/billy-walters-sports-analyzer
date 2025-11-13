"""Fetch MAC team statistics for matchup analysis."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.espn_api_client import ESPNAPIClient


def get_mac_team_stats():
    """Fetch Toledo and Miami OH team statistics."""
    client = ESPNAPIClient()

    try:
        # Get all NCAAF teams
        teams_data = client.get_ncaaf_teams()
        teams = teams_data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])

        # Find Toledo and Miami OH
        toledo = None
        miami_oh = None

        for team_item in teams:
            team = team_item.get("team", {})
            name = team.get("displayName", "")
            if "Toledo" in name:
                toledo = team
            elif "Miami" in name and ("RedHawks" in name or "OH" in name):
                miami_oh = team

        print("=" * 70)
        print("MAC TEAM INFORMATION")
        print("=" * 70)

        if toledo:
            print(f"\nToledo Rockets:")
            print(f"  Team ID: {toledo.get('id')}")
            print(f"  Full Name: {toledo.get('displayName')}")
            print(f"  Abbreviation: {toledo.get('abbreviation')}")

            # Get team statistics
            stats = client.get_team_statistics(toledo.get("id"), "college-football")
            if stats:
                print(f"\nOffensive Stats:")
                print(f"  Points/Game: {stats.get('points_per_game', 0):.1f}")
                print(f"  Total Yards/Game: {stats.get('total_yards_per_game', 0):.1f}")
                print(
                    f"  Passing Yards/Game: {stats.get('passing_yards_per_game', 0):.1f}"
                )
                print(
                    f"  Rushing Yards/Game: {stats.get('rushing_yards_per_game', 0):.1f}"
                )
                print(f"\nDefensive Stats:")
                print(
                    f"  Points Allowed/Game: "
                    f"{stats.get('points_allowed_per_game', 0):.1f}"
                )
                print(
                    f"  Total Yards Allowed/Game: "
                    f"{stats.get('total_yards_allowed_per_game', 0):.1f}"
                )
                print(f"\nTurnover Stats:")
                print(f"  Turnover Margin: {stats.get('turnover_margin', 0)}")
                print(f"  Takeaways: {stats.get('takeaways', 0)}")
                print(f"  Giveaways: {stats.get('giveaways', 0)}")

        if miami_oh:
            print(f"\n\nMiami (OH) RedHawks:")
            print(f"  Team ID: {miami_oh.get('id')}")
            print(f"  Full Name: {miami_oh.get('displayName')}")
            print(f"  Abbreviation: {miami_oh.get('abbreviation')}")

            # Get team statistics
            stats = client.get_team_statistics(miami_oh.get("id"), "college-football")
            if stats:
                print(f"\nOffensive Stats:")
                print(f"  Points/Game: {stats.get('points_per_game', 0):.1f}")
                print(f"  Total Yards/Game: {stats.get('total_yards_per_game', 0):.1f}")
                print(
                    f"  Passing Yards/Game: {stats.get('passing_yards_per_game', 0):.1f}"
                )
                print(
                    f"  Rushing Yards/Game: {stats.get('rushing_yards_per_game', 0):.1f}"
                )
                print(f"\nDefensive Stats:")
                print(
                    f"  Points Allowed/Game: "
                    f"{stats.get('points_allowed_per_game', 0):.1f}"
                )
                print(
                    f"  Total Yards Allowed/Game: "
                    f"{stats.get('total_yards_allowed_per_game', 0):.1f}"
                )
                print(f"\nTurnover Stats:")
                print(f"  Turnover Margin: {stats.get('turnover_margin', 0)}")
                print(f"  Takeaways: {stats.get('takeaways', 0)}")
                print(f"  Giveaways: {stats.get('giveaways', 0)}")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    get_mac_team_stats()
