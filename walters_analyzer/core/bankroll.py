"""Professional bankroll management helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .calculator import kelly_fraction


@dataclass(slots=True)
class BetRecord:
    """Stores the outcome of a recommendation for performance tracking."""

    wager_pct: float
    odds: int
    win_probability: float
    result: Optional[float] = None  # +1 for win, -1 for loss, 0 for push


class BankrollManager:
    """Applies (fractional) Kelly sizing with practical risk controls."""

    def __init__(
        self,
        initial_bankroll: float = 10000.0,
        max_risk_pct: float = 3.0,
        min_bet_pct: float = 0.5,
        fractional_kelly: float = 0.5,
    ) -> None:
        self.bankroll = initial_bankroll
        self.initial_bankroll = initial_bankroll
        self.max_risk_pct = max_risk_pct
        self.min_bet_pct = min_bet_pct
        self.fractional_kelly = fractional_kelly
        self.history: List[BetRecord] = []

    def recommend_pct(self, win_probability: float, odds: int) -> float:
        """Return the recommended percentage of bankroll to risk."""
        kelly = kelly_fraction(win_probability, odds, self.fractional_kelly)
        if kelly <= 0.0:
            return 0.0

        stake_pct = min(kelly * 100.0, self.max_risk_pct)
        stake_pct = max(stake_pct, self.min_bet_pct)
        return round(stake_pct, 2)

    def stake_amount(self, stake_pct: float) -> float:
        """Convert a percentage stake into an actual currency amount."""
        return round(self.bankroll * (stake_pct / 100.0), 2)

    def register_bet(self, stake_pct: float, odds: int, win_probability: float) -> None:
        """Store a bet recommendation so performance can be tracked later."""
        self.history.append(BetRecord(stake_pct, odds, win_probability))

    def record_result(self, bet_index: int, result: float) -> None:
        """
        Apply a result (+1 win, -1 loss, 0 push) to a previously recorded bet.
        Updates bankroll accordingly.
        """
        record = self.history[bet_index]
        stake = self.stake_amount(record.wager_pct)
        if result > 0:
            if record.odds > 0:
                payout = stake * (record.odds / 100.0)
            else:
                payout = stake / (abs(record.odds) / 100.0)
            self.bankroll += payout
        elif result < 0:
            self.bankroll -= stake
        record.result = result
