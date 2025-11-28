#!/usr/bin/env python3
"""
Closing Line Value (CLV) Tracker for Billy Walters Sports Analyzer.

Tracks betting performance using CLV as primary metric (not win percentage).
CLV = (Our Odds - Closing Odds) / 100

Success metric: Average CLV of +2 to +5 points
This measures how well we beat the closing line (expert consensus).
"""

import json
import sys
from datetime import date
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@dataclass
class BetRecord:
    """Single bet tracking record."""

    bet_id: str  # Unique identifier (game_id)
    matchup: str  # Team matchup
    league: str  # NFL or NCAAF
    week: int  # Week number
    game_date: str  # Game date (YYYY-MM-DD)
    bet_type: str  # spread, moneyline, total, etc
    pick: str  # Our pick
    opening_odds: float  # Our odds at time of bet
    opening_line: float  # Opening spread/line
    closing_odds: Optional[float] = None  # Closing odds
    closing_line: Optional[float] = None  # Closing spread/line
    result: Optional[str] = None  # WIN, LOSS, PUSH
    confidence: float = 0.0  # Our confidence (0-100)
    edge: float = 0.0  # Our edge in points
    kelly_fraction: float = 0.0  # Kelly % for unit sizing
    units_bet: float = 0.5  # Units wagered
    clv: Optional[float] = None  # Closing Line Value
    roi: Optional[float] = None  # Return on Investment
    notes: str = ""  # Additional notes

    def calculate_clv(self) -> None:
        """Calculate CLV if closing odds available."""
        if self.closing_odds is not None and self.opening_odds is not None:
            # CLV = (Our Odds - Closing Odds) / 100
            self.clv = (self.opening_odds - self.closing_odds) / 100

    def calculate_roi(self, win: bool) -> None:
        """Calculate ROI based on result."""
        if win:
            self.roi = self.units_bet * 1.1  # Assume standard -110 odds
        else:
            self.roi = -self.units_bet


class CLVTracker:
    """Manage and track CLV for all bets."""

    def __init__(self, data_file: Path = None):
        """Initialize tracker."""
        if data_file is None:
            data_file = Path("output/clv_tracking/clv_tracker.json")
        self.data_file = data_file
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.bets = self._load_bets()

    def _load_bets(self) -> dict:
        """Load existing bets from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                    return {k: BetRecord(**v) for k, v in data.get("bets", {}).items()}
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_bets(self) -> None:
        """Save bets to file."""
        data = {
            "last_updated": date.today().isoformat(),
            "total_bets": len(self.bets),
            "bets": {k: asdict(v) for k, v in self.bets.items()},
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_bet(self, bet: BetRecord) -> None:
        """Add new bet record."""
        bet.calculate_clv()
        self.bets[bet.bet_id] = bet
        self._save_bets()

    def update_closing_line(
        self, bet_id: str, closing_odds: float, closing_line: float
    ) -> None:
        """Update closing odds/line for a bet."""
        if bet_id in self.bets:
            self.bets[bet_id].closing_odds = closing_odds
            self.bets[bet_id].closing_line = closing_line
            self.bets[bet_id].calculate_clv()
            self._save_bets()

    def record_result(self, bet_id: str, result: str, final_score: str = "") -> None:
        """Record game result (WIN, LOSS, PUSH)."""
        if bet_id in self.bets:
            self.bets[bet_id].result = result
            self.bets[bet_id].notes = final_score
            win = result == "WIN"
            self.bets[bet_id].calculate_roi(win)
            self._save_bets()

    def get_stats(self, league: str = None, week: int = None) -> dict:
        """Get statistics for filtered bets."""
        filtered = [
            b
            for b in self.bets.values()
            if (league is None or b.league == league)
            and (week is None or b.week == week)
        ]

        if not filtered:
            return {}

        wins = sum(1 for b in filtered if b.result == "WIN")
        losses = sum(1 for b in filtered if b.result == "LOSS")
        pushes = sum(1 for b in filtered if b.result == "PUSH")
        completed = sum(1 for b in filtered if b.result is not None)

        clv_values = [b.clv for b in filtered if b.clv is not None]
        avg_clv = sum(clv_values) / len(clv_values) if clv_values else 0

        roi_values = [b.roi for b in filtered if b.roi is not None]
        total_roi = sum(roi_values) if roi_values else 0

        return {
            "total_bets": len(filtered),
            "completed": completed,
            "pending": len(filtered) - completed,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_pct": (wins / completed * 100) if completed else 0,
            "avg_clv": avg_clv,
            "avg_clv_target": "2.0-5.0",
            "total_roi": total_roi,
            "total_units": sum(b.units_bet for b in filtered),
            "avg_confidence": (
                sum(b.confidence for b in filtered) / len(filtered) if filtered else 0
            ),
        }

    def print_summary(self, league: str = None, week: int = None) -> None:
        """Print summary statistics."""
        stats = self.get_stats(league, week)

        if not stats:
            print("No bets found for specified criteria")
            return

        filter_str = ""
        if league and week:
            filter_str = f" ({league} Week {week})"
        elif league:
            filter_str = f" ({league})"
        elif week:
            filter_str = f" (Week {week})"

        print(f"\nCLV TRACKING SUMMARY{filter_str}")
        print("=" * 60)
        print(f"Total Bets: {stats['total_bets']}")
        print(f"Completed: {stats['completed']} | Pending: {stats['pending']}")
        print(
            f"Record: {stats['wins']}-{stats['losses']}-{stats['pushes']} "
            f"({stats['win_pct']:.1f}%)"
        )
        print(f"Total Units Wagered: {stats['total_units']:.1f}")
        print(f"Total ROI: {stats['total_roi']:.2f} units")
        print(
            f"\nAverage CLV: {stats['avg_clv']:+.2f} "
            f"(Target: {stats['avg_clv_target']})"
        )
        print(f"Average Confidence: {stats['avg_confidence']:.1f}%")
        print("=" * 60)


def main():
    """Example usage."""
    tracker = CLVTracker()

    # Example: Add a bet
    bet = BetRecord(
        bet_id="indiana_purdue_20251128",
        matchup="Indiana @ Purdue",
        league="NCAAF",
        week=14,
        game_date="2025-11-28",
        bet_type="spread",
        pick="Indiana -28.5",
        opening_odds=-110,
        opening_line=-28.5,
        confidence=95.0,
        edge=66.1,
        kelly_fraction=0.05,
        units_bet=0.5,
    )
    tracker.add_bet(bet)

    # Print summary
    tracker.print_summary()


if __name__ == "__main__":
    main()
