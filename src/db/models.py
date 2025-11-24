"""
Database Models

Pydantic models for type-safe database operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class Game(BaseModel):
    """Game model."""

    game_id: str
    season: int
    week: int
    league: str = Field(..., pattern="^(NFL|NCAAF)$")
    game_date: datetime

    home_team: str
    away_team: str

    home_score: Optional[int] = None
    away_score: Optional[int] = None
    final_margin: Optional[int] = None
    total_points: Optional[int] = None

    status: str = "SCHEDULED"
    stadium: Optional[str] = None
    is_outdoor: Optional[bool] = None
    is_neutral_site: bool = False

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


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
    updated_at: datetime = Field(default_factory=datetime.now)


class Odds(BaseModel):
    """Odds model."""

    game_id: str
    sportsbook: str
    odds_type: str = Field(..., pattern="^(opening|current|closing)$")

    home_spread: Optional[Decimal] = None
    home_spread_juice: int = -110
    away_spread: Optional[Decimal] = None
    away_spread_juice: int = -110

    total: Optional[Decimal] = None
    over_juice: int = -110
    under_juice: int = -110

    home_moneyline: Optional[int] = None
    away_moneyline: Optional[int] = None

    timestamp: datetime
    line_movement: Optional[Decimal] = None

    created_at: datetime = Field(default_factory=datetime.now)


class Bet(BaseModel):
    """Bet model."""

    bet_id: str
    game_id: str

    # Bet details
    bet_type: str = Field(..., pattern="^(spread|total|moneyline)$")
    side: str
    line: Decimal
    juice: int = -110
    sportsbook: Optional[str] = None

    # Edge analysis
    predicted_line: Optional[Decimal] = None
    market_line: Optional[Decimal] = None
    edge_points: Decimal
    edge_category: str = Field(..., pattern="^(MAX|STRONG|MEDIUM|WEAK)$")
    confidence: Optional[int] = Field(None, ge=1, le=100)

    # Position sizing
    kelly_pct: Optional[Decimal] = None
    actual_pct: Optional[Decimal] = None
    units: Decimal
    risk_amount: Optional[Decimal] = None

    # Results
    closing_line: Optional[Decimal] = None
    clv: Optional[Decimal] = None

    result: str = "PENDING"
    profit_loss: Optional[Decimal] = None
    roi: Optional[Decimal] = None

    # Tracking
    placed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None
    key_factors: Optional[List[str]] = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Weather(BaseModel):
    """Weather model."""

    game_id: str

    # Temperature
    temperature: Optional[Decimal] = None
    feels_like: Optional[Decimal] = None

    # Wind
    wind_speed: Optional[Decimal] = None
    wind_gust: Optional[Decimal] = None
    wind_direction: Optional[str] = None

    # Precipitation
    humidity: Optional[int] = None
    precipitation_chance: Optional[int] = None
    precipitation_type: Optional[str] = None
    precipitation_amount: Optional[Decimal] = None

    # Visibility
    visibility: Optional[Decimal] = None
    cloud_cover: Optional[int] = None

    # Billy Walters adjustments
    total_adjustment: Optional[Decimal] = None
    spread_adjustment: Optional[Decimal] = None
    weather_severity_score: Optional[int] = Field(None, ge=0, le=100)
    weather_category: Optional[str] = Field(
        None, pattern="^(IDEAL|GOOD|MODERATE|POOR|SEVERE)$"
    )

    # Source
    source: str
    forecast_type: Optional[str] = None
    forecast_hours_ahead: Optional[int] = None
    is_actual: bool = False

    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.now)


class Injury(BaseModel):
    """Injury model."""

    game_id: str
    team: str

    # Player info
    player_name: str
    position: str
    jersey_number: Optional[int] = None

    # Injury details
    injury_status: str = Field(..., pattern="^(OUT|DOUBTFUL|QUESTIONABLE|PROBABLE|HEALTHY)$")
    injury_type: Optional[str] = None
    injury_side: Optional[str] = None

    # Impact
    impact_points: Optional[Decimal] = None
    player_tier: Optional[str] = Field(
        None, pattern="^(ELITE|STARTER|BACKUP|DEPTH)$"
    )
    is_key_player: bool = False

    # Timeline
    reported_date: Optional[datetime] = None
    game_status: Optional[str] = Field(
        None, pattern="^(ACTIVE|INACTIVE|LIMITED|DNP|FULL)$"
    )
    last_updated: Optional[datetime] = None

    # Source
    source: str

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SituationalFactors(BaseModel):
    """Situational factors model (SWEF)."""

    game_id: str
    team: str

    # Situation
    days_rest: Optional[int] = None
    is_short_rest: bool = False
    is_extra_rest: bool = False

    travel_distance: Optional[int] = None
    time_zone_change: Optional[int] = None
    is_long_travel: bool = False

    # Emotion
    is_division_game: bool = False
    is_rivalry: bool = False
    is_playoff_implications: bool = False
    is_revenge_game: bool = False
    is_prime_time: bool = False

    # Fundamentals
    current_streak: Optional[int] = None
    home_record: Optional[str] = None
    away_record: Optional[str] = None
    ats_record: Optional[str] = None
    ats_last_5: Optional[str] = None

    scoring_avg: Optional[Decimal] = None
    scoring_avg_last_3: Optional[Decimal] = None
    points_allowed_avg: Optional[Decimal] = None
    points_allowed_last_3: Optional[Decimal] = None

    turnover_margin: Optional[int] = None
    turnover_margin_last_3: Optional[int] = None

    # Billy Walters adjustments
    situational_adjustment: Optional[Decimal] = None
    situation_score: Optional[int] = Field(None, ge=-10, le=10)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""

    season: int
    week: Optional[int] = None
    league: Optional[str] = Field(None, pattern="^(NFL|NCAAF)$")

    # Betting results
    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    pending: int = 0
    win_pct: Optional[Decimal] = None

    # By category
    max_bets: int = 0
    max_wins: int = 0
    max_roi: Optional[Decimal] = None

    strong_bets: int = 0
    strong_wins: int = 0
    strong_roi: Optional[Decimal] = None

    medium_bets: int = 0
    medium_wins: int = 0
    medium_roi: Optional[Decimal] = None

    weak_bets: int = 0
    weak_wins: int = 0
    weak_roi: Optional[Decimal] = None

    # By type
    spread_bets: int = 0
    spread_wins: int = 0
    total_bets_count: int = 0
    total_wins: int = 0
    moneyline_bets: int = 0
    moneyline_wins: int = 0

    # Financial
    total_risked: Optional[Decimal] = None
    total_profit: Optional[Decimal] = None
    roi: Optional[Decimal] = None
    roi_per_bet: Optional[Decimal] = None

    # CLV
    avg_clv: Optional[Decimal] = None
    median_clv: Optional[Decimal] = None
    positive_clv_pct: Optional[Decimal] = None
    clv_wins: int = 0
    clv_losses: int = 0

    # Edge analysis
    avg_edge: Optional[Decimal] = None
    median_edge: Optional[Decimal] = None
    edge_realization_pct: Optional[Decimal] = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
