"""Key number and situational spread analysis."""

from __future__ import annotations

from typing import Iterable, List, Sequence

from .models import KeyNumberAlert

DEFAULT_KEY_NUMBERS: Sequence[float] = (3, 7, 6, 10, 14)


class PointAnalyzer:
    """Detects when projections cross or sit on key NFL numbers."""

    def __init__(self, key_numbers: Iterable[float] = DEFAULT_KEY_NUMBERS) -> None:
        self.key_numbers = tuple(sorted(key_numbers))

    def evaluate(
        self, projected_spread: float, market_spread: float
    ) -> List[KeyNumberAlert]:
        """
        Return alerts for each key number that sits between projection and market.
        Uses absolute spreads so favorites/underdogs share the same thresholds.
        """
        alerts: List[KeyNumberAlert] = []
        proj_abs = abs(projected_spread)
        market_abs = abs(market_spread)
        lower = min(proj_abs, market_abs)
        upper = max(proj_abs, market_abs)
        movement_toward_favorite = proj_abs > market_abs

        for number in self.key_numbers:
            if lower <= number <= upper:
                direction = (
                    "toward the favorite"
                    if movement_toward_favorite
                    else "toward the underdog"
                )
                alerts.append(
                    KeyNumberAlert(
                        number=number,
                        crossed=True,
                        description=f"Projection crosses {number} (moving {direction})",
                    )
                )
            elif abs(proj_abs - number) <= 0.5:
                alerts.append(
                    KeyNumberAlert(
                        number=number,
                        crossed=False,
                        description=f"Projection sits on key number {number}",
                    )
                )

        return alerts
