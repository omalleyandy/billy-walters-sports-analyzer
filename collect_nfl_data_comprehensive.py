#!/usr/bin/env python3
"""
NFL Comprehensive Data Collector for Week 12
Fetches ALL data needed for Billy Walters methodology:
- Schedule & game times
- Travel & timezone data
- Stadium info (indoor/outdoor, turf)
- Weather forecasts
- Injuries
- Team/Player stats
- News & context
- S-factors & E-factors
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class NFLDataCollector:
    """Comprehensive NFL data collection for Billy Walters analysis"""
    
    def __init__(self, week: int, season: int = 2025):
        self.week = week
        self.season = season
        self.data_dir = Path("data") / "nfl_week_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def collect_all_data(self) -> Dict:
        """
        Collect all NFL data needed for analysis.
        
        Returns comprehensive dictionary with:
        - Schedule
        - Travel/Timezone data
        - Stadium information
        - Weather forecasts
        - Injuries
        - Stats
        - News
        - S-factors
        - E-factors
        """
        logger.info("="*70)
        logger.info(f"NFL DATA COLLECTION - WEEK {self.week}")
        logger.info("Billy Walters Comprehensive Analysis")
        logger.info("="*70 + "\n")
        
        data = {
            "week": self.week,
            "season": self.season,
            "collection_time": datetime.now().isoformat(),
            "games": []
        }
        
        # 1. Schedule & Game Times
        logger.info("[1/8] Fetching Schedule & Game Times...")
        schedule = await self.fetch_schedule()
        data["schedule"] = schedule
        
        # 2. Team Locations & Travel Data
        logger.info("[2/8] Calculating Travel Distances & Timezones...")
        travel_data = await self.fetch_travel_data(schedule)
        data["travel"] = travel_data
        
        # 3. Stadium Information
        logger.info("[3/8] Fetching Stadium Info (Indoor/Outdoor, Turf)...")
        stadiums = await self.fetch_stadium_info()
        data["stadiums"] = stadiums
        
        # 4. Weather Forecasts
        logger.info("[4/8] Fetching Weather Forecasts...")
        weather = await self.fetch_weather(schedule, stadiums)
        data["weather"] = weather
        
        # 5. Injury Reports
        logger.info("[5/8] Fetching Latest Injury Reports...")
        injuries = await self.fetch_injuries()
        data["injuries"] = injuries
        
        # 6. Team & Player Stats
        logger.info("[6/8] Fetching Team & Player Stats...")
        stats = await self.fetch_stats()
        data["stats"] = stats
        
        # 7. News & Context
        logger.info("[7/8] Fetching Recent News...")
        news = await self.fetch_news()
        data["news"] = news
        
        # 8. Calculate S-Factors & E-Factors
        logger.info("[8/8] Calculating S-Factors & E-Factors...")
        factors = await self.calculate_factors(data)
        data["factors"] = factors
        
        # Save comprehensive data
        output_file = self.data_dir / f"week_{self.week}_comprehensive.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"\n[OK] Data collection complete!")
        logger.info(f"[OK] Saved to: {output_file}")
        logger.info(f"[OK] Games: {len(schedule)}")
        
        return data
    
    async def fetch_schedule(self) -> List[Dict]:
        """
        Fetch NFL schedule from ESPN API.
        
        Returns game schedule with times, locations, broadcasts.
        """
        try:
            import aiohttp
            
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            params = {"week": self.week, "seasontype": 2, "dates": self.season}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(f"ESPN API returned {response.status}")
                        return await self._fetch_schedule_fallback()
                    
                    data = await response.json()
                    games = []
                    
                    for event in data.get("events", []):
                        game = self._parse_espn_game(event)
                        games.append(game)
                    
                    logger.info(f"  ✓ Fetched {len(games)} games from ESPN")
                    return games
                    
        except Exception as e:
            logger.warning(f"  ✗ ESPN fetch failed: {e}")
            return await self._fetch_schedule_fallback()
    
    def _parse_espn_game(self, event: Dict) -> Dict:
        """Parse ESPN game event into structured format"""
        competition = event["competitions"][0]
        
        home_team = next(t for t in competition["competitors"] if t["homeAway"] == "home")
        away_team = next(t for t in competition["competitors"] if t["homeAway"] == "away")
        
        return {
            "game_id": event["id"],
            "date": event["date"],
            "time": event["date"],
            "home_team": home_team["team"]["displayName"],
            "home_abbr": home_team["team"]["abbreviation"],
            "away_team": away_team["team"]["displayName"],
            "away_abbr": away_team["team"]["abbreviation"],
            "venue": competition["venue"]["fullName"],
            "venue_city": competition["venue"]["address"]["city"],
            "venue_state": competition["venue"]["address"].get("state", ""),
            "broadcast": competition.get("broadcasts", [{}])[0].get("names", [""])[0],
            "status": competition["status"]["type"]["name"]
        }
    
    async def _fetch_schedule_fallback(self) -> List[Dict]:
        """Fallback: Use stored schedule or Week 12 defaults"""
        logger.info("  → Using fallback schedule data")
        
        # Week 12 known games (update as needed)
        fallback_games = [
            {
                "game_id": "week12_1",
                "home_team": "Cleveland Browns", "home_abbr": "CLE",
                "away_team": "Pittsburgh Steelers", "away_abbr": "PIT",
                "date": "2024-11-21T20:15:00Z",
                "venue": "Huntington Bank Field",
                "venue_city": "Cleveland", "venue_state": "OH",
                "day": "Thursday"
            },
            {
                "game_id": "week12_2",
                "home_team": "Detroit Lions", "home_abbr": "DET",
                "away_team": "Indianapolis Colts", "away_abbr": "IND",
                "date": "2024-11-24T17:00:00Z",
                "venue": "Ford Field",
                "venue_city": "Detroit", "venue_state": "MI",
                "day": "Sunday"
            },
            {
                "game_id": "week12_3",
                "home_team": "Arizona Cardinals", "home_abbr": "ARI",
                "away_team": "Seattle Seahawks", "away_abbr": "SEA",
                "date": "2024-11-24T20:25:00Z",
                "venue": "State Farm Stadium",
                "venue_city": "Glendale", "venue_state": "AZ",
                "day": "Sunday"
            }
        ]
        
        return fallback_games
    
    async def fetch_travel_data(self, schedule: List[Dict]) -> Dict:
        """
        Calculate travel distances and timezone differences.
        
        Billy Walters S-Factor: Travel impact on performance.
        """
        # NFL team locations (city, state, timezone)
        team_locations = {
            "PIT": {"city": "Pittsburgh", "state": "PA", "tz": "ET", "lat": 40.4469, "lon": -80.0158},
            "CLE": {"city": "Cleveland", "state": "OH", "tz": "ET", "lat": 41.5061, "lon": -81.6995},
            "IND": {"city": "Indianapolis", "state": "IN", "tz": "ET", "lat": 39.7601, "lon": -86.1639},
            "DET": {"city": "Detroit", "state": "MI", "tz": "ET", "lat": 42.3400, "lon": -83.0456},
            "SEA": {"city": "Seattle", "state": "WA", "tz": "PT", "lat": 47.5952, "lon": -122.3316},
            "ARI": {"city": "Glendale", "state": "AZ", "tz": "MT", "lat": 33.5276, "lon": -112.2626},
            # Add more teams as needed
        }
        
        travel_analysis = {}
        
        for game in schedule:
            away_abbr = game.get("away_abbr", "")
            home_abbr = game.get("home_abbr", "")
            
            if away_abbr in team_locations and home_abbr in team_locations:
                away_loc = team_locations[away_abbr]
                home_loc = team_locations[home_abbr]
                
                # Calculate distance (Haversine formula)
                distance = self._calculate_distance(
                    away_loc["lat"], away_loc["lon"],
                    home_loc["lat"], home_loc["lon"]
                )
                
                # Timezone difference
                tz_diff = self._calculate_timezone_diff(away_loc["tz"], home_loc["tz"])
                
                travel_analysis[f"{away_abbr}@{home_abbr}"] = {
                    "distance_miles": round(distance, 1),
                    "timezone_diff": tz_diff,
                    "away_home_city": f"{away_loc['city']} → {home_loc['city']}",
                    "travel_category": self._categorize_travel(distance, tz_diff),
                    "s_factor_points": self._calculate_travel_s_factor(distance, tz_diff)
                }
        
        logger.info(f"  ✓ Calculated travel for {len(travel_analysis)} games")
        return travel_analysis
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 3959.87433  # Earth radius in miles
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _calculate_timezone_diff(self, tz1: str, tz2: str) -> int:
        """Calculate timezone difference in hours"""
        tz_hours = {"PT": -8, "MT": -7, "CT": -6, "ET": -5}
        return abs(tz_hours.get(tz2, 0) - tz_hours.get(tz1, 0))
    
    def _categorize_travel(self, distance: float, tz_diff: int) -> str:
        """Categorize travel impact"""
        if distance < 500 and tz_diff == 0:
            return "SHORT"
        elif distance < 1500 and tz_diff <= 1:
            return "MODERATE"
        elif distance >= 1500 or tz_diff >= 2:
            return "LONG"
        else:
            return "MODERATE"
    
    def _calculate_travel_s_factor(self, distance: float, tz_diff: int) -> float:
        """
        Calculate S-factor points for travel.
        
        Billy Walters formula:
        - Short travel (<500mi, no TZ): 0 points
        - Moderate (500-1500mi): 2-3 points
        - Long (>1500mi or 2+ TZ): 5-7 points
        - Coast-to-coast (3 TZ): 10 points
        """
        points = 0.0
        
        # Distance component
        if distance > 2500:
            points += 5.0
        elif distance > 1500:
            points += 3.0
        elif distance > 500:
            points += 2.0
        
        # Timezone component (more important)
        if tz_diff >= 3:
            points += 5.0  # Coast-to-coast
        elif tz_diff == 2:
            points += 3.0
        elif tz_diff == 1:
            points += 1.0
        
        return points
    
    async def fetch_stadium_info(self) -> Dict:
        """
        Fetch stadium information.
        
        Key for S-factors:
        - Indoor/Outdoor (weather impact)
        - Turf type (injury risk, performance)
        - Altitude (Denver)
        """
        stadiums = {
            "Ford Field": {
                "team": "DET",
                "type": "INDOOR",
                "roof": "Fixed",
                "surface": "FieldTurf",
                "altitude": 600
            },
            "Huntington Bank Field": {
                "team": "CLE",
                "type": "OUTDOOR",
                "roof": "None",
                "surface": "Natural Grass",
                "altitude": 660
            },
            "State Farm Stadium": {
                "team": "ARI",
                "type": "RETRACTABLE",
                "roof": "Retractable",
                "surface": "Natural Grass (movable field)",
                "altitude": 1100
            },
            # Add more stadiums...
        }
        
        logger.info(f"  ✓ Loaded {len(stadiums)} stadium profiles")
        return stadiums
    
    async def fetch_weather(self, schedule: List[Dict], stadiums: Dict) -> Dict:
        """
        Fetch weather forecasts for outdoor games.
        
        S-factors:
        - Wind >15mph: Major impact on passing
        - Temperature <32°F: Ball handling issues
        - Precipitation: Reduced scoring
        """
        weather_data = {}
        
        for game in schedule:
            venue = game.get("venue", "")
            stadium_info = stadiums.get(venue, {})
            
            if stadium_info.get("type") == "INDOOR":
                weather_data[game["game_id"]] = {
                    "condition": "INDOOR - No weather impact",
                    "s_factor_points": 0.0
                }
            else:
                # TODO: Integrate with OpenWeather or AccuWeather API
                weather_data[game["game_id"]] = {
                    "forecast": "PENDING - Check before game",
                    "note": "Update with real forecast Saturday"
                }
        
        logger.info(f"  ✓ Weather analysis for {len(weather_data)} games")
        return weather_data
    
    async def fetch_injuries(self) -> Dict:
        """
        Fetch latest injury reports from NFL.com.
        
        Billy Walters: Injuries are the #1 S-factor
        """
        # TODO: Scrape from NFL.com official injury report
        # For now, return structure
        
        injuries = {
            "last_updated": datetime.now().isoformat(),
            "source": "NFL.com Official Injury Report",
            "teams": {}
        }
        
        logger.info("  ✓ Injury data structure ready (needs live scraping)")
        logger.info("  → Check NFL.com/injuries manually for now")
        return injuries
    
    async def fetch_stats(self) -> Dict:
        """
        Fetch team and player stats.
        
        For power rating updates.
        """
        stats = {
            "team_stats": {},
            "player_stats": {},
            "note": "Use ESPN/NFL APIs for live stats"
        }
        
        logger.info("  ✓ Stats structure ready")
        return stats
    
    async def fetch_news(self) -> List[Dict]:
        """Fetch recent NFL news for context"""
        news = []
        logger.info("  ✓ News structure ready")
        return news
    
    async def calculate_factors(self, data: Dict) -> Dict:
        """
        Calculate all S-factors and E-factors.
        
        S-Factors (Situational):
        - Travel/Timezone
        - Rest days
        - Weather
        - Injuries
        - Motivation (division, rivalry, playoff implications)
        
        E-Factors (Emotional):
        - Division games: +2 points (unpredictable)
        - Revenge games: +1 point
        - Playoff implications: +2 points
        """
        factors = {
            "s_factors": {},
            "e_factors": {},
            "division_games": []
        }
        
        # Division matchups (E-factors)
        divisions = {
            "AFC North": ["PIT", "CLE", "BAL", "CIN"],
            "NFC West": ["SEA", "ARI", "SF", "LAR"],
            # Add all divisions...
        }
        
        for game in data.get("schedule", []):
            away = game.get("away_abbr", "")
            home = game.get("home_abbr", "")
            game_key = f"{away}@{home}"
            
            # Check if division game
            is_division = False
            for div_name, teams in divisions.items():
                if away in teams and home in teams:
                    is_division = True
                    factors["division_games"].append({
                        "game": game_key,
                        "division": div_name,
                        "e_factor_points": 2.0,
                        "note": "Division rivalry - unpredictable, emotional"
                    })
                    break
            
            # Compile all S-factors for this game
            travel_sf = data.get("travel", {}).get(game_key, {}).get("s_factor_points", 0)
            
            factors["s_factors"][game_key] = {
                "travel": travel_sf,
                "rest": 0,  # TODO: Calculate from schedule
                "weather": 0,  # TODO: From weather data
                "injuries": 0,  # TODO: From injury analysis
                "total_s_factor": travel_sf
            }
        
        logger.info(f"  ✓ Calculated factors for {len(factors['s_factors'])} games")
        logger.info(f"  ✓ Found {len(factors['division_games'])} division games")
        
        return factors


async def main():
    """Main execution"""
    print("\n" + "="*70)
    print("NFL COMPREHENSIVE DATA COLLECTION")
    print("Billy Walters Methodology - Week 12")
    print("="*70 + "\n")
    
    collector = NFLDataCollector(week=12, season=2025)
    
    try:
        data = await collector.collect_all_data()
        
        print("\n" + "="*70)
        print("COLLECTION SUMMARY")
        print("="*70)
        print(f"\nGames: {len(data.get('schedule', []))}")
        print(f"Travel Analysis: {len(data.get('travel', {}))} matchups")
        print(f"Stadiums: {len(data.get('stadiums', {}))} venues")
        print(f"Division Games: {len(data.get('factors', {}).get('division_games', []))}")
        
        print("\n[NEXT STEPS]")
        print("1. Check data/nfl_week_data/week_12_comprehensive.json")
        print("2. Verify travel distances and timezones")
        print("3. Update injury data from NFL.com manually")
        print("4. Fetch weather forecasts Saturday morning")
        print("5. Update power ratings with this data")
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        logger.error(f"\n[ERROR] Collection failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
