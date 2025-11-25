#!/usr/bin/env python3
"""
ESPN API Client - DEPRECATED

⚠️ DEPRECATION NOTICE: This module is deprecated and should not be used.
Use espn_client.py instead, which provides:
  - Async/await support for better concurrency
  - Automatic retry logic with exponential backoff
  - Circuit breaker pattern for resilience
  - Superior error handling

This module is maintained for backwards compatibility only.
Migration path: Replace all imports of ESPNAPIClient with AsyncESPNClient from espn_client.py

Simple REST API client for ESPN football data (NFL & NCAAF)
No authentication required!
"""

import os
import json
import httpx
from datetime import datetime
from typing import Dict, Optional


class ESPNAPIClient:
    """Client for ESPN's public REST APIs"""

    def __init__(self):
        """Initialize ESPN API client"""
        # Website base URLs
        self.nfl_base_url = "https://www.espn.com/nfl"
        self.ncaaf_base_url = "https://www.espn.com/college-football"

        # API base URLs
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football"
        self.core_api_url = "https://sports.core.api.espn.com/v2/sports/football"
        self.web_api_url = "https://site.web.api.espn.com/apis/v3/sports/football"

        # News endpoint
        self.news_url = "https://www.espn.com/google-news-posts"

        self.session = httpx.Client()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

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
        params = {"limit": limit, "active": str(active_only).lower()}
        r = self.session.get(url, params=params, timeout=30)
        return r.json()

    # Schedules

    def get_nfl_schedule(
        self, week: Optional[int] = None, season_type: int = 2
    ) -> Dict:
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

    # Standings

    def get_nfl_standings(self, season: Optional[int] = None) -> Dict:
        """
        Get NFL standings

        Note: ESPN Site API standings endpoint returns only redirect links.
        We build actual standings from scoreboard data which includes team records.

        Args:
            season: Season year (optional, defaults to current year)

        Returns:
            Standings data with division/conference breakdowns and team records
        """
        import datetime

        if season is None:
            season = datetime.datetime.now().year

        # Try primary endpoint first (may return redirect)
        url = f"{self.base_url}/nfl/standings"
        params = {"season": season}

        try:
            r = self.session.get(url, params=params, timeout=30)
            data = r.json()

            # Check if we got actual standings data (not just redirect link)
            if "children" in data or ("entries" in data and len(data.get("entries", [])) > 0):
                return data

            # If only redirect link, build from scoreboard
            if "fullViewLink" in data or len(data) == 1:
                print(f"[INFO] Site API returned redirect, building standings from scoreboard...")
                return self._build_nfl_standings_from_scoreboard(season)

        except Exception as e:
            print(f"[WARNING] Error fetching NFL standings: {e}")
            return self._build_nfl_standings_from_scoreboard(season)

        # Fallback
        return self._build_nfl_standings_from_scoreboard(season)

    def _build_nfl_standings_from_scoreboard(self, season: int) -> Dict:
        """
        Build NFL standings from scoreboard data.

        Args:
            season: Season year

        Returns:
            Standings structured with divisions and team records
        """
        try:
            # Get scoreboard for all weeks
            url = f"{self.base_url}/nfl/scoreboard"
            params = {"season": season, "limit": 1000}
            r = self.session.get(url, params=params, timeout=30)
            scoreboard = r.json()

            # Extract standings from scoreboard
            if "leagues" in scoreboard and len(scoreboard["leagues"]) > 0:
                league = scoreboard["leagues"][0]
                if "standings" in league:
                    return {"children": league["standings"]}

            # If no standings in scoreboard, return basic structure
            return {
                "season": season,
                "league": "NFL",
                "note": "Partial data from scoreboard - detailed standings unavailable",
                "children": []
            }

        except Exception as e:
            print(f"[ERROR] Could not build standings from scoreboard: {e}")
            return {
                "season": season,
                "league": "NFL",
                "error": f"Failed to fetch standings: {str(e)}",
                "children": []
            }

    def get_ncaaf_standings(self, season: Optional[int] = None) -> Dict:
        """
        Get NCAA Football standings

        Note: ESPN Site API standings endpoint returns only redirect links.
        We build actual standings from scoreboard data which includes team records.

        Args:
            season: Season year (optional, defaults to current year)

        Returns:
            Standings data with conference breakdowns and team records
        """
        import datetime

        if season is None:
            season = datetime.datetime.now().year

        # Try primary endpoint first (may return redirect)
        url = f"{self.base_url}/college-football/standings"
        params = {"season": season}

        try:
            r = self.session.get(url, params=params, timeout=30)
            data = r.json()

            # Check if we got actual standings data (not just redirect link)
            if "children" in data or ("entries" in data and len(data.get("entries", [])) > 0):
                return data

            # If only redirect link, build from scoreboard
            if "fullViewLink" in data or len(data) == 1:
                print(f"[INFO] Site API returned redirect, building standings from scoreboard...")
                return self._build_ncaaf_standings_from_scoreboard(season)

        except Exception as e:
            print(f"[WARNING] Error fetching NCAAF standings: {e}")
            return self._build_ncaaf_standings_from_scoreboard(season)

        # Fallback
        return self._build_ncaaf_standings_from_scoreboard(season)

    def _build_ncaaf_standings_from_scoreboard(self, season: int) -> Dict:
        """
        Build NCAAF standings from scoreboard data.

        Args:
            season: Season year

        Returns:
            Standings structured with conferences and team records
        """
        try:
            # Get scoreboard for all weeks (FBS only - group 80)
            url = f"{self.base_url}/college-football/scoreboard"
            params = {"season": season, "groups": 80, "limit": 1000}
            r = self.session.get(url, params=params, timeout=30)
            scoreboard = r.json()

            # Extract standings from scoreboard
            if "leagues" in scoreboard and len(scoreboard["leagues"]) > 0:
                league = scoreboard["leagues"][0]
                if "standings" in league:
                    return {"children": league["standings"]}

            # If no standings in scoreboard, return basic structure
            return {
                "season": season,
                "league": "NCAAF",
                "note": "Partial data from scoreboard - detailed standings unavailable",
                "children": []
            }

        except Exception as e:
            print(f"[ERROR] Could not build standings from scoreboard: {e}")
            return {
                "season": season,
                "league": "NCAAF",
                "error": f"Failed to fetch standings: {str(e)}",
                "children": []
            }

    # Stats

    def get_nfl_stats(self) -> Dict:
        """Get NFL statistics page data"""
        # Note: Stats page is HTML, may need scraping. API endpoint might be available.
        url = f"{self.base_url}/nfl/stats"
        r = self.session.get(url, timeout=30)
        # This returns HTML - may need separate scraper for parsing
        return {"url": url, "content_type": r.headers.get("content-type")}

    def get_ncaaf_stats(self) -> Dict:
        """Get NCAA Football statistics page data"""
        # Note: Stats page is HTML, may need scraping. API endpoint might be available.
        url = f"{self.base_url}/college-football/stats"
        r = self.session.get(url, timeout=30)
        # This returns HTML - may need separate scraper for parsing
        return {"url": url, "content_type": r.headers.get("content-type")}

    # News

    def get_espn_news_posts(self) -> Dict:
        """
        Get ESPN news posts

        Returns:
            Dictionary with news posts data
        """
        url = self.news_url
        r = self.session.get(url, timeout=30)
        return r.json()

    # Team Statistics

    def get_team_statistics(
        self, team_id: str, league: str = "college-football"
    ) -> Dict:
        """
        Get comprehensive team statistics including offensive, defensive, and special teams

        Args:
            team_id: ESPN team ID
            league: 'nfl' or 'college-football'

        Returns:
            Complete statistics including team stats and opponent stats
        """
        url = f"{self.base_url}/{league}/teams/{team_id}/statistics"
        r = self.session.get(url, timeout=30)
        return r.json()

    def extract_power_rating_metrics(
        self, team_id: str, league: str = "college-football"
    ) -> Dict:
        """
        Extract key metrics for Billy Walters power rating calculations

        Args:
            team_id: ESPN team ID
            league: 'nfl' or 'college-football'

        Returns:
            Dictionary with offensive/defensive efficiency metrics
        """
        data = self.get_team_statistics(team_id, league)

        # Helper function to extract stat value
        def get_stat_value(stats_list, stat_name):
            stat = next((s for s in stats_list if s["name"] == stat_name), None)
            return stat["value"] if stat else None

        # Extract team offensive stats
        team_stats = data["results"]["stats"]["categories"]
        scoring = next(c for c in team_stats if c["name"] == "scoring")
        misc = next(c for c in team_stats if c["name"] == "miscellaneous")
        passing = next(c for c in team_stats if c["name"] == "passing")
        rushing = next(c for c in team_stats if c["name"] == "rushing")

        # Extract opponent (defensive) stats
        opponent = data["results"]["opponent"]
        opp_scoring = next(c for c in opponent if c["name"] == "scoring")
        opp_passing = next(c for c in opponent if c["name"] == "passing")
        opp_rushing = next(c for c in opponent if c["name"] == "rushing")

        # Build metrics dictionary
        metrics = {
            # Team info
            "team_id": team_id,
            "team_name": data.get("team", {}).get("displayName"),
            "games_played": get_stat_value(misc["stats"], "gamesPlayed"),
            # Offensive metrics
            "points_per_game": get_stat_value(scoring["stats"], "totalPointsPerGame"),
            "total_points": get_stat_value(scoring["stats"], "totalPoints"),
            "passing_yards_per_game": get_stat_value(
                passing["stats"], "netPassingYardsPerGame"
            ),
            "rushing_yards_per_game": get_stat_value(
                rushing["stats"], "rushingYardsPerGame"
            ),
            # Defensive metrics (opponent stats)
            "points_allowed_per_game": get_stat_value(
                opp_scoring["stats"], "totalPointsPerGame"
            ),
            "passing_yards_allowed_per_game": get_stat_value(
                opp_passing["stats"], "passingYardsPerGame"
            ),
            "rushing_yards_allowed_per_game": get_stat_value(
                opp_rushing["stats"], "rushingYardsPerGame"
            ),
            # Advanced metrics
            "turnover_margin": get_stat_value(misc["stats"], "turnOverDifferential"),
            "third_down_pct": get_stat_value(misc["stats"], "thirdDownConvPct"),
            "takeaways": get_stat_value(misc["stats"], "totalTakeaways"),
            "giveaways": get_stat_value(misc["stats"], "totalGiveaways"),
        }

        # Calculate total yards per game (offensive)
        if metrics["passing_yards_per_game"] and metrics["rushing_yards_per_game"]:
            metrics["total_yards_per_game"] = (
                metrics["passing_yards_per_game"] + metrics["rushing_yards_per_game"]
            )

        # Calculate total yards allowed per game (defensive)
        if (
            metrics["passing_yards_allowed_per_game"]
            and metrics["rushing_yards_allowed_per_game"]
        ):
            metrics["total_yards_allowed_per_game"] = (
                metrics["passing_yards_allowed_per_game"]
                + metrics["rushing_yards_allowed_per_game"]
            )

        return metrics

    def get_all_fbs_teams(self) -> Dict:
        """
        Get all FBS (Division I-A) college football teams

        Returns:
            Dictionary with team list and metadata
        """
        url = f"{self.base_url}/college-football/teams"
        params = {"groups": "80"}  # Group 80 = FBS
        r = self.session.get(url, params=params, timeout=30)
        return r.json()

    # Helper Methods

    def save_to_json(
        self,
        data: Dict,
        filename: Optional[str] = None,
        data_type: Optional[str] = None,
        league: Optional[str] = None,
        output_dir: str = "output/espn",
    ):
        """
        Save data to JSON file with organized directory structure

        Args:
            data: Data dictionary to save
            filename: Full filename path (if provided, used as-is)
            data_type: Type of data (scoreboard, schedule, standings, stats, teams, odds, news)
            league: League name (nfl or ncaaf)
            output_dir: Base output directory (default: output/espn)
        """
        if filename:
            # Use provided filename as-is
            filepath = filename
        elif data_type and league:
            # Use organized structure: output/espn/{data_type}/{league}/
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(
                output_dir, data_type, league, f"{data_type}_{league}_{timestamp}.json"
            )
        elif data_type:
            # No league subdirectory (e.g., news)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(
                output_dir, data_type, f"{data_type}_{timestamp}.json"
            )
        else:
            # Fallback to old behavior
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"espn_data_{timestamp}.json")

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"Saved to {filepath}")
        return filepath


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

        events = scoreboard.get("events", [])
        print(f"   Games: {len(events)}")

        if events:
            game = events[0]
            comps = game.get("competitions", [{}])[0]
            teams = comps.get("competitors", [])

            if len(teams) >= 2:
                away = teams[0].get("team", {}).get("displayName", "Team 1")
                home = teams[1].get("team", {}).get("displayName", "Team 2")
                print(f"\n   Sample game: {away} @ {home}")

        # Save
        client.save_to_json(scoreboard, data_type="scoreboard", league="nfl")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: NCAAF Scoreboard
    print("\n2. Fetching NCAA Football scoreboard...")
    try:
        scoreboard = client.get_ncaaf_scoreboard()

        print(f"   Season: {scoreboard.get('season', {}).get('year')}")
        print(f"   Week: {scoreboard.get('week', {}).get('number')}")

        events = scoreboard.get("events", [])
        print(f"   Games: {len(events)}")

        if events:
            game = events[0]
            comps = game.get("competitions", [{}])[0]
            teams = comps.get("competitors", [])

            if len(teams) >= 2:
                away = teams[0].get("team", {}).get("displayName", "Team 1")
                home = teams[1].get("team", {}).get("displayName", "Team 2")
                print(f"\n   Sample game: {away} @ {home}")

        # Save
        client.save_to_json(scoreboard, data_type="scoreboard", league="ncaaf")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: NFL Teams
    print("\n3. Fetching NFL teams...")
    try:
        teams = client.get_nfl_teams()

        team_list = (
            teams.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
        )
        print(f"   Teams: {len(team_list)}")

        if team_list:
            team = team_list[0].get("team", {})
            print(
                f"\n   Sample: {team.get('displayName')} ({team.get('abbreviation')})"
            )

        # Save
        client.save_to_json(teams, data_type="teams", league="nfl")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 4: NFL Odds
    print("\n4. Fetching NFL odds...")
    try:
        odds = client.get_nfl_odds()

        items = odds.get("items", [])
        print(f"   Games with odds: {len(items)}")

        if items:
            game = items[0]
            print(f"\n   Sample: Event {game.get('id')}")

            odds_providers = game.get("odds", [])
            print(f"   Sportsbooks: {len(odds_providers)}")

        # Save
        client.save_to_json(odds, data_type="odds", league="nfl")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 5: NFL Standings
    print("\n5. Fetching NFL standings...")
    try:
        standings = client.get_nfl_standings()
        client.save_to_json(standings, data_type="standings", league="nfl")
        print("   [OK] Saved NFL standings")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 6: NCAAF Standings
    print("\n6. Fetching NCAAF standings...")
    try:
        standings = client.get_ncaaf_standings()
        client.save_to_json(standings, data_type="standings", league="ncaaf")
        print("   [OK] Saved NCAAF standings")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 7: ESPN News
    print("\n7. Fetching ESPN news posts...")
    try:
        news = client.get_espn_news_posts()
        client.save_to_json(news, data_type="news")
        print("   [OK] Saved news posts")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("Demo complete! Check output/espn/ for JSON files")
    print("=" * 60)


if __name__ == "__main__":
    main()
