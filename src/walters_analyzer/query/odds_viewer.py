#!/usr/bin/env python3
"""
Overtime.ag Odds Viewer - Query and display scraped pregame odds

This module provides utilities to query, filter, and display odds data
scraped from overtime.ag in a clean, readable format.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class OddsViewer:
    """Query and display overtime.ag scraped odds"""
    
    def __init__(self, data_dir: str = "data/overtime_live"):
        self.data_dir = Path(data_dir)
        self.games = []
    
    def load_latest(self, sport: Optional[str] = None) -> int:
        """Load the most recent scraped data file"""
        jsonl_files = sorted(self.data_dir.glob("overtime-live-*.jsonl"), reverse=True)
        
        if not jsonl_files:
            print(f"No scraped data found in {self.data_dir}", file=sys.stderr)
            return 0
        
        latest_file = jsonl_files[0]
        return self.load_file(latest_file, sport=sport)
    
    def load_file(self, file_path: Path, sport: Optional[str] = None) -> int:
        """Load odds from a specific JSONL file"""
        self.games = []
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    game = json.loads(line)
                    
                    # Filter by source (skip injury data, etc.)
                    if game.get("source") != "overtime.ag":
                        continue
                    
                    # Filter by sport if specified
                    if sport and game.get("sport") != sport:
                        continue
                    
                    self.games.append(game)
                
                except json.JSONDecodeError:
                    continue
        
        return len(self.games)
    
    def filter_by_sport(self, sport: str) -> List[Dict[str, Any]]:
        """Filter games by sport (nfl, college_football)"""
        return [g for g in self.games if g.get("sport") == sport]
    
    def filter_by_date(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter games by event date (ISO format: YYYY-MM-DD)"""
        if not date_str:
            return self.games
        return [g for g in self.games if g.get("event_date") == date_str]
    
    def filter_by_team(self, team_name: str) -> List[Dict[str, Any]]:
        """Filter games involving a specific team (case-insensitive partial match)"""
        team_lower = team_name.lower()
        filtered = []
        
        for game in self.games:
            teams = game.get("teams", {})
            away = teams.get("away", "").lower()
            home = teams.get("home", "").lower()
            
            if team_lower in away or team_lower in home:
                filtered.append(game)
        
        return filtered
    
    def get_today_games(self) -> List[Dict[str, Any]]:
        """Get games scheduled for today"""
        today = datetime.now().date().isoformat()
        return self.filter_by_date(today)
    
    def get_upcoming_games(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get games in the next N days"""
        today = datetime.now().date()
        end_date = (today + timedelta(days=days)).isoformat()
        
        filtered = []
        for game in self.games:
            event_date = game.get("event_date")
            if event_date and event_date <= end_date and event_date >= today.isoformat():
                filtered.append(game)
        
        return filtered
    
    def display_game(self, game: Dict[str, Any], show_details: bool = True):
        """Display a single game in a readable format"""
        teams = game.get("teams", {})
        away = teams.get("away", "UNKNOWN")
        home = teams.get("home", "UNKNOWN")
        
        rotation = game.get("rotation_number", "")
        event_date = game.get("event_date", "")
        event_time = game.get("event_time", "")
        
        # Header
        print("=" * 80)
        print(f"🏈 {away} @ {home}")
        if rotation:
            print(f"   Rotation: {rotation}")
        if event_date and event_time:
            print(f"   📅 {event_date} at {event_time}")
        elif event_date:
            print(f"   📅 {event_date}")
        
        if not show_details:
            print()
            return
        
        markets = game.get("markets", {})
        
        # Spread
        spread = markets.get("spread", {})
        spread_away = spread.get("away")
        spread_home = spread.get("home")
        
        if spread_away or spread_home:
            print("\n   📊 SPREAD:")
            if spread_away:
                line = spread_away.get("line")
                price = spread_away.get("price")
                sign = "+" if line and line > 0 else ""
                print(f"      {away:30s}  {sign}{line:5.1f}  ({price:+4d})")
            if spread_home:
                line = spread_home.get("line")
                price = spread_home.get("price")
                sign = "+" if line and line > 0 else ""
                print(f"      {home:30s}  {sign}{line:5.1f}  ({price:+4d})")
        
        # Total
        total = markets.get("total", {})
        total_over = total.get("over")
        total_under = total.get("under")
        
        if total_over or total_under:
            print("\n   🎯 TOTAL:")
            if total_over:
                line = total_over.get("line")
                price = total_over.get("price")
                print(f"      {'OVER':30s}  {line:5.1f}  ({price:+4d})")
            if total_under:
                line = total_under.get("line")
                price = total_under.get("price")
                print(f"      {'UNDER':30s}  {line:5.1f}  ({price:+4d})")
        
        # Moneyline
        moneyline = markets.get("moneyline", {})
        ml_away = moneyline.get("away")
        ml_home = moneyline.get("home")
        
        if ml_away or ml_home:
            print("\n   💰 MONEYLINE:")
            if ml_away:
                price = ml_away.get("price")
                print(f"      {away:30s}  ({price:+4d})")
            if ml_home:
                price = ml_home.get("price")
                print(f"      {home:30s}  ({price:+4d})")
        
        print()
    
    def display_games(self, games: List[Dict[str, Any]], show_details: bool = True):
        """Display multiple games"""
        if not games:
            print("No games found.")
            return
        
        print(f"\nFound {len(games)} game(s):\n")
        
        for game in games:
            self.display_game(game, show_details=show_details)
    
    def display_summary(self):
        """Display summary of loaded games"""
        if not self.games:
            print("No games loaded.")
            return
        
        # Group by sport
        by_sport = defaultdict(list)
        for game in self.games:
            sport = game.get("sport", "unknown")
            by_sport[sport].append(game)
        
        print(f"\n📊 LOADED GAMES SUMMARY:")
        print("=" * 80)
        print(f"Total Games: {len(self.games)}")
        print()
        
        for sport, games in sorted(by_sport.items()):
            sport_label = sport.upper().replace("_", " ")
            print(f"{sport_label}: {len(games)} games")
            
            # Group by date
            by_date = defaultdict(list)
            for game in games:
                date = game.get("event_date", "Unknown")
                by_date[date].append(game)
            
            for date in sorted(by_date.keys()):
                if date != "Unknown":
                    print(f"  - {date}: {len(by_date[date])} games")
        
        print()
    
    def compare_lines(self, team_name: str):
        """Compare betting lines for a team across different games/dates"""
        games = self.filter_by_team(team_name)
        
        if not games:
            print(f"No games found for '{team_name}'")
            return
        
        print(f"\n📈 LINE COMPARISON FOR '{team_name.upper()}':")
        print("=" * 80)
        
        for game in sorted(games, key=lambda g: g.get("event_date", "")):
            teams = game.get("teams", {})
            away = teams.get("away", "")
            home = teams.get("home", "")
            
            is_away = team_name.lower() in away.lower()
            opponent = home if is_away else away
            location = "@ " if is_away else "vs "
            
            event_date = game.get("event_date", "Unknown")
            event_time = game.get("event_time", "")
            
            markets = game.get("markets", {})
            spread = markets.get("spread", {})
            
            if is_away:
                spread_line = spread.get("away")
            else:
                spread_line = spread.get("home")
            
            if spread_line:
                line = spread_line.get("line")
                price = spread_line.get("price")
                sign = "+" if line and line > 0 else ""
                
                print(f"{event_date} {event_time:12s} | {location}{opponent:25s} | {sign}{line:5.1f} ({price:+4d})")
            else:
                print(f"{event_date} {event_time:12s} | {location}{opponent:25s} | No spread available")
        
        print()
    
    def export_csv(self, games: List[Dict[str, Any]], output_file: str):
        """Export filtered games to CSV"""
        import csv
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Date', 'Time', 'Rotation', 'Away Team', 'Home Team',
                'Away Spread Line', 'Away Spread Price',
                'Home Spread Line', 'Home Spread Price',
                'Total Over Line', 'Total Over Price',
                'Total Under Line', 'Total Under Price',
                'Away ML Price', 'Home ML Price'
            ])
            
            # Data
            for game in games:
                teams = game.get("teams", {})
                markets = game.get("markets", {})
                
                spread = markets.get("spread", {})
                total = markets.get("total", {})
                ml = markets.get("moneyline", {})
                
                writer.writerow([
                    game.get("event_date", ""),
                    game.get("event_time", ""),
                    game.get("rotation_number", ""),
                    teams.get("away", ""),
                    teams.get("home", ""),
                    spread.get("away", {}).get("line", ""),
                    spread.get("away", {}).get("price", ""),
                    spread.get("home", {}).get("line", ""),
                    spread.get("home", {}).get("price", ""),
                    total.get("over", {}).get("line", ""),
                    total.get("over", {}).get("price", ""),
                    total.get("under", {}).get("line", ""),
                    total.get("under", {}).get("price", ""),
                    ml.get("away", {}).get("price", ""),
                    ml.get("home", {}).get("price", ""),
                ])
        
        print(f"✅ Exported {len(games)} games to {output_file}")


def main():
    """CLI interface for odds viewer"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="View and query scraped overtime.ag odds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View all NFL games
  python odds_viewer.py --sport nfl
  
  # View today's games
  python odds_viewer.py --today
  
  # Search for a specific team
  python odds_viewer.py --team "Cowboys"
  
  # Compare lines for a team
  python odds_viewer.py --compare "Cardinals"
  
  # Export to CSV
  python odds_viewer.py --sport nfl --export nfl_odds.csv
        """
    )
    
    parser.add_argument("--data-dir", default="data/overtime_live",
                       help="Directory containing scraped data")
    parser.add_argument("--file", help="Specific JSONL file to load")
    parser.add_argument("--sport", choices=["nfl", "college_football"],
                       help="Filter by sport")
    parser.add_argument("--date", help="Filter by date (YYYY-MM-DD)")
    parser.add_argument("--today", action="store_true",
                       help="Show today's games")
    parser.add_argument("--upcoming", type=int, metavar="DAYS",
                       help="Show games in next N days")
    parser.add_argument("--team", help="Filter by team name")
    parser.add_argument("--compare", metavar="TEAM",
                       help="Compare lines for a team")
    parser.add_argument("--summary", action="store_true",
                       help="Show summary only")
    parser.add_argument("--brief", action="store_true",
                       help="Brief output (no detailed odds)")
    parser.add_argument("--export", metavar="FILE",
                       help="Export results to CSV file")
    
    args = parser.parse_args()
    
    # Initialize viewer
    viewer = OddsViewer(data_dir=args.data_dir)
    
    # Load data
    if args.file:
        count = viewer.load_file(Path(args.file), sport=args.sport)
        print(f"Loaded {count} games from {args.file}")
    else:
        count = viewer.load_latest(sport=args.sport)
        if count > 0:
            latest_file = sorted(Path(args.data_dir).glob("overtime-live-*.jsonl"), reverse=True)[0]
            print(f"Loaded {count} games from {latest_file.name}")
    
    if count == 0:
        print("No games loaded. Run scraper first:")
        print("  uv run walters-analyzer scrape-overtime --sport nfl")
        sys.exit(1)
    
    # Show summary if requested
    if args.summary:
        viewer.display_summary()
        sys.exit(0)
    
    # Compare mode
    if args.compare:
        viewer.compare_lines(args.compare)
        sys.exit(0)
    
    # Filter games
    games = viewer.games
    
    if args.today:
        games = viewer.get_today_games()
    elif args.upcoming:
        games = viewer.get_upcoming_games(days=args.upcoming)
    elif args.date:
        games = viewer.filter_by_date(args.date)
    
    if args.team:
        games = [g for g in games if any(
            args.team.lower() in team.lower()
            for team in [g.get("teams", {}).get("away", ""), g.get("teams", {}).get("home", "")]
        )]
    
    # Export if requested
    if args.export:
        viewer.export_csv(games, args.export)
    else:
        # Display games
        viewer.display_games(games, show_details=not args.brief)


if __name__ == "__main__":
    main()

