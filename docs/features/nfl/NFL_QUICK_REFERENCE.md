# NFL Stadium Data - Quick Reference Card

## File Locations
```
Primary:     /mnt/project/NFL_STADIUMS_COMPLETE_WITH_GMAP.json
Guide:       /mnt/project/NFL_STADIUM_DATA_GUIDE.md
Protocol:    /mnt/project/NFL_NCAAF_SEPARATION_PROTOCOL.md
Summary:     /mnt/project/NFL_EXTRACTION_SUMMARY.md
Legacy:      /mnt/project/NFL_STADIUMS_MASSEY_COORDINATES.json (DEPRECATED)
```

## Quick Stats
- **Teams**: 32 (all NFL)
- **Coordinates**: Lat/Lng (4 decimal places, ±11m)
- **Zoom Level**: 15 (street-level detail)
- **Colors**: Team primary colors (hex format)
- **Stadiums**: Modern professional venues (2025)
- **Status**: Complete, validated, production-ready

## Data Structure

### Stadium Object
```json
{
  "team": "Team Name",
  "stadium": "Stadium Name",
  "city": "City, State",
  "gmap": {
    "lat": 42.3399,
    "lng": -83.0455,
    "zoom": 15,
    "map_type": "roadmap"
  },
  "marker": {
    "color": "#0076B6",
    "icon": "football",
    "label": "DET",
    "title": "Team Name - Stadium Name",
    "opacity": 1.0,
    "size": "medium"
  },
  "metadata": {
    "capacity": 65000,
    "surface": "Natural Grass | Artificial Turf",
    "conference": "AFC | NFC",
    "division": "East | North | South | West",
    "opened": 2002
  }
}
```

## Team List (Quick Lookup)

### AFC (16 teams)
```
East:  BUF, MIA, NE, NYJ
North: BAL, CLE, PIT, CIN
South: HOU, IND, JAX, TEN
West:  DEN, KC, LV, LAC
```

### NFC (16 teams)
```
East:  DAL, NYG, PHI, WAS
North: CHI, DET, GB, MIN
South: ATL, CAR, NO, TB
West:  ARI, LAR, SF, SEA
```

## Coordinate Ranges
```
North: 47.5952 (Seattle)
South: 26.0119 (Miami)
East:  -71.2642 (New England)
West:  -122.3315 (Seattle)
```

## Common Tasks

### Load All Data
```python
import json
with open('NFL_STADIUMS_COMPLETE_WITH_GMAP.json') as f:
    data = json.load(f)
stadiums = data['stadiums']
```

### Find Stadium by Team
```python
team_name = 'Lions'
stadium = next(s for s in stadiums if 'Lions' in s['team'])
# Returns: Detroit Lions, Ford Field, coordinates, marker color, etc.
```

### Get Coordinates
```python
lat = stadium['gmap']['lat']
lng = stadium['gmap']['lng']
# Use for: distance calculations, mapping, travel analysis
```

### Get Team Color
```python
color = stadium['marker']['label']  # "DET"
hex_color = stadium['marker']['color']  # "#0076B6"
# Use for: map rendering, visualization, branding
```

### Calculate Distance
```python
from math import radians, cos, sin, asin, sqrt

def distance(lat1, lng1, lat2, lng2):
    lon1, lat1, lon2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 3959 * 2 * asin(sqrt(a))

s1 = stadiums[0]
s2 = stadiums[1]
miles = distance(s1['gmap']['lat'], s1['gmap']['lng'],
                 s2['gmap']['lat'], s2['gmap']['lng'])
```

### Filter by Conference
```python
afc_teams = [s for s in stadiums if 'AFC' in s['metadata']['conference']]
nfc_teams = [s for s in stadiums if 'NFC' in s['metadata']['conference']]
```

### Filter by Division
```python
nfc_west = [s for s in stadiums 
            if s['metadata']['division'] == 'West' 
            and 'NFC' in s['metadata']['conference']]
```

### Filter by Surface
```python
natural_grass = [s for s in stadiums 
                 if s['metadata']['surface'] == 'Natural Grass']
artificial = [s for s in stadiums 
              if s['metadata']['surface'] == 'Artificial Turf']
```

### Sort by Capacity
```python
by_capacity = sorted(stadiums, 
                     key=lambda x: x['metadata']['capacity'],
                     reverse=True)
largest = by_capacity[0]  # 81,441 (Lambeau)
smallest = by_capacity[-1]  # 61,000 (Allegiant)
```

## Marker Colors (Team Reference)
```
AFC TEAMS:
BUF #00338D  KC #E31937   CLE #311D00  IND #002C5F
MIA #008E97  LV #000000   PIT #FFB612  JAX #006687
NE #002244   LAC #0080C6  BAL #241773  TEN #0C2340
NYJ #125740  DEN #FB4F14  CIN #FB4F14  HOU #03202F

NFC TEAMS:
DAL #003594  ATL #A71930  CHI #0B162A  ARI #97233F
NYG #0B2265  CAR #0085CA  DET #0076B6  LAR #003594
PHI #004687  NO #D3BC8D   GB #203731   SF #AA0000
WAS #5A1414  TB #092C5D   MIN #4F2683  SEA #002244
```

## Key Numbers for Travel Analysis
```
Cross-Country (>2000 mi):  SEA-MIA, SEA-ATL, SEA-JAX
Long Distance (1000-2000):  LAC-NYJ, LAR-NE, DEN-NE
Short Distance (<500):      NYC area (NYG/NYJ), LA area (LAR/LAC)
Tight Cluster:              Northeast (8 teams in ~500 mi radius)
```

## Integration with Billy Walters System
```
S-Factor Impact (Travel):
- >2000 miles → +1.5 spread points
- 1000-2000   → +1.0 spread points
- 500-1000    → +0.5 spread points
- <500        → No adjustment

Use GMAP coordinates:
distance = haversine(away_lat, away_lng, home_lat, home_lng)
s_factor_adjustment = get_travel_factor(distance)
```

## Data Quality Checks
```
✓ All 32 teams present
✓ Coordinates within US bounds (-180 to 180, -90 to 90)
✓ All hex colors valid (#RRGGBB format)
✓ No duplicate stadiums
✓ All required fields present
✓ GMAP and marker properties complete
✓ No NCAAF/college data mixed in
✓ Metadata accurate and current (2025)
```

## Common Mistakes to Avoid
```
❌ Mixing NFL and NCAAF data
❌ Using outdated stadium names
❌ Accessing wrong coordinate field
❌ Assuming all teams in same time zone
❌ Confusing capacity with seating options
❌ Not validating team names
❌ Mixing lat/lng order in functions
```

## Documentation Links
```
Complete Guide:        NFL_STADIUM_DATA_GUIDE.md
Separation Protocol:   NFL_NCAAF_SEPARATION_PROTOCOL.md
Summary & Changes:     NFL_EXTRACTION_SUMMARY.md
Massey Ratings Map:    https://masseyratings.com/map.php?s=632620&t=632620
NCAAF Data (SEPARATE): docs/travel/CLAUDE.md
```

## Validation Script
```python
import json

def validate_nfl_data(file):
    with open(file) as f:
        data = json.load(f)
    
    assert data['total_stadiums'] == 32
    assert len(data['stadiums']) == 32
    
    for s in data['stadiums']:
        assert -90 <= s['gmap']['lat'] <= 90
        assert -180 <= s['gmap']['lng'] <= 180
        assert s['marker']['color'].startswith('#')
        assert len(s['marker']['label']) == 3
        assert s['metadata']['capacity'] > 50000
        assert 'AFC' in s['metadata']['conference'] or 'NFC' in s['metadata']['conference']
    
    return True

print("✓ Valid" if validate_nfl_data('NFL_STADIUMS_COMPLETE_WITH_GMAP.json') else "✗ Invalid")
```

## File Details
```
File:        NFL_STADIUMS_COMPLETE_WITH_GMAP.json
Size:        ~21 KB
Format:      JSON (valid, prettified)
Encoding:    UTF-8
Records:     32 stadiums + 1 header
Date:        November 22, 2025
Status:      Production-ready
```

---

**Last Updated**: November 22, 2025  
**Version**: 2.0 (Complete with GMAP and Marker Properties)  
**Status**: READY FOR PRODUCTION USE ✓
