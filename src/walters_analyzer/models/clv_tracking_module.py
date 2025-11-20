from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class CLVOutcome(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    PENDING = "pending"

class CLVTracking(BaseModel):
    recommendation_id: str
    game_id: str
    opening_line: float
    bet_side: str
    bet_type: str
    edge_percentage: float
    bankroll: float
    stake_fraction: float
    opening_date: datetime = Field(default_factory=datetime.utcnow)
    closing_line: Optional[float] = None
    closing_date: Optional[datetime] = None
    clv_points: Optional[float] = None
    clv_outcome: CLVOutcome = CLVOutcome.PENDING
    final_line: Optional[float] = None
    did_bet_win: Optional[bool] = None
    beat_closing_line: Optional[bool] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_resolved(self) -> bool:
        return self.closing_line is not None and self.final_line is not None
    
    @property
    def clv_beats_spread(self) -> Optional[bool]:
        if self.clv_points is None:
            return None
        return self.clv_points > 0.0

class CLVSummary(BaseModel):
    total_bets: int
    bets_resolved: int
    bets_pending: int
    bets_beating_closing: int
    clv_percentage: float
    average_clv_points: float
    wins: int
    losses: int
    win_rate: float
    total_wagered: float
    gross_winnings: float
    gross_losses: float
    net_profit_loss: float
    roi: float
    clv_roi_correlation: str
    assessment: str
    tracked_date: date

class CLVAnalyzer:
    @staticmethod
    def calculate_clv(opening_line: float, closing_line: float):
        clv_points = closing_line - opening_line
        if clv_points > 0.25:
            outcome = CLVOutcome.POSITIVE
        elif clv_points < -0.25:
            outcome = CLVOutcome.NEGATIVE
        else:
            outcome = CLVOutcome.NEUTRAL
        return clv_points, outcome

__all__ = ["CLVOutcome", "CLVTracking", "CLVSummary", "CLVAnalyzer"]
