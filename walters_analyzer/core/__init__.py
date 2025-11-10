"""
Core analysis engine for the Billy Walters Sports Analyzer.

These modules translate the valuation layer (player values, injuries, market
analysis) into actionable betting recommendations with bankroll management.
"""

from .models import (
    GameInput,
    GameAnalysis,
    GameOdds,
    SpreadLine,
    TotalLine,
    Moneyline,
    TeamSnapshot,
    InjuryBreakdown,
    KeyNumberAlert,
    BetRecommendation,
)
from .config import AnalyzerConfig
from .calculator import (
    american_to_decimal,
    implied_probability,
    expected_value,
    kelly_fraction,
    closing_line_value,
)
from .bankroll import BankrollManager
from .point_analyzer import PointAnalyzer
from .analyzer import BillyWaltersAnalyzer

__all__ = [
    "AnalyzerConfig",
    "BankrollManager",
    "BetRecommendation",
    "BillyWaltersAnalyzer",
    "GameAnalysis",
    "GameInput",
    "GameOdds",
    "InjuryBreakdown",
    "KeyNumberAlert",
    "Moneyline",
    "PointAnalyzer",
    "SpreadLine",
    "TeamSnapshot",
    "TotalLine",
    "american_to_decimal",
    "implied_probability",
    "expected_value",
    "kelly_fraction",
    "closing_line_value",
]
