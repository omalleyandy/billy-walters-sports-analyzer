"""
CLV (Closing Line Value) Command Line Interface

Provides production-ready CLI for tracking betting performance against closing lines.
This is the PRIMARY metric for evaluating betting system quality - more important
than win rate in the short term.

Billy Walters Principle:
"If you consistently beat the closing line, you're a winning bettor. 
The results will come over time."

Usage:
    python -m walters_analyzer.cli.clv_cli record-bet --game "IND_KC" --line -3.5 --amount 500
    python -m walters_analyzer.cli.clv_cli update-closing-line --bet-id 12 --closing-line -5.0
    python -m walters_analyzer.cli.clv_cli update-result --bet-id 12 --result won
    python -m walters_analyzer.cli.clv_cli summary
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from walters_analyzer.models.clv_tracking_module import (
    CLVTracking,
    CLVOutcome,
    CLVSummary
)
from walters_analyzer.utils.clv_storage import CLVStorage, CLVReporter


class CLVCli:
    """Command-line interface for CLV tracking"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize CLI with data directory"""
        if data_dir is None:
            data_dir = Path("data") / "clv"
        self.storage = CLVStorage(data_dir)
        
    def _get_bet_by_id(self, bet_id_input: str) -> Optional[CLVTracking]:
        """Helper to find bet by numeric ID or recommendation ID"""
        all_bets = sorted(self.storage.list_all(), key=lambda b: b.created_at)
        
        # Try as numeric ID (1, 2, 3...)
        try:
            numeric_id = int(bet_id_input)
            if 1 <= numeric_id <= len(all_bets):
                return all_bets[numeric_id - 1]  # 1-indexed to 0-indexed
        except (ValueError, IndexError):
            pass
        
        # Try as full recommendation ID
        for bet in all_bets:
            if bet.recommendation_id == bet_id_input:
                return bet
        
        return None
    
    def record_bet(self, args: argparse.Namespace) -> None:
        """
        Record a new bet with opening line.
        
        This should be called IMMEDIATELY when bet is placed.
        Records opening line for later CLV calculation.
        """
        # Parse game_id (format: "AWAY_HOME" or "AWAY@HOME")
        game_id = args.game.replace('@', '_').replace(' ', '_').upper()
        
        # Determine bet side and type
        bet_side = args.side if args.side else ("away" if args.line > 0 else "home")
        bet_type = args.bet_type if args.bet_type else "spread"
        
        # Create CLV tracking record
        tracking = CLVTracking(
            recommendation_id=args.rec_id if args.rec_id else f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            game_id=game_id,
            opening_line=args.line,
            bet_side=bet_side,
            bet_type=bet_type,
            edge_percentage=args.edge if args.edge else 0.0,
            bankroll=args.bankroll if args.bankroll else 20000.0,
            stake_fraction=args.amount / (args.bankroll if args.bankroll else 20000.0),
            opening_date=datetime.now(),
            notes=args.notes if args.notes else None
        )
        
        # Save to storage
        self.storage.save_bet(tracking)
        bet_id = tracking.recommendation_id
        
        # Display confirmation
        print(f"\n[OK] Bet Recorded")
        print(f"Bet ID: {bet_id}")
        print(f"Game: {game_id}")
        print(f"Side: {bet_side} {args.line}")
        print(f"Amount: ${args.amount:.2f}")
        print(f"Type: {bet_type}")
        if args.edge:
            print(f"Edge: {args.edge:.1f}%")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nNext: Update closing line before game starts")
        
    def update_closing_line(self, args: argparse.Namespace) -> None:
        """
        Update bet with closing line.
        
        Should be called RIGHT BEFORE game starts (within 1 hour).
        This is critical for accurate CLV calculation.
        """
        # Load bet using helper
        bet = self._get_bet_by_id(str(args.bet_id))
        if not bet:
            print(f"\n[ERROR] Bet {args.bet_id} not found")
            return
            
        # Calculate CLV
        clv_points = bet.opening_line - args.closing_line
        
        # Determine outcome
        if abs(clv_points) < 0.5:
            clv_outcome = CLVOutcome.NEUTRAL
        elif clv_points > 0:
            clv_outcome = CLVOutcome.POSITIVE
        else:
            clv_outcome = CLVOutcome.NEGATIVE
            
        # Update bet
        bet.closing_line = args.closing_line
        bet.closing_date = datetime.now()
        bet.clv_points = clv_points
        bet.clv_outcome = clv_outcome
        bet.beat_closing_line = (clv_points > 0)
        bet.updated_at = datetime.now()
        
        # Save
        self.storage.save_bet(bet)
        
        # Display results
        print(f"\n[OK] Closing Line Updated")
        print(f"Bet ID: {args.bet_id}")
        print(f"Game: {bet.game_id}")
        print(f"Opening Line: {bet.opening_line}")
        print(f"Closing Line: {args.closing_line}")
        print(f"CLV: {clv_points:+.1f} points")
        
        # Format outcome
        if clv_outcome == CLVOutcome.POSITIVE:
            symbol = "[WIN]"
            msg = "Beat closing line! (Good)"
        elif clv_outcome == CLVOutcome.NEUTRAL:
            symbol = "[PUSH]"
            msg = "Matched closing line (Neutral)"
        else:
            symbol = "[LOSS]"
            msg = "Closing line moved against us (Bad)"
            
        print(f"{symbol} {msg}")
        print(f"\nNext: Update result after game finishes")
        
    def update_result(self, args: argparse.Namespace) -> None:
        """
        Update bet with final result.
        
        Call after game finishes to record win/loss/push.
        """
        # Load bet using helper
        bet = self._get_bet_by_id(str(args.bet_id))
        if not bet:
            print(f"\n[ERROR] Bet {args.bet_id} not found")
            return
            
        # Parse result
        result_map = {
            'won': True,
            'win': True,
            'w': True,
            'lost': False,
            'lose': False,
            'l': False,
            'push': None,
            'tie': None,
            'p': None
        }
        
        result_str = args.result.lower()
        if result_str not in result_map:
            print(f"\n[ERROR] Invalid result: {args.result}")
            print("Valid options: won, lost, push")
            return
            
        did_win = result_map[result_str]
        
        # Update bet
        bet.did_bet_win = did_win
        bet.final_line = args.final_line if args.final_line else bet.closing_line
        bet.updated_at = datetime.now()
        
        if args.notes:
            bet.notes = (bet.notes or "") + f"\n{args.notes}"
            
        # Save
        self.storage.save_bet(bet)
        
        # Display results
        print(f"\n[OK] Bet Result Recorded")
        print(f"Bet ID: {args.bet_id}")
        print(f"Game: {bet.game_id}")
        
        if did_win is True:
            symbol = "[WIN]"
            result_text = "BET WON"
        elif did_win is False:
            symbol = "[LOSS]"
            result_text = "BET LOST"
        else:
            symbol = "[PUSH]"
            result_text = "BET PUSHED"
            
        print(f"{symbol} {result_text}")
        
        # Show CLV context
        if bet.clv_points:
            print(f"\nCLV: {bet.clv_points:+.1f} points")
            if bet.beat_closing_line:
                print("[CLV BEAT] We had better line than close")
            else:
                print("[CLV MISS] Closing line was better")
                
    def show_summary(self, args: argparse.Namespace) -> None:
        """Display CLV summary statistics"""
        
        # Get summary
        if args.week:
            bets = self.storage.list_by_week(args.week, args.season or 2025)
        else:
            bets = self.storage.list_all()
        
        summary = CLVReporter.generate_summary(bets)
        
        if not summary:
            print("\n[INFO] No bets recorded yet")
            return
            
        # Display summary
        print(f"\n{'='*60}")
        print(f"CLV TRACKING SUMMARY")
        if args.week:
            print(f"Week {args.week}, {args.season if args.season else 2025}")
        print(f"{'='*60}")
        
        print(f"\nTotal Bets: {summary.total_bets}")
        print(f"Resolved: {summary.bets_resolved}")
        print(f"Pending: {summary.bets_pending}")
        
        if summary.bets_resolved > 0:
            print(f"\n--- CLV Performance ---")
            print(f"Beating Closing: {summary.bets_beating_closing} / {summary.bets_resolved}")
            print(f"CLV Percentage: {summary.clv_percentage:.1f}%")
            print(f"Average CLV: {summary.average_clv_points:+.2f} points")
            
            # Evaluation
            if summary.clv_percentage >= 55.0:
                rating = "[EXCELLENT]"
                msg = "Sharp betting! You're beating the market."
            elif summary.clv_percentage >= 50.0:
                rating = "[GOOD]"
                msg = "Solid performance, slightly above break-even."
            elif summary.clv_percentage >= 45.0:
                rating = "[ACCEPTABLE]"
                msg = "Near break-even. Need more sample size."
            else:
                rating = "[CONCERNING]"
                msg = "Below break-even. Review bet timing and selection."
                
            print(f"\n{rating} {msg}")
            
            # Sample size guidance
            if summary.total_bets < 50:
                print(f"\n[NOTICE] Only {summary.total_bets} bets. Need 50+ for statistical validity.")
            elif summary.total_bets < 100:
                print(f"\n[NOTICE] {summary.total_bets} bets is good. 100+ needed for strong conclusions.")
            else:
                print(f"\n[OK] {summary.total_bets} bets is statistically significant sample.")
                
        print(f"\n{'='*60}\n")
        
    def list_pending(self, args: argparse.Namespace) -> None:
        """List all bets awaiting closing line or result"""
        
        # Get all bets sorted by creation time (same as _get_bet_by_id)
        all_bets = sorted(self.storage.list_all(), key=lambda b: b.created_at)
        
        bets_dict = {}
        for idx, bet in enumerate(all_bets, start=1):
            bets_dict[idx] = bet
        
        pending_closing = []
        pending_result = []
        
        for bet_id, bet in bets_dict.items():
            if bet.closing_line is None:
                pending_closing.append((bet_id, bet))
            elif bet.did_bet_win is None:
                pending_result.append((bet_id, bet))
                
        if not pending_closing and not pending_result:
            print("\n[OK] No pending updates needed. All bets up to date.")
            return
            
        # Show pending closing lines
        if pending_closing:
            print(f"\n{'='*60}")
            print(f"BETS NEEDING CLOSING LINE ({len(pending_closing)})")
            print(f"{'='*60}\n")
            
            for bet_id, bet in pending_closing:
                print(f"Bet {bet_id}: {bet.game_id}")
                print(f"  Opened: {bet.opening_line} on {bet.opening_date.strftime('%Y-%m-%d')}")
                print(f"  Command: python clv_track.py update-closing-line --bet-id {bet_id} --closing-line X.X")
                print()
                
        # Show pending results
        if pending_result:
            print(f"\n{'='*60}")
            print(f"BETS NEEDING RESULT ({len(pending_result)})")
            print(f"{'='*60}\n")
            
            for bet_id, bet in pending_result:
                print(f"Bet {bet_id}: {bet.game_id}")
                print(f"  CLV: {bet.clv_points:+.1f} points")
                print(f"  Command: python clv_track.py update-result --bet-id {bet_id} --result [won/lost/push]")
                print()


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="CLV (Closing Line Value) Tracking System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # record-bet command
    record_parser = subparsers.add_parser('record-bet', help='Record a new bet')
    record_parser.add_argument('--game', required=True, help='Game ID (e.g., IND_KC or IND@KC)')
    record_parser.add_argument('--line', type=float, required=True, help='Opening line when bet placed')
    record_parser.add_argument('--amount', type=float, required=True, help='Bet amount in dollars')
    record_parser.add_argument('--side', choices=['home', 'away'], help='Which side (auto-detected if not provided)')
    record_parser.add_argument('--bet-type', default='spread', choices=['spread', 'total', 'moneyline'], help='Type of bet')
    record_parser.add_argument('--edge', type=float, help='Calculated edge percentage')
    record_parser.add_argument('--bankroll', type=float, help='Current bankroll (default: 20000)')
    record_parser.add_argument('--rec-id', help='Recommendation ID (auto-generated if not provided)')
    record_parser.add_argument('--notes', help='Optional notes')
    
    # update-closing-line command
    closing_parser = subparsers.add_parser('update-closing-line', help='Update bet with closing line')
    closing_parser.add_argument('--bet-id', type=int, required=True, help='Bet ID to update')
    closing_parser.add_argument('--closing-line', type=float, required=True, help='Closing line right before game')
    
    # update-result command
    result_parser = subparsers.add_parser('update-result', help='Update bet with final result')
    result_parser.add_argument('--bet-id', type=int, required=True, help='Bet ID to update')
    result_parser.add_argument('--result', required=True, choices=['won', 'lost', 'push', 'win', 'lose', 'w', 'l', 'p'], help='Bet outcome')
    result_parser.add_argument('--final-line', type=float, help='Final closing line if different')
    result_parser.add_argument('--notes', help='Optional notes about the game')
    
    # summary command
    summary_parser = subparsers.add_parser('summary', help='Show CLV summary statistics')
    summary_parser.add_argument('--week', type=int, help='Filter by week')
    summary_parser.add_argument('--season', type=int, help='Filter by season')
    
    # list-pending command
    pending_parser = subparsers.add_parser('list-pending', help='List bets needing updates')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # Initialize CLI
    cli = CLVCli()
    
    # Route to appropriate handler
    if args.command == 'record-bet':
        cli.record_bet(args)
    elif args.command == 'update-closing-line':
        cli.update_closing_line(args)
    elif args.command == 'update-result':
        cli.update_result(args)
    elif args.command == 'summary':
        cli.show_summary(args)
    elif args.command == 'list-pending':
        cli.list_pending(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
