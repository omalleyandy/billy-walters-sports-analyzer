"""Find favorites with positive edges (not just underdogs)."""

import json
from pathlib import Path

# Load data
ratings_file = Path("data/power_ratings/ncaaf_2025_week_11.json")
with open(ratings_file) as f:
    ratings_data = json.load(f)
    ratings = ratings_data.get("ratings", {})

odds_dir = Path("output/overtime/ncaaf/pregame")
odds_files = sorted(odds_dir.glob("api_walters_*.json"), reverse=True)
odds_file = odds_files[0]

with open(odds_file) as f:
    odds_data = json.load(f)
    games = odds_data.get("games", [])

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


def normalize_team_name(name):
    return TEAM_NAME_MAP.get(name, name)


print(f"\n{'=' * 100}")
print(f"FAVORITES WITH POSITIVE EDGES")
print(f"{'=' * 100}\n")

favorite_edges = []

for game in games:
    if game.get("period") != "Game" or "11/15/2025" not in game.get("game_time", ""):
        continue

    away = game["away_team"]
    home = game["home_team"]

    away_rating = ratings.get(normalize_team_name(away))
    home_rating = ratings.get(normalize_team_name(home))

    if not away_rating or not home_rating:
        continue

    spread = game.get("spread", {})
    market_spread = spread.get("home", 0)

    # Calculate predicted spread
    predicted_spread = (home_rating - away_rating) + 2.5  # HFA

    # Edge calculation
    edge = predicted_spread - market_spread

    # Identify who is the market favorite
    if market_spread < 0:
        # Home team is market favorite
        market_favorite = home
        market_line = market_spread

        # Check if our model says home should be favored by MORE
        if edge < 0:  # Negative edge means home team undervalued
            favorite_edges.append(
                {
                    "game": f"{away} @ {home}",
                    "time": game["game_time"],
                    "favorite": home,
                    "market_line": market_line,
                    "predicted_line": round(predicted_spread, 1),
                    "edge": round(abs(edge), 1),
                    "play": f"{home} {market_line:.1f}",
                    "ratings": f"{away}: {away_rating:.2f}, {home}: {home_rating:.2f}",
                }
            )

    elif market_spread > 0:
        # Away team is market favorite
        market_favorite = away
        market_line = spread.get("away", 0)

        # Check if our model says away should be favored by MORE
        if edge > 0:  # Positive edge means away team undervalued
            # Calculate the away line that should exist
            predicted_away_line = -predicted_spread

            favorite_edges.append(
                {
                    "game": f"{away} @ {home}",
                    "time": game["game_time"],
                    "favorite": away,
                    "market_line": market_line,
                    "predicted_line": round(predicted_away_line, 1),
                    "edge": round(edge, 1),
                    "play": f"{away} {market_line:.1f}",
                    "ratings": f"{away}: {away_rating:.2f}, {home}: {home_rating:.2f}",
                }
            )

# Sort by edge
favorite_edges.sort(key=lambda x: x["edge"], reverse=True)

if not favorite_edges:
    print("[INFO] No favorites with positive edges found.")
    print("\nThis means:")
    print("- All market favorites are either correctly priced or overvalued")
    print("- The value is on UNDERDOGS getting too many points")
    print("- This is common in college football where public loves favorites")
else:
    print(f"Found {len(favorite_edges)} favorites with positive edges:\n")

    for i, fav in enumerate(favorite_edges, 1):
        grade = (
            "MAX BET"
            if fav["edge"] >= 7
            else "STRONG"
            if fav["edge"] >= 4
            else "MODERATE"
            if fav["edge"] >= 2
            else "LEAN"
        )

        print(f"{i}. [{grade}] {fav['game']} ({fav['time']})")
        print(f"   PLAY: {fav['play']}")
        print(f"   Market Line: {fav['market_line']:+.1f}")
        print(f"   Predicted Line: {fav['predicted_line']:+.1f}")
        print(f"   Edge: {fav['edge']:.1f} points")
        print(f"   Ratings: {fav['ratings']}")
        print()

print(f"\n{'=' * 100}")
print(f"ANALYSIS COMPLETE")
print(f"{'=' * 100}\n")

# Additional analysis
print("\nWHY ARE THERE FEW/NO FAVORITE EDGES?")
print("-" * 100)
print("1. Market Efficiency: Recreational bettors love favorites")
print("2. Line Inflation: Bookmakers shade lines toward favorites to balance action")
print("3. True Edges: Most value in NCAAF comes from inflated favorite lines")
print("4. Billy Walters Approach: Historically won by betting inflated underdogs")
print("\nRECOMMENDATION: Focus on the underdog plays identified earlier.")
print(f"{'=' * 100}\n")
