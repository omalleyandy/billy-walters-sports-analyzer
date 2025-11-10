"""
Bet Tracking System

Track active bets, monitor games, calculate CLV, and record results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class BetTracker:
    """Track and manage sports betting performance."""

    def __init__(self, data_dir: str = "data/bets"):
        """Initialize bet tracker with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.active_bets_file = self.data_dir / "active_bets.json"
        self.completed_bets_file = self.data_dir / "completed_bets.json"
        self.bet_history_file = self.data_dir / "bet_history.json"

    def load_active_bets(self) -> list[dict[str, Any]]:
        """Load all active bets."""
        if not self.active_bets_file.exists():
            return []

        with open(self.active_bets_file, "r") as f:
            return json.load(f)

    def save_active_bets(self, bets: list[dict[str, Any]]) -> None:
        """Save active bets to file."""
        with open(self.active_bets_file, "w") as f:
            json.dump(bets, f, indent=2)

    def get_bet(self, bet_id: str) -> dict[str, Any] | None:
        """Get specific bet by ID."""
        bets = self.load_active_bets()
        for bet in bets:
            if bet["bet_id"] == bet_id:
                return bet
        return None

    def update_closing_line(
        self, bet_id: str, closing_line: float
    ) -> dict[str, float]:
        """
        Update closing line and calculate CLV.

        Args:
            bet_id: Bet identifier
            closing_line: Actual closing line

        Returns:
            Dictionary with CLV details
        """
        bets = self.load_active_bets()
        bet = None
        bet_index = -1

        for i, b in enumerate(bets):
            if b["bet_id"] == bet_id:
                bet = b
                bet_index = i
                break

        if not bet:
            raise ValueError(f"Bet {bet_id} not found")

        bet_line = bet["bet_details"]["line"]
        clv = bet_line - closing_line

        bet["tracking"]["closing_line"] = closing_line
        bet["tracking"]["closing_line_value"] = clv
        bet["tracking"]["game_started"] = True

        bets[bet_index] = bet
        self.save_active_bets(bets)

        return {
            "bet_line": bet_line,
            "closing_line": closing_line,
            "clv": clv,
            "clv_percentage": (clv / closing_line * 100) if closing_line else 0,
        }

    def update_final_score(
        self, bet_id: str, away_score: int, home_score: int
    ) -> dict[str, Any]:
        """
        Update final score and calculate bet result.

        Args:
            bet_id: Bet identifier
            away_score: Final away team score
            home_score: Final home team score

        Returns:
            Dictionary with bet result details
        """
        bets = self.load_active_bets()
        bet = None
        bet_index = -1

        for i, b in enumerate(bets):
            if b["bet_id"] == bet_id:
                bet = b
                bet_index = i
                break

        if not bet:
            raise ValueError(f"Bet {bet_id} not found")

        # Update score
        bet["tracking"]["final_score"]["away"] = away_score
        bet["tracking"]["final_score"]["home"] = home_score

        # Calculate actual margin (from away team perspective)
        actual_margin = away_score - home_score
        bet["tracking"]["actual_margin"] = actual_margin

        # Determine bet result
        bet_line = bet["bet_details"]["line"]
        bet_side = bet["bet_details"]["side"]
        away_team = bet["game_info"]["away_team"]

        # Check if bet was on away or home team
        betting_away = bet_side == away_team

        if betting_away:
            # Betting away team with + line
            adjusted_margin = actual_margin + bet_line
            cover_margin = adjusted_margin
        else:
            # Betting home team with - line
            adjusted_margin = -actual_margin + bet_line
            cover_margin = adjusted_margin

        bet["tracking"]["cover_margin"] = cover_margin

        # Determine result
        if cover_margin > 0:
            result = "win"
        elif cover_margin < 0:
            result = "loss"
        else:
            result = "push"

        bet["tracking"]["result"] = result

        # Calculate profit/loss
        stake = bet["bet_details"]["stake"]
        odds = bet["bet_details"]["odds"]

        if result == "win":
            # Calculate profit (stake + winnings)
            if odds > 0:
                profit = stake * (odds / 100)
            else:
                profit = stake * (100 / abs(odds))
        elif result == "loss":
            profit = -stake
        else:  # push
            profit = 0.0

        bet["tracking"]["profit_loss"] = profit

        # Update status
        bet["status"] = "completed"

        bets[bet_index] = bet
        self.save_active_bets(bets)

        return {
            "result": result,
            "actual_margin": actual_margin,
            "cover_margin": cover_margin,
            "profit_loss": profit,
            "final_score": f"{away_score}-{home_score}",
        }

    def display_active_bets(self) -> None:
        """Display all active bets in a formatted way."""
        bets = self.load_active_bets()

        if not bets:
            print("No active bets found.")
            return

        print("=" * 80)
        print(f"ACTIVE BETS - {len(bets)} bet(s)")
        print("=" * 80)

        for bet in bets:
            print(f"\n>> BET ID: {bet['bet_id']}")
            print(f"   Status: {bet['status'].upper()}")

            game = bet["game_info"]
            print(f"\n   Game: {game['away_team']} @ {game['home_team']}")
            print(f"   Date: {game['game_date']} at {game['game_time']}")
            print(f"   Venue: {game['stadium']}")

            details = bet["bet_details"]
            print(f"\n   >> BET: {details['side']} {details['line']:+.1f}")
            print(f"   Odds: {details['odds']}")
            print(f"   Stake: {details['stake']} units")
            print(f"   To Win: {details['to_win']:.2f} units")

            analysis = bet["analysis"]
            print(f"\n   >> ANALYSIS:")
            print(f"   Opening Line: {analysis['opening_line']['spread']}")
            print(
                f"   Line Movement: "
                f"{analysis['opening_line']['spread']} -> "
                f"{details['line']:+.1f} "
                f"({analysis['edge']['points']:+.2f} pts edge)"
            )
            print(f"   Expected Value: +{analysis['edge']['expected_value']:.1f}%")
            print(
                f"   True Win Prob: {analysis['true_win_probability']:.1f}% "
                f"(Market: {analysis['market_implied_probability']:.1f}%)"
            )

            if bet["tracking"]["closing_line"] is not None:
                clv = bet["tracking"]["closing_line_value"]
                print(f"\n   >> CLOSING LINE VALUE: {clv:+.1f} points")
                print(
                    f"   Bet Line: {details['line']:+.1f} | "
                    f"Closing Line: {bet['tracking']['closing_line']:+.1f}"
                )

            print(f"\n   >> SHARP INDICATORS:")
            sharp = bet["sharp_indicators"]
            if sharp["reverse_line_movement"]:
                print("   [X] Reverse Line Movement (RLM)")
            if sharp["crossed_key_number"]:
                print(
                    f"   [X] Crossed Key Numbers: "
                    f"{sharp['key_numbers_crossed']}"
                )
            if sharp["steam_move"]:
                print("   [X] Steam Move Detected")
            print(f"   Confidence Score: {sharp['confidence_score']}/10")

            print(f"\n   >> KEY FACTORS:")
            for factor in bet["key_factors"][:3]:
                print(f"   - {factor}")

            if bet["tracking"]["result"]:
                result = bet["tracking"]["result"].upper()
                profit = bet["tracking"]["profit_loss"]
                print(f"\n   >> RESULT: {result}")
                print(
                    f"   Final Score: "
                    f"{bet['tracking']['final_score']['away']}-"
                    f"{bet['tracking']['final_score']['home']}"
                )
                print(f"   Profit/Loss: {profit:+.2f} units")

            print("\n" + "-" * 80)

    def get_performance_summary(self) -> dict[str, Any]:
        """Calculate overall betting performance."""
        bets = self.load_active_bets()

        total_bets = len(bets)
        completed_bets = [b for b in bets if b["status"] == "completed"]
        active_bets = [b for b in bets if b["status"] == "active"]

        wins = len([b for b in completed_bets if b["tracking"]["result"] == "win"])
        losses = len(
            [b for b in completed_bets if b["tracking"]["result"] == "loss"]
        )
        pushes = len(
            [b for b in completed_bets if b["tracking"]["result"] == "push"]
        )

        total_profit = sum(
            b["tracking"]["profit_loss"] or 0 for b in completed_bets
        )
        total_staked = sum(b["bet_details"]["stake"] for b in completed_bets)

        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        # CLV analysis
        bets_with_clv = [
            b
            for b in completed_bets
            if b["tracking"]["closing_line_value"] is not None
        ]
        avg_clv = (
            sum(b["tracking"]["closing_line_value"] for b in bets_with_clv)
            / len(bets_with_clv)
            if bets_with_clv
            else 0
        )

        return {
            "total_bets": total_bets,
            "active": len(active_bets),
            "completed": len(completed_bets),
            "record": {"wins": wins, "losses": losses, "pushes": pushes},
            "win_rate": (wins / len(completed_bets) * 100)
            if completed_bets
            else 0,
            "total_profit_loss": total_profit,
            "total_staked": total_staked,
            "roi": roi,
            "average_clv": avg_clv,
            "clv_sample_size": len(bets_with_clv),
        }

    def display_performance_summary(self) -> None:
        """Display formatted performance summary."""
        stats = self.get_performance_summary()

        print("\n" + "=" * 80)
        print("BETTING PERFORMANCE SUMMARY")
        print("=" * 80)

        print(f"\n>> OVERALL RECORD:")
        print(
            f"   Total Bets: {stats['total_bets']} "
            f"(Active: {stats['active']}, Completed: {stats['completed']})"
        )
        print(
            f"   W-L-P: {stats['record']['wins']}-"
            f"{stats['record']['losses']}-{stats['record']['pushes']}"
        )
        print(f"   Win Rate: {stats['win_rate']:.1f}%")

        print(f"\n>> FINANCIAL:")
        print(f"   Total Staked: {stats['total_staked']:.2f} units")
        print(f"   Total P/L: {stats['total_profit_loss']:+.2f} units")
        print(f"   ROI: {stats['roi']:+.1f}%")

        if stats["clv_sample_size"] > 0:
            print(f"\n>> CLOSING LINE VALUE:")
            print(
                f"   Average CLV: {stats['average_clv']:+.2f} points "
                f"(n={stats['clv_sample_size']})"
            )

        print("\n" + "=" * 80 + "\n")


def main():
    """CLI interface for bet tracker."""
    import argparse

    parser = argparse.ArgumentParser(description="Track sports betting performance")
    parser.add_argument(
        "--list", action="store_true", help="List all active bets"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show performance summary"
    )
    parser.add_argument("--bet-id", help="Specific bet ID to view")
    parser.add_argument(
        "--update-closing-line",
        type=float,
        help="Update closing line for bet",
    )
    parser.add_argument(
        "--update-score", nargs=2, type=int, help="Update final score (away home)"
    )

    args = parser.parse_args()

    tracker = BetTracker()

    if args.list:
        tracker.display_active_bets()
    elif args.summary:
        tracker.display_performance_summary()
    elif args.bet_id:
        if args.update_closing_line is not None:
            result = tracker.update_closing_line(
                args.bet_id, args.update_closing_line
            )
            print(f"\n✅ Updated closing line for {args.bet_id}")
            print(f"   Bet Line: {result['bet_line']:+.1f}")
            print(f"   Closing Line: {result['closing_line']:+.1f}")
            print(f"   CLV: {result['clv']:+.2f} points")
        elif args.update_score:
            away, home = args.update_score
            result = tracker.update_final_score(args.bet_id, away, home)
            print(f"\n✅ Updated final score for {args.bet_id}")
            print(f"   Final Score: {result['final_score']}")
            print(f"   Result: {result['result'].upper()}")
            print(f"   Profit/Loss: {result['profit_loss']:+.2f} units")
        else:
            bet = tracker.get_bet(args.bet_id)
            if bet:
                print(json.dumps(bet, indent=2))
            else:
                print(f"Bet {args.bet_id} not found")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
