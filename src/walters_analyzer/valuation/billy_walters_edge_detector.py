#!/usr/bin/env python3
"""
Billy Walters Edge Detection System
Integrates power ratings, odds, weather, and situational factors to identify
betting edges

Based on Billy Walters' Advanced Masterclass Principles:
- Power Ratings (70-100 scale with 90/10 update formula)
- Edge Detection (minimum 3.5-point threshold)
- Situational Factors (S-factor)
- Weather Impact
- Emotional/Motivational Factors
- Sharp Action Analysis
- Key Numbers (3, 7 points)
- Kelly Criterion (25% fraction)
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from src.data.accuweather_client import AccuWeatherClient
from src.data.openweather_client import OpenWeatherClient

# Import weather alert mapper and injury/player valuation modules
from src.walters_analyzer.valuation.weather_alert_mapper import WeatherAlertMapper
from src.walters_analyzer.valuation.injury_impacts import InjuryImpactCalculator
from src.walters_analyzer.valuation.player_values import PlayerValuation

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class EdgeType(Enum):
    """Types of betting edges"""

    POWER_RATING = "power_rating"
    SHARP_ACTION = "sharp_action"
    WEATHER = "weather"
    SITUATIONAL = "situational"
    KEY_NUMBER = "key_number"
    COMBINED = "combined"


@dataclass
class PowerRating:
    """Team power rating"""

    team: str
    rating: float  # 70-100 scale
    offensive_rating: float
    defensive_rating: float
    home_field_advantage: float
    source: str  # "massey", "calculated"


@dataclass
class SituationalFactor:
    """S-factor components"""

    rest_days: int = 7
    rest_advantage: float = 0.0  # -3 to +3 points
    travel_distance: int = 0
    travel_penalty: float = 0.0  # 0 to -2 points
    divisional_game: bool = False
    rivalry_game: bool = False
    revenge_spot: bool = False
    lookahead_spot: bool = False
    letdown_spot: bool = False
    total_adjustment: float = 0.0


@dataclass
class WeatherImpact:
    """Weather impact on game"""

    temperature: Optional[float] = None  # Fahrenheit
    wind_speed: Optional[float] = None  # MPH
    precipitation: Optional[str] = None  # "rain", "snow", "none"
    indoor: bool = False
    total_adjustment: float = 0.0  # Points to subtract from total
    spread_adjustment: float = 0.0  # Favors defense/rushing teams

    # Weather Alert Fields (NWS via OpenWeather One Call API 3.0)
    alerts: Optional[List] = None  # List of WeatherAlert objects from alert mapper
    alert_severity: str = "NONE"  # CRITICAL/MAJOR/MODERATE/MINOR/NONE
    alert_total_adjustment: float = 0.0  # Alert-specific total adjustment
    alert_spread_adjustment: float = 0.0  # Alert-specific spread adjustment

    # Combined Impact (uses maximum principle: max(conditions, alerts))
    # final_total_adjustment uses most severe of condition or alert impact
    # final_spread_adjustment uses most severe of condition or alert impact


@dataclass
class InjuryImpact:
    """Injury impact on team performance"""

    team: str
    total_impact: float = 0.0  # Total point impact
    critical_injuries: List[Dict] = None  # Critical injuries (≥2.0 pts)
    moderate_injuries: List[Dict] = None  # Moderate injuries (≥0.8 pts)
    minor_injuries: List[Dict] = None  # Minor injuries (<0.8 pts)
    severity: str = "NEGLIGIBLE"  # CRITICAL/MAJOR/MODERATE/MINOR/NEGLIGIBLE
    confidence: str = "LOW"  # HIGH/MEDIUM/LOW
    injury_count: int = 0
    position_group_multipliers: Dict[str, float] = None  # e.g., OFFENSIVE_LINE_CRISIS

    def __post_init__(self):
        if self.critical_injuries is None:
            self.critical_injuries = []
        if self.moderate_injuries is None:
            self.moderate_injuries = []
        if self.minor_injuries is None:
            self.minor_injuries = []
        if self.position_group_multipliers is None:
            self.position_group_multipliers = {}


@dataclass
class SharpAction:
    """Sharp vs public betting analysis"""

    line_movement: float = 0.0  # Positive = moved toward favorite
    money_percent: float = 50.0  # Sharp money %
    tickets_percent: float = 50.0  # Public tickets %
    reverse_line_movement: bool = False  # Line moved against public
    sharp_side: Optional[str] = None  # "home", "away", "none"
    confidence: float = 0.0  # 0-1 scale


@dataclass
class BettingEdge:
    """Identified betting edge"""

    game_id: str
    matchup: str
    week: int
    game_time: str

    # Teams
    away_team: str
    home_team: str

    # Power ratings
    away_rating: float
    home_rating: float
    predicted_spread: float  # Negative = home favored

    # Market
    market_spread: float
    market_total: float
    best_odds: int  # American odds

    # Edge calculation
    edge_points: float  # Difference between predicted and market
    edge_type: str
    edge_strength: str  # "weak", "medium", "strong", "very_strong"

    # Adjustments
    situational_adjustment: float
    weather_adjustment: float
    emotional_adjustment: float
    injury_adjustment: float  # Net injury impact (away - home)

    # Sharp action
    sharp_action: SharpAction

    # Key numbers
    crosses_key_number: bool
    key_number_value: Optional[int]

    # Kelly Criterion
    recommended_bet: Optional[str]  # "home", "away", None
    kelly_fraction: float  # 0-0.25 (conservative)
    confidence_score: float  # 0-100

    # Metadata
    timestamp: str
    data_sources: List[str]

    # Injury impacts (with defaults, must come last)
    away_injuries: Optional[InjuryImpact] = None
    home_injuries: Optional[InjuryImpact] = None


class BillyWaltersEdgeDetector:
    """
    Main edge detection system following Billy Walters principles
    """

    # Constants from Billy Walters methodology
    MIN_EDGE_THRESHOLD = 3.5  # Minimum edge in points
    KELLY_FRACTION = 0.25  # Conservative Kelly (25%)
    MAX_BET_PERCENT = 3.0  # Maximum 3% of bankroll per bet
    KEY_NUMBERS = [3, 7, 10, 6, 4, 14]  # NFL key numbers in order of importance

    # Power rating update formula: New = (Old * 0.9) + (Actual * 0.1)
    POWER_RATING_WEIGHT_OLD = 0.9
    POWER_RATING_WEIGHT_NEW = 0.1

    # Team name mapping: Action Network -> Massey Ratings
    TEAM_NAME_MAP = {
        # NFL Teams
        "Cardinals": "Arizona",
        "Falcons": "Atlanta",
        "Ravens": "Baltimore",
        "Bills": "Buffalo",
        "Panthers": "Carolina",
        "Bears": "Chicago",
        "Bengals": "Cincinnati",
        "Browns": "Cleveland",
        "Cowboys": "Dallas",
        "Broncos": "Denver",
        "Lions": "Detroit",
        "Packers": "Green Bay",
        "Texans": "Houston",
        "Colts": "Indianapolis",
        "Jaguars": "Jacksonville",
        "Chiefs": "Kansas City",
        "Raiders": "Las Vegas",
        "Chargers": "LA Chargers",
        "Rams": "LA Rams",
        "Dolphins": "Miami",
        "Vikings": "Minnesota",
        "Patriots": "New England",
        "Saints": "New Orleans",
        "Giants": "NY Giants",
        "Jets": "NY Jets",
        "Eagles": "Philadelphia",
        "Steelers": "Pittsburgh",
        "49ers": "San Francisco",
        "Seahawks": "Seattle",
        "Buccaneers": "Tampa Bay",
        "Titans": "Tennessee",
        "Commanders": "Washington",
    }

    def __init__(self, output_dir: str = "output/edge_detection"):
        """Initialize edge detector"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Data caches
        self.power_ratings: Dict[str, PowerRating] = {}
        self.situational_factors: Dict[str, SituationalFactor] = {}
        self.weather_data: Dict[str, WeatherImpact] = {}
        self.injury_data: Dict[str, List[Dict]] = {}  # team -> list of injuries

        # Injury and player valuation calculators
        self.injury_calculator = InjuryImpactCalculator()
        self.player_valuation = PlayerValuation(sport="NFL")

        logger.info("Billy Walters Edge Detector initialized")

    def normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team name from Action Network to Massey format

        Args:
            team_name: Team name from Action Network

        Returns:
            Normalized team name for Massey lookup
        """
        # Try direct mapping first
        if team_name in self.TEAM_NAME_MAP:
            return self.TEAM_NAME_MAP[team_name]

        # Try case-insensitive search
        for action_name, massey_name in self.TEAM_NAME_MAP.items():
            if action_name.lower() == team_name.lower():
                return massey_name

        # Return as-is if no mapping found
        logger.warning(f"No mapping found for team: {team_name}")
        return team_name

    # =================================================================
    # DATA LOADING
    # =================================================================

    def load_massey_ratings(self, filepath: str, league: str = "nfl"):
        """
        Load Massey power ratings

        Args:
            filepath: Path to massey ratings JSON
            league: "nfl" or "ncaaf"
        """
        logger.info(f"Loading Massey {league.upper()} ratings from {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        for team in data.get("teams", []):
            team_name = team["team"]

            # Massey already uses appropriate scale for each league
            # NFL: ~7-10 rating scale
            # NCAAF: ~60-90 rating scale
            rating = float(team["rating"]) if team["rating"] else 70.0

            # Convert to consistent 70-100 scale if needed
            if league == "nfl":
                # NFL ratings are 7-10, scale to 70-100
                rating = rating * 10  # 7.0 -> 70, 9.0 -> 90

            # Extract offensive and defensive ratings from rawData
            offensive_rating = 0.0
            defensive_rating = 0.0

            raw_data = team.get("rawData", [])
            if len(raw_data) > 6:
                try:
                    # rawData[5] = "12\n25.59" -> offensive (rank\nrating)
                    off_parts = raw_data[5].split("\n")
                    if len(off_parts) > 1:
                        offensive_rating = float(off_parts[1])

                    # rawData[6] = "2\n4.67" -> defensive (rank\nrating)
                    def_parts = raw_data[6].split("\n")
                    if len(def_parts) > 1:
                        defensive_rating = float(def_parts[1])
                except (ValueError, IndexError) as e:
                    logger.warning(
                        f"Could not extract Off/Def ratings for {team_name}: {e}"
                    )

            self.power_ratings[team_name] = PowerRating(
                team=team_name,
                rating=rating,
                offensive_rating=offensive_rating,
                defensive_rating=defensive_rating,
                home_field_advantage=2.5,  # Standard NFL HFA
                source="massey",
            )

        logger.info(f"Loaded {len(self.power_ratings)} {league.upper()} power ratings")

    def load_proprietary_ratings(self, week: int = None, filepath: str = None):
        """
        Load Billy Walters proprietary 90/10 power ratings from weekly snapshots

        Args:
            week: NFL week number (1-18). If None, loads from master file
            filepath: Optional custom filepath. If None, uses standard naming
        """
        if filepath:
            ratings_file = filepath
        elif week:
            ratings_file = f"data/power_ratings/nfl_2025_week_{week:02d}.json"
        else:
            ratings_file = "data/power_ratings_nfl_2025.json"

        logger.info(f"Loading proprietary 90/10 power ratings from {ratings_file}")

        if not os.path.exists(ratings_file):
            logger.error(f"Proprietary ratings file not found: {ratings_file}")
            logger.error(
                "Please run backfill script: python scripts/backfill_weekly_ratings.py"
            )
            raise FileNotFoundError(f"Missing {ratings_file}")

        with open(ratings_file, "r") as f:
            data = json.load(f)

        # Load ratings dictionary
        ratings_dict = data.get("ratings", {})

        for team_name, rating in ratings_dict.items():
            # Ratings are already on correct scale from 90/10 formula
            # Scale is ~0-25 (different from Massey's 70-100)
            # Keep as-is for proper Billy Walters methodology

            self.power_ratings[team_name] = PowerRating(
                team=team_name,
                rating=rating,
                offensive_rating=0.0,  # TODO: Extract from separate system
                defensive_rating=0.0,
                home_field_advantage=2.0,  # Billy Walters uses 2.0
                source="proprietary_90_10",
            )

        week_info = f"Week {data.get('week')}" if "week" in data else "Master file"
        logger.info(
            f"Loaded {len(self.power_ratings)} proprietary ratings ({week_info})"
        )
        logger.info(
            f"System: 90/10 formula, "
            f"{data.get('games_processed_total', 'N/A')} games processed"
        )

    def load_action_network_odds(self, filepath: str):
        """
        Load Action Network odds and sharp action data

        Args:
            filepath: Path to Action Network API response JSON
        """
        logger.info(f"Loading Action Network data from {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        # Find scoreboard response
        scoreboard = None
        if isinstance(data, list):
            for item in data:
                if "url" in item and "scoreboard" in item["url"]:
                    scoreboard = item["data"]
                    break

        if not scoreboard:
            logger.warning("No scoreboard data found in Action Network response")
            return {}

        games_data = {}
        for game in scoreboard.get("games", []):
            game_id = str(game["id"])
            games_data[game_id] = game

        logger.info(f"Loaded {len(games_data)} games from Action Network")
        return games_data

    # =================================================================
    # SITUATIONAL ANALYSIS
    # =================================================================

    def calculate_situational_factors(
        self,
        team: str,
        opponent: str,
        week: int,
        game_date: datetime,
        last_game_date: Optional[datetime] = None,
        is_divisional: bool = False,
        is_rivalry: bool = False,
        recent_performance: Optional[List[str]] = None,
    ) -> SituationalFactor:
        """
        Calculate S-factor (situational adjustments)

        Billy Walters emphasizes:
        - Rest advantage (each extra day = ~0.5 points)
        - Travel fatigue (cross-country = -1.5 to -2 points)
        - Divisional games (more competitive, lower margins)
        - Revenge spots (previous loss to opponent)
        - Lookahead/letdown spots
        """
        s_factor = SituationalFactor(
            divisional_game=is_divisional, rivalry_game=is_rivalry
        )

        # Rest advantage
        if last_game_date:
            rest_days = (game_date - last_game_date).days
            s_factor.rest_days = rest_days

            # Extra rest = advantage
            if rest_days > 7:
                s_factor.rest_advantage = (rest_days - 7) * 0.5
            elif rest_days < 7:
                s_factor.rest_advantage = (rest_days - 7) * 0.5  # Negative

        # Divisional game adjustment
        if is_divisional:
            # Divisional games typically closer, reduce spread by 1-2 points
            s_factor.total_adjustment -= 1.5

        # Rivalry intensity
        if is_rivalry:
            s_factor.total_adjustment += 1.0  # More intense, higher scoring

        # Letdown spot detection (after big win)
        if recent_performance and len(recent_performance) >= 2:
            if recent_performance[0] == "W" and recent_performance[1] == "W":
                s_factor.letdown_spot = True
                s_factor.total_adjustment -= 1.0

        s_factor.total_adjustment = s_factor.rest_advantage + s_factor.travel_penalty

        return s_factor

    # =================================================================
    # WEATHER ANALYSIS
    # =================================================================

    def calculate_weather_impact(
        self,
        temperature: Optional[float],
        wind_speed: Optional[float],
        precipitation: Optional[str],
        indoor: bool = False,
        alerts: Optional[List] = None,
    ) -> WeatherImpact:
        """
        Calculate weather impact on game

        Billy Walters principles:
        - Wind >15 MPH: Reduce total by 3-5 points, favor defense
        - Temp <32°F: Reduce total by 2-3 points, favor rushing
        - Rain/Snow: Reduce total by 2-4 points
        - Indoor: No adjustments
        - Weather Alerts: Use maximum impact principle (not additive)

        Args:
            temperature: Temperature in Fahrenheit
            wind_speed: Wind speed in MPH
            precipitation: Precipitation type ("rain", "snow", "none")
            indoor: Indoor stadium flag
            alerts: List of WeatherAlert objects from NWS

        Returns:
            WeatherImpact with combined condition + alert analysis
        """
        impact = WeatherImpact(
            temperature=temperature,
            wind_speed=wind_speed,
            precipitation=precipitation,
            indoor=indoor,
        )

        if indoor:
            return impact

        # Calculate condition-based adjustments (Billy Walters W-Factors)
        condition_total_adj = 0.0
        condition_spread_adj = 0.0

        # Wind impact (Billy Walters: -0.20 for 15mph, -0.40 for 20mph)
        if wind_speed:
            if wind_speed >= 20:
                condition_total_adj -= 0.40  # wind_20mph (Billy Walters)
                condition_spread_adj -= 0.15
            elif wind_speed >= 15:
                condition_total_adj -= 0.20  # wind_15mph (Billy Walters)
                condition_spread_adj -= 0.10

        # Temperature impact (Billy Walters: -0.20 for extreme)
        if temperature:
            if temperature < 20:
                condition_total_adj -= 0.20  # extreme_cold (Billy Walters)
                condition_spread_adj -= 0.10
            elif temperature > 90:
                condition_total_adj -= 0.20  # extreme_heat (Billy Walters)
                condition_spread_adj -= 0.10

        # Precipitation (Billy Walters: -0.20 light, -0.60 heavy)
        if precipitation:
            precip_lower = precipitation.lower()
            if precip_lower == "snow":
                # Assume moderate-heavy snow without additional data
                condition_total_adj -= 0.40  # snow_moderate-heavy (Billy Walters)
                condition_spread_adj -= 0.15
            elif precip_lower == "rain":
                # Assume moderate rain
                condition_total_adj -= 0.30  # rain_moderate (Billy Walters)
                condition_spread_adj -= 0.12

        # Process weather alerts if available
        alert_total_adj = 0.0
        alert_spread_adj = 0.0
        alert_severity = "NONE"

        if alerts:
            mapper = WeatherAlertMapper()
            max_total, max_spread = mapper.get_max_alert_impact(alerts)
            alert_total_adj = max_total
            alert_spread_adj = max_spread

            # Determine most severe alert
            if alerts:
                most_severe = min(alerts, key=lambda a: a.total_adjustment)
                alert_severity = most_severe.severity

        # Billy Walters Maximum Principle:
        # Use most severe impact (conditions OR alerts, not both)
        # Alerts already account for underlying conditions
        final_total = min(condition_total_adj, alert_total_adj)
        final_spread = min(condition_spread_adj, alert_spread_adj)

        impact.total_adjustment = final_total
        impact.spread_adjustment = final_spread
        impact.alerts = alerts
        impact.alert_severity = alert_severity
        impact.alert_total_adjustment = alert_total_adj
        impact.alert_spread_adjustment = alert_spread_adj

        return impact

    # =================================================================
    # INJURY ANALYSIS
    # =================================================================

    def load_injury_data(
        self, injury_file: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Load injury data from NFL official scraper output

        Args:
            injury_file: Path to injury JSON file. If None, finds latest file

        Returns:
            Dictionary mapping team names to list of injuries
        """
        if injury_file is None:
            # Find latest injury file
            injury_dir = "output/injuries"
            if not os.path.exists(injury_dir):
                logger.warning(f"Injury directory {injury_dir} not found")
                return {}

            injury_files = [
                f
                for f in os.listdir(injury_dir)
                if f.endswith(".json") and "nfl_official" in f
            ]
            if not injury_files:
                logger.warning("No NFL official injury files found")
                return {}

            injury_files.sort(reverse=True)  # Most recent first
            injury_file = os.path.join(injury_dir, injury_files[0])

        logger.info(f"Loading injury data from {injury_file}")

        try:
            with open(injury_file) as f:
                data = json.load(f)

            injuries_by_team = {}
            injuries_list = data.get("injuries", [])

            for injury in injuries_list:
                team = injury.get("team", "Unknown")
                if team not in injuries_by_team:
                    injuries_by_team[team] = []
                injuries_by_team[team].append(injury)

            logger.info(
                f"Loaded {len(injuries_list)} injuries across "
                f"{len(injuries_by_team)} teams"
            )
            self.injury_data = injuries_by_team
            return injuries_by_team

        except Exception as e:
            logger.error(f"Error loading injury data: {e}")
            return {}

    def calculate_team_injury_impact(self, team_name: str) -> InjuryImpact:
        """
        Calculate total injury impact for a team

        Args:
            team_name: Team name (normalized)

        Returns:
            InjuryImpact object with detailed breakdown
        """
        if not self.injury_data:
            return InjuryImpact(team=team_name)

        team_injuries = self.injury_data.get(team_name, [])
        if not team_injuries:
            return InjuryImpact(team=team_name)

        # Convert injury data to format expected by injury calculator
        injured_players = []

        for injury in team_injuries:
            position = injury.get("position", "")
            injury_type_str = injury.get("injury_type", "")
            game_status = injury.get("game_status", "Questionable")

            # Parse injury type
            injury_type = self.injury_calculator.parse_injury_status(
                game_status, injury_type_str
            )

            # Get player value based on position
            player_value = self.player_valuation.calculate_player_value(position)

            injured_players.append(
                {
                    "name": injury.get("player_name", ""),
                    "position": position,
                    "value": player_value,
                    "injury_type": injury_type,
                    "days_since_injury": 0,  # Default to current injury
                }
            )

        # Calculate team-level impact
        impact_data = self.injury_calculator.calculate_team_injury_impact(
            injured_players
        )

        return InjuryImpact(
            team=team_name,
            total_impact=impact_data["total_impact"],
            critical_injuries=impact_data["critical_injuries"],
            moderate_injuries=impact_data["moderate_injuries"],
            minor_injuries=impact_data["minor_injuries"],
            severity=impact_data["severity"],
            confidence=impact_data["confidence"],
            injury_count=impact_data["injury_count"],
        )

    # =================================================================
    # SHARP ACTION ANALYSIS
    # =================================================================

    def analyze_sharp_action(
        self, money_percent: float, tickets_percent: float, line_movement: float = 0.0
    ) -> SharpAction:
        """
        Analyze sharp vs public betting

        Billy Walters key: Follow the smart money!
        - Reverse line movement = sharp action indicator
        - Money % >> Tickets % = sharp action on that side
        - Typical threshold: 30%+ discrepancy
        """
        action = SharpAction(
            money_percent=money_percent,
            tickets_percent=tickets_percent,
            line_movement=line_movement,
        )

        # Calculate discrepancy
        discrepancy = abs(money_percent - tickets_percent)

        # Reverse line movement detection
        if line_movement > 0 and tickets_percent > 60:
            # Line moved toward favorite despite public on underdog
            action.reverse_line_movement = True
            action.sharp_side = "favorite"
        elif line_movement < 0 and tickets_percent < 40:
            # Line moved toward underdog despite public on favorite
            action.reverse_line_movement = True
            action.sharp_side = "underdog"

        # Sharp side determination
        if money_percent > tickets_percent + 20:
            action.sharp_side = "high_money_side"
            action.confidence = min(discrepancy / 50, 1.0)
        elif tickets_percent > money_percent + 20:
            action.sharp_side = "low_money_side"  # Fade the public
            action.confidence = min(discrepancy / 50, 1.0)

        return action

    # =================================================================
    # EDGE DETECTION
    # =================================================================

    def calculate_predicted_spread(
        self,
        away_team: str,
        home_team: str,
        situational_adj: float = 0.0,
        weather_adj: float = 0.0,
    ) -> Tuple[float, float, float]:
        """
        Calculate predicted spread using power ratings

        Returns:
            (predicted_spread, away_rating, home_rating)
        """
        away_rating = self.power_ratings.get(away_team)
        home_rating = self.power_ratings.get(home_team)

        if not away_rating or not home_rating:
            logger.warning(f"Missing ratings for {away_team} vs {home_team}")
            return 0.0, 0.0, 0.0

        # Base calculation: Home - Away + HFA
        predicted = (
            home_rating.rating
            - away_rating.rating
            + home_rating.home_field_advantage
            + situational_adj
            + weather_adj
        )

        return predicted, away_rating.rating, home_rating.rating

    def detect_edge(
        self,
        game_id: str,
        away_team: str,
        home_team: str,
        market_spread: float,
        market_total: float,
        week: int,
        game_time: str,
        situational: Optional[SituationalFactor] = None,
        weather: Optional[WeatherImpact] = None,
        sharp_action: Optional[SharpAction] = None,
        best_odds: int = -110,
    ) -> Optional[BettingEdge]:
        """
        Detect betting edge following Billy Walters principles

        Returns:
            BettingEdge if edge >= 3.5 points, else None
        """
        # Calculate injury impacts for both teams
        away_injury_impact = self.calculate_team_injury_impact(away_team)
        home_injury_impact = self.calculate_team_injury_impact(home_team)

        # Net injury adjustment (away injuries hurt away team, home injuries hurt home)
        # Positive = favors home, Negative = favors away
        injury_adj = away_injury_impact.total_impact - home_injury_impact.total_impact

        logger.info(
            f"{away_team} injuries: {away_injury_impact.total_impact:.1f} pts "
            f"({away_injury_impact.severity})"
        )
        logger.info(
            f"{home_team} injuries: {home_injury_impact.total_impact:.1f} pts "
            f"({home_injury_impact.severity})"
        )
        logger.info(
            f"Net injury adjustment: {injury_adj:+.1f} pts "
            f"(favors {'home' if injury_adj > 0 else 'away'})"
        )

        # Calculate other adjustments
        sit_adj = situational.total_adjustment if situational else 0.0
        weather_adj = weather.spread_adjustment if weather else 0.0

        # Get predicted spread with all adjustments
        predicted_spread, away_rating, home_rating = self.calculate_predicted_spread(
            away_team, home_team, sit_adj + injury_adj, weather_adj
        )

        # Calculate edge
        edge_points = abs(predicted_spread - market_spread)

        # Determine which side has edge
        recommended_bet = None
        if predicted_spread - market_spread > self.MIN_EDGE_THRESHOLD:
            recommended_bet = "home"  # Market undervaluing home team
        elif market_spread - predicted_spread > self.MIN_EDGE_THRESHOLD:
            recommended_bet = "away"  # Market undervaluing away team

        # Only proceed if we have minimum edge
        if edge_points < self.MIN_EDGE_THRESHOLD and not (
            sharp_action and sharp_action.reverse_line_movement
        ):
            return None

        # Check for key number crossing
        crosses_key = False
        key_number_value = None
        for key_num in self.KEY_NUMBERS:
            if (
                min(predicted_spread, market_spread)
                < key_num
                < max(predicted_spread, market_spread)
            ):
                crosses_key = True
                key_number_value = key_num
                # Add value for crossing key number
                if key_num == 3:
                    edge_points += 0.8  # 3 is worth 8% extra
                elif key_num == 7:
                    edge_points += 0.6  # 7 is worth 6% extra
                break

        # Determine edge strength
        if edge_points >= 7.0:
            edge_strength = "very_strong"
        elif edge_points >= 5.5:
            edge_strength = "strong"
        elif edge_points >= 4.0:
            edge_strength = "medium"
        else:
            edge_strength = "weak"

        # Calculate Kelly fraction (conservative 25%)
        kelly = self.KELLY_FRACTION * (edge_points / 7.0)  # Scale to edge size
        kelly = min(kelly, self.KELLY_FRACTION)  # Cap at 25%

        # Confidence score (0-100)
        confidence = min((edge_points / 10.0) * 100, 100)

        # Boost confidence for sharp action alignment
        if sharp_action and sharp_action.reverse_line_movement:
            confidence = min(confidence * 1.2, 100)

        # Determine edge type
        edge_type = EdgeType.POWER_RATING.value
        if sharp_action and sharp_action.reverse_line_movement:
            edge_type = EdgeType.SHARP_ACTION.value
        if weather and abs(weather.total_adjustment) > 3:
            edge_type = EdgeType.WEATHER.value
        if situational and abs(situational.total_adjustment) > 2:
            edge_type = EdgeType.SITUATIONAL.value

        edge = BettingEdge(
            game_id=game_id,
            matchup=f"{away_team} @ {home_team}",
            week=week,
            game_time=game_time,
            away_team=away_team,
            home_team=home_team,
            away_rating=away_rating,
            home_rating=home_rating,
            predicted_spread=predicted_spread,
            market_spread=market_spread,
            market_total=market_total,
            best_odds=best_odds,
            edge_points=edge_points,
            edge_type=edge_type,
            edge_strength=edge_strength,
            situational_adjustment=sit_adj,
            weather_adjustment=weather_adj,
            emotional_adjustment=0.0,  # Can add later
            injury_adjustment=injury_adj,
            away_injuries=away_injury_impact,
            home_injuries=home_injury_impact,
            sharp_action=sharp_action or SharpAction(),
            crosses_key_number=crosses_key,
            key_number_value=key_number_value,
            recommended_bet=recommended_bet,
            kelly_fraction=kelly,
            confidence_score=confidence,
            timestamp=datetime.now().isoformat(),
            data_sources=["massey", "action_network", "nfl_official_injuries"],
        )

        return edge

    # =================================================================
    # OUTPUT
    # =================================================================

    def save_edges_jsonl(self, edges: List[BettingEdge], filename: str):
        """Save detected edges to JSONL format"""
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            for edge in edges:
                # Convert to dict
                edge_dict = asdict(edge)
                # Write as JSON line
                f.write(json.dumps(edge_dict) + "\n")

        logger.info(f"Saved {len(edges)} edges to {filepath}")

    def generate_report(self, edges: List[BettingEdge]) -> str:
        """Generate human-readable edge report"""
        report = []
        report.append("=" * 80)
        report.append("BILLY WALTERS EDGE DETECTION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")

        if not edges:
            report.append("No edges detected above minimum threshold (3.5 points)")
            return "\n".join(report)

        # Sort by edge strength
        edges_sorted = sorted(edges, key=lambda e: e.edge_points, reverse=True)

        for i, edge in enumerate(edges_sorted, 1):
            report.append(f"{i}. {edge.matchup} (Week {edge.week})")
            report.append(f"   Time: {edge.game_time}")
            report.append(
                f"   Power Ratings: {edge.away_team} {edge.away_rating:.1f} @ "
                f"{edge.home_team} {edge.home_rating:.1f}"
            )
            report.append(f"   Predicted Spread: {edge.predicted_spread:+.1f}")
            report.append(f"   Market Spread: {edge.market_spread:+.1f}")
            report.append(
                f"   EDGE: {edge.edge_points:.1f} points ({edge.edge_strength.upper()})"
            )
            report.append(
                f"   Recommendation: BET "
                f"{edge.recommended_bet.upper() if edge.recommended_bet else 'NONE'}"
            )
            report.append(
                f"   Kelly Sizing: {edge.kelly_fraction * 100:.1f}% of bankroll"
            )
            report.append(f"   Confidence: {edge.confidence_score:.0f}/100")

            if edge.situational_adjustment != 0:
                report.append(f"   Situational Adj: {edge.situational_adjustment:+.1f}")
            if edge.weather_adjustment != 0:
                report.append(f"   Weather Adj: {edge.weather_adjustment:+.1f}")
            if edge.sharp_action.reverse_line_movement:
                report.append("   [!] REVERSE LINE MOVEMENT DETECTED!")
            if edge.crosses_key_number:
                report.append(f"   [KEY] Crosses key number: {edge.key_number_value}")

            report.append("")

        report.append("=" * 80)
        report.append(f"Total Edges Found: {len(edges)}")
        report.append(
            f"Strong/Very Strong: "
            f"{sum(1 for e in edges if e.edge_strength in ['strong', 'very_strong'])}"
        )
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Demo: Run edge detection on real data"""
    detector = BillyWaltersEdgeDetector()

    # Initialize weather client
    weather_client = AccuWeatherClient()
    if not weather_client.api_key:
        logger.warning("No AccuWeather API key - weather analysis will be skipped")

    # Load proprietary 90/10 power ratings (Week 9 is latest with real data)
    logger.info("=" * 80)
    logger.info("USING BILLY WALTERS PROPRIETARY 90/10 POWER RATINGS FOR SPREADS")
    logger.info("=" * 80)
    detector.load_proprietary_ratings(week=9)  # Latest week with actual game results

    # Load Massey ratings for Offensive/Defensive data (needed for totals)
    logger.info("=" * 80)
    logger.info("LOADING MASSEY OFF/DEF RATINGS FOR TOTALS ANALYSIS")
    logger.info("=" * 80)
    massey_file = "output/massey/nfl_ratings_20251109_050042.json"
    massey_ratings_for_totals = {}
    if os.path.exists(massey_file):
        # Store current ratings
        spread_ratings = detector.power_ratings.copy()

        # Load Massey with Off/Def extraction
        detector.load_massey_ratings(massey_file, league="nfl")

        # Save Massey ratings for totals
        massey_ratings_for_totals = detector.power_ratings.copy()

        # Restore proprietary ratings for spread detection
        detector.power_ratings = spread_ratings

        logger.info(
            f"Loaded {len(massey_ratings_for_totals)} Massey ratings with "
            f"Off/Def for totals"
        )

    # Initialize totals detector
    from walters_analyzer.valuation.billy_walters_totals_detector import (
        BillyWaltersTotalsDetector,
    )

    totals_detector = BillyWaltersTotalsDetector()
    totals_detector.load_power_ratings(massey_ratings_for_totals)
    totals_detector.injury_data = {}  # Will share injury data

    # Load injury data (finds latest file automatically)
    detector.load_injury_data()
    totals_detector.injury_data = detector.injury_data  # Share with totals detector

    # Load Action Network odds (latest)
    action_file = "output/action_network/nfl_api_responses_20251109_045916.json"
    if os.path.exists(action_file):
        games_data = detector.load_action_network_odds(action_file)

        # Analyze each game
        edges = []
        totals_edges = []
        for game_id, game in games_data.items():
            # Extract teams
            teams = game.get("teams", [])
            if len(teams) < 2:
                continue

            # Normalize team names for Massey lookup
            home_team = detector.normalize_team_name(teams[0]["display_name"])
            away_team = detector.normalize_team_name(teams[1]["display_name"])

            # Extract market data
            markets = game.get("markets", {})
            if not markets:
                continue

            # Get first sportsbook's odds
            first_book = list(markets.values())[0]
            event_markets = first_book.get("event", {})

            # Extract spread
            spread_data = event_markets.get("spread", [])
            if not spread_data:
                continue

            market_spread = spread_data[0].get("value", 0)

            # Extract total
            total_data = event_markets.get("total", [])
            market_total = total_data[0].get("value", 47.0) if total_data else 47.0

            # Extract sharp action
            if spread_data and "bet_info" in spread_data[0]:
                bet_info = spread_data[0]["bet_info"]
                money_pct = bet_info.get("money", {}).get("percent", 50)
                tickets_pct = bet_info.get("tickets", {}).get("percent", 50)

                sharp = detector.analyze_sharp_action(money_pct, tickets_pct)
            else:
                sharp = None

            # Fetch weather data for the game
            weather_impact = None
            game_time_str = game.get("start_time", "")
            if weather_client.api_key and game_time_str:
                try:
                    # Parse game time (format: "2025-11-09T18:00:00.000Z")
                    game_time = datetime.fromisoformat(
                        game_time_str.replace("Z", "+00:00")
                    )

                    # Get weather for home team's location
                    # (async call - run synchronously)
                    async def fetch_weather():
                        await weather_client.connect()
                        return await weather_client.get_game_weather(
                            home_team, game_time
                        )

                    weather_data = asyncio.run(fetch_weather())

                    if weather_data:
                        # Fetch weather alerts from OpenWeather (if available)
                        weather_alerts = []
                        try:
                            # Check if we have OpenWeather client
                            # (needs OPENWEATHER_API_KEY)
                            if os.getenv("OPENWEATHER_API_KEY"):
                                # Get stadium coordinates from weather data
                                lat = weather_data.get("latitude")
                                lon = weather_data.get("longitude")

                                if lat and lon:
                                    # Define async helper to fetch alerts
                                    async def fetch_alerts():
                                        openweather = OpenWeatherClient()
                                        await openweather.connect()
                                        try:
                                            alert_data = (
                                                await openweather.get_weather_alerts(
                                                    lat=lat,
                                                    lon=lon,
                                                    game_time=game_time,
                                                )
                                            )
                                            return alert_data
                                        finally:
                                            await openweather.close()

                                    # Run async function in sync context
                                    alert_data = asyncio.run(fetch_alerts())

                                    # Map alerts to Billy Walters adjustments
                                    mapper = WeatherAlertMapper()
                                    for alert in alert_data:
                                        weather_alerts.append(mapper.map_alert(alert))

                                    if weather_alerts:
                                        logger.info(
                                            f"Found {len(weather_alerts)} active "
                                            f"weather alerts for {home_team}"
                                        )
                        except Exception as alert_error:
                            logger.debug(f"Weather alerts unavailable: {alert_error}")

                        # Calculate combined weather impact (conditions + alerts)
                        weather_impact = detector.calculate_weather_impact(
                            temperature=weather_data.get("temperature"),
                            wind_speed=weather_data.get("wind_speed"),
                            precipitation=weather_data.get("precipitation"),
                            indoor=weather_data.get("indoor", False),
                            alerts=weather_alerts if weather_alerts else None,
                        )

                        # Log weather impact details
                        alert_info = ""
                        if weather_impact.alert_severity != "NONE":
                            alert_info = (
                                f" [ALERT: {weather_impact.alert_severity} "
                                f"({weather_impact.alert_total_adjustment:.1f} pts)]"
                            )

                        logger.info(
                            f"Weather for {home_team}: "
                            f"{weather_data.get('temperature')}°F, "
                            f"{weather_data.get('wind_speed')} MPH wind, "
                            f"Total adj: {weather_impact.total_adjustment:.1f}, "
                            f"Spread adj: {weather_impact.spread_adjustment:.1f}"
                            f"{alert_info}"
                        )
                except Exception as e:
                    logger.warning(f"Could not fetch weather for {home_team}: {e}")

            # Detect edge
            edge = detector.detect_edge(
                game_id=game_id,
                away_team=away_team,
                home_team=home_team,
                market_spread=market_spread,
                market_total=market_total,
                week=game.get("week", 10),
                game_time=game.get("start_time", ""),
                weather=weather_impact,
                sharp_action=sharp,
            )

            if edge:
                edges.append(edge)

            # Detect totals edge
            totals_edge = totals_detector.detect_totals_edge(
                game_id=game_id,
                away_team=away_team,
                home_team=home_team,
                market_total=market_total,
                market_over_odds=total_data[0].get("odds", -110)
                if total_data
                else -110,
                market_under_odds=total_data[1].get("odds", -110)
                if len(total_data) > 1
                else -110,
                week=game.get("week", 10),
                game_time=game.get("start_time", ""),
                weather=weather_impact,
                sharp_action=sharp,
                away_injuries=detector.calculate_team_injury_impact(away_team),
                home_injuries=detector.calculate_team_injury_impact(home_team),
            )

            if totals_edge:
                totals_edges.append(totals_edge)

        # Save and report spread edges
        if edges:
            detector.save_edges_jsonl(edges, "nfl_edges_detected.jsonl")
            report = detector.generate_report(edges)
            print(report)

            # Save report
            with open(f"{detector.output_dir}/edge_report.txt", "w") as f:
                f.write(report)
        else:
            logger.info("No spread edges detected above threshold")

        # Save and report totals edges
        if totals_edges:
            totals_detector.save_totals_edges(totals_edges, "nfl_totals_detected.jsonl")
            totals_report = totals_detector.generate_totals_report(totals_edges)

            # Print with UTF-8 encoding for Windows console
            try:
                print("\n" + totals_report)
            except UnicodeEncodeError:
                # Fallback: encode to ASCII, replacing special characters
                print("\n" + totals_report.encode("ascii", "replace").decode("ascii"))

            # Save totals report
            with open(
                f"{totals_detector.output_dir}/totals_report.txt", "w", encoding="utf-8"
            ) as f:
                f.write(totals_report)
        else:
            logger.info("No totals edges detected above threshold")

    else:
        logger.error("Required data files not found")


if __name__ == "__main__":
    main()
