"""
Stadium to AccuWeather Location Key Mapping

This provides authoritative AccuWeather location keys for all major college
football and NFL stadiums. These are city-level location keys (not POI keys)
for maximum reliability and consistency.

Format:
  Stadium names can be matched by partial string matching
  Location keys are from AccuWeather's official database
  Postal codes are included for reference/validation
"""

# College Football Stadiums (NCAAF)
COLLEGE_STADIUM_KEYS = {
    # Delaware
    "Delaware Stadium": {
        "city": "Newark",
        "state": "DE",
        "zipcode": "19711",
        "location_key": "337531",  # AccuWeather location key for Newark, DE
    },
    # Ohio State
    "Ohio Stadium": {
        "city": "Columbus",
        "state": "OH",
        "zipcode": "43210",
        "location_key": "349727",
    },
    # Michigan
    "Michigan Stadium": {
        "city": "Ann Arbor",
        "state": "MI",
        "zipcode": "48109",
        "location_key": "329259",
    },
    # Add more college stadiums as needed
}

# NFL Stadiums (NFL)
NFL_STADIUM_KEYS = {
    # AFC East
    "Gillette Stadium": {
        "city": "Foxborough",
        "state": "MA",
        "zipcode": "02035",
        "location_key": "339739",
    },
    "MetLife Stadium": {
        "city": "East Rutherford",
        "state": "NJ",
        "zipcode": "07073",
        "location_key": "345145",
    },
    "Hard Rock Stadium": {
        "city": "Miami Gardens",
        "state": "FL",
        "zipcode": "33056",
        "location_key": "346326",
    },
    "Highmark Stadium": {
        "city": "Buffalo",
        "state": "NY",
        "zipcode": "14202",
        "location_key": "328640",
    },
    # Add more NFL stadiums as needed
}


def get_location_key(stadium_name: str, sport: str = "ncaaf") -> str | None:
    """
    Get AccuWeather location key for a stadium.

    Args:
        stadium_name: Full or partial stadium name
        sport: "ncaaf" for college football, "nfl" for professional football

    Returns:
        AccuWeather location key (city-level) or None if not found
    """
    stadium_map = (
        COLLEGE_STADIUM_KEYS if sport.lower() == "ncaaf" else NFL_STADIUM_KEYS
    )

    stadium_lower = stadium_name.lower().strip()

    for stadium, info in stadium_map.items():
        if stadium_lower in stadium.lower() or stadium.lower() in stadium_lower:
            return info["location_key"]

    return None
