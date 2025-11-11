#!/usr/bin/env python3
"""
CLI Script for Overtime.ag NFL Odds Scraping

This script scrapes NFL betting lines from Overtime.ag and optionally
converts them to Billy Walters analyzer format.

Usage:
    python scripts/scrape_overtime_nfl.py [--headless] [--convert] [--save-db]
    
Examples:
    # Scrape with visible browser
    python scripts/scrape_overtime_nfl.py
    
    # Scrape headless and convert to Walters format
    python scripts/scrape_overtime_nfl.py --headless --convert
    
    # Scrape, convert, and save to database
    python scripts/scrape_overtime_nfl.py --headless --convert --save-db
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.overtime_pregame_nfl_scraper import OvertimeNFLScraper
from data.overtime_data_converter import convert_overtime_to_walters


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Scrape NFL betting lines from Overtime.ag",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Scrape with visible browser
  %(prog)s --headless                # Scrape in headless mode
  %(prog)s --headless --convert      # Scrape and convert to Walters format
  %(prog)s --output data/odds        # Save to custom directory
        """
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no visible window)"
    )
    
    parser.add_argument(
        "--convert",
        action="store_true",
        help="Convert scraped data to Billy Walters analyzer format"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output/overtime/nfl/pregame",
        help="Output directory for scraped data (default: output/overtime/nfl/pregame)"
    )
    
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Save converted data to database (requires --convert)"
    )
    
    parser.add_argument(
        "--periods",
        nargs="+",
        choices=["GAME", "1ST_HALF", "1ST_QUARTER"],
        default=["GAME"],
        help="Betting periods to scrape (default: GAME)"
    )
    
    parser.add_argument(
        "--proxy",
        type=str,
        help="Proxy URL (format: http://user:pass@host:port)"
    )
    
    parser.add_argument(
        "--customer-id",
        type=str,
        help="Overtime.ag customer ID (overrides OV_CUSTOMER_ID env var)"
    )
    
    parser.add_argument(
        "--password",
        type=str,
        help="Overtime.ag password (overrides OV_PASSWORD env var)"
    )
    
    return parser.parse_args()


async def main():
    """Main execution flow"""
    args = parse_args()
    
    print("=" * 70)
    print("Overtime.ag NFL Odds Scraper")
    print("=" * 70)
    print(f"Mode: {'Headless' if args.headless else 'Visible Browser'}")
    print(f"Output Directory: {args.output}")
    print(f"Convert to Walters Format: {args.convert}")
    print(f"Save to Database: {args.save_db}")
    print("=" * 70)
    print()
    
    # Create scraper
    scraper = OvertimeNFLScraper(
        customer_id=args.customer_id,
        password=args.password,
        proxy_url=args.proxy,
        headless=args.headless,
        output_dir=args.output
    )
    
    # Scrape data
    try:
        print("Starting scrape...")
        overtime_data = await scraper.scrape()
        
        # Save raw Overtime data
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = overtime_data["scrape_metadata"]["timestamp"].replace(":", "-").replace(".", "-")
        raw_file = output_dir / f"overtime_nfl_raw_{timestamp}.json"
        
        with open(raw_file, "w") as f:
            json.dump(overtime_data, f, indent=2, default=str)
        
        print(f"\n[OK] Raw data saved to: {raw_file}")
        
        # Convert if requested
        if args.convert:
            print("\nConverting to Billy Walters format...")
            walters_data = convert_overtime_to_walters(overtime_data)
            
            # Save converted data
            walters_file = output_dir / f"overtime_nfl_walters_{timestamp}.json"
            with open(walters_file, "w") as f:
                json.dump(walters_data, f, indent=2, default=str)
            
            print(f"[OK] Converted data saved to: {walters_file}")
            print(f"  - Games converted: {walters_data['summary']['total_converted']}")
            print(f"  - Conversion rate: {walters_data['summary']['conversion_rate']}")
            
            # Save to database if requested
            if args.save_db:
                print("\nSaving to database...")
                try:
                    # Import database functions
                    from walters_analyzer.ingest.odds_ingest import ingest_odds
                    
                    # Save games to database
                    for game in walters_data["games"]:
                        ingest_odds(game)
                    
                    print(f"[OK] Saved {len(walters_data['games'])} games to database")

                except ImportError:
                    print("[WARNING] Database module not found - skipping database save")
                except Exception as e:
                    print(f"[ERROR] Error saving to database: {e}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("SCRAPE COMPLETE")
        print("=" * 70)
        print(f"Total Games: {overtime_data['summary']['total_games']}")
        print(f"Unique Matchups: {overtime_data['summary']['unique_matchups']}")
        print(f"Periods: {', '.join(overtime_data['summary']['periods'])}")
        
        if overtime_data.get("account_info"):
            print(f"\nAccount Balance: {overtime_data['account_info']['balance']}")
            print(f"Available: {overtime_data['account_info']['available_balance']}")
        
        print("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n[WARNING] Scrape interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Error during scrape: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

