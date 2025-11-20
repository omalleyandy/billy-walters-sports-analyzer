"""
Highlightly NFL/NCAA API Client
https://highlightly.net/documentation/american-football/

Provides access to:
- Teams and team statistics
- Matches and detailed match data
- Live and prematch odds from multiple bookmakers
- Player profiles and statistics
- Highlights and video content
- Standings and rankings
- Head-to-head and recent form data
"""

from typing import Optional, List, Dict, Any
import httpx
import os
from walters_analyzer.config import get_settings
from walters_analyzer.feeds.highlightly_models import (
    HighlightlyTeam,
    TeamStatistics,
    HighlightlyMatch,
    MatchDetails,
    MatchOdds,
    Bookmaker,
    HighlightlyHighlight,
    GeoRestriction,
    StandingsData,
    Lineups,
    HighlightlyPlayer,
    PlayerSummary,
    PlayerStatistics,
)


class HighlightlyClient:
    """
    Async HTTP client for Highlightly NFL/NCAA API

    Example:
        client = HighlightlyClient()
        teams = await client.get_teams(league="NFL")
        matches = await client.get_matches(league="NFL", date="2024-11-08")
        odds = await client.get_odds(match_id=12345)
    """

    def __init__(self, api_key: Optional[str] = None, use_rapidapi: bool = False):
        """
        Initialize Highlightly client

        Args:
            api_key: Highlightly API key (defaults to HIGHLIGHTLY_API_KEY env var)
            use_rapidapi: Use RapidAPI endpoint (default: False, uses Highlightly direct)
        """
        self.settings = get_settings()

        # Try multiple sources for API key
        self.api_key = (
            api_key
            or os.getenv("HIGHLIGHTLY_API_KEY")
            or getattr(self.settings, "highlightly_api_key", None)
        )

        if not self.api_key:
            raise ValueError(
                "HIGHLIGHTLY_API_KEY not set. Add to .env file:\n"
                "HIGHLIGHTLY_API_KEY=your_key_here"
            )

        # Base URL selection
        if use_rapidapi:
            self.base_url = "https://nfl-ncaa-highlights-api.p.rapidapi.com"
            self.rapidapi_host = "nfl-ncaa-highlights-api.p.rapidapi.com"
        else:
            self.base_url = "https://american-football.highlightly.net"
            self.rapidapi_host = "nfl-ncaa-highlights-api.p.rapidapi.com"

        self.use_rapidapi = use_rapidapi
        self.client = httpx.AsyncClient(timeout=30.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {"x-rapidapi-key": self.api_key, "Content-Type": "application/json"}

        # RapidAPI requires host header
        if self.use_rapidapi:
            headers["x-rapidapi-host"] = self.rapidapi_host

        return headers

    async def _request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make API request

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()

            # Check rate limits
            remaining = response.headers.get("x-ratelimit-requests-remaining")
            if remaining:
                print(f"ℹ️  API requests remaining: {remaining}")

            return response.json()

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.HTTPError as e:
            print(f"❌ Request error: {e}")
            raise

    # ========================================================================
    # Teams Endpoints
    # ========================================================================

    async def get_teams(
        self,
        league: Optional[str] = None,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        abbreviation: Optional[str] = None,
    ) -> List[HighlightlyTeam]:
        """
        Get all teams

        Args:
            league: Filter by league (NFL, NCAA)
            name: Filter by team name (e.g., "Bengals")
            display_name: Filter by display name (e.g., "Cincinnati Bengals")
            abbreviation: Filter by abbreviation (e.g., "CIN")

        Returns:
            List of teams
        """
        params = {}
        if league:
            params["league"] = league
        if name:
            params["name"] = name
        if display_name:
            params["displayName"] = display_name
        if abbreviation:
            params["abbreviation"] = abbreviation

        data = await self._request("/teams", params=params)

        # API returns array directly, not wrapped
        if isinstance(data, list):
            return [HighlightlyTeam(**team) for team in data]
        return []

    async def get_team_by_id(self, team_id: int) -> Optional[HighlightlyTeam]:
        """
        Get team by ID

        Args:
            team_id: Team ID

        Returns:
            Team information
        """
        data = await self._request(f"/teams/{team_id}")

        if isinstance(data, list) and len(data) > 0:
            return HighlightlyTeam(**data[0])
        return None

    async def get_team_statistics(
        self, team_id: int, from_date: str, timezone: str = "Etc/UTC"
    ) -> List[TeamStatistics]:
        """
        Get team statistics

        Args:
            team_id: Team ID
            from_date: Start date (YYYY-MM-DD format)
            timezone: Timezone identifier (default: "Etc/UTC")

        Returns:
            List of team statistics by league/season
        """
        params = {"fromDate": from_date, "timezone": timezone}

        data = await self._request(f"/teams/statistics/{team_id}", params=params)

        if isinstance(data, list):
            return [TeamStatistics(**stat) for stat in data]
        return []

    # ========================================================================
    # Matches Endpoints
    # ========================================================================

    async def get_matches(
        self,
        league: Optional[str] = None,
        date: Optional[str] = None,
        timezone: str = "Etc/UTC",
        season: Optional[int] = None,
        home_team_id: Optional[int] = None,
        away_team_id: Optional[int] = None,
        home_team_name: Optional[str] = None,
        away_team_name: Optional[str] = None,
        home_team_abbreviation: Optional[str] = None,
        away_team_abbreviation: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[HighlightlyMatch]:
        """
        Get all matches

        Args:
            league: Filter by league (NFL, NCAA)
            date: Date (YYYY-MM-DD format)
            timezone: Timezone identifier (default: "Etc/UTC")
            season: Filter by season year
            home_team_id: Filter by home team ID
            away_team_id: Filter by away team ID
            home_team_name: Filter by home team name
            away_team_name: Filter by away team name
            home_team_abbreviation: Filter by home team abbreviation
            away_team_abbreviation: Filter by away team abbreviation
            limit: Max results (default: 100, max: 100)
            offset: Pagination offset (default: 0)

        Returns:
            List of matches
        """
        params = {"timezone": timezone, "limit": min(limit, 100), "offset": offset}

        if league:
            params["league"] = league
        if date:
            params["date"] = date
        if season:
            params["season"] = season
        if home_team_id:
            params["homeTeamId"] = home_team_id
        if away_team_id:
            params["awayTeamId"] = away_team_id
        if home_team_name:
            params["homeTeamName"] = home_team_name
        if away_team_name:
            params["awayTeamName"] = away_team_name
        if home_team_abbreviation:
            params["homeTeamAbbreviation"] = home_team_abbreviation
        if away_team_abbreviation:
            params["awayTeamAbbreviation"] = away_team_abbreviation

        data = await self._request("/matches", params=params)

        # Response has pagination wrapper
        if isinstance(data, dict) and "data" in data:
            return [HighlightlyMatch(**match) for match in data["data"]]
        return []

    async def get_match_by_id(self, match_id: int) -> Optional[MatchDetails]:
        """
        Get detailed match information by ID

        Includes: venue, weather, injuries, events, box scores, top performers

        Args:
            match_id: Match ID

        Returns:
            Detailed match information
        """
        data = await self._request(f"/matches/{match_id}")

        if isinstance(data, list) and len(data) > 0:
            return MatchDetails(**data[0])
        return None

    # ========================================================================
    # Odds Endpoints
    # ========================================================================

    async def get_odds(
        self,
        match_id: Optional[int] = None,
        odds_type: str = "prematch",
        league_name: Optional[str] = None,
        date: Optional[str] = None,
        timezone: str = "Etc/UTC",
        bookmaker_id: Optional[int] = None,
        bookmaker_name: Optional[str] = None,
        limit: int = 5,
        offset: int = 0,
    ) -> List[MatchOdds]:
        """
        Get odds (prematch or live)

        Args:
            match_id: Filter by match ID (most common use)
            odds_type: "prematch" or "live" (default: "prematch")
            league_name: Filter by league (NFL, NCAA)
            date: Date (YYYY-MM-DD format)
            timezone: Timezone identifier (default: "Etc/UTC")
            bookmaker_id: Filter by bookmaker ID
            bookmaker_name: Filter by bookmaker name
            limit: Max results (default: 5, max: 5)
            offset: Pagination offset (default: 0)

        Returns:
            List of match odds from multiple bookmakers
        """
        params = {
            "oddsType": odds_type,
            "timezone": timezone,
            "limit": min(limit, 5),
            "offset": offset,
        }

        if match_id:
            params["matchId"] = match_id
        if league_name:
            params["leagueName"] = league_name
        if date:
            params["date"] = date
        if bookmaker_id:
            params["bookmakerId"] = bookmaker_id
        if bookmaker_name:
            params["bookmakerName"] = bookmaker_name

        data = await self._request("/odds", params=params)

        # Response has pagination wrapper
        if isinstance(data, dict) and "data" in data:
            return [MatchOdds(**odds) for odds in data["data"]]
        return []

    async def get_bookmakers(
        self, name: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[Bookmaker]:
        """
        Get all bookmakers

        Args:
            name: Filter by bookmaker name
            limit: Max results (default: 20, max: 100)
            offset: Pagination offset (default: 0)

        Returns:
            List of bookmakers
        """
        params = {"limit": min(limit, 100), "offset": offset}

        if name:
            params["name"] = name

        data = await self._request("/bookmakers", params=params)

        # Response has pagination wrapper
        if isinstance(data, dict) and "data" in data:
            return [Bookmaker(**bookmaker) for bookmaker in data["data"]]
        return []

    async def get_bookmaker_by_id(self, bookmaker_id: int) -> Optional[Bookmaker]:
        """
        Get bookmaker by ID

        Args:
            bookmaker_id: Bookmaker ID

        Returns:
            Bookmaker information
        """
        data = await self._request(f"/bookmakers/{bookmaker_id}")

        if isinstance(data, list) and len(data) > 0:
            return Bookmaker(**data[0])
        return None

    # ========================================================================
    # Highlights Endpoints
    # ========================================================================

    async def get_highlights(
        self,
        league_name: Optional[str] = None,
        date: Optional[str] = None,
        timezone: str = "Etc/UTC",
        season: Optional[int] = None,
        match_id: Optional[int] = None,
        home_team_id: Optional[int] = None,
        away_team_id: Optional[int] = None,
        home_team_name: Optional[str] = None,
        away_team_name: Optional[str] = None,
        limit: int = 40,
        offset: int = 0,
    ) -> List[HighlightlyHighlight]:
        """
        Get highlights

        Args:
            league_name: Filter by league (NFL, NCAA)
            date: Date (YYYY-MM-DD format)
            timezone: Timezone identifier (default: "Etc/UTC")
            season: Filter by season year
            match_id: Filter by match ID
            home_team_id: Filter by home team ID
            away_team_id: Filter by away team ID
            home_team_name: Filter by home team name
            away_team_name: Filter by away team name
            limit: Max results (default: 40, max: 40)
            offset: Pagination offset (default: 0)

        Returns:
            List of highlights
        """
        params = {"timezone": timezone, "limit": min(limit, 40), "offset": offset}

        if league_name:
            params["leagueName"] = league_name
        if date:
            params["date"] = date
        if season:
            params["season"] = season
        if match_id:
            params["matchId"] = match_id
        if home_team_id:
            params["homeTeamId"] = home_team_id
        if away_team_id:
            params["awayTeamId"] = away_team_id
        if home_team_name:
            params["homeTeamName"] = home_team_name
        if away_team_name:
            params["awayTeamName"] = away_team_name

        data = await self._request("/highlights", params=params)

        # Response has pagination wrapper
        if isinstance(data, dict) and "data" in data:
            return [HighlightlyHighlight(**highlight) for highlight in data["data"]]
        return []

    async def get_highlight_by_id(
        self, highlight_id: int
    ) -> Optional[HighlightlyHighlight]:
        """
        Get highlight by ID

        Args:
            highlight_id: Highlight ID

        Returns:
            Highlight information
        """
        data = await self._request(f"/highlights/{highlight_id}")

        if isinstance(data, list) and len(data) > 0:
            return HighlightlyHighlight(**data[0])
        return None

    async def get_highlight_geo_restrictions(
        self, highlight_id: int
    ) -> Optional[GeoRestriction]:
        """
        Get geo restrictions for highlight

        Args:
            highlight_id: Highlight ID

        Returns:
            Geo restriction information
        """
        data = await self._request(f"/highlights/geo-restrictions/{highlight_id}")

        if isinstance(data, dict):
            return GeoRestriction(**data)
        return None

    # ========================================================================
    # Standings Endpoints
    # ========================================================================

    async def get_standings(
        self,
        league_type: Optional[str] = None,
        league_name: Optional[str] = None,
        abbreviation: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Optional[StandingsData]:
        """
        Get standings

        Args:
            league_type: Filter by league type (NFL, NCAA)
            league_name: Filter by league/conference name
            abbreviation: Filter by abbreviation (e.g., "NFC", "AFC", "SEC")
            year: Filter by year
            limit: Max results (default: 10, max: 10)
            offset: Pagination offset (default: 0)

        Returns:
            Standings data
        """
        params = {"limit": min(limit, 10), "offset": offset}

        if league_type:
            params["leagueType"] = league_type
        if league_name:
            params["leagueName"] = league_name
        if abbreviation:
            params["abbreviation"] = abbreviation
        if year:
            params["year"] = year

        data = await self._request("/standings", params=params)

        if isinstance(data, dict):
            return StandingsData(**data)
        return None

    # ========================================================================
    # Lineups Endpoints
    # ========================================================================

    async def get_lineups(self, match_id: int) -> Optional[Lineups]:
        """
        Get lineups by match ID

        Args:
            match_id: Match ID

        Returns:
            Lineups for both teams
        """
        data = await self._request(f"/lineups/{match_id}")

        if isinstance(data, dict):
            return Lineups(**data)
        return None

    # ========================================================================
    # Players Endpoints
    # ========================================================================

    async def get_players(
        self, name: Optional[str] = None, limit: int = 1000, offset: int = 0
    ) -> List[HighlightlyPlayer]:
        """
        Get all players

        Args:
            name: Filter by player name
            limit: Max results (default: 1000, max: 1000)
            offset: Pagination offset (default: 0)

        Returns:
            List of players
        """
        params = {"limit": min(limit, 1000), "offset": offset}

        if name:
            params["name"] = name

        data = await self._request("/players", params=params)

        # Response has pagination wrapper
        if isinstance(data, dict) and "data" in data:
            return [HighlightlyPlayer(**player) for player in data["data"]]
        return []

    async def get_player_summary(self, player_id: int) -> Optional[PlayerSummary]:
        """
        Get player summary by ID

        Args:
            player_id: Player ID

        Returns:
            Player summary with profile
        """
        data = await self._request(f"/players/{player_id}")

        if isinstance(data, list) and len(data) > 0:
            return PlayerSummary(**data[0])
        return None

    async def get_player_statistics(self, player_id: int) -> Optional[PlayerStatistics]:
        """
        Get player statistics by ID

        Args:
            player_id: Player ID

        Returns:
            Player statistics by season
        """
        data = await self._request(f"/players/{player_id}/statistics")

        if isinstance(data, list) and len(data) > 0:
            return PlayerStatistics(**data[0])
        return None

    # ========================================================================
    # Historical Data Endpoints
    # ========================================================================

    async def get_last_five_games(self, team_id: int) -> List[HighlightlyMatch]:
        """
        Get last five finished games for a team

        Args:
            team_id: Team ID

        Returns:
            List of last 5 finished matches
        """
        params = {"teamId": team_id}

        data = await self._request("/last-five-games", params=params)

        if isinstance(data, list):
            return [HighlightlyMatch(**match) for match in data]
        return []

    async def get_head_to_head(
        self, team_id_one: int, team_id_two: int
    ) -> List[HighlightlyMatch]:
        """
        Get head-to-head games between two teams

        Args:
            team_id_one: First team ID
            team_id_two: Second team ID

        Returns:
            List of last 10 head-to-head matches
        """
        params = {"teamIdOne": team_id_one, "teamIdTwo": team_id_two}

        data = await self._request("/head-2-head", params=params)

        if isinstance(data, list):
            return [HighlightlyMatch(**match) for match in data]
        return []

    # ========================================================================
    # Utility Methods
    # ========================================================================

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
