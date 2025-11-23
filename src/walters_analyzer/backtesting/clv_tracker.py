#!/usr/bin/env python3
"""
Closing Line Value (CLV) Tracker for ESPN Enhancement Impact

Tracks how ESPN team statistics affect CLV - the key success metric
in sports betting. Measures:
- CLV with baseline predictions (without ESPN)
- CLV with enhanced predictions (with ESPN)
- CLV improvement from ESPN metrics
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class BetRecord:
    """Individual bet tracking record"""

    bet_id: str
    league: str
    week: int
    matchup: str
    away_team: str
    home_team: str
    pick: str  # Team picked
    bet_type: str  # "spread", "total", "moneyline"
    opening_line: float
    closing_line: float
    closing_line_source: str  # "opening", "market", "manual"
    bet_size: float  # Units wagered
    odds: float  # Decimal odds
    win: Optional[bool] = None  # None if not settled
    final_score: Optional[str] = None  # "24-21" format
    cash_won: Optional[float] = None
    closing_line_value: Optional[float] = None  # CLV in units
    predicted_with_espn: bool = True
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def calculate_clv(self) -> float:
        """
        Calculate CLV (Closing Line Value) in units

        CLV = (closing_odds - opening_odds) * bet_size

        Returns:
            CLV in units (positive = favorable move, negative = unfavorable)
        """
        if not self.win:
            return 0.0

        # Convert closing line to decimal odds
        closing_odds = self._line_to_decimal(self.closing_line)
        opening_odds = self._line_to_decimal(self.odds)

        clv = (closing_odds - opening_odds) * self.bet_size
        return clv

    @staticmethod
    def _line_to_decimal(line: float) -> float:
        """Convert American odds/line to decimal odds"""
        if line == 0:
            return 0
        if line > 0:
            return 1 + (line / 100)
        return 1 + (100 / abs(line))

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class CLVSummary:
    """Summary statistics for CLV analysis"""

    league: str
    period: str  # "week", "season", etc.
    total_bets: int
    settled_bets: int
    winning_bets: int
    win_rate: float
    total_wagered: float
    total_won: float
    net_profit: float
    roi: float
    avg_odds: float
    avg_clv: float
    positive_clv_bets: int
    avg_positive_clv: float
    avg_negative_clv: float
    clv_with_espn: float
    clv_without_espn: Optional[float] = None
    espn_improvement: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


class CLVTracker:
    """Track and analyze CLV for ESPN impact measurement"""

    def __init__(self, data_dir: str = "data/bets"):
        """Initialize CLV tracker"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.bets: Dict[str, BetRecord] = {}
        self.load_bets()

    def load_bets(self) -> int:
        """Load existing bet records"""
        bets_file = self.data_dir / "active_bets.json"

        if not bets_file.exists():
            logger.info("No existing bets file found")
            return 0

        try:
            with open(bets_file, "r") as f:
                data = json.load(f)

            if isinstance(data, dict) and "bets" in data:
                bets_list = data["bets"]
            else:
                bets_list = data

            for bet_data in bets_list:
                if isinstance(bet_data, dict):
                    bet = BetRecord(**bet_data)
                    self.bets[bet.bet_id] = bet

            logger.info(f"Loaded {len(self.bets)} bet records")
            return len(self.bets)

        except Exception as e:
            logger.error(f"Error loading bets: {e}")
            return 0

    def add_bet(
        self,
        league: str,
        week: int,
        matchup: str,
        away_team: str,
        home_team: str,
        pick: str,
        bet_type: str,
        opening_line: float,
        bet_size: float,
        odds: float,
        predicted_with_espn: bool = True,
        notes: str = "",
    ) -> str:
        """Add a new bet record"""

        bet_id = f"{league.upper()}{week:02d}_{away_team}_{home_team}"

        if bet_id in self.bets:
            logger.warning(f"Bet {bet_id} already exists, skipping")
            return bet_id

        bet = BetRecord(
            bet_id=bet_id,
            league=league.lower(),
            week=week,
            matchup=matchup,
            away_team=away_team,
            home_team=home_team,
            pick=pick,
            bet_type=bet_type,
            opening_line=opening_line,
            closing_line=opening_line,  # Start with opening
            closing_line_source="opening",
            bet_size=bet_size,
            odds=odds,
            predicted_with_espn=predicted_with_espn,
            notes=notes,
        )

        self.bets[bet_id] = bet
        logger.info(f"Added bet: {bet_id}")
        return bet_id

    def update_closing_line(
        self, bet_id: str, closing_line: float, source: str = "manual"
    ) -> bool:
        """Update closing line for a bet"""

        if bet_id not in self.bets:
            logger.error(f"Bet {bet_id} not found")
            return False

        self.bets[bet_id].closing_line = closing_line
        self.bets[bet_id].closing_line_source = source
        logger.info(f"Updated closing line for {bet_id}: {closing_line}")
        return True

    def settle_bet(
        self,
        bet_id: str,
        won: bool,
        final_score: Optional[str] = None,
        cash_won: Optional[float] = None,
    ) -> bool:
        """Mark a bet as settled"""

        if bet_id not in self.bets:
            logger.error(f"Bet {bet_id} not found")
            return False

        bet = self.bets[bet_id]
        bet.win = won
        bet.final_score = final_score
        bet.cash_won = cash_won

        # Calculate CLV if we have both opening and closing lines
        bet.closing_line_value = bet.calculate_clv()

        logger.info(f"Settled {bet_id}: Win={won}, CLV={bet.closing_line_value:.2f}")
        return True

    def save_bets(self) -> Path:
        """Save bet records to file"""

        bets_file = self.data_dir / "active_bets.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "bets": [bet.to_dict() for bet in self.bets.values()],
        }

        with open(bets_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(self.bets)} bets to {bets_file}")
        return bets_file

    def get_clv_summary(self, league: Optional[str] = None) -> CLVSummary:
        """Calculate CLV summary statistics"""

        # Filter bets
        bets_to_analyze = list(self.bets.values())
        if league:
            bets_to_analyze = [b for b in bets_to_analyze if b.league == league.lower()]

        if not bets_to_analyze:
            logger.warning("No bets to analyze")
            return None

        # Calculate statistics
        settled = [b for b in bets_to_analyze if b.win is not None]
        winners = [b for b in settled if b.win]

        total_wagered = sum(b.bet_size for b in bets_to_analyze)
        total_won = sum(b.cash_won or 0 for b in settled)
        net_profit = total_won - total_wagered
        win_rate = len(winners) / len(settled) if settled else 0
        roi = (net_profit / total_wagered) if total_wagered > 0 else 0

        # CLV analysis
        clv_values = [
            b.closing_line_value for b in settled if b.closing_line_value is not None
        ]
        avg_clv = sum(clv_values) / len(clv_values) if clv_values else 0
        positive_clv = [c for c in clv_values if c > 0]
        negative_clv = [c for c in clv_values if c < 0]

        clv_with_espn = sum(
            b.closing_line_value
            for b in settled
            if b.closing_line_value and b.predicted_with_espn
        )

        avg_positive_clv = sum(positive_clv) / len(positive_clv) if positive_clv else 0
        avg_negative_clv = sum(negative_clv) / len(negative_clv) if negative_clv else 0

        summary = CLVSummary(
            league=league.upper() if league else "ALL",
            period="custom",
            total_bets=len(bets_to_analyze),
            settled_bets=len(settled),
            winning_bets=len(winners),
            win_rate=win_rate,
            total_wagered=total_wagered,
            total_won=total_won,
            net_profit=net_profit,
            roi=roi,
            avg_odds=1.95,  # Placeholder
            avg_clv=avg_clv,
            positive_clv_bets=len(positive_clv),
            avg_positive_clv=avg_positive_clv,
            avg_negative_clv=avg_negative_clv,
            clv_with_espn=clv_with_espn,
        )

        return summary

    def print_summary(self, summary: Optional[CLVSummary]) -> None:
        """Print CLV summary to console"""

        if not summary:
            logger.warning("No summary to print")
            return

        print("\n" + "=" * 70)
        print(f"CLV ANALYSIS REPORT - {summary.league}")
        print("=" * 70)
        print(f"Total Bets:                {summary.total_bets}")
        print(f"Settled Bets:              {summary.settled_bets}")
        print(
            f"Winning Bets:              {summary.winning_bets} "
            f"({summary.win_rate:.1%})"
        )
        print(f"Total Wagered:             ${summary.total_wagered:.2f}")
        print(f"Total Won:                 ${summary.total_won:.2f}")
        print(f"Net Profit:                ${summary.net_profit:+.2f}")
        print(f"ROI:                       {summary.roi:+.1%}")
        print(f"Average CLV (per bet):     {summary.avg_clv:+.2f} units")
        print(f"Bets with Positive CLV:    {summary.positive_clv_bets}")
        print(f"Avg Positive CLV:          {summary.avg_positive_clv:+.2f} units")
        print(f"Avg Negative CLV:          {summary.avg_negative_clv:+.2f} units")
        print(f"CLV with ESPN:             {summary.clv_with_espn:+.2f} units")

        if summary.espn_improvement is not None:
            arrow = "↑" if summary.espn_improvement > 0 else "↓"
            print(f"ESPN Improvement:          {summary.espn_improvement:+.2f} {arrow}")

        print("=" * 70 + "\n")


def main():
    """CLI interface for CLV tracking"""

    import argparse

    parser = argparse.ArgumentParser(description="Track CLV for ESPN impact")
    subparsers = parser.add_subparsers(dest="command")

    # Add bet command
    add_parser = subparsers.add_parser("add", help="Add new bet")
    add_parser.add_argument("--league", required=True, choices=["nfl", "ncaaf"])
    add_parser.add_argument("--week", type=int, required=True)
    add_parser.add_argument("--matchup", required=True)
    add_parser.add_argument("--away-team", required=True)
    add_parser.add_argument("--home-team", required=True)
    add_parser.add_argument("--pick", required=True)
    add_parser.add_argument("--type", dest="bet_type", default="spread")
    add_parser.add_argument("--opening-line", type=float, required=True)
    add_parser.add_argument("--size", type=float, default=1.0)
    add_parser.add_argument("--odds", type=float, default=-110)

    # Settle bet command
    settle_parser = subparsers.add_parser("settle", help="Settle a bet")
    settle_parser.add_argument("--bet-id", required=True)
    settle_parser.add_argument("--won", action="store_true")
    settle_parser.add_argument("--score", dest="final_score")
    settle_parser.add_argument("--cash", type=float, dest="cash_won")

    # Update line command
    line_parser = subparsers.add_parser("update-line", help="Update closing line")
    line_parser.add_argument("--bet-id", required=True)
    line_parser.add_argument("--closing-line", type=float, required=True)

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show CLV summary")
    summary_parser.add_argument("--league", choices=["nfl", "ncaaf"])

    # List command
    list_parser = subparsers.add_parser("list", help="List all bets")
    list_parser.add_argument("--league", choices=["nfl", "ncaaf"])

    args = parser.parse_args()

    tracker = CLVTracker()

    if args.command == "add":
        tracker.add_bet(
            league=args.league,
            week=args.week,
            matchup=args.matchup,
            away_team=args.away_team,
            home_team=args.home_team,
            pick=args.pick,
            bet_type=args.bet_type,
            opening_line=args.opening_line,
            bet_size=args.size,
            odds=args.odds,
        )
        tracker.save_bets()

    elif args.command == "settle":
        tracker.settle_bet(
            bet_id=args.bet_id,
            won=args.won,
            final_score=args.final_score,
            cash_won=args.cash_won,
        )
        tracker.save_bets()

    elif args.command == "update-line":
        tracker.update_closing_line(bet_id=args.bet_id, closing_line=args.closing_line)
        tracker.save_bets()

    elif args.command == "summary":
        summary = tracker.get_clv_summary(league=args.league)
        tracker.print_summary(summary)

    elif args.command == "list":
        bets = tracker.bets.values()
        if args.league:
            bets = [b for b in bets if b.league == args.league.lower()]

        print(f"\nTotal: {len(bets)} bets\n")
        for bet in sorted(bets, key=lambda b: b.timestamp):
            status = "SETTLED" if bet.win is not None else "OPEN"
            result = f"{'WIN' if bet.win else 'LOSS'}" if bet.win is not None else "?"
            print(
                f"{bet.bet_id:30} {status:8} {result:5} "
                f"CLV: {bet.closing_line_value or 0:+.1f}"
            )


if __name__ == "__main__":
    main()
