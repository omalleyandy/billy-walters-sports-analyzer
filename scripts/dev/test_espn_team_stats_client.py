#!/usr/bin/env python3
"""
Test ESPN Team Statistics Client Methods
Validates new team statistics functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from data.espn_api_client import ESPNAPIClient


def test_team_statistics():
    """Test get_team_statistics method"""
    print("=" * 70)
    print("TEST 1: Get Team Statistics (Ohio State)")
    print("=" * 70)

    client = ESPNAPIClient()

    try:
        stats = client.get_team_statistics("194", "college-football")

        print(f"[OK] Status: {stats.get('status')}")
        print(f"[OK] Team: {stats.get('team', {}).get('displayName')}")
        print(f"[OK] Season: {stats.get('season', {}).get('year')}")

        # Check structure
        assert "results" in stats, "Missing 'results' key"
        assert "stats" in stats["results"], "Missing 'stats' key"
        assert "opponent" in stats["results"], "Missing 'opponent' key"

        categories = stats["results"]["stats"]["categories"]
        print(f"[OK] Team stat categories: {len(categories)}")

        opponent_categories = stats["results"]["opponent"]
        print(f"[OK] Opponent stat categories: {len(opponent_categories)}")

        print("\n[SUCCESS] get_team_statistics() working correctly\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] get_team_statistics() failed: {e}\n")
        return False


def test_power_rating_metrics():
    """Test extract_power_rating_metrics method"""
    print("=" * 70)
    print("TEST 2: Extract Power Rating Metrics")
    print("=" * 70)

    client = ESPNAPIClient()

    test_teams = [
        ("194", "Ohio State"),
        ("333", "Alabama"),
        ("61", "Georgia"),
        ("130", "Michigan"),
    ]

    all_passed = True

    for team_id, team_name in test_teams:
        print(f"\nTesting: {team_name} (ID: {team_id})")
        print("-" * 70)

        try:
            metrics = client.extract_power_rating_metrics(team_id, "college-football")

            # Check required fields
            required_fields = [
                "team_id",
                "team_name",
                "games_played",
                "points_per_game",
                "points_allowed_per_game",
                "total_yards_per_game",
                "total_yards_allowed_per_game",
                "turnover_margin",
            ]

            for field in required_fields:
                if field not in metrics:
                    print(f"  [ERROR] Missing field: {field}")
                    all_passed = False
                    continue

                value = metrics[field]
                print(f"  [OK] {field}: {value}")

            # Display offensive efficiency
            ppg = metrics.get("points_per_game", 0)
            ypg = metrics.get("total_yards_per_game", 0)
            print("\n  Offensive Efficiency:")
            print(f"    Points/Game: {ppg:.1f}")
            print(f"    Yards/Game: {ypg:.1f}")

            # Display defensive efficiency
            papg = metrics.get("points_allowed_per_game", 0)
            yapg = metrics.get("total_yards_allowed_per_game", 0)
            print("\n  Defensive Efficiency:")
            print(f"    Points Allowed/Game: {papg:.1f}")
            print(f"    Yards Allowed/Game: {yapg:.1f}")

            # Display turnover margin
            to_margin = metrics.get("turnover_margin", 0)
            print(f"\n  Turnover Margin: {to_margin:+.0f}")

            print(f"\n  [SUCCESS] {team_name} metrics extracted")

        except Exception as e:
            print(f"  [ERROR] Failed to extract metrics: {e}")
            all_passed = False

    if all_passed:
        print("\n" + "=" * 70)
        print("[SUCCESS] All power rating metrics tests passed")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("[ERROR] Some tests failed")
        print("=" * 70)

    return all_passed


def test_fbs_teams_list():
    """Test get_all_fbs_teams method"""
    print("\n" + "=" * 70)
    print("TEST 3: Get All FBS Teams")
    print("=" * 70)

    client = ESPNAPIClient()

    try:
        data = client.get_all_fbs_teams()

        # Extract teams from response
        sports = data.get("sports", [])
        if not sports:
            print("[ERROR] No sports data in response")
            return False

        leagues = sports[0].get("leagues", [])
        if not leagues:
            print("[ERROR] No leagues data in response")
            return False

        teams_data = leagues[0].get("teams", [])
        print(f"[OK] Total FBS teams: {len(teams_data)}")

        # Show sample teams
        print("\nSample teams:")
        for i, team_item in enumerate(teams_data[:10]):
            team = team_item.get("team", {})
            team_id = team.get("id")
            team_name = team.get("displayName")
            team_abbr = team.get("abbreviation")
            print(f"  {i + 1}. {team_name} ({team_abbr}) - ID: {team_id}")

        print("\n[SUCCESS] get_all_fbs_teams() working correctly")
        print(f"[INFO] Can collect stats for all {len(teams_data)} FBS teams\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] get_all_fbs_teams() failed: {e}\n")
        return False


def calculate_sample_power_rating():
    """Demonstrate power rating calculation with team stats"""
    print("=" * 70)
    print("TEST 4: Sample Power Rating Calculation")
    print("=" * 70)

    client = ESPNAPIClient()

    # League averages (approximate 2024 FBS)
    LEAGUE_AVG_PPG = 28.5
    LEAGUE_AVG_PAPG = 28.5

    try:
        # Get Ohio State metrics
        metrics = client.extract_power_rating_metrics("194", "college-football")

        team_name = metrics["team_name"]
        ppg = metrics["points_per_game"]
        papg = metrics["points_allowed_per_game"]
        to_margin = metrics["turnover_margin"]

        print(f"\nTeam: {team_name}")
        print(f"Points Per Game: {ppg:.1f}")
        print(f"Points Allowed Per Game: {papg:.1f}")
        print(f"Turnover Margin: {to_margin:+.0f}")

        # Simulated base Massey rating
        base_massey = 90.0

        # Calculate adjustments
        offensive_adj = (ppg - LEAGUE_AVG_PPG) * 0.15
        defensive_adj = (LEAGUE_AVG_PAPG - papg) * 0.15
        turnover_adj = to_margin * 0.3

        enhanced_rating = base_massey + offensive_adj + defensive_adj + turnover_adj

        print(f"\n{'Power Rating Calculation:'}")
        print(f"  Base (Massey): {base_massey:.2f}")
        print(f"  Offensive Adj: {offensive_adj:+.2f}")
        print(f"  Defensive Adj: {defensive_adj:+.2f}")
        print(f"  Turnover Adj: {turnover_adj:+.2f}")
        print(f"  {'=' * 40}")
        print(f"  Enhanced Rating: {enhanced_rating:.2f}")

        print("\n[SUCCESS] Power rating calculation complete")
        print(
            f"[INFO] {team_name} shows elite performance (rating: {enhanced_rating:.1f})\n"
        )

        return True

    except Exception as e:
        print(f"\n[ERROR] Power rating calculation failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "#" * 70)
    print("# ESPN TEAM STATISTICS CLIENT TEST SUITE")
    print("#" * 70 + "\n")

    results = []

    # Run tests
    results.append(("Team Statistics", test_team_statistics()))
    results.append(("Power Rating Metrics", test_power_rating_metrics()))
    results.append(("FBS Teams List", test_fbs_teams_list()))
    results.append(("Power Rating Calculation", calculate_sample_power_rating()))

    # Summary
    print("\n" + "#" * 70)
    print("# TEST SUMMARY")
    print("#" * 70)

    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n[SUCCESS] All tests passed! ESPN team stats client is ready.")
        print("[INFO] Ready to integrate into Billy Walters power ratings.")
        return 0
    else:
        print(f"\n[ERROR] {total_tests - passed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
