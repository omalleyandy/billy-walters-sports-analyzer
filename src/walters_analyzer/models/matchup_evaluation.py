from __future__ import annotations

"""
Public-facing aliases for matchup evaluation models.

This module exists so callers can import:

    from walters_analyzer.models.matchup_evaluation import (
        AdjustmentBreakdown,
        BetRecommendation,
        MatchupEvaluation,
    )

while the actual implementations live in ``core.py``.
"""

from .core import AdjustmentBreakdown, BetRecommendation, MatchupEvaluation

__all__ = [
    "AdjustmentBreakdown",
    "BetRecommendation",
    "MatchupEvaluation",
]
