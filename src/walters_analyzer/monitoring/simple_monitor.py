#!/usr/bin/env python3
"""
Simple Monitoring Loop - Works Immediately
No package installation required
"""

import time
import argparse
from datetime import datetime
import sys


def simple_monitor(interval_seconds: int = 60):
    """
    Basic monitoring loop that runs at specified intervals

    This is a template - you'll add your actual analysis code here
    """
    print(f"\n{'=' * 60}")
    print("[*] SIMPLE MONITOR STARTED")
    print(f"Interval: {interval_seconds} seconds ({interval_seconds / 60:.1f} min)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to stop")
    print(f"{'=' * 60}\n")

    iteration = 0
    start_time = datetime.now()

    try:
        while True:
            iteration += 1
            iter_start = datetime.now()

            print(f"\n{'[*]' * 60}")
            print(f"[*] Iteration #{iteration} - {iter_start.strftime('%H:%M:%S')}")
            print(f"{'[*]' * 60}")

            try:
                # =================================================================
                # YOUR ANALYSIS CODE GOES HERE
                # =================================================================

                print("[CHART] Step 1: Fetching data...")
                time.sleep(0.5)  # Simulate work

                print("[SEARCH] Step 2: Analyzing edges...")
                time.sleep(0.5)  # Simulate work

                print("[*] Step 3: Complete")

                # Example of what you might do:
                # 1. Call your CLI: subprocess.run(["python", "-m", "walters_analyzer.cli", "scrape-ai"])
                # 2. Import your modules: from walters_analyzer import analyze_game
                # 3. Call external APIs
                # 4. Write results to files

                # =================================================================

                iter_time = (datetime.now() - iter_start).total_seconds()
                print(f"⏱[*]  Iteration completed in {iter_time:.1f}s")

            except Exception as e:
                print(f"[ERROR] Error in iteration: {e}")
                print("   Continuing with next iteration...")

            # Calculate runtime stats
            runtime = datetime.now() - start_time
            hours = int(runtime.total_seconds() // 3600)
            minutes = int((runtime.total_seconds() % 3600) // 60)

            print(
                f"\n[CHART] Stats: Runtime={hours}h {minutes}m | Iterations={iteration}"
            )

            # Wait for next iteration
            next_check = datetime.now()
            next_check = next_check.replace(second=0, microsecond=0)

            if interval_seconds >= 60:
                wait_msg = f"{interval_seconds / 60:.1f} minutes"
            else:
                wait_msg = f"{interval_seconds} seconds"

            print(f"⏳ Waiting {wait_msg} until next check...")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        runtime = datetime.now() - start_time
        hours = int(runtime.total_seconds() // 3600)
        minutes = int((runtime.total_seconds() % 3600) // 60)

        print(f"\n\n{'=' * 60}")
        print("[*] MONITOR STOPPED")
        print(f"Total runtime: {hours}h {minutes}m")
        print(f"Total iterations: {iteration}")
        print(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Simple monitoring loop - runs at specified intervals"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60 = 1 minute)",
    )

    args = parser.parse_args()

    # Validation
    if args.interval < 10:
        print("[ERROR] Error: Minimum interval is 10 seconds")
        sys.exit(1)

    if args.interval < 30:
        print("[WARNING]  Warning: Intervals <30 seconds may trigger rate limits")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(0)

    simple_monitor(args.interval)


if __name__ == "__main__":
    main()
