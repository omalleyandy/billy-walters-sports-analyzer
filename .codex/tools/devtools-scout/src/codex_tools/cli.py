# src/codex_tools/cli.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from io import StringIO
import json
import re

import httpx
import pandas as pd
import typer
from rich import print as rprint

app = typer.Typer(help="Endpoint discovery & scoreboard extraction")

# --- Sub-apps ---------------------------------------------------------------
espn_cmd = typer.Typer(help="ESPN scoreboard tools")
massey_cmd = typer.Typer(help="Massey Ratings tools")
overtime_cmd = typer.Typer(help="Overtime.ag capture/replay tools")

app.add_typer(espn_cmd, name="espn")
app.add_typer(massey_cmd, name="massey")
app.add_typer(overtime_cmd, name="overtime")


# ===================== ESPN =====================

@espn_cmd.command("discover")
def espn_discover():
    rprint({
        "url": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard",
        "example": "uv run codex-devtools espn pull --dates 20251106-20251109",
    })

@espn_cmd.command("pull")
def espn_pull(
    dates: str = typer.Option(..., help="YYYYMMDD or YYYYMMDD-YYYYMMDD"),
):
    base = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
    outdir = Path(__file__).resolve().parents[2] / "exports"
    outdir.mkdir(parents=True, exist_ok=True)

    def _fetch_one(d: str) -> list[dict]:
        with httpx.Client(timeout=30) as client:
            resp = client.get(base, params={"dates": d})
            resp.raise_for_status()
            data = resp.json()
        ev = data.get("events", [])
        return ev

    chunks: list[dict] = []
    if "-" in dates:
        start, end = dates.split("-", 1)
        cur = datetime.strptime(start, "%Y%m%d")
        end_dt = datetime.strptime(end, "%Y%m%d")
        while cur <= end_dt:
            chunks.extend(_fetch_one(cur.strftime("%Y%m%d")))
            cur = cur.fromordinal(cur.toordinal() + 1)
    else:
        chunks.extend(_fetch_one(dates))

    # flatten minimal fields
    rows = []
    for e in chunks:
        rows.append({
            "id": e.get("id"),
            "date": e.get("date"),
            "name": e.get("name"),
            "shortName": e.get("shortName"),
            "status": (e.get("status") or {}).get("type", {}).get("description"),
            "competitions": json.dumps(e.get("competitions", [])),
        })

    df = pd.DataFrame(rows)
    stem = f"espn_scoreboard_{dates}"
    (outdir / f"{stem}.csv").write_text(df.to_csv(index=False), encoding="utf-8")
    (outdir / f"{stem}.json").write_text(df.to_json(orient="records"), encoding="utf-8")
    try:
        df.to_parquet(outdir / f"{stem}.parquet", index=False)
    except Exception as e:
        rprint({"warn": f"parquet export skipped: {e}"})

    rprint({
        "exports": {
            "csv": str(outdir / f"{stem}.csv"),
            "json": str(outdir / f"{stem}.json"),
            "parquet": str(outdir / f"{stem}.parquet"),
        }
    })


# ===================== MASSEY =====================

@massey_cmd.command("pull")
def massey_pull(
    season: int = typer.Option(...),
    week: int = typer.Option(...),
):
    """
    Pulls Massey Ratings CFB FBS games table for a given season/week.
    Uses BeautifulSoup (bs4/html5lib) to avoid lxml dependency.
    """
    page_url = "https://masseyratings.com/cf/fbs/games"
    params = {"season": season, "week": week}

    with httpx.Client(timeout=30) as client:
        resp = client.get(page_url, params=params)
        resp.raise_for_status()
        html = resp.text

    # Parse with bs4 flavor explicitly (no lxml needed)
    tables = pd.read_html(StringIO(html), flavor="bs4")
    if not tables:
        rprint({"error": "no tables found on page"})
        raise typer.Exit(2)

    df = max(tables, key=lambda t: len(t))  # largest table heuristic
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]

    outdir = Path(__file__).resolve().parents[2] / "exports"
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"massey_cfb_{season}_wk{week:02d}"

    df.to_csv(outdir / f"{stem}.csv", index=False)
    (outdir / f"{stem}.json").write_text(df.to_json(orient="records"), encoding="utf-8")
    try:
        df.to_parquet(outdir / f"{stem}.parquet", index=False)
    except Exception as e:
        rprint({"warn": f"parquet export skipped: {e}"})

    rprint({
        "exports": {
            "csv": str(outdir / f"{stem}.csv"),
            "json": str(outdir / f"{stem}.json"),
            "parquet": str(outdir / f"{stem}.parquet"),
        }
    })


# ===================== OVERTIME =====================

from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

@overtime_cmd.command("discover")
def overtime_discover(
    out_dir: Path = typer.Option(Path("exports"), help="Where to write capture JSON"),
    headless: bool = True,
    wait_ms: int = 4000,
    max_items: int = 400,
):
    """
    Launches overtime.ag and records JSON/XHR endpoints while the app loads core markets.
    Captures url, status, content-type, and a small preview body (first 8KB if JSON).
    """
    out_dir = (Path(__file__).resolve().parents[2] / out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    outpath = out_dir / f"overtime_discover_{stamp}.json"

    captures: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120 Safari/537.36"
        ))
        page = ctx.new_page()

        def _log_response(resp):
            try:
                ct = resp.headers.get("content-type", "")
                if "json" in ct.lower():
                    u = resp.url
                    # keep only API-ish urls; trim images/fonts
                    if any(s in u for s in ("/api/", ".json", "graphql", "rest", "/odds", "/markets")):
                        rec = {
                            "url": u,
                            "status": resp.status,
                            "content_type": ct,
                            "method": resp.request.method,
                        }
                        # best-effort tiny preview
                        try:
                            body = resp.text()[:8192]
                            rec["preview"] = body
                        except Exception:
                            rec["preview"] = None
                        captures.append(rec)
            except Exception:
                pass

        page.on("response", _log_response)

        # Load the SPA root; let it settle
        page.goto("https://overtime.ag/sports#", wait_until="domcontentloaded")
        page.wait_for_timeout(wait_ms)

        # Nudge a couple of common markets (these selectors are resilient fallbacks)
        for frag in ("#/sports", "#/sports?league=NFL", "#/sports?league=NCAA%20Football"):
            try:
                page.goto(f"https://overtime.ag/sports{frag}", wait_until="networkidle")
                page.wait_for_timeout(1500)
            except Exception:
                pass

        # Trim and write
        if len(captures) > max_items:
            captures = captures[:max_items]

        with open(outpath, "w", encoding="utf-8") as f:
            json.dump({"captures": captures}, f, ensure_ascii=False, indent=2)

        ctx.close()
        browser.close()

    # Show a few JSON endpoints
    json_urls = [c["url"] for c in captures if "json" in (c.get("content_type") or "").lower()]
    rprint({"discover": str(outpath), "top_json": json_urls[:5]})

@overtime_cmd.command("list")
def overtime_list(
    discover_file: Path = typer.Argument(..., exists=True),
    limit: int = typer.Option(10, "--limit", "-n", help="Max urls to print"),
):
    data = json.loads(discover_file.read_text(encoding="utf-8"))
    caps = data.get("captures", [])
    urls = [c["url"] for c in caps if "json" in (c.get("content_type") or "").lower()]
    for i, u in enumerate(urls[:limit], 1):
        rprint(f"{i}. {u}")

@overtime_cmd.command("replay")
def overtime_replay(
    url: str = typer.Option(..., help="Captured JSON endpoint (must start with https://)"),
    params: list[str] = typer.Option([], help="key=value pairs"),
    limit: int = 200,
    save_json: Path | None = typer.Option(None, help="Optional path to save raw JSON"),
):
    if not (url.startswith("http://") or url.startswith("https://")):
        raise typer.BadParameter("url must begin with http:// or https://")

    q: dict[str, str] = {}
    for p in params:
        if "=" in p:
            k, v = p.split("=", 1)
            q[k] = v

    with httpx.Client(timeout=30) as client:
        resp = client.get(url, params=q)
        resp.raise_for_status()
        data = resp.json()

    if save_json:
        save_json.parent.mkdir(parents=True, exist_ok=True)
        save_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = data if isinstance(data, list) else data.get("data") or data.get("items") or []
    if not isinstance(rows, list):
        rows = [data]
    if limit and isinstance(rows, list):
        rows = rows[:limit]

    df = pd.DataFrame(rows)
    outdir = Path(__file__).resolve().parents[2] / "exports"
    outdir.mkdir(parents=True, exist_ok=True)
    stem = "overtime_replay_" + datetime.now().strftime("%Y%m%d-%H%M%S")

    df.to_csv(outdir / f"{stem}.csv", index=False)
    (outdir / f"{stem}.json").write_text(df.to_json(orient="records"), encoding="utf-8")
    try:
        df.to_parquet(outdir / f"{stem}.parquet", index=False)
    except Exception as e:
        rprint({"warn": f"parquet export skipped: {e}"})

    rprint({
        "url": url,
        "params": q,
        "rows": len(df),
        "exports": {
            "csv": str(outdir / f"{stem}.csv"),
            "json": str(outdir / f"{stem}.json"),
            "parquet": str(outdir / f"{stem}.parquet"),
        }
    })


if __name__ == "__main__":
    app()