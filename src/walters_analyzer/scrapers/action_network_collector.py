#!/usr/bin/env python3
"""
Action Network Automated Data Collector

Runs periodic scraping of Action Network odds data for the Billy Walters
betting system. Designed to be run as a background process or scheduled task.

Features:
- Configurable scrape intervals
- Multiple league support (NFL, NCAAF)
- Data retention and cleanup
- Error recovery with exponential backoff
- Logging with rotation

Usage:
    # Run continuously (scrapes every 4 hours)
    python action_network_collector.py --continuous

    # Single scrape
    python action_network_collector.py --once

    # Custom interval (in minutes)
    python action_network_collector.py --continuous --interval 120

For Windows Task Scheduler:
    - Program: python
    - Arguments: action_network_collector.py --once
    - Schedule: Every 4 hours during betting windows
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from walters_analyzer.scrapers.action_network_scraper import ActionNetworkScraper
except ImportError:
    # Fallback for direct execution
    from action_network_scraper import ActionNetworkScraper

# Configure logging
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "action_network_collector.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ActionNetworkCollector")


class ActionNetworkCollector:
    """
    Automated collector for Action Network betting data.

    Manages periodic scraping, data storage, and error recovery.
    """

    # Default settings
    DEFAULT_INTERVAL_MINUTES = 240  # 4 hours
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 60  # seconds

    # Leagues to scrape
    LEAGUES = ["nfl", "ncaaf"]  # NFL and College Football

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
        headless: bool = True,
    ):
        """
        Initialize collector.

        Args:
            data_dir: Directory for storing scraped data
            interval_minutes: Minutes between scrapes
            headless: Run browser in headless mode
        """
        self.data_dir = (
            Path(data_dir)
            if data_dir
            else Path(__file__).parent.parent.parent.parent / "data" / "action_network"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.interval_minutes = interval_minutes
        self.headless = headless
        self.scraper: Optional[ActionNetworkScraper] = None

        # State tracking
        self.last_scrape: Optional[datetime] = None
        self.scrape_count = 0
        self.error_count = 0

        # Load state if exists
        self._load_state()

    def _state_file(self) -> Path:
        """Get path to state file."""
        return self.data_dir / ".collector_state.json"

    def _load_state(self):
        """Load collector state from file."""
        state_file = self._state_file()
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                self.last_scrape = (
                    datetime.fromisoformat(state.get("last_scrape"))
                    if state.get("last_scrape")
                    else None
                )
                self.scrape_count = state.get("scrape_count", 0)
                self.error_count = state.get("error_count", 0)
                logger.info(
                    f"Loaded state: {self.scrape_count} scrapes, last at {self.last_scrape}"
                )
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def _save_state(self):
        """Save collector state to file."""
        state = {
            "last_scrape": self.last_scrape.isoformat() if self.last_scrape else None,
            "scrape_count": self.scrape_count,
            "error_count": self.error_count,
            "updated_at": datetime.now().isoformat(),
        }
        try:
            with open(self._state_file(), "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save state: {e}")

    async def _initialize_scraper(self):
        """Initialize the scraper with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                self.scraper = ActionNetworkScraper(
                    headless=self.headless, data_dir=self.data_dir
                )
                await self.scraper.initialize()
                logger.info("Scraper initialized successfully")
                return
            except Exception as e:
                logger.error(
                    f"Failed to initialize scraper (attempt {attempt + 1}): {e}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY_BASE * (2**attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise

    async def _close_scraper(self):
        """Close the scraper safely."""
        if self.scraper:
            try:
                await self.scraper.close()
            except Exception as e:
                logger.warning(f"Error closing scraper: {e}")
            self.scraper = None

    async def scrape_all_leagues(self) -> dict:
        """
        Scrape all configured leagues.

        Returns:
            Dictionary with results per league
        """
        results = {}

        for league in self.LEAGUES:
            try:
                logger.info(f"Scraping {league.upper()}...")
                games = await self.scraper.scrape_odds(league)

                if games:
                    filepath = self.scraper.save_data(games, league)
                    # Use league-specific thresholds for sharp play detection
                    sharp_plays = self.scraper.get_sharp_plays(games, league=league)
                    min_div = self.scraper.get_min_divergence(league)

                    results[league] = {
                        "success": True,
                        "game_count": len(games),
                        "sharp_plays": len(sharp_plays),
                        "filepath": str(filepath),
                        "min_divergence": min_div,
                    }

                    logger.info(
                        f"Scraped {len(games)} {league.upper()} games, {len(sharp_plays)} sharp plays (threshold: {min_div}+)"
                    )
                else:
                    results[league] = {"success": False, "error": "No games found"}
                    logger.warning(f"No {league.upper()} games found")

                # Small delay between leagues
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error scraping {league}: {e}")
                results[league] = {"success": False, "error": str(e)}

        return results

    async def run_once(self) -> dict:
        """
        Run a single scrape cycle.

        Returns:
            Dictionary with scrape results
        """
        logger.info("Starting single scrape cycle...")
        start_time = datetime.now()

        try:
            await self._initialize_scraper()
            results = await self.scrape_all_leagues()

            self.last_scrape = datetime.now()
            self.scrape_count += 1
            self._save_state()

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Scrape cycle completed in {duration:.1f} seconds")

            return {
                "success": True,
                "timestamp": self.last_scrape.isoformat(),
                "duration_seconds": duration,
                "results": results,
            }

        except Exception as e:
            self.error_count += 1
            self._save_state()
            logger.error(f"Scrape cycle failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

        finally:
            await self._close_scraper()

    async def run_continuous(self):
        """
        Run continuous scraping at configured interval.

        Runs until interrupted (Ctrl+C).
        """
        logger.info(
            f"Starting continuous collection (interval: {self.interval_minutes} minutes)"
        )
        logger.info(f"Data directory: {self.data_dir}")
        logger.info("Press Ctrl+C to stop")

        while True:
            try:
                # Check if enough time has passed since last scrape
                if self.last_scrape:
                    elapsed = (datetime.now() - self.last_scrape).total_seconds() / 60
                    if elapsed < self.interval_minutes:
                        wait_minutes = self.interval_minutes - elapsed
                        logger.info(
                            f"Waiting {wait_minutes:.1f} minutes until next scrape..."
                        )
                        await asyncio.sleep(wait_minutes * 60)

                # Run scrape
                result = await self.run_once()

                if result["success"]:
                    logger.info(
                        f"Next scrape scheduled in {self.interval_minutes} minutes"
                    )
                else:
                    # On error, use shorter retry interval
                    retry_minutes = min(30, self.interval_minutes / 4)
                    logger.warning(
                        f"Scrape failed, retrying in {retry_minutes:.0f} minutes"
                    )
                    await asyncio.sleep(retry_minutes * 60)
                    continue

                # Wait for next interval
                await asyncio.sleep(self.interval_minutes * 60)

            except asyncio.CancelledError:
                logger.info("Continuous collection cancelled")
                break
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Unexpected error in continuous loop: {e}")
                # Wait before retrying
                await asyncio.sleep(60)

    def cleanup_old_files(self, days_to_keep: int = 30):
        """
        Remove data files older than specified days.

        Args:
            days_to_keep: Number of days to retain data
        """
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        removed = 0

        for file in self.data_dir.glob("*_odds_week*.json"):
            try:
                # Extract timestamp from filename
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime < cutoff:
                    file.unlink()
                    removed += 1
            except Exception as e:
                logger.warning(f"Could not process {file}: {e}")

        if removed:
            logger.info(f"Cleaned up {removed} old data files")

    def get_status(self) -> dict:
        """Get collector status."""
        # Count data files
        data_files = list(self.data_dir.glob("*_odds_*.json"))

        # Find latest files per league
        latest_files = {}
        for league in self.LEAGUES:
            latest = self.data_dir / f"{league}_odds_latest.json"
            if latest.exists():
                with open(latest) as f:
                    data = json.load(f)
                latest_files[league] = {
                    "scraped_at": data.get("scraped_at"),
                    "game_count": data.get("game_count"),
                    "sharp_plays": len(data.get("sharp_plays", [])),
                }

        return {
            "last_scrape": self.last_scrape.isoformat() if self.last_scrape else None,
            "scrape_count": self.scrape_count,
            "error_count": self.error_count,
            "data_files": len(data_files),
            "data_dir": str(self.data_dir),
            "interval_minutes": self.interval_minutes,
            "leagues": self.LEAGUES,
            "latest_data": latest_files,
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Action Network Automated Data Collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Single scrape
    python action_network_collector.py --once
    
    # Continuous collection (every 4 hours)
    python action_network_collector.py --continuous
    
    # Custom interval (every 2 hours)
    python action_network_collector.py --continuous --interval 120
    
    # Show status
    python action_network_collector.py --status
    
    # Cleanup old files
    python action_network_collector.py --cleanup --days 14
        """,
    )

    parser.add_argument(
        "--once", action="store_true", help="Run single scrape and exit"
    )
    parser.add_argument(
        "--continuous", action="store_true", help="Run continuous collection"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=240,
        help="Scrape interval in minutes (default: 240)",
    )
    parser.add_argument("--status", action="store_true", help="Show collector status")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup old data files")
    parser.add_argument(
        "--days", type=int, default=30, help="Days to keep when cleaning up"
    )
    parser.add_argument(
        "--headless", action="store_true", default=True, help="Run browser headless"
    )
    parser.add_argument(
        "--no-headless", action="store_true", help="Show browser window"
    )
    parser.add_argument("--data-dir", type=str, help="Custom data directory")

    args = parser.parse_args()

    # Determine headless mode
    headless = not args.no_headless

    # Create collector
    collector = ActionNetworkCollector(
        data_dir=Path(args.data_dir) if args.data_dir else None,
        interval_minutes=args.interval,
        headless=headless,
    )

    if args.status:
        status = collector.get_status()
        print("\n" + "=" * 50)
        print("ACTION NETWORK COLLECTOR STATUS")
        print("=" * 50)
        print(f"Data Directory: {status['data_dir']}")
        print(f"Total Scrapes: {status['scrape_count']}")
        print(f"Total Errors: {status['error_count']}")
        print(f"Data Files: {status['data_files']}")
        print(f"Last Scrape: {status['last_scrape'] or 'Never'}")
        print(f"Interval: {status['interval_minutes']} minutes")
        print(f"Leagues: {', '.join(status['leagues'])}")

        if status["latest_data"]:
            print("\nLatest Data:")
            for league, data in status["latest_data"].items():
                print(
                    f"  {league.upper()}: {data['game_count']} games, {data['sharp_plays']} sharp plays"
                )
                print(f"    Scraped: {data['scraped_at']}")

        return

    if args.cleanup:
        print(f"Cleaning up files older than {args.days} days...")
        collector.cleanup_old_files(args.days)
        return

    if args.continuous:
        await collector.run_continuous()
    elif args.once:
        result = await collector.run_once()

        if result["success"]:
            print("\n" + "=" * 50)
            print("SCRAPE COMPLETED SUCCESSFULLY")
            print("=" * 50)
            for league, data in result["results"].items():
                if data["success"]:
                    print(f"\n{league.upper()}:")
                    print(f"  Games: {data['game_count']}")
                    print(f"  Sharp Plays: {data['sharp_plays']}")
                    print(f"  File: {data['filepath']}")
                else:
                    print(f"\n{league.upper()}: FAILED - {data.get('error')}")
        else:
            print(f"\nScrape failed: {result.get('error')}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
