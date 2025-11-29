#!/usr/bin/env python3
"""
X (Twitter) News Scraper for Billy Walters Data Collection Workflow

Integrates with RealDataIntegrator to collect breaking news and injury updates
from official X sources. Automatically used during /collect-all-data workflow.

Free Tier Implementation:
- OAuth 2.0 Bearer Token authentication
- 5 API calls/day maximum (conservative)
- 24-hour caching (95% API savings)
- Graceful degradation if quota exhausted

Usage:
    # Collect NFL injury posts (Wednesday)
    uv run python scripts/scrapers/scrape_x_news_integrated.py --league nfl --type injury

    # Collect NCAAF injury posts (Thursday)
    uv run python scripts/scrapers/scrape_x_news_integrated.py --league ncaaf --type injury

    # Collect both leagues
    uv run python scripts/scrapers/scrape_x_news_integrated.py --all

    # Check quota status only (no API call)
    uv run python scripts/scrapers/scrape_x_news_integrated.py --quota-status
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.data_integration.real_data_integrator import RealDataIntegrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class XNewsCollector:
    """Collects X news posts for Billy Walters data collection workflow."""

    def __init__(self):
        """Initialize X News Collector."""
        self.integrator: Optional[RealDataIntegrator] = None
        self.output_dir = Path("output/x_news/integrated")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> bool:
        """
        Initialize data integrator with X News Scraper.

        Returns:
            True if initialization successful
        """
        try:
            self.integrator = RealDataIntegrator()
            await self.integrator.initialize()

            if not self.integrator.x_news_scraper:
                logger.error(
                    "[ERROR] X News Scraper not available - "
                    "check X_BEARER_TOKEN in .env"
                )
                return False

            logger.info("[OK] X News Collector initialized")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize: {e}")
            return False

    async def fetch_league_news(
        self,
        league: str,
        source_type: str = "injury",
        days: int = 7,
        min_relevance: float = 0.7,
    ) -> List[Dict]:
        """
        Fetch X posts for a league.

        Args:
            league: "nfl" or "ncaaf"
            source_type: "injury", "news", or "all"
            days: Number of days to look back
            min_relevance: Minimum relevance threshold

        Returns:
            List of high-relevance X posts
        """
        if not self.integrator:
            logger.error("[ERROR] Integrator not initialized")
            return []

        try:
            logger.info(
                f"[INFO] Fetching {league.upper()} {source_type} posts "
                f"(days: {days}, min_relevance: {min_relevance:.0%})..."
            )

            posts = await self.integrator.fetch_x_news(
                league=league,
                source_type=source_type,
                days=days,
                min_relevance=min_relevance,
            )

            if posts:
                logger.info(f"[OK] Found {len(posts)} {league.upper()} posts")
                # Log sample posts
                for post in posts[:2]:
                    logger.info(
                        f"     @{post['author_handle']}: "
                        f"{post['text'][:60]}... "
                        f"(relevance: {post['relevance']:.0%})"
                    )
            else:
                logger.info(f"[INFO] No high-relevance {league.upper()} posts found")

            return posts

        except Exception as e:
            logger.error(f"[ERROR] Failed to fetch {league.upper()} posts: {e}")
            return []

    async def save_posts(
        self, posts: List[Dict], league: str, source_type: str
    ) -> Optional[Path]:
        """
        Save posts to JSON file.

        Args:
            posts: List of posts to save
            league: "nfl" or "ncaaf"
            source_type: "injury", "news", or "all"

        Returns:
            Path to saved file, or None if no posts
        """
        if not posts:
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"x_news_{league}_{source_type}_{timestamp}.json"
            output_path = self.output_dir / filename

            output_path.write_text(
                json.dumps(
                    {
                        "league": league,
                        "type": source_type,
                        "collected_at": datetime.now().isoformat(),
                        "post_count": len(posts),
                        "posts": posts,
                    },
                    indent=2,
                )
            )

            logger.info(f"[OK] Saved {len(posts)} posts to {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"[ERROR] Failed to save posts: {e}")
            return None

    async def check_quota_status(self) -> Dict:
        """
        Check X API quota status without making API call.

        Returns:
            Quota status dictionary
        """
        if not self.integrator or not self.integrator.x_news_scraper:
            logger.error("[ERROR] X News Scraper not initialized")
            return {}

        try:
            quota = self.integrator.x_news_scraper.get_quota_status()
            logger.info("[OK] X API Quota Status:")
            logger.info(
                f"     Calls today: {quota['calls_today']}/{quota['daily_limit']}"
            )
            logger.info(f"     Remaining: {quota['remaining']}")
            logger.info(f"     Exhausted: {quota['exhausted']}")
            logger.info(f"     Cached items: {quota['cached_items']}")
            return quota

        except Exception as e:
            logger.error(f"[ERROR] Failed to get quota status: {e}")
            return {}

    async def close(self) -> None:
        """Close integrator connections."""
        if self.integrator:
            await self.integrator.close()
            logger.info("[OK] X News Collector closed")


async def main() -> int:
    """
    Main entry point for X News collection.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    parser = argparse.ArgumentParser(
        description="Collect X (Twitter) news for Billy Walters analysis"
    )
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        help="League to collect (nfl or ncaaf)",
    )
    parser.add_argument(
        "--type",
        choices=["injury", "news", "all"],
        default="injury",
        help="Type of posts to collect (default: injury)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)",
    )
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=0.7,
        help="Minimum relevance threshold (default: 0.7)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Collect both NFL and NCAAF injury posts",
    )
    parser.add_argument(
        "--quota-status",
        action="store_true",
        help="Check quota status only (no API call)",
    )

    args = parser.parse_args()

    collector = XNewsCollector()

    try:
        # Initialize integrator
        if not await collector.initialize():
            return 1

        # If quota-status only
        if args.quota_status:
            logger.info("\n" + "=" * 70)
            logger.info("QUOTA STATUS CHECK")
            logger.info("=" * 70)
            await collector.check_quota_status()
            await collector.close()
            return 0

        # Determine which leagues to collect
        leagues_to_collect = []
        if args.all:
            leagues_to_collect = ["nfl", "ncaaf"]
        elif args.league:
            leagues_to_collect = [args.league]
        else:
            logger.error("[ERROR] Must specify --league, --all, or --quota-status")
            return 1

        logger.info("\n" + "=" * 70)
        logger.info("X NEWS COLLECTION")
        logger.info("=" * 70)

        # Check quota before starting
        await collector.check_quota_status()

        # Collect posts for each league
        results = {}
        for league in leagues_to_collect:
            logger.info(f"\n[{league.upper()}]")

            posts = await collector.fetch_league_news(
                league=league,
                source_type=args.type,
                days=args.days,
                min_relevance=args.min_relevance,
            )

            if posts:
                saved_path = await collector.save_posts(posts, league, args.type)
                results[league] = {
                    "posts_found": len(posts),
                    "saved_to": str(saved_path) if saved_path else None,
                }
            else:
                results[league] = {
                    "posts_found": 0,
                    "saved_to": None,
                }

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 70)
        total_posts = sum(r["posts_found"] for r in results.values())
        logger.info(f"Total posts collected: {total_posts}")
        for league, result in results.items():
            status = "[OK]" if result["posts_found"] > 0 else "[NO DATA]"
            logger.info(f"  {league.upper()}: {result['posts_found']} posts {status}")

        logger.info("\n[OK] X News collection complete")
        await collector.close()
        return 0

    except KeyboardInterrupt:
        logger.info("\n[INFO] Collection interrupted by user")
        await collector.close()
        return 1
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {e}")
        await collector.close()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
