from __future__ import annotations

import json
from typing import Any, Dict, Optional
from datetime import datetime

import scrapy
from scrapy.http import Response, JsonRequest

# Local modules
from ..items import LiveGameItem, Market, QuoteSide, iso_now, game_key_from


def parse_aspnet_date(date_str: str) -> Optional[str]:
    """
    Parse ASP.NET date format: /Date(1762387201000)/
    Returns ISO format date string (YYYY-MM-DD)
    """
    try:
        if not date_str or not date_str.startswith("/Date("):
            return None
        # Extract timestamp (milliseconds since epoch)
        timestamp = int(date_str.split("(")[1].split(")")[0].split("+")[0].split("-")[0])
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def parse_aspnet_datetime(date_str: str) -> Optional[str]:
    """
    Parse ASP.NET date format: /Date(1762387201000)/
    Returns ISO format datetime string
    """
    try:
        if not date_str or not date_str.startswith("/Date("):
            return None
        timestamp = int(date_str.split("(")[1].split(")")[0].split("+")[0].split("-")[0])
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.isoformat()
    except Exception:
        return None


def parse_game_time(datetime_str: str) -> Optional[str]:
    """
    Parse GameDateTimeString: "11/05/2025 19:00"
    Returns time in format: "7:00 PM ET"
    """
    try:
        if not datetime_str:
            return None
        # Parse "11/05/2025 19:00"
        dt = datetime.strptime(datetime_str, "%m/%d/%Y %H:%M")
        # Format as "7:00 PM ET"
        time_str = dt.strftime("%-I:%M %p" if hasattr(dt, "strftime") else "%I:%M %p")
        return f"{time_str} ET"
    except Exception:
        return None


class OvertimeApiSpider(scrapy.Spider):
    """
    API-based scraper for Overtime.ag college football odds.

    This spider uses the Overtime.ag API directly instead of browser automation,
    making it 45x faster than the Playwright-based scraper!

    Usage:
        scrapy crawl overtime_api -o output.json
    """

    name = "overtime_api"

    custom_settings = {
        "BOT_NAME": "overtime_api",
        "DEFAULT_REQUEST_HEADERS": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://overtime.ag",
            "referer": "https://overtime.ag/sports",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        },
        "CONCURRENT_REQUESTS": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [429, 403, 500, 502, 503, 504],
    }

    def __init__(self, sport="cfb", *args, **kwargs):
        """
        Initialize spider.

        Args:
            sport: "cfb" for college football, "nfl" for NFL (default: "cfb")
        """
        super().__init__(*args, **kwargs)
        self.target_sport = sport.lower()

    def start_requests(self):
        """Entry point - make API request for college football odds"""
        url = "https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering"

        # Determine sport parameters
        if self.target_sport == "nfl":
            sport_type = "Football"
            sport_subtype = "NFL"
        else:  # default to college football
            sport_type = "Football"
            sport_subtype = "College Football"

        payload = {
            "sportType": sport_type,
            "sportSubType": sport_subtype,
            "wagerType": "Straight Bet",
            "hoursAdjustment": 0,
            "periodNumber": None,
            "gameNum": None,
            "parentGameNum": None,
            "teaserName": "",
            "requestMode": None,
        }

        self.logger.info(f"Requesting {sport_subtype} odds from Overtime.ag API...")

        # Use JsonRequest which automatically handles JSON payload and disables SSL verification
        yield JsonRequest(
            url=url,
            data=payload,
            callback=self.parse,
            errback=self.errback,
            dont_filter=True,
            # Disable SSL verification to avoid certificate errors
            meta={"dont_retry": False},
        )

    def errback(self, failure):
        """Handle request failures"""
        self.logger.error(f"Request failed: {failure.value}")

    def parse(self, response: Response):
        """Parse API response and yield LiveGameItem objects"""
        try:
            data = json.loads(response.text)

            # ASP.NET format - data is in 'd' key
            if "d" not in data:
                self.logger.error("No 'd' key in response")
                return

            response_data = data["d"]

            if not response_data.get("IsSuccess"):
                self.logger.error(f"API returned error: {response_data.get('Message')}")
                return

            # Extract games from Data.GameLines
            if "Data" not in response_data or "GameLines" not in response_data["Data"]:
                self.logger.warning("No GameLines found in response")
                return

            games = response_data["Data"]["GameLines"]
            self.logger.info(f"Found {len(games)} games in API response")

            # Determine sport and league
            sport_name = "college_football" if self.target_sport == "cfb" else "nfl"
            league = "NCAAF" if self.target_sport == "cfb" else "NFL"

            for game in games:
                try:
                    item = self._parse_game(game, sport_name, league)
                    if item:
                        yield item.to_dict()
                except Exception as e:
                    self.logger.error(f"Error parsing game: {e}", exc_info=True)

        except Exception as e:
            self.logger.error(f"Error parsing response: {e}", exc_info=True)

    def _parse_game(self, game_data: Dict[str, Any], sport: str, league: str) -> Optional[LiveGameItem]:
        """
        Parse a single game from the API response into a LiveGameItem.

        Key API fields:
        - Team1ID: away team name
        - Team2ID: home team name
        - GameDateTime: game time (/Date(timestamp)/ format)
        - Spread1/Spread2: spread lines (1=away, 2=home)
        - SpreadAdj1/SpreadAdj2: spread prices (juice)
        - TotalPoints: total line
        - TtlPtsAdj1/TtlPtsAdj2: total prices (1=over, 2=under)
        - MoneyLine1/MoneyLine2: moneylines (1=away, 2=home)
        - Team1RotNum/Team2RotNum: rotation numbers
        """
        away_team = game_data.get("Team1ID")
        home_team = game_data.get("Team2ID")

        if not away_team or not home_team:
            return None

        # Parse date/time
        event_date = parse_aspnet_date(game_data.get("GameDateTime"))
        event_time = parse_game_time(game_data.get("GameDateTimeString"))

        # Rotation numbers
        away_rot = game_data.get("Team1RotNum")
        home_rot = game_data.get("Team2RotNum")
        rotation_number = f"{away_rot}-{home_rot}" if away_rot and home_rot else None

        # Parse markets
        markets = self._parse_markets(game_data)

        # Create LiveGameItem
        item = LiveGameItem(
            source="overtime.ag",
            sport=sport,
            league=league,
            collected_at=iso_now(),
            game_key=game_key_from(away_team, home_team, event_date),
            event_date=event_date,
            event_time=event_time,
            rotation_number=rotation_number,
            teams={"away": away_team, "home": home_team},
            state={},  # No state for pregame
            markets=markets,
            is_live=False,
        )

        return item

    def _parse_markets(self, game_data: Dict[str, Any]) -> Dict[str, Market]:
        """
        Parse spread, total, and moneyline markets from game data.

        API conventions:
        - Spread1 = away spread, Spread2 = home spread
        - SpreadAdj1 = away price, SpreadAdj2 = home price
        - TotalPoints = total line (same for over/under)
        - TtlPtsAdj1 = over price, TtlPtsAdj2 = under price
        - MoneyLine1 = away ML, MoneyLine2 = home ML
        """
        markets = {}

        # Spread market
        spread_away = None
        spread_home = None

        away_spread_line = game_data.get("Spread1")
        away_spread_price = game_data.get("SpreadAdj1")
        home_spread_line = game_data.get("Spread2")
        home_spread_price = game_data.get("SpreadAdj2")

        if away_spread_line is not None and away_spread_price is not None:
            spread_away = QuoteSide(line=float(away_spread_line), price=int(away_spread_price))

        if home_spread_line is not None and home_spread_price is not None:
            spread_home = QuoteSide(line=float(home_spread_line), price=int(home_spread_price))

        if spread_away or spread_home:
            markets["spread"] = Market(away=spread_away, home=spread_home)

        # Total market
        total_over = None
        total_under = None

        total_line = game_data.get("TotalPoints")
        over_price = game_data.get("TtlPtsAdj1")
        under_price = game_data.get("TtlPtsAdj2")

        if total_line is not None and over_price is not None:
            total_over = QuoteSide(line=float(total_line), price=int(over_price))

        if total_line is not None and under_price is not None:
            total_under = QuoteSide(line=float(total_line), price=int(under_price))

        if total_over or total_under:
            markets["total"] = Market(over=total_over, under=total_under)

        # Moneyline market
        ml_away = None
        ml_home = None

        away_ml_price = game_data.get("MoneyLine1")
        home_ml_price = game_data.get("MoneyLine2")

        if away_ml_price is not None:
            ml_away = QuoteSide(line=None, price=int(away_ml_price))

        if home_ml_price is not None:
            ml_home = QuoteSide(line=None, price=int(home_ml_price))

        if ml_away or ml_home:
            markets["moneyline"] = Market(away=ml_away, home=ml_home)

        return markets
