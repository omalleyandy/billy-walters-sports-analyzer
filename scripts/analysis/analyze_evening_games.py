"""Analyze evening games (7:00 PM ET and later) for Saturday NCAAF."""

import json
from pathlib import Path
from typing import Dict, List


# Load data
def load_power_ratings() -> Dict[str, float]:
    """Load NCAAF power ratings."""
    ratings_file = Path("data/power_ratings/ncaaf_2025_week_11.json")
    with open(ratings_file) as f:
        data = json.load(f)
        return data.get("ratings", {})


def load_latest_odds() -> List[Dict]:
    """Load latest odds."""
    odds_dir = Path("output/overtime/ncaaf/pregame")
    odds_files = sorted(odds_dir.glob("api_walters_*.json"), reverse=True)
    odds_file = odds_files[0]

    with open(odds_file) as f:
        data = json.load(f)

    return data.get("games", [])


def load_weather() -> Dict[str, Dict]:
    """Load weather data."""
    weather_file = Path("output/reports/saturday_weather_report_11-15-2025.json")
    if not weather_file.exists():
        return {}

    with open(weather_file) as f:
        weather_reports = json.load(f)

    return {r["home_team"]: r["impact"] for r in weather_reports}


# Team name mapping
TEAM_NAME_MAP = {
    "Miami Florida": "Miami FL",
    "Boise State": "Boise St",
    "Central Florida": "UCF",
    "Coastal Carolina": "Coastal Car",
    "Washington State": "Washington St",
    "Penn State": "Penn St",
    "Florida State": "Florida St",
    "Michigan State": "Michigan St",
    "Fresno State": "Fresno St",
    "San Diego State": "San Diego St",
    "San Jose State": "San Jose St",
    "Utah State": "Utah St",
    "Colorado State": "Colorado St",
    "New Mexico State": "New Mexico St",
    "Mississippi State": "Mississippi St",
    "Western Kentucky": "WKU",
    "Middle Tennessee State": "MTSU",
    "Appalachian State": "Appalachian St",
    "Florida Atlantic": "FL Atlantic",
    "Florida International": "Florida Intl",
    "UL Monroe": "ULM",
    "Georgia Southern": "Ga Southern",
    "Texas State": "Texas St",
    "Kennesaw State": "Kennesaw",
    "Jacksonville State": "Jacksonville St",
}


def normalize_team_name(name: str) -> str:
    return TEAM_NAME_MAP.get(name, name)


def calculate_edge(away_rating, home_rating, market_spread, weather_adj=0, hfa=2.5):
    """Calculate spread edge."""
    predicted = (home_rating - away_rating) + hfa + weather_adj
    return predicted - market_spread


def calculate_total_edge(away_rating, home_rating, market_total, weather_adj=0):
    """Calculate total edge."""
    avg_rating = (away_rating + home_rating) / 2
    predicted = avg_rating * 7.0 + weather_adj
    return predicted - market_total


def classify_edge(edge):
    """Classify edge strength."""
    abs_edge = abs(edge)
    if abs_edge >= 7:
        return "MAX BET", "5%"
    elif abs_edge >= 4:
        return "STRONG", "3%"
    elif abs_edge >= 2:
        return "MODERATE", "2%"
    elif abs_edge >= 1:
        return "LEAN", "1%"
    return "NO PLAY", "0%"


def parse_time(time_str):
    """Parse game time to hour."""
    # Format: "11/15/2025 19:00"
    return int(time_str.split()[1].split(":")[0])


def main():
    print(f"\n{'=' * 100}")
    print("EVENING GAMES ANALYSIS (7:00 PM ET and Later)")
    print(f"{'=' * 100}\n")

    # Load data
    ratings = load_power_ratings()
    all_games = load_latest_odds()
    weather = load_weather()

    # Filter for evening games (19:00 = 7:00 PM or later)
    evening_games = [
        g
        for g in all_games
        if g.get("period") == "Game"
        and "11/15/2025" in g.get("game_time", "")
        and parse_time(g.get("game_time", "00:00")) >= 19
    ]

    print(f"Found {len(evening_games)} evening games (7:00 PM ET+)\n")

    # Analyze each game
    games_analysis = []

    for game in evening_games:
        away = game["away_team"]
        home = game["home_team"]

        away_rating = ratings.get(normalize_team_name(away))
        home_rating = ratings.get(normalize_team_name(home))

        if not away_rating or not home_rating:
            continue

        spread = game.get("spread", {})
        total = game.get("total", {})

        weather_impact = weather.get(home, {})
        total_adj = weather_impact.get("total_adjustment", 0)
        spread_adj = weather_impact.get("spread_adjustment", 0)
        weather_sev = weather_impact.get("severity", "NONE")

        # Calculate edges
        market_spread = spread.get("home", 0)
        spread_edge = calculate_edge(
            away_rating, home_rating, market_spread, spread_adj
        )
        spread_grade, spread_stake = classify_edge(spread_edge)

        market_total = total.get("points", 0)
        total_edge = calculate_total_edge(
            away_rating, home_rating, market_total, total_adj
        )
        total_grade, total_stake = classify_edge(total_edge)

        games_analysis.append(
            {
                "game": f"{away} @ {home}",
                "time": game["game_time"],
                "away": away,
                "home": home,
                "spread": {
                    "market": market_spread,
                    "edge": round(spread_edge, 1),
                    "grade": spread_grade,
                    "stake": spread_stake,
                    "away_line": spread.get("away"),
                    "away_odds": spread.get("away_odds"),
                },
                "total": {
                    "market": market_total,
                    "edge": round(total_edge, 1),
                    "grade": total_grade,
                    "stake": total_stake,
                    "over_odds": total.get("over_odds"),
                    "under_odds": total.get("under_odds"),
                },
                "weather": weather_sev,
                "ratings": {"away": away_rating, "home": home_rating},
            }
        )

    # Sort by time
    games_analysis.sort(key=lambda x: x["time"])

    # Group by time slot
    time_slots = {}
    for g in games_analysis:
        hour = parse_time(g["time"])
        slot = f"{hour}:00 PM ET" if hour <= 12 else f"{hour - 12}:00 PM ET"
        if slot not in time_slots:
            time_slots[slot] = []
        time_slots[slot].append(g)

    # Print analysis
    for slot in sorted(time_slots.keys(), key=lambda x: int(x.split(":")[0])):
        games = time_slots[slot]
        print(f"\n{'=' * 100}")
        print(f"{slot} ({len(games)} games)")
        print(f"{'=' * 100}\n")

        for game in games:
            weather_tag = (
                f" [{game['weather']}]"
                if game["weather"] in ["HIGH", "EXTREME"]
                else ""
            )
            print(f"{game['game']}{weather_tag}")
            print(
                f"  Ratings: {game['away']} {game['ratings']['away']:.2f} vs {game['home']} {game['ratings']['home']:.2f}"
            )

            # Spread
            if game["spread"]["grade"] != "NO PLAY":
                rec = (
                    f"{game['away']} {game['spread']['away_line']:+.1f}"
                    if game["spread"]["edge"] > 0
                    else f"{game['home']} {game['spread']['market']:+.1f}"
                )
                print(
                    f"  SPREAD: [{game['spread']['grade']}] {rec} ({game['spread']['edge']:+.1f} edge, {game['spread']['stake']} Kelly)"
                )

            # Total
            if game["total"]["grade"] != "NO PLAY":
                rec = "OVER" if game["total"]["edge"] > 0 else "UNDER"
                print(
                    f"  TOTAL:  [{game['total']['grade']}] {rec} {game['total']['market']:.1f} ({game['total']['edge']:+.1f} edge, {game['total']['stake']} Kelly)"
                )

            print()

    # Summary
    print(f"\n{'=' * 100}")
    print("EVENING GAMES SUMMARY")
    print(f"{'=' * 100}\n")

    max_spreads = [g for g in games_analysis if g["spread"]["grade"] == "MAX BET"]
    strong_spreads = [g for g in games_analysis if g["spread"]["grade"] == "STRONG"]

    max_totals = [g for g in games_analysis if g["total"]["grade"] == "MAX BET"]
    strong_totals = [g for g in games_analysis if g["total"]["grade"] == "STRONG"]

    print("SPREAD OPPORTUNITIES:")
    print(f"  MAX BET (7+ pts):   {len(max_spreads)}")
    print(f"  STRONG (4-7 pts):   {len(strong_spreads)}")

    print("\nTOTAL OPPORTUNITIES:")
    print(f"  MAX BET (7+ pts):   {len(max_totals)}")
    print(f"  STRONG (4-7 pts):   {len(strong_totals)}")

    print(
        f"\nWeather-impacted:    {len([g for g in games_analysis if g['weather'] in ['HIGH', 'EXTREME']])}"
    )

    print(f"\n{'=' * 100}\n")


if __name__ == "__main__":
    main()
