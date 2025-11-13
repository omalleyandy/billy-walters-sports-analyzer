#!/usr/bin/env python3
"""
Scrape ESPN Team Statistics for NCAAF/NFL
Collects offensive/defensive metrics for Billy Walters power rating calculations
"""

import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from data.espn_api_client import ESPNAPIClient


def scrape_all_team_stats(league="college-football", week=None):
    """
    Scrape team statistics for all teams in a league

    Args:
        league: 'college-football' or 'nfl'
        week: Week number (for filename)

    Returns:
        List of team metrics dictionaries
    """
    client = ESPNAPIClient()

    print("=" * 70)
    print(f"ESPN TEAM STATISTICS SCRAPER - {league.upper()}")
    print("=" * 70)

    # Get all teams
    if league == "college-football":
        print("\nFetching FBS teams from scoreboard...")

        # Use scoreboard-based team list (more complete than teams API)
        fbs_teams_file = Path("data/current/fbs_teams_from_scoreboard.json")

        if fbs_teams_file.exists():
            # Load from cached scoreboard extract
            with open(fbs_teams_file) as f:
                fbs_data = json.load(f)
                teams_list = [
                    {
                        "team": {
                            "id": t["id"],
                            "displayName": t["name"],
                            "abbreviation": t["abbreviation"],
                        }
                    }
                    for t in fbs_data["teams"]
                ]
            print(f"Loaded {len(teams_list)} teams from scoreboard cache")
        else:
            # Fallback to teams API (less complete, 50 teams)
            print("[WARNING] Scoreboard cache not found, using teams API (incomplete)")
            print("[INFO] Run: uv run python extract_fbs_teams_from_scoreboard.py")
            teams_data = client.get_all_fbs_teams()
            teams_list = teams_data["sports"][0]["leagues"][0]["teams"]

        league_short = "ncaaf"
    else:
        print("\nFetching NFL teams...")
        teams_data = client.get_nfl_teams()
        teams_list = teams_data["sports"][0]["leagues"][0]["teams"]
        league_short = "nfl"

    total_teams = len(teams_list)
    print(f"Found {total_teams} teams")
    print("\nCollecting statistics (rate limited: 1 request/second)...")

    # Collect stats for each team
    all_team_stats = []
    success_count = 0
    error_count = 0

    for i, team_item in enumerate(teams_list, 1):
        team = team_item["team"]
        team_id = team["id"]
        team_name = team["displayName"]
        team_abbr = team.get("abbreviation", "???")

        print(f"\n[{i}/{total_teams}] {team_name} ({team_abbr})...", end=" ")

        try:
            metrics = client.extract_power_rating_metrics(team_id, league)
            all_team_stats.append(metrics)
            success_count += 1
            print("[OK]")

            # Show key metrics
            ppg = metrics.get("points_per_game", 0)
            papg = metrics.get("points_allowed_per_game", 0)
            to_margin = metrics.get("turnover_margin", 0)
            print(
                f"    PPG: {ppg:.1f} | PA/G: {papg:.1f} | TO Margin: {to_margin:+.0f}"
            )

        except Exception as e:
            error_count += 1
            print(f"[ERROR] {e}")
            continue

        # Rate limiting (respectful to ESPN API)
        if i < total_teams:
            time.sleep(1.0)  # 1 second delay between requests

    # Summary statistics
    print(f"\n{'=' * 70}")
    print("COLLECTION SUMMARY")
    print("=" * 70)
    print(f"Total teams: {total_teams}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Success rate: {success_count / total_teams * 100:.1f}%")

    # Calculate league averages
    if all_team_stats:
        avg_ppg = sum(t["points_per_game"] for t in all_team_stats) / len(
            all_team_stats
        )
        avg_papg = sum(t["points_allowed_per_game"] for t in all_team_stats) / len(
            all_team_stats
        )

        print("\nLeague Averages:")
        print(f"  Points Per Game: {avg_ppg:.1f}")
        print(f"  Points Allowed Per Game: {avg_papg:.1f}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if week:
        filename = f"data/current/{league_short}_team_stats_week_{week}.json"
    else:
        filename = f"output/espn/{league_short}_team_stats_{timestamp}.json"

    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "timestamp": timestamp,
        "league": league,
        "week": week,
        "team_count": len(all_team_stats),
        "success_count": success_count,
        "error_count": error_count,
        "teams": all_team_stats,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n{'=' * 70}")
    print("[SUCCESS] Team statistics saved")
    print("=" * 70)
    print(f"File: {filename}")
    print(f"Size: {os.path.getsize(filename) / 1024:.1f} KB")
    print(f"Teams: {len(all_team_stats)}")

    return all_team_stats


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape ESPN team statistics for power ratings"
    )
    parser.add_argument(
        "--league",
        choices=["ncaaf", "nfl"],
        default="ncaaf",
        help="League to scrape (default: ncaaf)",
    )
    parser.add_argument(
        "--week", type=int, help="Week number (for filename in data/current/)"
    )

    args = parser.parse_args()

    # Map short names to ESPN API league names
    league_map = {"ncaaf": "college-football", "nfl": "nfl"}

    try:
        stats = scrape_all_team_stats(league_map[args.league], args.week)

        if stats:
            print("\n[INFO] Ready to integrate into power rating calculations")
            print(
                "[INFO] Use metrics: points_per_game, points_allowed_per_game, turnover_margin"
            )
            return 0
        else:
            print("\n[ERROR] No stats collected")
            return 1

    except KeyboardInterrupt:
        print("\n\n[INFO] Scraping interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n[ERROR] Scraping failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
