"""ProFootballDoc fetcher for injury reports with point value impact."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ProFootballDocFetcher:
    """Client for fetching injury reports from ProFootballDoc."""

    BASE_URL = "https://www.profootballdoc.com"

    def __init__(self) -> None:
        """Initialize ProFootballDoc fetcher."""
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "Mozilla/5.0 (Educational Research Bot)"}
            )
        return self._session

    async def get_team_injuries(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Fetch injury report for a team.

        Args:
            team_name: Team name (e.g., "Philadelphia Eagles")

        Returns:
            List of injury dicts with player, position, status, impact points
        """
        # For now, return empty list - this would need actual scraping implementation
        # The real implementation would:
        # 1. Normalize team name to ProFootballDoc URL format
        # 2. Fetch the injury page
        # 3. Parse injury data with BeautifulSoup
        # 4. Map injuries to point values

        logger.debug(f"Fetching injuries for {team_name}")

        # Placeholder - replace with actual implementation
        # For now, try to load from local injury data if available
        return await self._get_cached_injuries(team_name)

    async def _get_cached_injuries(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Load injuries from local cache (data/injuries directory).

        Args:
            team_name: Team name

        Returns:
            List of injury dicts
        """
        import json
        from pathlib import Path

        # Try to find cached injury data
        injury_dir = Path("data/injuries")
        if not injury_dir.exists():
            return []

        # Search for recent injury files
        for sport_dir in ["nfl", "ncaaf"]:
            sport_path = injury_dir / sport_dir
            if not sport_path.exists():
                continue

            # Load most recent JSONL file
            jsonl_files = sorted(sport_path.glob("*.jsonl"), reverse=True)
            if not jsonl_files:
                continue

            injuries = []
            with open(jsonl_files[0], "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        injury_data = json.loads(line)
                        # Check if this injury belongs to the requested team
                        if self._team_matches(injury_data.get("team", ""), team_name):
                            injuries.append(
                                {
                                    "name": injury_data.get("player", "Unknown"),
                                    "position": injury_data.get("position", "UNK"),
                                    "status": injury_data.get("status", "Questionable"),
                                    "injury": injury_data.get("injury_type", "Unknown"),
                                    "points": self._estimate_point_value(
                                        injury_data.get("position", "UNK"),
                                        injury_data.get("status", "Questionable"),
                                    ),
                                }
                            )
                    except json.JSONDecodeError:
                        continue

            if injuries:
                logger.info(f"Loaded {len(injuries)} cached injuries for {team_name}")
                return injuries

        return []

    def _team_matches(self, stored_name: str, query_name: str) -> bool:
        """Check if team names match (flexible matching)."""
        stored = stored_name.lower().replace(" ", "")
        query = query_name.lower().replace(" ", "")
        return stored == query or stored in query or query in stored

    def _estimate_point_value(self, position: str, status: str) -> float:
        """
        Estimate point impact value for an injury.

        Args:
            position: Player position
            status: Injury status (Out, Doubtful, Questionable, etc.)

        Returns:
            Estimated point value impact
        """
        # Base values by position (when Out)
        position_values = {
            "QB": 10.0,
            "RB": 3.0,
            "WR": 2.5,
            "TE": 2.0,
            "OL": 1.5,
            "OT": 1.8,
            "OG": 1.3,
            "C": 1.5,
            "DE": 2.0,
            "DT": 1.5,
            "LB": 2.0,
            "CB": 2.5,
            "S": 2.0,
            "K": 0.5,
            "P": 0.3,
        }

        # Status multipliers
        status_multipliers = {
            "Out": 1.0,
            "Doubtful": 0.75,
            "Questionable": 0.35,
            "Probable": 0.15,
            "IR": 1.0,
            "PUP": 1.0,
        }

        base_value = position_values.get(position.upper(), 1.0)
        multiplier = status_multipliers.get(status, 0.5)

        return round(base_value * multiplier, 1)

    async def scrape_live_injuries(self, sport: str = "nfl") -> List[Dict[str, Any]]:
        """
        Scrape live injury data from ProFootballDoc.

        Args:
            sport: Sport type (nfl or ncaaf)

        Returns:
            List of all current injuries
        """
        # This would implement actual web scraping
        # For now, return empty list
        logger.warning("Live injury scraping not yet implemented")
        return []

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
