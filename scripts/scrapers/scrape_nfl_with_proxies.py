"""
CLI: Scrape NFL Game Stats with ProxyScrape Residential Proxies

Enhanced scraper that uses rotating residential proxies to bypass
bot detection and rate limiting.

Usage:
    # Using rotating proxies (default)
    python scrape_nfl_with_proxies.py

    # Using random proxy selection
    python scrape_nfl_with_proxies.py --proxy-strategy random

    # Test proxies first
    python scrape_nfl_with_proxies.py --test-proxies 5

    # Show proxy health
    python scrape_nfl_with_proxies.py --show-proxy-health

    # Specific week
    python scrape_nfl_with_proxies.py --year 2025 --week reg-13

    # With retries
    python scrape_nfl_with_proxies.py --max-retries 5

    # Show browser
    python scrape_nfl_with_proxies.py --headless false
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.nfl_game_stats_client_with_proxies import NFLGameStatsClientWithProxies

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape NFL.com game stats with rotating proxies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape_nfl_with_proxies.py
  python scrape_nfl_with_proxies.py --year 2025 --week reg-13
  python scrape_nfl_with_proxies.py --proxy-strategy random
  python scrape_nfl_with_proxies.py --test-proxies 5
  python scrape_nfl_with_proxies.py --show-proxy-health
  python scrape_nfl_with_proxies.py --headless false --verbose
        """,
    )

    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="NFL season year (default: 2025)",
    )

    parser.add_argument(
        "--week",
        type=str,
        default="reg-12",
        help="Week identifier (reg-12, reg-13, post-1, etc.)",
    )

    parser.add_argument(
        "--headless",
        type=str,
        default="true",
        choices=["true", "false"],
        help="Run browser in headless mode (default: true)",
    )

    parser.add_argument(
        "--proxy-strategy",
        type=str,
        default="rotate",
        choices=["rotate", "random"],
        help="Proxy selection strategy (default: rotate)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retries per page (default: 3)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output/nfl_game_stats",
        help="Output directory for JSON files",
    )

    parser.add_argument(
        "--test-proxies",
        type=int,
        default=0,
        help="Test N proxies and exit (0 = skip testing)",
    )

    parser.add_argument(
        "--show-proxy-health",
        action="store_true",
        help="Show proxy system health and exit",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Check for ProxyScrape credentials
    username = os.getenv("PROXYSCRAPE_USERNAME")
    password = os.getenv("PROXYSCRAPE_PASSWORD")

    if not username or not password:
        logger.warning(
            "No ProxyScrape credentials found. Set environment variables:\n"
            "    export PROXYSCRAPE_USERNAME=your-username\n"
            "    export PROXYSCRAPE_PASSWORD=your-password"
        )
        logger.info("Proceeding without proxies (will use direct connection)")
    else:
        logger.info(
            "Using ProxyScrape direct mode (20 rotating residential US proxies)"
        )

    # Parse headless flag
    headless = args.headless.lower() == "true"

    logger.info("Starting NFL game stats scraper with proxies")
    logger.info(f"  Year: {args.year}")
    logger.info(f"  Week: {args.week}")
    logger.info(f"  Headless: {headless}")
    logger.info(f"  Proxy strategy: {args.proxy_strategy}")
    logger.info(f"  Max retries: {args.max_retries}")
    logger.info(f"  Output: {args.output}")

    client = NFLGameStatsClientWithProxies(
        headless=headless,
        proxyscrape_username=username,
        proxyscrape_password=password,
        use_proxies=bool(username and password),
        proxy_rotation_strategy=args.proxy_strategy,
    )

    try:
        # Test proxies if requested
        if args.test_proxies > 0:
            logger.info(f"Testing {args.test_proxies} proxies...")
            await client.connect()

            results = await client.test_proxies(limit=args.test_proxies)

            print("\n" + "=" * 70)
            print("PROXY TEST RESULTS")
            print("=" * 70)

            working = 0
            for proxy, is_working in results.items():
                status = "[OK]" if is_working else "[FAIL]"
                print(f"{status} {proxy}")
                if is_working:
                    working += 1

            print(f"\n{working}/{len(results)} proxies working")
            return 0

        # Show proxy health if requested
        if args.show_proxy_health:
            await client.connect()
            health = await client.get_proxy_health()

            print("\n" + "=" * 70)
            print("PROXY HEALTH REPORT")
            print("=" * 70)

            for key, value in health.items():
                print(f"{key}: {value}")

            return 0

        # Fetch stats for the week
        await client.connect()
        logger.info(f"Fetching stats for {args.year} week {args.week}...")

        stats = await client.get_week_stats(
            year=args.year,
            week=args.week,
            max_retries=args.max_retries,
        )

        if not stats.get("games"):
            logger.warning("No game stats were collected")
            return 1

        # Export results
        logger.info(f"Collected stats for {len(stats['games'])} games")
        filepath = await client.export_stats(stats, args.output)

        logger.info(f"Stats exported to {filepath}")

        # Print summary
        print("\n" + "=" * 70)
        print("NFL GAME STATS SCRAPE COMPLETE (WITH PROXIES)")
        print("=" * 70)
        print(f"Games collected: {len(stats['games'])}")
        print(f"Output file: {filepath}")
        print(f"Proxy info: {stats['proxy_info']}")

        for game in stats["games"]:
            if "away_team" in game and "home_team" in game:
                away = game["away_team"]
                home = game["home_team"]
                print(f"  - {away} @ {home}")

        return 0

    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        return 1

    finally:
        await client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
