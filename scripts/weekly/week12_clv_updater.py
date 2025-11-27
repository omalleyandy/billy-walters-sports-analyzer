#!/usr/bin/env python3
"""
Week 12 CLV Updater
Update closing lines and results for tracked bets
"""

import sys
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from src.walters_analyzer.models.clv_tracking_module import CLVOutcome, CLVAnalyzer
from src.walters_analyzer.utils.clv_storage import CLVStorage


def update_closing_lines():
    """Update closing lines for all Week 12 bets"""
    storage = CLVStorage(Path("data") / "clv")

    print("\n" + "=" * 70)
    print("UPDATE CLOSING LINES - WEEK 12")
    print("=" * 70 + "\n")

    # Get all pending bets
    bets = sorted(storage.list_all(), key=lambda b: b.created_at)
    pending = [b for b in bets if b.closing_line is None]

    if not pending:
        print("[INFO] No bets pending closing line update")
        return

    print(f"Found {len(pending)} bets to update:\n")

    # Closing lines (UPDATE THESE WITH ACTUAL CLOSING LINES BEFORE RUNNING!)
    closing_lines = {
        "WEEK12_IND_KC": 3.0,  # ← UPDATE: Actual closing line for IND @ KC
        "WEEK12_LAR_TB": -6.5,  # ← UPDATE: Actual closing line for LAR @ TB
        "WEEK12_CIN_NE": 6.5,  # ← UPDATE: Actual closing line for CIN vs NE
        "WEEK12_SEA_TEN": -13.0,  # ← UPDATE: Actual closing line for SEA @ TEN
    }

    for i, bet in enumerate(pending, 1):
        rec_id = bet.recommendation_id

        if rec_id not in closing_lines:
            print(f"[{i}] SKIP: {rec_id} - No closing line provided")
            continue

        closing = closing_lines[rec_id]

        # Calculate CLV using analyzer
        clv_points, clv_outcome = CLVAnalyzer.calculate_clv(bet.opening_line, closing)

        # Update bet
        bet.closing_line = closing
        bet.clv_points = clv_points
        bet.clv_outcome = clv_outcome
        bet.beat_closing_line = clv_points > 0
        bet.closing_date = datetime.now()
        bet.updated_at = datetime.now()

        storage.save(bet)

        # Display
        print(f"[{i}] UPDATED: {bet.game_id}")
        print(f"    Opening Line: {bet.opening_line:+.1f}")
        print(f"    Closing Line: {closing:+.1f}")
        print(f"    CLV:          {clv_points:+.2f} points", end="")
        if bet.beat_closing_line:
            print(" [BEAT CLOSING LINE ✓]")
        else:
            print(" [LOST TO CLOSING LINE]")
        print(f"    Outcome:      {clv_outcome.value.upper()}")
        print()

    print("=" * 70)
    print("CLOSING LINES UPDATED")
    print("=" * 70 + "\n")


def update_results():
    """Update results for completed games"""
    storage = CLVStorage(Path("data") / "clv")

    print("\n" + "=" * 70)
    print("UPDATE RESULTS - WEEK 12")
    print("=" * 70 + "\n")

    # Get bets with closing lines but no results
    bets = sorted(storage.list_all(), key=lambda b: b.created_at)
    pending = [b for b in bets if b.closing_line is not None and b.did_bet_win is None]

    if not pending:
        print("[INFO] No bets pending result update")
        return

    print(f"Found {len(pending)} bets to update:\n")

    # Results (UPDATE THESE WITH ACTUAL OUTCOMES AFTER GAMES!)
    results = {
        "WEEK12_IND_KC": True,  # ← UPDATE: True=won, False=lost, None=push
        "WEEK12_LAR_TB": True,  # ← UPDATE: True=won, False=lost, None=push
        "WEEK12_CIN_NE": False,  # ← UPDATE: True=won, False=lost, None=push
        "WEEK12_SEA_TEN": True,  # ← UPDATE: True=won, False=lost, None=push
    }

    # Final lines (actual game results for reference)
    final_lines = {
        "WEEK12_IND_KC": 0.0,  # ← UPDATE: Final margin (+ = home won by X)
        "WEEK12_LAR_TB": 0.0,  # ← UPDATE: Final margin
        "WEEK12_CIN_NE": 0.0,  # ← UPDATE: Final margin
        "WEEK12_SEA_TEN": 0.0,  # ← UPDATE: Final margin
    }

    for i, bet in enumerate(pending, 1):
        rec_id = bet.recommendation_id

        if rec_id not in results:
            print(f"[{i}] SKIP: {rec_id} - No result provided")
            continue

        did_win = results[rec_id]
        final_line = final_lines.get(rec_id, 0.0)

        # Update bet
        bet.did_bet_win = did_win
        bet.final_line = final_line
        bet.updated_at = datetime.now()

        storage.save(bet)

        # Display
        result_str = "WON" if did_win else "LOST" if did_win is False else "PUSH"
        print(f"[{i}] UPDATED: {bet.game_id}")
        print(f"    Result:       {result_str}")
        print(f"    Final Margin: {final_line:+.1f}")
        print(f"    CLV:          {bet.clv_points:+.2f} points")
        print(f"    Beat Close:   {'YES ✓' if bet.beat_closing_line else 'NO'}")
        print()

    print("=" * 70)
    print("RESULTS UPDATED")
    print("=" * 70 + "\n")


def show_summary():
    """Show comprehensive CLV summary"""
    storage = CLVStorage(Path("data") / "clv")

    print("\n" + "=" * 70)
    print("WEEK 12 CLV SUMMARY")
    print("=" * 70 + "\n")

    # Get all bets
    bets = storage.list_all()

    if not bets:
        print("[INFO] No bets recorded yet")
        print("\nRun: python week12_clv_recorder.py")
        return

    # Calculate summary stats
    total_bets = len(bets)
    with_closing = len([b for b in bets if b.closing_line is not None])
    with_results = len([b for b in bets if b.did_bet_win is not None])
    resolved = len([b for b in bets if b.is_resolved])

    print(f"Total Bets:       {total_bets}")
    print(f"Closing Lines:    {with_closing}/{total_bets}")
    print(f"Results Settled:  {with_results}/{total_bets}")
    print(f"Fully Resolved:   {resolved}/{total_bets}")
    print()

    # CLV analysis
    if with_closing > 0:
        clv_positive = len([b for b in bets if b.beat_closing_line == True])
        clv_avg = (
            sum(b.clv_points for b in bets if b.clv_points is not None) / with_closing
        )

        print("=" * 70)
        print("CLV PERFORMANCE")
        print("=" * 70)
        print(
            f"Beat Closing:     {clv_positive}/{with_closing} ({clv_positive / with_closing * 100:.1f}%)"
        )
        print(f"Average CLV:      {clv_avg:+.2f} points")

        # Billy Walters assessment
        if clv_positive / with_closing >= 0.55:
            assessment = "EXCELLENT - On track for long-term profitability"
        elif clv_positive / with_closing >= 0.50:
            assessment = "GOOD - Positive CLV indicates sharp betting"
        else:
            assessment = "NEEDS IMPROVEMENT - Review bet selection process"

        print(f"Assessment:       {assessment}")
        print()

        # Show each bet
        print("INDIVIDUAL BETS:")
        print("-" * 70)
        for i, bet in enumerate(sorted(bets, key=lambda b: b.created_at), 1):
            clv_str = f"{bet.clv_points:+.2f}" if bet.clv_points is not None else "TBD"
            beat_str = (
                "✓"
                if bet.beat_closing_line
                else "✗"
                if bet.beat_closing_line == False
                else "?"
            )
            result_str = (
                "WON"
                if bet.did_bet_win == True
                else "LOST"
                if bet.did_bet_win == False
                else "PENDING"
            )

            print(f"{i}. {bet.game_id}")
            print(
                f"   Open: {bet.opening_line:+.1f} | Close: {bet.closing_line:+.1f if bet.closing_line else 'TBD':>6} | CLV: {clv_str:>6} {beat_str}"
            )
            print(
                f"   Edge: {bet.edge_percentage:.1f}% | Stake: {bet.stake_fraction * 100:.1f}% (${bet.stake_fraction * bet.bankroll:.0f}) | Result: {result_str}"
            )
            print()

    # Win/Loss if we have results
    if with_results > 0:
        wins = len([b for b in bets if b.did_bet_win == True])
        losses = len([b for b in bets if b.did_bet_win == False])
        pushes = with_results - wins - losses

        # Calculate profit (assuming -110 odds)
        total_staked = sum(
            b.stake_fraction * b.bankroll for b in bets if b.did_bet_win is not None
        )
        total_profit = sum(
            (b.stake_fraction * b.bankroll * 0.91)
            if b.did_bet_win == True
            else (-(b.stake_fraction * b.bankroll))
            if b.did_bet_win == False
            else 0
            for b in bets
            if b.did_bet_win is not None
        )
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        print("=" * 70)
        print("BETTING RESULTS")
        print("=" * 70)
        print(f"Record:           {wins}-{losses}-{pushes}")
        if wins + losses > 0:
            print(f"Win Rate:         {wins / (wins + losses) * 100:.1f}%")
        print(f"Total Staked:     ${total_staked:.2f}")
        print(f"Total Profit:     ${total_profit:+.2f}")
        print(f"ROI:              {roi:+.1f}%")
        print()

        # Billy Walters principle reminder
        print("=" * 70)
        print('Billy Walters: "If you consistently beat the closing line,')
        print("               you're a winning bettor. Results come over time.\"")
        print("=" * 70)

    print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Update Week 12 CLV tracking")
    parser.add_argument(
        "action",
        choices=["update-closing", "update-results", "summary"],
        help="Action to perform",
    )

    args = parser.parse_args()

    if args.action == "update-closing":
        update_closing_lines()
    elif args.action == "update-results":
        update_results()
    elif args.action == "summary":
        show_summary()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Update failed: {e}")
        import traceback

        traceback.print_exc()
