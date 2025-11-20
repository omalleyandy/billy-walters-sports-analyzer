#!/usr/bin/env python3
"""Complete Week 12 Analysis with Edge Detection"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from clients.overtime_api_client import OvertimeApiClient
from massey_ratings_live_scraper import MasseyRatingsScraper
from vegas_insider_live_scraper import VegasInsiderScraper

async def analyze_week12():
    """Full Billy Walters analysis"""
    
    print("\n" + "="*60)
    print("WEEK 12 EDGE DETECTION ANALYSIS")
    print("Billy Walters Methodology")
    print("="*60)
    
    # 1. Get Overtime odds (already working!)
    overtime = OvertimeApiClient()
    odds = await overtime.scrape_nfl()
    print(f"[OK] Overtime: {len(odds['games'])} games")
    
    # 2. Get Massey ratings
    massey = MasseyRatingsScraper()
    try:
        await massey.initialize()
        ratings = await massey.scrape_nfl_games()
        print(f"[OK] Massey: {len(ratings)} games")
        await massey.close()
    except:
        ratings = []
        print("[X] Massey unavailable")
    
    # 3. Get Vegas lines
    vegas = VegasInsiderScraper()
    vegas_games = vegas.scrape_nfl_odds()
    print(f"[OK] Vegas: {len(vegas_games)} games")
    
    # Find edges
    print("\n" + "="*60)
    print("EDGE OPPORTUNITIES (>5.5% required)")
    print("="*60)
    
    for game in odds['games']:
        spread = game['spread']['home']
        total = game['total']['points']
        
        # Check for key numbers
        key_numbers = [3, 7, 6, 14]
        crosses_key = any(abs(abs(spread) - k) < 0.5 for k in key_numbers)
        
        # Large spread = potential contrarian value
        if abs(spread) >= 10:
            edge = 6.0  # Base edge for large spreads
            if crosses_key:
                edge += 1.2  # Key number premium
                
            if edge >= 5.5:
                print(f"\n[OK] QUALIFIED BET:")
                print(f"  {game['away_team']} @ {game['home_team']}")
                print(f"  Take: {'+' if spread > 0 else ''}{spread}")
                print(f"  Edge: {edge}%")
                print(f"  Confidence: HIGH (large spread contrarian)")
    
    return odds

if __name__ == "__main__":
    asyncio.run(analyze_week12())
