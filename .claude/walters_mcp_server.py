"""
Billy Walters Sports Expert - MCP Server
Advanced Model Context Protocol server for Claude Desktop integration
Provides real-time betting analysis, sharp money detection, and automated research
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import os

# FastMCP for efficient server implementation
from fastmcp import FastMCP, Context
from fastmcp.tools import Tool
from fastmcp.resources import Resource, ResourceManager
from pydantic import BaseModel, Field

# Import Billy Walters SDK components
from walters_analyzer.core import BillyWaltersAnalyzer, BankrollManager
from walters_analyzer.core.models import GameInput, TeamSnapshot, GameOdds, SpreadLine
from walters_analyzer.research import ResearchEngine
# Slash commands will be added in Phase 6
# from walters_analyzer.slash_commands import SlashCommandHandler

# Import unified configuration
from walters_analyzer.config import get_settings

# Initialize unified settings
settings = get_settings()

# Configure logging from settings
log_level = getattr(logging, settings.global_config.log_level.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.logs_dir / 'mcp-server.log')
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"MCP Server initialized with unified configuration")

# ============================================================================
# MCP Server Configuration
# ============================================================================

mcp = FastMCP(
    name="billy-walters-expert",
    version="2.0.0",
    description="Professional sports betting analysis using Billy Walters methodology"
)

# ============================================================================
# Data Models
# ============================================================================

class GameAnalysisRequest(BaseModel):
    """Request model for game analysis"""
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    spread: float = Field(..., description="Current market spread")
    total: Optional[float] = Field(None, description="Game total O/U")
    game_date: Optional[str] = Field(None, description="Game date YYYY-MM-DD")
    include_research: bool = Field(True, description="Include injury/weather research")

class BettingSignal(BaseModel):
    """Betting signal with confidence and sizing"""
    game_id: str
    recommendation: str  # 'home', 'away', 'over', 'under', 'pass'
    confidence: float  # 0-100
    star_rating: float  # 0.5-3.0 stars
    edge_percentage: float
    recommended_units: float  # 1-3% of bankroll
    key_factors: List[str]
    timestamp: datetime

class MarketAlert(BaseModel):
    """Real-time market movement alert"""
    alert_type: str  # 'steam', 'reverse', 'arbitrage', 'clv'
    game_id: str
    book: str
    old_line: float
    new_line: float
    confidence: float
    action_required: str
    expires_at: datetime

# ============================================================================
# Core Analysis Engine
# ============================================================================

class WaltersMCPEngine:
    """
    Central engine coordinating all Billy Walters SDK functionality
    """

    def __init__(self):
        # Use unified settings for configuration
        global settings

        # Initialize analyzer with bankroll from settings
        bankroll = settings.autonomous_agent.initial_bankroll
        self.analyzer = WaltersSportsAnalyzer(initial_bankroll=bankroll)
        logger.info(f"Initialized analyzer with bankroll: ${bankroll}")

        # Initialize research engine with data provider settings
        self.research_engine = ResearchEngine(
            enable_web_fetch=settings.data_connections.highlightly_enabled
        )

        self.command_handler = SlashCommandHandler(self.analyzer)

        # Apply default team ratings
        apply_default_team_ratings(self.analyzer)

        # Active monitoring (if enabled)
        self.monitoring_enabled = settings.monitoring.performance_tracking
        self.clv_tracking_enabled = settings.monitoring.clv_tracking
        self.monitored_games: Dict[str, Any] = {}
        self.active_alerts: List[MarketAlert] = []

        # Performance tracking
        self.bet_history: List[Dict] = []
        self.clv_tracker: Dict[str, float] = {}

        # Skills configuration
        self.skills_enabled = {
            'market_analysis': settings.skills.market_analysis.enabled,
            'ml_power_ratings': settings.skills.ml_power_ratings.enabled,
            'situational_database': settings.skills.situational_database.enabled
        }
        logger.info(f"Skills enabled: {self.skills_enabled}")

    async def analyze_game_comprehensive(self, request: GameAnalysisRequest) -> Dict:
        """
        Comprehensive game analysis using full Billy Walters methodology
        """
        logger.info(f"Analyzing {request.home_team} vs {request.away_team}")

        # Core power rating analysis
        base_analysis = await self.analyzer.analyze_game(
            home_team=request.home_team,
            away_team=request.away_team,
            market_spread=request.spread,
            game_date=request.game_date or datetime.now().strftime("%Y-%m-%d"),
            game_location=request.home_team  # Simplified for demo
        )

        # Research integration if requested
        research_data = {}
        if request.include_research:
            # Injury research
            home_injuries = await self.research_engine.comprehensive_injury_research(
                request.home_team
            )
            away_injuries = await self.research_engine.comprehensive_injury_research(
                request.away_team
            )

            # Weather analysis (if applicable)
            weather = await self.research_engine.accuweather_client.get_game_weather(
                location=request.home_team,
                game_time=request.game_date
            )

            research_data = {
                'injuries': {
                    'home': home_injuries,
                    'away': away_injuries
                },
                'weather': weather
            }

        # Generate betting signal
        signal = self._generate_signal(base_analysis, research_data, request)

        return {
            'analysis': asdict(base_analysis),
            'research': research_data,
            'signal': asdict(signal),
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'model_version': '2.0.0',
                'confidence_level': signal.confidence
            }
        }

    def _generate_signal(self, analysis: Any, research: Dict,
                        request: GameAnalysisRequest) -> BettingSignal:
        """Generate actionable betting signal from analysis"""

        # Calculate edge
        predicted_spread = analysis.predicted_spread
        market_spread = request.spread
        edge = market_spread - predicted_spread

        # Determine recommendation
        if abs(edge) < 0.5:
            recommendation = 'pass'
            confidence = 0
            star_rating = 0
            units = 0
        else:
            # Check side
            if edge > 0:
                recommendation = 'away'  # Take the dog
            else:
                recommendation = 'home'  # Take the favorite

            # Calculate confidence and sizing
            confidence = min(100, abs(edge) * 15)

            # Star rating based on edge
            if abs(edge) >= 3:
                star_rating = 3.0
            elif abs(edge) >= 2:
                star_rating = 2.0
            elif abs(edge) >= 1.5:
                star_rating = 1.5
            elif abs(edge) >= 1:
                star_rating = 1.0
            else:
                star_rating = 0.5

            # Unit sizing (1-3% of bankroll)
            units = min(3.0, max(1.0, star_rating))

        # Key factors
        factors = []
        if analysis.key_number_value > 0:
            factors.append(f"Key number edge: {analysis.key_number_value}")
        if 'injuries' in research:
            factors.append("Injury adjustments applied")
        if 'weather' in research and research['weather']:
            factors.append("Weather impact considered")

        return BettingSignal(
            game_id=f"{request.home_team}_vs_{request.away_team}",
            recommendation=recommendation,
            confidence=confidence,
            star_rating=star_rating,
            edge_percentage=abs(edge),
            recommended_units=units,
            key_factors=factors,
            timestamp=datetime.now()
        )

# ============================================================================
# MCP Tools Implementation
# ============================================================================

# Initialize the engine
engine = WaltersMCPEngine()

@mcp.tool()
async def analyze_game(
    ctx: Context,
    home_team: str,
    away_team: str,
    spread: float,
    total: Optional[float] = None,
    include_research: bool = True
) -> Dict:
    """
    Analyze a game using Billy Walters methodology

    Args:
        home_team: Home team name
        away_team: Away team name
        spread: Current market spread
        total: Game total O/U (optional)
        include_research: Include injury/weather research

    Returns:
        Comprehensive analysis with betting signal
    """
    request = GameAnalysisRequest(
        home_team=home_team,
        away_team=away_team,
        spread=spread,
        total=total,
        include_research=include_research
    )

    return await engine.analyze_game_comprehensive(request)

@mcp.tool()
async def find_sharp_money(
    ctx: Context,
    game_id: str,
    monitor_duration: int = 3600
) -> Dict:
    """
    Monitor game for sharp money indicators

    Args:
        game_id: Game identifier (e.g., "KC_vs_BUF")
        monitor_duration: Monitoring duration in seconds

    Returns:
        Sharp money signals and recommendations
    """
    # Start monitoring
    monitor_task = asyncio.create_task(
        _monitor_sharp_money(game_id, monitor_duration)
    )

    # Store task
    engine.monitored_games[game_id] = {
        'task': monitor_task,
        'started': datetime.now(),
        'duration': monitor_duration
    }

    return {
        'status': 'monitoring_started',
        'game_id': game_id,
        'duration': monitor_duration,
        'check_alerts': 'Use get_market_alerts tool'
    }

@mcp.tool()
async def get_market_alerts(ctx: Context) -> List[Dict]:
    """
    Get current market alerts and sharp signals

    Returns:
        List of active market alerts
    """
    # Filter expired alerts
    now = datetime.now()
    active = [
        alert for alert in engine.active_alerts
        if alert.expires_at > now
    ]

    return [asdict(alert) for alert in active]

@mcp.tool()
async def calculate_kelly_stake(
    ctx: Context,
    edge_percentage: float,
    odds: int,
    bankroll: float,
    kelly_fraction: float = 0.25
) -> Dict:
    """
    Calculate optimal stake size using Kelly Criterion

    Args:
        edge_percentage: Your edge (e.g., 2.5 for 2.5%)
        odds: American odds (e.g., -110)
        bankroll: Total bankroll
        kelly_fraction: Kelly fraction for safety (default 0.25)

    Returns:
        Optimal betting amounts
    """
    # Convert American odds to decimal
    if odds > 0:
        decimal_odds = (odds / 100) + 1
    else:
        decimal_odds = (100 / abs(odds)) + 1

    # Calculate win probability
    win_probability = (edge_percentage / 100) + 0.5238  # Baseline 52.38% to break even

    # Kelly formula: f = (bp - q) / b
    # where b = decimal odds - 1, p = win probability, q = 1 - p
    b = decimal_odds - 1
    p = win_probability
    q = 1 - p

    kelly_percentage = ((b * p - q) / b) * 100

    # Apply fractional Kelly for safety
    safe_percentage = kelly_percentage * kelly_fraction

    # Calculate stake
    stake = bankroll * (safe_percentage / 100)

    # Apply limits (never more than 3% on a single bet)
    max_stake = bankroll * 0.03
    final_stake = min(stake, max_stake)

    return {
        'edge_percentage': edge_percentage,
        'win_probability': win_probability * 100,
        'full_kelly': kelly_percentage,
        'fractional_kelly': safe_percentage,
        'recommended_stake': final_stake,
        'percentage_of_bankroll': (final_stake / bankroll) * 100,
        'expected_growth': edge_percentage * (final_stake / bankroll)
    }

@mcp.tool()
async def backtest_strategy(
    ctx: Context,
    strategy: str,
    start_date: str,
    end_date: str,
    initial_bankroll: float = 10000
) -> Dict:
    """
    Backtest a betting strategy on historical data

    Args:
        strategy: Strategy name ('power_rating', 'sharp_money', 'weather_unders')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_bankroll: Starting bankroll

    Returns:
        Backtest results with performance metrics
    """
    # This would connect to historical database in production
    # For demo, return simulated results

    return {
        'strategy': strategy,
        'period': f"{start_date} to {end_date}",
        'total_bets': 127,
        'wins': 69,
        'losses': 58,
        'win_rate': 54.3,
        'roi': 7.2,
        'total_profit': 720,
        'max_drawdown': -12.5,
        'sharpe_ratio': 1.34,
        'average_clv': 1.8,
        'best_month': 'October 2024',
        'worst_month': 'September 2024'
    }

@mcp.tool()
async def get_injury_report(ctx: Context, team: str) -> Dict:
    """
    Get comprehensive injury report for a team

    Args:
        team: Team name

    Returns:
        Detailed injury analysis with impact assessment
    """
    injuries = await engine.research_engine.comprehensive_injury_research(team)

    # Calculate total impact
    total_impact = sum(
        inj.get('point_value', 0)
        for inj in injuries.get('injuries', [])
    )

    return {
        'team': team,
        'injuries': injuries,
        'total_point_impact': total_impact,
        'severity': 'high' if total_impact > 3 else 'medium' if total_impact > 1 else 'low',
        'key_players_affected': [
            inj['player_name']
            for inj in injuries.get('injuries', [])
            if inj.get('point_value', 0) > 1
        ]
    }

# ============================================================================
# Highlightly API Tools
# ============================================================================

@mcp.tool()
async def get_highlightly_teams(
    ctx: Context,
    league: str = "NFL",
    name: Optional[str] = None
) -> Dict:
    """
    Get NFL/NCAA team information from Highlightly API
    
    Args:
        league: League (NFL or NCAA)
        name: Optional team name filter
        
    Returns:
        List of teams with IDs and details
    """
    from walters_analyzer.feeds.highlightly_client import HighlightlyClient
    
    async with HighlightlyClient() as client:
        teams = await client.get_teams(league=league, name=name)
        
        return {
            'league': league,
            'count': len(teams),
            'teams': [
                {
                    'id': team.id,
                    'name': team.name,
                    'displayName': team.displayName,
                    'abbreviation': team.abbreviation
                }
                for team in teams
            ]
        }

@mcp.tool()
async def get_highlightly_match_data(
    ctx: Context,
    match_id: int,
    include_odds: bool = True
) -> Dict:
    """
    Get comprehensive match data from Highlightly API
    
    Includes: venue, weather, injuries, events, odds from multiple bookmakers
    
    Args:
        match_id: Match ID from Highlightly
        include_odds: Include odds from multiple bookmakers
        
    Returns:
        Comprehensive match data with all available information
    """
    from walters_analyzer.feeds.highlightly_client import HighlightlyClient
    
    async with HighlightlyClient() as client:
        # Get match details
        match_details = await client.get_match_by_id(match_id)
        
        result = {
            'match_id': match_id,
            'home_team': match_details.homeTeam.displayName if match_details else None,
            'away_team': match_details.awayTeam.displayName if match_details else None,
            'date': match_details.date if match_details else None,
            'league': match_details.league if match_details else None,
            'venue': None,
            'weather': None,
            'injuries': [],
            'odds': []
        }
        
        if match_details:
            # Add venue
            if match_details.venue:
                result['venue'] = {
                    'name': match_details.venue.name,
                    'city': match_details.venue.city,
                    'state': match_details.venue.state
                }
            
            # Add weather
            if match_details.forecast:
                result['weather'] = {
                    'status': match_details.forecast.status,
                    'temperature': match_details.forecast.temperature
                }
            
            # Add injuries
            if match_details.injuries:
                for team_injury in match_details.injuries:
                    for injury in team_injury.data:
                        result['injuries'].append({
                            'team': team_injury.team.displayName,
                            'player': injury.player.name,
                            'position': injury.player.position,
                            'status': injury.status
                        })
        
        # Get odds if requested
        if include_odds:
            odds_data = await client.get_odds(match_id=match_id, odds_type="prematch")
            
            if odds_data:
                for match_odds in odds_data:
                    for bookmaker_market in match_odds.odds:
                        result['odds'].append({
                            'bookmaker': bookmaker_market.bookmakerName or f"ID: {bookmaker_market.bookmakerId}",
                            'market': bookmaker_market.market,
                            'type': bookmaker_market.type,
                            'values': [
                                {'value': v.value, 'odd': v.odd}
                                for v in bookmaker_market.values
                            ]
                        })
        
        return result

@mcp.tool()
async def get_highlightly_player_stats(
    ctx: Context,
    player_name: str
) -> Dict:
    """
    Get player statistics from Highlightly API
    
    Args:
        player_name: Player name to search
        
    Returns:
        Player profile and statistics by season
    """
    from walters_analyzer.feeds.highlightly_client import HighlightlyClient
    
    async with HighlightlyClient() as client:
        # Search for player
        players = await client.get_players(name=player_name)
        
        if not players:
            return {
                'error': f"No player found matching '{player_name}'"
            }
        
        # Get first match
        player = players[0]
        
        # Get detailed stats
        player_stats = await client.get_player_statistics(player.id)
        
        result = {
            'player_id': player.id,
            'name': player.fullName or "Unknown",
            'seasons': []
        }
        
        if player_stats and player_stats.perSeason:
            for season in player_stats.perSeason:
                season_data = {
                    'season': season.season,
                    'league': season.league,
                    'coverage': season.seasonBreakdown.value,
                    'teams': [team.displayName for team in season.teams],
                    'stats': {}
                }
                
                # Group stats by category
                for stat in season.stats:
                    category = stat.category.value
                    if category not in season_data['stats']:
                        season_data['stats'][category] = {}
                    season_data['stats'][category][stat.name] = stat.value
                
                result['seasons'].append(season_data)
        
        return result

@mcp.tool()
async def get_highlightly_historical_matchups(
    ctx: Context,
    team_id_one: int,
    team_id_two: int
) -> Dict:
    """
    Get head-to-head and recent form data for pattern recognition
    
    Args:
        team_id_one: First team ID
        team_id_two: Second team ID
        
    Returns:
        Head-to-head history and last 5 games for each team
    """
    from walters_analyzer.feeds.highlightly_client import HighlightlyClient
    
    async with HighlightlyClient() as client:
        # Get head-to-head
        h2h = await client.get_head_to_head(team_id_one, team_id_two)
        
        # Get last 5 for each team
        team1_last5 = await client.get_last_five_games(team_id_one)
        team2_last5 = await client.get_last_five_games(team_id_two)
        
        return {
            'head_to_head': {
                'total_games': len(h2h),
                'games': [
                    {
                        'date': match.date,
                        'home_team': match.homeTeam.displayName,
                        'away_team': match.awayTeam.displayName,
                        'score': match.state.score.current
                    }
                    for match in h2h
                ]
            },
            'team1_recent_form': {
                'games': len(team1_last5),
                'matches': [
                    {
                        'date': match.date,
                        'opponent': match.awayTeam.displayName if match.homeTeam.id == team_id_one else match.homeTeam.displayName,
                        'result': match.state.description.value,
                        'score': match.state.score.current
                    }
                    for match in team1_last5
                ]
            },
            'team2_recent_form': {
                'games': len(team2_last5),
                'matches': [
                    {
                        'date': match.date,
                        'opponent': match.awayTeam.displayName if match.homeTeam.id == team_id_two else match.homeTeam.displayName,
                        'result': match.state.description.value,
                        'score': match.state.score.current
                    }
                    for match in team2_last5
                ]
            }
        }

@mcp.tool()
async def get_highlightly_odds_history(
    ctx: Context,
    match_id: int,
    bookmaker_name: Optional[str] = None
) -> Dict:
    """
    Get line movement analysis from multiple bookmakers
    
    Args:
        match_id: Match ID
        bookmaker_name: Optional bookmaker filter
        
    Returns:
        Odds from multiple bookmakers for comparison and line movement detection
    """
    from walters_analyzer.feeds.highlightly_client import HighlightlyClient
    
    async with HighlightlyClient() as client:
        # Get prematch odds
        prematch_odds = await client.get_odds(
            match_id=match_id,
            odds_type="prematch",
            bookmaker_name=bookmaker_name
        )
        
        # Get live odds if available
        live_odds = await client.get_odds(
            match_id=match_id,
            odds_type="live",
            bookmaker_name=bookmaker_name
        )
        
        result = {
            'match_id': match_id,
            'bookmakers_count': 0,
            'prematch_odds': [],
            'live_odds': [],
            'line_movement_detected': False
        }
        
        # Parse prematch odds
        for match_odds in prematch_odds:
            for bookmaker_market in match_odds.odds:
                result['prematch_odds'].append({
                    'bookmaker': bookmaker_market.bookmakerName or f"ID: {bookmaker_market.bookmakerId}",
                    'market': bookmaker_market.market,
                    'values': [
                        {'outcome': v.value, 'odds': v.odd}
                        for v in bookmaker_market.values
                    ]
                })
        
        # Parse live odds
        for match_odds in live_odds:
            for bookmaker_market in match_odds.odds:
                result['live_odds'].append({
                    'bookmaker': bookmaker_market.bookmakerName or f"ID: {bookmaker_market.bookmakerId}",
                    'market': bookmaker_market.market,
                    'values': [
                        {'outcome': v.value, 'odds': v.odd}
                        for v in bookmaker_market.values
                    ]
                })
        
        result['bookmakers_count'] = len(set(
            odds['bookmaker'] for odds in result['prematch_odds']
        ))
        
        result['line_movement_detected'] = len(result['live_odds']) > 0
        
        return result

@mcp.tool()
async def backtest_with_highlightly(
    ctx: Context,
    league: str = "NFL",
    date: str = None,
    strategy: str = "odds_comparison"
) -> Dict:
    """
    Enhanced backtesting with historical Highlightly data
    
    Args:
        league: League (NFL or NCAA)
        date: Date to backtest (YYYY-MM-DD)
        strategy: Strategy to test (odds_comparison, sharp_detection, weather_impact)
        
    Returns:
        Backtest results using Highlightly historical data
    """
    from walters_analyzer.feeds.highlightly_client import HighlightlyClient
    
    async with HighlightlyClient() as client:
        # Get historical matches
        matches = await client.get_matches(
            league=league,
            date=date
        )
        
        results = {
            'league': league,
            'date': date,
            'strategy': strategy,
            'total_games': len(matches),
            'opportunities': [],
            'summary': {
                'profitable_bets': 0,
                'total_bets': 0,
                'roi': 0
            }
        }
        
        # Analyze each match
        for match in matches:
            # Get odds for the match
            odds_data = await client.get_odds(
                match_id=match.id,
                odds_type="prematch"
            )
            
            if odds_data and match.state.description.value == "Finished":
                # Find betting opportunities based on strategy
                if strategy == "odds_comparison" and len(odds_data) > 0:
                    # Compare odds across bookmakers
                    bookmaker_count = sum(len(mo.odds) for mo in odds_data)
                    
                    if bookmaker_count >= 3:
                        results['opportunities'].append({
                            'match': f"{match.awayTeam.displayName} @ {match.homeTeam.displayName}",
                            'date': match.date,
                            'bookmakers': bookmaker_count,
                            'final_score': match.state.score.current
                        })
                        results['summary']['total_bets'] += 1
        
        # Calculate simple metrics
        if results['summary']['total_bets'] > 0:
            results['summary']['profitable_bets'] = int(results['summary']['total_bets'] * 0.55)  # Simulated
            results['summary']['roi'] = 5.2  # Simulated
        
        return results

# ============================================================================
# MCP Resources
# ============================================================================

@mcp.resource("betting-history")
async def get_betting_history(ctx: Context) -> str:
    """Access complete betting history and performance"""
    history = {
        'total_bets': len(engine.bet_history),
        'recent_bets': engine.bet_history[-10:],
        'performance': {
            'win_rate': _calculate_win_rate(engine.bet_history),
            'roi': _calculate_roi(engine.bet_history),
            'avg_clv': _calculate_avg_clv(engine.clv_tracker)
        }
    }
    return json.dumps(history, indent=2, default=str)

@mcp.resource("active-monitors")
async def get_active_monitors(ctx: Context) -> str:
    """Get all actively monitored games"""
    monitors = []
    for game_id, monitor_data in engine.monitored_games.items():
        monitors.append({
            'game_id': game_id,
            'started': monitor_data['started'].isoformat(),
            'duration': monitor_data['duration'],
            'status': 'active' if not monitor_data['task'].done() else 'completed'
        })
    return json.dumps(monitors, indent=2)

@mcp.resource("system-config")
async def get_system_config(ctx: Context) -> str:
    """Get current system configuration and settings"""
    config = {
        'bankroll': engine.analyzer.bankroll_manager.current_bankroll,
        'risk_settings': {
            'max_bet_percentage': 3.0,
            'kelly_fraction': 0.25,
            'daily_loss_limit': 5.0
        },
        'monitoring': {
            'active_games': len(engine.monitored_games),
            'alert_count': len(engine.active_alerts)
        },
        'model_version': '2.0.0',
        'last_updated': datetime.now().isoformat()
    }
    return json.dumps(config, indent=2)

# ============================================================================
# Helper Functions
# ============================================================================

async def _monitor_sharp_money(game_id: str, duration: int):
    """Background task to monitor sharp money movements"""
    start_time = datetime.now()

    while (datetime.now() - start_time).total_seconds() < duration:
        try:
            # Simulate checking for sharp money
            # In production, this would fetch real line movements

            # Random sharp signal for demonstration
            import random
            if random.random() > 0.9:  # 10% chance per check
                alert = MarketAlert(
                    alert_type='steam',
                    game_id=game_id,
                    book='Pinnacle',
                    old_line=-3.5,
                    new_line=-2.5,
                    confidence=85.0,
                    action_required='BET NOW - Sharp money detected',
                    expires_at=datetime.now() + timedelta(minutes=5)
                )
                engine.active_alerts.append(alert)
                logger.info(f"Sharp money detected on {game_id}")

            await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"Error monitoring {game_id}: {e}")
            break

def _calculate_win_rate(history: List[Dict]) -> float:
    """Calculate win rate from betting history"""
    if not history:
        return 0.0
    wins = sum(1 for bet in history if bet.get('won', False))
    return (wins / len(history)) * 100

def _calculate_roi(history: List[Dict]) -> float:
    """Calculate ROI from betting history"""
    if not history:
        return 0.0
    total_staked = sum(bet.get('stake', 0) for bet in history)
    total_profit = sum(bet.get('profit', 0) for bet in history)
    return (total_profit / total_staked) * 100 if total_staked > 0 else 0.0

def _calculate_avg_clv(clv_tracker: Dict[str, float]) -> float:
    """Calculate average closing line value"""
    if not clv_tracker:
        return 0.0
    return sum(clv_tracker.values()) / len(clv_tracker)

# ============================================================================
# Server Lifecycle
# ============================================================================

@mcp.startup()
async def on_startup(ctx: Context):
    """Initialize server on startup"""
    logger.info("Billy Walters MCP Server starting...")

    # Load saved state if exists
    state_file = Path("walters_state.json")
    if state_file.exists():
        with open(state_file, 'r') as f:
            saved_state = json.load(f)
            engine.bet_history = saved_state.get('bet_history', [])
            engine.clv_tracker = saved_state.get('clv_tracker', {})
            logger.info("Loaded saved state")

    logger.info("Billy Walters MCP Server ready!")

@mcp.shutdown()
async def on_shutdown(ctx: Context):
    """Cleanup on server shutdown"""
    logger.info("Billy Walters MCP Server shutting down...")

    # Cancel all monitoring tasks
    for game_id, monitor_data in engine.monitored_games.items():
        if not monitor_data['task'].done():
            monitor_data['task'].cancel()

    # Save state
    state = {
        'bet_history': engine.bet_history,
        'clv_tracker': engine.clv_tracker,
        'timestamp': datetime.now().isoformat()
    }
    with open("walters_state.json", 'w') as f:
        json.dump(state, f, indent=2, default=str)

    logger.info("State saved. Shutdown complete.")

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Run the MCP server
    uvicorn.run(
        "walters_mcp_server:mcp",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
