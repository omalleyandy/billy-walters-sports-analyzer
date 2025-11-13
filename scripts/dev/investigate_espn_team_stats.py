#!/usr/bin/env python3
"""
ESPN Team Statistics API Investigation Script
Tests various ESPN API endpoints to find team statistics data
"""

import json
import requests
from typing import Dict, Optional


class ESPNAPIInvestigator:
    """Investigates ESPN API endpoints for team statistics"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        # Test with a few well-known teams
        self.test_teams = {
            "ohio-state": "194",  # Ohio State Buckeyes
            "alabama": "333",  # Alabama Crimson Tide
            "georgia": "61",  # Georgia Bulldogs
            "michigan": "130",  # Michigan Wolverines
        }

    def test_endpoint(self, url: str, description: str) -> Optional[Dict]:
        """Test an API endpoint and return response"""
        print(f"\n{'=' * 70}")
        print(f"Testing: {description}")
        print(f"URL: {url}")
        print("=" * 70)

        try:
            response = self.session.get(url, timeout=30)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS! Response size: {len(json.dumps(data))} bytes")

                # Show sample of response structure
                if isinstance(data, dict):
                    print(f"Top-level keys: {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    print(f"List with {len(data)} items")

                return data
            else:
                print(f"FAILED: {response.status_code}")
                return None

        except Exception as e:
            print(f"ERROR: {e}")
            return None

    def investigate_team_endpoints(self, team_id: str, team_name: str):
        """Test various team-related endpoints"""
        print(f"\n\n{'#' * 70}")
        print(f"# INVESTIGATING: {team_name.upper()} (ID: {team_id})")
        print(f"{'#' * 70}")

        endpoints = [
            # Site API v2 - Team Profile
            (
                f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}",
                "Site API v2 - Team Profile",
            ),
            # Site API v2 - Team Statistics
            (
                f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/statistics",
                "Site API v2 - Team Statistics",
            ),
            # Core API - Team Statistics
            (
                f"https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/2025/teams/{team_id}/statistics",
                "Core API - Team Statistics (2025)",
            ),
            # Core API - Team (with stats link)
            (
                f"https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/2025/teams/{team_id}",
                "Core API - Team Profile (2025)",
            ),
            # Site API v2 - Team Schedule
            (
                f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/schedule",
                "Site API v2 - Team Schedule",
            ),
        ]

        results = {}
        for url, description in endpoints:
            data = self.test_endpoint(url, description)
            results[description] = data

        return results

    def analyze_statistics_response(self, data: Dict, endpoint_name: str):
        """Deep dive into statistics response structure"""
        print(f"\n\n{'*' * 70}")
        print(f"ANALYZING: {endpoint_name}")
        print("*" * 70)

        if not data:
            print("No data to analyze")
            return

        # Try to find statistics in the response
        stats_paths = [
            ("statistics", data.get("statistics")),
            ("stats", data.get("stats")),
            ("team.statistics", data.get("team", {}).get("statistics")),
            ("splits", data.get("splits")),
        ]

        for path, stats_data in stats_paths:
            if stats_data:
                print(f"\nFound statistics at: {path}")
                print(f"Type: {type(stats_data)}")

                # Show structure
                if isinstance(stats_data, dict):
                    print(f"Keys: {list(stats_data.keys())}")

                    # Look for categories
                    if "categories" in stats_data:
                        cats = stats_data["categories"]
                        print(f"\nCategories: {len(cats)}")
                        for cat in cats[:3]:
                            print(
                                f"  - {cat.get('name', 'Unknown')}: {len(cat.get('stats', []))} stats"
                            )

                    # Look for splits
                    if "splits" in stats_data:
                        splits = stats_data["splits"]
                        print(f"\nSplits: {type(splits)}")

                elif isinstance(stats_data, list):
                    print(f"List with {len(stats_data)} items")

        # Save full response for inspection
        filename = (
            f"output/espn/investigation_{endpoint_name.replace(' ', '_').lower()}.json"
        )
        try:
            import os

            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"\nSaved full response to: {filename}")
        except Exception as e:
            print(f"Could not save file: {e}")

    def extract_key_stats(self, data: Dict) -> Dict:
        """Try to extract key statistics from response"""
        stats = {
            "team_name": None,
            "points_per_game": None,
            "points_allowed_per_game": None,
            "total_yards_per_game": None,
            "yards_allowed_per_game": None,
            "turnover_margin": None,
        }

        # Try to find team name
        if "team" in data:
            stats["team_name"] = data["team"].get("displayName")

        # Try to find statistics
        # (This will need to be adjusted based on actual response structure)
        if "statistics" in data:
            stat_data = data["statistics"]
            # TODO: Parse based on actual structure discovered

        return stats


def main():
    """Run investigation"""
    print("=" * 70)
    print("ESPN TEAM STATISTICS API INVESTIGATION")
    print("=" * 70)

    investigator = ESPNAPIInvestigator()

    # Test with Ohio State first
    team_id = "194"
    team_name = "Ohio State"

    print(f"\nInvestigating endpoints for {team_name}...")
    results = investigator.investigate_team_endpoints(team_id, team_name)

    # Analyze any successful responses
    for endpoint_name, data in results.items():
        if data:
            investigator.analyze_statistics_response(data, endpoint_name)

    print("\n" + "=" * 70)
    print("INVESTIGATION COMPLETE")
    print("=" * 70)
    print("\nCheck output/espn/ for saved responses")
    print("Review the structure to determine best endpoint for team statistics")


if __name__ == "__main__":
    main()
