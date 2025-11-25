#!/usr/bin/env python3
"""
Scrape Action Network Live Odds using Playwright Browser Automation.

Fetches NFL and NCAAF odds data from Action Network using the ActionNetworkClient.
Includes login authentication, rate limiting, retry logic, and data validation.

Usage:
    # Scrape NFL only
    uv run python scripts/scrapers/scrape_action_network_live.py --nfl

    # Scrape NCAAF only
    uv run python scripts/scrapers/scrape_action_network_live.py --ncaaf

    # Scrape both leagues (default if neither specified)
    uv run python scripts/scrapers/scrape_action_network_live.py

    # Debug mode (visible browser)
    uv run python scripts/scrapers/scrape_action_network_live.py --nfl --no-headless

    # Quiet mode (minimal output)
    uv run python scripts/scrapers/scrape_action_network_live.py --ncaaf --quiet

Author: Claude Code
Date: 2025-11-25
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.action_network_client import ActionNetworkClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def save_odds_to_file(
    odds: list[dict], league: str, output_dir: str = "output/action_network"
) -> Path | None:
    """
    Save odds data to timestamped JSON file.

    Args:
        odds: List of game odds dictionaries
        league: League name (nfl or ncaaf)
        output_dir: Output directory path

    Returns:
        Path to saved file or None if no games
    """
    if not odds:
        return None

    # Create output directory structure: output/action_network/{league}/games/
    output_path = Path(output_dir) / league / "games"
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"odds_{league}_{timestamp}.json"
    file_path = output_path / filename

    # Save to file
    with open(file_path, "w") as f:
        json.dump(odds, f, indent=2)

    return file_path


async def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape Action Network live odds using Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  uv run python scripts/scrapers/scrape_action_network_live.py --nfl\n"
            "  uv run python scripts/scrapers/scrape_action_network_live.py --ncaaf\n"
            "  uv run python scripts/scrapers/scrape_action_network_live.py --nfl --ncaaf\n"
            "  uv run python scripts/scrapers/scrape_action_network_live.py --nfl --no-headless"
        ),
    )

    parser.add_argument("--nfl", action="store_true", help="Scrape NFL games")
    parser.add_argument("--ncaaf", action="store_true", help="Scrape NCAAF games")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/action_network",
        help="Output directory (default: output/action_network)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (debugging)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retry attempts (default: 3)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=2.0,
        help="Rate limit delay between requests in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output (no progress messages)",
    )

    args = parser.parse_args()

    # Default to both leagues if neither specified
    if not args.nfl and not args.ncaaf:
        args.nfl = True
        args.ncaaf = True

    # Configure logging verbosity
    if args.quiet:
        logging.getLogger("action_network_client").setLevel(logging.WARNING)
        logging.getLogger().setLevel(logging.WARNING)

    if not args.quiet:
        print("=" * 70)
        print("ACTION NETWORK LIVE ODDS SCRAPER")
        print("=" * 70)

    client = ActionNetworkClient(
        headless=not args.no_headless,
        rate_limit_delay=args.rate_limit,
    )

    total_games = 0
    saved_files = []

    try:
        # Connect and login
        if not args.quiet:
            print("\n[*] Connecting to Action Network...")
        await client.connect()
        if not args.quiet:
            print("[OK] Login successful")

        # Scrape NFL if requested
        if args.nfl:
            if not args.quiet:
                print("\n[*] Scraping NFL odds...")
            nfl_odds = await client.fetch_odds("NFL", max_retries=args.max_retries)
            total_games += len(nfl_odds)

            if not args.quiet:
                print(f"[OK] Found {len(nfl_odds)} NFL games")

            # Save to file
            file_path = save_odds_to_file(nfl_odds, "nfl", args.output_dir)
            if file_path:
                saved_files.append(file_path)
                if not args.quiet:
                    print(f"[SAVED] {file_path.relative_to('.')}")

            # Show sample game
            if nfl_odds and not args.quiet:
                sample = nfl_odds[0]
                print("\n[SAMPLE NFL GAME]")
                print(f"  {sample['away_team']} @ {sample['home_team']}")
                print(f"  Spread: {sample['spread']} ({sample['spread_odds']})")
                print(f"  O/U: {sample['over_under']} ({sample['total_odds']})")
                print(
                    f"  Moneyline: {sample['moneyline_away']} / {sample['moneyline_home']}"
                )

        # Scrape NCAAF if requested
        if args.ncaaf:
            if not args.quiet:
                print("\n[*] Scraping NCAAF odds...")
            ncaaf_odds = await client.fetch_odds("NCAAF", max_retries=args.max_retries)
            total_games += len(ncaaf_odds)

            if not args.quiet:
                print(f"[OK] Found {len(ncaaf_odds)} NCAAF games")

            # Save to file
            file_path = save_odds_to_file(ncaaf_odds, "ncaaf", args.output_dir)
            if file_path:
                saved_files.append(file_path)
                if not args.quiet:
                    print(f"[SAVED] {file_path.relative_to('.')}")

            # Show sample game
            if ncaaf_odds and not args.quiet:
                sample = ncaaf_odds[0]
                print("\n[SAMPLE NCAAF GAME]")
                print(f"  {sample['away_team']} @ {sample['home_team']}")
                print(f"  Spread: {sample['spread']} ({sample['spread_odds']})")
                print(f"  O/U: {sample['over_under']} ({sample['total_odds']})")
                print(
                    f"  Moneyline: {sample['moneyline_away']} / {sample['moneyline_home']}"
                )

        if not args.quiet:
            print("\n" + "=" * 70)
            print(f"[OK] Scraping complete: {total_games} total games")
            print("=" * 70)

        return 0

    except KeyboardInterrupt:
        if not args.quiet:
            print("\n[WARNING] Scraping interrupted by user")
        return 130

    except Exception as e:
        print(f"\n[ERROR] Scraping failed: {e}")
        logger.exception("Full exception traceback:")
        return 1

    finally:
        await client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
