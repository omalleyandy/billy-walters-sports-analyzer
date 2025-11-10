"""
Live market data feed clients for various sportsbooks
"""

from typing import Dict, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod
import httpx
from walters_analyzer.config import get_settings


class MarketDataFeed(ABC):
    """Abstract base class for market data feeds"""

    def __init__(self, book_name: str):
        self.book_name = book_name
        self.settings = get_settings()

    @abstractmethod
    async def get_odds(self, sport: str, game_id: Optional[str] = None) -> List[Dict]:
        """Fetch current odds for a sport or specific game"""
        pass

    @abstractmethod
    async def get_line_history(
        self, game_id: str, market: str = "spread"
    ) -> List[Dict]:
        """Get historical line movements for a game"""
        pass


class OddsAPIClient(MarketDataFeed):
    """
    The Odds API - Aggregates multiple books
    https://the-odds-api.com/

    Free tier: 500 requests/month
    Paid: $50-$200/month
    """

    def __init__(self):
        super().__init__("OddsAPI")
        self.base_url = "https://api.the-odds-api.com/v4"
        self.api_key = getattr(self.settings, "odds_api_key", None)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_odds(self, sport: str, game_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch odds from The Odds API

        Args:
            sport: Sport key (e.g., "americanfootball_nfl", "americanfootball_ncaaf")
            game_id: Optional specific game ID to fetch

        Returns:
            List of normalized odds dictionaries

        Example:
            client = OddsAPIClient()
            odds = await client.get_odds("americanfootball_nfl")
        """
        if not self.api_key:
            print("⚠️  ODDS_API_KEY not set. Add to .env file.")
            return []

        endpoint = f"{self.base_url}/sports/{sport}/odds"

        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "spreads,totals,h2h",
            "oddsFormat": "american",
        }

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()
            return self._normalize_odds(data)

        except httpx.HTTPError as e:
            print(f"❌ Error fetching odds: {e}")
            return []

    async def get_line_history(
        self, game_id: str, market: str = "spread"
    ) -> List[Dict]:
        """
        Get historical line movements (requires paid tier)

        Note: This requires The Odds API Historical endpoint (paid tier only)
        """
        print("⚠️  Line history requires paid tier of The Odds API")
        return []

    def _normalize_odds(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Normalize Odds API response to standard format

        Standard format:
        {
            'book': str,
            'game_id': str,
            'sport': str,
            'teams': {'away': str, 'home': str},
            'commence_time': str,
            'markets': {
                'spread': {
                    'away': {'line': float, 'price': int},
                    'home': {'line': float, 'price': int}
                },
                'total': {
                    'over': {'line': float, 'price': int},
                    'under': {'line': float, 'price': int}
                },
                'moneyline': {
                    'away': {'price': int},
                    'home': {'price': int}
                }
            },
            'timestamp': str
        }
        """
        normalized = []

        for game in raw_data:
            # Get basic game info
            game_id = game.get("id")
            sport_key = game.get("sport_key")
            away_team = game.get("away_team")
            home_team = game.get("home_team")
            commence_time = game.get("commence_time")

            # Extract bookmaker odds
            for bookmaker in game.get("bookmakers", []):
                book_name = bookmaker.get("title")

                normalized_game = {
                    "book": book_name,
                    "game_id": game_id,
                    "sport": sport_key,
                    "teams": {"away": away_team, "home": home_team},
                    "commence_time": commence_time,
                    "markets": self._extract_markets(bookmaker.get("markets", [])),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                normalized.append(normalized_game)

        return normalized

    def _extract_markets(self, markets: List[Dict]) -> Dict:
        """Extract spread, total, and moneyline from markets"""
        result = {}

        for market in markets:
            market_key = market.get("key")
            outcomes = market.get("outcomes", [])

            if market_key == "spreads" and len(outcomes) >= 2:
                # Outcomes: [away, home]
                result["spread"] = {
                    "away": {
                        "line": outcomes[0].get("point"),
                        "price": outcomes[0].get("price"),
                    },
                    "home": {
                        "line": outcomes[1].get("point"),
                        "price": outcomes[1].get("price"),
                    },
                }

            elif market_key == "totals" and len(outcomes) >= 2:
                # Outcomes: [over, under]
                result["total"] = {
                    "over": {
                        "line": outcomes[0].get("point"),
                        "price": outcomes[0].get("price"),
                    },
                    "under": {
                        "line": outcomes[1].get("point"),
                        "price": outcomes[1].get("price"),
                    },
                }

            elif market_key == "h2h" and len(outcomes) >= 2:
                # Outcomes: [away, home]
                result["moneyline"] = {
                    "away": {"price": outcomes[0].get("price")},
                    "home": {"price": outcomes[1].get("price")},
                }

        return result


class PinnacleClient(MarketDataFeed):
    """
    Pinnacle (sharp book) data feed

    Requires: Funded Pinnacle account
    API Docs: https://pinnacleapi.github.io/
    """

    def __init__(self):
        super().__init__("Pinnacle")
        self.base_url = self.settings.data_connections.pinnacle_api_endpoint
        self.api_key = getattr(self.settings, "pinnacle_api_key", None)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_odds(self, sport: str, game_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch Pinnacle odds

        Note: Requires Pinnacle API credentials
        """
        if not self.api_key:
            print("⚠️  PINNACLE_API_KEY not set. Requires funded Pinnacle account.")
            return []

        endpoint = f"{self.base_url}/v1/odds"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        params = {
            "sportId": self._get_sport_id(sport),
            "oddsFormat": "AMERICAN",
            "isLive": False,
        }

        try:
            response = await self.client.get(endpoint, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            return self._normalize_pinnacle_odds(data)

        except httpx.HTTPError as e:
            print(f"❌ Error fetching Pinnacle odds: {e}")
            return []

    async def get_line_history(
        self, game_id: str, market: str = "spread"
    ) -> List[Dict]:
        """Get Pinnacle line movement history"""
        # Pinnacle doesn't provide historical data via API
        print("⚠️  Pinnacle API doesn't provide historical line data")
        return []

    def _get_sport_id(self, sport: str) -> int:
        """Map sport name to Pinnacle sport ID"""
        sport_map = {"nfl": 15, "ncaaf": 8, "nba": 4, "mlb": 3, "nhl": 1}
        return sport_map.get(sport.lower(), 15)

    def _normalize_pinnacle_odds(self, raw_data: Dict) -> List[Dict]:
        """Normalize Pinnacle API response to standard format"""
        # Implementation depends on Pinnacle's actual API structure
        # This is a placeholder
        normalized = []
        # TODO: Parse Pinnacle response format
        return normalized


class DraftKingsClient(MarketDataFeed):
    """
    DraftKings (public book) data feed

    Note: DraftKings doesn't have a public API
    Use The Odds API or scraping instead
    """

    def __init__(self):
        super().__init__("DraftKings")
        self.base_url = self.settings.data_connections.draftkings_api_endpoint

    async def get_odds(self, sport: str, game_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch DraftKings odds

        Note: DraftKings doesn't offer a public API
        Recommend using The Odds API instead which includes DraftKings
        """
        print("⚠️  DraftKings doesn't have a public API. Use The Odds API instead.")
        return []

    async def get_line_history(
        self, game_id: str, market: str = "spread"
    ) -> List[Dict]:
        """Get DraftKings line movement history"""
        print("⚠️  DraftKings doesn't have a public API. Use The Odds API instead.")
        return []


# Utility function to get appropriate client
def get_client(book_name: str) -> MarketDataFeed:
    """
    Factory function to get the appropriate client for a book

    Args:
        book_name: Name of the sportsbook

    Returns:
        MarketDataFeed client instance

    Example:
        client = get_client("Pinnacle")
        odds = await client.get_odds("nfl")
    """
    clients = {
        "oddsapi": OddsAPIClient,
        "the-odds-api": OddsAPIClient,
        "pinnacle": PinnacleClient,
        "draftkings": DraftKingsClient,
    }

    client_class = clients.get(book_name.lower(), OddsAPIClient)
    return client_class()
