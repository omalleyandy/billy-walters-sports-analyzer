"""
News Feed Aggregator with Security & Validation

Implements official NFL/NCAAF news feed validation per Billy Walters methodology.
Aggregates news from official domains, validates authenticity, detects anomalies,
and categorizes items for E-Factor and modeling integration.

Sources:
- NFL.com official pages and team sites
- ESPN NFL news feeds
- NCAA.com official pages
- College Football Playoff official site
- Team athletic department sites

Security & Validation:
- Domain whitelist enforcement (official domains only)
- HTTPS/certificate validation
- Feed schema validation (RSS/Atom/JSON)
- GUID/ID stability tracking
- Redirect chain verification
- Anomaly detection (volume spikes, staleness, temporal patterns)

Usage:
    aggregator = NewsFeedAggregator()
    await aggregator.initialize()

    # Fetch and validate feeds
    items = await aggregator.fetch_league_news("nfl")
    categorized = aggregator.categorize_items(items)

    # Check feed health
    health = await aggregator.check_feed_health("nfl")
    print(f"Feed status: {health.status}")

    await aggregator.close()
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import feedparser
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class League(str, Enum):
    """Supported leagues."""

    NFL = "nfl"
    NCAAF = "ncaaf"


class NewsCategory(str, Enum):
    """News item categories for modeling impact."""

    INJURY_REPORT = "injury_report"
    COACHING_CHANGE = "coaching_change"
    DEPTH_CHART = "depth_chart"
    TRANSACTION = "transaction"
    PLAYOFF_IMPLICATION = "playoff_implication"
    RULE_CHANGE = "rule_change"
    GENERAL_NEWS = "general_news"


@dataclass
class FeedConfig:
    """Configuration for a news feed."""

    name: str
    url: str
    league: League
    feed_type: str = "rss"  # rss, atom, json
    official_domain: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate feed configuration."""
        if not self.official_domain:
            # Extract domain from URL
            parsed = urlparse(self.url)
            self.official_domain = parsed.netloc


@dataclass
class FeedItem:
    """Parsed feed item with metadata."""

    title: str
    link: str
    published_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    summary: str = ""
    content: str = ""
    guid: str = ""
    feed_name: str = ""
    league: League = League.NFL
    category: NewsCategory = NewsCategory.GENERAL_NEWS
    domain: str = ""
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def content_hash(self) -> str:
        """Get hash of content for duplicate detection."""
        content_str = f"{self.title}|{self.link}|{self.summary}"
        return hashlib.sha256(content_str.encode()).hexdigest()


class FeedHealthReport(BaseModel):
    """Health status of a feed."""

    feed_name: str
    league: League
    last_checked: datetime
    status: str = "healthy"  # healthy, degraded, failed
    items_count: int = 0
    items_per_day: float = 0.0
    last_published: Optional[datetime] = None
    days_since_update: int = 0
    anomalies: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)


class NewsFeedAggregator:
    """
    Aggregates and validates official NFL/NCAAF news feeds.

    Implements security and integrity checks per Billy Walters methodology.
    """

    # Official domains whitelist
    ALLOWED_DOMAINS = {
        # NFL
        "nfl.com",
        "nflopa.com",  # Players Association
        # Team domains
        "azcardinals.com",
        "atlantafalcons.com",
        "ravens.com",
        "baltimoreravens.com",
        "buffalobills.com",
        "carolinapanthers.com",
        "chicagobears.com",
        "cincinnatibengals.com",
        "clevelandbrowns.com",
        "dallascowboys.com",
        "denverbroncos.com",
        "detroitlions.com",
        "espn.com",
        "greenbaypackers.com",
        "houstontexans.com",
        "colts.com",
        "jacksonville.com",
        "jaguars.com",
        "kansascitychiefs.com",
        "larams.com",
        "chargers.com",
        "raiders.com",
        "dolphinsofficial.com",
        "miamidolphins.com",
        "vikings.com",
        "patriots.com",
        "neworleanssaints.com",
        "giants.com",
        "newyorkjets.com",
        "philadelphiaeagles.com",
        "steelers.com",
        "49ers.com",
        "seahawks.com",
        "buccaneers.com",
        "tennesseetitans.com",
        "washingtonfootball.com",
        # NCAAF
        "ncaa.com",
        "playoff.ncaa.org",
        "collegefootballplayoff.com",
        "espn.com",
        # Major team athletic sites (sample)
        "ohiostatebuckeyes.com",
        "fbf.olemiss.edu",
        "texassports.com",
        "clemsontigers.com",
        "lsusports.net",
        "georgiadogs.com",
        "miamiathleticshub.com",
        "alabama.com",
        "oklahoma.edu",
        "oregonducks.com",
        "uoregon.edu",
    }

    # Keywords for categorization
    CATEGORY_KEYWORDS = {
        NewsCategory.INJURY_REPORT: [
            "injury",
            "injured",
            "out",
            "doubtful",
            "questionable",
            "acl",
            "hamstring",
            "ankle",
            "concussion",
            "ir",
            "disabled list",
            "recovery",
        ],
        NewsCategory.COACHING_CHANGE: [
            "coach",
            "coaching",
            "hire",
            "fire",
            "interim",
            "replacement",
            "dismissal",
            "promotion",
            "coordinator",
        ],
        NewsCategory.DEPTH_CHART: [
            "depth chart",
            "starting",
            "starter",
            "benched",
            "snap count",
            "role",
            "position battle",
            "competition",
        ],
        NewsCategory.TRANSACTION: [
            "trade",
            "traded",
            "signing",
            "signed",
            "release",
            "released",
            "waiver",
            "free agent",
            "contract",
            "extension",
        ],
        NewsCategory.PLAYOFF_IMPLICATION: [
            "playoff",
            "playoffs",
            "playoff clinch",
            "elimination",
            "wild card",
            "seeding",
            "bowl",
            "cfp",
            "ncaa tournament",
        ],
        NewsCategory.RULE_CHANGE: [
            "rule change",
            "rule",
            "policy",
            "nfl operations",
            "integrity",
        ],
    }

    def __init__(
        self, timeout: int = 10000, max_redirects: int = 3, cache_ttl: int = 3600
    ):
        """
        Initialize news feed aggregator.

        Args:
            timeout: HTTP timeout in milliseconds
            max_redirects: Maximum redirect chain depth
            cache_ttl: Cache time-to-live in seconds
        """
        self.timeout = timeout / 1000
        self.max_redirects = max_redirects
        self.cache_ttl = cache_ttl
        self.client: Optional[httpx.AsyncClient] = None

        # Feed tracking
        self.feed_configs: Dict[str, FeedConfig] = {}
        self.item_history: Dict[str, Set[str]] = {
            "nfl": set(),
            "ncaaf": set(),
        }
        self.guid_history: Dict[str, Dict[str, str]] = {
            "nfl": {},
            "ncaaf": {},
        }
        self.feed_metrics: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize HTTP client and load feed configurations."""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_redirects=self.max_redirects),
        )
        logger.info("News feed aggregator initialized")

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
        logger.info("News feed aggregator closed")

    def add_feed(self, config: FeedConfig) -> None:
        """
        Add a feed configuration.

        Args:
            config: Feed configuration
        """
        self.feed_configs[config.name] = config
        logger.info(f"Added feed: {config.name} ({config.league.value})")

    async def fetch_league_news(
        self, league: League, validate: bool = True
    ) -> List[FeedItem]:
        """
        Fetch all news for a league.

        Args:
            league: League to fetch news for
            validate: Whether to validate items

        Returns:
            List of validated feed items
        """
        league_configs = [
            cfg for cfg in self.feed_configs.values() if cfg.league == league
        ]

        all_items = []
        for config in league_configs:
            items = await self._fetch_feed(config, validate)
            all_items.extend(items)

        # Deduplicate by content hash
        seen_hashes = set()
        unique_items = []
        for item in all_items:
            h = item.content_hash()
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_items.append(item)

        return sorted(
            unique_items, key=lambda x: x.published_date or datetime.min, reverse=True
        )

    async def _fetch_feed(
        self, config: FeedConfig, validate: bool = True
    ) -> List[FeedItem]:
        """
        Fetch a single feed.

        Args:
            config: Feed configuration
            validate: Whether to validate items

        Returns:
            List of parsed items
        """
        if not self.client:
            raise RuntimeError("Aggregator not initialized")

        try:
            response = await self.client.get(config.url)
            response.raise_for_status()

            # Parse feed
            feed = feedparser.parse(response.content)

            if feed.bozo:
                logger.warning(
                    f"Feed {config.name} has parsing issues: {feed.bozo_exception}"
                )

            items = []
            for entry in feed.entries:
                item = self._parse_entry(entry, config)

                if validate:
                    item = await self._validate_item(item, config)

                items.append(item)

            # Track metrics
            self._update_feed_metrics(config.name, items)

            return items

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch feed {config.name}: {e}")
            return []

    def _parse_entry(self, entry: Any, config: FeedConfig) -> FeedItem:
        """
        Parse feed entry to FeedItem.

        Args:
            entry: Feed entry from feedparser
            config: Feed configuration

        Returns:
            Parsed FeedItem
        """
        # Extract dates
        published = None
        updated = None

        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6])

        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            updated = datetime(*entry.updated_parsed[:6])

        # Extract link domain
        link = entry.get("link", "")
        domain = urlparse(link).netloc if link else ""

        # Extract content
        summary = entry.get("summary", "")
        content = (
            entry.get("content", [{}])[0].get("value", "")
            if entry.get("content")
            else ""
        )
        full_content = content or summary

        # Get GUID
        guid = entry.get("id", "") or entry.get("guid", "")

        item = FeedItem(
            title=entry.get("title", ""),
            link=link,
            published_date=published,
            updated_date=updated,
            summary=summary,
            content=full_content,
            guid=guid,
            feed_name=config.name,
            league=config.league,
            domain=domain,
        )

        # Categorize
        item.category = self._categorize_item(item)

        return item

    def _categorize_item(self, item: FeedItem) -> NewsCategory:
        """
        Categorize item based on content.

        Args:
            item: Feed item to categorize

        Returns:
            Detected category
        """
        combined_text = f"{item.title} {item.summary}".lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in combined_text for keyword in keywords):
                return category

        return NewsCategory.GENERAL_NEWS

    async def _validate_item(self, item: FeedItem, config: FeedConfig) -> FeedItem:
        """
        Validate item authenticity and structure.

        Args:
            item: Item to validate
            config: Feed configuration

        Returns:
            Validated item (is_valid field set)
        """
        # Check domain
        if item.domain and not self._is_domain_allowed(item.domain):
            item.is_valid = False
            item.validation_errors.append(f"Domain not in whitelist: {item.domain}")
            return item

        # Check GUID stability
        league_key = item.league.value
        if item.guid:
            if item.guid in self.guid_history[league_key]:
                stored_link = self.guid_history[league_key][item.guid]
                if stored_link != item.link:
                    item.validation_errors.append(
                        f"GUID mismatch: previously {stored_link}"
                    )
            else:
                self.guid_history[league_key][item.guid] = item.link
        else:
            item.validation_errors.append("Missing GUID/ID")

        # Verify redirect chain
        if item.link:
            try:
                response = await self.client.head(
                    item.link,
                    follow_redirects=True,
                )
                if response.status_code >= 400:
                    item.validation_errors.append(
                        f"Link returns {response.status_code}"
                    )

                # Check redirect domain match
                final_url = str(response.url)
                final_domain = urlparse(final_url).netloc
                if not self._is_domain_allowed(final_domain):
                    item.validation_errors.append(
                        f"Redirect to non-whitelisted domain: {final_domain}"
                    )
            except Exception as e:
                item.validation_errors.append(f"Link verification failed: {e}")

        # Check for required fields
        if not item.title:
            item.validation_errors.append("Missing title")
        if not item.link:
            item.validation_errors.append("Missing link")

        item.is_valid = len(item.validation_errors) == 0

        return item

    def _is_domain_allowed(self, domain: str) -> bool:
        """
        Check if domain is in whitelist.

        Args:
            domain: Domain to check

        Returns:
            Whether domain is allowed
        """
        # Remove www. prefix
        domain = domain.lstrip("www.")

        # Check exact match and parent domains
        return any(
            domain == allowed or domain.endswith(f".{allowed}")
            for allowed in self.ALLOWED_DOMAINS
        )

    def _update_feed_metrics(self, feed_name: str, items: List[FeedItem]) -> None:
        """
        Update feed metrics for anomaly detection.

        Args:
            feed_name: Feed name
            items: Items from feed
        """
        if feed_name not in self.feed_metrics:
            self.feed_metrics[feed_name] = {
                "last_checked": datetime.now(),
                "total_items": 0,
                "item_dates": [],
                "daily_counts": {},
            }

        metrics = self.feed_metrics[feed_name]
        metrics["last_checked"] = datetime.now()
        metrics["total_items"] = len(items)

        # Track daily counts
        today = datetime.now().date()
        today_key = str(today)
        metrics["daily_counts"][today_key] = len(
            [i for i in items if i.published_date and i.published_date.date() == today]
        )

        # Track item dates
        dates = [i.published_date for i in items if i.published_date]
        metrics["item_dates"] = sorted(dates, reverse=True)

    async def check_feed_health(self, league: League) -> List[FeedHealthReport]:
        """
        Check health of all feeds for a league.

        Args:
            league: League to check

        Returns:
            List of health reports
        """
        league_configs = [
            cfg for cfg in self.feed_configs.values() if cfg.league == league
        ]

        reports = []
        for config in league_configs:
            if not config.enabled:
                continue

            metrics = self.feed_metrics.get(config.name, {})
            last_checked = metrics.get("last_checked", datetime.now())
            items_count = metrics.get("total_items", 0)
            item_dates = metrics.get("item_dates", [])

            # Calculate items per day
            daily_counts = metrics.get("daily_counts", {})
            items_per_day = (
                sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0.0
            )

            # Detect anomalies
            anomalies = []
            last_published = item_dates[0] if item_dates else None
            days_since_update = 0

            if last_published:
                days_since_update = (datetime.now() - last_published).days
                if days_since_update > 7:
                    anomalies.append(f"No updates for {days_since_update} days")

            # Check for volume spike
            if daily_counts:
                recent_counts = list(daily_counts.values())[-7:]
                avg_count = sum(recent_counts) / len(recent_counts)
                max_count = max(recent_counts)
                if max_count > avg_count * 3:
                    anomalies.append(
                        f"Volume spike detected: {max_count} items "
                        f"(avg: {avg_count:.1f})"
                    )

            status = "degraded" if anomalies else "healthy"
            if items_count == 0:
                status = "failed"

            report = FeedHealthReport(
                feed_name=config.name,
                league=league,
                last_checked=last_checked,
                status=status,
                items_count=items_count,
                items_per_day=items_per_day,
                last_published=last_published,
                days_since_update=days_since_update,
                anomalies=anomalies,
            )
            reports.append(report)

        return reports

    def categorize_items(
        self, items: List[FeedItem]
    ) -> Dict[NewsCategory, List[FeedItem]]:
        """
        Group items by category.

        Args:
            items: Items to categorize

        Returns:
            Dict mapping category to items
        """
        categorized: Dict[NewsCategory, List[FeedItem]] = {
            cat: [] for cat in NewsCategory
        }

        for item in items:
            if item.is_valid:
                categorized[item.category].append(item)

        return categorized

    def get_modeling_items(self, items: List[FeedItem]) -> Dict[str, List[FeedItem]]:
        """
        Filter items relevant for E-Factor/S-Factor modeling.

        Args:
            items: All items

        Returns:
            Dict mapping impact type to items
        """
        modeling_items: Dict[str, List[FeedItem]] = {
            "e_factor_inputs": [],
            "s_factor_context": [],
            "w_factor_modifiers": [],
        }

        for item in items:
            if not item.is_valid:
                continue

            # E-Factor relevant
            if item.category in [
                NewsCategory.INJURY_REPORT,
                NewsCategory.COACHING_CHANGE,
                NewsCategory.TRANSACTION,
                NewsCategory.PLAYOFF_IMPLICATION,
            ]:
                modeling_items["e_factor_inputs"].append(item)

            # S-Factor relevant
            if item.category in [
                NewsCategory.DEPTH_CHART,
                NewsCategory.TRANSACTION,
            ]:
                modeling_items["s_factor_context"].append(item)

            # W-Factor relevant (injury + weather interaction)
            if item.category == NewsCategory.INJURY_REPORT:
                modeling_items["w_factor_modifiers"].append(item)

        return modeling_items


async def main() -> None:
    """Example usage."""
    aggregator = NewsFeedAggregator()
    await aggregator.initialize()

    # Add sample feeds
    aggregator.add_feed(
        FeedConfig(
            name="NFL Official",
            url="https://www.nfl.com/feeds-general/news",
            league=League.NFL,
            official_domain="nfl.com",
        )
    )

    # Fetch and validate
    items = await aggregator.fetch_league_news(League.NFL)
    print(f"Fetched {len(items)} items")

    # Categorize
    categorized = aggregator.categorize_items(items)
    for cat, cat_items in categorized.items():
        if cat_items:
            print(f"\n{cat.value}: {len(cat_items)} items")
            for item in cat_items[:2]:
                print(f"  - {item.title}")

    # Check health
    health_reports = await aggregator.check_feed_health(League.NFL)
    for report in health_reports:
        print(f"\nFeed: {report.feed_name} -> {report.status}")
        if report.anomalies:
            for anomaly in report.anomalies:
                print(f"  ⚠️  {anomaly}")

    await aggregator.close()


if __name__ == "__main__":
    asyncio.run(main())
