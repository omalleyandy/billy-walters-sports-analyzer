#!/usr/bin/env python3
"""
Overtime.ag Scraper Example

Demonstrates how to use the Overtime NFL scraper and data converter.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.overtime_pregame_nfl_scraper import OvertimeNFLScraper
from data.overtime_data_converter import convert_overtime_to_walters


async def basic_scrape_example():
    """Basic example: Scrape NFL odds"""
    print("=" * 70)
    print("Example 1: Basic NFL Odds Scraping")
    print("=" * 70)

    # Create scraper
    scraper = OvertimeNFLScraper(
        headless=False,  # Show browser for demo
        output_dir="examples/output",
    )

    # Scrape odds
    result = await scraper.scrape()

    # Display results
    print(f"\n✓ Scraped {result['summary']['total_games']} game entries")
    print(f"✓ {result['summary']['unique_matchups']} unique matchups")

    # Show first game
    if result["games"]:
        game = result["games"][0]
        print("\nFirst Game:")
        print(f"  {game['visitor']['teamName']} @ {game['home']['teamName']}")
        print(f"  Date: {game['game_date']} at {game['game_time']}")
        print(f"  Visitor Spread: {game['visitor']['spread']}")
        print(f"  Home Spread: {game['home']['spread']}")
        print(f"  Total: {game['visitor']['total']} / {game['home']['total']}")

    return result


async def convert_data_example():
    """Example 2: Scrape and convert to Walters format"""
    print("\n" + "=" * 70)
    print("Example 2: Scraping and Converting to Walters Format")
    print("=" * 70)

    # Scrape data
    scraper = OvertimeNFLScraper(headless=True, output_dir="examples/output")

    overtime_data = await scraper.scrape()

    # Convert to Walters format
    walters_data = convert_overtime_to_walters(overtime_data)

    # Display conversion results
    print("\n✓ Conversion Complete")
    print(f"  - Total converted: {walters_data['summary']['total_converted']}")
    print(f"  - Conversion rate: {walters_data['summary']['conversion_rate']}")

    # Show first converted game
    if walters_data["games"]:
        game = walters_data["games"][0]
        print("\nFirst Converted Game:")
        print(f"  ID: {game.get('game_id', 'N/A')}")
        print(
            f"  Away: {game['away_team']['name']} ({game['away_team']['abbreviation']})"
        )
        print(
            f"  Home: {game['home_team']['name']} ({game['home_team']['abbreviation']})"
        )
        if game.get("odds"):
            print(f"  Spread: {game['odds']['spread']} ({game['odds']['spread_odds']})")
            print(
                f"  Total: {game['odds']['over_under']} ({game['odds']['total_odds']})"
            )

    return walters_data


async def save_to_files_example():
    """Example 3: Scrape and save to files"""
    print("\n" + "=" * 70)
    print("Example 3: Scraping and Saving to Files")
    print("=" * 70)

    # Create output directory
    output_dir = Path("examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Scrape data
    scraper = OvertimeNFLScraper(headless=True, output_dir=str(output_dir))

    overtime_data = await scraper.scrape()

    # Save raw data
    raw_file = output_dir / "overtime_raw.json"
    with open(raw_file, "w") as f:
        json.dump(overtime_data, f, indent=2, default=str)

    print(f"✓ Raw data saved to: {raw_file}")

    # Convert and save
    walters_data = convert_overtime_to_walters(overtime_data)

    walters_file = output_dir / "overtime_walters.json"
    with open(walters_file, "w") as f:
        json.dump(walters_data, f, indent=2, default=str)

    print(f"✓ Walters data saved to: {walters_file}")

    # Create summary file
    summary_file = output_dir / "summary.txt"
    with open(summary_file, "w") as f:
        f.write("OVERTIME.AG SCRAPE SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Timestamp: {overtime_data['scrape_metadata']['timestamp']}\n")
        f.write(f"Total Games: {overtime_data['summary']['total_games']}\n")
        f.write(f"Unique Matchups: {overtime_data['summary']['unique_matchups']}\n")
        f.write(f"Periods: {', '.join(overtime_data['summary']['periods'])}\n")
        f.write(f"\nConversion Rate: {walters_data['summary']['conversion_rate']}\n")

        if overtime_data.get("account_info"):
            f.write("\nAccount Info:\n")
            f.write(f"  Balance: {overtime_data['account_info']['balance']}\n")
            f.write(
                f"  Available: {overtime_data['account_info']['available_balance']}\n"
            )
            f.write(f"  Pending: {overtime_data['account_info']['pending']}\n")

    print(f"✓ Summary saved to: {summary_file}")


async def analyze_games_example():
    """Example 4: Scrape and analyze games"""
    print("\n" + "=" * 70)
    print("Example 4: Scraping and Analyzing Games")
    print("=" * 70)

    # Scrape data
    scraper = OvertimeNFLScraper(headless=True)
    overtime_data = await scraper.scrape()

    # Convert to Walters format
    walters_data = convert_overtime_to_walters(overtime_data)

    # Simple analysis
    print("\nGAME ANALYSIS:")
    print("-" * 70)

    for game in walters_data["games"]:
        away = game["away_team"]["abbreviation"]
        home = game["home_team"]["abbreviation"]

        if game.get("odds"):
            odds = game["odds"]
            spread = odds["spread"]
            total = odds["over_under"]

            print(f"\n{away} @ {home}")
            print(f"  Spread: {away} {'+' if spread > 0 else ''}{spread}")
            print(f"  Total: {total}")

            # Simple value indicators
            if abs(spread) > 10:
                print("  ⚠️  Large spread - potential blowout")

            if total < 40:
                print("  🏈 Low-scoring game expected")
            elif total > 50:
                print("  🔥 High-scoring game expected")


async def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("OVERTIME.AG SCRAPER EXAMPLES")
    print("=" * 70)
    print("\nThis script demonstrates various uses of the Overtime NFL scraper.\n")

    try:
        # Example 1: Basic scraping
        await basic_scrape_example()

        # Example 2: Conversion
        await convert_data_example()

        # Example 3: Saving to files
        await save_to_files_example()

        # Example 4: Analysis
        await analyze_games_example()

        print("\n" + "=" * 70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nCheck the examples/output directory for saved files.")

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
