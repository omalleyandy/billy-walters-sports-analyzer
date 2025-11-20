#!/usr/bin/env python3
"""
Simple CLV (Closing Line Value) Tracker
Standalone version - no complex dependencies

Usage:
    python clv_simple.py record --game "IND_KC" --team "IND" --line +3.5 --amount 500 --edge 8.2
    python clv_simple.py update-closing --bet-id 1 --closing-line +2.5
    python clv_simple.py update-result --bet-id 1 --result won
    python clv_simple.py summary
    python clv_simple.py list-pending
"""

import argparse
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class CLVTracker:
    def __init__(self, data_dir: str = "data/clv"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.data_dir / "clv_tracking.csv"
        self.initialize_csv()
    
    def initialize_csv(self):
        """Create CSV file if it doesn't exist"""
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'bet_id', 'game', 'team', 'opening_line', 'bet_line', 
                    'closing_line', 'amount', 'edge_pct', 'placed_time', 
                    'result', 'clv_points', 'clv_percentage', 'notes'
                ])
    
    def record_bet(self, game: str, team: str, line: float, amount: int, 
                   edge_pct: float = 0.0, notes: str = "") -> int:
        """Record a new bet"""
        bet_id = self._get_next_bet_id()
        placed_time = datetime.now().isoformat()
        
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                bet_id, game, team, line, line, '', amount, edge_pct,
                placed_time, 'pending', '', '', notes
            ])
        
        print(f"\n✅ Bet #{bet_id} recorded: {team} {line:+.1f} ${amount}")
        print(f"   Game: {game}")
        print(f"   Edge: {edge_pct:.1f}%")
        print(f"   Time: {placed_time}")
        
        return bet_id
    
    def update_closing_line(self, bet_id: int, closing_line: float):
        """Update the closing line and calculate CLV"""
        bets = self._read_all_bets()
        updated = False
        
        for bet in bets:
            if int(bet['bet_id']) == bet_id:
                bet['closing_line'] = closing_line
                
                bet_line = float(bet['bet_line'])
                clv_points = self._calculate_clv_points(bet_line, closing_line, bet['team'], bet['game'])
                clv_percentage = (abs(clv_points) / abs(closing_line)) * 100 if closing_line != 0 else 0
                
                bet['clv_points'] = f"{clv_points:+.1f}"
                bet['clv_percentage'] = f"{clv_percentage:.1f}"
                
                print(f"\n✅ Bet #{bet_id} closing line updated")
                print(f"   Your line: {bet_line:+.1f}")
                print(f"   Closing: {closing_line:+.1f}")
                print(f"   CLV: {clv_points:+.1f} points ({clv_percentage:.1f}%)")
                
                if clv_points > 0:
                    print(f"   🎯 BEATING CLOSING LINE! Positive CLV!")
                elif clv_points < 0:
                    print(f"   ⚠️ Worse than closing - negative CLV")
                else:
                    print(f"   ➖ Equal to closing")
                
                updated = True
                break
        
        if updated:
            self._write_all_bets(bets)
        else:
            print(f"❌ Bet #{bet_id} not found")
    
    def update_result(self, bet_id: int, result: str):
        """Update bet result"""
        if result not in ['won', 'lost', 'push']:
            print(f"❌ Invalid result. Must be 'won', 'lost', or 'push'")
            return
        
        bets = self._read_all_bets()
        updated = False
        
        for bet in bets:
            if int(bet['bet_id']) == bet_id:
                bet['result'] = result
                
                amount = int(bet['amount'])
                if result == 'won':
                    profit = amount * 0.909  # -110 odds
                    print(f"\n✅ Bet #{bet_id} result: WON 💰")
                    print(f"   Profit: ${profit:.2f}")
                elif result == 'lost':
                    print(f"\n❌ Bet #{bet_id} result: LOST")
                    print(f"   Loss: ${amount}")
                else:
                    print(f"\n➖ Bet #{bet_id} result: PUSH (refunded)")
                
                updated = True
                break
        
        if updated:
            self._write_all_bets(bets)
        else:
            print(f"❌ Bet #{bet_id} not found")
    
    def summary(self):
        """Generate CLV summary report"""
        bets = self._read_all_bets()
        
        if not bets:
            print("\nNo bets recorded yet")
            return
        
        bets_with_clv = [b for b in bets if b['clv_points']]
        pending_bets = [b for b in bets if b['result'] == 'pending']
        completed_bets = [b for b in bets if b['result'] != 'pending']
        
        print("\n" + "="*60)
        print("📊 CLV TRACKING SUMMARY")
        print("="*60)
        
        print(f"\n📋 Total Bets: {len(bets)}")
        print(f"   Pending: {len(pending_bets)}")
        print(f"   Completed: {len(completed_bets)}")
        
        if bets_with_clv:
            clv_values = [float(b['clv_points']) for b in bets_with_clv]
            positive_clv = sum(1 for v in clv_values if v > 0)
            clv_percentage = (positive_clv / len(clv_values)) * 100
            avg_clv = sum(clv_values) / len(clv_values)
            
            print(f"\n🎯 CLV Performance:")
            print(f"   Beating Closing Line: {positive_clv}/{len(clv_values)} ({clv_percentage:.1f}%)")
            print(f"   Average CLV: {avg_clv:+.2f} points")
            
            if clv_percentage > 55:
                print(f"   ✅ EXCELLENT! Above 55% target")
            elif clv_percentage > 50:
                print(f"   ✅ GOOD! Positive CLV trend")
            else:
                print(f"   ⚠️ Below 50% - review line shopping")
        
        if completed_bets:
            wins = sum(1 for b in completed_bets if b['result'] == 'won')
            losses = sum(1 for b in completed_bets if b['result'] == 'lost')
            pushes = sum(1 for b in completed_bets if b['result'] == 'push')
            
            total_wagered = sum(int(b['amount']) for b in completed_bets)
            profit = sum(int(b['amount']) * 0.909 for b in completed_bets if b['result'] == 'won')
            loss = sum(int(b['amount']) for b in completed_bets if b['result'] == 'lost')
            net_profit = profit - loss
            roi = (net_profit / total_wagered * 100) if total_wagered > 0 else 0
            
            print(f"\n💰 Results:")
            print(f"   Record: {wins}-{losses}-{pushes}")
            if wins + losses > 0:
                win_pct = (wins / (wins + losses)) * 100
                print(f"   Win Rate: {win_pct:.1f}%")
            print(f"   Net Profit: ${net_profit:+,.2f}")
            print(f"   ROI: {roi:+.1f}%")
        
        print(f"\n📝 Recent Bets:")
        for bet in bets[-5:]:
            clv_str = bet['clv_points'] if bet['clv_points'] else 'TBD'
            result_emoji = {'won': '✅', 'lost': '❌', 'push': '➖', 'pending': '⏳'}.get(bet['result'], '?')
            print(f"   #{bet['bet_id']} {result_emoji} {bet['team']} {bet['bet_line']} ${bet['amount']} CLV:{clv_str}")
        
        print("="*60 + "\n")
    
    def list_pending(self):
        """List all pending bets"""
        bets = self._read_all_bets()
        pending = [b for b in bets if b['result'] == 'pending']
        
        if not pending:
            print("\nNo pending bets")
            return
        
        print("\n" + "="*60)
        print("⏳ PENDING BETS")
        print("="*60)
        
        for bet in pending:
            print(f"\nBet #{bet['bet_id']}: {bet['game']}")
            print(f"   Team: {bet['team']}")
            print(f"   Line: {bet['bet_line']}")
            print(f"   Amount: ${bet['amount']}")
            if bet['closing_line']:
                print(f"   Closing: {bet['closing_line']}")
                print(f"   CLV: {bet['clv_points']} points")
            else:
                print(f"   Closing: Not yet updated")
            print(f"   Placed: {bet['placed_time']}")
        
        print("="*60 + "\n")
    
    def _calculate_clv_points(self, bet_line: float, closing_line: float, 
                             team: str, game: str) -> float:
        """Calculate CLV in points"""
        away, home = game.split('_')
        
        if team == home:
            clv = bet_line - closing_line
        else:
            clv = closing_line - bet_line
        
        return clv
    
    def _get_next_bet_id(self) -> int:
        """Get next available bet ID"""
        bets = self._read_all_bets()
        if not bets:
            return 1
        return max(int(b['bet_id']) for b in bets) + 1
    
    def _read_all_bets(self) -> List[Dict]:
        """Read all bets from CSV"""
        bets = []
        if self.csv_file.exists():
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                bets = list(reader)
        return bets
    
    def _write_all_bets(self, bets: List[Dict]):
        """Write all bets to CSV"""
        if not bets:
            return
        
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=bets[0].keys())
            writer.writeheader()
            writer.writerows(bets)


def main():
    parser = argparse.ArgumentParser(description='Simple CLV Tracker for Billy Walters System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Record bet
    record = subparsers.add_parser('record', help='Record a new bet')
    record.add_argument('--game', required=True, help='Game format: AWAY_HOME')
    record.add_argument('--team', required=True, help='Team you are betting')
    record.add_argument('--line', required=True, type=float, help='Line you got (e.g., +3.5, -6.5)')
    record.add_argument('--amount', required=True, type=int, help='Bet amount in dollars')
    record.add_argument('--edge', type=float, default=0.0, help='Calculated edge percentage')
    record.add_argument('--notes', default='', help='Additional notes')
    
    # Update closing line
    closing = subparsers.add_parser('update-closing', help='Update closing line')
    closing.add_argument('--bet-id', required=True, type=int, help='Bet ID to update')
    closing.add_argument('--closing-line', required=True, type=float, help='Final closing line')
    
    # Update result
    result = subparsers.add_parser('update-result', help='Update bet result')
    result.add_argument('--bet-id', required=True, type=int, help='Bet ID to update')
    result.add_argument('--result', required=True, choices=['won', 'lost', 'push'], help='Bet result')
    
    # Summary
    subparsers.add_parser('summary', help='Show CLV summary')
    
    # List pending
    subparsers.add_parser('list-pending', help='List pending bets')
    
    args = parser.parse_args()
    
    tracker = CLVTracker()
    
    if args.command == 'record':
        tracker.record_bet(args.game, args.team, args.line, args.amount, args.edge, args.notes)
    elif args.command == 'update-closing':
        tracker.update_closing_line(args.bet_id, args.closing_line)
    elif args.command == 'update-result':
        tracker.update_result(args.bet_id, args.result)
    elif args.command == 'summary':
        tracker.summary()
    elif args.command == 'list-pending':
        tracker.list_pending()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
