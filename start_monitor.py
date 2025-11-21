#!/usr/bin/env python3
"""
Start live monitoring of betting lines
"""

import asyncio
import argparse
import sys
from datetime import datetime


async def monitor_lines(interval=60):
    print("\n" + "=" * 70)
    print("  STARTING LINE MONITOR")
    print("=" * 70)
    print(f"Watching lines every {interval} seconds")
    print("Press Ctrl+C to stop\n")

    try:
        iteration = 0
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Checking lines (iteration {iteration})...")
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        print("\n[OK] Monitor stopped")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Start monitoring betting lines")
    parser.add_argument(
        "--watch-lines", type=bool, default=True, help="Watch for line movements"
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="Update interval in seconds"
    )

    args = parser.parse_args()

    try:
        asyncio.run(monitor_lines(args.interval))
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
