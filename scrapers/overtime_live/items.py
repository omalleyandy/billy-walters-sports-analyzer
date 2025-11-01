from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import hashlib


@dataclass
class QuoteSide:
    line: Optional[float]  # spread/total number
    price: Optional[int]   # American odds (e.g., -110)


@dataclass
class Market:
    # For spread, keys are "away","home"; for total: "over","under"; for ML: "away","home"
    away: Optional[QuoteSide] = None
    home: Optional[QuoteSide] = None
    over: Optional[QuoteSide] = None
    under: Optional[QuoteSide] = None


@dataclass
class LiveGameItem:
    source: str                 # "overtime.ag"
    sport: str                  # "nfl" or "college_football"
    league: str                 # "NFL" or "NCAAF"
    collected_at: str           # ISO8601Z
    game_key: str               # stable hash of matchup + date bucket
    event_date: Optional[str]   # parsed date in ISO format (e.g., "2025-11-02")
    event_time: Optional[str]   # game time as displayed (e.g., "1:00 PM ET")
    rotation_number: Optional[str]  # e.g., "451-452" or "317-318"
    teams: Dict[str, str]       # {"away": "...", "home": "..."}
    state: Dict[str, Any]       # {"quarter": 4, "clock": "03:24"} best-effort
    markets: Dict[str, Market]  # {"spread": Market(...), "total": Market(...), "moneyline": Market(...)}
    is_live: bool = False       # True for live betting, False for pre-game

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this dataclass into a plain Python dictionary.

        `dataclasses.asdict()` will recursively convert nested dataclasses to
        dictionaries, which is sufficient for our needs.  If you need more
        control over serialisation (e.g. converting datetime objects), you
        should handle that in the caller.
        """
        return asdict(self)


def game_key_from(away: str, home: str, date_bucket: Optional[str] = None) -> str:
    base = f"{away.strip().lower()}@{home.strip().lower()}|{date_bucket or 'today'}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class InjuryReportItem:
    """
    Represents a player's injury status for a specific team/game.
    
    Status values: "Out", "Doubtful", "Questionable", "Probable", "Day-to-Day"
    """
    source: str                     # "espn", "team_site", etc.
    sport: str                      # "college_football", "nfl"
    league: str                     # "NCAAF", "NFL"
    collected_at: str               # ISO8601Z timestamp
    team: str                       # Team name
    team_abbr: Optional[str]        # Team abbreviation (e.g., "ALA", "UGA")
    player_name: str                # Full player name
    position: Optional[str]         # "QB", "RB", "WR", etc.
    injury_status: str              # "Out", "Doubtful", "Questionable", "Probable", "Day-to-Day"
    injury_type: Optional[str]      # "Knee", "Ankle", "Concussion", etc.
    date_reported: Optional[str]    # When injury was reported/updated
    game_date: Optional[str]        # Upcoming game date (if available)
    opponent: Optional[str]         # Opponent for upcoming game
    notes: Optional[str]            # Additional context/notes
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def get_impact_score(self) -> int:
        """
        Return a numeric impact score based on injury status.
        Higher = more impactful to betting decision.
        """
        impact_map = {
            "out": 100,
            "doubtful": 75,
            "questionable": 50,
            "probable": 25,
            "day-to-day": 40,
        }
        return impact_map.get(self.injury_status.lower(), 0)


@dataclass
class WeatherReportItem:
    """
    Weather conditions for a game location following Billy Walters methodology.
    
    Key factors for betting analysis:
    - Wind: >15mph affects passing games, FG accuracy
    - Precipitation: Rain/snow reduces scoring, affects ball handling
    - Temperature: <32°F or >90°F impacts player performance
    - Indoor games: Weather is irrelevant (dome=True)
    """
    source: str                         # "accuweather"
    sport: str                          # "college_football", "nfl"
    collected_at: str                   # ISO8601Z timestamp
    game_date: Optional[str]            # Game date (ISO format)
    game_time: Optional[str]            # Game time local (e.g., "7:30 PM")
    stadium: str                        # Stadium name
    location: str                       # City, State
    is_dome: bool                       # Indoor stadium (weather irrelevant)
    
    # Core weather factors for betting
    temperature_f: Optional[float]      # Temperature in Fahrenheit
    feels_like_f: Optional[float]       # Wind chill or heat index
    wind_speed_mph: Optional[float]     # Wind speed in MPH
    wind_gust_mph: Optional[float]      # Wind gusts in MPH
    wind_direction: Optional[str]       # Wind direction (N, NE, E, etc.)
    precipitation_prob: Optional[int]   # Chance of precipitation (0-100%)
    precipitation_type: Optional[str]   # "Rain", "Snow", "None"
    humidity: Optional[int]             # Relative humidity (0-100%)
    
    # Additional context
    weather_description: Optional[str]  # "Partly Cloudy", "Rainy", etc.
    cloud_cover: Optional[int]          # Cloud cover percentage (0-100%)
    visibility_miles: Optional[float]   # Visibility in miles
    
    # Billy Walters factors (computed)
    weather_impact_score: Optional[int] # 0-100 (higher = more impactful)
    betting_adjustment: Optional[str]   # "Favor Under", "Fade Passing", etc.
    
    # API metadata
    location_key: Optional[str]         # AccuWeather location key
    forecast_url: Optional[str]         # Direct link to forecast
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def calculate_impact_score(self) -> int:
        """
        Calculate weather impact on game (Billy Walters methodology).
        
        Returns 0-100:
        - 0-20: Minimal impact
        - 21-50: Moderate impact (monitor)
        - 51-75: High impact (adjust totals)
        - 76-100: Extreme impact (consider skipping bet)
        """
        if self.is_dome:
            return 0
        
        score = 0
        
        # Wind impact (most critical for passing/kicking)
        if self.wind_speed_mph:
            if self.wind_speed_mph > 25:
                score += 40
            elif self.wind_speed_mph > 20:
                score += 30
            elif self.wind_speed_mph > 15:
                score += 20
            elif self.wind_speed_mph > 10:
                score += 10
        
        # Precipitation impact
        if self.precipitation_prob and self.precipitation_prob > 50:
            if self.precipitation_type == "Snow":
                score += 35  # Snow is highly impactful
            elif self.precipitation_type == "Rain":
                score += 25
        
        # Temperature extremes
        if self.temperature_f:
            if self.temperature_f < 20:
                score += 20  # Extreme cold
            elif self.temperature_f < 32:
                score += 15  # Freezing
            elif self.temperature_f > 95:
                score += 15  # Extreme heat
        
        return min(score, 100)
    
    def get_betting_adjustment(self) -> str:
        """
        Return betting strategy adjustment based on weather.
        """
        if self.is_dome:
            return "No adjustment (indoor)"
        
        impact = self.calculate_impact_score()
        adjustments = []
        
        if self.wind_speed_mph and self.wind_speed_mph > 15:
            adjustments.append("Favor Under")
            adjustments.append("Fade Passing Yards")
            
        if self.precipitation_prob and self.precipitation_prob > 60:
            adjustments.append("Favor Under")
            adjustments.append("Favor Running Teams")
            
        if self.temperature_f and self.temperature_f < 32:
            adjustments.append("Monitor Ball Handling")
            
        if not adjustments:
            return "No significant adjustment"
        
        return " | ".join(adjustments)