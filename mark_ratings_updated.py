#!/usr/bin/env python3
"""
Simple helper to mark power ratings as updated in the session
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from walters_analyzer.core.session_manager import SessionManager

def main():
    manager = SessionManager(Path("data"))
    session = manager.load_latest_session(week=12)
    
    if not session:
        print("[ERROR] No Week 12 session found. Run quick start first.")
        return
        
    session.mark_power_ratings_updated()
    manager.save_session(session)
    
    print("[OK] Power ratings marked as updated")
    print(f"    Session: {session.session_id}")
    print(f"    Note: Using power ratings from data/power_ratings_nfl_2025.json")
    print(f"    Last updated: November 9, 2025")
    print()
    print("Next step: Check injury reports")

if __name__ == "__main__":
    main()
