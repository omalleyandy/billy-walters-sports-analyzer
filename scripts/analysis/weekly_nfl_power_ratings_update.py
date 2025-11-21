#!/usr/bin/env python3
"""
Weekly NFL Power Ratings Update Script

Implements Billy Walters' weekly power rating methodology:
1. Scrape current week NFL team statistics from NFL.com
2. Calculate offensive/defensive ratings from cumulative stats
3. Adjust for strength of schedule
4. Generate weekly power ratings
5. Save results for edge detection
6. Fallback to Massey ratings if NFL.com unavailable

Usage:
    python weekly_nfl_power_ratings_update.py --week 11 --season 2025
    python weekly_nfl_power_ratings_update.py --auto  # Auto-detect current week
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.nfl_stats_scraper import NFLStatsScraperClient
from walters_analyzer.valuation.nfl_power_ratings_builder import (
    NFLPowerRatingsBuilder,
)
from walters_analyzer.season_calendar import get_nfl_week

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def scrape_and_build_ratings(
    week: int,
    season: int,
    output_dir: str = "data/current",
    use_massey_fallback: bool = True,
) -> bool:
    """
    Complete workflow: Scrape stats + Build ratings

    Args:
        week: NFL week number (1-18)
        season: NFL season year
        output_dir: Directory for output files
        use_massey_fallback: Use Massey ratings if NFL.com fails

    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 80)
    logger.info("BILLY WALTERS NFL POWER RATINGS - WEEKLY UPDATE")
    logger.info(f"Week {week}, {season} Season")
    logger.info("=" * 80)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Step 1: Scrape NFL.com team statistics
    logger.info("\n[STEP 1] Scraping NFL.com team statistics...")
    scraper = NFLStatsScraperClient(output_dir=output_dir)

    try:
        stats = await scraper.scrape_all_teams(week=week, season=season)

        if not stats:
            logger.error("Failed to scrape team statistics from NFL.com")

            if use_massey_fallback:
                logger.warning("Falling back to Massey ratings...")
                return await use_massey_fallback_method(week, season, output_dir)

            return False

        # Save stats
        stats_file = scraper.save_stats(stats, week)
        logger.info(f"✓ Scraped {len(stats)} teams successfully")
        logger.info(f"✓ Saved stats to: {stats_file}")

    except Exception as e:
        logger.error(f"Error scraping NFL.com: {e}")

        if use_massey_fallback:
            logger.warning("Falling back to Massey ratings...")
            return await use_massey_fallback_method(week, season, output_dir)

        return False

    finally:
        await scraper.close()

    # Step 2: Build power ratings from stats
    logger.info("\n[STEP 2] Building power ratings from team statistics...")

    try:
        builder = NFLPowerRatingsBuilder(output_dir=f"{output_dir}/power_ratings")
        builder.load_team_stats(stats_file)
        builder.build_ratings_for_week(week=week, season=season)

        # Save ratings
        ratings_file = builder.save_ratings(week=week, season=season)
        logger.info(f"✓ Built ratings for {len(builder.power_ratings)} teams")
        logger.info(f"✓ Saved ratings to: {ratings_file}")

        # Print summary
        print()
        builder.print_ratings_summary()

        # Step 3: Generate comparison report
        logger.info("\n[STEP 3] Generating comparison report...")
        generate_comparison_report(builder, week, season, output_dir)

        logger.info("\n" + "=" * 80)
        logger.info("SUCCESS: Power ratings updated for Week %d", week)
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Error building power ratings: {e}")
        return False


async def use_massey_fallback_method(week: int, season: int, output_dir: str) -> bool:
    """
    Fallback to Massey ratings when NFL.com unavailable

    Args:
        week: NFL week number
        season: NFL season year
        output_dir: Directory for output files

    Returns:
        True if successful, False otherwise
    """
    logger.info("\n[FALLBACK] Using Massey composite ratings...")

    try:
        # Import Massey scraper
        from data.massey_scraper import MasseyRatingsScraper

        scraper = MasseyRatingsScraper()
        massey_ratings = await scraper.scrape_nfl_ratings()

        if not massey_ratings:
            logger.error("Failed to scrape Massey ratings")
            return False

        # Save Massey ratings in compatible format
        output_file = Path(output_dir) / f"nfl_power_ratings_week{week}_massey.json"

        with open(output_file, "w") as f:
            import json

            json.dump(massey_ratings, f, indent=2)

        logger.info(f"✓ Saved Massey ratings to: {output_file}")
        logger.info("✓ Fallback successful - using Massey composite ratings")

        return True

    except Exception as e:
        logger.error(f"Error with Massey fallback: {e}")
        return False


def generate_comparison_report(
    builder: NFLPowerRatingsBuilder, week: int, season: int, output_dir: str
):
    """
    Generate report comparing power ratings to Vegas lines

    Args:
        builder: Power ratings builder with calculated ratings
        week: Week number
        season: Season year
        output_dir: Output directory
    """
    try:
        output_file = Path(output_dir) / f"power_ratings_report_week{week}_{season}.txt"

        with open(output_file, "w") as f:
            f.write("=" * 100 + "\n")
            f.write("NFL POWER RATINGS COMPARISON REPORT\n")
            f.write(f"Week {week}, {season} Season\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 100 + "\n\n")

            # Sort teams by power rating
            sorted_ratings = sorted(
                builder.power_ratings.items(),
                key=lambda x: x[1].power_rating,
                reverse=True,
            )

            f.write("TEAM POWER RATINGS (Ranked by Overall Power)\n")
            f.write("-" * 100 + "\n")
            f.write(
                f"{'Rank':<5} {'Team':<25} {'Power':<8} {'Offensive':<10} "
                f"{'Defensive':<10} {'Record':<10}\n"
            )
            f.write("-" * 100 + "\n")

            for i, (team_abbr, rating) in enumerate(sorted_ratings, 1):
                f.write(
                    f"{i:<5} {rating.team:<25} {rating.power_rating:>6.2f}  "
                    f"{rating.offensive_rating:>8.2f}  "
                    f"{rating.defensive_rating:>8.2f}  "
                    f"{rating.record:<10}\n"
                )

            f.write("=" * 100 + "\n")
            f.write("\nNOTES:\n")
            f.write("- Higher power rating = stronger overall team\n")
            f.write("- Higher offensive rating = better scoring ability\n")
            f.write(
                "- LOWER defensive rating = better defense (fewer points allowed)\n"
            )
            f.write("- Use power ratings to predict spreads: Diff + HFA (2.5 pts)\n")
            f.write("=" * 100 + "\n")

        logger.info(f"✓ Saved comparison report to: {output_file}")

    except Exception as e:
        logger.error(f"Error generating comparison report: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Weekly NFL Power Ratings Update (Billy Walters Methodology)"
    )

    parser.add_argument(
        "--week",
        type=int,
        help="NFL week number (1-18, default: auto-detect current week)",
    )

    parser.add_argument(
        "--season", type=int, default=2025, help="NFL season year (default: 2025)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/current",
        help="Output directory (default: data/current)",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-detect current week (overrides --week)",
    )

    parser.add_argument(
        "--no-massey-fallback",
        action="store_true",
        help="Disable Massey ratings fallback if NFL.com fails",
    )

    args = parser.parse_args()

    # Determine week number
    if args.auto:
        week = get_nfl_week()
        if week is None:
            logger.error("Cannot auto-detect week (offseason or playoffs)")
            logger.info("Please specify --week manually")
            sys.exit(1)
        logger.info(f"Auto-detected current week: {week}")
    elif args.week:
        week = args.week
    else:
        logger.error("Must specify either --week or --auto")
        sys.exit(1)

    # Run update
    use_fallback = not args.no_massey_fallback

    success = asyncio.run(
        scrape_and_build_ratings(
            week=week,
            season=args.season,
            output_dir=args.output_dir,
            use_massey_fallback=use_fallback,
        )
    )

    if success:
        print("\n✓ COMPLETE: Power ratings updated successfully")
        print(f"  Week: {week}, Season: {args.season}")
        print(f"  Output: {args.output_dir}/")
        sys.exit(0)
    else:
        print("\n✗ FAILED: Power ratings update failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
