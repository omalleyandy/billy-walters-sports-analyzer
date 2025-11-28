"""
X (Twitter) News & Injury Scraper

Scrapes current news and injury information from official X sources for NFL and NCAAF.

Official Sources:
- NFL: @NFL, @nflofficial, @nflhealth, team accounts (@KansasCity Chiefs, etc)
- NCAAF: @ESPNCollegeFB, @FieldYates, team accounts
- Injuries: @AdamSchefter, @FieldYates, @NFL_Motive
- News: @ESPN, @ESPNCFB, team beat reporters

Usage:
    scraper = XNewsScraper(api_key, api_secret, access_token, access_secret)
    await scraper.initialize()

    # Get recent NFL injuries and news
    nfl_posts = await scraper.get_league_news("nfl", days=7)
    for post in nfl_posts:
        print(f"{post['author']}: {post['text']}")

    # Get team-specific news
    kc_news = await scraper.get_team_news("KC", "nfl")

    await scraper.close()
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any

import tweepy
from dotenv import load_dotenv

# Load .env file for credentials
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class XPost:
    """Single post from X with metadata."""

    post_id: str
    author: str
    author_handle: str
    text: str
    created_at: datetime
    likes: int
    retweets: int
    source_type: str  # "injury", "news", "team_update"
    league: str  # "nfl" or "ncaaf"
    team: Optional[str] = None  # Team abbreviation if team-specific
    relevance_score: float = 0.0  # 0.0-1.0 based on keywords
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        return d


class XNewsScraper:
    """
    Scrapes news and injury posts from X for NFL and NCAAF.

    Uses Tweepy v4 with Twitter API v2 endpoints for reliable access
    to official accounts and breaking news.
    """

    # Official sources to monitor
    OFFICIAL_SOURCES = {
        "nfl": {
            "injury": [
                "@NFL",
                "@AdamSchefter",
                "@FieldYates",
                "@NFL_Motive",
                "@nflhealth",
            ],
            "news": [
                "@NFL",
                "@nflofficial",
                "@ESPN",
                "@NFL_Motive",
                "@ProFootballTalk",
            ],
            "teams": {
                "KC": "@KansasCity",  # Chiefs
                "DAL": "@dallascowboys",
                "GB": "@packers",
                "NE": "@patriots",
                "SF": "@49ers",
                "BUF": "@BuffaloBills",
                "LAC": "@Chargers",
                "DEN": "@Broncos",
                "SEA": "@Seahawks",
                "PHI": "@eagles",
                "MIN": "@Vikings",
                "LAR": "@RamsNFL",
            },
        },
        "ncaaf": {
            "injury": [
                "@ESPNCollegeFB",
                "@FieldYates",
                "@Brett_McMurphy",
                "@Jeff_Schnitt",
            ],
            "news": [
                "@ESPNCollegeFB",
                "@ESPN",
                "@Brett_McMurphy",
                "@Jeff_Schnitt",
                "@RedditCFB",
            ],
            "teams": {
                "LSU": "@LSUfootball",
                "BAMA": "@AlabamaFTBL",
                "TAMU": "@AggieFootball",
                "OU": "@OU_Football",
                "TX": "@TexasFootball",
                "UF": "@GatorsFB",
                "OSU": "@OhioStateFB",
                "MICH": "@UMichFootball",
            },
        },
    }

    # Keywords indicating injuries, trades, coaching changes
    INJURY_KEYWORDS = [
        "out",
        "injured",
        "injury",
        "questionable",
        "doubtful",
        "probable",
        "day-to-day",
        "recovery",
        "surgery",
        "ACL",
        "ankle",
        "hamstring",
        "concussion",
        "sprain",
        "fractured",
        "broken",
        "illness",
        "status",
        "unavailable",
    ]

    NEWS_KEYWORDS = [
        "trade",
        "traded",
        "signing",
        "signed",
        "released",
        "free agent",
        "coaching",
        "hired",
        "fired",
        "suspended",
        "banished",
        "suspension",
        "draft",
        "playoff",
        "bye week",
        "game day",
        "this weekend",
        "weather alert",
    ]

    def __init__(
        self,
        bearer_token: Optional[str] = None,
        output_dir: str = "output/x_news",
    ):
        """
        Initialize X scraper with API credentials.

        Args:
            bearer_token: X Bearer Token (from environment if not provided)
            output_dir: Directory for caching posts
        """
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client: Optional[tweepy.Client] = None
        self.cache: Dict[str, List[XPost]] = {}

        # Free tier quota tracking (1 request per 15 min, 100 posts/month)
        self.api_calls: List[Dict[str, Any]] = []
        self.free_tier_mode = True  # Enforce free tier limits
        self.daily_limit = 5  # Conservative: max 5 calls/day
        self.cache_ttl_hours = 24  # Cache for 24 hours
        self.cache_timestamps: Dict[str, datetime] = {}

    async def initialize(self) -> bool:
        """Initialize X API client."""
        try:
            if not self.bearer_token:
                logger.warning(
                    "X API credentials not found. Set X_BEARER_TOKEN environment variable."
                )
                return False

            # Initialize Tweepy client with Bearer Token (OAuth 2.0)
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                wait_on_rate_limit=True,
            )

            logger.info("X API client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize X API client: {e}")
            return False

    def _record_api_call(self, league: str, source_type: str) -> None:
        """Record an API call for quota tracking."""
        now = datetime.now()
        self.api_calls.append(
            {
                "timestamp": now,
                "league": league,
                "type": source_type,
            }
        )

        # Clean old calls (older than 24h)
        cutoff = now - timedelta(hours=24)
        self.api_calls = [c for c in self.api_calls if c["timestamp"] > cutoff]

        remaining = max(0, self.daily_limit - len(self.api_calls))
        logger.info(f"[OK] API calls today: {len(self.api_calls)}/{self.daily_limit}")
        logger.info(f"[OK] Remaining quota: {remaining}")

    def _api_quota_exhausted(self) -> bool:
        """Check if daily quota exceeded (free tier protection)."""
        # Clean old calls (older than 24h)
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        self.api_calls = [c for c in self.api_calls if c["timestamp"] > cutoff]

        exhausted = len(self.api_calls) >= self.daily_limit
        if exhausted:
            logger.warning(
                "[WARNING] Daily API quota exhausted. "
                "Using cached data. "
                "Next quota reset in 24 hours."
            )
        return exhausted

    def _is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.cache_timestamps:
            return False

        age_hours = (
            datetime.now() - self.cache_timestamps[cache_key]
        ).total_seconds() / 3600
        return age_hours < self.cache_ttl_hours

    def _get_cached_posts(self, cache_key: str) -> List[XPost]:
        """Get cached posts if available."""
        if self._is_cache_fresh(cache_key):
            age_hours = (
                datetime.now() - self.cache_timestamps[cache_key]
            ).total_seconds() / 3600
            logger.info(f"[OK] Using cached posts ({age_hours:.1f}h old)")
            return self.cache.get(cache_key, [])
        return []

    async def get_league_news(
        self,
        league: str,
        source_type: str = "injury",
        days: int = 7,
        max_results: int = 100,
    ) -> List[XPost]:
        """
        Get recent posts from official sources for a league.

        Args:
            league: "nfl" or "ncaaf"
            source_type: "injury", "news", or "all"
            days: How many days back to search
            max_results: Maximum posts to return

        Returns:
            List of XPost objects
        """
        if not self.client:
            logger.warning("X API client not initialized")
            return []

        posts = []
        cache_key = f"{league}_{source_type}_{days}d"

        # Free tier: Check cache first (24-hour TTL)
        cached = self._get_cached_posts(cache_key)
        if cached:
            return cached

        # Free tier: Check quota before making API call
        if self.free_tier_mode and self._api_quota_exhausted():
            logger.warning(
                "[WARNING] Daily quota exhausted. "
                "Returning empty list. Use cache if available."
            )
            return []

        try:
            # Get source accounts
            sources = self.OFFICIAL_SOURCES.get(league, {}).get(source_type, [])
            if not sources:
                logger.warning(f"No sources configured for {league} {source_type}")
                return []

            start_time = datetime.utcnow() - timedelta(days=days)

            logger.info(
                f"Fetching {league.upper()} {source_type} posts "
                f"from official sources (days: {days})"
            )

            # Fetch posts from each official source account (free tier compatible)
            try:
                for source_handle in sources:
                    # Get user by username (free tier works)
                    user = self.client.get_user(username=source_handle.lstrip("@"))
                    if not user.data:
                        logger.warning(f"Could not find user {source_handle}")
                        continue

                    # Get user's recent tweets (free tier works)
                    tweets_response = self.client.get_users_tweets(
                        id=user.data.id,
                        start_time=start_time,
                        max_results=min(max_results // len(sources), 100),
                        tweet_fields=["created_at", "public_metrics"],
                    )

                    if tweets_response.data:
                        for tweet in tweets_response.data:
                            post = XPost(
                                post_id=tweet.id,
                                author=user.data.name,
                                author_handle=user.data.username,
                                text=tweet.text,
                                created_at=tweet.created_at,
                                likes=tweet.public_metrics.get("like_count", 0),
                                retweets=tweet.public_metrics.get("retweet_count", 0),
                                source_type=source_type,
                                league=league,
                                url=f"https://x.com/{user.data.username}/status/{tweet.id}",
                            )

                            # Calculate relevance score
                            post.relevance_score = self._calculate_relevance(
                                post.text, source_type
                            )
                            # Only include high relevance posts
                            if post.relevance_score >= 0.33:  # At least 1 keyword match
                                posts.append(post)

                logger.info(
                    f"[OK] Found {len(posts)} relevant {league} {source_type} posts"
                )

            except tweepy.TweepyException as e:
                logger.warning(f"X API error: {e}. Returning empty results.")
                return []

            # Cache results and record API call (free tier tracking)
            if posts:
                self.cache[cache_key] = posts
                self.cache_timestamps[cache_key] = datetime.now()
                self._record_api_call(league, source_type)
                logger.info(
                    f"[OK] Cached {len(posts)} posts for {cache_key} (24-hour TTL)"
                )

            return posts

        except Exception as e:
            logger.error(f"Error fetching {league} {source_type} news: {e}")
            return []

    async def get_team_news(
        self,
        team: str,
        league: str,
        days: int = 7,
        max_results: int = 50,
    ) -> List[XPost]:
        """
        Get recent posts from a specific team's X account.

        Args:
            team: Team abbreviation (e.g., "KC", "DAL", "LSU")
            league: "nfl" or "ncaaf"
            days: How many days back to search
            max_results: Maximum posts to return

        Returns:
            List of XPost objects
        """
        if not self.client:
            logger.warning("X API client not initialized")
            return []

        try:
            sources = self.OFFICIAL_SOURCES.get(league, {}).get("teams", {})
            team_handle = sources.get(team)

            if not team_handle:
                logger.warning(f"No X account configured for {team}")
                return []

            logger.info(f"Fetching posts from {team} ({team_handle})")

            start_time = datetime.utcnow() - timedelta(days=days)

            # Get user ID from handle
            user = self.client.get_user(username=team_handle.lstrip("@"))
            if not user.data:
                logger.warning(f"Could not find user {team_handle}")
                return []

            # Get user's recent tweets
            tweets = self.client.get_users_tweets(
                id=user.data.id,
                start_time=start_time,
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "public_metrics"],
            )

            posts = []
            if tweets[0]:
                for tweet in tweets[0]:
                    post = XPost(
                        post_id=tweet.id,
                        author=user.data.name,
                        author_handle=user.data.username,
                        text=tweet.text,
                        created_at=tweet.created_at,
                        likes=tweet.public_metrics.get("like_count", 0),
                        retweets=tweet.public_metrics.get("retweet_count", 0),
                        source_type="team_update",
                        league=league,
                        team=team,
                        url=f"https://x.com/{user.data.username}/status/{tweet.id}",
                    )

                    post.relevance_score = self._calculate_relevance(post.text, "news")
                    posts.append(post)

            logger.info(f"[OK] Found {len(posts)} posts from {team}")
            return posts

        except Exception as e:
            logger.error(f"Error fetching {team} news: {e}")
            return []

    def _build_search_query(self, league: str, source_type: str) -> str:
        """Build search query for league and source type."""
        sources = self.OFFICIAL_SOURCES.get(league, {}).get(source_type, [])
        sources_str = " OR ".join(sources)

        if source_type == "injury":
            keywords = " OR ".join(self.INJURY_KEYWORDS)
            return f"({sources_str}) ({keywords}) -is:retweet lang:en"
        elif source_type == "news":
            keywords = " OR ".join(self.NEWS_KEYWORDS)
            return f"({sources_str}) ({keywords}) -is:retweet lang:en"
        else:
            return f"({sources_str}) -is:retweet lang:en"

    def _calculate_relevance(self, text: str, source_type: str) -> float:
        """
        Calculate relevance score based on keywords present.

        Returns:
            Score from 0.0 to 1.0
        """
        text_lower = text.lower()
        keywords = (
            self.INJURY_KEYWORDS if source_type == "injury" else self.NEWS_KEYWORDS
        )

        matches = sum(1 for kw in keywords if kw in text_lower)
        return min(1.0, matches / 3.0)  # 3+ keywords = 1.0

    def get_quota_status(self) -> Dict[str, Any]:
        """Get current free tier quota status."""
        # Clean old calls (older than 24h)
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        self.api_calls = [c for c in self.api_calls if c["timestamp"] > cutoff]

        remaining = max(0, self.daily_limit - len(self.api_calls))
        return {
            "calls_today": len(self.api_calls),
            "daily_limit": self.daily_limit,
            "remaining": remaining,
            "exhausted": len(self.api_calls) >= self.daily_limit,
            "cache_ttl_hours": self.cache_ttl_hours,
            "cached_items": len(self.cache),
        }

    async def export_posts(
        self,
        posts: List[XPost],
        league: str,
        source_type: str = "all",
    ) -> Path:
        """Export posts to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"x_posts_{league}_{source_type}_{timestamp}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "league": league,
            "source_type": source_type,
            "count": len(posts),
            "posts": [post.to_dict() for post in posts],
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(posts)} posts to {filename}")
        return filename

    async def close(self) -> None:
        """Close API client."""
        if self.client:
            self.client = None
            logger.info("X API client closed")


async def main() -> None:
    """Demo usage."""
    scraper = XNewsScraper()

    if not await scraper.initialize():
        print(
            "X API not configured. Set environment variables: "
            "X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET"
        )
        return

    print("\n" + "=" * 70)
    print("X NEWS SCRAPER - NFL & NCAAF")
    print("=" * 70)

    # Get recent NFL injuries
    print("\n[1] Fetching NFL injuries...")
    nfl_injuries = await scraper.get_league_news("nfl", source_type="injury", days=7)
    print(f"Found {len(nfl_injuries)} relevant posts")
    for post in nfl_injuries[:3]:
        print(f"  - {post.author}: {post.text[:80]}...")

    # Get recent NCAAF news
    print("\n[2] Fetching NCAAF news...")
    ncaaf_news = await scraper.get_league_news("ncaaf", source_type="news", days=7)
    print(f"Found {len(ncaaf_news)} relevant posts")
    for post in ncaaf_news[:3]:
        print(f"  - {post.author}: {post.text[:80]}...")

    # Export results
    if nfl_injuries:
        await scraper.export_posts(nfl_injuries, "nfl", "injuries")

    await scraper.close()
    print("\n[OK] Done!")


if __name__ == "__main__":
    asyncio.run(main())
