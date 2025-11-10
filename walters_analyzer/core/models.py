"""Typed models shared across the core analysis engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Sequence


@dataclass(slots=True)
class Moneyline:
    """Moneyline odds for a matchup (American format)."""

    home: int = -110
    away: int = -110


@dataclass(slots=True)
class SpreadLine:
    """Spread line expressed from the home team's perspective."""

    home_spread: float
    home_price: int = -110
    away_price: int = -110

    @property
    def away_spread(self) -> float:
        return -self.home_spread


@dataclass(slots=True)
class TotalLine:
    """Totals market (Over/Under)."""

    total: float
    over_price: int = -110
    under_price: int = -110


@dataclass(slots=True)
class GameOdds:
    """Complete market snapshot for a single game."""

    spread: SpreadLine
    total: Optional[TotalLine] = None
    moneyline: Optional[Moneyline] = None


@dataclass(slots=True)
class InjuryBreakdown:
    """Normalized injury analysis for one team."""

    team: str
    total_points: float
    critical_players: List[str] = field(default_factory=list)
    detailed_notes: List[str] = field(default_factory=list)
    position_group_crises: List[str] = field(default_factory=list)


@dataclass(slots=True)
class TeamSnapshot:
    """Snapshot of a team's state before running the analyzer."""

    name: str
    injuries: Sequence[Dict[str, Any]] = field(default_factory=list)
    power_rating: Optional[float] = None
    situational_notes: List[str] = field(default_factory=list)


@dataclass(slots=True)
class GameInput:
    """All inputs required to grade a single matchup."""

    home_team: TeamSnapshot
    away_team: TeamSnapshot
    odds: Optional[GameOdds] = None
    kickoff: Optional[datetime] = None
    weather: Optional[str] = None
    sharp_indicator: Optional[float] = None  # e.g. steam/percentage values


@dataclass(slots=True)
class KeyNumberAlert:
    """Highlights whenever the projection crosses (or sits on) key numbers."""

    number: float
    crossed: bool
    description: str


@dataclass(slots=True)
class BetRecommendation:
    """Final recommendation produced by the analyzer."""

    bet_type: Literal["spread", "moneyline", "total"]
    team: Optional[str]
    edge: float
    win_probability: float
    stake_pct: float
    conviction: str
    notes: List[str] = field(default_factory=list)


@dataclass(slots=True)
class GameAnalysis:
    """Complete analysis output for a matchup."""

    matchup: GameInput
    predicted_spread: float
    predicted_total: Optional[float]
    injury_advantage: float
    market_spread: float
    edge: float
    confidence: str
    home_report: InjuryBreakdown
    away_report: InjuryBreakdown
    key_number_alerts: List[KeyNumberAlert]
    recommendation: BetRecommendation
