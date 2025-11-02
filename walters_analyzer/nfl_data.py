"""
NFL Data Models and Utilities

Provides data structures and conversion utilities for NFL game data,
including team name standardization and GameResult conversion for power ratings.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from .power_ratings import GameResult


# NFL Team Name Mappings
# Maps ESPN abbreviations to full team names (standardized format)
NFL_TEAMS = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams",
    "LV": "Las Vegas Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}

# Reverse mapping: Full name to abbreviation
NFL_TEAMS_REVERSE = {v: k for k, v in NFL_TEAMS.items()}


# NFL Divisions (for situational factor detection)
NFL_DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LAC", "LV"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "LAR", "SF", "SEA"],
}


# Dome stadiums (for weather factor detection)
NFL_DOME_STADIUMS = {
    "Allegiant Stadium",  # Las Vegas Raiders
    "AT&T Stadium",  # Dallas Cowboys
    "Caesars Superdome",  # New Orleans Saints
    "Ford Field",  # Detroit Lions
    "Lucas Oil Stadium",  # Indianapolis Colts
    "Mercedes-Benz Stadium",  # Atlanta Falcons
    "NRG Stadium",  # Houston Texans
    "SoFi Stadium",  # LA Rams/Chargers
    "State Farm Stadium",  # Arizona Cardinals
    "U.S. Bank Stadium",  # Minnesota Vikings
}


@dataclass
class NFLGame:
    """
    Structured representation of an NFL game.
    Converted from ESPN API or other sources.
    """
    # Game identification
    game_id: str
    season: int
    week: int
    game_date: str  # ISO format

    # Teams
    home_team: str
    away_team: str
    home_abbr: str
    away_abbr: str

    # Scores
    home_score: int
    away_score: int

    # Status
    is_completed: bool
    status: str

    # Venue
    venue_name: str
    is_dome: bool

    # Optional betting data
    odds_spread: Optional[str] = None
    odds_total: Optional[float] = None

    # Metadata
    source: str = "espn"

    @property
    def home_won(self) -> bool:
        """Did home team win?"""
        return self.home_score > self.away_score

    @property
    def away_won(self) -> bool:
        """Did away team win?"""
        return self.away_score > self.home_score

    @property
    def is_divisional(self) -> bool:
        """Is this a divisional game?"""
        return are_divisional_opponents(self.home_abbr, self.away_abbr)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "game_id": self.game_id,
            "season": self.season,
            "week": self.week,
            "game_date": self.game_date,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_abbr": self.home_abbr,
            "away_abbr": self.away_abbr,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "is_completed": self.is_completed,
            "status": self.status,
            "venue_name": self.venue_name,
            "is_dome": self.is_dome,
            "odds_spread": self.odds_spread,
            "odds_total": self.odds_total,
            "source": self.source,
        }


def normalize_team_name(team_name: str) -> str:
    """
    Normalize team name to standard format.

    Args:
        team_name: Team name (can be abbreviation or full name)

    Returns:
        Standardized full team name

    Examples:
        >>> normalize_team_name("KC")
        "Kansas City Chiefs"
        >>> normalize_team_name("Kansas City Chiefs")
        "Kansas City Chiefs"
    """
    # Check if it's an abbreviation
    if team_name.upper() in NFL_TEAMS:
        return NFL_TEAMS[team_name.upper()]

    # Check if it's already a full name
    if team_name in NFL_TEAMS_REVERSE:
        return team_name

    # Try to find partial match (case-insensitive)
    team_name_lower = team_name.lower()
    for abbr, full_name in NFL_TEAMS.items():
        if team_name_lower in full_name.lower():
            return full_name

    # Return original if no match found
    return team_name


def get_team_abbreviation(team_name: str) -> str:
    """
    Get team abbreviation from full name or abbreviation.

    Args:
        team_name: Team name (full or abbreviation)

    Returns:
        Team abbreviation (e.g., "KC")
    """
    # Check if already an abbreviation
    if team_name.upper() in NFL_TEAMS:
        return team_name.upper()

    # Look up from full name
    if team_name in NFL_TEAMS_REVERSE:
        return NFL_TEAMS_REVERSE[team_name]

    # Try partial match
    team_name_lower = team_name.lower()
    for abbr, full_name in NFL_TEAMS.items():
        if team_name_lower in full_name.lower():
            return abbr

    # Return original if no match
    return team_name


def are_divisional_opponents(team1: str, team2: str) -> bool:
    """
    Check if two teams are divisional opponents.

    Args:
        team1: First team (abbreviation)
        team2: Second team (abbreviation)

    Returns:
        True if teams are in same division
    """
    team1_abbr = get_team_abbreviation(team1)
    team2_abbr = get_team_abbreviation(team2)

    for division, teams in NFL_DIVISIONS.items():
        if team1_abbr in teams and team2_abbr in teams:
            return True

    return False


def is_dome_stadium(venue_name: str) -> bool:
    """
    Check if a stadium is a dome (indoor).

    Args:
        venue_name: Stadium name

    Returns:
        True if stadium is a dome
    """
    return venue_name in NFL_DOME_STADIUMS


def convert_espn_game_to_nfl_game(espn_game: dict) -> NFLGame:
    """
    Convert ESPN API game data to NFLGame object.

    Args:
        espn_game: Game dictionary from ESPN API

    Returns:
        NFLGame object
    """
    return NFLGame(
        game_id=espn_game["game_id"],
        season=espn_game["season"],
        week=espn_game["week"],
        game_date=espn_game["game_date"],
        home_team=espn_game["home_team"],
        away_team=espn_game["away_team"],
        home_abbr=espn_game["home_abbr"],
        away_abbr=espn_game["away_abbr"],
        home_score=espn_game["home_score"],
        away_score=espn_game["away_score"],
        is_completed=espn_game["is_completed"],
        status=espn_game["status"],
        venue_name=espn_game.get("venue_name", ""),
        is_dome=espn_game.get("is_dome", False),
        odds_spread=espn_game.get("odds_spread"),
        odds_total=espn_game.get("odds_total"),
        source=espn_game.get("source", "espn"),
    )


def nfl_game_to_game_results(
    game: NFLGame,
    injury_differential_home: float = 0.0,
    injury_differential_away: float = 0.0
) -> tuple[GameResult, GameResult]:
    """
    Convert NFLGame to two GameResult objects (one for each team).

    This is used to update power ratings for both teams after a game.

    Args:
        game: NFLGame object
        injury_differential_home: Injury impact for home team (optional)
        injury_differential_away: Injury impact for away team (optional)

    Returns:
        Tuple of (home_game_result, away_game_result)

    Example:
        >>> game = NFLGame(...)
        >>> home_result, away_result = nfl_game_to_game_results(game)
        >>> engine.update_rating(home_result)
        >>> engine.update_rating(away_result)
    """
    # Normalize team names
    home_team = normalize_team_name(game.home_team)
    away_team = normalize_team_name(game.away_team)

    # Home team's perspective
    home_result = GameResult(
        team=home_team,
        opponent=away_team,
        team_score=game.home_score,
        opponent_score=game.away_score,
        is_home=True,
        sport="nfl",
        date=game.game_date,
        injury_differential=injury_differential_home
    )

    # Away team's perspective
    away_result = GameResult(
        team=away_team,
        opponent=home_team,
        team_score=game.away_score,
        opponent_score=game.home_score,
        is_home=False,
        sport="nfl",
        date=game.game_date,
        injury_differential=injury_differential_away
    )

    return home_result, away_result


def load_games_from_jsonl(file_path: str) -> List[NFLGame]:
    """
    Load NFL games from JSONL file.

    Args:
        file_path: Path to JSONL file

    Returns:
        List of NFLGame objects
    """
    import json

    games = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                game_data = json.loads(line)
                game = convert_espn_game_to_nfl_game(game_data)
                games.append(game)

    return games


def filter_completed_games(games: List[NFLGame]) -> List[NFLGame]:
    """
    Filter to only completed games (for power ratings updates).

    Args:
        games: List of NFLGame objects

    Returns:
        List containing only completed games
    """
    return [game for game in games if game.is_completed]


def get_division_name(team_abbr: str) -> Optional[str]:
    """
    Get division name for a team.

    Args:
        team_abbr: Team abbreviation

    Returns:
        Division name (e.g., "AFC West") or None
    """
    for division, teams in NFL_DIVISIONS.items():
        if team_abbr.upper() in teams:
            return division
    return None


# Convenience function for quick lookups
def get_team_info(team_identifier: str) -> dict:
    """
    Get comprehensive team information.

    Args:
        team_identifier: Team name or abbreviation

    Returns:
        Dictionary with team info
    """
    abbr = get_team_abbreviation(team_identifier)
    full_name = normalize_team_name(team_identifier)
    division = get_division_name(abbr)

    return {
        "abbreviation": abbr,
        "full_name": full_name,
        "division": division,
        "conference": division.split()[0] if division else None,  # AFC or NFC
    }
