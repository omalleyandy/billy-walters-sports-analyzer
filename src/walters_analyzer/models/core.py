from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Team(BaseModel):
    team_id: str
    name: str
    conference: Optional[str] = None
    division: Optional[str] = None
    power_rating: Optional[float] = None


class Game(BaseModel):
    game_id: str
    season: int
    week: int
    home_team_id: str
    away_team_id: str
    kickoff_datetime: datetime
    stadium: Optional[str] = None
    surface_type: Optional[str] = None
    timezone: Optional[str] = None


class PowerRatingSnapshot(BaseModel):
    snapshot_id: str
    team_id: str
    season: int
    week: int

    old_rating: float
    true_game_performance: float
    new_rating: float

    score_differential: Optional[float] = None
    opponent_power_rating: Optional[float] = None
    injury_differential: Optional[float] = None
    home_field_advantage: Optional[float] = None

    source: Optional[str] = None
    created_at: datetime


class MatchupEvaluation(BaseModel):
    evaluation_id: str
    game_id: str
    model_version: str

    home_team_id: str
    away_team_id: str

    base_power_diff: float  # home - away

    s_factor_points_home: float
    s_factor_points_away: float
    w_factor_points_home: float
    w_factor_points_away: float
    e_factor_points_home: float
    e_factor_points_away: float

    adjusted_power_home: float
    adjusted_power_away: float

    predicted_spread: float   # home - away
    market_spread: float      # home - away
    effective_spread: float   # after vig adjustment

    edge_percentage: float
    star_rating: float
    qualifies_as_play: bool

    notes: Optional[str] = None


class BetRecommendation(BaseModel):
    recommendation_id: str
    game_id: str
    evaluation_id: str

    bet_type: Literal["spread", "moneyline", "total", "none"]
    side: Literal["home", "away", "over", "under", "none"]

    line: Optional[float] = None
    price: Optional[int] = None  # American odds

    edge_percentage: float
    star_rating: float

    stake_fraction: float = Field(ge=0.0, le=0.03)
    bankroll: Optional[float] = None

    is_play: bool
    rationale: str