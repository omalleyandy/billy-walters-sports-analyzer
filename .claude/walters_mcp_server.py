"""
Billy Walters Sports Expert - MCP Server (FIXED VERSION)
Advanced Model Context Protocol server for Claude Desktop integration
Provides real-time betting analysis, sharp money detection, and automated research
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from pathlib import Path

# ============================================================================
# CRITICAL: Setup logging FIRST before any imports
# MCP servers MUST NOT write to stdout (breaks JSON-RPC protocol)
# All diagnostic output goes to stderr and file only
# ============================================================================

# Create logs directory if needed
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure logging BEFORE imports (so errors go to stderr, not stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),  # Use stderr, NOT stdout
        logging.FileHandler(logs_dir / "mcp-server.log"),
    ],
)
logger = logging.getLogger(__name__)

# Add src to path if needed
project_root = Path(__file__).parent
if (project_root / "src").exists():
    sys.path.insert(0, str(project_root / "src"))

# FastMCP for efficient server implementation
try:
    from fastmcp import FastMCP, Context
    from pydantic import BaseModel, Field
except ImportError as e:
    logger.error(f"Missing required dependency: {e}")
    logger.error("Install with: uv pip install 'walters-analyzer[mcp]'")
    sys.exit(1)

# Import Billy Walters SDK components - with proper error handling
try:
    from walters_analyzer.core.analyzer import BillyWaltersAnalyzer
    from walters_analyzer.core.config import AnalyzerConfig
    from walters_analyzer.core.models import GameInput, TeamSnapshot, GameOdds
    from walters_analyzer.research.engine import ResearchEngine
    from walters_analyzer.config import get_settings
except ImportError as e:
    logger.error(f"Could not import walters_analyzer modules: {e}")
    logger.error("Make sure the package is installed: uv pip install -e .")
    sys.exit(1)

# Initialize unified settings
try:
    settings = get_settings()
    # Update logging level from settings if available
    if hasattr(settings, "global_config"):
        log_level = getattr(
            logging, settings.global_config.log_level.upper(), logging.INFO
        )
        logging.getLogger().setLevel(log_level)
        logger.info(f"Log level set to {settings.global_config.log_level}")
except Exception as e:
    logger.warning(f"Could not load advanced settings, using defaults: {e}")
    settings = None

logger.info("MCP Server logging configured - all output to stderr/file only")

# ============================================================================
# MCP Server Configuration
# ============================================================================

mcp = FastMCP(
    name="billy-walters-expert",
    version="2.0.1",  # Updated version with fixes
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

        # Initialize analyzer with config
        try:
            analyzer_config = AnalyzerConfig.from_settings()
            self.analyzer = BillyWaltersAnalyzer(config=analyzer_config)
            logger.info(
                f"Initialized analyzer with bankroll: ${analyzer_config.bankroll}"
            )
        except Exception as e:
            logger.error(f"Error initializing analyzer: {e}")
            # Use default values
            self.analyzer = BillyWaltersAnalyzer()

        # Initialize research engine (parameter configuration may vary by version)
        try:
            # Try to initialize with no arguments first
            self.research_engine = ResearchEngine()
        except Exception as e:
            logger.warning(f"Could not initialize research engine: {e}")
            self.research_engine = None

        # Active monitoring (if enabled)
        self.monitoring_enabled = (
            settings.monitoring.performance_tracking if settings else False
        )
        self.clv_tracking_enabled = (
            settings.monitoring.clv_tracking if settings else False
        )
        self.monitored_games: Dict[str, Any] = {}
        self.active_alerts: List[MarketAlert] = []

        # Performance tracking
        self.bet_history: List[Dict] = []
        self.clv_tracker: Dict[str, float] = {}

        # Skills configuration
        if settings:
            self.skills_enabled = {
                "market_analysis": settings.skills.market_analysis.enabled,
                "ml_power_ratings": settings.skills.ml_power_ratings.enabled,
                "situational_database": settings.skills.situational_database.enabled,
            }
            logger.info(f"Skills enabled: {self.skills_enabled}")
        else:
            self.skills_enabled = {}

    async def analyze_game_comprehensive(self, request: GameAnalysisRequest) -> Dict:
        """
        Comprehensive game analysis using full Billy Walters methodology
        """
        logger.info(f"Analyzing {request.home_team} vs {request.away_team}")

        try:
            # Build game input
            home_team = TeamSnapshot(
                name=request.home_team,
                injuries=[],  # Will be populated by research if enabled
            )
            away_team = TeamSnapshot(name=request.away_team, injuries=[])

            odds = GameOdds(
                spread=type(
                    "Spread",
                    (),
                    {
                        "home_spread": request.spread,
                        "home_price": -110,
                        "away_price": -110,
                    },
                )(),
                total=None
                if not request.total
                else type(
                    "Total",
                    (),
                    {"over": request.total, "over_price": -110, "under_price": -110},
                )(),
            )

            matchup = GameInput(
                home_team=home_team,
                away_team=away_team,
                odds=odds,
                game_date=request.game_date or datetime.now().strftime("%Y-%m-%d"),
            )

            # Core power rating analysis
            base_analysis = self.analyzer.analyze(matchup)

            # Research integration if requested
            research_data = {}
            if request.include_research and self.research_engine:
                try:
                    # Injury research
                    home_injuries = (
                        await self.research_engine.comprehensive_injury_research(
                            request.home_team
                        )
                    )
                    away_injuries = (
                        await self.research_engine.comprehensive_injury_research(
                            request.away_team
                        )
                    )

                    research_data = {
                        "injuries": {"home": home_injuries, "away": away_injuries},
                    }
                except Exception as e:
                    logger.warning(f"Error fetching research data: {e}")
                    research_data = {"error": str(e)}

            # Generate betting signal
            signal = self._generate_signal(base_analysis, research_data, request)

            return {
                "analysis": {
                    "predicted_spread": base_analysis.predicted_spread,
                    "market_spread": base_analysis.market_spread,
                    "edge": base_analysis.edge,
                    "confidence": base_analysis.confidence,
                    "injury_advantage": base_analysis.injury_advantage,
                },
                "research": research_data,
                "signal": asdict(signal),
                "metadata": {
                    "analyzed_at": datetime.now().isoformat(),
                    "model_version": "2.0.1",
                    "confidence_level": signal.confidence,
                },
            }
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {
                "error": str(e),
                "analysis": None,
                "research": {},
                "signal": None,
            }

    def _generate_signal(
        self, analysis: Any, research: Dict, request: GameAnalysisRequest
    ) -> BettingSignal:
        """Generate actionable betting signal from analysis"""

        # Calculate edge
        predicted_spread = analysis.predicted_spread
        market_spread = request.spread
        edge = market_spread - predicted_spread

        # Determine recommendation
        if abs(edge) < 0.5:
            recommendation = "pass"
            confidence = 0
            star_rating = 0
            units = 0
        else:
            # Check side
            if edge > 0:
                recommendation = "away"  # Take the dog
            else:
                recommendation = "home"  # Take the favorite

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
        if hasattr(analysis, "key_number_alerts") and analysis.key_number_alerts:
            factors.append(f"Key number alerts: {len(analysis.key_number_alerts)}")
        if "injuries" in research:
            factors.append("Injury adjustments applied")

        return BettingSignal(
            game_id=f"{request.home_team}_vs_{request.away_team}",
            recommendation=recommendation,
            confidence=confidence,
            star_rating=star_rating,
            edge_percentage=abs(edge),
            recommended_units=units,
            key_factors=factors,
            timestamp=datetime.now(),
        )


# ============================================================================
# MCP Tools Implementation
# ============================================================================

# Initialize the engine
try:
    engine = WaltersMCPEngine()
    logger.info("Engine initialized successfully")
except Exception as e:
    logger.error(f"FATAL: Could not initialize engine: {e}")
    sys.exit(1)


@mcp.tool()
async def analyze_game(
    ctx: Context,
    home_team: str,
    away_team: str,
    spread: float,
    total: Optional[float] = None,
    include_research: bool = True,
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
    try:
        request = GameAnalysisRequest(
            home_team=home_team,
            away_team=away_team,
            spread=spread,
            total=total,
            include_research=include_research,
        )

        return await engine.analyze_game_comprehensive(request)
    except Exception as e:
        logger.error(f"Error in analyze_game tool: {e}")
        return {"error": str(e)}


@mcp.tool()
async def calculate_kelly_stake(
    ctx: Context,
    edge_percentage: float,
    odds: int,
    bankroll: float,
    kelly_fraction: float = 0.25,
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
    try:
        # Convert American odds to decimal
        if odds > 0:
            decimal_odds = (odds / 100) + 1
        else:
            decimal_odds = (100 / abs(odds)) + 1

        # Calculate win probability
        win_probability = (
            edge_percentage / 100
        ) + 0.5238  # Baseline 52.38% to break even

        # Kelly formula: f = (bp - q) / b
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
            "edge_percentage": edge_percentage,
            "win_probability": win_probability * 100,
            "full_kelly": kelly_percentage,
            "fractional_kelly": safe_percentage,
            "recommended_stake": final_stake,
            "percentage_of_bankroll": (final_stake / bankroll) * 100,
            "expected_growth": edge_percentage * (final_stake / bankroll),
        }
    except Exception as e:
        logger.error(f"Error in calculate_kelly_stake: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_injury_report(ctx: Context, team: str) -> Dict:
    """
    Get comprehensive injury report for a team

    Args:
        team: Team name

    Returns:
        Detailed injury analysis with impact assessment
    """
    try:
        if not engine.research_engine:
            return {"error": "Research engine not available"}

        injuries = await engine.research_engine.comprehensive_injury_research(team)

        # Calculate total impact
        total_impact = sum(
            inj.get("point_value", 0) for inj in injuries.get("injuries", [])
        )

        return {
            "team": team,
            "injuries": injuries,
            "total_point_impact": total_impact,
            "severity": "high"
            if total_impact > 3
            else "medium"
            if total_impact > 1
            else "low",
            "key_players_affected": [
                inj["player_name"]
                for inj in injuries.get("injuries", [])
                if inj.get("point_value", 0) > 1
            ],
        }
    except Exception as e:
        logger.error(f"Error in get_injury_report: {e}")
        return {"error": str(e)}


# ============================================================================
# NFL Game Stats Tool
# ============================================================================


@mcp.tool()
async def get_nfl_game_stats(
    year: int = 2025,
    week: str = "reg-12",
    headless: bool = True,
) -> dict:
    """
    Fetch NFL game statistics from NFL.com for a specific week.

    Navigates NFL.com schedule pages, extracts game links, and scrapes
    detailed team stats from the STATS tab for each matchup.

    Args:
        year: NFL season year (default: 2025)
        week: Week identifier (reg-12, reg-13, post-1, etc.)
        headless: Run browser in headless mode (default: True)

    Returns:
        Dictionary with all games and team statistics for the week

    Example:
        stats = await get_nfl_game_stats(year=2025, week="reg-12")
    """
    try:
        logger.info(f"Fetching NFL game stats for {year} week {week}")

        # Import client
        try:
            from data.nfl_game_stats_client import NFLGameStatsClient
        except ImportError:
            # Try alternate import path
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent
            if (project_root / "src").exists():
                sys.path.insert(0, str(project_root / "src"))

            from data.nfl_game_stats_client import NFLGameStatsClient

        # Fetch stats
        client = NFLGameStatsClient(headless=headless)

        try:
            await client.connect()
            stats = await client.get_week_stats(year=year, week=week)

            return {
                "success": True,
                "year": year,
                "week": week,
                "games_count": len(stats.get("games", [])),
                "games": stats.get("games", []),
                "timestamp": stats.get("timestamp"),
            }

        finally:
            await client.close()

    except Exception as e:
        logger.error(f"Error fetching NFL game stats: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "year": year,
            "week": week,
        }


@mcp.tool()
async def get_nfl_game_stats_for_matchup(
    game_url: str,
    headless: bool = True,
) -> dict:
    """
    Fetch statistics for a specific NFL game.

    Args:
        game_url: Full URL to NFL.com game page
                  (e.g., https://www.nfl.com/games/bills-at-texans-2025-reg-12)
        headless: Run browser in headless mode (default: True)

    Returns:
        Dictionary with game info and team statistics

    Example:
        stats = await get_nfl_game_stats_for_matchup(
            game_url="https://www.nfl.com/games/bills-at-texans-2025-reg-12"
        )
    """
    try:
        logger.info(f"Fetching stats for game: {game_url}")

        # Import client
        try:
            from data.nfl_game_stats_client import NFLGameStatsClient
        except ImportError:
            # Try alternate import path
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent
            if (project_root / "src").exists():
                sys.path.insert(0, str(project_root / "src"))

            from data.nfl_game_stats_client import NFLGameStatsClient

        # Fetch stats
        client = NFLGameStatsClient(headless=headless)

        try:
            await client.connect()
            stats = await client.get_game_stats(game_url)

            return {
                "success": True,
                "game_url": game_url,
                "game_data": stats,
                "timestamp": stats.get("timestamp"),
            }

        finally:
            await client.close()

    except Exception as e:
        logger.error(f"Error fetching game stats: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "game_url": game_url,
        }


# ============================================================================
# MCP Resources
# ============================================================================


@mcp.resource("walters://betting-history")
async def get_betting_history(ctx: Context) -> str:
    """Access complete betting history and performance"""
    try:
        history = {
            "total_bets": len(engine.bet_history),
            "recent_bets": engine.bet_history[-10:],
            "performance": {
                "win_rate": _calculate_win_rate(engine.bet_history),
                "roi": _calculate_roi(engine.bet_history),
                "avg_clv": _calculate_avg_clv(engine.clv_tracker),
            },
        }
        return json.dumps(history, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error in get_betting_history: {e}")
        return json.dumps({"error": str(e)})


@mcp.resource("walters://system-config")
async def get_system_config(ctx: Context) -> str:
    """Get current system configuration and settings"""
    try:
        config = {
            "bankroll": engine.analyzer.bankroll.initial_bankroll,
            "risk_settings": {
                "max_bet_percentage": 3.0,
                "kelly_fraction": 0.25,
            },
            "monitoring": {
                "active_games": len(engine.monitored_games),
                "alert_count": len(engine.active_alerts),
            },
            "model_version": "2.0.1",
            "last_updated": datetime.now().isoformat(),
        }
        return json.dumps(config, indent=2)
    except Exception as e:
        logger.error(f"Error in get_system_config: {e}")
        return json.dumps({"error": str(e)})


# ============================================================================
# Helper Functions
# ============================================================================


def _calculate_win_rate(history: List[Dict]) -> float:
    """Calculate win rate from betting history"""
    if not history:
        return 0.0
    wins = sum(1 for bet in history if bet.get("won", False))
    return (wins / len(history)) * 100


def _calculate_roi(history: List[Dict]) -> float:
    """Calculate ROI from betting history"""
    if not history:
        return 0.0
    total_staked = sum(bet.get("stake", 0) for bet in history)
    total_profit = sum(bet.get("profit", 0) for bet in history)
    return (total_profit / total_staked) * 100 if total_staked > 0 else 0.0


def _calculate_avg_clv(clv_tracker: Dict[str, float]) -> float:
    """Calculate average closing line value"""
    if not clv_tracker:
        return 0.0
    return sum(clv_tracker.values()) / len(clv_tracker)


# ============================================================================
# Server Lifecycle
# ============================================================================

# NOTE: FastMCP doesn't support @mcp.startup() or @mcp.shutdown() decorators
# State management handled manually if needed

# @mcp.startup()
# async def on_startup(ctx: Context):
#     """Initialize server on startup"""
#     logger.info("Billy Walters MCP Server starting...")
#
#     # Load saved state if exists
#     try:
#         state_file = Path("walters_state.json")
#         if state_file.exists():
#             with open(state_file, "r") as f:
#                 saved_state = json.load(f)
#                 engine.bet_history = saved_state.get("bet_history", [])
#                 engine.clv_tracker = saved_state.get("clv_tracker", {})
#                 logger.info("Loaded saved state")
#     except Exception as e:
#         logger.warning(f"Could not load saved state: {e}")
#
#     logger.info("Billy Walters MCP Server ready!")
#
#
# @mcp.shutdown()
# async def on_shutdown(ctx: Context):
#     """Cleanup on server shutdown"""
#     logger.info("Billy Walters MCP Server shutting down...")
#
#     # Cancel all monitoring tasks
#     for game_id, monitor_data in engine.monitored_games.items():
#         if not monitor_data["task"].done():
#             monitor_data["task"].cancel()
#
#     # Save state
#     try:
#         state = {
#             "bet_history": engine.bet_history,
#             "clv_tracker": engine.clv_tracker,
#             "timestamp": datetime.now().isoformat(),
#         }
#         with open("walters_state.json", "w") as f:
#             json.dump(state, f, indent=2, default=str)
#         logger.info("State saved. Shutdown complete.")
#     except Exception as e:
#         logger.error(f"Error saving state: {e}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server with FastMCP's built-in runner
    mcp.run()
