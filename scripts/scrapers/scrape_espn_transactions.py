#!/usr/bin/env python3
"""
ESPN NFL Transactions Scraper

CLI script to fetch NFL team roster transactions from ESPN. Captures all
roster changes including trades, signings, releases, waivers, injuries, etc.

Usage:
    # Get transactions for one team
    uv run python scripts/scrapers/scrape_espn_transactions.py --team buf

    # Get transactions for all 32 NFL teams
    uv run python scripts/scrapers/scrape_espn_transactions.py --all-teams

    # Get for multiple teams
    uv run python scripts/scrapers/scrape_espn_transactions.py --teams buf nyj ne

Examples:
    # Buffalo Bills only
    %(prog)s --team buf

    # All AFC East
    %(prog)s --teams buf nyj ne mia

    # Entire league
    %(prog)s --all-teams

    # Custom output directory
    %(prog)s --all-teams --output-dir custom/path
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.espn_transactions_client import ESPNTransactionsClient, NFL_TEAMS


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ESPN NFL Transactions Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get transactions for Buffalo Bills
  %(prog)s --team buf

  # Get all AFC East teams
  %(prog)s --teams buf nyj ne mia

  # Get all 32 teams
  %(prog)s --all-teams

  # Save to custom location
  %(prog)s --all-teams --output-dir transactions/nfl
        """,
    )

    # Team selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--team",
        type=str,
        help="Single team abbreviation (e.g., buf, nyj, ne)",
    )
    group.add_argument(
        "--teams",
        type=str,
        nargs="+",
        help="Multiple team abbreviations (e.g., buf nyj ne mia)",
    )
    group.add_argument(
        "--all-teams",
        action="store_true",
        help="Scrape all 32 NFL teams",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/espn/transactions/nfl"),
        help="Output directory. Default: output/espn/transactions/nfl",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (except errors)",
    )

    args = parser.parse_args()

    # Determine teams to scrape
    teams_to_scrape = []

    if args.team:
        teams_to_scrape = [args.team.lower()]
    elif args.teams:
        teams_to_scrape = [t.lower() for t in args.teams]
    elif args.all_teams:
        teams_to_scrape = sorted(NFL_TEAMS.keys())

    # Validate team abbreviations
    invalid_teams = [t for t in teams_to_scrape if t not in NFL_TEAMS]
    if invalid_teams:
        print(f"[ERROR] Invalid team abbreviations: {', '.join(invalid_teams)}")
        return 1

    # Initialize client
    client = ESPNTransactionsClient()
    await client.connect()

    try:
        if not args.quiet:
            print("[*] ESPN NFL Transactions Scraper")
            print("=" * 70)

        all_results = {}
        total_transactions = 0

        # Fetch transactions for each team
        for team_abbr in teams_to_scrape:
            try:
                if not args.quiet:
                    team_full = NFL_TEAMS[team_abbr]["full_name"]
                    print(f"[*] Fetching {team_full}...")

                result = await client.get_team_transactions(team_abbr)
                all_results[team_abbr] = result
                total_transactions += result["transaction_count"]

                if not args.quiet:
                    trans_count = result["transaction_count"]
                    print(f"    [OK] {trans_count} transactions found")
                    if trans_count > 0 and trans_count <= 3:
                        for trans in result["transactions"][:3]:
                            print(
                                f"         - {trans['player_name']}: "
                                f"{trans['transaction_type']}"
                            )

            except Exception as e:
                print(f"[ERROR] Failed to fetch {team_abbr}: {e}")
                all_results[team_abbr] = {"error": str(e), "transactions": []}

        # Save aggregated results
        if not args.quiet:
            print("\n[*] Saving results...")

        output_file = await client.save_transactions_json(
            all_results,
            args.output_dir,
        )

        if not args.quiet:
            print("\n" + "=" * 70)
            print("TRANSACTIONS SCRAPING COMPLETE")
            print("=" * 70)
            print(
                f"Teams scraped: {len([r for r in all_results.values() if 'error' not in r])}"
            )
            print(f"Total transactions: {total_transactions}")
            print(f"Saved to: {output_file}")

        return 0

    except KeyboardInterrupt:
        if not args.quiet:
            print("\n[INFO] Scraping interrupted by user")
        return 130

    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        await client.close()


if __name__ == "__main__":
    exit(asyncio.run(main()))
