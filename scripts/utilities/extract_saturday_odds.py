"""Extract Saturday NCAAF odds from Overtime.ag data."""

import json
from pathlib import Path

# Load the latest odds file
odds_file = Path("output/overtime/ncaaf/pregame/api_walters_20251115_115946.json")
with open(odds_file) as f:
    data = json.load(f)

# Extract only full game lines for Saturday
all_games = data.get("games", [])
saturday_games = []
for game in all_games:
    if game.get("period") == "Game" and "11/15/2025" in game.get("game_time", ""):
        saturday_games.append(game)

# Sort by game time
saturday_games.sort(key=lambda x: x.get("game_time", ""))

# Print summary
print(f"\n{'=' * 80}")
print(f"NCAAF SATURDAY (11/15/2025) - FULL GAME LINES")
print(f"Total Games: {len(saturday_games)}")
print(f"{'=' * 80}\n")

# Group by time slots
time_slots = {}
for game in saturday_games:
    game_time = game.get("game_time", "").split()[1]  # Get just the time part
    if game_time not in time_slots:
        time_slots[game_time] = []
    time_slots[game_time].append(game)

# Print games by time slot
for time_slot in sorted(time_slots.keys()):
    games = time_slots[time_slot]
    print(f"\n{time_slot} ET ({len(games)} games)")
    print("-" * 80)

    for game in games:
        away = game.get("away_team")
        home = game.get("home_team")
        spread = game.get("spread", {})
        total = game.get("total", {})
        ml = game.get("moneyline", {})

        away_spread = spread.get("away", "N/A")
        home_spread = spread.get("home", "N/A")
        spread_odds = (
            f"({spread.get('away_odds', 'N/A')}/{spread.get('home_odds', 'N/A')})"
        )

        total_pts = total.get("points", "N/A")
        total_odds = (
            f"(O{total.get('over_odds', 'N/A')}/U{total.get('under_odds', 'N/A')})"
        )

        ml_away = ml.get("away", "N/A")
        ml_home = ml.get("home", "N/A")

        print(f"  {away:25} @ {home:25}")
        print(f"    Spread: {away_spread:+5} / {home_spread:+6} {spread_odds}")
        print(f"    Total:  {total_pts:5} {total_odds}")

        # Only print moneyline if available
        if (
            ml_away != "N/A"
            and ml_home != "N/A"
            and ml_away is not None
            and ml_home is not None
        ):
            print(f"    ML:     {ml_away:+5} / {ml_home:+6}")
        print()

print(f"\n{'=' * 80}")
print(f"Data pulled: {odds_file.name}")
print(f"{'=' * 80}\n")
