#!/usr/bin/env python3
"""
Scrape live NFL odds using The Odds API
Fast, reliable, no browser automation needed
"""

import os
import json
from datetime import datetime
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv()


def scrape_odds_api() -> list[dict]:
    """
    Fetch live NFL odds from The Odds API

    Returns:
        List of games in Billy Walters format
    """
    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        raise ValueError("ODDS_API_KEY not found in environment")

    print("Fetching live NFL odds from The Odds API...")

    # API endpoint for NFL odds
    url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"

    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american",
        "dateFormat": "iso",
    }

    response = httpx.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    print(f"[OK] Fetched {len(data)} games")

    # Check remaining quota
    remaining = response.headers.get("x-requests-remaining")
    used = response.headers.get("x-requests-used")
    if remaining:
        print(f"API quota: {used} used, {remaining} remaining")

    # Convert to Billy Walters format
    games = []
    for event in data:
        game = convert_to_walters_format(event)
        if game:
            games.append(game)

    return games


def convert_to_walters_format(event: dict) -> dict:
    """Convert Odds API format to Billy Walters format"""

    # Get the first bookmaker (preferably a sharp book)
    bookmaker = None
    for bm in event.get("bookmakers", []):
        if bm["key"] in ["pinnacle", "bovada", "fanduel"]:
            bookmaker = bm
            break

    if not bookmaker:
        bookmaker = event["bookmakers"][0] if event.get("bookmakers") else None

    if not bookmaker:
        return None

    # Extract markets
    markets_data = {"spread": {}, "total": {}, "moneyline": {}}

    for market in bookmaker.get("markets", []):
        market_key = market["key"]

        if market_key == "spreads":
            for outcome in market["outcomes"]:
                side = "away" if outcome["name"] == event["away_team"] else "home"
                markets_data["spread"][side] = {
                    "line": float(outcome["point"]),
                    "price": int(outcome["price"]),
                }

        elif market_key == "totals":
            for outcome in market["outcomes"]:
                side = "over" if outcome["name"] == "Over" else "under"
                markets_data["total"][side] = {
                    "side": side,
                    "line": float(outcome["point"]),
                    "price": int(outcome["price"]),
                }

        elif market_key == "h2h":
            for outcome in market["outcomes"]:
                side = "away" if outcome["name"] == event["away_team"] else "home"
                markets_data["moneyline"][side] = {
                    "line": None,
                    "price": int(outcome["price"]),
                }

    # Build game object
    game_time = event.get("commence_time", "")
    event_date = game_time.split("T")[0] if game_time else None

    game = {
        "source": f"the-odds-api/{bookmaker['key']}",
        "sport": "nfl",
        "league": "NFL",
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "game_key": event.get("id", ""),
        "rotation_number": "",  # Odds API doesn't provide rotation numbers
        "event_date": event_date,
        "event_time": game_time,
        "teams": {"away": event["away_team"], "home": event["home_team"]},
        "markets": markets_data,
        "state": {},
        "is_live": False,
    }

    return game


def save_games(games: list[dict], output_dir: str = "data/odds/nfl"):
    """Save games in multiple formats"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Save as JSONL
    jsonl_file = output_path / f"nfl-odds-{timestamp}.jsonl"
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for game in games:
            f.write(json.dumps(game) + "\n")

    # Save as JSON
    json_file = output_path / f"nfl-odds-{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2)

    # Save as CSV
    csv_file = output_path / f"nfl-odds-{timestamp}.csv"
    with open(csv_file, "w", encoding="utf-8") as f:
        headers = [
            "source",
            "sport",
            "league",
            "collected_at",
            "game_key",
            "event_date",
            "event_time",
            "away_team",
            "home_team",
            "away_spread_line",
            "away_spread_price",
            "home_spread_line",
            "home_spread_price",
            "over_line",
            "over_price",
            "under_line",
            "under_price",
            "away_moneyline",
            "home_moneyline",
        ]
        f.write(",".join(headers) + "\n")

        for game in games:
            teams = game["teams"]
            markets = game["markets"]
            spread = markets.get("spread", {})
            total = markets.get("total", {})
            ml = markets.get("moneyline", {})

            row = [
                game.get("source", ""),
                game.get("sport", ""),
                game.get("league", ""),
                game.get("collected_at", ""),
                game.get("game_key", ""),
                game.get("event_date", ""),
                game.get("event_time", ""),
                teams.get("away", ""),
                teams.get("home", ""),
                spread.get("away", {}).get("line", ""),
                spread.get("away", {}).get("price", ""),
                spread.get("home", {}).get("line", ""),
                spread.get("home", {}).get("price", ""),
                total.get("over", {}).get("line", ""),
                total.get("over", {}).get("price", ""),
                total.get("under", {}).get("line", ""),
                total.get("under", {}).get("price", ""),
                ml.get("away", {}).get("price", ""),
                ml.get("home", {}).get("price", ""),
            ]
            f.write(",".join(str(v) for v in row) + "\n")

    print(f"\nSaved {len(games)} games to:")
    print(f"  JSONL: {jsonl_file}")
    print(f"  JSON:  {json_file}")
    print(f"  CSV:   {csv_file}")

    return jsonl_file, json_file, csv_file


def display_summary(games: list[dict]):
    """Display summary of scraped games"""
    print("\n" + "=" * 80)
    print(f"  NFL LIVE ODDS - {len(games)} GAMES")
    print("=" * 80)

    for game in games:
        teams = game["teams"]
        time = game.get("event_time", "")

        print(f"\n{teams['away']:30} @ {teams['home']}")
        print(f"  Time: {time}")

        spread = game["markets"]["spread"]
        if spread.get("away") and spread.get("home"):
            away_line = spread["away"].get("line")
            home_line = spread["home"].get("line")
            away_price = spread["away"].get("price")
            home_price = spread["home"].get("price")
            print(
                f"  Spread: {away_line:+5.1f} ({away_price:+4}) / "
                f"{home_line:+5.1f} ({home_price:+4})"
            )

        total = game["markets"]["total"]
        if total.get("over") and total.get("under"):
            over_line = total["over"].get("line")
            over_price = total["over"].get("price")
            under_price = total["under"].get("price")
            print(f"  Total: O/U {over_line} ({over_price:+4}/{under_price:+4})")

        ml = game["markets"]["moneyline"]
        if ml.get("away") and ml.get("home"):
            away_ml = ml["away"].get("price")
            home_ml = ml["home"].get("price")
            print(f"  ML: {away_ml:+4} / {home_ml:+4}")


if __name__ == "__main__":
    try:
        games = scrape_odds_api()

        if games:
            save_games(games)
            display_summary(games)
            print("\n[SUCCESS] Live NFL odds scraped and saved.")
        else:
            print("No games found")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
