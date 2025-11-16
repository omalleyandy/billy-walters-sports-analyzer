"""Check weather for Saturday NCAAF games and apply Billy Walters impact methodology."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.accuweather_client import AccuWeatherClient
from dotenv import load_dotenv

load_dotenv()

# Team city mappings for weather lookups
TEAM_CITIES = {
    # ACC
    "Boston College": ("Chestnut Hill", "MA"),
    "Duke": ("Durham", "NC"),
    "Florida State": ("Tallahassee", "FL"),
    "Georgia Tech": ("Atlanta", "GA"),
    "Miami Florida": ("Miami", "FL"),
    "NC State": ("Raleigh", "NC"),
    "North Carolina": ("Chapel Hill", "NC"),
    "Virginia": ("Charlottesville", "VA"),
    "Virginia Tech": ("Blacksburg", "VA"),
    "Wake Forest": ("Winston-Salem", "NC"),

    # Big Ten
    "Illinois": ("Champaign", "IL"),
    "Iowa": ("Iowa City", "IA"),
    "Maryland": ("College Park", "MD"),
    "Michigan State": ("East Lansing", "MI"),
    "Penn State": ("State College", "PA"),
    "Purdue": ("West Lafayette", "IN"),
    "Washington": ("Seattle", "WA"),

    # Big 12
    "Baylor": ("Waco", "TX"),
    "BYU": ("Provo", "UT"),
    "TCU": ("Fort Worth", "TX"),
    "Texas Tech": ("Lubbock", "TX"),
    "Utah": ("Salt Lake City", "UT"),

    # SEC
    "Alabama": ("Tuscaloosa", "AL"),
    "Florida": ("Gainesville", "FL"),
    "Georgia": ("Athens", "GA"),
    "Mississippi": ("Oxford", "MS"),
    "Mississippi State": ("Starkville", "MS"),
    "Missouri": ("Columbia", "MO"),
    "Oklahoma": ("Norman", "OK"),
    "Tennessee": ("Knoxville", "TN"),
    "Texas": ("Austin", "TX"),

    # Pac-12 / Mountain West / Others
    "Boise State": ("Boise", "ID"),
    "Fresno State": ("Fresno", "CA"),
    "Nevada": ("Reno", "NV"),
    "San Diego State": ("San Diego", "CA"),
    "San Jose State": ("San Jose", "CA"),
    "UNLV": ("Las Vegas", "NV"),
    "USC": ("Los Angeles", "CA"),
    "UCLA": ("Los Angeles", "CA"),
    "Washington State": ("Pullman", "WA"),
    "Wyoming": ("Laramie", "WY"),

    # Sun Belt / Conference USA / AAC
    "Appalachian State": ("Boone", "NC"),
    "Coastal Carolina": ("Conway", "SC"),
    "East Carolina": ("Greenville", "NC"),
    "Florida Atlantic": ("Boca Raton", "FL"),
    "Florida International": ("Miami", "FL"),
    "Georgia Southern": ("Statesboro", "GA"),
    "James Madison": ("Harrisonburg", "VA"),
    "Jacksonville State": ("Jacksonville", "AL"),
    "Kennesaw State": ("Kennesaw", "GA"),
    "Liberty": ("Lynchburg", "VA"),
    "Memphis": ("Memphis", "TN"),
    "Middle Tennessee State": ("Murfreesboro", "TN"),
    "Sam Houston St": ("Huntsville", "TX"),
    "South Alabama": ("Mobile", "AL"),
    "Southern Miss": ("Hattiesburg", "MS"),
    "Texas State": ("San Marcos", "TX"),
    "Tulane": ("New Orleans", "LA"),
    "UL Monroe": ("Monroe", "LA"),
    "Western Kentucky": ("Bowling Green", "KY"),

    # Mountain West
    "Central Florida": ("Orlando", "FL"),
    "Colorado State": ("Fort Collins", "CO"),
    "New Mexico": ("Albuquerque", "NM"),
    "New Mexico State": ("Las Cruces", "NM"),
    "Ohio State": ("Columbus", "OH"),
    "Utah State": ("Logan", "UT"),

    # Others
    "Delaware": ("Newark", "DE"),
    "Louisiana Tech": ("Ruston", "LA"),
    "Missouri St": ("Springfield", "MO"),
    "UTEP": ("El Paso", "TX"),
}

# Known indoor/dome stadiums (exclude from weather checks)
INDOOR_STADIUMS = {
    "Syracuse",  # Carrier Dome
    "Idaho",  # Kibbie Dome
    # Most FBS stadiums are outdoor
}


def apply_walters_weather_impact(temp: float, wind: float, precip_prob: float) -> Dict:
    """Apply Billy Walters weather impact methodology.

    Returns total and spread adjustments based on weather conditions.
    """
    total_adj = 0.0
    spread_adj = 0.0
    notes = []

    # Temperature impact
    if temp < 20:
        total_adj -= 4
        spread_adj -= 0.5
        notes.append(f"EXTREME COLD ({temp}°F): -4 pts total, -0.5 spread")
    elif temp < 25:
        total_adj -= 3
        spread_adj -= 0.4
        notes.append(f"Very cold ({temp}°F): -3 pts total, -0.4 spread")
    elif temp < 32:
        total_adj -= 2
        spread_adj -= 0.3
        notes.append(f"Cold ({temp}°F): -2 pts total, -0.3 spread")
    elif temp < 40:
        total_adj -= 1
        spread_adj -= 0.1
        notes.append(f"Chilly ({temp}°F): -1 pt total, -0.1 spread")

    # Wind impact
    if wind > 20:
        total_adj -= 5
        spread_adj -= 0.5
        notes.append(f"HIGH WIND ({wind} mph): -5 pts total, -0.5 spread")
    elif wind > 15:
        total_adj -= 3
        spread_adj -= 0.3
        notes.append(f"Strong wind ({wind} mph): -3 pts total, -0.3 spread")
    elif wind > 10:
        total_adj -= 1
        spread_adj -= 0.1
        notes.append(f"Moderate wind ({wind} mph): -1 pt total, -0.1 spread")

    # Precipitation impact
    if precip_prob > 60:
        if temp < 32:
            total_adj -= 5
            notes.append(f"SNOW LIKELY ({precip_prob}%): -5 pts total")
        else:
            total_adj -= 3
            notes.append(f"Rain likely ({precip_prob}%): -3 pts total")

    return {
        "total_adjustment": round(total_adj, 1),
        "spread_adjustment": round(spread_adj, 1),
        "notes": notes,
        "severity": "EXTREME" if abs(total_adj) >= 5 else "HIGH" if abs(total_adj) >= 3 else "MODERATE" if abs(total_adj) >= 1 else "NONE"
    }


async def check_game_weather(
    client: AccuWeatherClient,
    home_team: str,
    game_time_str: str
) -> Optional[Dict]:
    """Check weather for a specific game."""

    # Skip if indoor stadium
    if home_team in INDOOR_STADIUMS:
        return None

    # Get city for home team
    city_info = TEAM_CITIES.get(home_team)
    if not city_info:
        return None

    city, state = city_info

    # Parse game time
    game_time = datetime.strptime(game_time_str, "%m/%d/%Y %H:%M")

    # Calculate hours until game
    now = datetime.now()
    hours_until = (game_time - now).total_seconds() / 3600

    try:
        # Get location key
        location_key = await client.get_location_key(city, state)
        if not location_key:
            return None

        # Get weather forecast (or current conditions if >12h away)
        weather = await client.get_game_weather(location_key, int(hours_until))
        if not weather:
            # Try current conditions as fallback
            weather = await client.get_current_conditions(location_key)
            if not weather:
                print(f"  [SKIP] No weather data for {home_team}")
                return None

        # Extract weather data
        temp = weather.get("temperature", 70)
        wind = weather.get("wind_speed", 0)
        precip_prob = weather.get("precipitation_probability", 0)
        description = weather.get("description", "")

        # Check if we got actual forecast or just current conditions
        forecast_type = "Forecast" if hours_until <= 12 else "Current Estimate"

        # Apply Billy Walters methodology
        impact = apply_walters_weather_impact(temp, wind, precip_prob)

        return {
            "home_team": home_team,
            "location": f"{city}, {state}",
            "game_time": game_time_str,
            "hours_until": round(hours_until, 1),
            "forecast_type": forecast_type,
            "weather": {
                "temperature": temp,
                "wind_speed": wind,
                "precipitation_prob": precip_prob,
                "description": description,
            },
            "impact": impact
        }

    except Exception as e:
        print(f"[ERROR] Failed to get weather for {home_team}: {e}")
        return None


async def main():
    """Main function to check weather for all Saturday games."""

    # Load games
    odds_file = Path("output/overtime/ncaaf/pregame/api_walters_20251115_115946.json")
    with open(odds_file) as f:
        data = json.load(f)

    # Filter for full games only
    all_games = data.get("games", [])
    saturday_games = [
        g for g in all_games
        if g.get("period") == "Game" and "11/15/2025" in g.get("game_time", "")
    ]

    print(f"\n{'='*80}")
    print(f"SATURDAY NCAAF WEATHER REPORT (11/15/2025)")
    print(f"{'='*80}\n")
    print(f"Total games: {len(saturday_games)}")
    print(f"Checking weather for outdoor games...\n")

    # Initialize weather client
    api_key = os.getenv("ACCUWEATHER_API_KEY")
    if not api_key:
        print("[ERROR] ACCUWEATHER_API_KEY not found in .env")
        return

    client = AccuWeatherClient(api_key=api_key)
    await client.connect()

    # Check weather for all games
    weather_reports = []
    checked_count = 0
    skipped_indoor = 0
    skipped_no_city = 0

    for game in saturday_games:
        home_team = game.get("home_team")
        game_time = game.get("game_time")
        away_team = game.get("away_team")

        # Debug output
        if home_team in INDOOR_STADIUMS:
            skipped_indoor += 1
            continue

        if home_team not in TEAM_CITIES:
            skipped_no_city += 1
            print(f"[SKIP] No city mapping for: {home_team}")
            continue

        checked_count += 1
        report = await check_game_weather(client, home_team, game_time)
        if report:
            report["away_team"] = away_team
            report["spread"] = game.get("spread", {})
            report["total"] = game.get("total", {})
            weather_reports.append(report)

    print(f"\n[INFO] Checked {checked_count} games, skipped {skipped_indoor} indoor, {skipped_no_city} without city mapping")

    await client.close()

    # Sort by impact severity
    severity_order = {"EXTREME": 0, "HIGH": 1, "MODERATE": 2, "NONE": 3}
    weather_reports.sort(key=lambda x: severity_order.get(x["impact"]["severity"], 99))

    # Print weather reports
    print(f"\n{'='*80}")
    print(f"WEATHER IMPACT ANALYSIS ({len(weather_reports)} outdoor games)")
    print(f"{'='*80}\n")

    for report in weather_reports:
        severity = report["impact"]["severity"]
        if severity == "NONE":
            continue  # Skip games with no weather impact

        print(f"[{severity}] {report['away_team']} @ {report['home_team']}")
        print(f"  Location: {report['location']}")
        print(f"  Game Time: {report['game_time']} ({report['hours_until']}h away)")
        print(f"  Forecast Type: {report.get('forecast_type', 'Unknown')}")
        print(f"  Weather: {report['weather']['temperature']}°F, {report['weather']['wind_speed']} mph wind, {report['weather']['precipitation_prob']}% precip")
        print(f"  Description: {report['weather']['description']}")
        print(f"  Impact: {report['impact']['total_adjustment']:+.1f} total, {report['impact']['spread_adjustment']:+.1f} spread")

        for note in report["impact"]["notes"]:
            print(f"    - {note}")

        print(f"  Market Total: {report['total'].get('points', 'N/A')}")
        print(f"  Adjusted Total: {report['total'].get('points', 0) + report['impact']['total_adjustment']:.1f}")
        print()

    # Summary
    extreme_games = [r for r in weather_reports if r["impact"]["severity"] == "EXTREME"]
    high_games = [r for r in weather_reports if r["impact"]["severity"] == "HIGH"]

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Games with EXTREME weather impact: {len(extreme_games)}")
    print(f"Games with HIGH weather impact: {len(high_games)}")
    print(f"\nRecommendation: Focus on games with EXTREME/HIGH impact for weather-based edges")
    print(f"{'='*80}\n")

    # Save report
    output_file = Path("output/reports/saturday_weather_report_11-15-2025.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(weather_reports, f, indent=2)

    print(f"[SAVED] {output_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
