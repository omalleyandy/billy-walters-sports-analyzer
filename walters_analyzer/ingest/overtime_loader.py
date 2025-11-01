from __future__ import annotations
from typing import List, Dict, Any
import orjson, pathlib

def load_overtime_jsonl(path: str | pathlib.Path) -> List[Dict[str, Any]]:
    path = pathlib.Path(path)
    out: List[Dict[str, Any]] = []
    with path.open("rb") as f:
        for line in f:
            out.append(orjson.loads(line))
    return out

# Example adapter that returns the minimal structure wk-card expects
def to_market_snapshots(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    snaps = []
    for r in rows:
        teams = r.get("teams", {})
        markets = r.get("markets", {})
        snaps.append({
            "book": "overtime.ag",
            "league": r.get("league"),
            "sport": r.get("sport"),
            "game_key": r.get("game_key"),
            "away": teams.get("away"),
            "home": teams.get("home"),
            "spread": markets.get("spread"),
            "total": markets.get("total"),
            "moneyline": markets.get("moneyline"),
            "collected_at": r.get("collected_at"),
        })
    return snaps