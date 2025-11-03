from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Mapping, Union
from datetime import datetime, timezone
import hashlib


@dataclass
class QuoteSide:
    line: Optional[float]  # spread/total number
    price: Optional[int]   # American odds (e.g., -110)

    def to_dict(self) -> Dict[str, Optional[Union[float, int]]]:
        return {"line": self.line, "price": self.price}


@dataclass
class Market:
    # For spread, keys are "away","home"; for total: "over","under"; for ML: "away","home"
    away: Optional[QuoteSide] = None
    home: Optional[QuoteSide] = None
    over: Optional[QuoteSide] = None
    under: Optional[QuoteSide] = None

    def to_dict(self) -> Dict[str, Dict[str, Optional[Union[float, int]]]]:
        out: Dict[str, Dict[str, Optional[Union[float, int]]]] = {}
        if self.away is not None:
            out["away"] = self.away.to_dict()
        if self.home is not None:
            out["home"] = self.home.to_dict()
        if self.over is not None:
            out["over"] = self.over.to_dict()
        if self.under is not None:
            out["under"] = self.under.to_dict()
        return out


@dataclass
class LiveGameItem:
    source: str                 # "overtime.ag"
    sport: str                  # "nfl" or "college_football"
    league: str                 # "NFL" or "NCAAF"
    collected_at: str           # ISO8601Z
    game_key: str               # stable hash of matchup + date bucket
    event_date: Optional[str]   # parsed date in ISO format (e.g., "2025-11-02")
    event_time: Optional[str]   # game time as displayed (e.g., "1:00 PM ET")
    rotation_number: Optional[str]  # e.g., "451-452" or "317-318"
    teams: Dict[str, str]       # {"away": "...", "home": "..."}
    state: Dict[str, Any]       # {"quarter": 4, "clock": "03:24"} best-effort
    markets: Dict[str, Market]  # {"spread": Market(...), "total": Market(...), "moneyline": Market(...)}
    is_live: bool = False       # True for live betting, False for pre-game

    def to_dict(self) -> Dict[str, Any]:
        """Efficient conversion to a plain dictionary without JSON round-trips."""

        def _copy_mapping(mapping: Mapping[str, Any]) -> Dict[str, Any]:
            return dict(mapping) if mapping else {}

        def _normalise_side(value: Any) -> Any:
            if isinstance(value, QuoteSide):
                return value.to_dict()
            if isinstance(value, Mapping):
                return {k: _normalise_side(v) for k, v in value.items()}
            return value

        markets_dict: Dict[str, Any] = {}
        for name, market in self.markets.items():
            if isinstance(market, Market):
                markets_dict[name] = market.to_dict()
            elif isinstance(market, Mapping):
                markets_dict[name] = {k: _normalise_side(v) for k, v in market.items() if v is not None}
            else:
                markets_dict[name] = market

        return {
            "source": self.source,
            "sport": self.sport,
            "league": self.league,
            "collected_at": self.collected_at,
            "game_key": self.game_key,
            "event_date": self.event_date,
            "event_time": self.event_time,
            "rotation_number": self.rotation_number,
            "teams": _copy_mapping(self.teams),
            "state": _copy_mapping(self.state),
            "markets": markets_dict,
            "is_live": self.is_live,
        }


def game_key_from(away: str, home: str, date_bucket: Optional[str] = None) -> str:
    base = f"{away.strip().lower()}@{home.strip().lower()}|{date_bucket or 'today'}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class InjuryReportItem:
    """
    Represents a player's injury status for a specific team/game.
    
    Status values: "Out", "Doubtful", "Questionable", "Probable", "Day-to-Day"
    """
    source: str                     # "espn", "team_site", etc.
    sport: str                      # "college_football", "nfl"
    league: str                     # "NCAAF", "NFL"
    collected_at: str               # ISO8601Z timestamp
    team: str                       # Team name
    team_abbr: Optional[str]        # Team abbreviation (e.g., "ALA", "UGA")
    player_name: str                # Full player name
    position: Optional[str]         # "QB", "RB", "WR", etc.
    injury_status: str              # "Out", "Doubtful", "Questionable", "Probable", "Day-to-Day"
    injury_type: Optional[str]      # "Knee", "Ankle", "Concussion", etc.
    date_reported: Optional[str]    # When injury was reported/updated
    game_date: Optional[str]        # Upcoming game date (if available)
    opponent: Optional[str]         # Opponent for upcoming game
    notes: Optional[str]            # Additional context/notes
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def get_impact_score(self) -> int:
        """
        Return a numeric impact score based on injury status.
        Higher = more impactful to betting decision.
        """
        impact_map = {
            "out": 100,
            "doubtful": 75,
            "questionable": 50,
            "probable": 25,
            "day-to-day": 40,
        }
        return impact_map.get(self.injury_status.lower(), 0)