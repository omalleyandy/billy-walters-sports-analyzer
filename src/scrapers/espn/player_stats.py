"""
ESPN Player Stats Client

Fetches individual player statistics for NFL and NCAAF directly from ESPN's
public statistics API. Supports multiple stat categories: passing, rushing,
receiving, defensive, kicking, and punting.

Usage:
    client = ESPNPlayerStatsClient()
    await client.connect()

    # Get NFL stats leaders
    stats = await client.get_nfl_stats()

    # Get specific stat category
    passing_leaders = await client.get_nfl_stats(stat_category="passingYards")

    # Get NCAAF stats
    ncaaf_stats = await client.get_ncaaf_stats()

    await client.close()

API Endpoints:
    - NFL: /apis/site/v2/sports/football/nfl/statistics
    - NCAAF: /apis/site/v2/sports/football/college-football/statistics

Stat Categories:
    - passingYards: Passing yards leaders
    - passingTouchdowns: Passing touchdowns
    - rushingYards: Rushing yards leaders
    - rushingTouchdowns: Rushing touchdowns
    - receivingYards: Receiving yards leaders
    - receivingTouchdowns: Receiving touchdowns
    - tackles: Tackles leaders (defensive)
    - sacks: Sacks leaders (defensive)
    - interceptions: Interceptions (defensive)
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class ESPNPlayerStatsClient:
    """
    ESPN Player Stats API client.

    Provides access to:
    - League-wide stat leaders across all categories
    - Individual player statistics
    - Season stats (aggregated) and game-by-game stats
    - Multiple leagues: NFL and NCAAF
    """

    # ESPN API base URLs
    SITE_API_BASE = "https://site.api.espn.com"

    # Supported stat categories (as returned by API)
    STAT_CATEGORIES = {
        "passing": ["passingYards", "passingTouchdowns", "interceptions"],
        "rushing": ["rushingYards", "rushingTouchdowns"],
        "receiving": ["receivingYards", "receivingTouchdowns", "receptions"],
        "defensive": ["tackles", "sacks", "interceptions", "forcedFumbles"],
        "kicking": ["fieldGoals", "fieldGoalAttempts", "extraPointsMade"],
        "punting": ["puntingYards", "puntingAverage"],
    }

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5,
    ):
        """
        Initialize ESPN Player Stats client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
            rate_limit_delay: Delay between requests (seconds)
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

                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)

                return response.json()

            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

        raise RuntimeError("Request failed after all retries")

    async def get_nfl_stats(self, stat_category: Optional[str] = None) -> dict:
        """
        Get NFL player statistics leaders.

        Args:
            stat_category: Optional specific stat (e.g., 'passingYards')
                          If None, returns all available categories

        Returns:
            Statistics data with leaders and player info

        Example response structure:
            {
                "timestamp": "2025-11-25T07:47:23Z",
                "status": "success",
                "season": {"year": 2025, "type": 2, "name": "Regular Season"},
                "league": {...},
                "stats": {
                    "categories": [
                        {
                            "name": "passingYards",
                            "displayName": "Passing Yards",
                            "leaders": [
                                {
                                    "displayValue": "520",
                                    "athlete": {...},
                                    "team": {...}
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                }
            }
        """
        url = f"{self.SITE_API_BASE}/apis/site/v2/sports/football/nfl/statistics"

        params = {"lang": "en-US", "region": "us"}

        data = await self._make_request(url, params)

        # Filter to specific category if requested
        if stat_category and "stats" in data and "categories" in data["stats"]:
            categories = data["stats"]["categories"]
            data["stats"]["categories"] = [
                c for c in categories if c.get("name") == stat_category
            ]

        return data

    async def get_ncaaf_stats(self, stat_category: Optional[str] = None) -> dict:
        """
        Get NCAAF player statistics leaders.

        Args:
            stat_category: Optional specific stat (e.g., 'passingYards')

        Returns:
            Statistics data with leaders and player info
        """
        url = (
            f"{self.SITE_API_BASE}/apis/site/v2/sports/football/"
            f"college-football/statistics"
        )

        params = {"lang": "en-US", "region": "us"}

        data = await self._make_request(url, params)

        # Filter to specific category if requested
        if stat_category and "stats" in data and "categories" in data["stats"]:
            categories = data["stats"]["categories"]
            data["stats"]["categories"] = [
                c for c in categories if c.get("name") == stat_category
            ]

        return data

    def extract_stat_leaders(self, stats_data: dict) -> list[dict]:
        """
        Extract player stats leaders from API response.

        Args:
            stats_data: Raw stats data from API

        Returns:
            List of player stat records

        Example:
            [
                {
                    "stat_category": "passingYards",
                    "player_id": "3120590",
                    "player_name": "Easton Stick",
                    "team_abbr": "ATL",
                    "team_name": "Atlanta Falcons",
                    "value": 520.0,
                    "displayValue": "520",
                    "rank": 1,
                    "position": "QB",
                    "jersey": "12"
                },
                ...
            ]
        """
        leaders = []

        if "stats" not in stats_data or "categories" not in stats_data["stats"]:
            return leaders

        categories = stats_data["stats"]["categories"]

        for category in categories:
            category_name = category.get("name", "")
            category_display = category.get("displayName", "")

            stat_leaders = category.get("leaders", [])

            for rank, leader in enumerate(stat_leaders, 1):
                athlete = leader.get("athlete", {})
                team = leader.get("team", {})

                record = {
                    "stat_category": category_name,
                    "stat_category_display": category_display,
                    "rank": rank,
                    "player_id": athlete.get("id"),
                    "player_name": athlete.get("displayName"),
                    "player_short_name": athlete.get("shortName"),
                    "position": athlete.get("position", {}).get("abbreviation"),
                    "jersey": athlete.get("jersey"),
                    "team_id": team.get("id"),
                    "team_name": team.get("displayName"),
                    "team_abbr": team.get("abbreviation"),
                    "value": leader.get("value"),
                    "displayValue": leader.get("displayValue"),
                    "headshot_url": athlete.get("headshot", {}).get("href"),
                    "player_card_url": next(
                        (
                            link.get("href")
                            for link in athlete.get("links", [])
                            if link.get("rel") == ["playercard", "desktop", "athlete"]
                        ),
                        None,
                    ),
                }

                leaders.append(record)

        return leaders

    async def save_stats_json(
        self,
        stats_data: dict,
        output_dir: Path,
        league: str = "nfl",
    ) -> Path:
        """
        Save raw statistics data to JSON file.

        Args:
            stats_data: Statistics API response
            output_dir: Output directory
            league: 'nfl' or 'ncaaf'

        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"player_stats_{league}_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved player stats: {filepath}")
        return filepath

    async def save_stats_leaders_json(
        self,
        leaders: list[dict],
        output_dir: Path,
        league: str = "nfl",
    ) -> Path:
        """
        Save extracted stat leaders to JSON file.

        Args:
            leaders: Extracted leaders list
            output_dir: Output directory
            league: 'nfl' or 'ncaaf'

        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"player_stats_leaders_{league}_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(leaders, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved player stats leaders: {filepath}")
        return filepath
