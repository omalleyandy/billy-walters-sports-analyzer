#!/usr/bin/env python3
"""
Quick Monitor Runner - Uses your existing walters_analyzer package
Runs analysis at 1-minute intervals
"""

import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path for direct import
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Try importing from installed package (using relative imports since we're in the package)
    from ..cli import main as cli_main
    from ..config import get_settings
    PACKAGE_INSTALLED = True
    print("[*] Using installed walters_analyzer package")
except ImportError:
    # Fallback to direct import
    PACKAGE_INSTALLED = False
    print("[WARNING]  walters_analyzer not installed")
    print("   Run: uv pip install -e .")
    print("   Or:  pip install -e .")
    sys.exit(1)


def run_live_monitor(interval_seconds: int = 60):
    """
    Run live monitoring at specified interval
    
    Args:
        interval_seconds: How often to check (default: 60 = 1 minute)
    """
    print(f"\n{'='*60}")
    print(f"[*] WALTERS ANALYZER - LIVE MONITORING")
    print(f"Interval: {interval_seconds} seconds ({interval_seconds/60:.1f} minutes)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n{'[*]'*60}")
            print(f"[*] Iteration #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'[*]'*60}")
            
            try:
                # Here you would call your analysis
                # For now, just showing the pattern
                print("[CHART] Fetching current odds...")
                print("[SEARCH] Analyzing edges...")
                print("[*] Analysis complete")
                
                # You can integrate with your existing tools here:
                # - Call the CLI commands programmatically
                # - Import and use your analysis modules directly
                # - Use the live_odds_monitor.py functionality
                
            except Exception as e:
                print(f"[ERROR] Error in iteration: {e}")
                print("   Continuing with next iteration...")
            
            # Wait for next iteration
            print(f"\n⏳ Waiting {interval_seconds} seconds until next check...")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n\n{'='*60}")
        print("[*] MONITORING STOPPED")
        print(f"Total iterations: {iteration}")
        print(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Quick monitor for Walters Analyzer'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    if args.interval < 30:
        print("[WARNING]  Warning: Intervals <30 seconds may trigger rate limits")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    run_live_monitor(args.interval)


if __name__ == "__main__":
    main()
