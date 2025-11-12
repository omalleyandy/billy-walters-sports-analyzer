#!/usr/bin/env python3
"""
Unified Overtime.ag Scraper - NFL and NCAAF

Scrapes both NFL and NCAAF (College Football) betting lines from Overtime.ag
in a single command. Run anytime to get whatever lines are currently available.

Usage:
    python scripts/scrape_overtime_all.py [--headless] [--convert] [--save-db]

Examples:
    # Scrape both sports with visible browser
    python scripts/scrape_overtime_all.py

    # Scrape headless and convert to Walters format
    python scripts/scrape_overtime_all.py --headless --convert

    # Scrape NFL only
    python scripts/scrape_overtime_all.py --nfl-only

    # Scrape NCAAF only
    python scripts/scrape_overtime_all.py --ncaaf-only

IMPORTANT: This scraper can run ANYTIME - there are no restrictions!
- Tuesday-Wednesday: Most lines available (14+ NFL, 50+ NCAAF) - OPTIMAL
- Thursday-Saturday: Some games available (varies by week)
- Sunday-Monday: Few/no pregame lines (games in progress)

The scraper will return whatever lines are currently posted by the sportsbook.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.overtime_pregame_nfl_scraper import OvertimeNFLScraper
from data.overtime_pregame_ncaaf_scraper import OvertimeNCAAFScraper
from data.overtime_data_converter import convert_overtime_to_walters
from data.models import League


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Scrape NFL and NCAAF betting lines from Overtime.ag",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Scrape both NFL and NCAAF with visible browser
  %(prog)s --headless                # Scrape both in headless mode
  %(prog)s --headless --convert      # Scrape and convert to Walters format
  %(prog)s --nfl-only                # Scrape NFL only
  %(prog)s --ncaaf-only              # Scrape NCAAF only
  %(prog)s --proxy ""                # Disable proxy (recommended)

Timing Notes:
  Run this command ANYTIME to get currently available lines.
  - Tuesday-Wednesday: 14+ NFL games, 50+ NCAAF games (optimal)
  - Thursday-Saturday: Varies by week
  - Sunday-Monday: Few/no pregame lines (games in progress)
        """,
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no visible window)",
    )

    parser.add_argument(
        "--convert",
        action="store_true",
        default=True,
        help="Convert scraped data to Billy Walters analyzer format (default: True)",
    )

    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Save converted data to database (requires --convert)",
    )

    parser.add_argument(
        "--nfl-only",
        action="store_true",
        help="Scrape NFL only (skip NCAAF)",
    )

    parser.add_argument(
        "--ncaaf-only",
        action="store_true",
        help="Scrape NCAAF only (skip NFL)",
    )

    parser.add_argument(
        "--proxy",
        type=str,
        help='Proxy URL (format: http://user:pass@host:port, use --proxy "" to disable)',
    )

    parser.add_argument(
        "--customer-id",
        type=str,
        help="Overtime.ag customer ID (overrides OV_CUSTOMER_ID env var)",
    )

    parser.add_argument(
        "--password",
        type=str,
        help="Overtime.ag password (overrides OV_PASSWORD env var)",
    )

    return parser.parse_args()


async def scrape_sport(
    scraper_class, sport_name, headless, convert, save_db, proxy, customer_id, password
):
    """Scrape a specific sport"""
    print("=" * 70)
    print(f"Scraping {sport_name}")
    print("=" * 70)
    print()

    # Initialize scraper
    scraper = scraper_class(
        headless=headless, proxy_url=proxy, customer_id=customer_id, password=password
    )

    try:
        # Run scrape
        result = await scraper.scrape()

        if result:
            games_found = len(result.get("games", []))
            print(f"[OK] {sport_name}: Found {games_found} games")

            # Save raw data
            output_dir = Path(scraper.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Get timestamp from result and make it filesystem-safe
            timestamp = (
                result["scrape_metadata"]["timestamp"]
                .replace(":", "-")
                .replace(".", "-")
            )

            # Save raw file
            raw_file = (
                output_dir / f"overtime_{sport_name.lower()}_raw_{timestamp}.json"
            )
            with open(raw_file, "w") as f:
                json.dump(result, f, indent=2, default=str)

            print(f"     Raw data saved to: {raw_file}")

            # Convert to Walters format if requested
            if convert:
                print(f"     Converting {sport_name} to Billy Walters format...")

                # Determine league
                league = League.NFL if sport_name == "NFL" else League.NCAAF

                # Convert the data object directly (not file path)
                walters_data = convert_overtime_to_walters(result, league)

                # Save Walters format
                walters_file = (
                    output_dir
                    / f"overtime_{sport_name.lower()}_walters_{timestamp}.json"
                )
                with open(walters_file, "w") as f:
                    json.dump(walters_data, f, indent=2, default=str)

                games_converted = walters_data.get("summary", {}).get(
                    "total_converted", 0
                )
                print(f"     Converted {games_converted} games to Walters format")
                print(f"     Walters data saved to: {walters_file}")

                # TODO: Add database save if --save-db flag is set
                if save_db:
                    print(
                        "     [WARNING] Database save not yet implemented for unified scraper"
                    )

            return result
        else:
            print(f"[WARNING] {sport_name}: No data returned from scraper")
            return None

    except Exception as e:
        print(f"[ERROR] {sport_name} scrape failed: {e}")
        return None


async def main():
    """Main scraper function"""
    args = parse_args()

    print("=" * 70)
    print("OVERTIME.AG UNIFIED SCRAPER")
    print("NFL and NCAAF Pregame Odds")
    print("=" * 70)
    print()
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Configuration:")
    print(f"  Headless: {args.headless}")
    print(f"  Convert to Walters format: {args.convert}")
    print(f"  Save to database: {args.save_db}")
    print(
        f"  Proxy: {'Disabled' if args.proxy == '' else args.proxy or 'From environment'}"
    )
    print()

    results = {}

    # Determine which sports to scrape
    scrape_nfl = not args.ncaaf_only
    scrape_ncaaf = not args.nfl_only

    # Scrape NFL
    if scrape_nfl:
        results["NFL"] = await scrape_sport(
            OvertimeNFLScraper,
            "NFL",
            args.headless,
            args.convert,
            args.save_db,
            args.proxy,
            args.customer_id,
            args.password,
        )
        print()

    # Scrape NCAAF
    if scrape_ncaaf:
        results["NCAAF"] = await scrape_sport(
            OvertimeNCAAFScraper,
            "NCAAF",
            args.headless,
            args.convert,
            args.save_db,
            args.proxy,
            args.customer_id,
            args.password,
        )
        print()

    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    total_games = 0
    for sport, result in results.items():
        if result:
            games = len(result.get("games", []))
            total_games += games
            print(f"  {sport}: {games} games")
        else:
            print(f"  {sport}: Failed or no data")

    print()
    print(f"Total Games: {total_games}")
    print()

    if total_games == 0:
        print("[WARNING] No games found")
        print()
        print("This is normal when:")
        print("  - Games are currently in progress (Sunday/Monday)")
        print("  - Week has ended and next week lines haven't posted yet")
        print()
        print("Optimal times to scrape:")
        print("  - Tuesday-Wednesday: New week lines post after MNF")
        print("  - Thursday morning: Fresh lines before TNF")
        print()
        print("Try running again Tuesday-Wednesday for best results.")
    else:
        print("[OK] Scrape completed successfully!")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
