"""
Database Models

Pydantic models for SQLite-based sports betting analytics.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class League(BaseModel):
    """League model."""

    id: int
    name: str
    display_name: str


class Team(BaseModel):
    """Team model."""

    id: int
    league_id: int
    name: str
    abbreviation: Optional[str] = None


class Game(BaseModel):
    """Game/matchup model."""

    id: Optional[int] = None
    game_id: str
    league_id: int
    week: int
    away_team_id: int
    home_team_id: int
    game_time: str
    total: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Edge(BaseModel):
    """Detected betting edge model."""

    id: Optional[int] = None
    game_id: str
    league_id: int
    week: int
    away_team: str
    home_team: str
    game_time: str
    predicted_line: float
    market_line: float
    edge: float
    edge_abs: float
    classification: str
    kelly_pct: Optional[float] = None
    win_rate: Optional[str] = None
    recommendation: Optional[str] = None
    rotation_team1: Optional[int] = None
    rotation_team2: Optional[int] = None
    total: Optional[float] = None
    generated_at: Optional[str] = None
    detected_at: Optional[str] = None


class CLVPlay(BaseModel):
    """CLV tracking play model."""

    id: Optional[int] = None
    game_id: str
    league_id: int
    week: int
    rank: Optional[int] = None
    matchup: str
    game_time: str
    pick: str
    pick_side: str
    spread: float
    total: Optional[float] = None
    market_spread: Optional[float] = None
    edge: Optional[float] = None
    confidence: Optional[str] = None
    kelly: Optional[float] = None
    units_recommended: Optional[float] = None
    away_team: str
    home_team: str
    away_power: Optional[float] = None
    home_power: Optional[float] = None
    opening_odds: Optional[float] = None
    opening_line: Optional[float] = None
    opening_datetime: Optional[str] = None
    closing_odds: Optional[float] = None
    closing_line: Optional[float] = None
    closing_datetime: Optional[str] = None
    result: Optional[str] = None
    clv: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class EdgeSession(BaseModel):
    """Edge detection session metadata."""

    id: Optional[int] = None
    league_id: int
    week: int
    edges_found: Optional[int] = None
    min_edge: Optional[float] = None
    hfa: Optional[float] = None
    generated_at: Optional[str] = None
    created_at: Optional[str] = None


class CLVSession(BaseModel):
    """CLV tracking session metadata."""

    id: Optional[int] = None
    league_id: int
    week: int
    total_max_bet: Optional[int] = None
    total_units_recommended: Optional[float] = None
    status: Optional[str] = None
    generated_at: Optional[str] = None
    created_at: Optional[str] = None


# Legacy models (kept for compatibility)
class PowerRating(BaseModel):
    """Power rating model."""

    season: int
    week: int
    league: str = Field(..., pattern="^(NFL|NCAAF)$")
    team: str
    rating: Decimal
    offense_rating: Optional[Decimal] = None
    defense_rating: Optional[Decimal] = None
    special_teams_rating: Optional[Decimal] = None
    sos_adjustment: Optional[Decimal] = None
    recent_form_adjustment: Optional[Decimal] = None
    injury_adjustment: Optional[Decimal] = None
    source: str
    raw_rating: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Odds(BaseModel):
    """Odds model."""

    season: int
    week: int
    league: str = Field(..., pattern="^(NFL|NCAAF)$")
    game_id: str
    home_team: str
    away_team: str
    spread: Decimal
    spread_odds: Optional[Decimal] = None
    total: Decimal
    total_odds: Optional[Decimal] = None
    moneyline_home: Optional[Decimal] = None
    moneyline_away: Optional[Decimal] = None
    source: str
    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.now)


class Bet(BaseModel):
    """Bet model."""

    bet_id: str
    league: str = Field(..., pattern="^(NFL|NCAAF)$")
    week: int
    game_id: str
    team: str
    bet_type: str
    amount: Decimal
    opening_odds: Decimal
    closing_odds: Decimal
    result: Optional[str] = None
    payout: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Weather(BaseModel):
    """Weather model."""

    league: str = Field(..., pattern="^(NFL|NCAAF)$")
    week: int
    game_id: str
    stadium: str
    game_time: datetime
    temperature: float
    wind_speed: float
    wind_direction: Optional[str] = None
    precipitation: Optional[float] = None
    conditions: str
    created_at: datetime = Field(default_factory=datetime.now)


class Injury(BaseModel):
    """Injury model."""

    league: str = Field(..., pattern="^(NFL|NCAAF)$")
    week: int
    team: str
    player_name: str
    position: str
    status: str
    expected_return: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class SituationalFactors(BaseModel):
    """Situational factors model."""

    league: str = Field(..., pattern="^(NFL|NCAAF)$")
    week: int
    game_id: str
    back_to_back: bool
    rest_advantage: Optional[str] = None
    travel_distance: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""

    league: str = Field(..., pattern="^(NFL|NCAAF)$")
    week: int
    team: str
    offensive_yards: Optional[float] = None
    defensive_yards: Optional[float] = None
    turnover_margin: Optional[float] = None
    third_down_conversion: Optional[float] = None
    red_zone_efficiency: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
