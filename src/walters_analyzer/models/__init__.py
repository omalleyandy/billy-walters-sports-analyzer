"""
Billy Walters Sports Analyzer - Models Package

Core data models for the betting analysis system.
"""

from .core import (
    AdjustmentBreakdown,
    BetRecommendation,
    BetSide,
    BetType,
    Game,
    MatchupEvaluation,
    PowerRatingSnapshot,
    Team,
)
from .knowledge_graph import (
    BettingKnowledgeGraph,
    create_recommendation_from_evaluation,
)

# Note: AdjustmentBreakdown, BetRecommendation, and MatchupEvaluation
# are already imported from .core above (no need to re-import from matchup_evaluation)
from .clv_tracking_module import (
    CLVAnalyzer,
    CLVOutcome,
    CLVSummary,
    CLVTracking,
)

__all__ = [
    # Core models
    "AdjustmentBreakdown",
    "BetRecommendation",
    "BetSide",
    "BetType",
    "Game",
    "MatchupEvaluation",
    "PowerRatingSnapshot",
    "Team",
    # Knowledge graph
    "BettingKnowledgeGraph",
    "create_recommendation_from_evaluation",
    # CLV tracking
    "CLVAnalyzer",
    "CLVOutcome",
    "CLVSummary",
    "CLVTracking",
]
