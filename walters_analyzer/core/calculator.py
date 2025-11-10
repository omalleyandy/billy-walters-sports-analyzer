"""Utility math helpers for betting edges, EV, and odds conversions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


def american_to_decimal(odds: int) -> float:
    """Convert American odds to decimal odds."""
    if odds == 0:
        raise ValueError("American odds cannot be zero")
    if odds > 0:
        return (odds / 100.0) + 1.0
    return (100.0 / abs(odds)) + 1.0


def decimal_to_american(decimal_odds: float) -> int:
    """Convert decimal odds back to American format."""
    if decimal_odds <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.0")
    if decimal_odds >= 2.0:
        return int(round((decimal_odds - 1.0) * 100))
    return int(round(-100 / (decimal_odds - 1.0)))


def implied_probability(odds: int) -> float:
    """Return the implied win probability for given American odds."""
    decimal = american_to_decimal(odds)
    return 1.0 / decimal


def expected_value(win_probability: float, odds: int) -> float:
    """
    Expected value per unit wagered.

    Positive values indicate a profitable bet in the long run.
    """
    payout = american_to_decimal(odds) - 1.0
    loss = 1.0
    return (win_probability * payout) - ((1 - win_probability) * loss)


def kelly_fraction(win_probability: float, odds: int, fraction: float = 1.0) -> float:
    """
    Kelly Criterion fraction (0-1) for the provided edge.

    Args:
        win_probability: Estimated chance of success (0-1)
        odds: American odds for the wager
        fraction: Apply fractional Kelly (e.g., 0.5 for half Kelly)
    """
    b = american_to_decimal(odds) - 1.0
    q = 1 - win_probability
    edge = (b * win_probability - q) / b if b != 0 else 0.0
    kelly = max(0.0, edge)
    return kelly * fraction


def closing_line_value(opening_line: float, closing_line: float) -> float:
    """Simple closing line value measurement (positive = beat the market)."""
    return closing_line - opening_line


@dataclass(slots=True)
class EdgeSummary:
    """Convenience container that bundles key analytics."""

    edge_points: float
    win_probability: float
    implied_probability: float
    expected_value: float
    kelly_fraction: float
    closing_line_value: Optional[float] = None
