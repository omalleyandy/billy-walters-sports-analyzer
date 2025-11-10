"""Analyzer-specific configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Tuple

from walters_analyzer.config import get_settings


@dataclass(slots=True)
class AnalyzerConfig:
    """Runtime configuration for the Billy Walters analysis engine."""

    bankroll: float = 10000.0
    max_bet_pct: float = 3.0
    min_bet_pct: float = 0.5
    fractional_kelly: float = 0.5
    key_numbers: Tuple[float, ...] = (3, 7, 6, 10, 14)
    confidence_buckets: Sequence[Tuple[float, str]] = field(
        default_factory=lambda: (
            (3.0, "High Confidence"),
            (2.0, "Elevated Confidence"),
            (1.0, "Standard Play"),
            (0.5, "Lean"),
        )
    )

    @classmethod
    def from_settings(cls) -> "AnalyzerConfig":
        """Build an AnalyzerConfig using the global Settings object."""
        settings = get_settings()
        bankroll = settings.autonomous_agent.initial_bankroll
        max_bet = settings.autonomous_agent.max_bet_percentage
        fractional_kelly = 0.5
        if settings.skills.market_analysis.enabled:
            fractional_kelly = 0.6
        return cls(
            bankroll=bankroll,
            max_bet_pct=max_bet,
            fractional_kelly=fractional_kelly,
        )
