from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import hashlib


@dataclass
class QuoteSide:
    line: Optional[float]  # spread/total number
    price: Optional[int]   # American odds (e.g., -110)


@dataclass
class Market:
    # For spread, keys are "away","home"; for total: "over","under"; for ML: "away","home"
    away: Optional[QuoteSide] = None
    home: Optional[QuoteSide] = None
    over: Optional[QuoteSide] = None
    under: Optional[QuoteSide] = None


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
        """
        Convert this dataclass into a plain Python dictionary.

        `dataclasses.asdict()` will recursively convert nested dataclasses to
        dictionaries, which is sufficient for our needs.  If you need more
        control over serialisation (e.g. converting datetime objects), you
        should handle that in the caller.
        """
        return asdict(self)


def game_key_from(away: str, home: str, date_bucket: Optional[str] = None) -> str:
    base = f"{away.strip().lower()}@{home.strip().lower()}|{date_bucket or 'today'}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()
