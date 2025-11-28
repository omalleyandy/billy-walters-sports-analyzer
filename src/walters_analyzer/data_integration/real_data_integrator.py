"""
Real Data Integrator for News & Injury E-Factors

Connects NewsInjuryEFactorAggregator to actual data sources:
- ESPN injury reports (API-based)
- ESPN news client (Playwright-based)
- NFL.com official injury reports
- Transaction feeds

Handles data transformation, validation, and caching with source tracking.

Usage:
    integrator = RealDataIntegrator()
    await integrator.initialize()

    # Fetch real injury data
    injuries = await integrator.fetch_nfl_injuries("DAL")

    # Fetch news with source quality tracking
    news_items = await integrator.fetch_team_news("DAL", league="nfl")

    # Auto-map to E-Factor inputs
    efactor_inputs = await integrator.get_efactor_inputs("DAL", league="nfl")

    await integrator.close()
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    """Metadata about a data source."""

    name: str  # e.g., "ESPN Injury API"
    source_type: str  # "injury", "news", "transaction"
    reliability_score: float = 1.0  # 0.0-1.0
    last_fetch: Optional[datetime] = None
    fetch_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    coverage_pct: float = 1.0  # % of teams/data covered


@dataclass
class SourcedData:
    """Data with source tracking and confidence."""

    data: Dict[str, Any]
    source_name: str
    fetch_time: datetime
    reliability_score: float = 1.0
    confidence_pct: float = 100.0
    validation_errors: List[str] = field(default_factory=list)


class RealDataIntegrator:
    """
    Integrates real data sources for E-Factor calculation.

    Manages:
    - Multiple data sources with fallback strategies
    - Source reliability tracking
    - Data validation and normalization
    - Caching for performance
    - Async concurrent fetching
    """

    def __init__(self, output_dir: str = "output/efactor_data"):
        """Initialize integrator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize data sources
        self.sources: Dict[str, DataSource] = {
            "espn_injuries": DataSource(
                name="ESPN Injury API",
                source_type="injury",
                reliability_score=0.95,
                coverage_pct=1.0,
            ),
            "nfl_injuries": DataSource(
                name="NFL.com Official Injuries",
                source_type="injury",
                reliability_score=1.0,
                coverage_pct=0.95,
            ),
            "espn_news": DataSource(
                name="ESPN News Client",
                source_type="news",
                reliability_score=0.90,
                coverage_pct=0.9,
            ),
            "espn_transactions": DataSource(
                name="ESPN Transactions API",
                source_type="transaction",
                reliability_score=0.98,
                coverage_pct=0.98,
            ),
        }

        # Data cache
        self.injury_cache: Dict[str, SourcedData] = {}
        self.news_cache: Dict[str, SourcedData] = {}
        self.transaction_cache: Dict[str, SourcedData] = {}

        # Clients (lazy initialized)
        self.espn_injury_scraper = None
        self.espn_news_client = None
        self.espn_transactions_client = None
        self.nfl_injury_scraper = None

    async def initialize(self) -> None:
        """Initialize data sources and clients."""
        try:
            # Import and initialize ESPN injury scraper
            from src.data.espn_injury_scraper import ESPNInjuryScraper

            self.espn_injury_scraper = ESPNInjuryScraper()
            logger.info("✓ ESPN Injury Scraper initialized")
        except ImportError:
            logger.warning("⚠ ESPN Injury Scraper not available")

        try:
            # Import and initialize ESPN news client
            from src.data.espn_news_client import ESPNNewsClient

            self.espn_news_client = ESPNNewsClient()
            await self.espn_news_client.connect()
            logger.info("✓ ESPN News Client initialized")
        except (ImportError, Exception) as e:
            logger.warning(f"⚠ ESPN News Client not available: {e}")

        try:
            # Import and initialize ESPN transactions client
            from src.data.espn_transactions_client import (
                ESPNTransactionsClient,
            )

            self.espn_transactions_client = ESPNTransactionsClient()
            logger.info("✓ ESPN Transactions Client initialized")
        except ImportError:
            logger.warning("⚠ ESPN Transactions Client not available")

        try:
            # Import and initialize NFL injury scraper
            from src.data.nfl_official_injury_scraper import (
                NFLOfficialInjuryScraper,
            )

            self.nfl_injury_scraper = NFLOfficialInjuryScraper()
            logger.info("✓ NFL Official Injury Scraper initialized")
        except ImportError:
            logger.warning("⚠ NFL Official Injury Scraper not available")

        logger.info("RealDataIntegrator initialized")

    async def close(self) -> None:
        """Close all client connections."""
        if self.espn_news_client:
            try:
                await self.espn_news_client.close()
            except Exception:
                pass

        logger.info("RealDataIntegrator closed")

    async def fetch_nfl_injuries(
        self, team: str, use_cache: bool = True
    ) -> Optional[SourcedData]:
        """
        Fetch NFL injury data with fallback strategy.

        Priority:
        1. NFL.com official (highest reliability)
        2. ESPN API (backup)

        Args:
            team: Team abbreviation (e.g., "DAL")
            use_cache: Use cached data if available

        Returns:
            SourcedData with injury information
        """
        cache_key = f"nfl_{team}_injuries"

        if use_cache and cache_key in self.injury_cache:
            cached = self.injury_cache[cache_key]
            # Check if cache is fresh (< 1 hour old)
            age_minutes = (datetime.now() - cached.fetch_time).total_seconds() / 60
            if age_minutes < 60:
                logger.debug(f"Using cached injury data for {team}")
                return cached

        # Try NFL.com official first
        if self.nfl_injury_scraper:
            try:
                injuries = self.nfl_injury_scraper.scrape_team_injuries(team)
                sourced = SourcedData(
                    data={"injuries": injuries, "team": team},
                    source_name="nfl_injuries",
                    fetch_time=datetime.now(),
                    reliability_score=self.sources["nfl_injuries"].reliability_score,
                    confidence_pct=100.0,
                )
                self.injury_cache[cache_key] = sourced
                self._update_source_stats("nfl_injuries", success=True)
                logger.info(
                    f"✓ Fetched {len(injuries)} injuries from NFL.com for {team}"
                )
                return sourced
            except Exception as e:
                logger.warning(f"NFL.com scrape failed for {team}: {e}")
                self._update_source_stats("nfl_injuries", success=False)

        # Fallback to ESPN API
        if self.espn_injury_scraper:
            try:
                injuries = self.espn_injury_scraper.scrape_nfl_team_injuries(team)
                sourced = SourcedData(
                    data={"injuries": injuries, "team": team},
                    source_name="espn_injuries",
                    fetch_time=datetime.now(),
                    reliability_score=self.sources["espn_injuries"].reliability_score,
                    confidence_pct=95.0,  # Slightly lower confidence due to fallback
                )
                self.injury_cache[cache_key] = sourced
                self._update_source_stats("espn_injuries", success=True)
                logger.info(f"✓ Fetched {len(injuries)} injuries from ESPN for {team}")
                return sourced
            except Exception as e:
                logger.warning(f"ESPN scrape failed for {team}: {e}")
                self._update_source_stats("espn_injuries", success=False)

        logger.warning(f"⚠ No injury data available for {team}")
        return None

    async def fetch_team_news(
        self, team: str, league: str = "nfl", use_cache: bool = True
    ) -> List[SourcedData]:
        """
        Fetch team news from all available sources.

        Args:
            team: Team abbreviation
            league: League ("nfl" or "ncaaf")
            use_cache: Use cached data if available

        Returns:
            List of SourcedData items from all sources
        """
        cache_key = f"{league}_{team}_news"

        if use_cache and cache_key in self.news_cache:
            cached = self.news_cache[cache_key]
            age_minutes = (datetime.now() - cached.fetch_time).total_seconds() / 60
            if age_minutes < 120:  # 2-hour cache for news
                logger.debug(f"Using cached news data for {team}")
                return [cached]

        results = []

        # Try ESPN News Client
        if self.espn_news_client and league == "nfl":
            try:
                news_items = await self.espn_news_client.get_team_news(team, limit=10)
                sourced = SourcedData(
                    data={"news": news_items, "team": team, "league": league},
                    source_name="espn_news",
                    fetch_time=datetime.now(),
                    reliability_score=self.sources["espn_news"].reliability_score,
                    confidence_pct=90.0,
                )
                results.append(sourced)
                self._update_source_stats("espn_news", success=True)
                logger.info(f"✓ Fetched {len(news_items)} news items from ESPN")
            except Exception as e:
                logger.warning(f"ESPN news fetch failed: {e}")
                self._update_source_stats("espn_news", success=False)

        # Try ESPN Transactions
        if self.espn_transactions_client:
            try:
                transactions = (
                    await self.espn_transactions_client.get_team_transactions(
                        team, league=league
                    )
                )
                sourced = SourcedData(
                    data={
                        "transactions": transactions,
                        "team": team,
                        "league": league,
                    },
                    source_name="espn_transactions",
                    fetch_time=datetime.now(),
                    reliability_score=self.sources[
                        "espn_transactions"
                    ].reliability_score,
                    confidence_pct=98.0,
                )
                results.append(sourced)
                self._update_source_stats("espn_transactions", success=True)
                logger.info(f"✓ Fetched {len(transactions)} transactions")
            except Exception as e:
                logger.warning(f"ESPN transactions fetch failed: {e}")
                self._update_source_stats("espn_transactions", success=False)

        # Cache first result
        if results:
            self.news_cache[cache_key] = results[0]

        return results

    async def fetch_all_nfl_teams(
        self, data_type: str = "injuries"
    ) -> Dict[str, SourcedData]:
        """
        Fetch data for all NFL teams concurrently.

        Args:
            data_type: "injuries", "news", or "transactions"

        Returns:
            Dict mapping team abbreviation to SourcedData
        """
        nfl_teams = [
            "ARI",
            "ATL",
            "BAL",
            "BUF",
            "CAR",
            "CHI",
            "CIN",
            "CLE",
            "DAL",
            "DEN",
            "DET",
            "GB",
            "HOU",
            "IND",
            "JAX",
            "KC",
            "LAC",
            "LAR",
            "LV",
            "MIA",
            "MIN",
            "NE",
            "NO",
            "NYG",
            "NYJ",
            "PHI",
            "PIT",
            "SF",
            "SEA",
            "TB",
            "TEN",
            "WAS",
        ]

        results = {}

        if data_type == "injuries":
            tasks = [self.fetch_nfl_injuries(team) for team in nfl_teams]
            responses = await asyncio.gather(*tasks)
            for team, data in zip(nfl_teams, responses):
                if data:
                    results[team] = data
        elif data_type == "news":
            tasks = [self.fetch_team_news(team, league="nfl") for team in nfl_teams]
            responses = await asyncio.gather(*tasks)
            for team, data_list in zip(nfl_teams, responses):
                if data_list:
                    results[team] = data_list[0]

        logger.info(f"✓ Fetched {data_type} for {len(results)}/{len(nfl_teams)} teams")
        return results

    async def get_efactor_inputs(
        self, team: str, league: str = "nfl"
    ) -> Dict[str, Any]:
        """
        Get E-Factor inputs from real data.

        Combines injuries, news, and transactions into E-Factor parameters.

        Args:
            team: Team abbreviation
            league: League ("nfl" or "ncaaf")

        Returns:
            Dict of E-Factor inputs
        """
        # Fetch real data
        injuries = await self.fetch_nfl_injuries(team)
        news = await self.fetch_team_news(team, league=league)

        # Import mapper
        from walters_analyzer.data_integration.news_injury_mapper import (
            NewsInjuryMapper,
        )

        mapper = NewsInjuryMapper()

        # Map injuries
        injury_data = {}
        if injuries:
            try:
                # Convert to InjuryData objects
                from walters_analyzer.data_integration.news_injury_mapper import (
                    InjuryData,
                )

                injury_list = [
                    InjuryData(
                        team=team,
                        position=inj.get("position", ""),
                        player_name=inj.get("player_name", ""),
                        injury_type=inj.get("injury_type", ""),
                        status=inj.get("injury_status", ""),
                        practice_status="dnp",
                    )
                    for inj in injuries.data.get("injuries", [])
                ]
                injury_data = mapper.map_injuries_to_efactor(injury_list, team)
            except Exception as e:
                logger.warning(f"Error mapping injuries: {e}")

        # Map news
        news_data = {}
        if news:
            try:
                # Import FeedItem
                from walters_analyzer.data_integration.news_feed_aggregator import (
                    FeedItem,
                )

                feed_items = []
                for item in news[0].data.get("news", []):
                    feed_item = FeedItem(
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        summary=item.get("summary", ""),
                    )
                    feed_items.append(feed_item)

                news_data = mapper.map_news_to_efactor(feed_items, team)
            except Exception as e:
                logger.warning(f"Error mapping news: {e}")

        # Merge and return
        efactor_inputs = {**injury_data, **news_data}
        return efactor_inputs

    def _update_source_stats(
        self, source_name: str, success: bool, latency_ms: float = 0.0
    ) -> None:
        """Update source reliability statistics."""
        if source_name not in self.sources:
            return

        source = self.sources[source_name]
        source.fetch_count += 1
        source.last_fetch = datetime.now()

        if not success:
            source.error_count += 1
            # Decrease reliability score
            source.reliability_score = max(0.5, source.reliability_score - 0.05)
        else:
            # Increase reliability score (up to 1.0)
            source.reliability_score = min(1.0, source.reliability_score + 0.01)

        if latency_ms > 0:
            # Update average latency (exponential moving average)
            alpha = 0.1
            source.avg_latency_ms = (
                alpha * latency_ms + (1 - alpha) * source.avg_latency_ms
            )

    def get_source_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health report for all sources."""
        health = {}
        for name, source in self.sources.items():
            success_rate = (
                ((source.fetch_count - source.error_count) / source.fetch_count * 100)
                if source.fetch_count > 0
                else 100.0
            )
            health[name] = {
                "name": source.name,
                "reliability_score": source.reliability_score,
                "success_rate": success_rate,
                "fetch_count": source.fetch_count,
                "error_count": source.error_count,
                "avg_latency_ms": source.avg_latency_ms,
                "coverage_pct": source.coverage_pct,
                "last_fetch": source.last_fetch.isoformat()
                if source.last_fetch
                else None,
            }

        return health

    async def export_data(self, week: int, league: str = "nfl") -> Path:
        """Export collected data to JSON file."""
        output_file = (
            self.output_dir
            / f"efactor_data_week{week}_{league}_{datetime.now().isoformat()}.json"
        )

        data = {
            "timestamp": datetime.now().isoformat(),
            "week": week,
            "league": league,
            "sources_health": self.get_source_health(),
            "injury_cache": {
                k: {
                    "data": v.data,
                    "source_name": v.source_name,
                    "fetch_time": v.fetch_time.isoformat(),
                    "reliability_score": v.reliability_score,
                    "confidence_pct": v.confidence_pct,
                }
                for k, v in self.injury_cache.items()
            },
            "news_cache": {
                k: {
                    "data": v.data,
                    "source_name": v.source_name,
                    "fetch_time": v.fetch_time.isoformat(),
                    "reliability_score": v.reliability_score,
                    "confidence_pct": v.confidence_pct,
                }
                for k, v in self.news_cache.items()
            },
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"✓ Exported E-Factor data to {output_file}")
        return output_file


async def main() -> None:
    """Demo usage."""
    integrator = RealDataIntegrator()
    await integrator.initialize()

    # Fetch injuries for a team
    print("\n=== Fetching Real Data ===")
    injuries = await integrator.fetch_nfl_injuries("DAL")
    if injuries:
        print(f"✓ Injuries for DAL: {len(injuries.data.get('injuries', []))} found")
        print(f"  Source: {injuries.source_name}")
        print(f"  Confidence: {injuries.confidence_pct}%")

    # Fetch news
    news = await integrator.fetch_team_news("DAL", league="nfl")
    if news:
        print(f"✓ News for DAL: {len(news[0].data.get('news', []))} articles")
        print(f"  Source: {news[0].source_name}")

    # Get E-Factor inputs
    print("\n=== E-Factor Inputs ===")
    efactor = await integrator.get_efactor_inputs("DAL", league="nfl")
    print(f"✓ E-Factor inputs generated:")
    for key, value in efactor.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value}")

    # Source health
    print("\n=== Source Health ===")
    health = integrator.get_source_health()
    for source_name, stats in health.items():
        print(f"  {stats['name']}: {stats['success_rate']:.1f}% success")

    # Export data
    await integrator.export_data(week=13, league="nfl")

    await integrator.close()


if __name__ == "__main__":
    asyncio.run(main())
