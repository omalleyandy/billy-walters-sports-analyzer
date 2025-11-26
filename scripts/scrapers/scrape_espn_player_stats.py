#!/usr/bin/env python3
"""
ESPN Player Stats Scraper

CLI script to fetch NFL and NCAAF player statistics leaders from ESPN's
public statistics API. Captures league-wide leaders across all stat categories.

Usage:
    # Get all NFL stat leaders
    uv run python scripts/scrapers/scrape_espn_player_stats.py --league nfl

    # Get all NCAAF stat leaders
    uv run python scripts/scrapers/scrape_espn_player_stats.py --league ncaaf

    # Get specific stat category (NFL)
    uv run python scripts/scrapers/scrape_espn_player_stats.py --league nfl --stat passingYards

    # Save leaders only (extracted/simplified format)
    uv run python scripts/scrapers/scrape_espn_player_stats.py --league nfl --extract-leaders

    # Both leagues
    uv run python scripts/scrapers/scrape_espn_player_stats.py --league all

Examples:
    # Get NFL passing leaders (top 50)
    %(prog)s --league nfl --stat passingYards

    # Get NCAAF rushing leaders
    %(prog)s --league ncaaf --stat rushingYards

    # Save both raw and extracted leaders
    %(prog)s --league nfl --extract-leaders

    # Get all stats and extract leaders
    %(prog)s --league all --extract-leaders
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.espn_player_stats_client import ESPNPlayerStatsClient


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ESPN Player Stats Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get all NFL stat leaders
  %(prog)s --league nfl

  # Get NCAAF passing leaders
  %(prog)s --league ncaaf --stat passingYards

  # Save extracted leaders (cleaner format)
  %(prog)s --league nfl --extract-leaders

  # Get stats for both leagues
  %(prog)s --league all
        """,
    )

    # Primary parameters
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf", "all"],
        required=True,
        help="League to scrape (nfl, ncaaf, or all)",
    )
    parser.add_argument(
        "--stat",
        type=str,
        help="Specific stat category (e.g., passingYards, rushingYards, tackles)",
    )
    parser.add_argument(
        "--extract-leaders",
        action="store_true",
        help="Save extracted leaders in simplified format",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/espn/player_stats"),
        help="Output directory for raw JSON. Default: output/espn/player_stats",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (except errors)",
    )

    args = parser.parse_args()

    # Initialize client
    client = ESPNPlayerStatsClient()
    await client.connect()

    try:
        results = {"nfl": None, "ncaaf": None}

        # Determine which leagues to scrape
        leagues = ["nfl", "ncaaf"] if args.league == "all" else [args.league]

        for league in leagues:
            if not args.quiet:
                print(f"[*] Fetching {league.upper()} player stats...")

            try:
                # Fetch stats
                if league == "nfl":
                    stats_data = await client.get_nfl_stats(args.stat)
                else:
                    stats_data = await client.get_ncaaf_stats(args.stat)

                # Save raw JSON
                output_league_dir = args.output_dir / league
                raw_file = await client.save_stats_json(
                    stats_data,
                    output_league_dir,
                    league=league,
                )

                if not args.quiet:
                    category_count = len(
                        stats_data.get("stats", {}).get("categories", [])
                    )
                    print(f"[OK] Saved raw stats: {raw_file}")
                    print(f"     Categories: {category_count}")

                # Extract and save leaders if requested
                if args.extract_leaders:
                    if not args.quiet:
                        print(f"[*] Extracting stat leaders...")

                    leaders = client.extract_stat_leaders(stats_data)

                    leaders_file = await client.save_stats_leaders_json(
                        leaders,
                        output_league_dir,
                        league=league,
                    )

                    if not args.quiet:
                        print(f"[OK] Saved extracted leaders: {leaders_file}")
                        print(f"     Players: {len(leaders)}")

                        # Show sample leaders by category
                        categories = {}
                        for leader in leaders:
                            cat = leader["stat_category"]
                            if cat not in categories:
                                categories[cat] = []
                            categories[cat].append(leader)

                        print(f"     Categories: {len(categories)}")
                        for cat in sorted(categories.keys())[:3]:
                            top_player = categories[cat][0]
                            print(
                                f"       - {top_player['stat_category_display']}: "
                                f"{top_player['player_name']} "
                                f"({top_player['team_abbr']}) - "
                                f"{top_player['displayValue']}"
                            )

                results[league] = {
                    "success": True,
                    "raw_file": str(raw_file),
                    "leaders": len(leaders) if args.extract_leaders else 0,
                }

            except Exception as e:
                print(f"[ERROR] {league.upper()} stats scraping failed: {e}")
                results[league] = {"success": False, "error": str(e)}

        # Print summary
        if not args.quiet:
            print("\n" + "=" * 70)
            print("PLAYER STATS SCRAPING COMPLETE")
            print("=" * 70)

            for league, result in results.items():
                if result is None:
                    continue
                if result.get("success"):
                    print(f"{league.upper()}: Success - {result['raw_file']}")
                    if result.get("leaders") > 0:
                        print(f"         - {result['leaders']} extracted leaders")
                else:
                    print(f"{league.upper()}: FAILED - {result.get('error')}")

        # Return exit code
        if all(r.get("success", False) for r in results.values() if r is not None):
            return 0
        else:
            return 1

    finally:
        await client.close()


if __name__ == "__main__":
    exit(asyncio.run(main()))
