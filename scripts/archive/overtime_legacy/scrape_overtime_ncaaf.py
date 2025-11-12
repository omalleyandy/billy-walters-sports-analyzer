#!/usr/bin/env python3
"""
CLI Script for Overtime.ag NCAAF Odds Scraping

This script scrapes NCAAF (NCAA College Football) betting lines from Overtime.ag
and optionally converts them to Billy Walters analyzer format.

Usage:
    python scripts/scrape_overtime_ncaaf.py [--headless] [--convert] [--save-db]

Examples:
    # Scrape with visible browser
    python scripts/scrape_overtime_ncaaf.py

    # Scrape headless and convert to Walters format
    python scripts/scrape_overtime_ncaaf.py --headless --convert

    # Scrape, convert, and save to database
    python scripts/scrape_overtime_ncaaf.py --headless --convert --save-db
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.overtime_pregame_ncaaf_scraper import OvertimeNCAAFScraper
from data.overtime_data_converter import convert_overtime_to_walters
from data.models import League


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Scrape NCAAF betting lines from Overtime.ag",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Scrape with visible browser
  %(prog)s --headless                # Scrape in headless mode
  %(prog)s --headless --convert      # Scrape and convert to Walters format
  %(prog)s --output data/odds        # Save to custom directory
        """,
    )

    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode"
    )

    parser.add_argument(
        "--convert",
        action="store_true",
        help="Convert output to Billy Walters format",
    )

    parser.add_argument(
        "--save-db", action="store_true", help="Save converted data to database"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output/overtime/ncaaf/pregame",
        help="Output directory for scraped data (default: output/overtime/ncaaf/pregame)",
    )

    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help='Proxy URL with credentials (e.g., "http://user:pass@host:port"). Leave empty to disable proxy.',
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    # Create scraper
    scraper = OvertimeNCAAFScraper(
        headless=args.headless, output_dir=args.output, proxy_url=args.proxy
    )

    # Run scraper
    print("\nStarting NCAAF scraper...")
    result = await scraper.scrape()

    # Print summary
    print("\n" + "=" * 70)
    print("SCRAPE COMPLETED")
    print("=" * 70)
    print(f"Total game entries: {result['summary']['total_games']}")
    print(f"Unique matchups: {result['summary']['unique_matchups']}")
    print(f"Periods scraped: {', '.join(result['summary']['periods'])}")

    if result.get("account_info"):
        print(f"\nAccount Balance: {result['account_info']['balance']}")
        print(f"Available: {result['account_info']['available_balance']}")

    # Convert to Billy Walters format if requested
    if args.convert:
        print("\n" + "=" * 70)
        print("CONVERTING TO BILLY WALTERS FORMAT")
        print("=" * 70)

        # Find the most recent scraped file
        output_dir = Path(args.output)
        json_files = sorted(output_dir.glob("overtime_ncaaf_odds_*.json"), reverse=True)

        if not json_files:
            print("[ERROR] No scraped data files found to convert")
            return

        input_file = json_files[0]
        print(f"Converting: {input_file.name}")

        # Load and convert
        with open(input_file, "r", encoding="utf-8") as f:
            overtime_data = json.load(f)

        walters_data = convert_overtime_to_walters(overtime_data, league=League.NCAAF)

        # Save converted file
        output_file = input_file.parent / input_file.name.replace("_odds_", "_walters_")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(walters_data, f, indent=2, default=str)

        print(f"[OK] Converted {walters_data['summary']['total_converted']} games")
        print(f"[OK] Saved to: {output_file}")

        if args.save_db:
            print("\n[INFO] Database saving not yet implemented for NCAAF")
            print("       Data is available in JSON format for manual import")

    print("\n" + "=" * 70)
    print("[OK] NCAAF scraping workflow complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
