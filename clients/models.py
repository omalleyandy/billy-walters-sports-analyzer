"""Data models for sports betting system"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class League(Enum):
    NFL = "NFL"
    NCAAF = "NCAAF"
    NBA = "NBA"
    NCAAB = "NCAAB"

@dataclass
class Team:
    name: str
    abbreviation: str
    league: League
    rotation_number: Optional[int] = None

@dataclass
class OddsMovement:
    spread: float
    spread_odds: int
    over_under: float
    total_odds: int
    timestamp: datetime
    moneyline_home: Optional[int] = None
    moneyline_away: Optional[int] = None

@dataclass
class Game:
    game_id: str
    league: League
    away_team: Team
    home_team: Team
    game_date: datetime
    week: int
    odds: OddsMovement
