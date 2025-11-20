"""Comprehensive edge detection for Saturday NCAAF games using Billy Walters methodology."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Team name mapping (odds file → ratings file)
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
    "East Carolina": "East Carolina",  # Same
}


def normalize_team_name(name: str) -> str:
    """Normalize team name for ratings lookup."""
    return TEAM_NAME_MAP.get(name, name)


# Load power ratings
def load_power_ratings() -> Dict[str, float]:
    """Load NCAAF power ratings."""
    ratings_file = Path("data/power_ratings/ncaaf_2025_week_11.json")
    with open(ratings_file) as f:
        data = json.load(f)
        return data.get("ratings", {})


# Load odds
def load_saturday_odds() -> List[Dict]:
    """Load Saturday odds data (latest file automatically)."""
    # Find the latest odds file
    odds_dir = Path("output/overtime/ncaaf/pregame")
    odds_files = sorted(odds_dir.glob("api_walters_*.json"), reverse=True)

    if not odds_files:
        raise FileNotFoundError("No odds files found!")

    odds_file = odds_files[0]  # Most recent file
    print(f"  Using odds file: {odds_file.name}")

    with open(odds_file) as f:
        data = json.load(f)

    # Filter for full games only on Saturday
    all_games = data.get("games", [])
    return [
        g
        for g in all_games
        if g.get("period") == "Game" and "11/15/2025" in g.get("game_time", "")
    ]


# Load weather adjustments
def load_weather_adjustments() -> Dict[str, Dict]:
    """Load weather impact adjustments."""
    weather_file = Path("output/reports/saturday_weather_report_11-15-2025.json")
    if not weather_file.exists():
        return {}

    with open(weather_file) as f:
        weather_reports = json.load(f)

    # Index by home team
    return {report["home_team"]: report["impact"] for report in weather_reports}


def calculate_predicted_spread(
    away_rating: float, home_rating: float, hfa: float = 2.5
) -> float:
    """Calculate predicted spread using power ratings.

    Positive = home favored, Negative = away favored
    """
    return (home_rating - away_rating) + hfa


def calculate_edge(predicted_line: float, market_line: float) -> float:
    """Calculate edge (predicted - market).

    Positive edge = value on away team
    Negative edge = value on home team
    """
    return predicted_line - market_line


def classify_edge(edge: float) -> Tuple[str, str]:
    """Classify edge strength using Billy Walters methodology.

    Returns (grade, recommended_stake)
    """
    abs_edge = abs(edge)

    if abs_edge >= 7:
        return ("MAX BET", "5%")
    elif abs_edge >= 4:
        return ("STRONG", "3%")
    elif abs_edge >= 2:
        return ("MODERATE", "2%")
    elif abs_edge >= 1:
        return ("LEAN", "1%")
    else:
        return ("NO PLAY", "0%")


def calculate_total_edge(
    away_rating: float,
    home_rating: float,
    market_total: float,
    weather_adj: float = 0.0,
) -> Tuple[float, float]:
    """Calculate predicted total and edge.

    Returns (predicted_total, edge)
    """
    # Simple total prediction: average of ratings * scoring multiplier
    avg_rating = (away_rating + home_rating) / 2
    predicted_total = avg_rating * 7.0  # Rough multiplier for NCAAF

    # Apply weather adjustment
    predicted_total += weather_adj

    # Edge = predicted - market (positive = OVER, negative = UNDER)
    edge = predicted_total - market_total

    return predicted_total, edge


def main():
    """Main edge detection function."""

    print(f"\n{'=' * 100}")
    print("SATURDAY NCAAF EDGE DETECTION - Billy Walters Methodology")
    print(f"{'=' * 100}\n")

    # Load data
    print("[1/4] Loading power ratings...")
    ratings = load_power_ratings()
    print(f"  Loaded {len(ratings)} team ratings")

    print("[2/4] Loading Saturday odds...")
    games = load_saturday_odds()
    print(f"  Loaded {len(games)} games")

    print("[3/4] Loading weather adjustments...")
    weather = load_weather_adjustments()
    print(f"  Loaded {len(weather)} weather reports")

    print("[4/4] Calculating edges...\n")

    # Calculate edges for all games
    spread_edges = []
    total_edges = []
    missing_ratings = set()

    for game in games:
        away_team = game["away_team"]
        home_team = game["home_team"]
        spread = game.get("spread", {})
        total = game.get("total", {})

        # Get ratings (normalize team names first)
        away_rating = ratings.get(normalize_team_name(away_team))
        home_rating = ratings.get(normalize_team_name(home_team))

        if not away_rating or not home_rating:
            missing_ratings.add(away_team if not away_rating else home_team)
            continue

        # Get weather adjustment
        weather_impact = weather.get(home_team, {})
        total_adj = weather_impact.get("total_adjustment", 0.0)
        spread_adj = weather_impact.get("spread_adjustment", 0.0)

        # SPREAD EDGE
        market_spread = spread.get("home", 0.0)  # Negative = home favored
        predicted_spread = calculate_predicted_spread(away_rating, home_rating)
        predicted_spread += spread_adj  # Apply weather adjustment

        edge = calculate_edge(predicted_spread, market_spread)
        grade, stake = classify_edge(edge)

        if abs(edge) >= 1.0:  # Only track edges >= 1 point
            spread_edges.append(
                {
                    "game": f"{away_team} @ {home_team}",
                    "away_team": away_team,
                    "home_team": home_team,
                    "game_time": game.get("game_time"),
                    "market_spread": market_spread,
                    "predicted_spread": round(predicted_spread, 1),
                    "edge": round(edge, 1),
                    "grade": grade,
                    "stake": stake,
                    "recommendation": f"{away_team} {spread.get('away', 0):+.1f}"
                    if edge > 0
                    else f"{home_team} {market_spread:+.1f}",
                    "weather_adj": spread_adj,
                    "power_ratings": f"{away_team}: {away_rating:.2f}, {home_team}: {home_rating:.2f}",
                }
            )

        # TOTAL EDGE
        market_total = total.get("points", 0.0)
        if market_total > 0:
            predicted_total, total_edge = calculate_total_edge(
                away_rating, home_rating, market_total, total_adj
            )

            total_grade, total_stake = classify_edge(total_edge)

            if abs(total_edge) >= 1.0:  # Only track edges >= 1 point
                total_edges.append(
                    {
                        "game": f"{away_team} @ {home_team}",
                        "away_team": away_team,
                        "home_team": home_team,
                        "game_time": game.get("game_time"),
                        "market_total": market_total,
                        "predicted_total": round(predicted_total, 1),
                        "edge": round(total_edge, 1),
                        "grade": total_grade,
                        "stake": total_stake,
                        "recommendation": f"OVER {market_total}"
                        if total_edge > 0
                        else f"UNDER {market_total}",
                        "weather_adj": total_adj,
                        "weather_severity": weather_impact.get("severity", "NONE"),
                        "power_ratings": f"{away_team}: {away_rating:.2f}, {home_team}: {home_rating:.2f}",
                    }
                )

    # Sort by edge strength
    spread_edges.sort(key=lambda x: abs(x["edge"]), reverse=True)
    total_edges.sort(key=lambda x: abs(x["edge"]), reverse=True)

    # Print spread edges
    print(f"\n{'=' * 100}")
    print(f"SPREAD EDGES ({len(spread_edges)} opportunities found)")
    print(f"{'=' * 100}\n")

    for i, edge in enumerate(spread_edges[:20], 1):  # Top 20
        print(f"{i}. [{edge['grade']}] {edge['game']}")
        print(f"   Game Time: {edge['game_time']}")
        print(f"   Market: {edge['market_spread']:+.1f}")
        print(
            f"   Predicted: {edge['predicted_spread']:+.1f} (weather adj: {edge['weather_adj']:+.1f})"
        )
        print(f"   Edge: {edge['edge']:+.1f} points")
        print(f"   PLAY: {edge['recommendation']} ({edge['stake']} Kelly)")
        print(f"   Ratings: {edge['power_ratings']}")
        print()

    # Print total edges
    print(f"\n{'=' * 100}")
    print(f"TOTAL EDGES ({len(total_edges)} opportunities found)")
    print(f"{'=' * 100}\n")

    for i, edge in enumerate(total_edges[:20], 1):  # Top 20
        weather_tag = (
            "[RAIN]" if edge.get("weather_severity") in ["HIGH", "EXTREME"] else ""
        )
        print(f"{i}. [{edge['grade']}] {edge['game']} {weather_tag}")
        print(f"   Game Time: {edge['game_time']}")
        print(f"   Market: {edge['market_total']:.1f}")
        print(
            f"   Predicted: {edge['predicted_total']:.1f} (weather adj: {edge['weather_adj']:+.1f})"
        )
        print(f"   Edge: {edge['edge']:+.1f} points")
        print(f"   PLAY: {edge['recommendation']} ({edge['stake']} Kelly)")
        print(f"   Ratings: {edge['power_ratings']}")
        print()

    # Summary
    print(f"\n{'=' * 100}")
    print("SUMMARY")
    print(f"{'=' * 100}")

    # Count by grade
    max_bet_spreads = [e for e in spread_edges if e["grade"] == "MAX BET"]
    strong_spreads = [e for e in spread_edges if e["grade"] == "STRONG"]
    moderate_spreads = [e for e in spread_edges if e["grade"] == "MODERATE"]

    max_bet_totals = [e for e in total_edges if e["grade"] == "MAX BET"]
    strong_totals = [e for e in total_edges if e["grade"] == "STRONG"]
    moderate_totals = [e for e in total_edges if e["grade"] == "MODERATE"]

    print("\nSPREAD OPPORTUNITIES:")
    print(f"  MAX BET (7+ pts):     {len(max_bet_spreads)}")
    print(f"  STRONG (4-7 pts):     {len(strong_spreads)}")
    print(f"  MODERATE (2-4 pts):   {len(moderate_spreads)}")
    print(f"  Total:                {len(spread_edges)}")

    print("\nTOTAL OPPORTUNITIES:")
    print(f"  MAX BET (7+ pts):     {len(max_bet_totals)}")
    print(f"  STRONG (4-7 pts):     {len(strong_totals)}")
    print(f"  MODERATE (2-4 pts):   {len(moderate_totals)}")
    print(f"  Total:                {len(total_edges)}")

    print(
        f"\nWeather-impacted games: {len([e for e in total_edges if e.get('weather_severity') in ['HIGH', 'EXTREME']])}"
    )

    if missing_ratings:
        print(f"\nTeams without ratings: {', '.join(sorted(missing_ratings))}")

    # Save results
    output = {
        "metadata": {
            "generated_at": "2025-11-15T12:00:00",
            "games_analyzed": len(games),
            "spread_edges_found": len(spread_edges),
            "total_edges_found": len(total_edges),
        },
        "spread_edges": spread_edges,
        "total_edges": total_edges,
    }

    output_file = Path("output/reports/saturday_edge_detection_11-15-2025.json")
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n[SAVED] {output_file}")
    print(f"{'=' * 100}\n")


if __name__ == "__main__":
    main()
