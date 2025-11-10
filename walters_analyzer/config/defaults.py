"""
Default configuration values.

This module documents all default values used throughout the application.
Actual defaults are defined in the Pydantic models in settings.py.
"""

# ==================== Skills Defaults ====================

DEFAULT_SHARP_BOOKS = ["Pinnacle", "Circa", "Bookmaker"]
DEFAULT_PUBLIC_BOOKS = ["DraftKings", "FanDuel", "BetMGM"]
DEFAULT_ALERT_THRESHOLD = 0.7
DEFAULT_MONITOR_INTERVAL = 30  # seconds

DEFAULT_ML_MODEL = "xgboost"
DEFAULT_UPDATE_FREQUENCY = "weekly"
DEFAULT_MIN_GAMES_FOR_UPDATE = 10

DEFAULT_TRACKED_SITUATIONS = [
    "sandwich_spot",
    "lookahead_game",
    "revenge_game",
    "division_rivalry",
    "primetime_under"
]

# ==================== Autonomous Agent Defaults ====================

DEFAULT_INITIAL_BANKROLL = 10000.0
DEFAULT_MAX_BET_PERCENTAGE = 3.0
DEFAULT_CONFIDENCE_THRESHOLD = 0.65
DEFAULT_MAX_CONCURRENT_BETS = 10
DEFAULT_LEARNING_RATE = 0.1
DEFAULT_MEMORY_BUFFER_SIZE = 10000

DEFAULT_DAILY_LOSS_LIMIT = 5.0  # percentage
DEFAULT_REQUIRE_CONFIRMATION = True
DEFAULT_PAPER_TRADING_MODE = True

# ==================== Data Connections Defaults ====================

DEFAULT_PINNACLE_ENDPOINT = "https://api.pinnacle.com/"
DEFAULT_DRAFTKINGS_ENDPOINT = "https://api.draftkings.com/"
DEFAULT_PROFOOTBALLDOC_URL = "https://profootballdoc.com/"

# ==================== Monitoring Defaults ====================

DEFAULT_PERFORMANCE_TRACKING = True
DEFAULT_CLV_TRACKING = True
DEFAULT_ALERT_LOG_FILE = "./logs/alerts.log"

DEFAULT_TRACK_ROI = True
DEFAULT_TRACK_WIN_RATE = True
DEFAULT_TRACK_CLV = True
DEFAULT_TRACK_SHARP_ACCURACY = True

# ==================== Global Defaults ====================

DEFAULT_AUTO_START = True
DEFAULT_DEBUG_MODE = False
DEFAULT_LOG_LEVEL = "info"
DEFAULT_MAX_CONCURRENT_REQUESTS = 10
DEFAULT_REQUEST_TIMEOUT = 30000  # milliseconds

# ==================== Development Defaults ====================

DEFAULT_TEST_MODE = False
DEFAULT_MOCK_DATA = False
DEFAULT_CACHE_TTL = 300  # seconds
DEFAULT_RATE_LIMITING_ENABLED = True
DEFAULT_REQUESTS_PER_MINUTE = 60

# ==================== Path Defaults ====================

DEFAULT_DATA_DIR = "data"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_ALERTS_LOG = "logs/alerts.log"
DEFAULT_BIAS_LOG = "logs/bias_log.csv"

# ==================== Billy Walters Methodology Defaults ====================
# These are loaded from billy_walters_config.json

# Position value thresholds
STRONG_PLAY_THRESHOLD = 2.5  # points
MODERATE_PLAY_THRESHOLD = 1.5  # points

# Injury impact multipliers (by severity)
OUT_MULTIPLIER = 1.0
QUESTIONABLE_MULTIPLIER = 0.5
DOUBTFUL_MULTIPLIER = 0.75

# Market movement thresholds
SIGNIFICANT_LINE_MOVE = 1.0  # points
REVERSE_LINE_MOVE_THRESHOLD = 0.5  # points with majority on other side

# Weather impact thresholds
WIND_THRESHOLD = 15  # mph
TEMP_THRESHOLD_LOW = 20  # fahrenheit
TEMP_THRESHOLD_HIGH = 90  # fahrenheit
PRECIPITATION_THRESHOLD = 0.3  # inches

# Betting sizing (Kelly Criterion)
KELLY_FRACTION = 0.25  # quarter Kelly for safety
MAX_BET_SIZE = 3.0  # percentage of bankroll
MIN_BET_SIZE = 0.5  # percentage of bankroll

# ==================== Documentation ====================

DEFAULTS_DOCUMENTATION = """
Configuration Defaults Documentation
=====================================

All settings have sensible defaults defined in the Pydantic models.
This module serves as a reference for those defaults.

Priority Order:
1. Environment variables (.env)
2. CLI arguments
3. User config file (if exists)
4. MCP config file
5. Billy Walters config file
6. Defaults (defined here)

To override any default:
- Set an environment variable (highest priority)
- Pass a CLI argument
- Modify the MCP or Billy Walters config files
- Create a custom config file

For development/testing:
- Use test_mode=True to enable mock data
- Use paper_trading_mode=True for safe testing
- Use debug_mode=True for verbose logging
"""
