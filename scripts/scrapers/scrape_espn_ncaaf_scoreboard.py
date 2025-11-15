"""
ESPN NCAAF Scoreboard Scraper

CLI script to fetch NCAAF scoreboard data mirroring Chrome DevTools workflow.

Usage:
    # Current week scoreboard (FBS only)
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py

    # Specific week (FBS + FCS)
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py --week 12 --groups 80 81

    # Specific date (rivalry week, 400 game limit)
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py --date 20251129 --limit 400

    # With complete game data (summary + plays + win prob)
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py --week 12 --complete

    # Save as parquet (normalized tables)
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py --week 12 --parquet

    # Verify data quality
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py --week 12 --verify

Examples:
    # Get rivalry week games
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py --date 20251129 --limit 400

    # Monitor live games (polls every 15 seconds like ESPN)
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py --week 12 --monitor --interval 15

    # Get complete CFP data
    uv run python scripts/scrape_espn_ncaaf_scoreboard.py --groups 55 --complete --parquet
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.espn_ncaaf_scoreboard_client import ESPNNCAAFScoreboardClient
from data.espn_ncaaf_normalizer import ESPNNCAAFNormalizer


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ESPN NCAAF Scoreboard Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Current week FBS games
  %(prog)s

  # Specific week with verification
  %(prog)s --week 12 --verify

  # Rivalry week (high game count)
  %(prog)s --date 20251129 --limit 400 --parquet

  # Monitor live games
  %(prog)s --week 12 --monitor --interval 15

  # Complete game data (all APIs)
  %(prog)s --week 12 --complete --parquet

  # CFP games only
  %(prog)s --groups 55 --complete
        """,
    )

    # Primary parameters (mirroring DevTools)
    parser.add_argument(
        "--week",
        type=int,
        help="Week number (1-15 regular, 16+ postseason)",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date in YYYYMMDD format (alternative to --week)",
    )
    parser.add_argument(
        "--groups",
        type=int,
        nargs="+",
        default=[80],
        help="Group IDs (80=FBS, 81=FCS, 55=CFP). Default: 80",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=400,
        help="Max games to return. Default: 400",
    )
    parser.add_argument(
        "--tz",
        type=str,
        default="America/New_York",
        help="Timezone for game times. Default: America/New_York",
    )

    # Data collection options
    parser.add_argument(
        "--complete",
        action="store_true",
        help="Fetch complete game data (summary + plays + win prob)",
    )
    parser.add_argument(
        "--parquet",
        action="store_true",
        help="Save normalized data as parquet tables",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification checklist on scoreboard data",
    )

    # Monitoring options
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor live games (continuous polling)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Polling interval in seconds (for --monitor). Default: 15",
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="Monitoring duration in seconds (for --monitor). Runs indefinitely if not set",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/espn/scoreboard/ncaaf"),
        help="Output directory for raw JSON. Default: output/espn/scoreboard/ncaaf",
    )
    parser.add_argument(
        "--parquet-dir",
        type=Path,
        default=Path("data/normalized/espn"),
        help="Output directory for parquet. Default: data/normalized/espn",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (except errors)",
    )

    args = parser.parse_args()

    # Initialize client
    client = ESPNNCAAFScoreboardClient()
    await client.connect()

    try:
        if args.monitor:
            await monitor_live_games(client, args)
        else:
            await fetch_scoreboard_once(client, args)

    finally:
        await client.close()


async def fetch_scoreboard_once(client: ESPNNCAAFScoreboardClient, args):
    """Fetch scoreboard data once."""
    if not args.quiet:
        print("[*] Fetching ESPN NCAAF scoreboard...")
        if args.week:
            print(f"    Week: {args.week}")
        if args.date:
            print(f"    Date: {args.date}")
        print(f"    Groups: {args.groups}")
        print(f"    Limit: {args.limit}")

    # Fetch scoreboard for each group
    all_scoreboards = []

    for group in args.groups:
        scoreboard = await client.get_scoreboard(
            week=args.week,
            date=args.date,
            groups=group,
            limit=args.limit,
            tz=args.tz,
        )
        all_scoreboards.append(scoreboard)

    # Combine scoreboards if multiple groups
    if len(all_scoreboards) == 1:
        combined_scoreboard = all_scoreboards[0]
    else:
        combined_scoreboard = combine_scoreboards(all_scoreboards)

    # Save raw JSON
    output_file = await client.save_scoreboard_raw(
        combined_scoreboard,
        args.output_dir,
        date=args.date,
    )

    if not args.quiet:
        event_count = len(combined_scoreboard.get("events", []))
        print(f"[OK] Saved scoreboard: {output_file}")
        print(f"     Events: {event_count}")

    # Verify data quality
    if args.verify:
        if not args.quiet:
            print("\n[*] Verifying scoreboard data...")

        verification = client.verify_scoreboard_response(combined_scoreboard)

        if not args.quiet:
            print(f"    Valid: {verification['valid']}")
            print(f"    Events: {verification['event_count']}")
            print(f"    Season Type: {verification['season_type']}")
            print(f"    Week: {verification['week_number']}")

            if "providers" in verification:
                print(f"    Odds Providers: {', '.join(verification['providers'])}")

            if verification["warnings"]:
                print("    Warnings:")
                for warning in verification["warnings"]:
                    print(f"      - {warning}")

            if verification["errors"]:
                print("    Errors:")
                for error in verification["errors"]:
                    print(f"      - {error}")

    # Fetch complete game data
    if args.complete:
        if not args.quiet:
            print("\n[*] Fetching complete game data...")

        events = combined_scoreboard.get("events", [])
        game_data_list = []

        for i, event in enumerate(events, 1):
            event_id = event["id"]

            if not args.quiet:
                print(f"    [{i}/{len(events)}] Fetching {event['name']}...")

            game_data = await client.get_complete_game_data(event_id)
            game_data_list.append(game_data)

            # Save individual game data
            await client.save_game_data_raw(
                game_data,
                args.output_dir,
                date=args.date,
            )

        if not args.quiet:
            print(f"[OK] Fetched complete data for {len(game_data_list)} games")

    # Save as parquet
    if args.parquet:
        if not args.quiet:
            print("\n[*] Normalizing to parquet...")

        normalizer = ESPNNCAAFNormalizer(args.parquet_dir)

        events_df, competitors_df, odds_df = normalizer.normalize_scoreboard(
            combined_scoreboard
        )

        parquet_paths = normalizer.save_parquet(
            events_df,
            competitors_df,
            odds_df,
            date=args.date,
        )

        if not args.quiet:
            print("[OK] Saved parquet tables:")
            print(f"     Events: {parquet_paths['events']} ({len(events_df)} rows)")
            print(
                f"     Competitors: {parquet_paths['competitors']} ({len(competitors_df)} rows)"
            )
            print(f"     Odds: {parquet_paths['odds']} ({len(odds_df)} rows)")


async def monitor_live_games(client: ESPNNCAAFScoreboardClient, args):
    """Monitor live games with continuous polling."""
    if not args.quiet:
        print("[*] Starting live game monitor...")
        print(f"    Polling interval: {args.interval} seconds")
        if args.duration:
            print(f"    Duration: {args.duration} seconds")
        else:
            print("    Duration: indefinite (Ctrl+C to stop)")

    start_time = datetime.now()
    iteration = 0

    try:
        while True:
            iteration += 1

            if not args.quiet:
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"\n[*] Poll #{iteration} (elapsed: {elapsed:.0f}s)")

            # Fetch scoreboard
            await fetch_scoreboard_once(client, args)

            # Check duration limit
            if args.duration:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= args.duration:
                    if not args.quiet:
                        print(f"\n[OK] Monitoring complete ({elapsed:.0f}s)")
                    break

            # Sleep until next poll
            await asyncio.sleep(args.interval)

    except KeyboardInterrupt:
        if not args.quiet:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"\n[OK] Monitoring stopped ({iteration} polls, {elapsed:.0f}s)")


def combine_scoreboards(scoreboards: list[dict]) -> dict:
    """
    Combine multiple scoreboard responses (e.g., FBS + FCS).

    Args:
        scoreboards: List of scoreboard API responses

    Returns:
        Combined scoreboard dictionary
    """
    if not scoreboards:
        return {}

    # Use first scoreboard as base
    combined = scoreboards[0].copy()

    # Combine events from all scoreboards
    all_events = []
    for scoreboard in scoreboards:
        all_events.extend(scoreboard.get("events", []))

    combined["events"] = all_events

    return combined


if __name__ == "__main__":
    asyncio.run(main())
