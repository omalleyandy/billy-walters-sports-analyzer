#!/usr/bin/env python3
"""
Week 12 Line Movement Monitor
Tracks line movements for Week 12 bets and alerts on significant changes
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "clients"))

from overtime_api_client import OvertimeApiClient
from src.walters_analyzer.utils.clv_storage import CLVStorage


class LineMonitor:
    """Monitor line movements for tracked bets"""
    
    def __init__(self):
        self.clv_storage = CLVStorage(Path("data") / "clv")
        self.overtime = OvertimeApiClient()
        self.history_file = Path("data") / "line_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load historical data
        self.history = self._load_history()
        
        # Week 12 game mappings (your tracked bets)
        self.tracked_games = {
            'IND_KC': {'away': 'Indianapolis Colts', 'home': 'Kansas City Chiefs'},
            'LAR_TB': {'away': 'Los Angeles Rams', 'home': 'Tampa Bay Buccaneers'},
            'CIN_NE': {'away': 'Cincinnati Bengals', 'home': 'New England Patriots'},
            'SEA_TEN': {'away': 'Seattle Seahawks', 'home': 'Tennessee Titans'}
        }
    
    def _load_history(self) -> Dict:
        """Load line movement history"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_history(self):
        """Save line movement history"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _normalize_team_name(self, name: str) -> str:
        """Normalize team names for matching"""
        # Remove common variations
        name = name.replace('Buffalo', '').replace('Bills', '').strip()
        name = name.replace('Kansas City', '').replace('Chiefs', '').strip()
        # Add more normalizations as needed
        return name.lower()
    
    def _match_game(self, api_game: Dict) -> str:
        """Match API game to tracked game"""
        api_away = api_game.get('away_team', '').lower()
        api_home = api_game.get('home_team', '').lower()
        
        for game_id, teams in self.tracked_games.items():
            track_away = teams['away'].lower()
            track_home = teams['home'].lower()
            
            # Check if key parts match
            if (track_away in api_away or api_away in track_away) and \
               (track_home in api_home or api_home in track_home):
                return game_id
        
        return None
    
    async def check_lines(self) -> Dict:
        """Check current lines and detect movements"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking lines...")
        
        # Get current odds
        try:
            odds_data = await self.overtime.scrape_nfl()
            games = odds_data.get('games', [])
        except Exception as e:
            print(f"[ERROR] Failed to fetch odds: {e}")
            return {}
        
        movements = {}
        timestamp = datetime.now().isoformat()
        
        for game in games:
            # Match to tracked game
            game_id = self._match_game(game)
            if not game_id:
                continue
            
            # Get current line
            current_spread = game.get('spread', {}).get('home', None)
            if current_spread is None:
                continue
            
            # Initialize history for this game if needed
            if game_id not in self.history:
                self.history[game_id] = {
                    'snapshots': [],
                    'original_line': current_spread
                }
            
            # Get last known line
            snapshots = self.history[game_id]['snapshots']
            last_line = snapshots[-1]['line'] if snapshots else current_spread
            
            # Calculate movement
            movement = current_spread - last_line
            
            # Record snapshot
            snapshot = {
                'timestamp': timestamp,
                'line': current_spread,
                'movement': movement
            }
            snapshots.append(snapshot)
            
            # Keep only last 100 snapshots
            if len(snapshots) > 100:
                snapshots.pop(0)
            
            # Track significant movement
            if abs(movement) >= 0.5:
                movements[game_id] = {
                    'game': f"{game.get('away_team')} @ {game.get('home_team')}",
                    'old_line': last_line,
                    'new_line': current_spread,
                    'movement': movement,
                    'direction': 'UP' if movement > 0 else 'DOWN'
                }
        
        # Save history
        self._save_history()
        
        return movements
    
    def display_status(self, movements: Dict):
        """Display current line status"""
        print("\n" + "="*70)
        print("WEEK 12 LINE MOVEMENT STATUS")
        print("="*70)
        
        # Load CLV bets
        clv_bets = self.clv_storage.list_all()
        
        for game_id in self.tracked_games:
            # Find corresponding bet
            bet = next((b for b in clv_bets if b.game_id == game_id), None)
            
            if not bet:
                continue
            
            # Get history
            history = self.history.get(game_id, {})
            snapshots = history.get('snapshots', [])
            
            if not snapshots:
                print(f"\n{game_id}: No data yet")
                continue
            
            current = snapshots[-1]
            original = history.get('original_line', current['line'])
            
            # Calculate total movement
            total_movement = current['line'] - original
            
            # Display
            print(f"\n{game_id}: {self.tracked_games[game_id]['away']} @ {self.tracked_games[game_id]['home']}")
            print(f"  Original Line: {original:+.1f}")
            print(f"  Current Line:  {current['line']:+.1f}")
            print(f"  Movement:      {total_movement:+.1f} points")
            
            # Compare to bet line
            if bet:
                bet_line = bet.opening_line
                clv = current['line'] - bet_line
                print(f"  Your Bet Line: {bet_line:+.1f}")
                print(f"  Current CLV:   {clv:+.1f} points", end="")
                if clv > 0:
                    print(" [GOOD - beating current line]")
                elif clv < 0:
                    print(" [BAD - losing to current line]")
                else:
                    print(" [EVEN]")
        
        # Show alerts
        if movements:
            print("\n" + "="*70)
            print("SIGNIFICANT MOVEMENTS (±0.5+ points)")
            print("="*70)
            for game_id, data in movements.items():
                direction_symbol = "↑" if data['direction'] == 'UP' else "↓"
                print(f"\n{direction_symbol} {data['game']}")
                print(f"   {data['old_line']:+.1f} → {data['new_line']:+.1f} ({data['movement']:+.1f})")
        
        print("\n" + "="*70 + "\n")
    
    async def monitor_loop(self, interval: int = 300):
        """Continuous monitoring loop"""
        print("\n" + "="*70)
        print("LINE MOVEMENT MONITOR - WEEK 12")
        print("="*70)
        print(f"Monitoring {len(self.tracked_games)} games")
        print(f"Check interval: {interval} seconds ({interval/60:.0f} minutes)")
        print("Press Ctrl+C to stop")
        print("="*70)
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n--- Check #{iteration} ---")
                
                movements = await self.check_lines()
                self.display_status(movements)
                
                print(f"Next check in {interval} seconds...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n[STOPPED] Monitoring stopped by user")
            print(f"Total checks: {iteration}")
            print("Line history saved to:", self.history_file)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor Week 12 line movements')
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300 = 5 minutes)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Check once and exit (no continuous monitoring)'
    )
    
    args = parser.parse_args()
    
    monitor = LineMonitor()
    
    if args.once:
        # Single check
        movements = await monitor.check_lines()
        monitor.display_status(movements)
    else:
        # Continuous monitoring
        await monitor.monitor_loop(args.interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n[ERROR] Monitor failed: {e}")
        import traceback
        traceback.print_exc()
