"""
Action Network Data Loader

Loads and parses Action Network sitemap scraping results for Billy Walters
pipeline integration.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ActionNetworkGame(BaseModel):
    """Action Network game record from sitemap scraping"""

    url: str
    league: str  # "nfl" or "ncaaf"
    content_type: str  # "game" or "category"
    category: Optional[str] = None
    path: str
    path_parts: List[str]
    slug: str
    scraped_at: datetime
    domain: str

    @property
    def game_id(self) -> str:
        """Extract game ID from slug (last path part)"""
        return self.path_parts[-1] if self.path_parts else self.slug

    @property
    def matchup(self) -> Optional[str]:
        """Extract matchup from path (e.g., 'atlanta-falcons-new-orleans-saints')"""
        if len(self.path_parts) >= 2:
            return self.path_parts[1]
        return None

    @property
    def teams(self) -> Optional[tuple[str, str]]:
        """
        Extract away/home teams from matchup string.

        Returns:
            Tuple of (away_team, home_team) or None if can't parse
        """
        if not self.matchup:
            return None

        # Split on common separators
        parts = self.matchup.replace("-at-", "-vs-").split("-vs-")
        if len(parts) == 2:
            away = parts[0].replace("-", " ").title()
            home = parts[1].replace("-", " ").title()
            return (away, home)

        return None


class ActionNetworkCategory(BaseModel):
    """Action Network category record"""

    url: str
    league: str
    content_type: str
    category: str
    path: str
    path_parts: List[str]
    slug: str
    scraped_at: datetime
    domain: str


class ActionNetworkData:
    """
    Action Network data loader and parser.

    Loads JSONL files from Action Network sitemap scraping and provides
    structured access to games and categories.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize loader.

        Args:
            data_dir: Base directory for Action Network data
                     (default: project_root/output/action_network/)
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "output" / "action_network"

        self.data_dir = Path(data_dir)
        self.nfl_dir = self.data_dir / "nfl"
        self.ncaaf_dir = self.data_dir / "ncaaf"

    def load_games(
        self, league: str, timestamp: Optional[str] = None
    ) -> List[ActionNetworkGame]:
        """
        Load game records for a league.

        Args:
            league: "nfl" or "ncaaf"
            timestamp: Optional timestamp suffix (e.g., "20251123_015458")
                      If None, loads most recent file

        Returns:
            List of ActionNetworkGame objects
        """
        league_dir = self.nfl_dir if league == "nfl" else self.ncaaf_dir

        if timestamp:
            games_file = league_dir / f"games_{timestamp}.jsonl"
        else:
            # Find most recent games file
            games_files = sorted(league_dir.glob("games_*.jsonl"), reverse=True)
            if not games_files:
                return []
            games_file = games_files[0]

        if not games_file.exists():
            return []

        games = []
        with open(games_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    games.append(ActionNetworkGame(**data))

        return games

    def load_category(
        self, league: str, category: str, timestamp: Optional[str] = None
    ) -> List[ActionNetworkCategory]:
        """
        Load category records (odds, futures, public-betting, etc.).

        Args:
            league: "nfl" or "ncaaf"
            category: Category name (e.g., "odds", "futures")
            timestamp: Optional timestamp suffix

        Returns:
            List of ActionNetworkCategory objects
        """
        league_dir = self.nfl_dir if league == "nfl" else self.ncaaf_dir

        if timestamp:
            category_file = league_dir / f"{category}_{timestamp}.jsonl"
        else:
            # Find most recent category file
            category_files = sorted(
                league_dir.glob(f"{category}_*.jsonl"), reverse=True
            )
            if not category_files:
                return []
            category_file = category_files[0]

        if not category_file.exists():
            return []

        categories = []
        with open(category_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    categories.append(ActionNetworkCategory(**data))

        return categories

    def get_game_url(self, away_team: str, home_team: str) -> Optional[str]:
        """
        Find Action Network URL for a specific matchup.

        Args:
            away_team: Away team name (e.g., "Atlanta Falcons")
            home_team: Home team name (e.g., "New Orleans Saints")

        Returns:
            URL string or None if not found
        """
        # Try NFL first, then NCAAF
        for league in ["nfl", "ncaaf"]:
            games = self.load_games(league)
            for game in games:
                if game.teams:
                    game_away, game_home = game.teams
                    if (
                        away_team.lower() in game_away.lower()
                        and home_team.lower() in game_home.lower()
                    ):
                        return game.url

        return None

    def get_latest_timestamp(self, league: str) -> Optional[str]:
        """
        Get timestamp of most recent scraping for a league.

        Args:
            league: "nfl" or "ncaaf"

        Returns:
            Timestamp string (e.g., "20251123_015458") or None
        """
        league_dir = self.nfl_dir if league == "nfl" else self.ncaaf_dir
        games_files = sorted(league_dir.glob("games_*.jsonl"), reverse=True)

        if not games_files:
            return None

        # Extract timestamp from filename
        filename = games_files[0].name
        # Format: games_20251123_015458.jsonl
        return filename.replace("games_", "").replace(".jsonl", "")

    def get_summary(self, league: str) -> Dict[str, int]:
        """
        Get summary statistics for scraped data.

        Args:
            league: "nfl" or "ncaaf"

        Returns:
            Dict with counts for each content type
        """
        games = self.load_games(league)

        summary = {"games": len(games), "timestamp": self.get_latest_timestamp(league)}

        # Count categories (try common ones)
        categories = ["futures", "odds", "public-betting"]
        for cat in categories:
            cat_data = self.load_category(league, cat)
            if cat_data:
                summary[cat] = len(cat_data)

        return summary


# Convenience functions for quick access
def load_nfl_games(timestamp: Optional[str] = None) -> List[ActionNetworkGame]:
    """Load NFL games (most recent or specific timestamp)"""
    loader = ActionNetworkData()
    return loader.load_games("nfl", timestamp)


def load_ncaaf_games(timestamp: Optional[str] = None) -> List[ActionNetworkGame]:
    """Load NCAAF games (most recent or specific timestamp)"""
    loader = ActionNetworkData()
    return loader.load_games("ncaaf", timestamp)


def find_game_url(away_team: str, home_team: str) -> Optional[str]:
    """Find Action Network URL for a matchup"""
    loader = ActionNetworkData()
    return loader.get_game_url(away_team, home_team)
