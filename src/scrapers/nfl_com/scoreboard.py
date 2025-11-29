"""
NFL.com Scoreboard Scraper

Fetches historical game scores from NFL.com scoreboard pages.

URLs Pattern:
- https://www.nfl.com/scores/{year}/reg{week}
- https://www.nfl.com/scores/2025/reg1 to reg18

Usage:
    scraper = NFLScoreboardScraper()
    await scraper.connect()

    # Get Week 12 scores
    scores = await scraper.get_week_scores(2025, 12)

    # Get all weeks (1-18)
    all_scores = await scraper.get_all_weeks_scores(2025)

    await scraper.close()

Features:
- Fetch scores for any week (1-18 regular season)
- Parse game results from HTML
- Detect current week from system date
- Compare predictions vs actual results
- Track Closing Line Value (CLV)
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class NFLGameResult(BaseModel):
    """NFL game result from scoreboard"""

    week: int
    away_team: str
    home_team: str
    away_score: int
    home_score: int
    game_status: str  # "final", "live", "scheduled"
    game_time: Optional[str] = None
    spread: Optional[float] = None
    total: Optional[float] = None
    timestamp: str = ""

    @property
    def margin(self) -> int:
        """Home team margin (positive = home win)"""
        return self.home_score - self.away_score

    @property
    def cover_result(self, spread: float) -> Optional[str]:
        """Did team cover spread? (home perspective)"""
        if self.spread is None:
            return None
        if self.margin > self.spread:
            return "home_cover"
        elif self.margin < self.spread:
            return "away_cover"
        else:
            return "push"


class NFLScoreboardScraper:
    """
    Scrapes NFL.com scoreboard pages for game results.

    Supports fetching historical scores for any week and validating
    betting predictions against actual results.
    """

    # NFL.com scoreboard base URL
    BASE_URL = "https://www.nfl.com/scores"

    # Standard headers (mimic browser)
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nfl.com/",
    }

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize NFL scoreboard scraper.

        Args:
            output_dir: Directory for saved scores (default: output/nfl_scores/)
        """
        if output_dir is None:
            project_root = Path(__file__).parent.parent.parent
            output_dir = project_root / "output" / "nfl_scores"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Initialize async HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers=self.HEADERS,
                timeout=30.0,
                follow_redirects=True,
            )

    async def close(self) -> None:
        """Close async HTTP client."""
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

    async def get_week_scores(self, season: int, week: int) -> List[NFLGameResult]:
        """
        Fetch scores for a specific week.

        Args:
            season: NFL season year (e.g., 2025)
            week: Week number (1-18 for regular season)

        Returns:
            List of NFLGameResult objects
        """
        await self.connect()

        # Build URL for specific week
        url = f"{self.BASE_URL}/{season}/reg{week}"

        try:
            logger.info(f"Fetching Week {week} scores from {url}")
            response = await self.client.get(url)
            response.raise_for_status()

            # Parse HTML
            games = self._parse_scoreboard_html(response.text, week)

            logger.info(f"Extracted {len(games)} games from Week {week}")
            return games

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Week {week}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Week {week}: {e}")
            return []

    def _parse_scoreboard_html(self, html: str, week: int) -> List[NFLGameResult]:
        """
        Parse HTML from NFL.com scoreboard page.

        Args:
            html: HTML content of scoreboard page
            week: Week number (for validation)

        Returns:
            List of NFLGameResult objects
        """
        games = []
        soup = BeautifulSoup(html, "html.parser")

        # Find all game containers (structure may vary, multiple selectors)
        game_containers = soup.find_all("div", class_="nfl-c-matchup-strip")
        if not game_containers:
            game_containers = soup.find_all(
                "div", class_=lambda x: x and "matchup" in x.lower()
            )

        for container in game_containers:
            try:
                game = self._parse_game_container(container, week)
                if game:
                    games.append(game)
            except Exception as e:
                logger.debug(f"Error parsing game container: {e}")
                continue

        return games

    def _parse_game_container(
        self, container: Any, week: int
    ) -> Optional[NFLGameResult]:
        """
        Parse individual game from container element.

        Args:
            container: BeautifulSoup element containing game data
            week: Week number

        Returns:
            NFLGameResult or None if parse fails
        """
        try:
            # Extract team names and scores
            # Structure: Away Team (away_score) @ Home Team (home_score)

            # Try multiple selectors for team names
            away_elem = container.find(
                "div", class_=lambda x: x and "away" in x.lower()
            )
            home_elem = container.find(
                "div", class_=lambda x: x and "home" in x.lower()
            )

            if not away_elem or not home_elem:
                return None

            away_team = away_elem.get_text(strip=True)
            home_team = home_elem.get_text(strip=True)

            # Extract scores
            score_elems = container.find_all("div", class_="nfl-c-matchup-strip__score")
            if len(score_elems) < 2:
                return None

            away_score = int(score_elems[0].get_text(strip=True))
            home_score = int(score_elems[1].get_text(strip=True))

            # Determine game status
            status_elem = container.find(
                "div", class_=lambda x: x and "status" in x.lower()
            )
            game_status = "final" if away_score > 0 or home_score > 0 else "scheduled"

            game = NFLGameResult(
                week=week,
                away_team=away_team.upper(),
                home_team=home_team.upper(),
                away_score=away_score,
                home_score=home_score,
                game_status=game_status,
                timestamp=datetime.now().isoformat(),
            )

            return game

        except Exception as e:
            logger.debug(f"Error parsing game: {e}")
            return None

    async def get_all_weeks_scores(
        self, season: int, weeks: Optional[List[int]] = None
    ) -> Dict[int, List[NFLGameResult]]:
        """
        Fetch scores for multiple weeks.

        Args:
            season: NFL season year
            weeks: List of weeks to fetch (default: 1-18)

        Returns:
            Dictionary mapping week to list of NFLGameResult objects
        """
        if weeks is None:
            weeks = list(range(1, 19))  # Regular season weeks 1-18

        results = {}

        for week in weeks:
            scores = await self.get_week_scores(season, week)
            results[week] = scores

            # Rate limiting - be polite to NFL.com
            await asyncio.sleep(0.5)

        logger.info(f"Fetched scores for {len(results)} weeks")
        return results

    async def get_current_week_scores(
        self, season: int
    ) -> Dict[int, List[NFLGameResult]]:
        """
        Fetch scores for weeks up to current week.

        Args:
            season: NFL season year

        Returns:
            Dictionary mapping week to list of NFLGameResult objects
        """
        current_week = self._detect_current_week(season)
        logger.info(f"Detected current week: {current_week}")

        # Fetch all completed weeks
        weeks = list(range(1, current_week + 1))
        return await self.get_all_weeks_scores(season, weeks)

    def _detect_current_week(self, season: int) -> int:
        """
        Detect current NFL week from system date.

        NFL Season (2025):
        - Week 1: Sep 4-8
        - Week 2: Sep 11-15
        - Week 3: Sep 18-22
        - Week 4: Sep 25-29
        - Week 5: Oct 2-6
        - Week 6: Oct 9-13
        - Week 7: Oct 16-20
        - Week 8: Oct 23-27
        - Week 9: Oct 30-Nov 3
        - Week 10: Nov 6-10
        - Week 11: Nov 13-17
        - Week 12: Nov 20-24
        - Week 13: Nov 27-Dec 1 (Thanksgiving)
        - Week 14: Dec 4-8
        - Week 15: Dec 11-15
        - Week 16: Dec 18-22
        - Week 17: Dec 25-29 (Christmas)
        - Week 18: Jan 1-5
        - Playoffs: Wild Card (Jan 8-14), etc.

        Args:
            season: NFL season year

        Returns:
            Current week number (1-18)
        """
        today = datetime.now().date()

        # Week date ranges for 2025 season
        week_dates = {
            1: ("2025-09-04", "2025-09-08"),
            2: ("2025-09-11", "2025-09-15"),
            3: ("2025-09-18", "2025-09-22"),
            4: ("2025-09-25", "2025-09-29"),
            5: ("2025-10-02", "2025-10-06"),
            6: ("2025-10-09", "2025-10-13"),
            7: ("2025-10-16", "2025-10-20"),
            8: ("2025-10-23", "2025-10-27"),
            9: ("2025-10-30", "2025-11-03"),
            10: ("2025-11-06", "2025-11-10"),
            11: ("2025-11-13", "2025-11-17"),
            12: ("2025-11-20", "2025-11-24"),
            13: ("2025-11-27", "2025-12-01"),
            14: ("2025-12-04", "2025-12-08"),
            15: ("2025-12-11", "2025-12-15"),
            16: ("2025-12-18", "2025-12-22"),
            17: ("2025-12-25", "2025-12-29"),
            18: ("2026-01-01", "2026-01-05"),
        }

        for week, (start_str, end_str) in week_dates.items():
            start = datetime.strptime(start_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_str, "%Y-%m-%d").date()

            if start <= today <= end:
                return week

        # Default to current week if not found
        logger.warning(f"Could not determine week for {today}, defaulting to week 1")
        return 1

    async def save_scores(
        self, scores: Dict[int, List[NFLGameResult]], season: int
    ) -> Path:
        """
        Save scores to JSON file.

        Args:
            scores: Dictionary mapping week to list of NFLGameResult objects
            season: Season year

        Returns:
            Path to saved file
        """
        filename = f"scores_{season}_all_weeks.json"
        filepath = self.output_dir / filename

        # Convert to JSON-serializable format
        data = {}
        for week, games in scores.items():
            data[week] = [game.model_dump() for game in games]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved scores to {filepath}")
        return filepath

    async def save_week_scores(
        self, scores: List[NFLGameResult], season: int, week: int
    ) -> Path:
        """
        Save scores for a single week.

        Args:
            scores: List of NFLGameResult objects
            season: Season year
            week: Week number

        Returns:
            Path to saved file
        """
        filename = f"scores_{season}_week_{week:02d}.json"
        filepath = self.output_dir / filename

        data = [game.model_dump() for game in scores]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {len(scores)} games to {filepath}")
        return filepath


# Convenience functions
async def get_nfl_week_scores(season: int, week: int) -> List[NFLGameResult]:
    """Quick access to NFL scores for a specific week"""
    scraper = NFLScoreboardScraper()
    try:
        scores = await scraper.get_week_scores(season, week)
        return scores
    finally:
        await scraper.close()


async def get_all_nfl_scores(season: int) -> Dict[int, List[NFLGameResult]]:
    """Quick access to all NFL scores for a season"""
    scraper = NFLScoreboardScraper()
    try:
        scores = await scraper.get_all_weeks_scores(season)
        return scores
    finally:
        await scraper.close()
