"""
NFL.com Official API Client

Comprehensive client for NFL.com's official API endpoints discovered via
Chrome DevTools reverse engineering.

Data Sources:
- Schedules: Game times, locations, TV networks
- News: Team news, transactions, injury updates
- Player Stats: Individual performance metrics
- Team Stats: Uses existing nfl_stats_scraper.py
- Injuries: Uses existing nfl_official_injury_scraper.py

Billy Walters Integration:
- Authoritative NFL data (official source)
- Real-time injury updates
- Schedule changes and postponements
- Sharp action via news/transactions
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class NFLGame(BaseModel):
    """NFL game from schedule API"""

    game_id: str
    season: int
    week: int
    game_type: str  # "REG", "POST", "PRE"
    away_team: str
    home_team: str
    game_time: datetime
    stadium: str
    network: Optional[str] = None
    away_score: Optional[int] = None
    home_score: Optional[int] = None
    game_status: str = "scheduled"


class NFLNews(BaseModel):
    """NFL news article"""

    article_id: str
    title: str
    summary: Optional[str] = None
    published_at: datetime
    team: Optional[str] = None
    category: str  # "injury", "transaction", "game_recap", etc.
    url: str


class NFLPlayerStats(BaseModel):
    """NFL player statistics"""

    player_id: str
    player_name: str
    position: str
    team: str
    week: int
    season: int

    # Passing (QB)
    completions: Optional[int] = None
    attempts: Optional[int] = None
    passing_yards: Optional[int] = None
    passing_tds: Optional[int] = None
    interceptions: Optional[int] = None

    # Rushing (RB, QB)
    rushing_attempts: Optional[int] = None
    rushing_yards: Optional[int] = None
    rushing_tds: Optional[int] = None

    # Receiving (WR, TE, RB)
    receptions: Optional[int] = None
    receiving_yards: Optional[int] = None
    receiving_tds: Optional[int] = None
    targets: Optional[int] = None


class NFLComClient:
    """
    NFL.com Official API Client

    Accesses NFL's official API discovered via Chrome DevTools reverse
    engineering. Provides schedules, news, and player statistics.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize NFL.com client.

        Args:
            output_dir: Directory for saved data (default: output/nfl_com/)
        """
        if output_dir is None:
            project_root = Path(__file__).parent.parent.parent
            output_dir = project_root / "output" / "nfl_com"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Official NFL API base URL (discovered via DevTools)
        self.base_url = "https://api.nfl.com"

        # Stealth headers (mimic browser)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nfl.com/",
            "Origin": "https://www.nfl.com",
        }

        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self):
        """Initialize async HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers=self.headers, timeout=30.0, follow_redirects=True
            )

    async def close(self):
        """Close async HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get_schedule(
        self, season: int, week: int, season_type: str = "REG"
    ) -> List[NFLGame]:
        """
        Get NFL schedule for a specific week.

        Args:
            season: NFL season year (e.g., 2025)
            week: Week number (1-18 for regular season)
            season_type: "REG" (regular), "POST" (playoffs), "PRE" (preseason)

        Returns:
            List of NFLGame objects
        """
        await self.connect()

        # NFL API endpoint pattern (discovered via DevTools)
        # Example: /v3/shield/?query=query{games(week:{season:2025,week:12})}
        endpoint = (
            f"{self.base_url}/v3/shield/"
            f"?query=query{{games(week:{{season:{season},week:{week},"
            f"seasonType:{season_type}}})}}"
        )

        try:
            response = await self.client.get(endpoint)
            response.raise_for_status()
            data = response.json()

            games = []
            # Parse response (structure from DevTools inspection)
            if "data" in data and "games" in data["data"]:
                for game_data in data["data"]["games"]:
                    game = NFLGame(
                        game_id=game_data.get("id", ""),
                        season=season,
                        week=week,
                        game_type=season_type,
                        away_team=game_data.get("awayTeam", {}).get("abbr", ""),
                        home_team=game_data.get("homeTeam", {}).get("abbr", ""),
                        game_time=datetime.fromisoformat(game_data.get("gameTime", "")),
                        stadium=game_data.get("venue", {}).get("name", ""),
                        network=game_data.get("network", {}).get("name"),
                        away_score=game_data.get("awayScore"),
                        home_score=game_data.get("homeScore"),
                        game_status=game_data.get("gameStatus", "scheduled"),
                    )
                    games.append(game)

            logger.info(
                f"Fetched {len(games)} games for {season} Week {week} ({season_type})"
            )
            return games

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching schedule: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            return []

    async def get_team_news(
        self, team_abbr: Optional[str] = None, limit: int = 20
    ) -> List[NFLNews]:
        """
        Get latest NFL news articles.

        Args:
            team_abbr: Team abbreviation (e.g., "KC", "BUF") or None for all
            limit: Maximum articles to return

        Returns:
            List of NFLNews objects
        """
        await self.connect()

        # NFL news endpoint (discovered via DevTools)
        endpoint = f"{self.base_url}/v3/shield/news"
        params = {"limit": limit}
        if team_abbr:
            params["team"] = team_abbr

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            news_articles = []
            if "data" in data and "articles" in data["data"]:
                for article in data["data"]["articles"]:
                    news = NFLNews(
                        article_id=article.get("id", ""),
                        title=article.get("title", ""),
                        summary=article.get("summary"),
                        published_at=datetime.fromisoformat(
                            article.get("publishedDate", "")
                        ),
                        team=article.get("teamAbbreviation"),
                        category=article.get("category", "general"),
                        url=article.get("url", ""),
                    )
                    news_articles.append(news)

            logger.info(
                f"Fetched {len(news_articles)} news articles"
                + (f" for {team_abbr}" if team_abbr else "")
            )
            return news_articles

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching news: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []

    async def get_player_stats(
        self, player_id: str, season: int, week: Optional[int] = None
    ) -> Optional[NFLPlayerStats]:
        """
        Get player statistics.

        Args:
            player_id: NFL player ID
            season: Season year
            week: Week number (None for season totals)

        Returns:
            NFLPlayerStats object or None
        """
        await self.connect()

        # Player stats endpoint
        endpoint = f"{self.base_url}/v3/shield/player/{player_id}/stats"
        params = {"season": season}
        if week:
            params["week"] = week

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            if "data" in data:
                stats_data = data["data"]
                stats = NFLPlayerStats(
                    player_id=player_id,
                    player_name=stats_data.get("playerName", ""),
                    position=stats_data.get("position", ""),
                    team=stats_data.get("teamAbbr", ""),
                    week=week or 0,
                    season=season,
                    # Passing
                    completions=stats_data.get("passingCompletions"),
                    attempts=stats_data.get("passingAttempts"),
                    passing_yards=stats_data.get("passingYards"),
                    passing_tds=stats_data.get("passingTouchdowns"),
                    interceptions=stats_data.get("interceptions"),
                    # Rushing
                    rushing_attempts=stats_data.get("rushingAttempts"),
                    rushing_yards=stats_data.get("rushingYards"),
                    rushing_tds=stats_data.get("rushingTouchdowns"),
                    # Receiving
                    receptions=stats_data.get("receptions"),
                    receiving_yards=stats_data.get("receivingYards"),
                    receiving_tds=stats_data.get("receivingTouchdowns"),
                    targets=stats_data.get("targets"),
                )

                logger.info(
                    f"Fetched stats for {stats.player_name} "
                    f"({season} Week {week or 'Season'})"
                )
                return stats

            return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching player stats: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching player stats: {e}")
            return None

    async def save_schedule(self, games: List[NFLGame], season: int, week: int) -> Path:
        """Save schedule to JSON file"""
        filename = f"schedule_{season}_week_{week}.json"
        filepath = self.output_dir / filename

        data = [game.model_dump(mode="json") for game in games]

        with open(filepath, "w", encoding="utf-8") as f:
            import json

            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved schedule to {filepath}")
        return filepath

    async def save_news(self, articles: List[NFLNews], team: Optional[str] = None):
        """Save news articles to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        team_suffix = f"_{team}" if team else ""
        filename = f"news{team_suffix}_{timestamp}.json"
        filepath = self.output_dir / filename

        data = [article.model_dump(mode="json") for article in articles]

        with open(filepath, "w", encoding="utf-8") as f:
            import json

            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {len(articles)} news articles to {filepath}")
        return filepath


# Convenience functions for quick access
async def get_nfl_schedule(season: int, week: int) -> List[NFLGame]:
    """Quick access to NFL schedule"""
    client = NFLComClient()
    try:
        games = await client.get_schedule(season, week)
        return games
    finally:
        await client.close()


async def get_nfl_news(team: Optional[str] = None, limit: int = 20) -> List[NFLNews]:
    """Quick access to NFL news"""
    client = NFLComClient()
    try:
        news = await client.get_team_news(team, limit)
        return news
    finally:
        await client.close()
