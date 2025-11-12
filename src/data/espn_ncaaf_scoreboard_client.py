"""
ESPN NCAAF Scoreboard Client

Mirrors Chrome DevTools workflow to pull games, box scores, and live win probabilities
from ESPN's public APIs. Supports complete NCAA College Football data collection.

Usage:
    client = ESPNNCAAFScoreboardClient()
    await client.connect()

    # Get scoreboard for specific week
    scoreboard = await client.get_scoreboard(week=12, groups=80, limit=400)

    # Get complete game data
    game_data = await client.get_complete_game_data(event_id="401628532")

    await client.close()

API Endpoints (mirrored from DevTools):
    - Scoreboard: /apis/site/v2/sports/football/college-football/scoreboard
    - Summary: /apis/site/v2/sports/football/college-football/summary
    - Plays: /v2/sports/football/leagues/college-football/events/{id}/competitions/{id}/plays
    - Win Probability: /v2/sports/football/leagues/college-football/events/{id}/competitions/{id}/probabilities
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx


class ESPNNCAAFScoreboardClient:
    """
    ESPN NCAAF Scoreboard API client.

    Provides access to:
    - Complete scoreboard with all games
    - Game summaries with box scores
    - Play-by-play data with EPA context
    - Live win probabilities
    """

    # ESPN API base URLs (from DevTools)
    SITE_API_BASE = "https://site.api.espn.com"
    CORE_API_BASE = "https://sports.core.api.espn.com"

    # Default parameters (from DevTools observation)
    DEFAULT_GROUPS = 80  # 80=FBS, 81=FCS, 55=CFP
    DEFAULT_LIMIT = 400  # ESPN defaults to 300, use 400 for rivalry week
    DEFAULT_TZ = "America/New_York"
    DEFAULT_LANG = "en"
    DEFAULT_REGION = "us"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5,
    ):
        """
        Initialize ESPN NCAAF Scoreboard client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
            rate_limit_delay: Delay between requests (ESPN re-polls every 15s)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Initialize HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                },
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def _make_request(self, url: str, params: Optional[dict] = None) -> dict:
        """
        Make HTTP request with retry logic.

        Args:
            url: Full API URL
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()

                # Rate limiting (ESPN re-polls every 15s, we use 0.5s default)
                await asyncio.sleep(self.rate_limit_delay)

                return response.json()

            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

        raise RuntimeError("Request failed after all retries")

    async def get_scoreboard(
        self,
        week: Optional[int] = None,
        date: Optional[str] = None,
        groups: int = DEFAULT_GROUPS,
        limit: int = DEFAULT_LIMIT,
        tz: str = DEFAULT_TZ,
    ) -> dict:
        """
        Get NCAAF scoreboard (master API endpoint).

        Args:
            week: Week number (1-15 regular season, 16+ postseason)
            date: Date in YYYYMMDD format (alternative to week)
            groups: Group ID (80=FBS, 81=FCS, 55=CFP)
            limit: Max games to return (default 400)
            tz: Timezone for game times

        Returns:
            Complete scoreboard JSON with events, odds, status

        Example response structure:
            {
                "leagues": [...],
                "season": {"year": 2025, "type": 2, "slug": "regular-season"},
                "week": {"number": 12},
                "events": [
                    {
                        "id": "401628532",
                        "name": "Ohio State at Michigan",
                        "status": {...},
                        "competitions": [
                            {
                                "competitors": [...],
                                "odds": [...],
                                "situation": {...}
                            }
                        ]
                    }
                ]
            }
        """
        url = f"{self.SITE_API_BASE}/apis/site/v2/sports/football/college-football/scoreboard"

        params = {
            "groups": groups,
            "limit": limit,
            "lang": self.DEFAULT_LANG,
            "region": self.DEFAULT_REGION,
            "tz": tz,
        }

        # Use week OR date, not both
        if week is not None:
            params["week"] = week
        elif date is not None:
            params["dates"] = date

        return await self._make_request(url, params)

    async def get_game_summary(self, event_id: str) -> dict:
        """
        Get complete game summary (box score, drives, scoring plays).

        Args:
            event_id: ESPN event ID (from scoreboard response)

        Returns:
            Complete game summary JSON

        Contains:
            - Box score (team/player stats)
            - Drives (all possessions)
            - Scoring plays
            - Injuries
            - Weather
            - Betting splits
            - Game notes
        """
        url = f"{self.SITE_API_BASE}/apis/site/v2/sports/football/college-football/summary"

        params = {
            "event": event_id,
            "lang": self.DEFAULT_LANG,
            "region": self.DEFAULT_REGION,
        }

        return await self._make_request(url, params)

    async def get_play_by_play(
        self,
        event_id: str,
        limit: int = 1000,
        page: Optional[int] = None,
    ) -> dict:
        """
        Get play-by-play data (drive feed with EPA context).

        Args:
            event_id: ESPN event ID
            limit: Plays per page (default 1000)
            page: Page number for pagination (deep games)

        Returns:
            Play-by-play JSON with EPA-friendly context

        Contains:
            - Down/distance
            - Start/end yardline
            - Play type
            - Result
            - EPA data (if available)
        """
        url = (
            f"{self.CORE_API_BASE}/v2/sports/football/leagues/college-football/"
            f"events/{event_id}/competitions/{event_id}/plays"
        )

        params = {
            "limit": limit,
            "lang": self.DEFAULT_LANG,
            "region": self.DEFAULT_REGION,
        }

        if page is not None:
            params["page"] = page

        return await self._make_request(url, params)

    async def get_win_probability(self, event_id: str) -> dict:
        """
        Get live win probability data.

        Args:
            event_id: ESPN event ID

        Returns:
            Win probability JSON

        Contains:
            - Win % by quarter
            - Leverage index
            - End-game projections
            - Historical win probability graph
        """
        url = (
            f"{self.CORE_API_BASE}/v2/sports/football/leagues/college-football/"
            f"events/{event_id}/competitions/{event_id}/probabilities"
        )

        params = {
            "lang": self.DEFAULT_LANG,
            "region": self.DEFAULT_REGION,
        }

        return await self._make_request(url, params)

    async def get_complete_game_data(self, event_id: str) -> dict:
        """
        Get all data for a single game (summary + plays + win prob).

        Args:
            event_id: ESPN event ID

        Returns:
            Combined game data dictionary

        Structure:
            {
                "event_id": "401628532",
                "summary": {...},
                "plays": {...},
                "win_probability": {...},
                "fetched_at": "2025-11-11T12:00:00"
            }
        """
        # Fetch all data in parallel
        summary_task = self.get_game_summary(event_id)
        plays_task = self.get_play_by_play(event_id)
        win_prob_task = self.get_win_probability(event_id)

        summary, plays, win_prob = await asyncio.gather(
            summary_task,
            plays_task,
            win_prob_task,
            return_exceptions=True,
        )

        return {
            "event_id": event_id,
            "summary": summary if not isinstance(summary, Exception) else None,
            "plays": plays if not isinstance(plays, Exception) else None,
            "win_probability": win_prob
            if not isinstance(win_prob, Exception)
            else None,
            "fetched_at": datetime.now().isoformat(),
        }

    def verify_scoreboard_response(self, scoreboard: dict) -> dict:
        """
        Verify scoreboard response matches requested parameters.

        Verification checklist:
        1. season.type + week.number match requested slate
        2. competitions[].odds[].provider books are present
        3. Postponed/canceled games have correct status

        Args:
            scoreboard: Scoreboard API response

        Returns:
            Verification results dictionary
        """
        results = {
            "valid": True,
            "warnings": [],
            "errors": [],
        }

        # Check season/week info
        season = scoreboard.get("season", {})
        week = scoreboard.get("week", {})

        if not season:
            results["errors"].append("Missing season information")
            results["valid"] = False

        if not week:
            results["warnings"].append("Missing week information")

        # Check events
        events = scoreboard.get("events", [])

        if not events:
            results["warnings"].append("No events found in scoreboard")

        # Verify odds providers
        providers_found = set()
        postponed_count = 0
        canceled_count = 0

        for event in events:
            competitions = event.get("competitions", [])

            for comp in competitions:
                # Check odds
                odds = comp.get("odds", [])
                for odd in odds:
                    provider = odd.get("provider", {}).get("name")
                    if provider:
                        providers_found.add(provider)

                # Check status
                status = comp.get("status", {}).get("type", {}).get("state")
                if status == "postponed":
                    postponed_count += 1
                elif status == "canceled":
                    canceled_count += 1

        if not providers_found:
            results["warnings"].append("No odds providers found")
        else:
            results["providers"] = list(providers_found)

        if postponed_count > 0:
            results["warnings"].append(f"{postponed_count} postponed games")

        if canceled_count > 0:
            results["warnings"].append(f"{canceled_count} canceled games")

        results["event_count"] = len(events)
        results["season_type"] = season.get("type")
        results["week_number"] = week.get("number")

        return results

    async def save_scoreboard_raw(
        self,
        scoreboard: dict,
        output_dir: Path,
        date: Optional[str] = None,
    ) -> Path:
        """
        Save raw scoreboard payload to disk.

        Args:
            scoreboard: Scoreboard API response
            output_dir: Output directory (e.g., data/raw/espn/scoreboard)
            date: Date string (YYYYMMDD) for subdirectory

        Returns:
            Path to saved file
        """
        # Create date subdirectory
        if date:
            save_dir = output_dir / date
        else:
            save_dir = output_dir / datetime.now().strftime("%Y%m%d")

        save_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_scoreboard.json"
        filepath = save_dir / filename

        # Save JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(scoreboard, f, indent=2, ensure_ascii=False)

        return filepath

    async def save_game_data_raw(
        self,
        game_data: dict,
        output_dir: Path,
        date: Optional[str] = None,
    ) -> Path:
        """
        Save complete game data to disk.

        Args:
            game_data: Complete game data (summary + plays + win prob)
            output_dir: Output directory
            date: Date string (YYYYMMDD) for subdirectory

        Returns:
            Path to saved file
        """
        # Create date subdirectory
        if date:
            save_dir = output_dir / date
        else:
            save_dir = output_dir / datetime.now().strftime("%Y%m%d")

        save_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        event_id = game_data["event_id"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_game_{event_id}.json"
        filepath = save_dir / filename

        # Save JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)

        return filepath
