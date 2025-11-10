#!/usr/bin/env python3
"""
ESPN API Client
Simple REST API client for ESPN football data (NFL & NCAAF)
No authentication required!
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional


class ESPNAPIClient:
    """Client for ESPN's public REST APIs"""

    def __init__(self):
        """Initialize ESPN API client"""
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football"
        self.core_api_url = "https://sports.core.api.espn.com/v2/sports/football"
        self.web_api_url = "https://site.web.api.espn.com/apis/v3/sports/football"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    # Scoreboards (Live Scores)

    def get_nfl_scoreboard(self) -> Dict:
        """Get NFL scoreboard with live scores"""
        url = f"{self.base_url}/nfl/scoreboard"
        r = self.session.get(url, timeout=30)
        return r.json()

    def get_ncaaf_scoreboard(self) -> Dict:
        """Get NCAA Football scoreboard with live scores"""
        url = f"{self.base_url}/college-football/scoreboard"
        r = self.session.get(url, timeout=30)
        return r.json()

    # Game Details

    def get_game_summary(self, event_id: str, league: str = "nfl") -> Dict:
        """
        Get detailed game summary

        Args:
            event_id: ESPN event ID
            league: 'nfl' or 'college-football'
        """
        url = f"{self.base_url}/{league}/summary"
        params = {"event": event_id}
        r = self.session.get(url, params=params, timeout=30)
        return r.json()

    # Teams

    def get_nfl_teams(self) -> Dict:
        """Get all NFL teams"""
        url = f"{self.base_url}/nfl/teams"
        r = self.session.get(url, timeout=30)
        return r.json()

    def get_ncaaf_teams(self, group: Optional[str] = None) -> Dict:
        """
        Get NCAA Football teams

        Args:
            group: Conference group (e.g., '80' for all FBS)
        """
        url = f"{self.base_url}/college-football/teams"
        params = {}
        if group:
            params["groups"] = group

        r = self.session.get(url, params=params, timeout=30)
        return r.json()

    # Injuries

    def get_team_injuries(self, team_id: str, league: str = "nfl") -> Dict:
        """
        Get team injury report

        Args:
            team_id: ESPN team ID
            league: 'nfl' or 'college-football'
        """
        url = f"{self.core_api_url}/leagues/{league}/teams/{team_id}/injuries"
        r = self.session.get(url, timeout=30)
        return r.json()

    # Odds/Betting

    def get_nfl_odds(self) -> Dict:
        """Get NFL betting odds"""
        url = f"{self.web_api_url}/nfl/odds"
        r = self.session.get(url, timeout=30)
        return r.json()

    def get_ncaaf_odds(self) -> Dict:
        """Get NCAA Football betting odds"""
        url = f"{self.web_api_url}/college-football/odds"
        r = self.session.get(url, timeout=30)
        return r.json()

    # Player Stats

    def get_nfl_players(self, active_only: bool = True, limit: int = 20000) -> Dict:
        """
        Get NFL players

        Args:
            active_only: Only return active players
            limit: Maximum number of players to return
        """
        url = f"{self.core_api_url}/nfl/athletes"
        params = {
            "limit": limit,
            "active": str(active_only).lower()
        }
        r = self.session.get(url, params=params, timeout=30)
        return r.json()

    # Schedules

    def get_nfl_schedule(self, week: Optional[int] = None, season_type: int = 2) -> Dict:
        """
        Get NFL schedule

        Args:
            week: Week number (None for all weeks)
            season_type: 1=preseason, 2=regular, 3=postseason
        """
        url = f"{self.base_url}/nfl/scoreboard"
        params = {"seasontype": season_type}
        if week:
            params["week"] = week

        r = self.session.get(url, params=params, timeout=30)
        return r.json()

    def get_ncaaf_schedule(self, week: Optional[int] = None) -> Dict:
        """
        Get NCAA Football schedule

        Args:
            week: Week number (None for current week)
        """
        url = f"{self.base_url}/college-football/scoreboard"
        params = {}
        if week:
            params["week"] = week

        r = self.session.get(url, params=params, timeout=30)
        return r.json()

    # Helper Methods

    def save_to_json(self, data: Dict, filename: str):
        """Save data to JSON file"""
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"Saved to {filename}")


def main():
    """Demo script"""
    print("=" * 60)
    print("ESPN API Client Demo")
    print("=" * 60)

    client = ESPNAPIClient()

    # Test 1: NFL Scoreboard
    print("\n1. Fetching NFL scoreboard...")
    try:
        scoreboard = client.get_nfl_scoreboard()

        print(f"   Season: {scoreboard.get('season', {}).get('year')}")
        print(f"   Week: {scoreboard.get('week', {}).get('number')}")

        events = scoreboard.get('events', [])
        print(f"   Games: {len(events)}")

        if events:
            game = events[0]
            comps = game.get('competitions', [{}])[0]
            teams = comps.get('competitors', [])

            if len(teams) >= 2:
                away = teams[0].get('team', {}).get('displayName', 'Team 1')
                home = teams[1].get('team', {}).get('displayName', 'Team 2')
                print(f"\n   Sample game: {away} @ {home}")

        # Save
        client.save_to_json(scoreboard, "output/espn/nfl_scoreboard.json")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: NCAAF Scoreboard
    print("\n2. Fetching NCAA Football scoreboard...")
    try:
        scoreboard = client.get_ncaaf_scoreboard()

        print(f"   Season: {scoreboard.get('season', {}).get('year')}")
        print(f"   Week: {scoreboard.get('week', {}).get('number')}")

        events = scoreboard.get('events', [])
        print(f"   Games: {len(events)}")

        if events:
            game = events[0]
            comps = game.get('competitions', [{}])[0]
            teams = comps.get('competitors', [])

            if len(teams) >= 2:
                away = teams[0].get('team', {}).get('displayName', 'Team 1')
                home = teams[1].get('team', {}).get('displayName', 'Team 2')
                print(f"\n   Sample game: {away} @ {home}")

        # Save
        client.save_to_json(scoreboard, "output/espn/ncaaf_scoreboard.json")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: NFL Teams
    print("\n3. Fetching NFL teams...")
    try:
        teams = client.get_nfl_teams()

        team_list = teams.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
        print(f"   Teams: {len(team_list)}")

        if team_list:
            team = team_list[0].get('team', {})
            print(f"\n   Sample: {team.get('displayName')} ({team.get('abbreviation')})")

        # Save
        client.save_to_json(teams, "output/espn/nfl_teams.json")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 4: NFL Odds
    print("\n4. Fetching NFL odds...")
    try:
        odds = client.get_nfl_odds()

        items = odds.get('items', [])
        print(f"   Games with odds: {len(items)}")

        if items:
            game = items[0]
            print(f"\n   Sample: Event {game.get('id')}")

            odds_providers = game.get('odds', [])
            print(f"   Sportsbooks: {len(odds_providers)}")

        # Save
        client.save_to_json(odds, "output/espn/nfl_odds.json")

    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("Demo complete! Check output/espn/ for JSON files")
    print("=" * 60)


if __name__ == "__main__":
    main()
