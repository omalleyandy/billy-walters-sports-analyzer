"""
Data models for Billy Walters Sports Analyzer.

All dataclasses and enums consolidated in one place for:
- Easy discovery
- Better code organization
- Single source of truth
- Improved IDE autocomplete

Usage:
    from walters.core.models import (
        TeamRating,
        GameResult,
        GameContext,
        BetRecommendation,
        BetType,
        KeyNumberAnalysis,
        ComprehensiveAnalysis
    )
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class BetType(Enum):
    """Types of bets supported."""
    SPREAD = "spread"
    TOTAL = "total"
    MONEYLINE = "moneyline"
    TEASER = "teaser"
    PARLAY = "parlay"


# ============================================================================
# Power Ratings Models
# ============================================================================

@dataclass
class TeamRating:
    """Power rating for a single team."""
    team: str
    sport: str
    rating: float = 0.0
    games_played: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Historical tracking
    rating_history: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'team': self.team,
            'sport': self.sport,
            'rating': round(self.rating, 2),
            'games_played': self.games_played,
            'last_updated': self.last_updated,
            'rating_history': [round(r, 2) for r in self.rating_history[-10:]]  # Last 10 games
        }


@dataclass
class GameResult:
    """Represents a completed game for rating updates."""
    team: str
    opponent: str
    team_score: int
    opponent_score: int
    is_home: bool
    sport: str
    date: str
    injury_differential: float = 0.0  # Team injuries - opponent injuries (in points)

    @property
    def score_differential(self) -> int:
        """Raw score differential (positive = win)."""
        return self.team_score - self.opponent_score

    @property
    def points_scored(self) -> int:
        return self.team_score

    @property
    def points_allowed(self) -> int:
        return self.opponent_score


# ============================================================================
# Situational Factors (S/W/E) Models
# ============================================================================

@dataclass
class GameContext:
    """
    Context information for a game needed to calculate S/W/E factors.
    """
    # Team identifiers
    team: str
    opponent: str
    sport: str
    is_home: bool
    game_date: str

    # Situational factors
    team_rest_days: int = 7  # Days since last game
    opponent_rest_days: int = 7
    travel_miles: int = 0  # Travel distance for away team
    is_divisional: bool = False
    is_conference: bool = False
    is_rivalry: bool = False
    is_revenge: bool = False  # Lost to this opponent recently
    team_ats_last_5: int = 0  # ATS record last 5 games (-5 to +5)
    opponent_ats_last_5: int = 0

    # Weather factors (if applicable)
    wind_speed_mph: float = 0.0
    precipitation_prob: float = 0.0
    precipitation_type: Optional[str] = None  # 'rain', 'snow', None
    temperature_f: float = 70.0
    is_dome: bool = False

    # Emotional factors
    playoff_implications: str = "none"  # 'none', 'elimination', 'clinch', 'seeding'
    coaching_change: bool = False  # New coach this season
    injury_motivation: bool = False  # Star player returning/out (emotional impact)
    public_betting_pct: Optional[float] = None  # % of public on this team


# ============================================================================
# Injury Models
# ============================================================================

@dataclass
class InjuryReport:
    """Player injury information with enhanced analysis."""
    player_name: str
    position: str
    injury_type: str
    status: str  # Out, Doubtful, Questionable, Probable
    point_value: float = 0.0  # Impact on spread
    replacement_value: float = 0.0  # Quality of backup
    severity: str = "MODERATE"  # MINOR, MODERATE, SIGNIFICANT, SEVERE
    confidence: float = 0.5  # 0.0-1.0 confidence in the analysis
    source: str = "Manual"  # Source of injury information
    prognosis: str = ""  # Expected timeline/outcome
    timestamp: Optional[datetime] = None  # When injury info was gathered
    
    def to_dict(self) -> dict:
        return {
            'player_name': self.player_name,
            'position': self.position,
            'injury_type': self.injury_type,
            'status': self.status,
            'point_value': round(self.point_value, 1),
            'severity': self.severity,
            'confidence': round(self.confidence, 2),
            'source': self.source,
            'prognosis': self.prognosis
        }


# ============================================================================
# Key Numbers Models
# ============================================================================

@dataclass
class KeyNumberAnalysis:
    """Analysis of key numbers between two lines."""
    sport: str
    line1: float
    line2: float
    key_numbers_crossed: List[int]
    total_value: float  # Sum of key number values crossed
    edge_percentage: float  # Total edge as percentage
    recommendation: str


# ============================================================================
# Betting Models
# ============================================================================

@dataclass
class BetRecommendation:
    """Complete bet recommendation with sizing."""
    game: str
    bet_type: BetType
    side: str  # 'home', 'away', 'over', 'under'
    line: float
    price: int  # American odds (e.g., -110)

    # Edge analysis
    edge_percentage: float
    stars: float
    confidence: str  # 'Low', 'Medium', 'High', 'Very High'

    # Sizing
    bankroll: float
    bet_amount: float
    bet_percentage: float  # % of bankroll
    kelly_full: float  # Full Kelly recommendation
    kelly_fraction: float  # Fractional Kelly (recommended)

    # Risk metrics
    risk_of_ruin: float  # Probability of losing entire bankroll
    expected_value: float  # Expected profit

    # Context
    reasoning: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'game': self.game,
            'bet_type': self.bet_type.value,
            'side': self.side,
            'line': self.line,
            'price': self.price,
            'edge_percentage': round(self.edge_percentage, 2),
            'stars': self.stars,
            'confidence': self.confidence,
            'bankroll': round(self.bankroll, 2),
            'bet_amount': round(self.bet_amount, 2),
            'bet_percentage': round(self.bet_percentage, 2),
            'kelly_full': round(self.kelly_full, 2),
            'kelly_fraction': round(self.kelly_fraction, 2),
            'risk_of_ruin': round(self.risk_of_ruin, 4),
            'expected_value': round(self.expected_value, 2),
            'reasoning': self.reasoning
        }


@dataclass
class ComprehensiveAnalysis:
    """Complete analysis of a game from all perspectives."""
    # Game info
    game: str
    sport: str
    away_team: str
    home_team: str

    # Power ratings
    away_rating: float
    home_rating: float
    predicted_spread: float
    predicted_total: float

    # S/W/E factors
    swe_spread_adjustment: float
    swe_total_adjustment: float
    swe_summary: str
    swe_details: dict

    # Market comparison
    market_spread: float
    market_total: Optional[float]
    spread_price: int
    total_price: int

    # Key number analysis
    key_number_analysis: KeyNumberAnalysis
    edge_percentage: float

    # Bet recommendation
    recommendation: Optional[BetRecommendation]
    should_bet: bool

    # Context
    reasoning: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'game': self.game,
            'sport': self.sport,
            'away_team': self.away_team,
            'home_team': self.home_team,
            'power_ratings': {
                'away_rating': round(self.away_rating, 2),
                'home_rating': round(self.home_rating, 2),
                'predicted_spread': round(self.predicted_spread, 1),
                'predicted_total': round(self.predicted_total, 1),
            },
            'swe_factors': {
                'spread_adjustment': round(self.swe_spread_adjustment, 1),
                'total_adjustment': round(self.swe_total_adjustment, 1),
                'summary': self.swe_summary,
                'details': self.swe_details
            },
            'market': {
                'spread': self.market_spread,
                'total': self.market_total,
                'spread_price': self.spread_price,
                'total_price': self.total_price
            },
            'key_numbers': {
                'crossed': self.key_number_analysis.key_numbers_crossed,
                'edge_percentage': self.key_number_analysis.edge_percentage
            },
            'recommendation': self.recommendation.to_dict() if self.recommendation else None,
            'should_bet': self.should_bet,
            'reasoning': self.reasoning
        }


# ============================================================================
# Backward Compatibility Imports
# ============================================================================

# Users can still import from original locations
# These will be deprecated in v3.0

__all__ = [
    # Enums
    'BetType',
    
    # Power Ratings
    'TeamRating',
    'GameResult',
    
    # S/W/E Factors
    'GameContext',
    
    # Injuries
    'InjuryReport',
    
    # Key Numbers
    'KeyNumberAnalysis',
    
    # Betting
    'BetRecommendation',
    'ComprehensiveAnalysis',
]


# Example usage
if __name__ == "__main__":
    print("Billy Walters Sports Analyzer - Data Models")
    print("=" * 50)
    print("\nAvailable Models:")
    
    for model_name in __all__:
        print(f"  - {model_name}")
    
    print("\nUsage Example:")
    print("""
    from walters.core.models import TeamRating, BetRecommendation
    
    # Create a team rating
    chiefs = TeamRating(
        team="Kansas City Chiefs",
        sport="nfl",
        rating=11.5,
        games_played=9
    )
    
    print(f"Team: {chiefs.team}")
    print(f"Rating: {chiefs.rating}")
    print(chiefs.to_dict())
    """)
    
    # Demo creating a model
    print("\nDemo - Creating TeamRating:")
    chiefs = TeamRating(
        team="Kansas City Chiefs",
        sport="nfl",
        rating=11.5,
        games_played=9
    )
    print(f"  Team: {chiefs.team}")
    print(f"  Rating: {chiefs.rating}")
    print(f"  JSON: {chiefs.to_dict()}")
    
    print("\n" + "=" * 50)
    print("All models consolidated in one place!")

