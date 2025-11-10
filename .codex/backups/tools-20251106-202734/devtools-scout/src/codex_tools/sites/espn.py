from __future__ import annotations
from typing import Any, List
import pandas as pd
from ..devtools_agent import capture_first_json
from ..utils import replay_get

SCOREBOARD_URL = "https://www.espn.com/college-football/scoreboard"


def discover_endpoint() -> dict:
    cap = capture_first_json(SCOREBOARD_URL, domain_hint="espn.com")
    return {
        "url": cap.url,
        "curl": cap.as_curl(),
        "fetch": cap.as_fetch(),
        "status": cap.status,
        "headers": cap.headers,
        "sample": (cap.body or b"")[:2048].decode("utf-8", "ignore"),
    }


def fetch_scoreboard(params: dict[str, Any]) -> dict[str, Any]:
    base = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
    r = replay_get(base, params=params)
    r.raise_for_status()
    return r.json()


def normalize_events(payload: dict[str, Any]) -> pd.DataFrame:
    rows: List[dict[str, Any]] = []
    for ev in payload.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        comps = comp.get("competitors", [])
        if len(comps) != 2:
            continue
        home = next((c for c in comps if c.get("homeAway") == "home"), comps[0])
        away = next((c for c in comps if c.get("homeAway") == "away"), comps[1])
        odds = (comp.get("odds") or [{}])[0]
        rows.append(
            {
                "event_id": ev.get("id"),
                "date": ev.get("date"),
                "status": comp.get("status", {}).get("type", {}).get("description"),
                "home_team": home.get("team", {}).get("displayName"),
                "away_team": away.get("team", {}).get("displayName"),
                "home_score": home.get("score"),
                "away_score": away.get("score"),
                "spread": odds.get("details"),
                "over_under": odds.get("overUnder"),
                "venue": comp.get("venue", {}).get("fullName"),
            }
        )
    return pd.DataFrame(rows)
