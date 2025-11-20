"""Create 'Reverse Favorites' betting card - Best teams getting points."""

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

weather_file = Path("output/reports/saturday_weather_report_11-15-2025.json")
if weather_file.exists():
    with open(weather_file) as f:
        weather_reports = json.load(f)
        weather = {r["home_team"]: r["impact"] for r in weather_reports}
else:
    weather = {}

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


def parse_time(time_str):
    return int(time_str.split()[1].split(":")[0])


print(f"\n{'=' * 100}")
print("REVERSE FAVORITES - QUALITY TEAMS GETTING POINTS")
print(f"{'=' * 100}\n")
print("These are situations where the BETTER (or equal) team is an underdog.")
print("You're not betting 'underdogs' - you're betting QUALITY getting disrespected!\n")

reverse_favs = []

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
    total = game.get("total", {})
    market_spread = spread.get("home", 0)

    # Calculate predicted spread
    predicted_spread = (home_rating - away_rating) + 2.5
    edge = predicted_spread - market_spread

    weather_impact = weather.get(home, {})
    weather_sev = weather_impact.get("severity", "NONE")

    # SCENARIO 1: Away dog is actually the BETTER team
    if market_spread < 0 and away_rating > home_rating:
        quality_edge = away_rating - home_rating
        reverse_favs.append(
            {
                "type": "BETTER TEAM",
                "team": away,
                "opponent": home,
                "location": "away",
                "play": f"{away} {spread.get('away'):+.1f}",
                "line": spread.get("away"),
                "time": game["game_time"],
                "quality_edge": round(quality_edge, 2),
                "spread_edge": round(edge, 1),
                "away_rating": away_rating,
                "home_rating": home_rating,
                "weather": weather_sev,
                "total": total.get("points", 0),
            }
        )

    # SCENARIO 2: Away dog is EQUAL or close (within 0.5 points)
    elif market_spread < 0 and abs(away_rating - home_rating) <= 0.5:
        quality_edge = away_rating - home_rating
        reverse_favs.append(
            {
                "type": "EQUAL TEAM",
                "team": away,
                "opponent": home,
                "location": "away",
                "play": f"{away} {spread.get('away'):+.1f}",
                "line": spread.get("away"),
                "time": game["game_time"],
                "quality_edge": round(quality_edge, 2),
                "spread_edge": round(edge, 1),
                "away_rating": away_rating,
                "home_rating": home_rating,
                "weather": weather_sev,
                "total": total.get("points", 0),
            }
        )

    # SCENARIO 3: Home dog is actually the BETTER team
    elif market_spread > 0 and home_rating > away_rating:
        quality_edge = home_rating - away_rating
        reverse_favs.append(
            {
                "type": "BETTER TEAM",
                "team": home,
                "opponent": away,
                "location": "home",
                "play": f"{home} {market_spread:+.1f}",
                "line": market_spread,
                "time": game["game_time"],
                "quality_edge": round(quality_edge, 2),
                "spread_edge": round(abs(edge), 1),
                "away_rating": away_rating,
                "home_rating": home_rating,
                "weather": weather_sev,
                "total": total.get("points", 0),
            }
        )

    # SCENARIO 4: Home dog is EQUAL or close
    elif market_spread > 0 and abs(home_rating - away_rating) <= 0.5:
        quality_edge = home_rating - away_rating
        reverse_favs.append(
            {
                "type": "EQUAL TEAM",
                "team": home,
                "opponent": away,
                "location": "home",
                "play": f"{home} {market_spread:+.1f}",
                "line": market_spread,
                "time": game["game_time"],
                "quality_edge": round(quality_edge, 2),
                "spread_edge": round(abs(edge), 1),
                "away_rating": away_rating,
                "home_rating": home_rating,
                "weather": weather_sev,
                "total": total.get("points", 0),
            }
        )

# Sort by quality edge (higher = more undervalued)
reverse_favs.sort(key=lambda x: x["quality_edge"], reverse=True)

print(f"{'=' * 100}")
print(f"FOUND {len(reverse_favs)} REVERSE FAVORITE OPPORTUNITIES")
print(f"{'=' * 100}\n")

# Group by type
better_teams = [r for r in reverse_favs if r["type"] == "BETTER TEAM"]
equal_teams = [r for r in reverse_favs if r["type"] == "EQUAL TEAM"]

print(f"\n{'=' * 100}")
print(f"TIER 1: BETTER TEAM GETTING POINTS ({len(better_teams)} games)")
print(f"{'=' * 100}")
print("These teams have HIGHER power ratings than their opponents but are underdogs!\n")

for i, play in enumerate(better_teams, 1):
    weather_tag = (
        f" [{play['weather']}]" if play["weather"] in ["HIGH", "EXTREME"] else ""
    )
    team_rating = (
        play["away_rating"] if play["location"] == "away" else play["home_rating"]
    )
    opp_rating = (
        play["home_rating"] if play["location"] == "away" else play["away_rating"]
    )

    print(f"{i}. {play['play']} ({play['time']}) {weather_tag}")
    print(
        f"   Quality Edge: {play['team']} is {play['quality_edge']:.2f} points BETTER"
    )
    print(
        f"   Ratings: {play['team']} {team_rating:.2f} vs {play['opponent']} {opp_rating:.2f}"
    )
    print(f"   Spread Edge: {play['spread_edge']:.1f} points")
    print(
        f"   WHY THEY'RE UNDERDOG: {play['location'].upper()} game, market overvaluing opponent"
    )
    print()

print(f"\n{'=' * 100}")
print(f"TIER 2: EQUAL TEAMS GETTING POINTS ({len(equal_teams)} games)")
print(f"{'=' * 100}")
print("These teams are virtually EQUAL in quality but getting points!\n")

for i, play in enumerate(equal_teams, 1):
    weather_tag = (
        f" [{play['weather']}]" if play["weather"] in ["HIGH", "EXTREME"] else ""
    )
    advantage = "slight edge" if play["quality_edge"] > 0 else "slight disadvantage"
    team_rating = (
        play["away_rating"] if play["location"] == "away" else play["home_rating"]
    )
    opp_rating = (
        play["home_rating"] if play["location"] == "away" else play["away_rating"]
    )

    print(f"{i}. {play['play']} ({play['time']}) {weather_tag}")
    print(f"   Quality: VIRTUAL PICK'EM ({advantage}: {play['quality_edge']:+.2f} pts)")
    print(
        f"   Ratings: {play['team']} {team_rating:.2f} vs {play['opponent']} {opp_rating:.2f}"
    )
    print(f"   Spread Edge: {play['spread_edge']:.1f} points")
    print(f"   VALUE: Getting {abs(play['line']):.1f} points in an even matchup")
    print()

print(f"\n{'=' * 100}")
print("RECOMMENDED BETTING STRATEGY")
print(f"{'=' * 100}\n")

print(
    "TIER 1 PLAYS (Better Team): Bet with confidence - you're backing the superior team"
)
print("TIER 2 PLAYS (Equal Team): Great value - you're getting points in a coin flip\n")

# Top 10 overall
print(f"\n{'=' * 100}")
print("TOP 10 REVERSE FAVORITES (Ranked by Quality)")
print(f"{'=' * 100}\n")

for i, play in enumerate(reverse_favs[:10], 1):
    tier = "BETTER TEAM" if play["type"] == "BETTER TEAM" else "EQUAL TEAM"
    print(
        f"{i}. [{tier}] {play['play']} (Quality: {play['quality_edge']:+.2f}, Spread Edge: {play['spread_edge']:.1f})"
    )

print(f"\n{'=' * 100}\n")
