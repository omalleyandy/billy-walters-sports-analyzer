"""
NFL Comprehensive Team Data
Complete reference for all 32 teams including:
- Locations (lat/lon for travel calculation)
- Timezones
- Stadiums (indoor/outdoor, surface, altitude)
- Division assignments
- Multiple abbreviation formats (for API compatibility)

Sources:
- Stadium data: Official NFL.com stadium specifications
- Coordinates: Google Maps verified locations
- Surface types: NFL Operations official data
"""

from typing import Dict, List

# All 32 NFL teams with complete data
NFL_TEAMS = {
    # AFC East
    "BUF": {
        "name": "Buffalo Bills",
        "city": "Orchard Park",
        "state": "NY",
        "timezone": "ET",
        "lat": 42.7738,
        "lon": -78.7870,
        "stadium": "Highmark Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass (A-Turf Titan)",
        "altitude": 600,
        "division": "AFC East",
        "aliases": ["Buffalo", "Buffalo Bills"],
    },
    "MIA": {
        "name": "Miami Dolphins",
        "city": "Miami Gardens",
        "state": "FL",
        "timezone": "ET",
        "lat": 25.9580,
        "lon": -80.2389,
        "stadium": "Hard Rock Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Artificial (Hellas Matrix Turf)",
        "altitude": 10,
        "division": "AFC East",
        "aliases": ["Miami", "Miami Dolphins"],
    },
    "NE": {
        "name": "New England Patriots",
        "city": "Foxborough",
        "state": "MA",
        "timezone": "ET",
        "lat": 42.0909,
        "lon": -71.2643,
        "stadium": "Gillette Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "FieldTurf",
        "altitude": 150,
        "division": "AFC East",
        "aliases": ["New England", "New England Patriots"],
    },
    "NYJ": {
        "name": "New York Jets",
        "city": "East Rutherford",
        "state": "NJ",
        "timezone": "ET",
        "lat": 40.8135,
        "lon": -74.0745,
        "stadium": "MetLife Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "FieldTurf",
        "altitude": 10,
        "division": "AFC East",
        "aliases": ["NY Jets", "New York Jets"],
    },
    # AFC North
    "BAL": {
        "name": "Baltimore Ravens",
        "city": "Baltimore",
        "state": "MD",
        "timezone": "ET",
        "lat": 39.2780,
        "lon": -76.6227,
        "stadium": "M&T Bank Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass",
        "altitude": 50,
        "division": "AFC North",
        "aliases": ["Baltimore", "Baltimore Ravens"],
    },
    "CIN": {
        "name": "Cincinnati Bengals",
        "city": "Cincinnati",
        "state": "OH",
        "timezone": "ET",
        "lat": 39.0954,
        "lon": -84.5160,
        "stadium": "Paycor Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "FieldTurf",
        "altitude": 490,
        "division": "AFC North",
        "aliases": ["Cincinnati", "Cincinnati Bengals"],
    },
    "CLE": {
        "name": "Cleveland Browns",
        "city": "Cleveland",
        "state": "OH",
        "timezone": "ET",
        "lat": 41.5061,
        "lon": -81.6995,
        "stadium": "Huntington Bank Field",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass",
        "altitude": 660,
        "division": "AFC North",
        "aliases": ["Cleveland", "Cleveland Browns"],
    },
    "PIT": {
        "name": "Pittsburgh Steelers",
        "city": "Pittsburgh",
        "state": "PA",
        "timezone": "ET",
        "lat": 40.4469,
        "lon": -80.0158,
        "stadium": "Acrisure Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass",
        "altitude": 750,
        "division": "AFC North",
        "aliases": ["Pittsburgh", "Pittsburgh Steelers"],
    },
    # AFC South
    "HOU": {
        "name": "Houston Texans",
        "city": "Houston",
        "state": "TX",
        "timezone": "CT",
        "lat": 29.6847,
        "lon": -95.4107,
        "stadium": "NRG Stadium",
        "stadium_type": "RETRACTABLE",
        "surface": "Natural Grass",
        "altitude": 50,
        "division": "AFC South",
        "aliases": ["Houston", "Houston Texans"],
    },
    "IND": {
        "name": "Indianapolis Colts",
        "city": "Indianapolis",
        "state": "IN",
        "timezone": "ET",
        "lat": 39.7601,
        "lon": -86.1639,
        "stadium": "Lucas Oil Stadium",
        "stadium_type": "RETRACTABLE",
        "surface": "FieldTurf",
        "altitude": 730,
        "division": "AFC South",
        "aliases": ["Indianapolis", "Indianapolis Colts"],
    },
    "JAX": {
        "name": "Jacksonville Jaguars",
        "city": "Jacksonville",
        "state": "FL",
        "timezone": "ET",
        "lat": 30.3240,
        "lon": -81.6373,
        "stadium": "EverBank Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass",
        "altitude": 20,
        "division": "AFC South",
        "aliases": ["Jacksonville", "Jacksonville Jaguars", "JAC"],
    },
    "TEN": {
        "name": "Tennessee Titans",
        "city": "Nashville",
        "state": "TN",
        "timezone": "CT",
        "lat": 36.1665,
        "lon": -86.7713,
        "stadium": "Nissan Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass",
        "altitude": 550,
        "division": "AFC South",
        "aliases": ["Tennessee", "Tennessee Titans"],
    },
    # AFC West
    "DEN": {
        "name": "Denver Broncos",
        "city": "Denver",
        "state": "CO",
        "timezone": "MT",
        "lat": 39.7439,
        "lon": -105.0201,
        "stadium": "Empower Field at Mile High",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass (Kentucky Bluegrass)",
        "altitude": 5280,  # Mile High!
        "division": "AFC West",
        "aliases": ["Denver", "Denver Broncos"],
    },
    "KC": {
        "name": "Kansas City Chiefs",
        "city": "Kansas City",
        "state": "MO",
        "timezone": "CT",
        "lat": 39.0489,
        "lon": -94.4839,
        "stadium": "GEHA Field at Arrowhead Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass (Tifway 419)",
        "altitude": 910,
        "division": "AFC West",
        "aliases": ["Kansas City", "Kansas City Chiefs"],
    },
    "LV": {
        "name": "Las Vegas Raiders",
        "city": "Las Vegas",
        "state": "NV",
        "timezone": "PT",
        "lat": 36.0909,
        "lon": -115.1833,
        "stadium": "Allegiant Stadium",
        "stadium_type": "INDOOR",
        "surface": "Natural Grass (tray system)",
        "altitude": 2030,
        "division": "AFC West",
        "aliases": ["Las Vegas", "Las Vegas Raiders", "Raiders"],
    },
    "LAC": {
        "name": "Los Angeles Chargers",
        "city": "Inglewood",
        "state": "CA",
        "timezone": "PT",
        "lat": 33.9535,
        "lon": -118.3392,
        "stadium": "SoFi Stadium",
        "stadium_type": "INDOOR",
        "surface": "Matrix Turf",
        "altitude": 100,
        "division": "AFC West",
        "aliases": ["LA Chargers", "Los Angeles Chargers", "Chargers"],
    },
    # NFC East
    "DAL": {
        "name": "Dallas Cowboys",
        "city": "Arlington",
        "state": "TX",
        "timezone": "CT",
        "lat": 32.7473,
        "lon": -97.0945,
        "stadium": "AT&T Stadium",
        "stadium_type": "RETRACTABLE",
        "surface": "Matrix Turf",
        "altitude": 600,
        "division": "NFC East",
        "aliases": ["Dallas", "Dallas Cowboys"],
    },
    "NYG": {
        "name": "New York Giants",
        "city": "East Rutherford",
        "state": "NJ",
        "timezone": "ET",
        "lat": 40.8135,
        "lon": -74.0745,
        "stadium": "MetLife Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "FieldTurf",
        "altitude": 10,
        "division": "NFC East",
        "aliases": ["NY Giants", "New York Giants", "Giants"],
    },
    "PHI": {
        "name": "Philadelphia Eagles",
        "city": "Philadelphia",
        "state": "PA",
        "timezone": "ET",
        "lat": 39.9008,
        "lon": -75.1675,
        "stadium": "Lincoln Financial Field",
        "stadium_type": "OUTDOOR",
        "surface": "Hellas Matrix Turf",
        "altitude": 40,
        "division": "NFC East",
        "aliases": ["Philadelphia", "Philadelphia Eagles", "Eagles"],
    },
    "WAS": {
        "name": "Washington Commanders",
        "city": "Landover",
        "state": "MD",
        "timezone": "ET",
        "lat": 38.9076,
        "lon": -76.8645,
        "stadium": "FedExField",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass",
        "altitude": 50,
        "division": "NFC East",
        "aliases": ["Washington", "Washington Commanders", "Commanders"],
    },
    # NFC North
    "CHI": {
        "name": "Chicago Bears",
        "city": "Chicago",
        "state": "IL",
        "timezone": "CT",
        "lat": 41.8623,
        "lon": -87.6167,
        "stadium": "Soldier Field",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass (Bermuda)",
        "altitude": 590,
        "division": "NFC North",
        "aliases": ["Chicago", "Chicago Bears", "Bears"],
    },
    "DET": {
        "name": "Detroit Lions",
        "city": "Detroit",
        "state": "MI",
        "timezone": "ET",
        "lat": 42.3400,
        "lon": -83.0456,
        "stadium": "Ford Field",
        "stadium_type": "INDOOR",
        "surface": "FieldTurf",
        "altitude": 600,
        "division": "NFC North",
        "aliases": ["Detroit", "Detroit Lions", "Lions"],
    },
    "GB": {
        "name": "Green Bay Packers",
        "city": "Green Bay",
        "state": "WI",
        "timezone": "CT",
        "lat": 44.5013,
        "lon": -88.0622,
        "stadium": "Lambeau Field",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass (Kentucky Bluegrass)",
        "altitude": 640,
        "division": "NFC North",
        "aliases": ["Green Bay", "Green Bay Packers", "Packers"],
    },
    "MIN": {
        "name": "Minnesota Vikings",
        "city": "Minneapolis",
        "state": "MN",
        "timezone": "CT",
        "lat": 44.9738,
        "lon": -93.2577,
        "stadium": "U.S. Bank Stadium",
        "stadium_type": "INDOOR",
        "surface": "FieldTurf",
        "altitude": 840,
        "division": "NFC North",
        "aliases": ["Minnesota", "Minnesota Vikings", "Vikings"],
    },
    # NFC South
    "ATL": {
        "name": "Atlanta Falcons",
        "city": "Atlanta",
        "state": "GA",
        "timezone": "ET",
        "lat": 33.7555,
        "lon": -84.4008,
        "stadium": "Mercedes-Benz Stadium",
        "stadium_type": "RETRACTABLE",
        "surface": "FieldTurf",
        "altitude": 1050,
        "division": "NFC South",
        "aliases": ["Atlanta", "Atlanta Falcons", "Falcons"],
    },
    "CAR": {
        "name": "Carolina Panthers",
        "city": "Charlotte",
        "state": "NC",
        "timezone": "ET",
        "lat": 35.2258,
        "lon": -80.8528,
        "stadium": "Bank of America Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass",
        "altitude": 750,
        "division": "NFC South",
        "aliases": ["Carolina", "Carolina Panthers", "Panthers"],
    },
    "NO": {
        "name": "New Orleans Saints",
        "city": "New Orleans",
        "state": "LA",
        "timezone": "CT",
        "lat": 29.9511,
        "lon": -90.0812,
        "stadium": "Caesars Superdome",
        "stadium_type": "INDOOR",
        "surface": "FieldTurf",
        "altitude": 0,
        "division": "NFC South",
        "aliases": ["New Orleans", "New Orleans Saints", "Saints"],
    },
    "TB": {
        "name": "Tampa Bay Buccaneers",
        "city": "Tampa",
        "state": "FL",
        "timezone": "ET",
        "lat": 27.9759,
        "lon": -82.5033,
        "stadium": "Raymond James Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass (Tifway 419)",
        "altitude": 10,
        "division": "NFC South",
        "aliases": ["Tampa Bay", "Tampa Bay Buccaneers", "Buccaneers", "Bucs"],
    },
    # NFC West
    "ARI": {
        "name": "Arizona Cardinals",
        "city": "Glendale",
        "state": "AZ",
        "timezone": "MT",
        "lat": 33.5276,
        "lon": -112.2626,
        "stadium": "State Farm Stadium",
        "stadium_type": "RETRACTABLE",
        "surface": "Natural Grass (movable field)",
        "altitude": 1100,
        "division": "NFC West",
        "aliases": ["Arizona", "Arizona Cardinals", "Cardinals"],
    },
    "LAR": {
        "name": "Los Angeles Rams",
        "city": "Inglewood",
        "state": "CA",
        "timezone": "PT",
        "lat": 33.9535,
        "lon": -118.3392,
        "stadium": "SoFi Stadium",
        "stadium_type": "INDOOR",
        "surface": "Matrix Turf",
        "altitude": 100,
        "division": "NFC West",
        "aliases": ["LA Rams", "Los Angeles Rams", "Rams"],
    },
    "SF": {
        "name": "San Francisco 49ers",
        "city": "Santa Clara",
        "state": "CA",
        "timezone": "PT",
        "lat": 37.4032,
        "lon": -121.9698,
        "stadium": "Levi's Stadium",
        "stadium_type": "OUTDOOR",
        "surface": "Natural Grass (Bandera Bermuda)",
        "altitude": 70,
        "division": "NFC West",
        "aliases": ["San Francisco", "San Francisco 49ers", "49ers"],
    },
    "SEA": {
        "name": "Seattle Seahawks",
        "city": "Seattle",
        "state": "WA",
        "timezone": "PT",
        "lat": 47.5952,
        "lon": -122.3316,
        "stadium": "Lumen Field",
        "stadium_type": "OUTDOOR",
        "surface": "FieldTurf",
        "altitude": 10,
        "division": "NFC West",
        "aliases": ["Seattle", "Seattle Seahawks", "Seahawks"],
    },
}


def get_team_by_name(name: str) -> Dict:
    """
    Find team by any name variant.

    Args:
        name: Team name (any format: "Buffalo Bills", "Buffalo", "BUF")

    Returns:
        Team data dict or None if not found
    """
    name = name.strip()

    # Try exact abbreviation match first
    if name in NFL_TEAMS:
        return NFL_TEAMS[name]

    # Try aliases
    for abbr, data in NFL_TEAMS.items():
        if name in data["aliases"] or name == data["name"]:
            return {**data, "abbreviation": abbr}

    return None


def get_all_divisions() -> Dict[str, List[str]]:
    """Get all divisions with their teams"""
    divisions = {}

    for abbr, data in NFL_TEAMS.items():
        div = data["division"]
        if div not in divisions:
            divisions[div] = []
        divisions[div].append(abbr)

    return divisions


def is_division_game(team1: str, team2: str) -> bool:
    """Check if two teams are in same division"""
    t1_data = get_team_by_name(team1)
    t2_data = get_team_by_name(team2)

    if not t1_data or not t2_data:
        return False

    return t1_data["division"] == t2_data["division"]


def get_indoor_stadiums() -> List[str]:
    """Get list of all indoor/retractable stadiums"""
    indoor = []
    for abbr, data in NFL_TEAMS.items():
        if data["stadium_type"] in ["INDOOR", "RETRACTABLE"]:
            indoor.append(data["stadium"])
    return indoor


def get_natural_grass_stadiums() -> List[str]:
    """Get stadiums with natural grass (higher injury risk)"""
    grass = []
    for abbr, data in NFL_TEAMS.items():
        if "Natural Grass" in data["surface"]:
            grass.append(data["stadium"])
    return grass


# Timezone offset mapping (for travel calculations)
TIMEZONE_OFFSETS = {
    "PT": -8,  # Pacific Time
    "MT": -7,  # Mountain Time
    "CT": -6,  # Central Time
    "ET": -5,  # Eastern Time
}


if __name__ == "__main__":
    # Validation
    print(f"Total Teams: {len(NFL_TEAMS)}")
    print(f"Divisions: {len(get_all_divisions())}")
    print(f"Indoor/Retractable Stadiums: {len(get_indoor_stadiums())}")
    print(f"Natural Grass Stadiums: {len(get_natural_grass_stadiums())}")

    # Test lookups
    print("\nTest Lookups:")
    print(
        f"'Pittsburgh Steelers' → {get_team_by_name('Pittsburgh Steelers')['abbreviation']}"
    )
    print(f"'PIT' → {get_team_by_name('PIT')['name']}")
    print(f"Division game? PIT vs CLE: {is_division_game('PIT', 'CLE')}")
    print(f"Division game? PIT vs DAL: {is_division_game('PIT', 'DAL')}")
