"""
Billy Walters NFL Power Ratings System
=====================================
Professional sports betting power ratings implementation
Based on Billy Walters' Advanced Master Class methodology

Author: NFL Analytics Team
Date: November 2025
Version: 2.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PART 1: DATA STRUCTURES AND CONSTANTS
# ============================================================================

class BetType(Enum):
    """Types of bets available"""
    SPREAD = "spread"
    MONEYLINE = "moneyline"
    TOTAL = "total"
    TEASER = "teaser"

class PlayerPosition(Enum):
    """NFL player positions with point values"""
    QB = "Quarterback"
    WR = "Wide Receiver"
    RB = "Running Back"
    TE = "Tight End"
    OL = "Offensive Line"
    DL = "Defensive Line"
    LB = "Linebacker"
    DB = "Defensive Back"
    K = "Kicker"
    P = "Punter"

@dataclass
class TeamRating:
    """Complete team rating with all factors"""
    team: str
    base_rating: float
    offensive_rating: float
    defensive_rating: float
    special_teams_rating: float
    home_field_advantage: float
    injury_adjustment: float
    momentum_factor: float
    weather_preference: float
    rest_days: int = 7
    travel_distance: int = 0
    division_game: bool = False
    primetime: bool = False
    revenge_game: bool = False
    must_win: bool = False
    updated: datetime = field(default_factory=datetime.now)
    
    @property
    def total_rating(self) -> float:
        """Calculate total power rating with all factors"""
        return (self.base_rating + 
                self.offensive_rating + 
                self.defensive_rating + 
                self.special_teams_rating * 0.5 +
                self.injury_adjustment +
                self.momentum_factor)

@dataclass
class PlayerInjury:
    """Track player injuries and their impact"""
    player_name: str
    position: PlayerPosition
    team: str
    status: str  # OUT, DOUBTFUL, QUESTIONABLE, PROBABLE
    injury_type: str
    point_impact: float
    weeks_out: int = 0
    replacement_quality: float = 0.5  # 0-1 scale

@dataclass
class GamePrediction:
    """Complete game prediction with all calculations"""
    home_team: str
    away_team: str
    home_rating: float
    away_rating: float
    raw_spread: float
    s_factors_home: float
    s_factors_away: float
    adjusted_spread: float
    market_spread: float
    edge: float
    edge_percentage: float
    confidence_stars: float
    recommended_bet: Optional[str]
    kelly_size: float
    max_bet_size: float
    key_number_proximity: float
    closing_line_value: Optional[float] = None

# ============================================================================
# PART 2: BILLY WALTERS CONSTANTS
# ============================================================================

class WaltersConstants:
    """All constants from Billy Walters' methodology"""
    
    # Power Rating Scale
    ELITE_RATING = 10.0
    AVERAGE_RATING = 0.0
    TERRIBLE_RATING = -10.0
    
    # Weekly Update Formula
    OLD_RATING_WEIGHT = 0.90
    NEW_PERFORMANCE_WEIGHT = 0.10
    
    # Home Field Advantages by Stadium
    HOME_FIELD_ADVANTAGES = {
        "Kansas City": 3.5, "Seattle": 3.5, "Denver": 3.5,
        "Buffalo": 3.0, "Green Bay": 3.0, "New Orleans": 3.0,
        "Baltimore": 2.8, "Philadelphia": 2.8, "Pittsburgh": 2.8,
        "Minnesota": 2.5, "Tennessee": 2.5, "Chicago": 2.5,
        "Cleveland": 2.5, "New England": 2.5, "Cincinnati": 2.5,
        "Tampa Bay": 2.3, "Miami": 2.3, "Arizona": 2.3,
        "San Francisco": 2.3, "Dallas": 2.3, "Houston": 2.3,
        "Indianapolis": 2.0, "Detroit": 2.0, "Atlanta": 2.0,
        "Las Vegas": 2.0, "Jacksonville": 2.0, "Carolina": 2.0,
        "LA Rams": 1.8, "LA Chargers": 1.8, "NY Giants": 1.8,
        "NY Jets": 1.8, "Washington": 2.0
    }
    
    # Player Position Values (in points)
    POSITION_VALUES = {
        PlayerPosition.QB: {"elite": 10.0, "starter": 7.0, "backup": 3.0},
        PlayerPosition.WR: {"elite": 3.0, "starter": 1.5, "backup": 0.5},
        PlayerPosition.RB: {"elite": 2.0, "starter": 1.0, "backup": 0.3},
        PlayerPosition.TE: {"elite": 2.5, "starter": 1.2, "backup": 0.4},
        PlayerPosition.OL: {"elite": 2.0, "starter": 1.5, "backup": 0.5},
        PlayerPosition.DL: {"elite": 2.5, "starter": 1.5, "backup": 0.5},
        PlayerPosition.LB: {"elite": 2.0, "starter": 1.2, "backup": 0.4},
        PlayerPosition.DB: {"elite": 2.0, "starter": 1.0, "backup": 0.3},
        PlayerPosition.K: {"elite": 1.5, "starter": 0.8, "backup": 0.2},
        PlayerPosition.P: {"elite": 1.0, "starter": 0.5, "backup": 0.1}
    }
    
    # S-Factor Adjustments
    REST_ADVANTAGE = {
        "extra_week": 2.0,      # Team with bye week advantage
        "short_week": -1.5,     # Thursday game after Sunday
        "monday_after": -1.0,   # Playing after Monday night
        "mini_bye": 0.5        # Playing after Thursday (extra rest)
    }
    
    TRAVEL_IMPACT = {
        "cross_country": -1.0,  # 3+ time zones
        "international": -1.5,  # London/Mexico games
        "divisional": 0.0,      # Division rival (minimal travel)
        "regional": -0.3        # 1-2 time zones
    }
    
    WEATHER_IMPACT = {
        "heavy_rain": -1.5,     # For passing teams
        "snow": -2.0,           # For dome teams
        "extreme_cold": -1.0,   # Below 20°F for warm weather teams
        "high_wind": -1.5,      # 20+ mph winds
        "perfect": 0.0          # No weather impact
    }
    
    # Key Numbers in NFL Betting
    KEY_NUMBERS = {
        3: 0.08,   # 8% of games land on 3
        7: 0.06,   # 6% of games land on 7
        6: 0.05,   # 5% of games land on 6
        10: 0.04,  # 4% of games land on 10
        14: 0.05,  # 5% of games land on 14
        4: 0.03,   # 3% of games land on 4
        1: 0.02,   # 2% of games land on 1
    }
    
    # Betting Thresholds
    MIN_EDGE_PERCENTAGE = 5.5  # Minimum 5.5% edge to bet
    MAX_BET_PERCENTAGE = 3.0    # Maximum 3% of bankroll per bet
    KELLY_FRACTION = 0.25       # Use 25% Kelly for sizing
    
    # Star System for Bet Sizing
    STAR_SYSTEM = {
        5.5: 0.5,   # 0.5 stars: 0.5% of bankroll
        7.0: 1.0,   # 1 star: 1% of bankroll
        9.0: 1.5,   # 1.5 stars: 1.5% of bankroll
        11.0: 2.0,  # 2 stars: 2% of bankroll
        13.0: 2.5,  # 2.5 stars: 2.5% of bankroll
        15.0: 3.0   # 3 stars: 3% of bankroll (max)
    }

# ============================================================================
# PART 3: POWER RATINGS ENGINE
# ============================================================================

class PowerRatingsEngine:
    """Main engine for calculating and updating power ratings"""
    
    def __init__(self):
        self.constants = WaltersConstants()
        self.team_ratings: Dict[str, TeamRating] = {}
        self.player_injuries: List[PlayerInjury] = []
        self.game_results: List[Dict] = []
        self.predictions: List[GamePrediction] = []
        
    def initialize_ratings(self, preseason_ratings: Dict[str, float]):
        """Initialize team ratings for the season"""
        for team, rating in preseason_ratings.items():
            self.team_ratings[team] = TeamRating(
                team=team,
                base_rating=rating,
                offensive_rating=0.0,
                defensive_rating=0.0,
                special_teams_rating=0.0,
                home_field_advantage=self.constants.HOME_FIELD_ADVANTAGES.get(team, 2.0),
                injury_adjustment=0.0,
                momentum_factor=0.0,
                weather_preference=0.0
            )
        logger.info(f"Initialized ratings for {len(self.team_ratings)} teams")
    
    def update_rating_after_game(self, team: str, game_result: Dict) -> float:
        """
        Update team rating using Billy Walters' 90/10 formula
        
        Formula: New Rating = (90% × Old Rating) + (10% × True Performance)
        True Performance = Margin + Opponent Rating + Injury Diff - HFA
        """
        if team not in self.team_ratings:
            logger.warning(f"Team {team} not found in ratings")
            return 0.0
        
        old_rating = self.team_ratings[team].total_rating
        
        # Calculate true game performance
        margin = game_result['margin'] if game_result['team'] == team else -game_result['margin']
        opponent_rating = self.team_ratings[game_result['opponent']].total_rating
        injury_diff = game_result.get('injury_differential', 0.0)
        
        # Adjust for home field
        if game_result['location'] == 'home' and game_result['team'] == team:
            hfa_adjustment = -self.team_ratings[team].home_field_advantage
        elif game_result['location'] == 'away' and game_result['team'] == team:
            hfa_adjustment = self.team_ratings[game_result['opponent']].home_field_advantage
        else:
            hfa_adjustment = 0.0
        
        true_performance = margin + opponent_rating + injury_diff + hfa_adjustment
        
        # Apply 90/10 formula
        new_rating = (self.constants.OLD_RATING_WEIGHT * old_rating + 
                     self.constants.NEW_PERFORMANCE_WEIGHT * true_performance)
        
        # Update the team's base rating
        self.team_ratings[team].base_rating = new_rating
        self.team_ratings[team].updated = datetime.now()
        
        # Update momentum factor
        self._update_momentum_factor(team, margin > 0)
        
        logger.info(f"Updated {team}: {old_rating:.2f} → {new_rating:.2f} "
                   f"(True Perf: {true_performance:.2f})")
        
        return new_rating
    
    def _update_momentum_factor(self, team: str, won: bool):
        """Update team's momentum based on recent results"""
        current_momentum = self.team_ratings[team].momentum_factor
        
        if won:
            # Winning increases momentum (max +2.0)
            new_momentum = min(current_momentum + 0.3, 2.0)
        else:
            # Losing decreases momentum (min -2.0)
            new_momentum = max(current_momentum - 0.3, -2.0)
        
        # Decay towards 0 over time
        new_momentum *= 0.9
        
        self.team_ratings[team].momentum_factor = new_momentum
    
    def calculate_injury_impact(self, team: str) -> float:
        """
        Calculate total injury impact for a team
        Uses cluster injury multiplier for multiple injuries
        """
        team_injuries = [inj for inj in self.player_injuries 
                        if inj.team == team and inj.status in ["OUT", "DOUBTFUL"]]
        
        if not team_injuries:
            return 0.0
        
        # Base injury impact
        total_impact = sum(inj.point_impact for inj in team_injuries)
        
        # Apply cluster injury multiplier (Billy Walters methodology)
        if len(team_injuries) >= 3:
            if any(inj.position == PlayerPosition.QB for inj in team_injuries):
                multiplier = 1.5  # Multiple injuries including QB
            else:
                multiplier = 1.3  # Multiple injuries, no QB
        else:
            multiplier = 1.0
        
        adjusted_impact = -total_impact * multiplier  # Negative because injuries hurt rating
        
        logger.info(f"{team} injury impact: {adjusted_impact:.2f} points "
                   f"({len(team_injuries)} injuries)")
        
        return adjusted_impact
    
    def calculate_s_factors(self, team: str, game_info: Dict) -> float:
        """
        Calculate all game-specific S-factors
        Includes: rest, travel, weather, situational
        """
        s_factors = 0.0
        rating = self.team_ratings[team]
        
        # Rest differential
        if game_info.get('rest_days', 7) > 10:
            s_factors += self.constants.REST_ADVANTAGE['extra_week']
        elif game_info.get('rest_days', 7) < 7:
            s_factors += self.constants.REST_ADVANTAGE['short_week']
        
        # Travel impact
        travel_distance = game_info.get('travel_distance', 0)
        if travel_distance > 2000:
            s_factors += self.constants.TRAVEL_IMPACT['cross_country']
        elif travel_distance > 500:
            s_factors += self.constants.TRAVEL_IMPACT['regional']
        
        # Weather conditions
        weather = game_info.get('weather', {})
        if weather.get('rain', False) and weather.get('wind_mph', 0) > 15:
            s_factors += self.constants.WEATHER_IMPACT['heavy_rain']
        elif weather.get('temp_f', 70) < 20:
            s_factors += self.constants.WEATHER_IMPACT['extreme_cold']
        elif weather.get('wind_mph', 0) > 20:
            s_factors += self.constants.WEATHER_IMPACT['high_wind']
        
        # Situational factors
        if game_info.get('division_game', False):
            s_factors += 0.5  # Division games are closer
        if game_info.get('primetime', False):
            s_factors += 0.3  # Primetime performance varies
        if game_info.get('revenge_game', False):
            s_factors += 1.0  # Revenge game motivation
        if game_info.get('must_win', False):
            s_factors += 1.5  # Desperation factor
        
        logger.debug(f"{team} S-factors: {s_factors:.2f}")
        return s_factors

# ============================================================================
# PART 4: BETTING ANALYSIS ENGINE
# ============================================================================

class BettingAnalysis:
    """Analyze games for betting opportunities using Billy Walters' criteria"""
    
    def __init__(self, ratings_engine: PowerRatingsEngine):
        self.engine = ratings_engine
        self.constants = WaltersConstants()
        
    def analyze_game(self, home_team: str, away_team: str, 
                     market_spread: float, game_info: Dict) -> GamePrediction:
        """
        Complete game analysis with edge identification
        """
        # Get team ratings
        home_rating = self.engine.team_ratings[home_team]
        away_rating = self.engine.team_ratings[away_team]
        
        # Calculate raw spread (home perspective)
        raw_spread = home_rating.total_rating - away_rating.total_rating
        
        # Add home field advantage
        raw_spread += home_rating.home_field_advantage
        
        # Calculate S-factors for each team
        s_factors_home = self.engine.calculate_s_factors(home_team, game_info)
        s_factors_away = self.engine.calculate_s_factors(away_team, game_info)
        s_factor_differential = (s_factors_home - s_factors_away) / 5  # Divide by 5 as per Walters
        
        # Adjusted spread
        adjusted_spread = raw_spread + s_factor_differential
        
        # Calculate edge
        edge = market_spread - adjusted_spread
        edge_percentage = self._calculate_edge_percentage(edge, market_spread)
        
        # Determine bet sizing using star system
        confidence_stars = self._calculate_stars(edge_percentage)
        
        # Check key numbers
        key_number_proximity = self._check_key_numbers(adjusted_spread, market_spread)
        
        # Determine if we should bet
        recommended_bet = self._determine_bet(edge, edge_percentage, key_number_proximity)
        
        # Calculate Kelly sizing
        kelly_size = self._calculate_kelly_size(edge_percentage, confidence_stars)
        
        # Create prediction
        prediction = GamePrediction(
            home_team=home_team,
            away_team=away_team,
            home_rating=home_rating.total_rating,
            away_rating=away_rating.total_rating,
            raw_spread=raw_spread,
            s_factors_home=s_factors_home,
            s_factors_away=s_factors_away,
            adjusted_spread=adjusted_spread,
            market_spread=market_spread,
            edge=edge,
            edge_percentage=edge_percentage,
            confidence_stars=confidence_stars,
            recommended_bet=recommended_bet,
            kelly_size=kelly_size,
            max_bet_size=min(kelly_size, self.constants.MAX_BET_PERCENTAGE),
            key_number_proximity=key_number_proximity
        )
        
        logger.info(f"Analysis: {home_team} vs {away_team}")
        logger.info(f"  Our line: {adjusted_spread:.1f}, Market: {market_spread:.1f}")
        logger.info(f"  Edge: {edge:.1f} points ({edge_percentage:.1f}%)")
        logger.info(f"  Bet: {recommended_bet}, Stars: {confidence_stars}")
        
        return prediction
    
    def _calculate_edge_percentage(self, edge: float, spread: float) -> float:
        """Convert point edge to percentage using implied probability"""
        # Simplified calculation - in reality would use more sophisticated model
        if abs(spread) < 0.5:
            return 0.0
        
        # Approximate edge percentage calculation
        # Each point of edge is worth roughly 2-3% depending on the spread
        if abs(spread) <= 3:
            percentage_per_point = 3.0
        elif abs(spread) <= 7:
            percentage_per_point = 2.5
        else:
            percentage_per_point = 2.0
        
        return abs(edge) * percentage_per_point
    
    def _calculate_stars(self, edge_percentage: float) -> float:
        """
        Calculate bet size using Billy Walters' star system
        Based on edge percentage thresholds
        """
        for threshold, stars in sorted(self.constants.STAR_SYSTEM.items(), reverse=True):
            if edge_percentage >= threshold:
                return stars
        return 0.0
    
    def _check_key_numbers(self, our_spread: float, market_spread: float) -> float:
        """
        Check proximity to key numbers (especially 3 and 7)
        Returns bonus/penalty for key number positioning
        """
        key_bonus = 0.0
        
        for key_num, frequency in self.constants.KEY_NUMBERS.items():
            # Check if we're getting value crossing a key number
            if (our_spread < key_num < market_spread) or (market_spread < key_num < our_spread):
                key_bonus += frequency * 10  # Bonus for crossing key number favorably
            
            # Check if we're on the right side of a key number
            if abs(market_spread - key_num) < 0.5:
                if (market_spread > key_num and our_spread > market_spread) or \
                   (market_spread < -key_num and our_spread < market_spread):
                    key_bonus += frequency * 5  # Bonus for being on right side
        
        return key_bonus
    
    def _determine_bet(self, edge: float, edge_percentage: float, 
                      key_number_proximity: float) -> Optional[str]:
        """
        Determine betting recommendation based on Billy Walters' criteria
        """
        # Adjust edge percentage for key numbers
        total_edge = edge_percentage + key_number_proximity
        
        # Must meet minimum edge threshold
        if total_edge < self.constants.MIN_EDGE_PERCENTAGE:
            return None
        
        # Determine which side to bet
        if edge > 0:
            return "AWAY"  # Market spread too high, bet on away team
        else:
            return "HOME"  # Market spread too low, bet on home team
    
    def _calculate_kelly_size(self, edge_percentage: float, stars: float) -> float:
        """
        Calculate bet size using Kelly Criterion
        Uses fractional Kelly (25%) for safety
        """
        if edge_percentage <= 0 or stars == 0:
            return 0.0
        
        # Simplified Kelly: edge / odds
        # Assuming standard -110 odds (52.4% implied probability)
        win_probability = 0.524 + (edge_percentage / 100)
        
        # Full Kelly
        full_kelly = (win_probability - 0.476) / 0.524
        
        # Fractional Kelly (25%) capped at star system max
        fractional_kelly = full_kelly * self.constants.KELLY_FRACTION
        
        # Use minimum of Kelly and star system
        return min(fractional_kelly * 100, stars)

# ============================================================================
# PART 5: WEEKLY WORKFLOW MANAGER
# ============================================================================

class WeeklyWorkflow:
    """Manage the complete weekly betting workflow"""
    
    def __init__(self, ratings_engine: PowerRatingsEngine, 
                 betting_analysis: BettingAnalysis):
        self.ratings = ratings_engine
        self.analysis = betting_analysis
        self.weekly_predictions = []
        self.weekly_bets = []
        
    def sunday_night_update(self, week_results: List[Dict]):
        """Sunday night: Update all power ratings based on results"""
        logger.info(f"=== SUNDAY NIGHT UPDATE - Week {week_results[0].get('week', 'N/A')} ===")
        
        for result in week_results:
            # Update both teams
            self.ratings.update_rating_after_game(result['home_team'], result)
            self.ratings.update_rating_after_game(result['away_team'], {
                **result,
                'team': result['away_team'],
                'opponent': result['home_team'],
                'margin': -result['margin'],
                'location': 'away'
            })
        
        logger.info("Power ratings updated for all teams")
    
    def tuesday_analysis(self, upcoming_games: List[Dict], 
                         market_lines: Dict[str, float]) -> List[GamePrediction]:
        """Tuesday/Wednesday: Analyze all upcoming games"""
        logger.info("=== TUESDAY ANALYSIS - Identifying Edges ===")
        
        predictions = []
        for game in upcoming_games:
            home = game['home_team']
            away = game['away_team']
            
            # Get market spread
            game_key = f"{away}@{home}"
            market_spread = market_lines.get(game_key, 0.0)
            
            # Analyze game
            prediction = self.analysis.analyze_game(home, away, market_spread, game)
            predictions.append(prediction)
            
            # Track if it's a betting opportunity
            if prediction.recommended_bet:
                self.weekly_bets.append(prediction)
        
        self.weekly_predictions = predictions
        
        # Sort by edge size
        self.weekly_bets.sort(key=lambda x: abs(x.edge_percentage), reverse=True)
        
        logger.info(f"Found {len(self.weekly_bets)} betting opportunities")
        return predictions
    
    def generate_bet_sheet(self, bankroll: float) -> pd.DataFrame:
        """Generate the weekly betting sheet with all recommendations"""
        bet_data = []
        
        for bet in self.weekly_bets:
            bet_amount = (bet.max_bet_size / 100) * bankroll
            
            bet_data.append({
                'Game': f"{bet.away_team} @ {bet.home_team}",
                'Bet': bet.recommended_bet,
                'Our Line': round(bet.adjusted_spread, 1),
                'Market Line': bet.market_spread,
                'Edge': round(bet.edge, 1),
                'Edge %': round(bet.edge_percentage, 1),
                'Stars': bet.confidence_stars,
                'Bet Size %': round(bet.max_bet_size, 2),
                'Bet Amount': round(bet_amount, 2),
                'Key #': 'Yes' if bet.key_number_proximity > 0 else 'No'
            })
        
        df = pd.DataFrame(bet_data)
        
        if not df.empty:
            # Add summary row
            total_risk = df['Bet Amount'].sum()
            avg_edge = df['Edge %'].mean()
            
            logger.info(f"\n=== WEEKLY BET SUMMARY ===")
            logger.info(f"Total Bets: {len(df)}")
            logger.info(f"Total Risk: ${total_risk:,.2f}")
            logger.info(f"Average Edge: {avg_edge:.1f}%")
            logger.info(f"Bankroll at Risk: {(total_risk/bankroll)*100:.1f}%")
        
        return df

# ============================================================================
# PART 6: CURRENT WEEK 9 NFL POWER RATINGS (2024 Season)
# ============================================================================

def get_current_nfl_ratings() -> Dict[str, float]:
    """
    Current NFL Power Ratings based on Week 9, 2024 season
    Synthesized from multiple sources with Billy Walters adjustments
    """
    return {
        # Elite Teams (+5 to +10)
        "Detroit": 8.5,
        "Kansas City": 8.0,
        "Buffalo": 7.0,
        "Baltimore": 6.5,
        
        # Very Good Teams (+3 to +5)
        "Philadelphia": 5.0,
        "Green Bay": 4.5,
        "Washington": 4.0,
        "Pittsburgh": 3.5,
        "Houston": 3.5,
        
        # Good Teams (+1 to +3)
        "Minnesota": 3.0,
        "Atlanta": 2.5,
        "San Francisco": 2.0,
        "Denver": 2.0,
        "LA Chargers": 1.5,
        "Arizona": 1.0,
        "Tampa Bay": 1.0,
        
        # Average Teams (-1 to +1)
        "Seattle": 0.5,
        "Cincinnati": 0.0,
        "Indianapolis": 0.0,
        "LA Rams": -0.5,
        "Chicago": -0.5,
        "Dallas": -1.0,
        
        # Below Average Teams (-3 to -1)
        "Miami": -1.5,
        "NY Jets": -2.0,
        "Jacksonville": -2.5,
        "New Orleans": -2.5,
        "Cleveland": -3.0,
        
        # Poor Teams (-6 to -3)
        "NY Giants": -4.0,
        "Las Vegas": -4.5,
        "Tennessee": -5.0,
        "New England": -5.5,
        
        # Terrible Teams (-10 to -6)
        "Carolina": -8.0
    }

# ============================================================================
# PART 7: EXAMPLE USAGE AND TESTING
# ============================================================================

def run_example_analysis():
    """Run example analysis for Week 10 games"""
    
    # Initialize the system
    engine = PowerRatingsEngine()
    engine.initialize_ratings(get_current_nfl_ratings())
    
    # Create betting analyzer
    analyzer = BettingAnalysis(engine)
    
    # Create workflow manager
    workflow = WeeklyWorkflow(engine, analyzer)
    
    # Example: Add some injuries
    engine.player_injuries = [
        PlayerInjury(
            player_name="Dak Prescott",
            position=PlayerPosition.QB,
            team="Dallas",
            status="OUT",
            injury_type="Hamstring",
            point_impact=7.0,
            weeks_out=4
        ),
        PlayerInjury(
            player_name="Chris Olave",
            position=PlayerPosition.WR,
            team="New Orleans",
            status="DOUBTFUL",
            injury_type="Concussion",
            point_impact=2.0,
            weeks_out=1
        )
    ]
    
    # Update injury impacts
    for team in ["Dallas", "New Orleans"]:
        impact = engine.calculate_injury_impact(team)
        engine.team_ratings[team].injury_adjustment = impact
    
    # Example Week 10 games with market lines
    upcoming_games = [
        {
            'home_team': 'Kansas City', 
            'away_team': 'Denver',
            'rest_days': 7,
            'travel_distance': 600,
            'division_game': True,
            'primetime': False,
            'weather': {'temp_f': 45, 'wind_mph': 10}
        },
        {
            'home_team': 'Buffalo', 
            'away_team': 'Indianapolis',
            'rest_days': 7,
            'travel_distance': 500,
            'division_game': False,
            'primetime': False,
            'weather': {'temp_f': 35, 'wind_mph': 15}
        },
        {
            'home_team': 'Philadelphia', 
            'away_team': 'Dallas',
            'rest_days': 7,
            'travel_distance': 200,
            'division_game': True,
            'primetime': True,
            'weather': {'temp_f': 55, 'wind_mph': 5}
        }
    ]
    
    market_lines = {
        'Denver@Kansas City': -7.5,
        'Indianapolis@Buffalo': -4.5,
        'Dallas@Philadelphia': -7.0
    }
    
    # Run Tuesday analysis
    predictions = workflow.tuesday_analysis(upcoming_games, market_lines)
    
    # Generate bet sheet
    bankroll = 10000  # $10,000 bankroll
    bet_sheet = workflow.generate_bet_sheet(bankroll)
    
    print("\n" + "="*80)
    print("BILLY WALTERS NFL POWER RATINGS - WEEK 10 BETTING SHEET")
    print("="*80)
    
    if not bet_sheet.empty:
        print(bet_sheet.to_string(index=False))
    else:
        print("No qualifying bets found (minimum 5.5% edge required)")
    
    print("\n" + "="*80)
    print("DETAILED PREDICTIONS")
    print("="*80)
    
    for pred in predictions:
        print(f"\n{pred.away_team} @ {pred.home_team}")
        print(f"  Power Ratings: {pred.home_team} {pred.home_rating:.1f} vs {pred.away_team} {pred.away_rating:.1f}")
        print(f"  Our Spread: {pred.adjusted_spread:.1f}")
        print(f"  Market Spread: {pred.market_spread:.1f}")
        print(f"  Edge: {pred.edge:.1f} points ({pred.edge_percentage:.1f}%)")
        if pred.recommended_bet:
            print(f"  ⭐ BET: {pred.recommended_bet} - {pred.confidence_stars} stars")
        else:
            print(f"  ❌ No bet (edge below 5.5% threshold)")

if __name__ == "__main__":
    # Run the example
    run_example_analysis()
    
    print("\n" + "="*80)
    print("SYSTEM READY FOR PRODUCTION USE")
    print("="*80)
    print("\nTo use this system:")
    print("1. Update team ratings weekly using Sunday night results")
    print("2. Input current injury reports")
    print("3. Get market lines from sportsbooks")
    print("4. Run analysis to identify edges")
    print("5. Place bets according to star system")
    print("6. Track results and closing line value")
    print("\nRemember: Never bet more than 3% of bankroll on any single game!")
