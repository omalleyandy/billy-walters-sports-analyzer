#!/usr/bin/env python3
"""
Simple Edge Analysis for Week 12
Uses existing project components without complex dependencies
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("\n" + "="*70)
    print("  BILLY WALTERS BETTING SYSTEM - EDGE ANALYSIS")
    print("  Week 12 NFL")
    print("="*70 + "\n")
    
    # Check for existing data
    data_dir = Path("data")
    output_dir = Path("output")
    
    print("[*] Checking for existing game data...")
    
    # Look for Week 12 data
    week12_files = [
        output_dir / "unified" / "nfl_week_12_games.json",
        data_dir / "nfl_2025_week_12_games.json",
        Path("WEEK12_NFL_DATA_UPDATE.md"),
    ]
    
    found_data = False
    for file in week12_files:
        if file.exists():
            print(f"[OK] Found: {file}")
            found_data = True
    
    if not found_data:
        print("\n[INFO] No Week 12 game data found yet.")
        print("\n[TODO] To analyze edges, you need:")
        print("  1. Week 12 game schedule")
        print("  2. Current betting lines")
        print("  3. Power ratings (already have ✓)")
        print("\n[NEXT STEPS]")
        print("  Option A: Scrape fresh data")
        print("    python scrape_week12_odds.py")
        print("\n  Option B: Use existing Week 12 analysis")
        print("    See: WEEK12_NFL_DATA_UPDATE.md")
        print("    See: PROJECT_CONTINUITY_WEEK12.md")
        return
    
    # Load power ratings
    print("\n[*] Loading power ratings...")
    ratings_file = data_dir / "power_ratings_nfl_2025.json"
    
    if ratings_file.exists():
        with open(ratings_file) as f:
            ratings_data = json.load(f)
        print(f"[OK] Loaded {len(ratings_data['ratings'])} team ratings")
        print(f"[OK] Last updated: {ratings_data.get('last_updated', 'Unknown')}")
    else:
        print("[ERROR] Power ratings not found!")
        return
    
    # Show high-priority games from documentation
    print("\n" + "="*70)
    print("  HIGH-PRIORITY WEEK 12 GAMES")
    print("  (From PROJECT_CONTINUITY_WEEK12.md)")
    print("="*70 + "\n")
    
    priority_games = [
        {
            "game": "PIT @ CLE",
            "time": "Thursday 8:15 PM",
            "current_line": "CLE +7.5",
            "edge": "3.0 pts (Check injury: Aaron Rodgers)",
            "priority": "HIGH"
        },
        {
            "game": "IND vs DET",
            "time": "Sunday 1:00 PM", 
            "current_line": "DET -7.5",
            "edge": "6.0 pts (Colts off bye)",
            "priority": "HIGH"
        },
        {
            "game": "ARI vs SEA",
            "time": "Sunday 4:25 PM",
            "current_line": "SEA -1.0",
            "edge": "3.0 pts (Division home dog)",
            "priority": "MEDIUM"
        }
    ]
    
    for i, game in enumerate(priority_games, 1):
        print(f"{i}. {game['game']} - {game['time']}")
        print(f"   Line: {game['current_line']}")
        print(f"   Raw Edge: {game['edge']}")
        print(f"   Priority: {game['priority']}")
        print()
    
    print("="*70)
    print("\n[IMPORTANT] These are PRELIMINARY edges from documentation.")
    print("             Need S-factor adjustments and validation!")
    print("\n[NEXT STEPS]")
    print("  1. Review injury reports (especially C.J. Stroud, Josh Jacobs)")
    print("  2. Check weather forecasts for outdoor games")
    print("  3. Apply S-factor adjustments")
    print("  4. Calculate final edges with all factors")
    print("\n[DOCUMENTATION]")
    print("  Full Week 12 Analysis: PROJECT_CONTINUITY_WEEK12.md")
    print("  S-Factor Reference: billy_walters_sfactor_reference.py")
    print("  Edge Calculator: billy_walters_edge_calculator.py")
    print("\n" + "="*70 + "\n")
    
    # Update session
    try:
        from walters_analyzer.core.session_manager import SessionManager
        
        manager = SessionManager(Path("data"))
        session = manager.load_latest_session(week=12)
        
        if session:
            # Mark opportunities as identified
            for game in priority_games:
                session.add_opportunity(game['game'])
            
            manager.save_session(session)
            print("[OK] Session updated with opportunities")
            print(f"[OK] Session: {session.session_id}")
            print(f"[OK] Opportunities identified: {session.opportunities_identified}")
        
    except Exception as e:
        print(f"[INFO] Could not update session: {e}")
    
    print("\n[OK] Edge analysis complete!")
    print("\nRun 'python scripts/quick_start_week12.py' to see updated status")

if __name__ == "__main__":
    main()
