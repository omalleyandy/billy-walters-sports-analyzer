"""
ESPN NFL Scoreboard Client

Fetches NFL game scores from ESPN's public API endpoint discovered via
Chrome DevTools reverse engineering.

Data Sources:
- Scoreboard: Game scores, status, times
- Summary: Full game details, statistics
- Plays: Play-by-play data

Usage:
    client = ESPNNFLScoreboardClient()
    await client.connect()

    # Get scoreboard for specific week
    scoreboard = await client.get_scoreboard(week=12)

    # Get complete game data
    game_data = await client.get_game_summary(event_id="401772946")

    await client.close()

API Endpoints (from DevTools):
    - Scoreboard: /apis/site/v2/sports/football/nfl/scoreboard?week={week}
    - Summary: /apis/site/v2/sports/football/nfl/summary?id={id}
    - Events: /apis/site/v2/sports/football/nfl/events
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class ESPNNFLScoreboardClient:
    """
    ESPN NFL Scoreboard API client.

    Provides access to:
    - Complete scoreboard with all games and scores
    - Game summaries with box scores
    - Play-by-play data
    - Real-time game status
    """

    # ESPN API base URLs (from DevTools)
    SITE_API_BASE = "https://site.api.espn.com"
    CORE_API_BASE = "https://sports.core.api.espn.com"

    # Default parameters
    DEFAULT_TZ = "America/New_York"
    DEFAULT_LANG = "en"
    DEFAULT_REGION = "us"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 0.3,
    ):
        """
        Initialize ESPN NFL Scoreboard client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
            rate_limit_delay: Delay between requests
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

    async def get_scoreboard(
        self, week: Optional[int] = None, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get NFL scoreboard (all games for a week or current week).

        Args:
            week: Week number (1-18). If None, gets current week
            limit: Maximum games to return

        Returns:
            Dictionary with events list containing game data
        """
        await self.connect()

        # Build endpoint
        endpoint = f"{self.SITE_API_BASE}/apis/site/v2/sports/football/nfl/scoreboard"

        params = {
            "limit": limit,
            "region": self.DEFAULT_REGION,
            "lang": self.DEFAULT_LANG,
        }

        if week:
            params["week"] = week

        try:
            logger.info(f"Fetching NFL scoreboard{f' (Week {week})' if week else ''}")
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(
                f"Retrieved {len(data.get('events', []))} games from scoreboard"
            )

            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching scoreboard: {e}")
            return {"events": []}
        except Exception as e:
            logger.error(f"Error fetching scoreboard: {e}")
            return {"events": []}

    async def get_game_summary(self, event_id: str) -> dict[str, Any]:
        """
        Get complete game summary with box scores.

        Args:
            event_id: ESPN event ID (e.g., "401772946")

        Returns:
            Dictionary with game summary data
        """
        await self.connect()

        endpoint = f"{self.SITE_API_BASE}/apis/site/v2/sports/football/nfl/summary"

        params = {
            "id": event_id,
            "region": self.DEFAULT_REGION,
            "lang": self.DEFAULT_LANG,
        }

        try:
            logger.info(f"Fetching game summary for event {event_id}")
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()
            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching game summary: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching game summary: {e}")
            return {}

    async def get_all_weeks_scores(
        self, season: int, weeks: Optional[list[int]] = None
    ) -> dict[int, list[dict[str, Any]]]:
        """
        Fetch scores for multiple weeks.

        Args:
            season: NFL season year (e.g., 2025)
            weeks: List of weeks (default: 1-18 for regular season)

        Returns:
            Dictionary mapping week to list of games
        """
        if weeks is None:
            weeks = list(range(1, 19))

        results = {}

        for week in weeks:
            scoreboard = await self.get_scoreboard(week=week)

            # Extract game results
            games = []
            for event in scoreboard.get("events", []):
                game = self._parse_game(event)
                if game:
                    games.append(game)

            results[week] = games

            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

        logger.info(f"Fetched scores for {len(results)} weeks")
        return results

    def _parse_game(self, event: dict[str, Any]) -> Optional[dict[str, Any]]:
        """
        Parse individual game from event data.

        Args:
            event: Game event from ESPN API

        Returns:
            Dictionary with game data or None
        """
        try:
            competition = event.get("competitions", [{}])[0]

            # ESPN uses "competitors" array (index 0=home, index 1=away)
            # OR separate away/home objects (legacy)
            competitors = competition.get("competitors", [])

            if competitors and len(competitors) >= 2:
                # New format: competitors array with homeAway field
                away_comp = next(
                    (c for c in competitors if c.get("homeAway") == "away"), None
                )
                home_comp = next(
                    (c for c in competitors if c.get("homeAway") == "home"), None
                )

                if not away_comp or not home_comp:
                    return None

                away_team = away_comp.get("team", {}).get("abbreviation", "")
                home_team = home_comp.get("team", {}).get("abbreviation", "")
                away_score = int(away_comp.get("score", 0) or 0)
                home_score = int(home_comp.get("score", 0) or 0)
            else:
                # Fallback to legacy format
                away = competition.get("away", {})
                home = competition.get("home", {})
                away_team = away.get("team", {}).get("abbreviation", "")
                home_team = home.get("team", {}).get("abbreviation", "")
                away_score = int(away.get("score", 0) or 0)
                home_score = int(home.get("score", 0) or 0)

            game = {
                "event_id": event.get("id", ""),
                "week": event.get("week", {}).get("number", 0),
                "game_status": event.get("status", {}).get("type", {}).get("state", ""),
                "away_team": away_team,
                "home_team": home_team,
                "away_score": away_score,
                "home_score": home_score,
                "game_time": event.get("date", ""),
                "venue": competition.get("venue", {}).get("fullName", ""),
            }

            return game

        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Error parsing game: {e}")
            return None

    async def save_week_scores(
        self,
        games: list[dict[str, Any]],
        week: int,
        output_dir: Optional[Path] = None,
        league: str = "nfl",
    ) -> Path:
        """
        Save week scores to JSON file.

        Args:
            games: List of game dictionaries
            week: Week number
            output_dir: Output directory (default: output/espn/scores/nfl/)
            league: League identifier for path organization

        Returns:
            Path to saved file
        """
        if output_dir is None:
            # NEW: Use organized structure output/espn/scores/{league}/
            output_dir = (
                Path(__file__).parent.parent.parent
                / "output"
                / "espn"
                / "scores"
                / league.lower()
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        # NEW: Use timestamped filename matching other scrapers

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scores_{league.lower()}_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(games, f, indent=2, default=str)

        logger.info(f"Saved {len(games)} games to {filepath}")

        # Backward compatibility: Create symlink in old location
        try:
            old_location = Path(__file__).parent.parent.parent / "output" / "nfl_scores"
            old_location.mkdir(parents=True, exist_ok=True)
            old_filename = f"scores_2025_week_{week:02d}.json"
            old_filepath = old_location / old_filename

            if old_filepath.exists():
                old_filepath.unlink()

            try:
                old_filepath.symlink_to(filepath.resolve())
                logger.info("Created symlink for backward compatibility")
            except OSError:
                # Windows fallback: copy instead of symlink
                import shutil

                shutil.copy2(filepath, old_filepath)
                logger.info("Copied to legacy location for backward compatibility")
        except Exception as e:
            logger.warning(f"Could not create backward compatibility link: {e}")

        return filepath

    async def save_all_scores(
        self,
        scores: dict[int, list[dict[str, Any]]],
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Save all week scores to JSON file.

        Args:
            scores: Dictionary mapping week to list of games
            output_dir: Output directory (default: output/espn/scores/nfl/)

        Returns:
            Path to saved file
        """
        if output_dir is None:
            # NEW: Use organized structure
            output_dir = (
                Path(__file__).parent.parent.parent
                / "output"
                / "espn"
                / "scores"
                / "nfl"
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        # NEW: Use timestamped filename

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scores_nfl_all_weeks_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=2, default=str)

        logger.info(f"Saved all weeks to {filepath}")
        return filepath


# Convenience functions
async def get_nfl_scoreboard(week: Optional[int] = None) -> dict[str, Any]:
    """Quick access to NFL scoreboard"""
    client = ESPNNFLScoreboardClient()
    try:
        scoreboard = await client.get_scoreboard(week=week)
        return scoreboard
    finally:
        await client.close()


async def get_nfl_all_scores(
    weeks: Optional[list[int]] = None,
) -> dict[int, list[dict[str, Any]]]:
    """Quick access to all NFL scores"""
    client = ESPNNFLScoreboardClient()
    try:
        scores = await client.get_all_weeks_scores(2025, weeks)
        return scores
    finally:
        await client.close()
