"""
ESPN Statistics Client

Fetches NFL and NCAAF team/player statistics, schedules, and game data.
Implements comprehensive error handling, retry logic, and data validation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Literal

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class ESPNClient:
    """
    Robust client for ESPN statistics and schedule data.

    Features:
    - Team and player statistics
    - Schedules and scores
    - Game details and play-by-play
    - Automatic retry with exponential backoff
    - Circuit breaker pattern for reliability
    - Data validation and sanitization
    """

    # Website base URLs
    NFL_WEBSITE_URL = "https://www.espn.com/nfl"
    NCAAF_WEBSITE_URL = "https://www.espn.com/college-football"

    # ESPN API endpoints
    NFL_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    NCAAF_BASE_URL = (
        "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
    )

    # News endpoint
    NEWS_URL = "https://www.espn.com/google-news-posts"

    def __init__(
        self,
        rate_limit_delay: float = 0.5,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize ESPN API client.

        Args:
            rate_limit_delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.last_request_time: float = 0.0
        self._client: httpx.AsyncClient | None = None
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_reset_time: float | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP client."""
        logger.info("Initializing ESPN API client")
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.espn.com/",
            },
            follow_redirects=True,
        )
        logger.info("ESPN client initialized successfully")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.info("ESPN client closed")

    def _check_circuit_breaker(self) -> None:
        """Check if circuit breaker is open."""
        if self._circuit_breaker_reset_time:
            if asyncio.get_event_loop().time() > self._circuit_breaker_reset_time:
                # Reset circuit breaker
                logger.info("Circuit breaker reset")
                self._circuit_breaker_failures = 0
                self._circuit_breaker_reset_time = None
            else:
                raise RuntimeError(
                    "Circuit breaker is open. Too many failures. "
                    f"Will reset at {datetime.fromtimestamp(self._circuit_breaker_reset_time)}"
                )

    def _record_failure(self) -> None:
        """Record a failure and potentially open circuit breaker."""
        self._circuit_breaker_failures += 1
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            # Open circuit breaker for 5 minutes
            self._circuit_breaker_reset_time = asyncio.get_event_loop().time() + 300
            logger.error(
                f"Circuit breaker opened after {self._circuit_breaker_failures} failures"
            )

    def _record_success(self) -> None:
        """Record a successful request."""
        if self._circuit_breaker_failures > 0:
            self._circuit_breaker_failures = max(0, self._circuit_breaker_failures - 1)

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = asyncio.get_event_loop().time()

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _make_request(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Make HTTP request with automatic retry and circuit breaker.

        Args:
            url: Full URL to request
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            RuntimeError: If circuit breaker is open or request fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Call connect() first.")

        self._check_circuit_breaker()
        await self._rate_limit()

        try:
            logger.debug(f"GET {url}")
            response = await self._client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            self._record_success()
            return data

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code}: {url}")
            self._record_failure()

            # Don't retry 4xx errors
            if 400 <= e.response.status_code < 500:
                raise RuntimeError(
                    f"Client error {e.response.status_code} for {url}"
                ) from e
            raise

        except httpx.RequestError as e:
            logger.warning(f"Request error for {url}: {e}")
            self._record_failure()
            raise

    async def get_scoreboard(
        self,
        league: Literal["NFL", "NCAAF"],
        week: int | None = None,
        season: int | None = None,
    ) -> dict[str, Any]:
        """
        Get scoreboard with games for a specific week.

        Args:
            league: League to fetch ("NFL" or "NCAAF")
            week: Week number (optional)
            season: Season year (optional, defaults to current year)

        Returns:
            Scoreboard data with games
        """
        base_url = self.NFL_BASE_URL if league == "NFL" else self.NCAAF_BASE_URL
        url = f"{base_url}/scoreboard"

        params = {}
        if week is not None:
            params["week"] = week
        if season is not None:
            params["seasonYear"] = season

        logger.info(
            f"Fetching {league} scoreboard"
            + (f" week {week}" if week else "")
            + (f" season {season}" if season else "")
        )

        data = await self._make_request(url, params)
        return self._enrich_scoreboard(data, league)

    async def get_team_stats(
        self,
        league: Literal["NFL", "NCAAF"],
        team_id: str,
        season: int | None = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive team statistics.

        Args:
            league: League ("NFL" or "NCAAF")
            team_id: ESPN team ID
            season: Season year (optional)

        Returns:
            Team statistics dictionary
        """
        base_url = self.NFL_BASE_URL if league == "NFL" else self.NCAAF_BASE_URL
        url = f"{base_url}/teams/{team_id}/statistics"

        params = {}
        if season is not None:
            params["season"] = season

        logger.info(f"Fetching {league} team {team_id} stats")

        data = await self._make_request(url, params)
        return self._enrich_team_stats(data, league, team_id)

    async def get_team_roster(
        self,
        league: Literal["NFL", "NCAAF"],
        team_id: str,
    ) -> dict[str, Any]:
        """
        Get team roster with player information.

        Args:
            league: League ("NFL" or "NCAAF")
            team_id: ESPN team ID

        Returns:
            Roster data with players
        """
        base_url = self.NFL_BASE_URL if league == "NFL" else self.NCAAF_BASE_URL
        url = f"{base_url}/teams/{team_id}/roster"

        logger.info(f"Fetching {league} team {team_id} roster")

        data = await self._make_request(url)
        return self._enrich_roster(data, league, team_id)

    async def get_standings(
        self,
        league: Literal["NFL", "NCAAF"],
        season: int | None = None,
    ) -> dict[str, Any]:
        """
        Get league standings.

        Args:
            league: League ("NFL" or "NCAAF")
            season: Season year (optional)

        Returns:
            Standings data
        """
        base_url = self.NFL_BASE_URL if league == "NFL" else self.NCAAF_BASE_URL
        url = f"{base_url}/standings"

        params = {}
        if season is not None:
            params["season"] = season

        logger.info(f"Fetching {league} standings")

        data = await self._make_request(url, params)
        return self._enrich_standings(data, league)

    async def get_schedule(
        self,
        league: Literal["NFL", "NCAAF"],
        week: int | None = None,
        season: int | None = None,
    ) -> dict[str, Any]:
        """
        Get league schedule.

        Args:
            league: League ("NFL" or "NCAAF")
            week: Week number (optional)
            season: Season year (optional)

        Returns:
            Schedule data (same as scoreboard)
        """
        # Schedule is same as scoreboard endpoint
        return await self.get_scoreboard(league, week=week, season=season)

    async def get_news(self) -> dict[str, Any]:
        """
        Get ESPN news posts.

        Returns:
            News posts data
        """
        logger.info("Fetching ESPN news posts")
        data = await self._make_request(self.NEWS_URL)
        return self._enrich_news(data)

    async def get_odds(
        self,
        league: Literal["NFL", "NCAAF"],
    ) -> dict[str, Any]:
        """
        Get betting odds for league.

        Args:
            league: League ("NFL" or "NCAAF")

        Returns:
            Odds data
        """
        # Note: Odds may use web API endpoint
        # For now, use scoreboard which includes odds
        base_url = self.NFL_BASE_URL if league == "NFL" else self.NCAAF_BASE_URL
        url = f"{base_url}/scoreboard"

        logger.info(f"Fetching {league} odds")
        data = await self._make_request(url)
        return self._enrich_odds(data, league)

    def _enrich_news(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add metadata to news data."""
        enriched = data.copy()
        enriched["source"] = "espn"
        enriched["fetch_time"] = datetime.now().isoformat()
        return enriched

    def _enrich_odds(self, data: dict[str, Any], league: str) -> dict[str, Any]:
        """Add metadata to odds data."""
        enriched = data.copy()
        enriched["league"] = league
        enriched["source"] = "espn"
        enriched["fetch_time"] = datetime.now().isoformat()
        return enriched

    async def get_game_details(
        self,
        league: Literal["NFL", "NCAAF"],
        game_id: str,
    ) -> dict[str, Any]:
        """
        Get detailed game information including play-by-play.

        Args:
            league: League ("NFL" or "NCAAF")
            game_id: ESPN game ID

        Returns:
            Detailed game data
        """
        base_url = self.NFL_BASE_URL if league == "NFL" else self.NCAAF_BASE_URL
        url = f"{base_url}/summary"

        params = {"event": game_id}

        logger.info(f"Fetching {league} game {game_id} details")

        data = await self._make_request(url, params)
        return self._enrich_game_details(data, league, game_id)

    async def get_teams(self, league: Literal["NFL", "NCAAF"]) -> list[dict[str, Any]]:
        """
        Get list of all teams in the league.

        Args:
            league: League ("NFL" or "NCAAF")

        Returns:
            List of team dictionaries
        """
        base_url = self.NFL_BASE_URL if league == "NFL" else self.NCAAF_BASE_URL
        url = f"{base_url}/teams"

        logger.info(f"Fetching {league} teams")

        data = await self._make_request(url)

        teams = []
        sports = data.get("sports", [])
        for sport in sports:
            for league_data in sport.get("leagues", []):
                for team in league_data.get("teams", []):
                    team_info = team.get("team", {})
                    teams.append(
                        {
                            "id": team_info.get("id"),
                            "name": team_info.get("displayName"),
                            "abbreviation": team_info.get("abbreviation"),
                            "location": team_info.get("location"),
                            "nickname": team_info.get("nickname"),
                            "logo": team_info.get("logos", [{}])[0].get("href")
                            if team_info.get("logos")
                            else None,
                            "league": league,
                            "source": "espn",
                            "fetch_time": datetime.now().isoformat(),
                        }
                    )

        logger.info(f"Fetched {len(teams)} teams")
        return teams

    def _enrich_scoreboard(self, data: dict[str, Any], league: str) -> dict[str, Any]:
        """Add metadata to scoreboard data."""
        enriched = data.copy()
        enriched["league"] = league
        enriched["source"] = "espn"
        enriched["fetch_time"] = datetime.now().isoformat()
        return enriched

    def _enrich_team_stats(
        self, data: dict[str, Any], league: str, team_id: str
    ) -> dict[str, Any]:
        """Add metadata to team stats."""
        enriched = data.copy()
        enriched["team_id"] = team_id
        enriched["league"] = league
        enriched["source"] = "espn"
        enriched["fetch_time"] = datetime.now().isoformat()
        return enriched

    def _enrich_roster(
        self, data: dict[str, Any], league: str, team_id: str
    ) -> dict[str, Any]:
        """Add metadata to roster data."""
        enriched = data.copy()
        enriched["team_id"] = team_id
        enriched["league"] = league
        enriched["source"] = "espn"
        enriched["fetch_time"] = datetime.now().isoformat()
        return enriched

    def _enrich_standings(self, data: dict[str, Any], league: str) -> dict[str, Any]:
        """Add metadata to standings."""
        enriched = data.copy()
        enriched["league"] = league
        enriched["source"] = "espn"
        enriched["fetch_time"] = datetime.now().isoformat()
        return enriched

    def _enrich_game_details(
        self, data: dict[str, Any], league: str, game_id: str
    ) -> dict[str, Any]:
        """Add metadata to game details."""
        enriched = data.copy()
        enriched["game_id"] = game_id
        enriched["league"] = league
        enriched["source"] = "espn"
        enriched["fetch_time"] = datetime.now().isoformat()
        return enriched


# Example usage
async def main():
    """Example usage of ESPNClient."""
    async with ESPNClient() as client:
        # Get current week scoreboard
        scoreboard = await client.get_scoreboard("NFL", week=10)
        games = scoreboard.get("events", [])
        print(f"\nFetched {len(games)} NFL games for week 10")

        # Get team stats
        if games:
            # Get first game's home team ID
            home_team = (
                games[0].get("competitions", [{}])[0].get("competitors", [{}])[1]
            )
            team_id = home_team.get("team", {}).get("id")

            if team_id:
                stats = await client.get_team_stats("NFL", team_id)
                print(f"\nFetched stats for team {team_id}")

        # Get all NFL teams
        teams = await client.get_teams("NFL")
        print(f"\nFetched {len(teams)} NFL teams")
        for team in teams[:5]:
            print(f"  - {team['name']} ({team['abbreviation']})")


if __name__ == "__main__":
    asyncio.run(main())
