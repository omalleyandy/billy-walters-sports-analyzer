#!/usr/bin/env python3
"""
Data validation hook for sports analytics data.
Validates odds, weather data, and game information.
"""

import json
import sys
from datetime import datetime


def validate_odds_data(odds: dict) -> list[str]:
    """Validate odds are within realistic ranges."""
    errors = []

    # Validate spread
    spread = odds.get("spread")
    if spread is not None:
        if not -50 < spread < 50:
            errors.append(f"Invalid spread: {spread} (must be between -50 and 50)")

    # Validate over/under
    over_under = odds.get("over_under")
    if over_under is not None:
        if not 20 < over_under < 100:
            errors.append(
                f"Invalid over/under: {over_under} (must be between 20 and 100)"
            )

    # Validate moneyline
    for team in ["home", "away"]:
        ml_key = f"moneyline_{team}"
        moneyline = odds.get(ml_key)
        if moneyline is not None:
            if not -10000 < moneyline < 10000:
                errors.append(f"Invalid {ml_key}: {moneyline} (out of realistic range)")

    return errors


def validate_weather_data(weather: dict) -> list[str]:
    """Validate weather data formats and ranges."""
    errors = []

    # Validate temperature
    temp = weather.get("temperature")
    if temp is not None:
        if not -20 < temp < 130:  # Fahrenheit
            errors.append(f"Invalid temperature: {temp}F (must be between -20 and 130)")

    # Validate wind speed
    wind = weather.get("wind_speed")
    if wind is not None:
        if not 0 <= wind < 100:
            errors.append(f"Invalid wind speed: {wind} mph (must be between 0 and 100)")

    # Validate precipitation probability
    precip = weather.get("precipitation_probability")
    if precip is not None:
        if not 0 <= precip <= 1:
            errors.append(f"Invalid precipitation probability: {precip} (must be 0-1)")

    return errors


def validate_game_data(game: dict) -> list[str]:
    """Validate game data structure."""
    errors = []

    # Check required fields
    required = ["game_id", "home_team", "away_team", "game_date"]
    for field in required:
        if field not in game:
            errors.append(f"Missing required field: {field}")

    # Validate game date format
    if "game_date" in game:
        try:
            datetime.fromisoformat(game["game_date"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            errors.append(
                f"Invalid game_date format: {game.get('game_date')} "
                "(must be ISO format)"
            )

    # Validate league
    league = game.get("league")
    if league and league not in ["NFL", "NCAAF"]:
        errors.append(f"Invalid league: {league} (must be NFL or NCAAF)")

    return errors


def main():
    """Main validation execution."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Invalid JSON input", file=sys.stderr)
        sys.exit(1)

    all_errors = []

    # Validate based on data type
    data_type = input_data.get("type")

    if data_type == "odds":
        all_errors.extend(validate_odds_data(input_data.get("data", {})))
    elif data_type == "weather":
        all_errors.extend(validate_weather_data(input_data.get("data", {})))
    elif data_type == "game":
        all_errors.extend(validate_game_data(input_data.get("data", {})))

    # Output results
    if all_errors:
        output = {"valid": False, "errors": all_errors}
    else:
        output = {"valid": True, "message": "Data validation passed!"}

    print(json.dumps(output, indent=2))
    sys.exit(0 if output["valid"] else 1)


if __name__ == "__main__":
    main()
