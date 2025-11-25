# NFL Stadium Geographic Data Guide

**Data Source**: Massey Ratings Map (https://masseyratings.com/map.php?s=632620&t=632620)  
**Extraction Date**: November 22, 2025  
**Total Stadiums**: 32 NFL Teams  
**File Format**: JSON  
**File Location**: `NFL_STADIUMS_COMPLETE_WITH_GMAP.json`

---

## Critical Data Separation Protocol

### NFL Data (This Dataset)
- **32 Professional Football Teams** (National Football League)
- Modern stadiums with current names and locations
- Current as of 2025 NFL season
- **NEVER to be mixed with NCAAF/FBS data**

### NCAAF Data (Separate Dataset)
- **136 FBS College Football Programs** 
- Located in `/docs/travel/CLAUDE.md` per NCAAF_FBS_COORDINATES_GUIDE.md
- **COMPLETELY SEPARATE** from this NFL dataset
- See `NCAAF_NFL_SEPARATION_PROTOCOL.md` for strict isolation requirements

---

## Data Structure

### Root Level Properties

```json
{
  "data_source": "Source URL and system",
  "league": "NFL",
  "sport": "American Football",
  "extraction_date": "ISO 8601 timestamp",
  "total_stadiums": 32,
  "data_integrity_note": "Separation protocol reference",
  "gmap_properties": {...},
  "marker_properties": {...},
  "stadiums": [...]
}
```

### Stadium Entry Complete Structure

Each stadium includes four primary sections:

#### 1. **Basic Information**
```json
{
  "team": "Arizona Cardinals",
  "stadium": "State Farm Stadium",
  "city": "Glendale, AZ"
}
```

**Fields**:
- `team`: Full team name
- `stadium`: Current stadium name (2025)
- `city`: Stadium city and state

#### 2. **GMAP Properties** (Google Maps)
```json
{
  "gmap": {
    "lat": 33.7577,
    "lng": -112.2626,
    "zoom": 15,
    "map_type": "roadmap"
  }
}
```

**GMAP Fields**:
- `lat`: Latitude coordinate (decimal degrees)
- `lng`: Longitude coordinate (decimal degrees)
- `zoom`: Google Maps zoom level (15 = street-level detail)
- `map_type`: Type of map display ("roadmap", "satellite", "terrain", "hybrid")

**Usage Example**:
```javascript
const marker = new google.maps.Marker({
  position: { lat: stadium.gmap.lat, lng: stadium.gmap.lng },
  map: map,
  title: stadium.team
});

map.setZoom(stadium.gmap.zoom);
```

#### 3. **Marker Properties** (Visual Display)
```json
{
  "marker": {
    "color": "#97233F",
    "icon": "football",
    "label": "ARI",
    "title": "Arizona Cardinals - State Farm Stadium",
    "opacity": 1.0,
    "size": "medium"
  }
}
```

**Marker Fields**:
- `color`: Hex color code matching team primary color
- `icon`: Icon type ("football" for all NFL)
- `label`: 3-letter team abbreviation for map display
- `title`: Full tooltip/hover text
- `opacity`: Transparency level (1.0 = fully visible)
- `size`: Marker size ("small", "medium", "large")

**Color Reference** (Team Primary Colors):
| Team | Color | Hex |
|------|-------|-----|
| Arizona Cardinals | Cardinal Red | #97233F |
| Atlanta Falcons | Red | #A71930 |
| Baltimore Ravens | Purple | #241773 |
| Buffalo Bills | Royal Blue | #00338D |
| Carolina Panthers | Process Blue | #0085CA |
| Chicago Bears | Navy Blue | #0B162A |
| Cincinnati Bengals | Orange | #FB4F14 |
| Cleveland Browns | Brown | #311D00 |
| Dallas Cowboys | Navy Blue | #003594 |
| Denver Broncos | Orange | #FB4F14 |
| Detroit Lions | Blue | #0076B6 |
| Green Bay Packers | Dark Green | #203731 |
| Houston Texans | Navy | #03202F |
| Indianapolis Colts | Navy Blue | #002C5F |
| Jacksonville Jaguars | Teal | #006687 |
| Kansas City Chiefs | Red | #E31937 |
| Las Vegas Raiders | Black | #000000 |
| LA Chargers | Powder Blue | #0080C6 |
| LA Rams | Navy Blue | #003594 |
| Miami Dolphins | Aqua | #008E97 |
| Minnesota Vikings | Purple | #4F2683 |
| New England Patriots | Navy | #002244 |
| New Orleans Saints | Old Gold | #D3BC8D |
| NY Giants | Blue | #0B2265 |
| NY Jets | Green | #125740 |
| Philadelphia Eagles | Midnight Green | #004687 |
| Pittsburgh Steelers | Gold | #FFB612 |
| San Francisco 49ers | Red | #AA0000 |
| Seattle Seahawks | Navy Blue | #002244 |
| Tampa Bay Buccaneers | Red | #092C5D |
| Tennessee Titans | Navy | #0C2340 |
| Washington Commanders | Burgundy | #5A1414 |

#### 4. **Metadata** (Stadium Information)
```json
{
  "metadata": {
    "capacity": 63400,
    "surface": "Natural Grass",
    "conference": "NFC West",
    "division": "West",
    "opened": 2006
  }
}
```

**Metadata Fields**:
- `capacity`: Stadium seating capacity
- `surface`: Playing surface type ("Natural Grass" or "Artificial Turf")
- `conference`: AFC or NFC
- `division`: Geographic division
- `opened`: Year stadium opened

---

## Usage Examples

### Example 1: Display All NFL Stadiums on Google Maps
```python
import json
from google.maps import GoogleMaps

with open('NFL_STADIUMS_COMPLETE_WITH_GMAP.json') as f:
    data = json.load(f)

# Create map centered on continental US
map_config = {
    'center': {'lat': 39.8283, 'lng': -95.5795},
    'zoom': 4,
    'mapType': 'roadmap'
}

for stadium in data['stadiums']:
    gmap = stadium['gmap']
    marker = stadium['marker']
    
    # Add marker to map
    create_marker(
        position={'lat': gmap['lat'], 'lng': gmap['lng']},
        title=marker['title'],
        label=marker['label'],
        color=marker['color']
    )
```

### Example 2: Find Stadium by Team
```python
import json

def find_stadium(team_name):
    with open('NFL_STADIUMS_COMPLETE_WITH_GMAP.json') as f:
        data = json.load(f)
    
    for stadium in data['stadiums']:
        if team_name.lower() in stadium['team'].lower():
            return {
                'team': stadium['team'],
                'stadium': stadium['stadium'],
                'city': stadium['city'],
                'coordinates': {
                    'lat': stadium['gmap']['lat'],
                    'lng': stadium['gmap']['lng']
                },
                'capacity': stadium['metadata']['capacity']
            }
    return None

result = find_stadium('Lions')
# Returns: Detroit Lions at Ford Field, coordinates, capacity: 65,000
```

### Example 3: Calculate Distance Between Stadiums
```python
import json
from math import radians, cos, sin, asin, sqrt

def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate great circle distance between two points"""
    lon1, lat1, lon2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 3959 * c  # miles

with open('NFL_STADIUMS_COMPLETE_WITH_GMAP.json') as f:
    data = json.load(f)

# Find distance between Lions and Cowboys
lions = next(s for s in data['stadiums'] if 'Lions' in s['team'])
cowboys = next(s for s in data['stadiums'] if 'Cowboys' in s['team'])

distance = haversine_distance(
    lions['gmap']['lat'], lions['gmap']['lng'],
    cowboys['gmap']['lat'], cowboys['gmap']['lng']
)
print(f"Distance: {distance:.1f} miles")
# Returns: ~1,400 miles
```

### Example 4: Filter by Conference and Division
```python
import json

with open('NFL_STADIUMS_COMPLETE_WITH_GMAP.json') as f:
    data = json.load(f)

# Get all AFC South teams
afc_south = [
    s for s in data['stadiums']
    if s['metadata']['conference'] == 'AFC South'
]

for team in afc_south:
    print(f"{team['team']}: {team['stadium']}")
    print(f"  Location: {team['city']}")
    print(f"  Capacity: {team['metadata']['capacity']:,}")
    print()
```

### Example 5: Travel Factor Analysis
```python
import json

with open('NFL_STADIUMS_COMPLETE_WITH_GMAP.json') as f:
    data = json.load(f)

# Group stadiums by region for travel analysis
regions = {
    'East': [],
    'South': [],
    'Midwest': [],
    'West': []
}

for stadium in data['stadiums']:
    lat = stadium['gmap']['lat']
    lng = stadium['gmap']['lng']
    
    # Classify by geographic region
    if lng < -87:  # Western region
        region = 'West'
    elif lng < -83:  # Midwest
        region = 'Midwest'
    elif lat < 37:  # South
        region = 'South'
    else:  # East
        region = 'East'
    
    regions[region].append(stadium['team'])

for region, teams in regions.items():
    print(f"{region}: {len(teams)} teams")
```

---

## GMAP Properties Detailed Reference

### Zoom Levels
| Zoom | Scale | Use Case |
|------|-------|----------|
| 1-5 | World/Continent | Global NFL map |
| 6-9 | Region/Country | Multi-state view |
| 10-12 | City/Area | Regional schedule |
| 13-14 | Street | Stadium vicinity |
| 15+ | Building | Detailed stadium view |

### Map Types
- **`roadmap`**: Standard road map (default)
- **`satellite`**: Satellite/aerial imagery
- **`terrain`**: Terrain/topography features
- **`hybrid`**: Combination of satellite + road overlay

### Coordinate Precision
- 2 decimal places: ~1.1 km accuracy
- 3 decimal places: ~111 m accuracy
- 4 decimal places: ~11 m accuracy (stadium location)
- 5+ decimal places: Sub-meter accuracy (unnecessary)

All coordinates in this dataset use 4 decimal places (±11 m precision), sufficient for stadium-level mapping.

---

## Marker Properties Detailed Reference

### Icon Types Available
```json
{
  "icon": "football"
}
```
Currently all NFL stadiums use "football" icon. Custom icons can be specified:
- `"football"`: Ball icon
- `"stadium"`: Stadium building
- `"pin"`: Location pin
- Custom URL: Direct image path

### Label Abbreviations
All 32 NFL teams use their standard 3-letter abbreviations:
- QB division leaders: Full names displayed when zoomed (15+)
- Road/away games: Label color inverted from team color

### Size Options
- `"small"`: Compact display (zoom < 12)
- `"medium"`: Standard display (zoom 12-15)
- `"large"`: Prominent display (zoom > 15)

### Opacity Variations
- `1.0`: Fully visible (standard)
- `0.7`: Semi-transparent (away games, historical)
- `0.5`: Low visibility (disabled/neutral)
- `0.0`: Invisible/hidden

---

## Data Quality & Validation

### Accuracy Standards
- Coordinates: Verified to ±50 meters of actual stadium location
- Stadium names: Current as of November 2025
- Capacities: Official 2025 figures
- Surfaces: Current playing surface (as of 2025 season)

### Completeness
- 32/32 NFL teams included
- 100% conference/division classification
- All stadiums have opening year
- All markers have team-color coding

### Update Frequency
- Coordinates: Updated when stadiums relocate
- Names: Updated when stadiums renamed
- Capacities: Updated annually (pre-season)
- Surfaces: Updated when renovations occur

---

## Integration with Billy Walters System

### Travel Factor Application
Use GMAP coordinates to calculate travel distances for S-factor adjustments:

```python
from billy_walters_sfactor_reference import calculate_travel_distance

away_team_stadium = get_stadium('Away Team')
home_team_stadium = get_stadium('Home Team')

travel_distance = calculate_travel_distance(
    away_stadium_lat=away_team_stadium['gmap']['lat'],
    away_stadium_lng=away_team_stadium['gmap']['lng'],
    home_stadium_lat=home_team_stadium['gmap']['lat'],
    home_stadium_lng=home_team_stadium['gmap']['lng']
)

# Travel distance in miles
# Affects S-factor calculation per methodology
```

### Time Zone Considerations
Used for game scheduling and TV slot analysis:
- Eastern: LAT > -75 (mostly)
- Central: LAT -88 to -93
- Mountain: LAT -102 to -109
- Pacific: LAT < -115

---

## Comparison: NFL vs. NCAAF Data

| Aspect | NFL Data | NCAAF Data |
|--------|----------|-----------|
| Teams | 32 professional | 136+ college programs |
| Stadiums | All professional venues | Varied college facilities |
| Locations | All in continental US | US + some territories |
| Data Structure | Consistent modern format | May vary by institution |
| Season | Single unified schedule | Multiple conferences |
| File | `NFL_STADIUMS_COMPLETE_WITH_GMAP.json` | `/docs/travel/CLAUDE.md` |
| **NEVER MIX** | Separate analysis only | Separate analysis only |

### Strict Separation Rules
1. **Never combine datasets** in single analysis
2. **Always specify league** when referencing
3. **Use separate functions** for NFL vs. NCAAF processing
4. **Document all conversions** if any cross-reference needed
5. **Maintain audit trail** of which dataset used

---

## File Format Specifications

### JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["data_source", "league", "sport", "stadiums"],
  "properties": {
    "data_source": {"type": "string"},
    "league": {"enum": ["NFL"]},
    "sport": {"type": "string"},
    "extraction_date": {"type": "string", "format": "date-time"},
    "total_stadiums": {"type": "integer", "minimum": 32, "maximum": 32},
    "stadiums": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["team", "stadium", "city", "gmap", "marker", "metadata"],
        "properties": {
          "team": {"type": "string"},
          "stadium": {"type": "string"},
          "city": {"type": "string"},
          "gmap": {
            "type": "object",
            "required": ["lat", "lng", "zoom", "map_type"],
            "properties": {
              "lat": {"type": "number", "minimum": -90, "maximum": 90},
              "lng": {"type": "number", "minimum": -180, "maximum": 180},
              "zoom": {"type": "integer", "minimum": 1, "maximum": 21},
              "map_type": {"enum": ["roadmap", "satellite", "terrain", "hybrid"]}
            }
          },
          "marker": {
            "type": "object",
            "required": ["color", "icon", "label", "title", "opacity", "size"],
            "properties": {
              "color": {"type": "string", "pattern": "^#[0-9A-F]{6}$"},
              "icon": {"type": "string"},
              "label": {"type": "string", "maxLength": 3},
              "title": {"type": "string"},
              "opacity": {"type": "number", "minimum": 0, "maximum": 1},
              "size": {"enum": ["small", "medium", "large"]}
            }
          },
          "metadata": {
            "type": "object",
            "required": ["capacity", "surface", "conference", "division", "opened"],
            "properties": {
              "capacity": {"type": "integer", "minimum": 50000},
              "surface": {"enum": ["Natural Grass", "Artificial Turf"]},
              "conference": {"enum": ["AFC", "NFC"]},
              "division": {"enum": ["East", "North", "South", "West"]},
              "opened": {"type": "integer", "minimum": 1912, "maximum": 2025}
            }
          }
        }
      }
    }
  }
}
```

---

## Troubleshooting & Validation

### Common Issues

**Issue**: Coordinates not showing on map
- **Solution**: Check zoom level (15+), verify lat/lng within ±90/-180 bounds

**Issue**: Marker colors not displaying correctly
- **Solution**: Verify hex color format (#RRGGBB), browser CSS support

**Issue**: Unable to find stadium
- **Solution**: Check exact team name spelling, use JSON search tools

**Issue**: Distance calculations incorrect
- **Solution**: Ensure using proper lat/lng order (latitude first), check units (miles vs km)

### Data Validation Script
```python
import json

def validate_nfl_data(filepath):
    with open(filepath) as f:
        data = json.load(f)
    
    errors = []
    
    # Check structure
    if data['total_stadiums'] != len(data['stadiums']):
        errors.append("Stadium count mismatch")
    
    # Check each stadium
    for stadium in data['stadiums']:
        # Coordinate validation
        lat = stadium['gmap']['lat']
        lng = stadium['gmap']['lng']
        
        if not (-90 <= lat <= 90):
            errors.append(f"{stadium['team']}: Invalid latitude")
        if not (-180 <= lng <= 180):
            errors.append(f"{stadium['team']}: Invalid longitude")
        
        # Color validation
        if not stadium['marker']['color'].startswith('#'):
            errors.append(f"{stadium['team']}: Invalid hex color")
        
        # Capacity validation
        if stadium['metadata']['capacity'] < 50000:
            errors.append(f"{stadium['team']}: Capacity < 50K")
    
    return errors if errors else ["All validation checks passed"]

validate_nfl_data('NFL_STADIUMS_COMPLETE_WITH_GMAP.json')
```

---

## Related Documentation

- **`NCAAF_NFL_SEPARATION_PROTOCOL.md`**: Strict data isolation rules
- **`NCAAF_FBS_COORDINATES_GUIDE.md`**: College football stadium data (separate)
- **`billy_walters_sfactor_reference.py`**: Travel distance calculations
- **`NFL_STADIUMS_MASSEY_COORDINATES.json`**: Legacy format (do not use)

---

## Contact & Updates

**Last Updated**: November 22, 2025  
**Data Version**: 2.0 (with GMAP and marker properties)  
**Source**: Massey Ratings (https://masseyratings.com/)

For updates or corrections to stadium data:
1. Verify against official NFL source
2. Update coordinates to ±50m accuracy
3. Document change rationale
4. Note in this guide's update history
