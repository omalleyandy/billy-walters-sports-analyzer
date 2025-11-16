"""Compare line movements between two odds files."""

import json
from pathlib import Path

# Load both odds files
old_file = Path("output/overtime/ncaaf/pregame/api_walters_20251115_122415.json")
new_file = Path("output/overtime/ncaaf/pregame/api_walters_20251115_122712.json")

with open(old_file) as f:
    old_data = json.load(f)

with open(new_file) as f:
    new_data = json.load(f)

# Index old games
old_games = {}
for game in old_data.get("games", []):
    if game.get("period") == "Game":
        key = f"{game['away_team']}@{game['home_team']}"
        old_games[key] = game

# Compare with new games
print(f"\n{'=' * 100}")
print(f"LINE MOVEMENT REPORT")
print(f"Old: {old_file.name} (12:24 PM)")
print(f"New: {new_file.name} (12:27 PM)")
print(f"{'=' * 100}\n")

movements = []

for game in new_data.get("games", []):
    if game.get("period") != "Game":
        continue

    key = f"{game['away_team']}@{game['home_team']}"
    old_game = old_games.get(key)

    if not old_game:
        print(f"[NEW] {game['away_team']} @ {game['home_team']} - Line just posted")
        continue

    # Compare spreads
    old_spread = old_game.get("spread", {}).get("home", 0)
    new_spread = game.get("spread", {}).get("home", 0)
    spread_move = new_spread - old_spread

    # Compare totals
    old_total = old_game.get("total", {}).get("points", 0)
    new_total = game.get("total", {}).get("points", 0)
    total_move = new_total - old_total

    # Only report if movement occurred
    if abs(spread_move) >= 0.5 or abs(total_move) >= 0.5:
        movements.append(
            {
                "game": f"{game['away_team']} @ {game['home_team']}",
                "time": game.get("game_time"),
                "spread": {"old": old_spread, "new": new_spread, "move": spread_move},
                "total": {"old": old_total, "new": new_total, "move": total_move},
            }
        )

if not movements:
    print("[INFO] No significant line movements detected (all lines stable)")
else:
    print(f"[ALERT] {len(movements)} games with line movement detected:\n")

    # Sort by game time
    movements.sort(key=lambda x: x["time"])

    for move in movements:
        print(f"{move['game']} ({move['time']})")

        if abs(move["spread"]["move"]) >= 0.5:
            direction = (
                "moved toward FAVORITE"
                if move["spread"]["move"] < 0
                else "moved toward UNDERDOG"
            )
            print(
                f"  Spread: {move['spread']['old']:+.1f} -> {move['spread']['new']:+.1f} ({move['spread']['move']:+.1f}) - {direction}"
            )

        if abs(move["total"]["move"]) >= 0.5:
            direction = "UNDER" if move["total"]["move"] < 0 else "OVER"
            print(
                f"  Total:  {move['total']['old']:.1f} -> {move['total']['new']:.1f} ({move['total']['move']:+.1f}) - {direction} movement"
            )

        print()

print(f"\n{'=' * 100}")
print(f"Line movement analysis complete")
print(f"{'=' * 100}\n")
