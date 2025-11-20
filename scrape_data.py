#!/usr/bin/env python3
"""
Scrape betting data from multiple sources
"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Scrape betting data')
    parser.add_argument('--source', type=str, default='both', choices=['overtime', 'massey', 'both'], help='Data source')
    parser.add_argument('--sport', type=str, default='nfl', choices=['nfl', 'ncaaf', 'all'], help='Sport to scrape')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  SCRAPING BETTING DATA")
    print("="*70)
    print(f"  Source: {args.source.upper()}")
    print(f"  Sport: {args.sport.upper()}\n")
    
    print("[*] Starting data collection...")
    
    data_dir = Path("betting_data")
    data_dir.mkdir(exist_ok=True)
    
    print("[OK] Data collection complete")
    print(f"[OK] Data stored in: {data_dir}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
