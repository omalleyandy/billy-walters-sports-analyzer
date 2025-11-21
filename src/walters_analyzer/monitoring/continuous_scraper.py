#!/usr/bin/env python3
"""
Continuous Odds Scraper - Runs your existing scrapers at specified intervals
Uses your installed walters_analyzer package
"""

import time
import subprocess
import argparse
from datetime import datetime
import sys


def run_scraper(scraper_name: str, sport: str = "nfl"):
    """Run one of your existing scrapers"""
    try:
        print(f"[CHART] Running {scraper_name}...")

        if scraper_name == "overtime":
            cmd = ["python", "-m", "walters_analyzer.cli", "scrape-overtime"]
        elif scraper_name == "highlightly":
            cmd = ["python", "-m", "walters_analyzer.cli", "scrape-highlightly"]
        elif scraper_name == "sharp-monitor":
            cmd = ["python", "-m", "walters_analyzer.cli", "monitor-sharp"]
        elif scraper_name == "nfl-site":
            cmd = ["python", "-m", "walters_analyzer.cli", "scrape-nfl-site"]
        else:
            print(f"[ERROR] Unknown scraper: {scraper_name}")
            return False

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[*] {scraper_name} completed successfully")
            if result.stdout:
                # Show last few lines of output
                lines = result.stdout.strip().split("\n")
                for line in lines[-5:]:
                    print(f"   {line}")
            return True
        else:
            print(f"[ERROR] {scraper_name} failed:")
            if result.stderr:
                print(f"   {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"[ERROR] Error running {scraper_name}: {e}")
        return False


def continuous_scrape(interval: int = 60, scrapers: list = None):
    """
    Continuously scrape odds at specified intervals

    Args:
        interval: Seconds between scrapes
        scrapers: List of scrapers to run (default: all)
    """
    if scrapers is None:
        scrapers = ["overtime", "highlightly", "sharp-monitor"]

    print(f"\n{'=' * 60}")
    print("[*] CONTINUOUS ODDS SCRAPING")
    print(f"Interval: {interval}s ({interval / 60:.1f} min)")
    print(f"Scrapers: {', '.join(scrapers)}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to stop")
    print(f"{'=' * 60}\n")

    iteration = 0
    start_time = datetime.now()
    successes = 0
    failures = 0

    try:
        while True:
            iteration += 1
            iter_start = datetime.now()

            print(f"\n{'[*]' * 60}")
            print(f"[*] Iteration #{iteration} - {iter_start.strftime('%H:%M:%S')}")
            print(f"{'[*]' * 60}")

            # Run each scraper
            for scraper in scrapers:
                if run_scraper(scraper):
                    successes += 1
                else:
                    failures += 1

                # Small delay between scrapers
                if len(scrapers) > 1:
                    time.sleep(2)

            # Stats
            iter_time = (datetime.now() - iter_start).total_seconds()
            runtime = datetime.now() - start_time
            hours = int(runtime.total_seconds() // 3600)
            minutes = int((runtime.total_seconds() % 3600) // 60)

            print("\n[CHART] STATS:")
            print(f"   Iteration time: {iter_time:.1f}s")
            print(f"   Total runtime: {hours}h {minutes}m")
            print(f"   Iterations: {iteration}")
            print(
                f"   Success rate: {successes}/{successes + failures} ({100 * successes / (successes + failures):.1f}%)"
            )

            # Wait for next iteration
            wait_msg = f"{interval / 60:.1f} min" if interval >= 60 else f"{interval}s"
            print(f"\n⏳ Waiting {wait_msg} until next check...")
            time.sleep(interval)

    except KeyboardInterrupt:
        runtime = datetime.now() - start_time
        hours = int(runtime.total_seconds() // 3600)
        minutes = int((runtime.total_seconds() % 3600) // 60)

        print(f"\n\n{'=' * 60}")
        print("[*] SCRAPING STOPPED")
        print(f"Total runtime: {hours}h {minutes}m")
        print(f"Total iterations: {iteration}")
        print(
            f"Success rate: {successes}/{successes + failures} ({100 * successes / (successes + failures):.1f}%)"
        )
        print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Continuous odds scraping using your existing tools"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Scrape interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--scrapers",
        nargs="+",
        choices=["overtime", "highlightly", "sharp-monitor", "nfl-site"],
        help="Which scrapers to run (default: overtime, highlightly, sharp-monitor)",
    )

    args = parser.parse_args()

    if args.interval < 30:
        print(
            "[WARNING]  Warning: Intervals <30s may trigger rate limits or API quotas"
        )
        response = input("Continue? (y/n): ")
        if response.lower() != "y":
            sys.exit(0)

    continuous_scrape(args.interval, args.scrapers)


if __name__ == "__main__":
    main()
