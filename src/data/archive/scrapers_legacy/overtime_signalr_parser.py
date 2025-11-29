#!/usr/bin/env python3
"""
Overtime.ag SignalR Message Parser

Converts SignalR WebSocket messages from Overtime.ag to Billy Walters format.

Common SignalR message structures observed:
- gameUpdate: Full game state (teams, scores, status)
- linesUpdate: Betting lines (spread, total, moneyline)
- oddsUpdate: Odds changes (American odds format)
- scoreUpdate: Live score changes during game

Author: Billy Walters Sports Analyzer
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BillyWaltersOdds(BaseModel):
    """Billy Walters standardized odds format"""

    team: str
    rotation: Optional[int] = None
    spread: Optional[float] = None
    spread_odds: Optional[int] = None  # American odds (e.g., -110)
    moneyline: Optional[int] = None
    total: Optional[float] = None
    total_over_odds: Optional[int] = None
    total_under_odds: Optional[int] = None


class BillyWaltersGame(BaseModel):
    """Billy Walters standardized game format"""

    game_id: Optional[str] = None
    league: str = "NFL"
    sport: str = "FOOTBALL"
    game_date: Optional[str] = None
    game_time: Optional[str] = None
    status: str = "scheduled"  # scheduled, live, final
    visitor: BillyWaltersOdds
    home: BillyWaltersOdds
    period: str = "GAME"  # GAME, 1ST HALF, 1ST QUARTER
    score_visitor: Optional[int] = None
    score_home: Optional[int] = None
    quarter: Optional[str] = None
    time_remaining: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    source: str = "overtime.ag/signalr"


class OvertimeSignalRParser:
    """
    Parser for Overtime.ag SignalR WebSocket messages.

    Converts various SignalR event types into Billy Walters standardized format.
    """

    @staticmethod
    def parse_game_update(data: Dict[str, Any]) -> Optional[BillyWaltersGame]:
        """
        Parse 'gameUpdate' SignalR event.

        Expected structure (guessed based on common patterns):
        {
            "gameId": 12345,
            "visitor": {"name": "Philadelphia Eagles", "rotation": 101},
            "home": {"name": "Green Bay Packers", "rotation": 102},
            "status": "live",
            "score": {"visitor": 14, "home": 21},
            "quarter": "Q2",
            "timeRemaining": "5:32"
        }
        """
        try:
            # Extract teams
            visitor_data = data.get("visitor", {})
            home_data = data.get("home", {})

            visitor_name = visitor_data.get("name") or visitor_data.get("team")
            home_name = home_data.get("name") or home_data.get("team")

            if not visitor_name or not home_name:
                return None

            # Extract scores
            score_data = data.get("score", {})
            score_visitor = score_data.get("visitor") or score_data.get("away")
            score_home = score_data.get("home")

            # Extract status
            status = data.get("status", "scheduled")
            if status in ["in_progress", "live", "playing"]:
                status = "live"
            elif status in ["completed", "final", "finished"]:
                status = "final"

            game = BillyWaltersGame(
                game_id=str(data.get("gameId") or data.get("id")),
                status=status,
                visitor=BillyWaltersOdds(
                    team=visitor_name,
                    rotation=visitor_data.get("rotation"),
                ),
                home=BillyWaltersOdds(
                    team=home_name,
                    rotation=home_data.get("rotation"),
                ),
                score_visitor=score_visitor,
                score_home=score_home,
                quarter=data.get("quarter") or data.get("period"),
                time_remaining=data.get("timeRemaining") or data.get("clock"),
            )

            return game

        except Exception as e:
            print(f"[ERROR] Failed to parse gameUpdate: {e}")
            return None

    @staticmethod
    def parse_lines_update(data: Dict[str, Any]) -> Optional[BillyWaltersGame]:
        """
        Parse 'linesUpdate' SignalR event.

        Expected structure:
        {
            "gameId": 12345,
            "lines": {
                "visitor": {
                    "spread": -3.5,
                    "spreadOdds": -110,
                    "moneyline": -170,
                    "total": 47.5,
                    "totalOdds": -110
                },
                "home": {
                    "spread": 3.5,
                    "spreadOdds": -110,
                    "moneyline": +150,
                    "total": 47.5,
                    "totalOdds": -110
                }
            }
        }
        """
        try:
            game_id = str(data.get("gameId") or data.get("id"))
            lines = data.get("lines", {})

            visitor_lines = lines.get("visitor", {}) or lines.get("away", {})
            home_lines = lines.get("home", {})

            # Get team names if available
            visitor_name = data.get("visitor", {}).get("name", "Visitor")
            home_name = data.get("home", {}).get("name", "Home")

            game = BillyWaltersGame(
                game_id=game_id,
                visitor=BillyWaltersOdds(
                    team=visitor_name,
                    spread=OvertimeSignalRParser._parse_float(
                        visitor_lines.get("spread")
                    ),
                    spread_odds=OvertimeSignalRParser._parse_int(
                        visitor_lines.get("spreadOdds")
                    ),
                    moneyline=OvertimeSignalRParser._parse_int(
                        visitor_lines.get("moneyline")
                    ),
                    total=OvertimeSignalRParser._parse_float(
                        visitor_lines.get("total")
                    ),
                    total_over_odds=OvertimeSignalRParser._parse_int(
                        visitor_lines.get("overOdds")
                    ),
                    total_under_odds=OvertimeSignalRParser._parse_int(
                        visitor_lines.get("underOdds")
                    ),
                ),
                home=BillyWaltersOdds(
                    team=home_name,
                    spread=OvertimeSignalRParser._parse_float(home_lines.get("spread")),
                    spread_odds=OvertimeSignalRParser._parse_int(
                        home_lines.get("spreadOdds")
                    ),
                    moneyline=OvertimeSignalRParser._parse_int(
                        home_lines.get("moneyline")
                    ),
                    total=OvertimeSignalRParser._parse_float(home_lines.get("total")),
                    total_over_odds=OvertimeSignalRParser._parse_int(
                        home_lines.get("overOdds")
                    ),
                    total_under_odds=OvertimeSignalRParser._parse_int(
                        home_lines.get("underOdds")
                    ),
                ),
            )

            return game

        except Exception as e:
            print(f"[ERROR] Failed to parse linesUpdate: {e}")
            return None

    @staticmethod
    def parse_odds_update(data: Dict[str, Any]) -> Optional[BillyWaltersGame]:
        """
        Parse 'oddsUpdate' SignalR event.

        Similar to linesUpdate but may have different structure.
        """
        return OvertimeSignalRParser.parse_lines_update(data)

    @staticmethod
    def parse_score_update(data: Dict[str, Any]) -> Optional[BillyWaltersGame]:
        """
        Parse 'scoreUpdate' SignalR event.

        Expected structure:
        {
            "gameId": 12345,
            "score": {
                "visitor": 14,
                "home": 21
            },
            "quarter": "Q2",
            "timeRemaining": "5:32"
        }
        """
        try:
            game_id = str(data.get("gameId") or data.get("id"))
            score = data.get("score", {})

            visitor_score = score.get("visitor") or score.get("away")
            home_score = score.get("home")

            game = BillyWaltersGame(
                game_id=game_id,
                status="live",
                visitor=BillyWaltersOdds(team="Visitor"),
                home=BillyWaltersOdds(team="Home"),
                score_visitor=OvertimeSignalRParser._parse_int(visitor_score),
                score_home=OvertimeSignalRParser._parse_int(home_score),
                quarter=data.get("quarter") or data.get("period"),
                time_remaining=data.get("timeRemaining") or data.get("clock"),
            )

            return game

        except Exception as e:
            print(f"[ERROR] Failed to parse scoreUpdate: {e}")
            return None

    @staticmethod
    def parse_generic_message(data: Any) -> Optional[Dict[str, Any]]:
        """
        Parse generic SignalR message.

        Returns raw data for analysis/debugging.
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "type": "generic",
            "data": data,
        }

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        """Safely parse float value"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        """Safely parse int value"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def merge_updates(
        base_game: BillyWaltersGame, update: BillyWaltersGame
    ) -> BillyWaltersGame:
        """
        Merge a game update into existing game data.

        Preserves non-None fields from base, updates with new values from update.
        """
        merged_data = base_game.model_dump()

        for key, value in update.model_dump().items():
            if value is not None:
                if key in ["visitor", "home"]:
                    # Merge nested odds data
                    for odds_key, odds_value in value.items():
                        if odds_value is not None:
                            merged_data[key][odds_key] = odds_value
                else:
                    merged_data[key] = value

        return BillyWaltersGame(**merged_data)


def example_usage():
    """Example of parsing SignalR messages"""

    # Example game update
    game_update = {
        "gameId": 12345,
        "visitor": {"name": "Philadelphia Eagles", "rotation": 101},
        "home": {"name": "Green Bay Packers", "rotation": 102},
        "status": "live",
        "score": {"visitor": 14, "home": 21},
        "quarter": "Q2",
        "timeRemaining": "5:32",
    }

    parser = OvertimeSignalRParser()
    game = parser.parse_game_update(game_update)

    if game:
        print("Parsed game:")
        print(game.model_dump_json(indent=2))

    # Example lines update
    lines_update = {
        "gameId": 12345,
        "lines": {
            "visitor": {
                "spread": -3.5,
                "spreadOdds": -110,
                "moneyline": -170,
                "total": 47.5,
            },
            "home": {
                "spread": 3.5,
                "spreadOdds": -110,
                "moneyline": 150,
                "total": 47.5,
            },
        },
    }

    lines_game = parser.parse_lines_update(lines_update)

    if lines_game:
        print("\nParsed lines:")
        print(lines_game.model_dump_json(indent=2))

    # Merge updates
    if game and lines_game:
        merged = parser.merge_updates(game, lines_game)
        print("\nMerged game:")
        print(merged.model_dump_json(indent=2))


if __name__ == "__main__":
    example_usage()
