from __future__ import annotations
from typing import Any
import pandas as pd
from bs4 import BeautifulSoup
from ..devtools_agent import capture_first_json
from ..utils import replay_get

GAMES_URL = "https://masseyratings.com/cf/fbs/games"


def discover_endpoint() -> dict:
    cap = capture_first_json(GAMES_URL, domain_hint="masseyratings.com")
    return {
        "url": cap.url,
        "curl": cap.as_curl(),
        "fetch": cap.as_fetch(),
        "status": cap.status,
        "headers": cap.headers,
        "sample": (cap.body or b"")[:2048].decode("utf-8", "ignore"),
    }


def fetch_games(params: dict[str, Any]) -> pd.DataFrame:
    r = replay_get(GAMES_URL, params=params)
    r.raise_for_status()
    ct = r.headers.get("content-type", "")
    if "text/csv" in ct:
        from io import StringIO

        return pd.read_csv(StringIO(r.text))
    if "application/json" in ct:
        return pd.json_normalize(r.json())
    # HTML fallback
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    if not table:
        return pd.DataFrame()
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    rows = []
    for tr in table.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if tds:
            rows.append(dict(zip(headers, tds + [""] * (len(headers) - len(tds)))))
    return pd.DataFrame(rows)
