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
    sport: str                  # "ncaa_football"
    league: str                 # "NCAAF"
    collected_at: str           # ISO8601Z
    game_key: str               # stable hash of matchup + date bucket
    event_date: Optional[str]   # if available (ISO), else None
    teams: Dict[str, str]       # {"away": "...", "home": "..."}
    state: Dict[str, Any]       # {"quarter": 4, "clock": "03:24"} best-effort
    markets: Dict[str, Market]  # {"spread": Market(...), "total": Market(...), "moneyline": Market(...)}

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # flatten nested dataclasses
        for k, v in list(d.get("markets", {}).items()):
            if isinstance(v, dict):
                for kk, vv in list(v.items()):
                    if isinstance(vv, dict):
                        pass
        return d


def game_key_from(away: str, home: str, date_bucket: Optional[str] = None) -> str:
    base = f"{away.strip().lower()}@{home.strip().lower()}|{date_bucket or 'today'}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()
