"""
Scrape Overtime.ag using reverse-engineered API endpoint (no browser required).

This is the NEW recommended method for scraping Overtime.ag odds.

Advantages over Playwright/SignalR:
- No browser automation required
- No CloudFlare bypass needed
- No proxy required
- Simple HTTP POST request
- Fast and reliable (< 5 seconds)
- Works on all platforms

Usage:
    # Scrape NFL
    uv run python scripts/scrape_overtime_api.py --nfl

    # Scrape NCAAF
    uv run python scripts/scrape_overtime_api.py --ncaaf

    # Scrape both
    uv run python scripts/scrape_overtime_api.py --nfl --ncaaf

Author: Claude Code
Date: 2025-11-11
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.overtime_api_client import OvertimeApiClient


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape Overtime.ag odds using reverse-engineered API"
    )
    parser.add_argument("--nfl", action="store_true", help="Scrape NFL games")
    parser.add_argument("--ncaaf", action="store_true", help="Scrape NCAAF games")
    parser.add_argument(
        "--output",
        type=str,
        default="output/overtime",
        help="Output directory (default: output/overtime)",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save output files"
    )

    args = parser.parse_args()

    # Default to both if neither specified
    if not args.nfl and not args.ncaaf:
        args.nfl = True
        args.ncaaf = True

    client = OvertimeApiClient(output_dir=args.output)

    total_games = 0

    # Scrape NFL
    if args.nfl:
        print("\n[SCRAPING NFL]")
        print(f"API: {client.BASE_URL}")

        nfl_data = await client.scrape_nfl(
            save_raw=not args.no_save, save_converted=not args.no_save
        )

        games_found = nfl_data["summary"]["total_games"]
        total_games += games_found

        print(f"[OK] Games found: {games_found}")

        if not args.no_save:
            # Show latest saved file
            nfl_dir = Path(args.output) / "nfl" / "pregame"
            files = sorted(nfl_dir.glob("api_walters_*.json"), reverse=True)
            if files:
                print(f"[SAVED] {files[0].relative_to('.')}")

        # Show sample game
        if nfl_data["games"]:
            sample = nfl_data["games"][0]
            print("\n[SAMPLE GAME]")
            print(f"  {sample['away_team']} @ {sample['home_team']}")
            print(
                f"  Spread: {sample['spread']['away']:+.1f} ({sample['spread']['away_odds']:+d}) / {sample['spread']['home']:+.1f} ({sample['spread']['home_odds']:+d})"
            )
            print(
                f"  Total: {sample['total']['points']:.1f} (O{sample['total']['over_odds']:+d}/U{sample['total']['under_odds']:+d})"
            )
            print(
                f"  Moneyline: {sample['moneyline']['away']:+d} / {sample['moneyline']['home']:+d}"
            )

    # Scrape NCAAF
    if args.ncaaf:
        print("\n[SCRAPING NCAAF]")
        print(f"API: {client.BASE_URL}")

        ncaaf_data = await client.scrape_ncaaf(
            save_raw=not args.no_save, save_converted=not args.no_save
        )

        games_found = ncaaf_data["summary"]["total_games"]
        total_games += games_found

        print(f"[OK] Games found: {games_found}")

        if not args.no_save:
            # Show latest saved file
            ncaaf_dir = Path(args.output) / "ncaaf" / "pregame"
            files = sorted(ncaaf_dir.glob("api_walters_*.json"), reverse=True)
            if files:
                print(f"[SAVED] {files[0].relative_to('.')}")

        # Show sample game
        if ncaaf_data["games"]:
            sample = ncaaf_data["games"][0]
            print("\n[SAMPLE GAME]")
            print(f"  {sample['away_team']} @ {sample['home_team']}")
            print(
                f"  Spread: {sample['spread']['away']:+.1f} ({sample['spread']['away_odds']:+d}) / {sample['spread']['home']:+.1f} ({sample['spread']['home_odds']:+d})"
            )
            print(
                f"  Total: {sample['total']['points']:.1f} (O{sample['total']['over_odds']:+d}/U{sample['total']['under_odds']:+d})"
            )
            if sample["moneyline"]["away"]:
                print(
                    f"  Moneyline: {sample['moneyline']['away']:+d} / {sample['moneyline']['home']:+d}"
                )

    # Summary
    print("\n" + "=" * 60)
    print(f"[SUCCESS] Total games scraped: {total_games}")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run edge detector: /edge-detector")
    print("  2. Generate betting card: /betting-card")


if __name__ == "__main__":
    asyncio.run(main())
