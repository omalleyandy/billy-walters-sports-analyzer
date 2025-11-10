from __future__ import annotations
from typing import Any, List
import pandas as pd
from ..devtools_agent import capture_first_json
from ..utils import replay_get

HOME = "https://overtime.ag/sports#/"
def discover_endpoint() -> dict:
    cap = capture_first_json(HOME, domain_hint="overtime.ag")
    return {
        "url": cap.url, "curl": cap.as_curl(), "fetch": cap.as_fetch(),
        "status": cap.status, "headers": cap.headers,
        "sample": (cap.body or b"")[:2048].decode("utf-8","ignore"),
    }

def fetch_any(url: str, params: dict[str, Any] | None = None, headers: dict[str,str] | None = None) -> dict:
    r = replay_get(url, params=params, headers=headers); r.raise_for_status()
    try: return r.json()
    except Exception: return {"raw": r.text}

def normalize_odds(payload: dict | list) -> pd.DataFrame:
    rows: List[dict] = []
    items = payload.get("events") if isinstance(payload, dict) else payload
    if items is None: items = payload.get("data", []) if isinstance(payload, dict) else []
    for ev in items:
        markets = ev.get("markets", []) if isinstance(ev, dict) else []
        for m in markets:
            for sel in m.get("selections", []):
                rows.append({
                    "event_id": ev.get("id"),
                    "event": ev.get("name") or ev.get("matchup"),
                    "market": m.get("name") or m.get("key"),
                    "side": sel.get("name"),
                    "price": sel.get("price") or sel.get("odds"),
                    "point": sel.get("point") or sel.get("line"),
                })
    return pd.DataFrame(rows)
